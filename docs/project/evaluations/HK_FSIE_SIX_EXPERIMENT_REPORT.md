<a id="香港股息双输入方式六次实验记录"></a>

# Hong Kong Dividend Consultations: Six Input-Method Experiments

[Companion English report](HK_FSIE_SIX_EXPERIMENT_REPORT.en.md)

Run date: 14 October 2026 (China Standard Time). All cases are fictional and come from the [Chinese case templates](../../product/HK_FSIE_USER_CASE_TEMPLATES.md); see the [English case templates](../../product/HK_FSIE_USER_CASE_TEMPLATES.en.md) for a translation. This report records software and product behavior. **It is not a professional tax validation.**

<a id="我们怎样判断回答好坏"></a>

## How we judge an answer

Each run is assessed against five criteria. A response is not good merely because it exists or because a model rates itself highly:

1. **Availability:** The request completes and returns a readable result. Failures, timeouts, and retries are recorded separately.
2. **Fact fidelity:** Stated amounts, parties, and transaction stage are preserved. A month without a day must not become the first day of that month; hearsay must not become verified evidence.
3. **Transaction boundaries:** Identify who pays the Hong Kong company directly. Keep planned and completed events apart, do not merge separate dividends, and do not attach a lower-tier company's ownership percentage to the proposed direct payer relationship.
4. **Traceable support:** Citation IDs must belong to material actually retrieved for the current run. Period, scope, and missing coverage still need checking. **A citation's existence does not show that it supports every inference.**
5. **User usefulness:** Address the actual question and prioritize missing facts, documents, and next steps. A long list of legal excerpts without case-specific explanation is at best partial.

An invented material fact, confused transaction party, or unsupported definitive tax conclusion prevents an **engineering pass**. Even a run passing all five engineering checks would still require a Hong Kong tax expert to review legal interpretation, effective versions, evidence, and conclusions before claiming professional correctness. The [IRD FSIE overview](https://www.ird.gov.hk/eng/tax/bus_fsie.htm) and [official illustrative examples](https://www.ird.gov.hk/eng/tax/fsie_example.htm) are official starting points for that review.

<a id="运行方式与范围"></a>

## Method and limits

- Model: the locally configured `deepseek-flash`; knowledge: the project's configured cloud collection of Hong Kong official materials. All six runs used **fictional facts** and isolated temporary SQLite case sessions. No personal user conversation was written.
- Three long-question runs used the existing `ChatService` with the real model, retrieval, and response path. Three form runs saved the same stated facts field by field and used the existing confirmation and analysis path. Where facts were missing, the run explicitly requested a partial research draft before analysis. **These were not clicks through a new template picker or browser UI tests.**
- Local raw JSON (`reports/fsie-user-six-experiments.json`, generated locally) is ignored by Git under `reports/`; regenerate it on another machine using the [evaluation script](../../../scripts/evaluate_fsie_user_cases.py).
- Completion only means a response returned in this run. These three synthetic cases have no expert-approved tax gold labels and cannot establish overall accuracy or retrieval recall.

<a id="六次实际结果"></a>

## Actual outcomes of the six planned runs

| No. | Case and input | Observed outcome | Assessment |
| --- | --- | --- | --- |
| 1 | Singapore dividend, long question | Returned in 19.90 seconds with 7 retrieved passages and 7 matching displayed citations. Extracted 35% ownership, an occurred event, and the Hong Kong bank route. However, it turned “March 2022” into `2022-03-01` and “August 2025” into `2025-08-01`, although the user gave no days. The reply mainly listed legal excerpts and did not prioritize the requested documents. | **Fail: invented dates.** Citations are traceable; usefulness is only partial. |
| 2 | Singapore dividend, guided facts | Saved and confirmed facts, explicitly authorized a partial draft, and analyzed them in 4.77 seconds. The first analysis attempt correctly returned `partial_confirmation_required`; after authorization, the run retrieved 21 statute passages and produced 6 nodes. Terminal state: `research_only_output`; evidence gate: `insufficient`; professional status: `unverified`. Exact accrual and receipt dates remain gaps. | **Partial engineering pass:** unknowns and sources preserved; no professional conclusion or complete natural-language answer. |
| 3 | Mainland China dividend, long question | Returned `model_failed` after 11.10 seconds, with no final answer or saved facts. A targeted retest returned the same error after 11.62 seconds. The current record does not distinguish a model-service failure from response parsing or another internal stage. | **Fail: no answer on two attempts.** |
| 4 | Mainland China dividend, guided facts | Saved and confirmed facts and completed partial analysis in 2.85 seconds. The first run was correctly blocked by missing-fact requirements; after explicit authorization, it returned 21 statute passages and 6 nodes with `research_only_output` / `insufficient` / `unverified`. It retained the 8% interest and “Mainland tax document obtained but not reviewed”; the holding route, exact dates, and Hong Kong business status remain gaps. | **Partial engineering pass:** missing facts were not silently treated as favorable. |
| 5 | Japanese project, long question | Returned in 13.67 seconds, retrieved 7 passages, and displayed 3 traceable citations. The model preserved “planned” but mapped the Singapore company's **22%** in the Japanese company to the Hong Kong company's `holding_percentage_pct=22` and “indirect” holding, omitting the Hong Kong company's **100%** in its proposed direct payer, the Singapore company. It also placed alternative future fund routes in the generic account-path fact. The reply mostly listed source excerpts and did not clearly separate the two dividends. | **Fail: confused transaction relationship.** Planned status was retained and citations were traceable. |
| 6 | Japanese project, guided facts | Saved and confirmed facts and completed an explicitly authorized partial analysis in 2.46 seconds. The proposed direct payer to the Hong Kong company is recorded as the Singapore holding company, with the Hong Kong company's 100% interest. Japan → Singapore and the 22% lower-tier interest remain separate background facts. No amount, date, or actual receipt path was invented. The result remains `research_only_output` / `insufficient` / `unverified`, with 21 statute passages and 6 nodes. | **Partial engineering pass:** transaction boundaries and planned status preserved; no definitive opinion on an event that has not occurred. |

Each form analysis included five professional review tasks: financial-entity exclusion, foreign-tax switch-over, anti-hybrid arrangements, main purpose, and filing. `missing_locators` was empty for all three form runs, meaning **the statute locations requested in this run were found**. That does not establish complete source coverage or professionally correct application. The form facts were manually mapped by the evaluation script from the case document; browser form entry has not been accepted.

<a id="对比结论与优先修复点"></a>

## Comparison and priorities

- **Input mode changed the outcome materially.** The long-question route invented dates in Case 1, failed in Case 2, and confused 22% with 100% in Case 3. The guided-fact route preserved those distinctions. The two modes cannot currently be presented as equivalent.
- **First priority: protect facts.** Month-only inputs must not be normalized to the first day. Multi-tier holdings need explicit holder → investee relations, and dividends need payer → recipient relations. A proposed fund route must not become an actual route.
- **Second priority: diagnose failures and improve responses.** Add stage-level diagnostics for `model_failed` without recording secrets, plus a user-facing retry path. When retrieval succeeds, answer the case question first, then show selected authorities and gaps instead of dumping legal text.
- **Third priority: accept the guided-template UI.** These six runs compare service paths; the three case cards, progressive field interactions, bilingual copy, save/resume, and browser behavior remain unimplemented or untested.

<a id="复跑"></a>

## Reproduction

With the existing model and cloud knowledge configured, run from the repository root:

```powershell
.venv/Scripts/python.exe scripts/evaluate_fsie_user_cases.py --output reports/fsie-user-six-experiments.json
```

This command incurs model API usage. Model behavior can vary, so this report describes **this run**, not an immutable benchmark. The original and repeat failures for Case 2 remain in the local JSON. The script uses the configured model key for requests but does not write it to its output, read real client data, or write cases to the shared cloud case table.
