<a id="knowledgeprovider-接口契约与模拟检索行为设计-v01"></a>

# KnowledgeProvider Contract and Mock Retrieval Design v0.1

| Item | Details |
|---|---|
| Date | 2026-10-02 |
| Status | B design contract; Provider, HTTP/MCP services, and real database connection not yet implemented |
| Current conditions | A page ready for integration; C database unfinished |
| Delivery | Common interface/semantics, permissions/errors, fixed fixtures, acceptance scenarios |
| Related | [Workflow v0.3](AGENT_BUSINESS_WORKFLOW_V0_1.md) · [Rules v0.2](AGENT_BUSINESS_RULES_V0_1.md) |
| Examples | [knowledge_provider_mock_fixtures.v0.1.json](knowledge_provider_mock_fixtures.v0.1.json) |

<a id="1-接入边界"></a>

## 1. Integration boundary

```text
Existing A pages
  → B agent and business workflow
    → KnowledgeProvider (unified contract)
      → MockKnowledgeProvider (current development/testing)
      → CKnowledgeProvider (subsequent API / MCP / read-only database adapter)
```

B determines when/what to retrieve, response checks, permissions, answer structure, and failures. C owns sources, database, retrieval, and rights metadata. A owns pages/citations. B separately persists conversations, cases, questions, and reply versions.

Server configuration selects providers. Business requests have no fixture_id; users/models cannot select providers/fixtures. Real failures never automatically fall back to Mock. Test drivers set scenario_id outside the online query protocol.

Conceptual interface, not importable code:

```text
search_evidence(request, trusted_context) -> SearchResult
get_evidence(reference, purpose, trusted_context) -> EvidenceResult
```

Authentication/fixed development identity supplies trusted_context containing access scope, processing environment, and policy. Models cannot supply authorized identity. purpose is model or display. get_evidence rechecks current permissions; previous successful search is insufficient.

<a id="2-查询输入-searchrequest"></a>

## 2. SearchRequest

| Field | Type/requirement | Semantics |
|---|---|---|
| schema_version | Required string, 0.1.0 | Reject incompatible contracts |
| request_id, trace_id | Required strings | Call identity/tracing; preserve logical retry associations |
| query | Nonempty string | Current question/issue; retain exact identifiers |
| intent | Enum | concept / reference_lookup / case_analysis |
| jurisdiction, topic, income_type | string/null | Filter known values; explicit null for unknown, no silent jurisdiction defaults |
| entity_type | company / individual / unknown / not_needed | Case-dependent; identifier queries need no entity question |
| applicable_date | ISO date/null | User/case applicability date, never today's date by default |
| date_status | actual / planned / unknown / not_needed | unknown/not_needed require null; actual/planned require explicit dates |
| reference_number | string/null | Preserve complete provision/ruling identifier format |
| fact_filters | Required array, possibly empty | Necessary field/value/status/fact_version only; unknown never negative |
| language | string | Desired result language; evidence separately declares original language |
| limit | Positive integer | Result limit, constrained by server maximum |
| deadline_ms | Positive integer | Remaining call budget; no unlimited wait |

B asks for missing minimum query information instead of asking C to guess. Do not send full conversations, passwords, or irrelevant client facts. Cache keys include trusted access scope/environment.

<a id="3-返回-searchresult"></a>

## 3. SearchResult

| Field | Type | Requirement |
|---|---|---|
| schema_version, request_id, trace_id | string | Match contract/request |
| retrieval_id | string | Unique retrieval record |
| provider | mock / c | Trusted adapter, not model-generated |
| is_synthetic | boolean | Mock true; actual C reflects actual provenance |
| corpus_version | string/null | Index/corpus snapshot; absent means unverified version |
| status | ok / partial / no_match / error | Query status, not legal applicability/evidence sufficiency |
| evidence | Evidence array | Empty on error/no_match; partial results require partial |
| coverage | object | unchecked / partial / sufficient_for_task / not_assessed, with scope/missing_requirements/truncated |
| error | object/null | On error: code/message/retryable; no credentials/raw sensitive data |
| timings_ms | object | db/retrieval/rerank/total nonnegative or null; Mock null, not performance evidence |

ok means successful call with results, not complete case conditions. sufficient_for_task requires check evidence and a defined task; B checks intended claims independently. Truncation/pagination is not full coverage. If all hits disallow model use, preserve actual ok/partial/permissions; B emits EVIDENCE_RESTRICTED, not no_match.

### Evidence

Every item includes:

- **Identity:** evidence_id, source_id, source_version_id, unit_id, content_hash (original unit SHA-256), is_synthetic.
- **Provenance:** title, publisher, source_type (law / guidance / case / synthetic_test), language, nullable url, locator.
- **Applicability:** jurisdiction, topic, publication_date, effective_from, effective_to, verification_status (verified / unverified / unknown). Unknown dates are null; publication is not effective date.
- **Permissions:** independent model_use/display_use (allowed / denied / unknown), policy_version, restriction_reason. Undeclared means unknown, never allowed by default.
- **Projection:** nullable model_text/display_ref. Nonempty model_text requires model_use=allowed; resolvable display_ref requires display_use=allowed.

Models consume only explicitly approved model_text and necessary server-approved metadata projections, never entire Evidence JSON. Server visibility does not authorize model use. Remove/redact undisplayable titles/metadata or omit the item rather than leak it to satisfy a required field.

display_ref contains evidence_id/source_version_id/unit_id, resolved by get_evidence(..., purpose=display). It is a locator, not a credential. Model-only materials cannot be echoed to users. Missing permitted source display becomes a citation gap and may require withdrawing claims.

content_hash covers the original unit, not a truncated summary. Extracts retain exact locators; C summaries identify their type/source rather than impersonating originals. Mock uses identical unit/model text for simplicity.

<a id="4-按引用取原文"></a>

## 4. Retrieve originals by reference

get_evidence takes request_id, trace_id, schema_version, complete reference (evidence_id/source_version_id/unit_id), and server-selected purpose.

Returns status (ok / not_found / restricted / version_unavailable / error), reference, content_hash, text, is_synthetic, error. Only ok permits nonempty text, matching the exact reference/hash.

Never resolve old references to latest versions automatically. Missing old versions return version_unavailable; changed permissions return restricted. A reads through B's proxy or an agreed C display service; transport awaits A/C agreement. B need not implement UI components.

<a id="5-检索结果到-agent-行为的映射"></a>

## 5. Retrieval-to-Agent mapping

| Result | B checks | Next action |
|---|---|---|
| ok + permitted | Version/scope/claim support | Compose if sufficient, otherwise EVIDENCE_INSUFFICIENT |
| partial | Gaps/truncation/supportable claims | Supported portions only, explicit limits, one question if needed |
| no_match | Distinguish no hits from transport failure | NO_MATCH and query gaps; no guessed conclusions |
| All hits model-restricted | Separate model/display rights | EVIDENCE_RESTRICTED; permitted displays in reference_only |
| Missing/unknown rights | Deny model use | Record rights gap; models cannot determine authorization |
| error | Cause/transience/budget | RETRIEVAL_FAILED; retry temporary failures only, bounded |
| Invalid fields/incompatible version | Contract | PROVIDER_CONTRACT_ERROR; no original passthrough |
| Unresolved citations | Exact version/original | CITATION_UNRESOLVED; repair/withdraw claims |

Generation failures belong to B, not fabricated Provider no_match/error. Return MODEL_FAILED; reuse retrieval only while snapshots/permissions/facts remain valid. Share retries across B/client layers; independent nested retries must not multiply requests.

<a id="6-mockknowledgeprovider-行为"></a>

## 6. MockKnowledgeProvider behavior

Mock is a future implementation specification. This delivery has loadable JSON fixtures, not a callable Provider class. Test drivers choose scenarios outside business parameters. Fixed results/versions are repeatable, without networking or invented “real legislation.”

| Scenario | Result | Check |
|---|---|---|
| MOCK-01 | ok, model/display allowed | Direct points/conditions/resolvable citations; all marked synthetic |
| MOCK-02 | no_match | No unsupported conclusions or pointless retries |
| MOCK-03 | ok, display only | reference_only available; restricted body absent from every model input |
| MOCK-04 | error, temporary timeout | Bounded retry then retrieval failure |
| MOCK-05 | partial, missing required sources | Supported scope only, no overall completion |
| MOCK-06 | ok, unknown rights | No model/display of unknown-permission originals |
| MOCK-07 | ok, date does not cover target | Applicability gap, not definitive case evidence |
| MOCK-08 | error, nonretryable denial | No retry, identity switching, or fake Mock success |

Fixture display_store simulates C originals for test get_evidence only, outside search responses. Never send entire fixtures to models. Original retrieval rechecks rights.

Additional injections: remove required fields → contract error; change reference version → version_unavailable; fail generation → MODEL_FAILED and check reuse. These are proposed runtime tests, not model/service tests performed here.

<a id="7-切换到-cknowledgeprovider"></a>

## 7. Switching to CKnowledgeProvider

1. C supplies interface/read-only-view documentation, examples, permissions, source version policy; credentials use service configuration, never documents/model messages.
2. B maps fields/defaults: unknown rights, null missing dates, no fabricated verification.
3. Share contract tests for normal/no-match/partial/restricted/failure/old references.
4. Compare actual originals/citations and measure performance/quality/corpus versions; Mock does not establish actual acceptance.
5. Enable C through server configuration. Switch back to Mock only in test environments when needed, retaining markers.

Equivalent semantics can adapt directly. Different rights, version retention, or coverage require contract/capability changes and regression; arbitrary C structures are not guaranteed zero-change integration.

<a id="8-完成标准与当前状态"></a>

## 8. Completion criteria/status

Design completion requires explicit boundaries, interpretable I/O/errors, separate model/display permissions, critical Mock branches, clear B/C/A responsibility; defined here.

Pending: Provider classes, transport, trusted filters, context construction, original service, actual model/page integration, persistence, real C connection. Fixture checks establish design consistency only, not runtime isolation, tax correctness, or performance.

2026-10-02 checks passed identifiers, status combinations, dates, synthetic flags, rights/projections, references/hashes for 8 fixtures, plus links/fences/Git whitespace. No Provider/model/C database/frontend integration tests ran.

<a id="9-与-a-的-zhihong-wu-分支对接代码核查"></a>

## 9. A `Zhihong-Wu` integration (code audit)

Read commit `7054c45323abf7d63d9725f03f81dab892c98110` on 2026-10-02. These are actual interfaces at that commit, not assumed future C delivery. A has React, FastAPI chat, persistence, lexical/identifier retrieval; this is A's implementation, not final C capabilities.

<a id="91-现有前端如何调用后端"></a>

### 9.1 Frontend calls

- [`apps/web/src/api.ts`](https://github.com/ZhihongWu-dev/Asia-Tax-AI-Agent/blob/7054c45323abf7d63d9725f03f81dab892c98110/apps/web/src/api.ts): `POST /api/cases/{id}/messages` with `text, data_approved, revision, request_id`, requesting `text/event-stream`; consumes delta/error/done, with complete done.case. Also `GET /api/knowledge/search?q=...`, sessions/cases, facts/confirmation/analysis.
- [`apps/web/src/hooks/useWorkspace.ts`](https://github.com/ZhihongWu-dev/Asia-Tax-AI-Agent/blob/7054c45323abf7d63d9725f03f81dab892c98110/apps/web/src/hooks/useWorkspace.ts): generates request IDs/revisions, reuses operations on retry, reloads on refresh. Preserve idempotency/conflicts/same-case recovery.
- [`apps/web/src/workspace.ts`](https://github.com/ZhihongWu-dev/Asia-Tax-AI-Agent/blob/7054c45323abf7d63d9725f03f81dab892c98110/apps/web/src/workspace.ts): Case has messages/facts/questions/analyses/confirmed_revision; Message.kind includes chat/research/analysis/intake; KnowledgeResult has status/passages/method/query. Preserve old fields initially.
- [`apps/web/src/components/Conversation.tsx`](https://github.com/ZhihongWu-dev/Asia-Tax-AI-Agent/blob/7054c45323abf7d63d9725f03f81dab892c98110/apps/web/src/components/Conversation.tsx): research shows message.text/research.passages; analysis resolves analysis_id in Case.analyses. Expandable passages/sources exist; claim-to-evidence interaction does not.

<a id="92-b-应接在哪一层"></a>

### 9.2 B integration layer

| Location | Current behavior | B action |
|---|---|---|
| [`apps/api/chat.py`](https://github.com/ZhihongWu-dev/Asia-Tax-AI-Agent/blob/7054c45323abf7d63d9725f03f81dab892c98110/apps/api/chat.py) | ChatService routes, JSON/SSE, get_service construction | Preserve paths/body, inject B; common decisions |
| [`packages/chat/service.py`](https://github.com/ZhihongWu-dev/Asia-Tax-AI-Agent/blob/7054c45323abf7d63d9725f03f81dab892c98110/packages/chat/service.py) | plan_turn chat/research/intake; commit_turn researcher(query), facts/messages | Add routing/questions/rights/scope/versions/replies; retain storage/idempotency |
| [`packages/chat/streaming.py`](https://github.com/ZhihongWu-dev/Asia-Tax-AI-Agent/blob/7054c45323abf7d63d9725f03f81dab892c98110/packages/chat/streaming.py) | Model reply deltas before retrieval/commit | Share B logic; validate substantive claims before output. Progress-only/direct done remains compatible |
| [`packages/chat/knowledge.py`](https://github.com/ZhihongWu-dev/Asia-Tax-AI-Agent/blob/7054c45323abf7d63d9725f03f81dab892c98110/packages/chat/knowledge.py) | Source/LegalUnit reads; available / no_matching_units / unavailable and passages; no external-model originals | Add common Provider/Evidence adapters for Mock/C, map to legacy display |
| [`packages/chat/store.py`](https://github.com/ZhihongWu-dev/Asia-Tax-AI-Agent/blob/7054c45323abf7d63d9725f03f81dab892c98110/packages/chat/store.py) | chat_cases documents, optimistic revisions/receipts | Store states/questions/source versions in the same case or controlled related tables, not unrelated session IDs |

Assigning C/Mock to researcher alone is insufficient: query-only calls lack issue, dates, fact version, environment, access scope. Extend service context/adapters identically for JSON/SSE. Frontend/models never access C connections.

<a id="93-最小兼容响应与功能差距"></a>

### 9.3 Minimal compatible response/gaps

Retain A's structure initially:

```json
{
  "type": "done",
  "case": {
    "id": "existing-case-id",
    "revision": 2,
    "state": "existing-agreed-state",
    "messages": [
      {
        "id": "backend-generated-message-id",
        "role": "assistant",
        "kind": "research",
        "text": "Key points: ...\n\nApplicable conditions: ...\n\nReferences: [1] (mock example)",
        "research": {
          "status": "available",
          "method": "mock_provider_adapter",
          "query": "query-for-this-turn",
          "passages": []
        }
      }
    ],
    "facts": {},
    "questions": [],
    "analyses": [],
    "confirmed_revision": null,
    "data_approved": true
  }
}
```

This illustrates field placement, not a complete Case. Retain required titles/timestamps and actual history. passages contains **display_use=allowed** projections only; model context separately uses approved model_text, never entire retrieval JSON. Message.text may organize points/conditions/citations as Markdown. Clickable claim [1] → evidence requires a B mapping plus A UI; expandable materials alone are not claim-level citation.

Existing research reply is a preretrieval preamble. B must compose validated answers after retrieval from permitted/applicable sources. Display-only originals permit viewing/limitations, not model summarization. No evidence, retrieval failure, and model failure use distinct safe errors.

FactEditor's confirm/analyze remains a case entry, meaning user fact verification, not final approval. B's sole final review still needs states/UI; review_required cannot automatically become approved.

<a id="94-联调顺序"></a>

### 9.4 Integration order

1. Preserve A paths, bodies, SSE, complete Case on its/common branch; adapt Mock without redesigning pages.
2. Check ordinary chat, facts, hits, no-match, display-only, failures through POST /messages; GET /cases/{id} checks recovery/citation snapshots.
3. Keep GET /knowledge/search for the panel, generating panel/chat passages from one evidence adapter.
4. Switch to actual C and repeat. Permissions, originals, versions, dates, and performance must pass before C integration is complete.

Read-only audit/recommendations for the specified commit; the local branch did not contain A code and this wiring was not implemented/run at that point.

<a id="10-首版代码落地2026-10-02"></a>

## 10. Initial implementation (2026-10-02)

This worktree implements `packages/agent/contracts.py`, `providers.py`, `knowledge.py`, including runtime fixtures. C HTTP is proposed, not actually accepted.
Machine-readable models: `docs/contracts/knowledge_provider_v0_1/`. Optional kind/locators support A search/rules; Evidence adds drift/heading/retrieved_at/coverage_cutoff/snapshot_sha256 to retain original page provenance.
Installation/configuration/rights/HTTP/tests: `docs/implementation/B_AGENT_LOCAL_RUN_AND_HANDOFF.md`.

<a id="2026-10-02-对话接入补充"></a>

## 2026-10-02 conversation integration supplement

B adds dynamic questions, candidate identification, and raw descriptions without expanding this C request/filter allowlist. User facts come from user descriptions/authorized materials, not public laws/cases. Independent inquiries omit old case dates. Case queries send applicable dates only with explicit actual/planned status; otherwise date_status=unknown.

Pure retrieval failure remains knowledge_unavailable. Mixed corrections may save facts then return workflow.status=partial_failure, reason_code=retrieval_failed, error_code=knowledge_unavailable, retryable. Case saves deferred_query; explicit retry restores only the query, not duplicate fact writes. Expose only error code/retryable, never raw exceptions/connections. No-match includes query/period/fact gaps, not a claim that legislation does not exist.

A's optional question/identification/dialogue fields: [implementation section 6](../implementation/B_GUIDED_INTAKE_DESIGN_2026_10_02.md#6-本轮落地接口与兼容方式).
