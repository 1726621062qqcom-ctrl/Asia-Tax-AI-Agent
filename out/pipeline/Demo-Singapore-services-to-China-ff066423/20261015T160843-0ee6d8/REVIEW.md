# To-do: Demo — Singapore services to China (run 20261015T160843-0ee6d8)

Extraction done; the items below are for a person to settle. Write the answers into `review.json` in this directory: `{"data": {"<path>": {"value": ..., "source": "...", "quote": "..."} | "unknown"}, "notes": [...]}`, then rerun `python -m tax_graph.pipeline C:/Coding/Projects/TUM/project_study_self/cases/private/Demo-Singapore-services-to-China-ff066423.json --run-id 20261015T160843-0ee6d8 --from review`. Unanswered items are computed as missing, never filled in.

## missing (16)

- `flows.fee.arms_length_low`: not stated in the documents, or not recalled by retrieval; usual source: 销售合同、采购合同、存货与成本账、物流单据
- `flows.fee.arms_length_max`: not stated in the documents, or not recalled by retrieval; usual source: 销售合同、采购合同、存货与成本账、物流单据
- `flows.fee.arms_length_value`: not stated in the documents, or not recalled by retrieval; usual source: 销售合同、采购合同、存货与成本账、物流单据
- `flows.fee.foreign_tax_rate`: not stated in the documents, or not recalled by retrieval; usual source: 境外完税证明、池化选择
- `flows.fee.input_vat_documents_kept`: not stated in the documents, or not recalled by retrieval; usual source: 增值税 / GST 登记、许可合同
- `flows.fee.price_includes_vat`: not stated in the documents, or not recalled by retrieval; usual source: 增值税 / GST 登记、许可合同
- `flows.fee.profit_margin`: not stated in the documents, or not recalled by retrieval; usual source: 服务合同、出入境与考勤记录、项目账簿
- `flows.fee.receipt_kind`: not stated in the documents, or not recalled by retrieval; usual source: 销售合同、采购合同、存货与成本账、物流单据
- `flows.fee.remitted_on`: not stated in the documents, or not recalled by retrieval; usual source: 支付凭证、申报表、评税通知、裁定书
- `flows.fee.service_days_12m`: not stated in the documents, or not recalled by retrieval; usual source: 登记、租约、人员记录
- `flows.fee.service_onshore_share`: not stated in the documents, or not recalled by retrieval; usual source: 服务合同、出入境与考勤记录、项目账簿
- `flows.fee.tax_paid_on`: not stated in the documents, or not recalled by retrieval; usual source: 支付凭证、申报表、评税通知、裁定书
- `flows.fee.tp_adjustment_paid_on`: not stated in the documents, or not recalled by retrieval; usual source: 关联申报表、同期资料、调整通知书
- `roles.SERVICER.attrs.residence_cert`: not stated in the documents, or not recalled by retrieval; usual source: 居民身份证明书
- `roles.CLIENT.attrs.related_party_volume`: not stated in the documents, or not recalled by retrieval; usual source: 关联申报表、同期资料、调整通知书
- `roles.CLIENT.attrs.tp_documentation_provided`: not stated in the documents, or not recalled by retrieval; usual source: 关联申报表、同期资料、调整通知书

## from a register / an official document (6)

- `flows.fee.assessment_notice_on`: to be provided from a register / an authority's document / the counterparty's confirmation; usual source: 支付凭证、申报表、评税通知、裁定书
- `flows.fee.corresponding_adjustment_granted`: to be provided from a register / an authority's document / the counterparty's confirmation; usual source: 关联申报表、同期资料、调整通知书
- `flows.fee.first_notification_on`: to be provided from a register / an authority's document / the counterparty's confirmation; usual source: 支付凭证、申报表、评税通知、裁定书
- `flows.fee.pboc_benchmark_rate`: to be provided from a register / an authority's document / the counterparty's confirmation; usual source: 关联申报表、同期资料、调整通知书
- `flows.fee.tp_adjustment_tax`: to be provided from a register / an authority's document / the counterparty's confirmation; usual source: 关联申报表、同期资料、调整通知书
- `roles.CLIENT.attrs.vat_general_taxpayer`: to be provided from a register / an authority's document / the counterparty's confirmation; usual source: 增值税 / GST 登记、许可合同

## derived by the program, input missing (2)

- `flows.fee.service_performed_in_residence`: the program derives this item; what is missing is its input: complete the corresponding core fields of the collection form
- `flows.fee.service_performed_in_source`: the program derives this item; what is missing is its input: complete the corresponding core fields of the collection form

## free text (3)

- `flows.fee.service_kind`: free text the program cannot check; a person fills it in
- `roles.SERVICER.attrs.ucmt_location`: free text the program cannot check; a person fills it in
- `roles.CLIENT.attrs.ucmt_location`: free text the program cannot check; a person fills it in

## register unmatched (2)

- `roles.SERVICER`: not found in the register: copy a record per cases/registry/README.md, or confirm the name
- `roles.CLIENT`: not found in the register: copy a record per cases/registry/README.md, or confirm the name
