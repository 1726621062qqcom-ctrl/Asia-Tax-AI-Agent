# 依据核对：K4-freetech-2024

运行 20261014T214314-K4-freetech-2024，版本 be566a8fb554。规划器给出的是问卷（下面核对的是目前最优的候选）；核对 46 项：通过 24，说明 21，警示 1，失败 0。

**结论**：每一步都落到现行条文的原文；陈述的事实都附出处。

候选 {'HOLD': None, 'exit_route': 'DIRECT'}；保证税额 4044884.50，最好情形 2465449.50；重算一致。

## 需要处理的

- 警示：exit/remit 期限按名义日期：库里缺 CN 2024 年的公众假期表

## 税项（保证税额一端）

| 流 | 法域 | 税种 | 承担方 | 金额 | 规则 | 依据 |
|---|---|---|---|---|---|---|
| exit | CN | stamp | ULT | 35549.50 | cn.stamp.seller | 通过 |
| exit | CN | stamp | BUYER（集团外） | 35549.50 | cn.stamp.buyer | 通过 |
| exit | CN | income | ULT | 2429900.00 | cn.wht.reduced、cn.gain.base | 通过 |
| exit | HK | income | ULT | 1579435.00 | hk.fsie.charge、hk.fsie.gain.base、hk.ftc.dta | 通过 |

## 方案动作

| 动作 | 依据所在的规则 | 依据 |
|---|---|---|
| ULT.registration_filing_compliant:is_true | hk.fsie.substance.share_transfer | 通过 |

## 待机关认可的判断

| 事项 | 流 | 判断所引条款 | 规则 | 依据 | 先例（案例采集.md §5） |
|---|---|---|---|---|---|
| payee.no_main_purpose_of_tax_benefit | exit | hk.cap112.en#s15N | hk.fsie.participation.share_transfer | 通过 | 无先例卡 |
| payee.adequate_substance | exit | hk.cap112.en#s15K | hk.fsie.substance.share_transfer | 通过 | 未被压住；成立最近的先例 HK-arc-69-2023（还差 as_minimal_loans） |

## 期限与罚款

| 流 | 规则 | 依据 |
|---|---|---|
| exit | cn.wht.remit | 通过 |

## 问卷的每个问题

| 类别 | 问题 | 由哪条规则提出 | 依据 |
|---|---|---|---|
| ruling | ULT.reorg_reasonable_commercial_purpose | cn.reorg.special [CN] | 说明 |
| ruling | ULT.reorg_wht_burden_unchanged | cn.reorg.special [CN] | 说明 |
| library | calendar:CN:2024 | remit | 说明 |
| data | ULT.pure_equity_holding | hk.fsie.substance.share_transfer [HK] | 说明 |
| data | ULT.substance_ruled_adequate | hk.fsie.substance.share_transfer [HK] | 说明 |
| data | flow:exit.deductible_at_payer | hk.fsie.participation.share_transfer [HK] | 说明 |
| data | flow:exit.foreign_headline_rate | hk.fsie.participation.share_transfer [HK] | 说明 |
| data | flow:exit.foreign_taxed | hk.fsie.participation.share_transfer [HK] | 说明 |
| data | flow:exit.underlying_profits_taxed | hk.fsie.participation.share_transfer [HK] | 说明 |
| ruling | ULT.adequate_substance | hk.fsie.substance.share_transfer [HK] | 说明 |
| ruling | ULT.no_main_purpose_of_tax_benefit | hk.fsie.participation.share_transfer [HK] | 说明 |
| blocking | flow:reorg.amount | data.amount | 说明 |
| data | flow:exit.cost_basis | cn.indirect.gain.base [CN]、hk.fsie.gain.base [HK]、sg.gain.base [SG] | 说明 |

## 规则依据（本方案用到的 10 条规则）

- **cn.gain.base**（A_TEXT，2024-11-22）通过
  - 参数 cn.wht.base_gain：uses = 1 bool；cn.law.eit#19（中华人民共和国企业所得税法 ）「转让财产所得，以收入全额减除财产净值后的余额为应纳税所得额」
  - 参数 cn.tp.related_transfer_arms_length：uses = 1 bool；cn.law.eit#41（中华人民共和国企业所得税法 ）「企业与其关联方之间的业务往来，不符合独立交易原则而减少企业或者其关联方应…」
  - 参数 cn.tp.related_share_min：uses = 25 %；cn.sta.2016-42#i2（国家税务总局关于完善关联申报和同期资料管理有关事项的公告 国家税务总局公告2016年第42号）「一方直接或者间接持有另一方的股份总和达到25%以上」
  - 求值器出处 cn.law.eit#16：中华人民共和国企业所得税法 
  - 口径 D32：锚点 7/7 找到原文
  - 口径 D38：锚点 9/9 找到原文
- **cn.stamp.buyer**（A_TEXT，2024-11-22）通过
  - 参数 cn.stamp.equity_rate：value = 0.05 %；cn.law.stamp.flk#20（中华人民共和国印花税法（国家法律法规数据库 PDF，含印花税税目税率表） 主席令第八十九号）「价款的万分之五」
  - 参数 cn.stamp.taxpayer_each_party：uses = 1 bool；cn.law.stamp.flk#1（中华人民共和国印花税法（国家法律法规数据库 PDF，含印花税税目税率表） 主席令第八十九号）「应当依照本法规定缴纳印花税」
  - 所依法律的施行条款 cn.law.stamp.flk#20：中华人民共和国印花税法（国家法律法规数据库 PDF，含印花税税目税率表） 主席令第八十九号
  - 口径 D19：锚点 12/12 找到原文
- **cn.stamp.seller**（A_TEXT，2024-11-22）通过
  - 参数 cn.stamp.equity_rate：value = 0.05 %；cn.law.stamp.flk#20（中华人民共和国印花税法（国家法律法规数据库 PDF，含印花税税目税率表） 主席令第八十九号）「价款的万分之五」
  - 参数 cn.stamp.taxpayer_each_party：uses = 1 bool；cn.law.stamp.flk#1（中华人民共和国印花税法（国家法律法规数据库 PDF，含印花税税目税率表） 主席令第八十九号）「应当依照本法规定缴纳印花税」
  - 所依法律的施行条款 cn.law.stamp.flk#20：中华人民共和国印花税法（国家法律法规数据库 PDF，含印花税税目税率表） 主席令第八十九号
  - 口径 D19：锚点 12/12 找到原文
- **cn.wht.reduced**（A_TEXT，2024-11-22）通过
  - 参数 cn.wht.rate：value = 10 %；cn.reg.eit#91（中华人民共和国企业所得税法实施条例 国务院令第512号）「减按10%的税率征收企业所得税」
- **cn.wht.remit**（A_TEXT，2024-11-22）通过
  - 参数 cn.wht.obligation_date：value = actual payment or date payable text；cn.sta.2017-37#i4（国家税务总局关于非居民企业所得税源泉扣缴有关问题的公告 国家税务总局公告2017年第37号）「扣缴义务发生之日为相关款项实际支付或者到期应支付之日」
  - 参数 cn.wht.remit_days：uses = 7 days；cn.sta.2017-37#i7（国家税务总局关于非居民企业所得税源泉扣缴有关问题的公告 国家税务总局公告2017年第37号）「扣缴义务人应当自扣缴义务发生之日起7日内向扣缴义务人所在地主管税务机关申…」
  - 参数 cn.wht.obligation_date_dividend：uses = actual payment text；cn.sta.2017-37#i7（国家税务总局关于非居民企业所得税源泉扣缴有关问题的公告 国家税务总局公告2017年第37号）「相关应纳税款扣缴义务发生之日为股息、红利等权益性投资收益实际支付之日」
  - 参数 cn.wht.fx_rule：uses = CNY central parity on the obligation date text；cn.sta.2017-37#i4（国家税务总局关于非居民企业所得税源泉扣缴有关问题的公告 国家税务总局公告2017年第37号）「应当按照扣缴义务发生之日人民币汇率中间价折合成人民币」
  - 参数 cn.time.holiday_roll：uses = 1 bool；cn.reg.tca#109（中华人民共和国税收征收管理法实施细则 国务院令第362号（2016年修订））「期限的最后一日是法定休假日的，以休假日期满的次日为期限的最后一日」
  - 参数 cn.time.long_holiday_days：uses = 3 days；cn.reg.tca#109（中华人民共和国税收征收管理法实施细则 国务院令第362号（2016年修订））「在期限内有连续３日以上法定休假日的，按休假日天数顺延」
- **hk.fsie.charge**（A_TEXT，2024-11-22）通过
  - 参数 hk.profits.rate_corp：value = 16.5 %；hk.cap112.en#sch8B（Inland Revenue Ordinance (Cap. 112) - whole chapter, English Cap. 112）「at the rate of 16.5% on any part of …」
  - 参数 hk.fsie.mne_entity_only：threshold = 1 bool；hk.cap112.en#s15I（Inland Revenue Ordinance (Cap. 112) - whole chapter, English Cap. 112）「is received in Hong Kong by an MNE e…」
  - 参数 hk.fsie.receipt_kinds：threshold = REMITTED;DEBT_SETTLED;MOVABLE_PROPERTY enum；hk.cap112.en#s15H（Inland Revenue Ordinance (Cap. 112) - whole chapter, English Cap. 112）「the sum is remitted to, or is transm…」
  - 参数 hk.fsie.commencement：threshold = 1 bool；hk.cap112.en#sch55（Inland Revenue Ordinance (Cap. 112) - whole chapter, English Cap. 112）「apply in relation to specified forei…」
  - 参数 hk.fsie.covered_income：uses = interest;dividend;disposal_gain;ip_income enum；hk.cap112.en#s15H（Inland Revenue Ordinance (Cap. 112) - whole chapter, English Cap. 112）「means any interest, dividend, dispos…」
  - 参数 hk.fsie.received_in_hk_trigger：uses = 1 bool；hk.cap112.en#s15I（Inland Revenue Ordinance (Cap. 112) - whole chapter, English Cap. 112）「is to be regarded as a receipt arisi…」
  - 参数 hk.fsie.remittance_is_receipt：uses = 1 bool；hk.cap112.en#s15H（Inland Revenue Ordinance (Cap. 112) - whole chapter, English Cap. 112）「the sum is remitted to, or is transm…」
  - 参数 hk.profits.charge_scope：uses = 1 bool；hk.cap112.en#s14（Inland Revenue Ordinance (Cap. 112) - whole chapter, English Cap. 112）「on every person carrying on a trade,…」
  - 参数 hk.profits.rate_entity：uses = 1 bool；hk.cap112.en#sch8B（Inland Revenue Ordinance (Cap. 112) - whole chapter, English Cap. 112）「at the rate of 8.25% on section 14 a…」
  - 参数 hk.fsie.in_kind_not_received：uses = 1 bool；hk.arc.75#all（Advance Ruling Case No. 75 ARC 75）「The Dividend shall not be regarded a…」
  - 参数 hk.fsie.stand_alone_mne：uses = 1 bool；hk.cap112.en#s15H（Inland Revenue Ordinance (Cap. 112) - whole chapter, English Cap. 112）「is located in one jurisdiction and h…」
  - 参数 hk.fsie.mne_group_pe：uses = 1 bool；hk.cap112.en#s15H（Inland Revenue Ordinance (Cap. 112) - whole chapter, English Cap. 112）「a group that includes at least one e…」
  - 口径 D34：锚点 2/2 找到原文
- **hk.fsie.gain.base**（A_TEXT，2024-11-22）通过
  - 参数 hk.fsie.gain_not_capital：uses = 1 bool；hk.cap112.en#s15I（Inland Revenue Ordinance (Cap. 112) - whole chapter, English Cap. 112）「is to be regarded as not arising fro…」
  - 参数 hk.fsie.disposal_gains_commencement：uses = 1 bool；hk.cap112.en#sch56（Inland Revenue Ordinance (Cap. 112) - whole chapter, English Cap. 112）「apply in relation to specified forei…」
  - 求值器出处 hk.cap112.en#s14：Inland Revenue Ordinance (Cap. 112) - whole chapter, English Cap. 112
  - 口径 D32：锚点 7/7 找到原文
- **hk.fsie.participation.share_transfer**（D_DISCRETION，2024-11-22）通过
  - 参数 hk.fsie.participation_resident_or_pe：threshold = 1 bool；hk.cap112.en#s15M（Inland Revenue Ordinance (Cap. 112) - whole chapter, English Cap. 112）「a Hong Kong resident person; or (ii)…」
  - 参数 hk.fsie.participation_ratio_min：threshold = 5 %；hk.cap112.en#s15M（Inland Revenue Ordinance (Cap. 112) - whole chapter, English Cap. 112）「has continuously held not less than …」
  - 参数 hk.fsie.participation_months_min：threshold = 12 months；hk.cap112.en#s15M（Inland Revenue Ordinance (Cap. 112) - whole chapter, English Cap. 112）「for a period of not less than 12 mon…」
  - 参数 hk.fsie.participation_subject_to_tax：threshold = 1 bool；hk.cap112.en#s15N（Inland Revenue Ordinance (Cap. 112) - whole chapter, English Cap. 112）「the income is subject to a qualifyin…」
  - 参数 hk.fsie.participation_headline_rate_basis：threshold = 1 bool；hk.cap112.en#s15N（Inland Revenue Ordinance (Cap. 112) - whole chapter, English Cap. 112）「the highest applicable rate, of a si…」
  - 参数 hk.fsie.intragroup_subject_to_tax：threshold = 1 bool；hk.fsie.examples#h15（IRD: FSIE regime - Illustrative Examples ）「would be accepted as having been met…」
  - 参数 hk.fsie.reference_rate：threshold = 15 %；hk.cap112.en#s15N（Inland Revenue Ordinance (Cap. 112) - whole chapter, English Cap. 112）「the reference rate is 15%」
  - 参数 hk.fsie.participation_anti_hybrid：threshold = 1 bool；hk.cap112.en#s15N（Inland Revenue Ordinance (Cap. 112) - whole chapter, English Cap. 112）「section 15M does not apply if, and t…」
  - 判断出处 hk.cap112.en#s15N：Inland Revenue Ordinance (Cap. 112) - whole chapter, English Cap. 112
  - 参数 hk.fsie.participation_main_purpose：uses = 1 bool；hk.cap112.en#s15N（Inland Revenue Ordinance (Cap. 112) - whole chapter, English Cap. 112）「the main purpose, or one of the main…」
  - 口径 D32：锚点 7/7 找到原文
- **hk.fsie.substance.share_transfer**（D_DISCRETION，2024-11-22）通过
  - 参数 hk.fsie.substance_pure_holding：threshold = 1 bool；hk.cap112.en#s15K（Inland Revenue Ordinance (Cap. 112) - whole chapter, English Cap. 112）「in the Commissioner’s opinion, the e…」
  - 判断出处 hk.cap112.en#s15K：Inland Revenue Ordinance (Cap. 112) - whole chapter, English Cap. 112
  - 参数 hk.fsie.substance_non_pure_holding：threshold = 1 bool；hk.cap112.en#s15K（Inland Revenue Ordinance (Cap. 112) - whole chapter, English Cap. 112）「the total amount of operating expend…」
  - 参数 hk.fsie.substance_exception_income：uses = interest;dividend;non_ip_disposal_gain enum；hk.cap112.en#s15K（Inland Revenue Ordinance (Cap. 112) - whole chapter, English Cap. 112）「the income is interest, a dividend o…」
  - 口径 D32：锚点 7/7 找到原文
- **hk.ftc.dta**（A_TEXT，2024-11-22）通过
  - 参数 hk.ftc.credit_limit：uses = hk_tax_on_same_income_at_average_rate enum；hk.cap112.en#s50（Inland Revenue Ordinance (Cap. 112) - whole chapter, English Cap. 112）「The credit shall not exceed the amou…」
  - 参数 hk.fsie.intragroup_foreign_tax：uses = 1 bool；hk.cap112.en#s15OA（Inland Revenue Ordinance (Cap. 112) - whole chapter, English Cap. 112）「that foreign tax is, for the purpose…」

## 事实来源（规则读到的事实，按流）

- exit：推导（facts.py） 16（accrued_in_fsie_regime、authority_action、cn_related、consideration、cost_basis、date_of_payment…）；方案动作 1（registration_filing_compliant）；未定（按两端计） 6（deductible_at_payer、foreign_headline_rate、foreign_taxed、underlying_profits_taxed、pure_equity_holding、substance_ruled_adequate）；未给出（规则判为不影响结果） 26（acquirer_chargeable_in_hk、arms_length_value、assessment_notice_on、clawback_event_within_2y、cn_cost_basis、determination_on…）；结构性缺省（按否） 2（shares_cancelled、subject_income_taxed_abroad）；陈述（有出处） 2（listed_market_trade、receipt_kind）

陈述的事实 2 个，附出处 2 个。
