"""Singapore evaluators: deadlines, penalties, computed BASE fractions and deduction caps of Singapore rules.

REGISTRY: the rule's value text for a deadline named by text, else the rule id -> (effect, evaluator, clauses the
evaluator implements); an unknown rule text raises instead of guessing. compile.check_registry checks that every
registered rule exists and is a Singapore rule (or a treaty rule with Singapore), that every clause is in the library,
and that every rule needing an evaluator has one. Numbers come from params; dates from official/calendars."""
import csv
from datetime import date, timedelta

from ..params import OFFICIAL
from .procedure_common import (add_months, arms_length_share, arms_length_uplift, corresponding_share, gain_share, goods_share,  # noqa: F401
                               ip_gain_share, ip_recapture_share, months_after, p2_shortfall_share, profit_share)

JUR = "SG"


_SG_HOLIDAYS = {}


def load_holidays(P):
    """Public holidays from the official calendar, plus the day after a holiday that falls on a Sunday; the calendar
    is read once per process."""
    sub = bool(P["sg.holiday.sunday_substitute"])
    if sub not in _SG_HOLIDAYS:
        with open(str(OFFICIAL / "calendars" / "sg_public_holidays.csv"), encoding="utf-8-sig", newline="") as f:
            days = {date.fromisoformat(r["date"]) for r in csv.DictReader(f)}
        years = {d.year for d in days}
        if sub:
            for h in sorted(days):
                if h.weekday() == 6:
                    nxt = h + timedelta(days=1)
                    while nxt in days:
                        nxt += timedelta(days=1)
                    days.add(nxt)
        _SG_HOLIDAYS[sub] = (frozenset(days), frozenset(years))
    return _SG_HOLIDAYS[sub]


class GapDate(date):
    """A nominal date that could not be rolled because that year's holiday calendar is missing; .gap names it."""
    gap = None


def gap_date(d, jur):
    g = GapDate(d.year, d.month, d.day)
    g.gap = (jur, d.year)
    return g


def roll_forward(d, P):
    """Interpretation Act s50: a last day that is an excluded day moves to the next day that is not."""
    kinds = P["sg.time.excluded_days"].split(";")
    if not P["sg.time.act_on_excluded_day"]:
        return d
    holidays, years = load_holidays(P)
    while True:
        if d.year not in years:
            return gap_date(d, "SG")                          # calendar for that year not in the library: reported, not assumed
        if ("sunday" in kinds and d.weekday() == 6) or ("public_holiday" in kinds and d in holidays):
            d += timedelta(days=1)
        else:
            return d


def saturday_roll(d, P):
    """IRAS practice under s45(2)(a): a Saturday also moves to the next working day (observed_rules.csv)."""
    while True:
        if d.weekday() == 5:
            d += timedelta(days=1)
        rolled = roll_forward(d, P)
        if rolled == d and d.weekday() != 5:
            return d
        d = rolled


# DEADLINE evaluators: value text -> (deadline name, fn(facts, P, deadlines) -> (nominal, date) or None)
def _filing(facts, P, deadlines):
    paid = facts.get(("flow", "date_of_payment"))
    if paid is None:
        return None
    nominal = add_months(paid, 2).replace(day=15)
    return nominal, roll_forward(nominal, P)


def _filing_practice(facts, P, deadlines):
    cur = deadlines.get("filing")
    return (cur[0], saturday_roll(cur[1], P)) if cur else None


def _cor_current(facts, P, deadlines):
    end = facts.get(("flow", "period_to"))
    return (date(end.year + 1, 3, 31),) * 2 if end else None


def _cor_prior(facts, P, deadlines):
    sub = facts.get(("flow", "as_at"))
    return (add_months(sub, 3),) * 2 if sub else None


def late_penalty(tax, due, as_at, P):
    """s45(4): 5% once the due date is missed; from 30 days after it, 1% per completed month, capped."""
    if as_at <= due:
        return 0.0
    start = due + timedelta(days=int(P["sg.wht.late_penalty_monthly_starts_after_days"]))
    months = 0
    while add_months(start, months + 1) <= as_at:
        months += 1
    extra = min(months * P["sg.wht.late_penalty_monthly"], P["sg.wht.late_penalty_monthly_cap"])
    return round(tax * (P["sg.wht.late_penalty"] + extra) / 100.0, 2)


def penalty(rule, facts, P, deadlines, tax):
    due, as_at = deadlines.get("filing"), facts.get(("flow", "as_at"))
    if due is None or as_at is None or tax is None:
        return None
    return late_penalty(tax, due[1], as_at, P)


def _sg_return_due(facts, P, deadlines):
    """ITA s34F(5)(a): documentation by the time for making the return. The Act sets no date (s62: by notice); the case's
    stated return date wins, else IRAS practice (sg.corp.return_due: 30 Nov of the year of assessment)."""
    due = facts.get(("payer", "return_due_on"))
    if due is not None:
        return due, due
    d = facts.get(("flow", "date_of_payment"))
    if d is None:
        return None
    due = date(d.year + 1, 11, 30)
    return due, due


def sg_tp_surcharge(rule, facts, P, deadlines, tax):
    """ITA s34E(1): 5% of the increase in income or the reduction of a deduction the Comptroller makes."""
    adj = facts.get(("flow", "tp_adjustment_amount"))
    if adj is None:
        return None
    return round(float(adj) * P["sg.tp.surcharge_rate"] / 100.0, 2)


def sg_tp_income_surcharge(rule, facts, P, deadlines, tax):
    """ITA s34E(1)(a) (decision D41): 5% of the increase in income the Comptroller makes under s34D(1A)(a) — the arm's-length
    amount less the price, when the price is outside the arm's-length range; whether or not tax is payable on it (IRAS TP
    Guidelines 9.2). Unknown relatedness: no amount."""
    alv, amount = facts.get(("flow", "arms_length_value")), facts.get(("flow", "amount"))
    if alv is None or not amount or float(alv) <= float(amount) or facts.get(("flow", "sg_related")) is not True:
        return None
    low = facts.get(("flow", "arms_length_low"))
    if low is not None and float(amount) >= float(low):
        return None
    return round((float(alv) - float(amount)) * P["sg.tp.surcharge_rate"] / 100.0, 2)


def sg_uplift(facts, P, ch):
    """decision D41: s34D(1A)(a) — the Singapore payee's income increased to the arm's-length amount, a price inside the
    arm's-length results left alone (IRAS TP Guidelines 5.115)."""
    return arms_length_uplift(facts, P, ch, "sg_related", True)


def sg_corresponding(facts, P, ch, items=()):
    """decision D41: a Singapore payer's deduction when the Mainland taxed the payee at arm's length (Agreement Art 9(2) as
    MLI Art 17(1) replaced it)."""
    return corresponding_share(facts, P, ch, items, JUR)


sg_corresponding.takes_items = True


def s10l_gain_share(facts, P, ch):
    """The gain share of a foreign disposal received here; s10L(10), (11) (decision D41): sold below its open-market price
    (arms_length_value), the Comptroller may treat A + B - C as the gain received — the model's receipt is the whole
    gain, so the share becomes (open-market price - basis) over the price. Whether the Comptroller does is a judgement
    unless the case states it (s10l_open_market_applied); a nil price brings no gain in (e-Tax Guide 11.3)."""
    share = gain_share(facts, P, ch)
    b, c, k = (facts.get(("flow", x)) for x in ("arms_length_value", "consideration", "cost_basis"))
    if b is None or c is None or k is None or c <= 0 or float(b) <= float(c):
        return share
    applied = facts.get(("flow", "s10l_open_market_applied"))
    if applied is None:
        applied = not ch.judged("flow.s10l_open_market_price")
    return max(0.0, (float(b) - float(k)) / float(c)) if applied else share


def _objection(f, P, d):
    return months_after(f, P, "assessment_notice_on", "sg.objection.months_company")


def _p2(f, P, ch):
    return p2_shortfall_share(f, P, ch, "sg.p2.minimum_rate")


S10, S45 = ("sg.ita1947.full#s10",), ("sg.ita1947.full#s45",)
def wda_share(facts, P, ch):
    """s19B(1AA), (2): the price is written down in equal parts over the period the company elects — the shortest, 5
    years — the share falling within the modelled years."""
    years = float(facts.get(("flow", "ip_horizon_years")) or 1)
    return min(1.0, years / P["sg.ip.wda_years"])



def sg_goods_share(facts, P, ch, items=()):
    """decision D42: the seller's profit on goods for Singapore, the price at arm's length (decision D41)."""
    return goods_share(facts, P, ch, items, "SG", "sg_related", True)


sg_goods_share.takes_items = True
GOODS_READS = ("flow.cost_basis", "flow.arms_length_value", "flow.arms_length_low", "flow.operating_costs", "flow.trading_resale",
                 "flow.purchase_price", "flow.purchase_arms_length_value", "flow.purchase_arms_length_low",
                 "flow.purchase_arms_length_max", "flow.purchase_supplier_jur", "flow.purchase_treaty", "flow.purchase_cn_related",
                 "flow.purchase_hk_associated", "flow.purchase_sg_related", "flow.corresponding_adjustment_granted", "flow.sg_related")

def _sgd(facts):
    """The price in Singapore dollars: the case's amount if it is stated in SGD, else times sgd_rate (SGD per unit)."""
    amount = float(facts.get(("flow", "amount")) or 0.0)
    if facts.get(("flow", "currency")) == "SGD":
        return amount
    rate = facts.get(("flow", "sgd_rate"))
    return None if rate is None else amount * float(rate)


def sg_bsd(facts, P, ch, items):
    """First Schedule Article 3(a)(iv) (decision D48): 1% / 2% / 3% / 4% on the first $180,000 / next $180,000 / next $640,000 /
    next $500,000, then 5% on the next $1,500,000 and 6% beyond for residential property; 5% beyond $1,500,000 for the
    rest. As a rate on the price; the use or the SGD value unknown: the scales' ends."""
    amount = float(facts.get(("flow", "amount")) or 0.0)
    if amount <= 0:
        return 0.0
    res, x = facts.get(("flow", "property_residential")), _sgd(facts)
    if res is None or x is None:                          # the residential scale is the higher one
        keys = [k for k, v in (("flow.property_use", res), ("flow.sgd_rate", x)) if v is None]
        fav = ch.missing(*keys)
        if x is None:
            return 0.0 if fav else P["sg.stamp.bsd_rate_top"]
        res = (not fav) if res is None else res
    return _scale(x, P, bool(res)) / x * 100.0


def _scale(x, P, residential):
    cuts = [P["sg.stamp.bsd_band_%d" % k] for k in range(1, 6)]
    rates = ([P["sg.stamp.bsd_res_%d" % k] for k in range(1, 6)] + [P["sg.stamp.bsd_rate_top"]] if residential else
             [P["sg.stamp.bsd_nonres_%d" % k] for k in range(1, 5)] + [P["sg.stamp.bsd_nonres_top"]])
    duty, left = 0.0, x
    for i, rate in enumerate(rates):
        width = cuts[i] if i < len(cuts) and (residential or i < 4) else float("inf")
        part = min(left, width)
        duty += part * rate / 100.0
        left -= part
        if left <= 0:
            break
    return duty


def sg_ssd(facts, P, ch, items):
    """First Schedule Article 3(bd), (bg), (bj) (decision D48): the seller's duty on residential property sold within 4 years
    (16 / 12 / 8 / 4%) when acquired on or after 4 July 2025, within 3 years (12 / 8 / 4%) when acquired from 11 March
    2017; on industrial property within 3 years (15 / 10 / 5%) when acquired on or after 12 January 2013. Other property,
    or a longer holding: none. As a rate on the price; the use or the acquisition date unknown: the ends."""
    use, acq, on = facts.get(("flow", "property_use")), facts.get(("flow", "acquired_on")), facts.get(("flow", "date_of_payment"))
    if use is None or acq is None:
        keys = [k for k, v in (("flow.property_use", use), ("flow.acquired_on", acq)) if v is None]
        return 0.0 if ch.missing(*keys) else P["sg.stamp.ssd_res_1y"]
    year = lambda n: on is not None and on <= add_months(acq, 12 * n)   # "within one year", "not exceeding n years"
    d = lambda k: date.fromisoformat(str(P[k]))
    if use == "residential" and acq >= d("sg.stamp.ssd_res_new_from"):
        steps = ("sg.stamp.ssd_res_1y", "sg.stamp.ssd_res_2y", "sg.stamp.ssd_res_3y", "sg.stamp.ssd_res_4y")
    elif use == "residential" and acq >= d("sg.stamp.ssd_res_old_from"):
        steps = ("sg.stamp.ssd_res_old_1y", "sg.stamp.ssd_res_old_2y", "sg.stamp.ssd_res_old_3y")
    elif use == "industrial" and acq >= d("sg.stamp.ssd_ind_from"):
        steps = ("sg.stamp.ssd_ind_1y", "sg.stamp.ssd_ind_2y", "sg.stamp.ssd_ind_3y")
    else:
        return 0.0
    for n, k in enumerate(steps, start=1):
        if year(n):
            return P[k]
    return 0.0


def sg_property_tax(facts, P, ch, items):
    """decision D49. The owner's property tax on the annual value (annual_value, SGD; the engine asks it): 10% for
    non-residential property; for residential property let (not owner-occupied) 12% / 20% / 28% on the first $30,000 /
    next $15,000 / next $15,000 and 36% above (IRAS, from 1 January 2024). As a rate on the rent; the use unknown: the
    ends."""
    amount, av = float(facts.get(("flow", "amount")) or 0.0), facts.get(("flow", "annual_value"))
    if amount <= 0 or av is None:
        return 0.0
    res = facts.get(("flow", "property_residential"))
    if res is None:
        res = not ch.missing("flow.property_use")
    av = float(av)
    if not res:
        tax = av * P["sg.property_tax.non_residential"] / 100.0
    else:
        cuts = [P["sg.property_tax.band_%d" % k] for k in range(1, 4)]
        rates = [P["sg.property_tax.res_%d" % k] for k in range(1, 5)]
        tax, left = 0.0, av
        for i, rate in enumerate(rates):
            part = min(left, cuts[i]) if i < 3 else left
            tax += part * rate / 100.0
            left -= part
            if left <= 0:
                break
    x = _sgd(facts)
    return 0.0 if not x else 100.0 * tax / x


REGISTRY = {
    "sg.property_tax.rent": ("PROPERTY_TAX", sg_property_tax, ("sg.pta1960.s9#all", "sg.iras.ptax.rates#h6", "sg.iras.ptax.rates#h9")),   # decision D49
    "sg.rent.base": ("BASE", profit_share, ("sg.ita1947.full#s10",)),
    "sg.rent.foreign.base": ("BASE", profit_share, ("sg.ita1947.full#s10",)),
    "sg.stamp.bsd": ("STAMP", sg_bsd, ("sg.sda1929.sch1#sch1",)),                    # decision D48
    "sg.stamp.ssd": ("STAMP", sg_ssd, ("sg.sda1929.sch1#sch1",)),
    "sg.property.base": ("BASE", gain_share, ("sg.ita1947.full#s10",)),
    "sg.goods.base": ("BASE", sg_goods_share, ("sg.ita1947.full#s10", "sg.ita1947.full#s34D")),   # decision D42
    "sg.goods.nonresident.base": ("BASE", sg_goods_share, ("sg.ita1947.full#s10", "sg.ita1947.full#s34D")),
    "sg.gain.base": ("BASE", gain_share, S10),
    "sg.ip.recapture": ("CHARGE", ip_recapture_share, ("sg.ita1947.full#s19B",)),                     # decision D22
    "sg.ip.revenue": ("CHARGE", ip_gain_share, S10),
    "sg.ip.wda.horizon": ("DEDUCT_BASE", wda_share, ("sg.ita1947.full#s19B",)),
    "sg.fsie.gain.base": ("BASE", s10l_gain_share, S10 + ("sg.ita1947.full#s10L", "sg.etax.10l#para11.3")),   # decision D41
    "sg.service.base": ("BASE", profit_share, S10),
    "sg.p2.base": ("BASE", _p2, ("sg.memta2024.s16#s16", "sg.memta2024.s17#s17", "sg.memta2024.s21#s21",
                                 "sg.memta2024.s30#s30")),                           # decision D13, D14, D15
    "sg.tp.deduction_cap": ("DEDUCT_BASE", arms_length_share, ("sg.ita1947.full#s34D",)),
    "15th day of the second month following payment": ("DEADLINE", ("filing", _filing), S45),
    "observed:sg.wht.due_date_saturday_rolls": ("DEADLINE", ("filing", _filing_practice), S45),
    "31 Mar of the following year": ("DEADLINE", ("cor", _cor_current), ("sg.iras.wht.dta-relief#h3",)),
    "3 months from WHT submission": ("DEADLINE", ("cor", _cor_prior), ("sg.iras.wht.dta-relief#h3",)),
    "sg.tp.documentation": ("DEADLINE", ("tp_local_file", _sg_return_due), ("sg.ita1947.full#s34F", "sg.iras.formc#h2")),
    "sg.objection": ("DEADLINE", ("objection", _objection), ("sg.ita1947.full#s76",)),
    "sg.objection.source": ("DEADLINE", ("objection", _objection), ("sg.ita1947.full#s76",)),
    "sg.wht.penalty": ("PENALTY", penalty, S45),
    "sg.tp.surcharge": ("PENALTY", sg_tp_surcharge, ("sg.ita1947.full#s34E",)),
    "sg.tp.income_uplift": ("BASE", sg_uplift, ("sg.ita1947.full#s34D", "sg.ita1947.full#s2", "sg.iras.etax.tp#para5.115")),
    "sg.tp.corresponding": ("DEDUCT_BASE", sg_corresponding, ("treaty.cn-sg.2007.mli.zh#9.2",)),
    "sg.tp.income_surcharge": ("PENALTY", sg_tp_income_surcharge, ("sg.ita1947.full#s34E", "sg.iras.etax.tp#para9.2")),
}

# facts each rule reads besides its parameters and condition; compile.py adds them to RuleObj.reads
READS = {
    "sg.goods.base": GOODS_READS, "sg.goods.nonresident.base": GOODS_READS,
    "sg.ftc.dta": ("flow.foreign_tax_rate",),
    "sg.ip.recapture": ("flow.consideration", "flow.cost_basis", "flow.ip_allowances_claimed"),
    "sg.ip.revenue": ("flow.consideration", "flow.cost_basis"),
    "sg.ip.wda.horizon": ("flow.ip_horizon_years",),
    "sg.ftc.unilateral": ("flow.foreign_tax_rate",),
    "sg.wht.due": ("flow.date_of_payment",),
    "sg.wht.due_practice": ("flow.date_of_payment",),
    "sg.wht.penalty": ("flow.as_at",),
    "sg.dtr.cor": ("flow.period_to",),
    "sg.dtr.cor_prior_years": ("flow.as_at",),
    "sg.objection": ("flow.assessment_notice_on",), "sg.objection.source": ("flow.assessment_notice_on",),
    "sg.fsie.gain.base": ("flow.consideration", "flow.cost_basis", "flow.arms_length_value", "flow.s10l_open_market_applied"),
    "sg.tp.income_uplift": ("flow.arms_length_value", "flow.arms_length_low", "flow.sg_related"),
    "sg.tp.corresponding": ("flow.parties_treaty", "flow.corresponding_adjustment_granted"),
    "sg.tp.income_surcharge": ("flow.arms_length_value", "flow.arms_length_low"),
    "sg.gain.base": ("flow.consideration", "flow.cost_basis"),
    "sg.service.base": ("flow.profit_margin",),
    "sg.p2.base": ("flow.p2_etr", "flow.p2_additional"),
    "sg.tp.surcharge": ("flow.tp_adjustment_amount",),
    "sg.tp.documentation": ("payer.gross_revenue", "payer.return_due_on"),
    "sg.tp.deduction_cap": ("flow.arms_length_max",),
}
