<a id="东亚税务-ai-平台香港-fsie-mvp-产品需求文档"></a>

# East Asian Tax AI Platform (Hong Kong FSIE MVP) — Product Requirements Document

| Item | Details |
|---|---|
| Document version | v0.2 |
| Date | 2026-08-15 |
| Status | 2026 East Asia Release 1 research baseline confirmed; implementation pending |
| MVP jurisdiction | Hong Kong, China |
| 2026 Release 1 | Mainland China, Hong Kong, Japan, South Korea |
| Initial users | Hong Kong tax advisors |
| Initial scenario | Preliminary FSIE analysis of foreign-sourced dividends received by a multinational enterprise entity |

<a id="1-产品摘要"></a>

## 1. Product summary

The product is a foreign-sourced dividend analysis workspace for Hong Kong tax advisors. Advisors describe cases in natural language. The Agent fills critical factual gaps through an interactive interview, creates advisor-confirmed fact cards, executes versioned tax rules, retrieves and attaches official Hong Kong evidence, and generates a traceable internal analysis draft for review.

The product does not replace tax advisors or automatically issue formal tax advice ready for client delivery. AI handles understanding and expression, the rule engine handles reproducible determinations, and tax advisors take responsibility for professional conclusions.

<a id="2-背景与问题"></a>

## 2. Background and problems

FSIE analysis of foreign-sourced dividends involves entity status, income character, fund flows, shareholding conditions, economic substance, foreign taxation, anti-hybrid rules, and main purpose. Traditional workflows have the following problems:

- Case information is scattered across emails, interviews, documents, and advisor notes.
- Important questions may be omitted or repeated.
- Legal evidence, facts, and conclusions lack clear mappings.
- Regulatory updates make it difficult to identify affected historical analyses.
- Advisors follow inconsistent analysis processes and report structures.
- Direct large-model answers may omit conditions, miscite sources, or produce irreproducible conclusions.

The MVP establishes a controlled workflow through natural-language interviews + fact cards + a rule engine + RAG citations + human review.

<a id="3-产品目标"></a>

## 3. Product objectives

<a id="31-mvp-目标"></a>

### 3.1 MVP objectives

- Let tax advisors start cases in natural language instead of completing long forms.
- Dynamically identify critical missing facts, contradictions, and evidence gaps.
- Reliably execute the core FSIE decision chain for foreign-sourced dividends.
- Make every substantive conclusion traceable to facts, rules, and official sources.
- Stop safely and escalate to humans when information is insufficient or professional judgment is needed.
- Generate consistently structured Chinese internal analysis drafts that are easy to review.
- Demonstrate testable, reproducible behavior through expert cases.

<a id="32-非目标"></a>

### 3.2 Non-goals

- Automatically filing tax returns or sending information to the Hong Kong Inland Revenue Department.
- Automatically issuing formal tax advice.
- Covering foreign-sourced interest, intellectual property income, or disposal gains.
- Providing complete tax conclusions for jurisdictions outside Hong Kong.
- Performing complete corporate structure optimization or recommending the lowest tax burden.
- Allowing final conclusions without human approval.

<a id="33-当前约束与无专家研究模式"></a>

### 3.3 Current constraints and research mode without experts

The team currently has no Hong Kong tax expert. This does not prevent technical research and prototype development, but changes the product's permitted use: until expert validation is complete, it may be used only as a research prototype and must not provide tax conclusions to real clients.

Work permitted before experts are available:

- Capture, parsing, versioning, and citation of official Hong Kong materials.
- Natural-language interviews, candidate fact extraction, and fact cards.
- Rule frameworks, candidate decision tables, and engineering tests.
- Report structure, audit, security, and evaluation infrastructure.
- Internal demonstrations using fictional or strictly anonymized cases.

Prohibited before experts are available:

- Marking candidate rules as professionally validated.
- Treating case answers proposed by the model or engineering team as tax gold standards.
- Providing real clients with exemption, taxability, or structure optimization conclusions.
- Claiming that the system already provides reliable Hong Kong tax advice.

All candidate rules, case conclusions, and research reports must display “Pending validation by Hong Kong tax experts.” Expert review of core rules, boundaries requiring human judgment, and expert cases is a mandatory gate for a closed advisor pilot, rather than a prerequisite for starting engineering work.

<a id="34-发布等级与使用边界"></a>

### 3.4 Release levels and usage boundaries

| Release level | Permitted users | Permitted data | Permitted output | Mandatory gates |
|---|---|---|---|---|
| L0 internal research prototype | Project team | Fictional cases or data with approved de-identification | Engineering demonstrations marked as research; not for client tax judgments | Research status cannot be bypassed; all sources are traceable |
| L1 closed advisor pilot | Authorized Hong Kong tax advisors | Pilot cases with approved data processing | Internal drafts solely for advisor review | Hong Kong expert validation and all permissions, recovery, and security gates passed |
| L2 production client capabilities | Formally authorized clients and advisors | Data permitted by contracts and compliance requirements | Formal product capabilities within the approved scope | Outside the default commitment for 2026 Release 1 |

The default December 2026 acceptance target is L0. Hong Kong capabilities may progress to L1 acceptance only after both expert and engineering security gates pass. Otherwise, L0 must not be described as a client release or as suitable for real client conclusions.

<a id="4-用户与使用场景"></a>

## 4. Users and scenarios

<a id="41-主要用户"></a>

### 4.1 Primary users

- Hong Kong tax advisors: create cases, answer interviews, confirm facts, and revise analyses.
- Reviewers: resolve judgment questions and approve internal review drafts.
- Knowledge administrators: maintain sources, rule mappings, and versions.
- System administrators: maintain users and deployment, without default access to case content.

<a id="42-核心用户故事"></a>

### 4.2 Core user story

> As a Hong Kong tax advisor, I want to describe a foreign-sourced dividend in natural language, have the system ask only questions affecting the tax conclusion, and receive an internal review draft containing facts, risks, the decision path, official evidence, and evidence gaps, so that I can complete professional review efficiently.

<a id="5-产品范围与判断链"></a>

## 5. Product scope and decision chain

<a id="51-2026-年项目范围"></a>

### 5.1 2026 project scope

The December 2026 product scope is limited to four East Asian jurisdictions:

- Mainland China.
- Hong Kong, China.
- Japan.
- South Korea.

Hong Kong is the first MVP with in-depth coverage. Its initial scenario remains FSIE analysis of foreign-sourced dividends received by multinational enterprise entities. Mainland China, Japan, and South Korea will not reproduce the full Hong Kong interaction and rule depth in 2026. The conservative 2026 baseline provides each jurisdiction with a searchable, maintainable `source-catalog baseline`, including official sources and validation statuses. Extending all eight topic categories to a `standard research package` becomes a 2026 stretch objective only if a second full-time engineer and a knowledge operations owner are confirmed by 2026-08-31.

All four jurisdictions share the platform, source specifications, rule format, citation mechanism, and evaluation framework. The interface and acceptance records must show whether each jurisdiction currently has a source-catalog baseline or a standard research package. Singapore, Southeast Asia, South Asia, Australia, New Zealand, and other Asia-Pacific jurisdictions are excluded from 2026 and will be planned after East Asia Release 1 acceptance.

<a id="52-香港-mvp-判断链"></a>

### 5.2 Hong Kong MVP decision chain

The MVP analyzes, in sequence:

1. Whether the recipient is a multinational enterprise entity within this product's scope.
2. Whether the income is foreign-sourced dividend income.
3. Whether the dividend is received in Hong Kong.
4. Whether exclusions such as those for regulated financial entities apply.
5. Whether economic substance requirements may be satisfied.
6. Whether the deterministic basic conditions for participation exemption are met.
7. Whether foreign taxation conditions and switchover rules are involved.
8. Whether anti-hybrid mismatch rules are involved.
9. Whether main purpose or other matters require human judgment.
10. Whether foreign tax credits, filing, evidence retention, or advance rulings need to be flagged.

Official baseline materials include the IRD's [FSIE page](https://www.ird.gov.hk/eng/tax/bus_fsie.htm), [FSIE FAQ](https://www.ird.gov.hk/eng/faq/fsie.htm), and [official examples](https://www.ird.gov.hk/eng/tax/fsie_example.htm). Applicable original legislation and effective versions take highest priority.

<a id="6-核心用户流程"></a>

## 6. Core user workflow

```text
Create a case
→ Advisor describes it in natural language
→ AI extracts candidate facts and contradictions
→ Agent asks critical questions one at a time
→ Advisor confirms fact cards
→ Lock the analysis version
→ Rule engine executes FSIE determinations
→ RAG retrieves official evidence for each node
→ Mark human judgment requirements and evidence gaps
→ Generate an internal review draft
→ Advisor revises, returns, or approves it
→ Archive fact, rule, source, and report versions
```

<a id="61-访谈原则"></a>

### 6.1 Interview principles

- Ask only one main question at a time.
- Prioritize scope blockers, then conclusion, anti-abuse, evidence, and presentation questions.
- Allow “unknown,” “provide later,” “confirm with the client,” “not applicable,” and “analyze under an assumption.”
- Never automatically convert unknown into a negative finding.
- Explain why important questions need answers.
- Let advisors inspect and edit fact cards at any time.

<a id="7-功能需求"></a>

## 7. Functional requirements

<a id="fr-01-自然语言案件创建"></a>

### FR-01 Natural-language case creation

- Accept case descriptions in Chinese or English.
- Identify candidate facts about entities, income, timing, amounts, shareholdings, fund flows, and foreign taxation.
- Clearly distinguish original statements from system inferences.

<a id="fr-02-动态访谈"></a>

### FR-02 Dynamic interviews

- Select the next question from factual gaps and the current rule node.
- Detect repetition, contradictions, and out-of-scope statements.
- Support pausing a case and recording items awaiting client confirmation.

<a id="fr-03-事实卡"></a>

### FR-03 Fact cards

Each fact stores at least its field, value, source, confirmation status, confidence, evidence, editor, modification time, and affected rule nodes.

Fact domains include:

- Recipient entity, group, and special status.
- Dividend amount, date, character, and underlying profit period.
- Receipt accounts, cash pooling, set-off, payments on behalf, and fund usage paths.
- Direct/indirect ownership percentages and continuous holding periods.
- Foreign taxation and dividend deductibility.
- Hong Kong personnel, activities, premises, expenditure, decisions, and outsourcing oversight.
- Structure establishment, restructuring, commercial purpose, and hybrid mismatches.
- Evidence such as company documents, bank records, and tax certificates.

<a id="fr-04-规则执行"></a>

### FR-04 Rule execution

- Deterministic rules must be reproducible and record inputs, results, and rule versions.
- Judgment matters must be marked for human review.
- Every rule stores its professional validation status, validator, and validation time.
- Unverified rules run only in research mode, with clearly watermarked outputs.
- Critical fact changes rerun only affected nodes.
- Old reports retain their original rule versions.

<a id="fr-05-法律资料检索与引证"></a>

### FR-05 Legal source retrieval and citation

- Retrieve using confirmed facts and the current rule node, not just keywords from the original prompt.
- Combine keyword and vector retrieval.
- Filter by authority level, jurisdiction, and validity period.
- Store exact sources and passage locations for every substantive conclusion.
- Do not fill gaps from model memory when reliable evidence is absent.

<a id="fr-06-内部复核稿"></a>

### FR-06 Internal review drafts

Generate Chinese reports by default, preserving English titles and original-text locations for legislation and guidance. Reports contain:

- Executive summary and preliminary risk level.
- Confirmed facts, system assumptions, and missing information.
- Step-by-step decision path.
- Evidence supporting and limiting the current conclusion.
- Official citations and the versions used.
- Required evidence checklist.
- Human review items.
- Preliminary conclusion and conclusion status.

<a id="fr-07-人工复核与版本"></a>

### FR-07 Human review and versioning

- Advisors can revise facts, analysis text, risk levels, and reasoning.
- Critical fact changes automatically invalidate the original report.
- Store reasons for approving, overturning, or modifying system recommendations.
- Archive corresponding fact, rule, and source versions when a report is approved.

<a id="fr-08-知识与规则管理"></a>

### FR-08 Knowledge and rule management

- Manage official source provenance, authority level, validity period, hashes, and capture dates.
- Display source differences and require review before publication.
- Rule changes require testing and tax expert approval.
- Store internal client materials separately from public authoritative materials and identify them clearly.

<a id="8-知识治理"></a>

## 8. Knowledge governance

The system must separate three asset classes:

1. Authoritative legal source library: retrieval and citation.
2. Versioned tax rule library: deterministic determinations.
3. Expert case evaluation library: testing Agent, rule, and retrieval quality.

The system captures and monitors official materials. Engineering may first create candidate rule mappings, but only Hong Kong tax experts may confirm legal authority, professional interpretations, and rule validation status. The user team primarily supplies anonymous cases, practical experience, and internal report templates rather than continually searching for public documents by hand.

Source annotation has three layers:

- Document metadata: source, type, authority level, validity period, language, and hash.
- Professional rule mappings: applicable nodes, supporting/limiting relationships, exceptions, and human judgment requirements.
- Expert case labels: correct follow-ups, expected paths, acceptable conclusions, and citations.

<a id="81-香港-fsie-资料总清单"></a>

### 8.1 Hong Kong FSIE source manifest

The Hong Kong FSIE package must maintain a versioned source manifest. Each record stores at least `source_id`, title, publisher, source type, original URL, jurisdiction, language, publication date, effective date, expiry date, capture time, content hash, authority level, associated rule nodes, supporting/limiting relationships, replacement versions, parsing status, professional validation status, and validation records.

Every evaluation and report stores `legal_coverage_cutoff`. Materials published or taking effect after the cutoff trigger an impact check by default. Until review is complete, affected nodes are `potentially_stale` and must not produce definitive professional conclusions.

Engineering completeness means required manifest fields, originals, hashes, parsing, indexing, and links pass checks. Professional completeness means Hong Kong tax experts confirm that legislation, amendments, FAQs, examples, DIPNs, public advance rulings, and other materials required by relevant nodes have no known critical gaps. Engineering completeness cannot substitute for professional completeness.

<a id="82-知识维护服务水平"></a>

### 8.2 Knowledge maintenance service levels

| Change level | Examples | Detection and handling | System status |
|---|---|---|---|
| Major | Legislation taking effect, repeal of core rules, or official corrections | Immediately freeze affected rules on detection; classify impact within 2 working days | `potentially_stale`; definitive professional outputs prohibited |
| Important | Updates to FAQs, DIPNs, filing obligations, or official examples | Check official entry points weekly; initial review within 5 working days | Warning until reviewed |
| Ordinary | Page changes, link migration, or metadata corrections | Process monthly in batches | Remain searchable and record changes |

Every jurisdiction must designate a source owner and backup owner. Machine translation cannot establish professional approval. Overdue maintenance must be visible, and overdue content must not continue to be labeled “up to date.”

<a id="9-状态与异常处理"></a>

## 9. States and exception handling

Case states include draft, interviewing, waiting for client information, waiting for fact confirmation, analyzing, requiring human judgment, pending review, approved, invalidated, and archived.

Safe stopping conditions include:

- Missing blocking facts.
- Contradictory facts.
- Missing or potentially stale official evidence.
- Suspected conflicts between rules and new materials.
- Questions outside MVP scope.
- Matters such as economic substance or main purpose requiring professional judgment.
- Uploaded materials containing instructions attempting to alter system behavior.

When stopping, explain what is known, what is missing, potential impacts, and the next required materials. Do not force an exempt/taxable conclusion.

<a id="10-非功能需求"></a>

## 10. Nonfunctional requirements

<a id="101-安全与隐私"></a>

### 10.1 Security and privacy

- Role- and case-level access control.
- Tenant data isolation.
- Encryption in transit and at rest.
- Redaction of sensitive logs.
- Configurable retention and deletion.
- User data is not used to train general-purpose models by default.
- Audit downloads, exports, approvals, and rule changes.
- Test backup and recovery procedures.

<a id="102-可审计性"></a>

### 10.2 Auditability

The system must explain who supplied or changed a fact and when, why a question was asked, which rule version produced a result, which source was cited, and who approved the final internal draft.

<a id="103-可维护性"></a>

### 10.3 Maintainability

- Isolate jurisdiction knowledge packages.
- Connect model providers through an adapter layer.
- Keep rules and parameters logically separate from application code.
- Run regression tests after updates to legislation, rules, prompts, or models.

<a id="11-成功指标与验收"></a>

## 11. Success metrics and acceptance

<a id="111-无专家研究原型验收"></a>

### 11.1 Research prototype acceptance without experts

- Hong Kong source manifest required metadata completeness reaches 100%; originals, versions, hashes, validity periods, and links are verifiable.
- Candidate rules map explicitly to source passages.
- Unverified rules and reports always show research-mode status.
- Natural language, fact cards, rules, RAG, and reporting run end to end.
- Prompts or ordinary user operations cannot remove professional validation gates.
- Only fictional cases or data with approved de-identification are used.
- At least 10 versioned candidate cases run end to end on a frozen research evaluation set.
- One statute, provision, or link in the evaluation set that cannot resolve to the source manifest blocks L0 release.

Meeting these metrics establishes only that the engineering prototype works, not that tax conclusions are correct.

<a id="112-封闭试点准入门槛"></a>

### 11.2 Closed pilot entry gates

Before a closed pilot:

- Critical fact identification completeness reaches at least 90%, calculated as correctly extracted or explicitly queried expert-labeled critical facts ÷ all expert-labeled critical facts.
- Blocking facts cannot be silently omitted from questioning.
- Deterministic rules have no known errors and pass boundary tests.
- The same facts and rule version produce the same structured results.
- Every substantive conclusion has verifiable official citations.
- High-risk and subjective-judgment cases correctly escalate to humans.
- The frozen release evaluation set contains no statute, provision, or link that cannot resolve to the source manifest; any occurrence blocks release.
- 30–50 expert cases complete end-to-end regression testing.
- Advisors can revise facts, judgments, and reports while preserving audit history.

These rules, case answers, and human judgment boundaries must be reviewed by professionals experienced in Hong Kong corporate tax. Without professional validation, passing every engineering metric still does not permit a real advisor or client pilot.

Each metric stores the test set version, denominator, formula, threshold, zero-tolerance failures, evidence location, and approver. During the pilot, also measure case completion time, follow-up count, advisor revision rate, error types, citation acceptance rate, and advisor satisfaction.

<a id="113-功能冻结前的工作流走查"></a>

### 11.3 Workflow walkthroughs before feature freeze

Complete 3–5 structured walkthroughs using fictional cases by 2026-09-20. Prefer potential users with Hong Kong corporate tax experience; if unavailable, use proxy users familiar with professional-service review workflows and record their backgrounds.

Walkthroughs assess only whether case creation, follow-up pacing, fact confirmation, gap notices, citations, report structure, and human escalation are understandable. They do not validate tax conclusions. Each records task completion, confusing fields, invalid/repeated follow-ups, report lookup time, key revisions, and open questions. Walkthrough records must not be labeled expert cases or tax gold standards.

<a id="114-中国内地日本和韩国研究包验收"></a>

### 11.4 Mainland China, Japan, and South Korea research package acceptance

Under `source-catalog baseline`, every declared topic has at least 1 first-party official entry point, required metadata completeness is 100%, broken links in the release snapshot are 0, and coverage gaps and professional validation statuses are nonempty.

If `standard research package` is enabled, record required source types, applicability dates, languages, spot-check results, and permitted gaps for each jurisdiction × tax topic. Document counts cannot substitute for coverage.

<a id="12-功能优先级"></a>

## 12. Feature priorities

### P0 — MVP

Complete the common jurisdiction tax package framework and Hong Kong natural-language input, dynamic interviews, fact cards, candidate FSIE rules, official source retrieval, citation ledger, research-mode internal review drafts, human judgment markers, professional validation status, versioning, and audit. Hong Kong tax expert validation is a separate release gate before a closed pilot.

<a id="p1--2026-东亚-release-1"></a>

### P1 — 2026 East Asia Release 1

Build a `source-catalog baseline` for mainland China, Japan, and South Korea, covering official catalogs, common metadata, topic classification, validity periods, coverage gaps, and professional validation statuses. Extending corporate income tax, turnover taxes, cross-border withholding taxes, tax residence/permanent establishments, transfer pricing, major anti-avoidance rules, treaty entry points, and filing cycles to a `standard research package` is a stretch objective only when additional resources are confirmed on time. Content without local expert validation remains in research status.

<a id="p2--release-1-后增强"></a>

### P2 — Enhancements after Release 1

File upload and fact extraction, organization chart parsing, Chinese/English reports, multi-advisor comments, regulatory change monitoring, Word/PDF export, internal template configuration, and extensions to Hong Kong foreign-sourced interest, disposal gains, and intellectual property income.

<a id="13-依赖与主要风险"></a>

## 13. Dependencies and principal risks

- Early engineering does not require continuous on-site Hong Kong tax expert involvement, but an expert validation sprint must finish before a closed pilot.
- Unconfirmed experts delay the pilot, not source, RAG, interview, or engineering framework development.
- To reduce expert costs, prepare rule mappings, open questions, and candidate cases as an expert review package first.
- Official source updates require change detection and release processes.
- Monitoring, difference review, and language review across four jurisdictions count toward knowledge operations capacity.
- Mandatory human nodes control excessive automation of judgment matters.
- Structured outputs, citation validation, and safe stopping control model hallucinations.
- Isolation, encryption, permissions, logs, and provider review control data leakage risks.
- The 2026 scope is strictly mainland China, Hong Kong, Japan, and South Korea, with expansion controlled through P0/P1/P2 gates.

<a id="14-产品演进"></a>

## 14. Product evolution

First, complete the in-depth Hong Kong foreign-sourced dividend MVP. Second, complete mainland China, Japan, and South Korea official source catalog research packages on the same platform and expand to standard research packages when resources permit, forming East Asia Release 1. Third, in 2027, complete outstanding standard research packages and expand to other Asia-Pacific jurisdictions according to resources and the expert network. Cross-jurisdiction comparisons must show content depth and professional validation status; basic source packages must not be described as complete tax advisory capabilities.
