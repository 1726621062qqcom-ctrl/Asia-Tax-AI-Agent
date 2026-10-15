"""Hong Kong evaluators: computed BASE fractions, deadlines and deduction caps of Hong Kong rules.

REGISTRY: rule id -> (effect, evaluator, clauses the evaluator implements). compile.check_registry checks that every
registered rule exists and is a Hong Kong rule (or a treaty rule with Hong Kong), that every clause is in the library,
and that every rule needing an evaluator has one. Arithmetic shared with other jurisdictions is in procedure_common."""
from datetime import date

from .procedure_common import (add_months, arms_length_share, arms_length_uplift, corresponding_share, gain_share, goods_share,
                               ip_basis, ip_gain_share, ip_recapture_share, months_after, p2_shortfall_share, profit_share)

JUR = "HK"


def nexus_taxable_share(facts, P, ch):
    """IP income: the excepted portion is F = min(100%, QE x uplift / (QE + NE)); the taxable share is 1 - F."""
    qe, ne = facts.get(("flow", "qualifying_rd_expenditure")), facts.get(("flow", "non_qualifying_expenditure"))
    if qe is None or ne is None:
        fav = ch.missing(*[k for k, v in (("flow.qualifying_rd_expenditure", qe), ("flow.non_qualifying_expenditure", ne)) if v is None])
        return 0.0 if fav else 1.0
    if qe + ne <= 0:
        return 1.0
    f = min(P["hk.fsie.nexus_cap"] / 100.0, qe * P["hk.fsie.nexus_uplift"] / 100.0 / (qe + ne))
    return 1.0 - f


def ip_nexus_fraction(facts, P, ch):
    """Sch 17FC: the excepted portion of a qualifying IP disposal gain (a patent or a software copyright) is its R&D
    fraction; any other IP's gain has none."""
    kind = facts.get(("flow", "ip_kind"))
    if kind is None:
        if not ch.missing("flow.ip_kind"):
            return 0.0
    elif kind not in str(P["hk.fsie.qualifying_ip_kinds"]).split(";"):
        return 0.0
    return 1.0 - nexus_taxable_share(facts, P, ch)


def ip_fsie_share(facts, P, ch):
    """s15I with s16E(3) / s16EB(2): the recaptured part is a trading receipt sourced here; the gain above the original
    cost (still unallowed plus allowed) is an IP disposal gain charged when received here, less the excepted portion."""
    parts = ip_basis(facts, ch)
    if parts is None:
        return 0.0
    c, k, a = parts
    rest = max(0.0, c - k - a) / c
    return ip_recapture_share(facts, P, ch) + rest * (1.0 - ip_nexus_fraction(facts, P, ch))


def _nine_months_after_period(facts, P, deadlines):
    """Cap 112 s58C(2)(a): master and local file within 9 months after the end of the entity's accounting period."""
    end = facts.get(("payer", "accounting_period_end"))
    if end is None:
        d = facts.get(("flow", "date_of_payment"))
        if d is None:
            return None
        end = date(d.year, 12, 31)                      # calendar-year period unless the entity states its own
    due = add_months(end, int(P["hk.tp.local_file_months"]))
    return due, due


def _objection(f, P, d):
    return months_after(f, P, "assessment_notice_on", "hk.objection.months")


def _appeal(f, P, d):
    return months_after(f, P, "determination_on", "hk.appeal.months")


def _p2(f, P, ch):
    return p2_shortfall_share(f, P, ch, "p2.minimum_rate")


S14 = ("hk.cap112.en#s14",)
def hk_fsie_gain_share(facts, P, ch):
    """The gain share of a foreign disposal gain; 口径 D44: after an intra-group transfer the relief deferred, the acquirer
    holds the property at the seller's cost (s15OA(5): hk_cost_basis)."""
    basis = facts.get(("flow", "hk_cost_basis"))
    if basis is None:
        return gain_share(facts, P, ch)
    f2 = dict(facts)
    f2[("flow", "cost_basis")] = basis
    return gain_share(f2, P, ch)


def hk_uplift(facts, P, ch):
    """口径 D41: s50AAF(1) — the Hong Kong payee's income at the arm's-length amount; a price inside the arm's-length range
    is left alone (DIPN 59 ¶121), one outside it goes normally to the median (¶122: the case's arm's-length amount)."""
    return arms_length_uplift(facts, P, ch, "hk_associated", True)


def hk_corresponding(facts, P, ch, items=()):
    """口径 D41: s50AAN — a Hong Kong payer's relief when the Mainland taxed the payee at arm's length, through the
    Arrangement's mutual agreement procedure."""
    return corresponding_share(facts, P, ch, items, JUR)


hk_corresponding.takes_items = True


def hk_goods_share(facts, P, ch, items=()):
    """口径 D42: the seller's profit on goods for Hong Kong, the price at arm's length (口径 D41)."""
    return goods_share(facts, P, ch, items, "HK", "hk_associated", True)


hk_goods_share.takes_items = True
GOODS_READS = ("flow.cost_basis", "flow.arms_length_value", "flow.arms_length_low", "flow.operating_costs", "flow.trading_resale",
                 "flow.purchase_price", "flow.purchase_arms_length_value", "flow.purchase_arms_length_low",
                 "flow.purchase_arms_length_max", "flow.purchase_supplier_jur", "flow.purchase_treaty", "flow.purchase_cn_related",
                 "flow.purchase_hk_associated", "flow.purchase_sg_related", "flow.corresponding_adjustment_granted", "flow.hk_associated")

def _hkd(facts, ch):
    """The price in Hong Kong dollars: the case's amount if it is stated in HKD, else times hkd_rate (HKD per unit)."""
    amount = float(facts.get(("flow", "amount")) or 0.0)
    if facts.get(("flow", "currency")) == "HKD":
        return amount
    rate = facts.get(("flow", "hkd_rate"))
    if rate is None:
        return None
    return amount * float(rate)


def hk_avd(facts, P, ch, items):
    """Cap 117 First Schedule head 1(1) Scale 1 (口径 D48): $100 up to $4,000,000; above it the band's rate on the whole
    consideration, where it crosses into a band the duty of the band below plus 20% (the first), 10% or 30% (above
    $100,000,000) of the excess, whichever is less. As a rate on the price; the price's HKD value unknown: the top rate at
    the unfavourable end, none at the other."""
    amount = float(facts.get(("flow", "amount")) or 0.0)
    x = _hkd(facts, ch)
    if amount <= 0:
        return 0.0
    if x is None:
        return 0.0 if ch.missing("flow.hkd_rate") else P["hk.stamp.avd_rate_top"]
    flat, lim0 = P["hk.stamp.avd_flat"], P["hk.stamp.avd_flat_limit"]
    bands = [(P["hk.stamp.avd_limit_%d" % k], P["hk.stamp.avd_rate_%d" % k]) for k in range(1, 6)]
    if x <= lim0:
        duty = flat
    else:
        lower, prev, duty = lim0, flat, None
        margin = P["hk.stamp.avd_first_marginal"]
        for upper, rate in bands + [(float("inf"), P["hk.stamp.avd_rate_top"])]:
            if x <= upper:
                duty = min(rate / 100.0 * x, prev + margin / 100.0 * (x - lower))
                break
            prev, lower = rate / 100.0 * upper, upper
            margin = P["hk.stamp.avd_top_marginal"] if upper == bands[-1][0] else P["hk.stamp.avd_marginal"]
    return 100.0 * duty / x


def hk_property_tax(facts, P, ch, items):
    """口径 D49. Cap 112 s5(1), s5(1A), s5B: the standard rate on the rent less the 20% repairs allowance."""
    return P["hk.property_tax.rate"] * (1.0 - P["hk.property_tax.repairs_allowance"] / 100.0)


def hk_lease_stamp(facts, P, ch, items):
    """口径 D49. Cap 117 First Schedule head 1(2)(b): a term up to one year 0.25% of the total rent (the year's), above
    one and up to three years 0.5% of the yearly rent, above three years 1%; an undefined term 0.25% of the yearly rent
    (lease_term_months unknown: the ends)."""
    term = facts.get(("flow", "lease_term_months"))
    if term is None:
        return P["hk.stamp.lease_short"] if ch.missing("flow.lease_term_months") else P["hk.stamp.lease_long"]
    term = float(term)
    return P["hk.stamp.lease_short"] if term <= 12 else P["hk.stamp.lease_mid"] if term <= 36 else P["hk.stamp.lease_long"]


REGISTRY = {
    "hk.property_tax.rent": ("PROPERTY_TAX", hk_property_tax, ("hk.cap112.en#s5", "hk.cap112.en#s5B")),      # 口径 D49
    "hk.stamp.lease.lessee": ("STAMP", hk_lease_stamp, ("hk.cap117.en#sch1",)),
    "hk.stamp.lease.lessor": ("STAMP", hk_lease_stamp, ("hk.cap117.en#sch1",)),
    "hk.rent.base": ("BASE", profit_share, S14),
    "hk.stamp.property.buyer": ("STAMP", hk_avd, ("hk.cap117.en#sch1",)),        # 口径 D48
    "hk.stamp.property.seller": ("STAMP", hk_avd, ("hk.cap117.en#sch1",)),
    "hk.property.base": ("BASE", gain_share, S14),
    "hk.goods.base": ("BASE", hk_goods_share, ("hk.cap112.en#s14", "hk.dipn.21#para23", "hk.cap112.en#s50AAF")),   # 口径 D42
    "hk.goods.nonresident.base": ("BASE", hk_goods_share, ("hk.cap112.en#s14", "hk.dipn.21#para23", "hk.cap112.en#s50AAF")),
    "hk.gain.base": ("BASE", gain_share, S14),
    "hk.fsie.gain.base": ("BASE", hk_fsie_gain_share, S14),
    "hk.service.base": ("BASE", profit_share, S14),
    "hk.service.base_resident": ("BASE", profit_share, S14),
    "hk.fsie.ip_nexus": ("BASE", nexus_taxable_share, ("hk.cap112.en#sch17FC",)),
    "hk.ip.recapture": ("CHARGE", ip_recapture_share, ("hk.cap112.en#s16E", "hk.cap112.en#s16EB")),      # 口径 D22
    "hk.ip.fsie": ("CHARGE", ip_fsie_share, ("hk.cap112.en#s15I", "hk.cap112.en#s16E", "hk.cap112.en#sch17FC")),
    "hk.ip.onshore": ("CHARGE", ip_gain_share, S14),
    "hk.p2.base": ("BASE", _p2, ("hk.ord.2025-21#p82", "hk.ord.2025-21#p83", "hk.ord.2025-21#p84", "hk.ord.2025-21#p85",
                                 "hk.ord.2025-21#p71", "hk.ord.2025-21#p91")),        # 口径 D14, D15
    "hk.tp.deduction_cap": ("DEDUCT_BASE", arms_length_share, ("hk.cap112.en#s50AAF",)),
    "hk.tp.income_uplift": ("BASE", hk_uplift, ("hk.cap112.en#s50AAF", "hk.cap112.en#s50AAH", "hk.dipn.59#para121",
                                                "hk.dipn.59#para122")),                                    # 口径 D40, D41
    "hk.tp.corresponding": ("DEDUCT_BASE", hk_corresponding, ("hk.cap112.en#s50AAN", "treaty.cn-hk.2006.zh#9.2")),
    "hk.tp.local_file": ("DEADLINE", ("tp_local_file", _nine_months_after_period), ("hk.cap112.en#s58C",)),
    "hk.objection": ("DEADLINE", ("objection", _objection), ("hk.cap112.en#s64",)),
    "hk.objection.source": ("DEADLINE", ("objection", _objection), ("hk.cap112.en#s64",)),
    "hk.appeal": ("DEADLINE", ("appeal", _appeal), ("hk.cap112.en#s66",)),
}

# facts each rule reads besides its parameters and condition; compile.py adds them to RuleObj.reads
READS = {
    "hk.goods.base": GOODS_READS, "hk.goods.nonresident.base": GOODS_READS,
    "hk.objection": ("flow.assessment_notice_on",), "hk.objection.source": ("flow.assessment_notice_on",),
    "hk.appeal": ("flow.determination_on",),
    "hk.ftc.dta": ("flow.foreign_tax_rate",),
    "hk.ftc.unilateral": ("flow.foreign_tax_rate",),
    "hk.gain.base": ("flow.consideration", "flow.cost_basis"),
    "hk.fsie.gain.base": ("flow.consideration", "flow.cost_basis", "flow.hk_cost_basis"),
    "hk.p2.base": ("flow.p2_etr", "flow.p2_additional"),
    "hk.service.base": ("flow.profit_margin",), "hk.service.base_resident": ("flow.profit_margin",),
    "hk.tp.local_file": ("payer.accounting_period_end",),
    "hk.tp.deduction_cap": ("flow.arms_length_max",),
    "hk.tp.income_uplift": ("flow.arms_length_value", "flow.arms_length_low", "flow.hk_associated"),
    "hk.tp.corresponding": ("flow.parties_treaty", "flow.corresponding_adjustment_granted"),
    "hk.fsie.ip_nexus": ("flow.qualifying_rd_expenditure", "flow.non_qualifying_expenditure"),
    "hk.ip.recapture": ("flow.consideration", "flow.cost_basis", "flow.ip_allowances_claimed"),
    "hk.ip.fsie": ("flow.consideration", "flow.cost_basis", "flow.ip_allowances_claimed", "flow.ip_kind",
                   "flow.qualifying_rd_expenditure", "flow.non_qualifying_expenditure"),
    "hk.ip.onshore": ("flow.consideration", "flow.cost_basis"),
}
