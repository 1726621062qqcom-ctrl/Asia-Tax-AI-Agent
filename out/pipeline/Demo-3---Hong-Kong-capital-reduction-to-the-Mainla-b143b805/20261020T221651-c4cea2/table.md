# Result: template recorded, subject GROUP, event {'on': '2026-09-01', 'as_at': '2026-10-20'}

Assumptions / gaps noted in the case file:
- Assessment of the recorded companies and dated transactions; no alternative structure is inferred.
- 0 fields read by qwen3.8-flash from demo_3_material-336cf8d3a5cf (2026-10-20, prompt 2026-10-15-en); quotes verified verbatim, numbers and dates parsed by the program from the quote; 0 conflicts and 0 constraint violations left unfilled; a person must review before use, then run tax_graph.verify.casecheck.
- review: confirmed as read
- reviewed by a person (2026-10-20, 0 items applied from review.json)

## Candidate table (group total tax lo / hi; subject share; discretion count, plan item count, fragility)

| Candidate | lo | hi | share@lo | share@hi | Discretion | Plan items | Fragility | Dominated |
|---|---|---|---|---|---|---|---|---|
| the only structure | 0.00 | 750000.00 | 0.00 | 750000.00 | 1 | 0 | 0.00 |  |

**The only structure**: lo 0.00 / hi 750000.00 (no structural variable; the conclusions lie in the pending items and the settled tax items).

## Tax items of the best candidate (flow / jurisdiction / levy / bearer / amount / basis)

lower bound:

upper bound:
- payment_1.div · CN · income · payee · 0.00 · cn.capital_reduction.split, cn.ftc.dividend_indirect, cn.resident.charge
- payment_1.gain · CN · income · payee · 255000.00 · cn.capital_reduction.split, cn.ftc.direct, cn.resident.gain.base, cn.resident.gain.charge
- payment_1.gain · HK · income · payee · 495000.00 · cn.capital_reduction.split, hk.gain.base, hk.gain.charge

## Pending facts (by the cost of losing them)
- 0.00  ('cn.capital_reduction.split', 'payment_1')  flow.accumulated_profits_share
- 0.00  ('cn.ftc.dividend_indirect', 'payment_1.div')  JINHAI_ASIA_LIMITED.after_tax_profit
- 0.00  ('hk.onshore_gain.certainty', 'payment_1.gain')  flow.held_as_trading_stock, payee.sch17k_elected
- 0.00  ('cn.resident.gain.base', 'payment_1.gain')  flow.cost_basis
- 0.00  ('hk.gain.base', 'payment_1.gain')  flow.cost_basis
- 0.00  ('data.p2_scope', 'HK')  group.group_revenue_eur
- 0.00  ('data.p2_tcsh', 'HK')  group.p2_cbcr_pbt_hk, group.p2_cbcr_revenue_hk, group.p2_cbcr_simplified_taxes_hk, group.p2_eur_rate, group.p2_qualified_cbcr_hk, group.p2_tcsh_history_hk
- 0.00  ('data.p2_dm', 'HK')  group.p2_dm_avg_income_eur_hk, group.p2_dm_avg_revenue_eur_hk
- 0.00  ('data.p2_income', 'JINHAI_ASIA_LIMITED')  group.group_revenue_eur
- 0.00  ('cn.residence.pem', 'JINHAI_ASIA_LIMITED')  JINHAI_ASIA_LIMITED.managed_from

## Pending conditions: plan items and discretion items (by cost)
- 0.00  ('hk.gain.capital', 'payment_1.gain')  payee.capital_asset

## Fields the rules read but the case does not give (3)
- payment_1  flow.assessment_notice_on
- payment_1  payee.ucmt_location
- payment_1  payer.ucmt_location
