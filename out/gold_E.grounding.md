# 依据核对：gold_E

运行 20261014T173558-gold_E，版本 5501a0239aac。规划器给出的是问卷（下面核对的是目前最优的候选）；核对 39 项：通过 25，说明 13，警示 1，失败 0。

**结论**：每一步都落到现行条文的原文；陈述的事实未附出处（0/23）。

候选 {'HOLD': 'HK', 'repatriation': 'LIQUIDATION', 'payment': False}；保证税额 252.00，最好情形 60.00；重算一致。

## 需要处理的

- 警示：gold_E 案例陈述的事实 23 个，附出处的 0 个（案例文件没有 provenance，见 案例采集.md §4.2）

## 税项（保证税额一端）

| 流 | 法域 | 税种 | 承担方 | 金额 | 规则 | 依据 |
|---|---|---|---|---|---|---|
| out.div | CN | income | HOLD | 60.00 | cn.wht.reduced、cn.liquidation.split | 通过 |
| out.div | HK | income | HOLD | 39.00 | hk.fsie.charge、hk.ftc.dta、cn.liquidation.split | 通过 |
| up2 | SG | income | ULT | 153.00 | sg.fsie.charge、sg.ftc.unilateral | 通过 |

## 待机关认可的判断

| 事项 | 流 | 判断所引条款 | 规则 | 依据 | 先例（案例采集.md §5） |
|---|---|---|---|---|---|
| payee.reasonable_commercial_purpose_absent | out.div | cn.law.eit#47、cn.reg.eit#120 | cn.gaar | 通过 | 无先例卡 |
| payee.no_main_purpose_of_tax_benefit | out.div | hk.cap112.en#s15N | hk.fsie.participation.dividend | 通过 | 无先例卡 |
| payee.adequate_substance | out.div | hk.cap112.en#s15K | hk.fsie.substance.dividend | 通过 | 未被压住；成立最近的先例 HK-arc-69-2023（还差 as_minimal_loans） |
| payee.exemption_beneficial | up2 | sg.ita1947.full#s13 | sg.fsie.exempt | 通过 | 无先例卡 |

## 期限与罚款

| 流 | 规则 | 依据 |
|---|---|---|
| out.div | cn.wht.remit | 通过 |
| out.gain | cn.wht.remit | 通过 |

## 问卷的每个问题

| 类别 | 问题 | 由哪条规则提出 | 依据 |
|---|---|---|---|
| blocking | group.group_revenue_eur | data.p2_income | 通过 |

## 规则依据（本方案用到的 11 条规则）

- **cn.gaar**（D_DISCRETION，2026-03-31）通过
  - 参数 cn.gaar：value = 1 bool；cn.law.eit#47（中华人民共和国企业所得税法 ）「企业实施其他不具有合理商业目的的安排而减少其应纳税收入或者所得额的，税务…」
  - 判断出处 cn.law.eit#47：中华人民共和国企业所得税法 
  - 判断出处 cn.reg.eit#120：中华人民共和国企业所得税法实施条例 国务院令第512号
- **cn.liquidation.split**（A_TEXT，2026-03-31）通过
  - 参数 cn.liquidation.split：uses = 1 bool；cn.cs.2009-60#i5（财政部 国家税务总局关于企业清算业务企业所得税处理若干问题的通知 财税〔2009〕60号）「其中相当于被清算企业累计未分配利润和累计盈余公积中按该股东所占股份比例计…」
- **cn.wht.reduced**（A_TEXT，2026-03-31）通过
  - 参数 cn.wht.rate：value = 10 %；cn.reg.eit#91（中华人民共和国企业所得税法实施条例 国务院令第512号）「减按10%的税率征收企业所得税」
- **cn.wht.remit**（A_TEXT，2026-03-31）通过
  - 参数 cn.wht.obligation_date：value = actual payment or date payable text；cn.sta.2017-37#i4（国家税务总局关于非居民企业所得税源泉扣缴有关问题的公告 国家税务总局公告2017年第37号）「扣缴义务发生之日为相关款项实际支付或者到期应支付之日」
  - 参数 cn.wht.remit_days：uses = 7 days；cn.sta.2017-37#i7（国家税务总局关于非居民企业所得税源泉扣缴有关问题的公告 国家税务总局公告2017年第37号）「扣缴义务人应当自扣缴义务发生之日起7日内向扣缴义务人所在地主管税务机关申…」
  - 参数 cn.wht.obligation_date_dividend：uses = actual payment text；cn.sta.2017-37#i7（国家税务总局关于非居民企业所得税源泉扣缴有关问题的公告 国家税务总局公告2017年第37号）「相关应纳税款扣缴义务发生之日为股息、红利等权益性投资收益实际支付之日」
  - 参数 cn.wht.fx_rule：uses = CNY central parity on the obligation date text；cn.sta.2017-37#i4（国家税务总局关于非居民企业所得税源泉扣缴有关问题的公告 国家税务总局公告2017年第37号）「应当按照扣缴义务发生之日人民币汇率中间价折合成人民币」
  - 参数 cn.time.holiday_roll：uses = 1 bool；cn.reg.tca#109（中华人民共和国税收征收管理法实施细则 国务院令第362号（2016年修订））「期限的最后一日是法定休假日的，以休假日期满的次日为期限的最后一日」
  - 参数 cn.time.long_holiday_days：uses = 3 days；cn.reg.tca#109（中华人民共和国税收征收管理法实施细则 国务院令第362号（2016年修订））「在期限内有连续３日以上法定休假日的，按休假日天数顺延」
- **hk.fsie.charge**（A_TEXT，2026-03-31）通过
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
- **hk.fsie.participation.dividend**（D_DISCRETION，2026-03-31）通过
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
- **hk.fsie.substance.dividend**（D_DISCRETION，2026-03-31）通过
  - 参数 hk.fsie.substance_pure_holding：threshold = 1 bool；hk.cap112.en#s15K（Inland Revenue Ordinance (Cap. 112) - whole chapter, English Cap. 112）「in the Commissioner’s opinion, the e…」
  - 判断出处 hk.cap112.en#s15K：Inland Revenue Ordinance (Cap. 112) - whole chapter, English Cap. 112
  - 参数 hk.fsie.substance_non_pure_holding：threshold = 1 bool；hk.cap112.en#s15K（Inland Revenue Ordinance (Cap. 112) - whole chapter, English Cap. 112）「the total amount of operating expend…」
  - 参数 hk.fsie.substance_exception_income：uses = interest;dividend;non_ip_disposal_gain enum；hk.cap112.en#s15K（Inland Revenue Ordinance (Cap. 112) - whole chapter, English Cap. 112）「the income is interest, a dividend o…」
  - 口径 D32：锚点 7/7 找到原文
- **hk.ftc.dta**（A_TEXT，2026-03-31）通过
  - 参数 hk.ftc.credit_limit：uses = hk_tax_on_same_income_at_average_rate enum；hk.cap112.en#s50（Inland Revenue Ordinance (Cap. 112) - whole chapter, English Cap. 112）「The credit shall not exceed the amou…」
  - 参数 hk.fsie.intragroup_foreign_tax：uses = 1 bool；hk.cap112.en#s15OA（Inland Revenue Ordinance (Cap. 112) - whole chapter, English Cap. 112）「that foreign tax is, for the purpose…」
- **sg.fsie.charge**（A_TEXT，2026-03-31）通过
  - 参数 sg.corp.rate：value = 17 %；sg.ita1947.full#s43（Income Tax Act 1947 (assembled whole-document HTML: base page + 36 lazy-load fragments) ）「every company or body of persons, ta…」
  - 参数 sg.fsie.receipt_kinds：threshold = REMITTED;DEBT_SETTLED;MOVABLE_PROPERTY enum；sg.ita1947.full#s10（Income Tax Act 1947 (assembled whole-document HTML: base page + 36 lazy-load fragments) ）「any amount from any income derived f…」
  - 参数 sg.charge.basis：uses = accruing_in_or_derived_from_sg;received_in_sg_from_outside enum；sg.ita1947.full#s10（Income Tax Act 1947 (assembled whole-document HTML: base page + 36 lazy-load fragments) ）「upon the income of any person accrui…」
  - 参数 sg.foreign_income.remittance_is_receipt：uses = 1 bool；sg.ita1947.full#s10（Income Tax Act 1947 (assembled whole-document HTML: base page + 36 lazy-load fragments) ）「any amount from any income derived f…」
  - 参数 sg.fsie.recipient：uses = 1 bool；sg.ita1947.full#s13（Income Tax Act 1947 (assembled whole-document HTML: base page + 36 lazy-load fragments) ）「on or after 1 June 2003 by any perso…」
  - 参数 sg.corp.rate_entity：uses = 1 bool；sg.ita1947.full#s43（Income Tax Act 1947 (assembled whole-document HTML: base page + 36 lazy-load fragments) ）「for every dollar of the first $10,00…」
- **sg.fsie.exempt**（D_DISCRETION，2026-03-31）通过
  - 参数 sg.fsie.subject_to_tax：threshold = 1 bool；sg.ita1947.full#s13（Income Tax Act 1947 (assembled whole-document HTML: base page + 36 lazy-load fragments) ）「the income is subject to tax of a si…」
  - 参数 sg.fsie.headline_rate_min：threshold = 15 %；sg.ita1947.full#s13（Income Tax Act 1947 (assembled whole-document HTML: base page + 36 lazy-load fragments) ）「is not less than 15%」
  - 判断出处 sg.ita1947.full#s13：Income Tax Act 1947 (assembled whole-document HTML: base page + 36 lazy-load fragments) 
  - 参数 sg.fsie.beneficial：uses = 1 bool；sg.ita1947.full#s13（Income Tax Act 1947 (assembled whole-document HTML: base page + 36 lazy-load fragments) ）「the Comptroller is satisfied that th…」
  - 参数 sg.fsie.ministerial_order：uses = 1 bool；sg.ita1947.full#s13（Income Tax Act 1947 (assembled whole-document HTML: base page + 36 lazy-load fragments) ）「the income received by a person resi…」
- **sg.ftc.unilateral**（A_TEXT，2026-03-31）通过
  - 参数 sg.ftc.unilateral：uses = 1 bool；sg.ita1947.full#s50A（Income Tax Act 1947 (assembled whole-document HTML: base page + 36 lazy-load fragments) ）「Even if there are no arrangements in…」
  - 参数 sg.ftc.unilateral_income：uses = dividend;royalty;interest;s10l_gain;other_income_nature enum；sg.ita1947.full#s50A（Income Tax Act 1947 (assembled whole-document HTML: base page + 36 lazy-load fragments) ）「( c ) any dividend derived from that…」
  - 参数 sg.ftc.credit_limit：uses = sg_tax_on_same_income_at_average_rate enum；sg.ita1947.full#s50（Income Tax Act 1947 (assembled whole-document HTML: base page + 36 lazy-load fragments) ）「The credit must not exceed the amoun…」

## 事实来源（规则读到的事实，按流）

- out.div：推导（facts.py） 16（accrued_in_fsie_regime、authority_action、capitalised、date_of_payment、direct_ratio、hk_holding_months…）；未给出（规则判为不影响结果） 18（assessment_notice_on、capitalised_from、determination_on、direct_payment、dividend_from_pre_reorg_profits、first_notification_on…）；结构性缺省（按否） 1（subject_income_taxed_abroad）；陈述 11（deductible_at_payer、foreign_headline_rate、foreign_taxed、receipt_kind、reinvested_in_cn、underlying_profits_taxed…）
- out.gain：推导（facts.py） 14（accrued_in_fsie_regime、authority_action、cn_related、date_of_payment、hk_holding_months、intragroup_transfer…）；未给出（规则判为不影响结果） 26（acquirer_chargeable_in_hk、arms_length_value、assessment_notice_on、clawback_event_within_2y、cn_cost_basis、determination_on…）；结构性缺省（按否） 1（subject_income_taxed_abroad）；设计或模板设定 3（consideration、cost_basis、shares_cancelled）；陈述 9（deductible_at_payer、foreign_headline_rate、foreign_taxed、receipt_kind、underlying_profits_taxed、pure_equity_holding…）
- up2：推导（facts.py） 1（payee_in_source_jur）；未给出（规则判为不影响结果） 4（assessment_notice_on、foreign_tax_rate、ucmt_location、ucmt_location）；陈述 3（foreign_headline_rate、foreign_taxed、receipt_kind）

陈述的事实 23 个，附出处 0 个。
