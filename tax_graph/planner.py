"""planner.py (优化方案 v2 §1): a case and the answers so far -> a question sheet, or one concrete plan.

    plan(template, event, case, answers) -> Outcome(questions, plan)

The plan is one when every ruling is answered yes or no; rulings answered "unknown" fork it into strategies (优化方案.md
§6): the head holds the comparison, each strategy its own plan and workpack.

Each round:
  1. every candidate structure is evaluated with the answers: data become facts of the case, confirmed actions and
     rulings become answers to the rules' conditions (addressed to a role or a flow, never to a field name at large);
  2. the plan candidate is the one with the least guaranteed tax — the tax under the worst outcome of every
     judgement and every datum still unknown, with the plan's own actions done — ties: least best-case tax, fewest
     open judgements, fewest companies (J6: Γ-maximin; E2/E3: an answer that holds in every completion);
  3. questions, in this order: data without which a tax is unbounded (always asked); data whose favourable answer
     could lower the plan's guaranteed tax or let another candidate beat it; actions the plan relies on that are not
     yet confirmed; rulings that would change the plan; library material (a holiday calendar) the deadlines need;
  4. no question left -> the plan: structure, actions, taxes, deadlines and the judgements it still depends on, each
     placed in its jurisdiction region (CN, HK, SG, CN∩HK, CN∩SG, HK∩SG, CN∩HK∩SG).
Answers are data values (with a source), yes / no, or "unknown". An unknown datum stays unknown: it is taken at its
worst, and if a tax is unbounded without it the candidates that need it cannot be planned. Nothing is filled in.
"""
import copy
import csv
import json
import re
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Dict, List, Optional

from .data.domain import ADJUSTABLE
from .engine import (EX_ANTE, OPPOSITE, PEM_RULE, RULES_BY_ID, Bounds, CaseCtx, Defect, Undecidable, bounds, flow_name,
                     outside_steps, plan_favourable)
from .ex_ante import validate_core
from .model import JURISDICTIONS, HoldEdge
from .params import Params
from .regions import absolute_key, item_region, name as region_name, order_key, rule_region
from .rules.eval import SHARED_GROUPS
from .rules.model import Discretion, Leaf, Not, And, Or, leaves
from .rules.tri import DATA, DISCRETION, MISSING, PLAN, Need
from .scenarios import NEW, same_settled
from . import scope as scope_mod

STEP_TEXT = {"ip_transfer": "IP transferred from %s to %s",       # decision D19: steps whose tax no rule computes
             # decision D30: a levy a group company bears on a flow dated before the law the library starts from
             "before_law": "flow %s (%s) predates the commencement of %s (%s); the earlier rules are not in the library (it keeps only the rules in force), so its %s is not computed"}


def _step_text(step):
    return STEP_TEXT.get(step[0], step[0] + ": %s → %s") % tuple(step[1:])

EPS = 0.005
CONTENTION_MAX = 12
GLOSS_FILE = Path(__file__).resolve().parent / "data" / "field_gloss.csv"
FORMS_FILE = Path(__file__).resolve().parents[1] / "official" / "form_fields.csv"
ISO = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def _load_gloss():
    with open(str(GLOSS_FILE), encoding="utf-8-sig") as f:       # the dictionary may carry a BOM
        return {r["field"]: r for r in csv.DictReader(f)}


def _load_forms():
    out = {}
    if FORMS_FILE.exists():
        with open(str(FORMS_FILE), encoding="utf-8-sig") as f:
            for r in csv.DictReader(f):
                out.setdefault(r["maps_to"], []).append("%s · %s" % (r["form_id"], r["label"][:40]))
    return out


GLOSS, FORMS = _load_gloss(), _load_forms()
JUR_NAME = {"cn": "the Mainland", "hk": "Hong Kong", "sg": "Singapore"}


def _gloss(f):
    """A field's gloss row; <name>_hk / _sg (a jurisdiction's own group fact, decision D17) reads <name>'s, the place named."""
    if f in GLOSS:
        return GLOSS[f]
    head, _, j = f.rpartition("_")
    if j in JUR_NAME and head in GLOSS:
        g = dict(GLOSS[head])
        g["gloss"] = "%s: %s" % (JUR_NAME[j], g.get("gloss", head))
        return g
    if j.isdigit() and head in GLOSS:                       # a year's own figure (p2_eur_rate_2027)
        g = dict(GLOSS[head])
        g["gloss"] = "FY %s: %s" % (j, g.get("gloss", head))
        return g
    return {}


# ---------------------------------------------------------------- answers
@dataclass
class Answers:
    data: Dict[str, object] = field(default_factory=dict)        # address -> value, {"value", "source"} or "unknown"
    actions: Dict[str, str] = field(default_factory=dict)        # address -> yes / no / unknown
    rulings: Dict[str, str] = field(default_factory=dict)        # address -> yes / no / unknown, or {"value", "reason"}
    library: Dict[str, object] = field(default_factory=dict)     # "calendar:SG:2028" -> answer

    @classmethod
    def load(cls, path):
        p = Path(path)
        if not p.exists():
            return cls()
        d = json.loads(p.read_text(encoding="utf-8"))
        return cls(d.get("data", {}), d.get("actions", {}), d.get("rulings", {}), d.get("library", {}))

    def value(self, key):
        v = self.data.get(key)
        if isinstance(v, dict):
            v = v.get("value")
        return v

    def answered(self, key):
        return key in self.data or key in self.actions or key in self.rulings or key in self.library

    def ruling(self, key):
        v = self.rulings.get(key)                     # "yes" / "no" / "unknown", or {"value", "reason"}
        return v.get("value") if isinstance(v, dict) else v

    def reason(self, key):
        v = self.rulings.get(key)
        return (v.get("reason") or "") if isinstance(v, dict) else ""


def _conv(v):
    if isinstance(v, str) and ISO.match(v):
        return date.fromisoformat(v)
    return v


def apply_data(case, answers):
    """A copy of the case with the data answers in it ("unknown" answers leave the fact absent)."""
    c = copy.deepcopy(case)
    extra = getattr(c, "extra", None)
    if extra is None:
        c.extra = extra = {}
    for key, raw in answers.data.items():
        v = answers.value(key)
        if v is None or v == "unknown":
            continue
        v = _conv(v)
        m = re.match(r"^hold:([A-Z_]+)>([A-Z_]+)\.(\w+)$", key)
        if m:
            a, b, attr = m.groups()
            h = c.holds.get((a, b)) or HoldEdge(a, b, None)
            c.holds[(a, b)] = HoldEdge(a, b, float(v) if attr == "ratio" else h.ratio,
                                       v if attr == "since" else h.since, float(v) if attr == "cost" else h.cost)
            continue
        m = re.match(r"^flow:(.+)\.(\w+)$", key)
        if m:
            fid, attr = m.groups()
            c.flows.setdefault(flow_name(fid), {})[attr] = v
            continue
        m = re.match(r"^group\.(\w+)$", key)
        if m:
            for rf in c.roles.values():
                rf.attrs[m.group(1)] = v
            continue
        m = re.match(r"^([A-Z_]+)\.(\w+)$", key)
        if m:
            role, attr = m.groups()
            if role in c.roles:
                c.roles[role].attrs[attr] = v
            else:
                extra.setdefault(role, {})[attr] = v
    return c


# ---------------------------------------------------------------- structures
@dataclass
class Question:
    key: str
    kind: str                     # blocking | data | action | ruling | library
    region: frozenset
    prompt: str
    value: str = ""
    source_hint: str = ""
    why: List[str] = field(default_factory=list)
    impact: Optional[float] = None
    forms: List[str] = field(default_factory=list)


@dataclass
class Evaluation:
    cand: dict
    graph: object
    b: object
    ticks: dict
    plan_keys: Dict[str, tuple]            # absolute PLAN key -> (group, need)
    blocking: Dict[str, tuple]             # absolute DATA key -> group
    excluded: str = ""                     # why this candidate cannot be planned (a blocking datum answered unknown)
    out_of_scope: list = field(default_factory=list)   # decision D52: the levies beyond income tax this structure attracts

    @property
    def n_discretion(self):
        return sum(1 for ns in self.b.groups.values() for n in ns if n.source == DISCRETION)


@dataclass
class Outcome:
    questions: List[Question]
    plan: Optional[dict]
    evaluations: List[Evaluation]
    note: str = ""
    scope: dict = field(default_factory=dict)          # decision D52: {policy, excluded: [{cand, why: [scope.Outside.json]}]}


# ---------------------------------------------------------------- helpers
def _flow_of_group(grp, ev_graph, b):
    for labels in ((b.L_lo, b.L_hi) if b is not None else ()):
        lb = labels.get(grp[1]) if isinstance(grp[1], str) else None
        if lb is not None:
            return lb.flow
    fid = grp[1] if isinstance(grp[1], str) else None
    return next((f for f in ev_graph.flows if fid in (f.id, flow_name(f.id)) or (fid and flow_name(fid) == f.id)), None)


def _abs(n, grp, graph, b):
    if n.source == DATA or grp[0] == PEM_RULE or str(grp[0]).startswith("data."):
        return n.key
    f = _flow_of_group(grp, graph, b)
    return absolute_key(n.key, f) if f is not None else n.key


def _field_of(key):
    """'OP.after_tax_profit' / 'flow:up1@2027.holding_months:ge' / 'hold:ULT>OP.ratio' -> the field name."""
    k = key.split(":", 1)[1] if key.startswith(("flow:", "hold:")) else key
    k = k.rsplit(".", 1)[-1] if "." in k else k
    return k.split(":")[0]


def _pred_of(key):
    last = key.rsplit(":", 1)
    return last[1] if len(last) == 2 and "." not in last[1] and not key.startswith("calendar") else ""


def _region_of_group(grp, graph):
    r = RULES_BY_ID.get(grp[0])
    if r is not None:
        return rule_region(r)
    if grp[0] in SHARED_GROUPS:                         # a decision several rules share (decision D23)
        return frozenset({SHARED_GROUPS[grp[0]]})
    if grp[0] == PEM_RULE:
        e = graph.entities.get(grp[1])
        return frozenset({"CN"} | ({e.loc} if e is not None and e.loc else set()))
    if str(grp[0]).startswith("data."):
        if grp[0] == "data.holding":
            a, b = grp[1].split(">")
            return frozenset(x.loc for x in (graph.entities.get(a), graph.entities.get(b)) if x is not None and x.loc)
        if grp[0] == "data.cfc_profit":
            e = graph.entities.get(grp[1])
            return frozenset({"CN"} | ({e.loc} if e is not None and e.loc else set()))
        if grp[1] in JURISDICTIONS:                     # a jurisdiction's own fact or action (Pillar Two, decision D14)
            return frozenset({grp[1]})
        e = graph.entities.get(grp[1])
        if e is not None and e.loc:
            return frozenset({e.loc})
        return frozenset(j for j in (x.loc for x in graph.entities.values()) if j)
    if grp[0] in ("cn.liquidation.split", "cn.capital_reduction.split"):
        return frozenset({"CN"})
    return frozenset()


def _polarity(rule, key):
    """True when the Discretion leaf `key` sits under an even number of negations (its True supports the rule)."""
    def walk(c, neg):
        if isinstance(c, Discretion):
            return [neg] if c.key == key else []
        if isinstance(c, Not):
            return walk(c.x, not neg)
        if isinstance(c, (And, Or)):
            return [x for y in c.xs for x in walk(y, neg)]
        return []
    hits = walk(rule.cond, False) if rule.cond is not None else []
    return (not hits[0]) if hits else True


def _fav_value(key):
    """The tick that gives the taxpayer the favourable reading of a judgement: a favourable rule wants it true, an
    unfavourable one (a denial, a charge) wants it false; None when no rule reads it."""
    field_ = key.split(".", 1)[1] if "." in key else key
    if field_ in ("effective_management_in_cn", "cn_main_controlling_investor"):
        return False                                    # not a Mainland resident by management
    for r in RULES_BY_ID.values():
        if r.cond is None:
            continue
        if any(isinstance(x, Discretion) and x.key == field_ for x in leaves(r.cond)):
            return bool(r.favourable) == _polarity(r, field_)
    return None


def _ruling_ticks(answers):
    """Rulings answered "yes" become ticks on the favourable side; "no" and "unknown" leave the judgement open."""
    out = {}
    for key in answers.rulings:
        if answers.ruling(key) != "yes":
            continue
        val = _fav_value(key)
        if val is not None:
            out[Need(DISCRETION, key)] = val
    return out


STRATEGY_MAX_KEYS = 6                                     # beyond this, only the baseline, each single ruling and all of them


def _strategies(template, event, case, answers, P, evals, g0, scope):
    """The rulings the client answered "unknown" fork the plan. Each combination of them taken favourable is a strategy:
    the structure it leads to and its guaranteed tax, sorted by that tax; the last row (the baseline) takes every open
    ruling against the taxpayer; each row names the strategy to fall back on when one of its rulings fails. The labels are
    branch labels, not assumptions of the plan; a ruling resolved in practice is answered yes / no and the tree shrinks."""
    live = [e for e in evals if not e.blocking and not e.excluded]
    open_keys = sorted({_abs(n, grp, e.graph, e.b) for e in live for grp, ns in e.b.groups.items() for n in ns if n.source == DISCRETION}
                       & {k for k in answers.rulings if answers.ruling(k) == "unknown"})
    if not open_keys or not live:
        return []
    from itertools import combinations
    if len(open_keys) <= STRATEGY_MAX_KEYS:
        subsets = [set(c) for r in range(len(open_keys) + 1) for c in combinations(open_keys, r)]
    else:
        subsets = [set()] + [{k} for k in open_keys] + [set(open_keys)]
    rows = {}
    for s in subsets:
        a2 = Answers(answers.data, answers.actions, dict(answers.rulings), answers.library)
        for k in s:
            a2.rulings[k] = "yes"
        if not s:
            found = list(live)                               # the baseline: the evaluations the plan already has
        else:
            found = []
            for e in live:                                   # only structures that can be chosen at all
                ev = evaluate(template, event, case, e.cand, a2, P, g0, scope=scope)
                if ev is not None and not ev.blocking and not ev.excluded:
                    found.append(ev)
        if not found:
            continue
        b2 = min(found, key=_key)
        key = (json.dumps(b2.cand, sort_keys=True, default=str), round(b2.b.hi, 2))
        if key not in rows or len(s) < len(rows[key]["assumes_favourable"]):
            rows[key] = {"assumes_favourable": sorted(s), "cand": dict(b2.cand), "guaranteed": round(b2.b.hi, 2), "best": round(b2.b.lo, 2),
                         "_best": b2, "_evals": found, "_answers": a2}
    out = sorted(rows.values(), key=lambda r: (r["guaranteed"], len(r["assumes_favourable"])))
    for i, r in enumerate(out, 1):
        r["id"] = i
        r["baseline"] = not r["assumes_favourable"]
        r["labels"] = {k: _gloss(_field_of(k)).get("gloss", _field_of(k)) for k in r["assumes_favourable"]}
        r["reasons"] = {k: answers.reason(k) for k in r["assumes_favourable"] if answers.reason(k)}
    for r in out:
        mine = set(r["assumes_favourable"])
        below = [x for x in out if x is not r and set(x["assumes_favourable"]) < mine]
        r["fallback"] = min(below, key=lambda x: x["guaranteed"])["id"] if below else None
    return out


def _ctx_of(ticks):
    return lambda facts: CaseCtx(facts, ticks, EX_ANTE, ADJUSTABLE)


def _plan_value(key, ticks):
    """The value the plan gives an action: decided by an action already taken on the same field (the opposite
    predicate), else the side that favours the taxpayer; None when only computing both can tell."""
    head, _, pred = key.rpartition(":")
    opp = OPPOSITE.get(pred)
    if opp and Need(PLAN, head + ":" + opp) in ticks:
        return not ticks[Need(PLAN, head + ":" + opp)]
    return plan_favourable(_field_of(key), pred)


def evaluate(template, event, case, a, answers, P, g0=None, scope=None):
    g = template.build(event, a, case)
    validate_core(g)
    if g0 is not None and not same_settled(g, g0, case.settled):
        return None
    if scope_mod.active(scope):                             # decision D52: a structure that attracts another levy is not compared
        bad = scope_mod.outside(g)
        if bad:
            ev = Evaluation(a, g, Bounds(float("-inf"), float("inf"), {}, {}, {}, {}), {}, {}, {})
            ev.prereq, ev.joint = {}, {}
            ev.excluded = scope_mod.reason(bad, case.names)
            ev.out_of_scope = bad
            return ev
    ticks = dict(_ruling_ticks(answers))
    for key, v in answers.actions.items():                  # "yes": the plan can take the favourable side
        fav = _plan_value(key, ticks)
        fav = True if fav is None else fav
        ticks[Need(PLAN, key)] = fav if v == "yes" else (not fav)
    plan_keys, undecided = {}, []
    b, joint = None, None
    for _ in range(5):
        try:
            b = bounds(g, _ctx_of(ticks), P, settled=case.settled, as_at=event.as_at, closed=case.closed, ticks=ticks)
        except Undecidable as u:                            # the plan's own actions first: they may close enough
            new = {}
            for grp, ns in u.groups.items():
                for n in ns:
                    if n.source == PLAN and Need(PLAN, _abs(n, grp, g, None)) not in ticks:
                        new[_abs(n, grp, g, None)] = (grp, n)
            for ak, gn in new.items():
                v = _plan_value(ak, ticks)
                if v is None:
                    undecided.append(ak)
                ticks[Need(PLAN, ak)] = True if v is None else v
                plan_keys[ak] = gn
            if new:
                continue
            joint = u
            break
        new = {}
        for grp, ns in b.groups.items():
            for n in ns:
                if n.source == PLAN:
                    ak = _abs(n, grp, g, b)
                    if Need(PLAN, ak) not in ticks:
                        new[ak] = (grp, n)
        if not new:
            break
        for ak, gn in new.items():                          # the plan's own action, pending confirmation
            v = _plan_value(ak, ticks)
            if v is None:
                undecided.append(ak)
            ticks[Need(PLAN, ak)] = True if v is None else v
            plan_keys[ak] = gn
    if joint is None:                                       # actions whose side only the numbers decide: the lower
        for ak in undecided:                                # guaranteed tax
            if answers.answered(ak):
                continue
            t2 = dict(ticks)
            t2[Need(PLAN, ak)] = not ticks[Need(PLAN, ak)]
            try:
                b2 = bounds(g, _ctx_of(t2), P, settled=case.settled, as_at=event.as_at, closed=case.closed, ticks=t2)
            except Undecidable:
                continue
            if b2.hi < b.hi - EPS:
                ticks, b = t2, b2
    if joint is not None:                                   # ask what closes the interacting decisions
        b = Bounds(float("-inf"), float("inf"), dict(joint.groups), {}, {}, {})
        blocking, kinds = {}, {}
        for grp, ns in joint.groups.items():
            for n in ns:
                if n.source in (MISSING, DISCRETION, DATA):
                    k = _abs(n, grp, g, None)
                    blocking[k] = grp
                    kinds[k] = "ruling" if n.source == DISCRETION else "joint"
        ev = Evaluation(a, g, b, ticks, plan_keys, blocking)
        ev.prereq, ev.joint = {}, kinds
        if all(answers.answered(k) for k in blocking):
            ev.excluded = "cannot be computed exactly: %d interacting open items remain open after the answers (%s)" % (len(blocking), ", ".join(sorted(blocking)[:6]))
        return ev
    blocking, prereq = {}, {}
    for grp, ns in b.groups.items():
        for n in ns:
            if n.source == DATA:
                blocking[n.key] = grp
                prereq[n.key] = [m.key for m in ns if m.source == MISSING]   # questions that decide whether it applies
    ev = Evaluation(a, g, b, ticks, plan_keys, blocking)
    ev.prereq = prereq
    unknown = [k for k in blocking if answers.data.get(k) == "unknown"]
    if unknown:
        ev.excluded = "unbounded without %s (answered unknown)" % ", ".join(sorted(unknown))
    steps = outside_steps(b, g)[0]                          # decision D30: a group-borne levy the library cannot compute there
    if steps:
        g.unmodelled = tuple(g.unmodelled) + tuple(x for x in steps if x not in g.unmodelled)
    if g.unmodelled:                                        # decision D19: the step's tax is not computed: no plan
        ev.excluded = "a step the structure needs is not modelled by this program (%s); its tax is unknown" % "; ".join(_step_text(x) for x in g.unmodelled)
    return ev


def _key(ev):
    return (ev.b.hi, ev.b.lo, ev.n_discretion, len(ev.graph.entities))


def _forced_hi(ev, groups, case, event, P):
    force = {g: "fav" for g in groups}
    try:
        return bounds(ev.graph, _ctx_of(ev.ticks), P, settled=case.settled, as_at=event.as_at, closed=case.closed,
                      ticks=ev.ticks, force=force).hi
    except Defect:
        return None


def _with_tick(ev, need, value, case, event, P):
    t = dict(ev.ticks)
    t[need] = value
    return bounds(ev.graph, _ctx_of(t), P, settled=case.settled, as_at=event.as_at, closed=case.closed, ticks=t).hi


PAIR_MAX = 60                                       # item pairs tried on the chosen structure, per round


def _joint_pairs(ev, case, event, P, answers):
    """Pairs of open data / rulings on the chosen structure that lower its guaranteed tax only together: each worth
    nothing alone (forcing its groups favourable leaves the guaranteed tax), both touching the same flow or company,
    forced favourable together. -> [(key_a, key_b, impact, groups_a, groups_b, source_a, source_b)]"""
    from itertools import combinations
    by_key = {}
    for grp, ns in ev.b.groups.items():
        for n in ns:
            if n.source in (MISSING, DISCRETION):
                k = _abs(n, grp, ev.graph, ev.b)
                if not answers.answered(k):
                    by_key.setdefault(k, (n.source, set()))[1].add(grp)
    zero = []
    for k, (src, grps) in by_key.items():
        hi = _forced_hi(ev, grps, case, event, P)
        if hi is not None and hi >= ev.b.hi - EPS:
            zero.append(k)

    def touch(k):
        out = {("flow", str(g[1]).split(".")[0]) for g in by_key[k][1]}
        head = k.split(":", 1)[1] if k.startswith(("flow:", "hold:")) else k
        out.add(("company", head.split(".")[0]))
        return out
    found = []
    for a, b in [(a, b) for a, b in combinations(sorted(zero), 2) if touch(a) & touch(b)][:PAIR_MAX]:
        hi = _forced_hi(ev, by_key[a][1] | by_key[b][1], case, event, P)
        if hi is not None and hi < ev.b.hi - EPS:
            found.append((a, b, round(ev.b.hi - hi, 2), by_key[a][1], by_key[b][1], by_key[a][0], by_key[b][0]))
    return found


# the amounts of the steps a structure itself needs (decision D18, D19): asked by name, never filled
STEP_AMOUNT = {"reorg": ("consideration for the reorganisation step: the price at which ULT transfers its OP shares to the new holding company (market value on the transfer date)", "amount", "valuation report or share transfer agreement"),
               "unwind": ("market value, on the transfer-out date, of the OP shares the existing HOLD holds (transferred at this value to ULT or the new company when HOLD is dissolved or migrated)", "amount", "valuation report"),
               "wind": ("all residual assets distributed to the shareholder ULT on the liquidation of the existing HOLD (including the OP shares or their sale proceeds, after taxes and liabilities)", "amount", "liquidation plan and balance sheet"),
               "iptx": ("IP transfer price: the price at which the company now holding the IP transfers its ownership to the new holder (market value on the transfer date)", "amount", "valuation report or IP transfer agreement")}


def _question_for(key, kind, region, why, impact=None, extra="", with_=None):
    f = _field_of(key)
    gl = _gloss(f)
    m = re.match(r"^flow:(.+)\.amount$", key)
    if m and flow_name(m.group(1)) in STEP_AMOUNT:
        g_, v_, h_ = STEP_AMOUNT[flow_name(m.group(1))]
        gl = {"gloss": g_, "value": v_, "source_hint": h_}
    target = key.split(":")[0] if key.startswith(("flow:", "hold:", "calendar:")) else key.split(".")[0]
    if kind == "action":
        prompt = "Can this be done: %s (%s)" % (gl.get("gloss", f), extra or key)
    elif kind == "ruling":
        prompt = "Has a written ruling or confirmation from the tax authority been obtained on: %s (%s)" % (gl.get("gloss", f), key)
    elif kind == "library":
        prompt = extra
    else:
        prompt = "Please provide: %s (%s)" % (gl.get("gloss", f), key)
    if with_:
        prompt += " — matters only together with `%s`" % with_
    forms = [x for x in FORMS.get(f, []) if not region or x.split(".", 1)[0].upper() in region]   # the region's own forms
    return Question(key, kind, region, prompt, gl.get("value", ""), gl.get("source_hint", ""), sorted(why), impact, forms[:3])


def _published(gap, today):
    jur, year = gap
    if jur == "CN":
        return today >= date(year - 1, 12, 1)        # the State Council notice comes out late in the year before
    return today >= date(year - 1, 7, 1)              # MOM publishes the coming year's holidays around mid-year


# ---------------------------------------------------------------- the plan
def plan(template, event, case, answers=None, P=None, today=None, scope=None) -> Outcome:
    """scope: None = the product's policy (scope.POLICY, income tax only); scope.ALL = the whole library (harnesses)."""
    answers = answers or Answers()
    P = P or Params()
    today = today or date.today()
    case = apply_data(case, answers)
    g0 = template.build(event, case.present, case) if case.settled else None
    evals = []
    for a in template.candidates(event, case):
        ev = evaluate(template, event, case, a, answers, P, g0, scope=scope)
        if ev is not None:
            evals.append(ev)
    if not evals:
        return Outcome([], None, [], "No candidate structure keeps the flows whose tax has been settled.")
    scope_info = {"policy": scope or scope_mod.POLICY,
                  "excluded": [{"cand": dict(e.cand), "why": [x.json(case.names) for x in e.out_of_scope]} for e in evals if e.out_of_scope]}
    plannable = [e for e in evals if not e.blocking and not e.excluded]
    best = min(plannable, key=_key) if plannable else None
    contention = sorted([e for e in evals if not e.excluded and (best is None or e is best or e.b.lo < best.b.hi - EPS)],
                        key=lambda e: e.b.lo)[:CONTENTION_MAX]
    qs: Dict[str, Question] = {}

    def add(q):
        cur = qs.get(q.key)
        if cur is None or (q.impact or 0) > (cur.impact or 0):
            qs[q.key] = q

    # 1. data without which a tax is unbounded
    for ev in contention:
        for key, grp in ev.blocking.items():
            pre = [k for k in getattr(ev, "prereq", {}).get(key, []) if not answers.answered(k)]
            for k in pre or ([key] if not answers.answered(key) else []):
                kind = getattr(ev, "joint", {}).get(k, "blocking") if getattr(ev, "joint", None) else "blocking"
                add(_question_for(k, kind, _region_of_group(grp, ev.graph), [grp[0]]))
    # 2. data and rulings that could lower the guaranteed tax or change the plan
    if best is not None:
        for ev in contention:
            by_key = {}
            for grp, ns in ev.b.groups.items():
                for n in ns:
                    if n.source in (MISSING, DISCRETION):
                        by_key.setdefault((n.source, _abs(n, grp, ev.graph, ev.b)), []).append(grp)
            for (src, key), grps in by_key.items():
                if answers.answered(key):
                    continue
                hi = _forced_hi(ev, grps, case, event, P)
                if hi is None or hi >= best.b.hi - EPS:
                    continue
                impact = round(best.b.hi - hi, 2)
                kind = "data" if src == MISSING else "ruling"
                why = sorted({"%s [%s]" % (g[0], region_name(_region_of_group(g, ev.graph))) for g in grps})
                add(_question_for(key, kind, frozenset().union(*(_region_of_group(g, ev.graph) for g in grps)), why, impact))
        # 2b. items that matter only together: on the chosen structure, a pair each worth nothing alone
        for a, b, impact, ga, gb, sa, sb in _joint_pairs(best, case, event, P, answers):
            for k, src, grps, other in ((a, sa, ga, b), (b, sb, gb, a)):
                why = sorted({"%s [%s]" % (g[0], region_name(_region_of_group(g, best.graph))) for g in grps})
                add(_question_for(k, "data" if src == MISSING else "ruling",
                                  frozenset().union(*(_region_of_group(g, best.graph) for g in grps)), why, impact, with_=other))
        # 3. the plan's own actions, if they matter
        for ak, (grp, n) in best.plan_keys.items():
            if answers.answered(ak) or Need(PLAN, ak) not in best.ticks:
                continue
            v = best.ticks[Need(PLAN, ak)]
            hi = _with_tick(best, Need(PLAN, ak), not v, case, event, P)
            if hi > best.b.hi + EPS:
                add(_question_for(ak, "action", _region_of_group(grp, best.graph), [grp[0]], round(hi - best.b.hi, 2),
                                  _action_text(ak, grp, P, v)))
        # 4. library material the deadlines need
        for labels in (best.b.L_hi,):
            for lb in labels.values():
                for name_, gap in (lb.gaps or {}).items():
                    k = "calendar:%s:%d" % gap
                    if _published(gap, today) and not answers.answered(k):
                        add(_question_for(k, "library", frozenset({gap[0]}), [name_], None,
                                          "The library lacks the %s public holiday table for %d (officially published); the deadline extension needs it: please provide the officially published holiday list" % gap))
    questions = sorted(qs.values(), key=lambda q: (order_key(q.region), ["blocking", "joint", "data", "action", "ruling", "library"].index(q.kind),
                                                   -(q.impact or 0), q.key))
    if questions:
        return Outcome(questions, None, evals, scope=scope_info)
    if best is None:
        why = "; ".join(sorted({e.excluded for e in evals if e.excluded})) or "every candidate needs data that leaves a tax unbounded"
        return Outcome([], None, evals, "No plan can be given: " + why, scope=scope_info)
    strategies = _strategies(template, event, case, answers, P, evals, g0, scope)
    head = build_plan(best, evals, case, event, answers, P, today, scope_info, strategies)
    if strategies:                                          # each strategy has its own plan and workpack; the head is the comparison only
        from .execution import for_strategy
        for s in strategies:
            tag = {"id": s["id"], "guaranteed": s["guaranteed"], "assumes_favourable": s["assumes_favourable"], "labels": s["labels"],
                   "fallback": s["fallback"], "fallback_guaranteed": next((x["guaranteed"] for x in strategies if x["id"] == s["fallback"]), None)}
            if s["baseline"]:                                 # the baseline is the head's own plan: not built twice
                s.pop("_best"), s.pop("_evals"), s.pop("_answers")
                sp = dict(head)
            else:
                sp = build_plan(s.pop("_best"), s.pop("_evals"), case, event, s.pop("_answers"), P, today, scope_info)
                sp["rulings_declared"] = head["rulings_declared"]   # declarations are the client's, not the branch labels
            for k in ("present", "ties", "runner_up", "unmodelled", "scope", "strategies"):   # comparison-only: on the head
                sp.pop(k, None)
            sp["execution"] = for_strategy(sp["execution"], tag)
            s["plan"] = sp
        head["execution"] = None                               # the strategies carry the workpacks
    return Outcome([], head, evals, scope=scope_info)


ENUM_TEXT = {"REMITTED": "remitted in", "DEBT_SETTLED": "applied to settle debts of the local business", "MOVABLE_PROPERTY": "brought in as movable property purchased",
             "PATENT": "patent", "KNOW_HOW": "know-how", "SOFTWARE_COPYRIGHT": "software copyright", "IC_LAYOUT": "integrated circuit layout design",
             "PLANT_VARIETY": "new plant variety", "BIOMEDICINE_VARIETY": "new biomedical variety", "capital_increase": "capital increase",
             "new_entity": "newly established enterprise", "unrelated_acquisition": "acquisition of equity from an unrelated party"}


def _action_text(ak, grp, P, value=True):
    """'flow:up1.holding_months:ge' on rule X -> 'flow:up1 holding months ≥ 12 months' with the threshold the rule reads; with
    value False the action is the opposite side ('< 12 months'; a yes/no field: no)."""
    f = _field_of(ak)
    pred = _pred_of(ak)
    if not value and pred in OPPOSITE:
        pred = OPPOSITE[pred]
    r = RULES_BY_ID.get(grp[0])
    thr = ""
    if r is not None and r.cond is not None:
        for x in leaves(r.cond):
            if isinstance(x, Leaf) and x.field == f and x.param:
                try:
                    v = P[x.param]
                    unit = P.rows[x.param].get("unit", "")
                    if pred == "is_in":                       # an enumerated field: the side the plan takes, in words
                        thr = ": %s %s" % ("one of" if value else "not one of", ", ".join(ENUM_TEXT.get(e, e) for e in str(v).split(";")))
                    else:
                        thr = " %s %s%s" % ({"ge": "≥", "gt": ">", "le": "≤", "lt": "<"}.get(pred, pred),
                                            ("%g" % v) if isinstance(v, float) else v, unit)
                except KeyError:
                    pass
                break
    target = ak.rsplit(".", 1)[0] if ak.startswith("flow:") else ak.split(".")[0]
    if f == "managed_from":
        return "%s · place of effective management (where the board and senior management take the business decisions) %s" % (target, "outside the Mainland" if value else "in the Mainland")
    if pred in ("is_true", "is_false"):
        thr = ": %s" % ("yes" if pred == "is_true" else "no")
    return "%s · %s%s" % (target, _gloss(f).get("gloss", f), thr)


def build_plan(best, evals, case, event, answers, P, today, scope_info=None, strategies=None):
    """The plan of one chosen evaluation. Called for the head (with the strategies list) and once per non-baseline
    strategy with that strategy's answers; the head carries the comparison keys, a strategy only its own plan."""
    g, b = best.graph, best.b
    regions = {}

    def bucket(rg):
        return regions.setdefault(rg or frozenset({"—"}), {"actions": [], "guaranteed": [], "best": [], "deadlines": [], "conditions": []})

    # structure
    structure = {"entities": [], "holds": [], "flows": []}
    for e in g.entities.values():
        if e.id not in g.group():
            status = "outside the group (location chosen by the plan)" if e.attrs.get("placed_by_plan") else "outside the group"
        elif e.attrs.get("wound_up_by_plan"):               # decision D19: the client's company leaves the chain
            status = "transfers its shares out, then liquidated and deregistered"
            took = next((f for f in g.flows if f.id == "unwind"), None)
            if took is not None:
                bucket(frozenset({e.loc})).get("actions").append(
                    ("%s (%s) transfers its %s shares at market value to %s, then is liquidated and deregistered with the residual assets distributed to its shareholder: both steps' taxes are counted (flows unwind, wind)"
                     % (e.id, e.loc, took.target, took.payer), "designed", None))
        else:
            status = "new" if e.attrs.get("created_by_plan") else ("migrated or rearranged" if e.attrs.get("placed_by_plan") else "existing")
            base = e.id[:-len(NEW)] if e.id.endswith(NEW) else None
            if base and base in case.roles and base not in g.entities:
                status = "new (takes over this business from the existing %s; the existing %s no longer provides it to OP)" % (base, base)
        structure["entities"].append((e.id, e.loc, status))
    for h in g.holds:
        how = "designed by the plan (wholly owned, new)" if h.designed else ("stated by the case" if (h.holder, h.held) in case.holds else "takes over the original holding")
        structure["holds"].append((h.holder, h.held, h.ratio, how))
        if h.designed:
            bucket(frozenset({g.entities[h.held].loc})).get("actions").append(
                ("Establish %s (%s), with %s holding %g%%; %s has only the flows this plan lists" % (h.held, g.entities[h.held].loc, h.holder, h.ratio, h.held),
                 "designed", None))
    for f in g.flows:
        structure["flows"].append((f.id, f.income, f.payer, f.payee, f.amount, f.on.isoformat() if f.on else ""))
    # actions the plan relies on (only those that change the guaranteed tax)
    for ak, (grp, n) in best.plan_keys.items():
        if Need(PLAN, ak) not in best.ticks:
            continue
        v = best.ticks[Need(PLAN, ak)]
        hi = _with_tick(best, Need(PLAN, ak), not v, case, event, P)
        if hi <= b.hi + EPS:
            continue
        status = "confirmed" if answers.actions.get(ak) == "yes" else "to be confirmed"
        bucket(_region_of_group(grp, g))["actions"].append((_action_text(ak, grp, P, v), status, round(hi - b.hi, 2)))
    # taxes, guaranteed and best case; items borne outside the group are shown but not counted
    members = g.group()
    for side, labels in (("guaranteed", b.L_hi), ("best", b.L_lo)):
        for fid, lb in labels.items():
            for it in lb.items:
                if not it.effective or it.deferred:
                    continue
                amt = round(lb.flow.amount * it.effective / 100.0, 2)
                rg = item_region(it, lb, RULES_BY_ID, g)
                who = lb.flow.payer if it.borne_by == "payer" else lb.flow.payee
                bucket(rg)[side].append((fid, it.jur, it.levy, who, amt, sorted(set(it.cites)), who in members))
    # deadlines
    for fid, lb in b.L_hi.items():
        for name_, d in (lb.deadlines or {}).items():
            jur = lb.deadline_jur.get(name_)
            gap = (lb.gaps or {}).get(name_)
            note = ""
            if gap:
                note = ("that year's holiday table is not yet officially published; nominal date, may be extended once published" if not _published(gap, today)
                        else "that year's holiday table is missing (requested from a person)")
            bucket(frozenset({jur}) if jur else frozenset())["deadlines"].append((fid, name_, d.isoformat() if d else "", note))
    # judgements the plan still depends on: what the authority would have to accept, and what it is worth
    seen = set()
    for grp, ns in b.groups.items():
        for n in ns:
            if n.source != DISCRETION:
                continue
            key = _abs(n, grp, g, b)
            if key in seen:
                continue
            seen.add(key)
            hi = _forced_hi(best, [x for x, y in b.groups.items() if any(_abs(m, x, g, b) == key for m in y)], case, event, P)
            upside = round(b.hi - hi, 2) if hi is not None else None
            gl = _gloss(_field_of(key)).get("gloss", _field_of(key))
            bucket(_region_of_group(grp, g))["conditions"].append((key, gl, grp[0], upside))
    present = next((e for e in evals if not e.out_of_scope and all(e.cand.get(k) == v for k, v in case.present.items())), None) if case.present else None
    others = sorted([e for e in evals if e is not best and not e.blocking and not e.excluded], key=_key)
    unmodelled = sorted([(e.cand, "; ".join(_step_text(x) for x in e.graph.unmodelled), e.b.hi, e.b.lo)
                         for e in evals if e.graph.unmodelled and not e.blocking and e.b.hi < b.hi - EPS], key=lambda x: x[2])
    ties = [e for e in others if e.b.hi <= b.hi + EPS]               # the same guaranteed tax: equal under the criterion
    runner = [e for e in others if e.b.hi > b.hi + EPS][:1]
    data_used = [(k, answers.value(k), (v.get("source") if isinstance(v, dict) else "")) for k, v in answers.data.items()]
    totals = {rg: (round(sum(x[4] for x in d["guaranteed"] if x[6]), 2), round(sum(x[4] for x in d["best"] if x[6]), 2))
              for rg, d in regions.items()}
    claims_ = []
    if case.settled:
        from .claims import claims as _claims
        cl, archived = _claims(b, case.settled, event.as_at, g)
        claims_ = [(c.flow, c.jur, c.actual, c.lo, c.hi, c.confirmed, c.potential, c.shortfall,
                    {k: (v.isoformat() if hasattr(v, "isoformat") else v) for k, v in c.deadlines.items()}, [r[0] for r in c.routes])
                   for c in cl] + [(f_, j_, None, None, None, None, None, None, {}, ["closed"]) for f_, j_ in archived]
    result = {"cand": best.cand, "guaranteed": b.hi, "best": b.lo, "structure": structure,
            "regions": dict(sorted(regions.items(), key=lambda kv: order_key(kv[0]))), "totals": totals,
            "present": (present.cand, present.b.hi, present.b.lo) if present else None,
            "runner_up": (runner[0].cand, runner[0].b.hi, runner[0].b.lo) if runner else None,
            "ties": [(e.cand, e.b.hi, e.b.lo) for e in ties],
            "data_used": data_used, "claims": claims_, "unmodelled": unmodelled, "scope": scope_info or {}, "strategies": strategies or [],
            "rulings_declared": {k: {"value": answers.ruling(k), "reason": answers.reason(k)} for k in answers.rulings if answers.ruling(k) in ("yes", "no")},
            "notes": (["A newly established company (if any) is taken, by the plan's design, to have only the flows listed; rerun if it is to have other business."]
                      if any(e.attrs.get("created_by_plan") for e in g.entities.values()) else [])
            + ["Flow %s (%s) predates the commencement of %s (%s): its %s is borne by %s outside the group; the library has no earlier rules, so it is not computed and does not affect the group's tax (decision D30)."
               % (x[1], x[2], x[3], x[4], x[5], x[6]) for x in outside_steps(b, g)[1]]}
    from .execution import build_execution, context_from_graph
    context = context_from_graph(case, event, g)
    context["template"] = "recorded" if case.transactions else "planning"
    result["execution"] = build_execution(result, context, len([e for e in evals if not e.blocking and not e.excluded and not e.graph.unmodelled]))
    return result


# ---------------------------------------------------------------- rendering
def answers_ruling(p, k):
    return p.get("rulings_declared", {}).get(k, {})


def scope_text(scope_info):
    """One line for the reports: the policy, and the candidate structures it left out (decision D52)."""
    s = scope_info or {}
    if s.get("policy") != scope_mod.INCOME_ONLY:
        return ""
    line = ("**Scope**: income tax only. VAT, GST, stamp duty, customs duty, land appreciation tax, deed tax and property tax are not "
            "assessed; a case or a structure that attracts one of them is not handled.")
    ex = s.get("excluded") or []
    if ex:
        line += " %d candidate structure%s not compared for that reason: %s." % (len(ex), "" if len(ex) == 1 else "s", scope_mod.compact([w for e in ex for w in e["why"]]))
    return line


def render(template, event, outcome, case_name=""):
    L = []
    w = L.append
    if outcome.questions:
        w("# Question sheet: %s (template %s)" % (case_name, template.name))
        w("")
        w("No plan can be given yet: the data or confirmations below would change the chosen plan or its guaranteed tax. Answer only these; where you cannot, enter unknown (taken at its worst, never filled in).")
        w("Write the answers into `<case>.answers.json`: data (a value or {\"value\", \"source\"}), actions (yes / no / unknown), rulings (yes / no / unknown), library.")
        if scope_text(outcome.scope):
            w("")
            w(scope_text(outcome.scope))
        cur = None
        for q in outcome.questions:
            if q.region != cur:
                cur = q.region
                w("")
                w("## %s" % region_name(q.region))
                w("")
                w("| Kind | Address | Question | Value | Usual source | Impact |")
                w("|---|---|---|---|---|---|")
            kind = {"blocking": "required (tax unbounded without it)", "joint": "required (too many interacting open items; cannot be computed exactly without it)", "data": "data",
                    "action": "action feasibility", "ruling": "ruling", "library": "library"}[q.kind]
            imp = "may lower the guaranteed tax by %.2f" % q.impact if q.impact else ({"blocking": "unbounded", "joint": "cannot be computed exactly"}.get(q.kind, "—"))
            hint = q.source_hint + ("; forms: " + "; ".join(q.forms) if q.forms else "")
            w("| %s | `%s` | %s | %s | %s | %s |" % (kind, q.key, q.prompt, q.value, hint, imp))
        w("")
        w("%d candidate structures; %d of them need the required data above before they can be computed." % (len(outcome.evaluations), sum(1 for e in outcome.evaluations if e.blocking)))
        return "\n".join(L) + "\n"
    if outcome.plan is None:
        w("# No plan: %s" % case_name)
        w("")
        w(outcome.note)
        return "\n".join(L) + "\n"
    p = outcome.plan
    w("# Plan: %s (template %s)" % (case_name, template.name))
    w("")
    w("**Structure**: %s" % (", ".join("%s=%s" % kv for kv in p["cand"].items()) or "the only structure"))
    if scope_text(p.get("scope")):
        w("")
        w(scope_text(p.get("scope")))
    declared = [(k, answers_ruling(p, k)) for k in sorted(p.get("rulings_declared", {}))]
    if declared:
        w("")
        w("**Rulings declared by the client** (not computed by the program; each with the basis given): " + "; ".join(
            "%s = %s (%s)" % (k, v["value"], v.get("reason") or "no basis given") for k, v in declared) + ".")
    if p.get("strategies"):
        w("")
        w("## Strategies")
        w("")
        w("The rulings answered \"unknown\" fork the plan. Sorted by guaranteed tax, lowest first; the last row (baseline) takes every open ruling against the taxpayer. "
          "A row's rulings are branch labels, not assumptions: resolve one in practice, answer yes / no, and reassess; if it fails, use the fallback row.")
        w("")
        w("| # | Guaranteed | Best case | Structure | Rulings taken as favourable on this path | Fallback |")
        w("|---|---|---|---|---|---|")
        for s in p["strategies"]:
            taken = "; ".join("%s (`%s`)%s" % (s["labels"].get(k, k), k, (" — client: " + s["reasons"][k]) if k in s.get("reasons", {}) else "")
                              for k in s["assumes_favourable"]) or "none (baseline)"
            w("| %d | %.2f | %.2f | %s | %s | %s |" % (s["id"], s["guaranteed"], s["best"], ", ".join("%s=%s" % kv for kv in s["cand"].items()) or "the only structure",
                                                  taken, ("#%d" % s["fallback"]) if s.get("fallback") else "—"))
        from .execution import render_execution
        for s in p["strategies"]:
            if s.get("plan"):
                w("")
                w("### Strategy #%d: guaranteed %.2f%s" % (s["id"], s["guaranteed"], " (baseline)" if s.get("baseline") else ""))
                w("")
                w(render_execution(s["plan"]["execution"]).replace("## Implementation plan", "#### Implementation plan", 1).replace("\n#### ", "\n###### ").replace("\n### ", "\n##### "))
    w("")
    w("**Guaranteed tax%s** (every discretion item unfavourable, unknown data unfavourable): %.2f; **best case** (every discretion item favourable): %.2f." % (
        " of the baseline" if p.get("strategies") else "", p["guaranteed"], p["best"]))
    if p["present"]:
        w("")
        w("**Present structure**: guaranteed %.2f / best %.2f." % (p["present"][1], p["present"][2]))
    if p.get("ties"):
        w("**Other structures with the same guaranteed tax** (this plan was chosen by best case, then fewer pending discretion items, then fewer companies; only data that do not affect the guaranteed tax could reorder them, and they are not asked): %s." % (
            "; ".join("%s (best %.2f)" % (c, lo) for c, hi, lo in p["ties"])))
    if p["runner_up"]:
        w("**Runner-up**: %s, guaranteed %.2f / best %.2f." % (p["runner_up"][0], p["runner_up"][1], p["runner_up"][2]))
    if p.get("unmodelled"):
        w("")
        w("**Structures not taken as the plan** (they need a step this program has not modelled; the figures below exclude that step's tax; they could be better only if that step's tax is below the difference): %s." % "; ".join(
            "%s: %s, guaranteed %.2f / best %.2f without that step, %.2f below this plan" % (c, why, hi, lo, p["guaranteed"] - hi)
            for c, why, hi, lo in p["unmodelled"]))
    if p.get("execution"):
        from .execution import render_execution
        w("")
        w(render_execution(p["execution"]))
    w("")
    w("## Summary by region")
    w("")
    w("| Region | Guaranteed tax | Best case | Actions | Deadlines | Conditions pending the authority's acceptance |")
    w("|---|---|---|---|---|---|")
    for rg, d in p["regions"].items():
        tg, tb = p["totals"].get(rg, (0, 0))
        w("| %s | %.2f | %.2f | %d | %d | %d |" % (region_name(rg), tg, tb, len(d["actions"]), len(d["deadlines"]), len(d["conditions"])))
    for rg, d in p["regions"].items():
        w("")
        w("## %s" % region_name(rg))
        if d["actions"]:
            w("")
            w("Actions:")
            for text, status, worth in d["actions"]:
                w("- %s (%s%s)" % (text, status, "; the guaranteed tax rises by %.2f if not done" % worth if worth else ""))
        if d["guaranteed"]:
            w("")
            w("Tax items (guaranteed):")
            for fid, jur, levy, who, amt, cites, mine in d["guaranteed"]:
                w("- %s · %s · %s · borne by %s%s · %.2f · %s" % (fid, jur, levy, who, "" if mine else " (outside the group, not counted)", amt, ", ".join(cites)))
        if d["deadlines"]:
            w("")
            w("Deadlines:")
            for fid, name_, dd, note in d["deadlines"]:
                w("- %s · %s · %s%s" % (fid, name_, dd, " (%s)" % note if note else ""))
        if d["conditions"]:
            w("")
            w("Conditions still depending on the tax authority's acceptance:")
            for key, gl, rule, upside in d["conditions"]:
                w("- %s (%s, rule %s)%s" % (gl, key, rule, ": if accepted, the tax falls by up to %.2f" % upside if upside else ""))
    if p.get("claims"):
        w("")
        w("## Settled tax: recoverable and shortfall risk")
        for fl, jur, actual, lo, hi, conf, pot, short, clocks, routes in p["claims"]:
            if actual is None:
                w("- %s / %s: closed (every clock has run out, or declared); no claim" % (fl, jur))
                continue
            w("- %s / %s: paid %.2f; per the rules [%.2f, %.2f]; confirmed recoverable %.2f, at most recoverable %.2f; shortfall risk [%.2f, %.2f]; clocks %s; routes %s" % (
                fl, jur, actual, lo, hi, conf, pot, short[0], short[1], clocks, " → ".join(routes)))
    w("")
    w("## Structure details")
    for e in p["structure"]["entities"]:
        w("- company %s · %s · %s" % e)
    for h in p["structure"]["holds"]:
        w("- holding %s → %s · %g%% · %s" % h)
    for f in p["structure"]["flows"]:
        w("- flow %s · %s · %s → %s · %.2f · %s" % f)
    if p["data_used"]:
        w("")
        w("## Answers used")
        for k, v, src in p["data_used"]:
            w("- %s = %s%s" % (k, v, " (%s)" % src if src else ""))
    if p["notes"]:
        w("")
        w("## Design premises of the plan")
        for n in p["notes"]:
            w("- " + n)
    return "\n".join(L) + "\n"
