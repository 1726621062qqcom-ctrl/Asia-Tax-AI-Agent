# Result: template inbound_services, subject SERVICER, event {'service_fee': 1000000, 'on': '2025-12-31', 'as_at': '2026-10-07'}

Assumptions / gaps noted in the case file:
- 合同金额 SGD 1,000,000，客户按 10% 扣缴 100,000 并取得扣缴凭证；金额单位为新元。
- 付款日与扣缴日案例未给，取 2025-12-31；这只影响退税与相互协商时钟的起算。
- 境内履行份额未知：已知境内工作 76 天、大部分工作在新加坡完成，故两地均有履行为事实，service_onshore_share 留空，内地核定税基对份额取区间。
- 新加坡税务居民证明（COR）是否已取得未给，residence_cert 留空；协定免税与退税都以它为前提。
- 新加坡部分免税（s43(6B)）按公司全年应税所得计算，案例只给了本项目的 100 万收入与 70 万成本，故未填 cit_rate，按 17% 名义税率；profit_margin 30 为本项目利润率。
- service_kind 取 ENGINEERING_DESIGN_CONSULTING（数据分析、模型、系统实施、培训属设计咨询类，国税发〔2010〕19 号第五条 15%–30%）。
- 合同未转让专利、著作权或专有技术，客户不得源代码；是否被认定为特许权使用费是裁量项（国税函〔2009〕507 号第四、六条）。
- Meridian 实收 900,000 = 合同额 − 10% 企业所得税，未被代扣增值税；代扣增值税（如有）由客户承担，故 vat_borne_by_payer = true。

## Candidate table (group total tax lo / hi; subject share; discretion count, plan item count, fragility)

| Candidate | lo | hi | share@lo | share@hi | Discretion | Plan items | Fragility | Dominated |
|---|---|---|---|---|---|---|---|---|
| the only structure | 51000.00 | 100000.00 | 51000.00 | 100000.00 | 3 | 0 | 49000.00 |  |

**The only structure**: lo 51000.00 / hi 100000.00 (no structural variable; the conclusions lie in the pending items and the settled tax items).

## Tax items of the best candidate (flow / jurisdiction / levy / bearer / amount / basis)

lower bound:
- fee · SG · income · payee · 51000.00 · sg.ftc.dta, sg.service.base, sg.service.charge, sg.tp.income_uplift
- fee · CN · income · payer · -250000.00 · cn.deduct.service, cn.tp.corresponding, cn.tp.deduction_cap

upper bound:
- fee · CN · income · payee · 100000.00 · cn.wht.service_as_royalty

## Pending facts (by the cost of losing them)
- 0.00  ('cn-sg.pe.no_pe@cn', 'fee')  payee.residence_cert
- 0.00  ('cn.service.deemed_profit', 'fee')  flow.service_onshore_share
- 0.00  ('sg.ftc.pooling', 'fee')  payee.ftc_pooling_election
- 0.00  ('data.p2_scope', 'SG')  group.group_revenue_eur
- 0.00  ('data.p2_tcsh', 'SG')  group.p2_cbcr_pbt_sg, group.p2_cbcr_revenue_sg, group.p2_cbcr_simplified_taxes_sg, group.p2_eur_rate, group.p2_qualified_cbcr_sg
- 0.00  ('data.p2_dm', 'SG')  group.p2_dm_avg_income_eur_sg, group.p2_dm_avg_revenue_eur_sg
- 0.00  ('data.p2_income', 'SERVICER')  group.group_revenue_eur

## Pending conditions: plan items and discretion items (by cost)
- 49000.00  ('cn.wht.service_as_royalty', 'fee')  payee.service_fee_is_royalty_for_know_how
- 0.00  ('cn.deduct.service', 'fee')  payer.reasonable_service_fee
- 0.00  ('cn-sg.ppt@cn', 'fee')  payee.ppt

## Settled tax items: recoverable / shortfall risk / routes
- fee/CN: paid 100000.00, per the rules [0.00, 100000.00]; confirmed recoverable 0.00, potentially recoverable 100000.00; shortfall risk [0.00, 0.00]; clocks {'refund': '2028-12-31'}; routes ['refund', 'map']

## Fields the rules read but the case does not give (18)
- fee  flow.arms_length_low
- fee  flow.arms_length_max
- fee  flow.arms_length_value
- fee  flow.assessment_notice_on
- fee  flow.corresponding_adjustment_granted
- fee  flow.first_notification_on
- fee  flow.foreign_tax_rate
- fee  flow.payable_on
- fee  flow.pboc_benchmark_rate
- fee  flow.service_onshore_share
- fee  flow.tax_paid_or_secured
- fee  flow.tp_adjustment_paid_on
- fee  flow.tp_adjustment_tax
- fee  payee.residence_cert
- fee  payee.ucmt_location
- fee  payer.related_party_volume
- fee  payer.tp_documentation_provided
- fee  payer.ucmt_location
