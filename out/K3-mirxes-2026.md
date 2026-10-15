# 问题单：K3-mirxes-2026（模板 holding）

方案尚不能给出：下列数据或确认会改变所选方案或其保证税额。只需答这些；答不上请填 unknown（按最不利处理，不会补值）。
答复写进 `<案例名>.answers.json`：data（数值或 {"value", "source"}）、actions（yes / no / unknown）、rulings（yes / no / unknown）、library。

## SG

| 类型 | 地址 | 问题 | 取值 | 常见出处 | 影响 |
|---|---|---|---|---|---|
| 数据 | `flow:up1.receipt_kind` | 请提供：境外所得的收取方式（汇入 / 视同汇入 / 未汇入）（flow:up1.receipt_kind） | 枚举 | 银行记录 | 可使保证税额下降 700000.00 |
| 裁定 | `ULT.exemption_beneficial` | 是否已取得税务机关对以下事项的书面裁定或确认：适用境外所得豁免是否对纳税人有利（ULT.exemption_beneficial） | 税务机关认定 | 新加坡申报 | 可使保证税额下降 700000.00 |

候选结构 16 个；其中需要上面必答数据才能计算的 0 个。
