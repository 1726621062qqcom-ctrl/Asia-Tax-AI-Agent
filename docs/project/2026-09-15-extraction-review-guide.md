<a id="case-74--75-事实提取复核草稿"></a>

# Case 74 / 75 Fact Extraction Review Draft

Status: awaiting user/team review; not a frozen evaluation answer. Baseline: branch agent/fsie-ruling-sources,
281c2f8618f2ba9ddf0dccb98631f950f1b44f67 (43 fact fields and intake/extraction.py).
This round checked data representation and fact annotation only; it changed no fields, ran no model, and established no accuracy score.

<a id="你现在需要打开什么"></a>

## What to open

1. This document and [PR #3](https://github.com/ZhihongWu-dev/Asia-Tax-AI-Agent/pull/3).
2. [Official Case 74](https://www.ird.gov.hk/eng/ppr/advance74.htm).
3. [Official Case 75](https://www.ird.gov.hk/eng/ppr/advance75.htm).

Use a side-by-side view. Read section 2 Background and section 3 The arrangement in each original,
then check every row below. Section 4's ruling is not model fact input. Check sections 5 and 7 only for source periods/dates.
No download, terminal, database, or model key is required.
The text reflects the previously captured, manually checked versions. Flag current-page differences rather than reusing answers unchanged.

<a id="case-74逐项复核"></a>

## Case 74: itemized review

| ID | Fact/expected treatment to confirm | Original location | Check |
|---|---|---|---|
| 74-1 | Applicant is incorporated in Hong Kong and primarily conducts investment holding | 2(a) | Incorporation does not automatically establish every legal status |
| 74-2 | Applicant owns 60% of Company F | 2(b) | Do not reverse entities or ownership direction |
| 74-3 | Ownership began in 1992; month/day undisclosed | 2(b) | Do not invent 1992-01-01 or calculate exact holding months from today's date |
| 74-4 | Jurisdiction F corporate income tax rate is 25% | 2(c) | Identify the tax and jurisdiction; this is not withholding tax |
| 74-5 | Jurisdiction F dividend withholding rate for nonresident companies is 10% | 2(c) | Record separately from 25% |
| 74-6 | Company F plans to distribute part of its post-corporate-tax profits to Applicant; Applicant will bear 10% withholding tax | 3(a) | Planned events are not taxes already paid or income already received |
| 74-7 | Specific amount, currency, and complete dividend date are undisclosed | 2–3 | Retain unknowns; do not infer from the ruling date |
| 74-8 | Ruling date 2023-11-07; years of assessment 2023/24–2027/28 | 5, 7 | Source metadata only, not transaction dates |

Do not copy section 4 conclusions such as “participation exemption satisfied” or “qualifying similar tax” into fact inputs.

<a id="case-75逐项复核"></a>

## Case 75: itemized review

| ID | Fact/expected treatment to confirm | Original location | Check |
|---|---|---|---|
| 75-1 | Company P is Applicant's direct parent; S1 is Applicant's wholly owned subsidiary | 2(a)–(b) | P, Applicant, and S1 are separate entities |
| 75-2 | S1 owned 100% of S2 before restructuring | 2(b) | Pre-restructuring status is not automatically post-restructuring status |
| 75-3 | S2 was incorporated in Jurisdiction A and had redomiciled to B and operated there at the relevant time | 2(c) | Retain initial incorporation and post-redomiciliation location separately |
| 75-4 | S2 has no establishment, business, or assets in Hong Kong | 2(c) | Do not apply this description to other entities |
| 75-5 | S1 distributes its S2 shares at fair value to Applicant as a dividend in kind | 3(a) | Payer S1, recipient Applicant, underlying asset S2 shares |
| 75-6 | Applicant distributes those shares on the same day to sole shareholder P as a dividend in kind | 3(b) | Second transaction Applicant → P; still S2 shares |
| 75-7 | Occurs on an unspecified day in 2024 | 3(a) | Do not substitute the ruling date; retain the same-day relationship |
| 75-8 | Dividend is a share distribution; amount, specific fair value, and bank account are undisclosed | 2–3 | Do not invent a cash remittance; an unmentioned account is not proof that no account exists |
| 75-9 | Ruling date 2024-09-30; year of assessment 2024/25 | 5, 7 | Not the business event date |

“Not regarded as received in Hong Kong” is a section 4 ruling, not a direct answer for extraction from sections 2–3.

<a id="已检查的字段与接口缺口"></a>

## Checked field/interface gaps

| Topic | Current capability | Recommendation, not implemented |
|---|---|---|
| Ownership percentage/investee | holding_percentage_pct, investee_entity | Retain fields; annotate entity ownership and evidence |
| Two tax rates | foreign_nominal_tax_rate_pct, foreign_tax_jurisdiction; no separate withholding rate | Clarify corporate-rate semantics; add withholding rate and subject associations without duplicate synonyms |
| Year precision | acquisition_date and receipt_date are date fields | Support year-only precision without invented month/day |
| Dividends in kind | income_type includes income classes such as dividend | Add distribution form separately from income class |
| Two-step share distribution | payer_entity and bank_or_account_path cannot structure multistep noncash transfers | Ordered events recording payer, recipient, underlying shares, and timing relationships |
| Original evidence | ExtractionResult returns facts/metadata, without evidence per fact | Add passage locations/evidence spans; compare values and ownership, not just numbers |
| Unknown numbers | validate_candidates skips null and rejects string unknown in numeric fields | Standardize undisclosed values and test them; do not copy candidate-case unknown directly into current intake |

Checked packages/contracts/fact_dictionary/hk_fsie_fact_fields.v0.json and
packages/intake/extraction.py. Findings come from code reading, not model runs.

<a id="怎么反馈"></a>

## Feedback

Respond directly in chat or in PR #3 comments, for example:

> Case 74: items 74-1 through 74-8 confirmed.
> Case 75: issue with 75-5; original section 3(a) means …; other items confirmed.
> Unable to confirm: …

Mark each item confirmed / revise / uncertain. No exemption judgment or code change is required.
Other reviewers should annotate independently from originals before comparing this table. One shared table after discussion is not two independent annotations.

<a id="复核后如何验证模型"></a>

## Model validation after review

Engineering implements fields/evidence structures, prepares approximately 12 synthetic variants, freezes expected answers, and runs the model.
Cover substituted/swapped rates, missing critical facts, renamed entities, changed narrative order, and reversed transaction directions.
Record model/prompt versions and report correctness of values, subjects, time precision, evidence, and fabrication counts separately.
Public originals remain synthetic=false; the synthetic-only model policy is unchanged.
This review does not authorize sending public originals to models; original ruling conclusions are not tax gold standards for synthetic variants.
