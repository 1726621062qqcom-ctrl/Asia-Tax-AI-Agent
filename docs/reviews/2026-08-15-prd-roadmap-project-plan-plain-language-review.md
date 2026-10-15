<a id="prd技术路线图与项目计划审查报告"></a>

# Review of the PRD, Technical Roadmap, and Project Plan

| Item | Result |
|---|---|
| Reviewed files | `docs/product/PRD.md`, `docs/architecture/TECHNICAL_ROADMAP.md`, `docs/project/PROJECT_PLAN_2026.md` |
| Review date | 2026-08-15 |
| Report version | v0.2 |
| Reviewed versions | v0.1 during review; v0.2 after approved changes and formal publication |
| Actions | The user approved all 8 recommendations; the three source files were revised and regression checks completed |
| Mechanical checks | No broken links, placeholders, duplicate headings, version conflicts, or milestone date conflicts after revision |
| Issue count | 5 high-priority; 3 medium-priority |
| Overall assessment | All 8 planning issues are addressed; the files can serve as the v0.2 implementation baseline, while L1 remains subject to expert, security, and resource gates |

<a id="审查范围"></a>

## Review scope

This review checks consistency across the three documents in scope, target users, release dates, resources, technical architecture, acceptance criteria, Hong Kong source completeness, prerequisite security decisions, and ongoing maintenance.

It is a product and engineering planning review, not professional tax, legal, or security assurance. Hong Kong FSIE rules and source completeness still require confirmation by Hong Kong tax experts.

<a id="总体判断"></a>

## Overall assessment

The overall direction is reasonable: Hong Kong FSIE is the in-depth MVP; mainland China, Japan, and South Korea initially receive standard research source packages. Responsibilities among AI, the rule engine, RAG, and tax experts are reasonably clear. The product remains in research status without experts, and facts, rules, sources, and reports require versioning and audit.

The principal issues concern December delivery boundaries, tying scope to resources, release audiences, computable acceptance, a Hong Kong source manifest, and decision deadlines. The user approved every recommendation. The three documents now consistently use L0/L1/L2 release levels, a conservative resource baseline, and explicit acceptance/fallback rules.

These changes improve planning feasibility; they do not establish professional validation of Hong Kong FSIE rules. Without expert and security gates, December delivery must remain an L0 internal research prototype.

<a id="发现的问题"></a>

## Findings

<a id="问题-1四地区范围没有与实际资源绑定"></a>

### Issue 1: four-jurisdiction scope is not tied to actual resources

**Priority: high**

**Problem:** the documents simultaneously promise an in-depth Hong Kong MVP, standard corporate tax packages for three jurisdictions, a unified platform, security, audit, and release work. The plan lists only a “minimum recommended staffing” without confirming actual available capacity.

**Evidence:**

- `PRD.md` section 12 includes standard tax packages for mainland China, Japan, and South Korea in 2026 Release 1.
- `PROJECT_PLAN_2026.md` section 6 recommends two full-time engineers, one knowledge operations contributor, and part-time support.
- Even with one engineer, the plan still prioritizes four-jurisdiction sources, the Hong Kong vertical workflow, and audit without materially reducing regional content scope.

**Why it matters:** below-recommended capacity may leave all four-jurisdiction content, the Hong Kong MVP, and security half-complete rather than delaying one complete deliverable. The team may improvise a lower definition of “usable” in December.

**Recommendation:** adopt a conservative resource baseline and specify stretch scope unlocked only when extra staff are confirmed.

<a id="问题-2研究模式发布到底给谁用没有说清楚"></a>

### Issue 2: the audience for a “research-mode release” is unclear

**Priority: high**

**Problem:** the PRD prohibits real-client tax conclusions without Hong Kong experts, while the plan permits a Hong Kong research-mode release without saying whether it is internal-only or accessible to advisors.

**Evidence:**

- `PRD.md` section 3.3 makes expert validation mandatory for a closed advisor pilot.
- `PROJECT_PLAN_2026.md` section 1 permits research-mode release without experts.
- Section 4 schedules a closed advisor pilot during the release candidate phase.

**Why it matters:** real users may apply watermarked research reports to client cases. Different participants may interpret “release complete” as different maturity levels.

**Recommendation:** distinguish internal research prototypes, closed advisor pilots, and production client capabilities.

<a id="问题-3很多验收条件无法重复计算"></a>

### Issue 3: many acceptance criteria are not reproducibly computable

**Priority: high**

**Problem:** criteria such as “90% critical fact identification completeness,” “no fabricated legislation,” and “usable tax packages for four jurisdictions” lack test sets, denominators, formulas, or passing standards.

**Evidence:**

- `PRD.md` section 11.
- `PROJECT_PLAN_2026.md` section 9.
- The roadmap mentions recall, citation locations, and case evaluation without specific thresholds.

**Why it matters:** different reviewers may pass or fail the same system, with no evidence that a new version improves on an old one.

**Recommendation:** create a requirements–test set–formula–threshold–release gate matrix.

<a id="问题-4香港资料是否完整没有一份可以验收的清单"></a>

### Issue 4: no assessable checklist establishes Hong Kong source completeness

**Priority: high; Hong Kong tax expert confirmation required**

**Problem:** the documents mention FSIE pages, FAQs, official examples, and legislation, but do not define required laws, amendments, FAQs, DIPNs, advance rulings, and other materials or pin a legal applicability cutoff.

**Evidence:**

- `PRD.md` sections 5.2, 8, and 11.1.
- `TECHNICAL_ROADMAP.md` section 4.4.

The [IRD FSIE page](https://www.ird.gov.hk/eng/tax/bus_fsie.htm) covers income scope, covered taxpayers, receipt in Hong Kong, exceptions, double-taxation relief, obligations, and advance rulings. Traceability of collected documents alone cannot establish that no critical materials were omitted.

**Why it matters:** RAG may accurately cite existing database materials while omitting important conditions because the library itself is incomplete.

**Recommendation:** create a versioned Hong Kong FSIE source manifest. Engineering checks files, links, versions, and indexes; Hong Kong experts confirm professional sufficiency.

<a id="问题-5会影响架构的决定安排得太晚"></a>

### Issue 5: architectural decisions are scheduled too late

**Priority: high**

**Problem:** storage region, provider/retention terms, tenant isolation, authentication, case de-identification, and report language remain undecided without deadlines.

**Evidence:** `TECHNICAL_ROADMAP.md` sections 5, 6, and 11, and `PROJECT_PLAN_2026.md` section 4.

**Why it matters:** these choices affect tables, permissions, deployment, model calls, and security testing. Decisions just before the pilot may require rework.

**Recommendation:** assign every open decision a deadline, interim default, and blocked workstream.

<a id="问题-6里程碑有日期但缺少可问责负责人和明确降级方案"></a>

### Issue 6: milestones lack accountable owners and explicit fallbacks

**Priority: medium**

**Problem:** M1–M6 specify dates and outputs but not one accountable owner per deliverable or what exactly to remove on failure.

**Why it matters:** weekly progress updates may obscure dependencies and critical-path blockers. Scope reduction becomes an improvised dispute.

**Recommendation:** add owners, dependencies, checkpoint results, and preapproved fallback actions for major deliverables.

<a id="问题-7等到-11-月才验证顾问工作流时间太晚"></a>

### Issue 7: advisor workflow validation waits until November

**Priority: medium**

**Problem:** Hong Kong advisors are the initial users, but no interviews, prototype walkthroughs, or report structure validation are scheduled before November.

**Why it matters:** discovering poor question order, fact cards, or report structure after feature freeze leaves little time for rework.

**Recommendation:** complete 3–5 September walkthroughs with fictional cases, testing interactions/report usability without treating feedback as professional tax conclusions.

<a id="问题-8四地区资料上线后的维护责任不够具体"></a>

### Issue 8: ongoing four-jurisdiction maintenance responsibilities lack detail

**Priority: medium**

**Problem:** automated capture, difference detection, and reviewed publication are required, but checking frequency, response times for major changes, regional owners, and overdue status are unspecified.

**Why it matters:** the system may accurately display an old version without detecting promptly that it is stale.

**Recommendation:** establish separate response times for major, important, and ordinary changes and designate source/backup owners for every jurisdiction.

<a id="跨文档需要统一的地方"></a>

## Cross-document alignment needed

| Topic | PRD wording | Roadmap/plan wording | Issue |
|---|---|---|---|
| Release audience | No real-client service before expert validation | Research-mode release permitted | Who may use the research release? |
| Resources and scope | Hong Kong MVP + three standard packages | Staffing is only recommended | Deadlines lack a capacity basis |
| Acceptance | Directional Hong Kong gates | “Usable,” “complete,” “accepted” | Passing cannot be judged reproducibly |
| Security architecture | Tenant isolation and case permissions required | Tenancy, authentication, deployment undecided | Security test target is not fixed |

<a id="已确认的优点"></a>

## Confirmed strengths

- RAG sources, rule execution, and case evaluation libraries are explicitly separate.
- Research status is retained without Hong Kong experts; real advisor pilots require expert gates.
- Facts, rules, sources, and reports require versions and audit records.
- Modular monolith, PostgreSQL, hybrid retrieval, and model adapters suit the MVP stage.
- The four-jurisdiction scope, October freeze, and December buffer broadly agree across the three documents.
- `pgvector` with PostgreSQL matches the official project's capabilities, with no identified obstacle to the MVP from this choice itself: [pgvector](https://github.com/pgvector/pgvector).

<a id="具体修改建议"></a>

## Specific revisions

<a id="建议修改-1采用保守资源基线"></a>

### Revision 1: adopt a conservative resource baseline

**Affected sections:** PRD 5.1 and 12; roadmap 3.1 and 8; plan 1, 2.2, and 6.

**Proposed text:**

> Default 2026 scheduling assumes 1 project/product owner + 1 primary engineer, with AI assistance permitted. The full standard tax package objective across four jurisdictions is enabled only if a second full-time engineer and knowledge operations owner are confirmed by August 31.
>
> The conservative baseline retains the Hong Kong end-to-end research MVP. Mainland China, Japan, and South Korea deliver official catalogs, common metadata, topic classifications, coverage gaps, and validation statuses in 2026. Completing standard research packages across eight topic categories is a stretch objective unlocked by additional resources.

**Post-change check:** all three documents use the same completion levels; without confirmed resources, completing all eight topics is no longer simultaneously promised.

**Status:** implemented; regression checks passed.

<a id="建议修改-2增加三级发布定义"></a>

### Revision 2: define three release levels

**Affected sections:** all references to research releases, closed pilots, and formal clients in the three documents.

**Proposed content:**

| Release level | Permitted users | Permitted data | Permitted outputs | Required gates |
|---|---|---|---|---|
| Internal research prototype | Project team | Fictional or approved de-identified cases | Engineering demonstrations marked as research | Research status cannot be bypassed; sources traceable |
| Closed advisor pilot | Authorized Hong Kong advisors | Approved pilot cases | Internal drafts solely for advisor review | All Hong Kong expert and security gates passed |
| Production client capabilities | Formally authorized clients/advisors | Contractually/compliantly permitted data | Formal product capabilities | Outside the default 2026 commitment |

Without expert gates, December accepts only the internal research prototype, which must not be called a client release.

**Post-change check:** every release/pilot/client reference maps to one level above.

**Status:** implemented; regression checks passed.

<a id="建议修改-3把验收条件改成可计算指标"></a>

### Revision 3: make acceptance criteria computable

**Affected sections:** PRD 11, roadmap 7, plan 9.

**Proposed content:**

- Record test set versions, denominators, formulas, thresholds, evidence, and approvers for every metric.
- Critical fact identification completeness is correctly extracted or explicitly queried expert-labeled critical facts ÷ all expert-labeled critical facts.
- One statute, provision, or link in the evaluation set that cannot map to the source manifest blocks release.
- The Hong Kong internal research prototype runs at least 10 candidate cases; the closed pilot uses 30–50 cases with expert-confirmed coverage.
- Every declared topic in the three jurisdictions has at least one first-party official entry point; required metadata is 100% complete; release snapshot broken links are 0; coverage gaps and validation statuses are nonempty.

**Post-change check:** every December acceptance criterion has test data, a calculation, and a passing standard.

**Status:** implemented; regression checks passed.

<a id="建议修改-4建立香港-fsie-资料总清单"></a>

### Revision 4: establish a Hong Kong FSIE source manifest

**Affected sections:** PRD 8 and 11.1; roadmap 4.4.

**Proposed content:** each source records title, publisher, type, original URL, language, publication/effective/expiry dates, capture time, hash, authority, associated nodes, supporting/limiting relationships, replacement versions, parsing status, and expert validation status.

Every report stores a legal coverage cutoff. Later published/effective materials trigger impact checks; until reviewed, related rules are potentially stale and stop producing definitive professional conclusions.

Engineering confirms files, versions, links, parsing, and indexes only; Hong Kong tax experts confirm professional sufficiency.

**Post-change check:** the documents explain what is collected, the applicability cutoff, gaps, and responsible reviewers.

**Status:** implemented; regression checks passed. Experts must still confirm professional completeness.

<a id="建议修改-5为基础决策设置截止日期"></a>

### Revision 5: set deadlines for foundational decisions

**Affected sections:** roadmap 11 and plan M1–M3.

| Decision | Latest date | Interim action | Blocked work |
|---|---|---|---|
| Case sources/de-identification | August 20 | Fictional cases only | Real or anonymous case import |
| Model provider/retention terms | August 31 | Synthetic data only | Pilot data entering models |
| Tenant isolation | August 31 | Single-organization research environment with organization fields | Permission/database interface freeze |
| Authentication | September 20 | Controlled local research accounts | Advisor pilot permissions acceptance |
| Deployment region, keys, backups | October 18 | No real pilot data deployment | Advisor pilot environment/security tests |
| Report language/templates | September 20 | Chinese body with English legal source names | Report feature freeze |

**Post-change check:** every open decision has a deadline, interim plan, owner, and blocked work.

**Status:** implemented; regression checks passed.

<a id="建议修改-6增加负责人和范围降级表"></a>

### Revision 6: add owners and scope fallback tables

**Affected sections:** roadmap 8 and plan 3–5 and 8.

Assign one ultimately accountable owner to tax package structure, the Hong Kong prototype, three-jurisdiction sources, the expert package, and security/release. Record prerequisites and fallbacks. One person may hold multiple roles, but no deliverable may lack an owner.

Standardize milestone results as pass, fail, or pass with approved degradation. Apply predefined fallback immediately on checkpoint failure rather than waiting two weeks to decide.

**Post-change check:** each critical deliverable has one owner, explicit dependencies, and a planned fallback.

**Status:** implemented; regression checks passed.

<a id="建议修改-79-月增加-35-次工作流走查"></a>

### Revision 7: add 3–5 September walkthroughs

**Affected sections:** PRD 11 and plan M2.

Use fictional cases with potential advisors or proxy users familiar with professional-service review to check case creation, pacing, confirmation, gap notices, citations, and report structure. Walkthroughs test usability, not tax conclusions, and cannot become tax gold standards.

Record confusing fields, repeated/invalid questions, completion time, report lookup difficulties, and major suggestions.

**Post-change check:** 3–5 walkthrough records exist before M2 and are not labeled expert cases.

**Status:** implemented; regression checks passed.

<a id="建议修改-8建立四地区资料维护标准"></a>

### Revision 8: establish four-jurisdiction maintenance standards

**Affected sections:** PRD 8 and 13; roadmap 4.6; plan 8.

| Change level | Handling | System status |
|---|---|---|
| Major: laws taking effect, core-rule repeal, official corrections | Immediately freeze affected rules; classify impact within two working days | Potentially stale; definitive professional outputs prohibited |
| Important: FAQ, DIPN, filing, official example updates | Check weekly; initial review within five working days | Warning until reviewed |
| Ordinary: page changes, moved links, metadata corrections | Monthly batches | Searchable; changes recorded |

Each jurisdiction has a source owner and backup owner. Machine translation cannot establish professional approval; overdue content must not remain labeled “up to date.”

**Post-change check:** each jurisdiction can identify who maintains content, checking/response frequency, and overdue presentation.

**Status:** implemented; regression checks passed.

<a id="用户决定与实施结果"></a>

## User decision and implementation results

On 2026-08-15, the user accepted all 8 recommendations.

| Revision | Content | Affected files | Decision |
|---|---|---|---|
| 1 | Conservative resource baseline | All three | Accepted and implemented |
| 2 | Three release levels | All three | Accepted and implemented |
| 3 | Computable acceptance | All three | Accepted and implemented |
| 4 | Hong Kong FSIE source manifest | PRD, roadmap | Accepted and implemented |
| 5 | Foundational decision deadlines | Roadmap, plan | Accepted and implemented |
| 6 | Owners and fallbacks | Roadmap, plan | Accepted and implemented |
| 7 | Earlier workflow walkthroughs | PRD, plan | Accepted and implemented |
| 8 | Four-jurisdiction maintenance standards | All three | Accepted and implemented |

<a id="回归检查结果"></a>

## Regression results

- Deterministic scans found 0 broken links, placeholders, duplicate headings, version conflicts, or milestone date conflicts.
- All three files remained v0.1 during local review; after user confirmation of formal Git publication, all became v0.2.
- L0/L1/L2, conservative resources, `source-catalog baseline`, and conditional stretch scope are consistent.
- Hong Kong L0/L1 case counts, fact identification formulas, citation blockers, and three-jurisdiction package thresholds align.
- Decision deadlines, owners, dependencies, defaults, and fallbacks are recorded in the roadmap/plan.
- Maintenance response times, owners, and stale status are recorded across all three.
- No residual ambiguous wording such as “research-mode release” or undefined “usable four-jurisdiction tax packages” was found.

<a id="审查限制"></a>

## Review limitations

- Implementation code, databases, budgets, staffing contracts, client interviews, and the original Hong Kong summary were not checked.
- No jurisdiction tax experts participated; professional rules/source completeness were not treated as validated.
- External checks confirmed key official/technical entry points only, not complete legislation, provider contracts, or data protection due diligence.
- The three source files already had uncommitted edits before review. This review changed only user-approved planning content; it did not clean unrelated edits, stage, commit, upload, or update versions.

<a id="内部追踪"></a>

## Internal tracking

These identifiers prevent mismatches during approval, revision, and regression; users need not use them.

| Item | Internal issue | Internal change | Final status |
|---|---|---|---|
| Issue 1 / revision 1 | REV-001 | CHG-001 | Resolved / applied |
| Issue 2 / revision 2 | REV-002 | CHG-002 | Resolved / applied |
| Issue 3 / revision 3 | REV-003 | CHG-003 | Resolved / applied |
| Issue 4 / revision 4 | REV-004 | CHG-004 | Resolved / applied |
| Issue 5 / revision 5 | REV-005 | CHG-005 | Resolved / applied |
| Issue 6 / revision 6 | REV-006 | CHG-006 | Resolved / applied |
| Issue 7 / revision 7 | REV-007 | CHG-007 | Resolved / applied |
| Issue 8 / revision 8 | REV-008 | CHG-008 | Resolved / applied |
