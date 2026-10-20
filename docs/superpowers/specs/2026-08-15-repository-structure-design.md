<a id="asia-tax-ai-agent-仓库结构设计"></a>

# Asia Tax AI Agent Repository Structure Design

| Item | Details |
|---|---|
| Status | User confirmed; implement as designed |
| Date | 2026-08-15 |
| Target branch | `main` |

<a id="1-目标"></a>

## 1. Objective

Establish an extensible documentation-first repository. New contributors should quickly understand objectives, stage, document locations, and future code boundaries without creating nonfunctional Python/frontend/database/deployment scaffolding.

<a id="2-设计原则"></a>

## 2. Principles

- Hong Kong FSIE is the in-depth MVP; mainland China, Japan, and South Korea are later East Asian expansion.
- Separate product, technical, project, and review records.
- Define future directory responsibilities in READMEs without prematurely fixing unimplemented structures.
- Exclude client data, keys, environment variables, temporary renderings, local review artifacts.
- Move only the four user-specified documents; preserve other files/uncommitted edits.
- Add no open-source license without the user's choice.

<a id="3-目标结构"></a>

## 3. Target structure

```text
Asia-Tax-AI-Agent/
├── README.md
├── .gitignore
├── docs/
│   ├── README.md
│   ├── product/
│   │   └── PRD.md
│   ├── architecture/
│   │   └── TECHNICAL_ROADMAP.md
│   ├── project/
│   │   └── PROJECT_PLAN_2026.md
│   ├── reviews/
│   │   └── 2026-08-15-prd-roadmap-project-plan-plain-language-review.md
│   └── superpowers/specs/
│       └── existing design records
├── apps/
│   └── README.md
├── packages/
│   └── README.md
├── knowledge/
│   └── README.md
├── tests/
│   └── README.md
├── scripts/
│   └── README.md
└── infrastructure/
    └── README.md
```

Git does not track empty directories. Use meaningful `README.md` responsibilities rather than `.gitkeep`.

<a id="4-文件职责"></a>

## 4. File responsibilities

<a id="根目录-readme"></a>

### Root README

Explain vision, delivery level, jurisdictions, core documents, structure, development state, and data boundaries. Do not claim implementation or client readiness.

<a id="文档目录"></a>

### Documentation

- `docs/product/`: scope/users/requirements/acceptance.
- `docs/architecture/`: architecture/data/security/roadmap.
- `docs/project/`: schedule/resources/owners/dependencies/milestones.
- `docs/archive/reviews/`: reports/approvals/regression.
- `docs/superpowers/specs/`: existing design history, without migration/rewrite in this task.

<a id="未来代码目录"></a>

### Future code

- `apps/`: deployable workspaces/APIs.
- `packages/`: reusable rules/retrieval/evaluation/shared types.
- `knowledge/`: public/version-controlled catalogs/annotations/rule metadata.
- `tests/`: automation/evaluation/data-use rules.
- `scripts/`: repeatable processing/checks/development.
- `infrastructure/`: future deployment/database/environments; no actual infrastructure files now.

<a id="5-四份文件的移动规则"></a>

## 5. Four document moves

| Current | Target |
|---|---|
| `docs/PRD.md` | `docs/product/PRD.md` |
| `docs/TECHNICAL_ROADMAP.md` | `docs/architecture/TECHNICAL_ROADMAP.md` |
| `docs/PROJECT_PLAN_2026.md` | `docs/project/PROJECT_PLAN_2026.md` |
| `docs/archive/reviews/2026-08-15-prd-roadmap-project-plan-plain-language-review.md` | Unchanged |

Fix relative links in the three core documents/root README. Keep stable review filenames for dates/subjects.

<a id="6-gitignore-边界"></a>

## 6. `.gitignore` boundaries

Ignore:

- `.env`, keys, local environments; allow `.env.example`.
- Python/Node/test/build/editor caches.
- Virtual environments/logs/temp/OS files.
- `.codex-doc-review/` and local rendering/review artifacts.
- `knowledge/**/raw/`, `data/`, and potentially restricted raw data.

Ignore rules prevent accidental commits, not replace access control for client data/secrets.

<a id="7-git-整合方式"></a>

## 7. Git integration

Remote default `main` has an initial README; local `master` documentation history has no common ancestor. Preserve both histories through nonforced integration, resolve README, then push to main. Never force-overwrite remote history.

Scope: framework READMEs, base `.gitignore`, updated root README, four documents/moves/link fixes. Exclude existing review caches and unrelated untracked designs.

<a id="8-验收标准"></a>

## 8. Acceptance

- Git tracks every target directory and READMEs define responsibilities.
- Root README directly links all four documents.
- Moved documents retain working links; versions follow formal Git publication rules.
- Deterministic documentation scans, relative links, `git diff --check` pass.
- No `.env`, keys, client data, restricted originals, `.codex-doc-review/` in commits.
- Update remote main with ordinary fast-forward push, never force.
