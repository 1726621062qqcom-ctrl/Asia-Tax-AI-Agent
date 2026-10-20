# Taxrora

The current `main` branch includes the tax chat workspace, A/B integration code, and combined orchestration, shared facts, and database interfaces for the pinned Li component release. See the [setup and run guide](docs/setup/README.md) for installation and operation, and start with the [acceptance testing entry point](docs/verification/README.md) before testing. The Li component is installed at a pinned version; later commits on the C branch do not automatically become part of `main`.

See the [account and authentication guide](docs/project/TAXORA_AUTH.md) for email sign-in and cloud user data configuration.

This project is an East Asian tax AI platform for corporate tax research and advisor review. Its primary MVP focuses on Hong Kong's foreign-sourced income exemption (FSIE) regime, with an extensible framework for official sources and rules covering mainland China, Japan, and South Korea.

The repository has passed engineering acceptance for the L0 internal research prototype (see the [L0 acceptance record](docs/project/L0_ACCEPTANCE_RECORD.md)). It does not yet provide formal tax advice or a product for direct client use. Progression to L1 requires validation by Hong Kong tax experts and completion of the security gates.

## Current delivery scope

- **L0 internal research prototype**: the default target for 2026, limited to controlled research and engineering validation.
- **L1 closed advisor pilot**: requires Hong Kong tax expert validation and completion of security and operational gates.
- **L2 production capabilities for clients**: outside the default scope for 2026.

Hong Kong is currently the only MVP with in-depth coverage. Under the conservative resource baseline, mainland China, Japan, and South Korea initially receive a `source-catalog baseline`, to be expanded into standard research packages when additional engineering and knowledge operations resources become available.

## Start here

- [Local installation and startup](docs/setup/README.md)
- [Cloud deployment and team updates](docs/project/RENDER_DEPLOYMENT.md)
- [Documentation and historical archives](docs/README.md)

## Core documents

- [Product requirements document](docs/product/PRD.md)
- [Technical roadmap](docs/architecture/TECHNICAL_ROADMAP.md)
- [2026 project plan](docs/project/PROJECT_PLAN_2026.md)
- [Critical documentation review](docs/archive/reviews/2026-08-15-prd-roadmap-project-plan-plain-language-review.md)
- [Documentation index](docs/README.md)

## Repository structure

| Directory | Current purpose |
|---|---|
| `docs/` | Product, architecture, project planning, integration acceptance, and design records |
| `apps/` | FastAPI API and React tax chat frontend |
| `packages/` | Data contracts, fact extraction, knowledge processing, rule execution, persistence, and reporting modules |
| `knowledge/` | Source catalogs, annotation definitions, and rule metadata approved for public release and version control |
| `tests/` | Offline unit tests and database integration tests |
| `evals/` | Evaluation inputs, historical run results, and supporting notes |
| `scripts/` | Startup, knowledge validation, and acceptance scripts |
| `infrastructure/` | Docker Compose configuration for local PostgreSQL / pgvector |
| `alembic/` | Database version migrations |
| `data/` | Local runtime data; ignored by Git and excluded from distribution |

The early web demo and its case analysis API remain on the `demo/hk-web` branch and have not been merged in full. The chat workspace on the current `main` branch is a separate, integrated frontend and API. See `Makefile` for development commands; its virtual environment paths and shell commands target Linux / WSL.

The [tax chat workspace](apps/web/README.md) provides Chinese and English interfaces and connects to cloud PostgreSQL through the API. It supports case interviews, fact confirmation, rule analysis, and recovery after a page refresh. Official statutory provisions and four ruling cases can be searched by identifier and Chinese or English keywords. Citations retain the original text, hash, capture date, and content change notices. Other development environments need database connections and model keys configured. See the [web research workflow record](docs/project/LIVE_CHAT_SLICE.md) and [cloud research workflow acceptance](docs/project/CLOUD_KNOWLEDGE_SLICE.md) for implementation scope and gaps.

```sh
cd apps/web
npm ci
npm run build
cd ../..
# Install Python dependencies first: python -m pip install -e ".[dev]"
python scripts/install_li_release.py
python scripts/run_chat.py
```

Open <http://127.0.0.1:8000>. Python 3.11+ and Node.js 20.19+ or 22.12+ are required. Configure the cloud `FSIE_DATABASE_URL`, model key, and Supabase email authentication in the root `.env`. Sessions use the same cloud database by default, with no SQLite fallback. Initialize the database with `python -m alembic upgrade head`. The public website is https://taxrora.onrender.com. Both local startup and the Render API entry point use `config/runtime.json` and the same application lifecycle: hybrid orchestration, bounded dynamic tools, and a managed read-only knowledge service. Render installs the pinned Li release during its build. See [deployment and startup](docs/project/RENDER_DEPLOYMENT.md).

Source inquiries now retrieve official passages from the cloud before generating explanations with citations. Passage IDs and verbatim quotations must pass validation before the response is saved. Missing evidence or citation validation failures are reported explicitly. See [current testing and handoff](docs/project/evaluations/README.md) for queries covering multiple provisions, limited topic keyword matching, context for short passages, and retesting with a live model. This citation check does not replace tax expert review of the explanation and its applicability.

## Knowledge and data security

- Prioritize verifiable official sources for the first release of professional materials.
- Manage RAG materials, deterministic rules, and case evaluations separately.
- Do not commit client cases, personal information, keys, `.env`, or restricted raw materials.
- On 2026-10-03, the user explicitly authorized sending public Hong Kong official statutory, guidance, and ruling passages from the source catalog to the configured DeepSeek service to produce explanations. This authorization excludes real client data and keys; fact extraction tests continue to use synthetic cases. The earlier restriction on sending official original text to models is updated within this scope; all other restrictions remain in effect.
- `knowledge/` stores only catalogs, metadata, annotation specifications, and rule definitions approved for version control.
- The first mainland China [official source catalog for cross-border dividends](knowledge/mainland_china/cross_border_dividends/README.md) has been loaded into the cloud database, covering five research topics and seven official sources. It currently contains catalog metadata only, with no mainland statutory passages or automated tax conclusions.
- System outputs must retain sources, rule versions, and applicability dates. Qualified professionals are responsible for final professional judgments.

## Project background

The project began as a TUM Project Study. Its longer-term goal is to expand gradually into an East Asian tax research and advisor support platform through controlled validation.
