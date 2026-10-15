# 问题单：holding_OPHK-ULCN_sparse_open_y1（模板 holding）

方案尚不能给出：下列数据或确认会改变所选方案或其保证税额。只需答这些；答不上请填 unknown（按最不利处理，不会补值）。
答复写进 `<案例名>.answers.json`：data（数值或 {"value", "source"}）、actions（yes / no / unknown）、rulings（yes / no / unknown）、library。

## CN

| 类型 | 地址 | 问题 | 取值 | 常见出处 | 影响 |
|---|---|---|---|---|---|
| 数据 | `OP.income_tax_other` | 请提供：该公司本年度在本案各笔流之外缴纳的所得税（其自身经营利润的所得税，未扣除本案所列付款；本案各笔流上的税由引擎自己计入，勿重复）（OP.income_tax_other） | 金额 | 纳税申报表与完税凭证 | 可使保证税额下降 1500000.00 |
| 数据 | `flow:exit.cost_basis` | 请提供：股权的计税成本（flow:exit.cost_basis） | 金额 | 投资时的出资或购买凭证；表单：cn.sta.2019-16.a08 · 扣除额；hk.fsie.forms.birs19 · is there any sold movable or immovable p | 可使保证税额下降 248.25 |
| 裁定 | `ULT.profits_not_mainly_active` | 是否已取得税务机关对以下事项的书面裁定或确认：受控外国企业利润是否主要不是积极经营所得（ULT.profits_not_mainly_active） | 税务机关认定 | 外国企业收入构成 | 可使保证税额下降 1499750.00 |
| 裁定 | `ULT.retention_without_reasonable_business_need` | 是否已取得税务机关对以下事项的书面裁定或确认：利润不分配是否缺乏合理经营需要（ULT.retention_without_reasonable_business_need） | 税务机关认定 | 利润留存用途说明 | 可使保证税额下降 1499750.00 |

## HK

| 类型 | 地址 | 问题 | 取值 | 常见出处 | 影响 |
|---|---|---|---|---|---|
| 必答（缺则税额无界） | `HOLD.globe_income` | 请提供：支柱二意义下该成员实体的GloBE所得（股息和持股10%以上股权处置利得一般不计入）（HOLD.globe_income） | 金额 | 集团支柱二计算底稿 | 无界 |

候选结构 28 个；其中需要上面必答数据才能计算的 16 个。
