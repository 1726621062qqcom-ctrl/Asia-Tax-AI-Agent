# To-do: Demo 1 - Singapore loan to Hong Kong (run 20261020T212337-1b4af9)

Extraction done; the items below are for a person to settle. Write the answers into `review.json` in this directory: `{"data": {"<path>": {"value": ..., "source": "...", "quote": "..."} | "unknown"}, "notes": [...]}`, then rerun `python -m tax_graph.pipeline C:/Coding/Projects/TUM/project_study_self/cases/private/Demo-1---Singapore-loan-to-Hong-Kong-12a603b2.json --run-id 20261020T212337-1b4af9 --from review`. Unanswered items are computed as missing, never filled in.

## missing (6)

- `flows.payment_1.arms_length_low`: not stated in the documents, or not recalled by retrieval; usual source: 销售合同、采购合同、存货与成本账、物流单据
- `flows.payment_1.arms_length_max`: not stated in the documents, or not recalled by retrieval; usual source: 销售合同、采购合同、存货与成本账、物流单据
- `flows.payment_1.arms_length_value`: samples disagree: 250000.0 / null; usual source: 销售合同、采购合同、存货与成本账、物流单据
- `flows.payment_1.foreign_tax_rate`: not stated in the documents, or not recalled by retrieval; usual source: 境外完税证明、池化选择
- `flows.payment_1.receipt_kind`: not stated in the documents, or not recalled by retrieval; usual source: 销售合同、采购合同、存货与成本账、物流单据
- `roles.MARLOW_HOLDINGS_LIMITED.attrs.accounting_period_end`: not stated in the documents, or not recalled by retrieval; usual source: 关联申报表、同期资料、调整通知书

## from a register / an official document (3)

- `flows.payment_1.assessment_notice_on`: to be provided from a register / an authority's document / the counterparty's confirmation; usual source: 支付凭证、申报表、评税通知、裁定书
- `flows.payment_1.corresponding_adjustment_granted`: to be provided from a register / an authority's document / the counterparty's confirmation; usual source: 关联申报表、同期资料、调整通知书
- `roles.MARLOW_CAPITAL_PTE_LTD.attrs.lender_interest_taxable_in_hk`: to be provided from a register / an authority's document / the counterparty's confirmation; usual source: 贷款合同、财务报表

## derived by the program, input missing (2)

- `roles.MARLOW_HOLDINGS_LIMITED.attrs.hk_tp_small_entity`: the program derives this item; what is missing is its input: complete the corresponding core fields of the collection form
- `roles.MARLOW_HOLDINGS_LIMITED.attrs.is_mne_member`: the program derives this item; what is missing is its input: complete the corresponding core fields of the collection form

## free text (2)

- `roles.MARLOW_CAPITAL_PTE_LTD.attrs.ucmt_location`: free text the program cannot check; a person fills it in
- `roles.MARLOW_HOLDINGS_LIMITED.attrs.ucmt_location`: free text the program cannot check; a person fills it in

## register unmatched (2)

- `roles.MARLOW_CAPITAL_PTE_LTD`: not found in the register: copy a record per cases/registry/README.md, or confirm the name
- `roles.MARLOW_HOLDINGS_LIMITED`: not found in the register: copy a record per cases/registry/README.md, or confirm the name
