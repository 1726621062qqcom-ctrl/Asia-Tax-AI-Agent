<a id="东亚税务-ai-平台香港-fsie-mvp-设计索引"></a>

# East Asian Tax AI Platform (Hong Kong FSIE MVP) — Design Index

Date: 2026-08-15
Status: design confirmed by the user; MVP implementation has not started

<a id="设计决策"></a>

## Design decisions

- Start with Hong Kong; the first vertical scenario is foreign-sourced dividends received by multinational enterprise entities.
- Direct users are Hong Kong tax advisors; outputs are internal review drafts.
- Natural-language interaction uses a step-by-step interview rather than fixed forms as the primary entry point.
- Use a hybrid architecture: AI interviews and expression, deterministic rules, RAG citations, and human review.
- Manage authoritative sources, tax rules, and expert cases separately.
- The first release uses a modular monolith, Python API, PostgreSQL, full-text retrieval, and pgvector.
- Prefer an isolated single-tenant environment for the first pilot.
- The absence of Hong Kong tax experts does not block research prototype development, but all candidate rules and cases must be marked unverified.
- Hong Kong expert validation of core rules, judgment boundaries, and gold cases is mandatory before a closed advisor pilot.
- The 2026 scope is mainland China, Hong Kong, Japan, and South Korea; Hong Kong is the in-depth MVP and the other three receive standard corporate tax packages.
- Plan other Asia-Pacific jurisdictions after East Asia Release 1 acceptance.
- Do not implement the MVP before design and documentation approval.

<a id="正式文档"></a>

## Formal documents

- [Product requirements document](../../product/PRD.md)
- [Technical roadmap](../../architecture/TECHNICAL_ROADMAP.md)
- [2026 project plan](../../project/PROJECT_PLAN_2026.md)

<a id="研究参考"></a>

## Research references

- [IRD FSIE page](https://www.ird.gov.hk/eng/tax/bus_fsie.htm)
- [IRD FSIE FAQ](https://www.ird.gov.hk/eng/faq/fsie.htm)
- [IRD official FSIE examples](https://www.ird.gov.hk/eng/tax/fsie_example.htm)
- [OpenFisca Core](https://github.com/openfisca/openfisca-core): reference for separating rules and parameters; not used directly as a commercial foundation because of licensing and product positioning.
- [LQ.AI](https://github.com/LegalQuants/lq-ai): reference for legal citations and audit design.
- [pgvector](https://github.com/pgvector/pgvector): PostgreSQL vector retrieval extension for the MVP.
