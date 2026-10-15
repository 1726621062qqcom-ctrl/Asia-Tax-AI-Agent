# 结果：模板 holding，主体 GROUP，事件 {'dividend': 50000000.0, 'onward': 50000000.0, 'on': '2026-06-30'}

案例文件注明的假设 / 待补：
- 来源：Carote Ltd（2549.HK，开曼注册）招股书 2024-09-23（cases/sources/K3-carote-2024/source.pdf）。K3 半合成：结构、比例、日期与税率来自招股书，股息额与日期是合成值（见 provenance）。
- 只截取三地内的部分：ULT 为 Carote Group（香港投资控股，2023-03-07 注册），OP 为浙江卡罗特（内地主要经营公司，高新技术企业资格 2022–2024 年，2026 年是否续期未披露），HOLD 为 Carote (Singapore) Management（新加坡，2024-01-23 起由 Carote Group 全资持有，现不持有浙江卡罗特）。开曼上市公司与 BVI 股东不在本例。
- 红筹重组本身（2023-08-29 七名股东把浙江卡罗特 100% 转给 Carote Group，现金对价 RMB68,000,000 或 RMB67,731,000）卖方是个人、内地公司与合伙企业，不在 v1（只建模公司）范围内，只作背景；本例检验重组后的香港—内地链条与插入新加坡中间公司的候选。
- 未披露：香港公司的经济实质、股息是否在香港收取、税务居民证明、受益所有人判断所需事实——留给程序发问。金额单位为人民币元。

## 候选表（集团总税 lo / hi；主体份额；裁量数、计划项数、脆弱度）

| 候选 | lo | hi | share@lo | share@hi | 裁量 | 计划 | 脆弱 | 被支配 |
|---|---|---|---|---|---|---|---|---|
| None/DEBT/False | -9000000.00 | 11250000.00 | -9000000.00 | 11250000.00 | 4 | 0 | 20250000.00 |  |
| None/DEBT/True | -9000000.00 | 11250000.00 | -9000000.00 | 11250000.00 | 4 | 0 | 20250000.00 |  |
| HK/DEBT/False | -9000000.00 | 11250000.00 | -9000000.00 | 11250000.00 | 8 | 9 | 20250000.00 |  |
| HK/DEBT/True | -9000000.00 | 11250000.00 | -9000000.00 | 11250000.00 | 8 | 9 | 20250000.00 |  |
| None/EQUITY/False | 0.00 | 8250000.00 | 0.00 | 8250000.00 | 5 | 2 | 2500000.00 |  |
| None/EQUITY/True | 0.00 | 8250000.00 | 0.00 | 8250000.00 | 5 | 2 | 2500000.00 |  |
| HK/EQUITY/False | 0.00 | 8250000.00 | 0.00 | 8250000.00 | 9 | 15 | 2500000.00 |  |
| HK/EQUITY/True | 0.00 | 8250000.00 | 0.00 | 8250000.00 | 9 | 15 | 2500000.00 |  |
| SG/DEBT/False | -7500000.00 | 19750000.00 | -7500000.00 | 19750000.00 | 9 | 8 | 16000000.00 | 是 |
| SG/DEBT/True | -7500000.00 | 19750000.00 | -7500000.00 | 19750000.00 | 9 | 8 | 16000000.00 | 是 |
| SG/EQUITY/False | 0.00 | 16750000.00 | 0.00 | 16750000.00 | 10 | 11 | 2500000.00 | 是 |
| SG/EQUITY/True | 0.00 | 16750000.00 | 0.00 | 16750000.00 | 10 | 11 | 2500000.00 | 是 |
| CN/EQUITY/False | 0.00 | 20750000.00 | 0.00 | 20750000.00 | 10 | 12 | 2500000.00 | 是 |
| CN/EQUITY/True | 0.00 | 20750000.00 | 0.00 | 20750000.00 | 10 | 12 | 2500000.00 | 是 |
| CN/DEBT/False | 0.00 | 23750000.00 | 0.00 | 23750000.00 | 10 | 10 | 15000000.00 | 是 |
| CN/DEBT/True | 0.00 | 23750000.00 | 0.00 | 23750000.00 | 10 | 10 | 15000000.00 | 是 |

**最优候选** {'HOLD': None, 'financing': 'DEBT', 'payment': False}（lo -9000000.00 / hi 11250000.00）；**现状** lo 0.00 / hi 8250000.00。

## 最优候选的税项（流 / 法域 / 税种 / 承担方 / 金额 / 依据）

下界：
- up1 · CN · income · payee · 3500000.00 · cn-hk.int.cap@cn, cn.wht.reduced
- up1 · CN · income · payer · -12500000.00 · cn.deduct.interest, cn.deduct.interest.benchmark, cn.tp.deduction_cap

上界：
- up1 · CN · vat · payee · 3000000.00 · cn.vat.law.interest
- up1 · CN · income · payee · 5000000.00 · cn.wht.reduced
- up1 · HK · income · payee · 3250000.00 · hk.ftc.dta, hk.onshore.charge

## 待定事实（按丢失代价排序）
- 12500000.00  ('cn.deduct.interest', 'up1')  payer.related_party_debt_equity_ratio
- 12500000.00  ('cn.deduct.interest.benchmark', 'up1')  flow.benchmark_rate, flow.interest_rate
- 2632075.47  ('cn.vat.law.interest', 'up1')  flow.unified_borrowing_relending
- 1500000.00  ('cn-hk.int.cap@cn', 'up1')  payee.residence_cert
- 0.00  ('hk.fsie.charge', 'up1')  flow.receipt_kind
- 0.00  ('cn.vat.law.price_includes_vat', 'up1')  flow.price_includes_vat

## 待定条件：计划项与裁量项（按代价排序）
- 12500000.00  ('cn.deduct.interest', 'up1')  payer.arms_length_interest
- 4750000.00  ('hk.onshore.charge', 'up1')  payee.income_sourced_in_hk
- 1500000.00  ('cn-hk.int.cap@cn', 'up1')  payee.no_adverse_bo_factors
- 1500000.00  ('cn-hk.ppt@cn', 'up1')  payee.ppt

## 规则会读但案例未给的字段（24）
- up1  flow.arms_length_max
- up1  flow.assessment_notice_on
- up1  flow.benchmark_rate
- up1  flow.determination_on
- up1  flow.first_notification_on
- up1  flow.foreign_tax_rate
- up1  flow.interest_rate
- up1  flow.payable_on
- up1  flow.pboc_benchmark_rate
- up1  flow.price_includes_vat
- up1  flow.receipt_kind
- up1  flow.remitted_on
- up1  flow.tax_paid_on
- up1  flow.tax_paid_or_secured
- up1  flow.tp_adjustment_paid_on
- up1  flow.tp_adjustment_tax
- up1  flow.unified_borrowing_relending
- up1  payee.pure_equity_holding
- up1  payee.registration_filing_compliant
- up1  payee.residence_cert
- up1  payee.substance_ruled_adequate
- up1  payer.related_party_debt_equity_ratio
- up1  payer.related_party_volume
- up1  payer.tp_documentation_provided
