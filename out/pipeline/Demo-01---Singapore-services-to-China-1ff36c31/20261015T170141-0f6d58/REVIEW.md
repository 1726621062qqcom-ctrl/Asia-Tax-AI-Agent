# To-do: Demo 01 - Singapore services to China (run 20261015T170141-0f6d58)

Extraction done; the items below are for a person to settle. Write the answers into `review.json` in this directory: `{"data": {"<path>": {"value": ..., "source": "...", "quote": "..."} | "unknown"}, "notes": [...]}`, then rerun `python -m tax_graph.pipeline C:/Coding/Projects/TUM/project_study_self/cases/private/Demo-01---Singapore-services-to-China-1ff36c31.json --run-id 20261015T170141-0f6d58 --from review`. Unanswered items are computed as missing, never filled in.

## missing (8)

- `flows.payment_1.arms_length_low`: not stated in the documents, or not recalled by retrieval; usual source: 销售合同、采购合同、存货与成本账、物流单据
- `flows.payment_1.arms_length_max`: not stated in the documents, or not recalled by retrieval; usual source: 销售合同、采购合同、存货与成本账、物流单据
- `flows.payment_1.foreign_tax_rate`: not stated in the documents, or not recalled by retrieval; usual source: 境外完税证明、池化选择
- `flows.payment_1.service_onshore_share`: no figure in the quote; usual source: 服务合同、出入境与考勤记录、项目账簿
- `flows.payment_1.tax_paid_on`: not stated in the documents, or not recalled by retrieval; usual source: 支付凭证、申报表、评税通知、裁定书
- `flows.payment_1.tp_adjustment_paid_on`: not stated in the documents, or not recalled by retrieval; usual source: 关联申报表、同期资料、调整通知书
- `roles.COMPANY_B.attrs.related_party_volume`: not stated in the documents, or not recalled by retrieval; usual source: 关联申报表、同期资料、调整通知书
- `roles.COMPANY_B.attrs.tp_documentation_provided`: not stated in the documents, or not recalled by retrieval; usual source: 关联申报表、同期资料、调整通知书

## from a register / an official document (6)

- `flows.payment_1.assessment_notice_on`: to be provided from a register / an authority's document / the counterparty's confirmation; usual source: 支付凭证、申报表、评税通知、裁定书
- `flows.payment_1.corresponding_adjustment_granted`: to be provided from a register / an authority's document / the counterparty's confirmation; usual source: 关联申报表、同期资料、调整通知书
- `flows.payment_1.first_notification_on`: to be provided from a register / an authority's document / the counterparty's confirmation; usual source: 支付凭证、申报表、评税通知、裁定书
- `flows.payment_1.pboc_benchmark_rate`: to be provided from a register / an authority's document / the counterparty's confirmation; usual source: 关联申报表、同期资料、调整通知书
- `flows.payment_1.tp_adjustment_tax`: to be provided from a register / an authority's document / the counterparty's confirmation; usual source: 关联申报表、同期资料、调整通知书
- `roles.COMPANY_B.attrs.vat_general_taxpayer`: to be provided from a register / an authority's document / the counterparty's confirmation; usual source: 增值税 / GST 登记、许可合同

## derived by the program, input missing (2)

- `flows.payment_1.service_performed_in_residence`: the program derives this item; what is missing is its input: complete the corresponding core fields of the collection form
- `flows.payment_1.service_performed_in_source`: the program derives this item; what is missing is its input: complete the corresponding core fields of the collection form

## free text (3)

- `flows.payment_1.service_kind`: free text the program cannot check; a person fills it in
- `roles.COMPANY_A.attrs.ucmt_location`: free text the program cannot check; a person fills it in
- `roles.COMPANY_B.attrs.ucmt_location`: free text the program cannot check; a person fills it in

## register unmatched (2)

- `roles.COMPANY_A`: not found in the register: copy a record per cases/registry/README.md, or confirm the name
- `roles.COMPANY_B`: not found in the register: copy a record per cases/registry/README.md, or confirm the name
