# 金额扫档：K3-sunsine-2026

按合成值缩放：roles.ULT.attrs.group_revenue_eur=467136346.12、event.dividend=180000000.0。

| 倍数 | 结果 | 选中或领先的结构 | 保证税额 | 下界 | 现有结构的保证税额 | 问题数 |
|---|---|---|---|---|---|---|
| ×0.5 | 问卷 | {'HOLD': 'SG', 'financing': 'EQUITY', 'payment': False} | 9000000.0 | 0.0 | 15300000.0 | 11 |
| ×1 | 问卷 | {'HOLD': 'SG', 'financing': 'EQUITY', 'payment': False} | 18000000.0 | 0.0 | 30600000.0 | 11 |
| ×2 | 问卷 | {'HOLD': 'SG', 'financing': 'EQUITY', 'payment': False} | 36000000.0 | 0.0 | 61200000.0 | 3 |

**变化**：×2：问卷多出 OP.globe_income、ULT.globe_income；少了 HOLD.income_sourced_in_sg、ULT.exemption_beneficial、ULT.reasonable_commercial_purpose_absent、flow:up1.direct_payment、flow:up1.receipt_kind、flow:up1.reinvested_in_cn、flow:up1.reinvestment_form、flow:up1.reinvestment_from_distributed_profit、flow:up2~HOLD-CN.foreign_taxed、flow:up2~HOLD-CN.receipt_kind
