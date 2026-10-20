# Scripts

This directory contains repeatable scripts for source processing, indexing, validation, migration, and development support.

Common entry points are grouped by purpose below. Use `python scripts/<script_name> --help` for specific arguments. See the [acceptance testing entry point](../docs/verification/README.md) for execution order and environment requirements.

**Startup and pinned dependencies**

- `run_chat.py`: starts FastAPI and the built frontend.
- `run_combined.py`: starts the built frontend, FastAPI, and the pinned knowledge service, using the accepted hybrid + combined route.
- `install_li_release.py`: downloads and validates the Li release specified in the integration guide and installs it in a local directory ignored by Git.

**Sources and offline checks**

- `validate_fsie_package.py`: validates the integrity of source, rule, evidence, and fictional case references in the Hong Kong FSIE candidate knowledge package.
- `inspect_ruling_sources.py`: checks content retention for four official ruling sources, reusing local snapshots. Results are stored in the Git-ignored raw source directory.

**Integration and evaluation**

- `check_postgres_acceptance.py`: creates a disposable PostgreSQL database, validates migrations, knowledge building, persistence, and the actual HTTP/Li combined workflow, and cleans up afterward. The originally configured database is not migrated or emptied.
- `check_combined_live.py`: combined live model and PostgreSQL acceptance testing; also supports mutually exclusive `--model-only` / `--database-only` modes. Use `--model-env-file` for separate configuration. See the [merged README](../docs/setup/README.md) for run instructions.
- `evaluate_retrieval.py`, `evaluate_chat.py`: rerun the historical A-side retrieval and chat question sets. See the [evaluation records](../docs/project/evaluations/README.md) for interpretation.
- `evaluate_b_workflow.py`: evaluates B-side multi-turn business scripts. See the [script guide](../evals/b_workflow/README.md) for inputs and known limitations.
- `evaluate_fsie_user_cases.py`: six live workflow experiments using detailed questions and step-by-step facts for three synthetic Hong Kong FSIE cases. See the [Chinese and English experiment reports](../docs/project/evaluations/README.md) for results and assessments. Raw run records are written to the Git-ignored `reports/` directory.

Scripts should support explicit inputs, auditable outputs, and failure states. They must not write keys or client data to the repository.
