<a id="b场景识别动态追问与对话兜底"></a>

# B: Scenario Identification, Dynamic Follow-Ups, and Conversational Fallbacks

Design: 2026-10-02; implementation/validation completed 2026-10-03. This describes engineering behavior, not tax gold standards. A owns pages, B the contract/orchestration, C sources/retrieval. Advisors intervene only at final review.

<a id="1-github-核查范围与发现"></a>

## 1. GitHub audit scope and findings

Fetched both remote branches: `Zhihong-Wu@7054c45323abf7d63d9725f03f81dab892c98110` and `main@8974ee78332749eda5c444823399ceca7f184fa9`. Checked structure, PRD, two workflow reviews, dictionary, 6 rules, 8 evidence classes, 10 synthetic cases/natural-language examples, evaluators, and page/API/extraction entry points. Dictionaries, rules, evidence, and synthetic cases match across branches.

Key sources: `packages/contracts/fact_dictionary/hk_fsie_fact_fields.v0.json`, `knowledge/hong_kong/fsie/rules.json`, `knowledge/hong_kong/fsie/evidence_requirements.json`, `packages/rule_engine/evaluators.py`, `tests/fsie/candidate_cases.json`.

- Of the original 43 fields, `expert_decision_status` is a system/final-advisor field, not ordinary user input. B's existing `recipient_type` supplies individual/company routing.
- Dictionary `blocking_level`, rule `required_facts`, and actual evaluator reads do not fully agree. Running code does not establish sufficient facts. The income node primarily reads income_type; that alone cannot establish source character.
- `source_analysis`, `income_legal_character`, `hk_adequate_employees`, etc. involve judgment. Users supply statements/materials; saying “adequate/exempt” cannot automatically establish legal conclusions.
- Public legislation/reference cases cannot fill users' transaction facts. Identifying candidate scenarios/retrieval scope does not match a case with identical legal outcomes.

<a id="2-先识别再按任务补充"></a>

## 2. Identify first, then collect by task

| Layer | User-side information | Purpose/boundaries |
|---|---|---|
| Entry | Ordinary chat / source inquiry / current case analysis | Chat does not retrieve; identifier queries do not require full case interviews; clarify rules versus own circumstances when unclear |
| Candidate scenario | recipient_type, income_type, analysis_jurisdiction, consultation_goal | Identify recipient, income, analyzed side/jurisdiction, and objective; collect missing items only. Do not infer jurisdiction from currency/language/company name |
| Basic applicability | payer_jurisdiction, entity_hk_business_status, group_structure_description, income_event_status, accrual_date, payer_entity | Business/group/occurred-versus-planned/period descriptions; group statements do not establish MNE eligibility. Aliases suffice; no real names/accounts required |
| Receipt | bank_or_account_path, receipt_date, set_off_or_clearing_arrangement, cash_pool_arrangement, payment_on_behalf_arrangement | Ask actual paths/arrangements, not users' legal conclusions on deemed Hong Kong receipt |
| Participation | direct_or_indirect_holding, holding_percentage_pct, continuous_holding_period_months, investee_entity, foreign_tax_description, commercial_rationale | Current-path requirements only; tax qualification/main purpose remain final judgments |
| Substance | entity_activity_profile, hk_staff_description, hk_premises_description, hk_operating_expenditure_amount/currency, strategic_decision_making_location, outsourcing_and_supervision | Ask duties, premises use, activities, not whether legal adequacy is satisfied |
| Supporting materials | Amount/currency, residence, acquisition date, underlying profits, inventories, etc. | Collect by question/rule dependencies, not universal entry gates; amount does not block candidate identification |

B adds objectives/jurisdiction, payer jurisdiction, occurred/planned, group/staff/premises/foreign-tax descriptions without changing C's original dictionary or adding unagreed filters. B extensions persist with cases; C retains the existing filter allowlist.

Specific payer jurisdiction, business, group, and dates support later determinations, not universal candidate-identification prerequisites. Identification establishes neither similar-ruling matches nor tax eligibility.

`identification.status` is collecting / candidate_identified / unsupported only. Unknown/conflicting/missing required fields prevent completion. Explicit individual/non-dividend/non-Hong Kong requests receive a scope explanation. “Hong Kong company” does not establish actual Hong Kong business.

<a id="3-追问状态机"></a>

## 3. Follow-up state machine

At most one main question, with `id、field、text、why、example、kind、attempt、based_on_revision`. B selects question text; the model parses messages into validated candidate facts/intents only.

Order: permissions/input → explicit revisions → current-task routing → task conflicts → missing identification fields → objective-specific facts → fact checks/gap notices → permitted evidence → draft → sole final advisor review.

- Do not reask concrete values. Save all supplied facts, then ask only one remaining item.
- unknown means explicit uncertainty; missing materials become deferred, never no. Industry retrieval cannot invent client facts.
- Display an item at most twice, explaining differently on the second attempt. Without an effective answer, offer other information / partial summary / pause. Silence advances nothing and is not consent.
- Immediately explain impacts/options when users cannot answer/provide material; do not force repeated questioning. Explicit partial-summary selection creates consent bound to the current fact snapshot; fact changes invalidate it.
- Partial summaries list knowns, unknowns, conflicts, and impacts, not confirmation, rule execution, or professional conclusions. Research with missing facts requires explicit partial-output consent.
- Ordinary chat/independent inquiries pause interviews while retaining pending. Resume on explicit continuation or clear factual supplementation. Isolated yes/unknown after pause does not bind old questions.
- For another case, direct users to A's new-conversation entry without overwriting the old case. No automatic cross-case task creation this round.

<a id="4-对话决策与兜底验收表"></a>

## 4. Conversation decisions and fallback acceptance

| Scenario | Trigger/priority | Action | Fallback/check |
|---|---|---|---|
| Greeting + correction | Explicit field correction/source span | Correct specified fact, retain history, invalidate old report | Authorization applies only to named fields; other differences remain conflicts |
| Different old/new values | No explicit correction evidence | Preserve previous/candidate, ask one question | No overwrite; old conflicts do not hijack independent chat/inquiries |
| Correction + inquiry | Recognizable revision/query | Save then retrieve | Failure retains facts, knowledge_unavailable, and retry query |
| Conflict + inquiry | Current factual conflict | Ask conflict first, save deferred_query | Restore inquiry after resolution; preserve second request |
| Unclear intent | Rules versus own case unclear | Ask one entry question | Do not assume individual/company inquiry; retain uncertainty |
| Unknown/no materials | Explicit response to current question | Mark unknown/deferred, explain impact/options | Never negative; attempt budget stops repetition |
| Objective change | Explicit receipt/participation/substance change | Adjust required queue | Do not ask obsolete fields |
| No evidence | C no_match | Explain query/period/coverage gaps | Does not establish nonexistent law; do not guess |
| Restricted/invalid sources | Permission/version/hash checks fail | Exclude material/claims | Check display/model rights separately; no historical leakage |
| Model failure | Call/structure failure | Technical error, no candidate writes | Preserve case/input for retry |
| Retrieval failure | Safe bounded retries exhausted | Pure queries error; mixed tasks save facts and disclose query failure | No Mock fallback or fake no_match |
| Judgment | Eligibility/adequacy/main purpose | Collect originals, queue final judgment | No intermediate advisor stage |

<a id="5-开发顺序与验收边界"></a>

## 5. Implementation order and acceptance boundaries

1. Central follow-up policy/auditable missing-field calculation replaces fixed order.
2. Extend parsing compatibly with original four-field responses, current-question context, constrained corrections/actions.
3. Persist dialogue / pending / deferred_query / partial_consent through LangGraph; retain idempotency/optimistic locking.
4. Return question/identification/dialogue and clear errors through existing JSON/SSE. A avoids duplicate questions.
5. Synthetic multi-turn regression for unknowns, unanswered items, unavailable evidence, corrections/conflicts, mixed requests, switch/resume, cross-case boundaries, partial consent, failures, permissions/citations; build/browser walkthroughs.

Controlled parsers/Mock retrieval test engineering. Actual model understanding, C, and professional rules require separate acceptance. Passing does not establish reliable tax conclusions. The historical 47-rule configuration remains a design baseline; this implements dialogue policy, not the entire general DSL.

<a id="6-本轮落地接口与兼容方式"></a>

## 6. Implemented interfaces and compatibility

Retain A's `/api/cases/{id}/messages`, `/facts`, `/confirm`, `/analyze`; additions appear in complete Case returns with one workflow for JSON/SSE done. The chat catalog now has 53 items but one question per turn. See the [field audit](B_USER_FACT_FIELD_AUDIT_2026_10_02.md).

| Field | Meaning | A consumption |
|---|---|---|
| Case.identification | Candidate status/missing entry fields, not eligibility | Progress, never confirmed exemption |
| Case.fact_gaps | All unresolved objective fields/impacts | On-demand panel, not simultaneous questions |
| Case.dialogue | policy_version, status, pending, attempts, deferred, deferred_query, partial_consent | Persist with case; A does not rewrite |
| Message.question | id/kind/field/text/why/example/attempt/based_on_revision | Latest main question; choice/mode have no fact field |
| Message.guided | Complete follow-up/summary text included this turn | Suppress old generic question/list duplication |
| Message.question_fields | Legacy compatibility | Retain list; question/message body authoritative |
| workflow.status/reason_code | Business status/cause | waiting_user, paused, partial_ready, unsupported, partial_failure, etc. |
| workflow.retrieval_reason_code | Retains query result cause when follow-up resumes | status=waiting_user/reason_code describe questioning; research/this field retain retrieval outcome |
| workflow.error_code/retryable | Mixed-task technical failure | Show saved progress/retryable query, not unsent message |
| research.error | Error category/retryable, no connection/raw exceptions | TIMEOUT/HTTP_ERROR/INVALID_RESPONSE, etc. |

`partial_confirmation_required` is a business 422: explicitly choose partial summary in chat (exact English command `partial summary`), then check/confirm facts and analyze. Confirmation and gap acceptance are separate. Partial drafts retain intake_gaps, identification, partial_output_authorized; missing items set evidence_gate=insufficient and prevent final approval.

C receives only agreed `KnowledgeProvider` requests/five fact_filters; no unagreed B descriptions. Independent queries omit case facts. applicable_date requires both a known date and explicit planned/occurred status; otherwise date_status=unknown, not a verified applicable version.

<a id="7-裁定研究卡暴露的建模补充"></a>

## 7. Modeling additions from ruling cards

Review of 4 cards in `knowledge/hong_kong/fsie/ruling_research_cards.json` added `dividend_form` and `transaction_flow_description`. Cash/noncash queues differ; share distributions are not bank transfers. Corporate profit and dividend withholding taxes remain separately described in foreign_tax_description by tax/period/evidence, not collapsed into one qualifying rate.

This round did not alter model_input_authorized=false, inject the cards into runtime prompts, or treat them as user facts. B lacks a multi-entity graph/per-tax calculator; text preserves materials for final review.

<a id="8-追问示例合成对话"></a>

## 8. Synthetic follow-up examples

1. “A Hong Kong company receives dividends from a Singapore subsidiary; check participation conditions.” → record company/dividend/Hong Kong/participation/payer jurisdiction; no amount question or inferred actual Hong Kong business.
2. Ask only whether the recipient actually conducts business in Hong Kong, explaining incorporation versus operation; proceed from known information.
3. “Unknown, no materials yet.” → save unknown/deferred, explain suspended judgments, offer other information/partial summary/pause.
4. “Show a partial summary first.” → list statements/gaps and bind consent to this snapshot; confirmation permits an incomplete research draft, still requiring final review.
5. “The amount was wrong; it should be 200. Also check the rules.” → if clearly attributable, update/history then retrieve; failure preserves amount/query and supports retry retrieval.
6. “Hello.” → chat while retaining pending; explicit case continuation resumes. Isolated yes after pause never affirms the old question automatically.

<a id="9-当前限制"></a>

## 9. Current limitations

- Engineering policy, not measured live recognition/tax correctness. Exact controls/current enum answers can be handled directly; free-form scenarios, facts, corrections need model parsing/validation and frozen-set live testing.
- Follow-ups are primarily Chinese. A's bilingual UI/labels remain, but complete English questions/partial-summary wording is outstanding. UI switching does not translate all history.
- Advisors intervene only finally. User eligibility/adequacy/tax statements remain candidates; complete descriptions do not validate evidence.
- One current case, main question, and deferred_query. Parallel transactions/independent queries require separate cases or later queues, never automatic transaction merging.

<a id="10-实现验收记录"></a>

## 10. Implementation acceptance record

- Python, 2026-10-03: `pytest -q -m 'not integration'`, 199 passed / 11 integration deselected; 42 dynamic-interview tests include post-answer state consistency.
- Browser: all 20 existing/new tests passed. Initial failures concerned old text/hardcoded ports and Chrome startup timing; revised assertions passed retests. Latest interview/conflict/partial-draft 3 passed again on isolated 8011/5184.
- TypeScript/Vite: `npm run build` passed.
- Manual service: backed-up synthetic database retains its 1 original case; 8001 API updated; 5174 frontend address retained.
- No actual C, live model quality, PostgreSQL integration, or professional tax acceptance. Synthetic tests are not tax gold standards.
