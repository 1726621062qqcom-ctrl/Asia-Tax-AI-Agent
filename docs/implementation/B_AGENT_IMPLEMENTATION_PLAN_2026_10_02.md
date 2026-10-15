<a id="b-模块开发计划接入-a-前端与预留-c-检索"></a>

# B Module Development Plan: A Frontend Integration and C Retrieval Interface

Date: 2026-10-02. Baseline: `Zhihong-Wu` / `7054c45323abf7d63d9725f03f81dab892c98110`.
Development: separate worktree `Asia-Tax-AI-Agent-B`, branch `feat/b-agent-workflow`.
Written before implementation. Completion is recorded below; completed design is not runtime acceptance.

<a id="1-目标和职责"></a>

## 1. Objectives and responsibilities

B delivers A's Agent business backend: chat/source/case routing, necessary questions, revisions, retrieval permissions, evidence/citations, candidate analysis, final review states, exceptions, and versions.
A retains UI ownership. B preserves API/SSE, adding only required types/synthetic markers. C owns corpus, retrieval quality, and source authorization; B calls C and interprets statuses.
Scope remains Hong Kong foreign-sourced dividend FSIE L0. Mock validates paths, not real tax evidence. No intermediate advisor stage; user fact checks are not advisor approval.

<a id="2-已有代码与缺口"></a>

## 2. Existing code and gaps

| A implementation | B work |
|---|---|
| React/TypeScript/Vite; FastAPI `/api` | Preserve routing/authentication/proxy/case structure |
| ChatStore JSON, revision, request_id receipts | Retain sole state source; add workflow metadata/report snapshots |
| Model chat/research/intake routing | Deterministic control/scope/questions; models cannot change system state |
| Research preamble before originals | Compose after retrieval under permissions; state insufficient evidence |
| SQL keywords | Provider contract, Mock, legacy adapter, C HTTP interface |
| Candidate rules after user facts confirmation | Retain confirmation; collect gaps/judgments at final review |
| SSE passes model JSON reply | Validate business responses before output; shared JSON/SSE logic |

<a id="3-技术选择"></a>

## 3. Technical decisions

- Retain Python >=3.11, FastAPI, Pydantic v2; strongly validate Provider boundaries.
- LangGraph 1.x `StateGraph`: route → facts → retrieve → compose → validate per turn. Deterministic edges control nodes; models handle understanding/constrained expression.
- No mandatory high-level LangChain Agent. Retain existing OpenAI-compatible adapter/DeepSeek configuration; no provider switch or browser keys.
- SQLAlchemy/PostgreSQL cases, SQLite tests. Graph computation has no database writes; ChatStore commits once under optimistic locking. Persist waiting state and end the call; reload on the next message.
- No simultaneous LangGraph checkpointer initially, avoiding duplicate case/checkpoint state. Rerun uncommitted turns; return receipts for committed request_id. Do not claim node-level failure recovery. Add persistent checkpoints/outbox if long tasks justify them.
- HTTP JSON is the simplest C integration; MCP may be another Provider adapter without changing Agent/frontend protocols. Frontend need not call MCP.
- No Redis, queues, vector database, or autonomous multi-Agent loops. Long tasks/full statutory coverage/professional evaluation remain separate.

[LangGraph overview](https://docs.langchain.com/oss/python/langgraph/overview) permits use independently of LangChain; [Persistence](https://docs.langchain.com/oss/python/langgraph/persistence) distinguishes checkpoints from application persistence. Use bounded single-turn graphs plus existing storage.

<a id="4-模块划分与调用链"></a>

## 4. Modules and call chain

```text
A pages: api.stream / api.mutate
  → FastAPI authentication and input validation
  → ChatService (owner isolation, revision, request_id)
  → B TurnWorkflow (LangGraph, no persistence side effects)
      route → facts/scope → retrieval → answer → validation
                   ↓ waiting_user / unsupported / paused_gap
  → ChatStore atomic commit → SSE done{case} or JSON Case

C data boundary: KnowledgeProvider.search_evidence / get_evidence
  ├─ MockKnowledgeProvider: server-selected MOCK-01..08
  ├─ LegacyKnowledgeProvider: existing read-only search; original text display only
  └─ CKnowledgeProvider: HTTP address from trusted server configuration; no Mock fallback on failure
```

Plan `packages/agent/`: contracts.py, providers.py, knowledge.py, workflow.py, review.py; modify `packages/chat/service.py`, `streaming.py`, `analysis.py`, and `apps/api/chat.py`. Keep the rule engine; models do not rewrite tax calculations.

<a id="5-业务行为与状态"></a>

## 5. Business behavior/status

| Situation | Expected behavior | Tool/status |
|---|---|---|
| Greeting/help | Natural reply, no retrieval/confirmation reset | chat |
| Concept/provision query | Retrieve without full interview | research |
| Case description/supplement | Update explicit facts only; preserve versions | intake |
| Missing essential context | One main question; do not repeatedly force unknowns | waiting_user |
| Different old/new facts | Preserve values, request clarification/edit | needs_resolution |
| No matches | Explain gaps; no tax conclusions | no_match / paused_gap |
| Display-only material | Display originals; exclude from every model context | reference_only |
| Unknown permissions | Deny model/display use by default | evidence_restricted |
| Wrong period/jurisdiction | Exclude support, record gap | evidence_insufficient |
| Out of scope | Explicit supported scope | unsupported |
| Judgment/missing rules | Unresolved items in candidate draft/final review | pending_final_review |
| Service failure | Distinguish model_failed / knowledge_unavailable | technical_error |

Separate facts from conversation: unknown remains unknown; empty values mean deletion, never no/0. Identical facts do not stale reports; actual changes stale analysis and clear confirmation/review validity. Models cannot autonomously overwrite conflicts.
If the original dictionary lacks individual/company, use separate consultation context rather than assuming a company. Synchronize field catalogs/page compatibility on changes.

<a id="6-与-a-的接口契约"></a>

## 6. A interface contract

Retain POST `/api/cases/{id}/messages`, `{text,data_approved,revision,request_id}`.
JSON returns complete Case; SSE returns `delta{text}`, `done{case}`, or `error{code}`. Initial tax replies may emit only validated delta+done.
Retain facts PATCH, confirm POST, analyze POST. `confirm` means user fact checking; analysis remains `review_required`, never approved by chat.
Add without removing: message.workflow (status/reason_code/trace/timings), research.provider/is_synthetic/reason_code, answer (summary/conditions/claims/citations/limitations/review_status). Existing pages still render text/passages.
GET `/api/knowledge/search` and analysis also use the same Provider, avoiding direct C database side paths.
Retain A's lowercase errors. No-match is a normal response, not a fake network error. revision_conflict requires refresh; retries reuse request_id.
Initially expose final review service/API; server authorization determines reviewers. Ordinary accounts cannot self-designate advisors. Without configuration, retain pending review. A adds review pages/buttons later.

<a id="7-c-插槽与授权"></a>

## 7. C interface and authorization

Full contract: `../architecture/KNOWLEDGE_PROVIDER_CONTRACT_V0_1.md`.
Requests contain query/intent, jurisdiction/topic, applicable date, required fact filters, request_id/trace_id/limit/deadline. Owner/permissions derive from server trusted_context, never frontend assertions.
Responses distinguish ok/partial/no_match/error, with corpus_version/coverage/evidence/timings. Evidence includes versions/locations/hashes, model_use/display_use, policy_version. get_evidence reads exact versions without latest-version fallback.
Server configuration selects Mock; user text cannot choose fixtures. Eight fixture groups test the contract. Missing C HTTP configuration errors explicitly; no real C connection means no claimed integration success.
Construct an allowlisted model-text projection separately. Do not serialize entire responses, display originals, or internal metadata into prompts. Historical messages must not reintroduce display-only text.
If model use is allowed but display denied, initially prohibit disclosive summaries until C explicitly authorizes derivatives. Summaries must not bypass display rights.
External text is data, never authority to change prompts, permissions, or rules.

<a id="8-回答和分析边界"></a>

## 8. Answer/analysis boundaries

Retrieval replies include direct points, conditions, citations, gaps, review markers. Citations must be from this permitted evidence set with matching hashes/versions. On validation failure, discard the draft and return gaps.
Use verifiable extracts initially; generated long reasoning is not validated advice. Stop conclusions when scope/date/rights fail.
Retain candidate rules with evidence coverage/node gates, gaps, synthetic markers. Existing limited rules are not a complete chain. Map old human_gate wording to final-review tasks, not intermediate human tools.
Final review binds report hash + facts/rules/source versions. Changes invalidate approval. Approve/return/unable-to-confirm all audit. Mock analysis cannot receive formal approval.

<a id="9-性能失败与一致性"></a>

## 9. Performance, failures, consistency

- At most one routing model call and two retrievals per turn, retrying only explicitly retryable failures once; never loop on no_match.
- 3-second total retrieval budget with HTTP timeouts; retain 45-second model limit, 90-second turn. Unknown exceptions return safe errors.
- At most 12 history messages, 4000 characters each; 7 citations; bounded model text.
- Record node timings, retrieval counts, provider/corpus_version, trace_id; no credentials/full prompts.
- Fixed graph nodes/recursion limit, no unlimited reflection.
- Check SSE disconnect before commit. Computation has no persistence effects, but a request reaching commit may succeed after disconnect. GET/retry request_id to confirm; cancellation cannot promise transaction reversal.
- Optimistic locking prevents contamination. Concurrent identical requests may recompute but commit once and return the same result. Add request leases only if duplicate model cost justifies them.

<a id="10-开发顺序与验收"></a>

## 10. Development order/acceptance

| Phase | Deliverables | Acceptance |
|---|---|---|
| P0 baseline | Plan, worktree, copied designs | No original workspace overwrites |
| P1 Provider | Types, 8 Mock states, legacy/C adapters, permissions | No unapproved originals in model input; no silent fallback |
| P2 graph | Facts/questions/retrieval/answers | Chat does not search; unknowns not reasked; conflicts not overwritten |
| P3 A integration | Shared JSON/SSE, search/analysis Provider | Compatible protocol, idempotency, errors/cancellation |
| P4 final review | Hash/statuses/server permissions | Ordinary users, stale versions, Mock cannot approve |
| P5 regression | Unit/API/SSE/build/browser where available | Reproducible local acceptance independent of real models/C |

Cover 8 fixtures, retries, unknown/one-way rights, date mismatch, fabricated citations, absent sources, no_match versus timeout, exact versions, cross-user isolation, invalidation, one question, revision conflicts, same request_id, JSON/SSE consistency, final permissions/hash.
Type validation is not content evaluation. Live routing accuracy, C recall/completeness, real frontend sign-in, and expert review need their environments.

<a id="11-后续扩展条件"></a>

## 11. Expansion conditions

When C is ready, jointly confirm fields, permissions, versions, and coverage; run the same contracts against the actual service before c mode. Changing a connection string is insufficient.
Multi-issue/long-task extensions require dependency scheduling/checkpoint/outbox, asynchronous cancellation, and legal-change triggers. The business JSON remains a review baseline; explicitly distinguish implemented rules rather than claiming all 47 execute.

<a id="12-执行记录"></a>

## 12. Execution record

- Plan written before any online business write.
- Implementation, commands/results, gaps, and external dependencies follow.

<a id="2026-10-02-实施结果"></a>

### 2026-10-02 results

P0–P5 local L0 implementation/validation completed: single-turn LangGraph, typed Provider, 8 fixtures, legacy/C HTTP adapters, permissions/date/hash boundaries, request/version retention, final review service/API, connected to A JSON/SSE/search/analysis. Frontend changes are limited to required markers/fields/review statuses.

Adjustments:

1. Evidence replies use extracts, not a second free-summary model call; source presence is verifiable, professional correctness is separate.
2. Persist graph turn results in ChatStore, not memory checkpoints presented as fault recovery.
3. Final review requires server UUID allowlist plus case owner. No cross-account assignment/review page; A adds later.
4. legacy default preserves A compatibility; developers explicitly select mock. c mode does not fall back to Mock.
5. No general interpreter for all 47 configured rules; explicit code covers current consultations. Multi-issue/long scheduling remains future work.
6. Chat/research share the graph. SSE sends validated done; existing loading/stopping remains usable. Future latency work must preserve validation.

Results: Python 157 passed / 11 integration deselected; A Playwright 19 passed; TypeScript/Vite and git diff --check passed. No actual C/model/PostgreSQL/professional acceptance. See [local handoff](B_AGENT_LOCAL_RUN_AND_HANDOFF.md).

<a id="2026-10-02-至-2026-10-03-动态追问及兜底细化结果"></a>

### 2026-10-02–2026-10-03 guided follow-up/fallback results

Added `guided-intake-0.2`: four entry fields, objective queues, one question with rationale/example, choices after two unanswered attempts, unknown/deferred, pause/resume, field corrections/conflict history, mixed-task saving/query restoration, snapshot-bound partial consent. Audited both GitHub branches' fields/rules/cases and four ruling cards, adding noncash/tax descriptions. See [design/interfaces](B_GUIDED_INTAKE_DESIGN_2026_10_02.md) and [53-field audit](B_USER_FACT_FIELD_AUDIT_2026_10_02.md).

Final results: Python 199 passed / 11 integration deselected; 42 dynamic-interview tests including post-answer state consistency; all 20 browser cases passed, with revised old assertions retested; latest interview/conflict/partial-draft 3 passed again; TypeScript/Vite passed. Retained synthetic cases; manual 8001 API restarted, 5174 page retained.

Actual model routing/extraction, C contracts/quality/dates, PostgreSQL, and professional rules remain unaccepted. Free-language correction recognition is conservative. Complete English follow-ups, multi-entity graphs, and multi-query queues are not completed capabilities.

<a id="2026-10-03-固定入口与动态调度首版工程完成"></a>

### 2026-10-03 fixed entry/dynamic scheduling (initial engineering complete)

See [unified orchestration](B_HYBRID_ORCHESTRATION_PLAN_2026_10_03.md) and [54-item acceptance](B_HYBRID_ORCHESTRATION_ACCEPTANCE_2026_10_03.md). Reused five intents, fields, follow-ups/fallbacks; added entry/task states, shared subgraphs, bounded planning, common analysis admission, A UI. Added 54 hybrid and 3 transport deadline tests. Backend 256, page 25, TypeScript/Vite passed. Real model/C/PG acceptance pending; code not committed/pushed at this record, and manual pages use synthetic model boundaries.
