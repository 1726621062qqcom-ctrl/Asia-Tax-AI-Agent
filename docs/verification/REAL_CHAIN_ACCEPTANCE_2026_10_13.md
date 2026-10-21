<a id="真实链路验收旧新检索与依据追溯2026-10-13"></a>

# Live Workflow Acceptance: Old/New Retrieval and Evidence Traceability (2026-10-13)

<a id="判定方案"></a>

## Assessment plan

Assess retrieval, answering, and traceability separately. A pass at one layer cannot substitute for acceptance of the entire workflow.

| Layer | Actual entry point and passing criteria |
|---|---|
| Old/new retrieval on identical questions | Run the same 20 synthetic questions through old cloud PostgreSQL retrieval and new C HTTP statutory + cloud ruling retrieval. Check expected provision/case locations for 15 positives and explicit no-match results for 5 negatives; record individual/aggregate timings and source versions. |
| Chat answers | Actual DeepSeek, chat flow, and the same new retrieval configuration. Matched questions require checkable evidence extracts and IDs; unmatched questions must not fabricate conclusions. |
| Rules to original text | Retrieve pinned originals through each actual case report's `rule_id → citation → passage`; check text SHA-256, missing citations, frozen report hashes, user isolation, and state after fact corrections. |
| Tax correctness | Passes only after human experts label facts, periods, applicable provisions, and conclusions for each question. No expert gold standard exists in this round, so it is not marked passed. |

<a id="运行记录"></a>

## Run record

Used the current `main` working tree and pinned tax engine commit `771e4524961bcc36718db1c9331e7a5f4cda0ce7`. SQLite SHA-256 is `2756d2862330cb746d4103f0e690182fdc9fe7b2436a4ac738b156416aeca143`; the cross-platform manifest hash for 103 source files is `d4c5495302fc9c755eb750d70fc181dc99f58e6905a79709e93845ea7b5d37e9`. Old materials came from cloud PostgreSQL; the actual model was `deepseek-flash`. All questions, company facts, and amounts were synthetic. No keys were written to reports.

| Check | Result | Interpretation |
|---|---|---|
| Pinned release installation/hash checks | Passed | The expected source hash was stale and caused `release_hash_mismatch`; a cross-platform hash for the pinned commit now verifies installation. |
| Old/new retrieval, same 20 questions | Final rerun: old 20/20, new 20/20; both negative sets 5/5 | Old-path N04 failed temporarily earlier but passed targeted/final reruns. This establishes fixes for 9 known new-path misses, **not an overall recall improvement**. The source databases also differ. |
| 8 live chat questions | 7 evidence-bearing questions produced extract drafts with evidence IDs; 1 negative stopped at `no_match`; citation/hash checks 8/8 | Previously all 7 matched questions stopped at `evidence_restricted`. The fix permits only public Hong Kong official sources into models. Outputs remain extracts pending review, not complete tax advice. |
| PostgreSQL + C HTTP + pinned rules + actual model | Passed | Isolated PostgreSQL 17.6 random schema, actual local HTTP knowledge service, pinned rules, and DeepSeek all ran. Reports retain `evidence_gate=insufficient`; unknown facts block planning. |
| Rule traceability | All 6 rule entries have retrievable evidence; 21 statutory locations, 7 ruling passages; all 47 retrieved passage hashes correct | 0 missing rule evidence and 0 missing domain citations. Frozen report hashes and user isolation passed. Pinned rules still return `blocked` for unknown facts; the evidence gate remains `insufficient`. |
| Code/frontend build | Python 341 passed, 11 skipped; frontend build passed | The 11 skips are optional live integration tests that manipulate existing databases. This round validated cloud PostgreSQL through a combined script with random isolated schemas, without cleaning existing business tables. |
| Combined startup | Local `/health` returned 200 with `ok`; homepage returned 200 and loaded Taxora | Establishes startup/page serving only, not sign-in or manual browser acceptance. |

`DeepSeek` independently extracted 7 of 8 required fields from synthetic cases; `payer_jurisdiction` was missing/inaccurate. The combined script then explicitly supplied fixture facts. Successful later reporting cannot be described as independent model understanding of all fields.

Reproduction commands (require locally configured, ignored `.env`; actual model calls consume API usage):

```powershell
.venv\Scripts\python.exe -m scripts.evaluate_real_chain --output reports/strategy-comparison.json
.venv\Scripts\python.exe -m scripts.evaluate_combined_chat --output reports/chat-combined-grounding.json
.venv\Scripts\python.exe -m scripts.check_combined_live --env-file .env --output reports/combined-full-trace.json
.venv\Scripts\python.exe -m pytest -q
```

After building the frontend, start the accepted combined route locally with `.venv\Scripts\python.exe -m scripts.run_combined`. It starts/cleans up the local C knowledge service during the process lifetime, avoiding silent fallback to old retrieval when `.env` lacks `FSIE_AGENT_*`. Open `http://127.0.0.1:8000`. This remains a local service, not a public deployment.

Raw question-level results remain in Git-ignored `reports/` to avoid uploading model outputs/environment details. Reproducible scripts and credential-free assertions remain in code. Manual browser acceptance, end-to-end Supabase email, and real client data tests were not performed. Experts must supply question-level reference answers, and new questions independent of the development/tuning set must evaluate recall and tax correctness.
