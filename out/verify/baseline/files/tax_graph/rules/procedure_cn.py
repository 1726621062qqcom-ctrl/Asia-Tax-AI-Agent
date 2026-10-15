"""Mainland evaluators: deadlines, penalties, computed BASE fractions and deduction caps of Mainland rules.

REGISTRY: rule id, or the rule's value text for a deadline named by text -> (effect, evaluator, clauses the evaluator
implements). compile.check_registry checks that every registered rule exists and is a Mainland rule (or a treaty rule
with the Mainland), that every clause is in the library, and that every rule needing an evaluator has one.

Deadlines roll over public holidays per 税收征管法实施细则 第109条, with the State Council calendar in
official/calendars/cn_public_holidays.csv (holidays and adjusted working days)."""
import csv
from datetime import date, timedelta

from ..params import OFFICIAL
from .procedure_common import add_months, arms_length_share, arms_length_uplift, corresponding_share, gain_share, goods_share, profit_share


def cn_gain_share(facts, P, ch):
    """The gain share with the Mainland's own tax basis when it differs (口径 D18: after a special reorganisation the
    acquirer keeps the transferor's basis, 59号 §6(2)); otherwise as for every jurisdiction. 口径 D38: equity passing
    between related parties below its arm's-length value is taxed on that value (EIT art 41; 实施条例 第一百一十一条;
    公告2017年第6号 第十七、二十二条) — the gain is then (arm's-length value - basis) over the price paid, which can exceed
    the price. A nil price is the engine's (engine.arms_length_flows). Related by the Mainland's test (口径 D40); an open
    one is pending — the favourable end keeps the price."""
    basis = facts.get(("flow", "cn_cost_basis"))
    f2 = dict(facts)
    if basis is not None:
        f2[("flow", "cost_basis")] = basis
    related = lambda: f2.get(("flow", "cn_related")) or (
        f2.get(("flow", "cn_related")) is None and not ch.missing(*(f2.get(("_needs", "flow.cn_related")) or ("flow.cn_related",))))
    if f2.get(("flow", "cn_income_only")):              # the nil-price transfer at its value: only between related parties
        return gain_share(f2, P, ch) if related() else 0.0
    alv, c = f2.get(("flow", "arms_length_value")), f2.get(("flow", "consideration"))
    if (f2.get(("flow", "income")) == "SHARE_TRANSFER" and alv is not None and c is not None and c > 0
            and float(alv) > float(c) and related()):
        k = f2.get(("flow", "cost_basis"))
        if k is None:
            return 0.0 if ch.missing("flow.cost_basis") else float(alv) / float(c)
        return max(0.0, (float(alv) - float(k)) / float(c))
    return gain_share(f2, P, ch)


def reorg_spread_share(facts, P, ch):
    """59号 §8: the resident's gain spread evenly over ten tax years — the gain share times the share of the ten years
    the horizon holds (the rest falls after it)."""
    years = facts.get(("flow", "reorg_horizon_years")) or 1
    return cn_gain_share(facts, P, ch) * min(1.0, float(years) / P["cn.reorg.resident_spread_years"])

JUR = "CN"


def tech_transfer_share(facts, P, ch, items=()):
    """实施条例 第九十条 (财税〔2010〕111号): a year's technology-transfer income up to 5 million yuan is exempt, the excess
    halved — the taxed share of the gain the charge is on. The case's amounts are turned into yuan by cny_rate (yuan per
    unit; a flow stated in yuan needs none). Unknown: all exempt at the favourable end; at the other the gain is the
    whole proceeds, and with no rate only the halving is certain. 口径 D29: the proceeds are net of the VAT the seller
    takes out of a VAT-inclusive price."""
    c, k = facts.get(("flow", "consideration")), facts.get(("flow", "cost_basis"))
    x = sum(v.rate for v in items if v.levy == "vat" and v.jur == "CN" and not v.deduction and v.borne_by == "payee"
            and v.vat_inclusive) / 100.0
    if not c or c <= 0:
        return 1.0
    rate = 1.0 if facts.get(("flow", "currency")) == "CNY" else facts.get(("flow", "cny_rate"))
    half = P["cn.tech.excess_rate"] / 100.0
    if k is None or rate is None:
        if ch.missing(*["flow." + n for n, v in (("cost_basis", k), ("cny_rate", rate)) if v is None]):
            return 0.0
        if rate is None:
            return half
        k = 0.0
    gain = (float(c) * (1.0 - x) - float(k)) * float(rate)
    if gain <= 0:
        return 1.0
    return max(0.0, gain - P["cn.tech.exempt_max"]) * half / gain


tech_transfer_share.takes_items = True


def transfer_basis_share(facts, P, ch, items):
    """口径 D28. 公告2015年第40号 第三条: under the special treatment the buyer amortises the seller's tax basis, not the
    market value — the share basis / value of its deduction, when the seller's gain was exempted by it on this flow."""
    if not any("cn.reorg.asset_transfer" in it.cites for it in items if it.levy == "income" and not it.deduction):
        return 1.0
    c, k = facts.get(("flow", "consideration")), facts.get(("flow", "cost_basis"))
    if not c or c <= 0:
        return 1.0
    if k is None:
        return 1.0 if ch.missing("flow.cost_basis") else 0.0
    return max(0.0, min(1.0, float(k) / float(c)))


transfer_basis_share.takes_items = True


def amortization_share(facts, P, ch):
    """实施条例 第六十七条: an acquired intangible is amortised straight-line over at least 10 years, or over a shorter life a
    law or the contract sets — the share of the price deducted within the modelled years. An unknown life: the whole
    price within them at the favourable end, ten years at the other."""
    years = float(facts.get(("flow", "ip_horizon_years")) or 1)
    least = P["cn.ip.amortization_years_min"]
    life = facts.get(("flow", "ip_useful_life_years"))
    if life is None:
        return 1.0 if ch.missing("flow.ip_useful_life_years") else min(1.0, years / least)
    return min(1.0, years / max(1e-9, min(float(life), least)))


_CN_HOLIDAYS = []


def load_cn_holidays():
    """The official calendar, read once per process."""
    if not _CN_HOLIDAYS:
        with open(str(OFFICIAL / "calendars" / "cn_public_holidays.csv"), encoding="utf-8-sig", newline="") as f:
            rows = list(csv.DictReader(f))
        from datetime import date
        _CN_HOLIDAYS.append((frozenset(date.fromisoformat(r["date"]) for r in rows if r["kind"] == "holiday"),
                             frozenset(int(r["date"][:4]) for r in rows)))
    return _CN_HOLIDAYS[0]


def roll_cn(start, due, P):
    """第109条: a last day on a statutory holiday moves to the day after the holiday ends; a run of 3 or more
    statutory holidays inside the period extends it by their number of days."""
    if not P["cn.time.holiday_roll"]:
        return due
    holidays, years = load_cn_holidays()
    if due.year not in years:                         # the State Council publishes each year's calendar in November
        from .procedure_sg import gap_date            # of the year before: reported as a gap, not assumed
        return gap_date(due, "CN")
    run, d, extra = 0, start + timedelta(days=1), 0
    while d <= due:                                   # consecutive statutory holidays inside the period
        run = run + 1 if d in holidays else 0
        if run == int(P["cn.time.long_holiday_days"]):
            extra += run
        elif run > int(P["cn.time.long_holiday_days"]):
            extra += 1
        d += timedelta(days=1)
    due = due + timedelta(days=extra)
    while due in holidays:
        due += timedelta(days=1)
    return due


def obligation_date(facts):
    """cn.sta.2017-37 #i4 / #i7: the earlier of actual payment and the date the amount fell due; dividends on payment only."""
    paid, payable = facts.get(("flow", "date_of_payment")), facts.get(("flow", "payable_on"))
    if facts.get(("flow", "income")) == "DIVIDEND":
        return paid
    return min(d for d in (paid, payable) if d) if (paid or payable) else None


def _remit(facts, P, deadlines):
    on = obligation_date(facts)
    if on is None:
        return None
    nominal = on + timedelta(days=int(P["cn.wht.remit_days"]))
    return nominal, roll_cn(on, nominal, P)


def _recapture(facts, P, deadlines):
    """口径 D46. 财税〔2018〕102号 第六条: the deferred tax within 7 days of receiving the proceeds of the withdrawal."""
    on = facts.get(("flow", "reinvestment_withdrawn_on"))
    if on is None:
        return None
    nominal = on + timedelta(days=int(P["cn.reinvest.recapture_days"]))
    return nominal, roll_cn(on, nominal, P)


def _refund(facts, P, deadlines):
    paid = facts.get(("flow", "tax_paid_on"))
    if paid is None:
        return None
    due = paid.replace(year=paid.year + int(P["cn.refund.limit_years"]))
    return due, due


def _map(facts, P, deadlines, pid):
    first = facts.get(("flow", "first_notification_on"))
    if first is None:
        return None
    due = first.replace(year=first.year + int(P[pid]))
    return due, due


# keyed by the rule's value text where the value is a text, by rule id where the value is a number of years
def _review(facts, P, deadlines):
    """行政复议法第20条: 60 days from knowing of the act; 征管法第88条: the tax (or security) must be in first."""
    d = facts.get(("flow", "assessment_notice_on"))
    if d is None:
        return None
    due = d + timedelta(days=int(P["cn.review.days"]))
    return due, due


def late_surcharge(tax, due, paid_on, P):
    """税收征管法 s32: 0.05% of the tax per day of delay."""
    days = (paid_on - due).days
    if days <= 0:
        return 0.0
    return round(tax * P["cn.tca.late_surcharge_daily"] / 100.0 * days, 2)


def surcharge(rule, facts, P, deadlines, tax):
    """A deferred tax paid on a withdrawal runs from its own clock (口径 D46), every other withholding from the remittance one."""
    due, paid_on = deadlines.get("recapture") or deadlines.get("remit"), facts.get(("flow", "remitted_on"))
    if due is None or paid_on is None or tax is None:
        return None
    return late_surcharge(tax, due[1], paid_on, P)


def deemed_profit_share(facts, P, ch):
    """国税发〔2010〕19号 第五条: the authority fixes a profit rate inside the range for the kind of service. "Other"
    services have a floor only, so their upper end is the whole fee; an unknown kind spans the lowest floor to that."""
    ranges = {"MANAGEMENT": ("cn.service.deemed_profit_min", "cn.service.deemed_profit_max"),
              "ENGINEERING_DESIGN_CONSULTING": ("cn.service.deemed_profit_design_min", "cn.service.deemed_profit_design_max"),
              "OTHER": ("cn.service.deemed_profit_other_min", None)}
    kind = facts.get(("flow", "service_kind"))
    lo, hi = ranges.get(kind, ("cn.service.deemed_profit_other_min", None))
    fav = ch.missing("flow.service_kind") if kind not in ranges else ch.fav
    onshore = facts.get(("flow", "service_onshore_share"))     # 实施条例 第七条: only the work done in the Mainland is sourced there
    if onshore is None:
        onshore = 0.0 if ch.missing("flow.service_onshore_share") else 100.0
    base = (P[lo] / 100.0) if fav else (P[hi] / 100.0 if hi else 1.0)
    return base * float(onshore) / 100.0


def benchmark_share(facts, P, ch):
    """实施条例 第三十八条(二): interest between non-financial enterprises is deductible up to the rate a financial
    enterprise would charge for the same kind of loan over the same period; the share is benchmark / actual."""
    rate, bench = facts.get(("flow", "interest_rate")), facts.get(("flow", "benchmark_rate"))
    if facts.get(("payee", "payee_is_financial_institution")):
        return 1.0                                        # 第三十八条(一): borrowing from a financial enterprise, in full
    if rate is None or bench is None:
        fav = ch.missing(*[k for k, v in (("flow.interest_rate", rate), ("flow.benchmark_rate", bench)) if v is None])
        return 1.0 if fav else 0.0
    return 1.0 if rate <= 0 else max(0.0, min(1.0, float(bench) / float(rate)))


def _june_30_next_year(facts, P, deadlines):
    """公告2016年第42号 第十九条: the local file is ready by 30 June of the year after the related-party dealings."""
    d = facts.get(("flow", "date_of_payment"))
    if d is None:
        return None
    due = date(d.year + 1, 6, 30)
    return due, due


def cn_uplift(facts, P, ch):
    """口径 D41: a Mainland payee taxed at the arm's-length amount (EIT art 41); a profit below the median, to the median
    (公告2017年第6号 第二十五条) — the payment against the arm's-length amount, whatever range is stated."""
    return arms_length_uplift(facts, P, ch, "cn_related", False)


def cn_corresponding(facts, P, ch, items=()):
    """口径 D41: a Mainland payer's deduction when Hong Kong or Singapore taxed the payee at arm's length (Arrangement
    Art 9(2); Agreement Art 9(2) as MLI Art 17(1) replaced it)."""
    return corresponding_share(facts, P, ch, items, "CN")


cn_corresponding.takes_items = True


def cn_export_vat(facts, P, ch):
    """口径 D43. Goods exported are zero-rated (增值税法 第十条第四项); the input VAT on them is refunded at the export refund
    rate — the applicable rate unless the MOF and SAT set a lower one (公告2026年第11号 第三条) — and the difference is a
    cost of the export (第五条第三项): (applicable - refund) on the export's FOB value for a manufacturer (免抵退, 第四条
    第一项), on its purchase invoice for a trader (免退, 第四条第七项), as a rate on the price. Unknown rates: nothing at
    the favourable end; at the other the highest applicable rate for goods (第十条: 13%) and no refund."""
    amount = facts.get(("flow", "amount"))
    if not amount or amount <= 0:
        return 0.0
    app, ref = facts.get(("flow", "goods_vat_rate")), facts.get(("flow", "export_refund_rate"))
    if app is None or ref is None:
        if ch.missing(*[k for k, v in (("flow.goods_vat_rate", app), ("flow.export_refund_rate", ref)) if v is None]):
            return 0.0
        app = P["cn.vat.law.rate_goods"] if app is None else app
        ref = 0.0 if ref is None else ref
    gap = max(0.0, float(app) - float(ref))
    if not facts.get(("flow", "trading_resale")):
        return gap
    k = facts.get(("flow", "purchase_price"))
    if k is None:
        return 0.0 if ch.missing(*(facts.get(("_needs", "flow.cost_basis")) or ("flow.purchase_price",))) else gap
    return gap * float(k) / float(amount)


def customs_value(facts, P, ch):
    """关税法 第二十四条: the duty value is the transaction price (the case's price, carriage and insurance to the place of
    import included) — between related parties only when the relationship did not affect it (第二十四条第三款第四项):
    below their arm's-length price that is the authority's judgement, the arm's-length price at the other end. As a
    share of the price."""
    alv, amount = facts.get(("flow", "arms_length_value")), facts.get(("flow", "amount"))
    if alv is None or not amount or float(alv) <= float(amount) or not facts.get(("flow", "parties_linked")):
        return 1.0
    return 1.0 if ch.judged("flow.customs_price_affected") else float(alv) / float(amount)


def cn_import_duty(facts, P, ch):
    """口径 D43. 关税法 第二十三条: duty at the tariff rate (the case's, from the 税则) on the duty value, paid by the
    consignee (第三条) — the buyer. A rate not given: none here; the engine asks it of a group importer."""
    rate = facts.get(("flow", "import_duty_rate"))
    return 0.0 if rate is None else float(rate) * customs_value(facts, P, ch)


def cn_export_duty(facts, P, ch):
    """口径 D43. 关税法 第三条、第二十三条: export duty, where the tariff lists the goods, paid by the consignor — the
    seller — on the export price. A rate not given: none here; the engine asks it of a group exporter."""
    rate = facts.get(("flow", "export_duty_rate"))
    return 0.0 if rate is None else float(rate)


def cn_import_vat(facts, P, ch):
    """口径 D43. 增值税法 第十四条第三款: import VAT on the composite value — the duty value plus the duty (consumption tax
    not modelled) — at the applicable rate (第十条; unknown: 13% at the other end, 9% at the favourable one)."""
    app = facts.get(("flow", "goods_vat_rate"))
    if app is None:
        app = P["cn.vat.law.rate_goods_reduced"] if ch.missing("flow.goods_vat_rate") else P["cn.vat.law.rate_goods"]
    duty = float(facts.get(("flow", "import_duty_rate")) or 0.0)
    return float(app) * customs_value(facts, P, ch) * (1.0 + duty / 100.0)


def cn_import_vat_credit(facts, P, ch):
    """增值税法 第十六条: a general taxpayer credits the import VAT it paid (its input tax) — the same amount, negative."""
    return cn_import_vat(facts, P, ch)


cn_import_vat_credit.credit = True


# ---- 口径 D48: a sale of land or a building in the Mainland


def _inclusive(facts, ch):
    """Whether the price includes the VAT — a fact of the contract (口径 D23); unknown: the favourable reading."""
    inc = facts.get(("flow", "price_includes_vat"))
    return bool(ch.missing("flow.price_includes_vat")) if inc is None else bool(inc)


def cn_property_vat(facts, P, ch):
    """增值税法 第十条第二项: 9%; a VAT-inclusive price carries r / (1 + r). 公告2026年第10号 三（二）4-5 (to 2027-12-31): a
    general taxpayer may take the 5% simplified method for land or a building it acquired before 2016-05-01, and then,
    unless it built it itself, deduct the purchase price from the VAT-inclusive price (四（八）); a small-scale taxpayer
    pays 3% (第十一条) on the same difference. Unknown election, status or purchase price: the favourable end and the
    other. Returns (rate on the price, taken out of a VAT-inclusive price)."""
    amount = float(facts.get(("flow", "amount")) or 0.0)
    if amount <= 0:
        return 0.0
    inc = _inclusive(facts, ch)
    gen = lambda r: 100.0 * (r / 100.0) / (1.0 + r / 100.0) if inc else r

    def simplified(r):
        gross = amount if inc else amount * (1.0 + r / 100.0)
        built, bought = facts.get(("flow", "self_built")), facts.get(("flow", "acquisition_price"))
        if built is None or (not built and bought is None):
            keys = [k for k, v in (("flow.self_built", built), ("flow.acquisition_price", bought)) if v is None]
            ded = gross if ch.missing(*keys) else 0.0
        else:
            ded = 0.0 if built else float(bought)
        return 100.0 * max(0.0, gross - ded) / (1.0 + r / 100.0) * (r / 100.0) / amount

    general = facts.get(("payee", "vat_general_taxpayer"))
    small = simplified(P["cn.vat.law.simplified_rate"])
    full = gen(P["cn.vat.law.rate_property"])
    on = facts.get(("flow", "date_of_payment"))
    old = facts.get(("flow", "acquired_before_2016_05"))
    window = on is not None and on <= date.fromisoformat(str(P["cn.vat.property_simplified_until"]))
    best = full
    elected = facts.get(("flow", "vat_simplified_elected"))
    if window and old is not False and elected is not False:
        five = simplified(P["cn.vat.property_simplified_rate"])
        if old and elected:
            best = five
        else:                                             # the acquisition date or the election open: either end
            keys = [k for k, v in (("flow.acquired_on", old), ("flow.vat_simplified_elected", elected)) if v is None]
            best = min(full, five) if ch.missing(*keys) else max(full, five)
    if general is None:
        best = min(best, small) if ch.missing("payee.vat_general_taxpayer") else max(best, small)
    elif general is False:
        best = small
    return best, inc


def cn_rent_vat(facts, P, ch):
    """口径 D49. 增值税法 第十条第二项: 9% on the rent (r / (1 + r) of a VAT-inclusive one); 公告2026年第10号 三（二）3 (to
    2027-12-31): a general taxpayer may take 5% for land or a building acquired before 2016-05-01; a small-scale
    taxpayer 3% (第十一条; its 1% reduction excludes the lease of immovable property, 三（三）6). (rate, inclusive)."""
    amount = float(facts.get(("flow", "amount")) or 0.0)
    if amount <= 0:
        return 0.0
    inc = _inclusive(facts, ch)
    at = lambda r: 100.0 * (r / 100.0) / (1.0 + r / 100.0) if inc else r
    full, five, small = at(P["cn.vat.rent_rate"]), at(P["cn.vat.property_simplified_rate"]), at(P["cn.vat.law.simplified_rate"])
    general = facts.get(("payee", "vat_general_taxpayer"))
    on, old, elected = facts.get(("flow", "date_of_payment")), facts.get(("flow", "acquired_before_2016_05")), facts.get(("flow", "vat_simplified_elected"))
    best = full
    if on is not None and on <= date.fromisoformat(str(P["cn.vat.property_simplified_until"])) and old is not False and elected is not False:
        if old and elected:
            best = five
        else:
            keys = [k for k, v in (("flow.acquired_on", old), ("flow.vat_simplified_elected", elected)) if v is None]
            best = five if ch.missing(*keys) else full
    if general is None:
        best = min(best, small) if ch.missing("payee.vat_general_taxpayer") else max(best, small)
    elif general is False:
        best = small
    return best, inc


def cn_property_tax(facts, P, ch, items):
    """口径 D49. 房产税暂行条例 第三条、第四条: 12% of the rent; the rent net of the VAT (财税〔2016〕43号 第二条)."""
    return P["cn.property_tax.rent_rate"] * (1.0 - _vat_out(items))


def _vat_out(items):
    """The seller's output VAT on the flow taken out of a VAT-inclusive price, as a share of the price."""
    return sum(it.rate * it.base_share for it in items if it.jur == "CN" and it.levy == "vat" and it.borne_by == "payee"
               and not it.deduction and it.vat_inclusive) / 100.0


def _surcharge(facts, P, ch, items, rate_of):
    """公告2021年第28号 第一条: the VAT actually paid — each Mainland VAT item, with its bearer and sign (an input credit
    lowers the VAT its bearer pays) — but not import VAT, the export refund's, or a foreign seller's VAT on services or
    intangibles (城市维护建设税法 第三条)."""
    foreign_seller = facts.get(("payee", "payee_in_source_jur")) is False      # the Mainland is the source: a foreign seller
    income = facts.get(("flow", "income"))
    out = []
    for it in items:
        if it.jur != "CN" or it.levy != "vat":
            continue
        if any(c.startswith(("cn.vat.import", "cn.vat.export")) for c in it.cites):
            continue
        if it.borne_by == "payee" and not it.deduction and foreign_seller and income not in ("GOODS", "PROPERTY_TRANSFER"):
            continue
        rate = rate_of(it)
        if rate:
            out.append((it.rate * it.base_share * rate / 100.0, it.borne_by, it.deduction))
    return out


def cn_ucmt(facts, P, ch, items):
    """城市维护建设税法 第四条: 7% where the taxpayer is in a city district, 5% in a county town or town, 1% elsewhere
    (ucmt_location urban / county / other); unknown: 1% on a payment, 7% on a credit at the favourable end."""
    rates = {"urban": P["cn.ucmt.rate_urban"], "county": P["cn.ucmt.rate_county"], "other": P["cn.ucmt.rate_other"]}

    def rate_of(it):
        elem = "payer" if it.borne_by == "payer" else "payee"
        loc = facts.get((elem, "ucmt_location"))
        if loc is None:
            fav = ch.missing(elem + ".ucmt_location")
            return min(rates.values()) if fav != it.deduction else max(rates.values())
        if loc not in rates:
            raise ValueError("ucmt_location %r is outside the model (urban, county, other)" % loc)
        return rates[loc]
    return _surcharge(facts, P, ch, items, rate_of)


def cn_local_edu(facts, P, ch, items):
    """财综〔2010〕98号 第二条: 2% of the VAT actually paid; the base is the city-maintenance tax's (公告2021年第28号 第二条)."""
    return _surcharge(facts, P, ch, items, lambda it: P["cn.local_edu.rate"])


def lat_years(acquired, sold, P):
    """国税函〔2010〕220号 第七条: from the purchase invoice to the sale invoice, every full 12 months a year; beyond one year a
    remaining period of more than 6 months counts as a year."""
    if acquired is None or sold is None:
        return None
    full = int(P["cn.lat.invoice_year"])
    m = (sold.year - acquired.year) * 12 + sold.month - acquired.month - (1 if sold.day < acquired.day else 0)
    years = m // full
    if years >= 1 and sold > add_months(acquired, full * years + full // 2):
        years += 1
    return years


def cn_lat(facts, P, ch, items):
    """土地增值税暂行条例 第四条、第六条、第七条; 细则 第七条、第十条. The revenue net of the VAT (公告2016年第70号 第一条) less the
    deductions: an old building's appraised value with the land price (第六条（一）、（三）; 细则 第七条（四）;
    lat_appraised_value), else the purchase invoice uplifted 5% a year (财税〔2006〕21号 第二条; 公告2016年第70号 第六条;
    lat_years) with the deed tax paid on it (21号: deductible, not uplifted); and the taxes on the transfer — the
    surcharges and the stamp duty (细则 第七条（五）; 70号 第三条; 公告2026年第3号 第五条). Four bands with quick deductions
    (细则 第十条). A developer's sale is outside the model. Unknown deductions: none payable at the favourable end."""
    amount = float(facts.get(("flow", "amount")) or 0.0)
    if amount <= 0:
        return 0.0
    if facts.get(("payee", "property_developer")):
        raise ValueError("a property developer's sale is outside the model (口径 D48: 土地增值税 开发成本、加计扣除)")
    revenue = amount * (1.0 - _vat_out(items))
    taxes = sum(it.effective for it in items if it.jur == "CN" and it.levy in ("surcharge", "stamp") and it.borne_by == "payee") / 100.0 * amount
    appraised = facts.get(("flow", "lat_appraised_value"))
    if appraised is not None:
        base = float(appraised)
    else:
        bought, acq = facts.get(("flow", "acquisition_price")), facts.get(("flow", "acquired_on"))
        years = lat_years(acq, facts.get(("flow", "date_of_payment")), P)
        if bought is None or years is None:
            keys = [k for k, v in (("flow.lat_appraised_value", appraised), ("flow.acquisition_price", bought), ("flow.acquired_on", acq))
                    if v is None]
            if ch.missing(*keys):
                return 0.0
            bought, years = (0.0 if bought is None else bought), (0 if years is None else years)
        base = float(bought) * (1.0 + P["cn.lat.invoice_uplift"] / 100.0 * years)
        deed = facts.get(("flow", "deed_paid_on_acquisition"))
        if deed is None:                                  # the deed tax certificate: at most 5% of the price paid, at least none
            deed = float(bought) * P["cn.deed.rate_max"] / 100.0 if ch.missing("flow.deed_paid_on_acquisition") else 0.0
        taxes += float(deed)
    ded = base + taxes
    added = revenue - ded
    if added <= 0:
        return 0.0
    ratio = 100.0 * added / ded if ded > 0 else float("inf")
    if ratio <= P["cn.lat.band_1"]:
        tax = added * P["cn.lat.rate_1"] / 100.0
    elif ratio <= P["cn.lat.band_2"]:
        tax = added * P["cn.lat.rate_2"] / 100.0 - ded * P["cn.lat.quick_2"] / 100.0
    elif ratio <= P["cn.lat.band_3"]:
        tax = added * P["cn.lat.rate_3"] / 100.0 - ded * P["cn.lat.quick_3"] / 100.0
    else:
        tax = added * P["cn.lat.rate_4"] / 100.0 - ded * P["cn.lat.quick_4"] / 100.0
    return 100.0 * tax / amount


def cn_deed(facts, P, ch, items):
    """契税法 第三条: 3% to 5%, the province's rate (deed_tax_rate; unknown: the range's ends); 第四条（一）: on the
    contract price, net of the VAT (财税〔2016〕43号 第一条)."""
    rate = facts.get(("flow", "deed_tax_rate"))
    if rate is None:
        rate = P["cn.deed.rate_min"] if ch.missing("flow.deed_tax_rate") else P["cn.deed.rate_max"]
    elif not P["cn.deed.rate_min"] <= float(rate) <= P["cn.deed.rate_max"]:
        raise ValueError("deed_tax_rate %s outside 契税法 第三条 (3%%-5%%)" % rate)
    return float(rate) * (1.0 - _vat_out(items))


def cn_property_resident_share(facts, P, ch, items):
    """口径 D48. A resident's gain on land or a building: the price net of its output VAT (口径 D29), less its basis and
    the taxes on the sale it bears — surcharges, 土地增值税, stamp duty, wherever levied (实施条例 第三十一条)."""
    g = gain_share(facts, P, ch)
    taxes = sum(it.effective for it in items if it.levy in ("surcharge", "lat", "stamp") and it.borne_by == "payee") / 100.0
    return max(0.0, g - _vat_out(items) - taxes)


cn_property_resident_share.takes_items = True


def tp_interest(rule, facts, P, deadlines, tax):
    """公告2017年第6号 第四十四条: interest on a special tax adjustment from 1 June of the year after the tax year to the
    day the tax is paid, at the PBOC benchmark plus five points (benchmark only when documentation was provided) — the
    payer's documentation for a deduction cut, the payee's for its income raised (口径 D41)."""
    adj, paid_on, base = facts.get(("flow", "tp_adjustment_tax")), facts.get(("flow", "tp_adjustment_paid_on")), facts.get(("flow", "pboc_benchmark_rate"))
    if adj is None or paid_on is None or base is None:
        return None
    year = facts[("flow", "date_of_payment")].year
    start = date(year + 1, 6, 1)
    days = max(0, (paid_on - start).days)
    side = "payee" if rule.scope.side == "residence" else "payer"
    spread = 0.0 if facts.get((side, "tp_documentation_provided")) else P["cn.tp.interest_spread"]
    return round(float(adj) * (float(base) + spread) / 100.0 * days / 365.0, 2)


GAIN = ("cn.law.eit#16",)

def cn_goods_share(facts, P, ch, items=()):
    """口径 D42: the seller's profit on goods for the Mainland, the price at arm's length (口径 D41)."""
    return goods_share(facts, P, ch, items, "CN", "cn_related", False)


cn_goods_share.takes_items = True
GOODS_READS = ("flow.cost_basis", "flow.arms_length_value", "flow.arms_length_low", "flow.operating_costs", "flow.trading_resale",
                 "flow.purchase_price", "flow.purchase_arms_length_value", "flow.purchase_arms_length_low",
                 "flow.purchase_arms_length_max", "flow.purchase_supplier_jur", "flow.purchase_treaty", "flow.purchase_cn_related",
                 "flow.purchase_hk_associated", "flow.purchase_sg_related", "flow.corresponding_adjustment_granted", "flow.cn_related")

REGISTRY = {
    "cn.gain.base": ("BASE", cn_gain_share, GAIN),
    "cn.goods.base": ("BASE", cn_goods_share, ("cn.reg.eit#14", "cn.reg.eit#29", "cn.law.eit#41")),   # 口径 D42
    "cn.goods.nonresident.base": ("BASE", cn_goods_share, ("cn.reg.eit#14", "cn.reg.eit#29", "cn.law.eit#41")),
    "cn.resident.ip.charge": ("CHARGE", cn_gain_share, ("cn.law.eit#16", "cn.reg.eit#74")),             # 口径 D22
    "cn.ip.wht": ("CHARGE", cn_gain_share, ("cn.law.eit#19",)),
    "cn.resident.ip.tech": ("BASE", tech_transfer_share, ("cn.reg.eit#90",)),
    "cn.ip.amortization.horizon": ("DEDUCT_BASE", amortization_share, ("cn.reg.eit#67",)),
    "cn.reorg.asset_transfer.basis": ("DEDUCT_BASE", transfer_basis_share, ("cn.sta.2015-40#i3",)),     # 口径 D28
    "cn.indirect.gain.base": ("BASE", cn_gain_share, GAIN),
    "cn.resident.gain.base": ("BASE", cn_gain_share, GAIN),
    "cn.reorg.special_resident": ("BASE", reorg_spread_share, ("cn.cs.2009-59#i8",)),             # 口径 D18
    "cn.service.deemed_profit": ("BASE", deemed_profit_share, ("cn.gsf.2010-19#5", "cn.reg.eit#7")),
    "cn.deduct.interest.benchmark": ("DEDUCT_BASE", benchmark_share, ("cn.reg.eit#38",)),
    "cn.tp.deduction_cap": ("DEDUCT_BASE", arms_length_share, ("cn.law.eit#41",)),
    "cn.tp.income_uplift": ("BASE", cn_uplift, ("cn.law.eit#41", "cn.sta.2017-06#25", "cn.sta.2016-42#i2")),        # 口径 D40, D41
    "cn.vat.export.goods": ("VAT", cn_export_vat, ("cn.law.vat#10", "cn.cs.2026-11#i3", "cn.cs.2026-11#i4", "cn.cs.2026-11#i5")),  # 口径 D43
    "cn.customs.export": ("CUSTOMS", cn_export_duty, ("cn.law.tariff#3", "cn.law.tariff#23")),
    "cn.customs.import": ("CUSTOMS", cn_import_duty, ("cn.law.tariff#3", "cn.law.tariff#23", "cn.law.tariff#24")),
    "cn.vat.import.goods": ("VAT", cn_import_vat, ("cn.law.vat#14", "cn.law.vat#10", "cn.law.tariff#24")),
    "cn.vat.import.goods.credit": ("VAT", cn_import_vat_credit, ("cn.law.vat#16",)),
    "cn.tp.corresponding": ("DEDUCT_BASE", cn_corresponding, ("treaty.cn-hk.2006.zh#9.2", "treaty.cn-sg.2007.mli.zh#9.2")),
    "cn.vat.law.property": ("VAT", cn_property_vat, ("cn.law.vat#10", "cn.law.vat#11", "cn.cs.2026-10#i3", "cn.cs.2026-10#i4")),   # 口径 D48
    "cn.surcharge.ucmt": ("SURCHARGE", cn_ucmt, ("cn.law.ucmt#2", "cn.law.ucmt#3", "cn.law.ucmt#4", "cn.cs.2021-28#i1")),
    "cn.surcharge.local_edu": ("SURCHARGE", cn_local_edu, ("cn.cz.2010-98#i2", "cn.cs.2021-28#i2")),
    "cn.lat.charge": ("LAT", cn_lat, ("cn.reg.lat#4", "cn.reg.lat#6", "cn.reg.lat#7", "cn.reg.lat.rules#7", "cn.reg.lat.rules#10",
                                      "cn.cs.2006-21#i2", "cn.gsh.2010-220#i7", "cn.sta.2016-70#i1", "cn.sta.2016-70#i3",
                                      "cn.sta.2016-70#i6", "cn.sta.2026-03#i5")),
    "cn.deed.charge": ("DEED", cn_deed, ("cn.law.deed#3", "cn.law.deed#4", "cn.cs.2016-43#i1")),
    "cn.property.resident.base": ("BASE", cn_property_resident_share, ("cn.reg.eit#31", "cn.reg.eit#16")),
    "cn.vat.law.rent": ("VAT", cn_rent_vat, ("cn.law.vat#10", "cn.law.vat#11", "cn.cs.2026-10#i3")),            # 口径 D49
    "cn.property_tax.rent": ("PROPERTY_TAX", cn_property_tax, ("cn.reg.property#3", "cn.reg.property#4", "cn.cs.2016-43#i2")),
    "cn.rent.base": ("BASE", profit_share, ("cn.law.eit#8",)),
    "cn.review": ("DEADLINE", ("review", _review), ("cn.law.ar#20",)),
    "actual payment or date payable": ("DEADLINE", ("remit", _remit), ("cn.sta.2017-37#i4", "cn.sta.2017-37#i7")),
    "cn.refund": ("DEADLINE", ("refund", _refund), ("cn.law.tca#51",)),
    "cn.reinvest.recapture.due": ("DEADLINE", ("recapture", _recapture), ("cn.cs.2018-102#i6",)),                  # 口径 D46
    "cn-hk.map": ("DEADLINE", ("map", lambda f, P, d: _map(f, P, d, "cn-hk.map.limit")), ("treaty.cn-hk.2006.zh#23.1",)),
    "cn-sg.map": ("DEADLINE", ("map", lambda f, P, d: _map(f, P, d, "cn-sg.map.limit")), ("treaty.cn-sg.2007.zh#24.1",)),
    "cn.tp.local_file": ("DEADLINE", ("tp_local_file", _june_30_next_year), ("cn.sta.2016-42#i19",)),
    "cn.wht.late_surcharge": ("PENALTY", surcharge, ("cn.law.tca#32",)),
    "cn.tp.adjustment_interest": ("PENALTY", tp_interest, ("cn.sta.2017-06#44", "cn.reg.eit#122")),
    "cn.tp.adjustment_interest.income": ("PENALTY", tp_interest, ("cn.sta.2017-06#44", "cn.reg.eit#122")),          # 口径 D41
}

# facts each rule reads besides its parameters and condition; compile.py adds them to RuleObj.reads
READS = {
    "cn.goods.base": GOODS_READS, "cn.goods.nonresident.base": GOODS_READS,
    "cn.review": ("flow.assessment_notice_on",),
    "cn.wht.remit": ("flow.date_of_payment", "flow.payable_on"),
    "cn-hk.map": ("flow.first_notification_on",),
    "cn-sg.map": ("flow.first_notification_on",),
    "cn.wht.late_surcharge": ("flow.remitted_on",),
    "cn.refund": ("flow.tax_paid_on",),
    "cn.reinvest.recapture.due": ("flow.reinvestment_withdrawn_on",),
    "cn.gain.base": ("flow.consideration", "flow.cost_basis", "flow.cn_cost_basis", "flow.arms_length_value", "flow.cn_related"),
    "cn.resident.ip.charge": ("flow.consideration", "flow.cost_basis"), "cn.ip.wht": ("flow.consideration", "flow.cost_basis"),
    "cn.resident.ip.tech": ("flow.consideration", "flow.cost_basis", "flow.cny_rate", "flow.currency"),
    "cn.ip.amortization.horizon": ("flow.ip_horizon_years", "flow.ip_useful_life_years"),
    "cn.reorg.asset_transfer.basis": ("flow.consideration", "flow.cost_basis"),
    "cn.vat.law.service": ("flow.price_includes_vat",), "cn.vat.law.royalty": ("flow.price_includes_vat",),
    "cn.vat.law.lease": ("flow.price_includes_vat",), "cn.vat.law.ip": ("flow.price_includes_vat",),
    "cn.vat.law.ip_sale": ("flow.price_includes_vat",),
    "cn.vat.law.interest": ("flow.price_includes_vat",), "cn.vat.law.interest_received": ("flow.price_includes_vat",),
    "cn.indirect.gain.base": ("flow.consideration", "flow.cost_basis", "flow.cn_cost_basis", "flow.arms_length_value",
                              "flow.cn_related"),
    "cn.resident.gain.base": ("flow.consideration", "flow.cost_basis", "flow.cn_cost_basis", "flow.arms_length_value",
                              "flow.cn_related"),
    "cn.reorg.special_resident": ("flow.consideration", "flow.cost_basis", "flow.cn_cost_basis", "flow.reorg_horizon_years",
                                  "flow.arms_length_value", "flow.cn_related"),
    "cn.service.deemed_profit": ("flow.service_kind", "flow.service_onshore_share"),
    "cn.ftc.dividend_indirect": ("flow.underlying_tax_share",),
    "cn.deduct.interest.benchmark": ("flow.interest_rate", "flow.benchmark_rate"),
    "cn.tp.adjustment_interest": ("flow.tp_adjustment_tax", "flow.tp_adjustment_paid_on", "flow.pboc_benchmark_rate", "payer.tp_documentation_provided"),
    "cn.tp.local_file": ("payer.related_party_volume",),
    "cn.tp.deduction_cap": ("flow.arms_length_max",),
    "cn.tp.income_uplift": ("flow.arms_length_value", "flow.cn_related"),
    "cn.vat.export.goods": ("flow.goods_vat_rate", "flow.export_refund_rate", "flow.trading_resale", "flow.purchase_price"),
    "cn.customs.export": ("flow.export_duty_rate",),
    "cn.customs.import": ("flow.import_duty_rate", "flow.arms_length_value", "flow.parties_linked"),
    "cn.vat.import.goods": ("flow.goods_vat_rate", "flow.import_duty_rate", "flow.arms_length_value", "flow.parties_linked"),
    "cn.vat.import.goods.credit": ("flow.goods_vat_rate", "flow.import_duty_rate", "flow.arms_length_value", "flow.parties_linked"),
    "cn.tp.corresponding": ("flow.parties_treaty", "flow.corresponding_adjustment_granted"),
    "cn.vat.law.property": ("flow.price_includes_vat", "flow.self_built", "flow.acquisition_price", "flow.acquired_on",
                            "flow.vat_simplified_elected", "payee.vat_general_taxpayer"),       # 口径 D48
    "cn.surcharge.ucmt": ("payer.ucmt_location", "payee.ucmt_location"),
    "cn.lat.charge": ("flow.lat_appraised_value", "flow.acquisition_price", "flow.acquired_on", "flow.deed_paid_on_acquisition",
                      "payee.property_developer"),
    "cn.deed.charge": ("flow.deed_tax_rate",),
    "cn.vat.law.rent": ("flow.price_includes_vat", "flow.acquired_on", "flow.vat_simplified_elected", "payee.vat_general_taxpayer"),
    "cn.rent.base": ("flow.profit_margin",),
    "cn.property.resident.base": ("flow.consideration", "flow.cost_basis"),
    "cn.tp.adjustment_interest.income": ("flow.tp_adjustment_tax", "flow.tp_adjustment_paid_on", "flow.pboc_benchmark_rate",
                                         "payee.tp_documentation_provided"),
}
