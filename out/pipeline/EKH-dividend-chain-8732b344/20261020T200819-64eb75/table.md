# Result: template recorded, subject GROUP, event {'on': '2026-06-30', 'as_at': '2026-10-20'}

Assumptions / gaps noted in the case file:
- Assessment of the recorded companies and dated transactions; no alternative structure is inferred.
- 2 fields read by qwen3.8-flash from client_description-8a9715dee41b (2026-10-20, prompt 2026-10-15-en); quotes verified verbatim, numbers and dates parsed by the program from the quote; 0 conflicts and 0 constraint violations left unfilled; a person must review before use, then run tax_graph.verify.casecheck.
- review: confirmed as read
- reviewed by a person (2026-10-20, 0 items applied from review.json)

## Candidate table (group total tax lo / hi; subject share; discretion count, plan item count, fragility)

| Candidate | lo | hi | share@lo | share@hi | Discretion | Plan items | Fragility | Dominated |
|---|---|---|---|---|---|---|---|---|
| the only structure | 0.00 | 670000.00 | 0.00 | 670000.00 | 4 | 2 | 100000.00 |  |

**The only structure**: lo 0.00 / hi 670000.00 (no structural variable; the conclusions lie in the pending items and the settled tax items).

## Tax items of the best candidate (flow / jurisdiction / levy / bearer / amount / basis)

lower bound:
- payment_1 · CN · income · payee · 100000.00 · cn.reinvest.deferral, cn.wht.reduced

upper bound:
- payment_1 · CN · income · payee · 100000.00 · cn-hk.div.cap_other@cn, cn-hk.div.cap_qualified@cn, cn.wht.reduced
- payment_1 · HK · income · payee · 230000.00 · hk.fsie.charge, hk.ftc.dta
- payment_2 · SG · income · payee · 340000.00 · sg.fsie.charge, sg.ftc.unilateral

## Pending facts (by the cost of losing them)
- 100000.00  ('cn.reinvest.deferral', 'payment_1')  flow.direct_payment, flow.reinvested_in_cn, flow.reinvestment_form, flow.reinvestment_from_distributed_profit
- 100000.00  ('cn.reinvest.recapture', 'payment_1')  flow.reinvestment_withdrawn
- 0.00  ('hk.fsie.charge', 'payment_1')  flow.receipt_kind
- 0.00  ('hk.fsie.substance.dividend', 'payment_1')  payee.pure_equity_holding, payee.substance_ruled_adequate
- 0.00  ('hk.fsie.participation.dividend', 'payment_1')  flow.deductible_at_payer, flow.foreign_headline_rate, flow.foreign_taxed, flow.underlying_profits_taxed
- 0.00  ('sg.fsie.charge', 'payment_2')  flow.receipt_kind
- 0.00  ('sg.fsie.exempt', 'payment_2')  flow.foreign_headline_rate, flow.foreign_taxed
- 0.00  ('sg.ftc.pooling', 'payment_2')  flow.foreign_headline_rate, flow.foreign_taxed, payee.ftc_pooling_election
- 0.00  ('data.p2_scope', 'HK')  group.group_revenue_eur
- 0.00  ('data.p2_scope', 'SG')  group.group_revenue_eur
- 0.00  ('data.p2_scope', 'CN')  group.group_revenue_eur
- 0.00  ('cn.reinvest.credit', 'payment_1')  flow.direct_payment, flow.investee_encouraged_industry, flow.reinvested_in_cn, flow.reinvestment_form
- 0.00  ('data.p2_tcsh', 'HK')  group.p2_cbcr_pbt_hk, group.p2_cbcr_revenue_hk, group.p2_cbcr_simplified_taxes_hk, group.p2_eur_rate, group.p2_qualified_cbcr_hk, group.p2_tcsh_history_hk
- 0.00  ('data.p2_dm', 'HK')  group.p2_dm_avg_income_eur_hk, group.p2_dm_avg_revenue_eur_hk
- 0.00  ('data.p2_income', 'BEST_CHINA_DEVELOPMENT_L')  group.group_revenue_eur
- 0.00  ('data.p2_tcsh', 'SG')  group.p2_cbcr_pbt_sg, group.p2_cbcr_revenue_sg, group.p2_cbcr_simplified_taxes_sg, group.p2_eur_rate, group.p2_qualified_cbcr_sg, group.p2_tcsh_history_sg
- 0.00  ('data.p2_dm', 'SG')  group.p2_dm_avg_income_eur_sg, group.p2_dm_avg_revenue_eur_sg
- 0.00  ('data.p2_income', 'EKH_LIMITED')  group.group_revenue_eur
- 0.00  ('data.p2_tcsh', 'CN')  group.p2_cbcr_pbt_cn, group.p2_cbcr_revenue_cn, group.p2_cbcr_simplified_taxes_cn, group.p2_eur_rate, group.p2_qualified_cbcr_cn, group.p2_tcsh_history_cn
- 0.00  ('data.p2_dm', 'CN')  group.p2_dm_avg_income_eur_cn, group.p2_dm_avg_revenue_eur_cn
- 0.00  ('data.p2_income', 'SHANGHAI_ANXIN_RONG_CHEN')  group.group_revenue_eur

## Pending conditions: plan items and discretion items (by cost)
- 100000.00  ('cn.gaar', 'payment_1')  payee.reasonable_commercial_purpose_absent
- 0.00  ('hk.fsie.substance.dividend', 'payment_1')  payee.adequate_substance, payee.registration_filing_compliant:is_true
- 0.00  ('hk.fsie.participation.dividend', 'payment_1')  payee.no_main_purpose_of_tax_benefit
- 0.00  ('sg.fsie.exempt', 'payment_2')  payee.exemption_beneficial
- 0.00  ('cn.reinvest.credit', 'payment_1')  flow.planned_holding_months:ge

## Settled tax items: recoverable / shortfall risk / routes
- payment_1/CN: closed (every clock has run out, or declared); no claim

## Fields the rules read but the case does not give (35)
- payment_1  flow.assessment_notice_on
- payment_1  flow.capitalised_from
- payment_1  flow.deductible_at_payer
- payment_1  flow.determination_on
- payment_1  flow.direct_payment
- payment_1  flow.dividend_from_pre_reorg_profits
- payment_1  flow.first_notification_on
- payment_1  flow.foreign_headline_rate
- payment_1  flow.foreign_tax_rate
- payment_1  flow.foreign_taxed
- payment_1  flow.receipt_kind
- payment_1  flow.reinvested_in_cn
- payment_1  flow.reinvestment_form
- payment_1  flow.reinvestment_from_distributed_profit
- payment_1  flow.reinvestment_withdrawn
- payment_1  flow.reinvestment_withdrawn_on
- payment_1  flow.remitted_on
- payment_1  flow.reorg_same_residence
- payment_1  flow.subject_income_taxed_abroad
- payment_1  flow.tax_paid_on
- payment_1  flow.underlying_profits_taxed
- payment_1  payee.bo_safe_harbour
- payment_1  payee.pure_equity_holding
- payment_1  payee.registration_filing_compliant
- payment_1  payee.residence_cert
- payment_1  payee.substance_ruled_adequate
- payment_1  payee.ucmt_location
- payment_1  payer.ucmt_location
- payment_2  flow.assessment_notice_on
- payment_2  flow.foreign_headline_rate
- payment_2  flow.foreign_tax_rate
- payment_2  flow.foreign_taxed
- payment_2  flow.receipt_kind
- payment_2  payee.ucmt_location
- payment_2  payer.ucmt_location
