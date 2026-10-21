# Plan: Demo 1 - Singapore loan to Hong Kong (template recorded)

**Structure**: the only structure

**Scope**: income tax only. VAT, GST, stamp duty, customs duty, land appreciation tax, deed tax and property tax are not assessed; a case or a structure that attracts one of them is not handled.

## Strategies

The rulings answered "unknown" fork the plan. Sorted by guaranteed tax, lowest first; the last row (baseline) takes every open ruling against the taxpayer. A row's rulings are branch labels, not assumptions: resolve one in practice, answer yes / no, and reassess; if it fails, use the fallback row.

| # | Guaranteed | Best case | Structure | Rulings taken as favourable on this path | Fallback |
|---|---|---|---|---|---|
| 1 | 42500.00 | 1250.00 | the only structure | none (baseline) | — |

### Strategy #1: guaranteed 42500.00 (baseline)

#### Implementation plan

**Aim and result:** Settle the tax on SGD 250,000.00 interest from Marlow Holdings Limited to Marlow Capital Pte. Ltd. at the lowest amount the facts support. Conservative tax: SGD 42,500.00 (Singapore income tax SGD 42,500.00).

The recorded arrangement is retained. Alternative structures were not compared; this plan implements and resolves the entered transactions. Scope: income tax only; VAT, GST, stamp duty, customs duty and property taxes are not assessed. This window shows strategy #1 of the list; the other strategies are the alternatives.

| Jurisdiction | Conservative | If treatments are supported | Made up of |
|---|---|---|---|
| Hong Kong | 0.00 | -41,250.00 | — |
| Singapore | 42,500.00 | 42,500.00 | Singapore income tax SGD 42,500.00 |

Status: conditional. Assessment date: 2026-10-20. Currency: SGD.

Ready for review means the workpack is generated. It does not mean documents have been approved, filings submitted, taxes paid or authority acceptance obtained.

**This strategy's path: SGD 42,500.00.** The guaranteed tax of this strategy, with its rulings taken as the list says. Verify the liability and actual payments before filing.

##### Phase 1. Establish the facts behind each payment

###### 1. Prepare the financing and interest file

Why: The conservative tax on this payment is Singapore income tax SGD 42,500.00; every later step relies on these facts.

Owner: Marlow Capital Pte. Ltd. finance, with Marlow Holdings Limited finance. Status: todo.

Marlow Holdings Limited pays Marlow Capital Pte. Ltd. SGD 250,000.00 for interest on 2026-12-31. Match the interest to the borrowing period, loan purpose, rate and contractual allocation of withholding tax.

Evidence: Loan agreement and interest schedule; Use of funds and lender details; Interest benchmark and related-party pricing support

Completion: A reconciled transaction workpaper with the supporting documents and a named reviewer.

###### 2. Obtain the facts answered Unknown

Why: Unknown facts are taken at their least favourable value, so they hold the conservative estimate up until a supported answer replaces them.

Owner: Assessment owner's tax lead. Status: conditional.

Obtain supporting records for: annual taxable income outside the case's flows (may be negative: the company's own loss; decision D51); whether the Singapore foreign tax credit pooling election is made; the source jurisdiction's statutory corporate income tax rate for resident enterprises; not a withholding, treaty or non-resident rate. Until supported answers are entered and reassessed, keep these facts Unknown and retain the conservative treatment.

Evidence: annual tax return; Singapore tax return; source jurisdiction's tax law

Completion: Each available fact has a reviewed source and the assessment is rerun; unavailable facts remain explicitly Unknown.

After steps: 1

##### Phase 2. Settle the treatments that move the tax

###### 3. Resolve the outstanding tax treatment

Why: Decides whether the expense was incurred in the production of assessable profits. On its own it does not lower the conservative estimate; it matters together with the other open treatments.

Owner: Marlow Holdings Limited tax lead and tax adviser. Status: conditional.

Prepare a supported position on: whether the expense was incurred in the production of assessable profits. Record the conclusion and any authority response.

Evidence: evidence of the purpose of the expense; Written treatment analysis and any relevant authority correspondence

Completion: A reviewed treatment memo with evidence; any required authority acceptance is recorded separately.

After steps: 1

Rule references: hk.deduct.interest

##### Phase 3. File, pay and reconcile

###### 4. Confirm the Hong Kong position

Why: No Hong Kong tax on the conservative basis. If the open treatments are supported, SGD -41,250.00 arises here (Hong Kong income tax SGD -41,250.00).

Owner: Marlow Holdings Limited finance and local tax adviser. Status: todo.

Reconcile the transaction income, costs, taxes and any credit with the local accounts and actual payment evidence. Use the conservative position for unresolved treatment; verify credit entitlement separately from proof that tax was paid.

Evidence: Transaction tax workpaper and local return; Income and expense ledger; Foreign tax assessment and receipts, if a credit is claimed

Completion: The local return position, reserve and any permitted credit are approved by the responsible reviewer.

After steps: 1, 3

Rule references: hk.deduct.interest, hk.tp.corresponding, hk.tp.deduction_cap

###### 5. Settle the Singapore tax: SGD 42,500.00

Why: Conservative Singapore tax: Singapore income tax SGD 42,500.00.

Owner: Marlow Capital Pte. Ltd. finance and local tax adviser. Status: todo.

Reconcile the transaction income, costs, taxes and any credit with the local accounts and actual payment evidence. Use the conservative position for unresolved treatment; verify credit entitlement separately from proof that tax was paid.

Evidence: Transaction tax workpaper and local return; Income and expense ledger; Foreign tax assessment and receipts, if a credit is claimed

Completion: The local return position, reserve and any permitted credit are approved by the responsible reviewer.

After steps: 1, 3

Rule references: sg.fsie.charge, sg.ftc.unilateral, sg.onshore.charge, sg.tp.income_uplift

##### Phase 4. Record and close

###### 6. Approve the workpack and keep the audit trail

Why: Closes the plan: who decided what, on which evidence, and what remains open.

Owner: Assessment owner's finance lead. Status: todo.

Assign each work item, review the conditional decisions and reserve, and retain contracts, computations, approvals and submission receipts. Rerun the assessment when a material fact or treatment changes.

Evidence: Reviewed transaction workpapers; Signed decision log; Filing acknowledgements and payment receipts, where applicable

Completion: The responsible reviewer signs the workpack; unresolved treatments and remaining actions are explicitly recorded.

After steps: 4, 5

##### Conditional decisions

- whether the expense was incurred in the production of assessable profits: if supported, record the conclusion and reassess; on its own this does not change the conservative estimate. Otherwise: Keep the conservative treatment and its reserve; do not record an unapproved saving.

Condition impacts may overlap and must not be added as separate savings.

##### This path

Rulings taken as favourable on this path: none: every open ruling taken against the taxpayer.


**Guaranteed tax of the baseline** (every discretion item unfavourable, unknown data unfavourable): 42500.00; **best case** (every discretion item favourable): 1250.00.

## Summary by region

| Region | Guaranteed tax | Best case | Actions | Deadlines | Conditions pending the authority's acceptance |
|---|---|---|---|---|---|
| HK | 0.00 | -41250.00 | 0 | 0 | 1 |
| SG | 42500.00 | 42500.00 | 0 | 0 | 0 |

## HK

Conditions still depending on the tax authority's acceptance:
- whether the expense was incurred in the production of assessable profits (MARLOW_HOLDINGS_LIMITED.incurred_in_production_of_profits, rule hk.deduct.interest)

## SG

Tax items (guaranteed):
- payment_1 · SG · income · borne by MARLOW_CAPITAL_PTE_LTD · 42500.00 · sg.ftc.unilateral, sg.onshore.charge, sg.tp.income_uplift

## Structure details
- company MARLOW_CAPITAL_PTE_LTD · SG · existing
- company MARLOW_HOLDINGS_LIMITED · HK · existing
- holding MARLOW_HOLDINGS_LIMITED → MARLOW_CAPITAL_PTE_LTD · 100% · stated by the case
- flow payment_1 · INTEREST · MARLOW_HOLDINGS_LIMITED → MARLOW_CAPITAL_PTE_LTD · 250000.00 · 2026-12-31

## Answers used
- group.group_revenue_eur = 20000000 (Marlow Holdings consolidated accounts 2025)
- MARLOW_HOLDINGS_LIMITED.taxable_income_other = unknown
- MARLOW_CAPITAL_PTE_LTD.ftc_pooling_election = unknown
- flow:payment_1.foreign_headline_rate = unknown
- flow:payment_1.foreign_taxed = False (no Hong Kong tax was withheld (loan agreement; bank advice))
- flow:payment_1.receipt_kind = REMITTED (loan agreement: paid to the Lender's bank account in Singapore)
