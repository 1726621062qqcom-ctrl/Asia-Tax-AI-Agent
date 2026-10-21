# To-do: EKH dividend chain (run 20261020T200819-64eb75)

Extraction done; the items below are for a person to settle. Write the answers into `review.json` in this directory: `{"data": {"<path>": {"value": ..., "source": "...", "quote": "..."} | "unknown"}, "notes": [...]}`, then rerun `python -m tax_graph.pipeline C:/Coding/Projects/TUM/project_study_self/cases/private/EKH-dividend-chain-8732b344.json --run-id 20261020T200819-64eb75 --from review`. Unanswered items are computed as missing, never filled in.

## missing (19)

- `flows.payment_1.capitalised_from`: not stated in the documents, or not recalled by retrieval; usual source: 股东会决议、验资或工商变更记录、资产负债表
- `flows.payment_1.deductible_at_payer`: not stated in the documents, or not recalled by retrieval; usual source: 银行流水、境外完税证明、付款方申报表
- `flows.payment_1.direct_payment`: not stated in the documents, or not recalled by retrieval; usual source: 增资、新设或收购文件、银行流水、《利润再投资情况表》、鼓励目录对照
- `flows.payment_1.dividend_from_pre_reorg_profits`: not stated in the documents, or not recalled by retrieval; usual source: 重组协议、备案表
- `flows.payment_1.foreign_tax_rate`: value not in the quote (quote states 100000); usual source: 境外完税证明、池化选择
- `flows.payment_1.foreign_taxed`: not stated in the documents, or not recalled by retrieval; usual source: 银行流水、境外完税证明、付款方申报表
- `flows.payment_1.receipt_kind`: not stated in the documents, or not recalled by retrieval; usual source: 销售合同、采购合同、存货与成本账、物流单据
- `flows.payment_1.reinvested_in_cn`: not stated in the documents, or not recalled by retrieval; usual source: 增资、新设或收购文件、银行流水、《利润再投资情况表》、鼓励目录对照
- `flows.payment_1.reinvestment_form`: not stated in the documents, or not recalled by retrieval; usual source: 增资、新设或收购文件、银行流水、《利润再投资情况表》、鼓励目录对照
- `flows.payment_1.reinvestment_from_distributed_profit`: not stated in the documents, or not recalled by retrieval; usual source: 增资、新设或收购文件、银行流水、《利润再投资情况表》、鼓励目录对照
- `flows.payment_1.reinvestment_withdrawn`: not stated in the documents, or not recalled by retrieval; usual source: 增资、新设或收购文件、银行流水、《利润再投资情况表》、鼓励目录对照
- `flows.payment_1.remitted_on`: not stated in the documents, or not recalled by retrieval; usual source: 支付凭证、申报表、评税通知、裁定书
- `flows.payment_1.tax_paid_on`: not stated in the documents, or not recalled by retrieval; usual source: 支付凭证、申报表、评税通知、裁定书
- `flows.payment_1.underlying_profits_taxed`: not stated in the documents, or not recalled by retrieval; usual source: 银行流水、境外完税证明、付款方申报表
- `roles.BEST_CHINA_DEVELOPMENT_L.attrs.pure_equity_holding`: not stated in the documents, or not recalled by retrieval; usual source: 登记与申报记录、事先裁定书。人员、场所、开支、外包是裁量的证据，随 `Discretion.cites` 输出，不是字段
- `roles.BEST_CHINA_DEVELOPMENT_L.attrs.residence_cert`: not stated in the documents, or not recalled by retrieval; usual source: 居民身份证明书
- `flows.payment_2.foreign_tax_rate`: not stated in the documents, or not recalled by retrieval; usual source: 境外完税证明、池化选择
- `flows.payment_2.foreign_taxed`: not stated in the documents, or not recalled by retrieval; usual source: 银行流水、境外完税证明、付款方申报表
- `flows.payment_2.receipt_kind`: not stated in the documents, or not recalled by retrieval; usual source: 销售合同、采购合同、存货与成本账、物流单据

## from a register / an official document (9)

- `flows.payment_1.assessment_notice_on`: to be provided from a register / an authority's document / the counterparty's confirmation; usual source: 支付凭证、申报表、评税通知、裁定书
- `flows.payment_1.determination_on`: to be provided from a register / an authority's document / the counterparty's confirmation; usual source: 支付凭证、申报表、评税通知、裁定书
- `flows.payment_1.first_notification_on`: to be provided from a register / an authority's document / the counterparty's confirmation; usual source: 支付凭证、申报表、评税通知、裁定书
- `flows.payment_1.foreign_headline_rate`: to be provided from a register / an authority's document / the counterparty's confirmation; usual source: 银行流水、境外完税证明、付款方申报表
- `roles.BEST_CHINA_DEVELOPMENT_L.attrs.bo_safe_harbour`: to be provided from a register / an authority's document / the counterparty's confirmation; usual source: 合同、银行流水、完税证明
- `roles.BEST_CHINA_DEVELOPMENT_L.attrs.registration_filing_compliant`: to be provided from a register / an authority's document / the counterparty's confirmation; usual source: 登记与申报记录、事先裁定书。人员、场所、开支、外包是裁量的证据，随 `Discretion.cites` 输出，不是字段
- `roles.BEST_CHINA_DEVELOPMENT_L.attrs.substance_ruled_adequate`: to be provided from a register / an authority's document / the counterparty's confirmation; usual source: 登记与申报记录、事先裁定书。人员、场所、开支、外包是裁量的证据，随 `Discretion.cites` 输出，不是字段
- `flows.payment_2.assessment_notice_on`: to be provided from a register / an authority's document / the counterparty's confirmation; usual source: 支付凭证、申报表、评税通知、裁定书
- `flows.payment_2.foreign_headline_rate`: to be provided from a register / an authority's document / the counterparty's confirmation; usual source: 银行流水、境外完税证明、付款方申报表

## derived by the program, input missing (3)

- `flows.payment_1.reinvestment_withdrawn_on`: the program derives this item; what is missing is its input: complete the corresponding core fields of the collection form
- `flows.payment_1.reorg_same_residence`: the program derives this item; what is missing is its input: complete the corresponding core fields of the collection form
- `flows.payment_1.subject_income_taxed_abroad`: the program derives this item; what is missing is its input: complete the corresponding core fields of the collection form

## free text (4)

- `roles.BEST_CHINA_DEVELOPMENT_L.attrs.ucmt_location`: free text the program cannot check; a person fills it in
- `roles.SHANGHAI_ANXIN_RONG_CHEN.attrs.ucmt_location`: free text the program cannot check; a person fills it in
- `roles.EKH_LIMITED.attrs.ucmt_location`: free text the program cannot check; a person fills it in
- `roles.BEST_CHINA_DEVELOPMENT_L.attrs.ucmt_location`: free text the program cannot check; a person fills it in

## register unmatched (3)

- `roles.SHANGHAI_ANXIN_RONG_CHEN`: not found in the register: copy a record per cases/registry/README.md, or confirm the name
- `roles.BEST_CHINA_DEVELOPMENT_L`: not found in the register: copy a record per cases/registry/README.md, or confirm the name
- `roles.EKH_LIMITED`: not found in the register: copy a record per cases/registry/README.md, or confirm the name
