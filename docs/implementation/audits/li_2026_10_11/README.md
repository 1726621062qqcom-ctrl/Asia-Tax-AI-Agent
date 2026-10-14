# Audit Record for the Earlier Li Release

> This is a historical record for c8a4cf7. The current 771e452 release has resolved the earlier missing items. See the [merged handoff README](../../../../README_MERGED.md) for current installation and acceptance testing entry points.

Audit date: 2026-10-11. Source: LiZiheng / c8a4cf7a59ef9d8895cd115ce2e4df66850b30e2.

Conclusion: the source code and actual database were obtained. The knowledge database can be opened and passed the retrieval spot checks performed in this audit. This release package cannot start the tax_graph domain engine.

- Database integrity checks passed; size: 210808832 bytes; SHA-256 matches the LFS pointer.
- Compiling 184 rule definitions produced 146 missing-reference errors affecting 37 rules. After deduplication, 74 parameters and eight statutory references are missing.
- All parameter rows in params.csv match SQLite, and the clause ID sets in clauses.csv and the database match. The missing items are also absent from the CSV files; rebuilding the database alone cannot supply them.
- The new source code references D14–D31, but the database's interpretation records contain only D01–D13.
- The root file `信息收集.md`, required by the optional document extractor, was not delivered.
- cases/battery contains no generated JSON. The repository includes the battery.py generator and two gold JSON files; cases can be generated and validated after repairing the data. Test results from an empty directory must not be reported as a pass.

Files: release_audit.json stores the complete machine-readable results; missing_references.csv lists deduplicated missing items and affected rules; compile_errors.txt stores the compiler's 146 original error lines; audit_release.py is the reproduction script.

Reproduce from the B repository root:

```bash
python3 docs/implementation/audits/li_2026_10_11/audit_release.py \
  ../Asia-Tax-AI-Agent-LiZiheng \
  docs/implementation/audits/li_2026_10_11
```

The script reads the source snapshot and writes only to the audit directory. Successful completion means the audit records were written; inspect compile_passed rather than treating the exit code as release acceptance. The actual rule compilation can be reproduced separately from the source directory:

```bash
python3 -m tax_graph.rules
```

This command fails on the audited snapshot. Repair release dependencies before running planner/engine checks; there is no need to repeatedly start all tests that depend on the same failing import.

Retrieval checks covered only four returned passages from exact and BM25 retrieval and their unique original-text locations. They did not validate the vector model, full retrieval coverage, legal conclusions, HTTP, PostgreSQL, the frontend, or live model multi-turn workflows. Rule compilation failures prevented end-to-end validation of the actual planner.
