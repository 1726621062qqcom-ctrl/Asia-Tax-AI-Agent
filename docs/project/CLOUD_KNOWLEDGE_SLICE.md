<a id="云端知识与聊天研究链路"></a>

# Cloud Knowledge and Chat Research Workflow

Date: 2026-09-27. This round completed a controlled Hong Kong FSIE research workflow, not acceptance of the full PRD, L1, or client tax conclusions.

**Later update (2026-10-03)**: the implementation and validation records below are retained as historical records. Email accounts and answers based on public official passages are now integrated. The user has authorized sending public Hong Kong official materials to DeepSeek, excluding real client data. Original-text IDs, contiguous quotations, and source links are validated by the program, but explanations still need expert review. See [current testing and handoff](evaluations/README.md) for the latest scope, retest results, and remaining work.

<a id="可用流程"></a>

## Available workflow

1. The user enters a question. DeepSeek uses the latest 12 messages across both sides to distinguish ordinary conversation, source retrieval, and case updates, returning a reply, candidate facts, and retrieval intent in one call. Greetings, everyday conversation, and general explanations receive natural replies without querying the database or changing confirmed facts. Only inquiries explicitly requiring official sources trigger retrieval. Specific case details trigger fact extraction while retaining confirmation.
2. Retrieval supports four ruling identifiers (68, 72, 74, 75), statutory identifiers, and Chinese/English keywords for a limited set of tax topics. No matches are explicitly shown as empty results; connection failures return retryable errors, and failed messages are not persisted.
3. Case workflows retain field-by-field follow-up questions and explicit fact confirmation. Analysis runs the existing five business rule nodes and human gate, attaching original-text citations to each node.
4. Financial entity exclusion, foreign taxation and switchover, anti-hybrid rules, main purpose, and filing/evidence retention produce explicit human review tasks, missing fields, and statutory navigation; they are not automatically determined.
5. Dividend analysis includes two official ruling references selected by keyword matching, retaining all seven sections of each. Case relevance does not establish applicability, and rulings are not converted into conclusions for the user's case.
6. Results, original text, and source metadata are frozen in session JSON. Later database imports do not rewrite saved citations. Fact changes mark earlier analysis as stale.

<a id="云端配置与数据"></a>

## Cloud configuration and data

- `FSIE_DATABASE_URL` points to Supabase Session pooler PostgreSQL; standard `postgresql://` URLs are automatically converted to the psycopg driver. Sessions use the same connection by default; the application does not create a local database by default.
- The existing 10 in-scope official sources have been imported, comprising 697 passages; the four rulings contain 28 sections. The 2023 disposal gains amendment source remains excluded according to the manifest.
- Hashes for 8 HTML sources differ from the original manifest. The manifest was not changed to conceal the differences, and the frontend marks them for review. Capture dates are not legal effective dates; this download does not advance the original manifest's coverage cutoff.
- Migration `0004_cloud_chat_rls` takes over the existing session table and enables RLS on application tables without client policies. The server uses a trusted database account; the browser does not receive connection credentials. This does not replace sign-in, organization permissions, or production least-privilege design.
- Legal and case queries read from the cloud. Raw downloads remain in the local Git-ignored raw directory; cloud original-file archiving and backup recovery drills remain outstanding. Original passages and source hashes are already in the cloud.
- Old SQLite sessions are not migrated automatically. Random browser cookies are not team accounts; private cases in different browsers are isolated.

<a id="检索方法与边界"></a>

## Retrieval method and boundaries

Statutory or ruling identifiers use exact lookup. General keywords first use bound-parameter candidate retrieval in PostgreSQL (at most 120 candidates), then rank by matches and passage length, limit each source to two passages, and return at most seven results. Chinese uses fixed topic mappings; arbitrary Chinese semantic coverage is not claimed.

Embeddings, vector indexes, reranking models, and freely generated tax conclusions based on original sources are not integrated. Ordinary conversation uses natural replies from the actual model; source inquiries return original quotations; case analysis uses deterministic rules and review checklists. Official ruling originals are not sent to external models. Source catalog filtering prevents unregistered sources from entering citations directly.

<a id="验证与复现"></a>

## Validation and reproduction

Actual results in this round: 100 offline tests passed; 7 browser tests passed; the actual DeepSeek service extracted 13 candidate fields, and confirmation saved 21 statutory passages, 14 sections from two reference cases, and five review tasks in the cloud. Each of the four ruling identifiers returned seven sections; an unrelated weather query returned no results. Cloud records were consistent on rereading, RLS was enabled, and fact changes invalidated earlier analysis. Synthetic validation cases were cleaned up.

Later natural-conversation fixes: 108 offline tests and 8 browser tests passed. The actual model was verified over three consecutive turns for a greeting, capability introduction, and request to switch to English; all returned natural chat without generating case facts, and could then transition to ruling retrieval. Ordinary messages, assistant replies, and limited structured interview context feed later turns; original source text remains excluded from external model input. One actual model call failed and was not counted as success. Idempotent retries with the same request were retained, and delivery followed successful retesting.

Sending interaction improvements: clicking send immediately shows the user message, clears the submitted input, and displays a three-dot waiting animation at the assistant position; the next draft remains editable. On success, server records replace temporary messages. On failure, the message is marked incomplete and the original input is restored without overwriting a new draft; retries use the original request ID. Waiting and error states are shown per case. Pending messages exist only in frontend memory; the backend still saves a completed turn atomically. Another 10 browser tests and the production build passed, covering controlled delays, sending failures, preservation of new drafts, and retries without duplication.

- Offline: `python -m pytest -q -m "not integration"`, covering rule regression for 10 synthetic candidate cases, two ruling HTML structures, identifiers/keywords/empty results, no writes on failure, citation snapshots, confirmation protection, and API boundaries.
- Browser: run Playwright in `apps/web`. Test servers use separate temporary databases and explicit model/knowledge substitutes, covering Chinese/English interfaces, refresh, fact confirmation, source change notices, empty retrieval results, and mobile layouts.
- Live cloud: start `scripts/run_chat.py`, then run `python scripts/verify_cloud_chat.py`. It uses a separate cookie workspace, synthetic case details, and actual DeepSeek/cloud retrieval to check persistence, citations, RLS, and invalidation after fact changes; only test cases created by the script are deleted. Results are written to the Git-ignored `reports/cloud-chat-verification.json`, without credentials or case details.
- The old 11 database integration tests were not run against the shared cloud database to avoid their initialization affecting data.

<a id="与-prd-尚有的差距"></a>

## Remaining gaps relative to the PRD

Complete automatic ten-node rules and dynamic evidence interviews, vector hybrid retrieval and recall evaluation, expert validation and gold cases, advisor approval and report archiving, account/organization permissions, cloud original-file storage and recovery, freezing affected results after regulatory changes, and public deployment remain separate future tasks. Engineering acceptance in this round must not be treated as certification of professional correctness.

<a id="实现依据"></a>

## Implementation references

Before development, the [official pgvector repository](https://github.com/pgvector/pgvector) was checked for its PostgreSQL License, version, and open issues. Its hybrid retrieval example shows how lexical and vector retrieval can share PostgreSQL. This round adds no vector dependencies and validates lexical and identifier retrieval first. The existing [SQLAlchemy](https://github.com/sqlalchemy/sqlalchemy) (MIT) bound-parameter approach and ORM are retained; no external implementation was copied. Supabase connections follow its [official connection guide](https://supabase.com/docs/guides/database/connecting-to-postgres).
