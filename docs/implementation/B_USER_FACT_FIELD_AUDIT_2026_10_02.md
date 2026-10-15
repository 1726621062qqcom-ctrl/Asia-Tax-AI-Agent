<a id="用户侧字段核查表github-基线--b-扩展"></a>

# User-Facing Field Audit (GitHub Baseline + B Extensions)

Audit date: 2026-10-02. The original repository has 43 fields. B exposes 42 candidate fields, excluding expert_decision_status, plus 11 B fields, for 53 total. This is not a form requiring every field.

Original fields are from `Zhihong-Wu@7054c45`, matching the dictionary/rules at `main@8974ee7`. See [follow-up design](B_GUIDED_INTAKE_DESIGN_2026_10_02.md) for sources.

<a id="原有字段逐项对应"></a>

## Original field mappings

User-side information means user descriptions/authorized materials, not facts invented from C legislation/reference cases. Judgment statements remain candidates; user fact confirmation is not professional approval. Fields unnecessary for entry may still block specific nodes.

| Field | Meaning | Source/use | Original required_facts | Required for candidate identification? |
|---|---|---|---|---|
| `entity_hk_business_status` | Whether the recipient carries on a trade, profession, or business in Hong Kong | User facts/materials; remain missing if absent | scope | No |
| `mne_group_status` | Whether the entity belongs to an MNE group covered by FSIE | User statements/materials; legal eligibility/adequacy remains for final judgment, not a conclusion requested from the user | scope | No |
| `regulated_financial_entity_status` | Whether the regulated financial entity exclusion applies (decision step 4) | User statements/materials; legal eligibility/adequacy remains for final judgment, not a conclusion requested from the user | Not required by the current 6 rules | No |
| `pure_equity_holding_entity_status` | Pure equity-holding status, determining simplified economic substance requirements | User statements/materials; legal eligibility/adequacy remains for final judgment, not a conclusion requested from the user | economic_substance | No |
| `entity_tax_residency` | Entity tax residence | User facts/materials; remain missing if absent | Not required by the current 6 rules | No |
| `income_type` | Income class; the L0 vertical slice handles dividend only | User facts/materials; remain missing if absent | scope, income_characterisation | Yes |
| `income_legal_character` | Whether the income is foreign-sourced dividends within this framework | User statements/materials; legal eligibility/adequacy remains for final judgment, not a conclusion requested from the user | income_characterisation | No |
| `payer_entity` | Investee paying the dividend | User facts/materials; remain missing if absent | income_characterisation | No |
| `dividend_amount` | Numeric dividend amount; currency is in the paired field | User facts/materials; remain missing if absent | Not required by the current 6 rules | No |
| `dividend_currency` | Dividend currency, ISO 4217 | User facts/materials; remain missing if absent | Not required by the current 6 rules | No |
| `accrual_date` | Accrual date for selecting the effective rule version | User facts/materials; remain missing if absent | scope, income_characterisation | No |
| `underlying_profit_period` | Underlying profit period for the dividend | User facts/materials; remain missing if absent | income_characterisation | No |
| `source_analysis` | Income source analysis | User statements/materials; legal eligibility/adequacy remains for final judgment, not a conclusion requested from the user | income_characterisation | No |
| `receipt_location` | Whether received or deemed received in Hong Kong | User statements/materials; legal eligibility/adequacy remains for final judgment, not a conclusion requested from the user | receipt | No |
| `receipt_date` | Actual/deemed receipt date | User facts/materials; remain missing if absent | receipt | No |
| `bank_or_account_path` | Receipt account, cash pooling, fund path; replaces receipt_account | User facts/materials; remain missing if absent | receipt | No |
| `set_off_or_clearing_arrangement` | Set-off, clearing, or other deemed-receipt arrangements | User facts/materials; remain missing if absent | receipt | No |
| `cash_pool_arrangement` | Group cash pooling | User facts/materials; remain missing if absent | Not required by the current 6 rules | No |
| `payment_on_behalf_arrangement` | Payment-on-behalf arrangements | User facts/materials; remain missing if absent | Not required by the current 6 rules | No |
| `direct_or_indirect_holding` | Direct/indirect ownership relationship | User facts/materials; remain missing if absent | participation_basic | No |
| `investee_entity` | Investee entity, cross-checked against payer_entity | User facts/materials; remain missing if absent | participation_basic | No |
| `holding_percentage_pct` | Ownership percentage (0–100); replaces holding_percentage | User facts/materials; remain missing if absent | participation_basic | No |
| `continuous_holding_period_months` | Continuous ownership months before accrual | User facts/materials; remain missing if absent | participation_basic | No |
| `acquisition_date` | Share acquisition date for continuous holding calculations | User facts/materials; remain missing if absent | Not required by the current 6 rules | No |
| `beneficial_owner_status` | Beneficial owner status | User statements/materials; legal eligibility/adequacy remains for final judgment, not a conclusion requested from the user | Not required by the current 6 rules | No |
| `foreign_tax_on_dividend_or_underlying_profit` | Whether dividend/underlying profits bear qualifying similar foreign tax | User statements/materials; legal eligibility/adequacy remains for final judgment, not a conclusion requested from the user | participation_basic | No |
| `foreign_nominal_tax_rate_pct` | Foreign nominal rate compared with the 15% reference rate | User statements + C evidence for the tax/period; do not confuse with dividend withholding rates | Not required by the current 6 rules | No |
| `foreign_tax_jurisdiction` | Foreign taxing jurisdiction | User facts/materials; remain missing if absent | Not required by the current 6 rules | No |
| `underlying_tax_deductible_status` | Deductibility of underlying profit tax in the investee jurisdiction (anti-hybrid mismatch) | User facts/materials; remain missing if absent | Not required by the current 6 rules | No |
| `foreign_tax_credit_available` | Foreign tax credit switchover availability when participation exemption does not apply | User statements/materials; legal eligibility/adequacy remains for final judgment, not a conclusion requested from the user | Not required by the current 6 rules | No |
| `entity_activity_profile` | Core income-generating activities in Hong Kong | User facts/materials; remain missing if absent | economic_substance | No |
| `hk_adequate_employees` | Adequate qualified Hong Kong employees; adequacy requires human judgment | User statements/materials; legal eligibility/adequacy remains for final judgment, not a conclusion requested from the user | economic_substance | No |
| `hk_adequate_premises` | Adequate Hong Kong business premises | User statements/materials; legal eligibility/adequacy remains for final judgment, not a conclusion requested from the user | economic_substance | No |
| `hk_operating_expenditure_amount` | Hong Kong operating expenditure amount | User facts/materials; remain missing if absent | economic_substance | No |
| `hk_operating_expenditure_currency` | Operating expenditure currency | User facts/materials; remain missing if absent | Not required by the current 6 rules | No |
| `strategic_decision_making_location` | Strategic decision location | User facts/materials; remain missing if absent | economic_substance | No |
| `outsourcing_and_supervision` | Outsourcing and supervision in Hong Kong | User facts/materials; remain missing if absent | economic_substance | No |
| `hybrid_mismatch_arrangement` | Hybrid mismatch arrangements | User statements/materials; legal eligibility/adequacy remains for final judgment, not a conclusion requested from the user | Not required by the current 6 rules | No |
| `main_purpose_tax_benefit_flag` | Whether obtaining tax benefits is a main purpose; mandatory human judgment | User statements/materials; legal eligibility/adequacy remains for final judgment, not a conclusion requested from the user | participation_basic | No |
| `restructuring_near_income_date` | Restructuring close to accrual | User facts/materials; remain missing if absent | Not required by the current 6 rules | No |
| `commercial_rationale` | Commercial rationale | User facts/materials; remain missing if absent | Not required by the current 6 rules | No |
| `evidence_inventory` | Evidence inventory/statuses: provided/missing/conflict/not_applicable | User inventory + actual system receipts; claimed provision does not validate attachments | human_gate | No |
| `expert_decision_status` | Human/expert review status for the mandatory gate | Final advisor/system; chat and fact edits cannot write this | human_gate | No |

<a id="b-的补充输入与作用"></a>

## B extension inputs and roles

| Field | Meaning | Collection timing |
|---|---|---|
| `recipient_type` | Recipient type | Required for candidate scenario identification |
| `analysis_jurisdiction` | Jurisdiction analyzed in this inquiry | Required for candidate scenario identification |
| `consultation_goal` | Consultation objective | Required for candidate scenario identification |
| `payer_jurisdiction` | Payer jurisdiction | Later cross-border background checks; not an identification blocker |
| `income_event_status` | Occurred versus planned income | Collect as required by the current task |
| `group_structure_description` | Group members and operating jurisdictions | Collect as required by the current task |
| `hk_staff_description` | Hong Kong employee numbers and responsibilities | Collect as required by the current task |
| `hk_premises_description` | Hong Kong premises and usage | Collect as required by the current task |
| `foreign_tax_description` | Actual foreign taxation | Collect as required by the current task |
| `dividend_form` | Dividend payment form | Receipt branch distinguishes cash/in-kind; not a universal entry gate |
| `transaction_flow_description` | Noncash assets and transfer flow | Receipt branch distinguishes cash/in-kind; not a universal entry gate |

<a id="本轮保留的边界"></a>

## Retained boundaries

- Original required_facts differ from actual evaluator reads. Follow-ups have explicit task dependencies; error-free code does not establish complete facts.
- The 4 ruling cards highlight modeling gaps around noncash distributions, pooling/reinvestment, corporate/withholding taxes, and undisclosed staff counts. Do not transfer applicants’ facts into user cases.
- Noncash paths/tax descriptions are text within structured fields. There is no multi-entity graph, two-tax ledger, or automatic ruling applicability.
- File upload/parsing is outside this round’s A chat entry. User descriptions, candidates, and inventories do not establish that client evidence was read.
- C returns legislation, rules, versions, periods, display/model permissions, and coverage. Do not ask users which statutory version/hash to use.
- Retain list/unknown types; do not invent real company names, account numbers, rates, or transaction dates.
