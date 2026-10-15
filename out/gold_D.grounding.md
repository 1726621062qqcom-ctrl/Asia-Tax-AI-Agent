# 依据核对：gold_D

运行 20261014T173555-gold_D，版本 5501a0239aac。规划器给出的是问卷（下面核对的是目前最优的候选）；核对 19 项：通过 14，说明 4，警示 1，失败 0。

**结论**：每一步都落到现行条文的原文；陈述的事实未附出处（0/1）。

候选 {'SERVICER': 'CN', 'payment': False}；保证税额 100.00，最好情形 -140.00；重算一致。

## 需要处理的

- 警示：gold_D 案例陈述的事实 1 个，附出处的 0 个（案例文件没有 provenance，见 案例采集.md §4.2）

## 税项（保证税额一端）

| 流 | 法域 | 税种 | 承担方 | 金额 | 规则 | 依据 |
|---|---|---|---|---|---|---|
| svc | CN | income | SERVICER_NEW | 100.00 | cn.domestic.charge、cn.service.deemed_profit、cn.ftc.direct | 通过 |

## 待机关认可的判断

| 事项 | 流 | 判断所引条款 | 规则 | 依据 | 先例（案例采集.md §5） |
|---|---|---|---|---|---|
| payer.reasonable_service_fee | svc | cn.law.eit#8 | cn.deduct.service | 通过 | 未被压住；不成立最近的先例 CN-js-m-2018（还差 sf_fees_rising、sf_many_labels；多出不利 sf_strategy_claimed） |

## 期限与罚款

| 流 | 规则 | 依据 |
|---|---|---|
| svc | cn.wht.remit | 通过 |

## 问卷的每个问题

| 类别 | 问题 | 由哪条规则提出 | 依据 |
|---|---|---|---|
| blocking | group.group_revenue_eur | data.p2_income | 通过 |

## 规则依据（本方案用到的 5 条规则）

- **cn.deduct.service**（D_DISCRETION，2026-03-31）通过
  - 参数 cn.eit.rate：value = 25 %；cn.law.eit#4（中华人民共和国企业所得税法 ）「企业所得税的税率为25％」
  - 判断出处 cn.law.eit#8：中华人民共和国企业所得税法 
  - 参数 cn.deduct.general：uses = 1 bool；cn.law.eit#8（中华人民共和国企业所得税法 ）「企业实际发生的与取得收入有关的、合理的支出，包括成本、费用、税金、损失和…」
  - 参数 cn.eit.rate_entity：uses = 1 bool；cn.law.eit#28（中华人民共和国企业所得税法 ）「国家需要重点扶持的高新技术企业，减按15％的税率征收企业所得税」
- **cn.domestic.charge**（A_TEXT，2026-03-31）通过
  - 参数 cn.eit.rate：value = 25 %；cn.law.eit#4（中华人民共和国企业所得税法 ）「企业所得税的税率为25％」
  - 参数 cn.eit.resident_worldwide：uses = 1 bool；cn.law.eit#3（中华人民共和国企业所得税法 ）「居民企业应当就其来源于中国境内、境外的所得缴纳企业所得税」
  - 参数 cn.eit.rate_entity：uses = 1 bool；cn.law.eit#28（中华人民共和国企业所得税法 ）「国家需要重点扶持的高新技术企业，减按15％的税率征收企业所得税」
- **cn.ftc.direct**（A_TEXT，2026-03-31）通过
  - 参数 cn.ftc.credit：uses = 1 bool；cn.law.eit#23（中华人民共和国企业所得税法 ）「企业取得的下列所得已在境外缴纳的所得税税额，可以从其当期应纳税额中抵免，…」
  - 参数 cn.ftc.limit_per_country：uses = 1 bool；cn.reg.eit#78（中华人民共和国企业所得税法实施条例 国务院令第512号）「该抵免限额应当分国(地区)不分项计算」
  - 参数 cn.ftc.carryforward_years：uses = 5 years；cn.law.eit#23（中华人民共和国企业所得税法 ）「超过抵免限额的部分，可以在以后五个年度内」
  - 参数 cn.ftc.method_lock_years：uses = 5 years；cn.cs.2017-84#i1（财政部 税务总局关于完善企业境外所得税收抵免政策问题的通知 财税〔2017〕84号）「上述方式一经选择，5年内不得改变」
  - 参数 cn.ftc.not_due_under_treaty_not_creditable：uses = 1 bool；cn.cs.2009-125#i4（财政部 国家税务总局关于企业境外所得税收抵免有关问题的通知 财税〔2009〕125号）「按照税收协定规定不应征收的境外所得税税款」
- **cn.service.deemed_profit**（A_TEXT，2026-03-31）通过
  - 参数 cn.service.deemed_profit_min：uses = 30 %；cn.gsf.2010-19#5（国家税务总局关于印发《非居民企业所得税核定征收管理办法》的通知 国税发〔2010〕19号）「从事管理服务的，利润率为30%-50%」
  - 参数 cn.service.deemed_profit_max：uses = 50 %；cn.gsf.2010-19#5（国家税务总局关于印发《非居民企业所得税核定征收管理办法》的通知 国税发〔2010〕19号）「从事管理服务的，利润率为30%-50%」
  - 参数 cn.service.deemed_profit_design_min：uses = 15 %；cn.gsf.2010-19#5（国家税务总局关于印发《非居民企业所得税核定征收管理办法》的通知 国税发〔2010〕19号）「从事承包工程作业、设计和咨询劳务的，利润率为15%-30%」
  - 参数 cn.service.deemed_profit_design_max：uses = 30 %；cn.gsf.2010-19#5（国家税务总局关于印发《非居民企业所得税核定征收管理办法》的通知 国税发〔2010〕19号）「从事承包工程作业、设计和咨询劳务的，利润率为15%-30%」
  - 参数 cn.service.deemed_profit_other_min：uses = 15 %；cn.gsf.2010-19#5（国家税务总局关于印发《非居民企业所得税核定征收管理办法》的通知 国税发〔2010〕19号）「从事其他劳务或劳务以外经营活动的，利润率不低于15%」
  - 求值器出处 cn.gsf.2010-19#5：国家税务总局关于印发《非居民企业所得税核定征收管理办法》的通知 国税发〔2010〕19号
  - 求值器出处 cn.reg.eit#7：中华人民共和国企业所得税法实施条例 国务院令第512号
- **cn.wht.remit**（A_TEXT，2026-03-31）通过
  - 参数 cn.wht.obligation_date：value = actual payment or date payable text；cn.sta.2017-37#i4（国家税务总局关于非居民企业所得税源泉扣缴有关问题的公告 国家税务总局公告2017年第37号）「扣缴义务发生之日为相关款项实际支付或者到期应支付之日」
  - 参数 cn.wht.remit_days：uses = 7 days；cn.sta.2017-37#i7（国家税务总局关于非居民企业所得税源泉扣缴有关问题的公告 国家税务总局公告2017年第37号）「扣缴义务人应当自扣缴义务发生之日起7日内向扣缴义务人所在地主管税务机关申…」
  - 参数 cn.wht.obligation_date_dividend：uses = actual payment text；cn.sta.2017-37#i7（国家税务总局关于非居民企业所得税源泉扣缴有关问题的公告 国家税务总局公告2017年第37号）「相关应纳税款扣缴义务发生之日为股息、红利等权益性投资收益实际支付之日」
  - 参数 cn.wht.fx_rule：uses = CNY central parity on the obligation date text；cn.sta.2017-37#i4（国家税务总局关于非居民企业所得税源泉扣缴有关问题的公告 国家税务总局公告2017年第37号）「应当按照扣缴义务发生之日人民币汇率中间价折合成人民币」
  - 参数 cn.time.holiday_roll：uses = 1 bool；cn.reg.tca#109（中华人民共和国税收征收管理法实施细则 国务院令第362号（2016年修订））「期限的最后一日是法定休假日的，以休假日期满的次日为期限的最后一日」
  - 参数 cn.time.long_holiday_days：uses = 3 days；cn.reg.tca#109（中华人民共和国税收征收管理法实施细则 国务院令第362号（2016年修订））「在期限内有连续３日以上法定休假日的，按休假日天数顺延」

## 事实来源（规则读到的事实，按流）

- svc：推导（facts.py） 7（cn_related、date_of_payment、parties_treaty、service_consumed_on_site_abroad、service_onshore_share、service_performed_in_source…）；未给出（规则判为不影响结果） 19（arms_length_max、arms_length_value、assessment_notice_on、corresponding_adjustment_granted、input_vat_documents_kept、payable_on…）；陈述 1（service_kind）

陈述的事实 1 个，附出处 0 个。
