<a id="合并编排工程验收与交接记录"></a>

# Combined Orchestration Engineering Acceptance and Handoff

Date: 2026-10-11. Baseline: `zijian-Luo / 1de0163`; pinned Li dependency `771e4524961bcc36718db1c9331e7a5f4cda0ce7`. See the [merged README](../../README_MERGED.md) for installation, framework, and takeover tests.

Later Windows revalidation found the source-set hash below incorrect. The current installer uses cross-platform hash `d4c5495302fc9c755eb750d70fc181dc99f58e6905a79709e93845ea7b5d37e9`. See [2026-10-13 acceptance](../verification/REAL_CHAIN_ACCEPTANCE_2026_10_13.md) for actual combined results.

Delivery includes shared facts, legacy ownership bindings, actual domain calls, fixed-structure/planning modes, question classification/writeback, read-only sources, combined routing, pages, combined research drafts/export/review, pinned installation, and retest scripts. Initial combined logic is complete and actual PostgreSQL + C HTTP + Li passed. Per the user's 2026-10-11 arrangement, actual model acceptance is deferred and does not block engineering handoff. Complete joint acceptance of all external dependencies is not claimed. Normal-account page tests, professional review, and later business scope remain separate.

<a id="固定发布核验"></a>

## Pinned release verification

| Item | Result |
|---|---|
| SQLite | 243703808 bytes; integrity `ok` |
| Database SHA-256 | `2756d2862330cb746d4103f0e690182fdc9fe7b2436a4ac738b156416aeca143` |
| Code/CSV SHA-256 (historical, now corrected) | `b1f2c38a996481f1d1099aae43f5cb2ed68e7e2abdb1a32863289306811dd921` |
| File set | 103 files: tax_graph Python/CSV/JSON, official/tools Python, official CSV at all levels, including `official/labels/observed_rules.csv` |
| Upstream handoff audit rerun | Passed; 396 documents, 8438 clauses, 390 parameters, 31 interpretation IDs; CSV/database consistent; 145 interpretation quotation checks passed; D14–D31 complete |
| Rule compilation | 184 rules; 0 missing parameters, 0 missing statutory references; 38 in-scope parameters remain unused by rules, which does not establish complete professional coverage |
| Upstream check_engine | 94 candidates, 0 defects, including bounds, post-payment requests, and scaling engineering checks |

The installer initially omitted `official/labels`; clean-directory testing exposed compilation failure, then labels were added and validation expanded to all official CSVs. The old hash covered 97 files; the corrected hash above governs the 103-file set. Pinned commit/SQLite are unchanged.

Li tax-item `cites` values are rule IDs. The adapter retains `rule_citations/citation_map` and converts compiled rule sources → parameter cite_id / explicit statutory references before asking the service for originals. Rule IDs are not treated as statutory IDs.

<a id="实测结果"></a>

## Actual results

| Check | Result/scope |
|---|---|
| Complete Python suite | 337 passed; 11 live PostgreSQL tests skipped under existing switches, not counted as passed |
| Frontend build | TypeScript/Vite passed |
| Browser | Original 27 passed; 2 structure tests, including new answer/partial-draft/export coverage, passed. Temporary SQLite, deterministic model double, actual Li engine |
| Actual C HTTP | Separate loopback uvicorn started; actual HTTP `/search`, `/evidence` → B → actual Li → frozen report → reread passed; service stopped afterward |
| Combined report example | Explicit direct CN→HK ownership; fixed OP/ULT; 21 FSIE locations; 24 evidence reads; all 19 domain statutory citations retrieved, 0 unretrieved; final `insufficient/unverified` retained |
| Two-round planner | Actual engine ran three times (initial + two answers); shared facts/results saved/restored. Unknown key amounts correctly produced blocked rather than fabricated computable plans |
| State regression | Old-case migration, bidirectional bindings, unknown/false, entity isolation, duplicate requests/different content, owner/revision, no commit on failure, deferral/pause, expired questions, professional permissions/revocation, confirmation/partial drafts/freezing/staleness |
| Actual model (deferred) | Historical attempt failed: Python initially lacked CA defaults; OS truststore retained TLS verification, then API returned HTTP 401 / invalid_api_key. No further calls/key requests currently; not counted as passed |
| Complete PostgreSQL follow-up | Passed with isolated project-local PostgreSQL 17.11 / pgvector 0.8.7; fresh migrations/rules/official-source build and 14 persistence checks passed; 2 actual model checks explicitly skipped. Test database deleted afterward |
| PostgreSQL combined workflow | Actual C HTTP → Li → PostgreSQL → frozen report → recovery/owner isolation passed; 21 statutory locations, 7 actual ruling passages, 0 unretrieved domain citations; three planner runs retained 16 candidates, correctly blocked on missing amounts |

Reports share one 45-second budget. Ordinary session limits remain; explicitly generated combined reports allow up to 35 original reads (FSIE 7, rulings 7, domain 21) and 10 search attempts (at most 5 requests, each with one retry), sharing a read cache. Missing/over-budget citations remain gaps. Expanded limits apply only to full reports without resetting subflow budgets.

The early SQLite HTTP example used an explicitly empty ruling reader. PostgreSQL follow-up used actual official knowledge: 10 in-scope materials produced 697 units, including 7 per ruling; the remaining one of 11 sources is explicitly out of scope. Eight web snapshots differ from manifest hashes and retain drift flags. Reports remain `insufficient/unverified`. See sanitized [PostgreSQL results](COMBINED_POSTGRES_RESULT_2026_10_11.json). Local database testing is not cloud deployment acceptance.

Follow-up fixed two contract gaps: Alembic comparison omitted ChatStore's independent metadata, and Source ORM omitted the existing jurisdiction index declaration. Migration tests now check both complete schemas, verifying `downgrade base` preserves chat cases/RLS and `upgrade head` preserves data with zero metadata differences. Chat tables were not deleted to pass tests.

<a id="接手后的补测与暂缓事项"></a>

## Follow-up tests and deferred items

1. **Actual model deferred**: no key update or model API call currently required. When resumed, configure a valid key locally and test actual model/database jointly. Retain historical 401 records.
2. **Database retesting complete**: a dedicated migrated/populated local database remains, with connection in ignored `.env.integration`. Other machines can reproduce through `check_postgres_acceptance.py`. The **environment owner** separately supplies normal Supabase email configuration; team members test pages with test accounts.
3. **Running team member** currently uses `python scripts/check_combined_live.py --database-only --env-file .env.integration`, saving sanitized results and checking existing structure/multi-turn planning, refresh/owner isolation, combined reports, and actual rulings. Full model commands wait until acceptance resumes.
4. **Li/tax lead** review D14–D31, parameter units, rule validity, unresolved bound conditions, and special arrangements. Original locations/hashes cannot replace professional review.

<a id="已明确保留的范围限制"></a>

## Explicit limitations

- Initially CNY only; other currencies explicitly do not calculate. Fields such as group EUR revenue retain specified units regardless of CNY transaction currency.
- Bind old facts only after human confirmation of entity ownership; legal judgments do not automatically become Li discretion. Existing graphs without `present` block.
- Li originals are display-only; ordinary users cannot answer ruling/library directly. Professional answers retrieve evidence and record hashes, but humans still check relevance/applicability.
- Final approval gates remain. Li `unverified` materials/synthetic cases cannot be directly approved as formal advice. Expert UI may record returns or inability to conclude.
- `review_paid`, non-holding templates, complex combinations, vectors, Li document extraction, currency conversion, cross-account expert assignment, and public deployment require dedicated acceptance.
- Not all upstream battery tests, full-text builds, or vector models were rerun; completed checks are handoff/rules/check_engine and the described combined workflow.

<a id="可复现入口"></a>

## Reproduction

```sh
python scripts/install_li_release.py
python -m pytest -q
npm --prefix apps/web run build
python scripts/check_combined_local.py
# No model call; creates, validates, and cleans up a disposable PostgreSQL database
python scripts/check_postgres_acceptance.py --env-file .env.integration --system-trust
# Dedicated populated database: test database and actual HTTP/Li combined workflow only
python scripts/check_combined_live.py --database-only --env-file .env.integration
# Model commands below are deferred; require a valid model, dedicated PostgreSQL, and original ruling materials when resumed
python scripts/check_combined_live.py --env-file .env
# Actual model only; explicitly not PostgreSQL acceptance
python scripts/check_combined_live.py --model-only --system-trust --env-file .env
# Separate database/model configurations
python scripts/check_combined_live.py --env-file .env.integration --model-env-file ../Asia-Tax-AI-Agent/.env --system-trust
```

Distinguish actual dependencies, model doubles, and synthetic data on every retest. Test counts alone cannot establish external joint acceptance or professional tax acceptance.
