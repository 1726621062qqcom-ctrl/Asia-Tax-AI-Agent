<a id="真实链路首轮冒烟与下一轮判定"></a>

# Initial Live Workflow Smoke Tests and Next-Round Assessment

Date: 2026-10-12. Code baseline: `main` at `f7e9e69`. This round used only synthetic repository questions and the configured model/cloud knowledge database. Raw local results are Git-ignored: `reports/retrieval-main-2026-10-12.json`, `reports/chat-main-grounding-2026-10-12.json`, and `reports/chat-hybrid-legacy-2026-10-12.json`. No real client data or keys are included.

<a id="已实测"></a>

## Actual tests

| Stage | Result | Limits of the conclusion |
|---|---|---|
| Direct cloud retrieval | Existing 20 location questions: 20/20 expected matches; median 1.031 seconds, maximum 12.072 seconds, 7 questions over 3 seconds | Development regression questions do not establish independent recall or net improvement over the old strategy |
| Actual model + current default chat configuration | 6 of 8 synthetic questions returned messages; 2 returned `knowledge_unavailable`; none of the 7 questions requiring sources produced traceable answers | T05/T07 failed; T06 requested task clarification; T08–T11 returned empty sources; nonexistent Case 999999 was correctly not fabricated |
| Temporarily enable hybrid, retain legacy source adapter | Of 4 selected questions, T05/T07/T08 failed and T16 returned no match | Changing orchestration alone did not resolve source availability; this is not combined acceptance of C's source service |
| Pinned tax engine release installation | Again returned `release_hash_mismatch`; target directory was not installed | Hash checks retained; structure calculations and the full local actual C HTTP + tax engine workflow were not run |

Further checks using the installer's algorithm: the downloaded SQLite is 243703808 bytes and matches the pinned SHA-256. The 103 Python/CSV/JSON files at commit `771e452...` produce `d4c5495302fc9c755eb750d70fc181dc99f58e6905a79709e93845ea7b5d37e9`, while `main` pins `b1f2c38a996481f1d1099aae43f5cb2ed68e7e2abdb1a32863289306811dd921`. The mismatch therefore concerns the **code/source file set**, not SQLite. Whether the recorded hash is incorrect or acceptance used a different source snapshot is not yet established; do not simply change the hash to permit installation.

The current `.env` has model/cloud database settings but no `FSIE_AGENT_ORCHESTRATION`, `FSIE_AGENT_PROVIDER`, or `FSIE_AGENT_C_URL`. Actual chat therefore uses the default legacy adapter, while the direct retrieval script calls A's retrieval function. These are different paths. Adapter spot checks found `UNAVAILABLE` responses; requests with passages may still return `evidence_restricted` because legacy materials are display-only and cannot enter models. “Direct retrieval 20/20” cannot establish that chat answers found evidence. Evaluation scripts used temporary SQLite sessions, without HTTP sign-in, Supabase accounts, or a browser.

<a id="下一轮用两条线判断"></a>

## Two assessment tracks for the next round

**Compare old and current strategies on identical questions.** Pin the commit, knowledge snapshot, model, prompts, question order, and timeouts. Run the old A retrieval/answer path and the combined path with C enabled. Retain the existing 20 regression questions and add independent tax-lead-labeled questions not used for development/tuning, covering explicit identifiers, natural language, similar but inapplicable provisions, cases, cross-jurisdiction questions, and unsupported questions. Report availability, expected-source Recall@5, false retrievals, whether answers resolve questions, p50/p95 duration, and model calls separately. Historical 8/20 is background and cannot simply be subtracted from this round's 20/20.

**Trace outputs item by item.** For every critical tax claim record `claim → evidence_id → unit_id/locator → source_version_id/hash → original passage`; for structure calculations also trace `rule_id → parameters and validity periods → provisions/interpretations → input fact sources`. Automatically check citation existence, version/hash consistency, quotations in originals, and jurisdiction/date matching. The tax lead separately judges whether evidence supports conclusions and whether critical conditions were omitted. Unsourced tax claims cannot pass; correct statements of insufficient evidence are scored separately.

C branch `tax-engine-source`'s [`tax_graph/verify/grounding.py`](https://github.com/ZhihongWu-dev/Asia-Tax-AI-Agent/blob/tax-engine-source/tax_graph/verify/grounding.py) checks rules, parameters, quotations, validity periods, and fact sources. It can be reused for downstream structure-calculation traceability, but is not merged into `main` and does not directly check every chat-text claim. Connect chat `claim/evidence_id` to rule execution records before claiming end-to-end traceability.

Next, check the pinned commit against the accepted 103-file snapshot and resolve release validation; start the actual C source service and explicitly enable `combined`; then run both paths on identical questions. Suggested minimum release criteria: no fabricated citations in critical claims; every displayed quote is retrievable by version with matching hashes; case isolation passes with actual accounts and databases. Experts must assess tax interpretation correctness separately; the program cannot certify it itself.
