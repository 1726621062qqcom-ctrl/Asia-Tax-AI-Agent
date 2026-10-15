# 问题单：K4-shuion-kic-2024（模板 holding）

方案尚不能给出：下列数据或确认会改变所选方案或其保证税额。只需答这些；答不上请填 unknown（按最不利处理，不会补值）。
答复写进 `<案例名>.answers.json`：data（数值或 {"value", "source"}）、actions（yes / no / unknown）、rulings（yes / no / unknown）、library。

## CN

| 类型 | 地址 | 问题 | 取值 | 常见出处 | 影响 |
|---|---|---|---|---|---|
| 数据 | `flow:exit~HOLD-CN.cost_basis` | 请提供：所转让资产（股权或 IP）的计税成本；IP 为尚未扣除的开支（内地为计税基础减已摊销后的净值）（flow:exit~HOLD-CN.cost_basis） | 金额 | 投资或购买凭证、无形资产摊销台账；表单：cn.sta.2019-16.a08 · 扣除额 | 可使保证税额下降 440220000.00 |
| 数据 | `flow:exit~HOLD-HK.cost_basis` | 请提供：所转让资产（股权或 IP）的计税成本；IP 为尚未扣除的开支（内地为计税基础减已摊销后的净值）（flow:exit~HOLD-HK.cost_basis） | 金额 | 投资或购买凭证、无形资产摊销台账；表单：cn.sta.2019-16.a08 · 扣除额 | 可使保证税额下降 440220000.00 |
| 裁定 | `ULT.reorg_reasonable_commercial_purpose` | 是否已取得税务机关对以下事项的书面裁定或确认：重组是否具有合理商业目的、不以减少免除或推迟缴税为主要目的（59号第五条第（一）项）（ULT.reorg_reasonable_commercial_purpose） | 税务机关认定 | 重组说明 | 可使保证税额下降 173420000.00 |
| 裁定 | `ULT.reorg_wht_burden_unchanged` | 是否已取得税务机关对以下事项的书面裁定或确认：重组后以后该项股权转让所得的预提税负担是否不变（59号第七条第（一）项）（ULT.reorg_wht_burden_unchanged） | 税务机关认定 | 协定比对 | 可使保证税额下降 173420000.00 |
| 资料 | `calendar:CN:2024` | 库里缺 CN 2024 年的公众假期表（官方已公布），期限顺延需要它：请提供官方公布的假期清单 |  |  | — |

## HK

| 类型 | 地址 | 问题 | 取值 | 常见出处 | 影响 |
|---|---|---|---|---|---|
| 数据 | `ULT.pure_equity_holding` | 请提供：是否为纯股权持有实体（ULT.pure_equity_holding） | 是/否 | 经营范围与资产构成 | 可使保证税额下降 173420000.00 |
| 数据 | `ULT.substance_ruled_adequate` | 请提供：香港税务局是否已认定经济实质足够（ULT.substance_ruled_adequate） | 是/否 | 裁定书 | 可使保证税额下降 173420000.00 |
| 数据 | `flow:exit.deductible_at_payer` | 请提供：该笔支付在付款方是否可扣除（flow:exit.deductible_at_payer） | 是/否 | 付款方纳税申报 | 可使保证税额下降 173420000.00 |
| 数据 | `flow:exit.foreign_headline_rate` | 请提供：来源地法定税率（flow:exit.foreign_headline_rate） | % | 来源地税法；表单：hk.fsie.forms.birs19 · state three main jurisdictions where the；hk.fsie.forms.birs19 · state three main jurisdictions where the；hk.fsie.forms.birs19 · the applicable rate or the highest appli | 可使保证税额下降 173420000.00 |
| 数据 | `flow:exit.foreign_taxed` | 请提供：该所得在境外是否已纳税（flow:exit.foreign_taxed） | 是/否 | 境外完税凭证；表单：hk.fsie.forms.birs19 · whether the dividend is subject to a qua；hk.fsie.forms.birs19 · whether the equity interest disposal gai | 可使保证税额下降 173420000.00 |
| 数据 | `flow:exit.receipt_kind` | 请提供：境外所得的收取方式（汇入 / 视同汇入 / 未汇入）（flow:exit.receipt_kind） | 枚举 | 银行记录 | 可使保证税额下降 173420000.00 |
| 数据 | `flow:exit.underlying_profits_taxed` | 请提供：股息所对应利润是否已纳税（flow:exit.underlying_profits_taxed） | 是/否 | 付款方纳税申报 | 可使保证税额下降 173420000.00 |
| 数据 | `flow:exit~HOLD-CN.foreign_taxed` | 请提供：该所得在境外是否已纳税（flow:exit~HOLD-CN.foreign_taxed） | 是/否 | 境外完税凭证；表单：hk.fsie.forms.birs19 · whether the dividend is subject to a qua；hk.fsie.forms.birs19 · whether the equity interest disposal gai | 可使保证税额下降 173420000.00 |
| 数据 | `flow:exit~HOLD-CN.receipt_kind` | 请提供：境外所得的收取方式（汇入 / 视同汇入 / 未汇入）（flow:exit~HOLD-CN.receipt_kind） | 枚举 | 银行记录 | 可使保证税额下降 173420000.00 |
| 数据 | `flow:exit~HOLD-CN.underlying_profits_taxed` | 请提供：股息所对应利润是否已纳税（flow:exit~HOLD-CN.underlying_profits_taxed） | 是/否 | 付款方纳税申报 | 可使保证税额下降 173420000.00 |
| 数据 | `flow:reorg~HOLD-HK.acquirer_chargeable_in_hk` | 请提供：受让方是否在香港就该所得纳税（flow:reorg~HOLD-HK.acquirer_chargeable_in_hk） | 是/否 | 受让方确认 | 可使保证税额下降 173420000.00 |
| 数据 | `flow:reorg~HOLD-HK.deductible_at_payer` | 请提供：该笔支付在付款方是否可扣除（flow:reorg~HOLD-HK.deductible_at_payer） | 是/否 | 付款方纳税申报 | 可使保证税额下降 173420000.00 |
| 数据 | `flow:reorg~HOLD-HK.foreign_headline_rate` | 请提供：来源地法定税率（flow:reorg~HOLD-HK.foreign_headline_rate） | % | 来源地税法；表单：hk.fsie.forms.birs19 · state three main jurisdictions where the；hk.fsie.forms.birs19 · state three main jurisdictions where the；hk.fsie.forms.birs19 · the applicable rate or the highest appli | 可使保证税额下降 173420000.00 |
| 数据 | `flow:reorg~HOLD-HK.foreign_taxed` | 请提供：该所得在境外是否已纳税（flow:reorg~HOLD-HK.foreign_taxed） | 是/否 | 境外完税凭证；表单：hk.fsie.forms.birs19 · whether the dividend is subject to a qua；hk.fsie.forms.birs19 · whether the equity interest disposal gai | 可使保证税额下降 173420000.00 |
| 数据 | `flow:reorg~HOLD-HK.receipt_kind` | 请提供：境外所得的收取方式（汇入 / 视同汇入 / 未汇入）（flow:reorg~HOLD-HK.receipt_kind） | 枚举 | 银行记录 | 可使保证税额下降 173420000.00 |
| 数据 | `flow:reorg~HOLD-HK.underlying_profits_taxed` | 请提供：股息所对应利润是否已纳税（flow:reorg~HOLD-HK.underlying_profits_taxed） | 是/否 | 付款方纳税申报 | 可使保证税额下降 173420000.00 |
| 数据 | `flow:reorg~HOLD-SG.acquirer_chargeable_in_hk` | 请提供：受让方是否在香港就该所得纳税（flow:reorg~HOLD-SG.acquirer_chargeable_in_hk） | 是/否 | 受让方确认 | 可使保证税额下降 173420000.00 |
| 数据 | `flow:reorg~HOLD-SG.deductible_at_payer` | 请提供：该笔支付在付款方是否可扣除（flow:reorg~HOLD-SG.deductible_at_payer） | 是/否 | 付款方纳税申报 | 可使保证税额下降 173420000.00 |
| 数据 | `flow:reorg~HOLD-SG.foreign_headline_rate` | 请提供：来源地法定税率（flow:reorg~HOLD-SG.foreign_headline_rate） | % | 来源地税法；表单：hk.fsie.forms.birs19 · state three main jurisdictions where the；hk.fsie.forms.birs19 · state three main jurisdictions where the；hk.fsie.forms.birs19 · the applicable rate or the highest appli | 可使保证税额下降 173420000.00 |
| 数据 | `flow:reorg~HOLD-SG.foreign_taxed` | 请提供：该所得在境外是否已纳税（flow:reorg~HOLD-SG.foreign_taxed） | 是/否 | 境外完税凭证；表单：hk.fsie.forms.birs19 · whether the dividend is subject to a qua；hk.fsie.forms.birs19 · whether the equity interest disposal gai | 可使保证税额下降 173420000.00 |
| 数据 | `flow:reorg~HOLD-SG.receipt_kind` | 请提供：境外所得的收取方式（汇入 / 视同汇入 / 未汇入）（flow:reorg~HOLD-SG.receipt_kind） | 枚举 | 银行记录 | 可使保证税额下降 173420000.00 |
| 数据 | `flow:reorg~HOLD-SG.underlying_profits_taxed` | 请提供：股息所对应利润是否已纳税（flow:reorg~HOLD-SG.underlying_profits_taxed） | 是/否 | 付款方纳税申报 | 可使保证税额下降 173420000.00 |
| 数据 | `ULT.sch17k_elected` | 请提供：是否选择香港附表17K（ULT.sch17k_elected） | 是/否 | 香港申报 | 可使保证税额下降 172086000.00 |
| 数据 | `flow:exit~HOLD-HK.held_as_trading_stock` | 请提供：该股权是否作为交易存货持有（flow:exit~HOLD-HK.held_as_trading_stock） | 是/否 | 会计处理 | 可使保证税额下降 172086000.00 |
| 裁定 | `ULT.adequate_substance` | 是否已取得税务机关对以下事项的书面裁定或确认：在当地是否有足够的经济实质（人员、场所、开支）（ULT.adequate_substance） | 税务机关认定 | 经济实质说明材料 | 可使保证税额下降 173420000.00 |
| 裁定 | `ULT.no_main_purpose_of_tax_benefit` | 是否已取得税务机关对以下事项的书面裁定或确认：取得该所得是否不以获取税收利益为主要目的（ULT.no_main_purpose_of_tax_benefit） | 税务机关认定 | 商业目的说明 | 可使保证税额下降 173420000.00 |
| 裁定 | `ULT.capital_asset` | 是否已取得税务机关对以下事项的书面裁定或确认：该资产是否为资本性资产（非经营性）（ULT.capital_asset） | 税务机关认定 | 持有目的与交易记录 | 可使保证税额下降 172086000.00 |

## SG

| 类型 | 地址 | 问题 | 取值 | 常见出处 | 影响 |
|---|---|---|---|---|---|
| 数据 | `flow:exit~HOLD-SG.foreign_headline_rate` | 请提供：来源地法定税率（flow:exit~HOLD-SG.foreign_headline_rate） | % | 来源地税法；表单：sg.iras.forms.s13-12 · Headline tax rate；sg.iras.forms.s13-12 · headline tax rate of this jurisdiction | 可使保证税额下降 173420000.00 |
| 数据 | `flow:exit~HOLD-SG.foreign_taxed` | 请提供：该所得在境外是否已纳税（flow:exit~HOLD-SG.foreign_taxed） | 是/否 | 境外完税凭证；表单：sg.iras.forms.s13-12 · whether income tax has been paid in the ；sg.iras.forms.s13-12 · (please state the reasons below)；sg.iras.forms.s13-12 · whether income tax has been paid in this | 可使保证税额下降 173420000.00 |
| 数据 | `ULT.fixed_place_in_sg` | 请提供：在新加坡是否有固定营业场所（ULT.fixed_place_in_sg） | 是/否 | 租约、员工与经营地点 | 可使保证税额下降 1334000.00 |
| 裁定 | `ULT.gain_is_capital_in_nature` | 是否已取得税务机关对以下事项的书面裁定或确认：处置收益是否属资本性质（ULT.gain_is_capital_in_nature） | 税务机关认定 | 持有目的与交易记录 | 可使保证税额下降 1334000.00 |

## CN∩HK

| 类型 | 地址 | 问题 | 取值 | 常见出处 | 影响 |
|---|---|---|---|---|---|
| 数据 | `flow:exit.cost_basis` | 请提供：所转让资产（股权或 IP）的计税成本；IP 为尚未扣除的开支（内地为计税基础减已摊销后的净值）（flow:exit.cost_basis） | 金额 | 投资或购买凭证、无形资产摊销台账；表单：cn.sta.2019-16.a08 · 扣除额；hk.fsie.forms.birs19 · is there any sold movable or immovable p | 可使保证税额下降 440220000.00 |
| 数据 | `ULT.residence_cert` | 请提供：是否持有收款方居民身份证明（覆盖支付年度）（ULT.residence_cert） | 是/否 | 税务居民身份证明；表单：cn.sta.2019-35.a01 · 13.非居民纳税人是否取得缔约对方税务主管当局开具的证明；cn.sta.2025-04.a02 · 申请目的：□享受协定待遇；hk.form.ir1313a · Latest Certificate of Resident Status is | 可使保证税额下降 173420000.00 |
| 数据 | `flow:reorg~HOLD-HK.cost_basis` | 请提供：所转让资产（股权或 IP）的计税成本；IP 为尚未扣除的开支（内地为计税基础减已摊销后的净值）（flow:reorg~HOLD-HK.cost_basis） | 金额 | 投资或购买凭证、无形资产摊销台账；表单：cn.sta.2019-16.a08 · 扣除额；hk.fsie.forms.birs19 · is there any sold movable or immovable p | 可使保证税额下降 173420000.00 |
| 数据 | `flow:reorg~HOLD-HK.listed_market_trade` | 请提供：是否在公开市场交易上市股份（flow:reorg~HOLD-HK.listed_market_trade） | 是/否 | 交易记录；表单：hk.form.bir51.s21 · Were the subject interests listed or tra | 可使保证税额下降 173420000.00 |
| 数据 | `flow:reorg~HOLD-SG.cost_basis` | 请提供：所转让资产（股权或 IP）的计税成本；IP 为尚未扣除的开支（内地为计税基础减已摊销后的净值）（flow:reorg~HOLD-SG.cost_basis） | 金额 | 投资或购买凭证、无形资产摊销台账；表单：cn.sta.2019-16.a08 · 扣除额；hk.fsie.forms.birs19 · is there any sold movable or immovable p | 可使保证税额下降 173420000.00 |
| 数据 | `flow:reorg~HOLD-SG.listed_market_trade` | 请提供：是否在公开市场交易上市股份（flow:reorg~HOLD-SG.listed_market_trade） | 是/否 | 交易记录；表单：hk.form.bir51.s21 · Were the subject interests listed or tra | 可使保证税额下降 173420000.00 |
| 裁定 | `ULT.ppt` | 是否已取得税务机关对以下事项的书面裁定或确认：主要目的测试：是否以获取协定优惠为主要目的之一（是则不给协定待遇）（ULT.ppt） | 税务机关认定 | 商业目的说明 | 可使保证税额下降 173420000.00 |

## CN∩HK∩SG

| 类型 | 地址 | 问题 | 取值 | 常见出处 | 影响 |
|---|---|---|---|---|---|
| 必答（缺则税额无界） | `flow:reorg.amount` | 请提供：重组步骤的对价：ULT 把所持 OP 股权转给新控股公司的价格（按转让日市场价值）（flow:reorg.amount） | 金额 | 评估报告或股权转让协议；表单：cn.sta.2019-35.a01 · 14.享受协定待遇所得金额；cn.sta.2019-16.a08 · 合同总金额；cn.sta.2019-16.a08 · 本次申报收入 人民币金额 | 无界 |
| 数据 | `flow:exit~HOLD-SG.cost_basis` | 请提供：所转让资产（股权或 IP）的计税成本；IP 为尚未扣除的开支（内地为计税基础减已摊销后的净值）（flow:exit~HOLD-SG.cost_basis） | 金额 | 投资或购买凭证、无形资产摊销台账；表单：cn.sta.2019-16.a08 · 扣除额；hk.fsie.forms.birs19 · is there any sold movable or immovable p | 可使保证税额下降 441554000.00 |

候选结构 7 个；其中需要上面必答数据才能计算的 6 个。
