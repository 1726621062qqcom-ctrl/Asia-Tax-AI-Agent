"""Mainland withholding on dividends, interest and royalties paid to a Hong Kong or Singapore company, with the
Arrangement / Agreement on top (规则层.md §7 step 2). Structure only; numbers come from params.csv.

Treaty rule ids end in "@cn" because the same treaty parameter also serves the Singapore-source direction.
"""
from .model import (ALL, ALWAYS, And, Discretion, Effect, Leaf, Mount, Not, Or, RuleObj, Scope, ge, gt, is_false, is_in, is_true, le, lt)

CN, HK, SG = "CN", "HK", "SG"
DIVIDEND, INTEREST, ROYALTY, SHARE_TRANSFER = "DIVIDEND", "INTEREST", "ROYALTY", "SHARE_TRANSFER"
SERVICE_FEE, LIQUIDATION, CAPITAL_REDUCTION = "SERVICE_FEE", "LIQUIDATION", "CAPITAL_REDUCTION"
CFC_INCLUSION = "CFC_INCLUSION"
IP_TRANSFER = "IP_TRANSFER"
GOODS = "GOODS"                                                 # decision D42
BRANCH_PROFIT = "BRANCH_PROFIT"                                 # decision D47
PROPERTY = "PROPERTY_TRANSFER"                                  # decision D48
RENT = "PROPERTY_RENT"                                          # decision D49
RELATED = (INTEREST, ROYALTY, SERVICE_FEE)                       # the related-party dealings the model prices
PASSIVE = (DIVIDEND, INTEREST, ROYALTY, SHARE_TRANSFER, PROPERTY, RENT)   # EIT art 3(3) income, withheld at source (art 37)
INDIRECT = Scope(ALL, None, SHARE_TRANSFER, mount=Mount.SUBGRAPH, side=CN)   # an offshore transfer the Mainland taxes


def dom(income):
    return Scope(CN, None, income)


LOSS_CN = Scope(ALL, CN, ALL, mount=Mount.ENTITY, side="residence")      # decision D51


# 财税〔2018〕102号 第二条: the conditions of the reinvestment deferral
REINVEST_DEFERRAL = And(Leaf("reinvested_in_cn", is_true),
                        Leaf("reinvestment_form", is_in, "cn.reinvest.forms"),
                        Leaf("direct_payment", is_true, "cn.reinvest.direct_payment"),
                        Leaf("reinvestment_from_distributed_profit", is_true, "cn.reinvest.profit_is_distributed_retained_earnings"))
CAPITALISED = Leaf("capitalised", is_true)                      # decision D46: capitalisation of reserves (转增股本)
SHARE_PREMIUM = And(CAPITALISED, Leaf("capitalised_from", is_in, "cn.capitalisation.not_income_sources"))

# 财税〔2009〕59号 §5 with 109号 §1: the conditions every special reorganisation meets (decision D18)
REORG_COMMON = And(Leaf("reorg_step", is_true),
                   Leaf("reorg_control_ratio", ge, "cn.reorg.control_ratio"),
                   Leaf("reorg_acquired_ratio", ge, "cn.reorg.acquired_ratio_min"),
                   Leaf("reorg_equity_payment_share", ge, "cn.reorg.equity_payment_min"),
                   Discretion("reorg_reasonable_commercial_purpose", cites=("cn.cs.2009-59#i5",)),
                   Leaf("reorg_operations_unchanged_12m", is_true, "cn.reorg.keep_months"),
                   Leaf("reorg_shares_kept_12m", is_true, "cn.reorg.keep_months"),
                   Leaf("reorg_filed", is_true, "cn.reorg.filing_days"))


def to(residence, income):
    return Scope(CN, residence, income)


# ---- beneficial owner (国家税务总局公告2018年第9号): safe harbours are text, the adverse-factor analysis is a judgement
RESIDENT = Leaf("residence_cert", is_true, on="payee")
CROSS_BORDER = Leaf("payee_in_source_jur", is_false, on="payee")
DOMESTIC = Leaf("payee_in_source_jur", is_true, on="payee")
BO_FACTORS = And(Leaf("onpay_ratio_12m", lt, "cn.bo.onpay_ratio", on="payee"),
                 Discretion("no_adverse_bo_factors", cites=("cn.sta.2018-09#i2",)))
BO_DIVIDEND = Or(Leaf("bo_safe_harbour", is_true, "cn.bo.safe_harbour", on="payee"),
                 Leaf("bo_via_100pct_owner", is_true, "cn.bo.via_100pct_owner", on="payee"),
                 BO_FACTORS)
BO_OTHER = BO_FACTORS
QUALIFIED = lambda ratio_param: And(Leaf("direct_ratio", ge, ratio_param),
                                    Leaf("holding_months", ge, "cn.div.holding_months_min"))
CLAIM = ("cn.treaty.claim_proc", "cn.bo.onpay_window")
# a mutual agreement procedure answers an action of the other authority (2013-56 第七条) and is not re-opened after a
# withdrawal or a refused result on the same facts (第十九条); domestic remedies do not bar it (MLI 16(1))
MAP_COND = And(Leaf("authority_action", is_in, "cn.map.actions"),
               Not(Leaf("prior_map_outcome", is_in, "cn.map.no_reacceptance_after")))        # how relief is claimed; the 12-month window behind onpay_ratio_12m

HK_TREATY = ("cn-hk.div.cap_qualified@cn", "cn-hk.div.cap_other@cn", "cn-hk.int.cap@cn", "cn-hk.int.government_exempt@cn",
             "cn-hk.roy.cap@cn", "cn-hk.roy.cap_aircraft_ship_lease@cn", "cn-hk.gain.residence_only@cn", "cn-hk.gain.listed@cn",
             "cn-hk.pe.no_pe@cn", "cn-hk.gain.other@cn")
SG_TREATY = ("cn-sg.div.cap_qualified@cn", "cn-sg.div.cap_other@cn", "cn-sg.int.cap_bank@cn", "cn-sg.int.cap_other@cn",
             "cn-sg.int.government_exempt@cn", "cn-sg.roy.cap@cn", "cn-sg.roy.equipment_base@cn", "cn-sg.gain.residence_only@cn",
             "cn-sg.pe.no_pe@cn", "cn-sg.gain.other@cn")
# Art 5(3)(b) / Art 7(1): services performed in the Mainland by a resident of the other side are taxed there only through a
# permanent establishment, which arises once presence exceeds 183 days in any 12 months
NO_PE = lambda days_param: And(RESIDENT, Leaf("fixed_place_in_cn", is_false, on="payee"), Leaf("service_days_12m", le, days_param))
# Art 13: the source state keeps the right to tax a share gain only for immovable-property-rich companies (> 50%)
# or substantial participations (>= 25% within 12 months); otherwise the gain is taxable only in the residence state
GAIN_RESIDENCE_ONLY = lambda immovable, ratio: And(RESIDENT, Leaf("immovable_ratio", le, immovable),
                                                    Leaf("max_ratio_12m", lt, ratio))

# decision D30: the laws the library starts from — a flow dated before one is outside the library for that levy (the VAT
# rules of 营改增 36号 and the stamp-duty regulations they replaced are not kept: current law only)
VAT_LAW = ("增值税法", "cn.law.vat#38")
LAT_REG = ("土地增值税暂行条例", "cn.reg.lat#15")                  # decision D48
DEED_LAW = ("契税法", "cn.law.deed#16")
UCMT_LAW = ("城市维护建设税法", "cn.law.ucmt#11")
STAMP_LAW = ("印花税法", "cn.law.stamp.flk#20")
TARIFF_LAW = ("关税法", "cn.law.tariff#72")                     # decision D43
# decision D23: the VAT Law's cross-border charge — withheld by the buyer (第十五条) on the sales amount, a VAT-inclusive price
# divided by 1 + rate (实施条例 第十六条); the buyer credits it (实施条例 第十二条) when a general taxpayer holding the contract,
# the payment proof and the seller's statement or invoice (公告2026年第13号), or the special invoice of a domestic seller
LAW_VAT = ("cn.vat.law.withholding_agent", "cn.vat.law.withheld_on_sales", "cn.vat.law.inclusive_price", "cn.vat.law.taxable_in_cn")
INPUT_LAW = And(Leaf("vat_general_taxpayer", is_true, "cn.vat.law.input_credit", on="payer"),
                Or(DOMESTIC, Leaf("input_vat_documents_kept", is_true, "cn.vat.law.input_documents")))
# decision D25: 统借统还 — a group's core company on-lending what it borrowed from banks at no more than their rate
UNIFIED = Leaf("unified_borrowing_relending", is_false, "cn.vat.law.unified_borrowing_exempt")
# decision D22: technology transfers — the income-tax reduction (财税〔2010〕111号: the kinds listed, the contract registered, no
# restricted export, not between companies one of which holds the other wholly; sisters wholly held by one holder are
# not named there — judged) and the VAT exemption (公告2026年第10号: patents and know-how, the contract recognised)
TECH = And(Leaf("ip_kind", is_in, "cn.tech.kinds"), Leaf("tech_transfer_registered", is_true, "cn.tech.registration"),
           Leaf("technology_export_restricted", is_false, "cn.tech.export_restricted_excluded"),
           Leaf("ip_parties_100pct_held", is_false, "cn.tech.related_100_excluded"),
           Or(Leaf("ip_parties_100pct_sisters", is_false),
              Discretion("tech_transfer_between_sisters_allowed", cites=("cn.cs.2010-111#i4",), on="flow")))
VAT_TECH = And(Leaf("ip_kind", is_in, "cn.vat.tech_kinds"), Leaf("vat_tech_recognized", is_true, "cn.vat.tech_recognition"))
# 印花税法 第一条: a party in the Mainland writes the instrument; parties both abroad pay if it is used in the Mainland
STAMP_IP = Or(Leaf("cn_party", is_true, "cn.stamp.taxpayer_each_party"),
              Leaf("instrument_used_in_cn", is_true, "cn.stamp.abroad_used_in_cn"))

SPEC = [
    # ---- domestic charge: the law names 20%, the implementing regulations reduce it to 10% (general rule + exception)
    RuleObj("cn.wht.statutory", dom(PASSIVE), Effect.CHARGE, "cn.eit.rate_nonresident_statutory", cond=Leaf("payee_in_source_jur", is_false, on="payee"), uses=("cn.wht.at_source", "cn.wht.base_gross")),
    RuleObj("cn.wht.reduced", dom(PASSIVE), Effect.CHARGE, "cn.wht.rate", cond=Leaf("payee_in_source_jur", is_false, on="payee"), overrides=frozenset({"cn.wht.statutory"})),

    # ---- services a non-resident performs in the Mainland: an establishment (实施条例 第五条), 25% on the profit, which the
    #      authority fixes by a deemed rate when the accounts do not show it (国税发〔2010〕19号 第五条); the treaties lift the
    #      charge below the permanent-establishment threshold
    RuleObj("cn.service.charge", dom(SERVICE_FEE), Effect.CHARGE, "cn.eit.rate",
            cond=And(Leaf("payee_in_source_jur", is_false, on="payee"),
                     Leaf("service_performed_in_source", is_true, "cn.service.source_where_performed")),
            uses=("cn.service.establishment", "cn.service.deemed_basis")),
    # 国税函〔2009〕507号 第四条、第六条: a service that uses know-how without licensing it is not a royalty; whether a fee
    # is really for know-how is the authority's judgement — if so, 10% on the gross as a royalty instead of the service charge
    RuleObj("cn.wht.service_as_royalty", dom(SERVICE_FEE), Effect.CHARGE, "cn.wht.rate",
            cond=And(CROSS_BORDER, Discretion("service_fee_is_royalty_for_know_how", cites=("cn.gsh.2009-507#i4", "cn.gsh.2009-507#i6"))),
            overrides=frozenset({"cn.service.charge", "cn.service.deemed_profit", "cn-hk.pe.no_pe@cn", "cn-sg.pe.no_pe@cn"}),
            uses=("cn.treaty.service_not_royalty", "cn.treaty.professional_services_business_profits"), ambiguous=True),
    RuleObj("cn.service.deemed_profit", dom(SERVICE_FEE), Effect.BASE, None,
            uses=("cn.service.deemed_profit_min", "cn.service.deemed_profit_max", "cn.service.deemed_profit_design_min",
                  "cn.service.deemed_profit_design_max", "cn.service.deemed_profit_other_min")),
    RuleObj("cn.deduct.service", dom(SERVICE_FEE), Effect.DEDUCTION, "cn.eit.rate",
            cond=Discretion("reasonable_service_fee", cites=("cn.law.eit#8",), on="payer"),
            uses=("cn.deduct.general", "cn.eit.rate_entity")),
    RuleObj("cn-hk.pe.no_pe@cn", to(HK, SERVICE_FEE), Effect.EXEMPT, None, cond=NO_PE("cn-hk.pe.service_days"),
            uses=("cn-hk.pe.business_profits_residence_only",)),
    RuleObj("cn-sg.pe.no_pe@cn", to(SG, SERVICE_FEE), Effect.EXEMPT, None, cond=NO_PE("cn-sg.pe.service_days"),
            uses=("cn-sg.pe.business_profits_residence_only",)),

    # ---- transfer pricing (范围.md 4): the local file when related-party dealings exceed the threshold, due 30 June of the
    #      next year; interest on a special adjustment at the benchmark plus five points (benchmark only with documentation)
    RuleObj("cn.tp.local_file", dom(RELATED), Effect.DEADLINE, "cn.tp.local_file_due",
            cond=And(Leaf("cn_related", is_true), Leaf("related_party_volume", gt, "cn.tp.local_file_other_threshold", on="payer")),
            uses=("cn.tp.related_share_min",)),
    RuleObj("cn.tp.adjustment_interest", dom(RELATED), Effect.PENALTY, "cn.tp.interest_spread",
            cond=Leaf("cn_related", is_true), uses=("cn.tp.interest_from", "cn.tp.interest_base_only_with_docs", "cn.tp.related_share_min")),
    # ---- decision D41: a related payer's interest, royalty or fee below its arm's-length amount — the Mainland payee is taxed
    #      on that amount (EIT art 41; 公告2017年第6号 第二十五条: a profit below the median, to the median), the special
    #      adjustment's interest on the payee's side too; a Mainland payer's deduction follows a Hong Kong or Singapore
    #      adjustment of the payee through the treaties' corresponding adjustment (Art 9(2)) — the authority's judgement
    RuleObj("cn.tp.income_uplift", Scope(ALL, CN, RELATED, side="residence"), Effect.BASE, None, cond=CROSS_BORDER,
            uses=("cn.tp.income_arms_length", "cn.tp.adjust_to_median", "cn.tp.related_share_min", "cn.tp.related_via_intermediate")),
    RuleObj("cn.tp.adjustment_interest.income", Scope(ALL, CN, RELATED, side="residence"), Effect.PENALTY, "cn.tp.interest_spread",
            cond=And(CROSS_BORDER, Leaf("cn_related", is_true)),
            uses=("cn.tp.interest_from", "cn.tp.interest_base_only_with_docs", "cn.tp.related_share_min")),
    RuleObj("cn.tp.corresponding", dom(RELATED), Effect.DEDUCT_BASE, None, cond=CROSS_BORDER,
            uses=("cn-hk.tp.corresponding", "cn-sg.tp.corresponding")),

    # ---- decision D23: the VAT Law from 2026-01-01 (decision D30: before it, outside the library): a foreign
    #      seller's services and IP sold to a Mainland buyer are consumed in the Mainland (实施条例 第四条) — services
    #      consumed on site abroad excepted, IP without exception; 6%, a lease of tangible movables 13% (第十条)
    RuleObj("cn.vat.law.service", dom(SERVICE_FEE), Effect.VAT, "cn.vat.law.rate_services", before=VAT_LAW, bearer="payee",
            cond=And(CROSS_BORDER, Leaf("service_consumed_on_site_abroad", is_false, "cn.vat.law.consumed_in_cn")), uses=LAW_VAT),
    RuleObj("cn.vat.law.royalty", dom(ROYALTY), Effect.VAT, "cn.vat.law.rate_services", before=VAT_LAW, bearer="payee",
            cond=And(CROSS_BORDER, Leaf("is_equipment_lease", is_false, "cn.vat.law.consumed_in_cn"), Leaf("is_aircraft_or_ship_lease", is_false)),
            uses=LAW_VAT),
    RuleObj("cn.vat.law.lease", dom(ROYALTY), Effect.VAT, "cn.vat.law.rate_tangible_lease", before=VAT_LAW, bearer="payee",
            cond=And(CROSS_BORDER, Or(Leaf("is_equipment_lease", is_true), Leaf("is_aircraft_or_ship_lease", is_true))), uses=LAW_VAT),
    # decision D48: a sale of land use rights or a building in the Mainland (增值税法 第四条第二项): 9% (第十条第二项), or for
    # one acquired before 2016-05-01 the 5% simplified method on the price less the purchase price (公告2026年第10号
    # 三（二）4-5、四（八）), a small-scale taxpayer 3% on the same difference (第十一条; 四（八）)
    RuleObj("cn.vat.law.property", dom(PROPERTY), Effect.VAT, "cn.vat.law.rate_property", before=VAT_LAW, bearer="payee",
            uses=("cn.vat.law.taxable_in_cn", "cn.vat.property_simplified_rate", "cn.vat.property_old_cutoff",
                  "cn.vat.property_simplified_until", "cn.vat.property_purchase_deducted", "cn.vat.law.simplified_rate")),
    # decision D49: the lease of land or a building in the Mainland, 9% (第十条第二项 不动产租赁服务); one acquired before 2016-05-01
    # at the 5% simplified method (公告2026年第10号 三（二）3), a small-scale taxpayer 3% (第十一条)
    RuleObj("cn.vat.law.rent", dom(RENT), Effect.VAT, "cn.vat.rent_rate", before=VAT_LAW, bearer="payee",
            uses=("cn.vat.law.taxable_in_cn", "cn.vat.property_simplified_rate", "cn.vat.property_old_cutoff",
                  "cn.vat.property_simplified_until", "cn.vat.law.simplified_rate")),
    RuleObj("cn.vat.law.input_credit", dom((SERVICE_FEE, ROYALTY, IP_TRANSFER, PROPERTY, RENT)), Effect.VAT, "cn.vat.law.rate_services", before=VAT_LAW, bearer="payer",
            cond=INPUT_LAW, uses=("cn.vat.law.input_credit_invoice",)),
    # ---- decision D25: interest is the price of a loan service (实施条例 第二条): a foreign lender's interest from a Mainland
    #      borrower is consumed in the Mainland and withheld at 6%; a Mainland lender's is taxed whoever borrows (销售方为
    #      境内单位); the borrower credits none of it (实施条例 第二十一条) — no input credit rule covers interest, so the VAT
    #      is a cost of the group. 统借统还 interest is exempt (公告2026年第10号)
    RuleObj("cn.vat.law.interest", dom(INTEREST), Effect.VAT, "cn.vat.law.rate_services", before=VAT_LAW, bearer="payee",
            cond=And(CROSS_BORDER, UNIFIED), uses=LAW_VAT + ("cn.vat.law.loan_services", "cn.vat.law.loan_input_not_creditable")),
    RuleObj("cn.vat.law.interest_received", Scope(ALL, CN, INTEREST, side="residence"), Effect.VAT, "cn.vat.law.rate_services", before=VAT_LAW,
            bearer="payee", cond=UNIFIED,
            uses=("cn.vat.law.taxable_in_cn", "cn.vat.law.inclusive_price", "cn.vat.law.loan_services",
                  "cn.vat.law.loan_input_not_creditable")),
    # ---- decision D26: a non-resident's Article 3(3) income is taxed on the income net of the VAT (公告2013年第9号): with a
    #      VAT-inclusive price the withholding base, and the treaty cap's base, are the price ÷ (1 + rate); a gain is the
    #      net price less the basis. Services done here are establishment income, outside the announcement
    RuleObj("cn.wht.vat_exclusive", dom((INTEREST, ROYALTY, IP_TRANSFER, PROPERTY, RENT)), Effect.BASE, "cn.wht.base_excludes_vat", cond=CROSS_BORDER),
    # ---- decision D49: property tax (房产税) on a building let, 12% of the rent net of the VAT (房产税暂行条例 第三条、第四条; 财税〔2016〕43号
    #      第二条), the owner's (第二条), in cities, county towns, towns and industrial and mining areas (第一条); the lease
    #      contract's stamp duty, 0.1% of the rent, each party (印花税法 税目税率表)
    RuleObj("cn.property_tax.rent", dom(RENT), Effect.PROPERTY_TAX, "cn.property_tax.rent_rate", bearer="payee",
            cond=Leaf("property_tax_area", is_true, "cn.property_tax.area"),
            uses=("cn.property_tax.rent_base", "cn.property_tax.owner", "cn.property_tax.rent_excludes_vat")),
    RuleObj("cn.stamp.lease.lessor", dom(RENT), Effect.STAMP, "cn.stamp.lease_rate", before=STAMP_LAW, bearer="payee",
            uses=("cn.stamp.taxpayer_each_party",)),
    RuleObj("cn.stamp.lease.lessee", dom(RENT), Effect.STAMP, "cn.stamp.lease_rate", before=STAMP_LAW, bearer="payer",
            uses=("cn.stamp.taxpayer_each_party",)),
    # a Mainland lessor's rent is income net of its costs (the profit in it, profit_margin); the tenant deducts it (实施条例
    # 第四十七条: operating-lease rent spread over the lease)
    RuleObj("cn.rent.base", Scope(ALL, CN, RENT, side="residence"), Effect.BASE, None, uses=("cn.rent.lessor_profit",)),
    RuleObj("cn.deduct.rent", dom(RENT), Effect.DEDUCTION, "cn.eit.rate", uses=("cn.deduct.operating_lease", "cn.eit.rate_entity")),
    # ---- decision D48: on every VAT actually paid in the Mainland (城市维护建设税法 第二条; 公告2021年第28号 第一条) — not on
    #      import VAT or the VAT of a foreign seller of services or intangibles (第三条) — each item's own bearer and sign:
    #      7% / 5% / 1% by where the taxpayer is (第四条), and the local education surcharge of 2% on the same base (财综
    #      〔2010〕98号 第二条; 公告2021年第28号 第二条). The education surcharge (国发〔1986〕50号) is not in the library
    RuleObj("cn.surcharge.ucmt", Scope(ALL, None, ALL, side=CN), Effect.SURCHARGE, "cn.ucmt.rate_urban", before=UCMT_LAW,
            uses=("cn.ucmt.base_vat_paid", "cn.ucmt.no_foreign_services", "cn.ucmt.rate_county", "cn.ucmt.rate_other",
                  "cn.ucmt.location_of_taxpayer")),
    RuleObj("cn.surcharge.local_edu", Scope(ALL, None, ALL, side=CN), Effect.SURCHARGE, "cn.local_edu.rate", before=UCMT_LAW,
            uses=("cn.local_edu.base_as_ucmt",)),
    # ---- decision D48: LAT on the value a transfer of land or buildings adds (条例 第二条至第七条; 细则 第七条、第十条),
    #      the transferor's; deed tax on the price, the transferee's (契税法 第一条、第三条、第四条), each net of the VAT (财税
    #      〔2016〕43号); stamp duty on the transfer instrument by each party (印花税法 税目税率表)
    RuleObj("cn.lat.charge", dom(PROPERTY), Effect.LAT, "cn.lat.rate_1", before=LAT_REG, bearer="payee",
            uses=("cn.lat.rate_2", "cn.lat.rate_3", "cn.lat.rate_4", "cn.lat.band_1", "cn.lat.band_2", "cn.lat.band_3",
                  "cn.lat.quick_2", "cn.lat.quick_3", "cn.lat.quick_4", "cn.lat.revenue_excludes_vat", "cn.lat.old_building_appraisal",
                  "cn.lat.invoice_uplift", "cn.lat.invoice_year", "cn.lat.deed_deductible", "cn.lat.taxes_deductible",
                  "cn.lat.stamp_and_local_edu_deductible")),
    RuleObj("cn.deed.charge", dom(PROPERTY), Effect.DEED, "cn.deed.rate_min", before=DEED_LAW, bearer="payer",
            uses=("cn.deed.rate_max", "cn.deed.transferee", "cn.deed.base_price", "cn.deed.base_excludes_vat")),
    RuleObj("cn.stamp.property.seller", dom(PROPERTY), Effect.STAMP, "cn.stamp.property_rate", before=STAMP_LAW, bearer="payee",
            uses=("cn.stamp.taxpayer_each_party",)),
    RuleObj("cn.stamp.property.buyer", dom(PROPERTY), Effect.STAMP, "cn.stamp.property_rate", before=STAMP_LAW, bearer="payer",
            uses=("cn.stamp.taxpayer_each_party",)),
    # ---- decision D29: a Mainland company's revenue leaves out the VAT on its own sale (增值税会计处理规定: the output VAT is a
    #      liability, not income; the annual return starts from that revenue, A101010): with a VAT-inclusive price its
    #      interest income, and the proceeds of its IP sale, are net of the VAT — before the technology-transfer relief
    RuleObj("cn.resident.vat_exclusive", Scope(ALL, CN, (INTEREST, IP_TRANSFER), side="residence"), Effect.BASE,
            "cn.eit.revenue_excludes_output_vat"),
    # ---- decision D22: the IP transfer step's VAT — a foreign seller's IP sold to a Mainland buyer, withheld; a Mainland
    #      seller's, charged whoever buys (销售方为境内单位, 第四条); a technology transfer recognised is exempt — whether a
    #      foreign seller, which has no 所在地 for the recognition, can have it is the authority's judgement. The zero rate
    #      for technology used wholly abroad (实施条例 第九条) does not arise: OP goes on using the IP in the Mainland.
    RuleObj("cn.vat.law.ip", dom(IP_TRANSFER), Effect.VAT, "cn.vat.law.rate_services", before=VAT_LAW, bearer="payee",
            cond=And(CROSS_BORDER, Not(And(VAT_TECH, Discretion("tech_recognition_open_to_foreign_seller",
                                                                cites=("cn.cs.2026-10#i2",), on="flow")))),
            uses=LAW_VAT + ("cn.vat.tech_transfer_exempt",)),
    RuleObj("cn.vat.law.ip_sale", Scope(ALL, CN, IP_TRANSFER, side="residence"), Effect.VAT, "cn.vat.law.rate_services", before=VAT_LAW, bearer="payee",
            cond=Not(VAT_TECH), uses=("cn.vat.law.taxable_in_cn", "cn.vat.law.inclusive_price", "cn.vat.tech_transfer_exempt")),
    # ---- decision D22: the IP transfer step's income tax. A Mainland seller: the gain (proceeds less net value, 实施条例
    #      第十六条、第七十四条) at its rate, a technology transfer's first 5 million yuan exempt and the rest halved
    #      (第九十条). A non-resident seller: 10% on the gain (第十九条) if the gain arises in the Mainland — 第七条 names no
    #      source for intangibles and leaves "other income" to the authorities, who have set none: their judgement; the
    #      treaties leave gains from other property to the seller's residence (CN-HK Art 13(7), CN-SG Art 13(6)).
    #      The Mainland buyer amortises the price over at least 10 years or a shorter legal or agreed life (第六十七条).
    RuleObj("cn.resident.ip.charge", Scope(ALL, CN, IP_TRANSFER, side="residence"), Effect.CHARGE, "cn.eit.rate",
            uses=("cn.eit.resident_worldwide", "cn.eit.rate_entity", "cn.ip.transfer_income", "cn.ip.net_value")),
    RuleObj("cn.resident.ip.tech", Scope(ALL, CN, IP_TRANSFER, side="residence"), Effect.BASE, None, cond=TECH,
            uses=("cn.tech.exempt_max", "cn.tech.excess_rate", "cn.tech.ownership_or_licence")),
    RuleObj("cn.ip.wht", dom(IP_TRANSFER), Effect.CHARGE, "cn.wht.rate",
            cond=And(CROSS_BORDER, Discretion("ip_transfer_gain_sourced_in_cn", cites=("cn.reg.eit#7",), on="flow")),
            uses=("cn.eit.rate_nonresident_statutory", "cn.ip.nonresident_gain_base", "cn.ip.source_other_income", "cn.ip.net_value")),
    RuleObj("cn-hk.gain.other@cn", to(HK, IP_TRANSFER), Effect.EXEMPT, None,
            cond=And(Leaf("residence_cert", is_true, "cn-hk.gain.other_residence_only", on="payee"),
                     Leaf("fixed_place_in_cn", is_false, on="payee"))),
    RuleObj("cn-sg.gain.other@cn", to(SG, IP_TRANSFER), Effect.EXEMPT, None,
            cond=And(Leaf("residence_cert", is_true, "cn-sg.gain.other_residence_only", on="payee"),
                     Leaf("fixed_place_in_cn", is_false, on="payee"))),
    RuleObj("cn.ip.amortization", dom(IP_TRANSFER), Effect.DEDUCTION, "cn.eit.rate", uses=("cn.deduct.general", "cn.eit.rate_entity")),
    RuleObj("cn.ip.amortization.horizon", dom(IP_TRANSFER), Effect.DEDUCT_BASE, None,
            uses=("cn.ip.amortization_years_min", "cn.ip.amortization_agreed_life")),
    RuleObj("cn.stamp.ip.seller", Scope(ALL, None, IP_TRANSFER, side=CN), Effect.STAMP, "cn.stamp.ip_rate", before=STAMP_LAW, bearer="payee", cond=STAMP_IP,
            uses=("cn.stamp.unstated_amount_market_price", "cn.stamp.restructuring_exemption_scope")),
    RuleObj("cn.stamp.ip.buyer", Scope(ALL, None, IP_TRANSFER, side=CN), Effect.STAMP, "cn.stamp.ip_rate", before=STAMP_LAW, bearer="payer", cond=STAMP_IP,
            uses=("cn.stamp.unstated_amount_market_price", "cn.stamp.restructuring_exemption_scope")),
    # ---- decision D28: the IP step at book value between Mainland companies one wholly holding the other or both wholly held
    #      by the same Mainland company (the template allows the mode only then): with a reasonable business purpose (a
    #      judgement), no change of the IP's business for 12 months and the filing at the annual return (the plan's
    #      actions), neither side recognises a gain and the buyer amortises the seller's tax basis (109号 第三条; 公告2015年
    #      第40号 第三条、第五条). Otherwise a deemed sale at fair value (第八条) — what the sale at market value computes.
    #      VAT: a deemed sale at market value (增值税法 第五条、第十九条); stamp duty on the market value (印花税法 第六条)
    RuleObj("cn.reorg.asset_transfer", Scope(ALL, CN, IP_TRANSFER, side="residence"), Effect.EXEMPT, None,
            cond=And(Leaf("ip_transfer_mode", is_in, "cn.reorg.transfer_mode"),
                     Discretion("asset_transfer_reasonable_purpose", cites=("cn.cs.2014-109#i3",), on="flow"),
                     Leaf("reorg_operations_unchanged_12m", is_true, "cn.reorg.transfer_keep_months"),
                     Leaf("reorg_filed", is_true, "cn.reorg.transfer_filing")),
            uses=("cn.reorg.transfer_no_gain", "cn.reorg.transfer_fails_deemed_sale")),
    RuleObj("cn.reorg.asset_transfer.basis", dom(IP_TRANSFER), Effect.DEDUCT_BASE, "cn.reorg.transfer_basis",
            uses=("cn.vat.law.deemed_sale_market_value",)),

    # ---- controlled foreign company (范围.md 5): the engine's deemed distribution is charged at 25% with the indirect credit
    #      unless the foreign company is not low-taxed, sits on the white list, is small, or earns mainly active income /
    #      retains for a business reason (judgements)
    RuleObj("cn.cfc.charge", Scope(ALL, CN, CFC_INCLUSION, side="residence"), Effect.CHARGE, "cn.eit.rate",
            cond=And(Or(Leaf("cfc_share_control", is_true, "cn.cfc.control_joint_min"),
                        Discretion("substantive_control_over_foreign_company", cites=("cn.reg.eit#117",))),
                     Leaf("cfc_tax_burden_ratio", lt, "cn.cfc.low_tax_ratio"), Leaf("cfc_whitelisted", is_false, "cn.cfc.exempt_whitelist"),
                     Leaf("cfc_profit_total", ge, "cn.cfc.exempt_profit_max"),
                     Discretion("profits_not_mainly_active", cites=("cn.gsf.2009-02#84",)),
                     Discretion("retention_without_reasonable_business_need", cites=("cn.law.eit#45",))),
            uses=("cn.cfc.definition", "cn.cfc.control_single_min", "cn.cfc.control_joint_min", "cn.cfc.chain_over_50_counts_100",
                  "cn.cfc.whitelist", "cn.cfc.exempt_active", "cn.eit.rate_entity")),

    # ---- stamp duty (范围.md 2): the equity-transfer instrument is stamped at 0.05% of the price by each party writing it
    #      — a writing that transfers shares: shares a liquidation or capital reduction cancels pass by none (decision D19)
    RuleObj("cn.stamp.seller", dom(SHARE_TRANSFER), Effect.STAMP, "cn.stamp.equity_rate", before=STAMP_LAW, bearer="payee",
            cond=Leaf("shares_cancelled", is_false, "cn.stamp.equity_rate"), uses=("cn.stamp.taxpayer_each_party",)),
    RuleObj("cn.stamp.buyer", dom(SHARE_TRANSFER), Effect.STAMP, "cn.stamp.equity_rate", before=STAMP_LAW, bearer="payer",
            cond=Leaf("shares_cancelled", is_false, "cn.stamp.equity_rate"), uses=("cn.stamp.taxpayer_each_party",)),

    # ---- a liquidation or capital-reduction distribution is decomposed before any rule applies (engine.normalise):
    #      the holder's share of accumulated profits and reserves is a dividend, the rest a disposal of the holding
    RuleObj("cn.liquidation.split", Scope(ALL, None, LIQUIDATION), Effect.SPLIT, None, uses=("cn.liquidation.split",)),
    RuleObj("cn.capital_reduction.split", Scope(ALL, None, CAPITAL_REDUCTION), Effect.SPLIT, None, uses=("cn.capital_reduction.split",)),

    # ---- domestic flows (EIT art 3(1), art 4, art 26(2), 实施条例 第八十三条): a resident's domestic interest, royalty or fee
    #      is charged at its own rate; a dividend between residents is exempt unless on listed shares held under 12 months
    RuleObj("cn.domestic.charge", Scope(CN, CN, (INTEREST, ROYALTY, SERVICE_FEE, GOODS, RENT), side="residence"), Effect.CHARGE, "cn.eit.rate",
            cond=DOMESTIC, uses=("cn.eit.resident_worldwide", "cn.eit.rate_entity")),
    RuleObj("cn.domestic.dividend_exempt", Scope(CN, CN, DIVIDEND, side="residence"), Effect.NOCHARGE, None, cond=DOMESTIC,
            uses=("cn.domestic.dividend_exempt",)),
    RuleObj("cn.domestic.dividend_listed", Scope(CN, CN, DIVIDEND, side="residence"), Effect.CHARGE, "cn.eit.rate",
            cond=And(DOMESTIC, Leaf("listed_market_trade", is_true), Leaf("holding_months", lt, "cn.domestic.dividend_listed_months")),
            uses=("cn.eit.rate_entity",)),

    # ---- the Mainland as residence: worldwide income at 25% (art 3(1)); foreign tax credited within the Mainland tax on
    #      the same income (art 23), per country, five-year carry-forward; the tax a >= 20% subsidiary bore on the profits
    #      behind a dividend is credited too (art 24, five tiers)
    RuleObj("cn.resident.charge", Scope(ALL, CN, (DIVIDEND, INTEREST, ROYALTY, SERVICE_FEE, GOODS, BRANCH_PROFIT, RENT), side="residence"),
            Effect.CHARGE, "cn.eit.rate",
            cond=CROSS_BORDER, uses=("cn.eit.resident_worldwide", "cn.eit.rate_entity",
                                     # decision D47: a foreign branch's profit in the year its own year ends, remitted or not; a
                                     # loss does not reach the Mainland profit (engine.branch_flows places none)
                                     "cn.branch.accrual", "cn.branch.tax_year", "cn.branch.loss_not_offset")),
    # a domestic share sale is charged too: the buyer gets a cost base, not a deduction, so nothing offsets it
    RuleObj("cn.resident.gain.charge", Scope(ALL, CN, (SHARE_TRANSFER, PROPERTY), side="residence"), Effect.CHARGE, "cn.eit.rate",
            uses=("cn.eit.resident_worldwide", "cn.eit.rate_entity")),
    # decision D48: a resident's gain on land or a building is the price net of the VAT less its basis and the taxes on the sale
    # (实施条例 第三十一条: 税金 other than the income tax and the creditable VAT)
    RuleObj("cn.property.resident.base", Scope(ALL, CN, PROPERTY, side="residence"), Effect.BASE, None,
            uses=("cn.property.taxes_deductible", "cn.property.source")),   # the output VAT taken out inside (not NET_OF_VAT)
    RuleObj("cn.resident.gain.base", Scope(ALL, CN, SHARE_TRANSFER, side="residence"), Effect.BASE, None,
            uses=("cn.eit.asset_net_value_deductible", "cn.tp.related_transfer_arms_length", "cn.tp.related_share_min")),  # decision D38, D40
    RuleObj("cn.ftc.direct", Scope(ALL, CN, (INTEREST, ROYALTY, SHARE_TRANSFER, SERVICE_FEE, GOODS, BRANCH_PROFIT, PROPERTY, RENT), side="residence"),
            Effect.CREDIT,
            None,
            uses=("cn.ftc.credit", "cn.ftc.limit_per_country", "cn.ftc.carryforward_years", "cn.ftc.method_lock_years",
                  "cn.ftc.not_due_under_treaty_not_creditable")),
    # per-country limit with a five-year carry-forward, across the entity's flows and years (engine.carryforward_credit)
    RuleObj("cn.ftc.carryforward", Scope(ALL, CN, ALL, mount=Mount.ENTITY, side="residence"), Effect.CREDIT, None,
            uses=("cn.ftc.limit_per_country", "cn.ftc.carryforward_years")),
    # decision D51: losses, by year and by country, over the company's items (tax_graph.losses — the stage reads the company's
    # facts and every item of the year; nothing is read per flow)
    RuleObj("cn.loss.carryforward", LOSS_CN, Effect.DEDUCTION, "cn.loss.carryforward_years",
            uses=("cn.loss.definition", "cn.loss.order", "cn.loss.carryforward_years_extended", "cn.loss.carryforward_years_2020",
                  "cn.loss.covid_loss_year")),
    RuleObj("cn.loss.foreign_offset", LOSS_CN, Effect.DEDUCTION, None,
            uses=("cn.loss.foreign_offset_elective", "cn.loss.foreign_offset_order", "cn.loss.foreign_offset_limit")),
    RuleObj("cn.loss.foreign_branch", LOSS_CN, Effect.DEDUCTION, None,
            uses=("cn.loss.foreign_not_domestic", "cn.loss.foreign_branch_country", "cn.loss.branch_nonactual_unlimited")),
    # foreign-source only (decision D08): a dividend between residents is the domestic rules' business
    RuleObj("cn.ftc.dividend", Scope(ALL, CN, (DIVIDEND, CFC_INCLUSION), side="residence"), Effect.CREDIT, None,
            cond=And(CROSS_BORDER, Leaf("direct_ratio", lt, "cn.ftc.indirect_ratio_min")),
            uses=("cn.ftc.credit", "cn.ftc.limit_per_country", "cn.ftc.income_recognition_dividend")),
    RuleObj("cn.ftc.dividend_indirect", Scope(ALL, CN, (DIVIDEND, CFC_INCLUSION), side="residence"), Effect.CREDIT, None,
            cond=And(CROSS_BORDER, Leaf("direct_ratio", ge, "cn.ftc.indirect_ratio_min")),
            uses=("cn.ftc.credit", "cn.ftc.indirect", "cn.ftc.indirect_tiers", "cn.ftc.indirect_formula", "cn.ftc.gross_up",
                  "cn.ftc.limit_per_country", "cn.ftc.income_recognition_dividend", "cn.cfc.credit")),

    # ---- reinvestment deferral (财税〔2018〕102号): withholding on a dividend reinvested in the Mainland is deferred
    RuleObj("cn.reinvest.deferral", dom(DIVIDEND), Effect.DEFER, "cn.reinvest.deferral", cond=REINVEST_DEFERRAL,
            uses=("cn.reinvest.excludes_listed_shares", "cn.reinvest.recapture_days", "cn.reinvest.special_reorg_continues",
                  "cn.reinvest.fifo_disposal", "cn.reinvest.treaty_at_payment_time")),
    # decision D46 (第六条): the investment taken back among the modelled flows — the deferred tax is paid within 7 days of the
    # proceeds; its clock replaces the withholding one (procedure_cn.surcharge)
    RuleObj("cn.reinvest.recapture", dom(DIVIDEND), Effect.DENY, "cn.reinvest.recapture_days",
            cond=Leaf("reinvestment_withdrawn", is_true, "cn.reinvest.withdrawal_forms"),
            overrides=frozenset({"cn.reinvest.deferral"}), uses=("cn.reinvest.fifo_disposal",)),
    RuleObj("cn.reinvest.recapture.due", dom(DIVIDEND), Effect.DEADLINE, "cn.reinvest.recapture_days",
            cond=And(REINVEST_DEFERRAL, Leaf("reinvestment_withdrawn", is_true, "cn.reinvest.withdrawal_forms")),
            uses=("cn.time.holiday_roll", "cn.time.long_holiday_days")),
    # 2025–2028 reinvestment credit (财政部 税务总局 商务部公告2025年第2号): 10% of the reinvested amount (the treaty dividend
    # rate if lower) offsets later Mainland tax on income from the same payer; entity-level because it spans flows
    RuleObj("cn.reinvest.credit", Scope(CN, None, DIVIDEND, mount=Mount.ENTITY), Effect.CREDIT, "cn.reinvest.credit_rate",
            cond=And(Leaf("reinvested_in_cn", is_true),
                     Leaf("reinvestment_form", is_in, "cn.reinvest.forms"),
                     Leaf("direct_payment", is_true, "cn.reinvest.direct_payment"),
                     Leaf("investee_encouraged_industry", is_true, "cn.reinvest.credit_encouraged_industry"),
                     Leaf("planned_holding_months", ge, "cn.reinvest.credit_min_holding_months")),
            uses=("cn.reinvest.credit_rate_treaty_lower", "cn.reinvest.credit_against", "cn.reinvest.credit_recapture_days",
                  "cn.reinvest.credit_early_withdrawal_reduces", "cn.reinvest.credit_fx", "cn.reinvest.credit_holding_stop")),
    RuleObj("cn.gaar", dom(ALL), Effect.DENY, "cn.gaar",
            cond=Discretion("reasonable_commercial_purpose_absent", cites=("cn.law.eit#47", "cn.reg.eit#120")),
            overrides=frozenset({"cn.reinvest.deferral", "cn.reinvest.credit", "cn.reinvest.recapture.due"})),
    # ---- decision D47: a foreign company's establishment in the Mainland (机构、场所) is taxed on its own profit at 25% (EIT art
    #      3(2), art 4); nothing is withheld (art 37 reaches art 3(3) income only) and its passing to the head office is no income
    RuleObj("cn.branch.charge", dom(BRANCH_PROFIT), Effect.CHARGE, "cn.eit.rate", cond=CROSS_BORDER,
            uses=("cn.branch.own_computation", "cn.eit.rate_entity")),
    # ---- decision D46: capitalisation of reserves (国税函〔2010〕79号 第四条). Retained earnings capitalised are a dividend on the
    #      decision (the dividend rules apply as they stand); share premium capitalised is no dividend for the investor,
    #      wherever it sits. The investee's books stamp on the increase in paid-in capital and capital reserve (印花税法
    #      第五条（三）、第十一条; 财税公告2024年第14号 第一条（四）): retained earnings moved into capital raise it, share
    #      premium moved into share capital leaves the total unchanged
    RuleObj("cn.capitalisation.share_premium", dom(DIVIDEND), Effect.EXEMPT, None, cond=SHARE_PREMIUM,
            uses=("cn.capitalisation.share_premium_not_income", "cn.capitalisation.share_premium_no_basis",
                  "cn.capitalisation.dividend_on_decision", "cn.capitalisation.basis_paid_in")),
    RuleObj("cn.capitalisation.share_premium.resident", Scope(ALL, CN, DIVIDEND, side="residence"), Effect.EXEMPT, None, cond=SHARE_PREMIUM,
            uses=("cn.capitalisation.share_premium_not_income", "cn.capitalisation.share_premium_no_basis")),
    RuleObj("cn.stamp.books", dom(DIVIDEND), Effect.STAMP, "cn.stamp.books_rate", before=STAMP_LAW, bearer="payer",
            cond=And(CAPITALISED, Leaf("capitalised_from", is_in, "cn.stamp.books_increase_sources")),
            uses=("cn.stamp.books_base", "cn.stamp.books_increase_only")),

    # ---- Arrangement with Hong Kong
    RuleObj("cn-hk.div.cap_qualified@cn", to(HK, DIVIDEND), Effect.RATE_CAP, "cn-hk.div.cap_qualified",
            cond=And(RESIDENT, QUALIFIED("cn-hk.div.ratio_min"), BO_DIVIDEND), uses=CLAIM),
    RuleObj("cn-hk.div.cap_other@cn", to(HK, DIVIDEND), Effect.RATE_CAP, "cn-hk.div.cap_other",
            cond=And(RESIDENT, BO_DIVIDEND), uses=CLAIM),
    RuleObj("cn-hk.int.cap@cn", to(HK, INTEREST), Effect.RATE_CAP, "cn-hk.int.cap", cond=And(RESIDENT, BO_OTHER), uses=CLAIM),
    RuleObj("cn-hk.int.government_exempt@cn", to(HK, INTEREST), Effect.EXEMPT, "cn-hk.int.government_exempt",
            cond=Leaf("payee_is_government", is_true, on="payee")),        # "or a body agreed by both authorities": part of the fact
    RuleObj("cn-hk.roy.cap@cn", to(HK, ROYALTY), Effect.RATE_CAP, "cn-hk.roy.cap", cond=And(RESIDENT, BO_OTHER), uses=CLAIM),
    RuleObj("cn-hk.roy.cap_aircraft_ship_lease@cn", to(HK, ROYALTY), Effect.RATE_CAP, "cn-hk.roy.cap_aircraft_ship_lease",
            cond=And(RESIDENT, BO_OTHER, Leaf("is_aircraft_or_ship_lease", is_true)), uses=CLAIM),
    RuleObj("cn-hk.ppt@cn", to(HK, ALL), Effect.DENY, "cn-hk.ppt",
            cond=Discretion("ppt", cites=("treaty.cn-hk.2006.p5.zh#6",)), overrides=frozenset(HK_TREATY)),

    # ---- Agreement with Singapore
    RuleObj("cn-sg.div.cap_qualified@cn", to(SG, DIVIDEND), Effect.RATE_CAP, "cn-sg.div.cap_qualified",
            cond=And(RESIDENT, QUALIFIED("cn-sg.div.ratio_min"), BO_DIVIDEND), uses=CLAIM),
    RuleObj("cn-sg.div.cap_other@cn", to(SG, DIVIDEND), Effect.RATE_CAP, "cn-sg.div.cap_other",
            cond=And(RESIDENT, BO_DIVIDEND), uses=CLAIM),
    RuleObj("cn-sg.int.cap_bank@cn", to(SG, INTEREST), Effect.RATE_CAP, "cn-sg.int.cap_bank",
            cond=And(RESIDENT, BO_OTHER, Leaf("payee_is_financial_institution", is_true, on="payee")), uses=CLAIM),
    RuleObj("cn-sg.int.cap_other@cn", to(SG, INTEREST), Effect.RATE_CAP, "cn-sg.int.cap_other", cond=And(RESIDENT, BO_OTHER), uses=CLAIM),
    RuleObj("cn-sg.int.government_exempt@cn", to(SG, INTEREST), Effect.EXEMPT, "cn-sg.int.government_exempt",
            cond=And(Leaf("payee_is_government", is_true, on="payee"),
                     Leaf("government_exempt_condition_met", is_true, "cn-sg.int.government_exempt_condition_sg", on="payee"))),
    RuleObj("cn-sg.roy.cap@cn", to(SG, ROYALTY), Effect.RATE_CAP, "cn-sg.roy.cap", cond=And(RESIDENT, BO_OTHER), uses=CLAIM),
    RuleObj("cn-sg.roy.equipment_base@cn", to(SG, ROYALTY), Effect.BASE, "cn-sg.roy.equipment_base",
            cond=And(RESIDENT, BO_OTHER, Leaf("is_equipment_lease", is_true)),
            uses=("cn-sg.roy.includes_equipment", "cn-sg.roy.equipment_rent_is_royalty")),
    RuleObj("cn-sg.ppt@cn", to(SG, ALL), Effect.DENY, "cn-sg.ppt",
            cond=Discretion("ppt", cites=("treaty.cn-sg.2007.mli.zh#27",)), overrides=frozenset(SG_TREATY)),

    # ---- decision D42: a sale of goods. The Mainland seller (charged above, at home or abroad) on its profit — the price, at
    #      least the arm's-length price from a related buyer (decision D41), less the cost of the goods (实施条例 第十四条、
    #      第二十九条). A non-resident seller only on Mainland-source profits, which arise where the transaction takes place
    #      (第七条): through an establishment here a judgement, at 25% (EIT art 3(2)); without one, its sales into the
    #      Mainland are made abroad — no charge (art 3(3))
    RuleObj("cn.goods.base", Scope(ALL, CN, GOODS, side="residence"), Effect.BASE, None,
            uses=("cn.goods.income", "cn.goods.cost", "cn.tp.income_arms_length", "cn.tp.adjust_to_median", "cn.tp.related_share_min")),
    RuleObj("cn.goods.nonresident", dom(GOODS), Effect.CHARGE, "cn.eit.rate",
            cond=And(CROSS_BORDER, Leaf("fixed_place_in_cn", is_true, on="payee"),
                     Discretion("goods_sale_sourced_in_cn", cites=("cn.reg.eit#7",))),
            uses=("cn.goods.source", "cn.goods.nonresident_scope", "cn.eit.rate_entity")),
    RuleObj("cn.goods.nonresident.base", dom(GOODS), Effect.BASE, None, cond=CROSS_BORDER, uses=("cn.goods.cost",)),
    RuleObj("cn.nocharge.goods_nonresident", dom(GOODS), Effect.NOCHARGE, None,
            cond=And(CROSS_BORDER, Leaf("fixed_place_in_cn", is_false, on="payee")),
            uses=("cn.goods.source", "cn.goods.nonresident_scope")),

    # ---- decision D43: goods crossing the Mainland's border. An export is zero-rated, the input VAT refunded at the refund
    #      rate and the difference a cost of the seller (公告2026年第11号); export duty where the tariff lists the goods,
    #      paid by the consignor. An import: duty on the duty value and import VAT on it plus the duty, paid by the
    #      consignee — the buyer (关税法 第三条) — which credits the VAT as a general taxpayer (增值税法 第十六条)
    RuleObj("cn.vat.export.goods", Scope(ALL, CN, GOODS, side="residence"), Effect.VAT, "cn.vat.law.export_zero", before=VAT_LAW,
            bearer="payee", cond=Leaf("goods_exported_from_cn", is_true),
            uses=("cn.vat.law.rate_goods", "cn.vat.export.refund_rate_default", "cn.vat.export.non_refundable",
                  "cn.vat.export.fob_basis", "cn.vat.export.trader_basis")),
    RuleObj("cn.customs.export", Scope(ALL, CN, GOODS, side="residence"), Effect.CUSTOMS, None, before=TARIFF_LAW, bearer="payee",
            cond=Leaf("goods_exported_from_cn", is_true), uses=("cn.tariff.taxpayer", "cn.tariff.ad_valorem")),
    RuleObj("cn.customs.import", dom(GOODS), Effect.CUSTOMS, None, before=TARIFF_LAW, bearer="payer",
            cond=Leaf("goods_imported_into_cn", is_true), uses=("cn.tariff.taxpayer", "cn.tariff.ad_valorem", "cn.tariff.value",
                                                                "cn.tariff.related")),
    RuleObj("cn.vat.import.goods", dom(GOODS), Effect.VAT, "cn.vat.law.rate_goods", before=VAT_LAW, bearer="payer",
            cond=Leaf("goods_imported_into_cn", is_true), uses=("cn.vat.law.import", "cn.vat.law.rate_goods_reduced", "cn.tariff.value")),
    RuleObj("cn.vat.import.goods.credit", dom(GOODS), Effect.VAT, "cn.vat.law.rate_goods", before=VAT_LAW, bearer="payer",
            cond=And(Leaf("goods_imported_into_cn", is_true), Leaf("vat_general_taxpayer", is_true, "cn.vat.law.input_tax", on="payer"))),

    # ---- share transfers: the charge above applies to the gain, not the proceeds (a non-resident's base, art 19(2); a
    #      resident's gain has cn.resident.gain.base — both on one item would take the gain share twice; decision D32)
    RuleObj("cn.gain.base", dom((SHARE_TRANSFER, PROPERTY)), Effect.BASE, None, cond=CROSS_BORDER,
            uses=("cn.wht.base_gain", "cn.tp.related_transfer_arms_length", "cn.tp.related_share_min")),  # decision D38, D40
    RuleObj("cn-hk.gain.residence_only@cn", to(HK, SHARE_TRANSFER), Effect.EXEMPT, None,
            cond=GAIN_RESIDENCE_ONLY("cn-hk.gain.immovable_ratio_over", "cn-hk.gain.share_ratio_min"),
            uses=("cn-hk.gain.immovable_lookback", "cn-hk.gain.share_lookback")),
    RuleObj("cn-hk.gain.listed@cn", to(HK, SHARE_TRANSFER), Effect.EXEMPT, None,
            cond=And(RESIDENT, Leaf("listed_market_trade", is_true, "cn-hk.gain.listed_shares_residence_only"))),
    RuleObj("cn-sg.gain.residence_only@cn", to(SG, SHARE_TRANSFER), Effect.EXEMPT, None,
            cond=GAIN_RESIDENCE_ONLY("cn-sg.gain.immovable_ratio_over", "cn-sg.gain.share_ratio_min"),
            uses=("cn-sg.gain.share_lookback",)),

    # ---- indirect transfer of Mainland taxable property (公告2015年第7号): an offshore transfer is re-characterised
    #      when the arrangement lacks a reasonable commercial purpose; the four-factor case is deemed, the rest is judged
    RuleObj("cn.indirect.charge", INDIRECT, Effect.CHARGE, "cn.wht.rate",
            cond=And(Leaf("payee_resident_in_cn", is_false, on="payee"), And(Leaf("indirect_cn_target", is_true),
                     Or(And(Leaf("cn_value_ratio", ge, "cn.indirect.value_ratio"),
                            Or(Leaf("cn_asset_ratio", ge, "cn.indirect.asset_or_income_ratio"),
                               Leaf("cn_income_ratio", ge, "cn.indirect.asset_or_income_ratio")),
                            Leaf("limited_functions_and_risks", is_true),
                            Leaf("foreign_tax_lower_than_cn", is_true)),
                        Discretion("no_reasonable_commercial_purpose", cites=("cn.sta.2015-07#i3",)))))),
    RuleObj("cn.indirect.gain.base", INDIRECT, Effect.BASE, None,           # a non-resident's (7号 第一条; decision D32): a
            cond=Leaf("payee_resident_in_cn", is_false, on="payee"),        # resident's gain has cn.resident.gain.base
            uses=("cn.tp.related_transfer_arms_length", "cn.tp.related_share_min")),   # decision D38, D40
    RuleObj("cn.indirect.listed_safe_harbour", INDIRECT, Effect.EXEMPT, None,
            cond=Leaf("listed_market_trade", is_true, "cn.indirect.listed_safe_harbour")),
    # ---- the restructuring step (decision D18): 财税〔2009〕59号 §5 (all five conditions), §7(1) a non-resident's transfer to
    #      the non-resident it holds wholly — deferred; §7(3), §8 a resident's investment in the non-resident it holds
    #      wholly — the gain spread over ten tax years; 109号 §1 (50%); 公告2013年第72号 §2 (filing), §8 (dividends);
    #      decision D35: §7(2) a non-resident's transfer to the resident it holds wholly — deferred, with neither §7(1)'s
    #      withholding-burden test nor its 3-year commitment (72号 §5 and §8 name §7(1) only)
    RuleObj("cn.reorg.special", dom(SHARE_TRANSFER), Effect.DEFER, None,
            cond=And(REORG_COMMON, Leaf("payee_resident_in_cn", is_false, on="payee"), Leaf("reorg_buyer_resident_in_cn", is_false),
                     Or(Leaf("reorg_same_residence", is_true),
                        Discretion("reorg_wht_burden_unchanged", cites=("cn.cs.2009-59#i7",))),
                     Leaf("reorg_commitment_3y", is_true, "cn.reorg.commitment_years")),
            uses=("cn.reorg.control_ratio", "cn.reorg.filing_days")),
    RuleObj("cn.reorg.special_inbound", dom(SHARE_TRANSFER), Effect.DEFER, None,
            cond=And(REORG_COMMON, Leaf("payee_resident_in_cn", is_false, on="payee"), Leaf("reorg_buyer_resident_in_cn", is_true)),
            uses=("cn.reorg.control_ratio", "cn.reorg.filing_days")),
    RuleObj("cn.reorg.special_resident", Scope(ALL, CN, SHARE_TRANSFER, side="residence"), Effect.BASE, None,
            cond=And(REORG_COMMON, Leaf("payee_resident_in_cn", is_true, on="payee"), Leaf("reorg_buyer_resident_in_cn", is_false)),
            overrides=frozenset({"cn.resident.gain.base"}),      # the gain share is taken inside, spread over the years
            uses=("cn.reorg.resident_spread_years", "cn.reorg.control_ratio")),
    RuleObj("cn.reorg.treaty_dividend_denied", dom(DIVIDEND), Effect.DENY, "cn.reorg.dividend_treaty_denied",
            cond=And(Leaf("payee_resident_in_cn", is_false, on="payee"),       # §7(1)'s transferee (decision D35)
                     Leaf("reorg_special_applied", is_true), Leaf("reorg_same_residence", is_false),
                     Leaf("dividend_from_pre_reorg_profits", is_true)),
            overrides=frozenset({"cn-hk.div.cap_qualified@cn", "cn-hk.div.cap_other@cn", "cn-sg.div.cap_qualified@cn",
                                 "cn-sg.div.cap_other@cn"})),
    RuleObj("cn.indirect.reorg", INDIRECT, Effect.EXEMPT, None,
            cond=And(Leaf("intragroup_reorg_ratio", ge, "cn.indirect.reorg_ratio"),
                     Leaf("reorg_consideration_in_equity", is_true),
                     Leaf("later_cn_tax_not_reduced", is_true))),

    # ---- the payer's deduction: interest within the related-party debt-equity limit (or at arm's length), royalties
    #      if reasonable; both are judgements beyond the stated ratio, so grade D
    RuleObj("cn.deduct.interest", dom(INTEREST), Effect.DEDUCTION, "cn.eit.rate",
            cond=Or(Leaf("cn_related", is_false),
                    Leaf("related_party_debt_equity_ratio", le, "cn.thincap.ratio_other", on="payer"),
                    Discretion("arms_length_interest", cites=("cn.cs.2008-121#i2",), on="payer")),
            uses=("cn.deduct.general", "cn.thincap.disallow", "cn.thincap.ratio_financial", "cn.thincap.arms_length_exception",
                  "cn.eit.rate_entity", "cn.tp.related_share_min")),
    # 实施条例 第三十八条: interest from a non-financial lender is deductible only up to the financial-enterprise rate
    RuleObj("cn.deduct.interest.benchmark", dom(INTEREST), Effect.DEDUCT_BASE, None,
            uses=("cn.deduct.interest_benchmark",)),
    # a stated arm's-length ceiling caps the deductible royalty / fee / interest (公告2017年第6号 第二十五条: adjustment to the median)
    *[RuleObj("cn.tp.deduction_cap", dom((INTEREST, ROYALTY, SERVICE_FEE)), Effect.DEDUCT_BASE, None, cond=CROSS_BORDER,
              uses=("cn.tp.adjust_to_median", "cn.tp.domestic_same_burden_no_adjustment"))],
    RuleObj("cn.deduct.royalty", dom(ROYALTY), Effect.DEDUCTION, "cn.eit.rate",
            cond=Discretion("reasonable_royalty", cites=("cn.law.eit#8",), on="payer"),
            uses=("cn.deduct.general", "cn.eit.rate_entity")),

    # ---- procedure: remittance within 7 days of the obligation date; surcharge; refund and MAP clocks
    RuleObj("cn.wht.remit", dom(ALL), Effect.DEADLINE, "cn.wht.obligation_date",
            uses=("cn.wht.remit_days", "cn.wht.obligation_date_dividend", "cn.wht.fx_rule", "cn.time.holiday_roll", "cn.time.long_holiday_days")),
    RuleObj("cn.wht.late_surcharge", dom(ALL), Effect.PENALTY, "cn.tca.late_surcharge_daily"),
    RuleObj("cn.refund", dom(ALL), Effect.DEADLINE, "cn.refund.limit_years", uses=("cn.treaty.refund_route", "cn.treaty.refund_check_days")),
    # administrative review of a tax decision: tax or security first (征管法第88条), 60 days from knowing (行政复议法第20条)
    RuleObj("cn.review", dom(ALL), Effect.DEADLINE, "cn.review.days", cond=Leaf("tax_paid_or_secured", is_true, "cn.review.pay_first")),
    RuleObj("cn-hk.map", to(HK, ALL), Effect.DEADLINE, "cn-hk.map.limit", cond=MAP_COND),
    RuleObj("cn-sg.map", to(SG, ALL), Effect.DEADLINE, "cn-sg.map.limit", cond=MAP_COND),
]
