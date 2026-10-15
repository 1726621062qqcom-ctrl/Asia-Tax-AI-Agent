# Plan: K4-smit-2026 (template holding)

**Structure**: HOLD=None, exit_route=DIRECT

**Guaranteed tax** (every discretion item unfavourable, unknown data unfavourable): 25063100.00; **best case** (every discretion item favourable): 25063100.00.

**Present structure**: guaranteed 25063100.00 / best 25063100.00.

## Summary by region

| Region | Guaranteed tax | Best case | Actions | Deadlines | Conditions pending the authority's acceptance |
|---|---|---|---|---|---|
| CN | 25063100.00 | 25063100.00 | 0 | 1 | 0 |

## CN

Tax items (guaranteed):
- exit · CN · stamp · borne by ULT · 133100.00 · cn.stamp.seller
- exit · CN · stamp · borne by BUYER (outside the group, not counted) · 133100.00 · cn.stamp.buyer
- exit · CN · income · borne by ULT · 24930000.00 · cn.ftc.direct, cn.resident.gain.base, cn.resident.gain.charge

Deadlines:
- exit · remit · 2026-04-12

## Structure details
- company OP · CN · outside the group
- company ULT · CN · existing
- company BUYER · CN · outside the group
- holding ULT → OP · 7.8125% · stated by the case
- flow exit · SHARE_TRANSFER · BUYER → ULT · 266200000.00 · 2026-04-02

## Answers used
- flow:exit.cost_basis = unknown
- flow:exit.intragroup_reorg_ratio = unknown
- flow:exit.later_cn_tax_not_reduced = unknown
- flow:exit.reorg_consideration_in_equity = unknown
- group.group_revenue_eur = unknown
- flow:reorg.amount = unknown
