# Result: template holding, subject GROUP, event {'exit': 266200000.0, 'on': '2026-04-02'}

Assumptions / gaps noted in the case file:
- Source: SMIT Holdings (2239.HK) circular of 2026-06-15 (cases/sources/K4-smit-2026/source.pdf).
- The domestic seller (Mainland, high-tech enterprise at 15%) is recorded as ULT; the target (an associate, 7.8125% held) is OP and is outside the group's tax total (members contains only ULT); the buyer is a domestic limited partnership outside the group.
- The consideration is "approximately RMB 266.2 million"; amounts are in RMB.
- names: each party's defined term / full name in the document (aliases separated by /), individuals written as in the document, used for locating extraction patterns, search queries and registry look-ups (抽取改造.md §2, §7)
- 0 fields read by deepseek-flash from K4-smit-2026 (2026-10-15, prompt 2026-10-15-en); quotes verified verbatim, numbers and dates parsed by the program from the quote; 0 conflicts and 0 constraint violations left unfilled; a person must review before use, then run tax_graph.verify.casecheck.
- not reviewed by a person (--auto, 2026-10-15): the to-do list todo.json was not handled; conflicts and missing items are computed as missing

## Candidate table (group total tax lo / hi; subject share; discretion count, plan item count, fragility)

| Candidate | lo | hi | share@lo | share@hi | Discretion | Plan items | Fragility | Dominated |
|---|---|---|---|---|---|---|---|---|
| SG/INDIRECT | 0.00 | 39930000.00 | 0.00 | 39930000.00 | 1 | 3 | 0.00 |  |
| None/DIRECT | 25063100.00 | 25063100.00 | 25063100.00 | 25063100.00 | 0 | 0 | 0.00 |  |
| CN/INDIRECT | 133100.00 | 40063100.00 | 133100.00 | 40063100.00 | 0 | 0 | 0.00 | yes |
| CN/DIRECT | 133100.00 | 66683100.00 | 133100.00 | 66683100.00 | 0 | 0 | 0.00 | yes |
| HK/DIRECT | 133100.00 | 66683100.00 | 133100.00 | 66683100.00 | 0 | 2 | 0.00 | yes |
| SG/DIRECT | 133100.00 | 66683100.00 | 133100.00 | 66683100.00 | 2 | 4 | 0.00 | yes |
| HK/INDIRECT | 266200.00 | 40196200.00 | 266200.00 | 40196200.00 | 1 | 2 | 0.00 | yes |

**Best candidate** {'HOLD': 'SG', 'exit_route': 'INDIRECT'}: lo 0.00 / hi 39930000.00.

## Tax items of the best candidate (flow / jurisdiction / levy / bearer / amount / basis)

lower bound:
- reorg · CN · stamp · payee · 0.00 · cn.stamp.seller
- reorg · CN · stamp · payer · 0.00 · cn.stamp.buyer
- exit · SG · stamp · payer · 532400.00 · sg.stamp.buyer

upper bound:
- reorg · CN · stamp · payee · 0.00 · cn.stamp.seller
- reorg · CN · stamp · payer · 0.00 · cn.stamp.buyer
- exit · SG · stamp · payer · 532400.00 · sg.stamp.buyer
- exit · SG · income · payee · 39930000.00 · sg.gain.base, sg.gain.charge

## Pending facts (by the cost of losing them)
- 0.00  ('sg.gain.charge', 'exit')  payee.fixed_place_in_sg
- 0.00  ('sg.gain.s13w.group', 'exit')  hold:ULT>HOLD.since
- 0.00  ('cn.indirect.reorg', 'exit')  flow.intragroup_reorg_ratio, flow.later_cn_tax_not_reduced, flow.reorg_consideration_in_equity
- 0.00  ('sg.gain.base', 'exit')  flow.cost_basis
- 0.00  ('cn.resident.gain.base', 'exit')  flow.cost_basis
- 0.00  ('data.p2_scope', 'SG')  group.group_revenue_eur
- 0.00  ('data.p2_tcsh', 'SG')  group.p2_cbcr_pbt_sg, group.p2_cbcr_revenue_sg, group.p2_cbcr_simplified_taxes_sg, group.p2_eur_rate, group.p2_qualified_cbcr_sg, group.p2_tcsh_history_sg
- 0.00  ('data.p2_dm', 'SG')  group.p2_dm_avg_income_eur_sg, group.p2_dm_avg_revenue_eur_sg

## Pending conditions: plan items and discretion items (by cost)
- 0.00  ('sg.gain.capital', 'exit')  payee.gain_is_capital_in_nature
- 0.00  ('sg.gain.s13w', 'exit')  flow.holding_months:ge
- 0.00  ('sg.gain.s13w.group', 'exit')  flow.holding_months:ge
- 0.00  ('cn.residence.pem', 'HOLD')  HOLD.managed_from:not_cn

## Fields the rules read but the case does not give (44)
- exit  flow.arms_length_value
- exit  flow.as_at
- exit  flow.assessment_notice_on
- exit  flow.asset_disposed_within_2y
- exit  flow.clawback_event_within_2y
- exit  flow.cn_asset_ratio
- exit  flow.cn_cost_basis
- exit  flow.cn_income_ratio
- exit  flow.cn_value_ratio
- exit  flow.cost_basis
- exit  flow.foreign_tax_lower_than_cn
- exit  flow.holding_months
- exit  flow.intragroup_reorg_ratio
- exit  flow.later_cn_tax_not_reduced
- exit  flow.limited_functions_and_risks
- exit  flow.period_to
- exit  flow.reorg_acquired_ratio
- exit  flow.reorg_buyer_resident_in_cn
- exit  flow.reorg_consideration_in_equity
- exit  flow.reorg_control_ratio
- exit  flow.reorg_equity_payment_share
- exit  flow.reorg_filed
- exit  flow.reorg_horizon_years
- exit  flow.reorg_operations_unchanged_12m
- exit  flow.reorg_shares_kept_12m
- exit  flow.sg_group_ratio
- exit  flow.shares_cancelled
- exit  flow.stamp_relief_claimed
- exit  payee.fixed_place_in_sg
- exit  payee.ucmt_location
- exit  payer.ucmt_location
- reorg  flow.arms_length_value
- reorg  flow.assessment_notice_on
- reorg  flow.cn_cost_basis
- reorg  flow.payable_on
- reorg  flow.remitted_on
- reorg  flow.reorg_equity_payment_share
- reorg  flow.reorg_filed
- reorg  flow.reorg_operations_unchanged_12m
- reorg  flow.shares_cancelled
- reorg  flow.tax_paid_on
- reorg  flow.tax_paid_or_secured
- reorg  payee.ucmt_location
- reorg  payer.ucmt_location
