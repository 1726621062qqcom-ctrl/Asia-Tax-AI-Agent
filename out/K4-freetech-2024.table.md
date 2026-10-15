# 结果：模板 holding，主体 GROUP，事件 {'exit': 71099000.0, 'on': '2024-11-22'}

案例文件注明的假设 / 待补：
- 来源：英達公路再生科技（6888.HK）2024-12-16 通函（cases/sources/K4-freetech-2024/source.pdf）。
- 只建模三地内的部分：卖方（香港）记为 ULT，其上层的开曼上市公司等不在范围内；标的为 OP，买方（内地国企，原持 45%）为集团外 BUYER。
- 计税成本取通函所载“约人民币 4,680 万元”的出资对价；金额单位为人民币元。

## 候选表（集团总税 lo / hi；主体份额；裁量数、计划项数、脆弱度）

| 候选 | lo | hi | share@lo | share@hi | 裁量 | 计划 | 脆弱 | 被支配 |
|---|---|---|---|---|---|---|---|---|
| CN/DIRECT | 0.00 | 0.00 | 0.00 | 0.00 | 0 | 0 | 0.00 |  |
| SG/DIRECT | 0.00 | 0.00 | 0.00 | 0.00 | 3 | 7 | 0.00 |  |
| HK/DIRECT | 0.00 | 0.00 | 0.00 | 0.00 | 3 | 10 | 0.00 |  |
| SG/INDIRECT | 0.00 | 19196730.00 | 0.00 | 19196730.00 | 2 | 0 | 0.00 | 是 |
| CN/INDIRECT | 35549.50 | 11766884.50 | 35549.50 | 11766884.50 | 2 | 2 | 0.00 | 是 |
| HK/INDIRECT | 71099.00 | 18912334.00 | 71099.00 | 18912334.00 | 4 | 3 | 0.00 | 是 |
| None/DIRECT | 2465449.50 | 4044884.50 | 2465449.50 | 4044884.50 | 2 | 1 | 0.00 | 是 |

**最优候选** {'HOLD': 'CN', 'exit_route': 'DIRECT'}：lo 0.00 / hi 0.00。

## 最优候选的税项（流 / 法域 / 税种 / 承担方 / 金额 / 依据）

下界：
- reorg · CN · stamp · payee · 0.00 · cn.stamp.seller
- reorg · CN · stamp · payer · 0.00 · cn.stamp.buyer
- exit · CN · stamp · payee · 35549.50 · cn.stamp.seller
- exit · CN · stamp · payer · 35549.50 · cn.stamp.buyer

上界：
- reorg · CN · stamp · payee · 0.00 · cn.stamp.seller
- reorg · CN · stamp · payer · 0.00 · cn.stamp.buyer
- exit · CN · income · payee · 17774750.00 · cn.ftc.direct, cn.gain.base, cn.resident.gain.base, cn.resident.gain.charge
- exit · CN · stamp · payee · 35549.50 · cn.stamp.seller
- exit · CN · stamp · payer · 35549.50 · cn.stamp.buyer

## 待定事实（按丢失代价排序）
- 0.00  ('hk.fsie.charge', 'reorg')  flow.receipt_kind
- 0.00  ('cn.resident.gain.base', 'exit')  flow.cost_basis
- 0.00  ('cn.gain.base', 'exit')  flow.cost_basis
- 0.00  ('data.p2_scope', 'HK')  group.group_revenue_eur
- 0.00  ('data.p2_dm', 'HK')  group.p2_dm_avg_income_eur_hk, group.p2_dm_avg_revenue_eur_hk
- 0.00  ('data.p2_income', 'ULT')  group.group_revenue_eur

## 待定条件：计划项与裁量项（按代价排序）

## 规则会读但案例未给的字段（46）
- exit  flow.assessment_notice_on
- exit  flow.cn_cost_basis
- exit  flow.cost_basis
- exit  flow.payable_on
- exit  flow.remitted_on
- exit  flow.reorg_acquired_ratio
- exit  flow.reorg_buyer_resident_in_cn
- exit  flow.reorg_commitment_3y
- exit  flow.reorg_control_ratio
- exit  flow.reorg_equity_payment_share
- exit  flow.reorg_filed
- exit  flow.reorg_horizon_years
- exit  flow.reorg_operations_unchanged_12m
- exit  flow.reorg_same_residence
- exit  flow.reorg_shares_kept_12m
- exit  flow.shares_cancelled
- exit  flow.tax_paid_on
- exit  flow.tax_paid_or_secured
- reorg  flow.acquirer_chargeable_in_hk
- reorg  flow.assessment_notice_on
- reorg  flow.clawback_event_within_2y
- reorg  flow.cn_cost_basis
- reorg  flow.deductible_at_payer
- reorg  flow.determination_on
- reorg  flow.first_notification_on
- reorg  flow.foreign_headline_rate
- reorg  flow.foreign_tax_rate
- reorg  flow.foreign_taxed
- reorg  flow.immovable_ratio
- reorg  flow.listed_market_trade
- reorg  flow.payable_on
- reorg  flow.receipt_kind
- reorg  flow.remitted_on
- reorg  flow.reorg_commitment_3y
- reorg  flow.reorg_equity_payment_share
- reorg  flow.reorg_filed
- reorg  flow.reorg_operations_unchanged_12m
- reorg  flow.reorg_shares_kept_12m
- reorg  flow.shares_cancelled
- reorg  flow.tax_paid_on
- reorg  flow.tax_paid_or_secured
- reorg  flow.underlying_profits_taxed
- reorg  payee.pure_equity_holding
- reorg  payee.registration_filing_compliant
- reorg  payee.residence_cert
- reorg  payee.substance_ruled_adequate
