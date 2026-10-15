# -*- coding: utf-8 -*-
"""案例采集 K5, Mainland: factors and precedents for the judgements of spec_cn.py (issue keys "CN:<Discretion key>").
Nothing here binds (案例采集.md §1, §5): a Supreme People's Court typical case, SAT replies and advance rulings are
persuasive; tax bureau case reports and the examples in the SAT interpretation of 公告2018年第9号 are practice. TCI and
燕莎 were decided under 国税函〔2009〕698号, repealed by 公告2015年第7号: kept for factors that 7号公告 第三条 lists too.
Not used: 税总函〔2013〕165号 applies 601号 and 公告2012年第30号, both repealed in 2018 (library holds current law only)."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cards_lib import write  # noqa: E402

JD, DY, TCI, YS, JY = ("cn.jd.2018-09", "cn.case.js-danyang-2026", "cn.case.spc-tci-2017", "cn.gsh.2014-579", "cn.case.js-jiangyin-2026")
SH24, SH25, GD, JSM, SQ, JT = ("cn.ruling.sh-2024-tsxcl", "cn.ruling.sh-2025-xshb", "cn.case.gd-trademark-2021", "cn.case.js-m-2018",
                               "cn.case.js-suqian-2026", "cn.case.js-jintan-2025")
BO, RCP, RR, RY, SF, AL = ("CN:no_adverse_bo_factors", "CN:no_reasonable_commercial_purpose", "CN:reorg_reasonable_commercial_purpose",
                           "CN:reasonable_royalty", "CN:reasonable_service_fee", "CN:arms_length_interest")

FACTORS = [
    # beneficial owner (公告2018年第9号 第二条): true = no adverse factor, the treaty rate applies
    (BO, "bo_pays_out", "payee", "pays_out_over_half_within_12m", "is_true", "false", JD,
     "一个月内即通过关联贷款的名义将该笔所得的80%以上支付给母公司", "9号公告 interpretation: the related-party loan establishes the fact of payment"),
    (BO, "bo_reinvests", "payee", "income_reinvested", "is_true", "true", JD, "申请人取得的每笔股息所得均转增已投资项目的资本", "9号公告 interpretation"),
    (BO, "bo_staff_not_own", "payee", "staff_perform_parent_functions", "is_true", "false", JD,
     "其声称的5名雇员实际与A国公司签订合同并履行A国公司的职能", "9号公告 interpretation: shell company"),
    (BO, "bo_income_idle", "payee", "income_left_idle", "is_true", "false", JD, "其收到的股息暂无投资计划，在账户中闲置", "9号公告 interpretation"),
    (BO, "bo_directors_by_parent", "payee", "directors_appointed_by_upper_parent", "is_true", "false", JD,
     "中国公司的外方董事不是由其直接股东B国公司派出而是由A国公司直接派出", "9号公告 interpretation"),
    (BO, "bo_regional_functions", "payee", "performs_regional_investment_functions", "is_true", "true", JD,
     "评估分析、投资决策以及亚洲区域内各公司之间的资金统筹调配等功能由B国公司承担", "9号公告 interpretation: regional headquarters"),
    (BO, "bo_many_investments", "payee", "invests_in_many_companies", "is_true", "true", JD,
     "还投资日本、韩国、新加坡、越南等十余个国家近50家公司", "9号公告 interpretation"),
    (BO, "bo_too_few_staff", "payee", "staff_insufficient_for_functions", "is_true", "false", JD,
     "但B国公司仅有8名员工，不足以承担相关功能", "9号公告 interpretation; same in the Danyang case (fewer than 10 employees, mostly in sales)"),
    (BO, "bo_funds_raised_locally", "payee", "funds_raised_in_residence_state", "is_true", "true", JD,
     "所需资金的30%从B国融入，与B国有一定联系", "9号公告 interpretation: financing platform"),
    (BO, "bo_unexplained_shift", "payee", "functions_moved_without_business_need", "is_true", "false", JD,
     "B国公司无法证明做此调整的商业必要性", "9号公告 interpretation"),
    (BO, "bo_other_income_small", "payee", "other_business_income_share_small", "is_true", "false", JD,
     "（含从中国境内取得的全部所得）的比例仅为8%", "9号公告 interpretation; same in the Danyang case (under 10%)"),
    (BO, "bo_many_staff", "payee", "substantial_own_staff", "is_true", "true", JD, "B国公司有超过50个员工", "9号公告 interpretation: positive example"),
    (BO, "bo_single_investment", "payee", "single_investment_only", "is_true", "false", DY, "仅投资设立了N公司", "Danyang"),
    (BO, "bo_no_investment_records", "payee", "no_investment_decision_records", "is_true", "false", DY,
     "无法提供对该投资项目投前研究、投中决策、投后管理的完整证明材料", "Danyang"),
    (BO, "bo_director_abroad", "payee", "directors_not_in_residence_state", "is_true", "false", DY,
     "仅有1名董事在乙国办公，不在甲国拿董事费", "Danyang"),
    (BO, "bo_related_loan_payout", "payee", "large_share_paid_out_via_related_loans", "is_true", "false", DY,
     "将股息所得的49%以关联贷款名义支付给L公司", "Danyang: under 50% but clearly contrived"),
    (BO, "bo_not_taxed_home", "payee", "income_not_taxed_in_residence", "is_true", "false", DY,
     "甲国对M公司取得的来源于境外的股息所得不征税", "Danyang; 9号公告 art. 2 item (3)"),

    # indirect transfer (公告2015年第7号 第三条): true = no reasonable commercial purpose, recharacterised
    (RCP, "rcp_value_from_cn", "flow", "offshore_value_mainly_from_cn", "is_true", "true", YS,
     "新诚股权主要价值由对燕莎的权益性投资价值构成", "579号; 7号公告 art. 3 item (1); same in the Jiangyin case"),
    (RCP, "rcp_income_from_cn", "flow", "offshore_income_mainly_from_cn", "is_true", "true", YS, "新诚收入主要来源于对燕莎的投资", "579号"),
    (RCP, "rcp_no_substance", "flow", "offshore_entities_without_substance", "is_true", "true", YS,
     "新诚无雇员，实际不履行功能，不承担风险，无实质性经营活动", "579号; same in TCI and Jiangyin"),
    (RCP, "rcp_low_tax", "flow", "offshore_tax_on_transfer_low", "is_true", "true", YS, "该间接股权转让交易的境外实际税负低于10%", "579号"),
    (RCP, "rcp_some_services", "flow", "offshore_entity_has_some_service_income", "is_true", "false", YS,
     "另有部分服务费收入来源于坚信为燕莎提供管理服务", "579号: not enough to change the conclusion"),
    (RCP, "rcp_haven_registration", "flow", "intermediates_in_low_tax_places", "is_true", "true", TCI,
     "有关公司仅在避税地或低税率地区注册", "TCI 案"),
    (RCP, "rcp_price_by_cn_asset", "flow", "price_driven_by_cn_asset_value", "is_true", "true", TCI,
     "股权转让价主要取决于国益路桥公司估值", "TCI 案"),
    (RCP, "rcp_buyer_disclosed_target", "flow", "buyer_disclosed_cn_target", "is_true", "true", TCI,
     "股权受让方对外披露收购的实际标的为国益路桥公司股权", "TCI 案"),

    # special reorganisation (财税〔2009〕59号 第五条第（一）项): true = reasonable commercial purpose
    (RR, "rr_stated_purpose", "flow", "stated_business_purpose", "is_true", "true", SH24,
     "具有合理的商业目的，且不以减少、免除或者推迟缴纳税款为主要目的", "Shanghai advance ruling: the applicant's statement; the ruling did not analyse it further"),
    (RR, "rr_all_equity", "flow", "consideration_all_in_equity", "is_true", "true", SH24,
     "本次重组交易对价均为100%A公司自身股权，不涉及现金支付", "Shanghai advance ruling"),
    (RR, "rr_lockup", "flow", "shares_kept_12m", "is_true", "true", SH24, "B公司在重组后连续12个月内不转让所取得的股权", "Shanghai advance ruling"),
    (RR, "rr_integration", "flow", "integration_of_group_resources", "is_true", "true", SH25,
     "为整合公司资源，拟由A公司吸收合并E公司", "Shanghai advance ruling (merger by absorption)"),

    # related-party prices (企业所得税法第四十一条): true = at arm's length
    (RY, "ry_brand_value_cn", "flow", "brand_value_created_in_cn", "is_true", "false", GD, "品牌的主要价值在内地形成", "Guangdong: trademark royalty"),
    (RY, "ry_licensee_markets", "payer", "licensee_bears_main_marketing", "is_true", "false", GD, "A公司承担了品牌主要的营销与推广活动", "Guangdong"),
    (RY, "ry_licensor_limited", "payee", "licensor_limited_functions", "is_true", "false", GD,
     "M公司只负责服装的设计、商业规划以及在中国香港和中国澳门的推广", "Guangdong"),
    (SF, "sf_fees_rising", "flow", "related_service_fees_rising_while_trade_falls", "is_true", "false", JSM,
     "集团内关联劳务支付项目和金额越来越多", "Jiangsu Company M: related-party purchases and sales fell while service payments rose"),
    (SF, "sf_many_labels", "flow", "many_fee_labels", "is_true", "false", JSM, "包括咨询费、管理费、服务费、佣金等众多名目", "Jiangsu Company M"),
    (SF, "sf_only_profitable_years", "flow", "fees_only_in_profitable_years", "is_true", "false", SQ,
     "丙公司仅在盈利年度向亏损母公司支付高额服务费", "Suqian interview example"),
    (SF, "sf_arbitrary_amounts", "flow", "fee_amounts_arbitrary", "is_true", "false", SQ, "且有关年度支付的金额较为随意", "Suqian"),
    (SF, "sf_shareholder_activity", "flow", "services_are_shareholder_activities", "is_true", "false", SQ,
     "仅是母公司作为股东身份本应履行的义务", "Suqian"),
    (SF, "sf_strategy_claimed", "flow", "parent_provides_strategy_and_decisions", "is_true", "true", SQ,
     "母公司作为公司股东为其制定经营战略、作出重大经营决策等提供服务", "Suqian: the enterprise's claim, not accepted"),
    (AL, "al_tax_burden_differs", "flow", "related_parties_tax_burden_differs", "is_true", "false", JT,
     "发现集团成员企业间均实际存在税负差异", "Jintan"),
    (AL, "al_same_tax_burden", "flow", "related_parties_same_tax_burden", "is_true", "true", JT,
     "实际税负相同的境内关联方之间的交易", "Jintan citing 公告2017年第6号 art. 38: in principle no special tax adjustment"),
    (AL, "al_no_long_balances", "flow", "no_long_outstanding_balances", "is_true", "true", JT,
     "无长期挂账现象，实质未造成收入减少", "Jintan: the enterprise's claim, not accepted"),
]

PRECEDENTS = [
    ("CN-jd9-conduit", BO, "CN", "SAT interpretation example", "practice", "2018-02-06", "false",
     [], ["bo_pays_out"], [], JD, "上述事实对判定其“受益所有人”身份非常不利", "Related-party loan: over 80% paid out within a month, no repayment term, 0.5% interest"),
    ("CN-jd9-reinvest", BO, "CN", "SAT interpretation example", "practice", "2018-02-06", "true",
     ["bo_reinvests"], [], [], JD, "或者用于投资在中国境内的新项目", "All dividends capitalised or invested in new Mainland projects: not a payment of over 50% within 12 months"),
    ("CN-jd9-shell", BO, "CN", "SAT interpretation example", "practice", "2018-02-06", "false",
     [], ["bo_staff_not_own", "bo_income_idle", "bo_directors_by_parent"], [], JD,
     "但实际履行的功能及承担的风险有限，不足以证实其活动具有实质性", "Claimed investment holding: employees perform the upper parent's functions, dividends left idle, directors sent by the upper parent"),
    ("CN-jd9-rhq", BO, "CN", "SAT interpretation example", "practice", "2018-02-06", "true",
     ["bo_regional_functions", "bo_many_investments"], [], [], JD, "应认为B国公司承担的区域总部功能具有一定实质性",
     "Regional headquarters: invests in nearly 50 companies in over ten countries and carries out appraisal, decisions and fund allocation itself: substantive business activity (on that adverse factor only)"),
    ("CN-jd9-rhq-8staff", BO, "CN", "SAT interpretation example", "practice", "2018-02-06", "false",
     ["bo_many_investments"], ["bo_too_few_staff"], [], JD, "应认为B国公司从事的活动不具有实质性", "Variant of the same example: only 8 employees, not enough to carry out the functions"),
    ("CN-jd9-financing", BO, "CN", "SAT interpretation example", "practice", "2018-02-06", "true",
     ["bo_funds_raised_locally"], [], [], JD, "所需资金的30%从B国融入，与B国有一定联系", "Financing platform: 30% of the funds raised in the residence state: some substance"),
    ("CN-jd9-otherbiz", BO, "CN", "SAT interpretation example", "practice", "2018-02-06", "false",
     [], ["bo_unexplained_shift", "bo_other_income_small"], [], JD, "上述案例可以认为申请人从事的其他经营活动不够显著，不构成实质性经营活动",
     "Procurement function moved in without business need; other business income only 8%"),
    ("CN-jd9-positive", BO, "CN", "SAT interpretation example", "practice", "2018-02-06", "true",
     ["bo_many_staff", "bo_reinvests"], [], [], JD, "倾向于认为B国公司具有“受益所有人”身份", "Regional investment holding: own team of over 50 staff, profits reinvested"),
    ("CN-danyang-2026", BO, "CN", "Tax bureau (丹阳)", "practice", "2026-09-21", "false",
     [], ["bo_single_investment", "bo_no_investment_records", "bo_director_abroad", "bo_too_few_staff", "bo_other_income_small",
          "bo_related_loan_payout", "bo_not_taxed_home"], [], DY, "M公司补缴了相关税款及滞纳金",
     "Treaty shopping: the intermediate company in state A invests in one Mainland company only, under 10 employees, 49% paid out as related-party loans: not the beneficial owner, tax collected at 10%"),
    ("CN-tci-2017", RCP, "CN", "Supreme People's Court typical case", "persuasive", "2017-06-13", "true",
     ["rcp_haven_registration", "rcp_no_substance", "rcp_price_by_cn_asset", "rcp_buyer_disclosed_target"], [], [], TCI,
     "属于以减少我国企业所得税为主要目的的安排", "Indirect transfer of an expressway company: recharacterised, over CNY 100 million collected, retrial application dismissed; under 698号 (repealed) and 企业所得税法 art. 47"),
    ("CN-yansha-2014", RCP, "CN", "SAT reply", "persuasive", "2014-12-03", "true",
     ["rcp_value_from_cn", "rcp_income_from_cn", "rcp_no_substance", "rcp_low_tax"], ["rcp_some_services"], [], YS,
     "视同直接转让燕莎股权", "Indirect transfer of Yansha: the Singapore intermediate company has no employees, its value and income come mainly from Yansha, offshore tax burden under 10%; under 698号 (repealed)"),
    ("CN-jiangyin-2026", RCP, "CN", "Tax bureau (江阴)", "practice", "2026-08-04", "true",
     ["rcp_no_substance", "rcp_value_from_cn"], [], [], JY, "依法缴纳了股权转让税款2.8亿元", "Offshore shell company, all value from the Mainland company: CNY 280 million paid"),
    ("CN-sh-ruling-2024", RR, "CN", "Shanghai advance ruling", "persuasive", "2024-03-01", "true",
     ["rr_stated_purpose", "rr_all_equity", "rr_lockup"], [], [], SH24, "上述重组业务符合企业所得税特殊性税务处理条件，可以选择适用特殊性税务处理",
     "Share acquisition: paid entirely in shares, control acquired, no transfer for 12 months: special tax treatment may be elected; on the applicant's statement, binds the applicant only"),
    ("CN-sh-ruling-2025", RR, "CN", "Shanghai advance ruling", "persuasive", "2025-05-01", "true",
     ["rr_integration", "rr_stated_purpose"], [], [], SH25, "可以选择适用企业所得税特殊性税务处理",
     "Merger by absorption of two wholly owned subsidiaries of the same parent, no consideration: special tax treatment may be elected; binds the applicant only"),
    ("CN-gd-trademark-2021", RY, "CN", "Tax bureau (广东)", "practice", "2021-07-13", "false",
     [], ["ry_brand_value_cn", "ry_licensee_markets", "ry_licensor_limited"], [], GD, "商标使用费应采用剩余利润分割法进行调整",
     "Trademark fee of 8% of sales paid to the Hong Kong parent: the brand value was created in the Mainland: income adjusted up by over CNY 200 million, over CNY 60 million collected"),
    ("CN-js-m-2018", SF, "CN", "Tax bureau (江苏)", "practice", "2018-11-23", "false",
     [], ["sf_fees_rising", "sf_many_labels"], [], JSM, "最终查实550多万元费用不得税前扣除", "Related-party service fees under many labels, rising year by year: over CNY 5.5 million not deductible"),
    ("CN-suqian-2026", SF, "CN", "Tax bureau (宿迁) example", "practice", "2026-03-06", "false",
     ["sf_strategy_claimed"], ["sf_only_profitable_years", "sf_arbitrary_amounts", "sf_shareholder_activity"], [], SQ,
     "仅是母公司作为股东身份本应履行的义务", "Paid only in profitable years, arbitrary amounts, shareholder activities: service fees not recognised (example given in an interview)"),
    ("CN-jintan-2025", AL, "CN", "Tax bureau (金坛)", "practice", "2025-02-06", "false",
     ["al_no_long_balances"], ["al_tax_burden_differs"], [], JT, "应分别调增应税收入117万元、4926万元",
     "Interest-free intra-group funds: tax burdens differ between members: interest income adjusted up; domestic related parties with the same tax burden are in principle not adjusted"),
]

nf, np_, missing = write(FACTORS, PRECEDENTS)
print("factors", nf, "precedents", np_)
for m in missing:
    print("  NOT FOUND", m)
