<a id="taxora-前端下一步检查"></a>

# Taxora Frontend: Next Checks

<a id="2026-09-29-完成更新"></a>

## Completion update, 2026-09-29

Six items are implemented: expired-link recovery, verification email resend, Markdown/copying, reading-aware scrolling/return to bottom, rename/time grouping/archive/restore, and actual model streaming/stopping. The original checklist below is retained as a historical issue record, not a statement that these items remain unfinished.

History archiving uses existing JSON document fields without cloud table migration. Archiving preserves content and supports restoration from Archived. Rename/archive respect account isolation, version conflicts, and idempotency.

Stop terminates the streaming HTTP request and closes the upstream model connection. Partial replies/candidate facts are not persisted; the original question is restored unless a new draft exists. If a full reply committed before stopping, reload and retain the server result. Formal rule analysis still follows complete confirmation and is not presented as model token output. A retrieval thread already started may finish after cancellation but cannot commit canceled results. In the brief race after database commit begins, cloud results are authoritative.

Validation: 126 offline Python tests passed; 11 cloud integration tests were not run; 19 browser tests passed; an actual synthetic DeepSeek greeting produced 17 increments and passed structural validation. Browser tests use independent data and controlled model doubles without reading real conversations. The user configured Gmail SMTP/templates and reported successful actual delivery.

Review method: read frontend, API, and test code. Browser connection failed, so this review did not operate actual pages or mobile devices. The list distinguishes code gaps from unverified items. No existing frontend behavior was changed.

<a id="已有基础"></a>

## Existing foundation

Email registration, sign-in, password recovery, verification callbacks, sign-out; Chinese/English switching; immediate sent-message display/thinking animation; retries; history/search; collapsible legal sources/versions; case fact editing/analysis; mobile drawers, focus constraints, and reduced motion.

These have implementations and existing automated tests, not complete acceptance of actual email, mobile devices, or cross-device cloud workflows.

<a id="建议顺序"></a>

## Suggested order

| Order | Work | Current evidence and acceptance | Collaborators |
| --- | --- | --- | --- |
| 1 | Restore sign-in after expired verification links | auth.tsx stops requesting session after callback errors, leaving configured false and AuthPage disabled. Retain link errors while allowing sign-in/new requests; add regression. | A leads |
| 2 | Add verification email resend | AuthPage only says to verify, with no resend; api/auth.py has no resend endpoint. Add entry point, rate limits, and generic feedback without disclosing account existence. | A + backend |
| 3 | Add basic chat operations | Conversation uses p only, without copying/Markdown. Add copy, lists/tables/headings, prohibit unsafe HTML, then consider regeneration. | A; regeneration needs backend |
| 4 | Improve waiting/interruption | api.ts waits for complete JSON with a common 65-second timeout, no streaming/active-stop API. Show actual processing state first, then streaming/cancellation with explicit persistence semantics; stopping animation alone is insufficient. | A + B |
| 5 | Add conversation management | Sidebar supports title search/select/create only; no rename, archive/delete, or time groups. useWorkspace drafts are memory-only. Add titles/groups, then safe delete/archive and account-isolated draft recovery. | A + backend |
| 6 | Improve long-answer reading | Conversation forces scrollIntoView on message-count/busy changes without checking old-message reading. Add return-to-bottom; auto-follow only near the bottom. | A |
| 7 | Organize tax results | Existing sources, facts, and review lists need no rebuild. Show current assessment, missing items, and next steps first, with expandable originals/versions. Pending review is not confirmation. Passages' unverified label is fixed text and later needs actual review status. | A + B/C |
| 8 | Add account/data explanations | Only email/sign-out exist, without account settings or a separate privacy explanation. Explain storage, deletion, and model input use. Password changes/data deletion need real backend support. | A + backend |
| 9 | Accept mobile/exception behavior | Existing responsive layouts/tests still need actual soft keyboards, narrow tables, long quotes, offline/expired sessions, multi-tab sign-out, and cross-device history recovery. Do not rebuild existing responsive features as missing. | A |

<a id="最先完成的一小批"></a>

## First small batch

1. Fix expired-link recovery and integrate resend.
2. Add copying, basic formatting, and noninterrupting scrolling.
3. Add rename/time groups; define delete/archive APIs before implementation.
4. Validate these flows in Chinese/English, mobile, and network failures.

Streaming and actual stop are the next batch for A and B. Upload, report export, and expert review UI should follow defined data/business APIs; do not add nonfunctional buttons.

<a id="本轮邮件状态"></a>

## Email status in this round

Chinese/English branded registration verification and password reset HTML is saved in infrastructure/supabase/email-templates. It is not published to Supabase, and the default sender is unchanged. Save after dashboard connection recovery and verify actual delivery.
