# B Agent Multi-Turn Business Evaluation

Date: 2026-10-03. Dataset version: `b-workflow-0.1`. There are 62 scripts and 135 steps, with 15 scripts in the initial smoke subset. All case details are synthetic. Expected values are engineering behavior criteria, not yet expert tax gold standards.

**2026-10-04 update**: some actual model calls have been completed using the user-authorized free OpenRouter configuration. Ordinary conversation/language switching and some fact extraction/follow-up questions succeeded. Complete consecutive workflows were repeatedly blocked by model timeouts/rate limits; there were also actual behavior failures involving specified case scope, mixed corrections, and other scenarios. The end-to-end workflow and all 62 scripts cannot currently be reported as passing online. The “awaiting credentials” text below is a historical record from 2026-10-03; the latest collaboration entry point after submission is [B_TEAM_HANDOFF](../../docs/implementation/B_TEAM_HANDOFF.md).

Added `v0.1/model_e2e.json`, containing a complete workflow from an empty case and three diagnostic scenarios; select it with `--dataset`. Each call records its stage (such as plan_turn/plan_next), cost, duration, and sanitized failure category, without saving keys. Expectations for the complete workflow remain unchanged; failures are not relabeled as passes. As of 2026-10-04, engineering validation comprises 270 passing backend tests and 26 passing browser tests, plus successful build and knowledge package validation. These results are separate from online results.

## Sources

`git fetch origin` was run, and the remote main and Zhihong-Wu branches were inspected. Exact source commits, paths, and SHA-256 values are stored in sources in [cases.json](v0.1/cases.json). The builder requires local sources to match the corresponding GitHub blobs exactly.

- main's `tests/fsie/candidate_cases.json`: ten versioned synthetic candidate cases with structured prerequisite facts and blockers.
- main's `tests/fsie/natural_language_cases`: six existing natural-language cases and one system instruction override attack. Business expectations were redefined for this round; the old stop_and_escalate/human_review_required values do not imply adding an advisor midway through the workflow.
- Zhihong-Wu's `docs/project/evaluations/Taxora_测试记录.xlsx` and README: historical records for 20 questions. This round extracts relevant questions and failure themes covering concepts/jurisdictions, the Case 68 date, specified provisions, participation exemption, case summaries, no matches, latest amendments, and unsupported confirmation of exemption. Previous model answers were not used as gold standards, and no claim is made that the entire old 20-question sheet was rerun in this round.
- B's existing follow-up, hybrid orchestration, and acceptance matrices: additional coverage for unknown, deferred, explicit corrections/genuine contradictions, task switching/recovery, permissions, budgets, idempotency, partial drafts, analysis, and final review.

## Script contents and coverage

Each script includes an ID, synthetic-data marker, sources, prerequisite test facts, mock configuration, multiple operations, and behavior assertions for each step. seed_facts establishes prerequisites only and does not count as successful model extraction. Actual messages run through the original FastAPI JSON/SSE API, production plan_turn/harness, actual LangGraph, storage, and business validation. Only identity and the not-yet-ready C component are replaced with test doubles. The test launcher's fake model parser does not participate in actual model evaluation.

| Behavior group | Scripts | Focus |
|---|---:|---|
| Three entry points / casual conversation / scope | 10 | Entry points are prompts; ordinary chat does not retrieve; assumptions are not stored as facts; personal/other-jurisdiction cases do not use the Hong Kong corporate workflow |
| Facts / follow-up targets / corrections | 15 | One question at a time, unknown, temporarily missing information, stopping repeated questions, no guessed dates or inferred eligibility from descriptions, Chinese/English numbers, and unit corrections |
| Sources / unsupported answers / permissions | 8 | Preserving specified identifiers, query continuity, distinguishing no matches from failures, display/model-use permissions, and version anomalies |
| Tasks / mixed messages | 8 | Pause/resume, isolation of independent inquiries and conflicts, corrections + retrieval failures, retaining multiple results, and preventing a new client from overwriting an existing case |
| Analysis / transport / security | 11 | Fact confirmation, invalidation of partial-draft consent, a single final review, idempotency, question IDs, SSE, refresh, and attacks |
| Historical natural-language / error questions | 10 | Six historical cases and regression for participation exemption, summaries, unsupported answers, and current applicability |

Checks cover return statuses/error codes, whether answers include required known facts and gaps, field values and prohibited inferences, actual search counts, query identifiers/scope, analysis timing, external calls on duplicate requests, and preventing original text from entering the model. A display-only sentinel is embedded in MOCK-03. Meter checks before every actual model request; an absence of leaks in the final answer cannot replace context inspection.

Another model is not used to automatically declare tax answers correct. These 62 scripts cover the behavior of a limited prototype, not all real tax transactions, expression variants, actual C recall/coverage/permissions, or account assignment. Claim filtering in ordinary conversation still uses conservative rules; a small number of negative string checks cannot establish an absence of hallucinations.

## Free API selection and current blockers

The official model catalog was queried. At the time, OpenRouter `qwen/qwen3.8-27b:free` had prompt/completion prices of 0 and offered a chat/completions-compatible API. See the [official model page](https://openrouter.ai/qwen/qwen3.8-27b:free), [authentication example](https://openrouter.ai/docs/quickstart), and [free quota and rate limits](https://openrouter.ai/docs/api/reference/limits). Free use still requires an account key. Free models, quotas, and availability change over time and must be rechecked before running.

Anonymous Pollinations probes: POST to `text.pollinations.ai/openai` returned 404; POST to `gen.pollinations.ai/v1/chat/completions` returned 401. Only a JSON greeting without case details was sent. No successful inference occurred, no strangers' keys were obtained, and a GET of the model catalog was not counted as a successful smoke test. The official newer documentation also requires an API key; see the [authentication documentation](https://github.com/pollinations/pollinations/blob/main/gen.pollinations.ai/src/docs/apidocs-recipes.md).

The local B repository and process have no free-provider key. The original project has Alibaba Cloud Qwen Token Plan configuration; only its presence, host, and model name were checked. The key was not printed, copied, or used. Sufficient free/included quota has not been verified, and this alternative requires user authorization before use.

The current [complete preflight](runs/preflight_full_2026_10_03.json) reports **62 blocked, 0 passed, 0 failed, and 0 model calls**, due to missing_openrouter_key. It is not an online pass report. The existing 268 Python engineering regression tests and the online results of these 62 scripts must be reported separately.

## Running the evaluation

Run all commands from the B repository root. Configure only your own free account key in a private, Git-ignored `.env`, using `OPENROUTER_API_KEY`. Do not paste keys into chat, code, command arguments, or reports. The code does not modify the existing .env, change the model manually selected on the page, or change the production database.

```sh
# Validate scripts only; no inference, and not counted as case passes
.venv/bin/python scripts/evaluate_b_workflow.py --validate-only

# Initial 15 scripts: at most 40 model requests, serial execution with a 3-second interval
.venv/bin/python scripts/evaluate_b_workflow.py --suite smoke --output evals/b_workflow/runs/smoke.json

# Retest selected failing scripts, keeping the original dataset expectations
.venv/bin/python scripts/evaluate_b_workflow.py --select BWF-017,BWF-059 --output evals/b_workflow/runs/recheck.json

# Full suite; still limited by free quota and the 40-request cap. Mark blocked if insufficient; do not pay automatically
.venv/bin/python scripts/evaluate_b_workflow.py --suite full --output evals/b_workflow/runs/full.json
```

Before running, verify an explicitly non-OpenAI :free model and all published prices through the official catalog, and read the remaining free quota for your own account. The request cap is the smaller of the remaining quota and --max-calls. Stop actual calls if the key is missing, prices are nonzero, preflight fails, or free quota is exhausted. By default, do not switch to a paid model, buy credits, or automatically fall back to mock model answers. Retrieval remains explicitly mocked.

The following command may be run only after the user explicitly authorizes the existing Qwen plan:

```sh
.venv/bin/python scripts/evaluate_b_workflow.py --provider existing-plan --authorized-existing-plan --env-file ../Asia-Tax-AI-Agent/.env --max-calls 30 --output evals/b_workflow/runs/qwen_plan.json
```

This mode reads the existing private configuration into memory without writing it back. It must not be labeled as “free OpenRouter results.” The default max-calls is 40, configurable from 1–200. If free quota is insufficient, preserve blocked/not-executed items; do not bypass rate limits by cycling through new accounts/keys. A complete multi-turn suite usually needs more than 40 calls. Run in batches within the free quota and retain a separate report for every run; a passing subset does not establish a passing full suite.

## Results and completion

Each step records synthetic input, expectations, actual workflow, facts, filtered page messages, tool count, and duration. Each model call records only status, exception type, and usage, without saving Authorization or raw error text containing keys. Workspace reports retain complete `.json` records and `.md` summaries. The case DB uses a temporary isolated directory that is destroyed afterward; personal sessions are not written.

Identified engineering gaps have been addressed: amount corrections support Chinese units for ten thousand and one hundred million, thousands separators, and explicit English units. Fact summaries are independent of consent for partial analysis, preserve the original question and task, do not consume follow-up attempts, confirm facts, or approve reports, and can respond to a direct initial summary request even without conversation state. Twelve tool and boundary tests were added. The complete Python suite reports **268 passed, 11 deselected**; the affected hybrid page group reports **6 passed**. Live model runs still await credential selection; these engineering results do not establish that all live workflows succeed.
