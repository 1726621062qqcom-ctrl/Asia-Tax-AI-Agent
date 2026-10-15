# 依据核对：gold_C

运行 20261014T173552-gold_C，版本 5501a0239aac。规划器给出的是问卷（下面核对的是目前最优的候选）；核对 46 项：通过 39，说明 6，警示 1，失败 0。

**结论**：每一步都落到现行条文的原文；陈述的事实未附出处（0/10）。

候选 {'IPCO': None, 'payment': False, 'ip_transfer': 'MARKET'}；保证税额 63.74，最好情形 -11.92；重算一致。

## 需要处理的

- 警示：gold_C 案例陈述的事实 10 个，附出处的 0 个（案例文件没有 provenance，见 案例采集.md §4.2）

## 税项（保证税额一端）

| 流 | 法域 | 税种 | 承担方 | 金额 | 规则 | 依据 |
|---|---|---|---|---|---|---|
| iptx | CN | vat | IPCO | 24.00 | cn.vat.law.ip | 通过 |
| iptx | CN | stamp | IPCO | 0.12 | cn.stamp.ip.seller | 通过 |
| iptx | CN | stamp | OP | 0.12 | cn.stamp.ip.buyer | 通过 |
| iptx | CN | income | IPCO | 30.00 | cn.ip.wht | 通过 |
| iptx | HK | income | IPCO | 19.50 | hk.ip.onshore、hk.ftc.dta | 通过 |
| iptx | CN | income | OP | -10.00 | cn.ip.amortization、cn.ip.amortization.horizon、cn.reorg.asset_transfer.basis | 通过 |

## 方案动作

| 动作 | 依据所在的规则 | 依据 |
|---|---|---|
| flow:iptx.input_vat_documents_kept:is_true | cn.vat.law.input_credit | 通过 |
| flow:iptx.vat_tech_recognized:is_true | cn.vat.law.ip | 通过 |

## 待机关认可的判断

| 事项 | 流 | 判断所引条款 | 规则 | 依据 | 先例（案例采集.md §5） |
|---|---|---|---|---|---|
| flow.ip_transfer_gain_sourced_in_cn | iptx | cn.reg.eit#7 | cn.ip.wht | 通过 | 无先例卡 |
| flow.tech_recognition_open_to_foreign_seller | iptx | cn.cs.2026-10#i2 | cn.vat.law.ip | 通过 | 无先例卡 |
| flow.ip_gain_sourced_in_hk | iptx | hk.cap112.en#s14 | hk.ip.fsie | 通过 | 无先例卡 |
| flow.ip_gain_sourced_in_hk | iptx | hk.cap112.en#s14 | hk.ip.onshore | 通过 | 无先例卡 |
| flow.ip_held_as_capital_asset | iptx | hk.cap112.en#s14 | hk.ip.onshore | 通过 | 无先例卡 |

## 期限与罚款

| 流 | 规则 | 依据 |
|---|---|---|
| iptx | cn.wht.remit | 通过 |

## 问卷的每个问题

| 类别 | 问题 | 由哪条规则提出 | 依据 |
|---|---|---|---|
| blocking | group.group_revenue_eur | data.p2_income | 通过 |

## 规则依据（本方案用到的 14 条规则）

- **cn.ip.amortization**（A_TEXT，2026-03-31）通过
  - 参数 cn.eit.rate：value = 25 %；cn.law.eit#4（中华人民共和国企业所得税法 ）「企业所得税的税率为25％」
  - 参数 cn.deduct.general：uses = 1 bool；cn.law.eit#8（中华人民共和国企业所得税法 ）「企业实际发生的与取得收入有关的、合理的支出，包括成本、费用、税金、损失和…」
  - 参数 cn.eit.rate_entity：uses = 1 bool；cn.law.eit#28（中华人民共和国企业所得税法 ）「国家需要重点扶持的高新技术企业，减按15％的税率征收企业所得税」
  - 口径 D22：锚点 16/16 找到原文
- **cn.ip.amortization.horizon**（A_TEXT，2026-03-31）通过
  - 参数 cn.ip.amortization_years_min：uses = 10 years；cn.reg.eit#67（中华人民共和国企业所得税法实施条例 国务院令第512号）「无形资产的摊销年限不得低于10年」
  - 参数 cn.ip.amortization_agreed_life：uses = 1 bool；cn.reg.eit#67（中华人民共和国企业所得税法实施条例 国务院令第512号）「作为投资或者受让的无形资产，有关法律规定或者合同约定了使用年限的，可以按…」
  - 求值器出处 cn.reg.eit#67：中华人民共和国企业所得税法实施条例 国务院令第512号
  - 口径 D22：锚点 16/16 找到原文
- **cn.ip.wht**（D_DISCRETION，2026-03-31）通过
  - 参数 cn.wht.rate：value = 10 %；cn.reg.eit#91（中华人民共和国企业所得税法实施条例 国务院令第512号）「减按10%的税率征收企业所得税」
  - 判断出处 cn.reg.eit#7：中华人民共和国企业所得税法实施条例 国务院令第512号
  - 参数 cn.eit.rate_nonresident_statutory：uses = 20 %；cn.law.eit#4（中华人民共和国企业所得税法 ）「非居民企业取得本法第三条第三款规定的所得，适用税率为20％」
  - 参数 cn.ip.nonresident_gain_base：uses = 1 bool；cn.law.eit#19（中华人民共和国企业所得税法 ）「转让财产所得，以收入全额减除财产净值后的余额为应纳税所得额」
  - 参数 cn.ip.source_other_income：uses = 1 bool；cn.reg.eit#7（中华人民共和国企业所得税法实施条例 国务院令第512号）「其他所得，由国务院财政、税务主管部门确定」
  - 参数 cn.ip.net_value：uses = 1 bool；cn.reg.eit#74（中华人民共和国企业所得税法实施条例 国务院令第512号）「是指有关资产、财产的计税基础减除已经按照规定扣除的折旧、折耗、摊销、准备…」
  - 求值器出处 cn.law.eit#19：中华人民共和国企业所得税法 
  - 口径 D22：锚点 16/16 找到原文
- **cn.reorg.asset_transfer.basis**（A_TEXT，2026-03-31）通过
  - 参数 cn.reorg.transfer_basis：value = 1 bool；cn.sta.2015-40#i3（国家税务总局关于资产（股权）划转企业所得税征管问题的公告 国家税务总局公告2015年第40号）「应按被划转资产的原计税基础计算折旧扣除或摊销」
  - 参数 cn.vat.law.deemed_sale_market_value：uses = 1 bool；cn.law.vat#19（中华人民共和国增值税法 ）「发生本法第五条规定的视同应税交易以及销售额为非货币形式的，纳税人应当按照…」
  - 求值器出处 cn.sta.2015-40#i3：国家税务总局关于资产（股权）划转企业所得税征管问题的公告 国家税务总局公告2015年第40号
  - 口径 D18：锚点 10/10 找到原文
  - 口径 D28：锚点 5/5 找到原文
- **cn.stamp.ip.buyer**（A_TEXT，2026-03-31）通过
  - 参数 cn.stamp.ip_rate：value = 0.03 %；cn.law.stamp.flk#20（中华人民共和国印花税法（国家法律法规数据库 PDF，含印花税税目税率表） 主席令第八十九号）「商标专用权、著作权、专利权、专有技术使用权转让书据价款的万分之三」
  - 参数 cn.stamp.taxpayer_each_party：threshold = 1 bool；cn.law.stamp.flk#1（中华人民共和国印花税法（国家法律法规数据库 PDF，含印花税税目税率表） 主席令第八十九号）「应当依照本法规定缴纳印花税」
  - 参数 cn.stamp.abroad_used_in_cn：threshold = 1 bool；cn.law.stamp.flk#1（中华人民共和国印花税法（国家法律法规数据库 PDF，含印花税税目税率表） 主席令第八十九号）「在中华人民共和国境外书立在境内使用的应税凭证的单位和个人，应当依照本法规…」
  - 参数 cn.stamp.unstated_amount_market_price：uses = 1 bool；cn.law.stamp.flk#6（中华人民共和国印花税法（国家法律法规数据库 PDF，含印花税税目税率表） 主席令第八十九号）「书立合同、产权转移书据时的市场价格确定」
  - 参数 cn.stamp.restructuring_exemption_scope：uses = 1 bool；cn.cs.2024-14#i3（财政部 税务总局关于企业改制重组及事业单位改制有关印花税政策的公告 财政部 税务总局公告2024年第14号）「对企业改制、合并、分立、破产清算以及事业单位改制书立的产权转移书据，免征…」
  - 所依法律的施行条款 cn.law.stamp.flk#20：中华人民共和国印花税法（国家法律法规数据库 PDF，含印花税税目税率表） 主席令第八十九号
  - 口径 D19：锚点 12/12 找到原文
  - 口径 D22：锚点 16/16 找到原文
- **cn.stamp.ip.seller**（A_TEXT，2026-03-31）通过
  - 参数 cn.stamp.ip_rate：value = 0.03 %；cn.law.stamp.flk#20（中华人民共和国印花税法（国家法律法规数据库 PDF，含印花税税目税率表） 主席令第八十九号）「商标专用权、著作权、专利权、专有技术使用权转让书据价款的万分之三」
  - 参数 cn.stamp.taxpayer_each_party：threshold = 1 bool；cn.law.stamp.flk#1（中华人民共和国印花税法（国家法律法规数据库 PDF，含印花税税目税率表） 主席令第八十九号）「应当依照本法规定缴纳印花税」
  - 参数 cn.stamp.abroad_used_in_cn：threshold = 1 bool；cn.law.stamp.flk#1（中华人民共和国印花税法（国家法律法规数据库 PDF，含印花税税目税率表） 主席令第八十九号）「在中华人民共和国境外书立在境内使用的应税凭证的单位和个人，应当依照本法规…」
  - 参数 cn.stamp.unstated_amount_market_price：uses = 1 bool；cn.law.stamp.flk#6（中华人民共和国印花税法（国家法律法规数据库 PDF，含印花税税目税率表） 主席令第八十九号）「书立合同、产权转移书据时的市场价格确定」
  - 参数 cn.stamp.restructuring_exemption_scope：uses = 1 bool；cn.cs.2024-14#i3（财政部 税务总局关于企业改制重组及事业单位改制有关印花税政策的公告 财政部 税务总局公告2024年第14号）「对企业改制、合并、分立、破产清算以及事业单位改制书立的产权转移书据，免征…」
  - 所依法律的施行条款 cn.law.stamp.flk#20：中华人民共和国印花税法（国家法律法规数据库 PDF，含印花税税目税率表） 主席令第八十九号
  - 口径 D19：锚点 12/12 找到原文
  - 口径 D22：锚点 16/16 找到原文
- **cn.surcharge.local_edu**（A_TEXT，2026-03-31）通过
  - 参数 cn.local_edu.rate：value = 2 %；cn.cz.2010-98#i2（财政部关于统一地方教育附加政策有关问题的通知 财综〔2010〕98号）「实际缴纳的增值税、营业税和消费税税额的2%」
  - 参数 cn.local_edu.base_as_ucmt：uses = 1 bool；cn.cs.2021-28#i2（财政部 税务总局关于城市维护建设税计税依据确定办法等事项的公告 财政部 税务总局公告2021年第28号）「教育费附加、地方教育附加计征依据与城市维护建设税计税依据一致」
  - 求值器出处 cn.cz.2010-98#i2：财政部关于统一地方教育附加政策有关问题的通知 财综〔2010〕98号
  - 求值器出处 cn.cs.2021-28#i2：财政部 税务总局关于城市维护建设税计税依据确定办法等事项的公告 财政部 税务总局公告2021年第28号
  - 所依法律的施行条款 cn.law.ucmt#11：中华人民共和国城市维护建设税法 主席令第五十一号
- **cn.surcharge.ucmt**（A_TEXT，2026-03-31）通过
  - 参数 cn.ucmt.rate_urban：value = 7 %；cn.law.ucmt#4（中华人民共和国城市维护建设税法 主席令第五十一号）「纳税人所在地在市区的，税率为百分之七」
  - 参数 cn.ucmt.base_vat_paid：uses = 1 bool；cn.law.ucmt#2（中华人民共和国城市维护建设税法 主席令第五十一号）「城市维护建设税以纳税人依法实际缴纳的增值税、消费税税额为计税依据」
  - 参数 cn.ucmt.no_foreign_services：uses = 1 bool；cn.law.ucmt#3（中华人民共和国城市维护建设税法 主席令第五十一号）「对进口货物或者境外单位和个人向境内销售劳务、服务、无形资产缴纳的增值税、…」
  - 参数 cn.ucmt.rate_county：uses = 5 %；cn.law.ucmt#4（中华人民共和国城市维护建设税法 主席令第五十一号）「纳税人所在地在县城、镇的，税率为百分之五」
  - 参数 cn.ucmt.rate_other：uses = 1 %；cn.law.ucmt#4（中华人民共和国城市维护建设税法 主席令第五十一号）「纳税人所在地不在市区、县城或者镇的，税率为百分之一」
  - 参数 cn.ucmt.location_of_taxpayer：uses = 1 bool；cn.law.ucmt#4（中华人民共和国城市维护建设税法 主席令第五十一号）「纳税人所在地，是指纳税人住所地或者与纳税人生产经营活动相关的其他地点，具…」
  - 求值器出处 cn.law.ucmt#2：中华人民共和国城市维护建设税法 主席令第五十一号
  - 求值器出处 cn.law.ucmt#3：中华人民共和国城市维护建设税法 主席令第五十一号
  - 求值器出处 cn.law.ucmt#4：中华人民共和国城市维护建设税法 主席令第五十一号
  - 求值器出处 cn.cs.2021-28#i1：财政部 税务总局关于城市维护建设税计税依据确定办法等事项的公告 财政部 税务总局公告2021年第28号
  - 所依法律的施行条款 cn.law.ucmt#11：中华人民共和国城市维护建设税法 主席令第五十一号
- **cn.vat.law.input_credit**（A_TEXT，2026-03-31）通过
  - 参数 cn.vat.law.rate_services：value = 6 %；cn.law.vat#10（中华人民共和国增值税法 ）「纳税人销售服务、无形资产，除本条第一项、第二项、第五项规定外，税率为百分…」
  - 参数 cn.vat.law.input_credit：threshold = 1 bool；cn.reg.vat#12（中华人民共和国增值税法实施条例（国务院令第826号） 国务院令第826号）「自境外单位或者个人购进服务、无形资产或者境内不动产取得的完税凭证上列明的…」
  - 参数 cn.vat.law.input_documents：threshold = 1 bool；cn.cs.2026-input#i1（财政部 税务总局关于增值税进项税额抵扣等有关事项的公告 ）「一般纳税人凭完税凭证抵扣进项税额的，应当具备书面合同、付款证明和境外单位…」
  - 参数 cn.vat.law.input_credit_invoice：uses = 1 bool；cn.reg.vat#12（中华人民共和国增值税法实施条例（国务院令第826号） 国务院令第826号）「从销售方取得的增值税专用发票上列明的增值税税额」
  - 所依法律的施行条款 cn.law.vat#38：中华人民共和国增值税法 
  - 口径 D23：锚点 6/6 找到原文
- **cn.vat.law.ip**（D_DISCRETION，2026-03-31）通过
  - 参数 cn.vat.law.rate_services：value = 6 %；cn.law.vat#10（中华人民共和国增值税法 ）「纳税人销售服务、无形资产，除本条第一项、第二项、第五项规定外，税率为百分…」
  - 参数 cn.vat.tech_kinds：threshold = PATENT;KNOW_HOW enum；cn.cs.2026-09.a02#p19（销售服务、无形资产、不动产注释.pdf 财政部 税务总局公告2026年第9号）「技术，包括专利技术和非专利技术」
  - 参数 cn.vat.tech_recognition：threshold = 1 bool；cn.cs.2026-10#i2（财政部 税务总局关于增值税法施行后增值税优惠政策衔接事项的公告（财政部 税务总局公告2026年第10号） 财政部 税务总局公告2026年第10号）「到纳税人所在地省级科技、工信主管部门进行认定」
  - 判断出处 cn.cs.2026-10#i2：财政部 税务总局关于增值税法施行后增值税优惠政策衔接事项的公告（财政部 税务总局公告2026年第10号） 财政部 税务总局公告2026年第10号
  - 参数 cn.vat.law.withholding_agent：uses = 1 bool；cn.law.vat#15（中华人民共和国增值税法 ）「境外单位和个人在境内发生应税交易，以购买方为扣缴义务人」
  - 参数 cn.vat.law.withheld_on_sales：uses = 1 bool；cn.law.vat#15（中华人民共和国增值税法 ）「按照销售额乘以税率计算应扣缴税额」
  - 参数 cn.vat.law.inclusive_price：uses = 1 bool；cn.reg.vat#16（中华人民共和国增值税法实施条例（国务院令第826号） 国务院令第826号）「一般计税方法的销售额＝含税销售额÷（1＋税率）」
  - 参数 cn.vat.law.taxable_in_cn：uses = 1 bool；cn.law.vat#4（中华人民共和国增值税法 ）「除本条第二项、第三项规定外，销售服务、无形资产的，服务、无形资产在境内消…」
  - 参数 cn.vat.tech_transfer_exempt：uses = 1 bool；cn.cs.2026-10#i2（财政部 税务总局关于增值税法施行后增值税优惠政策衔接事项的公告（财政部 税务总局公告2026年第10号） 财政部 税务总局公告2026年第10号）「纳税人提供技术转让、技术开发和与之相关的技术咨询、技术服务」
  - 所依法律的施行条款 cn.law.vat#38：中华人民共和国增值税法 
  - 口径 D22：锚点 16/16 找到原文
  - 口径 D23：锚点 6/6 找到原文
- **cn.wht.remit**（A_TEXT，2026-03-31）通过
  - 参数 cn.wht.obligation_date：value = actual payment or date payable text；cn.sta.2017-37#i4（国家税务总局关于非居民企业所得税源泉扣缴有关问题的公告 国家税务总局公告2017年第37号）「扣缴义务发生之日为相关款项实际支付或者到期应支付之日」
  - 参数 cn.wht.remit_days：uses = 7 days；cn.sta.2017-37#i7（国家税务总局关于非居民企业所得税源泉扣缴有关问题的公告 国家税务总局公告2017年第37号）「扣缴义务人应当自扣缴义务发生之日起7日内向扣缴义务人所在地主管税务机关申…」
  - 参数 cn.wht.obligation_date_dividend：uses = actual payment text；cn.sta.2017-37#i7（国家税务总局关于非居民企业所得税源泉扣缴有关问题的公告 国家税务总局公告2017年第37号）「相关应纳税款扣缴义务发生之日为股息、红利等权益性投资收益实际支付之日」
  - 参数 cn.wht.fx_rule：uses = CNY central parity on the obligation date text；cn.sta.2017-37#i4（国家税务总局关于非居民企业所得税源泉扣缴有关问题的公告 国家税务总局公告2017年第37号）「应当按照扣缴义务发生之日人民币汇率中间价折合成人民币」
  - 参数 cn.time.holiday_roll：uses = 1 bool；cn.reg.tca#109（中华人民共和国税收征收管理法实施细则 国务院令第362号（2016年修订））「期限的最后一日是法定休假日的，以休假日期满的次日为期限的最后一日」
  - 参数 cn.time.long_holiday_days：uses = 3 days；cn.reg.tca#109（中华人民共和国税收征收管理法实施细则 国务院令第362号（2016年修订））「在期限内有连续３日以上法定休假日的，按休假日天数顺延」
- **hk.ftc.dta**（A_TEXT，2026-03-31）通过
  - 参数 hk.ftc.credit_limit：uses = hk_tax_on_same_income_at_average_rate enum；hk.cap112.en#s50（Inland Revenue Ordinance (Cap. 112) - whole chapter, English Cap. 112）「The credit shall not exceed the amou…」
  - 参数 hk.fsie.intragroup_foreign_tax：uses = 1 bool；hk.cap112.en#s15OA（Inland Revenue Ordinance (Cap. 112) - whole chapter, English Cap. 112）「that foreign tax is, for the purpose…」
- **hk.ip.fsie**（D_DISCRETION，2026-03-31）通过
  - 参数 hk.profits.rate_corp：value = 16.5 %；hk.cap112.en#sch8B（Inland Revenue Ordinance (Cap. 112) - whole chapter, English Cap. 112）「at the rate of 16.5% on any part of …」
  - 参数 hk.fsie.mne_entity_only：threshold = 1 bool；hk.cap112.en#s15I（Inland Revenue Ordinance (Cap. 112) - whole chapter, English Cap. 112）「is received in Hong Kong by an MNE e…」
  - 参数 hk.fsie.receipt_kinds：threshold = REMITTED;DEBT_SETTLED;MOVABLE_PROPERTY enum；hk.cap112.en#s15H（Inland Revenue Ordinance (Cap. 112) - whole chapter, English Cap. 112）「the sum is remitted to, or is transm…」
  - 判断出处 hk.cap112.en#s14：Inland Revenue Ordinance (Cap. 112) - whole chapter, English Cap. 112
  - 参数 hk.fsie.ip_disposal_gain：uses = 1 bool；hk.cap112.en#s15H（Inland Revenue Ordinance (Cap. 112) - whole chapter, English Cap. 112）「means any gain or profit derived fro…」
  - 参数 hk.fsie.ip_disposal_not_capital：uses = 1 bool；hk.cap112.en#s15I（Inland Revenue Ordinance (Cap. 112) - whole chapter, English Cap. 112）「is to be regarded as not arising fro…」
  - 参数 hk.fsie.qualifying_ip_kinds：uses = PATENT;SOFTWARE_COPYRIGHT enum；hk.cap112.en#sch17FC（Inland Revenue Ordinance (Cap. 112) - whole chapter, English Cap. 112）「a copyright subsisting in software u…」
  - 参数 hk.fsie.nexus_uplift：uses = 130 %；hk.cap112.en#sch17FC（Inland Revenue Ordinance (Cap. 112) - whole chapter, English Cap. 112）「F = QE × 130% QE + NE」
  - 参数 hk.fsie.nexus_cap：uses = 100 %；hk.cap112.en#sch17FC（Inland Revenue Ordinance (Cap. 112) - whole chapter, English Cap. 112）「ascertained in accordance with subse…」
  - 参数 hk.ip.clawback：uses = 1 bool；hk.cap112.en#s16E（Inland Revenue Ordinance (Cap. 112) - whole chapter, English Cap. 112）「do not exceed the amount of the dedu…」
  - 参数 hk.profits.rate_entity：uses = 1 bool；hk.cap112.en#sch8B（Inland Revenue Ordinance (Cap. 112) - whole chapter, English Cap. 112）「at the rate of 8.25% on section 14 a…」
  - 求值器出处 hk.cap112.en#s15I：Inland Revenue Ordinance (Cap. 112) - whole chapter, English Cap. 112
  - 求值器出处 hk.cap112.en#s16E：Inland Revenue Ordinance (Cap. 112) - whole chapter, English Cap. 112
  - 求值器出处 hk.cap112.en#sch17FC：Inland Revenue Ordinance (Cap. 112) - whole chapter, English Cap. 112
  - 口径 D22：锚点 16/16 找到原文
- **hk.ip.onshore**（D_DISCRETION，2026-03-31）通过
  - 参数 hk.profits.rate_corp：value = 16.5 %；hk.cap112.en#sch8B（Inland Revenue Ordinance (Cap. 112) - whole chapter, English Cap. 112）「at the rate of 16.5% on any part of …」
  - 判断出处 hk.cap112.en#s14：Inland Revenue Ordinance (Cap. 112) - whole chapter, English Cap. 112
  - 参数 hk.profits.charge_scope：uses = 1 bool；hk.cap112.en#s14（Inland Revenue Ordinance (Cap. 112) - whole chapter, English Cap. 112）「on every person carrying on a trade,…」
  - 参数 hk.profits.rate_entity：uses = 1 bool；hk.cap112.en#sch8B（Inland Revenue Ordinance (Cap. 112) - whole chapter, English Cap. 112）「at the rate of 8.25% on section 14 a…」
  - 求值器出处 hk.cap112.en#s14：Inland Revenue Ordinance (Cap. 112) - whole chapter, English Cap. 112
  - 口径 D22：锚点 16/16 找到原文

## 事实来源（规则读到的事实，按流）

- iptx：推导（facts.py） 8（authority_action、cn_party、consideration、date_of_payment、prior_map_outcome、hk_resident_or_pe…）；方案动作 2（input_vat_documents_kept、vat_tech_recognized）；未定（按两端计） 3（ucmt_location、ucmt_location、vat_general_taxpayer）；未给出（规则判为不影响结果） 9（assessment_notice_on、determination_on、first_notification_on、foreign_tax_rate、payable_on、remitted_on…）；设计或模板设定 1（ip_horizon_years）；陈述 10（cost_basis、instrument_used_in_cn、ip_allowances_claimed、ip_kind、ip_useful_life_years、non_qualifying_expenditure…）

陈述的事实 10 个，附出处 0 个。
