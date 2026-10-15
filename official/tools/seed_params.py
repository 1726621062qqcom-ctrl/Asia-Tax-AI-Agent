"""Write official/params.csv. Every row was read from the clause text; `quote` must occur verbatim in the clause."""
import csv
import io
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
ROOT = Path(r"C:/Coding/Projects/TUM/project_study_self/official")
FIELDS = ["param_id", "scope", "income", "topic", "name", "value", "unit", "cite_id",
          "effective_from", "effective_to", "quote", "status", "cross_check", "note"]
R = []
XC_HK = "hk.ird.dta-rates#all, Mainland row: dividends 5/10, interest 7, royalties 5/7, consistent"
XC_2008 = "; cn.sta.2008-112 附件: Hong Kong and Singapore are listed under “5%（直接拥有支付股息公司至少25%股份情况下）”, 10% below 25%, consistent; cn.gsf.2010-75#10 interpretation of para. 2: at least 25% of capital 5%, otherwise 10%, consistent (China–Singapore only)"
XC_HK = XC_HK + XC_2008.split("; cn.gsf")[0]


def p(pid, scope, income, topic, name, value, unit, cite, eff, quote, note="", to="", xc=""):
    R.append(dict(param_id=pid, scope=scope, income=income, topic=topic, name=name, value=value, unit=unit,
                  cite_id=cite, effective_from=eff, effective_to=to, quote=quote, status="extracted",
                  cross_check=xc, note=note))


HK, SG = "pair(CN,HK)", "pair(CN,SG)"
A, AS = "treaty.cn-hk.2006.zh", "treaty.cn-sg.2007.zh"
n26 = "the Mainland application start date follows from 《安排》 art. 26; the effective date 2006-12-08 is in cn.sta.treaty-list and hk.ird.dta-mainland"

# ---- Mainland - Hong Kong
p("cn-hk.div.cap_qualified", HK, "DIVIDEND", "rate", "cap_qualified", 5, "%", A + "#10.2", "2007-01-01",
  "如果受益所有人是直接拥有支付股息公司至少25%资本的公司，为股息总额的5%", n26, xc=XC_HK)
p("cn-hk.div.ratio_min", HK, "DIVIDEND", "condition", "direct_ratio_min", 25, "%", A + "#10.2", "2007-01-01",
  "直接拥有支付股息公司至少25%资本的公司", n26)
p("cn-hk.div.cap_other", HK, "DIVIDEND", "rate", "cap_other", 10, "%", A + "#10.2", "2007-01-01",
  "在其它情况下，为股息总额的10%", n26, xc=XC_HK)
p("cn-hk.int.cap", HK, "INTEREST", "rate", "cap", 7, "%", A + "#11.2", "2007-01-01",
  "则所征税款不应超过利息总额的7%", n26, xc=XC_HK)
p("cn-hk.roy.cap", HK, "ROYALTY", "rate", "cap", 7, "%", A + "#12.2", "2007-01-01",
  "则所征税款不应超过特许权使用费总额的7%", n26, xc=XC_HK)
p("cn-hk.roy.cap_aircraft_ship_lease", HK, "ROYALTY", "rate", "cap_aircraft_ship_lease", 5, "%",
  "treaty.cn-hk.2006.p4.zh#2", "2015-12-29",
  "对飞机和船舶租赁业务支付的特许权使用费，所征税款不应超过特许权使用费总额的5%",
  "effective and application dates: see cn.sta.2016-12", xc="hk.ird.dta-rates.notes#all: 5% from 29.12.2015, consistent")
p("cn-hk.gain.immovable_ratio_over", HK, "SHARE_TRANSFER", "condition", "immovable_value_ratio_over", 50, "%",
  "treaty.cn-hk.2006.p5.zh#4", "2020-01-01",
  "超过50%的价值直接或间接来自于第六条所定义的位于另一方的不动产", "Fifth Protocol replaces art. 13 para. 4; effective and application dates: see cn.sta.2019-51")
p("cn-hk.gain.immovable_lookback", HK, "SHARE_TRANSFER", "condition", "immovable_lookback", 3, "years",
  "treaty.cn-hk.2006.p5.zh#4", "2020-01-01", "在转让行为前三年内的任一时间")
p("cn-hk.gain.share_ratio_min", HK, "SHARE_TRANSFER", "condition", "participation_ratio_min", 25, "%",
  "treaty.cn-hk.2006.p2.zh#5", "2008-06-11", "曾经直接或间接参与该公司至少百分之二十五的资", "Second Protocol replaces art. 13 para. 5")
p("cn-hk.gain.share_lookback", HK, "SHARE_TRANSFER", "condition", "participation_lookback", 12, "months",
  "treaty.cn-hk.2006.p2.zh#5", "2008-06-11", "如果该收益人在转让行为前的十二个月内")
p("cn-hk.gain.listed_shares_residence_only", HK, "SHARE_TRANSFER", "condition", "listed_shares_residence_only",
  1, "bool", "treaty.cn-hk.2006.p4.zh#3", "2015-12-29",
  "一方居民转让在被认可的证券交易所上市的另一方居民公司股票取得的收益，应仅在转让者为其居民的一方征税",
  "limited to shares bought and sold on the same stock exchange")
p("cn-hk.ppt", HK, "ALL", "anti_abuse", "principal_purpose_test", 1, "bool", "treaty.cn-hk.2006.p5.zh#6",
  "2020-01-01", "主要目的之一是获得该优惠，则不得就相关所得给予该优惠", "needs discretion, maps to U(DISCRETION)")
p("cn-hk.map.limit", HK, "ALL", "limit", "map_years", 3, "years", A + "#23.1", "2007-01-01", "三年内提出")

# ---- China - Singapore
n28 = "effective and application dates: see cn.gsf.2007-116"
p("cn-sg.div.cap_qualified", SG, "DIVIDEND", "rate", "cap_qualified", 5, "%", AS + "#10.2", "2008-01-01",
  "不应超过股息总额的百分之五", n28, xc=XC_2008.lstrip("; "))
p("cn-sg.div.ratio_min", SG, "DIVIDEND", "condition", "direct_ratio_min", 25, "%", AS + "#10.2", "2008-01-01",
  "直接拥有支付股息公司至少百分之二十五资本", "the beneficial owner must be a company, partnerships excluded")
p("cn-sg.div.cap_other", SG, "DIVIDEND", "rate", "cap_other", 10, "%", AS + "#10.2", "2008-01-01",
  "在其他情况下，不应超过股息总额的百分之十", xc=XC_2008.lstrip("; "))
p("cn-sg.int.cap_bank", SG, "INTEREST", "rate", "cap_bank_or_financial_institution", 7, "%", AS + "#11.2",
  "2008-01-01", "在该项利息是由银行或金融机构取得的情况下，不应超过利息总额的百分之七")
p("cn-sg.int.cap_other", SG, "INTEREST", "rate", "cap_other", 10, "%", AS + "#11.2", "2008-01-01",
  "在其他情况下，不应超过利息总额的百分之十")
p("cn-sg.roy.cap", SG, "ROYALTY", "rate", "cap", 10, "%", AS + "#12.2", "2008-01-01",
  "则所征税款不应超过特许权使用费总额的百分之十")
p("cn-sg.roy.equipment_base", SG, "ROYALTY", "rate", "equipment_tax_base_share", 60, "%", AS + "#protocol",
  "2008-01-01", "按支付特许权使用费总额的百分之六十确定税基", "only royalties for the use of industrial, commercial or scientific equipment")
p("cn-sg.gain.immovable_ratio_over", SG, "SHARE_TRANSFER", "condition", "immovable_value_ratio_over", 50, "%",
  AS + "#13.4", "2008-01-01", "如果股份价值的百分之五十以上直接或间接由位于缔约国另一方的不动产构成")
p("cn-sg.gain.share_ratio_min", SG, "SHARE_TRANSFER", "condition", "participation_ratio_min", 25, "%",
  AS + "#13.5", "2008-01-01", "该公司或其他法人至少百分之二十五的资本")
p("cn-sg.gain.share_lookback", SG, "SHARE_TRANSFER", "condition", "participation_lookback", 12, "months",
  AS + "#13.5", "2008-01-01", "如果该收益人在转让行为前的十二个月内")
p("cn-sg.map.limit", SG, "ALL", "limit", "map_years", 3, "years", AS + "#24.1", "2008-01-01", "三年内提出")
p("cn-sg.mli.in_operation", SG, "ALL", "procedure", "mli_modifications_in_operation", 1, "bool",
  "treaty.cn-sg.mli#p1", "2022-09-01", "comes into operation on 1 September 2022",
  "MLI modifications to the China–Singapore treaty; the specific provisions are in the Order's schedule, not yet taken as parameters one by one")
p("cn-sg.ppt", SG, "ALL", "anti_abuse", "principal_purpose_test", 1, "bool", "treaty.cn-sg.2007.mli.zh#27", "2023-01-01",
  "可以合理地认定就某项所得获取本协定某项优惠是直接或间接 产生该优惠的安排或交易的主要目的之一，则不应对该项所得给 予该优惠",
  "MLI art. 7 para. 1 in the synthesised text replaces treaty art. 10 para. 6, art. 11 para. 8 and art. 12 para. 7; overall judgement, maps to one U(DISCRETION); effective date 2023-01-01 per superseded.csv (withholding taxes from 1 January of the calendar year after the MLI took effect for both parties)")

# ---- Hong Kong - Singapore
p("hk-sg.no_comprehensive_dta", "pair(HK,SG)", "ALL", "condition", "comprehensive_dta", 0, "bool",
  "treaty.hk-sg.2003#1", "", "", "only a limited agreement on shipping and air transport income; Singapore is not on Hong Kong's list of comprehensive agreements, see hk.ird.dta-list")

# ---- Mainland domestic
p("cn.div.holding_months_min", "CN", "DIVIDEND", "condition", "holding_months_min", 12, "months",
  "cn.gsh.2009-81#i3", "", "在取得股息前连续12个月以内任何时候均符合税收协定规定的比例")
p("cn.bo.onpay_ratio", "CN", "ALL", "anti_abuse", "onpay_ratio_adverse_from", 50, "%", "cn.sta.2018-09#i2", "2018-04-01",
  "申请人有义务在收到所得的12个月内将所得的50%以上支付给第三国（地区）居民", "one of the adverse factors, overall analysis, needs discretion")
p("cn.bo.onpay_window", "CN", "ALL", "anti_abuse", "onpay_window", 12, "months", "cn.sta.2018-09#i2", "2018-04-01",
  "在收到所得的12个月内")
p("cn.bo.safe_harbour", "CN", "DIVIDEND", "condition", "safe_harbour_holders",
  "government;listed_company;individual;wholly_owned_by_these", "enum", "cn.sta.2018-09#i4", "2018-04-01",
  "可不根据本公告第二条规定的因素进行综合分析，直接判定申请人具有“受益所有人”身份", "dividends only")
p("cn.treaty.claim_proc", "CN", "ALL", "procedure", "claim_proc", "SELF_ASSESS", "enum", "cn.sta.2019-35#3", "2020-01-01",
  "自行判断、申报享受、相关资料留存备查")
p("cn.treaty.refund_route", "CN", "ALL", "procedure", "refund_of_overpaid_tax", 1, "bool", "cn.sta.2019-35#10", "2020-01-01",
  "可在税收征管法规定期限内自行或通过扣缴义务人向主管税务机关要求退还多缴税款", "the time limit itself is in 税收征管法; parameter to be added once that law is in the library")
p("cn.treaty.refund_check_days", "CN", "ALL", "limit", "refund_verification_days", 30, "days",
  "cn.sta.2019-35#10", "2020-01-01", "30日内查实")

p("cn.eit.rate_nonresident_statutory", "CN", "ALL", "rate", "statutory_rate_non_resident", 20, "%", "cn.law.eit#4",
  "2008-01-01", "非居民企业取得本法第三条第三款规定的所得，适用税率为20％", "statutory rate; actually levied at the reduced rate under the 实施条例")
p("cn.wht.rate", "CN", "ALL", "rate", "withholding_rate_non_resident", 10, "%", "cn.reg.eit#91", "2008-01-01",
  "减按10%的税率征收企业所得税", "domestic withholding rate; the lower of this and the treaty cap applies")
p("cn.wht.base_gross", "CN", "DIVIDEND", "condition", "tax_base_is_gross", 1, "bool", "cn.law.eit#19", "2008-01-01",
  "股息、红利等权益性投资收益和利息、租金、特许权使用费所得，以收入全额为应纳税所得额", "also applies to interest and royalties")
p("cn.wht.base_gain", "CN", "SHARE_TRANSFER", "condition", "tax_base_is_gain", 1, "bool", "cn.law.eit#19",
  "2008-01-01", "转让财产所得，以收入全额减除财产净值后的余额为应纳税所得额")
p("cn.wht.at_source", "CN", "ALL", "procedure", "withheld_by_payer", 1, "bool", "cn.law.eit#37", "2008-01-01",
  "实行源泉扣缴，以支付人为扣缴义务人")
p("cn.wht.remit_days", "CN", "ALL", "limit", "withholding_remit_days", 7, "days", "cn.sta.2017-37#i7", "2017-12-01",
  "扣缴义务人应当自扣缴义务发生之日起7日内向扣缴义务人所在地主管税务机关申报和解缴代扣税款")
p("cn.refund.limit_years", "CN", "ALL", "limit", "refund_claim_years", 3, "years", "cn.law.tca#51", "",
  "纳税人自结算缴纳税款之日起三年内发现的，可以向税务机关要求退还多缴的税款", "time limit for ex_post")
p("cn.ftc.carryforward_years", "CN", "ALL", "limit", "credit_carryforward_years", 5, "years", "cn.law.eit#23",
  "2008-01-01", "超过抵免限额的部分，可以在以后五个年度内")
p("cn.ftc.indirect_ratio_min", "CN", "DIVIDEND", "condition", "indirect_credit_ratio_min", 20, "%",
  "cn.reg.eit#80", "2008-01-01", "直接控制，是指居民企业直接持有外国企业20%以上股份")
p("cn.ftc.indirect_tiers", "CN", "DIVIDEND", "condition", "indirect_credit_tiers", 5, "tiers", "cn.cs.2017-84#i2",
  "2017-01-01", "五层外国企业")
p("cn.ftc.method_lock_years", "CN", "ALL", "limit", "credit_method_lock_years", 5, "years", "cn.cs.2017-84#i1",
  "2017-01-01", "上述方式一经选择，5年内不得改变", "per country without per item, or neither per country nor per item")
p("cn.indirect.value_ratio", "CN", "SHARE_TRANSFER", "anti_abuse", "deemed_no_purpose_value_ratio", 75, "%",
  "cn.sta.2015-07#i4", "2015-02-03", "境外企业股权75%以上价值直接或间接来自于中国应税财产", "all four conditions must be met together")
p("cn.indirect.asset_or_income_ratio", "CN", "SHARE_TRANSFER", "anti_abuse", "deemed_no_purpose_asset_or_income_ratio",
  90, "%", "cn.sta.2015-07#i4", "2015-02-03", "境外企业资产总额（不含现金）的90%以上直接或间接由在中国境内的投资构成")
p("cn.indirect.listed_safe_harbour", "CN", "SHARE_TRANSFER", "condition", "listed_market_trade_excluded", 1, "bool",
  "cn.sta.2015-07#i5", "2015-02-03", "非居民企业在公开市场买入并卖出同一上市境外企业股权取得间接转让中国应税财产所得")
p("cn.indirect.reorg_ratio", "CN", "SHARE_TRANSFER", "condition", "intragroup_reorg_ratio_min", 80, "%",
  "cn.sta.2015-07#i6", "2015-02-03", "股权转让方直接或间接拥有股权受让方80%以上的股权", "100% when immovable property exceeds half")

# ---- Hong Kong domestic
p("hk.profits.rate_corp", "HK", "ALL", "rate", "profits_tax_rate_corporation", 16.5, "%", "hk.cap112.en#sch8B",
  "2018-04-01", "at the rate of 16.5% on any part of section 14 assessable profits over $2,000,000")
p("hk.profits.rate_corp_first_tier", "HK", "ALL", "rate", "profits_tax_rate_first_2m", 8.25, "%",
  "hk.cap112.en#sch8B", "2018-04-01", "at the rate of 8.25% on section 14 assessable profits up to $2,000,000")
p("hk.royalty.deemed_profit", "HK", "ROYALTY", "rate", "deemed_assessable_profit_share", 30, "%",
  "hk.cap112.en#s21A", "2003-04-01", "for any sum received by or accrued to the person on or after 1 April 2003, 30%")
p("hk.royalty.deemed_profit_associate", "HK", "ROYALTY", "rate", "deemed_assessable_profit_share_associate", 100,
  "%", "hk.cap112.en#s21A", "", "100% of the sum in the case of a sum derived from an associate")
p("hk.fsie.participation_ratio_min", "HK", "DIVIDEND", "condition", "participation_ratio_min", 5, "%",
  "hk.cap112.en#s15M", "", "has continuously held not less than 5% of equity interests in the investee entity",
  "also applies to equity disposal gains")
p("hk.fsie.participation_months_min", "HK", "DIVIDEND", "condition", "participation_months_min", 12, "months",
  "hk.cap112.en#s15M", "", "for a period of not less than 12 months immediately before")
p("hk.fsie.reference_rate", "HK", "DIVIDEND", "condition", "subject_to_tax_reference_rate", 15, "%",
  "hk.cap112.en#s15N", "", "the reference rate is 15%")

# ---- Singapore domestic
S43 = "sg.ita1947.full#s43"
p("sg.corp.rate", "SG", "ALL", "rate", "corporate_income_tax_rate", 17, "%", S43, "",
  "every company or body of persons, tax at the rate of 17% on every dollar of the chargeable income thereof")
p("sg.wht.interest", "SG", "INTEREST", "rate", "withholding_rate_non_resident", 15, "%", S43, "",
  "tax at the rate of 15% is to be levied and paid on the gross amount of", "s43(3); income classes in s12(6) and others")
p("sg.wht.royalty", "SG", "ROYALTY", "rate", "withholding_rate_non_resident", 10, "%", S43, "",
  "tax at the rate of 10% is to be levied and paid on the gross amount of any income referred to in section 12(7)(a) and (b)",
  "s43(3A)")
p("sg.fsie.headline_rate_min", "SG", "DIVIDEND", "condition", "foreign_headline_rate_min", 15, "%",
  "sg.ita1947.full#s13", "", "is not less than 15%", "one of the s13(9) conditions; the income must also have been taxed at source")
p("sg.wht.filing_due", "SG", "INTEREST", "limit", "withholding_filing_due",
  "15th day of the second month following payment", "text", "sg.ita1947.full#s45", "",
  "by the 15th day of the second month following the month in which the interest from which the tax is to be deducted is paid")

# ---- Hong Kong and Singapore domestic conditions (read from the statutes; expired regimes are not kept)
# ==== Hong Kong / Singapore domestic statute parameters (generated; every quote checked against clauses.csv)
# ==== BLOCK 1: core rows
# ---- Hong Kong: Inland Revenue Ordinance (hk.cap112.en)
# s14 charge
p("hk.profits.charge_scope", "HK", "ALL", "condition", "charge_requires_hk_business_and_hk_source_profits", 1, "bool", "hk.cap112.en#s14", "", "on every person carrying on a trade, profession or business in Hong Kong in respect of his assessable profits arising in or derived from Hong Kong", "profits tax requires both carrying on business in Hong Kong and profits arising in or derived from Hong Kong")
p("hk.gain.capital_asset_excluded", "HK", "SHARE_TRANSFER", "condition", "capital_asset_sale_profits_excluded", 1, "bool", "hk.cap112.en#s14", "", "(excluding profits arising from the sale of capital assets)", "the provision gives no test for capital nature; case-by-case judgement")
# s15(1)(b), (ba), s20B, s21A royalties
p("hk.royalty.deemed_use_in_hk", "HK", "ROYALTY", "condition", "deemed_hk_receipt_ip_used_in_hk", 1, "bool", "hk.cap112.en#s15", "", "received by or accrued to a person for the use, or the right to the use, in Hong Kong of any patent, design, trade mark, copyright material", "s15(1)(b); limited to sums not otherwise chargeable under this Part")
p("hk.royalty.deemed_use_outside_hk_deductible", "HK", "ROYALTY", "condition", "deemed_hk_receipt_ip_used_outside_hk_if_deductible_in_hk", 1, "bool", "hk.cap112.en#s15", "2004-06-25", "which are deductible in ascertaining the assessable profits of a person under this Part", "s15(1)(ba): sums for the use of IP outside Hong Kong are deemed Hong Kong receipts only when deductible for Hong Kong profits tax; start date from the editorial note to the section")
p("hk.royalty.payer_chargeable", "HK", "ROYALTY", "procedure", "non_resident_chargeable_in_name_of_hk_payer", 1, "bool", "hk.cap112.en#s20B", "", "is chargeable to tax in respect of the sums described in subsection (1) in the name of any person in Hong Kong who paid or credited those sums", "applies to sums under s15(1)(a), (b), (ba) and (bb); the tax may be recovered from the Hong Kong payer")
p("hk.royalty.payer_must_deduct", "HK", "ROYALTY", "procedure", "payer_must_deduct_tax_at_payment", 1, "bool", "hk.cap112.en#s20B", "", "he shall, at the time he makes the payment or credit, deduct from those sums so much thereof as is sufficient to produce the amount of such tax", "the provision sets no fixed withholding rate; the amount deducted is enough to pay the tax")
p("hk.royalty.associate_carve_out", "HK", "ROYALTY", "condition", "associate_100pct_not_applied_if_ip_never_owned_by_hk_business", 1, "bool", "hk.cap112.en#s21A", "", "no person carrying on a trade, profession or business in Hong Kong has at any time wholly or partly owned the property in respect of which the sum is paid", "requires the Commissioner's satisfaction; sums from an associate are then still computed at 30%")
# s15(1)(f), s26A interest
p("hk.interest.deemed_corporation", "HK", "INTEREST", "condition", "deemed_hk_receipt_corporation_interest_derived_from_hk", 1, "bool", "hk.cap112.en#s15", "", "sums received by or accrued to a corporation carrying on a trade, profession or business in Hong Kong by way of interest derived from Hong Kong", "s15(1)(f); the corporation must carry on business in Hong Kong and the interest must be derived from Hong Kong")
p("hk.interest.exempt_instruments", "HK", "INTEREST", "condition", "interest_on_specified_instruments_excluded_from_profits", 1, "bool", "hk.cap112.en#s26A", "", "shall not be included in the profits of any corporation or other person chargeable to tax under this Part", "s26A(1) lists interest on tax reserve certificates, government bonds, Exchange Fund debt instruments, Hong Kong dollar multilateral agency debt instruments and long term debt instruments; not applicable to long term debt instruments issued from 2011-03-25 when received by an associate of the issuer (subsection (1B))")
# Division 3A foreign-sourced income (ss 15H-15OC)
p("hk.fsie.covered_income", "HK", "ALL", "condition", "specified_foreign_sourced_income_types", "interest;dividend;disposal_gain;ip_income", "enum", "hk.cap112.en#s15H", "", "means any interest, dividend, disposal gain or IP income arising in or derived from a territory outside Hong Kong", "the relevant income of regulated financial entities, entities enjoying a concessionary rate or exemption, and traders is excluded")
p("hk.fsie.mne_entity_only", "HK", "ALL", "condition", "recipient_is_mne_entity_carrying_on_business_in_hk", 1, "bool", "hk.cap112.en#s15I", "", "is received in Hong Kong by an MNE entity carrying on a trade, profession or business in Hong Kong", "an MNE group is a group with at least one entity or permanent establishment outside the jurisdiction of the ultimate parent entity (s15H)")
p("hk.fsie.received_in_hk_trigger", "HK", "ALL", "condition", "taxed_in_year_received_in_hk", 1, "bool", "hk.cap112.en#s15I", "", "is to be regarded as a receipt arising in or derived from Hong Kong for the basis period of the year of assessment during which the income is received in Hong Kong", "s15I(1) is not triggered unless received in Hong Kong")
p("hk.fsie.gain_not_capital", "HK", "SHARE_TRANSFER", "condition", "foreign_gain_not_treated_as_capital", 1, "bool", "hk.cap112.en#s15I", "", "is to be regarded as not arising from the sale of capital assets even if it so arises", "specified foreign-sourced income within s15I(1) cannot rely on the capital asset exclusion in s14")
p("hk.fsie.substance_exception_income", "HK", "ALL", "condition", "economic_substance_exception_income_types", "interest;dividend;non_ip_disposal_gain", "enum", "hk.cap112.en#s15K", "", "the income is interest, a dividend or a non-IP disposal gain", "s15I(1) does not apply when the economic substance requirement of s15K(2) is met; IP income and gains on its disposal are outside this exception")
p("hk.fsie.substance_pure_holding", "HK", "ALL", "condition", "pure_equity_holding_entity_adequate_people_and_premises", 1, "bool", "hk.cap112.en#s15K", "", "in the Commissioner’s opinion, the entity has adequate human resources and premises for carrying out the specified economic activities", "a pure equity-holding entity must also comply with registration and filing requirements and carry out, or arrange to carry out, the holding and management of equity in Hong Kong; needs discretion")
p("hk.fsie.participation_subject_to_tax", "HK", "DIVIDEND", "condition", "participation_exemption_requires_qualifying_similar_tax", 1, "bool", "hk.cap112.en#s15N", "", "the income is subject to a qualifying similar tax in a territory outside Hong Kong", "for dividends the condition may also be met by the underlying profits or the related downstream income having been subject to a qualifying similar tax; also applies to equity disposal gains")
p("hk.fsie.participation_anti_hybrid", "HK", "DIVIDEND", "anti_abuse", "participation_exemption_denied_if_dividend_deductible_abroad", 1, "bool", "hk.cap112.en#s15N", "", "section 15M does not apply if, and to the extent that, the income is allowable for deduction when computing the amount of the tax", "the case where the dividend is deductible abroad in computing the tax on the underlying profits")
p("hk.fsie.participation_main_purpose", "HK", "DIVIDEND", "anti_abuse", "participation_exemption_main_purpose_test", 1, "bool", "hk.cap112.en#s15N", "", "the main purpose, or one of the main purposes, of the entity in entering into the arrangement was to obtain a tax benefit", "requires the Commissioner's satisfaction, needs discretion")
p("hk.fsie.intragroup_assoc_ratio_min", "HK", "SHARE_TRANSFER", "condition", "intragroup_transfer_relief_associating_interest_min", 75, "%", "hk.cap112.en#s15OC", "", "entity A has at least 75% of direct or indirect beneficial interest in, or in relation to, entity B", "association threshold for the intra-group transfer relief in s15OA, may also be computed by voting rights; both seller and buyer must be chargeable to profits tax at the time of sale")
p("hk.fsie.intragroup_clawback_years", "HK", "SHARE_TRANSFER", "limit", "intragroup_transfer_relief_clawback_years", 2, "years", "hk.cap112.en#s15OB", "", "within 2 years after the subject sale", "the relief ends if within the period either party ceases to be chargeable to profits tax or the two cease to be associated")
# s50, s50AAA double taxation relief
p("hk.ftc.credit_limit", "HK", "ALL", "limit", "treaty_credit_limit", "hk_tax_on_same_income_at_average_rate", "enum", "hk.cap112.en#s50", "", "The credit shall not exceed the amount which would be produced by computing the amount of the income in accordance with the provisions of this Ordinance and then charging it to tax at a rate", "the rate is the tax payable before credit divided by total income")
p("hk.ftc.unilateral_no_dta", "HK", "ALL", "condition", "unilateral_credit_if_no_dta", 1, "bool", "hk.cap112.en#s50AAA", "", "no double taxation arrangements have been made with the government of a territory outside Hong Kong", "also applies where an arrangement exists but the income is not covered by its exemption or credit provisions; the creditable income is listed in Sch 54")
# Schedule 17K onshore equity disposal gains
p("hk.onshore_gain.ratio_min", "HK", "SHARE_TRANSFER", "condition", "qualifying_equity_interest_min", 15, "%", "hk.cap112.en#sch17K", "2024-01-01", "entitle the holder of the interests to at least a 15% share in the profits, capital or reserves of the investee entity", "Sch 17K; may be aggregated with interests held by closely related entities; applies only to disposal gains arising in or derived from Hong Kong")
p("hk.onshore_gain.holding_months_min", "HK", "SHARE_TRANSFER", "condition", "holding_months_min", 24, "months", "hk.cap112.en#sch17K", "2024-01-01", "means the continuous period of 24 months immediately before the date of the disposal", "must be held throughout the reference period")
p("hk.onshore_gain.election_required", "HK", "SHARE_TRANSFER", "procedure", "written_election_required", 1, "bool", "hk.cap112.en#sch17K", "2024-01-01", "Subsection (1) does not apply to an investor entity unless it elects in writing that the subsection applies to it", "Sch 17K s5(1) does not apply without a written election")
# ---- Singapore: Income Tax Act 1947 (sg.ita1947.full)
# s10 charge
p("sg.charge.basis", "SG", "ALL", "condition", "income_chargeable_bases", "accruing_in_or_derived_from_sg;received_in_sg_from_outside", "enum", "sg.ita1947.full#s10", "", "upon the income of any person accruing in or derived from Singapore or received in Singapore from outside Singapore", "s10(1)")
p("sg.foreign_income.remittance_is_receipt", "SG", "ALL", "condition", "foreign_income_remitted_counts_as_received_in_sg", 1, "bool", "sg.ita1947.full#s10", "", "any amount from any income derived from outside Singapore which is remitted to, transmitted or brought into, Singapore", "s10(25); also deemed received in Singapore when applied to a debt of a Singapore business or used to buy movable property brought into Singapore")
# s12(6), (7) deemed source
p("sg.source.interest_borne_by_sg", "SG", "INTEREST", "condition", "deemed_sg_source_if_borne_by_sg_resident_or_pe", 1, "bool", "sg.ita1947.full#s12", "", "borne, directly or indirectly, by a person resident in Singapore or a permanent establishment in Singapore except in respect of any business carried on outside Singapore", "s12(6); also deemed Singapore source when deductible against Singapore-sourced income; excludes a business carried on through a permanent establishment outside Singapore and immovable property outside Singapore")
p("sg.source.royalty_borne_by_sg", "SG", "ROYALTY", "condition", "deemed_sg_source_if_borne_by_sg_resident_or_pe", 1, "bool", "sg.ita1947.full#s12", "", "which is borne, directly or indirectly, by a person resident in Singapore or a permanent establishment in Singapore", "s12(7); also deemed Singapore source when deductible against Singapore-sourced income; excludes a business carried on outside Singapore through a permanent establishment there")
# s43(3) conditions of the 15% rate
p("sg.wht.interest_non_resident", "SG", "INTEREST", "condition", "recipient_not_resident_in_sg", 1, "bool", "sg.ita1947.full#s43", "1996-02-28", "accruing in or derived from Singapore on or after 28 February 1996 by a person not resident in Singapore", "s43(3)")
p("sg.wht.interest_not_sg_trade", "SG", "INTEREST", "condition", "not_derived_from_trade_carried_on_in_sg", 1, "bool", "sg.ita1947.full#s43", "1996-02-28", "which is not derived by the person from any trade, business, profession or vocation carried on or exercised by the person in Singapore", "s43(3); the 15% rate does not apply when not met")
p("sg.wht.interest_not_sg_pe", "SG", "INTEREST", "condition", "not_effectively_connected_with_sg_pe", 1, "bool", "sg.ita1947.full#s43", "1996-02-28", "which is not effectively connected with any permanent establishment in Singapore of the person", "s43(3); the 15% rate does not apply when not met")
# s45 withholding
p("sg.wht.payer_duty", "SG", "INTEREST", "procedure", "payer_must_withhold_if_payee_not_known_resident", 1, "bool", "sg.ita1947.full#s45", "", "Where a person is liable to pay to another person not known to the firstmentioned person to be resident in Singapore any interest which is chargeable to tax under this Act, the firstmentioned person must", "must deduct the tax, notify at once and pay the tax deducted to the Comptroller")
p("sg.wht.rate_fallback", "SG", "INTEREST", "rate", "withholding_rate_non_individual_when_s43_3_3a_not_applicable", 17, "%", "sg.ita1947.full#s45", "", "where the person to be paid is any other person, at the rate of 17%", "withholding rate when the payee is not an individual and s43(3) or (3A) does not apply; also applies to s12(6) and (7) income by virtue of s45A")
p("sg.wht.late_penalty", "SG", "INTEREST", "procedure", "late_payment_penalty", 5, "%", "sg.ita1947.full#s45", "", "a sum equal to 5% of such amount of tax is payable", "penalty for not paying the tax deducted to the Comptroller by the due date")
p("sg.wht.late_penalty_monthly", "SG", "INTEREST", "procedure", "late_payment_additional_penalty_per_month", 1, "%", "sg.ita1947.full#s45", "", "an additional penalty of 1% of such amount of tax is payable for each completed month that the tax remains unpaid", "charged per complete month when still unpaid 30 days after the due date")
p("sg.wht.late_penalty_monthly_cap", "SG", "INTEREST", "limit", "late_payment_additional_penalty_cap", 15, "%", "sg.ita1947.full#s45", "", "the total additional penalty under this paragraph must not exceed 15% of the amount of tax outstanding", "cap on the additional penalty")
# s13(8), (9) foreign-sourced dividends
p("sg.fsie.subject_to_tax", "SG", "DIVIDEND", "condition", "foreign_income_subject_to_tax_in_source_territory", 1, "bool", "sg.ita1947.full#s13", "", "the income is subject to tax of a similar character to income tax (by whatever name called)", "s13(9)(a); for dividends the tax paid by the paying company on its profits counts (subsection (10)); the Minister may waive this condition case by case (subsection (9B))")
p("sg.fsie.beneficial", "SG", "DIVIDEND", "condition", "comptroller_satisfied_exemption_beneficial", 1, "bool", "sg.ita1947.full#s13", "", "the Comptroller is satisfied that the tax exemption would be beneficial to the person resident in Singapore", "s13(9)(c), needs discretion")
# s10L gains from the sale of foreign assets
p("sg.s10l.relevant_group_entity", "SG", "SHARE_TRANSFER", "condition", "seller_is_entity_of_relevant_group", 1, "bool", "sg.ita1947.full#s10L", "2024-01-01", "gains from the sale or disposal by an entity (called in this section the seller entity) of a relevant group of any movable or immovable property situated outside Singapore", "a relevant group is one whose entities are not all incorporated in the same jurisdiction, or where any entity has a place of business in more than one jurisdiction")
p("sg.s10l.received_in_sg_trigger", "SG", "SHARE_TRANSFER", "condition", "gain_taxed_when_received_in_sg", 1, "bool", "sg.ita1947.full#s10L", "2024-01-01", "that are received in Singapore from outside Singapore, are treated as income chargeable to tax under section 10(1)", "charged under s10(1)(g); applies only to gains not otherwise chargeable under s10(1) or otherwise exempt (subsection (2))")
p("sg.s10l.excluded_entity", "SG", "SHARE_TRANSFER", "condition", "economic_substance_carve_out", 1, "bool", "sg.ita1947.full#s10L", "2024-01-01", "carried out by an entity that is an excluded entity in the basis period in which the sale or disposal occurred", "limited to foreign assets other than IP; an excluded entity must have its operations managed and performed in Singapore with adequate economic substance")
# s13W disposal of shares
p("sg.s13w.ratio_min", "SG", "SHARE_TRANSFER", "condition", "shareholding_ratio_min", 20, "%", "sg.ita1947.full#s13W", "2026-01-01", "legally and beneficially owned at least 20% of the ordinary shares in investee company B1", "s13W(1A); may also be met by at least 20% of the combined paid-up value of ordinary and preference shares; that subsection has no end date")
p("sg.s13w.holding_months_min", "SG", "SHARE_TRANSFER", "condition", "holding_months_min", 24, "months", "sg.ita1947.full#s13W", "2026-01-01", "at all times during a continuous period of at least 24 months ending on the date immediately before the date of disposal of such shares", "s13W(1A)")
# s50, s50A, s50C foreign tax credit
p("sg.ftc.credit_limit", "SG", "ALL", "limit", "treaty_credit_limit", "sg_tax_on_same_income_at_average_rate", "enum", "sg.ita1947.full#s50", "", "The credit must not exceed the amount which would be produced by computing the amount of the income in accordance with the provisions of this Act and then charging it to income tax at a rate", "the rate is the income tax payable before credit divided by assessable income")
p("sg.ftc.unilateral", "SG", "ALL", "condition", "unilateral_credit_if_no_treaty", 1, "bool", "sg.ita1947.full#s50A", "", "Even if there are no arrangements in force under section 49 with the government of any territory outside Singapore, tax credit under section 50 must, subject to this section, be given to any person resident in Singapore", "covers dividends, s10L gains and more; interest and royalties only when not borne by a Singapore resident or permanent establishment and not deductible in Singapore")
p("sg.ftc.pooling_foreign_tax_paid", "SG", "ALL", "condition", "pooling_requires_foreign_tax_paid", 1, "bool", "sg.ita1947.full#s50C", "", "income tax (by whatever name called) or qualified domestic minimum top\u2011up tax (but disregarding any excluded top\u2011up tax), has been paid on the income", "one of the pooling conditions (s50C(2)(a))")
p("sg.ftc.pooling_headline_rate_min", "SG", "ALL", "condition", "pooling_foreign_headline_rate_min", 15, "%", "sg.ita1947.full#s50C", "", "carried on by a company in that territory at that time, is not less than 15%", "one of the pooling conditions: the highest corporate tax rate at source is at least 15% when received")
#
# ==== BLOCK 2: supplementary rows (finer conditions of the same provisions; drop this block if a smaller set is wanted)
# ---- Hong Kong
p("hk.royalty.deemed_film_use_in_hk", "HK", "ROYALTY", "condition", "deemed_hk_receipt_film_or_recording_used_in_hk", 1, "bool", "hk.cap112.en#s15", "", "received by or accrued to a person from the exhibition or use in Hong Kong of cinematograph or television film or tape, any sound recording", "s15(1)(a); limited to sums not otherwise chargeable under this Part")
p("hk.interest.deemed_financial_institution", "HK", "INTEREST", "condition", "deemed_hk_receipt_financial_institution_hk_business", 1, "bool", "hk.cap112.en#s15", "", "received by or accrued to a financial institution by way of interest which arises through or from the carrying on by the financial institution of its business in Hong Kong", "s15(1)(i); even if the funds are made available outside Hong Kong")
p("hk.interest.deemed_intragroup_financing", "HK", "INTEREST", "condition", "deemed_hk_receipt_intragroup_financing_business_in_hk", 1, "bool", "hk.cap112.en#s15", "", "by way of interest that arises through or from the carrying on in Hong Kong by the corporation of its intra-group financing business", "s15(1)(ia); applies to corporations other than financial institutions, even if the funds are made available outside Hong Kong")
p("hk.fsie.remittance_is_receipt", "HK", "ALL", "condition", "sum_remitted_counts_as_received_in_hk", 1, "bool", "hk.cap112.en#s15H", "", "the sum is remitted to, or is transmitted or brought into, Hong Kong", "s15H(5); also deemed received in Hong Kong when applied to a debt of a Hong Kong business or used to buy movable property brought into Hong Kong")
p("hk.fsie.commencement", "HK", "ALL", "condition", "regime_applies_to_income_accrued_and_received_from", 1, "bool", "hk.cap112.en#sch55", "2023-01-01", "apply in relation to specified foreign-sourced income accrued and received on or after 1 January 2023", "transitional provisions in Sch 55; the wider scope of disposal gains under the 2023 amendment applies to income accrued and received from 2024-01-01 (Sch 56)")
p("hk.fsie.substance_non_pure_holding", "HK", "ALL", "condition", "non_pure_equity_holding_entity_adequate_operating_expenditure_in_hk", 1, "bool", "hk.cap112.en#s15K", "", "the total amount of operating expenditure incurred in Hong Kong for carrying out the specified economic activities is adequate in the Commissioner’s opinion", "a non-pure equity-holding entity must also have an adequate number of qualified employees in Hong Kong carrying out the specified economic activities; needs discretion")
p("hk.fsie.participation_headline_rate_basis", "HK", "DIVIDEND", "condition", "reference_rate_compared_with_highest_applicable_rate", 1, "bool", "hk.cap112.en#s15N", "", "the highest applicable rate, of a similar tax in that territory is equal to or higher than the reference rate", "what is compared is the applicable rate of the foreign similar tax (the highest if more than one), not the actual tax burden")
p("hk.fsie.intragroup_relief", "HK", "SHARE_TRANSFER", "condition", "intragroup_transfer_at_no_gain_no_loss", 1, "bool", "hk.cap112.en#s15OA", "", "the selling entity is to be regarded as having sold the subject property for a consideration of such amount as would secure that neither a gain nor a loss would accrue to the selling entity", "s15OA(3); seller and buyer must be associated and both chargeable to profits tax at the time of sale")
p("hk.fsie.ip_nexus_exception", "HK", "ROYALTY", "condition", "qualifying_ip_income_excepted_portion_by_nexus", 1, "bool", "hk.cap112.en#s15L", "", "section 15I(1) does not operate in relation to the excepted portion of the income ascertained under Part 2 of Schedule 17FC", "qualifying IP income only; the excepted portion is computed under Sch 17FC")
p("hk.ftc.unilateral_fsie_only", "HK", "ALL", "condition", "unilateral_credit_only_for_income_charged_under_s15I", 1, "bool", "hk.cap112.en#sch54", "2023-01-01", "the following condition is specified for the income: the income is chargeable to profits tax because of section 15I(1)", "unilateral credit applies only to specified foreign-sourced income chargeable under s15I(1); disposal gains other than on equity apply when accrued and received from 2024-01-01")
p("hk.ftc.underlying_ratio_min", "HK", "DIVIDEND", "condition", "underlying_tax_credit_adequate_interest_min", 10, "%", "hk.cap112.en#s50AAAC", "", "person A has at least 10% of direct or indirect beneficial interest in, or in relation to, person B", "the interest required for credit of the tax paid on a dividend's underlying profits; may also be computed by voting rights")
# ---- Singapore
p("sg.source.interest_loan_funds_used_in_sg", "SG", "INTEREST", "condition", "deemed_sg_source_if_loan_funds_used_in_sg", 1, "bool", "sg.ita1947.full#s12", "", "any income derived from loans where the funds provided by such loans are brought into or used in Singapore", "s12(6)(b)")
p("sg.wht.royalty_non_resident", "SG", "ROYALTY", "condition", "recipient_not_resident_in_sg", 1, "bool", "sg.ita1947.full#s43", "2005-01-01", "accruing in or derived from Singapore on or after 1 January 2005 by a person not resident in Singapore", "s43(3A)")
p("sg.wht.royalty_not_sg_trade", "SG", "ROYALTY", "condition", "not_derived_from_trade_carried_on_in_sg", 1, "bool", "sg.ita1947.full#s43", "2005-01-01", "which is not derived by the person from any trade, business, profession or vocation carried on or exercised by the person in Singapore", "s43(3A) has the same wording; the 10% rate does not apply when not met")
p("sg.wht.royalty_not_sg_pe", "SG", "ROYALTY", "condition", "not_effectively_connected_with_sg_pe", 1, "bool", "sg.ita1947.full#s43", "2005-01-01", "which is not effectively connected with any permanent establishment in Singapore of the person", "s43(3A) has the same wording; the 10% rate does not apply when not met")
p("sg.wht.duty_extends_to_royalty", "SG", "ROYALTY", "procedure", "withholding_duty_applies_to_s12_6_7_income", 1, "bool", "sg.ita1947.full#s45A", "", "Section 45(1) to (8) applies in relation to the payment of any income referred to in section 12(6) or (7)", "the withholding, filing deadline and penalty provisions of s45 also apply to s12(6) and (7) income")
p("sg.fsie.recipient", "SG", "DIVIDEND", "condition", "recipient_resident_non_individual", 1, "bool", "sg.ita1947.full#s13", "2003-06-01", "on or after 1 June 2003 by any person, not being an individual, resident in Singapore", "s13(8)(d); must be a foreign-sourced dividend received in Singapore")
p("sg.fsie.ministerial_order", "SG", "ALL", "condition", "exemption_or_concessionary_rate_by_ministerial_order", 1, "bool", "sg.ita1947.full#s13", "", "the income received by a person resident in Singapore from such source in any country outside Singapore as may be specified in the order", "s13(12); the Minister may by order exempt wholly or partly or apply a concessionary rate; a specific order is required")
p("sg.s10l.substance_pure_holding", "SG", "SHARE_TRANSFER", "condition", "pure_equity_holding_entity_adequate_people_and_premises_in_sg", 1, "bool", "sg.ita1947.full#s10L", "2024-01-01", "the entity has adequate human resources and premises in Singapore to carry out the operations of the entity", "a pure equity-holding entity must also file the returns required by law, with its operations managed and performed in Singapore")
p("sg.s10l.substance_non_pure_holding", "SG", "SHARE_TRANSFER", "condition", "non_pure_equity_holding_entity_adequate_economic_substance_in_sg", 1, "bool", "sg.ita1947.full#s10L", "2024-01-01", "the entity has adequate economic substance in Singapore, taking into account the following considerations", "operations must also be managed and performed in Singapore; the number of employees, their qualifications and experience, business expenditure and whether key decisions are made in Singapore are considered")
p("sg.s10l.share_situs", "SG", "SHARE_TRANSFER", "condition", "company_share_situs", "place_of_incorporation", "enum", "sg.ita1947.full#s10L", "2024-01-01", "any shares in or securities issued by a company, or any right or interest in such shares or securities, are situated where the company is incorporated", "used to decide whether an asset is a foreign asset; registered shares are situated where the register is kept (subsection (15)(i))")
p("sg.s10l.commencement", "SG", "SHARE_TRANSFER", "condition", "s10l_applies_to_disposals_from", "2024-01-01", "date", "sg.ita1947.full#s10L", "",
  "Subsection (1) applies only to gains from a sale or disposal of a foreign asset that occurs on or after 1 January 2024.",
  "s10L(3); the disposal takes place when the asset vests in the transferee (s10L(4)); the model uses the flow's date (decision D36)")
p("sg.ftc.underlying_ratio_min", "SG", "DIVIDEND", "condition", "underlying_tax_credit_shareholding_min", 25, "%", "sg.ita1947.full#s50A", "", "owns not less than 25% of the total number of issued shares of the company paying the dividend", "at that ratio the credit must include the tax paid by the paying company on its profits; the Minister may waive the ratio requirement case by case")
p("sg.ftc.pooling_election", "SG", "ALL", "procedure", "pooling_by_election", 1, "bool", "sg.ita1947.full#s50C", "", "the person may elect to be given a pooled credit for that year of assessment in lieu of any 2 or more of those credits", "from the year of assessment 2012")
p("sg.ftc.pooling_sg_tax_not_nil", "SG", "ALL", "condition", "pooling_requires_sg_tax_payable_on_income", 1, "bool", "sg.ita1947.full#s50C", "", "the income tax payable under this Act on the income for the year of assessment (before allowance of any credit under this Part) is not nil", "one of the pooling conditions (s50C(2)(c))")

# ---- exposed by the S45 calculator labels (labels/sg_s45_labels.csv)
p("sg.wht.late_penalty_monthly_starts_after_days", "SG", "INTEREST", "limit", "additional_penalty_starts_after_days", 30, "days",
  "sg.ita1947.full#s45", "", "within 30 days after the time specified in paragraph (a), an additional penalty of 1%",
  "the additional 1% per month penalty starts counting complete months only when still unpaid 30 days after the due date")
p("sg.dtr.cor_due", "SG", "ALL", "limit", "certificate_of_residence_due", "31 Mar of the following year", "text",
  "sg.iras.wht.dta-relief#h3", "", "The due date is 31 Mar of the following year if the claim is for a period in the current calendar year",
  "claiming treaty relief requires the counterparty's certificate of residence by 31 March of the following year")

p("sg.time.excluded_days", "SG", "ALL", "limit", "excluded_days", "sunday;public_holiday", "enum", "sg.ia1965.full#s50", "",
  "if the last day of the period is a Sunday or a public holiday (which days are called in this section excluded days) the period includes the next following day not being an excluded day",
  "when the last day of a period is a Sunday or public holiday it moves to the next non-excluded day; Saturdays are not excluded days")
p("sg.time.act_on_excluded_day", "SG", "ALL", "limit", "act_due_on_excluded_day_moves_to_next_day", 1, "bool", "sg.ia1965.full#s50", "",
  "if that day happens to be an excluded day, the act or proceeding is considered as done or taken in due time if it is done or taken on the next day afterwards, not being an excluded day",
  "an act required on a day that is an excluded day is in time if done on the next non-excluded day")
p("sg.holiday.sunday_substitute", "SG", "ALL", "limit", "holiday_on_sunday_next_day_is_holiday", 1, "bool", "sg.ha1998.full#s4", "",
  "if any day specified in the Schedule falls on a Sunday, the day next following not being itself a public holiday is declared a public holiday in Singapore",
  "when a public holiday falls on a Sunday, the next day is a public holiday")
p("sg.wht.movable_property_rent", "SG", "ROYALTY", "rate", "withholding_rate_non_resident_movable_property_rent", 15, "%",
  "sg.ita1947.full#s43", "", "tax at the rate of 15% is to be levied and paid on the gross amount of — ( a ) any income referred to in section 12(6); and ( b ) any income referred to in section 12(7)( a ), ( b ) and ( d )",
  "s43(3): rent for movable property under s12(7)(d) at 15%; royalties under (a) and (b) are reduced to 10% by subsection (3A)")
p("cn-sg.int.government_exempt", SG, "INTEREST", "condition", "exempt_if_beneficial_owner_is_listed_government_body", 1, "bool",
  "treaty.cn-sg.2007.p2.zh#2.1", "2010-01-01", "从缔约国一方取得的利息应在该国免税，如果受益所有人是",
  "art. 11 para. 3 as replaced by the Second Protocol; limited to the listed governments, central banks and wholly government-owned institutions")
p("cn-sg.int.government_exempt_condition", SG, "INTEREST", "condition", "wholly_government_owned_and_non_commercial", 1, "bool",
  "treaty.cn-sg.2007.p2.zh#2.1", "2010-01-01", "应为中国政府完全拥有并且不从事商业活动",
  "the listed institutions must also be wholly owned by the government and not carry on commercial activities")

p("cn-sg.roy.includes_equipment", SG, "ROYALTY", "condition", "royalties_include_equipment_use", 1, "bool", AS + "#12.3",
  "2008-01-01", "也包括使用或有权使用工业、商业、科学设备", "the treaty's definition of royalties includes payments for the use of equipment")
p("cn-sg.roy.equipment_rent_is_royalty", SG, "ROYALTY", "condition", "equipment_rent_is_royalty", 1, "bool",
  "cn.gsf.2010-75#12.3", "", "特许权使用费也包括使用或有权使用工业、商业、科学设备取得的所得，即设备租金",
  "SAT clause-by-clause interpretation; excludes the part of a finance lease treated as interest and payments for the use of immovable property")

p("sg.wht.comptroller_may_allow_other_period", "SG", "ALL", "procedure", "comptroller_may_allow_other_period", 1, "bool",
  "sg.ita1947.full#s45", "", "allow any person or class of persons to give notice of the deduction of tax and make payment of the amount so deducted within such other period and subject to such conditions as the Comptroller may determine",
  "s45(2)(a): the Comptroller may allow a person or class of persons to file and pay within another period; this is the legal authority when IRAS's practical due date is later than the statutory one")
p("sg.wht.penalty_runs_from_allowed_date", "SG", "ALL", "procedure", "penalty_date_is_15th_or_date_allowed", 1, "bool",
  "sg.ita1947.full#s45", "", "or such other date as may be allowed under subsection (2)(a), a sum equal to 5% of such amount of tax is payable",
  "s45(4)(a): the penalty runs from the 15th or the other date allowed by the Comptroller")

p("sg.dtr.cor_due_prior_years", "SG", "ALL", "limit", "certificate_of_residence_due_prior_years", "3 months from WHT submission", "text",
  "sg.iras.wht.dta-relief#h3", "", "Within 3 months from the date of WHT submission if the claim is for preceding calendar years",
  "when the payment belongs to a year before the filing year, the certificate of residence must be submitted within 3 months of filing")

p("cn-hk.cor.covers_following_years", HK, "ALL", "procedure", "hk_certificate_covers_following_calendar_years", 2, "years",
  "cn.sta.2016-35#all", "2016-04-15", "可用作证明该香港居民在该公历年度及其后连续两个公历年度的香港居民身份",
  "a certificate of resident status issued by the Hong Kong IRD for a calendar year can be used in the Mainland for that year and the following two consecutive calendar years; no longer applies after circumstances change")
p("cn-hk.cor.void_after_change", HK, "ALL", "procedure", "hk_certificate_void_after_change_of_circumstances", 1, "bool",
  "cn.sta.2016-35#all", "2016-04-15", "不再符合享受《安排》待遇条件，则原适用于该公历年度的居民身份证明书不能用作证明其在情况发生变化后的香港居民身份",
  "after a change in residence circumstances the original certificate no longer proves the resident status after the change")

# ---- Mainland: when the withholding obligation arises, and the exchange rate it fixes
p("cn.wht.obligation_date", "CN", "ALL", "procedure", "withholding_obligation_date", "actual payment or date payable", "text",
  "cn.sta.2017-37#i4", "2017-12-01", "扣缴义务发生之日为相关款项实际支付或者到期应支付之日",
  "the withholding obligation arises on the date of actual payment or of the payment falling due; falling due means a payable that accrual accounting books as a cost or expense (cn.reg.eit#105)")
p("cn.wht.obligation_date_dividend", "CN", "DIVIDEND", "procedure", "withholding_obligation_date_dividend", "actual payment", "text",
  "cn.sta.2017-37#i7", "2017-12-01", "相关应纳税款扣缴义务发生之日为股息、红利等权益性投资收益实际支付之日",
  "for dividends the withholding obligation arises on the actual payment date, regardless of when payment falls due")
p("cn.wht.fx_rule", "CN", "ALL", "procedure", "fx_conversion_rule", "CNY central parity on the obligation date", "text",
  "cn.sta.2017-37#i4", "2017-12-01", "应当按照扣缴义务发生之日人民币汇率中间价折合成人民币",
  "foreign-currency sums are converted at the CNY central parity on the day the withholding obligation arises; the central parity is published by CFETS (中国外汇交易中心), see tools/fx_cny.py")

# ---- Mainland: profits reinvested by the foreign investor, withholding deferred (财税〔2018〕102号, 公告2018年第53号)
D = "cn.cs.2018-102"
p("cn.reinvest.deferral", "CN", "DIVIDEND", "condition", "reinvestment_defers_withholding", 1, "bool", D + "#i1", "2018-01-01",
  "用于境内直接投资暂不征收预提所得税政策的适用范围，由外商投资鼓励类项目扩大至所有非禁止外商投资的项目和领域",
  "withholding tax is deferred when a foreign investor directly reinvests distributed profits in the Mainland; the scope is all projects and fields where foreign investment is not prohibited")
p("cn.reinvest.forms", "CN", "DIVIDEND", "condition", "qualifying_investment_forms", "capital_increase;new_entity;unrelated_acquisition", "text",
  D + "#i2", "2018-01-01", "1.新增或转增中国境内居民企业实收资本或者资本公积； 2.在中国境内投资新建居民企业； 3.从非关联方收购中国境内居民企业股权",
  "three forms of direct investment; paying up subscribed registered capital also counts as new paid-in capital (cn.sta.2018-53#i1)")
p("cn.reinvest.excludes_listed_shares", "CN", "DIVIDEND", "condition", "listed_shares_excluded_unless_strategic", 1, "bool", D + "#i2", "2018-01-01",
  "不包括新增、转增、收购上市公司股份（符合条件的战略投资除外）", "listed company shares do not count, except strategic investments")
p("cn.reinvest.profit_is_distributed_retained_earnings", "CN", "DIVIDEND", "condition", "profit_is_actually_distributed_retained_earnings", 1, "bool",
  D + "#i2", "2018-01-01", "境外投资者分得的利润属于中国境内居民企业向投资者实际分配已经实现的留存收益而形成的股息、红利等权益性投资收益",
  "must be realised retained earnings actually distributed")
p("cn.reinvest.direct_payment", "CN", "DIVIDEND", "condition", "funds_move_directly_to_investee", 1, "bool", D + "#i2", "2018-01-01",
  "相关款项从利润分配企业的账户直接转入被投资企业或股权转让方账户，在直接投资前不得在境内外其他账户周转",
  "the funds must go directly from the distributing enterprise's account to the investee's or transferor's account; a same-day transfer through a dedicated RMB reinvestment deposit account counts as direct (cn.sta.2018-53#i2)")
p("cn.reinvest.retroactive_claim_years", "CN", "DIVIDEND", "limit", "retroactive_claim_years", 3, "years", D + "#i5", "2018-01-01",
  "可在实际缴纳相关税款之日起三年内申请追补享受该政策，退还已缴纳的税款", "if not claimed, may be claimed retroactively with a refund within three years of paying the tax")
p("cn.reinvest.recapture_days", "CN", "DIVIDEND", "limit", "recapture_filing_days_after_withdrawal", 7, "days", D + "#i6", "2018-01-01",
  "在实际收取相应款项后7日内，按规定程序向税务部门申报补缴递延的税款", "the deferred tax is paid within 7 days of withdrawing the investment")
p("cn.reinvest.special_reorg_continues", "CN", "DIVIDEND", "condition", "special_reorganisation_keeps_deferral", 1, "bool", D + "#i7", "2018-01-01",
  "被投资企业发生重组符合特殊性重组条件，并实际按照特殊性重组进行税务处理的，可继续享受暂不征收预提所得税政策待遇", "a special reorganisation does not trigger repayment")
p("cn.reinvest.late_from_payment_date", "CN", "DIVIDEND", "procedure", "late_payment_runs_from_profit_payment", 1, "bool", D + "#i4", "2018-01-01",
  "税款延迟缴纳期限自相关利润支付之日起计算", "if later found not to qualify, the late-payment period runs from the date the profit was paid")
p("cn.reinvest.treaty_at_payment_time", "CN", "DIVIDEND", "procedure", "recapture_uses_treaty_in_force_at_payment", 1, "bool",
  "cn.sta.2018-53#i3", "2018-01-01", "仅可适用相关利润支付时有效的税收协定", "treaty benefits may be claimed on repayment, but under the treaty in force when the profit was paid")
p("cn.reinvest.fifo_disposal", "CN", "DIVIDEND", "procedure", "deferred_tranche_disposed_first", 1, "bool", "cn.sta.2018-53#i11", "2018-01-01",
  "视为先行处置已享受暂不征税政策的投资", "a partial disposal is treated as disposing of the deferred part first")
p("cn.reinvest.payer_filing_days", "CN", "DIVIDEND", "limit", "payer_filing_days_after_payment", 7, "days", "cn.sta.2018-53#i6", "2018-01-01",
  "应在实际支付利润之日起7日内，向主管税务机关提交以下资料", "the distributing enterprise files the withholding return and the information report within 7 days of payment")

# ---- Mainland: reinvestment tax credit 2025-2028 (财政部 税务总局 商务部公告2025年第2号, 公告2025年第18号)
C = "cn.cs.2025-02"
p("cn.reinvest.credit_rate", "CN", "DIVIDEND", "rate", "reinvestment_credit_rate", 10, "%", C + "#i1", "2025-01-01",
  "可按照投资额的10%抵免境外投资者当年的应纳税额，当年不足抵免的准予向以后结转",
  "10% of the reinvested amount is credited against the year's tax payable, any excess carried forward; after 2028-12-31 the balance may still be used down to zero (#i10)", to="2028-12-31")
p("cn.reinvest.credit_rate_treaty_lower", "CN", "DIVIDEND", "rate", "credit_rate_follows_lower_treaty_rate", 1, "bool", C + "#i1", "2025-01-01",
  "税收协定中关于股息、红利等权益性投资收益适用税率低于10%的，按照协定税率执行",
  "when the treaty dividend rate is below 10% the credit is computed at the treaty rate (5% for qualifying Mainland–Hong Kong dividends); once chosen the ratio cannot be changed (cn.sta.2025-18#i4)", to="2028-12-31")
p("cn.reinvest.credit_min_holding_months", "CN", "DIVIDEND", "condition", "credit_min_holding_months", 60, "months", C + "#i2", "2025-01-01",
  "境外投资者境内再投资需连续持有至少5年（60个月）以上", "held continuously for 60 months; counting starts in the month of the reinvestment time on the 《利润再投资情况表》 (cn.sta.2025-18#i2)", to="2028-12-31")
p("cn.reinvest.credit_encouraged_industry", "CN", "DIVIDEND", "condition", "investee_in_encouraged_catalogue", 1, "bool", C + "#i2", "2025-01-01",
  "被投资企业从事的产业属于《鼓励外商投资产业目录》所列的全国鼓励外商投资产业目录", "the investee must fall within the 全国鼓励外商投资产业目录", to="2028-12-31")
p("cn.reinvest.credit_against", "CN", "DIVIDEND", "condition", "credit_offsets_later_income_from_same_payer", 1, "bool", C + "#i3", "2025-01-01",
  "境外投资者从利润分配企业自利润分配再投资之日以后取得的企业所得税法第三条第三款规定的股息红利、利息、特许权使用费等所得应缴纳的企业所得税",
  "the credit can only offset tax on dividends, interest, royalties and similar received from the same distributing enterprise after the reinvestment date; several distributing enterprises are pooled separately (cn.sta.2025-18#i5)", to="2028-12-31")
p("cn.reinvest.credit_recapture_days", "CN", "DIVIDEND", "limit", "credit_recapture_filing_days", 7, "days", C + "#i5", "2025-01-01",
  "应在收回投资后7日内向利润分配企业所在地税务机关申报补缴递延的税款", "the deferred tax is paid within 7 days of withdrawing the investment; the carried-forward balance may be used against it", to="2028-12-31")
p("cn.reinvest.credit_early_withdrawal_reduces", "CN", "DIVIDEND", "condition", "withdrawal_before_60_months_reduces_credit", 1, "bool", C + "#i5", "2025-01-01",
  "还应按比例减少境外投资者可享受的税收抵免额度", "if withdrawn before 60 months, the credit amount is reduced pro rata and any excess already used is repaid within 7 days", to="2028-12-31")
p("cn.reinvest.credit_fx", "CN", "DIVIDEND", "procedure", "credit_fx_rule", "CNY central parity on the payment date", "text",
  "cn.sta.2025-18#i6", "2025-01-01", "按实际支付相关款项之日的汇率中间价折合成人民币", "foreign-currency reinvestment is converted at the central parity on the actual payment date", to="2028-12-31")
p("cn.reinvest.credit_holding_stop", "CN", "DIVIDEND", "procedure", "holding_stops_at_registration_change_month", 1, "bool",
  "cn.sta.2025-18#i3", "2025-01-01", "以被投资企业完成股权变更或注销登记手续当月，确认停止计算其持有该再投资被收回部分的时间",
  "the holding period ends in the month of the equity change or deregistration; if consideration is received earlier, in the month it is received", to="2028-12-31")

# ---- added 2026-10-07 for the CN rule spec
p("cn.bo.via_100pct_owner", "CN", "DIVIDEND", "condition", "beneficial_owner_via_100pct_owner", 1, "bool",
  "cn.sta.2018-09#i3", "2018-04-01", "直接或间接持有申请人100%股份的人符合“受益所有人”条件",
  "an applicant that does not qualify is treated as the beneficial owner when its 100% holder qualifies and is resident in the same state, or every intermediate tier qualifies; dividends only")
p("cn.gaar", "CN", "ALL", "anti_abuse", "general_anti_avoidance", 1, "bool", "cn.law.eit#47", "2008-01-01",
  "企业实施其他不具有合理商业目的的安排而减少其应纳税收入或者所得额的，税务机关有权按照合理方法调整",
  "lacking a reasonable commercial purpose means having the reduction, exemption or deferral of tax as the main purpose (实施条例 art. 120); overall judgement, maps to U(DISCRETION)")
p("cn.tca.late_surcharge_daily", "CN", "ALL", "procedure", "late_payment_surcharge_per_day", 0.05, "%", "cn.law.tca#32", "",
  "从滞纳税款之日起，按日加收滞纳税款万分之五的滞纳金", "withholding agent remitting late: 0.05% per day")
p("cn-sg.int.government_exempt_condition_sg", SG, "INTEREST", "condition", "sg_bodies_statutory_or_wholly_government_owned_and_non_commercial", 1, "bool",
  "treaty.cn-sg.2007.p2.zh#2.1", "2010-01-01", "应依照新加坡议会法案规定设立或完全由新加坡政府拥有，并且不从事商业活动",
  "additional condition for the institutions listed on the Singapore side (MAS, GIC, statutory bodies); applies to Mainland-sourced interest paid to Singapore government institutions")
p("cn-hk.int.government_exempt", HK, "INTEREST", "condition", "exempt_if_received_by_other_side_government_or_agreed_body", 1, "bool",
  "treaty.cn-hk.2006.zh#11.3", "2007-01-01", "发生于一方而为另一方政府或由双方主管当局认同的机构取得的利息，应在该一方免税",
  "interest received by a government or an institution recognised by both competent authorities is exempt")

# ---- added 2026-10-07 for the HK rule spec
p("hk.fsie.receipt_kinds", "HK", "ALL", "condition", "received_in_hk_kinds", "REMITTED;DEBT_SETTLED;MOVABLE_PROPERTY", "enum",
  "hk.cap112.en#s15H", "2023-01-01", "the sum is remitted to, or is transmitted or brought into, Hong Kong; (b) the sum is used to satisfy any debt incurred in respect of a trade, profession or business carried on in Hong Kong; or (c) the sum is used to buy movable property",
  "the three cases of 'received in Hong Kong' in s15H(5), matching the enum values of the dictionary field receipt_kind")
p("hk.fsie.nexus_uplift", "HK", "ROYALTY", "rate", "rd_fraction_uplift", 130, "%", "hk.cap112.en#sch17FC", "2024-01-01",
  "F = QE × 130% QE + NE", "nexus ratio F = QE×130%/(QE+NE), capped at 100% (Sch 17FC s3)")
p("hk.fsie.nexus_cap", "HK", "ROYALTY", "limit", "rd_fraction_cap", 100, "%", "hk.cap112.en#sch17FC", "2024-01-01",
  "ascertained in accordance with subsection (1) is more than 100%", "F is taken as 100% when it exceeds 100%")
p("hk.fsie.participation_resident_or_pe", "HK", "DIVIDEND", "condition", "participation_entity_resident_or_pe", 1, "bool",
  "hk.cap112.en#s15M", "2023-01-01", "a Hong Kong resident person; or (ii) a non-Hong Kong resident person who has a permanent establishment in Hong Kong",
  "the participation exemption is only for Hong Kong resident persons or non-residents with a permanent establishment in Hong Kong")
p("hk.onshore_gain.trading_stock_disregarded", "HK", "SHARE_TRANSFER", "condition", "trading_stock_periods_disregarded", 1, "bool",
  "hk.cap112.en#sch17K", "2024-01-01", "regarded as trading stock for any period are to be disregarded for the purposes of sections 5 and 6 of this Schedule",
  "periods in which the interest is treated as trading stock do not count towards the holding period and the 15% test")

# ---- added 2026-10-07 for the receiving-side rules (step 4)
p("sg.fsie.receipt_kinds", "SG", "ALL", "condition", "received_in_sg_kinds", "REMITTED;DEBT_SETTLED;MOVABLE_PROPERTY", "enum",
  "sg.ita1947.full#s10", "", "any amount from any income derived from outside Singapore which is remitted to, transmitted or brought into, Singapore; ( b ) any amount from any income derived from outside Singapore which is applied in or towards satisfaction of any debt incurred in respect of a trade or business carried on in Singapore; and ( c ) any amount from any income derived from outside Singapore which is applied to purchase any movable property which is brought into Singapore",
  "the three cases of 'received in Singapore' in s10(25), same structure as Hong Kong s15H(5)")
p("sg.ftc.unilateral_income", "SG", "ALL", "condition", "unilateral_credit_income_kinds", "dividend;royalty;interest;s10l_gain;other_income_nature", "enum",
  "sg.ita1947.full#s50A", "", "( c ) any dividend derived from that territory",
  "unilateral credit under s50A(1) covers dividends, royalties (not borne by a Singapore resident), interest (likewise), s10L gains and other income; for sources without a treaty such as Hong Kong and Macao")

# ---- added 2026-10-07: the payer's deduction (what makes debt vs equity and IP location comparable)
p("cn.eit.rate", "CN", "ALL", "rate", "corporate_income_tax_rate", 25, "%", "cn.law.eit#4", "2008-01-01",
  "企业所得税的税率为25％", "statutory rate for resident enterprises")
p("cn.deduct.general", "CN", "ALL", "condition", "reasonable_expense_deductible", 1, "bool", "cn.law.eit#8", "2008-01-01",
  "企业实际发生的与取得收入有关的、合理的支出，包括成本、费用、税金、损失和其他支出，准予在计算应纳税所得额时扣除",
  "reasonableness is an overall judgement, maps to U(DISCRETION)")
p("cn.thincap.disallow", "CN", "INTEREST", "anti_abuse", "excess_related_party_interest_not_deductible", 1, "bool", "cn.law.eit#46", "2008-01-01",
  "企业从其关联方接受的债权性投资与权益性投资的比例超过规定标准而发生的利息支出，不得在计算应纳税所得额时扣除", "thin capitalisation")
p("cn.thincap.ratio_other", "CN", "INTEREST", "condition", "related_debt_equity_ratio_other_enterprises", 2, "ratio", "cn.cs.2008-121#i1", "2008-01-01",
  "其他企业，为2：1", "related-party debt-to-equity cap of 2:1 for non-financial enterprises")
p("cn.thincap.ratio_financial", "CN", "INTEREST", "condition", "related_debt_equity_ratio_financial_enterprises", 5, "ratio", "cn.cs.2008-121#i1", "2008-01-01",
  "金融企业，为5：1", "5:1 for financial enterprises")
p("cn.thincap.arms_length_exception", "CN", "INTEREST", "condition", "excess_interest_deductible_if_arms_length", 1, "bool", "cn.cs.2008-121#i2", "2008-01-01",
  "证明相关交易活动符合独立交易原则的；或者该企业的实际税负不高于境内关联方的，其实际支付给境内关联方的利息支出，在计算应纳税所得额时准予扣除",
  "interest above the ratio remains deductible when the arm's length principle is demonstrated; overall judgement")
p("hk.deduct.general", "HK", "ALL", "condition", "outgoings_in_production_of_profits_deductible", 1, "bool", "hk.cap112.en#s16", "",
  "there shall be deducted all outgoings and expenses to the extent to which they are incurred during the basis period for that year of assessment by such person in the production of profits",
  "s16(1) general deduction")
p("sg.deduct.general", "SG", "ALL", "condition", "outgoings_wholly_exclusively_in_production_deductible", 1, "bool", "sg.ita1947.full#s14", "",
  "there are to be deducted all outgoings and expenses wholly and exclusively incurred during that period by that person in the production of the income",
  "s14(1) general deduction")

# ---- added 2026-10-07: Mainland deadline roll-over, MAP acceptance, intragroup clawback
p("cn.time.holiday_roll", "CN", "ALL", "limit", "last_day_on_public_holiday_rolls", 1, "bool", "cn.reg.tca#109", "2016-02-06",
  "期限的最后一日是法定休假日的，以休假日期满的次日为期限的最后一日", "实施细则 art. 109: when the last day falls on a statutory holiday it moves to the day after the holiday ends")
p("cn.time.long_holiday_days", "CN", "ALL", "limit", "consecutive_holiday_days_extend_by_count", 3, "days", "cn.reg.tca#109", "2016-02-06",
  "在期限内有连续３日以上法定休假日的，按休假日天数顺延", "when the period contains 3 or more consecutive statutory holiday days, it is extended by that number of days")
p("cn.map.actions", "CN", "ALL", "procedure", "map_requires_action_of_other_authority", "assessment;denial;adjustment", "enum", "cn.sta.2013-56#7", "2013-11-01",
  "缔约对方所采取的措施，已经或将会导致不符合税收协定所规定的征税行为", "mutual agreement is directed at the measures of the other side's tax authority")
p("cn.map.no_reacceptance_after", "CN", "ALL", "procedure", "no_reacceptance_after_withdrawal_or_refusal", "withdrawn;result_refused", "enum", "cn.sta.2013-56#19", "2013-11-01",
  "申请人撤回申请或者拒绝接受缔约双方主管当局达成一致的相互协商结果的，税务机关不再受理基于同一事实和理由的申请", "after a withdrawal or a rejected outcome no further application on the same facts is accepted")

# ---- added 2026-10-07: domestic remedies (objection, appeal, administrative review)
p("hk.objection.months", "HK", "ALL", "limit", "objection_months_after_notice_of_assessment", 1, "months", "hk.cap112.en#s64", "",
  "received by the Commissioner within 1 month after the date of the notice of assessment", "s64(1): written objection within 1 month of the notice of assessment")
p("hk.appeal.months", "HK", "ALL", "limit", "appeal_months_after_determination", 1, "months", "hk.cap112.en#s66", "",
  "1 month after the transmission to him under section 64(4) of the Commissioner’s written determination", "s66(1): appeal to the Board of Review within 1 month of the Commissioner's determination being served")
p("sg.objection.months_company", "SG", "ALL", "limit", "objection_months_company", 2, "months", "sg.ita1947.full#s76", "2014-01-01",
  "if the person is a company and the notice of assessment is served on the person on or after 1 January 2014, 2 months", "s76(3)(a): a company objects within 2 months of the notice of assessment being served")
p("cn.review.pay_first", "CN", "ALL", "procedure", "pay_or_secure_before_review", 1, "bool", "cn.law.tca#88", "",
  "必须先依照税务机关的纳税决定缴纳或者解缴税款及滞纳金或者提供相应的担保，然后可以依法申请行政复议", "tax disputes: administrative review comes first, after paying the tax or giving security")
p("cn.review.days", "CN", "ALL", "limit", "review_days_after_knowing", 60, "days", "cn.law.ar#20", "2024-01-01",
  "可以自知道或者应当知道该行政行为之日起六十日内提出行政复议申请", "行政复议法 art. 20: 60 days from the day of knowledge")

# ---- added 2026-10-07 (场景.md): explicit no-charge cites
p("hk.nocharge.scope", "HK", "ALL", "condition", "profits_tax_only_on_hk_business_profits", 1, "bool", "hk.cap112.en#s14", "",
  "on every person carrying on a trade, profession or business in Hong Kong in respect of his assessable profits arising in or derived from Hong Kong",
  "s14: profits tax reaches only the Hong Kong-sourced profits of those carrying on business in Hong Kong; Hong Kong has no withholding tax on dividends or interest, and non-residents' income is not charged")
p("sg.nocharge.dividend", "SG", "DIVIDEND", "condition", "one_tier_dividends_exempt", 1, "bool", "sg.ita1947.full#s13", "2008-01-01",
  "any dividends paid on or after 1 January 2008 by any company resident in Singapore", "s13(1)(za): dividends of Singapore companies are exempt under the one-tier corporate tax system")
# ---- CN residence side: worldwide income, foreign tax credit
p("cn.ftc.credit", "CN", "ALL", "condition", "foreign_tax_creditable", 1, "bool", "cn.law.eit#23", "2008-01-01",
  "企业取得的下列所得已在境外缴纳的所得税税额，可以从其当期应纳税额中抵免，抵免限额为该项所得依照本法规定计算的应纳税额",
  "art. 23: direct credit, limited to the tax payable on that income under this law; the excess is carried forward five years (cn.ftc.carryforward_years)")
p("cn.ftc.indirect", "CN", "DIVIDEND", "condition", "underlying_tax_creditable_if_controlled", 1, "bool", "cn.law.eit#24", "2008-01-01",
  "外国企业在境外实际缴纳的所得税税额中属于该项所得负担的部分，可以作为该居民企业的可抵免境外所得税税额",
  "art. 24: indirect credit, limited to foreign enterprises directly or indirectly controlled (20% or more, art. 80); tiers in cn.ftc.indirect_tiers")
p("cn.ftc.limit_per_country", "CN", "ALL", "condition", "credit_limit_per_country", 1, "bool", "cn.reg.eit#78", "2008-01-01",
  "该抵免限额应当分国(地区)不分项计算", "art. 78: per country without per item; 2017-84 allows electing no per-country split, fixed for 5 years once chosen")
p("cn.ftc.income_recognition_dividend", "CN", "DIVIDEND", "procedure", "foreign_dividend_recognised_on_resolution", 1, "bool", "cn.cs.2009-125#i3", "2010-01-01",
  "来源于境外的股息、红利等权益性投资收益，应按被投资方作出利润分配决定的日期确认收入实现", "foreign dividends are recognised on the date of the distribution resolution")
# ---- services and permanent establishment
p("cn.service.deemed_profit_design_min", "CN", "SERVICE_FEE", "rate", "deemed_profit_rate_engineering_design_consulting_min", 15, "%", "cn.gsf.2010-19#5", "2010-02-20",
  "从事承包工程作业、设计和咨询劳务的，利润率为15%-30%", "lower end of the deemed profit rate range")
p("cn.service.deemed_profit_design_max", "CN", "SERVICE_FEE", "rate", "deemed_profit_rate_engineering_design_consulting_max", 30, "%", "cn.gsf.2010-19#5", "2010-02-20",
  "从事承包工程作业、设计和咨询劳务的，利润率为15%-30%", "upper end of the deemed profit rate range")
p("cn.service.establishment", "CN", "SERVICE_FEE", "condition", "service_place_is_establishment", 1, "bool", "cn.reg.eit#5", "2008-01-01",
  "提供劳务的场所", "实施条例 art. 5: establishments and places include places where services are provided")
p("cn.eit.resident_worldwide", "CN", "ALL", "condition", "resident_taxed_on_worldwide_income", 1, "bool", "cn.law.eit#3", "2008-01-01",
  "居民企业应当就其来源于中国境内、境外的所得缴纳企业所得税", "taxing right on the residence side")
p("cn.eit.asset_net_value_deductible", "CN", "SHARE_TRANSFER", "condition", "asset_net_value_deductible_on_transfer", 1, "bool", "cn.law.eit#16", "2008-01-01",
  "企业转让资产，该项资产的净值，准予在计算应纳税所得额时扣除", "resident transferring equity: income = proceeds − net value")
p("cn.ftc.indirect_formula", "CN", "DIVIDEND", "condition", "underlying_tax_attributable_formula", 1, "bool", "cn.cs.2009-125#i5", "2010-01-01",
  "本层企业所纳税额属于由一家上一层企业负担的税额＝（本层企业就利润和投资收益所实际缴纳的税额+符合本通知规定的由本层企业间接负担的税额）×本层企业向一家上一层企业分配的股息（红利）÷本层企业所得税后利润额",
  "tier-by-tier formula for the tax borne indirectly; the field underlying_tax_share is given by this formula (as a percentage of the dividend)")
p("cn.ftc.gross_up", "CN", "DIVIDEND", "condition", "foreign_dividend_grossed_up_by_direct_and_underlying_tax", 1, "bool", "cn.sta.2010-01.a01#16", "2010-01-01",
  "该境外股息、红利所得应为境外股息、红利税后净所得与就该项所得直接缴纳和间接负担的税额之和",
  "操作指南 point 4: for indirect credit the dividend is grossed up by the tax paid directly and borne indirectly; the flow amount is already the gross before withholding, so the engine adds only the indirectly borne part")
# ---- 范围.md 1: the entity's own rate exists in each law (the rate the case states is the fact; these are the provenance)
p("cn.eit.rate_entity", "CN", "ALL", "condition", "entity_specific_rate_exists", 1, "bool", "cn.law.eit#28", "2008-01-01",
  "国家需要重点扶持的高新技术企业，减按15％的税率征收企业所得税", "the entity's applicable rate is the fact field cit_rate; this row is the provenance of its existence (15% for high-tech, 20% for small low-profit enterprises)")
p("hk.profits.rate_entity", "HK", "ALL", "condition", "entity_specific_rate_exists", 1, "bool", "hk.cap112.en#sch8B", "2018-04-01",
  "at the rate of 8.25% on section 14 assessable profits up to $2,000,000", "two-tiered: first HKD 2 million at 8.25%, the rest at 16.5%; the entity's marginal rate is the fact field cit_rate")
p("sg.corp.rate_entity", "SG", "ALL", "condition", "entity_specific_rate_exists", 1, "bool", "sg.ita1947.full#s43", "2020-01-01",
  "for every dollar of the first $10,000 of the chargeable income, only 25% is chargeable with tax", "s43(6B) partial exemption: first SGD 10,000 75% exempt, next 190,000 50% exempt; the entity's marginal rate is the fact field cit_rate")
# ---- 范围.md 3: interest deduction conditions
p("cn.deduct.interest_benchmark", "CN", "INTEREST", "condition", "interest_deductible_up_to_financial_enterprise_rate", 1, "bool", "cn.reg.eit#38", "2008-01-01",
  "非金融企业向非金融企业借款的利息支出，不超过按照金融企业同期同类贷款利率计算的数额的部分", "art. 38 item (2); item (1): borrowings from financial enterprises are fully deductible")
p("hk.deduct.interest_cond_fi", "HK", "INTEREST", "condition", "interest_deductible_if_lender_is_financial_institution", 1, "bool", "hk.cap112.en#s16", "",
  "the money has been borrowed from a financial institution or an overseas financial institution", "s16(2)(d)")
p("hk.deduct.interest_cond_lender_taxable", "HK", "INTEREST", "condition", "interest_deductible_if_taxable_in_lenders_hands", 1, "bool", "hk.cap112.en#s16", "",
  "the money has been borrowed from a person other than a financial institution or an overseas financial institution and the sums payable by way of interest are chargeable to tax under this Ordinance", "s16(2)(c)")
p("sg.deduct.interest_capital_employed", "SG", "INTEREST", "condition", "interest_deductible_if_capital_employed_in_acquiring_income", 1, "bool", "sg.ita1947.full#s14", "",
  "such sum is payable on capital employed in acquiring the income", "s14(1)(a): borrowings used to acquire exempt dividends are not deductible")
# ---- 范围.md 4: arm's length as a cap on the deduction when the taxpayer's own range is stated
p("cn.tp.adjust_to_median", "CN", "ALL", "condition", "tp_adjustment_to_interquartile_median", 1, "bool", "cn.sta.2017-06#25", "2017-05-01",
  "企业实际利润水平低于可比企业利润率区间中位值的，原则上应当按照不低于中位值进行调整", "interquartile method; payments above the upper bound of the range are not deductible; the original source 国税发〔2009〕2号 art. 41 was repealed by art. 62 of these measures")
p("hk.tp.arms_length", "HK", "ALL", "condition", "arms_length_principle_between_associated_persons", 1, "bool", "hk.cap112.en#s50AAF", "2018-07-13",
  "Arm’s length principle for provision between associated persons", "s50AAF Rule 1")
p("sg.tp.arms_length", "SG", "ALL", "condition", "related_party_transactions_at_arms_length", 1, "bool", "sg.ita1947.full#s34D", "",
  "Transactions not at arm’s length", "s34D(1A)")
# ---- 范围.md 2: stamp duty on share transfers
p("cn.stamp.equity_rate", "CN", "SHARE_TRANSFER", "rate", "stamp_duty_equity_transfer_instrument_rate", 0.05, "%", "cn.law.stamp.flk#20", "2022-07-01",
  "价款的万分之五", "印花税税目税率表: property transfer instruments — equity transfer instruments (excluding those liable to securities transaction stamp duty); PDF from the National Database of Laws and Regulations; the SAT law database attachment is an image .ppt, cn.law.stamp.sh is a government website repost")
p("cn.stamp.taxpayer_each_party", "CN", "SHARE_TRANSFER", "condition", "each_party_writing_the_instrument_is_taxpayer", 1, "bool", "cn.law.stamp.flk#1", "2022-07-01",
  "应当依照本法规定缴纳印花税", "art. 1: the units and individuals executing taxable instruments are the taxpayers; a property transfer instrument is executed by both parties, each paying its own tax")
p("hk.stamp.stock_rate", "HK", "SHARE_TRANSFER", "rate", "stamp_duty_contract_note_rate", 0.1, "%", "hk.cap117.en#sch1", "2023-11-17",
  "0.1% of the amount of the consideration or of its value at the date on which the contract note falls to be executed", "First Schedule head 2(1)(A); one contract note each for buyer and seller, 0.1% each")
p("hk.stamp.contract_note_each_party", "HK", "SHARE_TRANSFER", "condition", "contract_note_by_each_party", 1, "bool", "hk.cap117.en#s19", "",
  "any person who effects any sale or purchase of Hong Kong stock as principal or agent shall", "s19(1): seller and buyer each make and stamp a contract note")
# ---- 范围.md 4: documentation clocks, adjustment interest, surcharge
p("cn.tp.local_file_other_threshold", "CN", "ALL", "condition", "local_file_threshold_other_related_dealings", 40000000, "CNY", "cn.sta.2016-42#i13", "2016-01-01",
  "其他关联交易金额合计超过4000万元", "tangible assets 200 million, financial assets 100 million and intangible assets 100 million are the other three tiers; the model prices only interest, royalties and service fees, so the 'other' tier is taken")
p("cn.tp.local_file_due", "CN", "ALL", "procedure", "local_file_due_date", "next_year_june_30", "text", "cn.sta.2016-42#i19", "2016-01-01",
  "本地文档和特殊事项文档应当在关联交易发生年度次年6月30日之前准备完毕", "")
p("cn.tp.interest_spread", "CN", "ALL", "rate", "special_adjustment_interest_spread_over_benchmark", 5, "%", "cn.sta.2017-06#44", "2017-05-01",
  "加5个百分点计算，并按照一年365天折算日利息率", "percentage points; daily interest computed on 365 days")
p("cn.tp.interest_from", "CN", "ALL", "procedure", "special_adjustment_interest_runs_from", "next_year_june_1", "text", "cn.sta.2017-06#44", "2017-05-01",
  "自税款所属纳税年度的次年6月1日起至缴纳或者补缴税款之日止计算加收利息", "")
p("cn.tp.interest_base_only_with_docs", "CN", "ALL", "condition", "benchmark_only_if_documentation_provided", 1, "bool", "cn.sta.2017-06#44", "2017-05-01",
  "可以只按照基准利率加收利息", "art. 44 para. 2 item (3)")
p("hk.tp.local_file_months", "HK", "ALL", "limit", "master_and_local_file_within_months_after_period", 9, "months", "hk.cap112.en#s58C", "2018-07-13",
  "prepare, within 9 months after the end of each accounting period of the entity, a file in respect of the accounting period (local file)", "")
p("hk.tp.threshold_revenue", "HK", "ALL", "condition", "small_entity_revenue_threshold", 400000000, "HKD", "hk.cap112.en#sch17I", "2018-07-13",
  "total amount of revenue $400 million", "Sch 17I s4(a); exempt when any two are not exceeded")
p("hk.tp.threshold_assets", "HK", "ALL", "condition", "small_entity_assets_threshold", 300000000, "HKD", "hk.cap112.en#sch17I", "2018-07-13",
  "total value of assets $300 million", "Sch 17I s4(b)")
p("hk.tp.threshold_employees", "HK", "ALL", "condition", "small_entity_employees_threshold", 100, "persons", "hk.cap112.en#sch17I", "2018-07-13",
  "average number of employees 100", "Sch 17I s4(c)")
p("sg.tp.documentation_revenue_min", "SG", "ALL", "condition", "tp_documentation_gross_revenue_threshold", 10000000, "SGD", "sg.ita1947.full#s34F", "2019-01-01",
  "if the gross revenue of the company, firm or trust derived from its trade or business for the basis period concerned is more than $10 million", "s34F(2)(a)")
p("sg.tp.documentation_due", "SG", "ALL", "procedure", "tp_documentation_due", "return_due_30_nov", "text", "sg.ita1947.full#s34F", "2019-01-01",
  "must be prepared no later than the time for the making of the return", "s34F(5)(a); the Act itself sets no date (s62 leaves it to a notice); the filing deadline is supplied by the case as the fact return_due_on")
p("sg.corp.return_due", "SG", "ALL", "procedure", "corporate_return_filing_due", "30 Nov", "text", "sg.iras.formc#h2", "",
  "must be filed by 30 Nov every year", "IRAS page (practice, grade B): Form C-S / Form C filed by 30 November each year; the Act itself leaves the deadline to a notice (s62)")
p("sg.tp.surcharge_rate", "SG", "ALL", "rate", "tp_adjustment_surcharge", 5, "%", "sg.ita1947.full#s34E", "2019-01-01",
  "a surcharge equal to 5% of the amount of the increase or reduction", "s34E(1)")
# ---- 范围.md 5: controlled foreign companies
p("cn.cfc.definition", "CN", "ALL", "condition", "cfc_undistributed_profit_included", 1, "bool", "cn.law.eit#45", "2008-01-01",
  "并非由于合理的经营需要而对利润不作分配或者减少分配的，上述利润中应归属于该居民企业的部分，应当计入该居民企业的当期收入", "")
p("cn.cfc.control_single_min", "CN", "ALL", "condition", "cfc_control_single_holder_min", 10, "%", "cn.reg.eit#117", "2008-01-01",
  "直接或者间接单一持有外国企业10%以上有表决权股份", "")
p("cn.cfc.control_joint_min", "CN", "ALL", "condition", "cfc_control_joint_min", 50, "%", "cn.reg.eit#117", "2008-01-01",
  "共同持有该外国企业50%以上股份", "")
p("cn.cfc.chain_over_50_counts_100", "CN", "ALL", "condition", "cfc_chain_tier_over_50_counts_100", 1, "bool", "cn.sta.2023-17#i2", "2023-10-10",
  "中间层持有股份超过50%的，按100%计算", "decision D39: the original source 国税发〔2009〕2号 art. 77 was repealed by art. 4 of this announcement; the same rule is in art. 2 para. 2 of this announcement")
p("cn.cfc.low_tax_ratio", "CN", "ALL", "condition", "cfc_low_tax_share_of_statutory_rate", 50, "%", "cn.reg.eit#118", "2008-01-01",
  "低于企业所得税法第四条第一款规定税率的50%", "i.e. effective tax burden < 12.5%; the field cfc_tax_burden_ratio is the effective burden as a percentage of the statutory rate")
p("cn.cfc.exempt_whitelist", "CN", "ALL", "condition", "cfc_exempt_if_in_designated_non_low_tax_jurisdiction", 1, "bool", "cn.gsf.2009-02#84", "2008-01-01",
  "设立在国家税务总局指定的非低税率国家（地区）", "")
p("cn.cfc.whitelist", "CN", "ALL", "condition", "cfc_designated_non_low_tax_jurisdictions", "US;GB;FR;DE;JP;IT;CA;AU;IN;ZA;NZ;NO", "enum", "cn.gsh.2009-37#all", "2009-01-21",
  "美国、英国、法国、德国、日本、意大利、加拿大、澳大利亚、印度、南非、新西兰和挪威", "Hong Kong and Singapore are not on the list")
p("cn.cfc.exempt_active", "CN", "ALL", "condition", "cfc_exempt_if_mainly_active_income", 1, "bool", "cn.gsf.2009-02#84", "2008-01-01",
  "主要取得积极经营活动所得", "discretion")
p("cn.cfc.exempt_profit_max", "CN", "ALL", "condition", "cfc_exempt_if_annual_profit_below", 5000000, "CNY", "cn.gsf.2009-02#84", "2008-01-01",
  "年度利润总额低于500万元人民币", "")
p("cn.cfc.credit", "CN", "ALL", "condition", "cfc_inclusion_foreign_tax_creditable", 1, "bool", "cn.gsf.2009-02#82", "2008-01-01",
  "计入中国居民企业股东当期所得已在境外缴纳的企业所得税税款，可按照所得税法或税收协定的有关规定抵免", "")
# ---- decision D23: the VAT Law and its Regulations from 2026-01-01 (cross-border services, IP, leases)
V = "cn.law.vat"
p("cn.vat.law.taxable_in_cn", "CN", "ALL", "condition", "services_and_ip_taxable_where_consumed_or_seller_domestic", 1, "bool", V + "#4", "2026-01-01",
  "除本条第二项、第三项规定外，销售服务、无形资产的，服务、无形资产在境内消费，或者销售方为境内单位和个人", "art. 4 item (4)")
p("cn.vat.law.consumed_in_cn", "CN", "ALL", "condition", "foreign_seller_to_domestic_buyer_consumed_in_cn", 1, "bool", "cn.reg.vat#4", "2026-01-01",
  "境外单位或者个人向境内单位或者个人销售服务、无形资产，在境外现场消费的服务除外", "实施条例 art. 4 item (1); no exception for intangibles used abroad")
p("cn.vat.law.rate_services", "CN", "ALL", "rate", "vat_rate_services_and_ip", 6, "%", V + "#10", "2026-01-01",
  "纳税人销售服务、无形资产，除本条第一项、第二项、第五项规定外，税率为百分之六", "art. 10 item (3)")
p("cn.vat.law.rate_tangible_lease", "CN", "ROYALTY", "rate", "vat_rate_tangible_movable_lease", 13, "%", V + "#10", "2026-01-01",
  "纳税人销售货物、加工修理修配服务、有形动产租赁服务，进口货物，除本条第二项、第四项、第五项规定外，税率为百分之十三", "art. 10 item (1)")
p("cn.vat.law.withholding_agent", "CN", "ALL", "condition", "purchaser_withholds_vat_for_foreign_seller", 1, "bool", V + "#15", "2026-01-01",
  "境外单位和个人在境内发生应税交易，以购买方为扣缴义务人", "art. 15 para. 1")
p("cn.vat.law.withheld_on_sales", "CN", "ALL", "condition", "withheld_vat_is_sales_amount_times_rate", 1, "bool", V + "#15", "2026-01-01",
  "按照销售额乘以税率计算应扣缴税额", "art. 15 para. 2; the sales amount excludes VAT (art. 17)")
p("cn.vat.law.inclusive_price", "CN", "ALL", "condition", "vat_inclusive_price_divided_by_one_plus_rate", 1, "bool", "cn.reg.vat#16", "2026-01-01",
  "一般计税方法的销售额＝含税销售额÷（1＋税率）", "实施条例 art. 16: applies only to a combined price (VAT-inclusive); whether the price includes VAT is a contract fact")
p("cn.vat.law.input_credit", "CN", "ALL", "condition", "withheld_vat_creditable_as_input", 1, "bool", "cn.reg.vat#12", "2026-01-01",
  "自境外单位或者个人购进服务、无形资产或者境内不动产取得的完税凭证上列明的增值税税额", "实施条例 art. 12 item (3); general taxpayers")
p("cn.vat.law.input_credit_invoice", "CN", "ALL", "condition", "domestic_purchase_vat_creditable_on_special_invoice", 1, "bool", "cn.reg.vat#12", "2026-01-01",
  "从销售方取得的增值税专用发票上列明的增值税税额", "实施条例 art. 12 item (1)")
p("cn.vat.law.input_documents", "CN", "ALL", "condition", "credit_on_tax_receipt_needs_contract_payment_proof_statement", 1, "bool", "cn.cs.2026-input#i1", "2026-01-01",
  "一般纳税人凭完税凭证抵扣进项税额的，应当具备书面合同、付款证明和境外单位的对账单或者发票", "art. 1 item (5); no credit without the documents")
p("cn.vat.tech_transfer_exempt", "CN", "IP_TRANSFER", "condition", "technology_transfer_vat_exempt", 1, "bool", "cn.cs.2026-10#i2", "2026-01-01",
  "纳税人提供技术转让、技术开发和与之相关的技术咨询、技术服务", "art. 2 item (1) sub-item 2; no end date")
p("cn.vat.tech_recognition", "CN", "IP_TRANSFER", "procedure", "technology_contract_recognised_by_provincial_authority", 1, "bool", "cn.cs.2026-10#i2", "2026-01-01",
  "到纳税人所在地省级科技、工信主管部门进行认定", "recognised on the written contract, with the review opinion filed with the competent tax authority for record; a foreign seller has no 'place of location', whether recognition is possible is the tax authority's judgement")
p("cn.vat.tech_kinds", "CN", "IP_TRANSFER", "condition", "technology_for_vat", "PATENT;KNOW_HOW", "enum", "cn.cs.2026-09.a02#p19", "2026-01-01",
  "技术，包括专利技术和非专利技术", "附件2 《销售服务、无形资产、不动产注释》; software copyright, trademarks and the like are not 'technology'")
# ---- decision D25: VAT on interest (a loan service), both regimes
p("cn.vat.law.loan_services", "CN", "INTEREST", "condition", "loan_service_is_a_service", 1, "bool", "cn.reg.vat#2", "2026-01-01",
  "增值税法第三条所称服务，包括交通运输服务、邮政服务、电信服务、建筑服务、金融服务", "financial services include loan services (公告2026年第9号 附件2 notes)")
p("cn.vat.law.loan_input_not_creditable", "CN", "INTEREST", "condition", "loan_service_input_vat_not_creditable", 1, "bool", "cn.reg.vat#21", "2026-01-01",
  "纳税人购进贷款服务的利息支出，及其向贷款方支付的与该贷款服务直接相关的投融资顾问费、手续费、咨询费等费用支出，对应的进项税额暂不得从销项税额中抵扣",
  "the VAT on interest is a cost of the borrower")
p("cn.vat.law.unified_borrowing_exempt", "CN", "INTEREST", "condition", "unified_borrowing_relending_interest_exempt", 1, "bool", "cn.cs.2026-10#i2", "2026-01-01",
  "统借统还业务利息收入，是指统借统还业务中，企业集团或企业集团中的核心企业以及集团所属财务公司按不高于支付给金融机构的借款利率水平或者支付的债券票面利率水平，向企业集团或者集团内下属单位收取的利息",
  "field unified_borrowing_relending; presumed false for a lender outside the group")
# ---- decision D26: a non-resident's income net of the VAT
p("cn.wht.base_excludes_vat", "CN", "ALL", "condition", "nonresident_income_net_of_vat", 1, "bool", "cn.sta.2013-09#all", "2013-02-19",
  "应以不含增值税的收入全额作为应纳税所得额", "income under 企业所得税法 art. 3 para. 3; the SAT law database marks it fully in force (2026-10-09)")
# ---- decision D29: a Mainland company's revenue net of the VAT on its own sale
p("cn.eit.revenue_excludes_output_vat", "CN", "ALL", "condition", "resident_revenue_net_of_output_vat", 1, "bool", "cn.mof.2016-22#i2", "2016-12-03",
  "按取得的收入金额，贷记“主营业务收入”、“其他业务收入”、“固定资产清理”、“工程结算”等科目，按现行增值税制度规定计算的销项税额（或采用简易计税方法计算的应纳增值税额），贷记“应交税费——应交增值税（销项税额)”",
  "增值税会计处理规定 II(2)1; annual return A101010 reports revenue under the national unified accounting system; 收入准则 art. 14: amounts collected on behalf of third parties are not part of the transaction price")
# ---- decision D22: the IP transfer step — Mainland income tax
p("cn.ip.transfer_income", "CN", "IP_TRANSFER", "condition", "ip_disposal_is_property_transfer_income", 1, "bool", "cn.reg.eit#16", "2008-01-01",
  "转让固定资产、生物资产、无形资产、股权、债权等财产取得的收入", "a transfer of ownership is income from the transfer of property, not a royalty (art. 20 covers the right of use)")
p("cn.ip.net_value", "CN", "IP_TRANSFER", "condition", "net_value_is_basis_less_amortisation", 1, "bool", "cn.reg.eit#74", "2008-01-01",
  "是指有关资产、财产的计税基础减除已经按照规定扣除的折旧、折耗、摊销、准备金等后的余额", "the field cost_basis is that net value")
p("cn.ip.nonresident_gain_base", "CN", "IP_TRANSFER", "condition", "nonresident_gain_is_proceeds_less_net_value", 1, "bool", "cn.law.eit#19", "2008-01-01",
  "转让财产所得，以收入全额减除财产净值后的余额为应纳税所得额", "art. 19 item (2)")
p("cn.ip.source_other_income", "CN", "IP_TRANSFER", "condition", "source_of_other_income_set_by_mof_sat", 1, "bool", "cn.reg.eit#7", "2008-01-01",
  "其他所得，由国务院财政、税务主管部门确定", "art. 7 item (3) lists only immovable property, movable property and equity investment assets; the source of income from transferring intangibles has not been determined by the competent authority, left to the tax authority's judgement")
p("cn.tech.exempt_max", "CN", "IP_TRANSFER", "limit", "technology_transfer_income_exempt_up_to", 5000000, "CNY", "cn.reg.eit#90", "2008-01-01",
  "居民企业技术转让所得不超过500万元的部分，免征企业所得税", "within one tax year; case amounts converted at cny_rate")
p("cn.tech.excess_rate", "CN", "IP_TRANSFER", "rate", "technology_transfer_income_excess_taxed_share", 50, "%", "cn.reg.eit#90", "2008-01-01",
  "超过500万元的部分，减半征收企业所得税")
p("cn.tech.kinds", "CN", "IP_TRANSFER", "condition", "technology_kinds_for_reduction", "PATENT;SOFTWARE_COPYRIGHT;IC_LAYOUT;PLANT_VARIETY;BIOMEDICINE_VARIETY", "enum",
  "cn.cs.2010-111#i1", "2008-01-01", "包括居民企业转让专利技术、计算机软件著作权、集成电路布图设计权、植物新品种、生物医药新品种",
  "non-patented technology (know-how) is not listed")
p("cn.tech.ownership_or_licence", "CN", "IP_TRANSFER", "condition", "transfer_of_ownership_or_5y_global_exclusive_licence", 1, "bool", "cn.cs.2010-111#i2", "2008-01-01",
  "转让其拥有符合本通知第一条规定技术的所有权或5年以上（含5年）全球独占许可使用权的行为", "this template is a transfer of ownership")
p("cn.tech.registration", "CN", "IP_TRANSFER", "procedure", "technology_contract_registered", 1, "bool", "cn.cs.2010-111#i3", "2008-01-01",
  "境内的技术转让须经省级以上（含省级）科技部门认定登记，跨境的技术转让须经省级以上（含省级）商务部门认定登记", "plan action")
p("cn.tech.export_restricted_excluded", "CN", "IP_TRANSFER", "condition", "restricted_or_prohibited_export_technology_excluded", 1, "bool", "cn.cs.2010-111#i3", "2008-01-01",
  "居民企业取得禁止出口和限制出口技术转让所得，不享受技术转让减免企业所得税优惠政策", "technology exports only; the engine presumes false for a domestic buyer")
p("cn.tech.related_100_excluded", "CN", "IP_TRANSFER", "condition", "transfer_from_100pct_related_party_excluded", 1, "bool", "cn.cs.2010-111#i4", "2008-01-01",
  "居民企业从直接或间接持有股权之和达到100%的关联方取得的技术转让所得，不享受技术转让减免企业所得税优惠政策",
  "one party wholly owns the other directly or indirectly: the engine derives it; sister companies wholly owned by the same shareholder are not expressly covered, left to the tax authority's judgement")
p("cn.ip.amortization_years_min", "CN", "IP_TRANSFER", "limit", "intangible_amortisation_years_min", 10, "years", "cn.reg.eit#67", "2008-01-01",
  "无形资产的摊销年限不得低于10年")
p("cn.ip.amortization_agreed_life", "CN", "IP_TRANSFER", "condition", "acquired_intangible_amortised_over_legal_or_agreed_life", 1, "bool", "cn.reg.eit#67", "2008-01-01",
  "作为投资或者受让的无形资产，有关法律规定或者合同约定了使用年限的，可以按照规定或者约定的使用年限分期摊销", "field ip_useful_life_years")
p("cn.stamp.ip_rate", "CN", "IP_TRANSFER", "rate", "stamp_duty_ip_transfer_instrument_rate", 0.03, "%", "cn.law.stamp.flk#20", "2022-07-01",
  "商标专用权、著作权、专利权、专有技术使用权转让书据价款的万分之三", "property transfer instruments; technology contracts are also 0.03%")
p("cn.stamp.abroad_used_in_cn", "CN", "IP_TRANSFER", "condition", "instrument_written_abroad_used_in_cn_taxable", 1, "bool", "cn.law.stamp.flk#1", "2022-07-01",
  "在中华人民共和国境外书立在境内使用的应税凭证的单位和个人，应当依照本法规定缴纳印花税", "when both parties are abroad, it depends on whether the instrument is used in the Mainland (e.g. registering a Mainland patent or trademark transfer)")
# ---- decision D28: the IP step at book value between Mainland companies
p("cn.reorg.transfer_mode", "CN", "IP_TRANSFER", "condition", "transfer_at_book_value_between_wholly_held_residents", "BOOK", "enum",
  "cn.cs.2014-109#i3", "2014-01-01", "按账面净值划转股权或资产", "between a parent and a subsidiary under 100% direct control, or between resident enterprises under the 100% direct control of the same resident enterprise(s); the template offers this mode only then")
p("cn.reorg.transfer_keep_months", "CN", "IP_TRANSFER", "limit", "no_change_of_business_months_after_transfer", 12, "months",
  "cn.cs.2014-109#i3", "2014-01-01", "股权或资产划转后连续12个月内不改变被划转股权或资产原来实质性经营活动", "plan action reorg_operations_unchanged_12m")
p("cn.reorg.transfer_filing", "CN", "IP_TRANSFER", "procedure", "special_treatment_return_filed", 1, "bool", "cn.sta.2015-40#i5", "2014-01-01",
  "分别向各自主管税务机关报送《居民企业资产（股权）划转特殊性税务处理申报表》", "plan action reorg_filed; at the annual EIT settlement")
p("cn.reorg.transfer_no_gain", "CN", "IP_TRANSFER", "condition", "neither_side_recognises_income", 1, "bool", "cn.cs.2014-109#i3", "2014-01-01",
  "划出方企业和划入方企业均不确认所得")
p("cn.reorg.transfer_basis", "CN", "IP_TRANSFER", "condition", "buyer_amortises_seller_tax_basis", 1, "bool", "cn.sta.2015-40#i3", "2014-01-01",
  "应按被划转资产的原计税基础计算折旧扣除或摊销")
p("cn.reorg.transfer_fails_deemed_sale", "CN", "IP_TRANSFER", "condition", "conditions_broken_deemed_sale_at_fair_value", 1, "bool", "cn.sta.2015-40#i8",
  "2014-01-01", "划出方应按原划转完成时股权或资产的公允价值视同销售处理", "art. 8 item (1) sub-item 4; the transferee takes fair value as its tax basis")
p("cn.vat.law.deemed_sale_market_value", "CN", "IP_TRANSFER", "condition", "deemed_sale_valued_at_market_price", 1, "bool", "cn.law.vat#19", "2026-01-01",
  "发生本法第五条规定的视同应税交易以及销售额为非货币形式的，纳税人应当按照市场价格确定销售额", "art. 5 item (3): a gratuitous transfer of intangibles is deemed a taxable transaction")
p("cn.stamp.unstated_amount_market_price", "CN", "IP_TRANSFER", "condition", "unstated_amount_taxed_at_market_price", 1, "bool", "cn.law.stamp.flk#6",
  "2022-07-01", "书立合同、产权转移书据时的市场价格确定", "art. 6 para. 2: when the tax basis still cannot be determined from the actual settlement amount, the market price at execution is used")
p("cn.stamp.restructuring_exemption_scope", "CN", "IP_TRANSFER", "condition", "restructuring_exemption_not_for_ip_transfers", 1, "bool",
  "cn.cs.2024-14#i3", "2024-10-01", "对企业改制、合并、分立、破产清算以及事业单位改制书立的产权转移书据，免征印花税",
  "the intra-group transfer exemption lists only land use rights, buildings and structures; IP transfers remain taxable", to="2027-12-31")
# ---- decision D22: the treaties — gains from other property are taxed only where the seller resides
p("cn-hk.gain.other_residence_only", HK, "IP_TRANSFER", "condition", "other_property_gains_residence_only", 1, "bool", "treaty.cn-hk.2006.p4.zh#3", "2015-12-29",
  "转让第一款至第五款所述财产以外的其它财产取得的收益，应仅在转让者为其居民的一方征税", "Fourth Protocol art. 3 (art. 13 para. 7); effective and application dates: see cn.sta.2016-12")
p("cn-sg.gain.other_residence_only", SG, "IP_TRANSFER", "condition", "other_property_gains_residence_only", 1, "bool", AS + "#13.6", "2008-01-01",
  "缔约国一方居民转让本条以上各款所述财产以外的其他财产取得的收益，应仅在转让者为其居民的缔约国征税", n28)
# ---- decision D22: Hong Kong
p("hk.ip.clawback", "HK", "IP_TRANSFER", "condition", "proceeds_up_to_deductions_allowed_are_trading_receipt", 1, "bool", "hk.cap112.en#s16E", "",
  "do not exceed the amount of the deduction, to be treated as a trading receipt of the trade, profession or business, arising in or derived from Hong Kong",
  "s16E(3) patent rights, know-how")
p("hk.ip.clawback_specified", "HK", "IP_TRANSFER", "condition", "excess_over_unallowed_up_to_deductions_is_trading_receipt", 1, "bool", "hk.cap112.en#s16EB", "",
  "the excess is, to the extent that it is not chargeable to tax under any other section of this Part and does not exceed the amount of the deduction, to be treated as a trading receipt",
  "s16EB(2) copyright, registered designs, registered trade marks")
p("hk.ip.purchase_from_associate_no_deduction", "HK", "IP_TRANSFER", "condition", "no_deduction_for_ip_bought_from_associate", 1, "bool", "hk.cap112.en#s16EC", "",
  "No deduction is allowable under section 16E or 16EA in respect of any relevant right purchased by a person wholly or partly from an associate",
  "s16EC(2); no deduction for the buyer in an intra-group transfer")
p("hk.fsie.ip_disposal_gain", "HK", "IP_TRANSFER", "condition", "ip_disposal_gain_is_specified_foreign_sourced_income", 1, "bool", "hk.cap112.en#s15H", "2024-01-01",
  "means any gain or profit derived from the sale of intellectual property", "32 of 2023; foreign-sourced, must be received in Hong Kong")
p("hk.fsie.ip_disposal_not_capital", "HK", "IP_TRANSFER", "condition", "fsie_receipt_not_capital", 1, "bool", "hk.cap112.en#s15I", "2024-01-01",
  "is to be regarded as not arising from the sale of capital assets even if it so arises", "s15I(1)(b)")
p("hk.fsie.qualifying_ip_kinds", "HK", "IP_TRANSFER", "condition", "qualifying_ip_for_nexus", "PATENT;SOFTWARE_COPYRIGHT", "enum", "hk.cap112.en#sch17FC", "2024-01-01",
  "a copyright subsisting in software under the Copyright Ordinance (Cap. 528) or under the law of any place outside Hong Kong",
  "Sch 17FC s1(2): patents (including applications) and software copyright; gains on disposal of qualifying IP are exempted by the R&D fraction")
# ---- decision D22: Singapore
p("sg.ip.balancing_charge", "SG", "IP_TRANSFER", "condition", "sale_within_wda_period_charge", 1, "bool", "sg.ita1947.full#s19B", "2016-01-01",
  "a charge of an amount equal to the lower of", "s19B(4): the excess of the sale price over the writing-down allowances not yet given, capped at the allowances given")
p("sg.ip.charge_after_period", "SG", "IP_TRANSFER", "condition", "sale_after_wda_period_charge", 1, "bool", "sg.ita1947.full#s19B", "2016-01-01",
  "a charge in an amount equal to the price which the rights were sold, transferred or assigned or in an amount equal to the capital expenditure incurred in acquiring the rights, whichever is less",
  "s19B(5)")
p("sg.ip.wda_years", "SG", "IP_TRANSFER", "limit", "wda_period_shortest_election", 5, "years", "sg.ita1947.full#s19B", "2016-01-01",
  "5 years, 10 years or 15 years (as elected by the company)",
  "s19B(1AA), (1AB): irrevocable election, minimum 5 years; s19B(10)(aa): no allowance for IP acquired after the end of the basis period for YA 2028; by calendar financial year (a new company's financial year is set by the plan design)",
  to="2027-12-31")
p("sg.ip.wda_regime", "SG", "IP_TRANSFER", "condition", "wda_for_rights_acquired_from_ya2017_basis_period", 1, "bool", "sg.ita1947.full#s19B", "2016-01-01",
  "the acquisition date of those rights is on or after the first day of the basis period relating to the year of assessment 2017",
  "s19B(1AA)(b); cut-off in s19B(10)(aa)", to="2027-12-31")
p("sg.ip.wda_related_party_denial", "SG", "IP_TRANSFER", "condition", "no_wda_from_related_party_with_sg_creation_deductions", 1, "bool", "sg.ita1947.full#s19B", "2016-01-01",
  "whose proceeds from the sale, transfer or assignment of those intellectual property rights to the company are not chargeable to tax",
  "s19B(10A)(a): no allowance when the seller obtained a Singapore deduction for creating the IP and its sale proceeds are not taxed; not applicable to a foreign seller")
p("sg.ip.assignee_undertaking", "SG", "IP_TRANSFER", "procedure", "wda_needs_assignee_undertaking", 1, "bool", "sg.ita1947.full#s19B", "2016-01-01",
  "there is an undertaking by the company that it is an assignee of the intellectual property rights", "s19B(2A)(a)")
p("sg.ip.owner_situs", "SG", "IP_TRANSFER", "condition", "ip_situated_where_owner_resident", 1, "bool", "sg.ita1947.full#s10L", "2024-01-01",
  "any intellectual property right, or any licence or other right in respect of any intellectual property right, is situated where the owner of the intellectual property right, licence or right is resident",
  "s10L(15)(k): IP of a Singapore-resident seller is situated in Singapore, not a foreign asset under s10L")
p("sg.ip.purchase_not_use", "SG", "IP_TRANSFER", "condition", "deemed_source_covers_use_payments_only", 1, "bool", "sg.ita1947.full#s12", "",
  "royalty or other payment in one lump sum or otherwise for the use of or the right to use any movable property",
  "s12(7)(a): covers only payments for use; the price for a transfer of ownership is not deemed Singapore source, no withholding")
# ---- 范围.md 6: residence by place of effective management
p("cn.residence.pem_criteria", "CN", "ALL", "basis", "foreign_incorporated_cn_controlled_company_resident_if_four_criteria", 1, "bool", "cn.gsf.2009-82#i2", "2008-01-01",
  "境外中资企业同时符合以下条件的，根据企业所得税法第二条第二款和实施条例第四条的规定，应判定其为实际管理机构在中国境内的居民企业", "the four criteria are fact fields; recognition is confirmed by the tax authority (discretion); the engine takes the bound by graph variant")
p("cn.residence.substance_over_form", "CN", "ALL", "basis", "effective_management_substance_over_form", 1, "bool", "cn.gsf.2009-82#i3", "2008-01-01",
  "对于实际管理机构的判断，应当遵循实质重于形式的原则", "")
p("cn.residence.application", "CN", "ALL", "basis", "resident_determination_by_application_to_investor_authority", 1, "bool", "cn.sta.2014-09#i1", "2014-01-29",
  "须向其中国境内主要投资者登记注册地主管税务机关提出居民企业认定申请", "公告2014年第9号 art. 1")
# ---- 范围.md 9: Pillar Two (Hong Kong ordinance; Singapore's Act when the library has its text)
p("p2.revenue_threshold", "HK", "ALL", "condition", "globe_revenue_threshold", 750000000, "EUR", "hk.ord.2025-21#p42", "2025-01-01",
  "annual revenue of EUR 750 million or more in the consolidated financial statements of the ultimate parent entity", "GloBE Art 1.1.1, two or more of the four preceding fiscal years")
p("p2.minimum_rate", "HK", "ALL", "rate", "globe_minimum_rate", 15, "%", "hk.ord.2025-21#p147", "2025-01-01",
  "Minimum rate (最低稅率) means fifteen percent (15%)", "GloBE Art 10.1")
p("p2.sbie_payroll_rate", "HK", "ALL", "rate", "sbie_payroll_carve_out_rate", 5, "%", "hk.ord.2025-21#p86", "2025-01-01",
  "The payroll carve-out for a constituent entity located in a jurisdiction is equal to 5% of its eligible payroll costs", "GloBE Art 5.3.3; transition period per p2.sbie_payroll_transition")
p("p2.sbie_tangible_rate", "HK", "ALL", "rate", "sbie_tangible_asset_carve_out_rate", 5, "%", "hk.ord.2025-21#p87", "2025-01-01",
  "The tangible asset carve-out for a constituent entity located in a jurisdiction is equal to 5% of the carrying value of eligible tangible assets located in such jurisdiction", "GloBE Art 5.3.4")
p("p2.sbie_payroll_transition", "HK", "ALL", "procedure", "sbie_payroll_rate_by_fiscal_year", "2023:10;2024:9.8;2025:9.6;2026:9.4;2027:9.2;2028:9.0;2029:8.2;2030:7.4;2031:6.6;2032:5.8", "text", "hk.ord.2025-21#p120", "2025-01-01",
  "Fiscal Year Beginning In Article 5.3.3 Rate 2023 10% 2024 9.8% 2025 9.6% 2026 9.4% 2027 9.2% 2028 9.0% 2029 8.2% 2030 7.4% 2031 6.6% 2032 5.8%", "GloBE Art 9.2.1")
p("p2.sbie_tangible_transition", "HK", "ALL", "procedure", "sbie_tangible_rate_by_fiscal_year", "2023:8.0;2024:7.8;2025:7.6;2026:7.4;2027:7.2;2028:7.0;2029:6.6;2030:6.2;2031:5.8;2032:5.4", "text", "hk.ord.2025-21#p121", "2025-01-01",
  "Article 5.3.4 Rate 2023 8.0% 2024 7.8% 2025 7.6% 2026 7.4% 2027 7.2% 2028 7.0% 2029 6.6% 2030 6.2% 2031 5.8% 2032 5.4%", "GloBE Art 9.2.2")
p("hk.p2.hkmtt", "HK", "ALL", "condition", "hong_kong_minimum_top_up_tax_charged", 1, "bool", "hk.ord.2025-21#p21", "2025-01-01",
  "Schedule 62 has effect for charging a domestic minimum top-up tax within the meaning of the OECD GloBE model rules, to be called the Hong Kong minimum top-up tax or HKMTT", "s26AE(4)")
# ---- Singapore stamp duty, GST reverse charge, Pillar Two (范围.md 2, 7, 9)
p("sg.stamp.share_rate", "SG", "SHARE_TRANSFER", "rate", "stamp_duty_transfer_of_shares_rate", 0.2, "%", "sg.sda1929.sch1#sch1", "2014-02-22",
  "if executed on or after 22 February 2014 0.2% of the amount of the consideration", "First Schedule Article 3(c)(ii)")
p("sg.stamp.transferee_pays", "SG", "SHARE_TRANSFER", "condition", "stamp_duty_on_conveyance_paid_by_transferee", 1, "bool", "sg.sda1929.sch3#sch3", "",
  "The grantee, transferee or lessee", "Third Schedule Article 2(a): paid by the buyer")
p("sg.gst.reverse_charge", "SG", "ALL", "condition", "reverse_charge_on_imported_services_if_not_fully_recoverable", 1, "bool", "sg.gsta1993.s14#s14", "2020-01-01",
  "the recipient is not entitled to credit for the full amount of the recipient’s input tax under sections 19 and 20", "s14(1): imported services are self-accounted by a recipient that cannot fully recover input tax")
p("sg.gst.rate", "SG", "ALL", "rate", "gst_rate", 9, "%", "sg.gsta1993.s16#s16", "2024-01-01",
  "9% from and including 1 January 2024", "s16(cb)")
p("sg.p2.revenue_threshold", "SG", "ALL", "condition", "globe_revenue_threshold", 750000000, "EUR", "sg.memta2024.s8#s8", "2025-01-01",
  "A is EUR 750 million or its equivalent in other currency", "s8(2): pro-rated by the months of the fiscal year; two or more of the four preceding fiscal years")
p("sg.p2.minimum_rate", "SG", "ALL", "rate", "globe_minimum_rate", 15, "%", "sg.memta2024.s7#s7", "2025-01-01",
  "The minimum rate is 15%.", "s7")
p("sg.p2.dtt", "SG", "ALL", "condition", "domestic_top_up_tax_payable", 1, "bool", "sg.memta2024.s28#s28", "2025-01-01",
  "DTT is payable in respect of an MNE group for a financial year where", "s28(1): domestic top-up tax")
p("sg.p2.sbie_payroll_rate", "SG", "ALL", "rate", "sbie_payroll_carve_out_rate", 5, "%", "sg.memta2024.sch2#sch2", "2025-01-01",
  '( j ) for a financial year beginning in 2032, 5.8%; and ( k ) for a financial year beginning after 2032, 5.0%', "s18(2) with Second Schedule para 1(k): from 2032 onwards")
p("sg.p2.sbie_tangible_rate", "SG", "ALL", "rate", "sbie_tangible_asset_carve_out_rate", 5, "%", "sg.memta2024.sch2#sch2", "2025-01-01",
  '( j ) for a financial year beginning in 2032, 5.4%; and ( k ) for a financial year beginning after 2032, 5.0%', "s18(3) with Second Schedule para 2(k): from 2032 onwards")
p("sg.p2.sbie_payroll_transition", "SG", "ALL", "procedure", "sbie_payroll_rate_by_fiscal_year", '2023:10.0;2024:9.8;2025:9.6;2026:9.4;2027:9.2;2028:9.0;2029:8.2;2030:7.4;2031:6.6;2032:5.8', "text", "sg.memta2024.sch2#sch2", "2025-01-01",
  'In section 18(2), the applicable percentage is — ( a ) for a financial year beginning in 2023, 10.0%; ( b ) for a financial year beginning in 2024, 9.8%; ( c ) for a financial year beginning in 2025, 9.6%; ( d ) for a financial year beginning in 2026, 9.4%; ( e ) for a financial year beginning in 2027, 9.2%; ( f ) for a financial year beginning in 2028, 9.0%; ( g ) for a financial year beginning in 2029, 8.2%; ( h ) for a financial year beginning in 2030, 7.4%; ( i ) for a financial year beginning in 2031, 6.6%; ( j ) for a financial year beginning in 2032, 5.8%; and ( k ) for a financial year beginning after 2032, 5.0%', "Second Schedule para 1: by the year the fiscal year begins")
p("sg.p2.sbie_tangible_transition", "SG", "ALL", "procedure", "sbie_tangible_rate_by_fiscal_year", '2023:8.0;2024:7.8;2025:7.6;2026:7.4;2027:7.2;2028:7.0;2029:6.6;2030:6.2;2031:5.8;2032:5.4', "text", "sg.memta2024.sch2#sch2", "2025-01-01",
  'In section 18(3), the applicable percentage is — ( a ) for a financial year beginning in 2023, 8.0%; ( b ) for a financial year beginning in 2024, 7.8%; ( c ) for a financial year beginning in 2025, 7.6%; ( d ) for a financial year beginning in 2026, 7.4%; ( e ) for a financial year beginning in 2027, 7.2%; ( f ) for a financial year beginning in 2028, 7.0%; ( g ) for a financial year beginning in 2029, 6.6%; ( h ) for a financial year beginning in 2030, 6.2%; ( i ) for a financial year beginning in 2031, 5.8%; ( j ) for a financial year beginning in 2032, 5.4%; and ( k ) for a financial year beginning after 2032, 5.0%', "Second Schedule para 2: by the year the fiscal year begins")
p("p2.portfolio_shareholding_max", "HK", "ALL", "condition", "portfolio_shareholding_rights_below", 10, "%", "hk.ord.2025-21#p156", "2025-01-01",
  "carry rights to less than 10% of the profits, capital, reserves, or voting rights of that entity at the vesting date of the distribution or the date of disposition",
  "GloBE Art 10.1.1 portfolio shareholding: the exception to excluded dividends and excluded equity gains or losses")
p("p2.short_term_months", "HK", "ALL", "condition", "short_term_portfolio_shareholding_held_below_months", 12, "months", "hk.ord.2025-21#p161", "2025-01-01",
  "for less than one year at the vesting date of the distribution", "GloBE Art 10.1.1 short-term portfolio shareholding: one year")
p("sg.p2.portfolio_shareholding_max", "SG", "ALL", "condition", "portfolio_shareholding_rights_below", 10, "%", "sg.memta2024.s2#s2", "2025-01-01",
  "carry rights to less than 10% of the profits, capital, reserves, or voting rights of that entity at the date of distribution or disposition",
  "s2 portfolio shareholding")
p("sg.p2.short_term_months", "SG", "ALL", "condition", "short_term_portfolio_shareholding_held_below_months", 12, "months", "sg.memta2024.s2#s2", "2025-01-01",
  "for less than one year at the date of the distribution", "s2 excluded dividends (a): one year")
# ---- Pillar Two: de minimis exclusion and transitional CbCR safe harbour (decision D17)
p('sg.p2.dm_revenue_max', 'SG', "ALL", 'condition', 'de_minimis_average_revenue_below', 10000000, 'EUR', 'sg.memta2024.s19#s19', "2025-01-01",
  'the average of the following sums is less than EUR 10 million', 's19(1)(a): three-year average adjusted revenue')
p('sg.p2.dm_income_max', 'SG', "ALL", 'condition', 'de_minimis_average_globe_income_below', 1000000, 'EUR', 'sg.memta2024.s19#s19', "2025-01-01",
  'the average of the following sums is less than EUR 1 million', 's19(1)(b): three-year average GloBE income or loss')
p('sg.p2.tcsh_fy_start_from', 'SG', "ALL", 'condition', 'tcsh_fy_commences_from', '2025-01-01', 'date', 'sg.memta2024.regs.s70#s70', "2025-01-01",
  'the financial year commences in the period between 1 January 2025 and 31 December 2026 (both dates inclusive), and ends on or before 30 June 2028', 'reg 70(1)(a)')
p('sg.p2.tcsh_fy_start_to', 'SG', "ALL", 'condition', 'tcsh_fy_commences_by', '2026-12-31', 'date', 'sg.memta2024.regs.s70#s70', "2025-01-01",
  'the financial year commences in the period between 1 January 2025 and 31 December 2026 (both dates inclusive), and ends on or before 30 June 2028', 'reg 70(1)(a)')
p('sg.p2.tcsh_fy_end_by', 'SG', "ALL", 'condition', 'tcsh_fy_ends_by', '2028-06-30', 'date', 'sg.memta2024.regs.s70#s70', "2025-01-01",
  'the financial year commences in the period between 1 January 2025 and 31 December 2026 (both dates inclusive), and ends on or before 30 June 2028', 'reg 70(1)(a)')
p('sg.p2.tcsh_dm_revenue_max', 'SG', "ALL", 'condition', 'tcsh_de_minimis_cbcr_revenue_below', 10000000, 'EUR', 'sg.memta2024.regs.s71#s71', "2025-01-01",
  'as reported on its qualifying country‑by‑country report is less than EUR 10 million', 'reg 71(1)(a)')
p('sg.p2.tcsh_dm_pbt_max', 'SG', "ALL", 'condition', 'tcsh_de_minimis_cbcr_profit_below', 1000000, 'EUR', 'sg.memta2024.regs.s71#s71', "2025-01-01",
  'a total profit of less than EUR 1 million, or a loss, before income tax', 'reg 71(1)(b)')
p('sg.p2.tcsh_etr_2025', 'SG', "ALL", 'rate', 'tcsh_simplified_etr_min_fy_2025', 16, '%', 'sg.memta2024.regs.s72#s72', "2025-01-01",
  'in the case of a financial year beginning in 2025 — at least 16%', 'reg 72(1)(a)')
p('sg.p2.tcsh_etr_2026', 'SG', "ALL", 'rate', 'tcsh_simplified_etr_min_fy_2026', 17, '%', 'sg.memta2024.regs.s72#s72', "2025-01-01",
  'in the case of a financial year beginning on or after 1 January 2026 — at least 17%', 'reg 72(1)(b); the transition period only runs to fiscal years beginning in 2026')
p('p2.dm_revenue_max', 'HK', "ALL", 'condition', 'de_minimis_average_revenue_below', 10000000, 'EUR', 'hk.ord.2025-21#p91', "2025-01-01",
  'the average GloBE revenue of such jurisdiction is less than EUR 10 million', 'GloBE Art 5.5.1(a)')
p('p2.dm_income_max', 'HK', "ALL", 'condition', 'de_minimis_average_globe_income_below', 1000000, 'EUR', 'hk.ord.2025-21#p92', "2025-01-01",
  'the average GloBE income or loss of such jurisdiction is a loss or is less than EUR 1 million', 'GloBE Art 5.5.1(b)')
p('p2.tcsh_fy_start_to', 'HK', "ALL", 'condition', 'tcsh_fy_begins_by', '2026-12-31', 'date', 'hk.ord.2025-21#p173', "2025-01-01",
  'transition period (過渡期) means a period that covers all the fiscal years beginning on or before 31 December 2026 but does not include a fiscal year ending after 30 June 2028', 'Sch 61 Pt 3 s2(1)')
p('p2.tcsh_fy_end_by', 'HK', "ALL", 'condition', 'tcsh_fy_ends_by', '2028-06-30', 'date', 'hk.ord.2025-21#p173', "2025-01-01",
  'transition period (過渡期) means a period that covers all the fiscal years beginning on or before 31 December 2026 but does not include a fiscal year ending after 30 June 2028', 'Sch 61 Pt 3 s2(1)')
p('p2.tcsh_dm_revenue_max', 'HK', "ALL", 'condition', 'tcsh_de_minimis_cbcr_revenue_below', 10000000, 'EUR', 'hk.ord.2025-21#p179', "2025-01-01",
  'the MNE group’s total revenue for the jurisdiction for the fiscal year is less than EUR 10 million', 'Sch 61 Pt 3 s6(1)(a)')
p('p2.tcsh_dm_pbt_max', 'HK', "ALL", 'condition', 'tcsh_de_minimis_cbcr_profit_below', 1000000, 'EUR', 'hk.ord.2025-21#p179', "2025-01-01",
  'the MNE group’s profit before income tax for the jurisdiction for the fiscal year is less than EUR 1 million or the MNE group has a loss', 'Sch 61 Pt 3 s6(1)(b)')
p('p2.tcsh_etr_2025', 'HK', "ALL", 'rate', 'tcsh_simplified_etr_min_fy_2025', 16, '%', 'hk.ord.2025-21#p180', "2025-01-01",
  'if the fiscal year starts in the 2025 calendar year—16%', 'Sch 61 Pt 3 s7(1)(a)')
p('p2.tcsh_etr_2026', 'HK', "ALL", 'rate', 'tcsh_simplified_etr_min_fy_2026', 17, '%', 'hk.ord.2025-21#p180', "2025-01-01",
  'if the fiscal year starts in the 2026 calendar year—17%', 'Sch 61 Pt 3 s7(1)(b)')
# ---- the restructuring step (decision D18)
p('cn.reorg.acquired_ratio_min', 'CN', 'SHARE_TRANSFER', 'condition', 'special_reorg_equity_acquired_ratio_min', 50, '%', 'cn.cs.2014-109#i1', '2014-01-01',
  '收购企业购买的股权不低于被收购企业全部股权的50%', '109号 art. 1: the 75% in 59号 art. 6 item (2) is adjusted to 50%')
p('cn.reorg.equity_payment_min', 'CN', 'SHARE_TRANSFER', 'condition', 'special_reorg_equity_payment_share_min', 85, '%', 'cn.cs.2009-59#i6', '2008-01-01',
  '股权支付金额不低于其交易支付总额的85%', '59号 art. 6 item (2); art. 5 item (4)')
p('cn.reorg.control_ratio', 'CN', 'SHARE_TRANSFER', 'condition', 'special_reorg_direct_control_ratio', 100, '%', 'cn.cs.2009-59#i7', '2008-01-01',
  '非居民企业向其100%直接控股的另一非居民企业转让其拥有的居民企业股权', '59号 art. 7 items (1), (2) and (3): 100% direct shareholding')
p('cn.reorg.commitment_years', 'CN', 'SHARE_TRANSFER', 'condition', 'special_reorg_no_transfer_commitment_years', 3, 'years', 'cn.cs.2009-59#i7', '2008-01-01',
  '在3年（含3年）内不转让其拥有受让方非居民企业的股权', '59号 art. 7 item (1): written undertaking')
p('cn.reorg.keep_months', 'CN', 'SHARE_TRANSFER', 'condition', 'special_reorg_unchanged_months', 12, 'months', 'cn.cs.2009-59#i5', '2008-01-01',
  '在重组后连续12个月内，不得转让所取得的股权', '59号 art. 5 items (3) and (5)')
p('cn.reorg.resident_spread_years', 'CN', 'SHARE_TRANSFER', 'rate', 'special_reorg_resident_gain_spread_years', 10, 'years', 'cn.cs.2009-59#i8', '2008-01-01',
  '可以在10个纳税年度内均匀计入各年度应纳税所得额', '59号 art. 8: the gain under art. 7 item (3)')
p('cn.reorg.filing_days', 'CN', 'SHARE_TRANSFER', 'procedure', 'special_reorg_nonresident_filing_days', 30, 'days', 'cn.sta.2013-72#i2', '2013-12-12',
  '应于股权转让合同或协议生效且完成工商变更登记手续30日内进行备案', '公告2013年第72号 art. 2')
p('cn.reorg.dividend_treaty_denied', 'CN', 'DIVIDEND', 'condition', 'pre_reorg_profits_no_treaty_dividend_reduction', 1, 'bool', 'cn.sta.2013-72#i8', '2013-12-12',
  '不享受受让方所在国家（地区）与中国签订的税收协定（含税收安排）的股息减税优惠待遇', '公告2013年第72号 art. 8')
p('hk.stamp.associated_ratio', 'HK', 'SHARE_TRANSFER', 'condition', 's45_associated_body_ratio_min', 90, '%', 'hk.cap117.en#s45', '',
  'one is beneficial owner of not less than 90 per cent of the issued share capital of the other', 'SDO s45(2)')
p('sg.stamp.associated_capital_min', 'SG', 'SHARE_TRANSFER', 'condition', 's15_associated_voting_capital_min', 75, '%', 'sg.sda1929.relief2014.sch1#sch1', '2014-01-16',
  '75% or more voting capital; and ( b ) more than 50% voting power', 'SDA s15(1)(b); 2014 Rules r3(1)(b) and First Schedule')
p('hk.stamp.clawback_years', 'HK', 'SHARE_TRANSFER', 'limit', 's45_relief_clawback_years', 2, 'years', 'hk.cap117.en#s45', '',
  'within 2 years after the date of execution of the instrument', 'SDO s45(5A): relief is withdrawn when a change in the transferee\'s shareholding makes the two cease to be associated (subsection (4)(c))')
# ---- decision D20: the income inclusion rule — qualified status from the OECD central record (as at 1 December 2025)
p('p2.qualified_iir_hk', 'HK', 'ALL', 'condition', 'hong_kong_iir_has_transitional_qualified_status', 1, 'bool', 'intl.oecd.globe.central-record.2025-12#p7', '2025-01-01',
  'Hong Kong (China) Inland Revenue (Amendment) (Minimum Tax for Multinational Enterprise Groups) Ordinance 2025 1 January 2025',
  'OECD central record, first table (qualified IIR); GloBE Art 2.1.3 and MEMTA s13 decide whether an upper parent is subject to a qualified IIR')
p('p2.qualified_iir_sg', 'SG', 'ALL', 'condition', 'singapore_iir_has_transitional_qualified_status', 1, 'bool', 'intl.oecd.globe.central-record.2025-12#p8', '2025-01-01',
  'Singapore Multinational Enterprise (Minimum Tax) Act 2024 1 January 2025', 'OECD central record, first table (qualified IIR); the Mainland is not listed')
p('hk.p2.iir_payable_from', 'HK', 'ALL', 'condition', 'iir_top_up_tax_payable_for_fiscal_years_from', 1, 'bool', 'hk.ord.2025-21#p22', '2025-01-01',
  'The IIR top-up tax is payable in relation to a fiscal year beginning on or after 1 January 2025', 's26AE(6); UTPR awaits a date appointed by notice in the Gazette (s26AE(7)), not modelled')
p('sg.p2.mtt_chargeable_entity', 'SG', 'ALL', 'condition', 'mtt_charged_on_responsible_member_located_in_singapore', 1, 'bool', 'sg.memta2024.s12#s12', '2025-01-01',
  'An entity (called in this Act a chargeable entity) is chargeable with MTT for a financial year if', 's12; the responsible member in s13, the tax amount in s14 and s15')
p('sg.stamp.clawback_years', 'SG', 'SHARE_TRANSFER', 'limit', 's15_relief_clawback_years', 2, 'years', 'sg.sda1929.relief2014#s7', '2014-01-16',
  'within 2 years from the date of execution of the instrument', '2014 Rules r7(1): relief is withdrawn when within the period the parties cease to be associated ((a)) or the transferee disposes of the asset ((b))')
# ---- domestic flows, by the statutes (范围.md decision 2)
p("cn.domestic.dividend_exempt", "CN", "DIVIDEND", "condition", "qualifying_dividends_between_resident_companies_exempt", 1, "bool", "cn.law.eit#26", "2008-01-01",
  "符合条件的居民企业之间的股息、红利等权益性投资收益", "art. 26 item (2); conditions in 实施条例 art. 83: direct investment")
p("cn.domestic.dividend_listed_months", "CN", "DIVIDEND", "condition", "listed_shares_held_at_least_months_for_exemption", 12, "months", "cn.reg.eit#83", "2008-01-01",
  "不包括连续持有居民企业公开发行并上市流通的股票不足12个月取得的投资收益", "")
p("cn.tp.domestic_same_burden_no_adjustment", "CN", "ALL", "condition", "no_tp_adjustment_between_domestic_related_parties_with_same_burden", 1, "bool", "cn.sta.2017-06#38", "2017-05-01",
  "实际税负相同的境内关联方之间的交易，只要该交易没有直接或者间接导致国家总体税收收入的减少，原则上不作特别纳税调整", "the arm's length cap is used only for cross-border flows")
p("cn.tp.related_transfer_arms_length", "CN", "SHARE_TRANSFER", "condition", "related_party_transfer_taxed_at_arms_length_value", 1, "bool", "cn.law.eit#41", "2008-01-01",
  "企业与其关联方之间的业务往来，不符合独立交易原则而减少企业或者其关联方应纳税收入或者所得额的，税务机关有权按照合理方法调整。",
  "decision D38: an equity transfer between related parties below the arm's length price is taxed in the Mainland at the arm's length price; methods in 实施条例 art. 111 and 公告2017年第6号 arts. 17 and 22")
# ---- decision D40: related parties, each jurisdiction's own test
p("cn.tp.related_share_min", "CN", "ALL", "condition", "related_party_share_min", 25, "%", "cn.sta.2016-42#i2", "2016-01-01",
  "一方直接或者间接持有另一方的股份总和达到25%以上", "decision D40; also related when a third party holds 25% or more of both; where the holding is below the threshold but a shareholding exists, items (2) to (4) and (7) are left open")
p("cn.tp.related_via_intermediate", "CN", "ALL", "condition", "related_share_through_intermediate", 1, "bool", "cn.sta.2016-42#i2", "2016-01-01",
  "只要其对中间方持股比例达到25%以上，则其对另一方的持股比例按照中间方对另一方的持股比例计算", "decision D40; intermediate holdings below 25% are multiplied through, several chains are added")
p("hk.tp.control_more_than_half", "HK", "ALL", "condition", "participation_control_more_than_half", 50, "%", "hk.cap112.en#s50AAH", "2018-07-13",
  "more than half of the direct or indirect beneficial interest", "decision D40; s50AAH(2)(a)(i), indirect interests multiplied through under s50AAH(4); (a)(ii) more than half of the voting power exercised through controlled companies also counts")
p("hk.tp.participation", "HK", "ALL", "condition", "participation_condition", 1, "bool", "hk.cap112.en#s50AAG", "2018-07-13",
  "the same person or persons was or were participating in the management, control or capital of each of the affected persons",
  "decision D40; s50AAG(a) one controls the other, (b) the same person controls both")
p("sg.tp.related_party", "SG", "ALL", "condition", "related_party_by_control", 1, "bool", "sg.ita1947.full#s2", "",
  "who directly or indirectly controls", "decision D40; s2 does not define control, the graph recognises only wholly owned; other holdings left open")
# ---- decision D41: a related party's payment below its arm's-length amount — the payee's jurisdiction computes the income at it
p("cn.tp.income_arms_length", "CN", "ALL", "condition", "related_income_taxed_at_arms_length", 1, "bool", "cn.law.eit#41", "2008-01-01",
  "企业与其关联方之间的业务往来，不符合独立交易原则而减少企业或者其关联方应纳税收入或者所得额的，税务机关有权按照合理方法调整。",
  "decision D41: interest, royalties and service fees under-received by the payee are taxed at the arm's length amount; below the median, at the median (公告2017年第6号 art. 25)")
p("hk.tp.income_arms_length", "HK", "ALL", "condition", "income_computed_at_arms_length_amount", 1, "bool", "hk.cap112.en#s50AAF", "2018-07-13",
  "the advantaged person’s income or loss is to be computed as if the arm’s length provision had been made or imposed instead of the actual provision",
  "decision D41; s50AAJ: applies only when the actual arrangement reduces Hong Kong income")
p("hk.tp.range_no_adjustment", "HK", "ALL", "condition", "no_adjustment_inside_arms_length_range", 1, "bool", "hk.dipn.59#para121", "",
  "the results of the tested party fall within an arm’s length range, then no adjustment should be made", "decision D41; lower bound of the range arms_length_low")
p("hk.tp.adjustment_point_median", "HK", "ALL", "condition", "adjustment_point_normally_median", 1, "bool", "hk.dipn.59#para122", "",
  "Normally, the median is proposed but other points may also be considered", "decision D41; the median is the case's arms_length_value")
p("sg.tp.income_arms_length", "SG", "ALL", "condition", "income_increased_to_arms_length", 1, "bool", "sg.ita1947.full#s34D", "",
  "increase the amount of the income of the person mentioned in subsection (1)(c)(i) for the year of assessment",
  "decision D41; s34D(1)(c)(i); a 5% surcharge on the increase under s34E")
p("sg.tp.range_no_adjustment", "SG", "ALL", "condition", "adjust_into_arms_length_results", 1, "bool", "sg.iras.etax.tp#para5.115", "",
  "Testing will enable adjustments to the price of related party transactions to be made so as to bring the price to be within the arm’s length results.",
  "decision D41; no adjustment within the range, lower bound arms_length_low")
p("cn-hk.tp.corresponding", "pair(CN,HK)", "ALL", "condition", "corresponding_adjustment", 1, "bool", "treaty.cn-hk.2006.zh#9.2", "2007-01-01",
  "该另一方应对这部分利润所征收的税额作出适当的调整", "decision D41; the appropriate adjustment is set by the other competent authority: a determination")
p("cn-sg.tp.corresponding", "pair(CN,SG)", "ALL", "condition", "corresponding_adjustment", 1, "bool", "treaty.cn-sg.2007.mli.zh#9.2", "2023-01-01",
  "该缔约国另一方应对该部分利润的征税额进行适当调整", "decision D41; art. 9 para. 2 is replaced by MLI art. 17 para. 1")
p("hk.tp.corresponding_relief_map", "HK", "ALL", "condition", "corresponding_relief_through_map", 1, "bool", "hk.cap112.en#s50AAN", "2018-07-13",
  "as if the MAP arm’s length provision had been made or imposed instead of the actual provision", "decision D41; requires a treaty and the mutual agreement procedure")
p("sg.s10l.open_market_price", "SG", "SHARE_TRANSFER", "condition", "s10l_gain_at_open_market_price", 1, "bool", "sg.ita1947.full#s10L", "2024-01-01",
  "the Comptroller may treat the following amount as the amount of the gains received in Singapore from outside Singapore",
  "decision D41; s10L(10), (11): A + B − C; whether it applies is the Comptroller's determination")
# ---- decision D42: a sale of goods — the seller's profit on it, where it arises, the treaties' business-profits article
p("cn.goods.income", "CN", "GOODS", "condition", "goods_sale_income", 1, "bool", "cn.reg.eit#14", "2008-01-01",
  "所称销售货物收入，是指企业销售商品、产品、原材料、包装物、低值易耗品以及其他存货取得的收入", "decision D42")
p("cn.goods.cost", "CN", "GOODS", "condition", "cost_of_goods_deductible", 1, "bool", "cn.reg.eit#29", "2008-01-01",
  "所称成本，是指企业在生产经营活动中发生的销售成本、销货成本、业务支出以及其他耗费", "decision D42: gross profit = price − cost of goods sold")
p("cn.goods.source", "CN", "GOODS", "condition", "goods_income_sourced_where_transaction_takes_place", 1, "bool", "cn.reg.eit#7", "2008-01-01",
  "销售货物所得，按照交易活动发生地确定", "decision D42: where the transaction activity takes place is a determination")
p("cn.goods.nonresident_scope", "CN", "GOODS", "condition", "nonresident_taxed_on_mainland_source_only", 1, "bool", "cn.law.eit#3", "2008-01-01",
  "非居民企业在中国境内未设立机构、场所的，或者虽设立机构、场所但取得的所得与其所设机构、场所没有实际联系的，应当就其来源于中国境内的所得缴纳企业所得税",
  "decision D42")
p("hk.goods.both_in_hk", "HK", "GOODS", "condition", "trading_profits_taxable_both_contracts_in_hk", 1, "bool", "hk.dipn.21#para23", "",
  "Where both the contract of purchase and contract of sale are effected in Hong Kong, the profits are fully taxable.", "decision D42")
p("hk.goods.both_outside", "HK", "GOODS", "condition", "trading_profits_untaxed_both_contracts_outside", 1, "bool", "hk.dipn.21#para23", "",
  "Where both the contract of purchase and contract of sale are effected outside Hong Kong, no part of the profits are taxable.", "decision D42")
p("hk.goods.one_in_hk", "HK", "GOODS", "condition", "trading_profits_presumed_taxable_one_contract_in_hk", 1, "bool", "hk.dipn.21#para23", "",
  "Where either the contract of purchase or contract of sale is effected in Hong Kong, the initial presumption will be that the profits are fully taxable.",
  "decision D42: when only one side is in Hong Kong, all the operations are looked at: a determination")
p("hk.goods.hk_customer", "HK", "GOODS", "condition", "sale_to_hk_customer_effected_in_hk", 1, "bool", "hk.dipn.21#para23", "",
  "Where the sale is made to a Hong Kong customer (including the Hong Kong buying office of an overseas customer), the sale contract will usually be taken as having been effected in Hong Kong.",
  "decision D42: presumption when not stated")
p("hk.goods.hk_supplier", "HK", "GOODS", "condition", "purchase_from_hk_supplier_effected_in_hk", 1, "bool", "hk.dipn.21#para23", "",
  "Where the commodities or goods are purchased from either a Hong Kong supplier or manufacturer, the purchase contract will usually be taken as having been effected in Hong Kong.",
  "decision D42: presumption when not stated")
p("hk.goods.no_apportionment", "HK", "GOODS", "condition", "trading_profits_wholly_taxable_or_not", 1, "bool", "hk.dipn.21#para24", "",
  "Trading profits will be either wholly taxable or wholly non-taxable.", "decision D42")
p("sg.goods.trade_income", "SG", "GOODS", "condition", "gains_from_trade_charged", 1, "bool", "sg.ita1947.full#s10", "",
  "gains or profits from any trade, business, profession or vocation", "decision D42: s10(1)(a); the source is a determination; foreign-sourced income is taxed on remittance")
# ---- decision D43: goods crossing a border — the Mainland's export VAT and refund, import VAT and duty; Singapore's import GST
p("cn.vat.law.rate_goods", "CN", "GOODS", "rate", "vat_rate_goods", 13, "%", "cn.law.vat#10", "2026-01-01",
  "纳税人销售货物、加工修理修配服务、有形动产租赁服务，进口货物，除本条第二项、第四项、第五项规定外，税率为百分之十三", "decision D43: the highest applicable rate for goods")
p("cn.vat.law.rate_goods_reduced", "CN", "GOODS", "rate", "vat_rate_goods_listed", 9, "%", "cn.law.vat#10", "2026-01-01",
  "销售或者进口下列货物，除本条第四项、第五项规定外，税率为百分之九", "decision D43: the listed goods")
p("cn.vat.law.export_zero", "CN", "GOODS", "rate", "vat_rate_exported_goods", 0, "%", "cn.law.vat#10", "2026-01-01",
  "纳税人出口货物，税率为零", "decision D43")
p("cn.vat.export.refund_rate_default", "CN", "GOODS", "condition", "export_refund_rate_is_applicable_rate", 1, "bool", "cn.cs.2026-11#i3", "2026-01-01",
  "出口业务的退税率为其适用税率", "decision D43: except as otherwise specified by the MOF and the SAT; the refund rate of the goods is case data")
p("cn.vat.export.non_refundable", "CN", "GOODS", "condition", "non_refundable_input_vat_on_exports", 1, "bool", "cn.cs.2026-11#i5", "2026-01-01",
  "退税率低于适用税率的，相应计算出的差额部分的税款计入出口业务成本", "decision D43")
p("cn.vat.export.fob_basis", "CN", "GOODS", "condition", "manufacturer_refund_basis_fob", 1, "bool", "cn.cs.2026-11#i4", "2026-01-01",
  "生产企业（进料加工复出口货物除外）增值税退（免）税的计税依据，为出口货物实际离岸价（FOB）", "decision D43: exempt-credit-refund")
p("cn.vat.export.trader_basis", "CN", "GOODS", "condition", "trader_refund_basis_purchase_invoice", 1, "bool", "cn.cs.2026-11#i4", "2026-01-01",
  "适用免退税办法的外贸企业出口货物（委托加工、委托修理修配货物除外）增值税退（免）税的计税依据，为购进出口货物的增值税专用发票注明的金额",
  "decision D43: exempt-refund")
p("cn.vat.law.import", "CN", "GOODS", "condition", "import_vat_on_composite_value", 1, "bool", "cn.law.vat#14", "2026-01-01",
  "进口货物，按照本法规定的组成计税价格乘以适用税率计算缴纳增值税。组成计税价格，为关税计税价格加上关税和消费税", "decision D43")
p("cn.vat.law.input_tax", "CN", "GOODS", "condition", "input_tax_paid_on_purchases", 1, "bool", "cn.law.vat#16", "2026-01-01",
  "进项税额，是指纳税人购进货物、服务、无形资产、不动产支付或者负担的增值税税额", "decision D43: import VAT is creditable")
p("cn.tariff.taxpayer", "CN", "GOODS", "condition", "duty_borne_by_consignee_or_consignor", 1, "bool", "cn.law.tariff#3", "2024-12-01",
  "进口货物的收货人、出口货物的发货人、进境物品的携带人或者收件人，是关税的纳税人", "decision D43: the buyer on import, the seller on export")
p("cn.tariff.ad_valorem", "CN", "GOODS", "condition", "duty_value_times_rate", 1, "bool", "cn.law.tariff#23", "2024-12-01",
  "实行从价计征的，应纳税额按照计税价格乘以比例税率计算", "decision D43: the rate is case data (the tariff schedule)")
p("cn.tariff.value", "CN", "GOODS", "condition", "duty_value_transaction_price", 1, "bool", "cn.law.tariff#24", "2024-12-01",
  "进口货物的计税价格以成交价格以及该货物运抵中华人民共和国境内输入地点起卸前的运输及其相关费用、保险费为基础确定", "decision D43")
p("cn.tariff.related", "CN", "GOODS", "condition", "related_price_accepted_if_unaffected", 1, "bool", "cn.law.tariff#24", "2024-12-01",
  "买卖双方没有特殊关系，或者虽有特殊关系但未对成交价格产生影响", "decision D43: whether the relationship affected the price is a determination")
p("sg.gst.import_charge", "SG", "GOODS", "condition", "gst_on_importation_of_goods", 1, "bool", "sg.gsta1993.s16#s16", "2024-01-01",
  "the importation of goods, by reference to the value of the goods as determined under this Act", "decision D43: recoverable input tax is not a cost")
# ---- decision D44: Hong Kong intra-group transfer relief — the acquirer's later disposal stands in the seller's shoes
p("hk.fsie.intragroup_carry_over", "HK", "SHARE_TRANSFER", "condition", "acquirer_takes_sellers_cost_and_date", 1, "bool", "hk.cap112.en#s15OA", "",
  "the acquiring entity is to be regarded as having acquired the property for the consideration mentioned in subsection (3) at the time at which the selling entity acquired, or is to be regarded as having acquired, the property",
  "decision D44: s15OA(5)")
p("hk.fsie.intragroup_foreign_tax", "HK", "SHARE_TRANSFER", "condition", "sellers_foreign_tax_credited_on_future_income", 1, "bool", "hk.cap112.en#s15OA", "",
  "that foreign tax is, for the purposes of sections 50 and 50AAA and Schedule 54, to be regarded as tax paid in respect of the future income by the acquiring entity in that territory",
  "decision D44: s15OA(8)")
p("hk.fsie.intragroup_subject_to_tax", "HK", "SHARE_TRANSFER", "condition", "subject_to_tax_met_through_sellers_tax", 1, "bool", "hk.fsie.examples#h15", "",
  "would be accepted as having been met since Company S had paid withholding tax on its disposal gain",
  "decision D44: Example 38")
# ---- decision D45: Singapore s13W from 2026 — the 20% may be held by the divesting company together with its group
p("sg.s13w.group_basis", "SG", "SHARE_TRANSFER", "condition", "shareholding_together_with_group", 1, "bool", "sg.ita1947.full#s13W", "2026-01-01",
  "divesting company A2 together with one or more companies in the same group as divesting company A2", "decision D45: s13W(1B)")
p("sg.s13w.group_more_than_half", "SG", "SHARE_TRANSFER", "condition", "same_group_more_than_half", 50, "%", "sg.ita1947.full#s13W", "2026-01-01",
  "more than 50% of the total number of issued ordinary shares in one company are beneficially owned by the other company", "decision D45: s13W(1C)(b)")
p("sg.s13w.group_chain", "SG", "SHARE_TRANSFER", "condition", "group_ownership_multiplied_through_levels", 1, "bool", "sg.ita1947.full#s13W", "2026-01-01",
  "the percentage of such beneficial ownership is computed by the formula A × B", "decision D45: s13W(1D)")
# ---- decision D46: capitalisation of reserves (转增股本) — a dividend on the decision unless from share premium; the books stamp;
#      the reinvestment deferral ends when the investment is withdrawn
p("cn.capitalisation.dividend_on_decision", "CN", "DIVIDEND", "condition", "capitalisation_decision_realises_dividend", 1, "bool", "cn.gsh.2010-79#i4", "",
  "应以被投资企业股东会或股东大会作出利润分配或转股决定的日期，确定收入的实现", "decision D46: art. 4 para. 1; columns 6 and 7 of annual return A107011 agree")
p("cn.capitalisation.share_premium_not_income", "CN", "DIVIDEND", "condition", "share_premium_capitalisation_not_dividend", 1, "bool", "cn.gsh.2010-79#i4", "",
  "被投资企业将股权（票）溢价所形成的资本公积转为股本的，不作为投资方企业的股息、红利收入", "decision D46: art. 4 para. 2")
p("cn.capitalisation.not_income_sources", "CN", "DIVIDEND", "condition", "capitalised_items_not_income", "share_premium", "enum", "cn.gsh.2010-79#i4", "",
  "股权（票）溢价所形成的资本公积", "decision D46: this item only; capitalisation of other capital reserves is outside the model")
p("cn.capitalisation.share_premium_no_basis", "CN", "SHARE_TRANSFER", "condition", "share_premium_capitalisation_no_basis_increase", 1, "bool", "cn.gsh.2010-79#i4", "",
  "投资方企业也不得增加该项长期投资的计税基础", "decision D46: art. 4 para. 2")
p("cn.capitalisation.basis_paid_in", "CN", "SHARE_TRANSFER", "condition", "capitalised_profit_is_paid_in_capital", 1, "bool", "cn.sta.2017-37#i3", "2017-12-01",
  "股权的计税基础是股权转让人投资入股时向中国居民企业实际支付的出资成本",
  "decision D46: capitalising retained earnings is a direct investment of distributed profits (财税〔2018〕102号 art. 2 (1) 1, 公告2025年第2号 art. 2 (2) 1); the capitalised amount goes into the cost of the contribution; capitalised share premium does not (79号 art. 4 para. 2)")
p("cn.stamp.books_rate", "CN", "DIVIDEND", "rate", "stamp_duty_business_books_rate", 0.025, "%", "cn.law.stamp.flk#20", "2022-07-01",
  "合计金额的万分之二点五", "decision D46: 印花税税目税率表 — business account books, the total of paid-in capital (share capital) and capital reserve")
p("cn.stamp.books_base", "CN", "DIVIDEND", "condition", "books_base_paid_in_capital_and_reserve", 1, "bool", "cn.law.stamp#5", "2022-07-01",
  "应税营业账簿的计税依据，为账簿记载的实收资本(股本)、资本公积合计金额", "decision D46: art. 5 (3)")
p("cn.stamp.books_increase_only", "CN", "DIVIDEND", "condition", "books_taxed_on_the_increase", 1, "bool", "cn.law.stamp#11", "2022-07-01",
  "按照增加部分计算应纳税额", "decision D46: art. 11; capital reserve converted into share capital leaves the total unchanged")
p("cn.stamp.books_increase_sources", "CN", "DIVIDEND", "condition", "capitalised_items_that_increase_the_books_base", "retained_earnings", "enum", "cn.cs.2024-14#i1",
  "2024-10-01", "企业其他会计科目记载的资金转为实收资本（股本）或者资本公积的，应当按规定缴纳印花税",
  "decision D46: art. 1 (4); capitalisation of surplus reserve and undistributed profits", to="2027-12-31")
p("cn.reinvest.withdrawal_forms", "CN", "DIVIDEND", "condition", "investment_withdrawn_by_transfer_buyback_or_liquidation",
  "SHARE_TRANSFER;CAPITAL_REDUCTION;LIQUIDATION", "enum", "cn.cs.2018-102#i6", "2018-01-01",
  "通过股权转让、回购、清算等方式实际收回享受暂不征收预提所得税政策待遇的直接投资", "decision D46: a buy-back is treated as a capital reduction; repaid within 7 days of withdrawal (cn.reinvest.recapture_days)")
p("hk.fsie.in_kind_not_received", "HK", "DIVIDEND", "condition", "in_kind_dividend_of_overseas_shares_not_received", 1, "bool", "hk.arc.75#all", "",
  "The Dividend shall not be regarded as received in Hong Kong under section 15H of the IRO",
  "decision D46: Advance Ruling Case No. 75 (a dividend in specie of shares of an overseas company); a capitalisation pays no sum and nothing is received in Hong Kong (s15H(5))")
# ---- decision D47: branches — a company's branch in another jurisdiction is the company itself: the branch's jurisdiction
#      taxes the profit of its trade there, the head office's jurisdiction as its own law says
p("cn.branch.own_computation", "CN", "BRANCH_PROFIT", "condition", "establishment_taxed_on_its_own_income", 1, "bool", "cn.law.eit#3", "2008-01-01",
  "非居民企业在中国境内设立机构、场所的，应当就其所设机构、场所取得的来源于中国境内的所得", "decision D47: art. 3 para. 2; rate 25% under art. 4, no withholding (art. 37 reaches only income under art. 3 para. 3)")
p("cn.branch.accrual", "CN", "BRANCH_PROFIT", "condition", "foreign_branch_income_whether_or_not_remitted", 1, "bool", "cn.cs.2009-125#i3", "2008-01-01",
  "居民企业在境外设立不具有独立纳税地位的分支机构取得的各项境外所得，无论是否汇回中国境内，均应计入该企业所属纳税年度的境外应纳税所得额",
  "decision D47: art. 3 (1)")
p("cn.branch.tax_year", "CN", "BRANCH_PROFIT", "procedure", "foreign_year_ending_in_the_mainland_year", 1, "bool", "cn.cs.2009-125#i11", "2008-01-01",
  "与我国纳税年度当年度相对应的境外纳税年度，应为在我国有关纳税年度中任何一日结束的境外纳税年度", "decision D47: art. 11; 操作指南 example 10")
p("cn.branch.loss_not_offset", "CN", "BRANCH_PROFIT", "condition", "foreign_branch_loss_not_set_off", 1, "bool", "cn.law.eit#17", "2008-01-01",
  "其境外营业机构的亏损不得抵减境内营业机构的盈利", "decision D47: art. 17; the carry-forward of losses (操作指南 example 2) is outside the model")
p("hk.branch.profits_in_hk", "HK", "BRANCH_PROFIT", "condition", "profits_arising_in_hk_charged", 1, "bool", "hk.cap112.en#s14", "",
  "in respect of his assessable profits arising in or derived from Hong Kong", "decision D47: s14; whether the branch's profits are sourced in Hong Kong is a judgement")
p("hk.fsie.stand_alone_mne", "HK", "ALL", "condition", "entity_with_pe_abroad_is_mne_entity", 1, "bool", "hk.cap112.en#s15H", "2023-01-01",
  "is located in one jurisdiction and has one or more permanent establishments in other jurisdictions", "decision D47: s15H(1) “獨立跨國企業實體”")
p("hk.fsie.mne_group_pe", "HK", "ALL", "condition", "group_with_pe_abroad_is_mne_group", 1, "bool", "hk.cap112.en#s15H", "2023-01-01",
  "a group that includes at least one entity or permanent establishment that is not located or established in the jurisdiction of the ultimate parent entity of the group",
  "decision D47: s15H(1) “跨國企業集團”")
p("sg.branch.trade_income", "SG", "BRANCH_PROFIT", "condition", "branch_trade_income_accruing_in_sg", 1, "bool", "sg.ita1947.full#s10", "",
  "upon the income of any person accruing in or derived from Singapore or received in Singapore from outside Singapore", "decision D47: s10(1)")
p("sg.fsie.branch_profits", "SG", "BRANCH_PROFIT", "condition", "foreign_branch_profits_exempt", 1, "bool", "sg.ita1947.full#s13", "",
  "any profit derived from any trade or business carried on by a branch in any territory outside Singapore of a company resident in Singapore",
  "decision D47: s13(8)(b); same conditions as s13(9)")
p("sg.s10l.place_of_business", "SG", "SHARE_TRANSFER", "condition", "group_with_place_of_business_abroad_is_relevant", 1, "bool", "sg.ita1947.full#s10L", "2024-01-01",
  "any entity of the group has a place of business in more than one jurisdiction", "decision D47: s10L(5)(b)(ii); a single entity with a foreign branch is not a group (e-Tax Guide para 5.5)")
# ---- decision D48: a sale of land or a building — the Mainland (VAT, surcharges, land appreciation tax, deed tax, stamp duty, income tax),
#      Hong Kong (ad valorem stamp duty Scale 1, s14, FSIE non-IP disposal gains), Singapore (BSD, ABSD, SSD, GST, s10, s10L)
p("cn.property.source", "CN", "PROPERTY_TRANSFER", "condition", "immovable_gain_sourced_where_it_lies", 1, "bool", "cn.reg.eit#7", "2008-01-01",
  "不动产转让所得按照不动产所在地确定", "decision D48: 实施条例 art. 7 (3)")
p("cn.property.taxes_deductible", "CN", "PROPERTY_TRANSFER", "condition", "taxes_other_than_eit_and_creditable_vat_deductible", 1, "bool", "cn.reg.eit#31", "2008-01-01",
  "是指企业发生的除企业所得税和允许抵扣的增值税以外的各项税金及其附加", "decision D48: a resident enterprise's transfer income is net of the taxes on the transfer")
p("cn.vat.law.rate_property", "CN", "PROPERTY_TRANSFER", "rate", "vat_rate_immovable_property", 9, "%", "cn.law.vat#10", "2026-01-01",
  "销售不动产，转让土地使用权，销售或者进口下列货物，除本条第四项、第五项规定外，税率为百分之九", "decision D48: art. 10 item 2")
p("cn.vat.law.simplified_rate", "CN", "ALL", "rate", "vat_simplified_rate", 3, "%", "cn.law.vat#11", "2026-01-01",
  "适用简易计税方法计算缴纳增值税的征收率为百分之三", "decision D48: small-scale taxpayers selling immovable property they acquired")
p("cn.vat.property_simplified_rate", "CN", "PROPERTY_TRANSFER", "rate", "vat_simplified_rate_old_property", 5, "%", "cn.cs.2026-10#i3", "2026-01-01",
  "按照5%的规定征收率计算缴纳增值税", "decision D48: III(2) 4 and 5: general taxpayers selling or transferring immovable property or land use rights acquired before 30 April 2016")
p("cn.vat.property_old_cutoff", "CN", "PROPERTY_TRANSFER", "condition", "old_property_acquired_before", "2016-04-30", "date", "cn.cs.2026-10#i3", "2026-01-01",
  "销售其2016年4月30日前取得（含自建）的不动产", "decision D48")
p("cn.vat.property_simplified_until", "CN", "PROPERTY_TRANSFER", "condition", "old_property_simplified_method_until", "2027-12-31", "date", "cn.cs.2026-10#i3", "2026-01-01",
  "自2026年1月1日至2027年12月31日，一般纳税人发生以下应税交易，可以选择适用简易计税方法，按照5%的规定征收率计算缴纳增值税",
  "decision D48: the time limit is judged by date inside the evaluator, without narrowing the rule's validity period")
p("cn.vat.property_purchase_deducted", "CN", "PROPERTY_TRANSFER", "condition", "purchase_price_deducted_under_simplified_method", 1, "bool", "cn.cs.2026-10#i4", "2026-01-01",
  "该项不动产购置原价或者取得不动产时的作价允许从含税销售额中扣除", "decision D48: IV(8); no deduction for self-built property")
p("cn.ucmt.rate_urban", "CN", "ALL", "rate", "ucmt_rate_city_district", 7, "%", "cn.law.ucmt#4", "2021-09-01",
  "纳税人所在地在市区的，税率为百分之七", "decision D48: 城市维护建设税法 art. 4")
p("cn.ucmt.rate_county", "CN", "ALL", "rate", "ucmt_rate_county_town", 5, "%", "cn.law.ucmt#4", "2021-09-01",
  "纳税人所在地在县城、镇的，税率为百分之五", "decision D48")
p("cn.ucmt.rate_other", "CN", "ALL", "rate", "ucmt_rate_elsewhere", 1, "%", "cn.law.ucmt#4", "2021-09-01",
  "纳税人所在地不在市区、县城或者镇的，税率为百分之一", "decision D48")
p("cn.ucmt.location_of_taxpayer", "CN", "ALL", "condition", "rate_by_where_the_taxpayer_is", 1, "bool", "cn.law.ucmt#4", "2021-09-01",
  "纳税人所在地，是指纳税人住所地或者与纳税人生产经营活动相关的其他地点，具体地点由省、自治区、直辖市确定", "decision D48: the case supplies ucmt_location")
p("cn.ucmt.base_vat_paid", "CN", "ALL", "condition", "base_is_vat_actually_paid", 1, "bool", "cn.law.ucmt#2", "2021-09-01",
  "城市维护建设税以纳税人依法实际缴纳的增值税、消费税税额为计税依据", "decision D48: input credit reduces the VAT actually paid and so the surcharges too")
p("cn.ucmt.no_foreign_services", "CN", "ALL", "condition", "not_on_import_or_foreign_service_vat", 1, "bool", "cn.law.ucmt#3", "2021-09-01",
  "对进口货物或者境外单位和个人向境内销售劳务、服务、无形资产缴纳的增值税、消费税税额，不征收城市维护建设税", "decision D48: art. 3")
p("cn.local_edu.rate", "CN", "ALL", "rate", "local_education_surcharge_rate", 2, "%", "cn.cz.2010-98#i2", "2010-11-07",
  "实际缴纳的增值税、营业税和消费税税额的2%", "decision D48: local education surcharge; the education surcharge (国发〔1986〕50号) is not in the library")
p("cn.local_edu.base_as_ucmt", "CN", "ALL", "condition", "surcharges_share_the_ucmt_base", 1, "bool", "cn.cs.2021-28#i2", "2021-09-01",
  "教育费附加、地方教育附加计征依据与城市维护建设税计税依据一致", "decision D48: art. 2")
p("cn.lat.rate_1", "CN", "PROPERTY_TRANSFER", "rate", "lat_rate_band_1", 30, "%", "cn.reg.lat#7", "1994-01-01",
  "增值额未超过扣除项目金额50%的部分，税率为30%", "decision D48: four-bracket progressive rates on the appreciation ratio")
p("cn.lat.rate_2", "CN", "PROPERTY_TRANSFER", "rate", "lat_rate_band_2", 40, "%", "cn.reg.lat#7", "1994-01-01",
  "增值额超过扣除项目金额50%、未超过扣除项目金额100%的部分，税率为40%", "decision D48")
p("cn.lat.rate_3", "CN", "PROPERTY_TRANSFER", "rate", "lat_rate_band_3", 50, "%", "cn.reg.lat#7", "1994-01-01",
  "增值额超过扣除项目金额100%、未超过扣除项目金额200%的部分，税率为50%", "decision D48")
p("cn.lat.rate_4", "CN", "PROPERTY_TRANSFER", "rate", "lat_rate_band_4", 60, "%", "cn.reg.lat#7", "1994-01-01",
  "增值额超过扣除项目金额200%的部分，税率为60%", "decision D48")
p("cn.lat.band_1", "CN", "PROPERTY_TRANSFER", "limit", "lat_band_1_ratio", 50, "%", "cn.reg.lat#7", "1994-01-01",
  "增值额未超过扣除项目金额50%的部分", "decision D48: each bracket's ratio includes the boundary figure (细则 art. 10)")
p("cn.lat.band_2", "CN", "PROPERTY_TRANSFER", "limit", "lat_band_2_ratio", 100, "%", "cn.reg.lat#7", "1994-01-01",
  "未超过扣除项目金额100%的部分", "decision D48")
p("cn.lat.band_3", "CN", "PROPERTY_TRANSFER", "limit", "lat_band_3_ratio", 200, "%", "cn.reg.lat#7", "1994-01-01",
  "未超过扣除项目金额200%的部分", "decision D48")
p("cn.lat.quick_2", "CN", "PROPERTY_TRANSFER", "rate", "lat_quick_deduction_band_2", 5, "%", "cn.reg.lat.rules#10", "1995-01-27",
  "土地增值税税额=增值额×40%-扣除项目金额×5%", "decision D48: 细则 art. 10")
p("cn.lat.quick_3", "CN", "PROPERTY_TRANSFER", "rate", "lat_quick_deduction_band_3", 15, "%", "cn.reg.lat.rules#10", "1995-01-27",
  "土地增值税税额=增值额×50%-扣除项目金额×15%", "decision D48")
p("cn.lat.quick_4", "CN", "PROPERTY_TRANSFER", "rate", "lat_quick_deduction_band_4", 35, "%", "cn.reg.lat.rules#10", "1995-01-27",
  "土地增值税税额=增值额×60%-扣除项目金额×35%", "decision D48")
p("cn.lat.revenue_excludes_vat", "CN", "PROPERTY_TRANSFER", "condition", "lat_revenue_net_of_vat", 1, "bool", "cn.sta.2016-70#i1", "2016-11-10",
  "营改增后，纳税人转让房地产的土地增值税应税收入不含增值税", "decision D48; see also 财税〔2016〕43号 art. 3")
p("cn.lat.old_building_appraisal", "CN", "PROPERTY_TRANSFER", "condition", "old_building_appraised_value_deducted", 1, "bool", "cn.reg.lat.rules#7", "1995-01-27",
  "旧房及建筑物的评估价格，是指在转让已使用的房屋及建筑物时，由政府批准设立的房地产评估机构评定的重置成本价乘以成新度折扣率后的价格",
  "decision D48: 细则 art. 7 (4); the case supplies lat_appraised_value (including the amount paid for the land use right)")
p("cn.lat.invoice_uplift", "CN", "PROPERTY_TRANSFER", "rate", "invoice_uplift_per_year", 5, "%", "cn.cs.2006-21#i2", "2006-03-02",
  "可按发票所载金额并从购买年度起至转让年度止每年加计5%计算", "decision D48: no appraised value available but a purchase invoice can be provided; 公告2016年第70号 art. 6 agrees")
p("cn.lat.invoice_year", "CN", "PROPERTY_TRANSFER", "condition", "invoice_uplift_year_months", 12, "months", "cn.gsh.2010-220#i7", "2010-05-19",
  "每满12个月计一年", "decision D48: over one year; under 12 months but over 6 months may be treated as one year")
p("cn.lat.deed_deductible", "CN", "PROPERTY_TRANSFER", "condition", "deed_tax_paid_on_purchase_deducted_not_uplifted", 1, "bool", "cn.cs.2006-21#i2", "2006-03-02",
  "对纳税人购房时缴纳的契税，凡能提供契税完税凭证的，准予作为“与转让房地产有关的税金”予以扣除，但不作为加计5%的基数", "decision D48")
p("cn.lat.taxes_deductible", "CN", "PROPERTY_TRANSFER", "condition", "transfer_taxes_deducted_excluding_vat", 1, "bool", "cn.sta.2016-70#i3", "2016-11-10",
  "计算土地增值税增值额的扣除项目中“与转让房地产有关的税金”不包括增值税", "decision D48: urban maintenance and construction tax and education surcharge deducted as incurred (art. 3 (2))")
p("cn.lat.stamp_and_local_edu_deductible", "CN", "PROPERTY_TRANSFER", "condition", "stamp_duty_and_local_edu_deducted", 1, "bool", "cn.sta.2026-03#i5", "2026-01-01",
  "纳税人因转让房地产缴纳的印花税，在申报土地增值税时计入“与转让房地产有关的税金”扣除", "decision D48: the local education surcharge is deducted as a tax")
p("cn.deed.rate_min", "CN", "PROPERTY_TRANSFER", "rate", "deed_tax_rate_min", 3, "%", "cn.law.deed#3", "2021-09-01",
  "契税税率为百分之三至百分之五", "decision D48: the specific rate is set by the provincial people's congress standing committee; the case supplies deed_tax_rate, otherwise both ends are taken")
p("cn.deed.rate_max", "CN", "PROPERTY_TRANSFER", "rate", "deed_tax_rate_max", 5, "%", "cn.law.deed#3", "2021-09-01",
  "契税税率为百分之三至百分之五", "decision D48")
p("cn.deed.transferee", "CN", "PROPERTY_TRANSFER", "condition", "transferee_is_taxpayer", 1, "bool", "cn.law.deed#1", "2021-09-01",
  "承受的单位和个人为契税的纳税人", "decision D48")
p("cn.deed.base_price", "CN", "PROPERTY_TRANSFER", "condition", "base_is_contract_price", 1, "bool", "cn.law.deed#4", "2021-09-01",
  "为土地、房屋权属转移合同确定的成交价格", "decision D48: art. 4 (1)")
p("cn.deed.base_excludes_vat", "CN", "PROPERTY_TRANSFER", "condition", "deed_base_net_of_vat", 1, "bool", "cn.cs.2016-43#i1", "2016-05-01",
  "计征契税的成交价格不含增值税", "decision D48")
p("cn.stamp.property_rate", "CN", "PROPERTY_TRANSFER", "rate", "stamp_duty_property_transfer_instrument_rate", 0.05, "%", "cn.law.stamp.flk#20", "2022-07-01",
  "价款的万分之五", "decision D48: instruments transferring land use rights and ownership of buildings and structures")
p("hk.stamp.avd_all_parties", "HK", "PROPERTY_TRANSFER", "condition", "all_parties_liable_contract_allocates", 1, "bool", "hk.cap117.en#sch1", "",
  "All parties, and all other persons executing", "decision D48: head 1(1)(C); the case supplies stamp_borne_by")
p("hk.stamp.avd_flat", "HK", "PROPERTY_TRANSFER", "limit", "avd_flat_duty", 100, "HKD", "hk.cap117.en#sch1", "",
  "$100 plus 20% of the amount by which the amount or value of the consideration exceeds $4,000,000", "decision D48: Scale 1 (a), (b)")
p("hk.stamp.avd_flat_limit", "HK", "PROPERTY_TRANSFER", "limit", "avd_flat_up_to", 4000000, "HKD", "hk.cap117.en#sch1", "",
  "where the amount or value of the consideration does not exceed $4,000,000", "decision D48")
p("hk.stamp.avd_first_marginal", "HK", "PROPERTY_TRANSFER", "rate", "avd_marginal_above_flat", 20, "%", "hk.cap117.en#sch1", "",
  "$100 plus 20% of the amount by which the amount or value of the consideration exceeds $4,000,000", "decision D48")
p("hk.stamp.avd_rate_1", "HK", "PROPERTY_TRANSFER", "rate", "avd_rate_band_1", 1.5, "%", "hk.cap117.en#sch1", "",
  "1.5% of the amount or value of the consideration", "decision D48: Scale 1 (c)")
p("hk.stamp.avd_limit_1", "HK", "PROPERTY_TRANSFER", "limit", "avd_band_1_up_to", 4500000, "HKD", "hk.cap117.en#sch1", "",
  "exceeds $4,323,780 but does not exceed $4,500,000", "decision D48")
p("hk.stamp.avd_rate_2", "HK", "PROPERTY_TRANSFER", "rate", "avd_rate_band_2", 2.25, "%", "hk.cap117.en#sch1", "",
  "2.25% of the amount or value of the consideration", "decision D48: Scale 1 (e)")
p("hk.stamp.avd_limit_2", "HK", "PROPERTY_TRANSFER", "limit", "avd_band_2_up_to", 6000000, "HKD", "hk.cap117.en#sch1", "",
  "exceeds $4,935,480 but does not exceed $6,000,000", "decision D48")
p("hk.stamp.avd_rate_3", "HK", "PROPERTY_TRANSFER", "rate", "avd_rate_band_3", 3, "%", "hk.cap117.en#sch1", "",
  "(g) 3% of the amount or value of the consideration", "decision D48: Scale 1 (g)")
p("hk.stamp.avd_limit_3", "HK", "PROPERTY_TRANSFER", "limit", "avd_band_3_up_to", 9000000, "HKD", "hk.cap117.en#sch1", "",
  "exceeds $6,642,860 but does not exceed $9,000,000", "decision D48")
p("hk.stamp.avd_rate_4", "HK", "PROPERTY_TRANSFER", "rate", "avd_rate_band_4", 3.75, "%", "hk.cap117.en#sch1", "",
  "3.75% of the amount or value of the consideration", "decision D48: Scale 1 (i)")
p("hk.stamp.avd_limit_4", "HK", "PROPERTY_TRANSFER", "limit", "avd_band_4_up_to", 20000000, "HKD", "hk.cap117.en#sch1", "",
  "exceeds $10,080,000 but does not exceed $20,000,000", "decision D48")
p("hk.stamp.avd_rate_5", "HK", "PROPERTY_TRANSFER", "rate", "avd_rate_band_5", 4.25, "%", "hk.cap117.en#sch1", "",
  "4.25% of the amount or value of the consideration", "decision D48: Scale 1 (k)")
p("hk.stamp.avd_limit_5", "HK", "PROPERTY_TRANSFER", "limit", "avd_band_5_up_to", 100000000, "HKD", "hk.cap117.en#sch1", "",
  "exceeds $21,739,120 but does not exceed $100,000,000", "decision D48")
p("hk.stamp.avd_marginal", "HK", "PROPERTY_TRANSFER", "rate", "avd_marginal_between_bands", 10, "%", "hk.cap117.en#sch1", "",
  "$67,500 plus 10% of the amount by which the amount or value of the consideration exceeds $4,500,000", "decision D48: (d), (f), (h), (j)")
p("hk.stamp.avd_top_marginal", "HK", "PROPERTY_TRANSFER", "rate", "avd_marginal_above_100m", 30, "%", "hk.cap117.en#sch1", "",
  "$4,250,000 plus 30% of the amount by which the amount or value of the consideration exceeds $100,000,000", "decision D48: (l)")
p("hk.stamp.avd_rate_top", "HK", "PROPERTY_TRANSFER", "rate", "avd_rate_top", 6.5, "%", "hk.cap117.en#sch1", "",
  "6.5% of the amount or value of the consideration", "decision D48: (m)")
p("hk.fsie.disposal_gains_commencement", "HK", "PROPERTY_TRANSFER", "condition", "non_ip_disposal_gains_from", 1, "bool", "hk.cap112.en#sch56", "2024-01-01",
  "apply in relation to specified foreign-sourced income accrued and received on or after 1 January 2024", "decision D48: Sch 56 s2(1)")
p("hk.fsie.trader_excluded", "HK", "PROPERTY_TRANSFER", "condition", "trader_gain_from_its_trade_not_fsie", 1, "bool", "hk.cap112.en#s15H", "2024-01-01",
  "is derived from, or is incidental to, the entity’s business as a trader", "decision D48: s15H “指明外地收入” (e)")
p("sg.stamp.bsd_band_1", "SG", "PROPERTY_TRANSFER", "limit", "bsd_first_band", 180000, "SGD", "sg.sda1929.sch1#sch1", "2023-02-15",
  "for every dollar of the first $180,000", "decision D48: Article 3(a)(iv)")
p("sg.stamp.bsd_band_2", "SG", "PROPERTY_TRANSFER", "limit", "bsd_second_band", 180000, "SGD", "sg.sda1929.sch1#sch1", "2023-02-15",
  "for every dollar of the next $180,000", "decision D48")
p("sg.stamp.bsd_band_3", "SG", "PROPERTY_TRANSFER", "limit", "bsd_third_band", 640000, "SGD", "sg.sda1929.sch1#sch1", "2023-02-15",
  "for every dollar of the next $640,000", "decision D48")
p("sg.stamp.bsd_band_4", "SG", "PROPERTY_TRANSFER", "limit", "bsd_fourth_band", 500000, "SGD", "sg.sda1929.sch1#sch1", "2023-02-15",
  "for every dollar of the next $500,000", "decision D48")
p("sg.stamp.bsd_band_5", "SG", "PROPERTY_TRANSFER", "limit", "bsd_fifth_band_residential", 1500000, "SGD", "sg.sda1929.sch1#sch1", "2023-02-15",
  "for every dollar of the next $1,500,000", "decision D48")
for k, (v, q) in enumerate(((1, "first $180,000"), (2, "next $180,000"), (3, "next $640,000"), (4, "next $500,000"),
                             (5, "next $1,500,000")), start=1):
    p("sg.stamp.bsd_res_%d" % k, "SG", "PROPERTY_TRANSFER", "rate", "bsd_residential_band_%d" % k, v, "%", "sg.sda1929.sch1#sch1", "2023-02-15",
      "for every dollar of the %s %d%%" % (q, v), "decision D48: residential portion")
p("sg.stamp.bsd_rate_top", "SG", "PROPERTY_TRANSFER", "rate", "bsd_residential_beyond_3m", 6, "%", "sg.sda1929.sch1#sch1", "2023-02-15",
  "for every dollar exceeding $3,000,000 6%", "decision D48")
for k, (v, q) in enumerate(((1, "first $180,000"), (2, "next $180,000"), (3, "next $640,000"), (4, "next $500,000")), start=1):
    p("sg.stamp.bsd_nonres_%d" % k, "SG", "PROPERTY_TRANSFER", "rate", "bsd_other_band_%d" % k, v, "%", "sg.sda1929.sch1#sch1", "2023-02-15",
      "for every dollar of the %s %d%%" % (q, v), "decision D48: remaining portion")
p("sg.stamp.bsd_nonres_top", "SG", "PROPERTY_TRANSFER", "rate", "bsd_other_beyond_1_5m", 5, "%", "sg.sda1929.sch1#sch1", "2023-02-15",
  "for every dollar exceeding $1,500,000 5%", "decision D48")
p("sg.stamp.absd_entity", "SG", "PROPERTY_TRANSFER", "rate", "absd_entity_residential", 65, "%", "sg.sda1929.sch1#sch1", "2023-04-27",
  "65% of the amount or the total amount of consideration of the residential property or properties conveyed, assigned or transferred",
  "decision D48: Article 3(bi)(xix): entities (other than housing developers)")
p("sg.stamp.absd_by_purchaser", "SG", "PROPERTY_TRANSFER", "condition", "buyer_bears_conveyance_duty", 1, "bool", "sg.sda1929.sch3#sch3", "",
  "The grantee, transferee or lessee", "decision D48: Third Schedule 2(a); s34: absent agreement to the contrary")
p("sg.stamp.ssd_res_1y", "SG", "PROPERTY_TRANSFER", "rate", "ssd_residential_within_1y", 16, "%", "sg.sda1929.sch1#sch1", "2025-07-04",
  "16% of the amount of consideration or value (whichever is applicable) of the part of the property attributable to a residential purpose",
  "decision D48: Article 3(bj): acquired from 2025-07-04; borne by the seller (Third Schedule 2(b))")
p("sg.stamp.ssd_res_2y", "SG", "PROPERTY_TRANSFER", "rate", "ssd_residential_within_2y", 12, "%", "sg.sda1929.sch1#sch1", "2025-07-04",
  "12% of the amount of consideration or value (whichever is applicable) of the part of the property attributable to a residential purpose", "decision D48")
p("sg.stamp.ssd_res_3y", "SG", "PROPERTY_TRANSFER", "rate", "ssd_residential_within_3y", 8, "%", "sg.sda1929.sch1#sch1", "2025-07-04",
  "8% of the amount of consideration or value (whichever is applicable) of the part of the property attributable to a residential purpose", "decision D48")
p("sg.stamp.ssd_res_4y", "SG", "PROPERTY_TRANSFER", "rate", "ssd_residential_within_4y", 4, "%", "sg.sda1929.sch1#sch1", "2025-07-04",
  "4% of the amount of consideration or value (whichever is applicable) of the part of the property attributable to a residential purpose", "decision D48")
p("sg.stamp.ssd_res_old_1y", "SG", "PROPERTY_TRANSFER", "rate", "ssd_residential_2017_within_1y", 12, "%", "sg.sda1929.sch1#sch1", "2017-03-11",
  "12% of the amount of consideration or value (whichever is applicable) of the part of the property attributable to a residential purpose",
  "decision D48: Article 3(bg): acquired between 2017-03-11 and 2025-07-03")
p("sg.stamp.ssd_res_old_2y", "SG", "PROPERTY_TRANSFER", "rate", "ssd_residential_2017_within_2y", 8, "%", "sg.sda1929.sch1#sch1", "2017-03-11",
  "8% of the amount of consideration or value (whichever is applicable) of the part of the property attributable to a residential purpose", "decision D48")
p("sg.stamp.ssd_res_old_3y", "SG", "PROPERTY_TRANSFER", "rate", "ssd_residential_2017_within_3y", 4, "%", "sg.sda1929.sch1#sch1", "2017-03-11",
  "4% of the amount of consideration or value (whichever is applicable) of the part of the property attributable to a residential purpose", "decision D48")
p("sg.stamp.ssd_ind_1y", "SG", "PROPERTY_TRANSFER", "rate", "ssd_industrial_within_1y", 15, "%", "sg.sda1929.sch1#sch1", "2013-01-12",
  "15% of the amount of consideration or value (whichever is applicable) of the part of the property attributable to an industrial purpose",
  "decision D48: Article 3(bd): industrial property acquired from 2013-01-12")
p("sg.stamp.ssd_ind_2y", "SG", "PROPERTY_TRANSFER", "rate", "ssd_industrial_within_2y", 10, "%", "sg.sda1929.sch1#sch1", "2013-01-12",
  "10% of the amount of consideration or value (whichever is applicable) of the part of the property attributable to an industrial purpose", "decision D48")
p("sg.stamp.ssd_ind_3y", "SG", "PROPERTY_TRANSFER", "rate", "ssd_industrial_within_3y", 5, "%", "sg.sda1929.sch1#sch1", "2013-01-12",
  "5% of the amount of consideration or value (whichever is applicable) of the part of the property attributable to an industrial purpose", "decision D48")
p("sg.stamp.ssd_res_new_from", "SG", "PROPERTY_TRANSFER", "condition", "ssd_four_year_regime_acquired_from", "2025-07-04", "date", "sg.sda1929.sch1#sch1", "2025-07-04",
  "property acquired on or after 4 July 2025", "decision D48")
p("sg.stamp.ssd_res_old_from", "SG", "PROPERTY_TRANSFER", "condition", "ssd_three_year_regime_acquired_from", "2017-03-11", "date", "sg.sda1929.sch1#sch1", "2017-03-11",
  "acquired on or after 11 March 2017 but before 4 July 2025", "decision D48")
p("sg.stamp.ssd_ind_from", "SG", "PROPERTY_TRANSFER", "condition", "ssd_industrial_acquired_from", "2013-01-12", "date", "sg.sda1929.sch1#sch1", "2013-01-12",
  "industrial property acquired on or after 12 January 2013", "decision D48")
p("sg.gst.residential_land_exempt", "SG", "PROPERTY_TRANSFER", "condition", "residential_property_sale_exempt", 1, "bool", "sg.etax.gst.property#para2.1", "",
  "except for the sale and lease of residential properties which are exempt from GST", "decision D48: Fourth Schedule para 2")
p("sg.gst.registered_supplier", "SG", "PROPERTY_TRANSFER", "condition", "registered_seller_charges_gst", 1, "bool", "sg.etax.gst.property#para4.1", "",
  "If you are registered for GST, you have to charge GST when you sell or let out a non-residential property", "decision D48")
p("sg.gst.property_taxable", "SG", "PROPERTY_TRANSFER", "condition", "non_residential_sale_taxable", 1, "bool", "sg.etax.gst.property#para6.3", "",
  "The sale of a non-residential property is a taxable supply", "decision D48; the buyer may claim input tax (para 9.1)")
# ---- decision D49: the rent of land or a building
p("cn.vat.rent_rate", "CN", "PROPERTY_RENT", "rate", "vat_rate_immovable_lease", 9, "%", "cn.law.vat#10", "2026-01-01",
  "纳税人销售交通运输、邮政、基础电信、建筑、不动产租赁服务，销售不动产，转让土地使用权，销售或者进口下列货物，除本条第四项、第五项规定外，税率为百分之九",
  "decision D49: art. 10 item 2; property acquired before 30 April 2016 may opt for 5% (公告2026年第10号 III(2) 3)")
p("cn.property_tax.rent_rate", "CN", "PROPERTY_RENT", "rate", "property_tax_rate_on_rent", 12, "%", "cn.reg.property#4", "1986-10-01",
  "依照房产租金收入计算缴纳的，税率为12%", "decision D49: 房产税暂行条例 art. 4")
p("cn.property_tax.rent_base", "CN", "PROPERTY_RENT", "condition", "property_tax_on_rent_when_let", 1, "bool", "cn.reg.property#3", "1986-10-01",
  "房产出租的，以房产租金收入为房产税的计税依据", "decision D49")
p("cn.property_tax.owner", "CN", "PROPERTY_RENT", "condition", "owner_pays_property_tax", 1, "bool", "cn.reg.property#2", "1986-10-01",
  "房产税由产权所有人缴纳", "decision D49: when the owner is not where the property is, the custodian or user pays (same article)")
p("cn.property_tax.area", "CN", "PROPERTY_RENT", "condition", "levied_in_cities_towns_and_mining_areas", 1, "bool", "cn.reg.property#1", "1986-10-01",
  "房产税在城市、县城、建制镇和工矿区征收", "decision D49: the case supplies property_tax_area")
p("cn.property_tax.rent_excludes_vat", "CN", "PROPERTY_RENT", "condition", "rent_base_net_of_vat", 1, "bool", "cn.cs.2016-43#i2", "2016-05-01",
  "房产出租的，计征房产税的租金收入不含增值税", "decision D49")
p("cn.stamp.lease_rate", "CN", "PROPERTY_RENT", "rate", "stamp_duty_lease_contract_rate", 0.1, "%", "cn.law.stamp.flk#20", "2022-07-01",
  "租金的千分之一", "decision D49: lease contracts, each party")
p("cn.rent.lessor_profit", "CN", "PROPERTY_RENT", "condition", "lessor_taxed_on_rent_net_of_costs", 1, "bool", "cn.law.eit#8", "2008-01-01",
  "企业实际发生的与取得收入有关的、合理的支出，包括成本、费用、税金、损失和其他支出，准予在计算应纳税所得额时扣除", "decision D49: the case supplies profit_margin")
p("cn.deduct.operating_lease", "CN", "PROPERTY_RENT", "condition", "operating_lease_rent_deducted_over_term", 1, "bool", "cn.reg.eit#47", "2008-01-01",
  "以经营租赁方式租入固定资产发生的租赁费支出，按照租赁期限均匀扣除", "decision D49")
p("hk.property_tax.rate", "HK", "PROPERTY_RENT", "rate", "property_tax_standard_rate", 15, "%", "hk.cap112.en#sch1", "2024-04-01",
  "(b) for other taxes — 15%", "decision D49: Sch 1 standard rate")
p("hk.property_tax.repairs_allowance", "HK", "PROPERTY_RENT", "rate", "repairs_and_outgoings_allowance", 20, "%", "hk.cap112.en#s5", "",
  "an allowance for repairs and outgoings of 20% of that assessable value", "decision D49: s5(1A)")
p("hk.property_tax.assessable_value", "HK", "PROPERTY_RENT", "condition", "assessable_value_is_the_rent", 1, "bool", "hk.cap112.en#s5B", "",
  "The assessable value of land or buildings or land and buildings for each year of assessment shall be the consideration", "decision D49")
p("hk.property_tax.set_off", "HK", "PROPERTY_RENT", "condition", "property_tax_set_off_against_profits_tax", 1, "bool", "hk.cap112.en#s25", "",
  "any profits tax payable by such person in respect of that year of assessment shall be reduced by a sum not exceeding the amount of such property tax paid by him",
  "decision D49: s25; the excess is refunded, so a business operator bears profits tax only")
p("hk.deduct.rent_for_premises", "HK", "PROPERTY_RENT", "condition", "tenant_deducts_rent_for_premises", 1, "bool", "hk.cap112.en#s16", "",
  "rent paid by any tenant of land or buildings occupied by him for the purpose of producing such profits", "decision D49: s16(1)(b)")
p("hk.stamp.lease_short", "HK", "PROPERTY_RENT", "rate", "lease_stamp_term_up_to_a_year", 0.25, "%", "hk.cap117.en#sch1", "",
  "25 cents for every $100 or part thereof of the total rent payable over the term of the lease", "decision D49: First Schedule head 1(2)(b)(ii)")
p("hk.stamp.lease_mid", "HK", "PROPERTY_RENT", "rate", "lease_stamp_term_one_to_three_years", 0.5, "%", "hk.cap117.en#sch1", "",
  "50 cents for every $100 or part thereof of the yearly or average yearly rent", "decision D49: (iii)")
p("hk.stamp.lease_long", "HK", "PROPERTY_RENT", "rate", "lease_stamp_term_above_three_years", 1, "%", "hk.cap117.en#sch1", "",
  "$1 for every $100 or part thereof of the yearly or average yearly rent", "decision D49: (iv)")
p("sg.rent.income", "SG", "PROPERTY_RENT", "condition", "rents_are_income", 1, "bool", "sg.ita1947.full#s10", "",
  "rents, royalties, premiums and any other profits arising from property", "decision D49: s10(1)(f); the case supplies profit_margin")
p("sg.deduct.rent_for_premises", "SG", "PROPERTY_RENT", "condition", "tenant_deducts_rent_for_premises", 1, "bool", "sg.ita1947.full#s14", "",
  "rent payable by any person in respect of any land or building or part thereof occupied by the person for the purpose of acquiring the income",
  "decision D49: s14(1)(b)")
p("sg.property_tax.max_rate", "SG", "PROPERTY_RENT", "rate", "property_tax_rate_ceiling", 36, "%", "sg.pta1960.s9#all", "",
  "at the rate of 36% upon the annual value of every property included in the Valuation List", "decision D49: s9(1); the Minister's order sets lower rates")
p("sg.property_tax.non_residential", "SG", "PROPERTY_RENT", "rate", "property_tax_non_residential", 10, "%", "sg.iras.ptax.rates#h9", "2024-01-01",
  "Non-residential properties such as commercial and industrial buildings and land are taxed at 10% of the Annual Value", "decision D49")
p("sg.property_tax.res_1", "SG", "PROPERTY_RENT", "rate", "property_tax_let_residential_first_band", 12, "%", "sg.iras.ptax.rates#h6", "2024-01-01",
  "First 30,000 Next $15,000 12% 20%", "decision D49: non-owner-occupied residential, from 2024-01-01")
p("sg.property_tax.res_2", "SG", "PROPERTY_RENT", "rate", "property_tax_let_residential_second_band", 20, "%", "sg.iras.ptax.rates#h6", "2024-01-01",
  "First 30,000 Next $15,000 12% 20%", "decision D49")
p("sg.property_tax.res_3", "SG", "PROPERTY_RENT", "rate", "property_tax_let_residential_third_band", 28, "%", "sg.iras.ptax.rates#h6", "2024-01-01",
  "First $45,000 Next $15,000 - 28%", "decision D49")
p("sg.property_tax.res_4", "SG", "PROPERTY_RENT", "rate", "property_tax_let_residential_above_60000", 36, "%", "sg.iras.ptax.rates#h6", "2024-01-01",
  "First $60,000 Above $60,000 - 36%", "decision D49")
p("sg.property_tax.band_1", "SG", "PROPERTY_RENT", "limit", "property_tax_first_band", 30000, "SGD", "sg.iras.ptax.rates#h6", "2024-01-01",
  "First 30,000 Next $15,000 12% 20%", "decision D49")
p("sg.property_tax.band_2", "SG", "PROPERTY_RENT", "limit", "property_tax_second_band", 15000, "SGD", "sg.iras.ptax.rates#h6", "2024-01-01",
  "First 30,000 Next $15,000 12% 20%", "decision D49")
p("sg.property_tax.band_3", "SG", "PROPERTY_RENT", "limit", "property_tax_third_band", 15000, "SGD", "sg.iras.ptax.rates#h6", "2024-01-01",
  "First $45,000 Next $15,000 - 28%", "decision D49")
p("sg.stamp.lease_rate", "SG", "PROPERTY_RENT", "rate", "lease_duty_rate", 0.4, "%", "sg.sda1929.sch1#sch1", "2014-02-22",
  "0.4% × A × 4 where A is the average rent and other consideration calculated for a whole year",
  "decision D49: Article 8(aa); up to 4 years, 0.4% of the total rent over the lease term (formula image, formulas.csv)")
p("sg.stamp.lease_years", "SG", "PROPERTY_RENT", "condition", "lease_duty_on_at_most_four_years_rent", 4, "years", "sg.sda1929.sch1#sch1", "2014-02-22",
  "Not exceeding 4 years Exceeding 4 years or for any indefinite term", "decision D49")
p("sg.stamp.lease_by_lessee", "SG", "PROPERTY_RENT", "condition", "lessee_bears_lease_duty", 1, "bool", "sg.sda1929.sch3#sch3", "",
  "LEASE or AGREEMENT FOR A LEASE — Article 8 The lessee", "decision D49: Third Schedule 4")
# ---- decision D51: losses — each company's taxable income by year, losses carried between years (tax_graph.losses)
A106 = "cn.form.a108000.a01#all"
A100 = "cn.form.a108000.a01#all"
p("cn.loss.carryforward_years", "CN", "ALL", "limit", "loss_carryforward_years", 5, "years", "cn.law.eit#18", "2008-01-01",
  "企业纳税年度发生的亏损，准予向以后年度结转，用以后年度的所得弥补，但结转年限最长不得超过五年", "decision D51: loss-offset enterprise type 100")
p("cn.loss.definition", "CN", "ALL", "condition", "loss_after_exempt_income", 1, "bool", "cn.reg.eit#10", "2008-01-01",
  "将每一纳税年度的收入总额减除不征税收入、免税收入和各项扣除后小于零的数额", "decision D51: exempt income does not offset losses")
p("cn.loss.order", "CN", "ALL", "procedure", "loss_soonest_expiry_first", 1, "bool", A106, "2024-01-01",
  "先到期亏损先弥补、同时到期亏损先发生的先弥补", "decision D51: 公告2025年第1号 A106000 filing instructions, from the 2024 tax year")
p("cn.loss.carryforward_years_extended", "CN", "ALL", "limit", "loss_carryforward_years_extended", 10, "years", A106, "2024-01-01",
  "亏损结转年限为10年的纳税人", "decision D51: codes 200, 300, 400 (财税〔2018〕76号; 2020年第45号)")
p("cn.loss.carryforward_years_2020", "CN", "ALL", "limit", "loss_carryforward_years_2020", 8, "years", A106, "2024-01-01",
  "最长结转年限由5年延长至8年", "decision D51: codes 500 and 600, only losses incurred in 2020 (2020年第8号, 第25号)")
p("cn.loss.covid_loss_year", "CN", "ALL", "condition", "loss_year_extended_to_8", "2020", "text", A106, "2024-01-01",
  "2020年度发生的亏损", "decision D51")
p("cn.loss.foreign_offset_elective", "CN", "ALL", "condition", "foreign_income_offsets_domestic_loss_elective", 1, "bool", A100,
  "2024-01-01", "当纳税人选择用境外所得抵减境内亏损时，填报境外所得抵减当年度境内亏损的金额",
  "decision D51: A100000 line 23; prior-year losses in A106000 column 11; A108000 column 6 after offset is the foreign taxable income")
p("cn.loss.foreign_offset_order", "CN", "ALL", "condition", "foreign_offset_country_order_elective", 1, "bool", "cn.sta.2010-01.a01#16",
  "2010-01-01", "企业可以自行选择弥补境内亏损的境外所得来源国家（地区）顺序", "decision D51: 操作指南 ¶28")
p("cn.loss.foreign_offset_limit", "CN", "ALL", "condition", "foreign_offset_not_reused", 1, "bool", "cn.sta.2010-01.a01#16",
  "2010-01-01", "境内已用境外盈利弥补的亏损不得再用以后年度境内盈利重复弥补", "decision D51: 操作指南 ¶27, the limit then becomes zero (example 8)")
p("cn.loss.foreign_not_domestic", "CN", "ALL", "condition", "foreign_branch_loss_not_against_domestic", 1, "bool", "cn.law.eit#17",
  "2008-01-01", "其境外营业机构的亏损不得抵减境内营业机构的盈利", "decision D51")
p("cn.loss.foreign_branch_country", "CN", "ALL", "condition", "foreign_branch_loss_same_country", 1, "bool", "cn.cs.2009-125#i3",
  "2008-01-01", "不得抵减其境内或他国（地区）的应纳税所得额，但可以用同一国家（地区）其他项目或以后年度的所得按规定弥补", "decision D51")
p("cn.loss.branch_nonactual_unlimited", "CN", "ALL", "condition", "foreign_branch_nonactual_loss_unlimited", 1, "bool",
  "cn.sta.2010-01.a01#16", "2010-01-01", "今后在该分支机构的结转弥补期限不受5年期限制", "decision D51: 操作指南 ¶14 (example 2)")
p("hk.loss.carryforward", "HK", "ALL", "condition", "loss_carried_forward_unlimited", 1, "bool", "hk.cap112.en#s19C", "",
  "to the extent not so set off, shall be carried forward and set off against the corporation’s or the person’s assessable profits",
  "decision D51: s19C(4), no time limit")
p("hk.loss.hk_activities", "HK", "ALL", "condition", "loss_attributable_to_hk", 1, "bool", "hk.cap112.en#s19C", "",
  "the amount of any loss to be set off under this section shall be the loss attributable to activities in Hong Kong", "decision D51: s19C(6)(d)")
p("hk.loss.change", "HK", "ALL", "anti_abuse", "loss_after_shareholding_change_disallowed", 1, "bool", "hk.cap112.en#s61B", "",
  "the set off of any such loss or balance of loss against any such profits shall be disallowed", "decision D51: s61B, the Commissioner's finding (a judgement)")
p("sg.loss.carryforward", "SG", "ALL", "condition", "brought_forward_loss_first", 1, "bool", "sg.ita1947.full#s37", "",
  "firstly, any balance of such loss which remains unabsorbed at the end of the basis period for the previous year of assessment",
  "decision D51: s37(3)(a)")
p("sg.loss.order_years", "SG", "ALL", "procedure", "loss_earliest_year_first", 1, "bool", "sg.ita1947.full#s37", "",
  "from the statutory income of the first year of assessment after the year in which such loss was incurred", "decision D51: s37(5), no time limit")
p("sg.loss.continuity", "SG", "ALL", "anti_abuse", "loss_shareholders_substantially_same", 1, "bool", "sg.ita1947.full#s37", "",
  "is disregarded unless the Comptroller is satisfied that the shareholders of the company on the last day of the year in which the loss was incurred",
  "decision D51: s37(12), (13)")
p("sg.loss.shareholders_same_min", "SG", "ALL", "condition", "loss_same_shareholders_min", 50, "%", "sg.ita1947.full#s37", "",
  "not less than 50% of the total number of issued shares of the company are held by or on behalf of the same persons", "decision D51: s37(14)(a)")
p("sg.loss.look_through", "SG", "ALL", "condition", "loss_shareholders_looked_through", 1, "bool", "sg.ita1947.full#s37", "",
  "shares in a company held by or on behalf of another company are deemed to be held by the shareholders of the last mentioned company",
  "decision D51: s37(14)(b)")
p("sg.loss.waiver", "SG", "ALL", "condition", "loss_waiver_same_trade", 1, "bool", "sg.ita1947.full#s37", "",
  "may only be deducted against the profits from the same trade or business of the company in respect of which that loss was incurred",
  "decision D51: s37(17)(a) after a ministerial waiver under s37(16)")
p("sg.group_relief.transfer", "SG", "ALL", "condition", "group_relief", 1, "bool", "sg.ita1947.full#s37B", "",
  "a transferor company may transfer any qualifying deduction for any year of assessment to a claimant company of the same group",
  "decision D51: s37B(1)")
p("sg.group_relief.ratio_min", "SG", "ALL", "condition", "group_relief_ratio_min", 75, "%", "sg.ita1947.full#s37B", "",
  "at least 75% of the total number of issued ordinary shares in one company are beneficially held, directly or indirectly, by the other",
  "decision D51: s37B(3), (5), multiplied through Singapore companies")
p("sg.group_relief.qualifying_loss", "SG", "ALL", "condition", "group_relief_current_year_loss", 1, "bool", "sg.ita1947.full#s37B", "",
  "which is not deducted for that year of assessment because of insufficiency of statutory income of the transferor company",
  "decision D51: s37B(14)(b), only the current year's unabsorbed loss")
p("sg.group_relief.days", "SG", "ALL", "procedure", "group_relief_days_in_group", 1, "bool", "sg.ita1947.full#s37B", "",
  "the number of days in the continuous period ending on the last day of the basis period for that year of assessment during which the companies are members of the same group",
  "decision D51: s37B(9) A/B, formula image in formulas.csv")
p("sg.group_relief.singapore_company", "SG", "ALL", "condition", "group_relief_singapore_incorporated", 1, "bool", "sg.ita1947.full#s37B", "",
  "“Singapore company” means any company incorporated in Singapore", "decision D51: s37B(19)")
p("sg.group_relief.election", "SG", "ALL", "procedure", "group_relief_election", 1, "bool", "sg.ita1947.full#s37B", "",
  "make an irrevocable election to transfer or claim qualifying deductions", "decision D51: s37B(11), elected by both")

p("hk.domestic.dividend_excluded", "HK", "DIVIDEND", "condition", "dividend_from_chargeable_corporation_excluded", 1, "bool", "hk.cap112.en#s26", "",
  "a dividend from a corporation which is chargeable to tax under this Part shall not be included in", "s26(a)")
# ---- GST reverse charge: the cost is the unrecoverable share (s19, s20)
p("sg.gst.recovery_ratio_basis", "SG", "ALL", "condition", "input_tax_credit_by_recovery_ratio", 1, "bool", "sg.gsta1993.s14#s14", "2020-01-01",
  "credit for the full amount of the recipient’s input tax under sections 19 and 20", "the reverse-charged output tax is credited as input tax at the recovery ratio under s19/s20; net cost = 9% × (1 − ratio)")
# ---- royalty versus service (国税函〔2009〕507号); only tax due under the treaty is creditable
p("cn.treaty.service_not_royalty", "CN", "SERVICE_FEE", "condition", "service_using_know_how_without_licensing_not_royalty", 1, "bool", "cn.gsh.2009-507#i4", "2009-10-01",
  "如果服务提供方提供服务过程中使用了某些专门知识和技术，但并不转让或许可这些技术，则此类服务不属于特许权使用费范围", "art. 4; except where the result falls within the royalty definition and the provider keeps ownership")
p("cn.treaty.professional_services_business_profits", "CN", "SERVICE_FEE", "condition", "professional_services_are_business_profits", 1, "bool", "cn.gsh.2009-507#i6", "2009-10-01",
  "专门从事工程、管理、咨询等专业服务的机构或个人提供的相关服务所取得的款项", "art. 6 (3): service income, the business profits article applies")
p("cn.ftc.not_due_under_treaty_not_creditable", "CN", "ALL", "condition", "tax_not_due_under_treaty_not_creditable", 1, "bool", "cn.cs.2009-125#i4", "2010-01-01",
  "按照税收协定规定不应征收的境外所得税税款", "art. 4 (2): tax over-withheld is not credited; refund at source instead")
p("sg.ftc.tax_payable_under_arrangements", "SG", "ALL", "condition", "credit_for_tax_payable_under_the_arrangements", 1, "bool", "sg.ita1947.full#s50", "",
  "tax payable in respect of any income in the territory with the government of which the arrangements are made is to be allowed as a credit", "s50(1): credit limited to the tax payable under the treaty")
p("sg.wht.service_outside_sg_excluded", "SG", "SERVICE_FEE", "condition", "management_fee_performed_outside_sg_not_deemed", 1, "bool", "sg.ita1947.full#s12", "",
  "the management or assistance in the management of any trade, business or profession, where such management or assistance is performed outside Singapore for or on behalf of a person resident in Singapore or a permanent establishment in Singapore by a non‑resident person who",
  "s12(7A)(b): a non-resident performing the services abroad without a Singapore business or permanent establishment is not deemed Singapore source")
p("cn-sg.pe.service_days", SG, "SERVICE_FEE", "condition", "service_pe_days_in_12_months", 183, "days", "treaty.cn-sg.2007.p2.zh#1", "2010-01-01",
  "取消第三款第（二）项中“六个月”的规定，用“一百八十 三天”代替", "Second Protocol art. 1: service permanent establishment threshold of 183 days")
p("cn-hk.pe.service_days", HK, "SERVICE_FEE", "condition", "service_pe_days_in_12_months", 183, "days", "treaty.cn-hk.2006.p2.zh#3", "2008-06-11",
  "取消《安排》第五条第三款（二）项中“六个月”的规定， 用“一百八十三天”代替", "Second Protocol art. 3: service permanent establishment threshold of 183 days")
p("cn-sg.pe.business_profits_residence_only", SG, "SERVICE_FEE", "condition", "business_profits_taxed_at_source_only_through_pe", 1, "bool", "treaty.cn-sg.2007.zh#7.1", "2008-01-01",
  "缔约国一方企业的利润应仅在该缔约国征税，但该企业 通过设在缔约国另一方的常设机构在该缔约国另一方进行营业 的除外", "art. 7(1): without a permanent establishment the source state does not tax business profits")
p("cn-hk.pe.business_profits_residence_only", HK, "SERVICE_FEE", "condition", "business_profits_taxed_at_source_only_through_pe", 1, "bool", "treaty.cn-hk.2006.zh#7.1", "2007-01-01",
  "一方企业的利润应仅在该一方征税，但该企业通过设在另一 方的常设机构在该另一方进行营业的除外", "art. 7(1)")
p("cn.service.deemed_profit_min", "CN", "SERVICE_FEE", "rate", "deemed_profit_rate_management_min", 30, "%", "cn.gsf.2010-19#5", "2010-02-20",
  "从事管理服务的，利润率为30%-50%", "lower bound of the deemed profit rate for management services")
p("cn.service.deemed_profit_max", "CN", "SERVICE_FEE", "rate", "deemed_profit_rate_management_max", 50, "%", "cn.gsf.2010-19#5", "2010-02-20",
  "从事管理服务的，利润率为30%-50%", "upper bound of the deemed profit rate for management services")
p("cn.service.deemed_profit_other_min", "CN", "SERVICE_FEE", "rate", "deemed_profit_rate_other_min", 15, "%", "cn.gsf.2010-19#5", "2010-02-20",
  "从事其他劳务或劳务以外经营活动的，利润率不低于15%", "lower bound of the deemed profit rate for other services")
p("cn.service.deemed_basis", "CN", "SERVICE_FEE", "condition", "deemed_income_equals_revenue_times_profit_rate", 1, "bool", "cn.gsf.2010-19#4", "2010-02-20",
  "应纳税所得额=收入总额×经税务机关核定的利润率", "deemed on gross revenue")
p("cn.service.source_where_performed", "CN", "SERVICE_FEE", "condition", "service_income_sourced_where_performed", 1, "bool", "cn.reg.eit#7", "2008-01-01",
  "提供劳务所得，按照劳务发生地确定", "art. 7 (2): service income is sourced where the service is performed")
p("sg.wht.service_fee", "SG", "SERVICE_FEE", "condition", "management_fees_deemed_sg_source", 1, "bool", "sg.ita1947.full#s12", "",
  "any payment for the management or assistance in the management of any trade", "s12(7)(c): management fees deemed Singapore source; withheld under s45 by virtue of s45A")
p("sg.wht.s45a_applies", "SG", "SERVICE_FEE", "procedure", "s45_applies_to_s12_7_payments", 1, "bool", "sg.ita1947.full#s45A", "",
  "Section 45(1) to (8) applies in relation to the payment of any income referred to in section 12(6) or (7)", "s45A(1)")
# ---- liquidation and capital reduction: a distribution splits into a dividend part and a disposal part
p("cn.liquidation.split", "CN", "LIQUIDATION", "condition", "liquidation_proceeds_split_dividend_then_gain", 1, "bool", "cn.cs.2009-60#i5", "2008-01-01",
  "其中相当于被清算企业累计未分配利润和累计盈余公积中按该股东所占股份比例计算的部分，应确认为股息所得；剩余资产减除股息所得后的余额，超过或低于股东投资成本的部分，应确认为股东的投资转让所得或损失",
  "liquidation distribution: dividend first (accumulated undistributed profits and surplus reserve pro rata), the remainder less cost is transfer income")
p("cn.capital_reduction.split", "CN", "CAPITAL_REDUCTION", "condition", "capital_reduction_split_return_dividend_gain", 1, "bool", "cn.sta.2011-34#i5", "2011-07-01",
  "相当于初始出资的部分，应确认为投资收回；相当于被投资企业累计未分配利润和累计盈余公积按减少实收资本比例计算的部分，应确认为股息所得；其余部分确认为投资资产转让所得",
  "capital reduction: the initial contribution is a return of investment, accumulated profits pro rata are a dividend, the rest is transfer income")

XC = {
    "cn.reinvest.credit_rate": "cn.sta.2025-18.interp: the interpretation agrees with the announcement, a choice between 10% and the lower treaty rate",
    "sg.wht.late_penalty_monthly_cap": "S45 calculator 2026-10-06: nineteen months late, penalty 200 = 5% + 15% cap, consistent, label sg_s45.12",
    "sg.dtr.cor_due_prior_years": "S45 calculator 2026-10-06: a 2025 payment queried in 2026 prompts for submission within 3 months of filing, labels sg_s45.12, 13",
    "sg.time.excluded_days": "S45 calculator 2026-10-06: the Sunday roll-over is in label sg_s45.09; the public holiday 17 May 2027 met during the roll-over is excluded, see label sg_s45.11",
    "sg.dtr.cor_due": "S45 calculator 2026-10-06: a 2026 payment prompts 31 Mar 2027, a 2027 payment prompts 31 Mar 2028, consistent, labels sg_s45.01, 11",
    "cn-sg.int.cap_other": "S45 calculator 2026-10-06: 10.00%, consistent, label sg_s45.01; cn.gsf.2010-75#11 interpretation of para. 2: interest in other cases is taxed at 10%, consistent",
    "cn-sg.int.cap_bank": "S45 calculator 2026-10-06: 7.00%, consistent, label sg_s45.02; cn.gsf.2010-75#11 interpretation of para. 2: 7% when the beneficial owner is a bank or financial institution, consistent",
    "cn-sg.roy.cap": "S45 calculator 2026-10-06: 10.00%, consistent, label sg_s45.04; cn.gsf.2010-75#12 interpretation of para. 2: maximum rate set at 10%, consistent",
    "cn-sg.roy.equipment_base": "Protocol art. 3 in both the Chinese and English texts agrees with the 国税发〔2010〕75号 art. 12 interpretation: tax base at 60% of the gross; the later Second and Third Protocols and the MLI leave it unchanged. The S45 calculator 2026-10-06 shows only the nominal rate 10.00%, label sg_s45.05",
    "sg.wht.interest": "S45 calculator 2026-10-06: non-treaty rate 15.00%, consistent, labels sg_s45.01, 06",
    "sg.wht.royalty": "S45 calculator 2026-10-06: non-treaty rate 10.00%, consistent, labels sg_s45.04, 07",
    "sg.wht.rate_fallback": "S45 calculator 2026-10-06: 17.00% when derived through a fixed place of business, consistent, label sg_s45.08",
    "hk-sg.no_comprehensive_dta": "S45 calculator 2026-10-06: the treaty rate for Hong Kong is Not Applicable, consistent, labels sg_s45.06, 07",
    "sg.wht.late_penalty": "S45 calculator 2026-10-06: the penalty is computed on the tax at the treaty rate, label sg_s45.09",
    "sg.wht.filing_due": "S45 calculator 2026-10-06: 15 Mar 2026 is a Sunday, shows 16 Mar 2026, consistent with Interpretation Act s50, label sg_s45.09; the IRAS page example writes the nominal date 15 Jun 2025, label sg_iras_ex.01",
    "sg.wht.late_penalty_monthly_starts_after_days": "S45 calculator 2026-10-06: additional penalty for 5 complete months, label sg_s45.09; IRAS page example: 2 complete months totalling 490, label sg_iras_ex.02; both consistent",
}
for r in R:
    if r["param_id"] in XC:
        r["cross_check"] = XC[r["param_id"]]

with (ROOT / "params.csv").open("w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=FIELDS)
    w.writeheader()
    w.writerows(R)
print("params written:", len(R))
