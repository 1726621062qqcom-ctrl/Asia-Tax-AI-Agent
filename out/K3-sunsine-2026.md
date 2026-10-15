# 问题单：K3-sunsine-2026（模板 holding）

方案尚不能给出：下列数据或确认会改变所选方案或其保证税额。只需答这些；答不上请填 unknown（按最不利处理，不会补值）。
答复写进 `<案例名>.answers.json`：data（数值或 {"value", "source"}）、actions（yes / no / unknown）、rulings（yes / no / unknown）、library。

## CN

| 类型 | 地址 | 问题 | 取值 | 常见出处 | 影响 |
|---|---|---|---|---|---|
| 数据 | `flow:up1.direct_payment` | 请提供：是否由被投资企业直接支付（flow:up1.direct_payment）——须与 `ULT.reasonable_commercial_purpose_absent` 同时成立才有影响 | 是/否 | 支付安排 | 可使保证税额下降 18000000.00 |
| 数据 | `flow:up1.reinvested_in_cn` | 请提供：分得利润是否在内地再投资（flow:up1.reinvested_in_cn）——须与 `ULT.reasonable_commercial_purpose_absent` 同时成立才有影响 | 是/否 | 再投资协议 | 可使保证税额下降 18000000.00 |
| 数据 | `flow:up1.reinvestment_form` | 请提供：再投资方式（flow:up1.reinvestment_form）——须与 `ULT.reasonable_commercial_purpose_absent` 同时成立才有影响 | 枚举 | 再投资协议 | 可使保证税额下降 18000000.00 |
| 数据 | `flow:up1.reinvestment_from_distributed_profit` | 请提供：再投资资金是否来自分得利润（flow:up1.reinvestment_from_distributed_profit）——须与 `ULT.reasonable_commercial_purpose_absent` 同时成立才有影响 | 是/否 | 资金流水 | 可使保证税额下降 18000000.00 |
| 裁定 | `ULT.reasonable_commercial_purpose_absent` | 是否已取得税务机关对以下事项的书面裁定或确认：安排是否缺乏合理商业目的（一般反避税）（ULT.reasonable_commercial_purpose_absent）——须与 `flow:up1.direct_payment` 同时成立才有影响 | 税务机关认定 | 商业目的说明 | 可使保证税额下降 18000000.00 |

## SG

| 类型 | 地址 | 问题 | 取值 | 常见出处 | 影响 |
|---|---|---|---|---|---|
| 数据 | `flow:up1.receipt_kind` | 请提供：境外所得的收取方式（汇入 / 视同汇入 / 未汇入）（flow:up1.receipt_kind） | 枚举 | 银行记录 | 可使保证税额下降 12600000.00 |
| 数据 | `flow:up2~HOLD-CN.foreign_taxed` | 请提供：该所得在境外是否已纳税（flow:up2~HOLD-CN.foreign_taxed） | 是/否 | 境外完税凭证；表单：sg.iras.forms.s13-12 · whether income tax has been paid in the ；sg.iras.forms.s13-12 · (please state the reasons below)；sg.iras.forms.s13-12 · whether income tax has been paid in this | 可使保证税额下降 12600000.00 |
| 数据 | `flow:up2~HOLD-CN.receipt_kind` | 请提供：境外所得的收取方式（汇入 / 视同汇入 / 未汇入）（flow:up2~HOLD-CN.receipt_kind） | 枚举 | 银行记录 | 可使保证税额下降 12600000.00 |
| 裁定 | `ULT.exemption_beneficial` | 是否已取得税务机关对以下事项的书面裁定或确认：适用境外所得豁免是否对纳税人有利（ULT.exemption_beneficial） | 税务机关认定 | 新加坡申报 | 可使保证税额下降 12600000.00 |
| 裁定 | `HOLD.income_sourced_in_sg` | 是否已取得税务机关对以下事项的书面裁定或确认：该所得是否源自新加坡（在新加坡经营的许可、融资业务所得）（HOLD.income_sourced_in_sg） | 税务机关认定 | 业务运作地点分析 | 可使保证税额下降 1800000.00 |

## CN∩HK∩SG

| 类型 | 地址 | 问题 | 取值 | 常见出处 | 影响 |
|---|---|---|---|---|---|
| 必答（缺则税额无界） | `flow:reorg.amount` | 请提供：重组步骤的对价：ULT 把所持 OP 股权转给新控股公司的价格（按转让日市场价值）（flow:reorg.amount） | 金额 | 评估报告或股权转让协议；表单：cn.sta.2019-35.a01 · 14.享受协定待遇所得金额；cn.sta.2019-16.a08 · 合同总金额；cn.sta.2019-16.a08 · 本次申报收入 人民币金额 | 无界 |

候选结构 16 个；其中需要上面必答数据才能计算的 12 个。
