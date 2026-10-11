# 依据核对：meridian

运行 20261011T143101-meridian，版本 a7b5cac57b68。规划器给出的是问卷（下面核对的是目前最优的候选）；核对 28 项：通过 23，说明 4，警示 1，失败 0。

**结论**：每一步都落到现行条文的原文；陈述的事实未附出处（0/9）。

候选 {}；保证税额 100000.00，最好情形 51000.00；重算一致。

## 需要处理的

- 警示：meridian 案例陈述的事实 9 个，附出处的 0 个（案例文件没有 provenance，见 案例采集.md §4.2）

## 税项（保证税额一端）

| 流 | 法域 | 税种 | 承担方 | 金额 | 规则 | 依据 |
|---|---|---|---|---|---|---|
| fee | CN | income | SERVICER | 100000.00 | cn.wht.service_as_royalty | 通过 |

## 待机关认可的判断

| 事项 | 流 | 判断所引条款 | 规则 | 依据 |
|---|---|---|---|---|
| payee.ppt | fee | treaty.cn-sg.2007.mli.zh#27 | cn-sg.ppt@cn | 通过 |
| payer.reasonable_service_fee | fee | cn.law.eit#8 | cn.deduct.service | 通过 |
| payee.service_fee_is_royalty_for_know_how | fee | cn.gsh.2009-507#i4、cn.gsh.2009-507#i6 | cn.wht.service_as_royalty | 通过 |

## 期限与罚款

| 流 | 规则 | 依据 |
|---|---|---|
| fee | cn.wht.remit | 通过 |
| fee | cn.refund | 通过 |
| fee | cn.wht.late_surcharge | 通过 |

## 问卷的每个问题

| 类别 | 问题 | 由哪条规则提出 | 依据 |
|---|---|---|---|
| blocking | SERVICER.globe_income | data.p2_income | 通过 |

## 规则依据（本方案用到的 10 条规则）

- **cn-sg.ppt@cn**（D_DISCRETION，2025-12-31）通过
  - 参数 cn-sg.ppt：value = 1 bool；treaty.cn-sg.2007.mli.zh#27（公约（MLI）和中国—新加坡税收协定的整合文本 ）「可以合理地认定就某项所得获取本协定某项优惠是直接或间接 产生该优惠的安排…」
  - 判断出处 treaty.cn-sg.2007.mli.zh#27：公约（MLI）和中国—新加坡税收协定的整合文本 
- **cn.deduct.service**（D_DISCRETION，2025-12-31）通过
  - 参数 cn.eit.rate：value = 25 %；cn.law.eit#4（中华人民共和国企业所得税法 ）「企业所得税的税率为25％」
  - 判断出处 cn.law.eit#8：中华人民共和国企业所得税法 
  - 参数 cn.deduct.general：uses = 1 bool；cn.law.eit#8（中华人民共和国企业所得税法 ）「企业实际发生的与取得收入有关的、合理的支出，包括成本、费用、税金、损失和…」
  - 参数 cn.eit.rate_entity：uses = 1 bool；cn.law.eit#28（中华人民共和国企业所得税法 ）「国家需要重点扶持的高新技术企业，减按15％的税率征收企业所得税」
- **cn.refund**（A_TEXT，2025-12-31）通过
  - 参数 cn.refund.limit_years：value = 3 years；cn.law.tca#51（中华人民共和国税收征收管理法 ）「纳税人自结算缴纳税款之日起三年内发现的，可以向税务机关要求退还多缴的税款」
  - 参数 cn.treaty.refund_route：uses = 1 bool；cn.sta.2019-35#10（国家税务总局关于发布《非居民纳税人享受协定待遇管理办法》的公告 国家税务总局公告2019年第35号）「可在税收征管法规定期限内自行或通过扣缴义务人向主管税务机关要求退还多缴税…」
  - 参数 cn.treaty.refund_check_days：uses = 30 days；cn.sta.2019-35#10（国家税务总局关于发布《非居民纳税人享受协定待遇管理办法》的公告 国家税务总局公告2019年第35号）「30日内查实」
  - 求值器出处 cn.law.tca#51：中华人民共和国税收征收管理法 
- **cn.tp.deduction_cap**（A_TEXT，2025-12-31）通过
  - 参数 cn.tp.adjust_to_median：uses = 1 bool；cn.gsf.2009-02#41（国家税务总局关于印发《特别纳税调整实施办法（试行）》的通知 国税发〔2009〕2号）「企业利润水平低于可比企业利润率区间中位值的，原则上应按照不低于中位值进行…」
  - 参数 cn.tp.domestic_same_burden_no_adjustment：uses = 1 bool；cn.sta.2017-06#38（国家税务总局关于发布《特别纳税调查调整及相互协商程序管理办法》的公告 国家税务总局公告2017年第6号）「实际税负相同的境内关联方之间的交易，只要该交易没有直接或者间接导致国家总…」
  - 求值器出处 cn.law.eit#41：中华人民共和国企业所得税法 
- **cn.wht.late_surcharge**（A_TEXT，2025-12-31）通过
  - 参数 cn.tca.late_surcharge_daily：value = 0.05 %；cn.law.tca#32（中华人民共和国税收征收管理法 ）「从滞纳税款之日起，按日加收滞纳税款万分之五的滞纳金」
  - 求值器出处 cn.law.tca#32：中华人民共和国税收征收管理法 
- **cn.wht.remit**（A_TEXT，2025-12-31）通过
  - 参数 cn.wht.obligation_date：value = actual payment or date payable text；cn.sta.2017-37#i4（国家税务总局关于非居民企业所得税源泉扣缴有关问题的公告 国家税务总局公告2017年第37号）「扣缴义务发生之日为相关款项实际支付或者到期应支付之日」
  - 参数 cn.wht.remit_days：uses = 7 days；cn.sta.2017-37#i7（国家税务总局关于非居民企业所得税源泉扣缴有关问题的公告 国家税务总局公告2017年第37号）「扣缴义务人应当自扣缴义务发生之日起7日内向扣缴义务人所在地主管税务机关申…」
  - 参数 cn.wht.obligation_date_dividend：uses = actual payment text；cn.sta.2017-37#i7（国家税务总局关于非居民企业所得税源泉扣缴有关问题的公告 国家税务总局公告2017年第37号）「相关应纳税款扣缴义务发生之日为股息、红利等权益性投资收益实际支付之日」
  - 参数 cn.wht.fx_rule：uses = CNY central parity on the obligation date text；cn.sta.2017-37#i4（国家税务总局关于非居民企业所得税源泉扣缴有关问题的公告 国家税务总局公告2017年第37号）「应当按照扣缴义务发生之日人民币汇率中间价折合成人民币」
  - 参数 cn.time.holiday_roll：uses = 1 bool；cn.reg.tca#109（中华人民共和国税收征收管理法实施细则 国务院令第362号（2016年修订））「期限的最后一日是法定休假日的，以休假日期满的次日为期限的最后一日」
  - 参数 cn.time.long_holiday_days：uses = 3 days；cn.reg.tca#109（中华人民共和国税收征收管理法实施细则 国务院令第362号（2016年修订））「在期限内有连续３日以上法定休假日的，按休假日天数顺延」
- **cn.wht.service_as_royalty**（D_DISCRETION，2025-12-31）通过
  - 参数 cn.wht.rate：value = 10 %；cn.reg.eit#91（中华人民共和国企业所得税法实施条例 国务院令第512号）「减按10%的税率征收企业所得税」
  - 判断出处 cn.gsh.2009-507#i4：国家税务总局关于执行税收协定特许权使用费条款有关问题的通知 国税函〔2009〕507号
  - 判断出处 cn.gsh.2009-507#i6：国家税务总局关于执行税收协定特许权使用费条款有关问题的通知 国税函〔2009〕507号
  - 参数 cn.treaty.service_not_royalty：uses = 1 bool；cn.gsh.2009-507#i4（国家税务总局关于执行税收协定特许权使用费条款有关问题的通知 国税函〔2009〕507号）「如果服务提供方提供服务过程中使用了某些专门知识和技术，但并不转让或许可这…」
  - 参数 cn.treaty.professional_services_business_profits：uses = 1 bool；cn.gsh.2009-507#i6（国家税务总局关于执行税收协定特许权使用费条款有关问题的通知 国税函〔2009〕507号）「专门从事工程、管理、咨询等专业服务的机构或个人提供的相关服务所取得的款项」
- **sg.ftc.dta**（A_TEXT，2025-12-31）通过
  - 参数 sg.ftc.credit_limit：uses = sg_tax_on_same_income_at_average_rate enum；sg.ita1947.full#s50（Income Tax Act 1947 (assembled whole-document HTML: base page + 36 lazy-load fragments) ）「The credit must not exceed the amoun…」
  - 参数 sg.ftc.tax_payable_under_arrangements：uses = 1 bool；sg.ita1947.full#s50（Income Tax Act 1947 (assembled whole-document HTML: base page + 36 lazy-load fragments) ）「tax payable in respect of any income…」
- **sg.service.base**（A_TEXT，2025-12-31）通过
  - 参数 sg.charge.basis：uses = accruing_in_or_derived_from_sg;received_in_sg_from_outside enum；sg.ita1947.full#s10（Income Tax Act 1947 (assembled whole-document HTML: base page + 36 lazy-load fragments) ）「upon the income of any person accrui…」
  - 求值器出处 sg.ita1947.full#s10：Income Tax Act 1947 (assembled whole-document HTML: base page + 36 lazy-load fragments) 
- **sg.service.charge**（A_TEXT，2025-12-31）通过
  - 参数 sg.corp.rate：value = 17 %；sg.ita1947.full#s43（Income Tax Act 1947 (assembled whole-document HTML: base page + 36 lazy-load fragments) ）「every company or body of persons, ta…」
  - 参数 sg.charge.basis：threshold = accruing_in_or_derived_from_sg;received_in_sg_from_outside enum；sg.ita1947.full#s10（Income Tax Act 1947 (assembled whole-document HTML: base page + 36 lazy-load fragments) ）「upon the income of any person accrui…」
  - 参数 sg.fsie.receipt_kinds：threshold = REMITTED;DEBT_SETTLED;MOVABLE_PROPERTY enum；sg.ita1947.full#s10（Income Tax Act 1947 (assembled whole-document HTML: base page + 36 lazy-load fragments) ）「any amount from any income derived f…」
  - 参数 sg.corp.rate_entity：uses = 1 bool；sg.ita1947.full#s43（Income Tax Act 1947 (assembled whole-document HTML: base page + 36 lazy-load fragments) ）「for every dollar of the first $10,00…」

## 事实来源（规则读到的事实，按流）

- fee：推导（facts.py） 5（authority_action、date_of_payment、prior_map_outcome、payee_in_source_jur、payee_is_related）；未定（按两端计） 2（service_onshore_share、residence_cert）；未给出（规则判为不影响结果） 11（arms_length_max、assessment_notice_on、first_notification_on、foreign_tax_rate、payable_on、pboc_benchmark_rate…）；陈述 9（profit_margin、receipt_kind、remitted_on、service_days_12m、service_kind、service_performed_in_residence…）

陈述的事实 9 个，附出处 0 个。
