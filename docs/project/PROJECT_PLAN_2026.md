<a id="东亚税务-ai-平台--2026-项目计划"></a>

# East Asian Tax AI Platform — 2026 Project Plan

| Item | Details |
|---|---|
| Plan version | v0.2 |
| Date | 2026-08-15 |
| Target release date | 2026-12-18 |
| Release scope | Hong Kong L0 in-depth research MVP; mainland China, Japan, and South Korea source-catalog baseline |
| In-depth MVP | Hong Kong foreign-sourced dividend FSIE |
| Related documents | [PRD](../product/PRD.md) · [Technical roadmap](../architecture/TECHNICAL_ROADMAP.md) |

<a id="1-年度交付目标"></a>

## 1. Annual delivery objectives

Deliver East Asia Release 1 in 2026, rather than a Hong Kong-only tool. All four jurisdictions share the platform, source standards, versioning, RAG citations, and professional validation statuses. Acceptance defaults to a conservative resource baseline; standard research package stretch objectives are enabled only when additional resources become available.

- Hong Kong: complete the L0 internal research prototype for foreign-sourced dividend FSIE; progress to an L1 closed advisor pilot if expert validation and engineering security gates finish in time.
- Mainland China, Japan, and South Korea: complete `source-catalog baseline`, providing traceable official source catalogs, shared metadata, topic classifications, validity periods, coverage gaps, and validation statuses.
- Extending all eight topic categories in mainland China, Japan, and South Korea to `standard research package` is enabled only if a second full-time engineer and a knowledge operations owner are confirmed by 2026-08-31.
- Platform: support unified search, source versions, content levels, permissions, and audit across four jurisdictions.
- Add no other Asia-Pacific jurisdictions in 2026.

<a id="11-发布等级"></a>

### 1.1 Release levels

| Level | Meaning | Default 2026 commitment |
|---|---|---|
| L0 internal research prototype | Project team uses fictional cases or data with approved de-identification; outputs only engineering demonstrations marked as research | Yes |
| L1 closed advisor pilot | Authorized Hong Kong tax advisors use approved pilot cases; outputs only internal drafts for advisor review | Conditional: enabled after all Hong Kong expert and security gates pass |
| L2 production client capabilities | Product capabilities for formal clients | No |

If L1 gates do not pass, M6 accepts L0 only; L0 must not be described as a client release.

<a id="2-各地区完成标准"></a>

## 2. Completion standards by jurisdiction

<a id="21-香港"></a>

### 2.1 Hong Kong

- Natural-language interviews and fact cards.
- Candidate and validated rule statuses for foreign-sourced dividends.
- RAG and itemized official citations.
- Internal review drafts, human judgment, and audit.
- At least 10 versioned candidate cases for L0; 30–50 gold cases with an expert-confirmed coverage matrix for L1.
- Retain research watermarks and do not enter real client pilots without experts.

<a id="22-中国内地日本韩国"></a>

### 2.2 Mainland China, Japan, and South Korea

Under the conservative baseline, each jurisdiction delivers at least:

- A first-party official source catalog.
- Shared metadata, validity periods, capture times, and versions.
- Tax topic classifications.
- Content coverage, gaps, and professional validation statuses.
- At least 1 first-party official entry point for every declared topic.
- 100% completeness of required metadata and 0 broken links in the release snapshot.

If additional resources are confirmed on time, enable the `standard research package` stretch objective, covering:

- Corporate income tax.
- VAT, consumption tax, or the corresponding local turnover tax.
- Cross-border withholding taxes on dividends, interest, and royalties.
- Tax residence and permanent establishments.
- Transfer pricing.
- Major anti-avoidance rules.
- Tax treaty entry points.
- Major filing cycles.
- Official materials, validity periods, capture times, and versions.

These remain research packages and need not match the complete capabilities of Hong Kong's in-depth natural-language Agent. The interface and acceptance records must show whether each jurisdiction currently has a `source-catalog baseline` or a `standard research package`.

<a id="3-并行工作流"></a>

## 3. Parallel workstreams

| Deliverable | Accountable owner | Prerequisites | December delivery | Fallback on failure |
|---|---|---|---|---|
| Tax package schema and source pipeline | Technical lead | Tenant strategy, source schema | Common data and retrieval foundation for four jurisdictions | Retain batch import and versioning; defer administration UI |
| Hong Kong vertical prototype | Hong Kong MVP owner | Candidate cases, Hong Kong source manifest | L0 in-depth research MVP; L1 if conditions are met | Retain a single foreign-sourced dividend path; defer noncore interactions |
| Three-jurisdiction source packages | Knowledge operations owner | Tax package schema, language processing | source-catalog baseline | Do not enable standard research package stretch objectives |
| Expert review package | Product/professional validation owner | Decision tree, question list, candidate cases | Explicit validation statuses and gaps | Retain L0; cancel L1 |
| Security and release | Technical/security owner | Final deployment, authentication, backups | L0 release checks; L1 if conditions are met | Do not enter L1 |

One person may hold multiple roles, but every deliverable must have exactly one Accountable owner. Record names in the first weekly plan.

<a id="4-倒排计划"></a>

## 4. Backward schedule

<a id="8-月-16-日8-月-31-日统一基础"></a>

### August 16–August 31: common foundation

- Freeze the four-jurisdiction scope and tax topic list.
- Define the jurisdiction tax package format.
- Establish PostgreSQL, source acquisition, parsing, and versioning frameworks.
- Begin Hong Kong materials and candidate rules.
- Establish official source catalogs for mainland China, Japan, and South Korea.
- Begin searching for a part-time Hong Kong tax expert.
- Decide case sources and de-identification procedures by August 20; use fictional cases only until decided.
- Decide model data retention terms and tenant isolation strategy by August 31; until then, prohibit pilot data from entering models, run L0 as a single organization, and retain organization fields.
- Confirm whether a second engineer and knowledge operations owner are available by August 31, and lock delivery levels for the three jurisdictions accordingly.

Milestone M1: all four jurisdictions' materials can enter the system using the same data structure; delivery levels for the three jurisdictions are locked. Record `pass`, `fail`, or `pass-with-approved-degradation`.

<a id="9-月-1-日9-月-20-日香港纵向原型"></a>

### September 1–September 20: Hong Kong vertical prototype

- Connect natural language, fact cards, candidate rules, RAG, and research reports end to end.
- Complete the first 10 Hong Kong candidate cases.
- Complete source catalogs, metadata, and initial parsing for the other three jurisdictions.
- Establish a coverage and validation-status dashboard.
- Complete 3–5 structured workflow walkthroughs using fictional cases, testing interactions, fact confirmation, citations, and report structure only, not tax conclusions.
- Decide authentication and report language/templates by September 20; until then, L0 uses controlled local accounts and Chinese body text + English legal source names.

Milestone M2: at least 10 Hong Kong candidate cases run end to end; 3–5 nonprofessional workflow walkthrough records are complete; initial official materials for three jurisdictions are searchable. Record `pass`, `fail`, or `pass-with-approved-degradation`.

<a id="9-月-21-日10-月-18-日并行扩展"></a>

### September 21–October 18: parallel expansion

- Complete Hong Kong MVP core functionality and freeze new scope.
- Complete mainland China, Japan, and South Korea source-catalog baselines; continue to standard research packages if resources were confirmed on time.
- Complete hybrid retrieval, citations, validity periods, and source levels for four jurisdictions.
- Prepare the Hong Kong expert review package.
- Begin security, permissions, and audit tests.
- Decide deployment region, keys, and backups by October 18; do not deploy real pilot data until decided.

Milestone M3: Hong Kong features are frozen; baseline content for four jurisdictions is shown on the unified platform; L1 deployment prerequisites are decided or continued L0 status is explicit. Record `pass`, `fail`, or `pass-with-approved-degradation`.

<a id="10-月-19-日11-月-8-日验证与补缺"></a>

### October 19–November 8: validation and gap closure

- Run the Hong Kong expert validation sprint or confirm continued L0 internal research status.
- If preparing for L1, expand Hong Kong cases to 30–50 and obtain expert confirmation of their coverage matrix.
- Complete coverage gap checks for mainland China, Japan, and South Korea.
- Fix retrieval, citation, and rule consistency issues.
- Complete recovery drills and critical security tests.

Milestone M4: confirm Hong Kong as L0 or L1; content gaps across four jurisdictions have explicit records and owners. Record `pass`, `fail`, or `pass-with-approved-degradation`.

<a id="11-月-9-日12-月-6-日发布候选版"></a>

### November 9–December 6: release candidate

- Integrate all four jurisdiction tax packages.
- Complete the unified search, coverage, and validation-status interface.
- Conduct a closed Hong Kong advisor pilot if permitted.
- Complete user documentation, knowledge maintenance procedures, and demonstration cases.
- Accept only blocking issues and approved necessary fixes.

Milestone M5: the East Asia Release Candidate passes acceptance checks using the computable metrics in section 9, with an explicit L0 or L1 classification.

<a id="12-月-7-日12-月-18-日稳定与验收"></a>

### December 7–December 18: stabilization and acceptance

- Stop adding jurisdictions, tax categories, and major features.
- Complete regression, security, backup recovery, and release checks.
- Pin source, rule, model, and report versions.
- Complete demonstrations, acceptance records, and the 2027 expansion list.

Milestone M6: release East Asia Release 1. Accept L0 by default; accept L1 only if all conditions are met.

<a id="12-月-19-日12-月-31-日缓冲"></a>

### December 19–December 31: buffer

Handle only production blockers, serious source errors, and security issues; add no features or jurisdictions.

<a id="5-关键路径"></a>

## 5. Critical path

1. Define the common tax package format by the end of August, or parallel work on the three jurisdictions cannot proceed.
2. Run the Hong Kong vertical prototype end to end by September 20, or platform interfaces remain unvalidated.
3. Hong Kong expert validation determines progression from L0 to L1 but does not block the L0 internal research prototype.
4. Official source entry points and language processing determine the speed of baseline coverage for mainland China, Japan, and South Korea.
5. Freeze scope after October 18 to protect December integration and acceptance time.

<a id="6-资源假设"></a>

## 6. Resource assumptions

Conservative planning baseline:

- 1 product/project owner.
- 1 primary engineering contributor, with AI assistance permitted.
- The product owner also coordinates knowledge operations.
- Security, QA, and Hong Kong tax experts are brought in externally according to gates.

Prioritize the Hong Kong vertical workflow, four-jurisdiction source-catalog baselines, research status, source versions, and audit. Completing all eight topic categories as standard research packages for mainland China, Japan, and South Korea is not a default commitment.

Enable the expanded baseline only if a second full-time engineer and a source/knowledge operations owner are confirmed by 2026-08-31. Part-time security/QA, Hong Kong tax experts, and professional reviewers for mainland China, Japan, and South Korea are still introduced in stages according to release gates.

Weekly source monitoring, difference review, language review, and overdue maintenance handling must count toward knowledge operations capacity; they are not free work after launch.

<a id="7-项目治理"></a>

## 7. Project governance

- Monday: confirm weekly deliverables and blockers.
- Wednesday: check four-jurisdiction coverage, engineering progress, and expert dependencies.
- Friday: demonstrate working results and update risks.
- Every two weeks: run complete regression and review scope changes.
- Record each milestone as `pass`, `fail`, or `pass-with-approved-degradation`.
- On a failed checkpoint, immediately apply the fallback in section 3 rather than waiting two weeks to improvise a decision.
- Any new jurisdiction or tax category must specify which existing task it replaces; additions cannot be treated as cost-free.
- The project owner enforces feature freeze after October 18.

Knowledge maintenance service levels: immediately freeze affected nodes after major legal/core-rule changes and classify impact within 2 working days; check important FAQ, DIPN, filing, or official example updates weekly and review initially within 5 working days; process ordinary page and metadata changes monthly. Every jurisdiction has a source owner and backup owner; overdue content must not remain labeled “up to date.”

<a id="8-风险与应对"></a>

## 8. Risks and responses

| Risk | Trigger | Response |
|---|---|---|
| Hong Kong experts remain unavailable | No review scheduled by mid-October | Retain L0; cancel the L1 closed advisor pilot |
| Three-jurisdiction content falls behind | A milestone cannot meet the committed level | Retain source-catalog baseline; do not enable standard research packages |
| Inadequate Japanese/Korean language processing | Retrieval cannot reliably return originals and accurate locations | Keep originals and translations in separate layers; prohibit conclusions based solely on machine translation |
| Continued scope expansion | A fifth jurisdiction or new tax category is proposed | Move it to the 2027 list, outside the current iteration |
| Insufficient engineering capacity | Any milestone checkpoint fails | Apply the planned fallback immediately, preserving source, version, and validation requirements |
| Regulatory changes | Official source hashes or validity periods change | Flag and review affected content; do not overwrite silently |

<a id="9-12-月验收矩阵"></a>

## 9. December acceptance matrix

Each metric stores its test set version, denominator, formula, threshold, zero-tolerance failures, evidence location, and approver.

| Scope | Criterion | Passing standard |
|---|---|---|
| Hong Kong L0 | Candidate cases run end to end | At least 10 versioned candidate cases pass the frozen research evaluation set |
| Hong Kong L0/L1 | Authentic statutes, provisions, and links | One item in the evaluation set that cannot resolve to the source manifest blocks release |
| Hong Kong L1 | Critical fact identification completeness | Correctly extracted or explicitly queried expert-labeled critical facts ÷ all expert-labeled critical facts ≥ 90% |
| Hong Kong L1 | Professional cases | 30–50 gold cases with a Hong Kong expert-confirmed coverage matrix complete regression |
| Hong Kong L1 | Security and professional gates | Expert validation, permissions, audit, backup recovery, model data processing, and pilot data workflows all pass |
| Three-jurisdiction source-catalog baseline | Official source entry points | At least 1 first-party official entry point per declared topic |
| Three-jurisdiction source-catalog baseline | Metadata and links | 100% required-field completeness; 0 broken links in the release snapshot |
| Three-jurisdiction source-catalog baseline | Coverage transparency | Coverage gaps and professional validation statuses are nonempty |
| Standard research package (if enabled) | Jurisdiction × tax topic coverage | Record required source types, applicability dates, languages, spot-check results, and permitted gaps per topic |

Common acceptance: every source shows its official provenance, version, and validity period; unverified content is not presented as formal tax advice; project documentation, acceptance evidence, and the 2027 expansion list are complete.
