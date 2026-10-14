# Acceptance Testing Entry Point for the Current main

Use this page to begin the next round of live workflow testing. The [integrated setup and run guide](../../README_MERGED.md) is authoritative for detailed installation commands. See the [integration acceptance record](../implementation/COMBINED_INTEGRATION_ACCEPTANCE.md) for results from the previous checks; those are not results from this round.

See the [live workflow smoke test record](REAL_CHAIN_SMOKE_2026_10_12.md) for the first actual tests on 2026-10-12 and the assessment plan for the two evaluation tracks.

See the [live workflow acceptance record](REAL_CHAIN_ACCEPTANCE_2026_10_13.md) for the actual old/new path comparison, live chat, and rule traceability checks on 2026-10-13.

## Confirm the environment first

1. Install Python dependencies from the project root and build `apps/web`. Install the pinned Li component according to the integrated guide. The installer validates release files; failed validation does not count as a successful installation.
2. Configure cloud PostgreSQL, Supabase email authentication, and the model service in the Git-ignored `.env`. Do not put keys in commands, reports, or the repository.
3. Run `python -m scripts.run_combined` to start the combined route accepted in this round, and confirm that the page, sign-in, and health checks work. Cloud data storage does not mean the frontend and backend have been publicly deployed.

## Suggested testing sequence

| Stage | Entry point | Evidence to record |
|---|---|---|
| Code and frontend regression | `python -m pytest -q`, `npm --prefix apps/web run build` | Pass, fail, and skip counts, plus commit SHA |
| Database and C integration | `python scripts/check_combined_live.py --database-only --env-file .env.integration` | Source versions, citation retrieval, case recovery and isolation, and failure reasons |
| Combined workflow with a live model | `python scripts/check_combined_live.py --env-file .env.integration --model-env-file .env` | Actual model calls, questions and answers, sources, timings, and errors |
| Manual page operation | Current chat workspace and test accounts | Sign-in, the three entry points, fact confirmation, analysis, recovery after refresh, and export |
| Quality comparison | [Evaluation index](../../evals/README.md) | Old/new answers to the same questions, source matches, expert assessments, and timings |

Use `check_postgres_acceptance.py` for a complete repeat verification with a disposable database. It creates, migrates, and cleans up a test database, so read the [run guide](../../README_MERGED.md) first and confirm the connection being used. Evaluation reports should distinguish engineering acceptance, live model acceptance, and tax expert approval. Retrievable citations establish traceability but do not independently establish the correctness of a tax judgment.

The current `main` uses the pinned Li component release. Later commits on the C branch, including new traceability checks, require separate comparison and integration and cannot be counted as accepted on `main`. The early `demo/hk-web` also remains a separate branch.
