# 依据核对：holding_OPCN-ULSG_full_open_y1

运行 20261011T175115-holding_OPCN-ULSG_full_open_y1，版本 cd959f39ab46。规划器给出的是问卷（下面核对的是目前最优的候选）；核对 94 项：通过 57，说明 36，警示 1，失败 0。

**结论**：每一步都落到现行条文的原文；陈述的事实未附出处（0/18）。

候选 {'HOLD': 'SG', 'financing': 'EQUITY', 'payment': False, 'exit_route': 'INDIRECT'}；保证税额 3330812.23，最好情形 3330758.84；重算一致。

## 需要处理的

- 警示：holding_OPCN-ULSG_full_open_y1 案例陈述的事实 18 个，附出处的 0 个（案例文件没有 provenance，见 案例采集.md §4.2）

## 税项（保证税额一端）

| 流 | 法域 | 税种 | 承担方 | 金额 | 规则 | 依据 |
|---|---|---|---|---|---|---|
| up1 | CN | income | HOLD | 100.00 | cn.wht.reduced | 通过 |
| reorg | SG | income | ULT | 70.00 | sg.fsie.charge、sg.fsie.gain.base、sg.ftc.dta | 通过 |
| reorg | CN | income | ULT | 100.00 | cn.wht.reduced、cn.gain.base | 通过 |
| reorg | CN | stamp | ULT | 2.00 | cn.stamp.seller | 通过 |
| reorg | CN | stamp | HOLD | 2.00 | cn.stamp.buyer | 通过 |
| exit | CN | income | ULT | 100.00 | cn.indirect.charge、cn.indirect.gain.base | 通过 |
| exit | SG | stamp | BUYER（集团外） | 10.00 | sg.stamp.buyer | 通过 |
| p2:ULT | SG | income | ULT | 3330438.23 | sg.p2.topup、sg.p2.base | 通过 |

## 方案动作

| 动作 | 依据所在的规则 | 依据 |
|---|---|---|
| HOLD.ftc_pooling_election:is_true | sg.ftc.pooling | 通过 |
| HOLD.residence_cert:is_true | cn-sg.div.cap_qualified@cn | 通过 |
| flow:exit~HOLD-SG.holding_months:ge | sg.gain.s13w | 通过 |
| flow:up1~HOLD-SG.holding_months:ge | cn-sg.div.cap_qualified@cn | 通过 |
| flow:up1~HOLD-SG.receipt_kind:is_in | sg.fsie.charge | 通过 |
| group.p2_tcsh_elected_cn:elect | sg.p2.topup、sg.p2.mtt、sg.p2.base、hk.p2.topup、hk.p2.iir、hk.p2.base | 通过 |

## 待机关认可的判断

| 事项 | 流 | 判断所引条款 | 规则 | 依据 | 先例（案例采集.md §5） |
|---|---|---|---|---|---|
| payee.ppt | up1 | treaty.cn-sg.2007.mli.zh#27 | cn-sg.ppt@cn | 通过 | 无先例卡 |
| payee.reasonable_commercial_purpose_absent | up1 | cn.law.eit#47、cn.reg.eit#120 | cn.gaar | 通过 | 无先例卡 |
| payee.adequate_substance | reorg | sg.ita1947.full#s10L | sg.s10l.gain | 通过 | 未被压住；成立最近的先例 SG-ars-11-2026（还差 sub_parent_controls） |

## 期限与罚款

| 流 | 规则 | 依据 |
|---|---|---|
| up1 | cn.wht.remit | 通过 |
| reorg | cn.wht.remit | 通过 |

## 问卷的每个问题

| 类别 | 问题 | 由哪条规则提出 | 依据 |
|---|---|---|---|
| data | flow:up1~HOLD-SG.benchmark_rate | cn.deduct.interest.benchmark [CN] | 说明 |
| data | flow:up1~HOLD-SG.interest_rate | cn.deduct.interest.benchmark [CN] | 说明 |
| data | flow:up1.benchmark_rate | cn.deduct.interest.benchmark [CN] | 说明 |
| data | flow:up1.interest_rate | cn.deduct.interest.benchmark [CN] | 说明 |
| data | flow:up2~HOLD-CN.foreign_taxed | sg.fsie.exempt [SG]、sg.ftc.pooling [SG] | 说明 |
| action | flow:up1~HOLD-SG.receipt_kind:is_in | sg.fsie.charge | 通过 |
| action | flow:exit~HOLD-SG.holding_months:ge | sg.gain.s13w | 通过 |
| ruling | ULT.exemption_beneficial | sg.fsie.exempt [SG] | 说明 |
| ruling | ULT.adequate_substance | sg.s10l.gain [SG] | 说明 |
| ruling | HOLD.ppt | cn-sg.ppt@cn [CN∩SG] | 说明 |

## 规则依据（本方案用到的 24 条规则）

- **cn-sg.div.cap_other@cn**（D_DISCRETION，2026-03-31）通过
  - 参数 cn-sg.div.cap_other：value = 10 %；treaty.cn-sg.2007.zh#10.2（中华人民共和国政府和新加坡共和国政府关于对所得避免双重征税和防止偷漏税的协定 ）「在其他情况下，不应超过股息总额的百分之十」
  - 参数 cn.bo.safe_harbour：threshold = government;listed_company;individual;wholly_owned_by_these enum；cn.sta.2018-09#i4（国家税务总局关于税收协定中“受益所有人”有关问题的公告 国家税务总局公告2018年第9号）「可不根据本公告第二条规定的因素进行综合分析，直接判定申请人具有“受益所有…」
  - 参数 cn.bo.via_100pct_owner：threshold = 1 bool；cn.sta.2018-09#i3（国家税务总局关于税收协定中“受益所有人”有关问题的公告 国家税务总局公告2018年第9号）「直接或间接持有申请人100%股份的人符合“受益所有人”条件」
  - 参数 cn.bo.onpay_ratio：threshold = 50 %；cn.sta.2018-09#i2（国家税务总局关于税收协定中“受益所有人”有关问题的公告 国家税务总局公告2018年第9号）「申请人有义务在收到所得的12个月内将所得的50%以上支付给第三国（地区）…」
  - 判断出处 cn.sta.2018-09#i2：国家税务总局关于税收协定中“受益所有人”有关问题的公告 国家税务总局公告2018年第9号
  - 参数 cn.treaty.claim_proc：uses = SELF_ASSESS enum；cn.sta.2019-35#3（国家税务总局关于发布《非居民纳税人享受协定待遇管理办法》的公告 国家税务总局公告2019年第35号）「自行判断、申报享受、相关资料留存备查」
  - 参数 cn.bo.onpay_window：uses = 12 months；cn.sta.2018-09#i2（国家税务总局关于税收协定中“受益所有人”有关问题的公告 国家税务总局公告2018年第9号）「在收到所得的12个月内」
- **cn-sg.div.cap_qualified@cn**（D_DISCRETION，2026-03-31）通过
  - 参数 cn-sg.div.cap_qualified：value = 5 %；treaty.cn-sg.2007.zh#10.2（中华人民共和国政府和新加坡共和国政府关于对所得避免双重征税和防止偷漏税的协定 ）「不应超过股息总额的百分之五」
  - 参数 cn-sg.div.ratio_min：threshold = 25 %；treaty.cn-sg.2007.zh#10.2（中华人民共和国政府和新加坡共和国政府关于对所得避免双重征税和防止偷漏税的协定 ）「直接拥有支付股息公司至少百分之二十五资本」
  - 参数 cn.div.holding_months_min：threshold = 12 months；cn.gsh.2009-81#i3（国家税务总局关于执行税收协定股息条款有关问题的通知 国税函〔2009〕81号）「在取得股息前连续12个月以内任何时候均符合税收协定规定的比例」
  - 参数 cn.bo.safe_harbour：threshold = government;listed_company;individual;wholly_owned_by_these enum；cn.sta.2018-09#i4（国家税务总局关于税收协定中“受益所有人”有关问题的公告 国家税务总局公告2018年第9号）「可不根据本公告第二条规定的因素进行综合分析，直接判定申请人具有“受益所有…」
  - 参数 cn.bo.via_100pct_owner：threshold = 1 bool；cn.sta.2018-09#i3（国家税务总局关于税收协定中“受益所有人”有关问题的公告 国家税务总局公告2018年第9号）「直接或间接持有申请人100%股份的人符合“受益所有人”条件」
  - 参数 cn.bo.onpay_ratio：threshold = 50 %；cn.sta.2018-09#i2（国家税务总局关于税收协定中“受益所有人”有关问题的公告 国家税务总局公告2018年第9号）「申请人有义务在收到所得的12个月内将所得的50%以上支付给第三国（地区）…」
  - 判断出处 cn.sta.2018-09#i2：国家税务总局关于税收协定中“受益所有人”有关问题的公告 国家税务总局公告2018年第9号
  - 参数 cn.treaty.claim_proc：uses = SELF_ASSESS enum；cn.sta.2019-35#3（国家税务总局关于发布《非居民纳税人享受协定待遇管理办法》的公告 国家税务总局公告2019年第35号）「自行判断、申报享受、相关资料留存备查」
  - 参数 cn.bo.onpay_window：uses = 12 months；cn.sta.2018-09#i2（国家税务总局关于税收协定中“受益所有人”有关问题的公告 国家税务总局公告2018年第9号）「在收到所得的12个月内」
- **cn-sg.ppt@cn**（D_DISCRETION，2026-03-31）通过
  - 参数 cn-sg.ppt：value = 1 bool；treaty.cn-sg.2007.mli.zh#27（公约（MLI）和中国—新加坡税收协定的整合文本 ）「可以合理地认定就某项所得获取本协定某项优惠是直接或间接 产生该优惠的安排…」
  - 判断出处 treaty.cn-sg.2007.mli.zh#27：公约（MLI）和中国—新加坡税收协定的整合文本 
- **cn.gaar**（D_DISCRETION，2026-03-31）通过
  - 参数 cn.gaar：value = 1 bool；cn.law.eit#47（中华人民共和国企业所得税法 ）「企业实施其他不具有合理商业目的的安排而减少其应纳税收入或者所得额的，税务…」
  - 判断出处 cn.law.eit#47：中华人民共和国企业所得税法 
  - 判断出处 cn.reg.eit#120：中华人民共和国企业所得税法实施条例 国务院令第512号
- **cn.gain.base**（A_TEXT，2026-03-31）通过
  - 参数 cn.wht.base_gain：uses = 1 bool；cn.law.eit#19（中华人民共和国企业所得税法 ）「转让财产所得，以收入全额减除财产净值后的余额为应纳税所得额」
  - 求值器出处 cn.law.eit#16：中华人民共和国企业所得税法 
- **cn.indirect.charge**（D_DISCRETION，2026-12-31）通过
  - 参数 cn.wht.rate：value = 10 %；cn.reg.eit#91（中华人民共和国企业所得税法实施条例 国务院令第512号）「减按10%的税率征收企业所得税」
  - 参数 cn.indirect.value_ratio：threshold = 75 %；cn.sta.2015-07#i4（国家税务总局关于非居民企业间接转让财产企业所得税若干问题的公告 国家税务总局公告2015年第7号）「境外企业股权75%以上价值直接或间接来自于中国应税财产」
  - 参数 cn.indirect.asset_or_income_ratio：threshold = 90 %；cn.sta.2015-07#i4（国家税务总局关于非居民企业间接转让财产企业所得税若干问题的公告 国家税务总局公告2015年第7号）「境外企业资产总额（不含现金）的90%以上直接或间接由在中国境内的投资构成」
  - 判断出处 cn.sta.2015-07#i3：国家税务总局关于非居民企业间接转让财产企业所得税若干问题的公告 国家税务总局公告2015年第7号
- **cn.indirect.gain.base**（A_TEXT，2026-12-31）通过
  - 求值器出处 cn.law.eit#16：中华人民共和国企业所得税法 
- **cn.stamp.buyer**（A_TEXT，2026-03-31）通过
  - 参数 cn.stamp.equity_rate：value = 0.05 %；cn.law.stamp.flk#20（中华人民共和国印花税法（国家法律法规数据库 PDF，含印花税税目税率表） 主席令第八十九号）「价款的万分之五」
  - 参数 cn.stamp.taxpayer_each_party：uses = 1 bool；cn.law.stamp.flk#1（中华人民共和国印花税法（国家法律法规数据库 PDF，含印花税税目税率表） 主席令第八十九号）「应当依照本法规定缴纳印花税」
  - 所依法律的施行条款 cn.law.stamp.flk#20：中华人民共和国印花税法（国家法律法规数据库 PDF，含印花税税目税率表） 主席令第八十九号
  - 口径 D19：锚点 12/12 找到原文
- **cn.stamp.seller**（A_TEXT，2026-03-31）通过
  - 参数 cn.stamp.equity_rate：value = 0.05 %；cn.law.stamp.flk#20（中华人民共和国印花税法（国家法律法规数据库 PDF，含印花税税目税率表） 主席令第八十九号）「价款的万分之五」
  - 参数 cn.stamp.taxpayer_each_party：uses = 1 bool；cn.law.stamp.flk#1（中华人民共和国印花税法（国家法律法规数据库 PDF，含印花税税目税率表） 主席令第八十九号）「应当依照本法规定缴纳印花税」
  - 所依法律的施行条款 cn.law.stamp.flk#20：中华人民共和国印花税法（国家法律法规数据库 PDF，含印花税税目税率表） 主席令第八十九号
  - 口径 D19：锚点 12/12 找到原文
- **cn.wht.reduced**（A_TEXT，2026-03-31）通过
  - 参数 cn.wht.rate：value = 10 %；cn.reg.eit#91（中华人民共和国企业所得税法实施条例 国务院令第512号）「减按10%的税率征收企业所得税」
- **cn.wht.remit**（A_TEXT，2026-03-31）通过
  - 参数 cn.wht.obligation_date：value = actual payment or date payable text；cn.sta.2017-37#i4（国家税务总局关于非居民企业所得税源泉扣缴有关问题的公告 国家税务总局公告2017年第37号）「扣缴义务发生之日为相关款项实际支付或者到期应支付之日」
  - 参数 cn.wht.remit_days：uses = 7 days；cn.sta.2017-37#i7（国家税务总局关于非居民企业所得税源泉扣缴有关问题的公告 国家税务总局公告2017年第37号）「扣缴义务人应当自扣缴义务发生之日起7日内向扣缴义务人所在地主管税务机关申…」
  - 参数 cn.wht.obligation_date_dividend：uses = actual payment text；cn.sta.2017-37#i7（国家税务总局关于非居民企业所得税源泉扣缴有关问题的公告 国家税务总局公告2017年第37号）「相关应纳税款扣缴义务发生之日为股息、红利等权益性投资收益实际支付之日」
  - 参数 cn.wht.fx_rule：uses = CNY central parity on the obligation date text；cn.sta.2017-37#i4（国家税务总局关于非居民企业所得税源泉扣缴有关问题的公告 国家税务总局公告2017年第37号）「应当按照扣缴义务发生之日人民币汇率中间价折合成人民币」
  - 参数 cn.time.holiday_roll：uses = 1 bool；cn.reg.tca#109（中华人民共和国税收征收管理法实施细则 国务院令第362号（2016年修订））「期限的最后一日是法定休假日的，以休假日期满的次日为期限的最后一日」
  - 参数 cn.time.long_holiday_days：uses = 3 days；cn.reg.tca#109（中华人民共和国税收征收管理法实施细则 国务院令第362号（2016年修订））「在期限内有连续３日以上法定休假日的，按休假日天数顺延」
- **hk.p2.base**（A_TEXT，2026-03-31）通过
  - 参数 p2.minimum_rate：uses = 15 %；hk.ord.2025-21#p147（Inland Revenue (Amendment) (Minimum Tax for Multinational Enterprise Groups) Ordinance 2025 Ord. No. 21 of 2025）「Minimum rate (最低稅率) means fifteen pe…」
  - 参数 p2.sbie_payroll_rate：uses = 5 %；hk.ord.2025-21#p86（Inland Revenue (Amendment) (Minimum Tax for Multinational Enterprise Groups) Ordinance 2025 Ord. No. 21 of 2025）「The payroll carve-out for a constitu…」
  - 参数 p2.sbie_tangible_rate：uses = 5 %；hk.ord.2025-21#p87（Inland Revenue (Amendment) (Minimum Tax for Multinational Enterprise Groups) Ordinance 2025 Ord. No. 21 of 2025）「The tangible asset carve-out for a c…」
  - 参数 p2.sbie_payroll_transition：uses = 2023:10;2024:9.8;2025:9.6;2026:9.4;2027:9.2;2028:9.0;2029:8.2;2030:7.4;2031:6.6;2032:5.8 text；hk.ord.2025-21#p120（Inland Revenue (Amendment) (Minimum Tax for Multinational Enterprise Groups) Ordinance 2025 Ord. No. 21 of 2025）「Fiscal Year Beginning In Article 5.3…」
  - 参数 p2.sbie_tangible_transition：uses = 2023:8.0;2024:7.8;2025:7.6;2026:7.4;2027:7.2;2028:7.0;2029:6.6;2030:6.2;2031:5.8;2032:5.4 text；hk.ord.2025-21#p121（Inland Revenue (Amendment) (Minimum Tax for Multinational Enterprise Groups) Ordinance 2025 Ord. No. 21 of 2025）「Article 5.3.4 Rate 2023 8.0% 2024 7.…」
  - 求值器出处 hk.ord.2025-21#p82：Inland Revenue (Amendment) (Minimum Tax for Multinational Enterprise Groups) Ordinance 2025 Ord. No. 21 of 2025
  - 求值器出处 hk.ord.2025-21#p83：Inland Revenue (Amendment) (Minimum Tax for Multinational Enterprise Groups) Ordinance 2025 Ord. No. 21 of 2025
  - 求值器出处 hk.ord.2025-21#p84：Inland Revenue (Amendment) (Minimum Tax for Multinational Enterprise Groups) Ordinance 2025 Ord. No. 21 of 2025
  - 求值器出处 hk.ord.2025-21#p85：Inland Revenue (Amendment) (Minimum Tax for Multinational Enterprise Groups) Ordinance 2025 Ord. No. 21 of 2025
  - 求值器出处 hk.ord.2025-21#p71：Inland Revenue (Amendment) (Minimum Tax for Multinational Enterprise Groups) Ordinance 2025 Ord. No. 21 of 2025
  - 求值器出处 hk.ord.2025-21#p91：Inland Revenue (Amendment) (Minimum Tax for Multinational Enterprise Groups) Ordinance 2025 Ord. No. 21 of 2025
- **hk.p2.iir**（A_TEXT，2026-03-31）通过
  - 参数 p2.minimum_rate：value = 15 %；hk.ord.2025-21#p147（Inland Revenue (Amendment) (Minimum Tax for Multinational Enterprise Groups) Ordinance 2025 Ord. No. 21 of 2025）「Minimum rate (最低稅率) means fifteen pe…」
  - 参数 p2.revenue_threshold：threshold = 750000000 EUR；hk.ord.2025-21#p42（Inland Revenue (Amendment) (Minimum Tax for Multinational Enterprise Groups) Ordinance 2025 Ord. No. 21 of 2025）「annual revenue of EUR 750 million or…」
  - 参数 p2.qualified_iir_hk：threshold = 1 bool；intl.oecd.globe.central-record.2025-12#p7（OECD/G20 Inclusive Framework: Administrative Guidance on the GloBE Rules (Pillar Two) — Central Record of Legislation with Transitional Qualified Status (as at 1 December 2025) ）「Hong Kong (China) Inland Revenue (Am…」
  - 参数 hk.p2.iir_payable_from：uses = 1 bool；hk.ord.2025-21#p22（Inland Revenue (Amendment) (Minimum Tax for Multinational Enterprise Groups) Ordinance 2025 Ord. No. 21 of 2025）「The IIR top-up tax is payable in rel…」
  - 参数 p2.qualified_iir_sg：uses = 1 bool；intl.oecd.globe.central-record.2025-12#p8（OECD/G20 Inclusive Framework: Administrative Guidance on the GloBE Rules (Pillar Two) — Central Record of Legislation with Transitional Qualified Status (as at 1 December 2025) ）「Singapore Multinational Enterprise (…」
  - 口径 D20：锚点 12/12 找到原文
- **hk.p2.topup**（A_TEXT，2026-03-31）通过
  - 参数 p2.minimum_rate：value = 15 %；hk.ord.2025-21#p147（Inland Revenue (Amendment) (Minimum Tax for Multinational Enterprise Groups) Ordinance 2025 Ord. No. 21 of 2025）「Minimum rate (最低稅率) means fifteen pe…」
  - 参数 p2.revenue_threshold：threshold = 750000000 EUR；hk.ord.2025-21#p42（Inland Revenue (Amendment) (Minimum Tax for Multinational Enterprise Groups) Ordinance 2025 Ord. No. 21 of 2025）「annual revenue of EUR 750 million or…」
  - 参数 p2.qualified_iir_hk：threshold = 1 bool；intl.oecd.globe.central-record.2025-12#p7（OECD/G20 Inclusive Framework: Administrative Guidance on the GloBE Rules (Pillar Two) — Central Record of Legislation with Transitional Qualified Status (as at 1 December 2025) ）「Hong Kong (China) Inland Revenue (Am…」
  - 参数 hk.p2.hkmtt：uses = 1 bool；hk.ord.2025-21#p21（Inland Revenue (Amendment) (Minimum Tax for Multinational Enterprise Groups) Ordinance 2025 Ord. No. 21 of 2025）「Schedule 62 has effect for charging …」
  - 口径 D20：锚点 12/12 找到原文
- **sg.fsie.charge**（A_TEXT，2026-03-31）通过
  - 参数 sg.corp.rate：value = 17 %；sg.ita1947.full#s43（Income Tax Act 1947 (assembled whole-document HTML: base page + 36 lazy-load fragments) ）「every company or body of persons, ta…」
  - 参数 sg.fsie.receipt_kinds：threshold = REMITTED;DEBT_SETTLED;MOVABLE_PROPERTY enum；sg.ita1947.full#s10（Income Tax Act 1947 (assembled whole-document HTML: base page + 36 lazy-load fragments) ）「any amount from any income derived f…」
  - 参数 sg.charge.basis：uses = accruing_in_or_derived_from_sg;received_in_sg_from_outside enum；sg.ita1947.full#s10（Income Tax Act 1947 (assembled whole-document HTML: base page + 36 lazy-load fragments) ）「upon the income of any person accrui…」
  - 参数 sg.foreign_income.remittance_is_receipt：uses = 1 bool；sg.ita1947.full#s10（Income Tax Act 1947 (assembled whole-document HTML: base page + 36 lazy-load fragments) ）「any amount from any income derived f…」
  - 参数 sg.fsie.recipient：uses = 1 bool；sg.ita1947.full#s13（Income Tax Act 1947 (assembled whole-document HTML: base page + 36 lazy-load fragments) ）「on or after 1 June 2003 by any perso…」
  - 参数 sg.corp.rate_entity：uses = 1 bool；sg.ita1947.full#s43（Income Tax Act 1947 (assembled whole-document HTML: base page + 36 lazy-load fragments) ）「for every dollar of the first $10,00…」
- **sg.fsie.gain.base**（A_TEXT，2026-03-31）通过
  - 求值器出处 sg.ita1947.full#s10：Income Tax Act 1947 (assembled whole-document HTML: base page + 36 lazy-load fragments) 
- **sg.ftc.dta**（A_TEXT，2026-03-31）通过
  - 参数 sg.ftc.credit_limit：uses = sg_tax_on_same_income_at_average_rate enum；sg.ita1947.full#s50（Income Tax Act 1947 (assembled whole-document HTML: base page + 36 lazy-load fragments) ）「The credit must not exceed the amoun…」
  - 参数 sg.ftc.tax_payable_under_arrangements：uses = 1 bool；sg.ita1947.full#s50（Income Tax Act 1947 (assembled whole-document HTML: base page + 36 lazy-load fragments) ）「tax payable in respect of any income…」
- **sg.ftc.pooling**（A_TEXT，2026-03-31）通过
  - 参数 sg.ftc.pooling_election：threshold = 1 bool；sg.ita1947.full#s50C（Income Tax Act 1947 (assembled whole-document HTML: base page + 36 lazy-load fragments) ）「the person may elect to be given a p…」
  - 参数 sg.ftc.pooling_foreign_tax_paid：threshold = 1 bool；sg.ita1947.full#s50C（Income Tax Act 1947 (assembled whole-document HTML: base page + 36 lazy-load fragments) ）「income tax (by whatever name called)…」
  - 参数 sg.ftc.pooling_headline_rate_min：threshold = 15 %；sg.ita1947.full#s50C（Income Tax Act 1947 (assembled whole-document HTML: base page + 36 lazy-load fragments) ）「carried on by a company in that terr…」
  - 参数 sg.ftc.pooling_sg_tax_not_nil：uses = 1 bool；sg.ita1947.full#s50C（Income Tax Act 1947 (assembled whole-document HTML: base page + 36 lazy-load fragments) ）「the income tax payable under this Ac…」
- **sg.gain.s13w**（A_TEXT，2026-12-31）通过
  - 参数 sg.s13w.ratio_min：threshold = 20 %；sg.ita1947.full#s13W（Income Tax Act 1947 (assembled whole-document HTML: base page + 36 lazy-load fragments) ）「legally and beneficially owned at le…」
  - 参数 sg.s13w.holding_months_min：threshold = 24 months；sg.ita1947.full#s13W（Income Tax Act 1947 (assembled whole-document HTML: base page + 36 lazy-load fragments) ）「at all times during a continuous per…」
- **sg.p2.base**（A_TEXT，2026-03-31）通过
  - 参数 sg.p2.minimum_rate：uses = 15 %；sg.memta2024.s7#s7（Multinational Enterprise (Minimum Tax) Act 2024 - section 7 (Minimum rate), single-provision view ）「The minimum rate is 15%.」
  - 求值器出处 sg.memta2024.s16#s16：Multinational Enterprise (Minimum Tax) Act 2024 - section 16 (Top-up amounts of constituent entities other than special entities), single-provision view 
  - 求值器出处 sg.memta2024.s17#s17：Multinational Enterprise (Minimum Tax) Act 2024 - section 17 (Effective tax rate for constituent entities other than special entities), single-provision view 
  - 求值器出处 sg.memta2024.s21#s21：Multinational Enterprise (Minimum Tax) Act 2024 - section 21 (Additional current top-up amount for constituent entities other than special entities), single-provision view 
  - 求值器出处 sg.memta2024.s30#s30：Multinational Enterprise (Minimum Tax) Act 2024 - section 30 (Top-up amounts of constituent entities), single-provision view 
- **sg.p2.base**（A_TEXT，2027-01-02）通过
  - 参数 sg.p2.minimum_rate：uses = 15 %；sg.memta2024.s7#s7（Multinational Enterprise (Minimum Tax) Act 2024 - section 7 (Minimum rate), single-provision view ）「The minimum rate is 15%.」
  - 求值器出处 sg.memta2024.s16#s16：Multinational Enterprise (Minimum Tax) Act 2024 - section 16 (Top-up amounts of constituent entities other than special entities), single-provision view 
  - 求值器出处 sg.memta2024.s17#s17：Multinational Enterprise (Minimum Tax) Act 2024 - section 17 (Effective tax rate for constituent entities other than special entities), single-provision view 
  - 求值器出处 sg.memta2024.s21#s21：Multinational Enterprise (Minimum Tax) Act 2024 - section 21 (Additional current top-up amount for constituent entities other than special entities), single-provision view 
  - 求值器出处 sg.memta2024.s30#s30：Multinational Enterprise (Minimum Tax) Act 2024 - section 30 (Top-up amounts of constituent entities), single-provision view 
- **sg.p2.mtt**（A_TEXT，2026-03-31）通过
  - 参数 sg.p2.minimum_rate：value = 15 %；sg.memta2024.s7#s7（Multinational Enterprise (Minimum Tax) Act 2024 - section 7 (Minimum rate), single-provision view ）「The minimum rate is 15%.」
  - 参数 sg.p2.revenue_threshold：threshold = 750000000 EUR；sg.memta2024.s8#s8（Multinational Enterprise (Minimum Tax) Act 2024 - section 8 (MNE group to which this Act applies), single-provision view ）「A is EUR 750 million or its equivale…」
  - 参数 p2.qualified_iir_sg：threshold = 1 bool；intl.oecd.globe.central-record.2025-12#p8（OECD/G20 Inclusive Framework: Administrative Guidance on the GloBE Rules (Pillar Two) — Central Record of Legislation with Transitional Qualified Status (as at 1 December 2025) ）「Singapore Multinational Enterprise (…」
  - 参数 sg.p2.mtt_chargeable_entity：uses = 1 bool；sg.memta2024.s12#s12（Multinational Enterprise (Minimum Tax) Act 2024 - section 12 (Part 2, multinational enterprise minimum tax), single-provision view ）「An entity (called in this Act a char…」
  - 参数 p2.qualified_iir_hk：uses = 1 bool；intl.oecd.globe.central-record.2025-12#p7（OECD/G20 Inclusive Framework: Administrative Guidance on the GloBE Rules (Pillar Two) — Central Record of Legislation with Transitional Qualified Status (as at 1 December 2025) ）「Hong Kong (China) Inland Revenue (Am…」
  - 口径 D20：锚点 12/12 找到原文
- **sg.p2.topup**（A_TEXT，2026-03-31）通过
  - 参数 sg.p2.minimum_rate：value = 15 %；sg.memta2024.s7#s7（Multinational Enterprise (Minimum Tax) Act 2024 - section 7 (Minimum rate), single-provision view ）「The minimum rate is 15%.」
  - 参数 sg.p2.revenue_threshold：threshold = 750000000 EUR；sg.memta2024.s8#s8（Multinational Enterprise (Minimum Tax) Act 2024 - section 8 (MNE group to which this Act applies), single-provision view ）「A is EUR 750 million or its equivale…」
  - 参数 p2.qualified_iir_sg：threshold = 1 bool；intl.oecd.globe.central-record.2025-12#p8（OECD/G20 Inclusive Framework: Administrative Guidance on the GloBE Rules (Pillar Two) — Central Record of Legislation with Transitional Qualified Status (as at 1 December 2025) ）「Singapore Multinational Enterprise (…」
  - 参数 sg.p2.dtt：uses = 1 bool；sg.memta2024.s28#s28（Multinational Enterprise (Minimum Tax) Act 2024 - section 28 (DTT payable in respect of MNE group and amount of DTT), single-provision view ）「DTT is payable in respect of an MNE …」
  - 口径 D20：锚点 12/12 找到原文
- **sg.p2.topup**（A_TEXT，2027-01-02）通过
  - 参数 sg.p2.minimum_rate：value = 15 %；sg.memta2024.s7#s7（Multinational Enterprise (Minimum Tax) Act 2024 - section 7 (Minimum rate), single-provision view ）「The minimum rate is 15%.」
  - 参数 sg.p2.revenue_threshold：threshold = 750000000 EUR；sg.memta2024.s8#s8（Multinational Enterprise (Minimum Tax) Act 2024 - section 8 (MNE group to which this Act applies), single-provision view ）「A is EUR 750 million or its equivale…」
  - 参数 p2.qualified_iir_sg：threshold = 1 bool；intl.oecd.globe.central-record.2025-12#p8（OECD/G20 Inclusive Framework: Administrative Guidance on the GloBE Rules (Pillar Two) — Central Record of Legislation with Transitional Qualified Status (as at 1 December 2025) ）「Singapore Multinational Enterprise (…」
  - 参数 sg.p2.dtt：uses = 1 bool；sg.memta2024.s28#s28（Multinational Enterprise (Minimum Tax) Act 2024 - section 28 (DTT payable in respect of MNE group and amount of DTT), single-provision view ）「DTT is payable in respect of an MNE …」
  - 口径 D20：锚点 12/12 找到原文
- **sg.s10l.gain**（D_DISCRETION，2026-03-31）通过
  - 参数 sg.s10l.relevant_group_entity：threshold = 1 bool；sg.ita1947.full#s10L（Income Tax Act 1947 (assembled whole-document HTML: base page + 36 lazy-load fragments) ）「gains from the sale or disposal by a…」
  - 参数 sg.s10l.excluded_entity：threshold = 1 bool；sg.ita1947.full#s10L（Income Tax Act 1947 (assembled whole-document HTML: base page + 36 lazy-load fragments) ）「carried out by an entity that is an …」
  - 判断出处 sg.ita1947.full#s10L：Income Tax Act 1947 (assembled whole-document HTML: base page + 36 lazy-load fragments) 
  - 参数 sg.s10l.received_in_sg_trigger：uses = 1 bool；sg.ita1947.full#s10L（Income Tax Act 1947 (assembled whole-document HTML: base page + 36 lazy-load fragments) ）「that are received in Singapore from …」
  - 参数 sg.s10l.substance_pure_holding：uses = 1 bool；sg.ita1947.full#s10L（Income Tax Act 1947 (assembled whole-document HTML: base page + 36 lazy-load fragments) ）「the entity has adequate human resour…」
  - 参数 sg.s10l.substance_non_pure_holding：uses = 1 bool；sg.ita1947.full#s10L（Income Tax Act 1947 (assembled whole-document HTML: base page + 36 lazy-load fragments) ）「the entity has adequate economic sub…」
  - 参数 sg.s10l.share_situs：uses = place_of_incorporation enum；sg.ita1947.full#s10L（Income Tax Act 1947 (assembled whole-document HTML: base page + 36 lazy-load fragments) ）「any shares in or securities issued b…」
- **sg.stamp.buyer**（A_TEXT，2026-12-31）通过
  - 参数 sg.stamp.share_rate：value = 0.2 %；sg.sda1929.sch1#sch1（Stamp Duties Act 1929 - First Schedule (instruments chargeable with stamp duty), single-provision view ）「if executed on or after 22 February …」
  - 参数 sg.stamp.associated_capital_min：threshold = 75 %；sg.sda1929.relief2014.sch1#sch1（Stamp Duties (Relief from Stamp Duty upon Transfer of Assets between Associated Permitted Entities) Rules 2014 - Schedule 1, single-provision view S 28/2014）「75% or more voting capital; and ( b …」
  - 参数 sg.stamp.clawback_years：threshold = 2 years；sg.sda1929.relief2014#s7（Stamp Duties (Relief from Stamp Duty upon Transfer of Assets between Associated Permitted Entities) Rules 2014 (S 28/2014) S 28/2014）「within 2 years from the date of exec…」
  - 参数 sg.stamp.transferee_pays：uses = 1 bool；sg.sda1929.sch3#sch3（Stamp Duties Act 1929 - Third Schedule (persons liable to pay stamp duty), single-provision view ）「The grantee, transferee or lessee」
  - 口径 D18：锚点 10/10 找到原文
  - 口径 D19：锚点 12/12 找到原文

## 事实来源（规则读到的事实，按流）

- exit：推导（facts.py） 8（associated_ratio、consideration、cost_basis、indirect_cn_target、ratio、is_relevant_group_entity…）；方案动作 2（holding_months、receipt_kind）；未给出（规则判为不影响结果） 5（assessment_notice_on、asset_disposed_within_2y、clawback_event_within_2y、cn_cost_basis、stamp_relief_claimed）；结构性缺省（按否） 1（shares_cancelled）；陈述 11（cn_asset_ratio、cn_income_ratio、cn_value_ratio、foreign_tax_lower_than_cn、intragroup_reorg_ratio、later_cn_tax_not_reduced…）
- p2:ULT：推导（facts.py） 1（payee_in_source_jur）；推导（引擎） 1（p2_etr）；方案动作 1（receipt_kind）；未给出（规则判为不影响结果） 2（assessment_notice_on、p2_additional）；结构性缺省（按否） 1（p2_iir）；陈述 1（group_revenue_eur）
- reorg：推导（facts.py） 13（authority_action、consideration、date_of_payment、prior_map_outcome、reorg_acquired_ratio、reorg_buyer_resident_in_cn…）；方案动作 2（receipt_kind、residence_cert）；未给出（规则判为不影响结果） 11（assessment_notice_on、cn_cost_basis、first_notification_on、foreign_tax_rate、payable_on、remitted_on…）；结构性缺省（按否） 1（shares_cancelled）；设计或模板设定 3（cost_basis、max_ratio_12m、reorg_step）；陈述 2（immovable_ratio、is_excluded_entity）
- up1：推导（facts.py） 8（authority_action、date_of_payment、direct_ratio、prior_map_outcome、reorg_special_applied、bo_via_100pct_owner…）；推导（引擎） 1（reorg_same_residence）；方案动作 3（holding_months、receipt_kind、residence_cert）；未给出（规则判为不影响结果） 12（assessment_notice_on、direct_payment、dividend_from_pre_reorg_profits、first_notification_on、foreign_tax_rate、payable_on…）；陈述 3（foreign_headline_rate、foreign_taxed、reinvested_in_cn）
- up2：推导（facts.py） 1（payee_in_source_jur）；方案动作 1（receipt_kind）；未定（按两端计） 1（foreign_taxed）；未给出（规则判为不影响结果） 1（assessment_notice_on）；陈述 1（foreign_headline_rate）

陈述的事实 18 个，附出处 0 个。
