# Packages

This directory contains reusable business and technical modules.

Rule execution, RAG retrieval, and case evaluation must remain separate. Retrieval results must not be treated directly as deterministic rule conclusions or evaluation gold standards.

## Existing modules

- [`contracts/`](contracts/): data contracts shared across jurisdictions, including state machine enums, asset JSON Schemas, Python enums, and the Hong Kong FSIE fact field dictionary. These are shared upstream definitions for the database, rule engine, fact cards, and cases. See [contracts/README](contracts/README.md).
- `intake/`: natural-language fact extraction, dictionary validation, and command-line entry point.
- `model_adapter/`: model service configuration and call adaptation.
- `knowledge_loader/`: knowledge package parsing, validation, and database loading.
- `knowledge_pipeline/`: official source capture, snapshots, and legal text segmentation.
- `rule_engine/`: deterministic rule chains and fictional case evaluation.
- `persistence/`: database models, connections, and system settings.
- `reporting/`: research report assembly and Markdown output.
