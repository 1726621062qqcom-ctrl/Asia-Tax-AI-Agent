# Documentation Index

This directory contains product, technical, project governance, review, and design records. Planning documents are kept separate from implementation code so that scope, rules, risks, and acceptance gates can be reviewed independently.

## Where to start

| Task | Entry point |
|---|---|
| Install and run the current `main` | [Integrated setup and run guide](../README_MERGED.md) |
| Prepare to test the live workflow | [Acceptance testing entry point](verification/README.md) |
| Review the last integration test and outstanding items | [Integration acceptance record](implementation/COMBINED_INTEGRATION_ACCEPTANCE.md) |
| View evaluation inputs and historical results | [Evaluation index](../evals/README.md) |

The documents below provide product and implementation background. Historical plans or older evaluation results must not be treated as conclusions from the current acceptance round.

| Category | Document | Purpose |
|---|---|---|
| Product | [PRD](product/PRD.md) | Defines users, scope, features, knowledge governance, and acceptance criteria |
| Architecture | [Technical roadmap](architecture/TECHNICAL_ROADMAP.md) | Defines technical boundaries, data models, security, and implementation stages |
| Data | [Datasets and data sources](architecture/DATA_SOURCES_AND_DATASETS.md) | Defines the preloaded datasets needed for L0, their source channels, dependencies, and L1 data gaps |
| Implementation | [FSIE data extraction and validation plan](implementation/FSIE_DATA_EXTRACTION_VALIDATION_PLAN.md) | Defines legal sources, rules, fact extraction, validation, expert review, and regression release procedures |
| Project management | [2026 project plan](project/PROJECT_PLAN_2026.md) | Defines timelines, resources, owners, dependencies, and fallback plans |
| Review | [Critical review report](reviews/2026-08-15-prd-roadmap-project-plan-plain-language-review.md) | Records issues, approved changes, and regression check results |
| Design records | `superpowers/specs/` | Stores completed design process records |

Planning documents do not replace professional validation by tax experts in Hong Kong or other jurisdictions.

## B Agent integration development (2026-10-02)

- **Read first: [B module team handoff and iteration checklist (2026-10-04)](implementation/B_TEAM_HANDOFF.md)**: rules, scenarios, prompts, fallback behavior, the three entry points, A/C integration, attachment input, and unresolved alignment issues.
- [Free-form conversation tool execution loop and open-source approach selection](implementation/B_TOOL_HARNESS_DESIGN.md): capability catalog, pre- and post-tool validation, budgets, observations, stopping conditions, and switches.
- [Unified orchestration design and execution record for the three business entry points and free-form conversation (2026-10-03)](implementation/B_HYBRID_ORCHESTRATION_PLAN_2026_10_03.md)
- [Hybrid orchestration acceptance specification and engineering results (live model/C/PG acceptance pending)](implementation/B_HYBRID_ORCHESTRATION_ACCEPTANCE_2026_10_03.md)
- [B multi-turn evaluation dataset and actual API evaluation runner (62 scripts; online end-to-end workflow has not passed)](../evals/b_workflow/README.md)
- [Dynamic follow-up questions and conversational fallback design and implementation](implementation/B_GUIDED_INTAKE_DESIGN_2026_10_02.md)
- [Item-by-item audit of user-facing fields on GitHub](implementation/B_USER_FACT_FIELD_AUDIT_2026_10_02.md)
- [Detailed development plan](implementation/B_AGENT_IMPLEMENTATION_PLAN_2026_10_02.md)
- [Local operation and A/C handoff](implementation/B_AGENT_LOCAL_RUN_AND_HANDOFF.md)
- [Business workflow design](architecture/AGENT_BUSINESS_WORKFLOW_V0_1.md)
- [Business rules design](architecture/AGENT_BUSINESS_RULES_V0_1.md)
- [KnowledgeProvider contract](architecture/KNOWLEDGE_PROVIDER_CONTRACT_V0_1.md)
