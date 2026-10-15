# 依据核对：financing_OPCN-ULHK_full_open_y1

运行 20261011T071606-financing_OPCN-ULHK_full_open_y1，版本 f0b4ac2c2e8b。规划器给出了方案；核对 36 项：通过 28，说明 7，警示 1，失败 0。

**结论**：每一步都落到现行条文的原文；陈述的事实未附出处（0/8）。

候选 {'LENDER': 'CN', 'payment': False}；保证税额 5233550.00，最好情形 5233550.00；重算一致。

## 需要处理的

- 警示：financing_OPCN-ULHK_full_open_y1 案例陈述的事实 8 个，附出处的 0 个（案例文件没有 provenance，见 案例采集.md §4.2）

## 税项（保证税额一端）

| 流 | 法域 | 税种 | 承担方 | 金额 | 规则 | 依据 |
|---|---|---|---|---|---|---|
| int | CN | vat | LENDER（集团外） | 60.00 | cn.vat.law.interest_received | 通过 |
| int | CN | income | LENDER（集团外） | 250.00 | cn.domestic.charge、cn.ftc.direct | 通过 |
| int | CN | income | OP | -250.00 | cn.deduct.interest、cn.deduct.interest.benchmark | 通过 |
| p2:ULT | HK | income | ULT | 5233800.00 | hk.p2.topup、hk.p2.base | 通过 |

## 方案动作

| 动作 | 依据所在的规则 | 依据 |
|---|---|---|
| group.p2_tcsh_elected_cn:elect | sg.p2.topup、sg.p2.mtt、sg.p2.base、hk.p2.topup、hk.p2.iir、hk.p2.base | 通过 |

## 期限与罚款

| 流 | 规则 | 依据 |
|---|---|---|
| int | cn.wht.remit | 通过 |

## 规则依据（本方案用到的 12 条规则）

- **cn.deduct.interest**（D_DISCRETION，2026-03-31）通过
  - 参数 cn.eit.rate：value = 25 %；cn.law.eit#4（中华人民共和国企业所得税法 ）「企业所得税的税率为25％」
  - 参数 cn.thincap.ratio_other：threshold = 2 ratio；cn.cs.2008-121#i1（财政部 国家税务总局关于企业关联方利息支出税前扣除标准有关税收政策问题的通知 财税〔2008〕121号）「其他企业，为2：1」
  - 判断出处 cn.cs.2008-121#i2：财政部 国家税务总局关于企业关联方利息支出税前扣除标准有关税收政策问题的通知 财税〔2008〕121号
  - 参数 cn.deduct.general：uses = 1 bool；cn.law.eit#8（中华人民共和国企业所得税法 ）「企业实际发生的与取得收入有关的、合理的支出，包括成本、费用、税金、损失和…」
  - 参数 cn.thincap.disallow：uses = 1 bool；cn.law.eit#46（中华人民共和国企业所得税法 ）「企业从其关联方接受的债权性投资与权益性投资的比例超过规定标准而发生的利息…」
  - 参数 cn.thincap.ratio_financial：uses = 5 ratio；cn.cs.2008-121#i1（财政部 国家税务总局关于企业关联方利息支出税前扣除标准有关税收政策问题的通知 财税〔2008〕121号）「金融企业，为5：1」
  - 参数 cn.thincap.arms_length_exception：uses = 1 bool；cn.cs.2008-121#i2（财政部 国家税务总局关于企业关联方利息支出税前扣除标准有关税收政策问题的通知 财税〔2008〕121号）「证明相关交易活动符合独立交易原则的；或者该企业的实际税负不高于境内关联方…」
  - 参数 cn.eit.rate_entity：uses = 1 bool；cn.law.eit#28（中华人民共和国企业所得税法 ）「国家需要重点扶持的高新技术企业，减按15％的税率征收企业所得税」
- **cn.deduct.interest.benchmark**（A_TEXT，2026-03-31）通过
  - 参数 cn.deduct.interest_benchmark：uses = 1 bool；cn.reg.eit#38（中华人民共和国企业所得税法实施条例 国务院令第512号）「非金融企业向非金融企业借款的利息支出，不超过按照金融企业同期同类贷款利率…」
  - 求值器出处 cn.reg.eit#38：中华人民共和国企业所得税法实施条例 国务院令第512号
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
- **cn.vat.law.interest_received**（A_TEXT，2026-03-31）通过
  - 参数 cn.vat.law.rate_services：value = 6 %；cn.law.vat#10（中华人民共和国增值税法 ）「纳税人销售服务、无形资产，除本条第一项、第二项、第五项规定外，税率为百分…」
  - 参数 cn.vat.law.unified_borrowing_exempt：threshold = 1 bool；cn.cs.2026-10#i2（财政部 税务总局关于增值税法施行后增值税优惠政策衔接事项的公告（财政部 税务总局公告2026年第10号） 财政部 税务总局公告2026年第10号）「统借统还业务利息收入，是指统借统还业务中，企业集团或企业集团中的核心企业…」
  - 参数 cn.vat.law.taxable_in_cn：uses = 1 bool；cn.law.vat#4（中华人民共和国增值税法 ）「除本条第二项、第三项规定外，销售服务、无形资产的，服务、无形资产在境内消…」
  - 参数 cn.vat.law.inclusive_price：uses = 1 bool；cn.reg.vat#16（中华人民共和国增值税法实施条例（国务院令第826号） 国务院令第826号）「一般计税方法的销售额＝含税销售额÷（1＋税率）」
  - 参数 cn.vat.law.loan_services：uses = 1 bool；cn.reg.vat#2（中华人民共和国增值税法实施条例（国务院令第826号） 国务院令第826号）「增值税法第三条所称服务，包括交通运输服务、邮政服务、电信服务、建筑服务、…」
  - 参数 cn.vat.law.loan_input_not_creditable：uses = 1 bool；cn.reg.vat#21（中华人民共和国增值税法实施条例（国务院令第826号） 国务院令第826号）「纳税人购进贷款服务的利息支出，及其向贷款方支付的与该贷款服务直接相关的投…」
  - 所依法律的施行条款 cn.law.vat#38：中华人民共和国增值税法 
  - 口径 D23：锚点 6/6 找到原文
  - 口径 D25：锚点 4/4 找到原文
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
- **hk.p2.base**（A_TEXT，2026-04-02）通过
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
- **hk.p2.topup**（A_TEXT，2026-04-02）通过
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

- int：推导（facts.py） 3（date_of_payment、payee_in_source_jur、payee_is_related）；未给出（规则判为不影响结果） 9（arms_length_max、assessment_notice_on、payable_on、pboc_benchmark_rate、remitted_on、tax_paid_on…）；陈述 7（benchmark_rate、interest_rate、price_includes_vat、unified_borrowing_relending、related_party_debt_equity_ratio、related_party_volume…）
- p2:ULT：推导（引擎） 1（p2_etr）；未给出（规则判为不影响结果） 3（assessment_notice_on、determination_on、p2_additional）；结构性缺省（按否） 1（p2_iir）；陈述 1（group_revenue_eur）

陈述的事实 8 个，附出处 0 个。
