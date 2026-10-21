# Result: template recorded, subject GROUP, event {'on': '2026-12-31', 'as_at': '2026-10-20'}

Assumptions / gaps noted in the case file:
- Assessment of the recorded companies and dated transactions; no alternative structure is inferred.
- 0 fields read by qwen3.8-flash from demo_1_material-90be6c7132ab (2026-10-20, prompt 2026-10-15-en); quotes verified verbatim, numbers and dates parsed by the program from the quote; 0 conflicts and 0 constraint violations left unfilled; a person must review before use, then run tax_graph.verify.casecheck.
- review: confirmed as read
- reviewed by a person (2026-10-20, 0 items applied from review.json)

## Candidate table (group total tax lo / hi; subject share; discretion count, plan item count, fragility)

| Candidate | lo | hi | share@lo | share@hi | Discretion | Plan items | Fragility | Dominated |
|---|---|---|---|---|---|---|---|---|
| the only structure | -41250.00 | 42500.00 | -41250.00 | 42500.00 | 2 | 0 | 41250.00 |  |

**The only structure**: lo -41250.00 / hi 42500.00 (no structural variable; the conclusions lie in the pending items and the settled tax items).

## Tax items of the best candidate (flow / jurisdiction / levy / bearer / amount / basis)

lower bound:
- payment_1 · HK · income · payer · -41250.00 · hk.deduct.interest, hk.tp.corresponding, hk.tp.deduction_cap

upper bound:
- payment_1 · SG · income · payee · 42500.00 · sg.ftc.unilateral, sg.onshore.charge, sg.tp.income_uplift

## Pending facts (by the cost of losing them)
- 41250.00  ('hk.deduct.interest', 'payment_1')  payee.lender_interest_taxable_in_hk
- 41250.00  ('hk.loss.carryforward', 'entity:MARLOW_HOLDINGS_LIMITED')  MARLOW_HOLDINGS_LIMITED.taxable_income_other
- 0.00  ('sg.fsie.charge', 'payment_1')  flow.receipt_kind
- 0.00  ('sg.ftc.pooling', 'payment_1')  flow.foreign_headline_rate, flow.foreign_taxed, payee.ftc_pooling_election
- 0.00  ('data.p2_scope', 'HK')  group.group_revenue_eur
- 0.00  ('data.p2_scope', 'SG')  group.group_revenue_eur
- 0.00  ('data.p2_tcsh', 'HK')  group.p2_cbcr_pbt_hk, group.p2_cbcr_revenue_hk, group.p2_cbcr_simplified_taxes_hk, group.p2_eur_rate, group.p2_qualified_cbcr_hk, group.p2_tcsh_history_hk
- 0.00  ('data.p2_dm', 'HK')  group.p2_dm_avg_income_eur_hk, group.p2_dm_avg_revenue_eur_hk
- 0.00  ('data.p2_income', 'MARLOW_HOLDINGS_LIMITED')  group.group_revenue_eur
- 0.00  ('data.p2_tcsh', 'SG')  group.p2_cbcr_pbt_sg, group.p2_cbcr_revenue_sg, group.p2_cbcr_simplified_taxes_sg, group.p2_eur_rate, group.p2_qualified_cbcr_sg, group.p2_tcsh_history_sg
- 0.00  ('data.p2_dm', 'SG')  group.p2_dm_avg_income_eur_sg, group.p2_dm_avg_revenue_eur_sg
- 0.00  ('data.p2_income', 'MARLOW_CAPITAL_PTE_LTD')  group.group_revenue_eur

## Pending conditions: plan items and discretion items (by cost)
- 41250.00  ('hk.deduct.interest', 'payment_1')  payer.incurred_in_production_of_profits
- 0.00  ('sg.onshore.charge', 'payment_1')  payee.income_sourced_in_sg

## Fields the rules read but the case does not give (13)
- payment_1  flow.arms_length_low
- payment_1  flow.arms_length_max
- payment_1  flow.arms_length_value
- payment_1  flow.assessment_notice_on
- payment_1  flow.corresponding_adjustment_granted
- payment_1  flow.foreign_tax_rate
- payment_1  flow.receipt_kind
- payment_1  payee.lender_interest_taxable_in_hk
- payment_1  payee.ucmt_location
- payment_1  payer.accounting_period_end
- payment_1  payer.hk_tp_small_entity
- payment_1  payer.is_mne_member
- payment_1  payer.ucmt_location
