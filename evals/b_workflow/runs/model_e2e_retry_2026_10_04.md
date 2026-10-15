<a id="b-agent-实际模型评测记录"></a>

# B Agent Live Model Evaluation Record

Time: 2026-10-04T05:07:27.750788+00:00. Layer: M-model/D-knowledge/API. Model: qwen/qwen3.8-27b:free.

Selected 3 scripts; 0 passed, 3 failed, 0 blocked.

Actual model calls: 6. Overall status: incomplete.

Retrieval and identity use synthetic test doubles. These results do not establish actual C, sign-in, PostgreSQL, or professional tax acceptance.

| Script | Status | Issue |
|---|---|---|
| BWF-E2E-001 | failed | error expected=None actual=model_failed |
| BWF-021 | failed | reason expected=no_match actual=planner_failed |
| BWF-035 | failed | fact dividend_amount expected=2000000 actual='conflict' |
