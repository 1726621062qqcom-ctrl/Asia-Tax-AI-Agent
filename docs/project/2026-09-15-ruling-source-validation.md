<a id="香港-fsie-新增裁定资料与实测"></a>

# New Hong Kong FSIE Ruling Sources and Actual Validation

On 2026-09-15, Cases 68, 72, 74, and 75 were downloaded directly from IRD; all four HTTP requests returned 200.
Sources, SHA-256 values, byte counts, capture times, ruling dates, and applicable years of assessment were added to source_manifest.json.
The main legal coverage cutoff remains 2026-09-01; this download does not establish review of subsequent legal changes.

<a id="新增内容"></a>

## Additions

| Case | Official source | Research use | Existing segmenter output |
|---|---|---|---|
| 68 | https://www.ird.gov.hk/eng/ppr/advance68.htm | Non-pure equity-holding entities, personnel, and outsourcing arrangements | 14 blocks |
| 72 | https://www.ird.gov.hk/eng/ppr/advance72.htm | Foreign-sourced dividend account paths, capital subscriptions, and participation route | 13 blocks |
| 74 | https://www.ird.gov.hk/eng/ppr/advance74.htm | Distinction between 60% ownership, a 25% corporate tax rate, and a 10% withholding rate | 12 blocks |
| 75 | https://www.ird.gov.hk/eng/ppr/advance75.htm | Dividends in kind and same-day onward distribution to the parent | 11 blocks |

Research cards in knowledge/hong_kong/fsie/ruling_research_cards.json record fact summaries,
official ruling summaries, passage locations, questions requiring validation, and existing system boundaries. The summaries were prepared manually and have not been professionally validated.
Source/node associations are research indexes only and do not alter the execution basis of rules.json.
IR1298B was not added in this round; case materials remain the priority.

<a id="实测结果"></a>

## Actual results

The existing fetch_source downloaded files to the Git-ignored raw directory; segment_html produced 50 text blocks.
Then scripts/inspect_ruling_sources.py reused the same snapshots and checked manifest hashes.
All 16 original-text spot checks matched; segmentation retained 12/16, losing the ruling dates in all four cases.
The existing generic HTML segmenter filters blocks shorter than 40 characters. Dates are stored separately in source metadata,
but the segmenter itself is not yet fixed. This targeted spot check does not establish 75% recall across all content.

Knowledge package validation passed: 11 sources, 6 rules, 8 evidence requirements, 10 synthetic cases; 71 offline tests passed.
No database import, LLM extraction, or end-to-end rule evaluation was performed. The 50 blocks are parsed outputs, not newly persisted records.
The current L0 model policy permits synthetic data only, so public cases were not sent to the model provider.
These public anonymous cases have synthetic=false and are excluded from the candidate evaluation set requiring synthetic=true.

<a id="复现"></a>

## Reproduction

Run in an environment with the project's dev dependencies installed:

```sh
python scripts/inspect_ruling_sources.py
python scripts/validate_fsie_package.py
python -m pytest -m "not integration"
```

The script captures only the four sources listed in the research cards. Existing snapshots are reused; this is not real-time update monitoring.
A new environment downloads official pages. If hashes differ from this round's pinned hashes, validation for that case stops and reports the difference.
Complete records are written to knowledge/hong_kong/fsie/raw/ruling_probe_report.json.
Output retained_in_units=false is a diagnostic finding. A successful exit means original-text probes and hashes passed,
not that segmentation was lossless. Official phrases are location probes only, not automatic tax decision criteria.

<a id="使用边界和后续实验"></a>

## Usage boundaries and future experiments

IRD public rulings are anonymized, apply only to specific facts, and are not updated after legal changes:
https://www.ird.gov.hk/eng/ppr/arc.htm

The next round can first fix date and section-association preservation, then run fact extraction experiments.
Separate factual backgrounds/arrangements from ruling answers. If the entire ruling is in the retrieval database, the same case cannot establish successful blind testing.
If model processing remains synthetic-only, write clearly labeled synthetic variants; do not relabel public cases as synthetic.
