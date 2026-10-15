"""facts_for(graph, flow): the (element, field) -> value dictionary one flow's rules read.

Stated facts come from Entity.attrs and FlowEdge.attrs; derived facts come from the graph itself (holding ratios,
holding periods, residence in the source jurisdiction, what a transferred target holds). Absent = unknown = U.
"""
from datetime import date

from .model import GOODS, IP_TRANSFER, PROPERTY, RENT, ROYALTY, SHARE_TRANSFER, CN, HK, SG, Graph, FlowEdge, months, treaty
from .params import Params
from .rules.procedure_common import add_months

_P = []


def params():
    if not _P:
        _P.append(Params())
    return _P[0]


def regime_facts(facts, income, on, accrued, P):
    """The facts a regime's commencement gives a flow by its dates (no date: the rules in force today, as valid_on).
    Hong Kong Sch 55 s2(1): the FSIE regime applies to income "accrued and received on or after" its commencement — the
    flow's date is the receipt; a dividend accrued earlier (declared in 2022, received in 2023) stays outside (口径 D34).
    Singapore s10L(3): s10L reaches a sale or disposal on or after its commencement only; the time of disposal is when
    the asset vests in the buyer (s10L(4)) — the flow's date (口径 D36)."""
    start = P.rows.get("hk.fsie.commencement", {}).get("effective_from")
    if start:
        facts.setdefault(("flow", "accrued_in_fsie_regime"), accrued is None or accrued >= date.fromisoformat(start))
    s10l = P.rows.get("sg.s10l.commencement", {}).get("value")
    if s10l and income == SHARE_TRANSFER:
        facts.setdefault(("flow", "disposed_in_s10l_regime"), on is None or on >= date.fromisoformat(s10l))


def hk_months(facts):
    """口径 D44. The months Hong Kong's participation test counts: the flow's own holding period, unless an intra-group
    transfer's relief gives the seller's (engine.after_intragroup, which overrides it); unknown as that one is."""
    if facts.get(("flow", "holding_months")) is not None:
        facts.setdefault(("flow", "hk_holding_months"), facts[("flow", "holding_months")])
    elif ("flow", "hk_holding_months") not in facts:
        facts[("_needs", "flow.hk_holding_months")] = facts.get(("_needs", "flow.holding_months")) or ("flow.holding_months",)


def onpay_ratio(graph: Graph, f: FlowEdge, window_months):
    """cn.sta.2018-09 #i2(一): share of the income the recipient pays on, within the window after receipt, to
    residents of a third jurisdiction (neither the source state nor the recipient's own), as the flow graph shows it."""
    src, own = source_of(graph, f), graph.entities[f.payee].loc
    paid = 0.0
    for g in graph.flows:
        if g.payer != f.payee or g.income in (SHARE_TRANSFER, IP_TRANSFER):       # a purchase price is not income passed on
            continue
        gap = months(f.on, g.on)
        if gap is None or gap < 0 or gap > window_months or g.on < f.on:
            continue
        if graph.entities[g.payee].loc in (src, own):
            continue
        paid += g.amount
    return round(100.0 * paid / f.amount, 6) if f.amount else 0.0


def own_later(graph: Graph, f: FlowEdge, within_months):
    """The structure's own share transfers in the window after f (口径 D19): what they break is a fact, not a plan item."""
    end = add_months(f.on, within_months)
    return [g for g in graph.flows if g.income == SHARE_TRANSFER and g.id != f.id and g.target and f.on <= g.on <= end]


def leaves(graph: Graph, g: FlowEdge, y):
    """g takes y out of the group: y itself, or a company above it, sold to a buyer outside the group."""
    return g.payer not in graph.group() and (g.target == y or graph.chain_ratio(g.target, y) > 0)


# the window after an intragroup transfer within which the transferee's leaving the group undoes the relief, by the
# regime that gives it: stamp duty where the target is (HK SDO s45(5A); SG 2014 Rules r 7(1)), else Hong Kong's FSIE
# intragroup relief of the seller (s15OB)
CLAWBACK_YEARS = {HK: "hk.stamp.clawback_years", SG: "sg.stamp.clawback_years"}
HEADLINE = {CN: "cn.eit.rate", HK: "hk.profits.rate_corp", SG: "sg.corp.rate"}      # each jurisdiction's statutory rate
FIXED = "_fixed"            # (FIXED, "flow.field"): a plan-controlled field the structure's own flows fix — a fact


def fix(facts, field, value):
    facts[("flow", field)] = value
    facts[(FIXED, "flow." + field)] = True


def tax_year(f: FlowEdge, jur):
    """口径 D50. The tax year a flow's income falls in for jur. The Mainland recognises a dividend on the date the investee
    decides the distribution (实施条例 第十七条; 国税函〔2010〕79号 第四条: or the capitalisation), so a dividend declared in one
    year and paid in another is the declaring year's, its credits with it (操作指南 示例十一; declared_on). Every other
    flow, and the other jurisdictions (Hong Kong and Singapore charge foreign income in the year it is received): the
    flow's own date."""
    d = f.attrs.get("declared_on") if jur == CN and f.income == "DIVIDEND" else None
    return (d or f.on).year


def source_of(graph: Graph, f: FlowEdge):
    """Where the income arises: the investee for a share transfer (cn.reg.eit#7), otherwise the payer."""
    if f.income == SHARE_TRANSFER and f.target:
        return graph.entities[f.target].loc
    if f.income in (PROPERTY, RENT) and f.attrs.get("property_loc"):   # 口径 D48, D49: where the property lies
        return f.attrs["property_loc"]
    return graph.entities[f.payer].loc


# 口径 D40: whether a flow's two parties are related is each jurisdiction's own test — the Mainland's shares (公告2016年
# 第42号 第二条第（一）项), Hong Kong's control (Cap 112 s50AAG, s50AAH), Singapore's control (ITA s2 "related party",
# which does not define control: only whole ownership settles it from the graph). Holdings below a test leave that
# law's other ties open (loans, licences, control of dealings or of the board, common interests): unknown — the case
# says (parties_related, which then speaks for all three). Parties with no holding between them are not related unless
# the case says so.
RELATED = {CN: "cn_related", HK: "hk_associated", SG: "sg_related"}


def linked(graph: Graph, a, b):
    """A holding between a and b either way, or a holder of both."""
    return graph.chain_ratio(a, b) > 0 or graph.chain_ratio(b, a) > 0 or any(
        graph.chain_ratio(e, a) > 0 and graph.chain_ratio(e, b) > 0 for e in graph.entities if e not in (a, b))


def cn_holding(graph: Graph, a, b, lim, seen=()):
    """公告2016年第42号 第二条第（一）项: a's holding in b, in percent — directly; through an intermediate a holds at least
    the threshold of, at the intermediate's own holding in b; through one held below it, the ratios multiplied; the
    chains added up."""
    if a == b:
        return 100.0
    total = 0.0
    for h in graph.holds:
        if h.holder != a or h.held in seen:
            continue
        if h.held == b:
            total += h.ratio
            continue
        sub = cn_holding(graph, h.held, b, lim, seen + (a,))
        total += sub if h.ratio >= lim else h.ratio / 100.0 * sub
    return total


def beneficial(graph: Graph, a, b, seen=(), via=None):
    """Cap 112 s50AAH(3), (4): a's direct or indirect beneficial interest in b — multiplied down a chain, chains added.
    via: which interposed entities a chain may pass through (s13W(1D): companies only)."""
    if a == b:
        return 100.0
    return sum(h.ratio / 100.0 * beneficial(graph, h.held, b, seen + (a,), via)
               for h in graph.holds if h.holder == a and h.held not in seen
               and (h.held == b or via is None or via(graph.entities[h.held])))


def hk_associated(graph: Graph, a, b, P):
    """口径 D44. Cap 112 s15OC: associated — at least 75% of the beneficial interest (multiplied through interposed
    entities, s15OC(4)) one in the other, or a third in both."""
    lim = P["hk.fsie.intragroup_assoc_ratio_min"]
    assoc = lambda x, y: beneficial(graph, x, y) >= lim - 1e-9
    return assoc(a, b) or assoc(b, a) or any(assoc(e, a) and assoc(e, b) for e in graph.entities if e not in (a, b))


NOT_COMPANY = ("PARTNERSHIP", "LLP", "TRUST", "INDIVIDUAL", "GOVERNMENT")    # forms a group chain does not pass


def sg_same_group(graph: Graph, a, b, P):
    """口径 D45. ITA s13W(1C)(b), (1D): in the same group — one company holds more than half of the other's ordinary
    shares, or a common company more than half of both's, multiplied through companies only (Annex A2-1 Ex 3, 6)."""
    half = P["sg.s13w.group_more_than_half"]
    company = lambda e: e.type not in NOT_COMPANY
    grp = lambda x, y: beneficial(graph, x, y, via=company) > half
    return grp(a, b) or grp(b, a) or any(grp(c, a) and grp(c, b) for c in graph.entities if c not in (a, b)
                                         and company(graph.entities[c]))


def hk_controls(graph: Graph, a, b, lim, seen=()):
    """Cap 112 s50AAH(2)(a)(i), (ii): more than half of the beneficial interest in b, or of the votes in b — a's own and
    those of the companies a controls (a holding's votes taken as its ratio)."""
    if beneficial(graph, a, b) > lim:
        return True
    votes = sum(h.ratio for h in graph.holds if h.held == b and h.holder not in seen
                and (h.holder == a or hk_controls(graph, a, h.holder, lim, seen + (b,))))
    return votes > lim


def relatedness(graph: Graph, a, b, P):
    """口径 D40: {jurisdiction: True | False | None} for parties a and b, from the holdings."""
    if not linked(graph, a, b):
        return {CN: False, HK: False, SG: False}
    others = [e for e in graph.entities if e not in (a, b)]
    lim, half = P["cn.tp.related_share_min"], P["hk.tp.control_more_than_half"]
    sh = lambda x, y: cn_holding(graph, x, y, lim) >= lim
    ctl = lambda x, y: hk_controls(graph, x, y, half)
    whole = lambda x, y: beneficial(graph, x, y) >= 100.0 - 1e-9
    return {CN: (sh(a, b) or sh(b, a) or any(sh(e, a) and sh(e, b) for e in others)) or None,
            HK: (ctl(a, b) or ctl(b, a) or any(ctl(e, a) and ctl(e, b) for e in others)) or None,
            SG: (whole(a, b) or whole(b, a) or any(whole(e, a) and whole(e, b) for e in others)) or None}


def related_in(graph: Graph, f: FlowEdge, jur):
    """口径 D40: the flow's parties related under jur's test — the case's own statement first."""
    stated = f.attrs.get("parties_related")
    return bool(stated) if stated is not None else relatedness(graph, f.payer, f.payee, params())[jur]


def sg_group_facts(graph: Graph, f: FlowEdge, facts, accrued):
    """口径 D45. s13W(1B): the share of the target's ordinary shares the seller and the companies in its group held at the
    start of the 24 months before the disposal — group: one holds more than half of the other, or a third more than half
    of both, the holdings multiplied through levels ((1C)(b), (1D)); a holding that started later, or that its holder
    sells in the period (another flow), does not count. A holding with no start date leaves the share open: its date is
    asked when the dated ones fall short and all of them would reach the threshold."""
    P = params()
    seller, start = f.payee, add_months(accrued, -24) if accrued else None
    if start is None:
        return
    members = {seller} | {e for e in graph.entities if e != seller and sg_same_group(graph, e, seller, P)}
    sold = {g.payee for g in graph.flows if g.income == SHARE_TRANSFER and g.target == f.target and g.id != f.id
            and g.on is not None and start <= g.on < f.on}
    dated, open_ = 0.0, []
    for h in graph.holds:
        if h.held != f.target or h.holder not in members or (h.holder in sold and h.holder != seller):
            continue
        if h.since is None:
            open_.append(h)
        elif h.since <= start:
            dated += h.ratio
    lim = P["sg.s13w.ratio_min"]
    if dated >= lim or not open_ or dated + sum(h.ratio for h in open_) < lim:
        facts.setdefault(("flow", "sg_group_ratio"), dated)
    else:
        facts[("_needs", "flow.sg_group_ratio")] = tuple("hold:%s>%s.since" % (h.holder, h.held) for h in open_)


def goods_route(graph: Graph, f: FlowEdge):
    """口径 D43. (shipped_from, delivered_to) of a sale of goods. A manufacturer's goods leave from where it is (the
    template's OP makes them there); a resale's from where its purchase's left; a purchase a trader resells arrives where
    the resale delivers when the goods go straight there (routed_via_trader false), else at the trader — or at home, for a
    trader where the goods are, which exports them itself. delivered_to of
    a sale to the customer is the case's; None while unknown."""
    buy = next((g for g in graph.flows if g.id == f.attrs.get("purchase_flow")), None)
    resale = next((g for g in graph.flows if g.attrs.get("purchase_flow") == f.id), None)
    shipped = f.attrs.get("shipped_from") or (goods_route(graph, buy)[0] if buy is not None else graph.entities[f.payee].loc)
    delivered = f.attrs.get("delivered_to")
    if delivered is None and resale is not None:
        via, here = resale.attrs.get("routed_via_trader"), graph.entities[f.payer].loc
        if here == shipped:                      # a trader where the goods are buys them at home and exports them itself
            delivered = here
        else:
            delivered = here if via is True else (resale.attrs.get("delivered_to") if via is False else None)
    return shipped, delivered


def route_facts(graph: Graph, f: FlowEdge, facts):
    """口径 D43: whether the goods leave the Mainland, or enter the Mainland or Singapore, on this sale. Unknown delivery:
    what decides it is asked — the place of delivery, or for a purchase a trader resells, whether it routes the goods."""
    shipped, delivered = goods_route(graph, f)
    facts.setdefault(("flow", "shipped_from"), shipped)
    resale = next((g for g in graph.flows if g.attrs.get("purchase_flow") == f.id), None)
    ask = (("flow:%s.routed_via_trader" % (resale.attrs.get("fact_key") or resale.id),) if resale is not None
           and resale.attrs.get("routed_via_trader") is None else ("flow.delivered_to",))
    known = {"goods_exported_from_cn": False if shipped != CN else None,
             "goods_imported_into_cn": False if shipped == CN else None,
             "goods_imported_into_sg": False if shipped == SG else None}
    if delivered is not None:
        facts.setdefault(("flow", "delivered_to"), delivered)
        known = {"goods_exported_from_cn": shipped == CN and delivered != CN,
                 "goods_imported_into_cn": delivered == CN and shipped != CN,
                 "goods_imported_into_sg": delivered == SG and shipped != SG}
    for k, v in known.items():
        if v is None:
            facts[("_needs", "flow." + k)] = ask
        else:
            facts.setdefault(("flow", k), v)


def goods_facts(graph: Graph, f: FlowEdge, facts, payer, payee):
    """口径 D42. A trader's resale (the flow names the purchase it resells, purchase_flow): its cost of goods is what it
    paid its supplier, with that purchase's arm's-length figures, the supplier's jurisdiction and how each jurisdiction
    relates the two (口径 D40) — for the cap and the corresponding adjustment (procedure_common.purchase_cost). Where its
    contracts are effected, when the case does not say (DIPN 21 ¶23(d), (e)): a sale to a Hong Kong customer, a purchase
    from a Hong Kong supplier, in Hong Kong."""
    facts.setdefault(("flow", "consideration"), f.amount)
    route_facts(graph, f, facts)
    buy = next((g for g in graph.flows if g.id == f.attrs.get("purchase_flow")), None)
    facts.setdefault(("flow", "trading_resale"), buy is not None)
    if payer.loc == HK:
        facts.setdefault(("flow", "sale_effected_in_hk"), True)
    if buy is None:
        return
    sup = graph.entities[buy.payee]
    if buy.attrs.get("amount_unknown"):
        facts[("_needs", "flow.cost_basis")] = ("flow:%s.amount" % buy.id,)
    else:
        facts.setdefault(("flow", "cost_basis"), buy.amount)
        facts.setdefault(("flow", "purchase_price"), buy.amount)
    for k in ("arms_length_value", "arms_length_low", "arms_length_max"):
        if buy.attrs.get(k) is not None:
            facts.setdefault(("flow", "purchase_" + k), buy.attrs[k])
    facts.setdefault(("flow", "purchase_supplier_jur"), sup.loc)
    facts.setdefault(("flow", "purchase_treaty"), treaty(sup.loc, payee.loc))
    stated = buy.attrs.get("parties_related")
    rel = {j: bool(stated) for j in RELATED} if stated is not None else relatedness(graph, buy.payer, buy.payee, params())
    for j, k in RELATED.items():
        if rel[j] is not None:
            facts.setdefault(("flow", "purchase_" + k), rel[j])
    if sup.loc == HK:
        facts.setdefault(("flow", "purchase_effected_in_hk"), True)


CAPITALISED_FROM = ("retained_earnings", "share_premium")      # 口径 D46: the reserves the model capitalises


PE_FIELD = {CN: "fixed_place_in_cn", HK: "fixed_place_in_hk", SG: "fixed_place_in_sg"}


def pe_abroad(e):
    """口径 D47. Whether a company has a permanent establishment (a place of business) outside its own jurisdiction: a
    branch the case gives (branch_profit_<j>) or a fixed place there; None while a fixed place is unknown."""
    if e.type == "BRANCH":
        return False
    out = False
    for j, k in PE_FIELD.items():
        if j == e.loc:
            continue
        v = True if "branch_profit_" + j.lower() in e.attrs else e.attrs.get(k)
        if v is True:
            return True
        if v is None:
            out = None
    return out


def pe_scope(graph: Graph, facts, payee):
    """口径 D47. The FSIE regime's MNE entity (Cap 112 s15H(1)): one of a group with an entity or a permanent
    establishment outside the parent's jurisdiction, or a stand-alone entity with a permanent establishment abroad;
    s10L's relevant group (ITA s10L(5)(b)): a group of more than one entity whose members are not all in one
    jurisdiction or one of which has a place of business in more than one — a single company with a branch abroad is no
    group (e-Tax Guide para 5.5). A fixed place unknown where it decides: asked."""
    group = sorted(graph.component(payee.id))
    multi = any(graph.entities[e].loc != payee.loc for e in group)
    pes = [pe_abroad(graph.entities[e]) for e in group]
    pe = True if any(v is True for v in pes) else (None if any(v is None for v in pes) else False)
    open_ = tuple("%s.%s" % (e, k) for e in group for j, k in PE_FIELD.items()
                  if j != graph.entities[e].loc and graph.entities[e].attrs.get(k) is None
                  and "branch_profit_" + j.lower() not in graph.entities[e].attrs and graph.entities[e].type != "BRANCH")
    for field, applies in (("is_mne_member", True), ("is_relevant_group_entity", payee.loc == SG and len(group) > 1)):
        if ("payee", field) in facts:
            continue
        if not applies:
            facts[("payee", field)] = False
        elif multi or pe is True:
            facts[("payee", field)] = True
        elif pe is False:
            facts[("payee", field)] = False
        else:
            facts[("_needs", "payee." + field)] = open_


def capitalisation_facts(graph: Graph, f: FlowEdge, facts, payer, payee):
    """口径 D46. A capitalisation (转增股本): a DIVIDEND flow the payer books as share capital (capitalised: True), out of
    retained earnings (盈余公积、未分配利润) or share premium (股权（票）溢价形成的资本公积) — capitalised_from. No sum is paid:
    nothing is received in Hong Kong (Cap 112 s15H(5); Advance Ruling Case No. 75, an in-kind dividend of an overseas
    company's shares) or Singapore (ITA s10(25)). A Mainland company's capitalisation for a foreign investor is the
    investor's distributed profit reinvested in the company itself (财税〔2018〕102号 第二条（一）1、（二）), with no
    funds moving through any other account (第二条（三）)."""
    if not f.attrs.get("capitalised"):
        facts.setdefault(("flow", "capitalised"), False)
        return
    src = f.attrs.get("capitalised_from")
    if src is not None and src not in CAPITALISED_FROM:
        raise ValueError("flow %s: capitalised_from %r is outside the model (口径 D46: %s)" % (f.id, src, ", ".join(CAPITALISED_FROM)))
    fix(facts, "receipt_kind", "NONE")
    if payer.loc == CN and payee.loc != CN:                         # the capitalisation is the reinvestment: by definition
        facts.update({("flow", "reinvested_in_cn"): True, ("flow", "reinvestment_form"): "capital_increase",
                      ("flow", "direct_payment"): True, ("flow", "reinvested_into"): f.payer})
        if src is None:
            facts.pop(("flow", "reinvestment_from_distributed_profit"), None)
            facts[("_needs", "flow.reinvestment_from_distributed_profit")] = ("flow.capitalised_from",)
        else:
            facts[("flow", "reinvestment_from_distributed_profit")] = src == "retained_earnings"


def withdrawal_facts(graph: Graph, f: FlowEdge, facts):
    """口径 D46. 财税〔2018〕102号 第六条: a foreign investor that takes back the reinvested investment — sells it, has it
    bought back, the investee is wound up — files and pays the deferred tax within 7 days of receiving the proceeds.
    A sale or a winding-up in the model takes the whole holding, so the deferred tranche (which goes first: 公告2018年
    第53号 第十一条) is wholly taken back; a capital reduction of part of the capital takes back an amount the model
    cannot place against the tranche without the capital accounts — whether the deferred investment went is asked.
    Taken back among the modelled flows: reinvestment_withdrawn(_on), and the holding the 2025 credit needs ends there
    (公告2025年第18号 第三条). The investee unknown while the investor disposes of a Mainland company: asked
    (reinvested_into)."""
    if facts.get(("flow", "reinvested_in_cn")) is not True:
        return
    forms = str(params()["cn.reinvest.withdrawal_forms"]).split(";")
    held = lambda g: g.target if g.income == SHARE_TRANSFER else g.payer
    later = [g for g in graph.flows if g.id != f.id and g.income in forms and g.payee == f.payee and g.on >= f.on and held(g)]
    into = facts.get(("flow", "reinvested_into"))
    if into is None:
        if any(graph.entities[held(g)].loc == CN for g in later):
            facts[("_needs", "flow.reinvestment_withdrawn")] = ("flow.reinvested_into",)
        else:
            facts.setdefault(("flow", "reinvestment_withdrawn"), False)
        return
    out = sorted((g for g in later if held(g) == into), key=lambda g: g.on)
    if any(g.income == "CAPITAL_REDUCTION" and float(g.attrs.get("reduced_capital_ratio") or 0.0) < 100.0 for g in out):
        return                                                      # a part of the capital: asked
    facts.setdefault(("flow", "reinvestment_withdrawn"), bool(out))
    if out:
        facts.setdefault(("flow", "reinvestment_withdrawn_on"), out[0].on)
        fix(facts, "planned_holding_months", months(f.on, out[0].on))


PROPERTY_USES = ("residential", "non_residential", "industrial")     # 口径 D48


def property_facts(f: FlowEdge, facts):
    """口径 D48. A sale of land use rights or a building (PROPERTY_TRANSFER): the price is the consideration; how long the
    seller held it (acquired_on), whether it acquired it before 2016-05-01 (the VAT simplified method for old property,
    公告2026年第10号 三（二）4、四（八)); its use (property_use) drives the Singapore duties."""
    use = f.attrs.get("property_use")
    if use is not None and use not in PROPERTY_USES:
        raise ValueError("flow %s: property_use %r is outside the model (口径 D48: %s)" % (f.id, use, ", ".join(PROPERTY_USES)))
    facts.setdefault(("flow", "consideration"), f.amount)
    acq = f.attrs.get("acquired_on")
    if acq is not None:
        facts.setdefault(("flow", "holding_months"), months(acq, f.on))
        facts.setdefault(("flow", "acquired_before_2016_05"), acq <= date.fromisoformat(str(params()["cn.vat.property_old_cutoff"])))
    facts.setdefault(("flow", "property_residential"), None if use is None else use == "residential")
    facts.setdefault(("flow", "property_non_residential"), None if use is None else use != "residential")
    by = f.attrs.get("stamp_borne_by")                       # Hong Kong: who bears the ad valorem duty under the contract
    if by is not None:
        if by not in ("payer", "payee"):
            raise ValueError("flow %s: stamp_borne_by %r is outside the model (payer, payee)" % (f.id, by))
        facts.setdefault(("flow", "stamp_borne_by_payer"), by == "payer")


def rent_facts(graph: Graph, f: FlowEdge, facts, payer):
    """口径 D49. The rent of land or a building, a year at a time. The Mainland sources rent where the payer is (实施条例 第七条
    （五）), Hong Kong and Singapore where the property is: a tenant elsewhere than the property is outside the model (it
    pays and deducts where it sits, and the property is taxed where it lies — each rule reads one place). The lease's own
    stamp duty is on its execution (Hong Kong on the yearly rent once; Singapore on the rent of at most 4 years): the
    flow's lease year (lease_start, else the flow is the first)."""
    loc = f.attrs.get("property_loc")
    if loc is not None and payer.loc != loc:
        raise ValueError("flow %s: a tenant in %s for property in %s is outside the model (口径 D49)" % (f.id, payer.loc, loc))
    start = f.attrs.get("lease_start")
    year = 1 + (months(start, f.on) // 12 if start is not None and f.on is not None else (0 if "@" not in f.id else 1))
    facts.setdefault(("flow", "lease_year"), year)
    facts.setdefault(("flow", "lease_first_year"), year == 1)       # Hong Kong stamps the lease once, on its execution


def facts_for(graph: Graph, f: FlowEdge):
    payer, payee = graph.entities[f.payer], graph.entities[f.payee]
    facts = {("_meta", "flow"): f.attrs.get("fact_key") or f.id, ("_meta", "payer"): f.payer, ("_meta", "payee"): f.payee,
             ("_meta", "flow_base"): f.id, ("_meta", "flow_side"): frozenset(f.attrs.get("fact_key_fields") or ())}
    for k, v in payer.attrs.items():
        facts[("payer", k)] = v
    for k, v in payee.attrs.items():
        facts[("payee", k)] = v
    # 口径 D50: Hong Kong's economic substance is for the basis period of the year the income accrues (Cap 112 s15K(2);
    # Example 18) — a ruling or finding stated year by year ({"2025": true, ...}) is read for the flow's accrual year
    ruled = payee.attrs.get("substance_ruled_adequate")
    if isinstance(ruled, dict):
        facts[("payee", "substance_ruled_adequate")] = ruled.get(str((f.attrs.get("accrued_on") or f.on).year))
    for k, v in f.attrs.items():
        facts[("flow", k)] = v
    src = source_of(graph, f)
    # 口径 D21: a company the plan creates on the source side — the source jurisdiction's statutory rate is its headline
    # rate; a new company is not listed and its dividends (ordinary shares, by design) are not deductible
    origin = graph.entities[f.target] if f.income == SHARE_TRANSFER and f.target else payer
    if origin.attrs.get("created_by_plan"):
        Pp = params()
        facts.setdefault(("flow", "foreign_headline_rate"), Pp[HEADLINE[src]] if src in HEADLINE else None)
        facts.setdefault(("flow", "listed_market_trade"), False)
        if f.income in ("DIVIDEND", "DISTRIBUTION") or f.income == SHARE_TRANSFER:
            facts.setdefault(("flow", "deductible_at_payer"), False)
    facts[("payee", "payee_in_source_jur")] = payee.loc == src
    facts[("payee", "payee_resident_in_cn")] = payee.loc == CN
    # a residence certificate is a fact about years: valid for the flow's year unless circumstances changed before it
    years, changed = payee.attrs.get("cert_years"), payee.attrs.get("circumstances_changed_on")
    if years is not None and "residence_cert" not in payee.attrs:
        facts[("payee", "residence_cert")] = f.on.year in years and not (changed and changed <= f.on)
    accrued = f.attrs.get("accrued_on") or f.on         # holding periods are measured at accrual (hk s15M(2))
    regime_facts(facts, f.income, f.on, accrued, params())
    facts.setdefault(("payee", "payee_is_government"), payee.type == "GOVERNMENT")
    facts.setdefault(("payee", "payee_is_financial_institution"), payee.type == "BANK_FI")
    facts[("flow", "income")] = f.income
    facts[("flow", "amount")] = f.amount
    facts[("flow", "date_of_payment")] = f.on
    facts.setdefault(("flow", "authority_action"), "none")          # a dispute exists only when stated
    facts.setdefault(("flow", "prior_map_outcome"), "none")
    as_at, period_to = f.attrs.get("as_at"), f.attrs.get("period_to") or f.on
    facts.setdefault(("flow", "claim_is_for_prior_year"), bool(as_at) and period_to.year < as_at.year)
    if f.income == SHARE_TRANSFER:
        facts.setdefault(("flow", "consideration"), f.amount)
        h = graph.holding(f.payee, f.target) if f.target else None
        if h is not None:
            facts.setdefault(("flow", "cost_basis"), h.cost)
            facts.setdefault(("flow", "max_ratio_12m"), h.ratio)        # any holding within the look-back counts
            facts.setdefault(("flow", "ratio"), h.ratio)
            facts.setdefault(("flow", "holding_months"), months(h.since, accrued))
        # association (HK SDO s45(2); SG 2014 Rules r 3): one owns the other, or a third owns both, at the least link
        facts.setdefault(("flow", "associated_ratio"), max(
            [graph.chain_ratio(f.payer, f.payee), graph.chain_ratio(f.payee, f.payer)]
            + [min(graph.chain_ratio(e, f.payer), graph.chain_ratio(e, f.payee)) for e in graph.entities if e not in (f.payer, f.payee)]))
        facts.setdefault(("flow", "reorg_step"), False)             # 口径 D18: only the step the template generates is one
        if f.target:
            sg_group_facts(graph, f, facts, accrued)                # 口径 D45
        if f.attrs.get("reorg_step"):                               # the transfer that puts HOLD between ULT and OP
            ctl = graph.holding(f.payee, f.payer)
            acq = graph.holding(f.payer, f.target) if f.target else None
            facts.setdefault(("flow", "reorg_control_ratio"), ctl.ratio if ctl else 0.0)
            facts.setdefault(("flow", "reorg_acquired_ratio"), acq.ratio if acq else 0.0)
            facts.setdefault(("flow", "reorg_same_residence"), payer.loc == payee.loc)
            facts.setdefault(("flow", "reorg_buyer_resident_in_cn"), payer.loc == CN)
            # 59号 第五条(五) / 第七条(一): the transferor keeps the equity it received 12 months, its shares in the
            # transferee 3 years — the structure's own later sale of the transferee breaks them
            Pp = params()
            sold = [g for g in own_later(graph, f, 12 * int(Pp["cn.reorg.commitment_years"]))
                    if g.payee == f.payee and g.target == f.payer]
            if sold:
                fix(facts, "reorg_commitment_3y", False)
            if any(g.on <= add_months(f.on, int(Pp["cn.reorg.keep_months"])) for g in sold):
                fix(facts, "reorg_shares_kept_12m", False)
        if f.target:
            # 口径 D44: an intra-group transfer between entities associated under s15OC
            facts.setdefault(("flow", "intragroup_transfer"), hk_associated(graph, f.payer, f.payee, params()))
            Pp = params()
            years = int(Pp[CLAWBACK_YEARS.get(graph.entities[f.target].loc, "hk.fsie.intragroup_clawback_years")])
            later = own_later(graph, f, 12 * years)
            if any(leaves(graph, g, f.payer) for g in later):          # the transferee sold out of the group in the window
                fix(facts, "clawback_event_within_2y", True)
            if any(g.payee == f.payer and g.target == f.target for g in later):   # SG r 7(1)(b): the asset disposed of
                fix(facts, "asset_disposed_within_2y", True)
            ca, cc = f.attrs.get("ceased_associated_on"), f.attrs.get("ceased_chargeable_on")
            if ca is not None or cc is not None:
                facts.setdefault(("flow", "clawback_event_within_2y"),
                                 any(d is not None and 0 <= (d - f.on).days <= 2 * 365 for d in (ca, cc)))
            under = graph.subtree(f.target) - {f.target}
            facts.setdefault(("flow", "indirect_cn_target"),
                             graph.entities[f.target].loc != CN and any(graph.entities[e].loc == CN for e in under))
    else:
        if f.income == "DIVIDEND":                                  # 口径 D18: no restructuring step behind it unless the
            facts.setdefault(("flow", "reorg_special_applied"), False)   # engine finds one (engine.read)
            capitalisation_facts(graph, f, facts, payer, payee)     # 口径 D46
            withdrawal_facts(graph, f, facts)
        h = graph.holding(f.payee, f.payer)                         # the recipient's holding in the payer
        if h is not None:
            facts.setdefault(("flow", "direct_ratio"), h.ratio)
            facts.setdefault(("flow", "ratio"), h.ratio)
            facts.setdefault(("flow", "holding_months"), months(h.since, accrued))
        else:                                                       # holdings are core: no edge means no direct holding
            facts.setdefault(("flow", "direct_ratio"), 0.0)
            facts.setdefault(("flow", "ratio"), 0.0)
        # back-to-back payments: what the recipient pays on to third-jurisdiction residents inside the window
        facts.setdefault(("payee", "onpay_ratio_12m"), onpay_ratio(graph, f, int(params()["cn.bo.onpay_window"])))
    hk_months(facts)                                                # 口径 D44
    if f.income in (PROPERTY, RENT):                                # 口径 D48, D49: a sale or a lease of land or a building
        property_facts(f, facts)
    if f.income == RENT:
        rent_facts(graph, f, facts, payer)
    if f.income == GOODS:                                           # 口径 D42: a sale of goods
        goods_facts(graph, f, facts, payer, payee)
    if f.income == IP_TRANSFER:                                     # 口径 D22: the IP transfer step
        facts.setdefault(("flow", "consideration"), f.amount)
        # 财税〔2010〕111号 第四条: one holds the other wholly (directly or indirectly) — the reduction is denied; sisters
        # wholly held by one holder are not named there (a judgement, the rule's Discretion)
        held = max(graph.chain_ratio(f.payer, f.payee), graph.chain_ratio(f.payee, f.payer))
        facts.setdefault(("flow", "ip_parties_100pct_held"), held >= 100.0 - 1e-9)
        facts.setdefault(("flow", "ip_parties_100pct_sisters"), any(
            graph.chain_ratio(e, f.payer) >= 100.0 - 1e-9 and graph.chain_ratio(e, f.payee) >= 100.0 - 1e-9
            for e in graph.entities if e not in (f.payer, f.payee)))
        # 印花税法 第一条: a party in the Mainland writes or uses the instrument there
        facts.setdefault(("flow", "cn_party"), payer.loc == CN or payee.loc == CN)
        # ITA s19B(10A)(a)(i): only a seller with Singapore deductions for creating the IP can bar the buyer's allowance
        if payee.loc != SG:
            facts.setdefault(("flow", "seller_had_sg_creation_deductions"), False)
        if f.attrs.get("ip_transfer_mode") == "BOOK":              # 口径 D28: 增值税法 第五条、第十九条 — a deemed sale at
            facts.setdefault(("flow", "price_includes_vat"), False)   # market value, no price that could include the VAT
        if payer.loc == CN:                                         # 111号 第三条: only an export can be a restricted one
            facts.setdefault(("flow", "technology_export_restricted"), False)
    if f.income == ROYALTY and payee.attrs.get("created_by_plan"):
        # 口径 D22: an IP company the plan creates holds IP it bought (the iptx step) and does no R&D of its own in the
        # model: no qualifying R&D expenditure (Cap 112 Sch 17FC s5(3)(c) excludes the acquisition) — the R&D fraction is
        # nil whatever the other expenditure is, so the acquisition price stands for it (0 while unknown changes nothing)
        bought = [g for g in graph.flows if g.income == IP_TRANSFER and g.payer == f.payee]
        facts.setdefault(("flow", "qualifying_rd_expenditure"), 0.0)
        facts.setdefault(("flow", "non_qualifying_expenditure"), float(bought[0].amount) if bought else 0.0)
    # residence-side status the graph knows: a Hong Kong entity is a Hong Kong resident person; an entity whose
    # holding group reaches another jurisdiction belongs to an MNE group (hk s15H) / is a relevant group entity (sg s10L)
    facts.setdefault(("payee", "hk_resident_or_pe"), payee.loc == HK)
    pe_scope(graph, facts, payee)                                   # 口径 D47: and a permanent establishment abroad
    # Cap 112 s58C(1): an entity below any two of the three Schedule 17I thresholds keeps no master / local file
    rev, assets, staff = (payer.attrs.get(k) for k in ("revenue", "total_assets", "employees"))
    if rev is not None and assets is not None and staff is not None and ("payer", "hk_tp_small_entity") not in facts:
        Pp = params()
        below = sum([rev <= Pp["hk.tp.threshold_revenue"], assets <= Pp["hk.tp.threshold_assets"], staff <= Pp["hk.tp.threshold_employees"]])
        facts[("payer", "hk_tp_small_entity")] = below >= 2
    loc = f.attrs.get("service_location")                   # where the work was physically done, a jurisdiction code
    share = f.attrs.get("service_onshore_share")            # or the share of the work done in the source jurisdiction, %
    if loc is not None:
        facts.setdefault(("flow", "service_performed_in_source"), loc == src)
        if loc == src:                                              # 口径 D23: done in the Mainland, not consumed on site abroad
            facts.setdefault(("flow", "service_consumed_on_site_abroad"), False)
        facts.setdefault(("flow", "service_performed_in_residence"), loc == payee.loc)
        facts.setdefault(("flow", "service_onshore_share"), 100.0 if loc == src else 0.0)
    elif share is not None:
        facts.setdefault(("flow", "service_performed_in_source"), float(share) > 0)
        facts.setdefault(("flow", "service_performed_in_residence"), float(share) < 100 and payee.loc != src)
    # 口径 D40: related under each jurisdiction's own test; an open one asks the case (parties_related)
    stated = f.attrs.get("parties_related")
    rel = {j: bool(stated) for j in RELATED} if stated is not None else relatedness(graph, f.payer, f.payee, params())
    for j, k in RELATED.items():
        if rel[j] is None:
            facts[("_needs", "flow." + k)] = ("flow.parties_related",)
        else:
            facts.setdefault(("flow", k), rel[j])
    facts.setdefault(("flow", "parties_treaty"), treaty(payer.loc, payee.loc))    # 口径 D41: Art 9(2) between the two
    facts.setdefault(("flow", "parties_linked"), bool(stated) or linked(graph, f.payer, f.payee))   # 口径 D43: customs
    if f.income == "INTEREST" and not stated and not linked(graph, f.payer, f.payee):   # 口径 D25: 统借统还 is a group's
        facts.setdefault(("flow", "unified_borrowing_relending"), False)               # own on-lending
    # beneficial owner through a 100% owner in the same jurisdiction (cn.sta.2018-09 #i3), from the holding chain
    if ("payee", "bo_via_100pct_owner") not in facts:
        owners = [e for e in graph.entities.values()
                  if e.id != payee.id and graph.chain_ratio(e.id, payee.id) >= 100.0 - 1e-9]
        facts[("payee", "bo_via_100pct_owner")] = any(
            o.loc == payee.loc and o.attrs.get("bo_safe_harbour") is True for o in owners) if owners else False
    # 口径 D31: a party the effective-management variant moved to the Mainland is a Mainland resident for income tax only;
    # VAT and stamp duty read where it is established (its seat) — the facts that turn on a party's place, by the seat
    target = graph.entities[f.target] if f.target else None
    if any(e is not None and e.attrs.get("seat") for e in (payer, payee, target)):
        seat = lambda e: e.attrs.get("seat") or e.loc
        ssrc = seat(target) if f.income == SHARE_TRANSFER and target is not None else seat(payer)
        over = {("payee", "payee_in_source_jur"): seat(payee) == ssrc}
        if f.income == IP_TRANSFER and "cn_party" not in f.attrs:
            over[("flow", "cn_party")] = seat(payer) == CN or seat(payee) == CN
        facts[("_meta", "seat")] = tuple(sorted(over.items()))
    return facts
