# -*- coding: utf-8 -*-
"""decision D51 — losses. A company's tax on the modelled flows, where it sits, turns on its taxable income for the year as a
whole: the flows' income and deductions, what it earns outside the case (taxable_income_other) and the losses it carries
between years (loss_brought_forward). Each item keeps its rate; this stage sets how much of each item's base is still
taxed once the year's losses are set off, and what the flows change in the company's tax on the rest of its income.

- The Mainland (企业所得税法 第五条、第十七条、第十八条; 实施条例 第十条): domestic income and each country's foreign-sourced income apart (财税〔2009〕125号
  第三条（五）). A domestic loss carries five years — ten or eight by its A106000 type (弥补亏损企业类型) — the soonest to
  expire first (公告2025年第1号 A106000 填报说明). The enterprise chooses whether foreign income offsets its domestic losses,
  this year's and earlier years' (A100000 第23行; A106000 第11列; A108000 第6列), and in which countries' order (操作指南
  ¶28); the offset lowers that country's credit limit (¶27). A foreign branch's loss offsets only that country's income;
  its non-actual part carries without a time limit (¶14, 示例二).
- Hong Kong (Cap 112 s19C(4)): set off in the year, the rest carried forward without limit. s61B: a change in shareholding
  whose sole or dominant purpose is to use the loss — the Commissioner's view, judged.
- Singapore (ITA s37(3)(a), (5)): brought-forward losses first, the earliest first, without limit, while the shareholders
  are substantially the same (s37(12)-(14): 50% held by the same persons, looked through companies; the Minister's
  waiver s37(16), then against the same trade only, (17)(a)). Group relief (s37B): a current-year unabsorbed loss of a
  Singapore company to another of its 75% group, against the claimant's assessable income, both electing, in
  proportion to the days of the year they were one group.

What the flows add is the difference they make: the years are added one at a time, each to the earlier ones (with −
without). The change in a year's own figures scales that year's items — income items down when losses shelter them,
deductions down when no income absorbs them; the change it causes in later years, or in a company of the cluster with
no item that year (group relief), is the items' carry (TaxItem.carry, tax, not creditable). Nothing stated and flows
that never net to a loss: the marginal model stands (范围.md 1, cit_rate). Flows netting to a loss while the company's
other income is unknown: asked — the floor takes it absorbed (the marginal model), the ceiling takes none.
"""
from collections import defaultdict
from datetime import date, timedelta
from itertools import permutations, product

from .facts import HEADLINE, NOT_COMPANY, beneficial, source_of, tax_year
from .model import BRANCH, IP_TRANSFER, SHARE_TRANSFER, CN, HK, SG, Graph, HoldEdge
from .rules.tri import DISCRETION, MISSING

HOME = {CN: "cn.loss.carryforward", HK: "hk.loss.carryforward", SG: "sg.loss.carryforward"}
CN_OFFSET, CN_BRANCH = "cn.loss.foreign_offset", "cn.loss.foreign_branch"
HK_CHANGE, SG_CONTINUITY, SG_GROUP = "hk.loss.change", "sg.loss.continuity", "sg.loss.group_relief"
LOSS_RULES = frozenset(HOME.values()) | {CN_OFFSET, CN_BRANCH, HK_CHANGE, SG_CONTINUITY, SG_GROUP}
EPS = 1e-6
CHOICES_MAX = 256                # the Mainland's yearly elections enumerated jointly up to this many; beyond, year by year


def gid(eid):
    return "entity:" + eid       # a decision of one company, not of one flow


# ---------------------------------------------------------------------------------------------- facts of the company

def per_year(v, years):
    """A figure stated once (every modelled year) or by year ({"2026": 100, ...}); None where not stated."""
    if v is None:
        return {y: None for y in years}
    if isinstance(v, dict):
        out = {}
        for y in years:
            x = v.get(str(y), v.get(y))
            out[y] = None if x is None else float(x)
        return out
    return {y: float(v) for y in years}


def vintages(v):
    """loss_brought_forward: [[year, amount], ...] (a third element: the A106000 type code of that year's loss) or
    {year: amount} — the losses unabsorbed at the start of the first modelled year, by the year they were incurred."""
    if not v:
        return []
    rows = v.items() if isinstance(v, dict) else v
    out = []
    for r in rows:
        r = list(r)
        out.append((int(r[0]), float(r[1]), str(r[2]) if len(r) > 2 and r[2] is not None else None))
    return sorted(out)


def code_of(e, y):
    """The company's A106000 type (弥补亏损企业类型代码) for its year y: stated once or by year; None when not stated."""
    v = e.attrs.get("cn_loss_type")
    if isinstance(v, dict):
        v = v.get(str(y), v.get(y))
    return None if v is None else str(v)


def cn_life(P, code, loss_year):
    """Years a Mainland loss carries (EIT art 18; A106000 代码表): 100 five; 200, 300, 400 ten; 500, 600 eight for a 2020
    loss, else five. None: the type is not known."""
    if code is None:
        return None
    if code in ("200", "300", "400"):
        return int(P["cn.loss.carryforward_years_extended"])
    if code in ("500", "600") and loss_year == int(P["cn.loss.covid_loss_year"]):
        return int(P["cn.loss.carryforward_years_2020"])
    return int(P["cn.loss.carryforward_years"])


def branch_losses(e, years):
    """decision D47: a Mainland company's branch loss places no flow — it is the head office's datum (branch_profit_<j> < 0),
    in the year the branch's year ends."""
    out = {}
    for j in (HK, SG):
        v = e.attrs.get("branch_profit_" + j.lower())
        if v is not None and float(v) < 0:
            on = e.attrs.get("branch_period_end_" + j.lower())
            y = (date.fromisoformat(on) if isinstance(on, str) else on).year if on else years[-1]
            out[(y, j)] = -float(v)
    return out


# ------------------------------------------------------------------------------------------------- the year's pieces

def pieces_of(graph, labels, eid, jur):
    """The company's items in its own jurisdiction's income tax, one piece per year: [item, flow, eid, year, segment,
    base, sign]. Its receipts (+1; a nil or exempt item is no taxable income, 实施条例 第十条) and its deductions (−1; an
    IP bought is deducted over its years, decision D27). The Mainland's segments: domestic (CN) and each source country; elsewhere
    one. Deferred, closed and settled items are left as they are."""
    out = []
    for lb in labels.values():
        f = lb.flow
        for it in lb.items:
            if it.jur != jur or it.levy != "income" or it.deferred or it.actual is not None or it.rate * it.base_share <= 0:
                continue
            if it.deduction:
                if f.payer != eid or it.borne_by != "payer":
                    continue
                n = int(f.attrs.get("ip_horizon_years") or 1) if f.income == IP_TRANSFER else 1
                y0 = tax_year(f, jur)
                for k in range(n):
                    out.append([it, f, eid, y0 + k, jur, f.amount * it.base_share / n, -1])
            elif f.payee == eid:
                src = source_of(graph, f)
                out.append([it, f, eid, tax_year(f, jur), src if jur == CN and src != CN else jur, f.amount * it.base_share, 1])
    return out


# --------------------------------------------------------------------------------------------- ownership over time

def holds_at(graph, on):
    """The holdings after every share transfer up to and including `on` (the buyer takes the seller's stake)."""
    hs = [HoldEdge(h.holder, h.held, h.ratio, h.since, h.cost) for h in graph.holds]
    for f in sorted((g for g in graph.flows if g.income == SHARE_TRANSFER and g.target and g.on is not None and g.on <= on),
                    key=lambda g: g.on):
        for h in hs:
            if h.holder == f.payee and h.held == f.target:
                h.holder, h.since = f.payer, f.on
    return Graph(graph.entities, hs, graph.flows, graph.members)


def ultimate(g, eid, seen=()):
    """s37(14)(b): shares a company holds are held by its shareholders — down to the holders the case places nothing
    above, and the part of a company's shares the case does not place ('?<company>'); in percent of eid's shares."""
    out, placed = defaultdict(float), 0.0
    for h in g.holds:
        if h.held != eid or h.holder in seen:
            continue
        placed += h.ratio
        holder = g.entities.get(h.holder)
        if holder is None or holder.type in NOT_COMPANY or not g.holders_of(h.holder):
            out[h.holder] += h.ratio
            continue
        for p, s in ultimate(g, h.holder, seen + (eid,)).items():
            out[p] += h.ratio * s / 100.0
    if placed < 100.0 - EPS:
        out["?" + eid] += 100.0 - placed
    return out


def common(a, b):
    return sum(min(a.get(p, 0.0), b.get(p, 0.0)) for p in set(a) | set(b))


def year_end(y):
    return date(y, 12, 31)


class SgTests:
    """Singapore's two ownership tests, from the case's holdings and share transfers (cached)."""

    def __init__(self, graph, P, first):
        self.graph, self.P, self.first, self._own, self._t, self._f = graph, P, first, {}, {}, {}

    def owners(self, e, on):
        if (e, on) not in self._own:
            self._own[(e, on)] = ultimate(holds_at(self.graph, on), e)
        return self._own[(e, on)]

    def continuity(self, e, ly, y):
        """s37(12), (14): True, False, or None (open) — the shareholders at the end of the loss year and on the first day
        of the year of assessment of the deduction (the end of its basis year) are at least 50% the same persons. A loss
        from before the modelled years: the case's word (sg_loss_shareholders_same, as at the start of the modelled
        years) with no change since; with a change since, open."""
        k = (e, ly, y)
        if k not in self._t:
            lim, now = self.P["sg.loss.shareholders_same_min"], self.owners(e, year_end(y))
            if ly >= self.first:
                r = common(self.owners(e, year_end(ly)), now) >= lim - 1e-9
            else:
                stated = self.graph.entities[e].attrs.get("sg_loss_shareholders_same")
                start = self.owners(e, date(self.first, 1, 1) - timedelta(days=1))
                if stated is False or common(start, now) < lim - 1e-9:
                    r = False if stated is False else None
                elif stated is True and common(start, now) >= 100.0 - 1e-6:
                    r = True
                else:
                    r = None
            self._t[k] = r
        return self._t[k]

    def group(self, t, c, y):
        """s37B(2), (3), (5), (9): the fraction of year y two Singapore companies were continuously one group up to its last
        day (A / B: the model's years are the companies' basis periods, ending on the same day), 0 when not one group on
        that day. 75% of the ordinary shares (the graph's holdings) one in the other, or a third Singapore company's in
        both, multiplied through Singapore companies (s37B(19): incorporated in Singapore)."""
        k = (t, c, y)
        if k in self._f:
            return self._f[k]
        lim = self.P["sg.group_relief.ratio_min"]
        sgco = lambda e: e.attrs.get("incorporated_in", e.loc) == SG and e.type not in NOT_COMPANY

        def member(on):
            g = holds_at(self.graph, on)
            own = lambda x, z: beneficial(g, x, z, via=sgco) >= lim - 1e-9
            return own(t, c) or own(c, t) or any(own(x, t) and own(x, c) for x in g.entities
                                                 if x not in (t, c) and sgco(g.entities[x]))
        start, end = date(y, 1, 1), year_end(y)
        out = 0.0
        if sgco(self.graph.entities[t]) and sgco(self.graph.entities[c]) and member(end):
            since = start
            for d in sorted({f.on for f in self.graph.flows if f.income == SHARE_TRANSFER and f.on and start < f.on <= end},
                            reverse=True):
                if not member(d - timedelta(days=1)):
                    since = d
                    break
            out = ((end - since).days + 1) / ((end - start).days + 1)
        self._f[k] = out
        return out


def hk_change_on(graph, eid):
    """s61B(a): the first date a share transfer in the case changes the shareholding of the company or of one above it."""
    above, todo = set(), [eid]
    while todo:
        x = todo.pop()
        if x in above:
            continue
        above.add(x)
        todo += [h.holder for h in graph.holds if h.held == x]
    ds = sorted(f.on for f in graph.flows if f.income == SHARE_TRANSFER and f.target in above and f.on)
    return ds[0] if ds else None


# --------------------------------------------------------------------------------------------------------- the runs

def _use(vint, x, y, ok=None):
    """Sets off up to x from the losses usable in year y — the soonest to expire first, then the earliest incurred
    (A106000: 先到期亏损先弥补、同时到期亏损先发生的先弥补); expired ones drop. A vintage: [year, left, last year or None].
    Returns what is left of x."""
    vint[:] = [v for v in vint if v[2] is None or v[2] >= y]
    for v in sorted(vint, key=lambda v: (v[2] if v[2] is not None else 10 ** 6, v[0])):
        if x <= EPS:
            break
        if v[1] <= EPS or (ok is not None and not ok(v)):
            continue
        t = min(x, v[1])
        v[1] -= t
        x -= t
    vint[:] = [v for v in vint if v[1] > EPS]
    return x


def cn_run(years, w, cfg, P):
    """One Mainland company over the years: bases {(y, segment)} after losses, and the rules engaged each year."""
    life = lambda code, y: cn_life(P, code, y) or cfg["life_unknown"]
    dom = [[ly, a, ly + life(code if code is not None else w["code"](ly), ly)] for ly, a, code in w["bf"]]
    fl = defaultdict(list)
    countries = sorted({s for (_, s) in w["inc"] if s != CN} | {c for (_, c) in w["branch"]})
    out, marks = {}, defaultdict(set)
    for y in years:
        net = {}
        for c in countries:
            x = w["inc"].get((y, c), 0.0) - w["branch"].get((y, c), 0.0)
            if w["branch"].get((y, c)):
                marks[y].add(CN_BRANCH)
            if x > EPS and fl[c]:
                x2 = _use(fl[c], x, y)
                if x2 < x - EPS:
                    marks[y].add(CN_BRANCH)
                x = x2
            net[c] = x
        own = w["other"][y] + w["inc"].get((y, CN), 0.0) - w["ded"].get(y, 0.0)          # 当年境内所得额
        whole = own + sum(w["inc"].get((y, c), 0.0) - w["branch"].get((y, c), 0.0) for c in countries)
        d = _use(dom, own, y) if own > EPS else own
        cur, d = max(0.0, -d), max(0.0, d)
        for c in cfg["offset"].get(y) or ():             # 境外应税所得抵减境内亏损: this year's, then earlier years'
            if net.get(c, 0.0) <= EPS:
                continue
            before = net[c]
            t = min(net[c], cur)
            net[c] -= t
            cur -= t
            if net[c] > EPS:
                net[c] = _use(dom, net[c], y)
            if net[c] < before - EPS:
                marks[y].add(CN_OFFSET)
        if cur > EPS:
            dom.append([y, cur, y + life(w["code"](y), y)])
        lossy = {c: -net[c] for c in countries if net[c] < -EPS}
        if lossy:
            if whole >= -EPS:                             # 操作指南 ¶14(1): all of it non-actual
                actual = {c: 0.0 for c in lossy}
            elif len(lossy) == 1:                         # ¶14(2): the part beyond the enterprise's profit is actual
                c = next(iter(lossy))
                actual = {c: min(lossy[c], -whole)}
            else:                                         # several countries: how the actual part divides — judged
                actual = {c: (lossy[c] if cfg["branch_actual"] else 0.0) for c in lossy}
            for c, a in lossy.items():
                if a - actual[c] > EPS:
                    fl[c].append([y, a - actual[c], None])
                if actual[c] > EPS:
                    fl[c].append([y, actual[c], y + life(w["code"](y), y)])
                net[c] = 0.0
        out[(y, CN)] = d
        for c in countries:
            out[(y, c)] = max(0.0, net[c])
    return out, marks


def hk_run(years, w, cfg):
    """One Hong Kong company (s19C(4)); under s61B the losses before a change in shareholding stay off the profits after
    it — a later year's, and the change's own year when all its flows come after the change."""
    pool = [[ly, a, None] for ly, a, _ in w["bf"]]
    out, marks, change = {}, defaultdict(set), cfg["change"]
    for y in years:
        ti = w["other"][y] + w["inc"].get((y, HK), 0.0) - w["ded"].get(y, 0.0)
        if ti > EPS:
            after = change is not None and (y > change.year or (y == change.year and w["first"].get(y) and w["first"][y] > change))
            ok = (lambda v, _c=change.year: v[0] >= _c) if after else None
            left = _use(pool, ti, y, ok)
            if ok is not None and left > EPS and any(v[0] < change.year for v in pool):
                marks[y].add(HK_CHANGE)
            ti = left
        elif ti < -EPS:
            pool.append([y, -ti, None])
            ti = 0.0
        out[(y, HK)] = max(0.0, ti)
    return out, marks


def sg_run(years, ents, w, cfg, tests):
    """The Singapore companies together: s37(3)(a) — brought-forward losses first, the earliest first, only while the
    shareholders stay substantially the same (s37(12), (13): a loss failing the test is gone for good, unless waived
    and against the same trade); then s37B transfers of each year's unabsorbed loss to group companies with assessable
    income left, the claimants with the highest rate first."""
    pools = {e: [[ly, a, None] for ly, a, _ in w[e]["bf"]] for e in ents}
    out, marks = {}, defaultdict(set)
    for y in years:
        ai, qd = {}, {}
        for e in ents:
            ti = w[e]["other"][y] + w[e]["inc"].get((y, SG), 0.0) - w[e]["ded"].get(y, 0.0)
            if ti > EPS:
                keep = []
                for v in sorted(pools[e]):
                    r = tests.continuity(e, v[0], y)
                    if r is not True and not cfg["sg_allow"][e][r is None]:
                        marks[y].add(SG_CONTINUITY)
                        continue
                    t = min(ti, v[1])
                    v[1] -= t
                    ti -= t
                    if v[1] > EPS:
                        keep.append(v)
                pools[e] = keep
                ai[e], qd[e] = ti, 0.0
            else:
                ai[e], qd[e] = 0.0, max(0.0, -ti)
        ai0, qd0 = dict(ai), dict(qd)
        claimed, given = defaultdict(float), defaultdict(float)
        for t in sorted(e for e in ents if qd[e] > EPS and cfg["elect"][e]):
            for c in sorted((e for e in ents if e != t and cfg["elect"][e]), key=lambda e: (-cfg["rate"][e], e)):
                frac = tests.group(t, c, y)
                if frac <= 0 or ai[c] <= EPS or qd[t] <= EPS:
                    continue
                amt = min(ai0[c] * frac - claimed[c], qd0[t] * frac - given[t], ai[c], qd[t])   # s37B(9), (10)
                if amt > EPS:
                    ai[c] -= amt
                    qd[t] -= amt
                    claimed[c] += amt
                    given[t] += amt
                    marks[y].add(SG_GROUP)
        for e in ents:
            if qd[e] > EPS:
                pools[e].append([y, qd[e], None])
            out[(e, y, SG)] = ai[e]
    return out, marks


# -------------------------------------------------------------------------------------------------- the cluster

class Cluster:
    """The companies one run computes together: a Mainland or Hong Kong company alone; the case's Singapore companies
    together (group relief)."""

    def __init__(self, jur, ents, graph, labels, P):
        self.jur, self.ents, self.graph, self.P, self.years = jur, ents, graph, P, []
        self.pieces = [p for e in ents for p in pieces_of(graph, labels, e.id, jur)]
        self.rate = {}
        for e in ents:
            mine = [p[0].rate for p in self.pieces if p[2] == e.id]
            self.rate[e.id] = mine[0] if mine else float(e.attrs.get("cit_rate") or P[HEADLINE[jur]])
        self.paid = defaultdict(float)                    # the Mainland: foreign tax available, by (company, year, country)
        if jur == CN:
            for it, f, eid, y, seg, base, sign in self.pieces:
                if sign > 0 and seg != CN:
                    self.paid[(eid, y, seg)] += f.amount * it.creditable / 100.0
        self.tests = None

    def inputs(self, e, upto, other):
        inc, ded = defaultdict(float), defaultdict(float)
        for it, f, eid, y, seg, base, sign in self.pieces:
            if eid != e.id or y not in upto:
                continue
            if sign > 0:
                inc[(y, seg)] += base
            else:
                ded[y] += base
        first = {}
        for it, f, eid, y, seg, base, sign in self.pieces:
            if eid == e.id and y in upto and f.on is not None:
                first[y] = min(first.get(y, f.on), f.on)
        return {"inc": inc, "ded": ded, "other": other[e.id], "bf": vintages(e.attrs.get("loss_brought_forward")), "first": first,
                "branch": branch_losses(e, self.years) if self.jur == CN else {}, "code": lambda y, _e=e: code_of(_e, y)}

    def run(self, cfg, upto):
        """Bases after losses {(eid, y, segment)} with the flows of the years in `upto`, and the rules engaged."""
        if self.jur == SG:
            w = {e.id: self.inputs(e, upto, cfg["other"]) for e in self.ents}
            return sg_run(self.years, [e.id for e in self.ents], w, cfg, self.tests)
        e = self.ents[0]
        w = self.inputs(e, upto, cfg["other"])
        out, marks = cn_run(self.years, w, cfg, self.P) if self.jur == CN else hk_run(self.years, w, cfg)
        return {(e.id,) + k: v for k, v in out.items()}, marks

    def tax(self, bases):
        """What the bases cost at each company's rate; the Mainland's foreign tax credited by country, with its five-year
        carry-forward (财税〔2009〕125号 第九条), so that an election is judged on what it really saves."""
        total = sum(self.rate[eid] / 100.0 * v for (eid, y, seg), v in bases.items())
        if self.jur != CN:
            return total
        horizon = int(self.P["cn.ftc.carryforward_years"])
        for eid in {k[0] for k in bases}:
            for c in sorted({k[2] for k in bases if k[0] == eid and k[2] != CN}):
                carry = []
                for y in self.years:
                    limit = self.rate[eid] / 100.0 * bases.get((eid, y, c), 0.0)
                    own = self.paid.get((eid, y, c), 0.0)
                    carry = [v for v in carry if y - v[0] <= horizon and v[1] > EPS]
                    used = min(limit, own + sum(v[1] for v in carry))
                    from_own = min(own, used)
                    left = used - from_own
                    for v in sorted(carry):
                        t = min(v[1], left)
                        v[1] -= t
                        left -= t
                    if own - from_own > EPS:
                        carry.append([y, own - from_own])
                    total -= used
        return total

    def cost(self, cfg):
        """The tax the flows add, over the cluster and the years: with every year's flows, less without any."""
        return self.tax(self.run(cfg, set(self.years))[0]) - self.tax(self.run(cfg, set())[0])


# -------------------------------------------------------------------------------------------------- the decisions

def between(cl, cfg, key, a, b, choose, rid, eid, keys, source=MISSING, register=True):
    """Two values of an open matter: the same cost — no question; else the cheaper at the floor, the dearer at the
    ceiling, the question registered (in the final pass). Returns the cfg with the value taken."""
    ca, cb = cl.cost(dict(cfg, **{key: a})), cl.cost(dict(cfg, **{key: b}))
    if abs(ca - cb) <= 1e-6:
        return dict(cfg, **{key: a})
    lo, hi = (a, b) if ca < cb else (b, a)
    return dict(cfg, **{key: lo if choose(rid, gid(eid), keys, source, register) else hi})


def offsets(cl, cfg, worst=False, elected=False):
    """The Mainland election each year with foreign income: none, or foreign income offsetting the domestic losses in
    an order of countries (操作指南 ¶28) — the set that costs least (or most): jointly while few, else year by year.
    elected: the return says it offsets — only the order is open."""
    opts = []
    for y in sorted({p[3] for p in cl.pieces if p[6] > 0 and p[4] != CN}):
        cs = sorted({p[4] for p in cl.pieces if p[3] == y and p[6] > 0 and p[4] != CN})
        opts.append((y, ([] if elected else [None]) + [tuple(x) for x in permutations(cs)]))
    if not opts:
        return {}
    pick = max if worst else min
    n = 1
    for _, o in opts:
        n *= len(o)
    if n <= CHOICES_MAX:
        ys = [y for y, _ in opts]
        best = pick(product(*[o for _, o in opts]),
                    key=lambda ch: (round(cl.cost(dict(cfg, offset=dict(zip(ys, ch)))), 6), sum(c is not None for c in ch)))
        return {y: c for y, c in zip(ys, best) if c is not None}
    chosen = {}
    for y, o in opts:
        chosen[y] = pick(o, key=lambda c: round(cl.cost(dict(cfg, offset=dict(chosen, **{y: c}))), 6))
    return {y: c for y, c in chosen.items() if c is not None}


def engaged(cl, other):
    """The marginal model stands unless the case states the company's other income or its losses (a branch's loss
    included), or the flows net to a loss in some year."""
    for e in cl.ents:
        if any(v is not None for v in other[e.id].values()) or vintages(e.attrs.get("loss_brought_forward")):
            return True
        if cl.jur == CN and branch_losses(e, cl.years):
            return True
    net = defaultdict(float)
    for it, f, eid, y, seg, base, sign in cl.pieces:
        net[(eid, y)] += sign * base
    return any(v < -EPS for v in net.values())


def decide_cluster(cl, choose, ex_ante):
    """Every open matter of the cluster: its value when the case states it; else the cost decides — an enterprise's own
    election, ex ante, the cheaper; anything else asked (floor the cheaper, ceiling the dearer). Two passes: the first
    from the favourable values, the second takes each matter again with the others as the first left them, and
    registers what is still open — a question is asked only where it moves the tax."""
    P, ids = cl.P, [e.id for e in cl.ents]
    other = {e.id: per_year(e.attrs.get("taxable_income_other"), cl.years) for e in cl.ents}
    for e in cl.ents:                                     # decision D06: a company the plan creates has nothing else
        if e.attrs.get("created_by_plan"):
            other[e.id] = {y: (0.0 if v is None else v) for y, v in other[e.id].items()}
    if not engaged(cl, other):
        return None
    scale = 10.0 * (1.0 + sum(p[5] for p in cl.pieces) + sum(a for e in cl.ents for _, a, _ in vintages(e.attrs.get("loss_brought_forward")))
                    + sum(abs(v) for o in other.values() for v in o.values() if v is not None))
    fill = lambda cfg_, e, x: dict(cfg_["other"], **{e: {y: (x if v is None else v) for y, v in other[e].items()}})
    said = {e.id: e.attrs.get("sg_group_relief_elected") for e in cl.ents}
    yes, no = {k: v is not False for k, v in said.items()}, {k: v is True for k, v in said.items()}
    cfg = {"other": {e: {y: (scale if v is None else v) for y, v in o.items()} for e, o in other.items()}, "offset": {},
           "life_unknown": int(P["cn.loss.carryforward_years_extended"]), "branch_actual": False, "change": None,
           "rate": cl.rate, "sg_allow": {}, "elect": yes}
    allow = {}                                            # company -> (failed: allowed?, open: allowed?) in each reading
    for e in cl.ents:
        stated = e.attrs.get("sg_loss_shareholders_same")
        waived, same = e.attrs.get("sg_loss_continuity_waived"), e.attrs.get("sg_loss_same_trade")
        w_ok = True if (waived and same) else False if (waived is False or same is False) else None
        fav = (w_ok is not False, w_ok is not False or stated is not False)        # the s37(16) waiver, or the test met
        unfav = (w_ok is True, w_ok is True)
        keys = [("%s.sg_loss_shareholders_same" % e.id, MISSING)] if stated is not False else []
        if w_ok is None:
            keys += [("%s.sg_loss_continuity_waived" % e.id, DISCRETION), ("%s.sg_loss_same_trade" % e.id, DISCRETION)]
        allow[e.id] = (fav, unfav, keys)
        cfg["sg_allow"][e.id] = fav
    if cl.jur == SG:
        cl.tests = SgTests(cl.graph, P, cl.years[0])
    home = HOME[cl.jur]
    for final in (False, True):
        for e in cl.ents:                                 # other income unknown: enough to absorb all (the marginal model) or none
            if any(v is None for v in other[e.id].values()):
                cfg = between(cl, cfg, "other", fill(cfg, e.id, scale), fill(cfg, e.id, 0.0), choose, home, e.id,
                              ["%s.taxable_income_other" % e.id], register=final)
        if cl.jur == CN:
            e = cl.ents[0]
            bf = vintages(e.attrs.get("loss_brought_forward"))
            if any((c if c is not None else code_of(e, ly)) is None for ly, _, c in bf) or any(code_of(e, y) is None for y in cl.years):
                cfg = between(cl, cfg, "life_unknown", int(P["cn.loss.carryforward_years_extended"]), int(P["cn.loss.carryforward_years"]),
                              choose, home, e.id, ["%s.cn_loss_type" % e.id], register=final)
            if branch_losses(e, cl.years):
                cfg = between(cl, cfg, "branch_actual", False, True, choose, CN_BRANCH, e.id, ["%s.cn_branch_actual_loss" % e.id],
                              DISCRETION, register=final)
            stated = e.attrs.get("cn_foreign_loss_offset")
            if stated is not None:                        # the election as filed: offset (in the cheapest order) or not
                cfg["offset"] = offsets(cl, cfg, elected=True) if stated else {}
            elif ex_ante:                                 # the enterprise's own election under the single objective
                cfg["offset"] = offsets(cl, cfg)
            else:                                         # a past return's election, not stated
                cfg = between(cl, cfg, "offset", offsets(cl, cfg), offsets(cl, cfg, worst=True), choose, CN_OFFSET, e.id,
                              ["%s.cn_foreign_loss_offset" % e.id], register=final)
        if cl.jur == HK:
            e = cl.ents[0]
            yc = hk_change_on(cl.graph, e.id)
            stated = e.attrs.get("hk_loss_change_dominant_purpose")
            if yc is not None and stated is not None:
                cfg["change"] = yc if stated else None
            elif yc is not None:
                cfg = between(cl, cfg, "change", None, yc, choose, HK_CHANGE, e.id, ["%s.hk_loss_change_dominant_purpose" % e.id],
                              DISCRETION, register=final)
        if cl.jur == SG:
            for e in cl.ents:                             # the test open or failed: met (or waived) at the floor, not at the ceiling
                fav, unfav, keys = allow[e.id]
                if keys:
                    cfg = between(cl, cfg, "sg_allow", dict(cfg["sg_allow"], **{e.id: fav}), dict(cfg["sg_allow"], **{e.id: unfav}),
                                  choose, SG_CONTINUITY, e.id, keys, register=final)
                else:
                    cfg["sg_allow"] = dict(cfg["sg_allow"], **{e.id: fav})
            if yes != no and ex_ante:                     # s37B(11): both companies elect when it saves
                cfg["elect"] = yes if cl.cost(dict(cfg, elect=yes)) < cl.cost(dict(cfg, elect=no)) - 1e-6 else no
            elif yes != no:
                cfg = between(cl, cfg, "elect", yes, no, choose, SG_GROUP, ids[0],
                              ["%s.sg_group_relief_elected" % k for k, v in said.items() if v is None], register=final)
    return cfg


# ------------------------------------------------------------------------------------------------------ the stage

def loss_stage(graph, labels, P, choose, ex_ante, members):
    """decision D51. Sets each company's items to what its losses leave taxed (module docstring)."""
    from .engine import Defect
    years = sorted({f.on.year for f in graph.flows if f.on is not None} | {tax_year(f, CN) for f in graph.flows if f.on is not None})
    if not years:
        return
    by_jur = defaultdict(list)
    for e in graph.entities.values():
        if e.type == BRANCH or e.type in NOT_COMPANY or e.loc not in HOME or e.id not in members:
            continue
        by_jur[e.loc].append(e)
    clusters = [Cluster(j, [e], graph, labels, P) for j in (CN, HK) for e in by_jur.get(j, [])]
    if by_jur.get(SG):
        clusters.append(Cluster(SG, by_jur[SG], graph, labels, P))
    for cl in clusters:
        if not cl.pieces:
            continue
        ys = sorted(set(years) | {p[3] for p in cl.pieces})
        cl.years = list(range(ys[0], ys[-1] + 1))
        cfg = decide_cluster(cl, choose, ex_ante)
        if cfg is not None:
            apply(cl, cfg, Defect)


def apply(cl, cfg, Defect):
    """The years added one at a time (with − without): each year's own change scales that year's items; what it changes
    in later years, or in a company of the cluster with no item that year, is carried on the year's items."""
    target, cons, marks_all = {}, defaultdict(float), defaultdict(set)
    has = {(p[2], p[3], p[4]) for p in cl.pieces}
    prev, _ = cl.run(cfg, set())
    upto = set()
    for y in cl.years:
        if not any(p[3] == y for p in cl.pieces):
            continue
        upto.add(y)
        cur, marks = cl.run(cfg, upto)
        for yy, ms in marks.items():
            marks_all[yy] |= ms
        for key in has:
            if key[1] == y:
                target[key] = 0.0
        for key in set(cur) | set(prev):
            d = cur.get(key, 0.0) - prev.get(key, 0.0)
            if abs(d) <= EPS:
                continue
            eid, y2, seg = key
            if y2 < y:
                raise Defect("losses: adding year %d's flows moved year %d of %s" % (y, y2, eid))
            if y2 == y and key in has:
                target[key] += d
            else:
                cons[(y, eid)] += d
        prev = cur
    new = {}                                              # piece index -> its base after losses
    for (eid, y, seg), tgt in target.items():
        ps = [i for i, p in enumerate(cl.pieces) if (p[2], p[3], p[4]) == (eid, y, seg)]
        inc = sum(cl.pieces[i][5] for i in ps if cl.pieces[i][6] > 0)
        ded = sum(cl.pieces[i][5] for i in ps if cl.pieces[i][6] < 0)
        k = s = 1.0
        if tgt >= inc - ded - EPS:                        # less relief than the flows' own sum: deductions not absorbed
            if ded > EPS:
                s = min(1.0, max(0.0, (inc - tgt) / ded))
        elif inc > EPS:                                   # income sheltered by losses
            k = min(1.0, max(0.0, (tgt + ded) / inc))
        rem = tgt - (k * inc - s * ded)
        if abs(rem) > EPS:
            cons[(y, eid)] += rem
        for i in ps:
            new[i] = cl.pieces[i][5] * (k if cl.pieces[i][6] > 0 else s)
    carry = defaultdict(float)                            # piece index -> tax carried
    for (y, eid), d in cons.items():
        if abs(d) <= EPS:
            continue
        on = [i for i, p in enumerate(cl.pieces) if p[3] == y and p[2] == eid] or [i for i, p in enumerate(cl.pieces) if p[3] == y]
        w = sum(cl.pieces[i][5] for i in on)
        for i in on:
            carry[i] += d * cl.pieces[i][5] / w * cl.rate[eid] / 100.0
    items = {}
    for i, p in enumerate(cl.pieces):
        items.setdefault(id(p[0]), []).append(i)
    for idxs in items.values():
        it, f = cl.pieces[idxs[0]][0], cl.pieces[idxs[0]][1]
        old = sum(cl.pieces[i][5] for i in idxs)
        nb = sum(new.get(i, cl.pieces[i][5]) for i in idxs)
        c = sum(carry.get(i, 0.0) for i in idxs)
        if abs(nb - old) <= EPS and abs(c) <= EPS:
            continue
        if it.pre_loss is None:
            it.pre_loss = it.base_share
        it.base_share = it.base_share * nb / old
        it.credit = min(it.credit, it.rate * it.base_share)
        if f.amount:
            it.carry += 100.0 * c / f.amount
        moved = dict(it.loss_years or {})                 # the change in the item's tax, by the year it falls in (GloBE)
        for i in idxs:
            y, sign = cl.pieces[i][3], cl.pieces[i][6]
            moved[y] = moved.get(y, 0.0) + sign * it.rate / 100.0 * (new.get(i, cl.pieces[i][5]) - cl.pieces[i][5]) + carry.get(i, 0.0)
        it.loss_years = moved
        for r in [HOME[cl.jur]] + sorted(set().union(*(marks_all.get(cl.pieces[i][3], set()) for i in idxs))):
            if r not in it.cites:
                it.cites.append(r)


def p2_loss_tax(labels, eid, year, P):
    """GloBE Art 4.4.1 (MMT Regulations reg 44, 45): a loss the company uses or creates carries deferred tax, at the
    minimum rate when its own rate is higher, whatever the accounts recognise (Art 4.4.1(c); reg 45(1)(c)). The cash
    tax the loss stage moved in a year is in the covered taxes already; this adds the deferred tax that goes with it —
    the move undone at the lower of the two rates. A loss moved to a group company (s37B) leaves no deferred tax: its
    carry comes back as cash. The IP bought (decision D27) is left out of the cash (engine.p2_tax): its move counts in full
    here, less the same deferred tax."""
    m, total = P["p2.minimum_rate"], 0.0
    for lb in (labels or {}).values():
        f = lb.flow
        for it in lb.items:
            if it.levy != "income" or it.deferred or it.rate <= 0 or not it.loss_years or year not in it.loss_years:
                continue
            if (f.payer if it.borne_by == "payer" else f.payee) != eid:
                continue
            d = it.loss_years[year]
            if it.deduction and f.income == IP_TRANSFER:
                total += d
            total -= d * min(it.rate, m) / it.rate
    return total
