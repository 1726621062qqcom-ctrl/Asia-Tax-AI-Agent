<a id="l0-内部研究原型--验收记录"></a>

# L0 Internal Research Prototype — Acceptance Record

| Item | Details |
|---|---|
| Acceptance target | East Asian Tax AI Platform · Hong Kong FSIE foreign-sourced dividend L0 research prototype |
| Acceptance date | 2026-09-05 |
| Acceptance basis | [PRD section 11.1 (research prototype acceptance without expert validation)](../product/PRD.md), [2026 project plan section 9](PROJECT_PLAN_2026.md) |
| Branch | feat/fsie-data-extraction-validation-plan |
| Overall conclusion | **Engineering acceptance passed**. This record is not tax advice, does not establish completion of professional validation, and does not authorize any client use |

<a id="1-验收矩阵逐条对照-prd-111"></a>

## 1. Acceptance matrix (against PRD 11.1)

| Acceptance criterion | Result | Evidence |
|---|---|---|
| Source manifest required metadata is 100% complete; originals, versions, hashes, validity periods, and links are verifiable | ✅ | All 7 sources include URLs/hashes/effective periods/validation statuses. The 2026-09-04 pipeline recheck confirmed that Cap.112 XML and the 2022 Amendment Ordinance hashes match the manifest; drift was detected on 4 IRD pages and new snapshots were recorded |
| Candidate rules map explicitly to source passages | ✅ | All 6 rules map to source_ids; thresholds include statutory locations (s.15M(2), s.15N(7)); Cap.112 is segmented into 45 subparagraph-level legal units, allowing citations to resolve to original statutory text |
| Unverified rules and reports always show research-mode status | ✅ | The contract validator requires all rules/sources to remain `unverified` (changing them to verified rejects loading, as demonstrated by tests). The report watermark is hardcoded in the renderer with no switch parameter, as demonstrated by tests |
| Natural language, fact cards, rules, RAG, and reports work end to end | ✅ | Chinese natural-language case → model extraction of candidate facts (dictionary vocabulary only) → deterministic decision chain → persisted execution records → report with watermark and statutory citations; 6 natural-language cases + 1 injection attack case passed actual testing |
| Prompts or ordinary user operations cannot remove the professional validation gate | ✅ | Three guards: the validator rejects verified rules/sources; the model can propose only candidate facts constrained by the 43-field dictionary; terminal enums contain no tax-conclusion state, and human_gate cannot be bypassed by fabricated facts (live injection test) |
| Only fictional cases or cases with approved de-identification are used | ✅ | All 10 structured cases + 7 natural-language cases have `synthetic=true`; decision D-002 allows only synthetic data to enter the model at L0 |
| At least 10 versioned candidate cases run end to end on the frozen research evaluation set | ✅ | All 10/10 cases PASS with `make run-eval` (terminal states and blockers match the gold expectations case by case) |
| Any statute/provision/link in the evaluation set that cannot resolve to the source manifest blocks release | ✅ | The validator requires each rule's source_ids to resolve to the manifest; statutory citations are checked through persisted legal_units (queries find s.15M(2), among others) |

<a id="2-工程证据汇总"></a>

## 2. Engineering evidence summary

| Dimension | Count/details |
|---|---|
| Offline tests | 71 passed (contract drift, evaluator boundaries, renderer guards, segmenter, security guards, configuration seeds) |
| Live integration tests | 9 passed (evaluation runs, report reconstruction, natural-language gold terminal states, knowledge pipeline, injection resistance) |
| Gold evaluation cases | 10 (covering out of scope, outside the slice, receipt outside Hong Kong, failure of both thresholds, scope conflicts, substance escalation, human review, escalation, and research output) |
| Natural-language cases | 6 gold mappings + 1 injection attack fixture |
| Knowledge units | 669 (Cap.112: 45 subparagraph-level units; 2022 Ordinance: 62 pages; 4 IRD pages: 562 blocks) |
| Model | Token Plan · qwen3.8-flash (lowest-cost tier), receiving synthetic data only (D-002) |
| Database | 14 tables + 3 migrations (0001 baseline / 0002 knowledge layer / 0003 system configuration); three-step migration validation passed |

<a id="3-明确保留事项不在本验收范围内"></a>

## 3. Explicit reservations (outside this acceptance scope)

1. **Professional validation is incomplete**: no Hong Kong tax experts participated. All 6 rules and all case expectations are candidate engineering judgments, **not tax gold standards**.
2. **No tax conclusions are produced**: system terminal states comprise only three safe statuses. Any “exempt/taxable” statement is outside this system's output scope.
3. **Content drift on 4 IRD pages**: hashes changed relative to the 2026-09-01 manifest and new snapshots were recorded. Regulatory content review follows the maintenance procedure.
4. **L1 gates have not started**: the expert validation sprint, permissions/audit/backup recovery tests, and pilot data compliance plan have not begun.
5. **Coverage boundary**: only the Hong Kong foreign-sourced dividend slice; foreign-sourced interest, disposal gains, intellectual property income, and in-depth mainland China/Japan/South Korea content are outside L0.

<a id="4-结论与放行边界"></a>

## 4. Conclusion and release boundary

The L0 internal research prototype **passed engineering acceptance** and may be used for controlled internal research and engineering demonstrations.

This record explicitly prohibits using system outputs for real client cases, describing candidate rules as verified, or describing L0 as L1/L2 or any form of client release. The only route to L1 is through the PRD 3.4 gates: written validation by Hong Kong tax experts + completion of all security and operational gates.
