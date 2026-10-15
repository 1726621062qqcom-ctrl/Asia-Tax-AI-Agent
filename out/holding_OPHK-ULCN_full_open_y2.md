# 问题单：holding_OPHK-ULCN_full_open_y2（模板 holding）

方案尚不能给出：下列数据或确认会改变所选方案或其保证税额。只需答这些；答不上请填 unknown（按最不利处理，不会补值）。
答复写进 `<案例名>.answers.json`：data（数值或 {"value", "source"}）、actions（yes / no / unknown）、rulings（yes / no / unknown）、library。

## HK

| 类型 | 地址 | 问题 | 取值 | 常见出处 | 影响 |
|---|---|---|---|---|---|
| 数据 | `HOLD.pure_equity_holding` | 请提供：是否为纯股权持有实体（HOLD.pure_equity_holding） | 是/否 | 经营范围与资产构成 | 可使保证税额下降 431.44 |
| 数据 | `HOLD.sch17k_elected` | 请提供：是否选择香港附表17K（HOLD.sch17k_elected） | 是/否 | 香港申报 | 可使保证税额下降 431.44 |
| 数据 | `HOLD.substance_ruled_adequate` | 请提供：香港税务局是否已认定经济实质足够（HOLD.substance_ruled_adequate） | 是/否 | 裁定书 | 可使保证税额下降 431.44 |
| 数据 | `flow:exit.held_as_trading_stock` | 请提供：该股权是否作为交易存货持有（flow:exit.held_as_trading_stock） | 是/否 | 会计处理 | 可使保证税额下降 431.44 |
| 数据 | `HOLD.lender_interest_taxable_in_hk` | 请提供：贷款方的利息是否在香港纳税（HOLD.lender_interest_taxable_in_hk） | 是/否 | 贷款方确认 | 可使保证税额下降 14.73 |
| 裁定 | `HOLD.adequate_substance` | 是否已取得税务机关对以下事项的书面裁定或确认：在当地是否有足够的经济实质（人员、场所、开支）（HOLD.adequate_substance） | 税务机关认定 | 经济实质说明材料 | 可使保证税额下降 431.44 |
| 裁定 | `HOLD.capital_asset` | 是否已取得税务机关对以下事项的书面裁定或确认：该资产是否为资本性资产（非经营性）（HOLD.capital_asset） | 税务机关认定 | 持有目的与交易记录 | 可使保证税额下降 431.44 |
| 裁定 | `HOLD.no_main_purpose_of_tax_benefit` | 是否已取得税务机关对以下事项的书面裁定或确认：取得该所得是否不以获取税收利益为主要目的（HOLD.no_main_purpose_of_tax_benefit） | 税务机关认定 | 商业目的说明 | 可使保证税额下降 431.44 |
| 裁定 | `HOLD.profits_arise_in_hk` | 是否已取得税务机关对以下事项的书面裁定或确认：该利润是否产生于香港（HOLD.profits_arise_in_hk） | 税务机关认定 | 业务运作地点分析 | 可使保证税额下降 183.74 |
| 裁定 | `OP.incurred_in_production_of_profits` | 是否已取得税务机关对以下事项的书面裁定或确认：该支出是否为产生应评税利润而发生（OP.incurred_in_production_of_profits） | 税务机关认定 | 支出用途证明 | 可使保证税额下降 14.73 |

## SG

| 类型 | 地址 | 问题 | 取值 | 常见出处 | 影响 |
|---|---|---|---|---|---|
| 必答（缺则税额无界） | `HOLD.globe_income` | 请提供：支柱二意义下该成员实体的GloBE所得（股息和持股10%以上股权处置利得一般不计入）（HOLD.globe_income） | 金额 | 集团支柱二计算底稿 | 无界 |
| 数据 | `HOLD.ftc_pooling_election` | 请提供：是否选择新加坡境外税收抵免汇总法（HOLD.ftc_pooling_election） | 是/否 | 新加坡纳税申报表 | 可使保证税额下降 184.92 |
| 裁定 | `HOLD.exemption_beneficial` | 是否已取得税务机关对以下事项的书面裁定或确认：适用境外所得豁免是否对纳税人有利（HOLD.exemption_beneficial） | 税务机关认定 | 新加坡申报 | 可使保证税额下降 186.44 |

## CN∩HK

| 类型 | 地址 | 问题 | 取值 | 常见出处 | 影响 |
|---|---|---|---|---|---|
| 数据 | `flow:exit.cost_basis` | 请提供：股权的计税成本（flow:exit.cost_basis） | 金额 | 投资时的出资或购买凭证；表单：cn.sta.2019-16.a08 · 扣除额；hk.fsie.forms.birs19 · is there any sold movable or immovable p | 可使保证税额下降 520.36 |

候选结构 28 个；其中需要上面必答数据才能计算的 16 个。
