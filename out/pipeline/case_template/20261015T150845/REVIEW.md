# To-do: K6-example (run 20261015T150845)

Extraction done; the items below are for a person to settle. Write the answers into `review.json` in this directory: `{"data": {"<path>": {"value": ..., "source": "...", "quote": "..."} | "unknown"}, "notes": [...]}`, then rerun `python -m tax_graph.pipeline C:/Coding/Projects/TUM/project_study_self/cases/intake/case_template.json --run-id 20261015T150845 --from review`. Unanswered items are computed as missing, never filled in.

## missing (13)

- `flows.up1.capitalised_from`: not stated in the documents, or not recalled by retrieval; usual source: 股东会决议、验资或工商变更记录、资产负债表
- `flows.up1.direct_payment`: not stated in the documents, or not recalled by retrieval; usual source: 增资、新设或收购文件、银行流水、《利润再投资情况表》、鼓励目录对照
- `flows.up1.dividend_from_pre_reorg_profits`: not stated in the documents, or not recalled by retrieval; usual source: 重组协议、备案表
- `flows.up1.foreign_tax_rate`: not stated in the documents, or not recalled by retrieval; usual source: 境外完税证明、池化选择
- `flows.up1.foreign_taxed`: not stated in the documents, or not recalled by retrieval; usual source: 银行流水、境外完税证明、付款方申报表
- `flows.up1.payable_on`: not stated in the documents, or not recalled by retrieval; usual source: 支付凭证、申报表、评税通知、裁定书
- `flows.up1.reinvested_in_cn`: not stated in the documents, or not recalled by retrieval; usual source: 增资、新设或收购文件、银行流水、《利润再投资情况表》、鼓励目录对照
- `flows.up1.reinvestment_form`: not stated in the documents, or not recalled by retrieval; usual source: 增资、新设或收购文件、银行流水、《利润再投资情况表》、鼓励目录对照
- `flows.up1.reinvestment_from_distributed_profit`: not stated in the documents, or not recalled by retrieval; usual source: 增资、新设或收购文件、银行流水、《利润再投资情况表》、鼓励目录对照
- `flows.up1.reinvestment_withdrawn`: not stated in the documents, or not recalled by retrieval; usual source: 增资、新设或收购文件、银行流水、《利润再投资情况表》、鼓励目录对照
- `flows.up1.remitted_on`: not stated in the documents, or not recalled by retrieval; usual source: 支付凭证、申报表、评税通知、裁定书
- `flows.up1.tax_paid_on`: not stated in the documents, or not recalled by retrieval; usual source: 支付凭证、申报表、评税通知、裁定书
- `flows.up1.tax_paid_or_secured`: not stated in the documents, or not recalled by retrieval; usual source: 支付凭证、申报表、评税通知、裁定书

## from a register / an official document (4)

- `flows.up1.assessment_notice_on`: to be provided from a register / an authority's document / the counterparty's confirmation; usual source: 支付凭证、申报表、评税通知、裁定书
- `flows.up1.first_notification_on`: to be provided from a register / an authority's document / the counterparty's confirmation; usual source: 支付凭证、申报表、评税通知、裁定书
- `flows.up1.foreign_headline_rate`: to be provided from a register / an authority's document / the counterparty's confirmation; usual source: 银行流水、境外完税证明、付款方申报表
- `roles.ULT.attrs.bo_safe_harbour`: to be provided from a register / an authority's document / the counterparty's confirmation; usual source: 合同、银行流水、完税证明

## derived by the program, input missing (2)

- `flows.up1.reinvestment_withdrawn_on`: the program derives this item; what is missing is its input: complete the corresponding core fields of the collection form
- `flows.up1.reorg_same_residence`: the program derives this item; what is missing is its input: complete the corresponding core fields of the collection form

## free text (2)

- `roles.ULT.attrs.ucmt_location`: free text the program cannot check; a person fills it in
- `roles.OP.attrs.ucmt_location`: free text the program cannot check; a person fills it in
