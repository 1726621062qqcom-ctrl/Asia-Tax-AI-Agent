# 结果：模板 holding，主体 GROUP，事件 {'dividend': 10000000.0, 'onward': 10000000.0, 'on': '2026-06-14'}

案例文件注明的假设 / 待补：
- 来源：Mirxes Holding Company Limited（2629.HK，开曼注册）招股书 2025-05-15（cases/sources/K3-mirxes-2025/source.pdf）。K3 半合成：结构、比例、日期与重组对价来自招股书，股息额、日期、年数是合成值（见 provenance）。
- 只截取三地内的部分：ULT 为 MiRXEA Pte. Ltd.（新加坡投资控股），HOLD 为湖州觅瑞（内地外商独资，2023-05-05 设立），OP 为杭州觅未；其上的 MiRXES Holding Pte. Ltd.（新加坡）与开曼上市公司不在本例。
- 现状取重组前：MiRXEA 直接持有杭州觅未。实际所选是 HOLD=CN：2023-06-14 MiRXEA 把杭州觅未 100% 以 RMB83,463,359.41 转给湖州觅瑞，抵作其对湖州觅瑞注册资本 US$11,662,432 的实缴（pdf 288），属财税〔2009〕59号第七条第（二）项情形（口径 D35）；招股书未提特殊性税务处理、备案或纳税。重组日改到 2026-06-14。
- 未披露：MiRXEA 对杭州觅未的实缴额与计税基础、对价的定价依据、完成登记日——由程序提问。金额单位为人民币元。

## 候选表（集团总税 lo / hi；主体份额；裁量数、计划项数、脆弱度）

| 候选 | lo | hi | share@lo | share@hi | 裁量 | 计划 | 脆弱 | 被支配 |
|---|---|---|---|---|---|---|---|---|
| None/DEBT/False | -1500000.00 | 2300000.00 | -1500000.00 | 2300000.00 | 2 | 0 | 3200000.00 |  |
| None/DEBT/True | -1500000.00 | 2300000.00 | -1500000.00 | 2300000.00 | 2 | 0 | 3200000.00 |  |
| None/EQUITY/False | 0.00 | 1700000.00 | 0.00 | 1700000.00 | 4 | 1 | 500000.00 |  |
| None/EQUITY/True | 0.00 | 1700000.00 | 0.00 | 1700000.00 | 4 | 1 | 500000.00 |  |
| SG/DEBT/False | -1416536.64 | 16572234.46 | -1416536.64 | 16572234.46 | 4 | 6 | 3200000.00 | 是 |
| SG/DEBT/True | -1416536.64 | 16572234.46 | -1416536.64 | 16572234.46 | 4 | 6 | 3200000.00 | 是 |
| HK/DEBT/False | -1416536.64 | 18222234.46 | -1416536.64 | 18222234.46 | 6 | 5 | 3150000.00 | 是 |
| HK/DEBT/True | -1416536.64 | 18222234.46 | -1416536.64 | 18222234.46 | 6 | 5 | 3150000.00 | 是 |
| SG/EQUITY/False | 83463.36 | 15972234.46 | 83463.36 | 15972234.46 | 6 | 9 | 500000.00 | 是 |
| SG/EQUITY/True | 83463.36 | 15972234.46 | 83463.36 | 15972234.46 | 6 | 9 | 500000.00 | 是 |
| HK/EQUITY/False | 83463.36 | 17622234.46 | 83463.36 | 17622234.46 | 8 | 13 | 500000.00 | 是 |
| HK/EQUITY/True | 83463.36 | 17622234.46 | 83463.36 | 17622234.46 | 8 | 13 | 500000.00 | 是 |
| CN/EQUITY/False | 83463.36 | 18472234.46 | 83463.36 | 18472234.46 | 7 | 6 | 500000.00 | 是 |
| CN/EQUITY/True | 83463.36 | 18472234.46 | 83463.36 | 18472234.46 | 7 | 6 | 500000.00 | 是 |
| CN/DEBT/False | 83463.36 | 19072234.46 | 83463.36 | 19072234.46 | 7 | 4 | 3000000.00 | 是 |
| CN/DEBT/True | 83463.36 | 19072234.46 | 83463.36 | 19072234.46 | 7 | 4 | 3000000.00 | 是 |

**最优候选** {'HOLD': None, 'financing': 'DEBT', 'payment': False}（lo -1500000.00 / hi 2300000.00）；**现状** lo 0.00 / hi 1700000.00。

## 最优候选的税项（流 / 法域 / 税种 / 承担方 / 金额 / 依据）

下界：
- up1 · CN · income · payee · 1000000.00 · cn-sg.int.cap_other@cn, cn.wht.reduced
- up1 · CN · income · payer · -2500000.00 · cn.deduct.interest, cn.deduct.interest.benchmark, cn.tp.deduction_cap

上界：
- up1 · CN · vat · payee · 600000.00 · cn.vat.law.interest
- up1 · SG · income · payee · 700000.00 · sg.ftc.dta, sg.onshore.charge
- up1 · CN · income · payee · 1000000.00 · cn.wht.reduced

## 待定事实（按丢失代价排序）
- 2500000.00  ('cn.deduct.interest', 'up1')  payer.related_party_debt_equity_ratio
- 2500000.00  ('cn.deduct.interest.benchmark', 'up1')  flow.benchmark_rate, flow.interest_rate
- 700000.00  ('sg.fsie.charge', 'up1')  flow.receipt_kind
- 509433.96  ('cn.vat.law.interest', 'up1')  flow.unified_borrowing_relending
- 0.00  ('cn.vat.law.price_includes_vat', 'up1')  flow.price_includes_vat
- 0.00  ('sg.ftc.pooling', 'up1')  payee.ftc_pooling_election

## 待定条件：计划项与裁量项（按代价排序）
- 2500000.00  ('cn.deduct.interest', 'up1')  payer.arms_length_interest
- 700000.00  ('sg.onshore.charge', 'up1')  payee.income_sourced_in_sg

## 规则会读但案例未给的字段（21）
- up1  flow.arms_length_max
- up1  flow.assessment_notice_on
- up1  flow.benchmark_rate
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
- up1  payee.government_exempt_condition_met
- up1  payee.residence_cert
- up1  payer.related_party_debt_equity_ratio
- up1  payer.related_party_volume
- up1  payer.tp_documentation_provided
