<a id="b-模块agent-业务规则-v03"></a>

# Module B: Agent business rules v0.3

2026-10-02 Implementation update: The dialogue design of Sections 9 to 13 was refined and implemented by [Dynamic follow-up and fallback implementation specification](../implementation/B_GUIDED_INTAKE_DESIGN_2026_10_02.md). See [User-facing field audit](../implementation/B_USER_FACT_FIELD_AUDIT_2026_10_02.md) for the actual field source. The early "not yet implemented" description below is retained as design history, and the dialogue strategy for this round is subject to the new Section 14; not all 47 general rules are connected to the DSL executor.

| Item | Content |
|---|---|
| Date | 2026-10-02 |
| Status | Reviewable rule design + structured configuration draft; not yet connected to the business runtime |
| Basis | [Business process v0.3](AGENT_BUSINESS_WORKFLOW_V0_1.md), work week plan, [Product direction](../product/STRATEGIC_PRODUCT_PLAN.md) and existing environment policies |
| Scope of application | Initially applies to L0 synthetic cases for Hong Kong foreign-sourced dividend FSIE; the common workflow rules can be reused by subsequent rule packages |
| structured version | [agent_business_rules.v0.1.json](agent_business_rules.v0.1.json) covers BR-01~47; the new dialogue rules in this revision are designed based on sections 9~13, and have not yet been coded into this configuration. |

<a id="1-要解决的业务问题"></a>

## 1. Business problem to be solved

The agent should be able to determine: what the user is asking, how much is currently supported, what is missing that will affect the next step, which tool to call, when to wait, when a draft can be generated, and what should be recalculated after the advisor makes changes.

The long-term product goals include understanding real cross-border transactions and comparing a limited set of options. The currently validated analysis scope and deployment feature switches each constrain actual behavior. Mentioning a country does not mean that the country already has a rule package, and mentioning optimization goals does not mean that optimization tools can be called. The process rules themselves do not specify tax rates, shareholding thresholds, or tax-exempt status; these are provided by independent, versioned tax rule packages.

**The business workflow has one final advisor review stage.** Users can check records and supplement information in the interim; professional judgments are temporarily reserved for final review. In the end, the advisor can return the draft for revision, and the revised draft will still go back to the same review stage. User verification cannot automatically mark facts as professionally confirmed.

| business goals | Agent behavior constraints | Main rules |
|---|---|---|
| Decide early what can be done | Check scope and capabilities first, don’t ask the entire fact sheet first | BR-04～07 |
| Ask less and ask the key questions | Ask for facts required by the current node; do not recheck the same value and version. | BR-10～15、26～29 |
| Analyze with evidence | Actual retrieval, coverage verification, deterministic calculation, and node verification are executed in sequence. | BR-16～21 |
| You can still advance when you are stuck on a dispute point | Block dependencies only, continue standalone nodes | BR-09、19、22 |
| Output can be reviewed | Each claim has a fact/rule/source of law version, and gaps must not be omitted. | BR-25、32～37 |
| Cases can be resumed and maintained | Bind waiting, resumption, revision, and approval to specific versions | BR-26～29、38～47 |

<a id="2-典型业务场景"></a>

## 2. Typical business scenarios

The following are examples of product behavior and are not case-specific tax answers.

| User statements or events | What the agent should do | What can be output |
|---|---|---|
| “We have a foreign income, how much tax do we have to pay?” | First clarify the revenue type, involved entities/regions and transaction period; select the capability package before asking for node facts | Current scope, one major issue; tax amount not yet reported |
| "Hong Kong companies receive foreign-sourced dividends, help me analyze them." | Identify dividend issues; collect facts, retrieve evidence, execute rules, and validate each node | Internal research draft with basis, assumptions and gaps, awaiting final review |
| "We haven't paid any dividends yet, but we plan to operate it at the end of the year." | Distinguish between plan dates, projected values and actual facts; note applicable assumptions when future rules are uncertain | Conditional research results, do not treat the plan as having happened |
| "The contract says 1 million, and the receipt record is 800,000." | Mark amount conflicts and ask whether they are different batches, deductions or currencies, etc.; do not choose one side without clarification | Conflict explanation and information needed; independent decisions continue |
| "I don't know the holding period. Let's look at the existing information first." | Preserve unknowns; record the partial-draft scope explicitly selected by the user | Supportable partial results and gap list; suspend conclusions that depend on the holding period |
| "Help me compare which route is the most tax-saving among Mainland China, Hong Kong and Singapore." | Split each region and target; optimization is currently disabled and no ranking is performed; supported Hong Kong points continue | Clear scope of partial analysis, uncovered items, and follow-up data requirements |
| "We have employees and offices, do we meet the economic substance?" | Extract verifiable facts and organize the basis; professional adequacy is entered into the final to-be-judged list | Facts and supporting/limiting material, do not automatically assume conditions are met |
| “Can I pay less customs duties if it is transshipped through a third country?” | Identified as a goods/tariff subject; if there is no package, it means it is not covered and the dividend package is not applied. | Scope statement, final unified review |
| User uploads the same file/leaves the page | Deduplicate content and retain current issues and progress; leaving does not mean partial drafts are allowed | Recoverable case status |
| The advisor changes an amount at final review, or information changes during approval | Modify to generate a new version and recalculate; reject outdated approval | New review draft, then enter the final review |

Multi-entity transactions at least preserve ownership, contractual relationships, actual payments and goods flow respectively; each fact is bound to the entity/transaction and date. Entities or intermediate countries that are not provided cannot be added based on model reasoning. Only the scope is registered when the relevant capabilities are not enabled.

<a id="3-规则如何执行"></a>

## 3. How the rules are implemented

The structured configuration uses **first-match evaluation within each stage, in priority order**. Only one action is returned at a time. After the action is completed, the orchestrator enters the next stage or returns to the scheduler. Different nodes can make decisions separately, but the same case only displays one main issue or a set of related fact cards.

- Every external input, user reply, and final review action goes through admission first; the tool and data permissions still need to be rechecked every time the tool is executed.
- The smaller the number in the stage, the higher the priority. The fallback applies only when the fields are complete and the type and enumeration are legal.
- Missing fields, unknown enumerations, unknown stages, and tool returns that do not comply with the contract are configuration/technical errors; they cannot be treated as false or automatically hit "allow".
- `all` means all conditions are met, `any` means any one is met; `eq` is strictly equal, `in` means enumeration members; an empty `all` is a fallback match in a valid context. Do not perform natural language expressions or eval.
- Fields are generated by the server after reading permissions, versions, queues and tool results. The model only proposes candidate values and actions, and cannot self-report `access_allowed=true` or `report_validation=passed`.
- `outcome` in the configuration is the result of the orchestration decision and contains intermediate action states; it is not equivalent to the existing database enumeration. Persistent mapping must be implemented separately.

Minimum record of each decision: `decision_id / rule_id / config_version / case_id / issue_id / node_id / request_id / input_snapshot_id / action / reason / result / timestamp`. Identity and organization come from the authentication context; logs reference evidence IDs to avoid unnecessary duplication of case text.

Stage flow: admission → scope → node → evidence → result → aggregate. User events resume through `user_event`; technical failures enter `tool_error`. After aggregation authorizes a draft, proceed to `report`; enter `review` only after text validation passes. Version changes pass through `change` and return to the scheduler. BR-03 records an existing input-screening result; screening must happen before content is admitted to the model.

The above is the case analysis configuration path. The new dialogue entry is to select the general information reply or case path after admission; the general information reply does not directly apply the BR-18 running tax rule action. For details on the new rules, see Sections 9 to 13. Existing JSON cannot be declared as a complete chat agent configuration before ingress diversion is implemented.

<a id="4-完整决策表"></a>

## 4. Complete decision table

The concept fields in "conditions" are defined in Section 5 and JSON's `field_catalog`. Each stage is matched in the order listed below. The tool name is the proposed call contract, which cannot be understood to mean that the repository has already been implemented.

<a id="admission输入与权限"></a>

### admission: input and permissions

| No. | Trigger condition | Agent action | Output status |
|---|---|---|---|
| BR-01 Blocking of unauthorized requests | `access_allowed` = `false` | `block_request`: Keep the original case; do not expose unauthorized case details to the caller. | `blocked` |
| BR-02 The environment or input is unqualified | `data_allowed` = `false`; or `input_valid` = `false` | `block_invalid_input`: Block this processing and record restricted diagnosis; do not copy the original sensitive data to the audit log. | `blocked` |
| BR-03 Allow entry into business process | None of the aforementioned rules are hit at this stage (valid context) | `accept_input`: Read trusted case context; only pass approved content to subsequent models or tools. | `accepted` |

<a id="scope业务范围与能力"></a>

### scope: business scope and capabilities

| No. | Trigger condition | Agent action | Output status |
|---|---|---|---|
| BR-04 unclear scope | `capability` = `"need_scope"` | `ask_scope`: Only ask for enough range information to select the rule package; reuse the same version of unanswered questions. | `waiting_user` |
| BR-05 Request is entirely unsupported | `capability` = `"unsupported"` | `record_unsupported_scope`: Register all uncovered items; form a scope description after verification of summary and report, and do not output tax conclusions. | `scope_only` |
| BR-06 Request is partly supported | `capability` = `"partial"` | `split_supported_issues`: Continue supported issues, and mark other issues as unsupported; it is forbidden to describe partial conclusions as transnational complete conclusions. | `partial_scope` |
| BR-07 Request is within enabled scope | None of the aforementioned rules are hit at this stage (valid context) | `build_issue_nodes`: Create nodes and dependencies based on the capability package; the transaction plan and the facts that have occurred are modeled separately. | `scheduled` |

<a id="node事实与节点前置条件"></a>

### node: facts and node preconditions

| No. | Trigger condition | Agent action | Output status |
|---|---|---|---|
| BR-08 Dependency graph error | `dependency_state` = `"invalid"` | `stop_invalid_graph`: Record circular or non-existent node references; no substantive analysis draft can be generated until repaired. | `technical_error` |
| BR-09 The current node dependencies are not satisfied | `dependency_state` = `"blocked"` | `record_dependency_block`: Record the specific upstream and conditions, and call back to the scheduler to process the independent node. | `blocked_dependency` |
| BR-10 A question for the same version is already pending | `question_pending` = `true` | `reuse_pending_question`: Do not re-question; when new input appears, expired questions will be written off or replaced first, and then the current node will be evaluated. | `waiting_user` |
| BR-11 Conflict of Key Facts | `fact_gate` = `"conflict"` | `ask_conflict`: Displays conflicting values and sources, asking the user for clarification; does not automatically select sides based on the latest document or model confidence. | `waiting_user` |
| BR-12 Missing required facts | `fact_gate` = `"missing"` | `ask_required_fact`: Only the decisive information of the current node is supplemented; the amount, date, subject, etc. are unknown and cannot default to zero, today or no. | `waiting_user` |
| BR-13 Candidate extraction values need to be checked | `fact_gate` = `"needs_ack"` | `ask_fact_ack`: Provide the original text and fact cards; the user checks the bound fact version, and advisor_confirmed is not generated. | `waiting_user` |
| BR-14 Facts do not satisfy the operating policy | `fact_gate` = `"unusable"` | `record_fact_policy_gap`: Having a value or being checked by the user still does not mean it is operable; the running policy cannot be bypassed by improving the fact state. | `paused_gap` |
| BR-15 Facts are sufficient for preliminary analysis of this node | None of the aforementioned rules are hit at this stage (valid context) | `prepare_analysis_snapshot`: Freeze allowed facts and provenance; For explicit L0 research assumptions, create a separate snapshot and preserve the original candidate state. | `ready_for_sources` |

<a id="evidence检索与依据覆盖"></a>

### evidence: retrieval and basis coverage

| No. | Trigger condition | Agent action | Output status |
|---|---|---|---|
| BR-16 Retrieval or coverage has not yet been checked | `coverage` = `"not_checked"` | `retrieve_and_check`: Search by issue, subject, jurisdiction, tax type, transaction period and rule version, and check for exceptions and contrary materials. | `coverage_pending` |
| BR-17 There are gaps or conflicts in the basis | `coverage` belongs to `["gap", "stale", "conflict"]` | `record_source_gap`: Preserve specific gaps or conflicts; historical transactions can be used in their applicable historical versions, and the old release date itself does not mean expiration. | `paused_gap` |
| BR-18 Evidence satisfies the current execution policy | None of the aforementioned rules are hit at this stage (valid context) | `execute_rules`: Uses versioned rules and deterministic calculations; the model cannot self-populate tax rates or thresholds. | `execution_pending` |

<a id="result节点分析结果"></a>

### result: node analysis result

| No. | Trigger condition | Agent action | Output status |
|---|---|---|---|
| BR-19 Involving professional judgment | `node_result` = `"judgment"` | `collect_final_judgment`: Organize support/objection materials and pending issues; do not send advisors midway, and do not treat the condition as passed. | `pending_final_judgment` |
| BR-20 node output verification failed | `node_result` = `"invalid"` | `record_invalid_result`: Save the diagnosis and withdraw the conclusion; the independent node continues and is recalculated after the repair event arrives. | `paused_gap` |
| BR-21 Current node analysis completed | None of the aforementioned rules are hit at this stage (valid context) | `save_node_result`: Save conclusions, calculations, references and versions; return to the scheduler and cannot directly generate a full case report. | `completed` |

<a id="aggregate继续处理等待或出稿"></a>

### aggregate: continue processing, waiting or publishing

| No. | Trigger condition | Agent action | Output status |
|---|---|---|---|
| BR-22 Nodes can still advance | `runnable_nodes` = `true` | `schedule_next`: Schedule by scope-blocking items, conclusion-blocking items, supporting items, then node order and field name; do not spin on waiting nodes. | `analyzing` |
| BR-23 Awaiting user without permission for a partial draft | `waiting_questions` = `true`; and `partial_scope_covers_waits` = `false` | `save_and_wait`: The manuscript will not be published automatically when the user leaves or times out; the progress and current major issues will be retained. | `waiting_user_response` |
| BR-24 There are nodes with no clear destination | `all_nodes_accounted` = `false` | `stop_unaccounted_nodes`: Repair scheduling or complete node processing. These issues cannot be missed in the report. | `technical_error` |
| BR-25 A complete or partial draft can be prepared | None of the aforementioned rules are hit at this stage (valid context) | `freeze_and_draft`: Freeze all results, unknowns, conflicts, gaps and unsupported ranges; enter the report stage after generating the text. | `draft` |

<a id="user_event用户回答与恢复"></a>

### user_event: user response and recovery

| No. | Trigger condition | Agent action | Output status |
|---|---|---|---|
| BR-26 No reply or provide later | `user_event` belongs to `["no_reply", "later"]` | `preserve_wait`: Does not change the facts, does not presume consent; the scheduler can advance other independent nodes. | `waiting_user_response` |
| BR-27 User does not know | `user_event` = `"unknown"` | `record_unknown_offer_partial`: Save the unknown and ask whether to keep waiting or produce a partial draft; do not default the unknown to a failed condition. | `waiting_user` |
| BR-28 Explicitly Select Partial Drafts | `user_event` = `"partial"` | `record_partial_scope`: Record the user, time, issue/fact version and the gap range allowed to be retained; the relevant nodes are rescheduled after being suspended. | `reschedule` |
| BR-29 Supplement, check or correct | None of the aforementioned rules are hit at this stage (valid context) | `merge_versioned_answer`: After input check, write the idempotent key and expected version according to the request; clarify if the semantics are ambiguous; go to the change stage if it affects the judgment. | `reschedule` |

<a id="tool_error工具异常"></a>

### tool_error: tool exception

| No. | Trigger condition | Agent action | Output status |
|---|---|---|---|
| BR-30 Failure is safe to retry | `retryable` = `true`; and `budget_remaining` = `true`; and `safe_to_retry` = `true` | `bounded_retry`: Unify the budget count and back off; when the writing result is uncertain, check the execution record first. | `retry_scheduled` |
| BR-31 Failure cannot be retried further | None of the aforementioned rules are hit at this stage (valid context) | `record_tool_failure`: Keep tool errors and recovery conditions; timeout will not be interpreted as no applicable regulations, permission denial will not change the identity and try again. | `technical_error` |

<a id="report报告生成后校验"></a>

### report: Verification after report generation

| No. | Trigger condition | Agent action | Output status |
|---|---|---|---|
| BR-32 The draft input version is invalid | `snapshot_current` = `false` | `invalidate_and_reschedule`: Return to the impact analysis and recalculate the nodes that need to be updated; do not send the old text to the final review. | `invalidated` |
| BR-33 The text has not been verified after being generated or modified. | `report_validation` = `"not_checked"` | `validate_report`: Check actual text, figures, citation support, unknowns/hypotheses, scope, versions, sensitive data, and research marker. | `validation_pending` |
| BR-34 actual report verification passed | `report_validation` = `"passed"` | `submit_final_review`: Bind the text hash and input version package; this is where the only advisor review step is entered. | `pending_review` |
| BR-35 verification failed and can be revised | `repair_available` = `true` | `repair_and_revalidate`: By default, the same input snapshot can be automatically revised for up to two rounds; each new text must be re-verified, and the budget will not be reset for version increments. | `revision_pending` |
| BR-36 Revisions exhausted; simplified draft can still be attempted | `simplified_attempted` = `false` | `simplify_and_revalidate`: Only the supported range descriptions/gaps are retained; the simplified draft is also verified, at most once in each generation cycle. | `simplified_pending` |
| BR-37 Simplified draft still fails to verify | None of the aforementioned rules are hit at this stage (valid context) | `stop_report_submission`: Save the diagnosis and prohibit submitting failed drafts to the advisor to bypass verification. | `report_validation_failed` |

<a id="review唯一最终顾问复核"></a>

### review: the only final advisor review

| No. | Trigger condition | Agent action | Output status |
|---|---|---|---|
| BR-38 The version used for review has changed. | `snapshot_current` = `false` | `reject_stale_review`: Reject approval of the old version; retain review opinions but cannot automatically apply to new facts. | `invalidated` |
| BR-39 No advisory decision yet | `review_action` = `"waiting"` | `wait_final_review`: Continue to be reviewed when there is no advisor; it will not be automatically approved because the time has expired. | `pending_review` |
| BR-40 approved and scope of delivery allows | `review_action` = `"approve"`; and `release_allowed` = `true` | `approve_exact_version`: Recheck version/verify hash and permission within the transaction, save approval; L0 is still limited to internal research. | `approved` |
| BR-41 approved but delivery conditions not met | `review_action` = `"approve"` | `record_release_block`: Records decision attempts and blocking reasons; cannot increase release level through advisor click approval. | `pending_review` |
| BR-42 advisor Modifies Facts or Judgment | `review_action` = `"amend_facts"` | `apply_review_and_recompute`: Save the scope, reasons and sources of professional decisions; recalculate affected nodes, regenerate and verify, and return to the same final review stage. | `reschedule` |
| BR-43 advisor modifies report text | `review_action` = `"amend_text"` | `revise_text_and_validate`: Create a new text version and clear old approvals and verifications; if the facts/conclusions are actually changed, the recalculation branch must be changed. | `validation_pending` |
| BR-44 advisor requests additional information | `review_action` = `"request_data"` | `ask_review_question`: Establish specific user questions and retain review comments; add and then generate and verify. | `waiting_user_response` |
| BR-45 advisor unable to form an opinion | None of the aforementioned rules are hit at this stage (valid context) | `close_unapproved_review`: Keep the reasons and pending matters, end this round of review; it can be reopened if there is new material. | `unapproved` |

<a id="change事实与依据变化"></a>

### change: changes in facts and basis

| No. | Trigger condition | Agent action | Output status |
|---|---|---|---|
| BR-46 Changes impact existing analysis | `affected_results` = `true` | `invalidate_affected_results`: Reliance along facts/rules/sources to conclusions invalidates affected results, reports and approvals; original records retained. | `reschedule` |
| BR-47 Duplication of material or changes that do not affect the conclusion | None of the aforementioned rules are hit at this stage (valid context) | `reuse_valid_results`: Reuse valid results after checking content hashes and new evidence; do not check the same fact version repeatedly. | `resume` |

<a id="5-四个必须由程序落实的判断"></a>

## 5. Four decisions that must be enforced in code

<a id="51-当前节点的事实是否足够"></a>

### 5.1 Are the facts about the current node sufficient?

`fact_gate=ready` must meet the following requirements at the same time: the required fields of the current node have values and sources; the decisive conflict has been resolved; the extracted values have been verified as required and the versions are consistent; the time information for selecting the tax rule version is available; the unit, currency and entity/transaction ownership are clear; the fact state complies with the environment policy. The absence of a supporting field does not automatically block conclusions that do not rely on it. Confidence scores do not replace these conditions.

When checking the priority, first look at the blocking level, then the node order and field names; only the same field will be processed in order of conflict, missing, and unchecked. The fact has been checked but there is no authorization to run, it should be classified as unusable, and you cannot pretend that the authorization is completed by asking again.

The current run policy does not accept `client_statement` or `ai_candidate` directly. Under an explicit L0 policy, a research-assumption snapshot may record the original fact ID/version, assumed value, rationale, scope, and research marker; it must not overwrite the original fact. **Unknowns and conflicts must not be converted automatically into assumptions merely to complete execution.** Pre-analysis of future real cases requires an independent authority contract and cannot continue to use the L0 channel. This version does not introduce midway advisors to address this limitation.

<a id="52-是否有可用依据"></a>

### 5.2 Is there any basis available?

`coverage=covered` cannot be judged solely by search scores or "a link found." Module C needs to provide: required terms and original text positioning, version, jurisdiction/subject/validity period, source verification status, relevant exceptions, missing items and contrary basis. Module B then decides whether it can run based on the environment policy.

Historical transactions must be checked against applicable historical versions. Sources or rules that have not been professionally verified are only used under explicitly permitted L0 research policies and retain the Unverified designation. Technical timeouts use tool_error, not disguised as coverage=gap. Cases can only assist in proposing matters to be reviewed; case conclusions cannot be directly applied to this case just because they are similar.

<a id="53-是否允许部分出稿"></a>

### 5.3 Whether partial publication is allowed

There must be no nodes that can still be advanced, and all nodes must have a destination; if there are still questions for users to answer, there must be a clear selection of partial drafts that cover those specific questions/versions. No reply, provide later, and “don’t know” cannot be recorded directly as choices.

Professional pending matters, unsupported scope, technical failures and factual gaps are displayed separately. Independent conclusions may remain; any conclusions relying on pending matters remain suspended. Both complete manuscripts and partial manuscripts will go through the same text proofreading and final review process.

<a id="54-是否允许批准与交付"></a>

### 5.4 Whether approval and delivery are allowed

The prerequisite for entering review is that the text verification passes and the hash and input version are bound. When approving, check the permissions, current version of the case, and valid verification again at the same transaction boundary to prevent "valid when checked, expired when saving approval". All report modifications generate a new version, and the original approval remains in history but cannot be inherited.

Currently only internal research manuscripts can be approved for permitted purposes; advisor approval does not include validation of tax rules or upgrades to release levels. Missing advisors remain pending_review and are not automatically released.

<a id="6-工具调用约定"></a>

## 6. Tool calling convention

| action category | Tools | Calling conditions and return requirements |
|---|---|---|
| input/recognition | `screen_input`、`classify_case_scope`、`check_capability` | Complete data checks before admitting content to the model; capability matching returns supported contention points/unsupported contention points/missing range fields |
| Extraction/Q&A | `extract_candidate_facts`、`next_question`、`record_user_fact_check` | Each candidate value has the original text position; the question is bound to the field version and recovery node; the verification result does not improve the professional status |
| Scheduling | `decide_next_action` | Consume trusted context and return rule ID, action, object and reason; the results of the same context should be consistent |
| source of law | `retrieve_legal_sources`、`check_coverage` | Each return item comes with location, date, jurisdiction and verification status; separated by gaps and tool errors |
| analysis | `run_tax_rules`、`verify_node_result` | Consume only approved snapshots; use deterministic tools for calculations and retain pending professional judgments |
| report | `draft_review_report`、`verify_report` | Generated after locking the snapshot; verify the actual text and hash; revisions must be re-verified |
| final review | `review_report` (application service entrance) | Only Final advisor role can submit decisions; no approval rights for models; approve precise binding versions |

Each tool input contains case/node/snapshot references; permission identities are injected from the server side. The output uses clear `status + data + reason_code + provenance + version_refs`, and the model does not rely on reading error text to guess whether it is successful. MCP can host tool calls, and the tool service and orchestrator still perform authorization and precondition verification respectively.

This version re-uses the existing environment policy and shares the total budget; the report is automatically revised by default for two rounds and simplified draft at most once, both of which are design defaults. **Rewriting the text under the same frozen input cannot reset the number of revisions**. A new generation cycle will only be established when there is an effective change in the facts/sources of law, and records of the cumulative costs and time-consuming of the case will be retained.

<a id="7-结构化配置示例"></a>

## 7. Structured configuration example

The following fields are generated by the server, meaning "the necessary facts for this node are missing", rather than the model judging by itself that the entire case is incomplete:

```json
{
  "phase": "node",
  "context": {
    "dependency_state": "ready",
    "question_pending": false,
    "fact_gate": "missing"
  }
}
```

If the configuration hits `BR-12`, `ask_required_fact` is returned and the current node is marked as `waiting_user`. The action handler creates a question bound to the field version, then returns to the scheduler to advance independent nodes. Repeated execution of the same request should return an existing issue; duplicate creation is not allowed.

The configuration uses a custom simple decision format that is not native to LangGraph, LangChain, or MCP. If LangGraph is used, it can be read in the conditional routing node, and then the action is mapped to the graph node/application service; database transactions, idempotence, recovery and tool implementation still need to be developed. Keep business rules and tax calculation rules in independent versions to avoid changing the tax calculation logic when modifying the inquiry method.

<a id="8-落地顺序与验收"></a>

## 8. Implementation sequence and acceptance

1. B first implements context calculation, stage decision-making, reason codes and action processors; A integrates the questioning, verification, and partial-draft selection UI; C provides the capability catalog and actual coverage contract.
2. The first chain completes scope identification → key fact questioning → explicit research snapshot → search/rules → text verification → unique final review.
3. Implement resumption, idempotent resubmission, invalidation after fact changes, and approval of exact versions.
4. Extend integration acceptance with examples in JSON; repeated execution of the same input, recovery after restart, and concurrent change of facts and approvals must be done separately at runtime.

There are still interface gaps in the existing code: `queues.py` hands over verification/conflicts to the advisor and needs to be changed to a user queue; the factual professional status of `permissions.py` cannot be bypassed by ordinary user verification; the whole chain aggregation of `runner.py` needs to support node-by-node suspension and independent branches; the path for CLI to directly consume and extract values needs to be included in trusted snapshots. The old `human_gate` must not be used as a preliminary questioning step.

The condition selections for this rule configuration can be checked with an independent interpreter, but it does not prove that the tool behavior, real business processes, or tax conclusions are correct. All rules are draft business designs; tax thresholds still need to be verified by the rules package owner. This article does not change existing execution policies or production code.

2026-10-01 Configuration check record: The independent temporary interpreter passed the expected branch check of 49 scenarios in JSON; 129 legal stage context combinations were enumerated, 47 rules were all hit and there were no uncovered combinations; 6 missing fields, illegal types, unknown enumerations/stages and other inputs were refused execution. The document rule number and relative link check passed. These checks only verify the consistency of configuration conditions with the examples and do not include tool execution, database recovery, concurrency approval, or tax correctness testing.

<a id="9-新增对话规则与一句话期望行为"></a>

## 9. Added new dialogue rules and one sentence expected behavior

Numbers D-01 to D-12 in this section are business design items and have not yet been added to the original 47 readable configurations; classification, actions and integration tests need to be supplemented during implementation. Priority: Input/authority access control takes precedence; bind explicit additional information or corrections to the case before updating it; ordinary greetings do not cover business demands in the same message; other demands are handled separately according to tasks.

| No. | Situation | Expected behavior in one sentence |
|---|---|---|
| D-01 | Normal chat | Give a short response, do not call tax search, do not clear existing cases and unanswered questions. |
| D-02 | Concept explanation | Retrieve the permitted basis and explain the general meaning when supported by the scope, without requiring extraneous case context. |
| D-03 | Check regulations or cases | The number and original search conditions are retained, matching data and positioning are returned, and the entire case is not required to be completed. |
| D-04 | The background is unclear | Only ask for one piece of information necessary for the next step in the current task, rather than throwing the entire set of fact fields to the user at once. |
| D-05 | Supplementary information | Bind the new content to the current issue or case, retain existing valid facts and restore affected steps. |
| D-06 | clear correction | Updates the version of the corrected fact and invalidates the affected results; the old value cannot continue to be the currently valid value. |
| D-07 | inconsistent | List the conflicting values and sources and ask the user for clarification; if the conflict is not resolved, the conflict will be retained and sides will not be automatically selected. |
| D-08 | Don't know | Save the unknown and describe the impact based on the current task; get clear choices when part of the case draft is needed. |
| D-09 | No matching basis | Explain what basis and feasible supplementary directions were not found this time, and do not conclude that the regulations do not exist based on this. |
| D-10 | Out of range | Explain the uncovered content and the processable parts, and do not use the rules of adjacent regions or tax types to replace them. |
| D-11 | Information can only be displayed | Exclude restricted content from all model contexts, provide only approved display citations, and do not falsify interpretations based on the original text. |
| D-12 | Requires professional judgment | Arrange pending matters and evidence, keep them in pending status, and submit them to the final advisor for review. |

<a id="10-不同场景的最小信息及追问示例"></a>

## 10. Minimum information and questioning examples in different scenarios

The following is the minimum information required for querying/routing and is not a complete list of tax facts. Specific case nodes continue to use their required_facts; existing valid values will not be asked again.

| Scenario | What is the minimum required | Examples of major problems when missing | What not to ask first |
|---|---|---|---|
| Normal chat | current message | No business inquiries required | Subject, amount, shareholding, etc. |
| Concept explanation | Concept; area/scope that changes interpretation | "Do you want to know the relevant regulations of Hong Kong?" (only if the region is unclear) | All the circumstances of the user’s own case |
| Accurate data query | Number and identifiable source/region | "Which region or institution does this number belong to?" (When there is ambiguity in the number) | Individual or company, amount of income |
| Specific Dividend Inquiry First Route | Type of subject, relevant area, and target asked | "Is this dividend received by an individual or a company?" (if not yet provided) | Supporting information not relied upon for current judgment |
| Determine the applicable period | Transaction time and planned/actual status that affect current judgment | "Has this dividend occurred or is it about to occur?"; ask the necessary date in the next round | Use today as default transaction date |
| Supplement/Correction | Current case, issue, or identifiable fact | "Which transaction amount are you modifying?" (if there are multiple transactions) | Re-ask for all known information |
| Tax Amount/Eligibility Determination | Required facts listed in the current rule node and the basis for approval | Choose the one that most affects the conclusion from the unresolved items | Mechanically query all fields according to the fixed form |

Multiple rounds example:

1. User: "A Hong Kong company receives foreign-sourced dividends, help me analyze it." → Record the company, Hong Kong and dividends; no longer ask the individual or the company; if the period affects the next step, ask the occurrence/plan status.
2. User: "Planned to happen." → Save the planning facts; the next step is only to add the time required to determine the applicable version, and does not write the plan into actual receipts.
3. User: "The date is not known yet." → Save unknown, indicating that the period is not yet certain; general information can be provided first, and specific applicable conclusions are still suspended.
4. User: "First produce a partial draft based on the existing information." → Record the gaps and problem versions that are allowed to be retained, and then form a partial research draft according to the original process.

Another example: "Hello, I made a mistake just now. It was collected by the company, not me personally." The subject's correction should be responded to and processed; if it clearly corresponds to the current facts, the version will be updated, and corrections will not be missed due to the presence of "Hello" at the same time. If the new evidence conflicts with existing evidence and cannot be confirmed as a correction, follow D-07 for clarification.

<a id="11-检索接入和统一回答结构"></a>

## 11. Search access and unified answer structure

Retrieval is through [KnowledgeProvider](KNOWLEDGE_PROVIDER_CONTRACT_V0_1.md); a Mock implementation is currently planned, followed by the C adapter. Check model_use/display_use, version, and relevance to the current issue one by one before entering generation.

Well-founded replies always include:

- `answer_summary`: Directly answer this round of questions and limit the scope of support.
- `applicable_conditions`: The applicable conditions in the basis, and the currently known/unknown conditions.
- `claims`: Claim ID, text, supporting_evidence_ids; citations can only be selected from this approved evidence set.
- `limitations`: Uncovered scope, unknown facts, unfinished technology and pending professional matters.
- `citations`: Stable evidence ID, version, title, original text positioning, and permitted display entrance.
- `review_status`: The general information reply is not_required; the case study draft is pending_review, and it will be approved after the final authorized review. Once the source inquiry response contains case conclusions, it must be reclassified to the case path.

Display-only material is placed in `reference_only` and cannot be listed as supporting_evidence_ids actually used by the model. When there is no basis for the model, use a deterministic template to illustrate the data limitations and prevent the model from making tax claims from memory. Each source item and each reply under Mock retains the is_synthetic tag and "Mock materials, for workflow testing only."

<a id="12-提供给-a-的业务状态与提示"></a>

## 12. Business status and tips provided to A

A implements the display; B is responsible for returning the following semantics. The state is separated from the cause and does not require A to guess from natural language.

| status | reason_code | Tip example | B's follow-up action |
|---|---|---|---|
| completed | OK | "This round of information and applicable conditions have been compiled." | Save reply and basis version |
| waiting_user | NEED_BACKGROUND | “Also to confirm: Is this dividend received by an individual or a company?” | Save issue ID and recovery location |
| waiting_user | FACT_CONFLICT | "The two pieces of information are inconsistent. Please confirm which fact should be used this time, or provide additional explanations." | Keep sources from both sides |
| limited | NO_MATCH | "No matching basis was found this time, and no conclusion can be drawn based on this." | Return the query scope and specific gaps |
| limited | EVIDENCE_INSUFFICIENT | "There is relevant information, but it is not enough to support this judgment." | Point out the missing conditions/basis and suspend relevant claims |
| limited | EVIDENCE_RESTRICTED | "Viewable material found, but its original text is not currently allowed for use in model analysis." | Returns allowed reference_only |
| limited | OUT_OF_SCOPE | "This part is beyond the scope of current support, here are the parts that can continue to be worked on." | List scope; no substantive analysis is generated for unsupported sections |
| limited | PROFESSIONAL_JUDGMENT_REQUIRED | “The matter is reserved pending final advisory judgment.” | Import the final list and continue with independent nodes |
| error | RETRIEVAL_FAILED | "The data retrieval has temporarily failed, and the progress of this round has been retained." | Limited safety retry, retain recovery location on failure |
| error | MODEL_FAILED | "Reply generation failed temporarily, valid search results have been retained." | Reuse and regenerate while the version and permissions are still valid |
| error | PROVIDER_CONTRACT_ERROR | "The data service return format is abnormal and this round cannot continue." | Log diagnostics, do not interpret as no match |
| error | CITATION_UNRESOLVED | "Some quotes cannot be verified temporarily, and the relevant claims have not yet been exported." | Repair or withdraw the claim and verify again |

The outer layer of the reply contains at least conversation_id, turn_id, request_id, state_version, message_type, status, reason_code, content, question, citations, reference_only, review_status, is_synthetic. error also includes retryable, retry_after_ms; unused fields are empty. message_type is chat/clarification/reference_result/research_answer/scope_notice/error.

Normal questioning, no matching or professional pending judgment are not technical failures; no mechanical retry is allowed. Fields not produced because of a technical failure must not be filled with zero or guessed results.

<a id="13-新增规则的检查标准"></a>

## 13. Checking criteria for new rules

| Scenario | must be satisfied | not allowed to happen |
|---|---|---|
| Greetings | Do not call tax retrieval, keep the original task | Clear current cases |
| Concept or number query | Search by minimum criteria | Please fill in the complete fact cards first |
| Company entity has been stated | Reuse current facts | Again, individual or company? |
| The user said he didn’t know | Preserve unknown | becomes false or zero |
| User explicit correction | Generate a new version and update the affected steps | The old conclusion remains valid |
| Show data only | Every model call excludes restricted original text. | Let the model summarize the restricted data first |
| No match/timeout/model failed | Three causes are independently discernible | They all write "no basis" |
| Reply with citation | Claims mapped to parsable evidence and versions | Reference another version or model to make up an ID |
| Repeat request/interrupt recovery | The same request will not be written repeatedly, and the original problem can be recovered | Repeated questions and repeated calculations |
| Mock data | Replies and information are mock-tagged | Declaration of true tax conclusion or C accepted |

This section is the acceptance criteria to be implemented; see the contract document for the corresponding Mock response example. The real retrieval performance and recall rate must be measured after C is connected. Ordinary conversations and new interfaces must not reuse the test results of the previous 47 rules to declare acceptance.

<a id="14-对话策略实现guided-intake-02"></a>

## 14. Dialogue strategy implementation (guided-intake-0.2)

Centralized implementation: `packages/agent/dialogue.py`; orchestration: `packages/agent/workflow.py`; persistence and confirmation boundaries: `packages/chat/service.py`. Conversation JSON saves pending, attempts, deferred, deferred_query, partial_consent; continue to use case revision/request_id to prevent concurrency and repeated writing.

- D-01/D-03: Independent chatting and information inquiry are not interrupted by conflicts with old cases. Independent queries do not inherit the current case date and subject filtering. Only related facts are used in current case related queries.
- D-04/D-05: First identify the recipient, income type, analysis jurisdiction, and consultation goal; then ask for necessary descriptions such as the recipient jurisdiction for the target dividend. One item per round; exact enumerated responses are only bound to the active question, other natural language is parsed by the existing model adapter.
- D-06/D-07: Field-level explicit correction requires that the corrected fragment comes from this message and is consistent with the field and new value; a single word such as "change" cannot authorize overwriting all fields. If old and new values differ without an explicit correction, record a conflict and retain both values and their message history. When a correction expression cannot be reliably identified for the time being, it is conservative to request clarification.
- D-08: unknown is not equal to no; unavailable/unanswered is put into deferred. After a maximum of two questioning on the same item, you will be given the option to continue/partially sort out/pause. Do not advance automatically without a new user message. Permission for partial fact organization is bound to the current fact fingerprint; it is revoked when facts change. When gaps remain without permission, the analysis endpoint returns `partial_confirmation_required`.
- D-09: A no-match response includes the query, confirmed period, and specific gap; in the absence of actual/planned status, the given date cannot be automatically recognized as the actual transaction day. Missing evidence and service failures are handled separately.
- D-10: Personal, non-dividend or clearly non-Hong Kong cases indicate the scope of ability; new cases use the new conversation entry point of A to avoid overwriting existing case facts.
- D-11/D-12: Preserve itemized dual permissions, versions, hashes, and reference checks. Ask only for factual descriptions of staff, premises, taxes, and similar matters; reserve adequacy and eligibility judgments for final review. The receiving branch first distinguishes cash/non-cash. For non-cash payments, bank remittance is not required.
- Mixed task: Save the query to be checked when there is a conflict; after clear correction, the retrieval failure still saves the fact and returns `partial_failure / retrieval_failed` and `knowledge_unavailable`, and retries only restore the query. Pure query failure maintains the original 503/SSE error, and no partial write occurs.
- Topic pause/resume: keep pending; isolated "yes/no/don't know" after pause or chat are not automatically written to the old field. The missing item queue continues after recovery.

The current actual API uses lowercase reason_code, compatible with the full Case / done-only SSE of A , rather than requiring A to be replaced once with the Section 12 earlier proposed response shell. For new fields and consumption conventions, see Section 6 of the implementation specification.

<a id="15-2026-10-03-混合编排规则继承首版实现"></a>

## 15. 2026-10-03 Hybrid orchestration rule inheritance (first version implementation)

[Unified Orchestration Plan Section 12](../implementation/B_HYBRID_ORCHESTRATION_PLAN_2026_10_03.md#12-既有-47-条业务规则的继承矩阵) maps the existing basis, execution location and unfinished scope of BR-01～47 group by group; adds HY-01～10 management entrance, unanswered questions, independent query, task dependency, global budget, single submission and permissions. The BR number and business meaning are maintained, and the new design in this article is not written as an implemented DSL.

New constraints have been integrated into `hybrid.py/task_state.py/policy.py/budget.py/analysis_policy.py`: fixed entry and automatic routing share the same strategy; subgraphs only return status change proposals; unknown/gap/confirm/final approval semantics do not change due to mode switching. A conflict only blocks subtasks that depend on that fact, and independent regulatory queries can continue. The business tracking of HY rules and hit reasons is recorded in workflow.policy_version/rule_decisions; not all 47 JSON DSLs are executed.

See [Acceptance matrix execution record](../implementation/B_HYBRID_ORCHESTRATION_ACCEPTANCE_2026_10_03.md#7-2026-10-03-工程执行记录) for controlled backend and page regression results. The real model/C/PG layer is pending acceptance. The general revision executor, complete source-dependency invalidation, and advisor team editing/assignment in the original BR are still not all complete.
