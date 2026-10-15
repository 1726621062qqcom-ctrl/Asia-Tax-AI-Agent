# Plan: Demo 01 - Singapore services to China (template recorded)

**Structure**: the only structure

**Guaranteed tax** (every discretion item unfavourable, unknown data unfavourable): 160000.00; **best case** (every discretion item favourable): 111000.00.

## Summary by region

| Region | Guaranteed tax | Best case | Actions | Deadlines | Conditions pending the authority's acceptance |
|---|---|---|---|---|---|
| CN | 160000.00 | 60000.00 | 0 | 1 | 2 |
| SG | 0.00 | 51000.00 | 0 | 0 | 0 |
| CN∩SG | 0.00 | 0.00 | 0 | 0 | 1 |

## CN

Tax items (guaranteed):
- payment_1 · CN · vat · borne by COMPANY_A · 60000.00 · cn.vat.law.service
- payment_1 · CN · income · borne by COMPANY_A · 100000.00 · cn.wht.service_as_royalty

Deadlines:
- payment_1 · remit · 2026-09-22

Conditions still depending on the tax authority's acceptance:
- whether the service fee is a royalty because know-how is used (国税函〔2009〕507号) (COMPANY_A.service_fee_is_royalty_for_know_how, rule cn.wht.service_as_royalty): if accepted, the tax falls by up to 49000.00
- whether the service fee is reasonable and related to earning the income (COMPANY_B.reasonable_service_fee, rule cn.deduct.service)

## SG

## CN∩SG

Conditions still depending on the tax authority's acceptance:
- principal purpose test: whether obtaining the treaty benefit is one of the principal purposes (if so, no treaty relief) (COMPANY_A.ppt, rule cn-sg.ppt@cn)

## Structure details
- company COMPANY_A · SG · existing
- company COMPANY_B · CN · outside the group
- flow payment_1 · SERVICE_FEE · COMPANY_B → COMPANY_A · 1000000.00 · 2026-09-15

## Answers used
- group.group_revenue_eur = 20000000 (Fictional demo assumption: annual group consolidated revenue is EUR 20 million.)
- flow:payment_1.service_kind = ENGINEERING_DESIGN_CONSULTING (demo01_services.txt, section 1)
- flow:payment_1.service_onshore_share = 30 (demo01_services.txt, section 2)
- flow:payment_1.service_performed_in_source = True (demo01_services.txt, section 2)
