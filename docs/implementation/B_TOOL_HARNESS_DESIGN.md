<a id="b-自由对话工具执行循环"></a>

# B Free-Form Conversation Tool Execution Loop

<a id="技术选择与开源参考"></a>

## Technical choice and open-source references

Official open-source approaches reviewed on 2026-10-04:

- [LangGraph Workflows and agents](https://docs.langchain.com/oss/python/langgraph/workflows-agents): state graphs for dynamic model/tool loops.
- [LangChain middleware](https://docs.langchain.com/oss/python/langchain/middleware/built-in): tool errors, retries, model/tool limits, context management.
- [Deep Agents architecture](https://github.com/langchain-ai/deepagents/blob/main/libs/ARCHITECTURE.md): tools, middleware, planning, and context organized on a runtime; this project need not enable filesystem, shell, or delegation capabilities.
- [OpenAI Agents SDK runner](https://github.com/openai/openai-agents-python/blob/main/docs/running_agents.md) and [tool guardrails](https://github.com/openai/openai-agents-python/blob/main/docs/guardrails.md): model-selected actions, tool execution/results, maximum turns, and pre/post-execution validation.

Retain LangGraph and the existing model adapter, adding a custom tool loop without SDK migration or framework dependencies. Tool selection uses structured JSON compatible with the current provider, not provider-native function calling. A future native adapter can retain the same execution contract.

<a id="运行路径"></a>

## Runtime path

Fixed entry points, ordinary chat, existing follow-ups, corrections, permissions, and analysis admission retain their current flow. Free-form business conversation can use:

Intent/fact processing → tool catalog → one model-proposed action → server parameter/permission validation → execution → safe observation → next action or finish → existing output validation and one commit.

Tools: read_case_facts, check_fact_gaps, search_law, search_guidance, search_cases, prepare_analysis. finish is a control action. KnowledgeProvider remains the data layer; models receive no SQL, connection details, or arbitrary account/case IDs.

Model observations contain structured statuses, field names, evidence counts, gap reasons, executed tools, and remaining budgets only, excluding evidence originals and account keys. Final answers combine validated tool results; the scheduler cannot freely write tax conclusions.

<a id="强制边界"></a>

## Mandatory boundaries

- Support only the current Hong Kong dividend scope. Queries cannot alter user jurisdictions, periods, or identifiers; independent inquiries do not inherit old case filters.
- read_case_facts/check_fact_gaps are read-only for the current requested case; they neither confirm facts nor change gap consent.
- prepare_analysis requires explicit user request and fact confirmation/partial-consent admission. Fact changes in this turn require reconfirmation.
- Retain one main follow-up at a time and end the turn when waiting for the user. Final advisor review remains the only human decision stage.
- Share RunBudget, deduplicate parameter signatures, and allow at most one retrieval rewrite. Stop at budget limits while retaining results.
- Convert tool exceptions into statuses without raw error text; never switch automatically to Mock. JSON and SSE share preparation/commit paths.

<a id="开关与回滚"></a>

## Switches and rollback

```dotenv
FSIE_AGENT_ORCHESTRATION=hybrid
FSIE_AGENT_DYNAMIC_PLANNER=true
FSIE_AGENT_HARNESS_MODE=tools
```

Default harness_mode=rewrite retains the previous no-match query rewriting. tools applies only to business requests with entry_hint=auto; the three shortcuts retain current subgraphs. Enable in test environments first; switch to rewrite or disable dynamic_planner to roll back. Missing live model configuration must produce explicit failure, not claimed online success.

<a id="验收"></a>

## Acceptance

Cover multi-tool order, source types, read-only facts/gaps, duplicate-tool stopping, rejection of invalid parameters/identifiers/scope/unauthorized analysis, exclusion of restricted originals from planning, retained partial success after model failure, budget stopping, no extra scheduling for ordinary chat/fixed entry points, and existing JSON/SSE/follow-up/final-review regression. Actual C and models still need separate online acceptance.

<a id="实现与验证记录"></a>

## Implementation and validation

- `packages/agent/tools.py`: catalog, strict parameters, allowed actions, query validation.
- `packages/agent/tool_harness.py`: LangGraph plan/execute loop, metadata observations, deduplication, result retention, stopping.
- `packages/agent/harness.py::plan_tool`: production model selection and bounded JSON repair using the remaining deadline.
- `packages/agent/hybrid.py`: parent-graph integration, optionally enabled for free conversation; explicit multitask queues retain single execution to avoid duplicates/extra model calls.
- `tests/agent/test_tool_harness.py`: 31 engineering acceptance tests; scripted model choices and synthetic Mock retrieval.
- `tests/agent/test_real_eval.py`: retains production prompts/parser/LangGraph/actual message APIs/persistence, replacing model HTTP responses for workflow acceptance; not online success.

Online command (configure OpenRouter key privately in `.env`; at most four requests per script; select one first with a small quota):

```sh
.venv/bin/python scripts/evaluate_b_workflow.py --dataset evals/b_workflow/v0.1/tool_harness.json --harness-mode tools --select BWF-TOOLS-001 --max-calls 4 --output evals/b_workflow/runs/tool-live.json
```

Evaluation strictly checks tool sequences. If production intent parsing selects a predecomposed queue instead of the loop, record failure to meet this loop's acceptance rather than success. Engineering checks cover duplicate task execution across the two paths.

This preflight had two blocked scripts and zero model calls. Actual model tool-selection quality, C service, professional tax correctness, and PostgreSQL acceptance remain outstanding. No new free-form legal explanation node or similar-case comparison algorithm was added.

Final engineering regression (2026-10-04): 318 Python tests passed; 11 actual PostgreSQL tests not run; 26 existing page compatibility tests passed; TypeScript/Vite build, knowledge package, and two evaluation-set format checks passed. Python tests include JSON/SSE acceptance of the new loop. Page compatibility uses the original test service and does not establish actual model tool-selection quality.
