# 问题单：K4-freetech-2024（模板 holding）

方案尚不能给出：下列数据或确认会改变所选方案或其保证税额。只需答这些；答不上请填 unknown（按最不利处理，不会补值）。
答复写进 `<案例名>.answers.json`：data（数值或 {"value", "source"}）、actions（yes / no / unknown）、rulings（yes / no / unknown）、library。

## CN

| 类型 | 地址 | 问题 | 取值 | 常见出处 | 影响 |
|---|---|---|---|---|---|
| 裁定 | `ULT.reorg_reasonable_commercial_purpose` | 是否已取得税务机关对以下事项的书面裁定或确认：重组是否具有合理商业目的、不以减少免除或推迟缴税为主要目的（59号第五条第（一）项）（ULT.reorg_reasonable_commercial_purpose） | 税务机关认定 | 重组说明 | 可使保证税额下降 1579435.00 |
| 裁定 | `ULT.reorg_wht_burden_unchanged` | 是否已取得税务机关对以下事项的书面裁定或确认：重组后以后该项股权转让所得的预提税负担是否不变（59号第七条第（一）项）（ULT.reorg_wht_burden_unchanged） | 税务机关认定 | 协定比对 | 可使保证税额下降 1579435.00 |
| 资料 | `calendar:CN:2024` | 库里缺 CN 2024 年的公众假期表（官方已公布），期限顺延需要它：请提供官方公布的假期清单 |  |  | — |

## HK

| 类型 | 地址 | 问题 | 取值 | 常见出处 | 影响 |
|---|---|---|---|---|---|
| 数据 | `ULT.pure_equity_holding` | 请提供：是否为纯股权持有实体（ULT.pure_equity_holding） | 是/否 | 经营范围与资产构成 | 可使保证税额下降 1579435.00 |
| 数据 | `ULT.substance_ruled_adequate` | 请提供：香港税务局是否已认定经济实质足够（ULT.substance_ruled_adequate） | 是/否 | 裁定书 | 可使保证税额下降 1579435.00 |
| 数据 | `flow:exit.deductible_at_payer` | 请提供：该笔支付在付款方是否可扣除（flow:exit.deductible_at_payer） | 是/否 | 付款方纳税申报 | 可使保证税额下降 1579435.00 |
| 数据 | `flow:exit.foreign_headline_rate` | 请提供：来源地法定税率（flow:exit.foreign_headline_rate） | % | 来源地税法；表单：hk.fsie.forms.birs19 · state three main jurisdictions where the；hk.fsie.forms.birs19 · state three main jurisdictions where the；hk.fsie.forms.birs19 · the applicable rate or the highest appli | 可使保证税额下降 1579435.00 |
| 数据 | `flow:exit.foreign_taxed` | 请提供：该所得在境外是否已纳税（flow:exit.foreign_taxed） | 是/否 | 境外完税凭证；表单：hk.fsie.forms.birs19 · whether the dividend is subject to a qua；hk.fsie.forms.birs19 · whether the equity interest disposal gai | 可使保证税额下降 1579435.00 |
| 数据 | `flow:exit.underlying_profits_taxed` | 请提供：股息所对应利润是否已纳税（flow:exit.underlying_profits_taxed） | 是/否 | 付款方纳税申报 | 可使保证税额下降 1579435.00 |
| 裁定 | `ULT.adequate_substance` | 是否已取得税务机关对以下事项的书面裁定或确认：在当地是否有足够的经济实质（人员、场所、开支）（ULT.adequate_substance） | 税务机关认定 | 经济实质说明材料 | 可使保证税额下降 1579435.00 |
| 裁定 | `ULT.no_main_purpose_of_tax_benefit` | 是否已取得税务机关对以下事项的书面裁定或确认：取得该所得是否不以获取税收利益为主要目的（ULT.no_main_purpose_of_tax_benefit） | 税务机关认定 | 商业目的说明 | 可使保证税额下降 1579435.00 |

## CN∩HK

| 类型 | 地址 | 问题 | 取值 | 常见出处 | 影响 |
|---|---|---|---|---|---|
| 数据 | `flow:exit~HOLD-CN.cost_basis` | 请提供：所转让资产（股权或 IP）的计税成本；IP 为尚未扣除的开支（内地为计税基础减已摊销后的净值）（flow:exit~HOLD-CN.cost_basis） | 金额 | 投资或购买凭证、无形资产摊销台账；表单：cn.sta.2019-16.a08 · 扣除额；hk.fsie.forms.birs19 · is there any sold movable or immovable p | 可使保证税额下降 4009335.00 |
| 数据 | `flow:exit~HOLD-HK.cost_basis` | 请提供：所转让资产（股权或 IP）的计税成本；IP 为尚未扣除的开支（内地为计税基础减已摊销后的净值）（flow:exit~HOLD-HK.cost_basis） | 金额 | 投资或购买凭证、无形资产摊销台账；表单：cn.sta.2019-16.a08 · 扣除额；hk.fsie.forms.birs19 · is there any sold movable or immovable p | 可使保证税额下降 3973785.50 |

## CN∩HK∩SG

| 类型 | 地址 | 问题 | 取值 | 常见出处 | 影响 |
|---|---|---|---|---|---|
| 必答（缺则税额无界） | `flow:reorg.amount` | 请提供：重组步骤的对价：ULT 把所持 OP 股权转给新控股公司的价格（按转让日市场价值）（flow:reorg.amount） | 金额 | 评估报告或股权转让协议；表单：cn.sta.2019-35.a01 · 14.享受协定待遇所得金额；cn.sta.2019-16.a08 · 合同总金额；cn.sta.2019-16.a08 · 本次申报收入 人民币金额 | 无界 |
| 数据 | `flow:exit~HOLD-SG.cost_basis` | 请提供：所转让资产（股权或 IP）的计税成本；IP 为尚未扣除的开支（内地为计税基础减已摊销后的净值）（flow:exit~HOLD-SG.cost_basis） | 金额 | 投资或购买凭证、无形资产摊销台账；表单：cn.sta.2019-16.a08 · 扣除额；hk.fsie.forms.birs19 · is there any sold movable or immovable p | 可使保证税额下降 4044884.50 |

候选结构 7 个；其中需要上面必答数据才能计算的 6 个。
