# Evaluation Index

This directory stores reproducible evaluation inputs and historical run results; `tests/` is used for automated code regression. Historical scores do not directly represent the live workflow performance of the current `main`.

| Material | Coverage | Usage notes |
|---|---|---|
| [A-side test records](../docs/project/evaluations/README.md) | Retrieval and chat retesting with 20 questions, plus result spreadsheets | Uses historical questions and criteria; rerun on the current version and manually check citations and answers |
| [B multi-turn business evaluations](b_workflow/README.md) | 62 synthetic scripts, 135 steps | Expected engineering behavior is not a tax expert gold standard; the historical online workflow did not fully pass |
| [Integration acceptance record](../docs/implementation/COMBINED_INTEGRATION_ACCEPTANCE.md) | Engineering integration of the pinned tax engine release, PostgreSQL, and C HTTP | Records results from the previous environment; live models, normal account pages, and professional correctness still require repeat verification |

For the next round, fix the questions, versions, and source snapshots before comparing the old and current strategies. For each question, check whether the statutory provisions, cases, and rules cited in the answer can be retrieved, and record recall, citation accuracy, answer correctness, and timings separately. See the [acceptance testing entry point](../docs/verification/README.md) for the detailed execution order.

## Historical output archive

The October 2026 B-workflow run outputs are grouped under [archive/b-workflow-2026-10](archive/b-workflow-2026-10/). Active evaluation inputs remain in `b_workflow/v0.1/`; the evaluation script still writes new runs to `b_workflow/runs/`.
