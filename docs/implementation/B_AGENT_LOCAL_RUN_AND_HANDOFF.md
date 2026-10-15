<a id="b-agent本地运行与-ac-交接"></a>

# B Agent: Local Operation and A/C Handoff

Latest unified entry: [2026-10-04 team handoff/iteration list](B_TEAM_HANDOFF.md). Dated sections retain historical results. Actual free-model tests ran on 2026-10-04, but the complete continuous workflow did not pass; “no model calls yet” is no longer current.

Initial date 2026-10-02; latest hybrid handoff 2026-10-03, section 9. Branch `feat/b-agent-workflow`, based on A `7054c45`.
Runnable L0 development release; no page rewrite required. Mock validates paths before C is ready.

<a id="1-开发环境"></a>

## 1. Development environment

From `Asia-Tax-AI-Agent-B`:

```sh
python3 -m venv .venv
.venv/bin/pip install -r requirements-b-agent.lock
.venv/bin/pip install --no-deps -e .
cd apps/web
npm ci
```

Verified: Python 3.12, Node 22.13.1, LangGraph 1.2.12. The lockfile records this Python test environment; frontend retains A package-lock.json.

<a id="2-连接已有登录与模型环境"></a>

## 2. Existing authentication/model configuration

`config/agent.env.example` contains new samples only, no credentials. Merge required settings into private `.env`, retaining A's `FSIE_AUTH_*`/`FSIE_MODEL_*`; never overwrite credentials.

```text
FSIE_AGENT_PROVIDER=mock
FSIE_AGENT_MOCK_SCENARIO=MOCK-01
FSIE_WEB_DATABASE_URL=sqlite:///data/chat_cases.sqlite
FSIE_AGENT_REVIEWER_IDS=[]
```

Start API at repository root:

```sh
.venv/bin/python -m uvicorn apps.api.main:app --host 127.0.0.1 --port 8000
```

In another terminal run `npm run dev` under `apps/web`, open `http://127.0.0.1:5173`; Vite proxies `/api`. Normal frontend requires A authentication; intent understanding requires existing model configuration. This initial round did not read/copy private `.env` or send real-model data.

legacy defaults to A's existing read-only search. Only explicit mock uses synthetic materials; restart API after configuration changes. Page parameters/user text cannot select Mock.

<a id="3-不需要-c模型或登录服务的本地联调"></a>

## 3. Local integration without C, models, or authentication service

This local-only launcher uses synthetic identities/model outputs; never deploy it:

```sh
# Repository root, terminal 1
.venv/bin/python tests/chat/serve_browser.py

# apps/web, terminal 2
FSIE_WEB_API_URL=http://127.0.0.1:8001 npm run dev -- --port 5174
```

Open `http://127.0.0.1:5174`. Inputs include `你好` ("Hello"), `Synthetic foreign dividend case`, `FOLLOW_UP`, `CONFLICT_TEST`, `Case 68`. Model boundary is a double; API, storage, LangGraph, rules, pages are actual code. The next section tests 8 Mock scenarios.

<a id="4-可复现验收"></a>

## 4. Reproducible acceptance

```sh
# Repository root
.venv/bin/python -m pytest -q -m 'not integration'

# apps/web
npm run build
# Set FSIE_TEST_PYTHON to the absolute Python path in the virtual environment above; use channel=chrome when Chrome is installed.
PLAYWRIGHT_CHANNEL=chrome FSIE_TEST_PYTHON=/absolute/path/to/.venv/bin/python npm test -- --workers=2
```

Historical guided-intake results, 2026-10-03: 199 Python passed, 11 actual PostgreSQL tests not run; 20 Playwright passed after text/port assertion fixes and one Chrome startup timeout retest; latest 3 interview/conflict/partial-draft cases passed again. TypeScript/Vite passed. Initial counts 157/19; latest hybrid 256/25, section 9. Model/sign-in/retrieval networking uses doubles, not actual C/model quality acceptance.

<a id="5-a-的接入点"></a>

## 5. A integration

Retain api.ts/useWorkspace.ts protocol; compatible additions:

| Data | Fields | Purpose |
|---|---|---|
| Case / Message | workflow.status/reason_code/trace/timings_ms | Status/node timings |
| Case | fact_conflicts | Previous/candidate values |
| Message | answer.summary/conditions/claims/limitations/review_status | Structured answers |
| research / Passage | provider, is_synthetic, versions, permission summaries | Synthetic/actual provenance |
| Analysis | report_hash, review, evidence_gate, node workflow_status | Final review/version binding |

Initial research replies use deterministic extracts and condition/gap templates. Text must match authorized originals/hashes, without a second free-summary call. Ordinary chat retains the model. Initial SSE sends validated/committed `done{case}`, supported by A's existing loading/stopping UI.
The catalog has 53 fields: 42 editable originals + 11 B identity/objective/jurisdiction/occurred-planned/descriptive fields. C dictionary/filters are unchanged. First collect recipient/income/jurisdiction/objective, then required descriptions. Reuse knowns; ask one main question. Explicit corrections version history; otherwise differing values remain conflicts. See [guided design](B_GUIDED_INTAKE_DESIGN_2026_10_02.md) and [audit](B_USER_FACT_FIELD_AUDIT_2026_10_02.md).

Case.identification/fact_gaps/dialogue and Message.question/guided are added. Suppress duplicate generic questions on guided messages; show intake_gaps for partial drafts. Missing facts without partial consent give 422 partial_confirmation_required. Use the Chinese partial-summary command or `partial summary`, then confirm/analyze. Independent inquiries require no complete case and inherit no old filters.

Final review API:

```text
POST /api/cases/{case_id}/analyses/{report_id}/review
{revision, request_id, report_hash, decision, note}
decision: approved | changes_requested | unable_to_conclude
```

Identity comes from authentication, not body roles. Require a UUID in server `FSIE_AGENT_REVIEWER_IDS` plus case access. Nobody is authorized by default. Current owner isolation lacks cross-account assignment; A needs reviewer/assignment pages for team review. Chat, confirm, or forged roles cannot approve. Mock/incomplete evidence/rules cannot be approved; returns/unable-to-conclude are allowed. New facts stale reports.
After return, revise/reconfirm/analyze to create a new report hash while retaining audit. No intermediate advisor tool exists.

<a id="6-c-的接入点"></a>

## 6. C integration

Implement KnowledgeProvider search_evidence/get_evidence in `packages/agent/contracts.py`. Schemas: `docs/contracts/knowledge_provider_v0_1/`.
Existing `CKnowledgeProvider` supports this **proposed** HTTP contract; C has not confirmed actual routes:

```text
POST {FSIE_AGENT_C_URL}/search
{request: SearchRequest, trusted_context: {owner, case_id}}
→ SearchResult

POST {FSIE_AGENT_C_URL}/evidence
{reference: {evidence_id, source_version_id, unit_id}, purpose: display|model,
 trusted_context: {owner, case_id}}
→ EvidenceResult
```

Server tokens use Authorization, never browsers. C authenticates B and validates owner/policy; untrusted self-declared trusted_context is insufficient.
provider=c and request/trace IDs match. Missing rights mean unknown. Invalid text/hash/version is neither displayed nor used. No retries on no_match; one retry for temporary timeout/unavailability; no Mock fallback.

Optional v0.1 extensions: SearchRequest.kind/locators; Evidence.drift/heading/retrieved_at/coverage_cutoff/snapshot_sha256. Send allowlisted enum filters only, not unnecessary names/accounts. Different fields adapt locally; different permission/coverage semantics require contract confirmation.
Check display rights, then model_use=allowed for model contexts. Display-only originals can be shown but not summarized by a model. Unverified/date-unknown references do not establish deterministic node conclusions.

<a id="7-当前边界与下一轮验收"></a>

## 7. Boundaries and next acceptance

These prehybrid limits are supplemented by section 9. Professional/source rights/external environment limits remain.

- Single-turn route/facts/retrieve/compose/validate; storage restores later turns. No node checkpoints, task queues, or persistent multi-issue dependencies initially.
- Existing deterministic rules continue; 5 missing nodes enter final review. The 47-rule JSON is a design baseline, not a general DSL runtime.
- Eight Mock paths are tested; real understanding needs a separate Chinese set and authorized online evaluation.
- Actual C, PostgreSQL deployment, RLS roles, and sign-in require A/C environments.
- Historical citations freeze authorization/versions. If C revokes saved-text display, add notifications/read-time authorization; search-time rights alone are insufficient. L0 allows synthetic cases/approved public references, not sensitive corpora.
- Concurrent identical requests may duplicate computation but not overwrite revisions. Add durable leases if cost warrants. Disconnect cannot undo a started commit; GET verifies state.
- 3-second search budgets and one retry initially; HTTP connect/read timeouts do not guarantee hard deadlines against slow chunking. Analysis separately searches provisions/cases. Limit database connections/statements separately; deployment requires request deadlines.
- Actual advisor approval requires full rules/evidence and account assignment; B service/security completion is not professional delivery.

<a id="8-当前手动测试服务与数据保留"></a>

## 8. Manual services/data retention

At 2026-10-03 completion, restarted 8001 API; existing 5174 Vite retains it. Original 1 synthetic case remains in ignored `data/browser_cases_guided_intake_20261002.sqlite`. Refresh updates code while retaining conversation ID. Synthetic identity/model boundaries, not online models or production.

Restart while retaining data:

```sh
FSIE_TEST_DATABASE_PATH=data/browser_cases_guided_intake_20261002.sqlite .venv/bin/python tests/chat/serve_browser.py
```

Automatic tests omit FSIE_TEST_DATABASE_PATH and use independent temporary databases. Avoid manual ports in apps/web with:

```sh
FSIE_TEST_API_PORT=8011 FSIE_TEST_WEB_PORT=5184 FSIE_TEST_PYTHON=../../.venv/bin/python PLAYWRIGHT_CHANNEL=chrome npm test -- --workers=1
```

Exact controls include company (only for the active identity question), unknown, no materials, continue collecting, partial summary, pause, resume case, retry retrieval. Other natural language requires actual models. The launcher supports predefined synthetic inputs, not language quality measurement.

<a id="9-2026-10-03-混合编排首版交接"></a>

## 9. 2026-10-03 initial hybrid handoff

Delivery: three-entry contracts, shared parent/three subgraphs, bounded harness, recovery/budgets, shared admission, A entry/state UI. B workspace code/docs were uncommitted/unpushed. See [plan section 17](B_HYBRID_ORCHESTRATION_PLAN_2026_10_03.md#17-2026-10-03-首版执行记录) and [layered engineering results](B_HYBRID_ORCHESTRATION_ACCEPTANCE_2026_10_03.md#7-2026-10-03-工程执行记录).

| A sends/reads | Type/value | B behavior |
|---|---|---|
| Message.entry_hint | auto / dividend_consultation / fact_intake / reference_lookup | Default auto; shortcuts supply hints; editing clears stale hints |
| Message.reply_to_question_id | Optional ID | Reject stale binding with question_changed; reload |
| Case.orchestration | policy_version, active_task, suspended_task, queued_tasks | Persist tasks; same message API for resume |
| Message.research_results | Filtered retrieval bundles | Composite citations, no model-only originals |
| Case.workflow | task_results, rule_decisions, budget, reason_code | Partial failure/unfinished task explanations |

Keep JSON/SSE/confirm/analyze. Retry identical text/approval/entry_hint/reply_to_question_id/request_id, not a new draft. Changed payload gives 409 request_payload_conflict. Old receipts without hashes cannot safely replay under hybrid; reload/new ID. Keep paused tasks. legacy projections explicitly pause unsupported hybrid work, never bind isolated yes to old facts.

Server switches in `.env`, restart required:

```text
FSIE_AGENT_ORCHESTRATION=hybrid
FSIE_AGENT_DYNAMIC_PLANNER=false
```

Three paths still need the existing model adapter for initial understanding. Enable dynamic_planner only for authorized actual-model evaluation; server controls it. Normal defaults remain legacy/false. Local B lacked actual model configuration and made no online calls in this round.

Manual engineering tests retain synthetic cases without model/sign-in/C:

```sh
# Repository root; launcher port defaults to 8001
FSIE_TEST_ORCHESTRATION=hybrid FSIE_TEST_DATABASE_PATH=data/browser_cases_guided_intake_20261002.sqlite .venv/bin/python tests/chat/serve_browser.py
# Another terminal, in apps/web
FSIE_WEB_API_URL=http://127.0.0.1:8001 npm run dev -- --port 5174
```

Launcher defaults hybrid/dynamic_planner=False. Refresh http://127.0.0.1:5174 for three buttons/predefined controls. Initial parsing is a double, not arbitrary language evaluation. Automatic tests use independent databases, never the manual data file.

Latest: **256 Python passed, 11 actual PG not run; 25 hybrid Playwright passed; TypeScript/Vite passed.** Includes 54 hybrid and 3 transport deadline tests. Actual model/C semantics/professional correctness pending.

Bounded scheduling supports three sequential tasks, one active/one suspended, one in-scope no-match rewrite. Shared turn limits: 45 seconds, 4 model calls, 4 actions, 3 searches, 14 original reads, including nested analysis/retries. Originals never enter planning observations. Chunked model/C reading checks total duration and 2 MB size, but synchronous sockets may finish within remaining read timeout; deployment needs service-level deadlines. No background autonomy, node checkpoints, arbitrary SQL/code tools, or automatic approval.

Connect actual C through KnowledgeProvider/CKnowledgeProvider without changing A entry. Paths remain proposed; verify fields/versions/rights/coverage jointly. Answers remain extracts/conditions/gaps; model permission alone is not display permission. Professional items go only to final review.

<a id="10-2026-10-03-免费模型评测准备与回归"></a>

## 10. 2026-10-03 free-model evaluation preparation/regression

Added [62 multi-turn scripts/runner](../../evals/b_workflow/README.md): 135 steps, 15 smoke scripts, using both branches' candidate/natural-language cases and A's historical sheet; source commits/hashes saved with data.

Candidate OpenRouter Qwen `:free`: verify zero prices, account quota, request cap on each run; no automatic paid switch. Missing key means blocked; full preflight 62 blocked, 0 calls. Existing Qwen Token Plan requires separate quota authorization and does not alter manual-page settings.

Fixed amount correction for Chinese ten-thousand/hundred-million/thousands separators and independent summary actions. summary preserves pending/tasks without fact confirmation/partial consent; direct first summaries work without old dialogue.status. Regression: 268 passed, 11 deselected; affected `hybrid.spec.ts` 6 passed, including summary. This is not online success for 62 scripts; previous 25-page regression is historical.
