# 依据核对：hk_holding_services.synthetic

运行 20261011T143101-hk_holding_services.synthetic，版本 a7b5cac57b68。规划器给出的是问卷（下面核对的是目前最优的候选）；核对 112 项：通过 78，说明 32，警示 2，失败 0。

**结论**：每一步都落到现行条文的原文；陈述的事实未附出处（0/28）。

候选 {'HOLD': 'CN', 'SERVICER': 'CN', 'financing': 'EQUITY', 'payment': False, 'exit_route': 'DIRECT'}；保证税额 5234112.99，最好情形 5233766.34；重算一致。

## 需要处理的

- 警示：exit/remit 期限按名义日期：库里缺 CN 2027 年的公众假期表
- 警示：hk_holding_services.synthetic 案例陈述的事实 28 个，附出处的 0 个（案例文件没有 provenance，见 案例采集.md §4.2）

## 税项（保证税额一端）

| 流 | 法域 | 税种 | 承担方 | 金额 | 规则 | 依据 |
|---|---|---|---|---|---|---|
| svc | CN | income | SERVICER | 100.00 | cn.domestic.charge、cn.service.deemed_profit、cn.ftc.direct | 通过 |
| up2 | CN | income | ULT | 90.00 | cn.wht.reduced | 通过 |
| up2 | HK | income | ULT | 58.50 | hk.fsie.charge、hk.ftc.dta | 通过 |
| reorg | CN | income | ULT | 100.00 | cn.wht.reduced、cn.gain.base | 通过 |
| reorg | HK | income | ULT | 65.00 | hk.fsie.charge、hk.fsie.gain.base、hk.ftc.dta | 通过 |
| reorg | CN | stamp | ULT | 2.00 | cn.stamp.seller | 通过 |
| reorg | CN | stamp | HOLD | 2.00 | cn.stamp.buyer | 通过 |
| exit | CN | income | HOLD | 50.00 | cn.resident.gain.charge、cn.resident.gain.base、cn.gain.base、cn.ftc.direct | 通过 |
| exit | CN | stamp | HOLD | 2.50 | cn.stamp.seller | 通过 |
| exit | CN | stamp | BUYER（集团外） | 2.50 | cn.stamp.buyer | 通过 |
| p2:ULT | HK | income | ULT | 5233642.99 | hk.p2.topup、hk.p2.base | 通过 |

## 方案动作

| 动作 | 依据所在的规则 | 依据 |
|---|---|---|
| flow:reorg~HOLD-CN.clawback_event_within_2y:is_false | hk.fsie.intragroup_relief | 通过 |
| flow:up2~HOLD-CN.holding_months:ge | hk.fsie.participation.dividend | 通过 |
| group.p2_tcsh_elected_cn:elect | sg.p2.topup、sg.p2.mtt、sg.p2.base、hk.p2.topup、hk.p2.iir、hk.p2.base | 通过 |

## 待机关认可的判断

| 事项 | 流 | 判断所引条款 | 规则 | 依据 |
|---|---|---|---|---|
| payee.no_adverse_bo_factors | up2 | cn.sta.2018-09#i2 | cn-hk.div.cap_qualified@cn | 通过 |
| payee.ppt | up2 | treaty.cn-hk.2006.p5.zh#6 | cn-hk.ppt@cn | 通过 |
| payer.reasonable_service_fee | svc | cn.law.eit#8 | cn.deduct.service | 通过 |
| payee.reasonable_commercial_purpose_absent | up1 | cn.law.eit#47、cn.reg.eit#120 | cn.gaar | 通过 |
| payee.no_main_purpose_of_tax_benefit | up2 | hk.cap112.en#s15N | hk.fsie.participation.dividend | 通过 |
| payee.no_main_purpose_of_tax_benefit | reorg | hk.cap112.en#s15N | hk.fsie.participation.share_transfer | 通过 |
| payee.adequate_substance | up2 | hk.cap112.en#s15K | hk.fsie.substance.dividend | 通过 |
| payee.adequate_substance | reorg | hk.cap112.en#s15K | hk.fsie.substance.share_transfer | 通过 |

## 期限与罚款

| 流 | 规则 | 依据 |
|---|---|---|
| up1 | cn.wht.remit | 通过 |
| svc | cn.tp.local_file | 通过 |
| svc | cn.wht.remit | 通过 |
| up2 | cn.wht.remit | 通过 |
| reorg | cn.wht.remit | 通过 |
| exit | cn.wht.remit | 通过 |

## 问卷的每个问题

| 类别 | 问题 | 由哪条规则提出 | 依据 |
|---|---|---|---|
| data | flow:up1~HOLD-HK.benchmark_rate | cn.deduct.interest.benchmark [CN] | 说明 |
| data | flow:up1~HOLD-HK.interest_rate | cn.deduct.interest.benchmark [CN] | 说明 |
| data | flow:up1.benchmark_rate | cn.deduct.interest.benchmark [CN] | 说明 |
| data | flow:up1.interest_rate | cn.deduct.interest.benchmark [CN] | 说明 |
| ruling | OP.reasonable_service_fee | cn.deduct.service [CN] | 说明 |

## 规则依据（本方案用到的 30 条规则）

- **cn-hk.div.cap_other@cn**（D_DISCRETION，2026-03-31）通过
  - 参数 cn-hk.div.cap_other：value = 10 %；treaty.cn-hk.2006.zh#10.2（内地和香港特别行政区关于对所得避免双重征税和防止偷漏税的安排 ）「在其它情况下，为股息总额的10%」
  - 参数 cn.bo.safe_harbour：threshold = government;listed_company;individual;wholly_owned_by_these enum；cn.sta.2018-09#i4（国家税务总局关于税收协定中“受益所有人”有关问题的公告 国家税务总局公告2018年第9号）「可不根据本公告第二条规定的因素进行综合分析，直接判定申请人具有“受益所有…」
  - 参数 cn.bo.via_100pct_owner：threshold = 1 bool；cn.sta.2018-09#i3（国家税务总局关于税收协定中“受益所有人”有关问题的公告 国家税务总局公告2018年第9号）「直接或间接持有申请人100%股份的人符合“受益所有人”条件」
  - 参数 cn.bo.onpay_ratio：threshold = 50 %；cn.sta.2018-09#i2（国家税务总局关于税收协定中“受益所有人”有关问题的公告 国家税务总局公告2018年第9号）「申请人有义务在收到所得的12个月内将所得的50%以上支付给第三国（地区）…」
  - 判断出处 cn.sta.2018-09#i2：国家税务总局关于税收协定中“受益所有人”有关问题的公告 国家税务总局公告2018年第9号
  - 参数 cn.treaty.claim_proc：uses = SELF_ASSESS enum；cn.sta.2019-35#3（国家税务总局关于发布《非居民纳税人享受协定待遇管理办法》的公告 国家税务总局公告2019年第35号）「自行判断、申报享受、相关资料留存备查」
  - 参数 cn.bo.onpay_window：uses = 12 months；cn.sta.2018-09#i2（国家税务总局关于税收协定中“受益所有人”有关问题的公告 国家税务总局公告2018年第9号）「在收到所得的12个月内」
- **cn-hk.div.cap_qualified@cn**（D_DISCRETION，2026-03-31）通过
  - 参数 cn-hk.div.cap_qualified：value = 5 %；treaty.cn-hk.2006.zh#10.2（内地和香港特别行政区关于对所得避免双重征税和防止偷漏税的安排 ）「如果受益所有人是直接拥有支付股息公司至少25%资本的公司，为股息总额的5…」
  - 参数 cn-hk.div.ratio_min：threshold = 25 %；treaty.cn-hk.2006.zh#10.2（内地和香港特别行政区关于对所得避免双重征税和防止偷漏税的安排 ）「直接拥有支付股息公司至少25%资本的公司」
  - 参数 cn.div.holding_months_min：threshold = 12 months；cn.gsh.2009-81#i3（国家税务总局关于执行税收协定股息条款有关问题的通知 国税函〔2009〕81号）「在取得股息前连续12个月以内任何时候均符合税收协定规定的比例」
  - 参数 cn.bo.safe_harbour：threshold = government;listed_company;individual;wholly_owned_by_these enum；cn.sta.2018-09#i4（国家税务总局关于税收协定中“受益所有人”有关问题的公告 国家税务总局公告2018年第9号）「可不根据本公告第二条规定的因素进行综合分析，直接判定申请人具有“受益所有…」
  - 参数 cn.bo.via_100pct_owner：threshold = 1 bool；cn.sta.2018-09#i3（国家税务总局关于税收协定中“受益所有人”有关问题的公告 国家税务总局公告2018年第9号）「直接或间接持有申请人100%股份的人符合“受益所有人”条件」
  - 参数 cn.bo.onpay_ratio：threshold = 50 %；cn.sta.2018-09#i2（国家税务总局关于税收协定中“受益所有人”有关问题的公告 国家税务总局公告2018年第9号）「申请人有义务在收到所得的12个月内将所得的50%以上支付给第三国（地区）…」
  - 判断出处 cn.sta.2018-09#i2：国家税务总局关于税收协定中“受益所有人”有关问题的公告 国家税务总局公告2018年第9号
  - 参数 cn.treaty.claim_proc：uses = SELF_ASSESS enum；cn.sta.2019-35#3（国家税务总局关于发布《非居民纳税人享受协定待遇管理办法》的公告 国家税务总局公告2019年第35号）「自行判断、申报享受、相关资料留存备查」
  - 参数 cn.bo.onpay_window：uses = 12 months；cn.sta.2018-09#i2（国家税务总局关于税收协定中“受益所有人”有关问题的公告 国家税务总局公告2018年第9号）「在收到所得的12个月内」
- **cn-hk.ppt@cn**（D_DISCRETION，2026-03-31）通过
  - 参数 cn-hk.ppt：value = 1 bool；treaty.cn-hk.2006.p5.zh#6（《内地和香港特别行政区关于对所得避免双重征税和防止偷漏税的安排》第五议定书 ）「主要目的之一是获得该优惠，则不得就相关所得给予该优惠」
  - 判断出处 treaty.cn-hk.2006.p5.zh#6：《内地和香港特别行政区关于对所得避免双重征税和防止偷漏税的安排》第五议定书 
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
- **cn.ftc.direct**（A_TEXT，2026-12-31）通过
  - 参数 cn.ftc.credit：uses = 1 bool；cn.law.eit#23（中华人民共和国企业所得税法 ）「企业取得的下列所得已在境外缴纳的所得税税额，可以从其当期应纳税额中抵免，…」
  - 参数 cn.ftc.limit_per_country：uses = 1 bool；cn.reg.eit#78（中华人民共和国企业所得税法实施条例 国务院令第512号）「该抵免限额应当分国(地区)不分项计算」
  - 参数 cn.ftc.carryforward_years：uses = 5 years；cn.law.eit#23（中华人民共和国企业所得税法 ）「超过抵免限额的部分，可以在以后五个年度内」
  - 参数 cn.ftc.method_lock_years：uses = 5 years；cn.cs.2017-84#i1（财政部 税务总局关于完善企业境外所得税收抵免政策问题的通知 财税〔2017〕84号）「上述方式一经选择，5年内不得改变」
  - 参数 cn.ftc.not_due_under_treaty_not_creditable：uses = 1 bool；cn.cs.2009-125#i4（财政部 国家税务总局关于企业境外所得税收抵免有关问题的通知 财税〔2009〕125号）「按照税收协定规定不应征收的境外所得税税款」
- **cn.gaar**（D_DISCRETION，2026-03-31）通过
  - 参数 cn.gaar：value = 1 bool；cn.law.eit#47（中华人民共和国企业所得税法 ）「企业实施其他不具有合理商业目的的安排而减少其应纳税收入或者所得额的，税务…」
  - 判断出处 cn.law.eit#47：中华人民共和国企业所得税法 
  - 判断出处 cn.reg.eit#120：中华人民共和国企业所得税法实施条例 国务院令第512号
- **cn.gain.base**（A_TEXT，2026-03-31）通过
  - 参数 cn.wht.base_gain：uses = 1 bool；cn.law.eit#19（中华人民共和国企业所得税法 ）「转让财产所得，以收入全额减除财产净值后的余额为应纳税所得额」
  - 求值器出处 cn.law.eit#16：中华人民共和国企业所得税法 
- **cn.gain.base**（A_TEXT，2026-12-31）通过
  - 参数 cn.wht.base_gain：uses = 1 bool；cn.law.eit#19（中华人民共和国企业所得税法 ）「转让财产所得，以收入全额减除财产净值后的余额为应纳税所得额」
  - 求值器出处 cn.law.eit#16：中华人民共和国企业所得税法 
- **cn.resident.gain.base**（A_TEXT，2026-12-31）通过
  - 参数 cn.eit.asset_net_value_deductible：uses = 1 bool；cn.law.eit#16（中华人民共和国企业所得税法 ）「企业转让资产，该项资产的净值，准予在计算应纳税所得额时扣除」
  - 求值器出处 cn.law.eit#16：中华人民共和国企业所得税法 
- **cn.resident.gain.charge**（A_TEXT，2026-12-31）通过
  - 参数 cn.eit.rate：value = 25 %；cn.law.eit#4（中华人民共和国企业所得税法 ）「企业所得税的税率为25％」
  - 参数 cn.eit.resident_worldwide：uses = 1 bool；cn.law.eit#3（中华人民共和国企业所得税法 ）「居民企业应当就其来源于中国境内、境外的所得缴纳企业所得税」
  - 参数 cn.eit.rate_entity：uses = 1 bool；cn.law.eit#28（中华人民共和国企业所得税法 ）「国家需要重点扶持的高新技术企业，减按15％的税率征收企业所得税」
- **cn.service.deemed_profit**（A_TEXT，2026-03-31）通过
  - 参数 cn.service.deemed_profit_min：uses = 30 %；cn.gsf.2010-19#5（国家税务总局关于印发《非居民企业所得税核定征收管理办法》的通知 国税发〔2010〕19号）「从事管理服务的，利润率为30%-50%」
  - 参数 cn.service.deemed_profit_max：uses = 50 %；cn.gsf.2010-19#5（国家税务总局关于印发《非居民企业所得税核定征收管理办法》的通知 国税发〔2010〕19号）「从事管理服务的，利润率为30%-50%」
  - 参数 cn.service.deemed_profit_design_min：uses = 15 %；cn.gsf.2010-19#5（国家税务总局关于印发《非居民企业所得税核定征收管理办法》的通知 国税发〔2010〕19号）「从事承包工程作业、设计和咨询劳务的，利润率为15%-30%」
  - 参数 cn.service.deemed_profit_design_max：uses = 30 %；cn.gsf.2010-19#5（国家税务总局关于印发《非居民企业所得税核定征收管理办法》的通知 国税发〔2010〕19号）「从事承包工程作业、设计和咨询劳务的，利润率为15%-30%」
  - 参数 cn.service.deemed_profit_other_min：uses = 15 %；cn.gsf.2010-19#5（国家税务总局关于印发《非居民企业所得税核定征收管理办法》的通知 国税发〔2010〕19号）「从事其他劳务或劳务以外经营活动的，利润率不低于15%」
  - 求值器出处 cn.gsf.2010-19#5：国家税务总局关于印发《非居民企业所得税核定征收管理办法》的通知 国税发〔2010〕19号
  - 求值器出处 cn.reg.eit#7：中华人民共和国企业所得税法实施条例 国务院令第512号
- **cn.stamp.buyer**（A_TEXT，2026-03-31）通过
  - 参数 cn.stamp.equity_rate：value = 0.05 %；cn.law.stamp.flk#20（中华人民共和国印花税法（国家法律法规数据库 PDF，含印花税税目税率表） 主席令第八十九号）「价款的万分之五」
  - 参数 cn.stamp.taxpayer_each_party：uses = 1 bool；cn.law.stamp.flk#1（中华人民共和国印花税法（国家法律法规数据库 PDF，含印花税税目税率表） 主席令第八十九号）「应当依照本法规定缴纳印花税」
  - 所依法律的施行条款 cn.law.stamp.flk#20：中华人民共和国印花税法（国家法律法规数据库 PDF，含印花税税目税率表） 主席令第八十九号
  - 口径 D19：锚点 12/12 找到原文
- **cn.stamp.buyer**（A_TEXT，2026-12-31）通过
  - 参数 cn.stamp.equity_rate：value = 0.05 %；cn.law.stamp.flk#20（中华人民共和国印花税法（国家法律法规数据库 PDF，含印花税税目税率表） 主席令第八十九号）「价款的万分之五」
  - 参数 cn.stamp.taxpayer_each_party：uses = 1 bool；cn.law.stamp.flk#1（中华人民共和国印花税法（国家法律法规数据库 PDF，含印花税税目税率表） 主席令第八十九号）「应当依照本法规定缴纳印花税」
  - 所依法律的施行条款 cn.law.stamp.flk#20：中华人民共和国印花税法（国家法律法规数据库 PDF，含印花税税目税率表） 主席令第八十九号
  - 口径 D19：锚点 12/12 找到原文
- **cn.stamp.seller**（A_TEXT，2026-03-31）通过
  - 参数 cn.stamp.equity_rate：value = 0.05 %；cn.law.stamp.flk#20（中华人民共和国印花税法（国家法律法规数据库 PDF，含印花税税目税率表） 主席令第八十九号）「价款的万分之五」
  - 参数 cn.stamp.taxpayer_each_party：uses = 1 bool；cn.law.stamp.flk#1（中华人民共和国印花税法（国家法律法规数据库 PDF，含印花税税目税率表） 主席令第八十九号）「应当依照本法规定缴纳印花税」
  - 所依法律的施行条款 cn.law.stamp.flk#20：中华人民共和国印花税法（国家法律法规数据库 PDF，含印花税税目税率表） 主席令第八十九号
  - 口径 D19：锚点 12/12 找到原文
- **cn.stamp.seller**（A_TEXT，2026-12-31）通过
  - 参数 cn.stamp.equity_rate：value = 0.05 %；cn.law.stamp.flk#20（中华人民共和国印花税法（国家法律法规数据库 PDF，含印花税税目税率表） 主席令第八十九号）「价款的万分之五」
  - 参数 cn.stamp.taxpayer_each_party：uses = 1 bool；cn.law.stamp.flk#1（中华人民共和国印花税法（国家法律法规数据库 PDF，含印花税税目税率表） 主席令第八十九号）「应当依照本法规定缴纳印花税」
  - 所依法律的施行条款 cn.law.stamp.flk#20：中华人民共和国印花税法（国家法律法规数据库 PDF，含印花税税目税率表） 主席令第八十九号
  - 口径 D19：锚点 12/12 找到原文
- **cn.tp.local_file**（A_TEXT，2026-03-31）通过
  - 参数 cn.tp.local_file_due：value = next_year_june_30 text；cn.sta.2016-42#i19（国家税务总局关于完善关联申报和同期资料管理有关事项的公告 国家税务总局公告2016年第42号）「本地文档和特殊事项文档应当在关联交易发生年度次年6月30日之前准备完毕」
  - 参数 cn.tp.local_file_other_threshold：threshold = 40000000 CNY；cn.sta.2016-42#i13（国家税务总局关于完善关联申报和同期资料管理有关事项的公告 国家税务总局公告2016年第42号）「其他关联交易金额合计超过4000万元」
  - 求值器出处 cn.sta.2016-42#i19：国家税务总局关于完善关联申报和同期资料管理有关事项的公告 国家税务总局公告2016年第42号
- **cn.wht.reduced**（A_TEXT，2026-03-31）通过
  - 参数 cn.wht.rate：value = 10 %；cn.reg.eit#91（中华人民共和国企业所得税法实施条例 国务院令第512号）「减按10%的税率征收企业所得税」
- **cn.wht.remit**（A_TEXT，2026-03-31）通过
  - 参数 cn.wht.obligation_date：value = actual payment or date payable text；cn.sta.2017-37#i4（国家税务总局关于非居民企业所得税源泉扣缴有关问题的公告 国家税务总局公告2017年第37号）「扣缴义务发生之日为相关款项实际支付或者到期应支付之日」
  - 参数 cn.wht.remit_days：uses = 7 days；cn.sta.2017-37#i7（国家税务总局关于非居民企业所得税源泉扣缴有关问题的公告 国家税务总局公告2017年第37号）「扣缴义务人应当自扣缴义务发生之日起7日内向扣缴义务人所在地主管税务机关申…」
  - 参数 cn.wht.obligation_date_dividend：uses = actual payment text；cn.sta.2017-37#i7（国家税务总局关于非居民企业所得税源泉扣缴有关问题的公告 国家税务总局公告2017年第37号）「相关应纳税款扣缴义务发生之日为股息、红利等权益性投资收益实际支付之日」
  - 参数 cn.wht.fx_rule：uses = CNY central parity on the obligation date text；cn.sta.2017-37#i4（国家税务总局关于非居民企业所得税源泉扣缴有关问题的公告 国家税务总局公告2017年第37号）「应当按照扣缴义务发生之日人民币汇率中间价折合成人民币」
  - 参数 cn.time.holiday_roll：uses = 1 bool；cn.reg.tca#109（中华人民共和国税收征收管理法实施细则 国务院令第362号（2016年修订））「期限的最后一日是法定休假日的，以休假日期满的次日为期限的最后一日」
  - 参数 cn.time.long_holiday_days：uses = 3 days；cn.reg.tca#109（中华人民共和国税收征收管理法实施细则 国务院令第362号（2016年修订））「在期限内有连续３日以上法定休假日的，按休假日天数顺延」
- **cn.wht.remit**（A_TEXT，2026-12-31）通过
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
  - 参数 hk.fsie.covered_income：uses = interest;dividend;disposal_gain;ip_income enum；hk.cap112.en#s15H（Inland Revenue Ordinance (Cap. 112) - whole chapter, English Cap. 112）「means any interest, dividend, dispos…」
  - 参数 hk.fsie.received_in_hk_trigger：uses = 1 bool；hk.cap112.en#s15I（Inland Revenue Ordinance (Cap. 112) - whole chapter, English Cap. 112）「is to be regarded as a receipt arisi…」
  - 参数 hk.fsie.remittance_is_receipt：uses = 1 bool；hk.cap112.en#s15H（Inland Revenue Ordinance (Cap. 112) - whole chapter, English Cap. 112）「the sum is remitted to, or is transm…」
  - 参数 hk.fsie.commencement：uses = 1 bool；hk.cap112.en#sch55（Inland Revenue Ordinance (Cap. 112) - whole chapter, English Cap. 112）「apply in relation to specified forei…」
  - 参数 hk.profits.charge_scope：uses = 1 bool；hk.cap112.en#s14（Inland Revenue Ordinance (Cap. 112) - whole chapter, English Cap. 112）「on every person carrying on a trade,…」
  - 参数 hk.profits.rate_entity：uses = 1 bool；hk.cap112.en#sch8B（Inland Revenue Ordinance (Cap. 112) - whole chapter, English Cap. 112）「at the rate of 8.25% on section 14 a…」
- **hk.fsie.gain.base**（A_TEXT，2026-03-31）通过
  - 参数 hk.fsie.gain_not_capital：uses = 1 bool；hk.cap112.en#s15I（Inland Revenue Ordinance (Cap. 112) - whole chapter, English Cap. 112）「is to be regarded as not arising fro…」
  - 求值器出处 hk.cap112.en#s14：Inland Revenue Ordinance (Cap. 112) - whole chapter, English Cap. 112
- **hk.fsie.intragroup_relief**（A_TEXT，2026-03-31）通过
  - 参数 hk.fsie.intragroup_relief：threshold = 1 bool；hk.cap112.en#s15OA（Inland Revenue Ordinance (Cap. 112) - whole chapter, English Cap. 112）「the selling entity is to be regarded…」
  - 参数 hk.fsie.intragroup_clawback_years：threshold = 2 years；hk.cap112.en#s15OB（Inland Revenue Ordinance (Cap. 112) - whole chapter, English Cap. 112）「within 2 years after the subject sal…」
  - 参数 hk.fsie.intragroup_assoc_ratio_min：uses = 75 %；hk.cap112.en#s15OC（Inland Revenue Ordinance (Cap. 112) - whole chapter, English Cap. 112）「entity A has at least 75% of direct …」
- **hk.fsie.participation.dividend**（D_DISCRETION，2026-03-31）通过
  - 参数 hk.fsie.participation_resident_or_pe：threshold = 1 bool；hk.cap112.en#s15M（Inland Revenue Ordinance (Cap. 112) - whole chapter, English Cap. 112）「a Hong Kong resident person; or (ii)…」
  - 参数 hk.fsie.participation_ratio_min：threshold = 5 %；hk.cap112.en#s15M（Inland Revenue Ordinance (Cap. 112) - whole chapter, English Cap. 112）「has continuously held not less than …」
  - 参数 hk.fsie.participation_months_min：threshold = 12 months；hk.cap112.en#s15M（Inland Revenue Ordinance (Cap. 112) - whole chapter, English Cap. 112）「for a period of not less than 12 mon…」
  - 参数 hk.fsie.participation_subject_to_tax：threshold = 1 bool；hk.cap112.en#s15N（Inland Revenue Ordinance (Cap. 112) - whole chapter, English Cap. 112）「the income is subject to a qualifyin…」
  - 参数 hk.fsie.participation_headline_rate_basis：threshold = 1 bool；hk.cap112.en#s15N（Inland Revenue Ordinance (Cap. 112) - whole chapter, English Cap. 112）「the highest applicable rate, of a si…」
  - 参数 hk.fsie.reference_rate：threshold = 15 %；hk.cap112.en#s15N（Inland Revenue Ordinance (Cap. 112) - whole chapter, English Cap. 112）「the reference rate is 15%」
  - 参数 hk.fsie.participation_anti_hybrid：threshold = 1 bool；hk.cap112.en#s15N（Inland Revenue Ordinance (Cap. 112) - whole chapter, English Cap. 112）「section 15M does not apply if, and t…」
  - 判断出处 hk.cap112.en#s15N：Inland Revenue Ordinance (Cap. 112) - whole chapter, English Cap. 112
  - 参数 hk.fsie.participation_main_purpose：uses = 1 bool；hk.cap112.en#s15N（Inland Revenue Ordinance (Cap. 112) - whole chapter, English Cap. 112）「the main purpose, or one of the main…」
- **hk.fsie.participation.share_transfer**（D_DISCRETION，2026-03-31）通过
  - 参数 hk.fsie.participation_resident_or_pe：threshold = 1 bool；hk.cap112.en#s15M（Inland Revenue Ordinance (Cap. 112) - whole chapter, English Cap. 112）「a Hong Kong resident person; or (ii)…」
  - 参数 hk.fsie.participation_ratio_min：threshold = 5 %；hk.cap112.en#s15M（Inland Revenue Ordinance (Cap. 112) - whole chapter, English Cap. 112）「has continuously held not less than …」
  - 参数 hk.fsie.participation_months_min：threshold = 12 months；hk.cap112.en#s15M（Inland Revenue Ordinance (Cap. 112) - whole chapter, English Cap. 112）「for a period of not less than 12 mon…」
  - 参数 hk.fsie.participation_subject_to_tax：threshold = 1 bool；hk.cap112.en#s15N（Inland Revenue Ordinance (Cap. 112) - whole chapter, English Cap. 112）「the income is subject to a qualifyin…」
  - 参数 hk.fsie.participation_headline_rate_basis：threshold = 1 bool；hk.cap112.en#s15N（Inland Revenue Ordinance (Cap. 112) - whole chapter, English Cap. 112）「the highest applicable rate, of a si…」
  - 参数 hk.fsie.reference_rate：threshold = 15 %；hk.cap112.en#s15N（Inland Revenue Ordinance (Cap. 112) - whole chapter, English Cap. 112）「the reference rate is 15%」
  - 参数 hk.fsie.participation_anti_hybrid：threshold = 1 bool；hk.cap112.en#s15N（Inland Revenue Ordinance (Cap. 112) - whole chapter, English Cap. 112）「section 15M does not apply if, and t…」
  - 判断出处 hk.cap112.en#s15N：Inland Revenue Ordinance (Cap. 112) - whole chapter, English Cap. 112
  - 参数 hk.fsie.participation_main_purpose：uses = 1 bool；hk.cap112.en#s15N（Inland Revenue Ordinance (Cap. 112) - whole chapter, English Cap. 112）「the main purpose, or one of the main…」
- **hk.fsie.substance.dividend**（D_DISCRETION，2026-03-31）通过
  - 参数 hk.fsie.substance_pure_holding：threshold = 1 bool；hk.cap112.en#s15K（Inland Revenue Ordinance (Cap. 112) - whole chapter, English Cap. 112）「in the Commissioner’s opinion, the e…」
  - 判断出处 hk.cap112.en#s15K：Inland Revenue Ordinance (Cap. 112) - whole chapter, English Cap. 112
  - 参数 hk.fsie.substance_non_pure_holding：threshold = 1 bool；hk.cap112.en#s15K（Inland Revenue Ordinance (Cap. 112) - whole chapter, English Cap. 112）「the total amount of operating expend…」
  - 参数 hk.fsie.substance_exception_income：uses = interest;dividend;non_ip_disposal_gain enum；hk.cap112.en#s15K（Inland Revenue Ordinance (Cap. 112) - whole chapter, English Cap. 112）「the income is interest, a dividend o…」
- **hk.fsie.substance.share_transfer**（D_DISCRETION，2026-03-31）通过
  - 参数 hk.fsie.substance_pure_holding：threshold = 1 bool；hk.cap112.en#s15K（Inland Revenue Ordinance (Cap. 112) - whole chapter, English Cap. 112）「in the Commissioner’s opinion, the e…」
  - 判断出处 hk.cap112.en#s15K：Inland Revenue Ordinance (Cap. 112) - whole chapter, English Cap. 112
  - 参数 hk.fsie.substance_non_pure_holding：threshold = 1 bool；hk.cap112.en#s15K（Inland Revenue Ordinance (Cap. 112) - whole chapter, English Cap. 112）「the total amount of operating expend…」
  - 参数 hk.fsie.substance_exception_income：uses = interest;dividend;non_ip_disposal_gain enum；hk.cap112.en#s15K（Inland Revenue Ordinance (Cap. 112) - whole chapter, English Cap. 112）「the income is interest, a dividend o…」
- **hk.ftc.dta**（A_TEXT，2026-03-31）通过
  - 参数 hk.ftc.credit_limit：uses = hk_tax_on_same_income_at_average_rate enum；hk.cap112.en#s50（Inland Revenue Ordinance (Cap. 112) - whole chapter, English Cap. 112）「The credit shall not exceed the amou…」
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
- **hk.p2.base**（A_TEXT，2027-01-02）通过
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
- **hk.p2.topup**（A_TEXT，2027-01-02）通过
  - 参数 p2.minimum_rate：value = 15 %；hk.ord.2025-21#p147（Inland Revenue (Amendment) (Minimum Tax for Multinational Enterprise Groups) Ordinance 2025 Ord. No. 21 of 2025）「Minimum rate (最低稅率) means fifteen pe…」
  - 参数 p2.revenue_threshold：threshold = 750000000 EUR；hk.ord.2025-21#p42（Inland Revenue (Amendment) (Minimum Tax for Multinational Enterprise Groups) Ordinance 2025 Ord. No. 21 of 2025）「annual revenue of EUR 750 million or…」
  - 参数 p2.qualified_iir_hk：threshold = 1 bool；intl.oecd.globe.central-record.2025-12#p7（OECD/G20 Inclusive Framework: Administrative Guidance on the GloBE Rules (Pillar Two) — Central Record of Legislation with Transitional Qualified Status (as at 1 December 2025) ）「Hong Kong (China) Inland Revenue (Am…」
  - 参数 hk.p2.hkmtt：uses = 1 bool；hk.ord.2025-21#p21（Inland Revenue (Amendment) (Minimum Tax for Multinational Enterprise Groups) Ordinance 2025 Ord. No. 21 of 2025）「Schedule 62 has effect for charging …」
  - 口径 D20：锚点 12/12 找到原文
- **sg.p2.base**（A_TEXT，2026-03-31）通过
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

## 事实来源（规则读到的事实，按流）

- exit：推导（facts.py） 6（consideration、cost_basis、date_of_payment、reorg_step、payee_in_source_jur、payee_resident_in_cn）；未给出（规则判为不影响结果） 16（assessment_notice_on、cn_cost_basis、payable_on、remitted_on、reorg_acquired_ratio、reorg_buyer_resident_in_cn…）；结构性缺省（按否） 1（shares_cancelled）
- p2:ULT：推导（引擎） 1（p2_etr）；未给出（规则判为不影响结果） 3（assessment_notice_on、determination_on、p2_additional）；结构性缺省（按否） 1（p2_iir）；陈述 1（group_revenue_eur）
- reorg：推导（facts.py） 13（authority_action、consideration、date_of_payment、intragroup_transfer、prior_map_outcome、reorg_acquired_ratio…）；方案动作 2（clawback_event_within_2y、holding_months）；未定（按两端计） 1（acquirer_chargeable_in_hk）；未给出（规则判为不影响结果） 14（assessment_notice_on、cn_cost_basis、determination_on、first_notification_on、foreign_tax_rate、payable_on…）；结构性缺省（按否） 1（shares_cancelled）；设计或模板设定 4（cost_basis、max_ratio_12m、ratio、reorg_step）；陈述 11（deductible_at_payer、foreign_headline_rate、foreign_taxed、immovable_ratio、listed_market_trade、receipt_kind…）
- svc：推导（facts.py） 6（date_of_payment、service_consumed_on_site_abroad、service_onshore_share、service_performed_in_source、payee_in_source_jur、payee_is_related）；未给出（规则判为不影响结果） 10（arms_length_max、assessment_notice_on、input_vat_documents_kept、payable_on、pboc_benchmark_rate、remitted_on…）；陈述 5（price_includes_vat、service_kind、related_party_volume、tp_documentation_provided、vat_general_taxpayer）
- up1：推导（facts.py） 4（date_of_payment、direct_ratio、reorg_special_applied、payee_in_source_jur）；推导（引擎） 1（reorg_same_residence）；方案动作 1（holding_months）；未给出（规则判为不影响结果） 10（assessment_notice_on、direct_payment、dividend_from_pre_reorg_profits、payable_on、reinvestment_form、reinvestment_from_distributed_profit…）；陈述 2（listed_market_trade、reinvested_in_cn）
- up2：推导（facts.py） 11（authority_action、date_of_payment、direct_ratio、prior_map_outcome、ratio、reorg_special_applied…）；方案动作 1（holding_months）；未定（按两端计） 2（foreign_taxed、underlying_profits_taxed）；未给出（规则判为不影响结果） 13（assessment_notice_on、determination_on、direct_payment、dividend_from_pre_reorg_profits、first_notification_on、foreign_tax_rate…）；陈述 9（deductible_at_payer、foreign_headline_rate、receipt_kind、reinvested_in_cn、bo_safe_harbour、pure_equity_holding…）

陈述的事实 28 个，附出处 0 个。
