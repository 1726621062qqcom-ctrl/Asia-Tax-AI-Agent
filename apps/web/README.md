# AsiaTax · Tax Chat Workspace

A Chinese and English chat interface that calls the FastAPI endpoints for cases, messages, fact confirmation, and research analysis. Case details and sources expand on demand. The interface retains tax icons and mobile support, with no region selector or fixed assistant answers.

## Startup

From the repository root, install the Python 3.11+ dependencies and frontend dependencies first:

```sh
python -m pip install -e ".[dev]"
cd apps/web
npm ci
npm run build
cd ../..
python scripts/run_chat.py
```

Open <http://127.0.0.1:8000>; the same service serves the frontend and API. The Python interpreter in the root `.venv` is recommended. For development, also run `npm run dev` in `apps/web` and use <http://127.0.0.1:5173>; the same-origin `/api` proxy forwards to port 8000.

The backend reads `FSIE_MODEL_API_KEY` from `.env`; do not use a `VITE_` prefix. After updating it, the configuration is reread on the next send or retry. Without valid model configuration, sending produces an explicit error and preserves the input; it does not fall back to fixed answers.

## Workflow and boundaries

1. Describe a synthetic research case and confirm the data scope before the first message.
2. The model extracts candidate facts, and the backend asks core follow-up questions. You can also open fact cards to add, revise, or mark facts as unknown.
3. Save changes and click “Confirm facts and analyze.” Confirmation is blocked while conflicts remain.
4. Review research results from the existing rules, blockers, missing nodes, fact and rule versions, and sources.
5. Later changes invalidate the previous analysis; confirm and analyze again. Cases and results can be restored after a page refresh.

Sessions are saved by default to the cloud PostgreSQL database specified by `FSIE_DATABASE_URL`; use `FSIE_WEB_DATABASE_URL` to select another database. A random HttpOnly browser cookie isolates workspaces. localStorage stores only language preferences, and unsent drafts remain only in the current page's memory. Clearing the cookie removes access to the original workspace; this is currently not a complete account system. Old SQLite sessions are not migrated automatically.

The live model, knowledge database, and complete professional review workflow still require separate validation. There are currently only five business rule nodes. When the source database is unavailable, the interface shows only clearly labeled official index links. Full hybrid retrieval, professional approval, report export, and cross-region capabilities are not available. See the [implementation and validation record](../../docs/project/LIVE_CHAT_SLICE.md).

## Tests

```sh
npm run build
npx playwright install chromium
npm test
```

Tests require a Python environment with the project installed. By default, they use `python` from PATH; set `FSIE_TEST_PYTHON` to the absolute path of the root `.venv` interpreter if needed. On Windows, set `PLAYWRIGHT_CHANNEL=chrome` to use an installed Chrome browser. Tests automatically start isolated services on ports 8001/5174.

Six browser tests cover the bilingual initial screen, real API calls and persistence, the confirmation gate, rule results, invalidation after changes, retry after model failure, conflict revision, case isolation, input method handling, and mobile focus. The model boundary uses test responses and does not establish successful live model calls. Screenshots are stored in the untracked `test-results/` directory.

## Structure

- `src/api.ts`: same-origin API calls, timeouts, and safe error codes.
- `src/hooks/useWorkspace.ts`: session recovery, idempotent retries, and frontend state.
- `src/components/FactEditor.tsx`: dictionary-driven fact revision and confirmation.
- `src/components/Conversation.tsx`: follow-up questions, actual rule results, and sources.
- `src/locale.tsx` / `src/locales/`: Chinese and English interface and workflow text.
- `src/workspace.ts`: API types, quick questions, and official source index.

## References and licensing

Conversation organization was informed by [Vercel Chatbot](https://github.com/vercel/chatbot) (Apache-2.0), and API organization by the [official FastAPI template](https://github.com/fastapi/full-stack-fastapi-template) (MIT); their implementations were not copied. The page design is original, and v0 was used only to discuss design direction. Lucide is used under the ISC/MIT licenses included in its package; React and Vite use MIT. See [THIRD_PARTY_NOTICES.txt](public/THIRD_PARTY_NOTICES.txt) for runtime license notices.
