<a id="真实聊天研究链路"></a>

# Live Chat Research Workflow

The user approved “question → dynamic follow-up → fact confirmation → rule analysis and sources.” Implement this slice without expanding to complete tax determinations, approval, or other jurisdictions. Retain the simple bilingual page.

<a id="方案"></a>

## Approach

Extend the existing FastAPI modules, reusing the fact dictionary, model adapter, and candidate rule evaluator. The approach retains fact confirmation and deterministic determinations, without adding another Agent framework, runtime, or state system.

The model extracts candidate facts only. The orchestrator asks answerable questions based on facts and gaps. Unknowns may be skipped but remain blockers; conflicts require explicit edits. Analyze only after the user explicitly confirms the frozen fact version. Any new information immediately invalidates old analysis; user text or model output cannot be interpreted as confirmation or approval.

<a id="存储与接口"></a>

## Storage and interfaces

- Use a separate SQLAlchemy session table for messages, fact versions, execution results, and analysis history; isolate browser workspaces with random HttpOnly session cookies.
- The existing local PostgreSQL is unreachable. Development defaults to `data/chat.sqlite3`; `FSIE_WEB_DATABASE_URL` may configure separate PostgreSQL storage. Do not silently downgrade the existing business database. This storage serves the local slice and does not establish migration of existing Fact/FactVersion tables or a production account system.
- `/api/session` initializes the workspace; `/api/cases` creates/restores cases. Messages, fact edits, confirmation, and analysis have separate case endpoints. Version comparisons prevent concurrent overwrites. Model calls do not hold database transactions; compare versions on commit. Idempotency keys prevent duplicate messages.
- The browser receives no keys or connection strings. The development server proxies to the local API on the same origin. Writes require a custom header and same-origin checks; no open CORS. Bind only to loopback.

<a id="分析与来源"></a>

## Analysis and sources

Execute the existing 5 business nodes and human gate, explicitly listing the remaining unimplemented nodes. Assemble results from actual rule returns; models cannot fill unimplemented nodes. Map sources only from the repository manifest. If PostgreSQL legal units are available, attach retrieved passages and locations; otherwise return links with an explicit original-text-unavailable status, without fabricated citations. Save complete rule/fact/source snapshots and summaries; historical versions are read-only.

<a id="交互与错误"></a>

## Interaction and errors

Retain the simple homepage and show actual follow-ups after sending. Backend-dictionary-driven fact cards support unknowns and explicit revisions. Backend state controls confirmation and analysis buttons. Provide explicit loading, failure, retry, stale-version, and refresh recovery feedback. Return safe model error codes without exposing provider responses or keys.

Chinese/English interfaces, questions, and result labels can switch languages; user originals are not translated. Safe statuses are not formal tax conclusions. Before initial model use, confirm that only synthetic or approved de-identified data is submitted according to existing project boundaries. Place this confirmation in the relevant interaction rather than adding a wall of explanation to the homepage.

<a id="验收"></a>

## Acceptance

Automated tests cover case isolation, refresh recovery, confirmation gates, unknown/conflicting facts, invalidation after changes, version conflicts, model failure retries and idempotency, missing sources, and bilingual/mobile interfaces. Actual DeepSeek calls use synthetic cases only and are validated once configuration is available; mock tests must not be reported as online passes when it is unavailable. Complete hybrid retrieval, 5 missing rules, expert validation, and approval/archiving are outside this delivery.

<a id="实施顺序"></a>

## Implementation order

1. Session persistence, dictionary validation, and deterministic follow-ups.
2. APIs, model calls, fact confirmation, and rule results.
3. Frontend API client, fact cards, and results UI.
4. Unit/API/browser tests and actual model validation when available.

Reference: the official FastAPI full-stack-fastapi-template (MIT; repository and issues checked; used only for layering and same-origin organization). Keep existing dependencies and avoid template version migration. DeepSeek uses the existing OpenAI-compatible chat/completions adapter.
