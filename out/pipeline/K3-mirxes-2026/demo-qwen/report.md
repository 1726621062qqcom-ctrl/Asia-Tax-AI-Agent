# Question sheet: K3-mirxes-2026 (template holding)

No plan can be given yet: the data or confirmations below would change the chosen plan or its guaranteed tax. Answer only these; where you cannot, enter unknown (taken at its worst, never filled in).
Write the answers into `<case>.answers.json`: data (a value or {"value", "source"}), actions (yes / no / unknown), rulings (yes / no / unknown), library.

## SG

| Kind | Address | Question | Value | Usual source | Impact |
|---|---|---|---|---|---|
| data | `flow:up1.receipt_kind` | Please provide: how the foreign income is received (remitted / deemed remitted / not remitted) (flow:up1.receipt_kind) | enum | bank records | may lower the guaranteed tax by 700000.00 |
| ruling | `ULT.exemption_beneficial` | Has a written ruling or confirmation from the tax authority been obtained on: whether applying the foreign-sourced income exemption is beneficial to the taxpayer (ULT.exemption_beneficial) | tax authority determination | Singapore tax return | may lower the guaranteed tax by 700000.00 |

16 candidate structures; 0 of them need the required data above before they can be computed.
