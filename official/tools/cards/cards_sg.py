# -*- coding: utf-8 -*-
"""案例采集 K1, Singapore: factors and precedents for the judgements of spec_sg.py (issue keys "SG:<Discretion key>").
binding = High Court and above (案例采集.md §5); IRAS advance rulings bind only the applicant: persuasive."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cards_lib import write  # noqa: E402

CH, HY, BBO, JD, BFC, AQQ = ("sg.judg.1987-sghc-14", "sg.judg.2006-sgca-7", "sg.judg.2014-sgca-10", "sg.judg.2005-sgca-52",
                             "sg.judg.2014-sgca-39", "sg.judg.2014-sgca-15")
A3_21, A4_25, A8_26, A11_26, A7_25, A8_24, A17_26, A11_25 = ("sg.ars.2021-03", "sg.ars.2025-04", "sg.ars.2026-08", "sg.ars.2026-11",
                                                            "sg.ars.2025-07", "sg.ars.2024-08", "sg.ars.2026-17", "sg.ars.2025-11")
SRC, CAP, IPC, SUB, DED = ("SG:income_sourced_in_sg", "SG:gain_is_capital_in_nature", "SG:ip_held_as_capital_asset",
                           "SG:adequate_substance", "SG:incurred_in_production_of_income")
FACTORS = [
    # source of interest / royalty received by a Singapore company (s10(1); sg.onshore.charge)
    (SRC, "src_funded_sg", "flow", "loan_funded_from_sg", "is_true", "true", CH, "the funds for the loan were provided for in Singapore", "Chandos [26]"),
    (SRC, "src_disbursed_sg", "flow", "loan_disbursed_in_sg", "is_true", "true", CH,
     "that loan was disbursed in Singapore and credited to the account of the borrower in Singapore", "Chandos [26]"),
    (SRC, "src_used_sg", "flow", "loan_funds_used_in_sg", "is_true", "true", CH,
     "the funds provided by the loan of S$9m to Delacom were used in Singapore within the meaning of s 12(6)(b)", "Chandos [29]; s12(6)(b) deems it"),
    (SRC, "src_not_used_sg", "flow", "loan_funds_used_in_sg", "is_false", "false", A4_25,
     "The funds from the loans to Company B has not been brought into or used in Singapore", "ARS 4/2025 2(h)"),
    (SRC, "src_activities_sg", "flow", "income_activities_in_sg", "is_true", "true", A3_21,
     "The active management of the Franchise Agreement, regular monitoring of the Franchise Agreement and updating to Company A", "ARS 3/2021 5(b)"),
    (SRC, "src_no_activities_sg", "flow", "income_activities_in_sg", "is_false", "false", A4_25,
     "No part of the activities relating to the loans to Company B will be carried out in Singapore", "ARS 4/2025 2(j)"),
    (SRC, "src_owner_party", "flow", "payee_owner_and_contracting_party", "is_true", "true", A3_21,
     "will be the legal and economic owner of the IP rights", "ARS 3/2021 5(c)"),
    (SRC, "src_decisions_abroad", "flow", "key_decisions_outside_sg", "is_true", "false", A3_21,
     "All significant operating management and decision making as the owner of its IP rights will be done outside Singapore",
     "ARS 3/2021 2(f); Chandos [5]: the board approved the loan in Hong Kong"),
    (SRC, "src_contracts_abroad", "flow", "contracts_negotiated_outside_sg", "is_true", "false", A3_21,
     "All contracts relating to the IP rights will be negotiated and executed outside of Singapore", "ARS 3/2021 2(g); Chandos [27]: signing abroad carries no weight"),
    # capital or revenue: shares (s10(1); sg.gain.capital)
    (CAP, "cap_long_holding", "flow", "holding_years", "ge:20", "true", BBO, "weighs heavily in the balance of the Shares being found to be capital assets", "BBO [57]: held 20 to 30 years"),
    (CAP, "cap_strategic", "flow", "acquired_for_strategic_purpose", "is_true", "true", BBO, "gives rise to a very strong inference that they were capital assets", "BBO [56]"),
    (CAP, "cap_segregated", "flow", "held_apart_from_trading_stock", "is_true", "true", BBO,
     "The Shares were also treated differently and segregated from shares that were readily traded", "BBO [52]"),
    (CAP, "cap_infrequent", "flow", "disposals_infrequent", "is_true", "true", BBO, "There were only nine disposals of [C] shares over a span of 30 years", "BBO [58]"),
    (CAP, "cap_no_need", "flow", "sale_not_needed_for_business", "is_true", "true", BBO,
     "there was a weak nexus between the sale of the Shares and the carrying on of the Respondent", "BBO [60]"),
    (CAP, "cap_external", "flow", "sale_triggered_externally", "is_true", "true", BBO, "the Shares were eventually realised pursuant to the takeover of [C]", "BBO [63]"),
    (CAP, "rev_business_nature", "payee", "business_nature_infers_trading", "is_true", "false", BBO,
     "the nature of insurance (or similar) businesses would ordinarily give rise to an inference that the gains concerned arose in the course of trade", "BBO [40]"),
    # capital or revenue: IP (s10(1); sg.ip.revenue)
    (IPC, "ipcap_not_regular", "flow", "ip_transfers_not_regular", "is_true", "true", A11_25,
     "does not regularly transfer its right, title or interest in the Improvement IP in the ordinary course of its business", "ARS 11/2025 5(a)"),
    (IPC, "ipcap_group_reorg", "flow", "transfer_in_group_reorganisation", "is_true", "true", A11_25,
     "undertaken pursuant to a group restructuring to consolidate all relevant IP assets in Company C", "ARS 11/2025 5(b); ARS 17/2026 5(a)"),
    (IPC, "ipcap_not_in_lieu", "flow", "consideration_not_in_lieu_of_income", "is_true", "true", A11_25,
     "the consideration is not compensation for the loss of income or in lieu of trading receipts", "ARS 11/2025 5(c)"),
    # economic substance for s10L (sg.s10l.gain)
    (SUB, "sub_managed_sg", "payee", "operations_managed_in_sg", "is_true", "true", A7_25, "The operations and activities of Company A are managed in Singapore", "ARS 7/2025 2(g)"),
    (SUB, "sub_hr_premises", "payee", "adequate_hr_and_premises_in_sg", "is_true", "true", A7_25,
     "Company A has adequate human resources and premises in Singapore to carry out its operations", "ARS 7/2025 2(h); ARS 8/2026 2(h)"),
    (SUB, "sub_decisions_sg", "payee", "key_decisions_in_sg", "is_true", "true", A8_26, "The key business decisions of Company A are made by persons in Singapore", "ARS 8/2026 2(i)"),
    (SUB, "sub_parent_controls", "payee", "holdco_controls_and_defines_strategy", "is_true", "true", A11_26,
     "HoldCo has effective control over the company, derives economic benefits from the company", "ARS 11/2026 2(e)"),
    (SUB, "sub_no_employees", "payee", "has_no_employees", "is_true", "false", A11_26, "It has no employees", "ARS 11/2026 2(a)"),
    # deductions (s14; sg.deduct.*)
    (DED, "ded_link_broken", "payer", "borrowed_funds_not_used_for_income_source", "is_true", "false", JD,
     "this link would clearly be broken if the dividend income arose from a share investment counter which purchase was not funded by the loan", "JD Ltd [47]"),
    (DED, "ded_capital_loan", "payer", "loan_is_capital_in_nature", "is_true", "false", BFC,
     "A loan that is capital in nature is one that is taken for the purpose of acquiring or enlarging the permanent structure of a business", "BFC [30]"),
    (DED, "ded_no_real_cost", "payer", "interest_no_real_economic_cost_in_group", "is_true", "false", AQQ,
     "did not incur any real economic costs within the B Group as a whole", "AQQ [113]"),
]
PRECEDENTS = [
    ("SG-chandos-1987", SRC, "SG", "High Court", "binding", "1987-05-07", "true",
     ["src_funded_sg", "src_disbursed_sg", "src_used_sg"], ["src_decisions_abroad", "src_contracts_abroad"], ["src_funded_sg", "src_disbursed_sg"], CH,
     "source is not a legal concept but something which a practical man would regard as a real source of income",
     "Interest: the funds were raised in Singapore and disbursed in Singapore, held Singapore source; board approval in Hong Kong and signing in Johor do not change the conclusion ([5], [27]); the reasons are the two items at [26]"),
    ("SG-ars-3-2021", SRC, "SG", "IRAS advance ruling", "persuasive", "2021-04-01", "true",
     ["src_activities_sg", "src_owner_party"], ["src_decisions_abroad", "src_contracts_abroad"], [], A3_21,
     "The franchise income derived by Company A is sourced in Singapore", "Franchise income: the board's strategic decisions and contract management are in Singapore, held Singapore source; binds the applicant only"),
    ("SG-ars-4-2025", SRC, "SG", "IRAS advance ruling", "persuasive", "2025-03-03", "false",
     [], ["src_not_used_sg", "src_no_activities_sg"], [], A4_25,
     "would be regarded as foreign-sourced income for Singapore income tax purposes", "Loan interest: the funds were not brought into or used in Singapore and none of the activities are in Singapore, held foreign source; binds the applicant only"),
    ("SG-bbo-2014", CAP, "SG", "Court of Appeal", "binding", "2014-02-04", "true",
     ["cap_long_holding", "cap_strategic", "cap_segregated", "cap_infrequent", "cap_no_need", "cap_external"], ["rev_business_nature"], [], BBO,
     "whether the gain in question is a mere enhancement of value by realising a security or whether it was made in an operation of business",
     "Disposal of shares: an insurance business is presumed to trade, but long holding, strategic purpose, separate holding, rare disposals, no need to sell and a sale triggered by a takeover: held capital"),
    ("SG-ars-8-2024", CAP, "SG", "IRAS advance ruling", "persuasive", "2024-12-02", "true",
     ["cap_long_holding", "cap_infrequent"], [], [], A8_24, "is a capital transaction", "Held over 30 years, never sold subsidiary shares before: capital (s13W not applicable); binds the applicant only"),
    ("SG-ars-11-2025", IPC, "SG", "IRAS advance ruling", "persuasive", "2025-06-02", "true",
     ["ipcap_not_regular", "ipcap_group_reorg", "ipcap_not_in_lieu"], [], [], A11_25, "does not regularly transfer its right, title or interest",
     "IP transferred in a group reorganisation: capital receipt; binds the applicant only"),
    ("SG-ars-17-2026", IPC, "SG", "IRAS advance ruling", "persuasive", "2026-10-01", "true",
     ["ipcap_group_reorg"], [], [], A17_26, "is capital in nature", "IP transferred in an intra-group reorganisation: capital, but s19B(5) claws back the allowances given; binds the applicant only"),
    ("SG-ars-7-2025", SUB, "SG", "IRAS advance ruling", "persuasive", "2025-06-02", "true",
     ["sub_managed_sg", "sub_hr_premises"], [], [], A7_25, "The operations and activities of Company A are managed in Singapore",
     "Pure equity-holding entity: managed in Singapore with adequate staff and premises, s10L economic substance met; binds the applicant only"),
    ("SG-ars-8-2026", SUB, "SG", "IRAS advance ruling", "persuasive", "2026-06-02", "true",
     ["sub_hr_premises", "sub_decisions_sg"], [], [], A8_26, "The key business decisions of Company A are made by persons in Singapore",
     "Non-pure equity-holding entity: staff and decisions in Singapore, economic substance met; binds the applicant only"),
    ("SG-ars-11-2026", SUB, "SG", "IRAS advance ruling", "persuasive", "2026-07-01", "true",
     ["sub_parent_controls"], ["sub_no_employees"], [], A11_26, "The economic substance test will be applied at the HoldCo level",
     "Special purpose company without employees: economic substance tested at the holding company level; conditional; binds the applicant only"),
    ("SG-jd-2005", DED, "SG", "Court of Appeal", "binding", "2005-12-02", "false",
     [], ["ded_link_broken"], [], JD, "there must have been income produced before expenses are deductible", "Loan interest: the part without a direct link between the funds and the income-producing investment is not deductible"),
    ("SG-bfc-2014", DED, "SG", "Court of Appeal", "binding", "2014-07-25", "false",
     [], ["ded_capital_loan"], [], BFC, "all borrowing costs incurred on a loan that is capital in nature constitute capital expenditure",
     "Borrowing costs on a loan that is capital in nature are capital expenditure, not deductible"),
    ("SG-aqq-2014", DED, "SG", "Court of Appeal", "binding", "2014-02-26", "false",
     [], ["ded_no_real_cost"], [], AQQ, "Formal and mechanistic compliance with the letter of s 14(1)(a)(i) is insufficient",
     "Interest is not deductible when it carries no real economic cost for the group as a whole (s33 anti-avoidance also upheld in the same case)"),
]
nf, np_, missing = write(FACTORS, PRECEDENTS)
print("factors", nf, "precedents", np_)
for m in missing:
    print("  NOT FOUND", m)
