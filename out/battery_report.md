# Battery report

cases: 1103, clean: 1103, with defects: 0

## defects

## rules never fired (0 of 263)

## silent by construction
- cn.wht.statutory: displaced by cn.wht.reduced wherever both apply (实施条例 第九十一条)
- hk.loss.change: no template has a Hong Kong loss company earning after its shares change hands

## boundary values (params.csv thresholds tried below / at / above)

thresholds compared with a number: 38; tried on a case where the rule fires: 35; live (a tax item differs across the threshold): 26
- dead: cn-hk.pe.service_days — inbound_services_SECN-CLHK_full_open_y1__thr_cn-hk-pe-service_days_below
- dead: cn.domestic.dividend_listed_months — repatriation_OPCN-ULHK-HOSG_full_open_y1__thr_cn-domestic-dividend_listed_months_below
- dead: cn.ftc.indirect_ratio_min — financing_OPHK-ULCN_full_open_y1__thr_cn-ftc-indirect_ratio_min_below
- dead: cn.indirect.asset_or_income_ratio — holding_OPCN-ULHK-HOSG_full_open_y1__thr_cn-indirect-asset_or_income_ratio_below
- dead: cn.reinvest.credit_min_holding_months — holding_OPCN-ULHK_full_open_y1_reinvest__thr_cn-reinvest-credit_min_holding_months_below
- dead: cn.reorg.equity_payment_min — holding_OPCN-ULHK_full_open_y1__thr_cn-reorg-equity_payment_min_below
- dead: cn.thincap.ratio_other — financing_OPCN-ULHK_full_open_y1_bank__thr_cn-thincap-ratio_other_below
- dead: hk.onshore_gain.holding_months_min — holding_OPCN-ULSG-HOHK_full_open_y1__thr_hk-onshore_gain-holding_months_min_below
- dead: sg.s13w.holding_months_min — holding_OPCN-ULHK-HOSG_full_open_y1__thr_sg-s13w-holding_months_min_below
- not tried: cn.bo.onpay_ratio — derived (onpay_ratio_12m): tested by check_cn_wht / check_scope
- not tried: cn.cfc.exempt_profit_max — derived (cfc_profit_total): tested by check_cn_wht / check_scope
- not tried: cn.cfc.low_tax_ratio — derived (cfc_tax_burden_ratio): tested by check_cn_wht / check_scope

## pairwise covering array over yes/no facts (levels yes / no / unknown)

- financing: 24 facts, 43 cases cover all 2484 pairs (exhaustive would be 2.82e+11 cases)
- holding: 62 facts, 78 cases cover all 17019 pairs (exhaustive would be 3.82e+29 cases)
- inbound_services: 18 facts, 33 cases cover all 1377 pairs (exhaustive would be 3.87e+08 cases)
- ip: 29 facts, 53 cases cover all 3654 pairs (exhaustive would be 6.86e+13 cases)
- property: 25 facts, 43 cases cover all 2700 pairs (exhaustive would be 8.47e+11 cases)
- repatriation: 53 facts, 71 cases cover all 12402 pairs (exhaustive would be 1.94e+25 cases)
- services: 22 facts, 38 cases cover all 2079 pairs (exhaustive would be 3.14e+10 cases)
- trading: 36 facts, 57 cases cover all 5670 pairs (exhaustive would be 1.5e+17 cases)

## mutation score (python -m tax_graph.mutation)

killed 356 of 435 mutants (82%) on 131 cases; by operator: DROP 174/187, NEG 113/147, PRED 41/64, SHIFT 28/37
- survived: NEG sg.nocharge.ip_purchase
- survived: NEG sg.ip.revenue
- survived: NEG sg.gain.capital
- survived: NEG sg.deduct.interest
- survived: NEG sg.deduct.royalty
- survived: NEG sg.deduct.service_fee
- survived: NEG sg.tp.deduction_cap
- survived: NEG sg.tp.surcharge
- survived: NEG cn.deduct.service
- survived: NEG cn.tp.adjustment_interest
- survived: NEG cn.domestic.dividend_exempt
- survived: NEG cn.ftc.dividend
- survived: NEG cn-hk.div.cap_other@cn
- survived: NEG cn-hk.roy.cap@cn
- survived: NEG cn-sg.div.cap_other@cn
- survived: NEG cn-sg.int.cap_other@cn
- survived: NEG cn-sg.roy.cap@cn
- survived: NEG cn.tp.deduction_cap
- survived: NEG cn.deduct.royalty
- survived: NEG hk.nocharge.outbound
- survived: NEG hk.nocharge.service_offshore
- survived: NEG hk.royalty.deemed_profit_associate
- survived: NEG cn-hk.roy.cap@hk
- survived: NEG hk.deduct.interest
- survived: NEG hk.deduct.service_fee
- survived: NEG hk.tp.deduction_cap
- survived: NEG hk.fsie.ip_nexus
- survived: NEG hk.fsie.substance.dividend
- survived: NEG hk.nocharge.ip_purchase
- survived: NEG hk.ip.onshore
- survived: NEG hk.domestic.charge
- survived: NEG hk.domestic.dividend
- survived: NEG hk.nocharge.service_offshore_resident
- survived: NEG hk.gain.capital
- survived: DROP sg.nocharge.ip_purchase
- survived: DROP sg.nocharge.dividend
- survived: DROP sg.s10l.not_in_force
- survived: DROP cn.liquidation.split
- survived: DROP cn.capital_reduction.split
- survived: DROP cn.domestic.dividend_exempt
- survived: DROP cn.ftc.dividend
- survived: DROP cn.indirect.listed_safe_harbour
- survived: DROP hk.nocharge.outbound
- survived: DROP hk.nocharge.service_offshore
- survived: DROP hk.nocharge.ip_purchase
- survived: DROP hk.domestic.dividend
- survived: DROP hk.nocharge.service_offshore_resident
- survived: PRED sg.p2.mtt group_revenue_eur ge->gt
- survived: PRED sg.gain.s13w ratio ge->gt
- survived: PRED cn-hk.pe.no_pe@cn service_days_12m le->lt
- survived: PRED cn-sg.pe.no_pe@cn service_days_12m le->lt
- survived: PRED cn.cfc.charge cfc_tax_burden_ratio lt->le
- survived: PRED cn.cfc.charge cfc_profit_total ge->gt
- survived: PRED cn.ftc.dividend direct_ratio lt->le
- survived: PRED cn-hk.div.cap_qualified@cn onpay_ratio_12m lt->le
- survived: PRED cn-hk.div.cap_other@cn onpay_ratio_12m lt->le
- survived: PRED cn-hk.int.cap@cn onpay_ratio_12m lt->le
- survived: PRED cn-hk.roy.cap@cn onpay_ratio_12m lt->le
- survived: PRED cn-hk.roy.cap_aircraft_ship_lease@cn onpay_ratio_12m lt->le
- survived: PRED cn-sg.div.cap_qualified@cn onpay_ratio_12m lt->le
