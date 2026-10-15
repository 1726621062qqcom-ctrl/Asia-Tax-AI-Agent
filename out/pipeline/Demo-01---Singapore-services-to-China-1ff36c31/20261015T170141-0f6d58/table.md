# Result: template recorded, subject GROUP, event {'on': '2026-09-15', 'as_at': '2026-10-15'}

Assumptions / gaps noted in the case file:
- Assessment of the recorded companies and dated transactions; no alternative structure is inferred.
- 12 fields read by deepseek-flash from demo01_services-txt-91f5944a0a7b (2026-10-15, prompt 2026-10-15-en); quotes verified verbatim, numbers and dates parsed by the program from the quote; 0 conflicts and 0 constraint violations left unfilled; a person must review before use, then run tax_graph.verify.casecheck.
- reviewed by a person (2026-10-15, 12 items applied from review.json)

## Candidate table (group total tax lo / hi; subject share; discretion count, plan item count, fragility)

| Candidate | lo | hi | share@lo | share@hi | Discretion | Plan items | Fragility | Dominated |
|---|---|---|---|---|---|---|---|---|
| the only structure | 60000.00 | 310000.00 | 60000.00 | 310000.00 | 3 | 0 | 100000.00 |  |

**The only structure**: lo 60000.00 / hi 310000.00 (no structural variable; the conclusions lie in the pending items and the settled tax items).

## Tax items of the best candidate (flow / jurisdiction / levy / bearer / amount / basis)

lower bound:
- payment_1 · CN · vat · payee · 60000.00 · cn.vat.law.service
- payment_1 · CN · vat · payer · -60000.00 · cn.vat.law.input_credit
- payment_1 · CN · surcharge · payer · -4200.00 · cn.surcharge.ucmt
- payment_1 · CN · surcharge · payer · -1200.00 · cn.surcharge.local_edu
- payment_1 · CN · income · payer · -250000.00 · cn.deduct.service, cn.tp.corresponding, cn.tp.deduction_cap

upper bound:
- payment_1 · CN · vat · payee · 60000.00 · cn.vat.law.service
- payment_1 · CN · income · payee · 250000.00 · cn.service.charge, cn.service.deemed_profit

## Pending facts (by the cost of losing them)
- 51000.00  ('cn.service.charge', 'payment_1')  flow.service_performed_in_source
- 51000.00  ('sg.ftc.pooling', 'payment_1')  flow.foreign_headline_rate, flow.foreign_tax_rate, flow.foreign_taxed, payee.ftc_pooling_election
- 0.00  ('cn.vat.law.input_credit', 'payment_1')  payer.vat_general_taxpayer
- 0.00  ('cn.surcharge.ucmt', 'payment_1')  payer.ucmt_location
- 0.00  ('cn.service.deemed_profit', 'payment_1')  flow.service_kind, flow.service_onshore_share
- 0.00  ('data.p2_scope', 'SG')  group.group_revenue_eur
- 0.00  ('data.p2_tcsh', 'SG')  group.p2_cbcr_pbt_sg, group.p2_cbcr_revenue_sg, group.p2_cbcr_simplified_taxes_sg, group.p2_eur_rate, group.p2_qualified_cbcr_sg, group.p2_tcsh_history_sg
- 0.00  ('data.p2_dm', 'SG')  group.p2_dm_avg_income_eur_sg, group.p2_dm_avg_revenue_eur_sg
- 0.00  ('data.p2_income', 'COMPANY_A')  group.group_revenue_eur

## Pending conditions: plan items and discretion items (by cost)
- 100000.00  ('cn.wht.service_as_royalty', 'payment_1')  payee.service_fee_is_royalty_for_know_how
- 0.00  ('cn.deduct.service', 'payment_1')  payer.reasonable_service_fee
- 0.00  ('cn-sg.ppt@cn', 'payment_1')  payee.ppt

## Fields the rules read but the case does not give (19)
- payment_1  flow.arms_length_low
- payment_1  flow.arms_length_max
- payment_1  flow.assessment_notice_on
- payment_1  flow.corresponding_adjustment_granted
- payment_1  flow.first_notification_on
- payment_1  flow.foreign_tax_rate
- payment_1  flow.pboc_benchmark_rate
- payment_1  flow.service_kind
- payment_1  flow.service_onshore_share
- payment_1  flow.service_performed_in_residence
- payment_1  flow.service_performed_in_source
- payment_1  flow.tax_paid_on
- payment_1  flow.tp_adjustment_paid_on
- payment_1  flow.tp_adjustment_tax
- payment_1  payee.ucmt_location
- payment_1  payer.related_party_volume
- payment_1  payer.tp_documentation_provided
- payment_1  payer.ucmt_location
- payment_1  payer.vat_general_taxpayer
