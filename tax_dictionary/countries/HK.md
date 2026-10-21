# Hong Kong — country tax dictionary

Catalogue snapshot: **2026-10-16**. This is an index of the retained local corpus, not a fresh verification that every rule is current on this date.

[Comparison](../COMPARISON.md) · [Source catalogue](../SOURCES.md) · [Coverage gaps](../GAPS.md)

Jurisdiction code: **HK**. Local currency: **HKD**. Calculation subject: **companies within modelled scenarios**.

A parameter's source scope can be a treaty pair or another jurisdiction where the engine shares an input. The original scope is shown; shared use does not make a foreign statute domestic law.

## Double tax agreements and arrangements

The Mainland-Hong Kong arrangement is indexed with language and protocol versions. The Hong Kong-Singapore records cover limited airline / shipping income.

**Boundary:** Do not use limited transport coverage as a general treaty cap on dividends, interest or royalties.

Sources: `sources_indexed`; structured: `parameters_linked`; model: `rules_available`; judgement: `authority_or_facts_judgement_present`; completeness: `partial`.

Indexed links: 36 documents / 21 parameters / 3 compiled rules. Counts overlap across topics.

Representative archived documents (not an exhaustive reading list):

- [Hong Kong (China): MLI position upon deposit of the instrument (via China)](https://www.oecd.org/content/dam/oecd/en/topics/policy-sub-issues/beps-mli/beps-mli-position-hong-kong-instrument-deposit.pdf) · `intl.oecd.mli.hk` · [local original](../../official/raw/intl/intl.oecd.mli.hk.pdf)
- [Singapore-Hong Kong Limited DTA (IRAS PDF)](https://www.iras.gov.sg/docs/default-source/dtas/singaporehongkongdtatext.pdf?sfvrsn=cac0963f_11) · `sg.iras.dta-hk` · [local original](../../official/raw/sg/sg.iras.dta-hk.pdf)
- [Consolidated text of the Arrangement between the Mainland of China and the HKSAR for the Avoidance of Double Taxation and the Prevention of Fiscal Evasion with respect to Taxes on Income (as amended by its Protocols) - IRD reference text, not a source of law](https://www.ird.gov.hk/eng/pdf/Consolidated_Text_Mainland_HKSAR.pdf) · `treaty.cn-hk.2006.consolidated.en` · [local original](../../official/raw/hk/treaty.cn-hk.2006.consolidated.en.pdf)
- [內地和香港特別行政區關於對所得避免雙重徵稅和防止偷漏稅的安排 綜合文本 (IRD consolidated text, Chinese)](https://www.ird.gov.hk/chi/pdf/Consolidated_Text_Mainland_HKSAR.pdf) · `treaty.cn-hk.2006.consolidated.zh-hk` · [local original](../../official/raw/hk/treaty.cn-hk.2006.consolidated.zh-hk.pdf)
- [Specification of Arrangements (The Mainland of China) (Avoidance of Double Taxation and the Prevention of Fiscal Evasion with respect to Taxes on Income) Order (Cap. 112AY) - schedules the 2006 Arrangement (Arts 1-27) and its Protocol (First Protocol), Chinese text with English translation](https://www.elegislation.gov.hk/hk/cap112AY!en.rtf) · `treaty.cn-hk.2006.en` · [local original](../../official/raw/hk/treaty.cn-hk.2006.en.rtf)

## Corporate income / profits tax

Corporation profits tax has a standard rate and a separately indexed first tier; profits-source and eligibility conditions remain important.

**Boundary:** The first-tier rate is conditional; it must not replace the standard rate for the entire tax base.

Sources: `sources_indexed`; structured: `parameters_linked`; model: `rules_available`; judgement: `authority_or_facts_judgement_present`; completeness: `partial`.

Indexed links: 16 documents / 16 parameters / 21 compiled rules. Counts overlap across topics.

| Rate / condition and source parameter | Value | Source scope | Effective from | Effective to | Clause |
|---|---|---|---|---|---|
| profits tax rate corporation<br>`hk.profits.rate_corp` | 16.5 % | HK | 2018-04-01 | Open / not recorded | [hk.cap112.en#sch8B](https://www.elegislation.gov.hk/hk/cap112!en.rtf) |
| profits tax rate first 2m<br>`hk.profits.rate_corp_first_tier` | 8.25 % | HK | 2018-04-01 | Open / not recorded | [hk.cap112.en#sch8B](https://www.elegislation.gov.hk/hk/cap112!en.rtf) |

Source excerpt for `hk.profits.rate_corp`:

> at the rate of 16.5% on any part of section 14 assessable profits over $2,000,000

Source excerpt for `hk.profits.rate_corp_first_tier`:

> at the rate of 8.25% on section 14 assessable profits up to $2,000,000

Representative archived documents (not an exhaustive reading list):

- [Inland Revenue Ordinance (Cap. 112) - whole chapter, English](https://www.elegislation.gov.hk/hk/cap112!en.rtf) · `hk.cap112.en` · [local original](../../official/raw/hk/hk.cap112.en.rtf)
- [《稅務條例》(第112章) - Inland Revenue Ordinance (Cap. 112), whole chapter, Chinese](https://www.elegislation.gov.hk/hk/cap112!zh-Hant-HK.rtf) · `hk.cap112.zh` · [local original](../../official/raw/hk/hk.cap112.zh.rtf)
- [Board of Review Decision D7/19](https://www.info.gov.hk/bor/en/decisions/docs/D719.pdf) · `hk.bor.d7-19` · [local original](../../official/raw/hk/hk.bor.d7-19.pdf)
- [DIPN 13 Profits tax - Taxation of interest received](https://www.ird.gov.hk/eng/pdf/dipn13.pdf) · `hk.dipn.13` · [local original](../../official/raw/hk/hk.dipn.13.pdf)
- [DIPN 17 The taxation of persons chargeable to profits tax on behalf of non-residents](https://www.ird.gov.hk/eng/pdf/dipn17.pdf) · `hk.dipn.17` · [local original](../../official/raw/hk/hk.dipn.17.pdf)

## Personal income tax

The archived Inland Revenue Ordinance is a mixed-scope statute. A systematic personal / salaries-tax dictionary and individual calculation model are not implemented.

**Boundary:** A whole ordinance in the corpus is not equivalent to complete personal-tax coverage.

Sources: `incidental_sources_only`; structured: `source_metadata_only`; model: `not_modelled`; judgement: `not_assessed`; completeness: `partial`.

Indexed links: 2 documents / 0 parameters / 0 compiled rules. Counts overlap across topics.

Representative archived documents (not an exhaustive reading list):

- [Inland Revenue Ordinance (Cap. 112) - whole chapter, English](https://www.elegislation.gov.hk/hk/cap112!en.rtf) · `hk.cap112.en` · [local original](../../official/raw/hk/hk.cap112.en.rtf)
- [《稅務條例》(第112章) - Inland Revenue Ordinance (Cap. 112), whole chapter, Chinese](https://www.elegislation.gov.hk/hk/cap112!zh-Hant-HK.rtf) · `hk.cap112.zh` · [local original](../../official/raw/hk/hk.cap112.zh.rtf)

## Inheritance, estate and gift taxation

No dedicated inheritance / estate / gift tax inventory or calculation model is established in this catalogue.

**Boundary:** An empty category must not be displayed as a zero tax rate.

Sources: `not_indexed`; structured: `not_structured`; model: `not_modelled`; judgement: `not_assessed`; completeness: `not_assessed`.

Indexed links: 0 documents / 0 parameters / 0 compiled rules. Counts overlap across topics.

## Exit / migration taxation

Re-domiciliation procedure material exists, but it is not a complete exit / migration tax inventory.

**Boundary:** Company registration procedures and migration taxation are separate subjects.

Sources: `not_indexed`; structured: `not_structured`; model: `not_modelled`; judgement: `not_assessed`; completeness: `not_assessed`.

Indexed links: 0 documents / 0 parameters / 0 compiled rules. Counts overlap across topics.

## Controlled foreign companies

No dedicated Hong Kong CFC calculation rule is indexed. Foreign-sourced income and substance rules are classified separately.

**Boundary:** No indexed CFC rule is not proof of a legal absence of CFC or other anti-deferral measures.

Sources: `not_indexed`; structured: `not_structured`; model: `not_modelled`; judgement: `not_assessed`; completeness: `not_assessed`.

Indexed links: 0 documents / 0 parameters / 0 compiled rules. Counts overlap across topics.

## Withholding on dividends, interest, royalties and services

The model explicitly distinguishes outbound dividends / interest from royalty and other taxable situations.

**Boundary:** The cited NOCHARGE rule is scoped to the stated income and side, not a declaration that all cross-border payments are tax free.

Sources: `sources_indexed`; structured: `parameters_linked`; model: `rules_available`; judgement: `authority_or_facts_judgement_present`; completeness: `partial`.

Indexed links: 6 documents / 19 parameters / 9 compiled rules. Counts overlap across topics.

Representative archived documents (not an exhaustive reading list):

- [Inland Revenue Ordinance (Cap. 112) - whole chapter, English](https://www.elegislation.gov.hk/hk/cap112!en.rtf) · `hk.cap112.en` · [local original](../../official/raw/hk/hk.cap112.en.rtf)
- [《内地和香港特别行政区关于对所得避免双重征税和防止偷漏税的安排》第四议定书](https://www.chinatax.gov.cn/chinatax/n810341/n810770/c1153751/5131982/files/11537514.pdf) · `treaty.cn-hk.2006.p4.zh` · [local original](../../official/raw/cn/treaty.cn-hk.2006.p4.zh.pdf)
- [内地和香港特别行政区关于对所得避免双重征税和防止偷漏税的安排](https://www.chinatax.gov.cn/chinatax/n810341/n810770/c1153751/5131982/files/11537511.pdf) · `treaty.cn-hk.2006.zh` · [local original](../../official/raw/cn/treaty.cn-hk.2006.zh.pdf)
- [DIPN 17 The taxation of persons chargeable to profits tax on behalf of non-residents](https://www.ird.gov.hk/eng/pdf/dipn17.pdf) · `hk.dipn.17` · [local original](../../official/raw/hk/hk.dipn.17.pdf)
- [IRD FAQ leaflet: Non-resident Persons (Other Than Individuals) - incl. royalties / assignment fees / rentals received by offshore companies](https://www.ird.gov.hk/eng/pdf/faqciohk.pdf) · `hk.ird.royalty` · [local original](../../official/raw/hk/hk.ird.royalty.pdf)

## Foreign income, exemptions and tax credits

FSIE distinguishes covered foreign income, receipt, substance, participation and IP conditions; credit rules are linked separately.

**Boundary:** The thresholds are not a blanket exemption; entity, receipt, subject-to-tax and anti-abuse conditions remain relevant.

Sources: `sources_indexed`; structured: `parameters_linked`; model: `rules_available`; judgement: `authority_or_facts_judgement_present`; completeness: `partial`.

Indexed links: 14 documents / 40 parameters / 14 compiled rules. Counts overlap across topics.

| Rate / condition and source parameter | Value | Source scope | Effective from | Effective to | Clause |
|---|---|---|---|---|---|
| participation ratio min<br>`hk.fsie.participation_ratio_min` | 5 % | HK | Not recorded | Open / not recorded | [hk.cap112.en#s15M](https://www.elegislation.gov.hk/hk/cap112!en.rtf) |
| participation months min<br>`hk.fsie.participation_months_min` | 12 months | HK | Not recorded | Open / not recorded | [hk.cap112.en#s15M](https://www.elegislation.gov.hk/hk/cap112!en.rtf) |

Source excerpt for `hk.fsie.participation_ratio_min`:

> has continuously held not less than 5% of equity interests in the investee entity

Source excerpt for `hk.fsie.participation_months_min`:

> for a period of not less than 12 months immediately before

Representative archived documents (not an exhaustive reading list):

- [Inland Revenue Ordinance (Cap. 112) - whole chapter, English](https://www.elegislation.gov.hk/hk/cap112!en.rtf) · `hk.cap112.en` · [local original](../../official/raw/hk/hk.cap112.en.rtf)
- [Advance Ruling Case No. 75](https://www.ird.gov.hk/eng/ppr/advance75.htm) · `hk.arc.75` · [local original](../../official/raw/hk/hk.arc.75.html)
- [IRD: Advance Ruling on Compliance with the Economic Substance Requirement (ESR) under the FSIE Regime](https://www.ird.gov.hk/eng/tax/fsie_aru.htm) · `hk.fsie.aru` · [local original](../../official/raw/hk/hk.fsie.aru.html)
- [here](https://www.ird.gov.hk/eng/pdf/ir1297_annex.xlsx) · `hk.fsie.aru.a01` · [local original](../../official/raw/hk/hk.fsie.aru.a01.xlsx)
- [IRD: FSIE regime - Illustrative Examples](https://www.ird.gov.hk/eng/tax/fsie_example.htm) · `hk.fsie.examples` · [local original](../../official/raw/hk/hk.fsie.examples.html)

## Share disposals and capital / revenue gains

Capital / revenue character, onshore disposal certainty and foreign disposal income are separate rule routes.

**Boundary:** Do not summarise all share gains as automatically untaxed.

Sources: `sources_indexed`; structured: `parameters_linked`; model: `rules_available`; judgement: `authority_or_facts_judgement_present`; completeness: `partial`.

Indexed links: 10 documents / 11 parameters / 5 compiled rules. Counts overlap across topics.

| Rate / condition and source parameter | Value | Source scope | Effective from | Effective to | Clause |
|---|---|---|---|---|---|
| qualifying equity interest min<br>`hk.onshore_gain.ratio_min` | 15 % | HK | 2024-01-01 | Open / not recorded | [hk.cap112.en#sch17K](https://www.elegislation.gov.hk/hk/cap112!en.rtf) |
| holding months min<br>`hk.onshore_gain.holding_months_min` | 24 months | HK | 2024-01-01 | Open / not recorded | [hk.cap112.en#sch17K](https://www.elegislation.gov.hk/hk/cap112!en.rtf) |

Source excerpt for `hk.onshore_gain.ratio_min`:

> entitle the holder of the interests to at least a 15% share in the profits, capital or reserves of the investee entity

Source excerpt for `hk.onshore_gain.holding_months_min`:

> means the continuous period of 24 months immediately before the date of the disposal

Representative archived documents (not an exhaustive reading list):

- [Inland Revenue Ordinance (Cap. 112) - whole chapter, English](https://www.elegislation.gov.hk/hk/cap112!en.rtf) · `hk.cap112.en` · [local original](../../official/raw/hk/hk.cap112.en.rtf)
- [内地和香港特别行政区关于对所得避免双重征税和防止偷漏税的安排第二议定书](https://www.chinatax.gov.cn/chinatax/n810341/n810770/c1153751/5131982/files/11537512.pdf) · `treaty.cn-hk.2006.p2.zh` · [local original](../../official/raw/cn/treaty.cn-hk.2006.p2.zh.pdf)
- [《内地和香港特别行政区关于对所得避免双重征税和防止偷漏税的安排》第四议定书](https://www.chinatax.gov.cn/chinatax/n810341/n810770/c1153751/5131982/files/11537514.pdf) · `treaty.cn-hk.2006.p4.zh` · [local original](../../official/raw/cn/treaty.cn-hk.2006.p4.zh.pdf)
- [《内地和香港特别行政区关于对所得避免双重征税和防止偷漏税的安排》第五议定书](https://www.chinatax.gov.cn/chinatax/n810341/n810770/c1153751/5131982/files/%E9%A6%99%E6%B8%AF%E7%AC%AC%E4%BA%94%E8%AE%AE%E5%AE%9A%E4%B9%A6.pdf) · `treaty.cn-hk.2006.p5.zh` · [local original](../../official/raw/cn/treaty.cn-hk.2006.p5.zh.pdf)
- [Board of Review Decision D8/23](https://www.info.gov.hk/bor/en/decisions/D823.pdf) · `hk.bor.d8-23` · [local original](../../official/raw/hk/hk.bor.d8-23.pdf)

## Reorganisation, distributions and liquidation

Specific stamp-duty and FSIE intragroup provisions are represented, alongside scenario-specific unwind steps.

**Boundary:** An intragroup relationship does not by itself establish relief.

Sources: `sources_indexed`; structured: `parameters_linked`; model: `rules_available`; judgement: `authority_or_facts_judgement_present`; completeness: `partial`.

Indexed links: 3 documents / 8 parameters / 7 compiled rules. Counts overlap across topics.

Representative archived documents (not an exhaustive reading list):

- [Inland Revenue Ordinance (Cap. 112) - whole chapter, English](https://www.elegislation.gov.hk/hk/cap112!en.rtf) · `hk.cap112.en` · [local original](../../official/raw/hk/hk.cap112.en.rtf)
- [Stamp Duty Ordinance (Cap. 117) - whole chapter, English](https://www.elegislation.gov.hk/hk/cap117!en.rtf) · `hk.cap117.en` · [local original](../../official/raw/hk/hk.cap117.en.rtf)
- [IRD: FSIE regime - Illustrative Examples](https://www.ird.gov.hk/eng/tax/fsie_example.htm) · `hk.fsie.examples` · [local original](../../official/raw/hk/hk.fsie.examples.html)

## Tax residence, source and permanent establishments

Profits source, recipient residence certificates and treaty PE issues are indexed as separate questions, with selected source-of-profits precedents.

**Boundary:** A Hong Kong bank receipt or incorporation record alone does not settle the profits-source analysis.

Sources: `sources_indexed`; structured: `parameters_linked`; model: `rules_available`; judgement: `authority_or_facts_judgement_present`; completeness: `partial`.

Indexed links: 18 documents / 5 parameters / 3 compiled rules. Counts overlap across topics.

Representative archived documents (not an exhaustive reading list):

- [Inland Revenue Ordinance (Cap. 112) - whole chapter, English](https://www.elegislation.gov.hk/hk/cap112!en.rtf) · `hk.cap112.en` · [local original](../../official/raw/hk/hk.cap112.en.rtf)
- [内地和香港特别行政区关于对所得避免双重征税和防止偷漏税的安排第二议定书](https://www.chinatax.gov.cn/chinatax/n810341/n810770/c1153751/5131982/files/11537512.pdf) · `treaty.cn-hk.2006.p2.zh` · [local original](../../official/raw/cn/treaty.cn-hk.2006.p2.zh.pdf)
- [内地和香港特别行政区关于对所得避免双重征税和防止偷漏税的安排](https://www.chinatax.gov.cn/chinatax/n810341/n810770/c1153751/5131982/files/11537511.pdf) · `treaty.cn-hk.2006.zh` · [local original](../../official/raw/cn/treaty.cn-hk.2006.zh.pdf)
- [Administrative arrangement between the Mainland and Hong Kong on Certificate of Resident Status (notes exchanged 16 March 2016 and 15 April 2016) - as linked from the CoR page](https://www.ird.gov.hk/eng/pdf/Admin_arrangement_e.pdf) · `hk.cor.admin-arrangement` · [local original](../../official/raw/hk/hk.cor.admin-arrangement.pdf)
- [IRD FAQ: Certificate of Resident Status (CoR)](https://www.ird.gov.hk/eng/faq/dta_cor.htm) · `hk.cor.faq` · [local original](../../official/raw/hk/hk.cor.faq.html)

## Transfer pricing and interest deduction limits

Pricing adjustments, deduction limits and local / master file requirements have specific company and transaction conditions.

**Boundary:** Documentation exemptions and an arm's-length result are separate tests.

Sources: `sources_indexed`; structured: `parameters_linked`; model: `rules_available`; judgement: `no_discretion_flag_in_linked_rules`; completeness: `partial`.

Indexed links: 7 documents / 12 parameters / 4 compiled rules. Counts overlap across topics.

Representative archived documents (not an exhaustive reading list):

- [Inland Revenue Ordinance (Cap. 112) - whole chapter, English](https://www.elegislation.gov.hk/hk/cap112!en.rtf) · `hk.cap112.en` · [local original](../../official/raw/hk/hk.cap112.en.rtf)
- [内地和香港特别行政区关于对所得避免双重征税和防止偷漏税的安排](https://www.chinatax.gov.cn/chinatax/n810341/n810770/c1153751/5131982/files/11537511.pdf) · `treaty.cn-hk.2006.zh` · [local original](../../official/raw/cn/treaty.cn-hk.2006.zh.pdf)
- [DIPN 45 Relief from double taxation due to transfer pricing or profit reallocation adjustments](https://www.ird.gov.hk/eng/pdf/dipn45.pdf) · `hk.dipn.45` · [local original](../../official/raw/hk/hk.dipn.45.pdf)
- [DIPN 59 Transfer Pricing between Associated Persons](https://www.ird.gov.hk/eng/pdf/dipn59.pdf) · `hk.dipn.59` · [local original](../../official/raw/hk/hk.dipn.59.pdf)
- [BIRS2 Supplementary Form S2 to Profits Tax Return - Transfer pricing and international tax obligations](https://www.ird.gov.hk/eng/pdf/birs2.pdf) · `hk.form.bir51.s2` · [local original](../../official/raw/hk/hk.form.bir51.s2.pdf)

## Anti-abuse, beneficial ownership and substance

FSIE substance, beneficial ownership and treaty anti-abuse conditions are separately indexed; selected IRD rulings and judgments support fact analysis.

**Boundary:** A ruling for another applicant is not the current company's approval.

Sources: `sources_indexed`; structured: `parameters_linked`; model: `rules_available`; judgement: `authority_or_facts_judgement_present`; completeness: `partial`.

Indexed links: 17 documents / 36 parameters / 11 compiled rules. Counts overlap across topics.

Representative archived documents (not an exhaustive reading list):

- [Inland Revenue Ordinance (Cap. 112) - whole chapter, English](https://www.elegislation.gov.hk/hk/cap112!en.rtf) · `hk.cap112.en` · [local original](../../official/raw/hk/hk.cap112.en.rtf)
- [《内地和香港特别行政区关于对所得避免双重征税和防止偷漏税的安排》第五议定书](https://www.chinatax.gov.cn/chinatax/n810341/n810770/c1153751/5131982/files/%E9%A6%99%E6%B8%AF%E7%AC%AC%E4%BA%94%E8%AE%AE%E5%AE%9A%E4%B9%A6.pdf) · `treaty.cn-hk.2006.p5.zh` · [local original](../../official/raw/cn/treaty.cn-hk.2006.p5.zh.pdf)
- [Advance Ruling Case No. 68](https://www.ird.gov.hk/eng/ppr/advance68.htm) · `hk.arc.68` · [local original](../../official/raw/hk/hk.arc.68.html)
- [Advance Ruling Case No. 69](https://www.ird.gov.hk/eng/ppr/advance69.htm) · `hk.arc.69` · [local original](../../official/raw/hk/hk.arc.69.html)
- [Advance Ruling Case No. 70](https://www.ird.gov.hk/eng/ppr/advance70.htm) · `hk.arc.70` · [local original](../../official/raw/hk/hk.arc.70.html)

## IP licensing, ownership transfers and allowances

Royalty charging, IP ownership disposals and FSIE IP nexus conditions are separate rule families.

**Boundary:** Non-IP holding substance relief must not be applied automatically to IP income.

Sources: `sources_indexed`; structured: `parameters_linked`; model: `rules_available`; judgement: `authority_or_facts_judgement_present`; completeness: `partial`.

Indexed links: 8 documents / 13 parameters / 7 compiled rules. Counts overlap across topics.

Representative archived documents (not an exhaustive reading list):

- [Inland Revenue Ordinance (Cap. 112) - whole chapter, English](https://www.elegislation.gov.hk/hk/cap112!en.rtf) · `hk.cap112.en` · [local original](../../official/raw/hk/hk.cap112.en.rtf)
- [《内地和香港特别行政区关于对所得避免双重征税和防止偷漏税的安排》第四议定书](https://www.chinatax.gov.cn/chinatax/n810341/n810770/c1153751/5131982/files/11537514.pdf) · `treaty.cn-hk.2006.p4.zh` · [local original](../../official/raw/cn/treaty.cn-hk.2006.p4.zh.pdf)
- [内地和香港特别行政区关于对所得避免双重征税和防止偷漏税的安排](https://www.chinatax.gov.cn/chinatax/n810341/n810770/c1153751/5131982/files/11537511.pdf) · `treaty.cn-hk.2006.zh` · [local original](../../official/raw/cn/treaty.cn-hk.2006.zh.pdf)
- [DIPN 22 Taxation of royalties and other income from intellectual properties](https://www.ird.gov.hk/eng/pdf/dipn22.pdf) · `hk.dipn.22` · [local original](../../official/raw/hk/hk.dipn.22.pdf)
- [IRD: Tax Rates for Dividends, Interest, Royalties and Technical Fees (under comprehensive DTAs)](https://www.ird.gov.hk/eng/tax/dta_rates.htm) · `hk.ird.dta-rates` · [local original](../../official/raw/hk/hk.ird.dta-rates.html)

## VAT / GST

No VAT / GST calculation family or dedicated non-charge evidence is indexed under this topic.

**Boundary:** This catalogue does not infer the legal absence of a tax from the absence of a rule.

Sources: `not_indexed`; structured: `not_structured`; model: `not_modelled`; judgement: `not_assessed`; completeness: `not_assessed`.

Indexed links: 0 documents / 0 parameters / 0 compiled rules. Counts overlap across topics.

## Stamp duties

Stock-transfer stamp duty is catalogued separately from profits tax; property instruments have their own rules.

**Boundary:** The cited stock parameter does not describe the entire property duty schedule.

Sources: `sources_indexed`; structured: `parameters_linked`; model: `rules_available`; judgement: `no_discretion_flag_in_linked_rules`; completeness: `partial`.

Indexed links: 1 documents / 24 parameters / 6 compiled rules. Counts overlap across topics.

| Rate / condition and source parameter | Value | Source scope | Effective from | Effective to | Clause |
|---|---|---|---|---|---|
| stamp duty contract note rate<br>`hk.stamp.stock_rate` | 0.1 % | HK | 2023-11-17 | Open / not recorded | [hk.cap117.en#sch1](https://www.elegislation.gov.hk/hk/cap117!en.rtf) |

Source excerpt for `hk.stamp.stock_rate`:

> 0.1% of the amount of the consideration or of its value at the date on which the contract note falls to be executed

Representative archived documents (not an exhaustive reading list):

- [Stamp Duty Ordinance (Cap. 117) - whole chapter, English](https://www.elegislation.gov.hk/hk/cap117!en.rtf) · `hk.cap117.en` · [local original](../../official/raw/hk/hk.cap117.en.rtf)

## Property, rent, land appreciation and deed taxes

Property-tax rate, statutory allowance and set-off parameters are indexed separately from profits tax and property-transfer duties.

**Boundary:** The allowance percentage and tax rate use different bases and must not be added.

Sources: `sources_indexed`; structured: `parameters_linked`; model: `rules_available`; judgement: `authority_or_facts_judgement_present`; completeness: `partial`.

Indexed links: 1 documents / 4 parameters / 8 compiled rules. Counts overlap across topics.

| Rate / condition and source parameter | Value | Source scope | Effective from | Effective to | Clause |
|---|---|---|---|---|---|
| property tax standard rate<br>`hk.property_tax.rate` | 15 % | HK | 2024-04-01 | Open / not recorded | [hk.cap112.en#sch1](https://www.elegislation.gov.hk/hk/cap112!en.rtf) |
| repairs and outgoings allowance<br>`hk.property_tax.repairs_allowance` | 20 % | HK | Not recorded | Open / not recorded | [hk.cap112.en#s5](https://www.elegislation.gov.hk/hk/cap112!en.rtf) |

Source excerpt for `hk.property_tax.rate`:

> (b) for other taxes — 15%

Source excerpt for `hk.property_tax.repairs_allowance`:

> an allowance for repairs and outgoings of 20% of that assessable value

Representative archived documents (not an exhaustive reading list):

- [Inland Revenue Ordinance (Cap. 112) - whole chapter, English](https://www.elegislation.gov.hk/hk/cap112!en.rtf) · `hk.cap112.en` · [local original](../../official/raw/hk/hk.cap112.en.rtf)

## VAT-related surcharges

No dedicated VAT-related surcharge calculation family is indexed for Hong Kong.

**Boundary:** This records model coverage and does not establish the legal absence of all additional levies.

Sources: `not_indexed`; structured: `not_structured`; model: `not_modelled`; judgement: `not_assessed`; completeness: `not_assessed`.

Indexed links: 0 documents / 0 parameters / 0 compiled rules. Counts overlap across topics.

## Customs and cross-border goods

No dedicated Hong Kong customs calculation family is established in the current engine catalogue.

**Boundary:** No rule does not establish a zero duty for a specific product.

Sources: `not_indexed`; structured: `not_structured`; model: `not_modelled`; judgement: `not_assessed`; completeness: `not_assessed`.

Indexed links: 0 documents / 0 parameters / 0 compiled rules. Counts overlap across topics.

## Pillar Two / minimum top-up taxes

Hong Kong minimum-tax and group-rule material is collected, with modelled parameters and judgement-dependent conditions.

**Boundary:** Group thresholds, fiscal years, entity exclusions and the relevant domestic or income-inclusion rule must be checked separately.

Sources: `sources_indexed`; structured: `parameters_linked`; model: `rules_available`; judgement: `no_discretion_flag_in_linked_rules`; completeness: `partial`.

Indexed links: 1 documents / 20 parameters / 3 compiled rules. Counts overlap across topics.

Representative archived documents (not an exhaustive reading list):

- [Inland Revenue (Amendment) (Minimum Tax for Multinational Enterprise Groups) Ordinance 2025](https://www.ird.gov.hk/eng/pdf/iro/gazette/ord_112_21_2025.pdf) · `hk.ord.2025-21` · [local original](../../official/raw/hk/hk.ord.2025-21.pdf)

## Loss utilisation and group relief

Loss carryforward, Hong Kong activity scope and ownership-change conditions have model rules.

**Boundary:** A loss ledger does not by itself establish that the loss is available against this income.

Sources: `sources_indexed`; structured: `parameters_linked`; model: `rules_available`; judgement: `authority_or_facts_judgement_present`; completeness: `partial`.

Indexed links: 1 documents / 3 parameters / 2 compiled rules. Counts overlap across topics.

Representative archived documents (not an exhaustive reading list):

- [Inland Revenue Ordinance (Cap. 112) - whole chapter, English](https://www.elegislation.gov.hk/hk/cap112!en.rtf) · `hk.cap112.en` · [local original](../../official/raw/hk/hk.cap112.en.rtf)

## Returns, payments, refunds, disputes and calendars

CoR, FSIE and profits-tax forms, objection / appeal and MAP materials are linked separately.

**Boundary:** The objection period is tied to its notice and the applicable procedural conditions, not the transaction date alone.

Sources: `sources_indexed`; structured: `parameters_linked`; model: `rules_available`; judgement: `no_discretion_flag_in_linked_rules`; completeness: `partial`.

Indexed links: 20 documents / 5 parameters / 4 compiled rules. Counts overlap across topics.

| Rate / condition and source parameter | Value | Source scope | Effective from | Effective to | Clause |
|---|---|---|---|---|---|
| objection months after notice of assessment<br>`hk.objection.months` | 1 months | HK | Not recorded | Open / not recorded | [hk.cap112.en#s64](https://www.elegislation.gov.hk/hk/cap112!en.rtf) |

Source excerpt for `hk.objection.months`:

> received by the Commissioner within 1 month after the date of the notice of assessment

Representative archived documents (not an exhaustive reading list):

- [Inland Revenue Ordinance (Cap. 112) - whole chapter, English](https://www.elegislation.gov.hk/hk/cap112!en.rtf) · `hk.cap112.en` · [local original](../../official/raw/hk/hk.cap112.en.rtf)
- [内地和香港特别行政区关于对所得避免双重征税和防止偷漏税的安排](https://www.chinatax.gov.cn/chinatax/n810341/n810770/c1153751/5131982/files/11537511.pdf) · `treaty.cn-hk.2006.zh` · [local original](../../official/raw/cn/treaty.cn-hk.2006.zh.pdf)
- [Administrative arrangement between the Mainland and Hong Kong on Certificate of Resident Status (notes exchanged 16 March 2016 and 15 April 2016) - as linked from the CoR page](https://www.ird.gov.hk/eng/pdf/Admin_arrangement_e.pdf) · `hk.cor.admin-arrangement` · [local original](../../official/raw/hk/hk.cor.admin-arrangement.pdf)
- [IRD FAQ: Certificate of Resident Status (CoR)](https://www.ird.gov.hk/eng/faq/dta_cor.htm) · `hk.cor.faq` · [local original](../../official/raw/hk/hk.cor.faq.html)
- [IRD: Certificate of Resident Status - guidance page](https://www.ird.gov.hk/eng/tax/dta_cor.htm) · `hk.cor.page` · [local original](../../official/raw/hk/hk.cor.page.html)

## Corporate law and re-domiciliation procedures

Companies Registry re-domiciliation procedure material is indexed as supporting law.

**Boundary:** A migration procedure source does not establish the full tax cost of departure, entry or subsequent transactions.

Sources: `sources_indexed`; structured: `source_metadata_only`; model: `not_modelled`; judgement: `not_assessed`; completeness: `partial`.

Indexed links: 1 documents / 0 parameters / 0 compiled rules. Counts overlap across topics.

Representative archived documents (not an exhaustive reading list):

- [Companies Registry: Company Re-domiciliation Regime — Frequently Asked Questions](https://www.cr.gov.hk/en/legislation/co2025/redomiciliation/faq.htm) · `hk.cr.redomiciliation.faq` · [local original](../../official/raw/hk/hk.cr.redomiciliation.faq.html)
