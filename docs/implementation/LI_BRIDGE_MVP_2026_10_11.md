<a id="li--zijian-第一条联调链路历史阶段记录"></a>

# Li × Zijian Initial Integration Workflow (Historical Record)

> This records the initial MVP, not the final integration. See the [merged handoff README](../../README_MERGED.md) and [integration acceptance record](COMBINED_INTEGRATION_ACCEPTANCE.md) for later shared facts, fixed structures, reports, and tests.

On 2026-10-11, local integration code was connected to Zijian's workspace using the complete Li release snapshot at `771e4524961bcc36718db1c9331e7a5f4cda0ce7`. It is a controlled engineering prototype, short of the original full dual-orchestration acceptance.

<a id="已接通"></a>

## Connected capabilities

1. **Case conversion.** Users save explicit entity, shareholding, flow, and event JSON in an existing case's Structure Analysis panel. `DomainCase` validates roles, percentages, dates, and size. The bridge converts it to Li `Case`, `Event`, and `Answers`, calling actual `planner.plan`. This path does not guess company ownership from old flat facts.
2. **Sessions/storage.** Li questions, answers, candidates, input hashes, and dates are stored in the same `chat_cases.document`, retaining owner/revision/request_id isolation, optimistic locking, and replay receipts. Answers rerun the engine first and save once on success; timeout/failure does not save partial updates. Existing fact changes stale domain results, requiring review/resave of structure details.
3. **Knowledge interface.** A separate read-only service performs exact/BM25 retrieval from Li `official.sqlite`, rereads originals by citation ranges, and validates SHA-256. It connects to the source panel/B analysis through existing `CKnowledgeProvider` `/search` and `/evidence` contracts. Some IRO subprovisions have explicit location mappings. A turn returns at most 12 passages; uncovered locations are individual gaps to stay within B's 14-read budget. Li sources remain display-only, `model_use=denied`, without professionally validated conclusions.
4. **Page.** The structure panel loads synthetic examples, saves, runs, accepts sequential answers, and restores on refresh. Results show status, candidate count, structure, and modeled tax bounds. Configuring C provider routes the existing Evidence panel to Li's service.
5. **Version isolation.** Domain calls run in one-shot Python subprocesses. Service/subprocess validate the pinned SQLite hash and file-set hash covering Python/CSV/JSON under `tax_graph`, Python under `official/tools`, and top-level `official` CSVs. Results record commit, input hash, and analysis date. Only the same release is accepted; mismatch rejects execution.

<a id="本地运行"></a>

## Local operation

Install project dependencies from the root and retain the complete Li snapshot with actual LFS `official/official.sqlite`. Set `FSIE_LI_RELEASE_DIR` to its absolute path; do not copy code or SQLite alone. Start knowledge service first:

```sh
python -m uvicorn apps.knowledge_api.main:app --host 127.0.0.1 --port 8010
```

Set `FSIE_AGENT_PROVIDER=c` and `FSIE_AGENT_C_URL=http://127.0.0.1:8010`, then run `python scripts/run_chat.py`. If using `FSIE_AGENT_C_TOKEN`, both processes share the value. Existing authentication/database configuration follows `.env.example`; build with `npm run build` in `apps/web`. The knowledge service should listen only on loopback.

Reproducible check:

```sh
FSIE_LI_RELEASE_DIR=/absolute/path/to/release python -m pytest -q tests/integration/test_li_bridge.py
```

Tests use actual Li SQLite/CSV, planner, B API, and local case database, plus in-process HTTP transport to check C wire behavior, original retrieval, B budgets, and gaps. Production PostgreSQL, actual models, and browser end-to-end workflows were not run; these tests are not deployment acceptance.

<a id="还要补的部分"></a>

## Outstanding work

- Unified facts: B flat facts and domain structures are stored alongside each other. Stable entity/flow IDs, field/unit/time mappings, old-case migration, and bidirectional updates remain. Users must confirm missing ownership; do not assign it to companies automatically.
- `assess_current`, `review_paid`, professional routing for ruling/library, and unified entry points for Li results and B reports/review are not open yet.
- Complete mappings for 21 B locations, combined Li statutory/original B ruling routing, applicability boundaries, permissions, and professional validation. Actual B analysis can obtain Li originals but incomplete coverage explicitly returns `insufficient`.
- Business forms/more examples: JSON input and one user-answerable question are currently shown. Complex grouped inputs, combined questions, conflicts/deferrals, and conditional tax bounds need product work.
- Dedicated PostgreSQL, actual model multi-turn tests, browser integration, timeout/concurrency/old-version replay, and tax expert review must precede consideration of a closed pilot.

Li delivered the code, materials, and examples for this version. These are our integration/acceptance tasks; Li need not rebuild Zijian's system unless a release-package defect is found.
