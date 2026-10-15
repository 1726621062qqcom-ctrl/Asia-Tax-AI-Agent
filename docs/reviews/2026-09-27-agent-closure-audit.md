<a id="agent-闭环核查--2026-09-27"></a>

# Agent Workflow Audit · 2026-09-27

> This records the baseline before this development round. Web APIs, fact confirmation, research results, and session persistence were implemented later; see the [web research workflow record](../project/LIVE_CHAT_SLICE.md) for current status, limits, and startup. The full PRD workflow remains incomplete.

<a id="结论与核查范围"></a>

## Conclusion and scope

**An L0 command-line research slice exists, but the interactive product workflow required by the PRD is incomplete. The current webpage cannot fully answer tax questions.**

Reviewed `feat/tax-chat-workspace` code, the [PRD](../product/PRD.md), [technical roadmap](../architecture/TECHNICAL_ROADMAP.md), and [L0 acceptance record](../project/L0_ACCEPTANCE_RECORD.md). Old `demo/hk-web` is unmerged and its APIs do not count as current page capabilities. This records implementation gaps without changing approved scope or release gates.

The 2026-09-05 record establishes model/database/candidate-case integration validation of the command-line slice at that time, not current DeepSeek availability or complete FR-01–FR-08 delivery. Historical RAG means rule-to-legal-unit citations, not completion of keyword/vector hybrid retrieval.

<a id="对照-prd-的实际状态"></a>

## Actual status against the PRD

| Requirement | Existing code/evidence | Missing workflow |
|---|---|---|
| FR-01 Natural-language case creation | `packages/intake/extraction.py` calls a compatible model API and validates 43-field candidates; `packages/intake/cli.py` saves/runs research | `apps/api/main.py` has only `/health`, no case/chat/analysis APIs. The page does not call a backend; no verified DeepSeek end-to-end conversation |
| FR-02 Dynamic interviews | Evaluator produces missing facts/blockers | No dynamic queue, multi-turn orchestration, conflict resolution, pause/resume; missing-field notices are not an interviewing Agent |
| FR-03 Fact cards | Backend Fact/FactVersion; frontend manual entry of 6 basic facts | Candidate facts enter research without advisor confirmation. Frontend saving is not backend confirmation. Intake updates do not append FactVersion; full revision history is disconnected |
| FR-04 Rules | `packages/rule_engine/runner.py` has 5 evaluators for scope, income character, receipt, economic substance, participation basics, plus human_gate; runs include fact snapshots/rule versions | Missing financial entity exclusion, foreign tax switchover, anti-hybrid, main purpose, and filing evaluators from 10 business nodes. Existing nodes may need human judgment. Dependency reruns/invalidation are incomplete |
| FR-05 Retrieval/citations | Source manifest, snapshots, hashes, segmentation, persisted LegalUnits; intake uses predefined `statute_locator` | No question-driven keyword/vector retrieval, authority/applicability filters, or retrieval quality evaluation workflow. Sidebar official links are an index, not analysis citations |
| FR-06 Internal review drafts | `packages/reporting/` creates Markdown with sources, versions, blockers, research watermark | No web report service, complete decision-chain draft, or report version workflow; not a complete answer to arbitrary tax questions |
| FR-07 Human review/versioning | Execution batches, some audit data, disk reports | No approve/return/revise/archive APIs; invalidating old approvals after facts change, locking report/legal versions, and historical reconstruction are incomplete |
| FR-08 Knowledge management | `packages/knowledge_pipeline/build.py` detects drift and retains originals | Legal-unit refresh deletes/reimports rows; source review, publication freezing, and stable associations between old units/historical reports remain incomplete |

The manifest has 11 sources, 6 candidate rules, 8 evidence requirements, and 10 candidate cases. These describe engineering coverage, not professional validation. Initial in-depth scope remains **Hong Kong FSIE foreign-sourced dividends**, not all tax/financial questions or jurisdictions.

<a id="按技术路线推进的顺序"></a>

## Order of work under the roadmap

1. **Connect the minimal interactive actual workflow first.** Add case/chat/fact APIs to existing Python modules, connect and validate current DeepSeek/failures, persist sessions, ask multi-turn follow-ups, and analyze after advisor confirmation. Use one candidate case to test input → follow-ups → confirmation → research results/sources, plus refresh recovery, model failures, unknowns, and conflicts. Merely displaying model chat is insufficient.
2. **Complete core rules/retrieval.** In roadmap phase 2, complete business nodes, affected-node reruns, hybrid retrieval, date filters, paragraph citations, and knowledge version links. Every result traces to fact/rule/source versions used in that run.
3. **Complete report review/archiving.** In phase 3, implement edits, returns, approval, version locking, invalidation, and audit. Acceptance must actually test old reports after fact revisions and historical recovery, beyond Markdown generation.
4. **Complete pretrial security/professional gates.** Authentication, case access, organization isolation, log redaction, recovery tests, and model data processing remain required. Specifically, `/health` returns the raw database connection string; remove it before shared environments to prevent credential leakage. L1 also needs Hong Kong expert validation, 30–50 expert cases, and PRD metrics including ≥90% critical fact identification completeness. Engineering tests cannot replace these.

Some phase 1 backend paths exist, but web workflow/walkthrough evidence is incomplete; phases 2/3 retain major gaps. Historical L0 engineering acceptance does not establish L1 readiness. An API key supplies model access, not business state, retrieval, approval, or professional validation.

<a id="本次前端调整"></a>

## Frontend changes in this round

- Removed region selection, demo/preview labels, fictional presets, and fixed assistant answers.
- Kept the homepage title, input, and 3 quick questions for foreign-sourced dividends/fact organization/evidence; case/source panels open on demand.
- Retained bilingual switching, tax icons, mobile layout, and conversation-isolated input drafts.
- Submission retains messages on this page only and explicitly shows unsent/no analysis generated; manual facts are not presented as confirmed model facts.
- Refresh clears messages/facts; localStorage saves language only. Visual design does not change backend delivery level.

<a id="本次验证与限制"></a>

## Validation and limits

- `apps/web`: `npm run build` passed; Playwright using system Chrome **8 passed**, covering initial view, languages, isolation, fact saving, sources, input method, mobile layout, and focus. Desktop/mobile screenshots inspected.
- Current backend: `pytest -q -m 'not integration'` **74 passed, 11 deselected**, using a virtual-environment interpreter from an older worktree in the same workspace to test current code; old code was not merged.
- `scripts/validate_fsie_package.py` passed source/rule/evidence/fact dictionary metadata checks.
- **No actual DeepSeek calls, database integration tests, or expert case validation in this round.** No `.env` key was read/output. Offline tests do not establish current online deployment availability.

Interface organization references [Vercel Chatbot](https://github.com/vercel/chatbot)'s main conversation/on-demand tool interactions; components are original, without copied code/assets.
