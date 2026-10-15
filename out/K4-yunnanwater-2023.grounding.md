# 依据核对：K4-yunnanwater-2023

运行 20261012T204247-K4-yunnanwater-2023，版本 5832e6b4d381。规划器给出的是问卷（下面核对的是目前最优的候选）；核对 43 项：通过 23，说明 18，警示 2，失败 0。

**结论**：每一步都落到现行条文的原文；陈述的事实都附出处。

候选 {'HOLD': None, 'exit_route': 'DIRECT'}；保证税额 59400069.85，最好情形 148129.85；重算一致。

## 需要处理的

- 警示：exit/remit 期限按名义日期：库里缺 CN 2022 年的公众假期表
- 警示：unwind/remit 期限按名义日期：库里缺 CN 2022 年的公众假期表

## 税项（保证税额一端）

| 流 | 法域 | 税种 | 承担方 | 金额 | 规则 | 依据 |
|---|---|---|---|---|---|---|
| exit | CN | income | ULT | 29625970.00 | cn.wht.reduced、cn.gain.base、cn.indirect.gain.base | 通过 |
| exit | CN | income | ULT | 29625970.00 | cn.indirect.charge、cn.gain.base、cn.indirect.gain.base | 通过 |
| exit | CN | stamp | ULT | 148129.85 | cn.stamp.seller | 通过 |
| exit | CN | stamp | BUYER（集团外） | 148129.85 | cn.stamp.buyer | 通过 |
| unwind | CN | stamp | HOLD | 0.00 | cn.stamp.seller | 通过 |
| unwind | CN | stamp | ULT | 0.00 | cn.stamp.buyer | 通过 |

## 待机关认可的判断

| 事项 | 流 | 判断所引条款 | 规则 | 依据 | 先例（案例采集.md §5） |
|---|---|---|---|---|---|
| payee.no_reasonable_commercial_purpose | exit | cn.sta.2015-07#i3 | cn.indirect.charge | 通过 | 未被压住；成立最近的先例 CN-jiangyin-2026（还差 rcp_no_substance、rcp_value_from_cn；多出不利 rcp_some_services） |

## 期限与罚款

| 流 | 规则 | 依据 |
|---|---|---|
| exit | cn.wht.remit | 通过 |
| unwind | cn.wht.remit | 通过 |

## 问卷的每个问题

| 类别 | 问题 | 由哪条规则提出 | 依据 |
|---|---|---|---|
| blocking | flow:unwind.amount | data.amount | 说明 |
| blocking | flow:wind.amount | data.amount | 说明 |

## 规则依据（本方案用到的 7 条规则）

- **cn.gain.base**（A_TEXT，2022-11-03）通过
  - 参数 cn.wht.base_gain：uses = 1 bool；cn.law.eit#19（中华人民共和国企业所得税法 ）「转让财产所得，以收入全额减除财产净值后的余额为应纳税所得额」
  - 求值器出处 cn.law.eit#16：中华人民共和国企业所得税法 
  - 口径 D32：锚点 7/7 找到原文
- **cn.indirect.charge**（D_DISCRETION，2022-11-03）通过
  - 参数 cn.wht.rate：value = 10 %；cn.reg.eit#91（中华人民共和国企业所得税法实施条例 国务院令第512号）「减按10%的税率征收企业所得税」
  - 参数 cn.indirect.value_ratio：threshold = 75 %；cn.sta.2015-07#i4（国家税务总局关于非居民企业间接转让财产企业所得税若干问题的公告 国家税务总局公告2015年第7号）「境外企业股权75%以上价值直接或间接来自于中国应税财产」
  - 参数 cn.indirect.asset_or_income_ratio：threshold = 90 %；cn.sta.2015-07#i4（国家税务总局关于非居民企业间接转让财产企业所得税若干问题的公告 国家税务总局公告2015年第7号）「境外企业资产总额（不含现金）的90%以上直接或间接由在中国境内的投资构成」
  - 判断出处 cn.sta.2015-07#i3：国家税务总局关于非居民企业间接转让财产企业所得税若干问题的公告 国家税务总局公告2015年第7号
- **cn.indirect.gain.base**（A_TEXT，2022-11-03）通过
  - 求值器出处 cn.law.eit#16：中华人民共和国企业所得税法 
  - 口径 D32：锚点 7/7 找到原文
- **cn.stamp.buyer**（A_TEXT，2022-11-03）通过
  - 参数 cn.stamp.equity_rate：value = 0.05 %；cn.law.stamp.flk#20（中华人民共和国印花税法（国家法律法规数据库 PDF，含印花税税目税率表） 主席令第八十九号）「价款的万分之五」
  - 参数 cn.stamp.taxpayer_each_party：uses = 1 bool；cn.law.stamp.flk#1（中华人民共和国印花税法（国家法律法规数据库 PDF，含印花税税目税率表） 主席令第八十九号）「应当依照本法规定缴纳印花税」
  - 所依法律的施行条款 cn.law.stamp.flk#20：中华人民共和国印花税法（国家法律法规数据库 PDF，含印花税税目税率表） 主席令第八十九号
  - 口径 D19：锚点 12/12 找到原文
- **cn.stamp.seller**（A_TEXT，2022-11-03）通过
  - 参数 cn.stamp.equity_rate：value = 0.05 %；cn.law.stamp.flk#20（中华人民共和国印花税法（国家法律法规数据库 PDF，含印花税税目税率表） 主席令第八十九号）「价款的万分之五」
  - 参数 cn.stamp.taxpayer_each_party：uses = 1 bool；cn.law.stamp.flk#1（中华人民共和国印花税法（国家法律法规数据库 PDF，含印花税税目税率表） 主席令第八十九号）「应当依照本法规定缴纳印花税」
  - 所依法律的施行条款 cn.law.stamp.flk#20：中华人民共和国印花税法（国家法律法规数据库 PDF，含印花税税目税率表） 主席令第八十九号
  - 口径 D19：锚点 12/12 找到原文
- **cn.wht.reduced**（A_TEXT，2022-11-03）通过
  - 参数 cn.wht.rate：value = 10 %；cn.reg.eit#91（中华人民共和国企业所得税法实施条例 国务院令第512号）「减按10%的税率征收企业所得税」
- **cn.wht.remit**（A_TEXT，2022-11-03）通过
  - 参数 cn.wht.obligation_date：value = actual payment or date payable text；cn.sta.2017-37#i4（国家税务总局关于非居民企业所得税源泉扣缴有关问题的公告 国家税务总局公告2017年第37号）「扣缴义务发生之日为相关款项实际支付或者到期应支付之日」
  - 参数 cn.wht.remit_days：uses = 7 days；cn.sta.2017-37#i7（国家税务总局关于非居民企业所得税源泉扣缴有关问题的公告 国家税务总局公告2017年第37号）「扣缴义务人应当自扣缴义务发生之日起7日内向扣缴义务人所在地主管税务机关申…」
  - 参数 cn.wht.obligation_date_dividend：uses = actual payment text；cn.sta.2017-37#i7（国家税务总局关于非居民企业所得税源泉扣缴有关问题的公告 国家税务总局公告2017年第37号）「相关应纳税款扣缴义务发生之日为股息、红利等权益性投资收益实际支付之日」
  - 参数 cn.wht.fx_rule：uses = CNY central parity on the obligation date text；cn.sta.2017-37#i4（国家税务总局关于非居民企业所得税源泉扣缴有关问题的公告 国家税务总局公告2017年第37号）「应当按照扣缴义务发生之日人民币汇率中间价折合成人民币」
  - 参数 cn.time.holiday_roll：uses = 1 bool；cn.reg.tca#109（中华人民共和国税收征收管理法实施细则 国务院令第362号（2016年修订））「期限的最后一日是法定休假日的，以休假日期满的次日为期限的最后一日」
  - 参数 cn.time.long_holiday_days：uses = 3 days；cn.reg.tca#109（中华人民共和国税收征收管理法实施细则 国务院令第362号（2016年修订））「在期限内有连续３日以上法定休假日的，按休假日天数顺延」

## 事实来源（规则读到的事实，按流）

- exit：推导（facts.py） 10（authority_action、consideration、date_of_payment、intragroup_transfer、max_ratio_12m、prior_map_outcome…）；未定（按两端计） 5（cost_basis、foreign_tax_lower_than_cn、intragroup_reorg_ratio、later_cn_tax_not_reduced、reorg_consideration_in_equity）；未给出（规则判为不影响结果） 25（acquirer_chargeable_in_hk、assessment_notice_on、clawback_event_within_2y、cn_cost_basis、cn_income_ratio、determination_on…）；结构性缺省（按否） 1（shares_cancelled）；陈述（有出处） 5（cn_asset_ratio、cn_value_ratio、indirect_cn_target、limited_functions_and_risks、listed_market_trade）
- unwind：推导（facts.py） 5（consideration、date_of_payment、reorg_step、payee_in_source_jur、payee_resident_in_cn）；未给出（规则判为不影响结果） 13（cn_cost_basis、payable_on、remitted_on、reorg_acquired_ratio、reorg_buyer_resident_in_cn、reorg_commitment_3y…）；结构性缺省（按否） 1（shares_cancelled）；设计或模板设定 1（cost_basis）
- wind.div：推导（facts.py） 1（payee_in_source_jur）；未给出（规则判为不影响结果） 5（assessment_notice_on、determination_on、pure_equity_holding、registration_filing_compliant、substance_ruled_adequate）
- wind.gain：推导（facts.py） 2（intragroup_transfer、payee_in_source_jur）；未给出（规则判为不影响结果） 7（acquirer_chargeable_in_hk、assessment_notice_on、clawback_event_within_2y、determination_on、pure_equity_holding、registration_filing_compliant…）；设计或模板设定 2（consideration、cost_basis）

陈述的事实 5 个，附出处 5 个。
