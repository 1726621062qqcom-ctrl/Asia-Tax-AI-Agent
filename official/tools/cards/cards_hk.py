# -*- coding: utf-8 -*-
"""案例采集 K1, Hong Kong: factors and precedents for the judgements of spec_hk.py (issue keys "HK:<Discretion key>").
binding = High Court (CFI) and above: the CFA binds all courts and the Board, the CA binds the CFI and the Board, the
CFI binds the Board; Board of Review decisions and IRD advance rulings are persuasive only (案例采集.md §5).
Patrick Cox (CA 2024) apportioned the royalties and remitted the case: a factor source, not a binary precedent."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cards_lib import write  # noqa: E402

ING, KM, KE, SL, PC, LF, DT, LYS, ABW, ZE, CH = (
    "hk.judg.facv-19-2006", "hk.judg.facv-20-2003", "hk.judg.facv-11-2006", "hk.judg.hcia-1-2024", "hk.judg.2024-hkca-944",
    "hk.judg.cacv-86-2011", "hk.judg.cacv-275-2008", "hk.judg.facv-14-2007", "hk.judg.hcia-1-1992", "hk.judg.facv-15-2006",
    "hk.judg.2025-hkca-956")
B1122, B719, B823 = "hk.bor.d11-22", "hk.bor.d7-19", "hk.bor.d8-23"
A68, A69, A70 = "hk.arc.68", "hk.arc.69", "hk.arc.70"
PA, IS, CA, DD, AS = ("HK:profits_arise_in_hk", "HK:income_sourced_in_hk", "HK:capital_asset",
                      "HK:incurred_in_production_of_profits", "HK:adequate_substance")

FACTORS = [
    # where profits from services / trading operations arise (s14; hk.service.charge, hk.domestic.charge, ...)
    (PA, "pa_rendered_offshore", "flow", "service_rendered_outside_hk", "is_true", "false", ING,
     "his profit is earned in the place where the service is rendered not where the contract for commission is entered into", "ING Baring [147]"),
    (PA, "pa_agents_offshore", "flow", "work_done_by_others_outside_hk", "is_true", "false", ING,
     "where the taxpayer employs others to act for him in carrying out a transaction for a client, his profit is earned in the place where they carry out his instructions",
     "ING Baring [147]; same in Li & Fung"),
    (PA, "pa_hk_antecedent", "flow", "hk_activities_antecedent", "is_true", "false", ING,
     "Such antecedent activities will often be commercially essential to the operations and profitability of the taxpayer's business, but they do not provide the legal test",
     "ING Baring [38]"),
    (PA, "pa_administered_hk", "payee", "business_administered_in_hk", "is_true", "true", ING,
     "the place where a business was administered is certainly one factor which should be taken into consideration",
     "ING Baring [48] citing the Board's view; the CFA held that the place of management and decision-making is not the test; listed as a factor on the Commissioner's side so that precedent coverage can be seen"),
    (PA, "pa_exertions_hk", "flow", "profit_earning_activities_in_hk", "is_true", "true", KM,
     "What actually earned the Profits for the Taxpayer were its exertions in the form of its activities in marketing the Property. And those activities took place in Hong Kong.",
     "Kwong Mile [43]"),
    (PA, "pa_contract_offshore", "flow", "contract_signed_outside_hk", "is_true", "false", KM,
     "This underwriting arrangement came to be embodied in a contract in Chinese signed by the Taxpayer and the Developer in the Mainland city of Guangzhou on 22 November 1991",
     "Kwong Mile [16]"),
    (PA, "pa_offshore_antecedent", "flow", "offshore_activities_antecedent", "is_true", "true", DT,
     "The Taxpayer's activities in the mainland were merely antecedent or incidental to the profit-generating activities.", "Datatronic [35]"),
    (PA, "pa_staff_offshore", "flow", "own_staff_work_outside_hk", "is_true", "false", DT,
     "There were other employees of the Taxpayer seconded to DSC", "Datatronic: employees seconded to the Mainland subsidiary"),
    (PA, "pa_hk_purchase_sale", "flow", "profit_transactions_concluded_in_hk", "is_true", "true", DT,
     "The profit-producing transactions were the purchase from DSC and subsequent sale by the Taxpayer.", "Datatronic [36]"),

    # source of interest / royalties a Hong Kong company receives from abroad (s14; hk.onshore.charge)
    (IS, "is_funds_from_hk", "flow", "funds_made_available_from_hk", "is_true", "true", SL,
     "the Shareholder Loan was advanced in Hong Kong", "Sinolink [5.15]"),
    (IS, "is_signed_offshore", "flow", "loan_negotiated_signed_outside_hk", "is_true", "false", SL,
     "At the most, SSI's negotiation and signing of the Investment Agreement amount to antecedent acts.", "Sinolink [8.5] adopting the Board's view"),
    (IS, "is_payer_offshore", "payer", "payer_outside_hk", "is_true", "false", SL,
     "one must not conflate SSI's act of earning the Sums with the source of payment of the Sums", "Sinolink [5.17]: the source of payment is not the test"),
    (IS, "is_accounts_hk", "flow", "accounts_kept_in_hk", "is_true", "true", KE,
     "The accounts on which customers were extended such margin facilities were opened with and kept by the Taxpayer in Hong Kong.", "Kim Eng [59]"),
    (IS, "is_not_simple_loan", "flow", "credit_not_simple_on_lending", "is_true", "true", KE,
     "There is a difference between the granting of margin facilities and the simple on-lending of money.", "Kim Eng [57]"),
    (IS, "is_royalty_on_foreign_sales", "flow", "royalty_measured_by_foreign_sales", "is_true", "false", PC,
     "there is more justification to say that such royalty income is produced by the exploitation of property assets abroad", "Patrick Cox [61]"),
    (IS, "is_fixed_minimum", "flow", "royalty_fixed_minimum", "is_true", "true", PC,
     "argument will lose much of its force", "Patrick Cox [61]: fixed minimum"),
    (IS, "is_rights_acquired_hk", "flow", "licensing_rights_acquired_in_hk", "is_true", "true", PC,
     "a small part of the Royalties Income should on an apportionment be held taxable as having arisen in or derived from Hong Kong",
     "Patrick Cox [65]: apportionment"),
    (IS, "is_agent_offshore", "flow", "licensing_work_done_by_agent_outside_hk", "is_true", "false", PC,
     "it is not necessary to show that the transaction which produced the profit was carried out by the taxpayer's agent in the full legal sense",
     "Patrick Cox [58]"),

    # capital or revenue (s14; hk.gain.capital)
    (CA, "ca_lengthy_holding", "flow", "held_for_lengthy_period", "is_true", "true", LYS,
     "has held the asset or commodity for a lengthy period?", "Lee Yee Shing [60] badges of trade"),
    (CA, "ca_selling_effort", "flow", "selling_effort_beyond_non_trader", "is_true", "false", LYS,
     "has expended time, money or effort in selling the asset or commodity that goes beyond what might be expected of a non-trader seeking to sell an asset of that class?",
     "Lee Yee Shing [60]"),
    (CA, "ca_stated_intention", "payee", "stated_long_term_investment_intention", "is_true", "true", ABW,
     "if the intention is on the evidence, genuinely held, realistic and realisable", "All Best Wishes [34]: must be genuine, realistic and realisable"),
    (CA, "ca_quick_resale", "flow", "resold_soon_after_acquisition", "is_true", "false", ABW,
     "the Taxpayer's intention, from the beginning, was to trade, in spite of what it said and what resolutions were passed", "All Best Wishes [47]"),
    (CA, "ca_shareholder_loans", "flow", "funded_by_interest_free_shareholder_loans", "is_true", "false", B823,
     "The substantial financing by shareholders' loans, unsecured and interest-free with no repayment dates", "D8/23 [158(10)]"),
    (CA, "ca_reasons_not_credible", "flow", "reasons_for_sale_not_credible", "is_true", "false", B823,
     "are not credible and not accepted", "D8/23 [158(5)]"),

    # deduction: incurred in the production of chargeable profits (s16)
    (DD, "dd_preserve_assets", "payer", "borrowing_preserves_profit_earning_assets", "is_true", "true", ZE,
     "if it is apparent that the purpose of the borrowing in question is to maintain the profit-earning capacity of the company by avoiding the need to sell profit-earning assets",
     "Zeta [17]"),
    (DD, "dd_loan_for_dividend", "payer", "borrowing_funds_dividend", "is_true", "false", ZE,
     "It is altogether too simplistic to say that because a loan is taken out for one purpose it cannot be regarded as taken out for some other underlying purpose",
     "Zeta [22]"),
    (DD, "dd_not_under_agreement", "flow", "paid_outside_written_agreement", "is_true", "false", CH,
     "were not expenses incurred in the production of the Taxpayer's assessable profits, and therefore not deductible under sections 16 and 17",
     "Chapman CA [19(1)]"),
    (DD, "dd_associated_payee", "flow", "payee_associated", "is_true", "false", CH,
     "The Taxpayer and Profit Gain were at all material times associated companies, sharing common shareholders, directors, and a correspondence address.",
     "Chapman CA [8]"),
    (DD, "dd_margin_shift", "flow", "payer_margin_far_below_payee", "is_true", "false", CH,
     "resulting in a profit margin far lower than that of Profit Gain, whilst the overall profits remained within the Group", "Chapman CA [71] (s61A)"),
    (DD, "dd_payee_real", "flow", "payee_has_real_operations", "is_true", "true", B1122,
     "Company A had its operation and is not a", "D11/22 headnote 8: the payee had operations and was not a sham"),
    (DD, "dd_sale_licence_back", "flow", "payment_for_own_ip_after_sale_and_licence_back", "is_true", "false", B719,
     "the sale-and-licence-back arrangement in this case is far removed from the ordinary course of Company A's business, and has a strange and artificial air about it",
     "D7/19 [177]"),
    (DD, "dd_arms_length", "flow", "amount_at_arms_length", "is_true", "true", B719,
     "did not exceed an arms' length value", "D7/19 [65(4)]: not decisive"),

    # FSIE economic substance (s15K): IRD advance rulings — practice only
    (AS, "as_staff_hk", "payee", "adequate_qualified_employees_in_hk", "is_true", "true", A68,
     "have a predetermined number range of employees with necessary qualifications to carry out the specified economic activities in Hong Kong each year",
     "ARC 68 §3"),
    (AS, "as_opex_hk", "payee", "adequate_operating_expenditure_in_hk", "is_true", "true", A68,
     "incur a predetermined amount range of annual operating expenditures in Hong Kong for the specified economic activities", "ARC 68 §3"),
    (AS, "as_outsourced_monitored", "payee", "outsourced_activities_adequately_monitored", "is_true", "true", A68,
     "undertake adequate monitoring of the specified economic activities carried out in Hong Kong by the Service Provider", "ARC 68 §3"),
    (AS, "as_outsourced_associate", "payee", "activities_outsourced_to_associate", "is_true", "true", A70,
     "are outsourced to an associated servicer provider", "ARC 70 §3"),
    (AS, "as_minimal_loans", "payee", "only_minimal_activities_needed", "is_true", "true", A69,
     "minimal activities are required by the Applicant to manage the loans", "ARC 69 §3"),
]

PRECEDENTS = [
    ("HK-ingbaring-2007", PA, "HK", "Court of Final Appeal", "binding", "2007-10-05", "false",
     ["pa_administered_hk"], ["pa_agents_offshore", "pa_hk_antecedent"], ["pa_agents_offshore"], ING,
     "it is that offshore trading transaction which ought to be regarded as the relevant profit-generating transaction on his part",
     "Brokerage commission: the transactions were executed offshore by overseas brokers on its instructions; research, sales and back office in Hong Kong were antecedent: not Hong Kong source"),
    ("HK-kwongmile-2004", PA, "HK", "Court of Final Appeal", "binding", "2004-07-08", "true",
     ["pa_exertions_hk"], ["pa_contract_offshore"], ["pa_exertions_hk"], KM,
     "focusing on effective causes without being distracted by antecedent or incidental matters",
     "Underwriting of uncompleted flats: the contract signed in Guangzhou and the risk borne in the Mainland only obtained the opportunity; the profit was earned by the marketing in Hong Kong: Hong Kong source"),
    ("HK-lifung-2012", PA, "HK", "Court of Appeal", "binding", "2012-03-19", "false",
     ["pa_administered_hk"], ["pa_agents_offshore"], ["pa_agents_offshore"], LF,
     "all the profit producing/making activities/transactions took place outside Hong Kong",
     "Sourcing agency commission: all profit-producing activities were done by overseas affiliated sourcing companies; supervision by the Hong Kong head office is not the test: not Hong Kong source (the Commissioner did not appeal to the CFA)"),
    ("HK-datatronic-2009", PA, "HK", "Court of Appeal", "binding", "2009-07-15", "true",
     ["pa_offshore_antecedent", "pa_hk_purchase_sale"], ["pa_staff_offshore"], ["pa_hk_purchase_sale"], DT,
     "The profit-producing transactions were the purchase from DSC and subsequent sale by the Taxpayer.",
     "Hong Kong company buying from its wholly owned Mainland subsidiary and reselling: providing machinery, know-how and seconded staff was antecedent or incidental: Hong Kong source"),
    ("HK-sinolink-2026", IS, "HK", "Court of First Instance", "binding", "2026-07-29", "true",
     ["is_funds_from_hk"], ["is_signed_offshore", "is_payer_offshore"], ["is_funds_from_hk"], SL,
     "making available the funds under Clause 3.1.1 for the use of RGAP which was the profit-generating act",
     "Shareholder loan interest: the funds were made available in Hong Kong: Hong Kong source; negotiation and signing in Shanghai were antecedent (no appeal seen as at 2026-10-11)"),
    ("HK-kimeng-2007", IS, "HK", "Court of Final Appeal", "binding", "2007-03-29", "true",
     ["is_accounts_hk", "is_not_simple_loan"], [], ["is_accounts_hk", "is_not_simple_loan"], KE,
     "The accounts on which customers were extended such margin facilities were opened with and kept by the Taxpayer in Hong Kong.",
     "Margin financing interest: the accounts were opened and kept in Hong Kong, and margin facilities differ from simple on-lending: Hong Kong source"),
    ("HK-allbestwishes-1992", CA, "HK", "High Court", "binding", "1992-07-31", "false",
     ["ca_stated_intention"], ["ca_quick_resale"], ["ca_quick_resale"], ABW,
     "the stated intention of the taxpayer cannot be decisive and the actual intention can only be determined upon the whole of the evidence",
     "Resolutions stated long-term investment, sold within a month of the occupation permit: trading (adopted by the CFA in Lee Yee Shing [59])"),
    ("HK-d8-23", CA, "HK", "Board of Review", "persuasive", "2023-07-28", "false",
     ["ca_stated_intention"], ["ca_selling_effort", "ca_shareholder_loans", "ca_reasons_not_credible"], [], B823,
     "collectively the badges of trade indicate a trading intention",
     "Car parking spaces: sold through agents on commission, financed by interest-free shareholder loans, reasons for sale not credible: trading; a Board decision has no binding force as precedent"),
    ("HK-zeta-2007", DD, "HK", "Court of Final Appeal", "binding", "2007-03-29", "true",
     ["dd_preserve_assets"], ["dd_loan_for_dividend"], ["dd_preserve_assets"], ZE,
     "Zeta was highly profitable but highly illiquid.",
     "Declared dividends converted into interest-bearing shareholder loans: to avoid selling profit-earning assets and keep the earning capacity: interest deductible"),
    ("HK-chapman-2025", DD, "HK", "Court of Appeal", "binding", "2025-10-30", "false",
     ["dd_payee_real"], ["dd_not_under_agreement", "dd_associated_payee", "dd_margin_shift"], ["dd_not_under_agreement"], CH,
     "were not expenses incurred in the production of the Taxpayer's assessable profits, and therefore not deductible under sections 16 and 17",
     "Management fees paid to an associated BVI company: the part paid outside the written agreement is not deductible, s61A also applied; leave to appeal to the CFA refused ([2026] HKCA 436)"),
    ("HK-d7-19", DD, "HK", "Board of Review", "persuasive", "2019-07-30", "false",
     ["dd_arms_length"], ["dd_sale_licence_back", "dd_associated_payee"], [], B719,
     "There simply was no genuine commercial reason for Company A to pursue a course that resulted in itself",
     "Royalties for the company's own trademarks after a sale-and-licence-back: no genuine commercial reason: not deductible; leave for a direct appeal granted in 2020, outcome not seen"),
    ("HK-arc-68-2023", AS, "HK", "IRD advance ruling", "persuasive", "2023-03-01", "true",
     ["as_staff_hk", "as_opex_hk", "as_outsourced_monitored"], [], [], A68,
     "will satisfy the economic substance requirement under section 15K of the IRO",
     "Hong Kong company holding 75%: predetermined ranges of staff and expenditure, outsourced with adequate monitoring: economic substance met; binds the applicant only"),
    ("HK-arc-69-2023", AS, "HK", "IRD advance ruling", "persuasive", "2023-03-01", "true",
     ["as_minimal_loans"], [], [], A69, "minimal activities are required by the Applicant to manage the loans",
     "20% holding and interest-free intra-group loans: managing the loans needs only minimal activities: economic substance met; binds the applicant only"),
    ("HK-arc-70-2023", AS, "HK", "IRD advance ruling", "persuasive", "2023-06-26", "true",
     ["as_outsourced_associate"], [], [], A70, "are outsourced to an associated servicer provider",
     "Group application: outsourced to an associated service provider: economic substance met; binds the applicant only"),
]

nf, np_, missing = write(FACTORS, PRECEDENTS)
print("factors", nf, "precedents", np_)
for m in missing:
    print("  NOT FOUND", m)
