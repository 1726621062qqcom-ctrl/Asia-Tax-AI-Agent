"""Event, structural constants and ADJUSTABLE (v1 §4, 场景.md §2). The candidate space itself lives in scenarios.py as
templates: free roles × structural variables. Everything the taxpayer can simply "do more of" (substance, holding
ratio, holding period) is not enumerated but returned as a PLAN item.
"""
from dataclasses import dataclass
from typing import Optional

EQUITY, DEBT = "EQUITY", "DEBT"
DIRECT, INDIRECT = "DIRECT", "INDIRECT"
DIVIDEND_OUT = "DIVIDEND"

# Plan-controlled fields: under the single objective the taxpayer always takes the favourable side of a ">= threshold"
# condition, so these are returned as PLAN items instead of being enumerated. max_ratio_12m is deliberately absent:
# Art 13 favours holdings *below* 25%, and selling down is not a free choice.
ADJUSTABLE = frozenset({"headcount", "premises", "opex", "outsourced_in_hk", "registration_filing_compliant",
                        "direct_ratio", "ratio", "holding_months", "planned_holding_months", "clawback_event_within_2y",
                        "hk_holding_months",                                    # decision D44: Hong Kong's, as holding_months
                        # the restructuring step (decision D18): how it is paid, the commitments and filings, the relief claims,
                        # which profits a later dividend distributes
                        "reorg_equity_payment_share", "reorg_operations_unchanged_12m", "reorg_shares_kept_12m",
                        "reorg_commitment_3y", "reorg_filed", "stamp_relief_claimed", "dividend_from_pre_reorg_profits",
                        "asset_disposed_within_2y",
                        # the IP transfer step (decision D22, D23): the technology contract registered for the income-tax
                        # reduction and recognised for the VAT exemption; the buyer keeps what an input credit needs
                        "tech_transfer_registered", "vat_tech_recognized", "input_vat_documents_kept",
                        "vat_simplified_elected"})                # decision D48: the 5% simplified method for old property

# What a company the plan creates (created_by_plan) is designed to be: its own facts become PLAN items too. Judgements
# of an authority (substance ruled adequate, beneficial ownership, main purpose) stay rulings; listed status, legal
# form and the like are not designed.
DESIGNABLE = frozenset({"pure_equity_holding", "residence_cert", "fixed_place_in_cn", "fixed_place_in_hk", "fixed_place_in_sg",
                        "ftc_pooling_election", "sch17k_elected", "tp_documentation_provided",
                        "vat_general_taxpayer",           # 增值税法 第九条: a company may register as a general taxpayer
                        "gst_input_fully_recoverable"})   # GST Act s21(3): a company making only zero-rated supplies
DESIGNABLE_FLOW = frozenset({"held_as_trading_stock",      # a holding the created company disposes of (it is the payee)
                             "receipt_kind",               # decision D21: whether it brings what it receives into its jurisdiction
                             "purchase_effected_in_hk",    # decision D42: where a trader it creates effects its purchase and sale
                             "sale_effected_in_hk",        # contracts (DIPN 21 ¶23, ¶25: by its own staff or agents abroad)
                             "routed_via_trader"})         # decision D43: whether the goods pass through it or go straight on


@dataclass
class Event:
    dividend: Optional[float] = None       # upward distribution from the operating company (any repatriation form)
    onward: Optional[float] = None         # what the intermediate holder passes on (default: the same amount)
    exit: Optional[float] = None           # consideration for selling the operating company (or its holder)
    exit_on: object = None                 # date of the exit (default: on)
    capitalisable: Optional[float] = None  # decision D46: retained earnings OP may capitalise for its holder before the exit
    property_sale: Optional[float] = None  # decision D48: the price an outside buyer pays OWNER for its land or building
    property_rent: Optional[float] = None  # decision D49: the yearly rent an outside TENANT pays OWNER for it (recurring)
    royalty: Optional[float] = None
    service_fee: Optional[float] = None
    interest: Optional[float] = None       # interest to an outside lender (financing template)
    goods_sale: Optional[float] = None     # decision D42: the price the outside customer pays for the goods (trading template)
    goods_supply: Optional[float] = None   # decision D42: the price the manufacturer charges a group trader (a case fact)
    on: object = None                      # date of the flows
    as_at: object = None                   # the date the case is looked at: clocks of settled items are judged against it
    years: int = 1                         # recurring flows (dividend, interest, royalty, fee) repeat this many years
    horizon_years: int = 1
