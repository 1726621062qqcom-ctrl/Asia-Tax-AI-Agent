# Demo cases and user guide

Updated 2026-10-20 (evening) for the conversation-based front end. The three cases are fictional demonstration material, each run for real on that date.

## 1. What is covered: jurisdictions, entities and transactions

The system currently covers **companies in Mainland China, Hong Kong and Singapore**: several companies, several layers of ownership and several actual payments in one case.

Since 2026-10-20 the system handles **income tax only**. A case is accepted only when none of its transactions attracts VAT, GST, stamp duty, customs duty or a property tax in the jurisdictions it touches (the payer's, the payee's, the target company's for a share sale). The read-back of a description lists such a payment under "Left out"; the form shows, under `Transaction type`, where each type is handled, and a case with such a payment cannot be created.

| Transaction | Front-end `Transaction type` option | Handled |
|---|---|---|
| Dividend distribution | `Dividend` | Everywhere (the planner's capitalisation option is not offered: it attracts stamp duty in the Mainland) |
| Capital reduction | `Capital reduction` | Everywhere |
| Liquidation distribution | `Liquidation distribution` | Everywhere |
| Interest | `Interest` | Only when no party is in Mainland China (VAT on loan services there) |
| Service fee, Royalty, IP ownership transfer, Goods sale, Share disposal, Property sale, Property rent | not offered | Paused: these kinds attract VAT, GST, stamp duty or property taxes |

The rules for the other taxes remain in the library and can be switched back on in one place (`tax_graph/scope.py`); they are not maintained for now.

Not covered yet: individuals' tax and jurisdictions other than the three (being added to the library, see official/EXTENSION_GUIDE.md), partnerships and trusts, and automatic planning of arbitrary legal forms. The default structure form does not accept circular ownership. Uploading material does not extend these legal or structural limits.

## 2. How to start a case

| Entry | What it does | Limits to keep in mind |
|---|---|---|
| The conversation at `http://127.0.0.1:8765/` (`+ New conversation`) | Describe the companies, who holds whom and each payment in your own words, `Read my case`; the structure is read back with the sentence each value came from; `Looks right - create the conversation` creates it. Attach documents in the drop zone, then `Start the analysis`. | What the description does not state is asked for; a payment kind outside the scope is left out and said so. |
| `Edit in the form` (from the read-back; `#/new` directly) | Enter or correct companies, ownership links and payments in fields. | Same scope; no structure is inferred. |
| `Use a planning scenario` (`#/new-guided`) | A template that compares structural alternatives: profit repatriation, holding structure and dividends, external financing. | Only the three scenarios are offered. |

The result is a list of candidate strategies (section 4), not a single plan. Every conversation stays in the left rail (`x` deletes it with its analysis).

## 3. Conventions for all three cases

- Open <http://127.0.0.1:8765/>. Each case is one conversation; create each separately.
- Paste the description given for the case into the box on the home page and click `Read my case`. Check the read-back (every value shows the sentence it came from), then `Looks right - create the conversation`. If something was not read, `Edit in the form`.
- Create a UTF-8 `.txt` file with the text given under "Material", attach it with the drop zone, then `Start the analysis`. The analysis reads the file, checks the company registers and applies the rules; the page updates itself.
- "What the documents say" lists values found in the material; confirm, correct or reject each. In these three cases the material repeats the description, so the list is short or empty: confirm and continue.
- "A few questions" asks only what the rules need. Answer with the values given below and name the source; where the table says *I don't know*, tick that. For ruling questions choose `Not confirmed` unless you hold the ruling, and give the basis — every `Not confirmed` ruling forks the strategies.
- The three descriptions and materials are invented. A register check that does not find a fictional company does not mean anything was verified.
- The runs below were made on 2026-10-20 with qwen3.8-flash; the questions and their order can differ slightly between runs, the amounts do not.

## 4. Where to find the strategies and the plan

Once the questions are answered, the conversation shows **candidate strategies**, lowest guaranteed tax first. A strategy exists for every combination of the rulings you answered `Not confirmed` taken as favourable; the last card (baseline) takes every open ruling against you. Answering a ruling `Yes` or `No` (with its basis) removes it from the forks and is recorded as your declaration.

Each strategy opens in its own window (`Open`):

1. **Its numbers**: guaranteed tax, the tax if every open item turns out favourable, and the strategy to fall back on if one of its rulings fails (answer that ruling `No` and reassess).
2. **Start here**: the step to do first; a modelled date that has already passed is checked before anything else.
3. **The steps by phase**: establish the facts behind each payment; settle the treatments that move the tax; file, pay and reconcile; record and close. Each step says why it exists, who owns it, the documents, the completion test and its rule references; tick a step when it is done (kept in your browser).
4. **The Assistant** for that strategy only: what a step means, which provision applies, what to prepare, which form to file (it fills official forms from the case where it can), what to do if a ruling fails. It looks things up in the law library and on the web and cites what it found. **AI assistance can be wrong** — verify against the sources it cites. It cannot change amounts, answer rulings or switch strategies.
5. `Download this strategy` (its own report) and `Print / Save PDF`; the report over all strategies is on the `Full case page` linked from the conversation.

---

# Demo case 1: a Singapore company lends to its Hong Kong parent

## The case and what it practises

Marlow Capital (Singapore) lent SGD 5,000,000 to its parent Marlow Holdings (Hong Kong). On 31 December 2026 the parent pays SGD 250,000 interest. No tax has been paid on it.

This case practises: **interest between Hong Kong and Singapore (no Mainland party, so income tax only), reading a loan agreement, and seeing why some rulings do not fork the strategies until the facts behind them are known.**

```text
Ownership: Marlow Holdings Limited (HK) ──100%──→ Marlow Capital Pte. Ltd. (SG), since 2 May 2020
Payment:   Marlow Holdings Limited (HK) ── interest SGD 250,000 on 31 Dec 2026 ──→ Marlow Capital Pte. Ltd. (SG)
```

## Step 1: describe the case

Paste into the home page:

```text
Marlow Capital Pte. Ltd. is incorporated in Singapore. It is wholly owned by Marlow Holdings Limited, a Hong Kong company, since 2 May 2020. In 2025 Marlow Capital lent SGD 5,000,000 to Marlow Holdings at 5% a year under a written loan agreement dated 1 January 2025. On 31 December 2026 Marlow Holdings pays SGD 250,000 interest to Marlow Capital. No tax has been paid on the interest. We have the loan agreement, the board resolutions of both companies and the audited accounts for 2025. Please assess as at 20 October 2026; all amounts in SGD.
```

The read-back shows two companies (Singapore, Hong Kong), one ownership link (100% since 2020-05-02) and one payment (interest, SGD 250,000, 2026-12-31), each with its sentence, and nothing missing. Name the conversation `Demo 1 - Singapore loan to Hong Kong` and create it.

## Step 2: attach the material and start the analysis

File `demo01_loan.txt`:

```text
LOAN AGREEMENT dated 1 January 2025 between Marlow Capital Pte. Ltd. (Singapore, the Lender) and Marlow Holdings Limited (Hong Kong, the Borrower). Principal: SGD 5,000,000. Interest: 5% per annum, payable annually in arrears on 31 December. The loan is unsecured and is used by the Borrower to fund its working capital in Hong Kong. The Borrower shall pay interest gross; any withholding tax, if applicable, shall be borne by the Lender. Interest for 2026: SGD 250,000, paid on 31 December 2026 to the Lender's bank account in Singapore.
```

Click `Start the analysis`. The documents add no value beyond the description, so "What the documents say" is empty: confirm and continue.

## Step 3: answer the questions

Round 1 (one question):

| Question | Answer | Source |
|---|---|---|
| Group consolidated revenue in EUR (Pillar Two threshold) | `20000000` | Marlow Holdings consolidated accounts 2025 |

Round 2 (seven questions, grouped by jurisdiction):

| Question | Answer | Source / basis |
|---|---|---|
| Marlow Holdings: annual taxable income outside this payment | *I don't know* | — |
| Ruling: the interest is incurred in the production of Marlow Holdings' profits (Hong Kong deduction) | `Not confirmed` | No determination by the IRD; the loan funds the Hong Kong business |
| Marlow Capital: Singapore foreign tax credit pooling election | *I don't know* | — |
| Source jurisdiction's statutory rate on this payment | *I don't know* | — |
| Has the interest been taxed abroad | `No` | No Hong Kong tax was withheld (loan agreement; bank advice) |
| How the foreign income is received | `Remitted into the jurisdiction` | Loan agreement: paid to the Lender's bank account in Singapore |
| Ruling: the interest is sourced in Singapore | `Not confirmed` | The interest is paid by a Hong Kong borrower; no ruling on source has been sought |

## Step 4: read the strategies

One strategy only, guaranteed **SGD 42,500** (Singapore income tax on the interest, 17%), best case SGD 1,250. Two rulings were left `Not confirmed`, yet no fork appears: the Hong Kong deduction (worth up to SGD 41,250) cannot count while Marlow Holdings' other taxable income is unknown, so taking the ruling as favourable changes nothing on its own. To see that strategy, reopen the questions (`Edit the facts` → run again) and give the other taxable income.

Open the strategy: six steps — prepare the financing and interest file; obtain the facts answered Unknown; resolve the outstanding tax treatment; confirm the Hong Kong position; settle the Singapore tax of SGD 42,500; approve and keep the audit trail. Ask the Assistant, for example: *"Which Singapore provision taxes this interest, and is there anything to file in Hong Kong?"* — it cites the clauses it retrieves and says what it has not checked.

---

# Demo case 2: two-layer dividends, Mainland — Hong Kong — Singapore

## The case and what it practises

Shanghai Anxin (Mainland China) pays a dividend of CNY 2,000,000 to its Hong Kong holding company Best China, which passes it on to the Singapore parent EKH. Mainland withholding tax of CNY 100,000 was paid on the first dividend. The group also charged a management fee, which is outside the scope and is left out.

This case practises: **a dividend chain across all three jurisdictions, tax already paid, a payment kind outside the scope being refused, and three rulings that fork the plan into four strategies.**

```text
Ownership: EKH Limited (SG) ──100%──→ Best China Development Limited (HK) ──100%──→ Shanghai Anxin Rong Cheng Container Logistics Co., Ltd. (CN), since 12 Mar 2019
Payments:  Shanghai Anxin ── dividend CNY 2,000,000 on 30 Jun 2026 ──→ Best China   (Mainland withholding tax paid: CNY 100,000)
           Best China ── dividend CNY 2,000,000 on 15 Jul 2026 ──→ EKH
```

## Step 1: describe the case

```text
Shanghai Anxin Rong Cheng Container Logistics Co., Ltd. is incorporated in Shanghai, Mainland China. It is wholly owned by Best China Development Limited, a Hong Kong company, since 12 March 2019. Best China is 100% held by EKH Limited, which is incorporated in Singapore. On 30 June 2026 Shanghai Anxin declared and paid a dividend of CNY 2,000,000 to Best China; Best China paid a dividend of CNY 2,000,000 on to EKH on 15 July 2026. Mainland withholding tax of CNY 100,000 was paid on the first dividend. EKH also charged Shanghai Anxin a management fee of CNY 300,000 in 2026. We have the board resolutions, the dividend vouchers and the 2025 audited accounts of each company. Please assess as at 20 October 2026, all amounts in CNY.
```

The read-back shows three companies, two ownership links, two dividends with the tax paid on the first, and under "Left out (1)" the management fee: *not a kind this program handles*. Name it `EKH dividend chain` and create it.

## Step 2: attach the material and start the analysis

Save the description itself as `demo02_description.txt` and attach it (in practice: the board resolutions, the dividend vouchers, the audited accounts). Start the analysis; two values are read from the file and shown under "What the documents say": confirm and continue.

## Step 3: answer the questions

Round 1: group consolidated revenue in EUR — `50000000` (EKH consolidated accounts 2025).

Round 2 (14 questions):

| Question | Answer | Source / basis |
|---|---|---|
| Best China: pure equity-holding entity | `Yes` | Best China audited accounts 2025: only the shareholding |
| Best China: substance ruled adequate by the IRD | *I don't know* | — |
| Ruling: Best China has adequate economic substance in Hong Kong | `Not confirmed` | No advance ruling applied for; one director and a secretarial address |
| Ruling: obtaining a tax benefit is not a main purpose (treaty rate) | `Not confirmed` | No ruling; the holding was set up in 2019 for the listing |
| Dividend 1: deductible at the payer | `No` | Dividend out of after-tax profit |
| Dividend 1: source jurisdiction's statutory rate | `25` | Enterprise Income Tax Law article 4 |
| Dividend 1: taxed abroad | `Yes` | Mainland withholding certificate |
| Dividend 1: how received | `Remitted into the jurisdiction` | Bank statements of the recipient |
| Dividend 1: underlying profits taxed | `Yes` | Shanghai Anxin enterprise income tax return 2025 |
| EKH: Singapore FTC pooling election | `No` | EKH income tax return |
| Dividend 2: source jurisdiction's statutory rate | `25` | Enterprise Income Tax Law article 4 |
| Dividend 2: taxed abroad | `Yes` | Mainland withholding certificate |
| Dividend 2: how received | `Remitted into the jurisdiction` | Bank statements |
| Ruling: applying the Singapore foreign-sourced income exemption is beneficial | `Not confirmed` | Not yet assessed with the Singapore tax agent |

## Step 4: read the strategies

| Strategy | Guaranteed | Counts on | If it fails |
|---|---|---|---|
| 1 | CNY 100,000 (Mainland only) | adequate economic substance in Hong Kong; Singapore exemption beneficial | → 2 |
| 2 | CNY 330,000 (Mainland 100,000 + Hong Kong 230,000) | Singapore exemption beneficial | → 4 |
| 3 | CNY 440,000 (Mainland 100,000 + Singapore 340,000) | adequate economic substance in Hong Kong | → 4 |
| 4 (baseline) | CNY 670,000 | nothing | — |

The "main purpose" ruling does not appear on any card: with the facts given, taking it as favourable does not change the guaranteed tax. Open strategy 1: seven steps, starting with **step 6 — check that the Mainland remittance due 2026-07-07 was made** (the date has passed). Ask the Assistant: *"Best China needs a Hong Kong certificate of resident status to claim the 5% treaty rate on the dividend from Shanghai Anxin. Help me fill the application."* — it opens form IR1313A and the Mainland treaty-benefit report filled from the case, marks what you must add, and does not claim the rate is granted.

---

# Demo case 3: a Hong Kong subsidiary returns capital to its Mainland parent

## The case and what it practises

Jinhai Industrial (Suzhou) paid HKD 2,000,000 in 2018 for 100% of Jinhai Asia (Hong Kong). On 1 September 2026 Jinhai Asia reduced its capital and returned HKD 3,000,000 — HKD 1,000,000 of capital and HKD 2,000,000 of retained profits.

This case practises: **a capital reduction split into a dividend part and a disposal part, the cost of the capital withdrawn, the Mainland's controlled-foreign-company rule on a low-taxed Hong Kong subsidiary, and two strategies.**

```text
Ownership: Jinhai Industrial Co., Ltd. (CN) ──100%──→ Jinhai Asia Limited (HK), since 15 Mar 2018, cost HKD 2,000,000
Payment:   Jinhai Asia (HK) ── capital reduction HKD 3,000,000 on 1 Sep 2026 ──→ Jinhai Industrial (CN)
```

## Step 1: describe the case

```text
Jinhai Industrial Co., Ltd. is incorporated in Suzhou, Mainland China. Since 15 March 2018 it has held 100% of Jinhai Asia Limited, a Hong Kong company, for which it paid HKD 2,000,000. On 1 September 2026 Jinhai Asia reduced its share capital and returned HKD 3,000,000 to Jinhai Industrial. No tax has been paid on the distribution. We have the board resolution and the special resolution approving the reduction, the audited accounts of Jinhai Asia for 2025 and the bank remittance advice. Please assess as at 20 October 2026; all amounts in HKD.
```

The read-back shows the two companies, the holding with its cost, and one capital reduction of HKD 3,000,000. Name it `Demo 3 - Hong Kong capital reduction to the Mainland`.

## Step 2: attach the material and start the analysis

File `demo03_resolution.txt`:

```text
SPECIAL RESOLUTION of Jinhai Asia Limited (Hong Kong) passed on 20 August 2026: the share capital of the Company is reduced from HKD 2,000,000 to HKD 1,000,000 and the amount of HKD 3,000,000, being HKD 1,000,000 of share capital and HKD 2,000,000 of retained profits, is returned to the sole shareholder Jinhai Industrial Co., Ltd. (Suzhou, Mainland China). Audited accounts 2025: retained profits HKD 2,400,000; profits tax paid in Hong Kong for 2024/25 HKD 396,000. Remittance advice: HKD 3,000,000 paid on 1 September 2026 to the shareholder's account in Suzhou.
```

## Step 3: answer the questions

Round 1:

| Question | Answer | Source |
|---|---|---|
| Group consolidated revenue in EUR | `15000000` | Jinhai Industrial consolidated accounts 2025 |
| Jinhai Asia: after-tax profit for the year | `2400000` | Audited accounts 2025: retained profits HKD 2,400,000 |

Round 2:

| Question | Answer | Source / basis |
|---|---|---|
| Share of accumulated profits in the amount returned | `2000000` | Special resolution: HKD 2,000,000 of retained profits |
| Jinhai Asia: income tax paid outside this payment | *I don't know* | — |
| Ruling: the subsidiary's profits are mainly not active business income (CFC) | `Not confirmed` | No determination |
| Ruling: profits retained without a reasonable business need (CFC) | `Not confirmed` | No determination; the reduction returns surplus cash after the 2025 results |
| Tax cost of the capital withdrawn (disposal part) | `1000000` | Half of the HKD 2,000,000 paid in 2018: the capital was halved |

## Step 4: read the strategies

| Strategy | Guaranteed | Counts on | If it fails |
|---|---|---|---|
| 1 | HKD 500,000 (Mainland tax on the HKD 2,000,000 dividend part at 25%) | the subsidiary's profits are active business income | → 2 |
| 2 (baseline) | HKD 1,100,000 (the same plus HKD 600,000: the retained HKD 2,400,000 attributed to the parent under the CFC rule) | nothing | — |

The disposal part (HKD 1,000,000 returned against a cost of HKD 1,000,000) yields no gain, so Hong Kong and the Mainland tax nothing on it. Open strategy 1: four steps — the capital reduction file, the facts answered Unknown, the Mainland tax of HKD 500,000, the audit trail. Ask the Assistant which Mainland report covers the withholding and it opens the 扣缴企业所得税报告表 filled from the case.

---

# What the three cases have in common

```text
Describe in your own words → read-back with the sentence behind each value → confirm
   → attach documents → analysis → confirm what the documents say
   → answer only the questions the rules need (facts with a source; rulings with a basis, or Not confirmed)
   → strategies, lowest guaranteed tax first (a card per combination of favourable rulings, baseline last)
   → open one: numbers, start here, steps by phase, assistant, own report
```

What the system never does: fill a fact you did not give, confirm a relief or ruling on the authority's behalf, state a provision it did not retrieve, or change a tax amount in the assistant.
