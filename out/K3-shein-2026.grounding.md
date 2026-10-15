# 依据核对：K3-shein-2026

运行 20261014T214221-K3-shein-2026，版本 be566a8fb554。规划器给出的是问卷（下面核对的是目前最优的候选）；核对 73 项：通过 52，说明 20，警示 1，失败 0。

**结论**：每一步都落到现行条文的原文；陈述的事实未附出处（0/2）。

候选 {'HOLD': 'SG', 'financing': 'EQUITY', 'payment': False}；保证税额 10000000.00，最好情形 0.00；重算一致。

## 需要处理的

- 警示：K3-shein-2026 案例陈述的事实 2 个，附出处的 0 个（案例文件没有 provenance，见 案例采集.md §4.2）

## 税项（保证税额一端）

| 流 | 法域 | 税种 | 承担方 | 金额 | 规则 | 依据 |
|---|---|---|---|---|---|---|
| up1 | CN | income | HOLD | 10000000.00 | cn.wht.reduced | 通过 |
| reorg | CN | stamp | ULT | 0.00 | cn.stamp.seller | 通过 |
| reorg | CN | stamp | HOLD | 0.00 | cn.stamp.buyer | 通过 |
| reorg | SG | income | ULT | 0.00 | sg.fsie.charge、sg.fsie.gain.base、sg.ftc.dta | 通过 |
| reorg | CN | income | ULT | 0.00 | cn.wht.reduced、cn.gain.base | 通过 |

## 方案动作

| 动作 | 依据所在的规则 | 依据 |
|---|---|---|
| HOLD.ftc_pooling_election:is_true | sg.ftc.pooling | 通过 |
| HOLD.residence_cert:is_true | cn-sg.div.cap_qualified@cn | 通过 |
| flow:reorg.reorg_commitment_3y:is_true | cn.reorg.special | 通过 |
| flow:reorg.reorg_equity_payment_share:ge | cn.reorg.special | 通过 |
| flow:reorg.reorg_filed:is_true | cn.reorg.special | 通过 |
| flow:reorg.reorg_operations_unchanged_12m:is_true | cn.reorg.special | 通过 |
| flow:reorg.reorg_shares_kept_12m:is_true | cn.reorg.special | 通过 |
| flow:up1.holding_months:ge | cn-sg.div.cap_qualified@cn | 通过 |
| flow:up1.planned_holding_months:ge | cn.reinvest.credit | 通过 |
| flow:up1~HOLD-SG.receipt_kind:is_in | sg.fsie.charge | 通过 |
| group.p2_tcsh_elected_cn:elect | sg.p2.topup、sg.p2.mtt、sg.p2.base、hk.p2.topup、hk.p2.iir、hk.p2.base | 通过 |
| group.p2_tcsh_elected_sg:elect | sg.p2.topup、sg.p2.mtt、sg.p2.base | 通过 |

## 待机关认可的判断

| 事项 | 流 | 判断所引条款 | 规则 | 依据 | 先例（案例采集.md §5） |
|---|---|---|---|---|---|
| payee.no_adverse_bo_factors | up1 | cn.sta.2018-09#i2 | cn-sg.div.cap_qualified@cn | 通过 | 未被压住；不成立最近的先例 CN-jd9-rhq-8staff（还差 bo_too_few_staff；多出不利 bo_reinvests、bo_regional_functions、bo_funds_raised_locally、bo_many_staff）；成立最近的先例 CN-jd9-reinvest（还差 bo_reinvests；多出不利 bo_pays_out、bo_staff_not_own、bo_income_idle、bo_directors_by_parent、bo_too_few_staff、bo_unexplained_shift、bo_other_income_small、bo_single_investment、bo_no_investment_records、bo_director_abroad、bo_related_loan_payout、bo_not_taxed_home） |
| payee.ppt | up1 | treaty.cn-sg.2007.mli.zh#27 | cn-sg.ppt@cn | 通过 | 无先例卡 |
| payee.reasonable_commercial_purpose_absent | up1 | cn.law.eit#47、cn.reg.eit#120 | cn.gaar | 通过 | 无先例卡 |
| payee.reorg_reasonable_commercial_purpose | reorg | cn.cs.2009-59#i5 | cn.reorg.special | 通过 | 未被压住；成立最近的先例 CN-sh-ruling-2025（还差 rr_integration、rr_stated_purpose） |
| payee.adequate_substance | reorg | sg.ita1947.full#s10L | sg.s10l.gain | 通过 | 未被压住；成立最近的先例 SG-ars-11-2026（还差 sub_parent_controls） |

## 期限与罚款

| 流 | 规则 | 依据 |
|---|---|---|
| up1 | cn.wht.remit | 通过 |
| reorg | cn.wht.remit | 通过 |

## 问卷的每个问题

| 类别 | 问题 | 由哪条规则提出 | 依据 |
|---|---|---|---|
| blocking | OP.globe_income | data.p2_income | 通过 |
| blocking | ULT.globe_income | data.p2_income | 通过 |
| blocking | flow:reorg.amount | data.amount | 说明 |

## 规则依据（本方案用到的 21 条规则）

- **cn-sg.div.cap_qualified@cn**（D_DISCRETION，2026-06-30）通过
  - 参数 cn-sg.div.cap_qualified：value = 5 %；treaty.cn-sg.2007.zh#10.2（中华人民共和国政府和新加坡共和国政府关于对所得避免双重征税和防止偷漏税的协定 ）「不应超过股息总额的百分之五」
  - 参数 cn-sg.div.ratio_min：threshold = 25 %；treaty.cn-sg.2007.zh#10.2（中华人民共和国政府和新加坡共和国政府关于对所得避免双重征税和防止偷漏税的协定 ）「直接拥有支付股息公司至少百分之二十五资本」
  - 参数 cn.div.holding_months_min：threshold = 12 months；cn.gsh.2009-81#i3（国家税务总局关于执行税收协定股息条款有关问题的通知 国税函〔2009〕81号）「在取得股息前连续12个月以内任何时候均符合税收协定规定的比例」
  - 参数 cn.bo.safe_harbour：threshold = government;listed_company;individual;wholly_owned_by_these enum；cn.sta.2018-09#i4（国家税务总局关于税收协定中“受益所有人”有关问题的公告 国家税务总局公告2018年第9号）「可不根据本公告第二条规定的因素进行综合分析，直接判定申请人具有“受益所有…」
  - 参数 cn.bo.via_100pct_owner：threshold = 1 bool；cn.sta.2018-09#i3（国家税务总局关于税收协定中“受益所有人”有关问题的公告 国家税务总局公告2018年第9号）「直接或间接持有申请人100%股份的人符合“受益所有人”条件」
  - 参数 cn.bo.onpay_ratio：threshold = 50 %；cn.sta.2018-09#i2（国家税务总局关于税收协定中“受益所有人”有关问题的公告 国家税务总局公告2018年第9号）「申请人有义务在收到所得的12个月内将所得的50%以上支付给第三国（地区）…」
  - 判断出处 cn.sta.2018-09#i2：国家税务总局关于税收协定中“受益所有人”有关问题的公告 国家税务总局公告2018年第9号
  - 参数 cn.treaty.claim_proc：uses = SELF_ASSESS enum；cn.sta.2019-35#3（国家税务总局关于发布《非居民纳税人享受协定待遇管理办法》的公告 国家税务总局公告2019年第35号）「自行判断、申报享受、相关资料留存备查」
  - 参数 cn.bo.onpay_window：uses = 12 months；cn.sta.2018-09#i2（国家税务总局关于税收协定中“受益所有人”有关问题的公告 国家税务总局公告2018年第9号）「在收到所得的12个月内」
- **cn-sg.ppt@cn**（D_DISCRETION，2026-06-30）通过
  - 参数 cn-sg.ppt：value = 1 bool；treaty.cn-sg.2007.mli.zh#27（公约（MLI）和中国—新加坡税收协定的整合文本 ）「可以合理地认定就某项所得获取本协定某项优惠是直接或间接 产生该优惠的安排…」
  - 判断出处 treaty.cn-sg.2007.mli.zh#27：公约（MLI）和中国—新加坡税收协定的整合文本 
- **cn.gaar**（D_DISCRETION，2026-06-30）通过
  - 参数 cn.gaar：value = 1 bool；cn.law.eit#47（中华人民共和国企业所得税法 ）「企业实施其他不具有合理商业目的的安排而减少其应纳税收入或者所得额的，税务…」
  - 判断出处 cn.law.eit#47：中华人民共和国企业所得税法 
  - 判断出处 cn.reg.eit#120：中华人民共和国企业所得税法实施条例 国务院令第512号
- **cn.gain.base**（A_TEXT，2026-06-30）通过
  - 参数 cn.wht.base_gain：uses = 1 bool；cn.law.eit#19（中华人民共和国企业所得税法 ）「转让财产所得，以收入全额减除财产净值后的余额为应纳税所得额」
  - 参数 cn.tp.related_transfer_arms_length：uses = 1 bool；cn.law.eit#41（中华人民共和国企业所得税法 ）「企业与其关联方之间的业务往来，不符合独立交易原则而减少企业或者其关联方应…」
  - 参数 cn.tp.related_share_min：uses = 25 %；cn.sta.2016-42#i2（国家税务总局关于完善关联申报和同期资料管理有关事项的公告 国家税务总局公告2016年第42号）「一方直接或者间接持有另一方的股份总和达到25%以上」
  - 求值器出处 cn.law.eit#16：中华人民共和国企业所得税法 
  - 口径 D32：锚点 7/7 找到原文
  - 口径 D38：锚点 9/9 找到原文
- **cn.reinvest.credit**（A_TEXT，2026-06-30）通过
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
- **cn.reorg.special**（D_DISCRETION，2026-06-30）通过
  - 参数 cn.reorg.control_ratio：threshold = 100 %；cn.cs.2009-59#i7（财政部 国家税务总局关于企业重组业务企业所得税处理若干问题的通知 财税〔2009〕59号）「非居民企业向其100%直接控股的另一非居民企业转让其拥有的居民企业股权」
  - 参数 cn.reorg.acquired_ratio_min：threshold = 50 %；cn.cs.2014-109#i1（财政部 国家税务总局关于促进企业重组有关企业所得税处理问题的通知 财税〔2014〕109号）「收购企业购买的股权不低于被收购企业全部股权的50%」
  - 参数 cn.reorg.equity_payment_min：threshold = 85 %；cn.cs.2009-59#i6（财政部 国家税务总局关于企业重组业务企业所得税处理若干问题的通知 财税〔2009〕59号）「股权支付金额不低于其交易支付总额的85%」
  - 判断出处 cn.cs.2009-59#i5：财政部 国家税务总局关于企业重组业务企业所得税处理若干问题的通知 财税〔2009〕59号
  - 参数 cn.reorg.keep_months：threshold = 12 months；cn.cs.2009-59#i5（财政部 国家税务总局关于企业重组业务企业所得税处理若干问题的通知 财税〔2009〕59号）「在重组后连续12个月内，不得转让所取得的股权」
  - 参数 cn.reorg.filing_days：threshold = 30 days；cn.sta.2013-72#i2（国家税务总局关于非居民企业股权转让适用特殊性税务处理有关问题的公告 国家税务总局公告2013年第72号）「应于股权转让合同或协议生效且完成工商变更登记手续30日内进行备案」
  - 判断出处 cn.cs.2009-59#i7：财政部 国家税务总局关于企业重组业务企业所得税处理若干问题的通知 财税〔2009〕59号
  - 参数 cn.reorg.commitment_years：threshold = 3 years；cn.cs.2009-59#i7（财政部 国家税务总局关于企业重组业务企业所得税处理若干问题的通知 财税〔2009〕59号）「在3年（含3年）内不转让其拥有受让方非居民企业的股权」
  - 口径 D18：锚点 10/10 找到原文
- **cn.stamp.buyer**（A_TEXT，2026-06-30）通过
  - 参数 cn.stamp.equity_rate：value = 0.05 %；cn.law.stamp.flk#20（中华人民共和国印花税法（国家法律法规数据库 PDF，含印花税税目税率表） 主席令第八十九号）「价款的万分之五」
  - 参数 cn.stamp.taxpayer_each_party：uses = 1 bool；cn.law.stamp.flk#1（中华人民共和国印花税法（国家法律法规数据库 PDF，含印花税税目税率表） 主席令第八十九号）「应当依照本法规定缴纳印花税」
  - 所依法律的施行条款 cn.law.stamp.flk#20：中华人民共和国印花税法（国家法律法规数据库 PDF，含印花税税目税率表） 主席令第八十九号
  - 口径 D19：锚点 12/12 找到原文
- **cn.stamp.seller**（A_TEXT，2026-06-30）通过
  - 参数 cn.stamp.equity_rate：value = 0.05 %；cn.law.stamp.flk#20（中华人民共和国印花税法（国家法律法规数据库 PDF，含印花税税目税率表） 主席令第八十九号）「价款的万分之五」
  - 参数 cn.stamp.taxpayer_each_party：uses = 1 bool；cn.law.stamp.flk#1（中华人民共和国印花税法（国家法律法规数据库 PDF，含印花税税目税率表） 主席令第八十九号）「应当依照本法规定缴纳印花税」
  - 所依法律的施行条款 cn.law.stamp.flk#20：中华人民共和国印花税法（国家法律法规数据库 PDF，含印花税税目税率表） 主席令第八十九号
  - 口径 D19：锚点 12/12 找到原文
- **cn.wht.reduced**（A_TEXT，2026-06-30）通过
  - 参数 cn.wht.rate：value = 10 %；cn.reg.eit#91（中华人民共和国企业所得税法实施条例 国务院令第512号）「减按10%的税率征收企业所得税」
- **cn.wht.remit**（A_TEXT，2026-06-30）通过
  - 参数 cn.wht.obligation_date：value = actual payment or date payable text；cn.sta.2017-37#i4（国家税务总局关于非居民企业所得税源泉扣缴有关问题的公告 国家税务总局公告2017年第37号）「扣缴义务发生之日为相关款项实际支付或者到期应支付之日」
  - 参数 cn.wht.remit_days：uses = 7 days；cn.sta.2017-37#i7（国家税务总局关于非居民企业所得税源泉扣缴有关问题的公告 国家税务总局公告2017年第37号）「扣缴义务人应当自扣缴义务发生之日起7日内向扣缴义务人所在地主管税务机关申…」
  - 参数 cn.wht.obligation_date_dividend：uses = actual payment text；cn.sta.2017-37#i7（国家税务总局关于非居民企业所得税源泉扣缴有关问题的公告 国家税务总局公告2017年第37号）「相关应纳税款扣缴义务发生之日为股息、红利等权益性投资收益实际支付之日」
  - 参数 cn.wht.fx_rule：uses = CNY central parity on the obligation date text；cn.sta.2017-37#i4（国家税务总局关于非居民企业所得税源泉扣缴有关问题的公告 国家税务总局公告2017年第37号）「应当按照扣缴义务发生之日人民币汇率中间价折合成人民币」
  - 参数 cn.time.holiday_roll：uses = 1 bool；cn.reg.tca#109（中华人民共和国税收征收管理法实施细则 国务院令第362号（2016年修订））「期限的最后一日是法定休假日的，以休假日期满的次日为期限的最后一日」
  - 参数 cn.time.long_holiday_days：uses = 3 days；cn.reg.tca#109（中华人民共和国税收征收管理法实施细则 国务院令第362号（2016年修订））「在期限内有连续３日以上法定休假日的，按休假日天数顺延」
- **hk.p2.base**（A_TEXT，2026-06-30）通过
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
- **hk.p2.iir**（A_TEXT，2026-06-30）通过
  - 参数 p2.minimum_rate：value = 15 %；hk.ord.2025-21#p147（Inland Revenue (Amendment) (Minimum Tax for Multinational Enterprise Groups) Ordinance 2025 Ord. No. 21 of 2025）「Minimum rate (最低稅率) means fifteen pe…」
  - 参数 p2.revenue_threshold：threshold = 750000000 EUR；hk.ord.2025-21#p42（Inland Revenue (Amendment) (Minimum Tax for Multinational Enterprise Groups) Ordinance 2025 Ord. No. 21 of 2025）「annual revenue of EUR 750 million or…」
  - 参数 p2.qualified_iir_hk：threshold = 1 bool；intl.oecd.globe.central-record.2025-12#p7（OECD/G20 Inclusive Framework: Administrative Guidance on the GloBE Rules (Pillar Two) — Central Record of Legislation with Transitional Qualified Status (as at 1 December 2025) ）「Hong Kong (China) Inland Revenue (Am…」
  - 参数 hk.p2.iir_payable_from：uses = 1 bool；hk.ord.2025-21#p22（Inland Revenue (Amendment) (Minimum Tax for Multinational Enterprise Groups) Ordinance 2025 Ord. No. 21 of 2025）「The IIR top-up tax is payable in rel…」
  - 参数 p2.qualified_iir_sg：uses = 1 bool；intl.oecd.globe.central-record.2025-12#p8（OECD/G20 Inclusive Framework: Administrative Guidance on the GloBE Rules (Pillar Two) — Central Record of Legislation with Transitional Qualified Status (as at 1 December 2025) ）「Singapore Multinational Enterprise (…」
  - 口径 D20：锚点 12/12 找到原文
- **hk.p2.topup**（A_TEXT，2026-06-30）通过
  - 参数 p2.minimum_rate：value = 15 %；hk.ord.2025-21#p147（Inland Revenue (Amendment) (Minimum Tax for Multinational Enterprise Groups) Ordinance 2025 Ord. No. 21 of 2025）「Minimum rate (最低稅率) means fifteen pe…」
  - 参数 p2.revenue_threshold：threshold = 750000000 EUR；hk.ord.2025-21#p42（Inland Revenue (Amendment) (Minimum Tax for Multinational Enterprise Groups) Ordinance 2025 Ord. No. 21 of 2025）「annual revenue of EUR 750 million or…」
  - 参数 p2.qualified_iir_hk：threshold = 1 bool；intl.oecd.globe.central-record.2025-12#p7（OECD/G20 Inclusive Framework: Administrative Guidance on the GloBE Rules (Pillar Two) — Central Record of Legislation with Transitional Qualified Status (as at 1 December 2025) ）「Hong Kong (China) Inland Revenue (Am…」
  - 参数 hk.p2.hkmtt：uses = 1 bool；hk.ord.2025-21#p21（Inland Revenue (Amendment) (Minimum Tax for Multinational Enterprise Groups) Ordinance 2025 Ord. No. 21 of 2025）「Schedule 62 has effect for charging …」
  - 口径 D20：锚点 12/12 找到原文
- **sg.fsie.charge**（A_TEXT，2026-06-30）通过
  - 参数 sg.corp.rate：value = 17 %；sg.ita1947.full#s43（Income Tax Act 1947 (assembled whole-document HTML: base page + 36 lazy-load fragments) ）「every company or body of persons, ta…」
  - 参数 sg.fsie.receipt_kinds：threshold = REMITTED;DEBT_SETTLED;MOVABLE_PROPERTY enum；sg.ita1947.full#s10（Income Tax Act 1947 (assembled whole-document HTML: base page + 36 lazy-load fragments) ）「any amount from any income derived f…」
  - 参数 sg.charge.basis：uses = accruing_in_or_derived_from_sg;received_in_sg_from_outside enum；sg.ita1947.full#s10（Income Tax Act 1947 (assembled whole-document HTML: base page + 36 lazy-load fragments) ）「upon the income of any person accrui…」
  - 参数 sg.foreign_income.remittance_is_receipt：uses = 1 bool；sg.ita1947.full#s10（Income Tax Act 1947 (assembled whole-document HTML: base page + 36 lazy-load fragments) ）「any amount from any income derived f…」
  - 参数 sg.fsie.recipient：uses = 1 bool；sg.ita1947.full#s13（Income Tax Act 1947 (assembled whole-document HTML: base page + 36 lazy-load fragments) ）「on or after 1 June 2003 by any perso…」
  - 参数 sg.corp.rate_entity：uses = 1 bool；sg.ita1947.full#s43（Income Tax Act 1947 (assembled whole-document HTML: base page + 36 lazy-load fragments) ）「for every dollar of the first $10,00…」
- **sg.fsie.gain.base**（A_TEXT，2026-06-30）通过
  - 参数 sg.s10l.open_market_price：uses = 1 bool；sg.ita1947.full#s10L（Income Tax Act 1947 (assembled whole-document HTML: base page + 36 lazy-load fragments) ）「the Comptroller may treat the follow…」
  - 求值器出处 sg.ita1947.full#s10：Income Tax Act 1947 (assembled whole-document HTML: base page + 36 lazy-load fragments) 
  - 求值器出处 sg.ita1947.full#s10L：Income Tax Act 1947 (assembled whole-document HTML: base page + 36 lazy-load fragments) 
  - 求值器出处 sg.etax.10l#para11.3：IRAS e-Tax Guide: Income Tax: Tax Treatment of Gains or Losses from the Sale of Foreign Assets (Third Edition) Third Edition
  - 口径 D32：锚点 7/7 找到原文
- **sg.ftc.dta**（A_TEXT，2026-06-30）通过
  - 参数 sg.ftc.credit_limit：uses = sg_tax_on_same_income_at_average_rate enum；sg.ita1947.full#s50（Income Tax Act 1947 (assembled whole-document HTML: base page + 36 lazy-load fragments) ）「The credit must not exceed the amoun…」
  - 参数 sg.ftc.tax_payable_under_arrangements：uses = 1 bool；sg.ita1947.full#s50（Income Tax Act 1947 (assembled whole-document HTML: base page + 36 lazy-load fragments) ）「tax payable in respect of any income…」
- **sg.ftc.pooling**（A_TEXT，2026-06-30）通过
  - 参数 sg.ftc.pooling_election：threshold = 1 bool；sg.ita1947.full#s50C（Income Tax Act 1947 (assembled whole-document HTML: base page + 36 lazy-load fragments) ）「the person may elect to be given a p…」
  - 参数 sg.ftc.pooling_foreign_tax_paid：threshold = 1 bool；sg.ita1947.full#s50C（Income Tax Act 1947 (assembled whole-document HTML: base page + 36 lazy-load fragments) ）「income tax (by whatever name called)…」
  - 参数 sg.ftc.pooling_headline_rate_min：threshold = 15 %；sg.ita1947.full#s50C（Income Tax Act 1947 (assembled whole-document HTML: base page + 36 lazy-load fragments) ）「carried on by a company in that terr…」
  - 参数 sg.ftc.pooling_sg_tax_not_nil：uses = 1 bool；sg.ita1947.full#s50C（Income Tax Act 1947 (assembled whole-document HTML: base page + 36 lazy-load fragments) ）「the income tax payable under this Ac…」
- **sg.p2.base**（A_TEXT，2026-06-30）通过
  - 参数 sg.p2.minimum_rate：uses = 15 %；sg.memta2024.s7#s7（Multinational Enterprise (Minimum Tax) Act 2024 - section 7 (Minimum rate), single-provision view ）「The minimum rate is 15%.」
  - 求值器出处 sg.memta2024.s16#s16：Multinational Enterprise (Minimum Tax) Act 2024 - section 16 (Top-up amounts of constituent entities other than special entities), single-provision view 
  - 求值器出处 sg.memta2024.s17#s17：Multinational Enterprise (Minimum Tax) Act 2024 - section 17 (Effective tax rate for constituent entities other than special entities), single-provision view 
  - 求值器出处 sg.memta2024.s21#s21：Multinational Enterprise (Minimum Tax) Act 2024 - section 21 (Additional current top-up amount for constituent entities other than special entities), single-provision view 
  - 求值器出处 sg.memta2024.s30#s30：Multinational Enterprise (Minimum Tax) Act 2024 - section 30 (Top-up amounts of constituent entities), single-provision view 
- **sg.p2.mtt**（A_TEXT，2026-06-30）通过
  - 参数 sg.p2.minimum_rate：value = 15 %；sg.memta2024.s7#s7（Multinational Enterprise (Minimum Tax) Act 2024 - section 7 (Minimum rate), single-provision view ）「The minimum rate is 15%.」
  - 参数 sg.p2.revenue_threshold：threshold = 750000000 EUR；sg.memta2024.s8#s8（Multinational Enterprise (Minimum Tax) Act 2024 - section 8 (MNE group to which this Act applies), single-provision view ）「A is EUR 750 million or its equivale…」
  - 参数 p2.qualified_iir_sg：threshold = 1 bool；intl.oecd.globe.central-record.2025-12#p8（OECD/G20 Inclusive Framework: Administrative Guidance on the GloBE Rules (Pillar Two) — Central Record of Legislation with Transitional Qualified Status (as at 1 December 2025) ）「Singapore Multinational Enterprise (…」
  - 参数 sg.p2.mtt_chargeable_entity：uses = 1 bool；sg.memta2024.s12#s12（Multinational Enterprise (Minimum Tax) Act 2024 - section 12 (Part 2, multinational enterprise minimum tax), single-provision view ）「An entity (called in this Act a char…」
  - 参数 p2.qualified_iir_hk：uses = 1 bool；intl.oecd.globe.central-record.2025-12#p7（OECD/G20 Inclusive Framework: Administrative Guidance on the GloBE Rules (Pillar Two) — Central Record of Legislation with Transitional Qualified Status (as at 1 December 2025) ）「Hong Kong (China) Inland Revenue (Am…」
  - 口径 D20：锚点 12/12 找到原文
- **sg.p2.topup**（A_TEXT，2026-06-30）通过
  - 参数 sg.p2.minimum_rate：value = 15 %；sg.memta2024.s7#s7（Multinational Enterprise (Minimum Tax) Act 2024 - section 7 (Minimum rate), single-provision view ）「The minimum rate is 15%.」
  - 参数 sg.p2.revenue_threshold：threshold = 750000000 EUR；sg.memta2024.s8#s8（Multinational Enterprise (Minimum Tax) Act 2024 - section 8 (MNE group to which this Act applies), single-provision view ）「A is EUR 750 million or its equivale…」
  - 参数 p2.qualified_iir_sg：threshold = 1 bool；intl.oecd.globe.central-record.2025-12#p8（OECD/G20 Inclusive Framework: Administrative Guidance on the GloBE Rules (Pillar Two) — Central Record of Legislation with Transitional Qualified Status (as at 1 December 2025) ）「Singapore Multinational Enterprise (…」
  - 参数 sg.p2.dtt：uses = 1 bool；sg.memta2024.s28#s28（Multinational Enterprise (Minimum Tax) Act 2024 - section 28 (DTT payable in respect of MNE group and amount of DTT), single-provision view ）「DTT is payable in respect of an MNE …」
  - 口径 D20：锚点 12/12 找到原文
- **sg.s10l.gain**（D_DISCRETION，2026-06-30）通过
  - 参数 sg.s10l.relevant_group_entity：threshold = 1 bool；sg.ita1947.full#s10L（Income Tax Act 1947 (assembled whole-document HTML: base page + 36 lazy-load fragments) ）「gains from the sale or disposal by a…」
  - 参数 sg.s10l.excluded_entity：threshold = 1 bool；sg.ita1947.full#s10L（Income Tax Act 1947 (assembled whole-document HTML: base page + 36 lazy-load fragments) ）「carried out by an entity that is an …」
  - 判断出处 sg.ita1947.full#s10L：Income Tax Act 1947 (assembled whole-document HTML: base page + 36 lazy-load fragments) 
  - 参数 sg.s10l.received_in_sg_trigger：uses = 1 bool；sg.ita1947.full#s10L（Income Tax Act 1947 (assembled whole-document HTML: base page + 36 lazy-load fragments) ）「that are received in Singapore from …」
  - 参数 sg.s10l.substance_pure_holding：uses = 1 bool；sg.ita1947.full#s10L（Income Tax Act 1947 (assembled whole-document HTML: base page + 36 lazy-load fragments) ）「the entity has adequate human resour…」
  - 参数 sg.s10l.substance_non_pure_holding：uses = 1 bool；sg.ita1947.full#s10L（Income Tax Act 1947 (assembled whole-document HTML: base page + 36 lazy-load fragments) ）「the entity has adequate economic sub…」
  - 参数 sg.s10l.share_situs：uses = place_of_incorporation enum；sg.ita1947.full#s10L（Income Tax Act 1947 (assembled whole-document HTML: base page + 36 lazy-load fragments) ）「any shares in or securities issued b…」
  - 参数 sg.s10l.place_of_business：uses = 1 bool；sg.ita1947.full#s10L（Income Tax Act 1947 (assembled whole-document HTML: base page + 36 lazy-load fragments) ）「any entity of the group has a place …」
  - 口径 D32：锚点 7/7 找到原文

## 事实来源（规则读到的事实，按流）

- reorg：推导（facts.py） 13（authority_action、cn_related、consideration、date_of_payment、disposed_in_s10l_regime、prior_map_outcome…）；方案动作 7（receipt_kind、reorg_commitment_3y、reorg_equity_payment_share、reorg_filed、reorg_operations_unchanged_12m、reorg_shares_kept_12m…）；未定（按两端计） 2（cost_basis、is_excluded_entity）；未给出（规则判为不影响结果） 13（arms_length_value、assessment_notice_on、cn_cost_basis、first_notification_on、foreign_tax_rate、immovable_ratio…）；结构性缺省（按否） 1（shares_cancelled）；设计或模板设定 2（max_ratio_12m、reorg_step）
- up1：推导（facts.py） 10（authority_action、capitalised、date_of_payment、direct_ratio、prior_map_outcome、reorg_special_applied…）；推导（引擎） 1（reorg_same_residence）；方案动作 3（holding_months、receipt_kind、residence_cert）；未定（按两端计） 6（direct_payment、reinvested_in_cn、reinvestment_form、reinvestment_from_distributed_profit、reinvestment_withdrawn、bo_safe_harbour）；未给出（规则判为不影响结果） 12（assessment_notice_on、capitalised_from、dividend_from_pre_reorg_profits、first_notification_on、foreign_tax_rate、payable_on…）；陈述 2（foreign_headline_rate、foreign_taxed）
- up2：推导（facts.py） 2（foreign_headline_rate、payee_in_source_jur）；方案动作 1（receipt_kind）；未定（按两端计） 1（foreign_taxed）；未给出（规则判为不影响结果） 3（assessment_notice_on、ucmt_location、ucmt_location）

陈述的事实 2 个，附出处 0 个。
