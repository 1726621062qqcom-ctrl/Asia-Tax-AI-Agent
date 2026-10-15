# 依据核对：gold_B

运行 20261014T173519-gold_B，版本 5501a0239aac。规划器给出的是问卷（下面核对的是目前最优的候选）；核对 44 项：通过 26，说明 17，警示 1，失败 0。

**结论**：每一步都落到现行条文的原文；陈述的事实未附出处（0/17）。

候选 {'HOLD': 'HK', 'financing': 'EQUITY', 'payment': False, 'exit_route': 'DIRECT'}；保证税额 531.00，最好情形 169.65；重算一致。

## 需要处理的

- 警示：gold_B 案例陈述的事实 17 个，附出处的 0 个（案例文件没有 provenance，见 案例采集.md §4.2）

## 税项（保证税额一端）

| 流 | 法域 | 税种 | 承担方 | 金额 | 规则 | 依据 |
|---|---|---|---|---|---|---|
| up1 | HK | income | HOLD | 165.00 | hk.fsie.charge、hk.ftc.unilateral | 通过 |
| up2 | CN | income | ULT | 36.00 | cn.resident.charge、cn.ftc.dividend_indirect | 通过 |
| exit | SG | stamp | BUYER（集团外） | 10.00 | sg.stamp.buyer | 通过 |
| exit | HK | income | HOLD | 330.00 | hk.fsie.charge、hk.fsie.gain.base、hk.ftc.unilateral | 通过 |

## 待机关认可的判断

| 事项 | 流 | 判断所引条款 | 规则 | 依据 | 先例（案例采集.md §5） |
|---|---|---|---|---|---|
| payee.no_main_purpose_of_tax_benefit | up1 | hk.cap112.en#s15N | hk.fsie.participation.dividend | 通过 | 无先例卡 |
| payee.adequate_substance | up1 | hk.cap112.en#s15K | hk.fsie.substance.dividend | 通过 | 未被压住；成立最近的先例 HK-arc-69-2023（还差 as_minimal_loans） |
| payee.adequate_substance | exit | hk.cap112.en#s15K | hk.fsie.substance.share_transfer | 通过 | 未被压住；成立最近的先例 HK-arc-69-2023（还差 as_minimal_loans） |

## 问卷的每个问题

| 类别 | 问题 | 由哪条规则提出 | 依据 |
|---|---|---|---|
| blocking | group.group_revenue_eur | data.p2_income | 通过 |
| blocking | OP.after_tax_profit | data.cfc_profit | 通过 |

## 规则依据（本方案用到的 10 条规则）

- **cn.ftc.dividend**（A_TEXT，2026-03-31）通过
  - 参数 cn.ftc.indirect_ratio_min：threshold = 20 %；cn.reg.eit#80（中华人民共和国企业所得税法实施条例 国务院令第512号）「直接控制，是指居民企业直接持有外国企业20%以上股份」
  - 参数 cn.ftc.credit：uses = 1 bool；cn.law.eit#23（中华人民共和国企业所得税法 ）「企业取得的下列所得已在境外缴纳的所得税税额，可以从其当期应纳税额中抵免，…」
  - 参数 cn.ftc.limit_per_country：uses = 1 bool；cn.reg.eit#78（中华人民共和国企业所得税法实施条例 国务院令第512号）「该抵免限额应当分国(地区)不分项计算」
  - 参数 cn.ftc.income_recognition_dividend：uses = 1 bool；cn.cs.2009-125#i3（财政部 国家税务总局关于企业境外所得税收抵免有关问题的通知 财税〔2009〕125号）「来源于境外的股息、红利等权益性投资收益，应按被投资方作出利润分配决定的日…」
- **cn.ftc.dividend_indirect**（A_TEXT，2026-03-31）通过
  - 参数 cn.ftc.indirect_ratio_min：threshold = 20 %；cn.reg.eit#80（中华人民共和国企业所得税法实施条例 国务院令第512号）「直接控制，是指居民企业直接持有外国企业20%以上股份」
  - 参数 cn.ftc.credit：uses = 1 bool；cn.law.eit#23（中华人民共和国企业所得税法 ）「企业取得的下列所得已在境外缴纳的所得税税额，可以从其当期应纳税额中抵免，…」
  - 参数 cn.ftc.indirect：uses = 1 bool；cn.law.eit#24（中华人民共和国企业所得税法 ）「外国企业在境外实际缴纳的所得税税额中属于该项所得负担的部分，可以作为该居…」
  - 参数 cn.ftc.indirect_tiers：uses = 5 tiers；cn.cs.2017-84#i2（财政部 税务总局关于完善企业境外所得税收抵免政策问题的通知 财税〔2017〕84号）「五层外国企业」
  - 参数 cn.ftc.indirect_formula：uses = 1 bool；cn.cs.2009-125#i5（财政部 国家税务总局关于企业境外所得税收抵免有关问题的通知 财税〔2009〕125号）「本层企业所纳税额属于由一家上一层企业负担的税额＝（本层企业就利润和投资收…」
  - 参数 cn.ftc.gross_up：uses = 1 bool；cn.sta.2010-01.a01#16（《企业境外所得税收抵免操作指南》 ）「该境外股息、红利所得应为境外股息、红利税后净所得与就该项所得直接缴纳和间…」
  - 参数 cn.ftc.limit_per_country：uses = 1 bool；cn.reg.eit#78（中华人民共和国企业所得税法实施条例 国务院令第512号）「该抵免限额应当分国(地区)不分项计算」
  - 参数 cn.ftc.income_recognition_dividend：uses = 1 bool；cn.cs.2009-125#i3（财政部 国家税务总局关于企业境外所得税收抵免有关问题的通知 财税〔2009〕125号）「来源于境外的股息、红利等权益性投资收益，应按被投资方作出利润分配决定的日…」
  - 参数 cn.cfc.credit：uses = 1 bool；cn.gsf.2009-02#82（国家税务总局关于印发《特别纳税调整实施办法（试行）》的通知 国税发〔2009〕2号）「计入中国居民企业股东当期所得已在境外缴纳的企业所得税税款，可按照所得税法…」
  - 口径 D08：锚点 1/1 找到原文
- **cn.resident.charge**（A_TEXT，2026-03-31）通过
  - 参数 cn.eit.rate：value = 25 %；cn.law.eit#4（中华人民共和国企业所得税法 ）「企业所得税的税率为25％」
  - 参数 cn.eit.resident_worldwide：uses = 1 bool；cn.law.eit#3（中华人民共和国企业所得税法 ）「居民企业应当就其来源于中国境内、境外的所得缴纳企业所得税」
  - 参数 cn.eit.rate_entity：uses = 1 bool；cn.law.eit#28（中华人民共和国企业所得税法 ）「国家需要重点扶持的高新技术企业，减按15％的税率征收企业所得税」
  - 参数 cn.branch.accrual：uses = 1 bool；cn.cs.2009-125#i3（财政部 国家税务总局关于企业境外所得税收抵免有关问题的通知 财税〔2009〕125号）「居民企业在境外设立不具有独立纳税地位的分支机构取得的各项境外所得，无论是…」
  - 参数 cn.branch.tax_year：uses = 1 bool；cn.cs.2009-125#i11（财政部 国家税务总局关于企业境外所得税收抵免有关问题的通知 财税〔2009〕125号）「与我国纳税年度当年度相对应的境外纳税年度，应为在我国有关纳税年度中任何一…」
  - 参数 cn.branch.loss_not_offset：uses = 1 bool；cn.law.eit#17（中华人民共和国企业所得税法 ）「其境外营业机构的亏损不得抵减境内营业机构的盈利」
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
- **hk.fsie.charge**（A_TEXT，2026-12-31）通过
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
- **hk.fsie.gain.base**（A_TEXT，2026-12-31）通过
  - 参数 hk.fsie.gain_not_capital：uses = 1 bool；hk.cap112.en#s15I（Inland Revenue Ordinance (Cap. 112) - whole chapter, English Cap. 112）「is to be regarded as not arising fro…」
  - 参数 hk.fsie.disposal_gains_commencement：uses = 1 bool；hk.cap112.en#sch56（Inland Revenue Ordinance (Cap. 112) - whole chapter, English Cap. 112）「apply in relation to specified forei…」
  - 求值器出处 hk.cap112.en#s14：Inland Revenue Ordinance (Cap. 112) - whole chapter, English Cap. 112
  - 口径 D32：锚点 7/7 找到原文
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
- **hk.fsie.substance.share_transfer**（D_DISCRETION，2026-12-31）通过
  - 参数 hk.fsie.substance_pure_holding：threshold = 1 bool；hk.cap112.en#s15K（Inland Revenue Ordinance (Cap. 112) - whole chapter, English Cap. 112）「in the Commissioner’s opinion, the e…」
  - 判断出处 hk.cap112.en#s15K：Inland Revenue Ordinance (Cap. 112) - whole chapter, English Cap. 112
  - 参数 hk.fsie.substance_non_pure_holding：threshold = 1 bool；hk.cap112.en#s15K（Inland Revenue Ordinance (Cap. 112) - whole chapter, English Cap. 112）「the total amount of operating expend…」
  - 参数 hk.fsie.substance_exception_income：uses = interest;dividend;non_ip_disposal_gain enum；hk.cap112.en#s15K（Inland Revenue Ordinance (Cap. 112) - whole chapter, English Cap. 112）「the income is interest, a dividend o…」
  - 口径 D32：锚点 7/7 找到原文
- **hk.ftc.unilateral**（A_TEXT，2026-03-31）通过
  - 参数 hk.ftc.unilateral_no_dta：uses = 1 bool；hk.cap112.en#s50AAA（Inland Revenue Ordinance (Cap. 112) - whole chapter, English Cap. 112）「no double taxation arrangements have…」
  - 参数 hk.ftc.unilateral_fsie_only：uses = 1 bool；hk.cap112.en#sch54（Inland Revenue Ordinance (Cap. 112) - whole chapter, English Cap. 112）「the following condition is specified…」
  - 参数 hk.ftc.credit_limit：uses = hk_tax_on_same_income_at_average_rate enum；hk.cap112.en#s50（Inland Revenue Ordinance (Cap. 112) - whole chapter, English Cap. 112）「The credit shall not exceed the amou…」
  - 参数 hk.fsie.intragroup_foreign_tax：uses = 1 bool；hk.cap112.en#s15OA（Inland Revenue Ordinance (Cap. 112) - whole chapter, English Cap. 112）「that foreign tax is, for the purpose…」
- **hk.ftc.unilateral**（A_TEXT，2026-12-31）通过
  - 参数 hk.ftc.unilateral_no_dta：uses = 1 bool；hk.cap112.en#s50AAA（Inland Revenue Ordinance (Cap. 112) - whole chapter, English Cap. 112）「no double taxation arrangements have…」
  - 参数 hk.ftc.unilateral_fsie_only：uses = 1 bool；hk.cap112.en#sch54（Inland Revenue Ordinance (Cap. 112) - whole chapter, English Cap. 112）「the following condition is specified…」
  - 参数 hk.ftc.credit_limit：uses = hk_tax_on_same_income_at_average_rate enum；hk.cap112.en#s50（Inland Revenue Ordinance (Cap. 112) - whole chapter, English Cap. 112）「The credit shall not exceed the amou…」
  - 参数 hk.fsie.intragroup_foreign_tax：uses = 1 bool；hk.cap112.en#s15OA（Inland Revenue Ordinance (Cap. 112) - whole chapter, English Cap. 112）「that foreign tax is, for the purpose…」
- **sg.stamp.buyer**（A_TEXT，2026-12-31）通过
  - 参数 sg.stamp.share_rate：value = 0.2 %；sg.sda1929.sch1#sch1（Stamp Duties Act 1929 - First Schedule (instruments chargeable with stamp duty), single-provision view ）「if executed on or after 22 February …」
  - 参数 sg.stamp.associated_capital_min：threshold = 75 %；sg.sda1929.relief2014.sch1#sch1（Stamp Duties (Relief from Stamp Duty upon Transfer of Assets between Associated Permitted Entities) Rules 2014 - Schedule 1, single-provision view S 28/2014）「75% or more voting capital; and ( b …」
  - 参数 sg.stamp.clawback_years：threshold = 2 years；sg.sda1929.relief2014#s7（Stamp Duties (Relief from Stamp Duty upon Transfer of Assets between Associated Permitted Entities) Rules 2014 (S 28/2014) S 28/2014）「within 2 years from the date of exec…」
  - 参数 sg.stamp.transferee_pays：uses = 1 bool；sg.sda1929.sch3#sch3（Stamp Duties Act 1929 - Third Schedule (persons liable to pay stamp duty), single-provision view ）「The grantee, transferee or lessee」
  - 口径 D18：锚点 10/10 找到原文
  - 口径 D19：锚点 12/12 找到原文

## 事实来源（规则读到的事实，按流）

- cfc:HOLD>ULT：推导（facts.py） 2（direct_ratio、payee_in_source_jur）；推导（引擎） 4（cfc_profit_total、cfc_tax_burden_ratio、cfc_whitelisted、underlying_tax_share）；未给出（规则判为不影响结果） 3（assessment_notice_on、ucmt_location、ucmt_location）；设计或模板设定 1（cfc_share_control）
- exit：推导（facts.py） 12（accrued_in_fsie_regime、associated_ratio、consideration、cost_basis、hk_holding_months、holding_months…）；未给出（规则判为不影响结果） 10（acquirer_chargeable_in_hk、assessment_notice_on、asset_disposed_within_2y、clawback_event_within_2y、determination_on、foreign_tax_rate…）；结构性缺省（按否） 2（shares_cancelled、subject_income_taxed_abroad）；陈述 9（deductible_at_payer、foreign_headline_rate、foreign_taxed、receipt_kind、underlying_profits_taxed、fixed_place_in_sg…）
- up1：推导（facts.py） 6（accrued_in_fsie_regime、hk_holding_months、ratio、hk_resident_or_pe、is_mne_member、payee_in_source_jur）；未给出（规则判为不影响结果） 5（assessment_notice_on、determination_on、foreign_tax_rate、ucmt_location、ucmt_location）；结构性缺省（按否） 1（subject_income_taxed_abroad）；陈述 8（deductible_at_payer、foreign_headline_rate、foreign_taxed、receipt_kind、underlying_profits_taxed、pure_equity_holding…）
- up2：推导（facts.py） 3（capitalised、direct_ratio、payee_in_source_jur）；推导（引擎） 1（underlying_tax_share）；未给出（规则判为不影响结果） 4（assessment_notice_on、capitalised_from、ucmt_location、ucmt_location）

陈述的事实 17 个，附出处 0 个。
