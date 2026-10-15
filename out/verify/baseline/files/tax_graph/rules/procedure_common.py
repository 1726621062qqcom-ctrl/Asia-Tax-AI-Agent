"""Arithmetic several jurisdictions' rules share. It belongs to no jurisdiction: each jurisdiction's module registers it
for its own rules, with the clauses it implements there (REGISTRY; compile.check_registry checks every registration).

A fact an evaluator needs and does not find is reported through the chooser (eval.Chooser): it becomes a pending
item of the rule, and `ch.missing(keys)` says which end to take — the favourable one under FLOOR, the other under
CEILING, or whatever a forced run asks for. Rates and caps come from params; nothing is hard-coded."""
from datetime import date, timedelta


def add_months(d, k):
    y, m = divmod(d.year * 12 + d.month - 1 + k, 12)
    m += 1
    last = (date(y + (m == 12), m % 12 + 1, 1) - timedelta(days=1)).day
    return date(y, m, min(d.day, last))


def months_after(facts, P, fact, pid):
    """A deadline a number of months (a parameter) after a dated fact."""
    d = facts.get(("flow", fact))
    if d is None:
        return None
    due = add_months(d, int(P[pid]))
    return due, due


def gain_share(facts, P, ch):
    """Share of the consideration that is gain: (consideration - cost) / consideration (the profit, not the proceeds)."""
    c, k = facts.get(("flow", "consideration")), facts.get(("flow", "cost_basis"))
    if c is None or k is None:
        fav = ch.missing(*[k2 for k2, v in (("flow.consideration", c), ("flow.cost_basis", k)) if v is None])
        return 0.0 if fav else 1.0
    if c <= 0:
        return 0.0
    return max(0.0, min(1.0, (c - k) / c))


def ip_basis(facts, ch):
    """口径 D22. An IP sale: (proceeds, basis, allowances) — basis the seller's expenditure not yet allowed (the
    Mainland's net value, 实施条例 第七十四条), allowances the deductions already allowed on it (Hong Kong s16E/16EA,
    Singapore s19B). Unknown ones are decided together: the favourable end has the basis cover the proceeds, the other
    no basis and allowances as large as the proceeds. None when there are no proceeds."""
    c = facts.get(("flow", "consideration"))
    if not c or c <= 0:
        return None
    k, a = facts.get(("flow", "cost_basis")), facts.get(("flow", "ip_allowances_claimed"))
    if k is None or a is None:
        fav = ch.missing(*["flow." + n for n, v in (("cost_basis", k), ("ip_allowances_claimed", a)) if v is None])
        k = (c if fav else 0.0) if k is None else k
        a = (0.0 if fav else c) if a is None else a
    return float(c), float(k), float(a)


def ip_recapture_share(facts, P, ch):
    """Hong Kong s16E(3), s16EB(2); Singapore s19B(4), (5): the proceeds above the expenditure still unallowed, up to the
    deductions already allowed, are taxed (as a trading receipt / a balancing charge) — as a share of the proceeds."""
    parts = ip_basis(facts, ch)
    if parts is None:
        return 0.0
    c, k, a = parts
    return max(0.0, min(c - k, a)) / c


def ip_gain_share(facts, P, ch):
    """The whole gain over the seller's tax basis, as a share of the proceeds (a gain of revenue nature)."""
    parts = ip_basis(facts, ch)
    if parts is None:
        return 0.0
    c, k, _ = parts
    return max(0.0, c - k) / c


def profit_share(facts, P, ch):
    """The profit in a fee, a fact of the recipient's accounts; unknown: none or the whole fee."""
    m = facts.get(("flow", "profit_margin"))
    if m is None:
        return 0.0 if ch.missing("flow.profit_margin") else 1.0
    return max(0.0, min(1.0, float(m) / 100.0))


def arms_length_share(facts, P, ch):
    """A stated arm's-length ceiling (from the taxpayer's own study) caps the deductible amount; without one the
    deduction's own judgement condition carries the uncertainty, so nothing is registered here."""
    cap, amount = facts.get(("flow", "arms_length_max")), facts.get(("flow", "amount"))
    if cap is None or amount is None or amount <= 0:
        return 1.0
    return max(0.0, min(1.0, float(cap) / float(amount)))


def arms_length_uplift(facts, P, ch, related, range_test):
    """口径 D41. A related party's payment below its arm's-length amount (arms_length_value): the payee's income is computed
    at that amount — a factor (>= 1) on the amount. related: the field of the jurisdiction's own test (口径 D40), an open
    one pending (the favourable end keeps the price). range_test: Hong Kong and Singapore leave a price inside the
    arm's-length range alone (its lower end arms_length_low, when stated); the Mainland adjusts a profit below the
    median to the median (公告2017年第6号 第二十五条). No arm's-length amount stated: nothing to compute it from."""
    alv, amount = facts.get(("flow", "arms_length_value")), facts.get(("flow", "amount"))
    if alv is None or not amount or amount <= 0 or float(alv) <= float(amount):
        return 1.0
    low = facts.get(("flow", "arms_length_low"))
    if range_test and low is not None and float(amount) >= float(low):
        return 1.0
    rel = facts.get(("flow", related))
    if rel is None:
        rel = not ch.missing(*(facts.get(("_needs", "flow." + related)) or ("flow." + related,)))
    return float(alv) / float(amount) if rel else 1.0


def corresponding_share(facts, P, ch, items, jur):
    """口径 D41. The payer's corresponding adjustment (Arrangement Art 9(2); Agreement Art 9(2) as MLI Art 17(1) replaced
    it; Cap 112 s50AAN): when the payee's jurisdiction taxed the payee on the arm's-length amount, the payer's deduction
    follows it — the appropriate adjustment is the payer's authority's, a judgement unless the case states the outcome
    (corresponding_adjustment_granted); none without a treaty between the two (Hong Kong and Singapore)."""
    up = max((it.uplift for it in items if it.jur != jur and not it.deduction and it.levy == "income" and it.effective > 0),
             default=1.0)
    if up <= 1.0 or facts.get(("flow", "parties_treaty")) in (None, "NONE"):
        return 1.0
    granted = facts.get(("flow", "corresponding_adjustment_granted"))
    if granted is None:
        granted = ch.judged("flow.corresponding_adjustment")
    return up if granted else 1.0


def purchase_cost(facts, P, ch, jur):
    """口径 D42. A trader's cost of the goods it resells: what it paid its supplier (cost_basis) — capped at the purchase's
    arm's-length maximum when it paid more and its own jurisdiction relates the two (as the deduction cap); raised to the
    arm's-length price when the supplier's jurisdiction taxed the supplier on that price (口径 D41: related by its test,
    outside the range where it has one) and a treaty joins the two jurisdictions (Art 9(2)) — the trader's authority's
    appropriate adjustment, a judgement unless the case states it. None when the cost is unknown."""
    k = facts.get(("flow", "cost_basis"))
    if k is None:
        return None
    k, mine = float(k), "purchase_" + {"CN": "cn_related", "HK": "hk_associated", "SG": "sg_related"}[jur]
    cap = facts.get(("flow", "purchase_arms_length_max"))
    if cap is not None and k > float(cap) and facts.get(("flow", mine)):
        return float(cap)
    alv, price, sup = (facts.get(("flow", x)) for x in ("purchase_arms_length_value", "purchase_price", "purchase_supplier_jur"))
    if alv is None or price is None or float(alv) <= float(price) or sup in (None, jur):
        return k
    theirs = "purchase_" + {"CN": "cn_related", "HK": "hk_associated", "SG": "sg_related"}[sup]
    low = facts.get(("flow", "purchase_arms_length_low"))
    if not facts.get(("flow", theirs)) or (sup != "CN" and low is not None and float(price) >= float(low)):
        return k
    if facts.get(("flow", "purchase_treaty")) in (None, "NONE"):
        return k
    granted = facts.get(("flow", "corresponding_adjustment_granted"))
    if granted is None:
        granted = ch.judged("flow.corresponding_adjustment")
    return k + float(alv) - float(price) if granted else k


def goods_share(facts, P, ch, items, jur, related, range_test):
    """口径 D42. The seller's profit on a sale of goods as a share of the price: the price — raised to the arm's-length
    price when a related buyer paid less (口径 D41: arms_length_uplift, kept on the item for the buyer's corresponding
    adjustment) — less the cost of the goods (cost_basis: a manufacturer's, or what a trader paid, purchase_cost) and,
    for a trader's resale, its own costs of the trade (operating_costs). An unknown cost is pending: the favourable end
    lets it take the whole price."""
    price = facts.get(("flow", "amount"))
    if not price or price <= 0:
        return 0.0
    up = arms_length_uplift(facts, P, ch, related, range_test)
    for it in items:
        if it.jur == jur and it.levy == "income" and not it.deduction:
            it.uplift = up
    k = purchase_cost(facts, P, ch, jur) if facts.get(("flow", "trading_resale")) else facts.get(("flow", "cost_basis"))
    opex = facts.get(("flow", "operating_costs")) if facts.get(("flow", "trading_resale")) else 0.0
    gone = [n for n, v in (("cost_basis", k), ("operating_costs", opex)) if v is None]
    if gone:
        keys = [x for n in gone for x in (facts.get(("_needs", "flow." + n)) or ("flow." + n,))]
        if ch.missing(*keys):
            return 0.0
        k, opex = k or 0.0, opex or 0.0
    return max(0.0, float(price) * up - float(k) - float(opex)) / float(price)


def p2_shortfall_share(facts, P, ch, rate_pid="p2.minimum_rate"):
    """Top-up percentage = minimum rate - jurisdictional ETR; as a share of the minimum rate it scales a charge at the
    minimum rate on the entity's share of the excess profit. The ETR is the engine's fact from the labels and stated
    covered taxes. An additional current top-up's pseudo-flow already carries the amount: charged in full."""
    if facts.get(("flow", "p2_additional")):
        return 1.0
    etr = facts.get(("flow", "p2_etr"))
    if etr is None:
        keys = facts.get(("flow", "p2_etr_needs")) or ("flow.p2_etr",)
        return 1.0 if not ch.missing(*((keys,) if isinstance(keys, str) else keys)) else 0.0
    m = P[rate_pid]
    return max(0.0, min(1.0, (m - float(etr)) / m))
