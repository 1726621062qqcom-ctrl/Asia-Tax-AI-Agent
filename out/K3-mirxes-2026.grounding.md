# 依据核对：K3-mirxes-2026

运行 20261014T214152-K3-mirxes-2026，版本 be566a8fb554。规划器给出的是问卷（下面核对的是目前最优的候选）；核对 28 项：通过 20，说明 8，警示 0，失败 0。

**结论**：每一步都落到现行条文的原文；陈述的事实都附出处。

候选 {'HOLD': None, 'financing': 'EQUITY', 'payment': False}；保证税额 1700000.00，最好情形 0.00；重算一致。

## 税项（保证税额一端）

| 流 | 法域 | 税种 | 承担方 | 金额 | 规则 | 依据 |
|---|---|---|---|---|---|---|
| up1 | SG | income | ULT | 700000.00 | sg.fsie.charge、sg.ftc.dta | 通过 |
| up1 | CN | income | ULT | 1000000.00 | cn.wht.reduced | 通过 |

## 方案动作

| 动作 | 依据所在的规则 | 依据 |
|---|---|---|
| flow:up1.planned_holding_months:ge | cn.reinvest.credit | 通过 |

## 待机关认可的判断

| 事项 | 流 | 判断所引条款 | 规则 | 依据 | 先例（案例采集.md §5） |
|---|---|---|---|---|---|
| payee.no_adverse_bo_factors | up1 | cn.sta.2018-09#i2 | cn-sg.div.cap_qualified@cn | 通过 | 未被压住；不成立最近的先例 CN-jd9-rhq-8staff（还差 bo_too_few_staff；多出不利 bo_reinvests、bo_regional_functions、bo_funds_raised_locally、bo_many_staff）；成立最近的先例 CN-jd9-reinvest（还差 bo_reinvests；多出不利 bo_pays_out、bo_staff_not_own、bo_income_idle、bo_directors_by_parent、bo_too_few_staff、bo_unexplained_shift、bo_other_income_small、bo_single_investment、bo_no_investment_records、bo_director_abroad、bo_related_loan_payout、bo_not_taxed_home） |
| payee.ppt | up1 | treaty.cn-sg.2007.mli.zh#27 | cn-sg.ppt@cn | 通过 | 无先例卡 |
| payee.reasonable_commercial_purpose_absent | up1 | cn.law.eit#47、cn.reg.eit#120 | cn.gaar | 通过 | 无先例卡 |
| payee.exemption_beneficial | up1 | sg.ita1947.full#s13 | sg.fsie.exempt | 通过 | 无先例卡 |

## 期限与罚款

| 流 | 规则 | 依据 |
|---|---|---|
| up1 | cn.wht.remit | 通过 |

## 问卷的每个问题

| 类别 | 问题 | 由哪条规则提出 | 依据 |
|---|---|---|---|
| data | flow:up1.receipt_kind | sg.fsie.charge [SG] | 说明 |
| ruling | ULT.exemption_beneficial | sg.fsie.exempt [SG] | 说明 |

## 规则依据（本方案用到的 9 条规则）

- **cn-sg.div.cap_qualified@cn**（D_DISCRETION，2026-06-14）通过
  - 参数 cn-sg.div.cap_qualified：value = 5 %；treaty.cn-sg.2007.zh#10.2（中华人民共和国政府和新加坡共和国政府关于对所得避免双重征税和防止偷漏税的协定 ）「不应超过股息总额的百分之五」
  - 参数 cn-sg.div.ratio_min：threshold = 25 %；treaty.cn-sg.2007.zh#10.2（中华人民共和国政府和新加坡共和国政府关于对所得避免双重征税和防止偷漏税的协定 ）「直接拥有支付股息公司至少百分之二十五资本」
  - 参数 cn.div.holding_months_min：threshold = 12 months；cn.gsh.2009-81#i3（国家税务总局关于执行税收协定股息条款有关问题的通知 国税函〔2009〕81号）「在取得股息前连续12个月以内任何时候均符合税收协定规定的比例」
  - 参数 cn.bo.safe_harbour：threshold = government;listed_company;individual;wholly_owned_by_these enum；cn.sta.2018-09#i4（国家税务总局关于税收协定中“受益所有人”有关问题的公告 国家税务总局公告2018年第9号）「可不根据本公告第二条规定的因素进行综合分析，直接判定申请人具有“受益所有…」
  - 参数 cn.bo.via_100pct_owner：threshold = 1 bool；cn.sta.2018-09#i3（国家税务总局关于税收协定中“受益所有人”有关问题的公告 国家税务总局公告2018年第9号）「直接或间接持有申请人100%股份的人符合“受益所有人”条件」
  - 参数 cn.bo.onpay_ratio：threshold = 50 %；cn.sta.2018-09#i2（国家税务总局关于税收协定中“受益所有人”有关问题的公告 国家税务总局公告2018年第9号）「申请人有义务在收到所得的12个月内将所得的50%以上支付给第三国（地区）…」
  - 判断出处 cn.sta.2018-09#i2：国家税务总局关于税收协定中“受益所有人”有关问题的公告 国家税务总局公告2018年第9号
  - 参数 cn.treaty.claim_proc：uses = SELF_ASSESS enum；cn.sta.2019-35#3（国家税务总局关于发布《非居民纳税人享受协定待遇管理办法》的公告 国家税务总局公告2019年第35号）「自行判断、申报享受、相关资料留存备查」
  - 参数 cn.bo.onpay_window：uses = 12 months；cn.sta.2018-09#i2（国家税务总局关于税收协定中“受益所有人”有关问题的公告 国家税务总局公告2018年第9号）「在收到所得的12个月内」
- **cn-sg.ppt@cn**（D_DISCRETION，2026-06-14）通过
  - 参数 cn-sg.ppt：value = 1 bool；treaty.cn-sg.2007.mli.zh#27（公约（MLI）和中国—新加坡税收协定的整合文本 ）「可以合理地认定就某项所得获取本协定某项优惠是直接或间接 产生该优惠的安排…」
  - 判断出处 treaty.cn-sg.2007.mli.zh#27：公约（MLI）和中国—新加坡税收协定的整合文本 
- **cn.gaar**（D_DISCRETION，2026-06-14）通过
  - 参数 cn.gaar：value = 1 bool；cn.law.eit#47（中华人民共和国企业所得税法 ）「企业实施其他不具有合理商业目的的安排而减少其应纳税收入或者所得额的，税务…」
  - 判断出处 cn.law.eit#47：中华人民共和国企业所得税法 
  - 判断出处 cn.reg.eit#120：中华人民共和国企业所得税法实施条例 国务院令第512号
- **cn.reinvest.credit**（A_TEXT，2026-06-14）通过
  - 参数 cn.reinvest.credit_rate：value = 10 %；cn.cs.2025-02#i1（财政部 税务总局 商务部关于境外投资者以分配利润直接投资税收抵免政策的公告 财政部 税务总局 商务部公告2025年第2号）「可按照投资额的10%抵免境外投资者当年的应纳税额，当年不足抵免的准予向以…」
  - 参数 cn.reinvest.forms：threshold = capital_increase;new_entity;unrelated_acquisition text；cn.cs.2018-102#i2（财政部 税务总局 国家发展改革委 商务部关于扩大境外投资者以分配利润直接投资暂不征收预提所得税政策适用范围的通知 财税〔2018〕102号）「1.新增或转增中国境内居民企业实收资本或者资本公积； 2.在中国境内投资…」
  - 参数 cn.reinvest.direct_payment：threshold = 1 bool；cn.cs.2018-102#i2（财政部 税务总局 国家发展改革委 商务部关于扩大境外投资者以分配利润直接投资暂不征收预提所得税政策适用范围的通知 财税〔2018〕102号）「相关款项从利润分配企业的账户直接转入被投资企业或股权转让方账户，在直接投…」
  - 参数 cn.reinvest.credit_encouraged_industry：threshold = 1 bool；cn.cs.2025-02#i2（财政部 税务总局 商务部关于境外投资者以分配利润直接投资税收抵免政策的公告 财政部 税务总局 商务部公告2025年第2号）「被投资企业从事的产业属于《鼓励外商投资产业目录》所列的全国鼓励外商投资产…」
  - 参数 cn.reinvest.credit_min_holding_months：threshold = 60 months；cn.cs.2025-02#i2（财政部 税务总局 商务部关于境外投资者以分配利润直接投资税收抵免政策的公告 财政部 税务总局 商务部公告2025年第2号）「境外投资者境内再投资需连续持有至少5年（60个月）以上」
  - 参数 cn.reinvest.credit_rate_treaty_lower：uses = 1 bool；cn.cs.2025-02#i1（财政部 税务总局 商务部关于境外投资者以分配利润直接投资税收抵免政策的公告 财政部 税务总局 商务部公告2025年第2号）「税收协定中关于股息、红利等权益性投资收益适用税率低于10%的，按照协定税…」
  - 参数 cn.reinvest.credit_against：uses = 1 bool；cn.cs.2025-02#i3（财政部 税务总局 商务部关于境外投资者以分配利润直接投资税收抵免政策的公告 财政部 税务总局 商务部公告2025年第2号）「境外投资者从利润分配企业自利润分配再投资之日以后取得的企业所得税法第三条…」
  - 参数 cn.reinvest.credit_recapture_days：uses = 7 days；cn.cs.2025-02#i5（财政部 税务总局 商务部关于境外投资者以分配利润直接投资税收抵免政策的公告 财政部 税务总局 商务部公告2025年第2号）「应在收回投资后7日内向利润分配企业所在地税务机关申报补缴递延的税款」
  - 参数 cn.reinvest.credit_early_withdrawal_reduces：uses = 1 bool；cn.cs.2025-02#i5（财政部 税务总局 商务部关于境外投资者以分配利润直接投资税收抵免政策的公告 财政部 税务总局 商务部公告2025年第2号）「还应按比例减少境外投资者可享受的税收抵免额度」
  - 参数 cn.reinvest.credit_fx：uses = CNY central parity on the payment date text；cn.sta.2025-18#i6（国家税务总局关于境外投资者以分配利润直接投资税收抵免政策有关事项的公告 国家税务总局公告2025年第18号）「按实际支付相关款项之日的汇率中间价折合成人民币」
  - 参数 cn.reinvest.credit_holding_stop：uses = 1 bool；cn.sta.2025-18#i3（国家税务总局关于境外投资者以分配利润直接投资税收抵免政策有关事项的公告 国家税务总局公告2025年第18号）「以被投资企业完成股权变更或注销登记手续当月，确认停止计算其持有该再投资被…」
- **cn.wht.reduced**（A_TEXT，2026-06-14）通过
  - 参数 cn.wht.rate：value = 10 %；cn.reg.eit#91（中华人民共和国企业所得税法实施条例 国务院令第512号）「减按10%的税率征收企业所得税」
- **cn.wht.remit**（A_TEXT，2026-06-14）通过
  - 参数 cn.wht.obligation_date：value = actual payment or date payable text；cn.sta.2017-37#i4（国家税务总局关于非居民企业所得税源泉扣缴有关问题的公告 国家税务总局公告2017年第37号）「扣缴义务发生之日为相关款项实际支付或者到期应支付之日」
  - 参数 cn.wht.remit_days：uses = 7 days；cn.sta.2017-37#i7（国家税务总局关于非居民企业所得税源泉扣缴有关问题的公告 国家税务总局公告2017年第37号）「扣缴义务人应当自扣缴义务发生之日起7日内向扣缴义务人所在地主管税务机关申…」
  - 参数 cn.wht.obligation_date_dividend：uses = actual payment text；cn.sta.2017-37#i7（国家税务总局关于非居民企业所得税源泉扣缴有关问题的公告 国家税务总局公告2017年第37号）「相关应纳税款扣缴义务发生之日为股息、红利等权益性投资收益实际支付之日」
  - 参数 cn.wht.fx_rule：uses = CNY central parity on the obligation date text；cn.sta.2017-37#i4（国家税务总局关于非居民企业所得税源泉扣缴有关问题的公告 国家税务总局公告2017年第37号）「应当按照扣缴义务发生之日人民币汇率中间价折合成人民币」
  - 参数 cn.time.holiday_roll：uses = 1 bool；cn.reg.tca#109（中华人民共和国税收征收管理法实施细则 国务院令第362号（2016年修订））「期限的最后一日是法定休假日的，以休假日期满的次日为期限的最后一日」
  - 参数 cn.time.long_holiday_days：uses = 3 days；cn.reg.tca#109（中华人民共和国税收征收管理法实施细则 国务院令第362号（2016年修订））「在期限内有连续３日以上法定休假日的，按休假日天数顺延」
- **sg.fsie.charge**（A_TEXT，2026-06-14）通过
  - 参数 sg.corp.rate：value = 17 %；sg.ita1947.full#s43（Income Tax Act 1947 (assembled whole-document HTML: base page + 36 lazy-load fragments) ）「every company or body of persons, ta…」
  - 参数 sg.fsie.receipt_kinds：threshold = REMITTED;DEBT_SETTLED;MOVABLE_PROPERTY enum；sg.ita1947.full#s10（Income Tax Act 1947 (assembled whole-document HTML: base page + 36 lazy-load fragments) ）「any amount from any income derived f…」
  - 参数 sg.charge.basis：uses = accruing_in_or_derived_from_sg;received_in_sg_from_outside enum；sg.ita1947.full#s10（Income Tax Act 1947 (assembled whole-document HTML: base page + 36 lazy-load fragments) ）「upon the income of any person accrui…」
  - 参数 sg.foreign_income.remittance_is_receipt：uses = 1 bool；sg.ita1947.full#s10（Income Tax Act 1947 (assembled whole-document HTML: base page + 36 lazy-load fragments) ）「any amount from any income derived f…」
  - 参数 sg.fsie.recipient：uses = 1 bool；sg.ita1947.full#s13（Income Tax Act 1947 (assembled whole-document HTML: base page + 36 lazy-load fragments) ）「on or after 1 June 2003 by any perso…」
  - 参数 sg.corp.rate_entity：uses = 1 bool；sg.ita1947.full#s43（Income Tax Act 1947 (assembled whole-document HTML: base page + 36 lazy-load fragments) ）「for every dollar of the first $10,00…」
- **sg.fsie.exempt**（D_DISCRETION，2026-06-14）通过
  - 参数 sg.fsie.subject_to_tax：threshold = 1 bool；sg.ita1947.full#s13（Income Tax Act 1947 (assembled whole-document HTML: base page + 36 lazy-load fragments) ）「the income is subject to tax of a si…」
  - 参数 sg.fsie.headline_rate_min：threshold = 15 %；sg.ita1947.full#s13（Income Tax Act 1947 (assembled whole-document HTML: base page + 36 lazy-load fragments) ）「is not less than 15%」
  - 判断出处 sg.ita1947.full#s13：Income Tax Act 1947 (assembled whole-document HTML: base page + 36 lazy-load fragments) 
  - 参数 sg.fsie.beneficial：uses = 1 bool；sg.ita1947.full#s13（Income Tax Act 1947 (assembled whole-document HTML: base page + 36 lazy-load fragments) ）「the Comptroller is satisfied that th…」
  - 参数 sg.fsie.ministerial_order：uses = 1 bool；sg.ita1947.full#s13（Income Tax Act 1947 (assembled whole-document HTML: base page + 36 lazy-load fragments) ）「the income received by a person resi…」
- **sg.ftc.dta**（A_TEXT，2026-06-14）通过
  - 参数 sg.ftc.credit_limit：uses = sg_tax_on_same_income_at_average_rate enum；sg.ita1947.full#s50（Income Tax Act 1947 (assembled whole-document HTML: base page + 36 lazy-load fragments) ）「The credit must not exceed the amoun…」
  - 参数 sg.ftc.tax_payable_under_arrangements：uses = 1 bool；sg.ita1947.full#s50（Income Tax Act 1947 (assembled whole-document HTML: base page + 36 lazy-load fragments) ）「tax payable in respect of any income…」

## 事实来源（规则读到的事实，按流）

- up1：推导（facts.py） 11（authority_action、capitalised、date_of_payment、direct_ratio、holding_months、prior_map_outcome…）；未定（按两端计） 8（direct_payment、receipt_kind、reinvested_in_cn、reinvestment_form、reinvestment_from_distributed_profit、reinvestment_withdrawn…）；未给出（规则判为不影响结果） 13（assessment_notice_on、capitalised_from、dividend_from_pre_reorg_profits、first_notification_on、foreign_tax_rate、payable_on…）；陈述（有出处） 2（foreign_headline_rate、foreign_taxed）

陈述的事实 2 个，附出处 2 个。
