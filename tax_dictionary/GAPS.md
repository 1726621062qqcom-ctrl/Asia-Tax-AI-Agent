# Coverage gaps and classification review

Catalogue snapshot: **2026-10-16**. This is an index of the retained local corpus, not a fresh verification that every rule is current on this date.

## Requirement-level gaps

- **All tax treaties:** not established. Three bilateral pairs and selected MLI / protocol materials are indexed; treaty listing pages do not equal archived full treaties for every listed country.
- **All income / corporate regulations:** partial company-focused coverage. Whole-statute collection is not a statement that every provision has structured data or executable rules.
- **Inheritance / estate / gift tax:** no dedicated inventory or calculation coverage has been established. This includes the evidence needed to state that a regime was abolished or is not imposed.
- **Exit tax:** a separate inventory is still required. Disposal taxes, reorganisation rules and registration / re-domiciliation procedure material remain separate categories.
- **CFC:** Mainland company CFC rules are linked. No dedicated HK / SG CFC rule is indexed; no legal-absence conclusion is inferred.
- **History and legal currency:** the original library prunes superseded material and has incomplete date fields. It is not a complete historical law archive, and this build performs no new web currency verification.

## Work queue

| Priority | Work | Completion evidence |
|---|---|---|
| P1 | Inheritance / estate / gift tax inventories for each jurisdiction | Primary sources establishing existence, scope, repeal / abolition and relevant dates |
| P1 | Exit / migration taxation separately from disposals | Subject, departure trigger, deemed disposal, asset base, deferral and date sources |
| P1 | Personal income taxonomy and source selection | Tax bands, residence, reliefs, subject boundaries and source dates |
| P1 | Treaty completeness checklist | Per-pair original, protocols, entry-into-force and tax-effective dates; limited / comprehensive / EOI scope |
| P2 | Review inferred document tags | Checked taxonomy links with a reviewer and rationale; no whole-document scope inflation |
| P2 | Legal currency and missing effective dates | Dated official-source review, with repeal / amendment links |

## Classification queue

Classification is a catalogue operation. A reference-linked document is not a human-approved legal summary.

| State | Documents |
|---|---|
| metadata_inferred | 314 |
| needs_review | 20 |
| reference_linked | 141 |

### Documents without a topic assignment

- `cn.guide.hk` — 中国内地居民赴香港特别行政区投资税收指南
- `cn.guide.sg` — 中国居民赴新加坡共和国投资税收指南
- `cn.mof.cas14` — 财政部关于修订印发《企业会计准则第14号——收入》的通知
- `cn.mof.cas14.a01` — 企业会计准则第14号——收入.pdf
- `hk.arc.72` — Advance Ruling Case No. 72
- `hk.arc.73` — Advance Ruling Case No. 73
- `hk.arc.74` — Advance Ruling Case No. 74
- `hk.bor.d11-22` — Board of Review Decision D11/22
- `hk.bor.d58-01` — Board of Review Decision D58/01
- `hk.judg.2024-hkca-944` — Patrick Cox Asia Ltd v Commissioner of Inland Revenue
- `hk.judg.cacv-259-2012` — Turner Entertainment Networks Asia Inc v Commissioner of Inland Revenue
- `hk.judg.facv-14-2007` — Lee Yee Shing v Commissioner of Inland Revenue
- `hk.judg.facv-3-1999` — Commissioner of Inland Revenue v Emerson Radio Corporation
- `hk.judg.facv-8-2007` — Commissioner of Inland Revenue v HIT Finance Ltd
- `intl.oecd.beps6` — OECD/G20 BEPS Project: Preventing the Granting of Treaty Benefits in Inappropriate Circumstances, Action 6 - 2015 Final Report
- `intl.oecd.map.cn` — China Dispute Resolution Profile (OECD MAP profile)
- `intl.oecd.map.hk` — Hong Kong, China Dispute Resolution Profile (OECD MAP profile)
- `intl.oecd.map.sg` — Singapore Dispute Resolution Profile (OECD MAP profile)
- `sg.iras.corp-rate.examples` — IRAS: Examples on computing the amount of tax exemption for companies
- `sg.judg.2006-sgca-7` — Comptroller of Income Tax v HY

### Parameters without a recorded quotation

A clause reference without a verbatim supporting quote is not counted as quote-verified. In particular, the scope of a limited treaty alone does not prove that no other comprehensive treaty exists.

- `hk-sg.no_comprehensive_dta`

### Compiled rules without a direct clause link

These remain visible as model rules; no direct primary-source anchor is invented for them. Review their calculation context and add an explicit source if appropriate.

- `hk.gain.base` (HK; BASE)
- `hk.property.base` (HK; BASE)
- `hk.rent.base` (HK; BASE)
