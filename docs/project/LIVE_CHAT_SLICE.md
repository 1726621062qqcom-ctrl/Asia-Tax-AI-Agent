<a id="网页研究链路--实现与验证"></a>

# Web Research Workflow · Implementation and Validation

Date: 2026-09-27. The scope is the user-approved initial integration: questions, follow-ups, fact confirmation, existing rule analysis, and case recovery. It is not acceptance of the complete PRD or L1.

See [CLOUD_KNOWLEDGE_SLICE.md](CLOUD_KNOWLEDGE_SLICE.md) for later cloud and retrieval progress. Validation counts below retain the initial round's record; the newer record is authoritative for current connection status.

<a id="已实现"></a>

## Implemented

- FastAPI endpoints for cases, messages, fact changes, confirmation, and analysis; the frontend calls these actual endpoints.
- The model adapter uses `FSIE_MODEL_BASE_URL`, `FSIE_MODEL_API_KEY`, and `FSIE_MODEL_NAME` from the root `.env`. Configuration is reloaded for each request, so setting a key does not require restarting.
- The model proposes only candidate facts, subject to field, option, numeric range, and date validation; it cannot submit expert approval statuses or change the workflow.
- The backend chooses core follow-ups from known information. Explicitly unknown facts are not asked repeatedly, and conflicts require manual revision. Later fields may still be added through fact cards. Current follow-ups form a deterministic core interview, not a complete dynamic interview engine covering all rule dependencies.
- After user confirmation, the fact snapshot is saved and the existing rule engine is called. The existing 5 business nodes, human gate, and 5 unimplemented nodes are shown separately. Partial research is allowed on incomplete but conflict-free facts, retaining blockers.
- Messages, fact revisions, confirmation snapshots, rule package snapshots/hashes, source manifest hashes and records, and analysis history are persisted. Fact changes or additional messages invalidate earlier analysis.
- Optimistic version comparisons prevent old pages from overwriting new facts. Operation idempotency keys prevent a retry after a lost response from saving duplicate messages or results. Model failures do not change saved cases, and input remains on the current page.
- Original-text retrieval uses the implemented statutory-location mechanism for rules. If the knowledge database is unavailable, official index links are returned with an explicit notice that original text was not obtained; substitute citations are not generated.
- Chinese/English frontend interfaces, mobile layouts, loading/failure/retry states, results after confirmation, and recovery after refresh are connected.

<a id="运行"></a>

## Running

Initial local configuration:

```powershell
python -m venv .venv
.venv/Scripts/python.exe -m pip install -e ".[dev]"
cd apps/web
npm ci
npm run build
cd ../..
.venv/Scripts/python.exe scripts/run_chat.py
```

Open <http://127.0.0.1:8000>. The API also serves the built frontend, so a separate Vite server is unnecessary. For development, optionally run `npm run dev` in `apps/web` and open <http://127.0.0.1:5173>; that page uses a same-origin `/api` proxy to port 8000. Rebuild after frontend changes to update the static page on port 8000.

Set `FSIE_MODEL_API_KEY` in the root `.env`. Do not use a `VITE_` prefix, paste the key into chat, or commit it to Git. Model connection failures return only safe error codes to the page. Before the first send, the user confirms that only synthetic research data will be submitted. The normal startup path includes no test model or fixed answers.

<a id="存储及部署边界"></a>

## Storage and deployment boundaries

Sessions and knowledge now use cloud PostgreSQL, sharing `FSIE_DATABASE_URL` by default. `FSIE_WEB_DATABASE_URL` can specify separate PostgreSQL session storage. Old SQLite records remain and are not moved automatically. Unified migration with the existing CaseFile / Fact / FactVersion tables requires later work.

A random HttpOnly, SameSite=Strict cookie isolates browser workspaces. Writes require the same origin and a custom header; Host is restricted to loopback names. The service binds only to `127.0.0.1`. This round includes no account sign-in, organization roles, or public deployment authorization. Deleting the browser cookie leaves original cases in the database but removes access from a new workspace; complete account recovery and data retention policies are not implemented. The raw database connection string has been removed from `/health`.

Fact confirmation means the user has checked the inputs, not that a tax expert has approved them. Analysis has only a “pending review” status, with no fabricated approved or archived state. Saving current page results in the session database does not establish completion of report approval and archiving.

<a id="验证"></a>

## Validation

- Installed a separate repository `.venv`, removing dependence on an older worktree's interpreter; `pip check` passed.
- 94 backend offline tests passed (including 20 new tests); 11 database integration tests were not run.
- 6 browser tests passed, using the actual API, temporary database, and actual rule engine; **only the model extraction boundary and knowledge retrieval use controlled test responses**. The test server exists only in `tests/chat/serve_browser.py`; the normal application does not read test switches.
- The frontend TypeScript/Vite build passed. Chinese/English home pages, mobile layouts, and research result screenshots were inspected.
- The local port 8000 page, health check, and same-origin API proxy on port 5173 returned 200.
- After the user supplied a key, the actual DeepSeek smoke test passed: a separate test workspace was created through the local API. The first turn extracted 11 candidate fields and asked about multinational enterprise group status. The second correctly extracted group status, 10% ownership, 24 months of continuous holding, and unknown employee adequacy. Explicit confirmation executed 6 nodes (5 business nodes and the human gate), saved pending-review results and 6 associated official sources, and successfully restored results on rereading the case. Only synthetic cases were sent; keys were neither output nor committed.
- The knowledge database remained unavailable, and original-text retrieval returned `unavailable`. These two live model turns do not establish comprehensive model quality evaluation, original-text retrieval acceptance, or professional tax validation.

Test commands:

```powershell
.venv/Scripts/python.exe -m pytest -q -m "not integration"
cd apps/web
$env:PLAYWRIGHT_CHANNEL = 'chrome'
$env:FSIE_TEST_PYTHON = (Resolve-Path '../../.venv/Scripts/python.exe').Path
node node_modules/@playwright/test/cli.js test
```

After Python installation in CI, browser tests automatically start separate API 8001 / Vite 5174 services, without occupying the normal application or touching user sessions.

<a id="后续缺口"></a>

## Remaining gaps

Complete knowledge database integration and broader live model case regression; the other 5 business nodes; question-driven hybrid retrieval and applicability-period filtering; a complete dynamic question queue; unified business data migration; report approval/rejection/archiving; authentication, organization permissions, and recovery tests; Hong Kong tax expert validation. A working API key cannot replace any of these.

Implementation references the API layering and same-origin frontend/backend organization of the [official FastAPI full-stack template](https://github.com/fastapi/full-stack-fastapi-template) (MIT; no implementation copied), consistent with the existing React/Vite/FastAPI/SQLAlchemy stack.
