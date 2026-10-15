<a id="agent-下一阶段改进建议"></a>

# Recommendations for the Next Agent Iteration

Date: 2026-09-27. Scope: PRD, technical roadmap, 2026 plan, cloud knowledge acceptance, plus D-002 and ruling research cards. Original planning documents were not changed.

<a id="总体判断"></a>

## Overall assessment

Natural conversation, cloud retrieval, fact confirmation, partial rules, and citation snapshots exist. Next prioritize the user task: understand the question → ask critical follow-ups → find applicable evidence → answer with citations → produce a reviewable draft.

Four findings: three P1 and one P2; two risks, one open decision, one confirmed documentation defect. The main improvement is directly answering from evidence. Evidence supports continued iteration, not complete PRD delivery or L1. Application tests, tax explanations, and staffing availability were not reverified.

<a id="已有优势"></a>

## Existing strengths

- The PRD clearly separates model expression, deterministic rules, and professional judgment.
- Cloud records explicitly acknowledge limits in keywords, source changes, permissions, and original-file archiving.
- Retry, confirmation, historical citation snapshots, and invalidation after fact changes already have foundations.

<a id="问题与建议"></a>

## Findings and recommendations

<a id="1-检索结果还未成为完整回答"></a>

### 1. Retrieval results are not yet complete answers

- ID: REV-001; P1; risk; product value/cross-document traceability; high confidence; pending.
- Evidence: PRD FR-05/FR-06 require itemized evidence and review drafts; CLOUD_KNOWLEDGE_SLICE “Retrieval method and boundaries” says inquiries return originals without source-based tax analysis.
- Consequence: users must read/combine materials themselves; multi-turn conversation cannot reliably complete research tasks.
- Recommendation: complete one dividend journey with a short answer, applicability conditions, missing facts, and itemized sources; state insufficient-evidence gaps. General chat stays natural; specific cases enter confirmation/rules.
- Owner: product/engineering.

<a id="2-证据进入模型的范围尚需明确"></a>

### 2. Scope of evidence permitted into models needs clarification

- ID: REV-002; P1; decision-needed; technical feasibility/data governance; high confidence; pending.
- Evidence: D-002 permits synthetic data only; all four ruling cards have model_input_authorized=false; cloud records exclude originals from external models.
- Consequence: attaching every original passage to current DeepSeek requests is not an authorized default.
- Recommendation: establish source allowlists/data categories; clarify public-source review, provider terms, and case de-identification. Unapproved materials remain retrieval/display-only; use approved processing routes. This describes current project constraints, not a legal conclusion that public materials cannot be processed by models.
- Owner: product/data owner/engineering.

<a id="3-工程测试不能替代回答质量验收"></a>

### 3. Engineering tests cannot replace answer-quality acceptance

- ID: REV-003; P1; risk; testability/delivery; high confidence; pending.
- Evidence: PRD 11.1/11.2 require frozen end-to-end cases, critical fact coverage, and citation validation. Offline rule cases, substitute browser tests, and live synthetic cloud cases cover only part.
- Consequence: all tests may pass while answers miss the question, citations fail to support conclusions, or blocking facts are omitted.
- Recommendation: build full conversation evaluation from the existing ten candidates, recording questions, required follow-ups, paths, expected passages, and prohibited outputs. Include unknowns, conflicts, missing evidence, out-of-scope cases, and source changes. Engineering expectations are not tax gold standards. With experts, expand to 30–50 validated cases.
- Owner: engineering/product; Hong Kong experts confirm professional correctness.

<a id="4-十节点自动规则表述与人工判断边界不一致"></a>

### 4. “Automatic ten-node rules” conflicts with human judgment boundaries

- ID: REV-004; P2; confirmed-defect; internal consistency/cross-document traceability; high confidence; pending.
- Evidence: CLOUD_KNOWLEDGE_SLICE's PRD gaps refer to complete automatic ten-node rules; PRD FR-04/roadmap 4.3 require human review for judgment matters.
- Consequence: complete node coverage may be mistaken for automation of every tax judgment.
- Recommendation: complete each node's inputs, rule results or human-review exit, evidence, and statuses, preserving professional boundaries.
- Owner: product/engineering.

<a id="对照关系与待核实事项"></a>

## Alignment and open checks

| Topic | Target document | Current record | Assessment |
|---|---|---|---|
| Evidence-based answers | PRD FR-05/FR-06 | Original passages/rule lists | Implementation gap, finding 1 |
| Judgment boundaries | PRD FR-04, roadmap 4.3 | “Automatic ten-node rules” | Wording conflict, finding 4 |
| Source updates | PRD 8.1/8.2 | Eight HTML sources changed, awaiting checks | Review changes/impact; do not automatically infer legal changes |
| Release progress | Plan M2/M3 | Partial engineering acceptance | Staffing, walkthroughs, and regional delivery unverified; dates alone establish neither completion nor delay |

The scanner reported zero mechanical candidates; this establishes neither semantic consistency nor acceptance. Terminal Chinese had encoding/display issues; this review manually checked UTF-8 originals.

<a id="推荐实施顺序及验收"></a>

## Recommended order and acceptance

1. **Build answers and evaluation together.** Keep casual chat; identify research, specific cases, and out-of-scope questions. Ask one main question when critical identity is unclear. Approved evidence supports concise answers and locatable sources for every substantive conclusion; do not guess without evidence. Start with full conversations for ten candidates.
2. **Dynamic interviews/ten-node coverage.** Order missing facts by effect on results; distinguish unknown, negative, conflict, and assumption. Complete deterministic results or human exits; do not repeat confirmed facts.
3. **Retrieval/version governance.** Generate queries from facts, nodes, and applicability periods; measure the current baseline before roadmap hybrid retrieval/reranking. Case comparisons show shared facts, differences, and applicability limits. Review source changes, establish cloud original versions, and invalidate affected reports.
4. **Drafts/human handling.** Draft facts, assumptions, paths, supporting/limiting evidence, and missing materials; support edits, approval/return reasons, and archived versions. Keep body concise with expandable evidence.
5. **Team use/release.** Implement real accounts, organization/case permissions, reviewer identity, least-privilege databases, cloud originals, recovery drills, and deployment. Identity/permissions precede team use; L1 additionally requires expert/data gates.

This is dependency order, not a schedule commitment. Prioritize Hong Kong depth; retain other jurisdictions' source-catalog baseline and recheck resources before expanding depth. Multi-Agent work, broad tax expansion, and large numbers of UI panels are not higher priorities.

Example: “How much tax is due on a dividend from mainland China?” First establish whether the recipient is an individual or company, then clarify whether the user means payer withholding or recipient treatment using tax identity. Gather context conversationally without adding a region selector. This is an interaction example, not a tax-rate determination.

<a id="文档变更建议尚未应用"></a>

## Proposed documentation changes (not applied)

<a id="建议修改-1修正节点完成标准"></a>

### Revision 1: correct node completion criteria

- CHG-001, linked to REV-004.
- Target: CLOUD_KNOWLEDGE_SLICE, gaps relative to PRD.
- Replace “complete automatic ten-node rules and dynamic evidence interviews” with “complete coverage of the ten-node decision chain, comprising deterministic rules and explicit human-review exits, plus dynamic evidence interviews.”
- Related edits: none. Check consistency with PRD FR-04/roadmap 4.3.
- Status: pending / not-applied.

<a id="建议修改-2增加下一轮可验收任务表"></a>

### Revision 2: add an assessable next-iteration task table

- CHG-002, linked to REV-001, REV-002, REV-003.
- Target: add “Current iteration tasks and evidence” in PROJECT_PLAN_2026.
- Insert target behavior, owners, dependencies, acceptance cases, failures, and evidence locations in the order above. The first item explicitly includes model source allowlists and complete conversation evaluation. Set dates after verifying capacity.
- Related edits: none. Check that candidates are not gold standards and the four-jurisdiction baseline/L1 gates remain unchanged.
- Status: pending / not-applied.

<a id="决策与追踪"></a>

## Decisions and tracking

| Revision | Affected file | User decision |
|---|---|---|
| 1: node completion criteria | CLOUD_KNOWLEDGE_SLICE.md | Pending |
| 2: iteration acceptance table | PROJECT_PLAN_2026.md | Pending |

| Item | Internal findings | Internal change |
|---|---|---|
| Answers, input scope, evaluation | REV-001, REV-002, REV-003 | CHG-002 |
| Ten-node completion criteria | REV-004 | CHG-001 |

Open decisions: permitted model input categories, current team capacity/owners, expert review scheduling. This report supports next-round task selection without changing authorization or claiming release acceptance.
