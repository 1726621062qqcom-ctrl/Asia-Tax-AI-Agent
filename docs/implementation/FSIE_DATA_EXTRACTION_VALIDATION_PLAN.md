<a id="香港-fsie-数据提取与校验实施计划"></a>

# Hong Kong FSIE Data Extraction and Validation Implementation Plan

| Item | Details |
|---|---|
| Version | v0.1 |
| Date | 2026-08-21 |
| Scope | Hong Kong FSIE foreign-sourced dividend L0 research prototype |
| Status | Plan defined; rules remain `unverified` |
| Objective | Trace every fact, rule, number, and report conclusion to originals, validation records, and versions |

<a id="1-目标与非目标"></a>

## 1. Objectives and non-goals

<a id="11-目标"></a>

### 1.1 Objectives

Establish a repeatable, pausable, auditable workflow:

```text
Official originals
→ Source snapshots
→ Text/layout parsing
→ Legal unit segmentation
→ AI candidate extraction
→ Automated consistency checks
→ Professional confirmation
→ Versioned rules and facts
→ Node-by-node case assessment
→ Research reports with traceable citations
```

Every downstream result must identify:

- Original file/version/page or provision.
- Extractor, model, and prompt version.
- Passed/failed automated checks.
- Who confirmed, changed, or rejected it and when.
- Jurisdiction, income type, case date, and rule version.

<a id="12-非目标"></a>

### 1.2 Non-goals

- No automatic formal tax advice in the first phase.
- No LLM-memory completion of missing legal sources/rates.
- No automatic elevation of FAQs, examples, or secondary materials to legal rules.
- No client data in current L0 evaluation.
- No exempt/taxable conclusions without confirmed legal sources, rules, and critical facts.
- No complete mainland China/Hong Kong/Japan/South Korea tax coverage in this plan.

<a id="2-可信度分层与状态机"></a>

## 2. Trust layers and state machines

Every asset has a status and follows prescribed transitions:

```text
discovered
  → captured
  → parsed
  → candidate
  → machine_checked
  → human_review
  → verified
  → active
```

Any stage may enter:

- `rejected`: incorrect, inapplicable, or unexplained content.
- `stale`: changes after the legal coverage cutoff.
- `blocked`: unresolved conflict, missing originals, parsing failure, or security issues.

`candidate`, `machine_checked`, and `human_review` do not participate in professional calculations. `active` requires reviewed rules, sources, and necessary evidence. Withdrawn rules retain historical versions; never overwrite versions used by old reports.

<a id="3-数据资产与契约"></a>

## 3. Data assets and contracts

<a id="31-来源记录-sourcerecord"></a>

### 3.1 Source records `SourceRecord`

Initial file: [source_manifest.json](../../knowledge/hong_kong/fsie/source_manifest.json). Each source stores at least:

- `source_id`, title, publisher, original URL, jurisdiction, language.
- Type: legislation, amendment, official guidance, FAQ, example, advance ruling.
- Publication, effective, expiry, and capture times.
- Original hash, format, size, snapshot location.
- Authority level, associated nodes, replacement versions, coverage gaps.
- `parse_status`, `professional_validation_status`, validator, validation time.

Sources and rules are separate. Capturing a source does not validate a rule; engineering completeness is not professional completeness.

<a id="32-来源快照-sourcesnapshot"></a>

### 3.2 Source snapshots `SourceSnapshot`

Store immutable originals in object storage or content-addressed directories:

```text
raw/{source_id}/{retrieved_at}/{sha256}.{extension}
```

Changed URL content creates new snapshots without overwriting old files. Record capture tool version, HTTP status, content type, redirects, verification hash, and failure reasons. Restricted originals must not enter Git; commit only approved metadata, hashes, and parsed results.

<a id="33-法律单元-legalunit"></a>

### 3.3 Legal units `LegalUnit`

Smallest locatable extraction/citation objects, containing at least:

- `unit_id`, `source_id`, version hash, page/chapter/provision/paragraph location.
- Original text, language, parsing method, surrounding context, text hash.
- Table, footnote, definition, exception, or amendment markers.
- OCR quality, character anomalies, manual proofreading status.

Citations cannot contain only context-free vector fragments. Reports must open originals and highlight complete legal units.

<a id="34-候选规则-rulecandidate"></a>

### 3.4 Rule candidates `RuleCandidate`

Extend the existing [rules.json](../../knowledge/hong_kong/fsie/rules.json) approach with:

- Rule ID, node, purpose, scope.
- Inputs, evidence, prerequisites, exceptions, output statuses.
- Applicability dates, source `unit_id`, extracted quotation, adjacent context.
- Candidate values, extraction model/prompt versions, checks, differences.
- `unverified/verified/rejected` and professional review records.

Prefer statuses such as `in_scope`, `unknown`, `condition_not_demonstrated`, and `human_review_required`. Missing facts must not become satisfied or not satisfied.

<a id="35-事实与证据-factcandidate--fact"></a>

### 3.5 Facts and evidence `FactCandidate` / `Fact`

Distinguish:

- Original client statements.
- AI-extracted candidate facts.
- Advisor-confirmed facts.
- Externally evidenced facts.
- Assumed, unknown, conflicting, and stale facts.

Each stores field, value, unit/currency, period, source text, evidence file, confidence, confirmation status, history, and affected nodes. LLMs write only to candidates; advisor confirmation precedes rule inputs.

<a id="4-端到端提取流程"></a>

## 4. End-to-end extraction

<a id="阶段-a来源发现与抓取"></a>

### Stage A: discovery and capture

Inputs: official entry points, approved URLs, previous snapshots.

Steps:

1. Allow only manifest-listed official HTTPS sources.
2. Record redirects/types; reject unexpected domains/suspicious downloads.
3. Save originals, calculate SHA-256, record time.
4. Compare old/new snapshots at byte and structural levels.
5. Emit `captured`; failures become `blocked`, never silently continue.

Exit: replayable originals, verifiable hashes, complete metadata.

<a id="阶段-b格式解析与-ocr"></a>

### Stage B: parsing and OCR

Input: immutable snapshots.

Order:

1. Parse searchable PDF/HTML/Word while retaining layout information.
2. Send scans to a separate OCR queue, retaining page images/OCR versions.
3. Identify tables, footnotes, definitions, amendments separately.
4. Check percentages, numbers, decimals, minus signs, dates, and provision identifiers for character anomalies.
5. Block low-quality OCR/unstable structures before extraction.

Exit: each passage maps to the original page/region; text hashes are reproducible.

<a id="阶段-c法律单元切分与分类"></a>

### Stage C: legal segmentation/classification

Segment by provisions, paragraphs, definitions, conditions, exceptions, tables, and footnotes, not arbitrary character counts. Classifiers may assist; humans must be able to correct boundaries/types.

Retain:

- Surrounding context.
- Provision hierarchy.
- Cross-references.
- Amendment relationships.
- Distinction between legislation and explanatory materials.

<a id="阶段-dllm-候选提取"></a>

### Stage D: LLM candidate extraction

LLMs produce strict structured candidates, not tax conclusions. Each field includes:

```json
{
  "field": "minimum_holding_period",
  "value": null,
  "unit": "months",
  "source_quote": "Complete quotation from the original source",
  "source_unit_id": "...",
  "extraction_status": "not_found",
  "needs_human_review": true
}
```

Mandatory rules:

- Numbers absent from quotations return `not_found`.
- Numbers, percentages, periods, amounts, and dates use typed fields.
- Do not infer general statutory thresholds from FAQ examples.
- Do not merge jurisdictions or effective periods.
- Low confidence, multiple candidates, or contextual conflicts enter human queues.

<a id="阶段-e自动提取校验"></a>

### Stage E: automated validation

Checks identify obvious errors, not legal approval:

- **Quotation existence:** locate candidate values in quoted text.
- **Types:** valid percentages, amounts, dates, periods, enums.
- **Ranges:** block unreasonable values without automatic correction.
- **Units:** distinguish HKD, foreign currencies, percentages, months/years.
- **Time:** align case dates with effective periods.
- **Sources:** correct jurisdiction/authority.
- **Logic:** exceptions cannot trigger without primary conditions.
- **Cross-references:** cited provisions exist in consistent versions.

Retain candidates/errors on any failure; set `blocked` or `human_review`.

<a id="阶段-f专业审核与激活"></a>

### Stage F: professional review/activation

Reviewers inspect originals, context, candidates, check reports, and history, then choose:

- `verified`: usable within defined scope.
- `rejected`: incorrect extraction/interpretation.
- `needs_scope_change`: additional fields, exceptions, or jurisdiction dimensions required.
- `needs_more_evidence`: insufficient materials for approval.

High-impact rules, thresholds, anti-abuse rules, and matters the model cannot determine require at least a second reviewer or written expert confirmation. Record reasons; a pass button alone is insufficient.

<a id="5-公司事实提取与匹配"></a>

## 5. Company fact extraction/matching

<a id="51-事实采集顺序"></a>

### 5.1 Collection order

1. Company/group identity and case date.
2. Income type, payer, recipient, source jurisdiction, receipt method.
3. Ownership, period, direct/indirect relationships, beneficial owner.
4. Foreign taxation/underlying profits.
5. Hong Kong personnel, premises, activities, spending, decisions, outsourcing oversight.
6. Commercial purpose, restructuring, hybrid mismatches, other judgment facts.
7. Evidence and confirmation questions.

Prioritize conclusion blockers. Advisors may answer unknown, provide later, not applicable, or analyze under assumptions. Unknown never becomes negative.

<a id="52-事实匹配算法"></a>

### 5.2 Matching algorithm

For each `case_id + income_event_id + tax_period`:

1. Load `active` rules for dates/jurisdiction.
2. Read the currently confirmed fact card version.
3. Produce `satisfied / not_satisfied / unknown / conflict / human_review_required` per node.
4. Compute dependencies; rerun only affected nodes on critical changes.
5. Produce evidence gaps, rule versions, source units, stop reasons.
6. Allow structured research results only when deterministic prerequisites are met without blockers.

<a id="6-校验测试和回归体系"></a>

## 6. Validation, tests, regression

<a id="61-测试层级"></a>

### 6.1 Testing layers

- Capture: domains, statuses, types, hashes, redirects.
- Parsing: page count, text length, tables, OCR characters, page locations.
- Extraction units: known numbers/dates, negations, exceptions, not-found cases.
- Rules: normal, boundary, missing, conflict, effective periods, version changes.
- Facts: entities, amounts, currencies, dates, ownership, fund flows.
- Citations: every substantive result resolves to `source_manifest + legal_unit`.
- Security: injection, malicious files, unauthorized access, tenant isolation, sensitive logs.
- End to end: fictional cases from input to stopping/research reports.

<a id="62-质量指标"></a>

### 6.2 Quality metrics

Initially use interpretable metrics only:

- Required source metadata completeness: 100%.
- Original hash/version replayability: 100%.
- Critical numeric citation locatability: 100%.
- Silent omission of blocking questions: 0%.
- Unverified rules entering calculations: 0%.
- Unresolved legal sources/links in evaluation: 0%.
- Structured result consistency for identical facts/rules/dates: 100%.
- Every candidate case retains validation status/error records.

Before expert pilots, add fact recall, citation acceptance, advisor revisions, and correct high-risk escalation. Record test set versions, denominators, formulas, thresholds, evidence, and approvers.

<a id="63-测试数据原则"></a>

### 6.3 Test data principles

- L0 uses fictional or approved de-identified cases only.
- Every case declares dates, expected questions, gaps, and stopping states.
- Candidates are not tax gold standards.
- Expert-confirmed gold versions are separate and immutable, not candidate overwrites.
- Any unresolved manifest statute/provision/link blocks release.

<a id="7-失败处理与变更管理"></a>

## 7. Failure and change management

Stop automatic conclusions for missing originals, changed hashes, inadequate OCR, nonexistent citations, numeric conflicts, stale rules, unknown critical facts, contradictions, injection, expert rejection, or failed permission tests.

For regulatory changes:

1. Compare snapshots.
2. Set affected sources/rules `stale/potentially_stale`.
3. Freeze affected nodes.
4. Generate an impact review list.
5. Publish new rules after expert confirmation.
6. Find historical reports using old versions; add impact notices without changing old results.

<a id="8-实施顺序与交付物"></a>

## 8. Implementation order/deliverables

<a id="iteration-1契约与清单"></a>

### Iteration 1: contracts/catalogs

- Source, unit, candidate rule, fact, evidence, validation-event schemas.
- Validate current JSON packages.
- Pin state machines/stopping states.

<a id="iteration-2受控来源管线"></a>

### Iteration 2: controlled source pipeline

- Official capture, redirect restrictions, hashes, snapshots, failures.
- PDF/HTML/Word parsing and page locations.
- Initial Hong Kong FSIE manifest/parsing report.

<a id="iteration-3法律单元与候选提取"></a>

### Iteration 3: legal units/candidate extraction

- Segmentation, provision locations, tables/footnotes.
- Strict JSON LLM extraction.
- Candidate values, originals, automated checks.

<a id="iteration-4专家审核工作流"></a>

### Iteration 4: expert review

- Queues, differences, approve/reject/return, records.
- Only verified rules become `active`.
- Initial expert review packages.

<a id="iteration-5公司事实卡与规则匹配"></a>

### Iteration 5: company cards/rule matching

- Fictional input, candidate facts, confirmation, conflicts, gaps.
- Execute per `case + income event + tax period`.
- Research-mode node results/stopping reasons.

<a id="iteration-6回归与-l0-发布门槛"></a>

### Iteration 6: regression/L0 gates

- At least 10 versioned candidates.
- Source, parsing, extraction, rule, citation, security tests.
- Coverage/error/staleness/review reports.
- Any failed blocker retains L0 research status and prevents advisor pilots.

<a id="9-角色与审批责任"></a>

## 9. Roles and approval

| Work | Responsible | Final approval |
|---|---|---|
| Capture/completeness | Engineering lead | Engineering lead |
| Legal parsing | Knowledge operations lead | Knowledge operations lead |
| Rule interpretation/thresholds | Rule engineer | Hong Kong expert |
| Fields/interview order | Product/rule owner | Hong Kong expert |
| Prompts/extraction evaluation | AI/engineering lead | Engineering lead + expert spot checks |
| Release/security/backups | Security/platform lead | Release owner |

Roles are unassigned without names; M0 must record actual owners.

<a id="10-完成定义"></a>

## 10. Definition of done

The first phase completes only when:

- Replayable manifests and complete original hashes/versions.
- Report citations navigate to originals.
- All candidate extractions have originals/machine checks.
- Linked rule/fact/report versions.
- Unknown/conflict/stale statuses never silently produce conclusions.
- 0% unverified rules enter calculations.
- Repeatable fictional cases produce consistent structured states.
- Expert records distinguish verified rules from evidence gaps.
- Security/permissions/backup/recovery tests pass.
- Repository/runtime contain no client data, keys, or unapproved restricted originals.

<a id="11-当前包与下一步"></a>

## 11. Current package and next step

The current [Hong Kong FSIE candidate package](../../knowledge/hong_kong/fsie/README.md) provides 6 candidate sources, 6 candidate rules, 8 evidence requirements, and 3 fictional cases. Prioritize Iteration 2's controlled pipeline and expert confirmation of initial nodes. Until then, candidate rules must not be described as validated.
