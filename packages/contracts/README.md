# FSIE Data Contract

| Item | Details |
|---|---|
| Version | v0.1 (initial contract release) |
| Date | 2026-09-01 |
| Scope | L0 Hong Kong foreign-sourced dividend vertical slice; all four jurisdictions share the same contract structure |
| Status | Candidate contract; professional semantics remain `unverified`, but structural and naming consistency is mandatory from now on |
| Related documents | [Data extraction and validation plan](../../docs/implementation/FSIE_DATA_EXTRACTION_VALIDATION_PLAN.md) · [Datasets and data sources](../../docs/architecture/DATA_SOURCES_AND_DATASETS.md) · [Technical roadmap](../../docs/architecture/TECHNICAL_ROADMAP.md) |

## 1. Why define a contract first?

The contract is the **shared upstream definition** for database tables, the rule engine, fact cards, cases, and APIs. Defining the objects, their fields, permitted values, and state transitions before building applications and tables avoids repeated schema changes and inconsistent field names across files. It corresponds to **Iteration 1: contracts and catalogs** in the data plan.

The contract defines **structures and values**, not tax conclusions. All professional semantics remain `unverified` throughout L0.

## 2. Contract components and responsibilities

| Component | Location | Responsibility | Consumers |
|---|---|---|---|
| Shared enums / common structures | `json_schemas/definitions.schema.json` | **Authoritative source** for state machines, node keys, and value domains | All schemas and documentation |
| Asset JSON Schemas (7 files) | `json_schemas/*.schema.json` | Structures for SourceRecord / LegalUnit / RuleNode / EvidenceRequirement / FactRecord / FactField / CandidateCase | IDEs, backend models, and validation |
| Python enums | `enums.py` | Code constants matching definitions one-to-one, eliminating magic strings | Backend, migrations, and scripts |
| Fact field dictionary (DS-03) | `fact_dictionary/hk_fsie_fact_fields.v0.json` | System-wide fact fields, types, units, blocking levels, associated nodes, and evidence | Rules, fact cards, cases, and table definitions |

`definitions.schema.json` and `enums.py` **must match**. `scripts/validate_fsie_package.py` cross-checks them and fails on drift.

## 3. Defined state machines (keep them separate)

The system has several independent state machines, each governing a different layer:

| State machine | Values | Used for |
|---|---|---|
| Asset lifecycle | discovered→captured→parsed→candidate→machine_checked→human_review→verified→active; rejected/stale/potentially_stale/blocked may occur at any stage | Knowledge assets such as sources, legal units, and rules |
| Professional validation status | unverified / verified / rejected | Sources and rules; only Hong Kong tax experts may set verified |
| Fact confirmation status | client_statement / ai_candidate / advisor_confirmed / externally_evidenced / assumed / unknown / conflict | Each runtime fact; the LLM may write only ai_candidate |
| Rule node output | satisfied / not_satisfied / unknown / conflict / condition_not_demonstrated / human_review_required | Execution result of an individual rule node |
| Case terminal status | research_only_output / stop_and_escalate / human_review_required | Result of aggregating all nodes at the human gate |
| Evidence status | provided / missing / conflict / not_applicable | Evidence items |
| Case workflow status | draft/interviewing/waiting_*/analyzing/needs_human_judgment/pending_review/approved/invalidated/archived | Case lifecycle (PRD section 9) |
| Blocking level | scope_blocking / conclusion_blocking / supporting | Fact fields that block scope, block conclusions, or provide supporting information |

**Strict rule: missing facts can produce only unknown / condition_not_demonstrated; they must never be mapped to not_satisfied (a negative finding).**

### 3.1 Two design decisions that are easy to confuse

1. **Separate a fact's value from its confirmation status.** At runtime, the `value` field of `FactRecord` contains only the business value; who confirmed the fact is recorded in `confirmation_status`. Values such as `candidate_yes`, which combine status and value, are therefore no longer used. Inline `facts` in candidate cases contain only business values or the sentinel values `unknown/conflict/assumed/not_applicable`; the `ai_candidate` status is attached consistently when loading them into fact cards.
2. **Node outputs differ from case terminal statuses.** An individual node outputs only NodeOutputStatus. Case terminal statuses such as `research_only_output` result from aggregation of all nodes at the human gate and are not written into individual node outputs.

## 4. Naming conventions

- Use `snake_case` throughout.
- Use the suffix `_pct` for percentages, with values from 0–100; use `_months` for durations in integer months and `_date` for dates.
- Represent amounts with a numeric `_amount` field paired with an ISO 4217 `_currency` field.
- Use controlled enums for uncertain judgments rather than plain booleans, so that unknown/conflict can be represented.
- Evidence types must use the 26 controlled terms in the field dictionary's `controlled_evidence_types`; do not invent aliases.

Historical inconsistencies resolved in this contract: `holding_percentage`→`holding_percentage_pct`, `continuous_holding_period`→`continuous_holding_period_months`, `receipt_account`→`bank_or_account_path`; aggregated economic substance fields were split into specific fields such as `hk_adequate_employees/hk_adequate_premises/...`; blockers now reference actual field names instead of free text.

## 5. Standard decision-chain node keys (PRD 5.2: ten steps + human gate)

| ordinal | node key | IRO basis (checked) |
|---|---|---|
| 1 | scope | s.15H |
| 2 | income_characterisation | s.15H/s.15I |
| 3 | receipt | s.15I |
| 4 | financial_entity_exclusion | s.15H/s.15I (reserved; no L0 rule yet) |
| 5 | economic_substance | s.15K |
| 6 | participation_basic | s.15M (5% / 12-month thresholds in s.15M(2)) |
| 7 | foreign_tax_switchover | s.15N(2)(5); 15% reference rate in s.15N(7) |
| 8 | anti_hybrid | s.15N(3) (reserved; no L0 rule yet) |
| 9 | main_purpose | s.15N(4) (reserved; no L0 rule yet) |
| 10 | compliance_filing | s.15J/s.15S (reserved; no L0 rule yet) |
| 0 | human_gate | Cross-cutting gate, not a sequential step |

Rule `ordinal` values must match this table; validation enforces this. The current rule library implements six nodes (1/2/3/5/6 + gate). The contract reserves the four missing nodes; completing them is a next step outside this contract's scope.

## 6. Fact field dictionary (DS-03)

`fact_dictionary/hk_fsie_fact_fields.v0.json` defines **43 fields** and **26 controlled evidence types** across the eight fact domains in PRD FR-03. Each field includes its domain, type, unit, enum, blocking level, associated nodes, required evidence, whether it is required for the first vertical slice (`l0_first_slice`), statutory reference, and Chinese description.

- Approximately 22 fields have `l0_first_slice=true`. These are the fields that must actually be persisted and processed end to end in the first walking skeleton; the remaining fields are reserved for completing all ten nodes, avoiding later dictionary rework.
- New fields must be added to the dictionary and pass validation. Rules, cases, APIs, and table structures may reference only fields defined in the dictionary.

## 7. How to use this contract

- **Backend models**: generate pydantic models from the JSON Schemas, or write them manually while preserving consistency. Business code must use `from packages.contracts.enums import ...` rather than bare strings.
- **Database migrations (next step)**: map contract fields to tables as follows:
  - `SourceRecord`→`legal_sources`, `LegalUnit`→`legal_passages` (full text + future vector columns).
  - `RuleNode`→`rule_sets/rule_nodes` (Git remains authoritative for rule definitions; the database stores release records and `rule_executions`).
  - `FactRecord`→`facts/fact_versions` (separate value and confirmation status columns naturally support version history).
  - `CandidateCase`→`evaluation_cases`, execution results→`evaluation_runs/results`.
  - Dictionary enums→database CHECK constraints or lookup tables; every business table includes `organization_id` from day one.
- **Validation**: `python3 scripts/validate_fsie_package.py` performs both package safety checks and cross-file contract consistency checks for fields, evidence, nodes, enums, blockers, and enum drift.
- **IDE**: associate each JSON file with its schema in an editor supporting JSON Schema to enable field completion and immediate error reporting.

## 8. v0 scope and outstanding work

**Completed in this release**: enums/state machines, seven asset schemas, a 43-field dictionary, Python enums, dependency-free cross-file validation, and alignment of the existing rules/evidence/cases knowledge packages with the contract (validation passed).

**Outstanding work for later steps**:

1. Complete the four missing rule nodes (4/8/9/10); this is rule completion, not contract work.
2. Segment LegalUnit instances (schemas are ready; source pipeline output is pending), then populate `source_unit_id` for candidate rule thresholds.
3. Build database tables and migrations and backend pydantic models (the contract is their input; this directory does not create tables).
4. Add a general-purpose JSON Schema structural validator (current validation uses targeted, dependency-free cross-file checks; complete structural validation will follow backend pydantic integration).

## 9. Change process

The contract is a shared upstream dependency and requires careful changes: update enums/fields → synchronize `definitions.schema.json` and `enums.py` → synchronize affected knowledge packages → run validation until it passes → record version changes here. Any commit that causes `validate_fsie_package.py` to fail must not be merged.
