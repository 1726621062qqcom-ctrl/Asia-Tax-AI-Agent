"""Checks of the 范围.md v1.1 mechanics on hand-built graphs: Pillar Two top-up, the CFC inclusion, residence variants,
VAT withholding with the input credit, an outside lender (financing template), stamp duty on both sides, recurring
years. Expected values are read off the texts the params cite (oracle_kind = text_derived); the engine is run directly.

    python -m tax_graph.check_scope          (conda env "pytorch")
"""
import io
import sys
from dataclasses import replace
from datetime import date

from .cases import CASE_A, EVENT_A, BASE_A
from .data.domain import ADJUSTABLE, Event
from .engine import EX_ANTE, EX_POST, CaseCtx, bounds, engine
from .model import CN, HK, SG, DIVIDEND, INTEREST, ROYALTY, SERVICE_FEE, SHARE_TRANSFER, Entity, FlowEdge, Graph, HoldEdge
from .rules.tri import CEILING, DISCRETION, FLOOR, Need
from .scenarios import BUYER, FINANCING, HOLD, HOLDING, LENDER, OP, ULT, Case, RoleFacts

ON = date(2026, 3, 31)
NO_RELIEF = {"p2_qualified_cbcr_hk": False, "p2_qualified_cbcr_sg": False, "p2_dm_avg_revenue_eur_hk": 1e9, "p2_dm_avg_income_eur_hk": 1e9,
             "p2_dm_avg_revenue_eur_sg": 1e9, "p2_dm_avg_income_eur_sg": 1e9}   # neither Pillar Two relief available (decision D17)


def run(g, bound, mode=EX_POST):
    return engine(g, lambda facts: CaseCtx(facts, {}, mode, ADJUSTABLE), bound)


def main():
    out = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    bad = n = 0

    def check(ok, text):
        nonlocal bad, n
        bad += 0 if ok else 1
        n += 1
        out.write("%-4s %s\n" % ("ok" if ok else "FAIL", text))

    # ---- Pillar Two: a Hong Kong entity of an in-scope group with ETR 10% owes 5% of its excess profit (GloBE Art 5.2; HKMTT)
    g = Graph({"E": Entity("E", HK, attrs={**NO_RELIEF, "globe_income": 1000.0, "covered_taxes_other": 100.0, "group_revenue_eur": 1e9, "sbie": 0.0,
                                           "managed_from": HK}),
               "U": Entity("U", SG, attrs={"managed_from": SG})},
              [HoldEdge("U", "E", 100.0, date(2020, 1, 1), 100.0)],
              [FlowEdge("d", "E", "U", DIVIDEND, 100.0, ON, attrs={"receipt_kind": "NONE"})])
    lo = run(g, FLOOR)[2]
    check("p2:E" in lo and abs(lo["p2:E"].tax - 50.0) < 1e-6, "Pillar Two: (15%% - 10%%) x 1000 = 50 top-up on the HK entity (got %s)" % lo.get("p2:E", type("x", (), {"tax": None})).tax)
    with_sbie = replace(g.entities["E"], attrs={k: v for k, v in g.entities["E"].attrs.items() if k != "sbie"})
    with_sbie.attrs.update(payroll=1000.0, tangible_assets=1000.0)              # 2026: 9.4% + 7.4% = 168 excluded
    lo3 = run(Graph({**g.entities, "E": with_sbie}, g.holds, g.flows), FLOOR)[2]
    check(abs(lo3["p2:E"].tax - 0.05 * (1000.0 - 168.0)) < 1e-6, "Pillar Two: SBIE from payroll and tangible assets at the 2026 transition rates (got %s)" % lo3["p2:E"].tax)
    small = replace(g.entities["E"], attrs=dict(g.entities["E"].attrs, group_revenue_eur=1e8))
    lo2 = run(Graph({**g.entities, "E": small}, g.holds, g.flows), FLOOR)[2]
    check("p2:E" not in lo2 or lo2["p2:E"].tax == 0.0, "Pillar Two: below EUR 750 million the top-up rule does not apply")

    # ---- CFC: a Mainland parent's low-taxed Hong Kong subsidiary retaining 10m: nothing at the floor (judgements), 25% less
    #      the underlying tax at the ceiling, grossed up (EIT art 45; 实施条例 117-118; 2009-2 第八十四条; 125号 第五条)
    g = Graph({"ULT": Entity("ULT", CN), "SUB": Entity("SUB", HK, attrs={"after_tax_profit": 10_000_000.0, "managed_from": HK, "residence_cert": True,
                                                                          "bo_safe_harbour": True}),
               "OP": Entity("OP", CN)},
              [HoldEdge("ULT", "SUB", 100.0, date(2020, 1, 1), 1.0), HoldEdge("ULT", "OP", 100.0, date(2020, 1, 1), 1.0)],
              [FlowEdge("i", "OP", "SUB", INTEREST, 1_000_000.0, ON, attrs={"receipt_kind": "NONE", "interest_rate": 5.0, "benchmark_rate": 5.0})])
    lo, hi = run(g, FLOOR)[2], run(g, CEILING)[2]
    cfc = "cfc:SUB>ULT"
    check(cfc in lo and lo[cfc].tax == 0.0, "CFC: floor leaves the inclusion uncharged (active income / business need are judgements)")
    cn_hi = sum(hi[cfc].flow.amount * it.effective / 100.0 for it in hi[cfc].items if it.jur == CN) if cfc in hi else None
    # at the ceiling SUB bore 10% Mainland withholding on the 1m (treaty cap denied) and 16.5% Hong Kong FSIE tax less that
    # credit: 100,000 + 65,000 = 165,000; underlying share 1.65% grosses the 10m up and is credited
    expect = 0.25 * 10_000_000 * 1.0165 - 165_000
    check(cn_hi is not None and abs(cn_hi - expect) < 1.0, "CFC: ceiling charges 25%% on the grossed-up 10m less the 165k the subsidiary bore = %.0f (got %s)" % (expect, cn_hi))
    # decision D39: control counts a tier held above 50% as 100% (公告2023年第17号 第二条); the inclusion multiplies the tiers as
    # they are and adds the chains (国税发〔2009〕2号 第八十条)
    from .engine import cfc_flows
    from .params import Params
    ents = lambda: {"ULT": Entity("ULT", CN), "MID": Entity("MID", HK), "SUB": Entity("SUB", SG, attrs={"after_tax_profit": 1000.0})}
    since = date(2020, 1, 1)
    g = Graph(ents(), [HoldEdge("ULT", "MID", 60.0, since, 1.0), HoldEdge("MID", "SUB", 60.0, since, 1.0)],
              [FlowEdge("d", "MID", "ULT", DIVIDEND, 1.0, ON)])
    c = {f.id: f for f in cfc_flows(g, Params(), {}, None)}.get("cfc:SUB>ULT")
    check(c is not None and c.amount == 360.0 and c.attrs["cfc_share_control"],
          "CFC (decision D39): ULT holds 60%% of MID, MID 60%% of SUB — control (the 60%% tier counts as 100%%: 60%% >= 50%%), "
          "included 60%% x 60%% x 1000 = 360, not 600 (got %s)" % (c and c.amount))
    g = Graph(ents(), [HoldEdge("ULT", "SUB", 30.0, since, 1.0), HoldEdge("ULT", "MID", 100.0, since, 1.0),
                       HoldEdge("MID", "SUB", 40.0, since, 1.0)], [FlowEdge("d", "MID", "ULT", DIVIDEND, 1.0, ON)])
    c = {f.id: f for f in cfc_flows(g, Params(), {}, None)}.get("cfc:SUB>ULT")
    check(c is not None and c.amount == 700.0,
          "CFC (decision D39): 30%% directly and 40%% through a wholly held MID — the two chains add up: 70%% x 1000 = 700 (got %s)"
          % (c and c.amount))

    # ---- residence by effective management: a Mainland-controlled HK company managed from the Mainland is a pending group
    g = Graph({"ULT": Entity("ULT", CN), "HOLD": Entity("HOLD", HK, attrs={"managed_from": CN, "residence_cert": True, "bo_safe_harbour": True}),
               "OP": Entity("OP", SG, attrs={"managed_from": SG})},
              [HoldEdge("ULT", "HOLD", 100.0, date(2020, 1, 1), 1.0), HoldEdge("HOLD", "OP", 100.0, date(2020, 1, 1), 1.0)],
              [FlowEdge("d", "OP", "HOLD", DIVIDEND, 1000.0, ON, attrs={"receipt_kind": "REMITTED", "foreign_taxed": True, "foreign_headline_rate": 17})])
    b = bounds(g, lambda facts: CaseCtx(facts, {}, EX_POST))
    check(("cn.residence.pem", "HOLD") in b.groups and b.lo <= b.hi, "residence: the determination is a pending group, floor %.2f <= ceiling %.2f" % (b.lo, b.hi))
    check(b.cost[("cn.residence.pem", "HOLD")] >= 0, "residence: deciding it the other way never lowers the floor (cost %.2f)" % b.cost[("cn.residence.pem", "HOLD")])

    # ---- VAT: a fee for services performed in the Mainland carries 6/106 withheld from the payee and the same input credit for the payer
    g = Graph({"OP": Entity("OP", CN, attrs={"vat_general_taxpayer": True}), "ULT": Entity("ULT", SG, attrs={"managed_from": SG}),
               "S": Entity("S", SG, attrs={"managed_from": SG, "residence_cert": True, "fixed_place_in_cn": False})},
              [HoldEdge("ULT", "OP", 100.0, date(2020, 1, 1), 1.0), HoldEdge("ULT", "S", 100.0, date(2020, 1, 1), 1.0)],
              [FlowEdge("f", "OP", "S", SERVICE_FEE, 1060.0, ON, attrs={"service_location": CN, "service_days_12m": 10, "service_kind": "MANAGEMENT",
                                                                       "profit_margin": 20, "receipt_kind": "REMITTED", "foreign_taxed": True,
                                                                       "foreign_headline_rate": 25, "price_includes_vat": True})])
    lo = run(g, FLOOR)[2]["f"]
    vat = [it for it in lo.items if it.levy == "vat"]
    check(len(vat) == 2 and abs(sum(1060.0 * it.effective / 100.0 for it in vat)) < 1e-6 and any(abs(1060.0 * it.effective / 100.0 - 60.0) < 1e-6 for it in vat),
          "VAT: 1060 x 6/106 = 60 withheld from the payee and credited to the payer (net nil in the group)")

    # ---- an outside bank: its withholding is its own unless the loan grosses it up
    case = Case(roles={OP: RoleFacts(CN), ULT: RoleFacts(SG, {"managed_from": SG}), LENDER: RoleFacts(SG, {"residence_cert": True, "managed_from": SG}, type="BANK_FI")},
                holds={(ULT, OP): HoldEdge(ULT, OP, 100.0, date(2020, 1, 1), 1.0)},
                flows={"int": {"interest_rate": 5.0, "benchmark_rate": 5.0, "price_includes_vat": False}})
    ev = Event(interest=1000.0, on=ON)
    g = FINANCING.build(ev, {LENDER: SG, "payment": False}, case)
    total_lo = run(g, FLOOR, EX_ANTE)[0]
    check(abs(total_lo - (-250.0)) < 1e-6, "financing: the bank's 7%% withholding is outside the group; the group's floor is the 25%% deduction alone (got %.2f)" % total_lo)
    case2 = replace(case, flows={"int": {"interest_rate": 5.0, "benchmark_rate": 5.0, "wht_borne_by_payer": True, "price_includes_vat": False}})
    total_lo2 = run(FINANCING.build(ev, {LENDER: SG, "payment": False}, case2), FLOOR, EX_ANTE)[0]
    check(abs(total_lo2 - (70.0 - 250.0)) < 1e-6, "financing: with a gross-up clause the group bears the 7%% (got %.2f)" % total_lo2)

    # ---- stamp duty: a Hong Kong share sale stamps both contract notes at 0.1%; the outside buyer's note is not the group's
    g = HOLDING.build(replace(EVENT_A, dividend=None, onward=None), {**BASE_A, "exit_route": "INDIRECT"}, CASE_A)
    lo = run(g, FLOOR, EX_ANTE)[2]["exit"]
    stamps = [(it.borne_by, 5000.0 * it.effective / 100.0) for it in lo.items if it.levy == "stamp"]
    check(sorted(stamps) == [("payee", 5.0), ("payer", 5.0)], "stamp: 0.1%% on the seller's and the buyer's notes (got %s)" % stamps)

    # ---- Singapore: the buyer's 0.2% on a share transfer (an outside buyer: its own), GST reverse charge for a partially
    #      exempt payer, the domestic top-up tax at the same shortfall logic
    g = Graph({"S": Entity("S", SG, attrs={"managed_from": SG}), "U": Entity("U", HK, attrs={"managed_from": HK, "residence_cert": True}),
               "B": Entity("B", CN)},
              [HoldEdge("U", "S", 100.0, date(2020, 1, 1), 1000.0)],
              [FlowEdge("x", "B", "U", SHARE_TRANSFER, 5000.0, ON, target="S", attrs={"receipt_kind": "NONE"})])
    lb = run(g, FLOOR)[2]["x"]
    st = [(it.borne_by, round(5000.0 * it.effective / 100.0, 2)) for it in lb.items if it.levy == "stamp"]
    check(st == [("payer", 10.0)], "SG stamp: 0.2%% on the transferee only (got %s)" % st)
    g = Graph({"P": Entity("P", SG, attrs={"managed_from": SG, "gst_input_fully_recoverable": False}),
               "U": Entity("U", SG, attrs={"managed_from": SG}), "V": Entity("V", HK, attrs={"managed_from": HK, "residence_cert": True, "fixed_place_in_sg": False})},
              [HoldEdge("U", "P", 100.0, date(2020, 1, 1), 1.0), HoldEdge("U", "V", 100.0, date(2020, 1, 1), 1.0)],
              [FlowEdge("f", "P", "V", SERVICE_FEE, 1000.0, ON, attrs={"service_location": HK, "service_days_12m": 0, "profit_margin": 20})])
    hi = run(g, CEILING)[2]["f"]
    gst = [round(1000.0 * it.effective / 100.0, 2) for it in hi.items if it.levy == "vat" and it.borne_by == "payer"]
    check(gst == [90.0], "SG GST: a partially exempt payer with an unknown recovery ratio: 9%% at the ceiling, nil at the floor (got %s)" % gst)
    g = Graph({"E": Entity("E", SG, attrs={**NO_RELIEF, "globe_income": 1000.0, "covered_taxes_other": 100.0, "group_revenue_eur": 1e9, "sbie": 0.0, "managed_from": SG}),
               "U": Entity("U", HK, attrs={"managed_from": HK})},
              [HoldEdge("U", "E", 100.0, date(2020, 1, 1), 100.0)],
              [FlowEdge("d", "E", "U", DIVIDEND, 100.0, ON, attrs={"receipt_kind": "NONE"})])
    lo = run(g, FLOOR)[2]
    check("p2:E" in lo and abs(lo["p2:E"].tax - 50.0) < 1e-6, "SG Pillar Two: (15%% - 10%%) x 1000 = 50 domestic top-up (got %s)" % lo.get("p2:E", type("x", (), {"tax": None})).tax)

    # ---- Pillar Two by jurisdiction (decision D14): the constituent entities located in Hong Kong are blended (GloBE Art 5.1.1,
    #      5.2.3) and the top-up shared by GloBE income (Art 5.2.4; MMT Act s16(2) A x B / C)
    def p2_graph(loc, rows, **extra):
        ents = {k: Entity(k, loc, attrs=dict({**NO_RELIEF, "group_revenue_eur": 1e9, "sbie": 0.0, "managed_from": loc}, globe_income=inc,
                                             **({"covered_taxes_other": tax} if tax is not None else {}), **extra))
                for k, inc, tax in rows}
        ents["U"] = Entity("U", CN)
        return Graph(ents, [HoldEdge("U", k, 100.0, date(2020, 1, 1), 100.0) for k, _, _ in rows],
                     [FlowEdge("d", rows[0][0], "U", DIVIDEND, 100.0, ON, attrs={"receipt_kind": "NONE"})])

    def tax_of(labels, fid):
        return labels[fid].tax if fid in labels else None

    lo = run(p2_graph(HK, [("E1", 1000.0, 50.0), ("E2", 1000.0, 250.0)]), FLOOR)[2]
    check(tax_of(lo, "p2:E1") == 0.0 and tax_of(lo, "p2:E2") == 0.0,
          "P2 blending: ETRs 5%% and 25%% blend to 15%%: no top-up in the jurisdiction (got %s, %s)" % (tax_of(lo, "p2:E1"), tax_of(lo, "p2:E2")))
    lo = run(p2_graph(HK, [("E1", 3000.0, 0.0), ("E2", 1000.0, 0.0)]), FLOOR)[2]
    check(tax_of(lo, "p2:E1") == 450.0 and tax_of(lo, "p2:E2") == 150.0,
          "P2 allocation: 15%% x 4000 = 600 shared 3:1 by GloBE income = 450 / 150 (got %s, %s)" % (tax_of(lo, "p2:E1"), tax_of(lo, "p2:E2")))
    lo = run(p2_graph(SG, [("E1", 1000.0, 100.0), ("E2", -400.0, 0.0)]), FLOOR)[2]
    check(tax_of(lo, "p2:E1") == 0.0 and "p2:E2" not in lo,
          "P2 blending: a loss-making entity lowers the net GloBE income: 100 / 600 = 16.7%%, no top-up (got %s)" % tax_of(lo, "p2:E1"))

    # ---- additional current top-up (decision D15): no net GloBE income, covered taxes below 15% of the net loss
    lo = run(p2_graph(SG, [("E", -1000.0, -300.0)], p2_negative_tax_election=False), FLOOR)[2]
    check(tax_of(lo, "p2:E") == 150.0, "SG s21(1): 15%% x -1000 - (-300) = 150, all on the entity (s16(3)(a)) (got %s)" % tax_of(lo, "p2:E"))
    lo = run(p2_graph(SG, [("E", -1000.0, -300.0)], p2_negative_tax_election=True, p2_carry_back_topup=40.0), FLOOR)[2]
    check(tax_of(lo, "p2:E") == 40.0, "SG s21(2) election: only the part attributable to the carry back of losses stays (got %s)" % tax_of(lo, "p2:E"))
    g = p2_graph(SG, [("E", -1000.0, -300.0)])
    _, grp_lo, lo = run(g, FLOOR, EX_ANTE)
    hi = run(g, CEILING, EX_ANTE)[2]
    check(("data.p2_negative_tax_election", "SG") in grp_lo and tax_of(lo, "p2:E") is None and tax_of(hi, "p2:E") == 150.0,
          "SG s21(2) unstated ex ante: the election is a plan action; electing with the attribution unknown: nil .. 150 (got %s .. %s)"
          % (tax_of(lo, "p2:E"), tax_of(hi, "p2:E")))
    lo = run(p2_graph(HK, [("E1", 200.0, -100.0), ("E2", -1000.0, -50.0)]), FLOOR)[2]
    check(tax_of(lo, "p2:E1") == 30.0 and "p2:E2" not in lo,
          "HK Art 4.1.5 / 5.4.3: 15%% x -800 - (-150) = 30, all on the entity whose covered taxes fall below its own 15%% (got %s)" % tax_of(lo, "p2:E1"))
    grp = run(p2_graph(HK, [("E", -100.0, None)]), FLOOR)[1]
    check(("data.p2_taxes", "HK") in grp, "P2: a jurisdiction without net GloBE income asks for unknown covered taxes (they may be negative without limit)")

    # ---- decision D16: one top-up per financial year; a company the plan creates has exactly its modelled flows; the tax on
    #      excluded dividends is no covered tax (GloBE Art 3.2.1(b), 4.1.3(a); MMT Act s2, reg 38(2)(a))
    g = p2_graph(HK, [("E1", 1000.0, 0.0)])
    g = Graph(g.entities, g.holds, g.flows + [FlowEdge("d@2027", "E1", "U", DIVIDEND, 100.0, date(2027, 3, 31), attrs={"receipt_kind": "NONE"})])
    lo = run(g, FLOOR)[2]
    check(tax_of(lo, "p2:E1") == 150.0 and tax_of(lo, "p2:E1@2027") == 150.0,
          "P2 per year: the 2026 and the 2027 top-up, 150 each (got %s, %s)" % (tax_of(lo, "p2:E1"), tax_of(lo, "p2:E1@2027")))
    ents = {"ULT": Entity("ULT", HK, attrs={**NO_RELIEF, "group_revenue_eur": 1e9, "sbie": 0.0, "managed_from": HK, "globe_income": 1000.0,
                                            "covered_taxes_other": 0.0}),
            "HOLD": Entity("HOLD", HK, attrs={"created_by_plan": True, "placed_by_plan": True, "managed_from": HK}),
            "OP": Entity("OP", CN)}
    g = Graph(ents, [HoldEdge("ULT", "HOLD", 100.0, None, None, designed=True), HoldEdge("HOLD", "OP", 100.0, date(2020, 1, 1), 100.0)],
              [FlowEdge("d", "OP", "HOLD", DIVIDEND, 1000.0, ON, attrs={"receipt_kind": "NONE", "listed_market_trade": False})])
    _, grp, lo = run(g, FLOOR)
    check(tax_of(lo, "p2:ULT") == 150.0 and "p2:HOLD" not in lo and ("data.p2_income", "HOLD") not in grp,
          "P2: a created holding company's GloBE income comes from its flows (the dividend excluded): 15%% x 1000 on ULT (got %s)" % tax_of(lo, "p2:ULT"))
    ents["E"] = Entity("E", HK, attrs={**NO_RELIEF, "group_revenue_eur": 1e9, "sbie": 0.0, "managed_from": HK, "globe_income": 1000.0,
                                       "covered_taxes_other": 0.0, "residence_cert": True})
    g = Graph({"E": ents["E"], "OP": ents["OP"]}, [HoldEdge("E", "OP", 100.0, date(2020, 1, 1), 100.0)],
              [FlowEdge("d", "OP", "E", DIVIDEND, 1000.0, ON, attrs={"receipt_kind": "NONE", "listed_market_trade": False})])
    lo, hi = run(g, FLOOR)[2], run(g, CEILING)[2]
    wht = sum(1000.0 * it.effective / 100.0 for it in lo["d"].items if it.jur == "CN" and it.levy == "income")
    check(wht > 0 and tax_of(lo, "p2:E") == 150.0 and tax_of(hi, "p2:E") == 150.0,
          "P2: the Mainland tax withheld on an excluded dividend (%.0f) is no covered tax: the top-up stays 150 (got %s .. %s)"
          % (wht, tax_of(lo, "p2:E"), tax_of(hi, "p2:E")))

    # ---- decision D17: transitional CbCR safe harbour (SG regs 69-74; HK Sch 61 Pt 3 Div 2) and de minimis (s19; Art 5.5)
    cbcr = {"p2_qualified_cbcr_sg": True, "p2_tcsh_history_sg": True, "p2_cbcr_revenue_sg": 500000000.0, "p2_cbcr_pbt_sg": 1000.0,
            "p2_cbcr_simplified_taxes_sg": 0.0, "p2_eur_rate": 0.125, "p2_dm_avg_revenue_eur_sg": 62500000.0, "p2_dm_avg_income_eur_sg": 6250000.0}
    lo = run(p2_graph(SG, [("E", 1000.0, 0.0)], **dict(cbcr, p2_tcsh_elected_sg=False)), FLOOR)[2]
    check(tax_of(lo, "p2:E") == 150.0, "TCSH: no test met (CbC profit 1000 above the nil carve-out, ETR 0%%): top-up 150 (got %s)" % tax_of(lo, "p2:E"))
    lo = run(p2_graph(SG, [("E", 1000.0, 0.0)], **dict(cbcr, p2_cbcr_pbt_sg=-5.0, p2_tcsh_elected_sg=True)), FLOOR)[2]
    check("p2:E" not in lo, "TCSH: a CbC loss meets the routine profits test (reg 73(1)(b)); elected: SG top-up nil")
    lo = run(p2_graph(SG, [("E", 1000.0, 0.0)], **dict(cbcr, p2_cbcr_simplified_taxes_sg=170.0, p2_tcsh_elected_sg=True)), FLOOR)[2]
    check("p2:E" not in lo, "TCSH: simplified ETR 170 / 1000 = 17% meets the 2026 test (reg 72(1)(b)): top-up nil")
    lo = run(p2_graph(SG, [("E", 1000.0, 0.0)], **dict(cbcr, p2_cbcr_simplified_taxes_sg=160.0, p2_tcsh_elected_sg=True)), FLOOR)[2]
    check(tax_of(lo, "p2:E") == 150.0, "TCSH: 16%% is below the 2026 test of 17%%: top-up 150 (got %s)" % tax_of(lo, "p2:E"))
    _, grp, lo = run(p2_graph(SG, [("E", 1000.0, 0.0)], p2_tcsh_elected_sg=True, p2_qualified_cbcr_sg=None), FLOOR)
    hi = run(p2_graph(SG, [("E", 1000.0, 0.0)], p2_tcsh_elected_sg=True, p2_qualified_cbcr_sg=None), CEILING)[2]
    check(("data.p2_tcsh", "SG") in grp and "p2:E" not in lo and tax_of(hi, "p2:E") == 150.0,
          "TCSH: CbC data unknown: pending, nil at the floor, 150 at the ceiling (got %s)" % tax_of(hi, "p2:E"))
    g = p2_graph(SG, [("E", 1000.0, 0.0)], **dict(cbcr, p2_cbcr_pbt_sg=-5.0, p2_tcsh_elected_sg=True))
    g = Graph(g.entities, g.holds, [replace(f, on=date(2027, 3, 31)) for f in g.flows])
    lo = run(g, FLOOR)[2]
    check(tax_of(lo, "p2:E") == 150.0, "TCSH: a financial year beginning in 2027 is outside the transition period: top-up 150 (got %s)" % tax_of(lo, "p2:E"))
    _, grp, lo = run(p2_graph(SG, [("E", 1000.0, 0.0)], **dict(cbcr, p2_cbcr_pbt_sg=-5.0)), FLOOR, EX_ANTE)
    check(("data.p2_tcsh_elected_sg", "SG") in grp and "p2:E" not in lo,
          "TCSH: eligible ex ante, the election is the plan's action (pending; nil at the floor)")
    lo = run(p2_graph(HK, [("E", 1000.0, 0.0)], p2_dm_avg_revenue_eur_hk=5000000.0, p2_dm_avg_income_eur_hk=500000.0,
                      p2_dm_elected_hk=True, p2_qualified_cbcr_hk=False), FLOOR)[2]
    check("p2:E" not in lo, "HK de minimis (Art 5.5.1): averages EUR 5m revenue and EUR 0.5m income, elected: top-up nil")
    lo = run(p2_graph(HK, [("E", 1000.0, 0.0)], p2_dm_avg_revenue_eur_hk=5000000.0, p2_dm_avg_income_eur_hk=1000000.0,
                      p2_dm_elected_hk=True, p2_qualified_cbcr_hk=False), FLOOR)[2]
    check(tax_of(lo, "p2:E") == 150.0, "HK de minimis: an average income of EUR 1m is not below EUR 1m: top-up 150 (got %s)" % tax_of(lo, "p2:E"))

    # ---- decision D18: the restructuring step — ULT transfers OP to the new HOLD (财税〔2009〕59号 §5, §7(1); 109号; 公告2013年第72号)
    def reorg_case(op_loc, ult_loc, value=4000.0, reorg_facts=None, up1=None):
        flows = {"up1": dict({"receipt_kind": "NONE"}, **(up1 or {})), "up2": {"receipt_kind": "NONE"}, "exit": {"receipt_kind": "NONE"}}
        flows["reorg"] = dict({"amount": value} if value is not None else {}, **(reorg_facts or {}))
        return Case(roles={OP: RoleFacts(op_loc, {"managed_from": op_loc}), ULT: RoleFacts(ult_loc, {"managed_from": ult_loc, "residence_cert": True}),
                           BUYER: RoleFacts(CN if op_loc != CN else HK, {"managed_from": CN if op_loc != CN else HK})},
                    holds={(ULT, OP): HoldEdge(ULT, OP, 100.0, date(2020, 1, 1), 3000.0)}, flows=flows)

    ev = Event(dividend=1000.0, onward=900.0, exit=5000.0, exit_on=date(2026, 12, 31), on=ON)
    g = HOLDING.build(ev, {HOLD: SG, "financing": "EQUITY", "payment": False, "exit_route": "DIRECT"}, reorg_case(CN, HK))
    step = next((f for f in g.flows if f.id == "reorg"), None)
    check(step is not None and (step.payer, step.payee, step.target, step.amount) == (HOLD, ULT, OP, 4000.0),
          "restructuring: a new HOLD between ULT and OP makes ULT transfer OP to HOLD at the stated consideration")
    lo, hi = run(g, FLOOR, EX_ANTE)[2], run(g, CEILING, EX_ANTE)[2]
    cn = lambda lb: round(sum(4000.0 * it.effective / 100.0 for it in lb.items if it.jur == CN and it.levy == "income" and not it.deferred), 2)
    check(cn(hi["reorg"]) == 100.0 and cn(lo["reorg"]) == 0.0,
          "restructuring: 10%% on the 1000 gain in general, deferred as a special reorganisation (59号 §7(1)) (got %s .. %s)" % (cn(lo["reorg"]), cn(hi["reorg"])))
    met = {"reorg_equity_payment_share": 100.0, "reorg_operations_unchanged_12m": True, "reorg_shares_kept_12m": True,
           "reorg_commitment_3y": True, "reorg_filed": True}
    g = HOLDING.build(ev, {HOLD: HK, "financing": "EQUITY", "payment": False, "exit_route": "DIRECT"}, reorg_case(CN, HK, reorg_facts=met))
    t = {Need(DISCRETION, "payee.reorg_reasonable_commercial_purpose"): True}
    lb = engine(g, lambda facts: CaseCtx(facts, t, EX_POST, ADJUSTABLE), CEILING)[2]
    exit_cn = round(sum(5000.0 * it.effective / 100.0 for it in lb["exit"].items if it.jur == CN and it.levy == "income"), 2)
    check(all(it.deferred for it in lb["reorg"].items if it.jur == CN and it.levy == "income") and exit_cn == 200.0,
          "restructuring: special treatment met — the step deferred, HOLD keeps ULT's basis 3000: 10%% x 2000 on the exit (got %s)" % exit_cn)
    g = HOLDING.build(ev, {HOLD: HK, "financing": "EQUITY", "payment": False, "exit_route": "DIRECT"}, reorg_case(CN, HK, value=None))
    grp = run(g, FLOOR, EX_ANTE)[1]
    check(("data.amount", "reorg") in grp, "restructuring: the consideration unknown: asked (the step's tax is unbounded without it)")
    g = HOLDING.build(ev, {HOLD: CN, "financing": "EQUITY", "payment": False, "exit_route": "DIRECT"}, reorg_case(HK, SG))
    lo, hi = run(g, FLOOR, EX_ANTE)[2], run(g, CEILING, EX_ANTE)[2]
    stamp = lambda lb: round(sum(4000.0 * it.effective / 100.0 for it in lb.items if it.jur == HK and it.levy == "stamp"), 2)
    check(stamp(lo["reorg"]) == 0.0 and stamp(hi["reorg"]) == 8.0,
          "restructuring: HK stock to an associated body (SDO s45, 90%%): no duty when claimed, 0.1%% x 2 otherwise (got %s .. %s)" % (stamp(lo["reorg"]), stamp(hi["reorg"])))
    g = HOLDING.build(ev, {HOLD: SG, "financing": "EQUITY", "payment": False, "exit_route": "DIRECT"},
                      reorg_case(CN, HK, reorg_facts=met, up1={"dividend_from_pre_reorg_profits": True}))
    t = {Need(DISCRETION, "payee.reorg_reasonable_commercial_purpose"): True, Need(DISCRETION, "payee.reorg_wht_burden_unchanged"): True}
    lb = engine(g, lambda facts: CaseCtx(facts, t, EX_POST, ADJUSTABLE), FLOOR)[2]
    up1_cn = round(sum(1000.0 * it.effective / 100.0 for it in lb["up1"].items if it.jur == CN and it.levy == "income"), 2)
    check(up1_cn == 100.0, "restructuring: special treatment across HK / SG, a dividend of pre-transfer profits: no treaty rate (公告2013年第72号 §8): 10%% (got %s)" % up1_cn)
    # decision D35: §7(2) — the non-resident ULT transfers OP to the Mainland HOLD it holds wholly
    g = HOLDING.build(ev, {HOLD: CN, "financing": "EQUITY", "payment": False, "exit_route": "DIRECT"}, reorg_case(CN, SG, reorg_facts=met))
    lo, hi = run(g, FLOOR, EX_ANTE)[2], run(g, CEILING, EX_ANTE)[2]
    asked = run(g, CEILING, EX_ANTE)[1]
    lb = engine(g, lambda facts: CaseCtx(facts, {Need(DISCRETION, "payee.reorg_reasonable_commercial_purpose"): True}, EX_POST, ADJUSTABLE), CEILING)[2]
    exit_cn = round(sum(5000.0 * it.effective / 100.0 for it in lb["exit"].items if it.jur == CN and it.levy == "income"), 2)
    check(cn(hi["reorg"]) == 100.0 and cn(lo["reorg"]) == 0.0 and exit_cn == 500.0
          and all(it.deferred for it in lb["reorg"].items if it.jur == CN and it.levy == "income")
          and not any("pre_reorg" in str(k) or "wht_burden" in str(k) or "commitment_3y" in str(k) for k in asked),
          "restructuring to a Mainland HOLD (59号 §7(2)): 10%% on the 1000 gain in general, deferred when met; the resident HOLD "
          "keeps the basis 3000: 25%% x 2000 on the exit; no §7(1) test is asked (got %s .. %s, exit %s)" % (cn(lo["reorg"]), cn(hi["reorg"]), exit_cn))

    # ---- decision D38: equity passing between related parties below its arm's-length value — taxed in the Mainland on that value
    #      (EIT art 41; 实施条例 第一百一十一条; 公告2017年第6号 第十七、二十二条)
    def alv_graph(seller_loc, price, **flow):
        ents = {"ULT": Entity("ULT", seller_loc, attrs={"managed_from": seller_loc, "residence_cert": True}),
                "OP": Entity("OP", CN, attrs={"managed_from": CN}), "B": Entity("B", CN, attrs={"managed_from": CN})}
        return Graph(ents, [HoldEdge("ULT", "OP", 100.0, date(2020, 1, 1), 300.0)],
                     [FlowEdge("exit", "B", "ULT", SHARE_TRANSFER, price, ON, target="OP",
                               attrs=dict({"receipt_kind": "NONE", "listed_market_trade": False}, **flow))])
    cn_inc = lambda lb: round(sum(lb.flow.amount * it.effective / 100.0 for it in lb.items
                                  if it.jur == CN and it.levy == "income" and not it.deferred), 2)
    cn_stamp = lambda lb: round(sum(lb.flow.amount * it.effective / 100.0 for it in lb.items if it.jur == CN and it.levy == "stamp"), 2)
    hi = run(alv_graph(HK, 100.0, parties_related=True, arms_length_value=1000.0), CEILING)[2]
    check(cn_inc(hi["exit"]) == 70.0 and cn_stamp(hi["exit"]) == 0.1,
          "arm's length (decision D38): HK seller to a related buyer at 100, worth 1000, basis 300 — 10%% x 700 = 70; stamp duty "
          "on the price paid, 0.05%% x 100 (got %s, stamp %s)" % (cn_inc(hi["exit"]), cn_stamp(hi["exit"])))
    hi = run(alv_graph(HK, 100.0, parties_related=False, arms_length_value=1000.0), CEILING)[2]
    check(cn_inc(hi["exit"]) == 0.0, "arm's length: an unrelated buyer's price stands — 100 below the basis 300, no gain (got %s)" % cn_inc(hi["exit"]))
    hi = run(alv_graph(HK, 0.0, parties_related=True, arms_length_value=1000.0), CEILING)[2]
    check("exit.alv" in hi and cn_inc(hi["exit.alv"]) == 70.0 and cn_stamp(hi["exit.alv"]) == 0.0
          and all(it.jur == CN for it in hi["exit.alv"].items) and cn_inc(hi["exit"]) == 0.0,
          "arm's length: a nil price — the transfer at 1000 as exit.alv, Mainland income tax only: 10%% x 700 = 70 (got %s)"
          % (cn_inc(hi["exit.alv"]) if "exit.alv" in hi else None))
    grp = run(alv_graph(HK, 100.0, parties_related=True), CEILING)[1]
    check(("data.arms_length_value", "exit") in grp,
          "arm's length: a related buyer's price without the arm's-length value — asked (the Mainland tax is unbounded without it)")
    hi = run(alv_graph(CN, 100.0, parties_related=True, arms_length_value=1000.0), CEILING)[2]
    check(cn_inc(hi["exit"]) == 175.0, "arm's length: a Mainland seller — 25%% x (1000 - 300) = 175 (got %s)" % cn_inc(hi["exit"]))

    # ---- decision D40: related under each jurisdiction's own test
    from .facts import relatedness
    from .params import Params
    P0 = Params()

    def rel(*holds):
        g = Graph({k: Entity(k, CN) for k in ("A", "B", "M", "C")}, [HoldEdge(h, d, r, date(2020, 1, 1), 1.0) for h, d, r in holds], [])
        return relatedness(g, "A", "B", P0)
    r = rel(("A", "B", 30.0))
    check(r == {CN: True, HK: None, SG: None}, "related (decision D40): A holds 30%% of B — the Mainland's 25%% test is met; Hong Kong "
          "and Singapore control is open (got %s)" % r)
    r = rel(("A", "B", 20.0))
    check(r == {CN: None, HK: None, SG: None}, "related: 20%% — below every holding test, the law's other ties open (got %s)" % r)
    r = rel(("A", "M", 30.0), ("M", "B", 40.0))
    check(r[CN] is True, "related: A 30%% of M, M 40%% of B — through an intermediate held at 25%%, M's own 40%% counts "
          "(公告2016年第42号 第二条) (got %s)" % r)
    r = rel(("A", "M", 60.0), ("M", "B", 60.0))
    check(r[HK] is True and r[SG] is None, "related: A 60%% of M, M 60%% of B — Hong Kong control through the votes of a "
          "controlled company (s50AAH(2)(a)(ii)); Singapore's undefined control open (got %s)" % r)
    r = rel(("C", "A", 100.0), ("C", "B", 100.0))
    check(r == {CN: True, HK: True, SG: True}, "related: sisters wholly held by C — related everywhere (got %s)" % r)
    r = rel(("A", "M", 100.0))
    check(r == {CN: False, HK: False, SG: False}, "related: no holding between them — not related unless the case says so (got %s)" % r)

    # ---- decision D41: a related payer's fee below its arm's-length amount — the payee's jurisdiction taxes that amount; the
    #      payer's deduction follows through the treaty's corresponding adjustment (a judgement)
    def tp_graph(payer_loc, payee_loc, income, amount, ratio=100.0, **flow):
        ents = {"PAY": Entity("PAY", payer_loc, attrs={"managed_from": payer_loc, "gst_input_fully_recoverable": True}),
                "REC": Entity("REC", payee_loc, attrs={"managed_from": payee_loc, "residence_cert": True, "fixed_place_in_sg": False,
                                                       "fixed_place_in_cn": False, "fixed_place_in_hk": False})}
        return Graph(ents, [HoldEdge("REC", "PAY", ratio, date(2020, 1, 1), 1.0)],
                     [FlowEdge("fee", "PAY", "REC", income, amount, ON,
                               attrs=dict({"service_location": payee_loc, "receipt_kind": "NONE"}, **flow))])
    inc = lambda lb, j, ded=False: round(sum(lb.flow.amount * it.effective / 100.0 for it in lb.items
                                             if it.jur == j and it.levy == "income" and it.deduction == ded), 2)
    g = tp_graph(SG, CN, SERVICE_FEE, 100.0, arms_length_value=150.0)
    lo, hi = run(g, FLOOR)[2]["fee"], run(g, CEILING)[2]["fee"]
    check(inc(lo, CN) == 37.5 == inc(hi, CN), "arm's length (decision D41): a Singapore subsidiary pays its Mainland parent 100 for "
          "services worth 150 — the Mainland taxes 25%% x 150 = 37.5 (got %s, %s)" % (inc(lo, CN), inc(hi, CN)))
    check(inc(lo, SG, True) == -25.5 and inc(hi, SG, True) in (0.0, -17.0),
          "arm's length: the Singapore payer deducts 150 at the floor (17%% x 150: Art 9(2) granted), no more than the 100 it "
          "paid at the ceiling (got %s, %s)" % (inc(lo, SG, True), inc(hi, SG, True)))
    g = tp_graph(SG, CN, SERVICE_FEE, 100.0)
    check(inc(run(g, CEILING)[2]["fee"], CN) == 25.0, "arm's length: no arm's-length amount stated — the price stands, 25% x 100")
    g = tp_graph(SG, CN, SERVICE_FEE, 100.0, ratio=20.0, arms_length_value=150.0)
    res = run(g, CEILING)
    lo = run(g, FLOOR)[2]["fee"]
    check(inc(lo, CN) == 25.0 and inc(res[2]["fee"], CN) == 37.5
          and any(n.key.endswith("parties_related") for ns in res[1].values() for n in ns),
          "arm's length: a 20%% parent — related open under the Mainland's test: the price at the floor, 150 at the ceiling, "
          "parties_related asked (got %s, %s)" % (inc(lo, CN), inc(res[2]["fee"], CN)))
    ups = lambda lb, j: sorted({round(it.uplift, 4) for it in lb.items if it.jur == j and it.levy == "income" and not it.deduction})
    g = tp_graph(CN, SG, ROYALTY, 100.0, arms_length_value=150.0, arms_length_low=90.0, receipt_kind="REMITTED")
    check(ups(run(g, CEILING)[2]["fee"], SG) == [1.0], "arm's length: a royalty inside the range (90 to the median 150) — "
          "Singapore leaves it (IRAS TP Guidelines 5.115)")
    g = tp_graph(CN, SG, ROYALTY, 100.0, arms_length_value=150.0, arms_length_low=120.0, receipt_kind="REMITTED")
    hi = run(g, CEILING)[2]["fee"]
    from .rules.eval import Chooser
    from .rules.procedure_sg import s10l_gain_share, sg_tp_income_surcharge
    sur = sg_tp_income_surcharge(None, {("flow", "arms_length_value"): 150.0, ("flow", "amount"): 100.0,
                                        ("flow", "arms_length_low"): 120.0, ("flow", "sg_related"): True}, P0, {}, None)
    check(ups(hi, SG) == [1.5] and "sg.tp.income_surcharge" in hi.applied and sur == 2.5,
          "arm's length: below the range — Singapore taxes 150 (s34D(1A)(a)) with the 5%% surcharge on the 50 increase "
          "(s34E) (got %s, %s)" % (ups(hi, SG), sur))
    f10 = {("flow", "consideration"): 250000.0, ("flow", "cost_basis"): 220000.0, ("flow", "arms_length_value"): 600000.0}
    a, b = s10l_gain_share(f10, P0, Chooser("x", "f", FLOOR, {})), s10l_gain_share(f10, P0, Chooser("x", "f", CEILING, {}))
    check(abs(a - 0.12) < 1e-9 and abs(b - 1.52) < 1e-9, "s10L(10) (decision D41): sold for 250,000, open-market price 600,000, "
          "basis 220,000 — the Comptroller may count (600,000 - 220,000) over the price: 0.12 or 1.52 (got %s, %s)" % (a, b))

    # ---- decision D42: a sale of goods — OP (Mainland, cost 600) sells to an outside CUSTOMER for 1000, directly or through a
    #      group TRADER that buys at 800 (arm's length 900) and spends 50 of its own
    from .scenarios import CUSTOMER, TRADER, TRADING
    nofix = {"fixed_place_in_cn": False, "fixed_place_in_hk": False, "fixed_place_in_sg": False}

    def trade_case(tr, cust, **resale):
        roles = {OP: RoleFacts(CN, dict(nofix, managed_from=CN)), ULT: RoleFacts(CN, {"managed_from": CN}),
                 CUSTOMER: RoleFacts(cust, {"managed_from": cust})}
        holds = {(ULT, OP): HoldEdge(ULT, OP, 100.0, date(2020, 1, 1), 1.0)}
        if tr:
            roles[TRADER] = RoleFacts(tr, dict(nofix, managed_from=tr, residence_cert=True))
            holds[(ULT, TRADER)] = HoldEdge(ULT, TRADER, 100.0, date(2020, 1, 1), 1.0)
        flows = {"supply": {"cost_basis": 600.0, "arms_length_value": 900.0}, "sale": {"cost_basis": 600.0},
                 "resale": dict({"operating_costs": 50.0, "receipt_kind": "NONE"}, **resale)}
        return Case(roles, holds, flows, present={TRADER: tr, "payment": False})
    tev = Event(goods_sale=1000.0, goods_supply=800.0, on=ON)
    tax_of = lambda labs, j: round(sum(lb.flow.amount * it.effective / 100.0 for lb in labs.values() for it in lb.items
                                       if it.jur == j and it.levy == "income"), 2)

    def trade(tr, cust, place=None, **resale):
        g = TRADING.build(tev, {TRADER: place if place else tr, "payment": False}, trade_case(tr, cust, **resale))
        return [run(g, b) for b in (FLOOR, CEILING)]
    lo, hi = (r[2] for r in trade(None, SG))
    check(tax_of(lo, CN) == tax_of(hi, CN) == 100.0, "goods (decision D42): OP sells to the customer directly — the Mainland taxes "
          "25%% x (1000 - 600) = 100 (got %s, %s)" % (tax_of(lo, CN), tax_of(hi, CN)))
    lo, hi = (r[2] for r in trade(HK, SG, purchase_effected_in_hk=False, sale_effected_in_hk=False))
    check(tax_of(lo, CN) == tax_of(hi, CN) == 75.0 and tax_of(lo, HK) == tax_of(hi, HK) == 0.0,
          "goods: through a Hong Kong trader buying at 800 (arm's length 900) — the Mainland taxes 25%% x (900 - 600) = 75; "
          "both contracts effected outside Hong Kong: no Hong Kong tax (DIPN 21 ¶23(b)) (got %s, %s; %s, %s)"
          % (tax_of(lo, CN), tax_of(hi, CN), tax_of(lo, HK), tax_of(hi, HK)))
    lo, hi = (r[2] for r in trade(HK, SG, purchase_effected_in_hk=True, sale_effected_in_hk=True))
    check(tax_of(lo, HK) == 8.25 and tax_of(hi, HK) == 24.75,
          "goods: both contracts effected in Hong Kong — 16.5%% x (1000 - 900 - 50) = 8.25 with the corresponding adjustment "
          "(Arrangement Art 9(2), granted at the floor), 16.5%% x (1000 - 800 - 50) = 24.75 without (got %s, %s)"
          % (tax_of(lo, HK), tax_of(hi, HK)))
    lo, hi = (r[2] for r in trade(SG, HK))
    check(tax_of(lo, SG) == 0.0 and tax_of(hi, SG) == 25.5 and tax_of(lo, HK) == tax_of(hi, HK) == 0.0,
          "goods: a Singapore trader selling to a Hong Kong customer — where its trade is carried on is a judgement: none or "
          "17%% x 150 = 25.5; Hong Kong taxes no seller without a fixed place there (got %s, %s)" % (tax_of(lo, SG), tax_of(hi, SG)))
    lo, hi = trade(None, SG, place=HK)
    check(tax_of(lo[2], CN) == tax_of(hi[2], CN) == 75.0 and any(n.key.endswith("operating_costs") for ns in hi[1].values() for n in ns),
          "goods: a Hong Kong trader the plan creates buys at the arm's-length 900 — the Mainland taxes 75; its own costs "
          "are asked (got %s)" % tax_of(hi[2], CN))
    # ---- decision D44: Hong Kong intra-group transfer relief (s15OA–s15OC). S held 30% of the Mainland F since 2023-04-01 at
    #      100; sells it to its sister A for 110 on 2024-01-01 (relief), A sells it to an outside buyer for 108 on 2024-06-01
    from .facts import facts_for as _ff

    def hk_ig(sister_ratio=100.0):
        hk = {"managed_from": HK, "residence_cert": True, "fixed_place_in_cn": False, "bo_safe_harbour": True}
        ents = {"U": Entity("U", HK, attrs=dict(hk)), "S": Entity("S", HK, attrs=dict(hk)), "A": Entity("A", HK, attrs=dict(hk)),
                "F": Entity("F", CN, attrs={"managed_from": CN}), "X": Entity("X", SG, attrs={"managed_from": SG})}
        gain = {"receipt_kind": "REMITTED", "foreign_headline_rate": 25, "deductible_at_payer": False, "listed_market_trade": False,
                "immovable_ratio": 0, "acquirer_chargeable_in_hk": True, "underlying_profits_taxed": False}
        return Graph(ents, [HoldEdge("U", "S", 100.0, date(2020, 1, 1), 1.0), HoldEdge("U", "A", sister_ratio, date(2020, 1, 1), 1.0),
                            HoldEdge("S", "F", 30.0, date(2023, 4, 1), 100.0), HoldEdge("A", "F", 30.0, date(2024, 1, 1), 110.0)],
                     [FlowEdge("r", "A", "S", SHARE_TRANSFER, 110.0, date(2024, 1, 1), target="F", attrs=dict(gain, clawback_event_within_2y=False)),
                      FlowEdge("g", "X", "A", SHARE_TRANSFER, 108.0, date(2024, 6, 1), target="F", attrs=dict(gain))])
    g = hk_ig()
    check(_ff(g, g.flows[0])[("flow", "intragroup_transfer")] and not _ff(hk_ig(70.0), hk_ig(70.0).flows[0])[("flow", "intragroup_transfer")],
          "intra-group (decision D44): sisters wholly held are associated; one held 70% is not (s15OC: 75% of the beneficial interest)")
    lo, hi = run(g, FLOOR)[2], run(g, CEILING)[2]
    hk_ = lambda lb: round(sum(lb.flow.amount * it.effective / 100.0 for it in lb.items if it.jur == HK and it.levy == "income"), 2)
    cn_r = round(sum(110.0 * it.effective / 100.0 for it in hi["r"].items if it.jur == CN and it.levy == "income"), 2)
    check(hk_(lo["r"]) == hk_(hi["r"]) == 0.0 and "hk.fsie.intragroup_relief" in hi["r"].applied,
          "intra-group: S's gain of 10 relieved — no gain, no loss (s15OA(3)) (got %s)" % hk_(hi["r"]))
    check(hk_(lo["g"]) == 0.0 and abs(hk_(hi["g"]) - round(16.5 * 8 / 100.0 - cn_r, 2)) < 0.011,
          "intra-group: A sells at 108 — for the FSIE regime it bought at S's 100 on S's date (s15OA(5)): gain 8, held 14 months, "
          "the participation exemption at the floor (Example 38: S's Mainland tax %.2f meets the subject-to-tax test); at the "
          "ceiling 16.5%% x 8 less that tax as credited (s15OA(8)) (got %s, %s)" % (cn_r, hk_(lo["g"]), hk_(hi["g"])))

    # ---- decision D45: Singapore s13W(1B) from 2026 — S sells its 10% of T; its parent U held another 15% since 2020
    def sg_grp(u_since):
        sg = {"managed_from": SG, "residence_cert": True}
        ents = {"U": Entity("U", SG, attrs=dict(sg)), "S": Entity("S", SG, attrs=dict(sg)), "T": Entity("T", SG, attrs=dict(sg)),
                "X": Entity("X", HK, attrs={"managed_from": HK})}
        return Graph(ents, [HoldEdge("U", "S", 100.0, date(2020, 1, 1), 1.0), HoldEdge("U", "T", 15.0, u_since, 1.0),
                            HoldEdge("S", "T", 10.0, date(2020, 1, 1), 50.0)],
                     [FlowEdge("g", "X", "S", SHARE_TRANSFER, 150.0, date(2026, 6, 1), target="T",
                               attrs={"listed_market_trade": False, "receipt_kind": "NONE"})])
    sg_ = lambda b: round(sum(150.0 * it.effective / 100.0 for it in run(b, CEILING)[2]["g"].items if it.jur == SG and it.levy == "income"), 2)
    check(sg_(sg_grp(date(2020, 1, 1))) == 0.0 and sg_(sg_grp(date(2025, 1, 1))) == 17.0,
          "s13W (decision D45): S's 10%% with its parent's 15%% held since 2020 — 25%% for the group at the start of the 24 months: "
          "exempt (s13W(1B)); the parent's stake bought in 2025 does not count — 17%% x (150 - 50) = 17 (got %s, %s)"
          % (sg_(sg_grp(date(2020, 1, 1))), sg_(sg_grp(date(2025, 1, 1)))))

    # ---- decision D46: capitalisation of reserves (国税函〔2010〕79号 第四条). The Hong Kong H has held all of the Mainland OP since
    #      2020 at 2000; OP capitalises 1000 for it on 2026-03-31; an outside buyer may pay H 5000 for OP on 2026-09-15
    def cap_graph(source="retained_earnings", sell=True, parent=HK, cap_attrs=None):
        hk = {"managed_from": HK, "residence_cert": True, "fixed_place_in_cn": False, "bo_safe_harbour": True}
        ents = {"H": Entity("H", parent, attrs=dict(hk) if parent == HK else {"managed_from": CN}),
                "OP": Entity("OP", CN if parent == HK else HK, attrs={"managed_from": CN if parent == HK else HK}),
                "X": Entity("X", SG, attrs={"managed_from": SG})}
        div = {"receipt_kind": "REMITTED", "foreign_headline_rate": 25, "underlying_profits_taxed": True, "deductible_at_payer": False,
               "listed_market_trade": False, "underlying_tax_share": 0.0, "foreign_taxed": False}
        flows = [FlowEdge("cap", "OP", "H", DIVIDEND, 1000.0, ON, attrs=dict(dict(div, capitalised=True, capitalised_from=source), **(cap_attrs or {})))]
        if sell:
            flows.append(FlowEdge("exit", "X", "H", SHARE_TRANSFER, 5000.0, date(2026, 9, 15), target="OP",
                                  attrs={"listed_market_trade": False, "immovable_ratio": 0, "receipt_kind": "NONE"}))
        return Graph(ents, [HoldEdge("H", "OP", 100.0, date(2020, 1, 1), 2000.0)], flows)
    pay = lambda lb, j, levy="income", who=None: round(sum(lb.flow.amount * it.effective / 100.0 for it in lb.items
                                                           if it.jur == j and it.levy == levy and not it.deferred
                                                           and (who is None or it.borne_by == who)), 2)
    lo, hi = run(cap_graph(sell=False), FLOOR)[2], run(cap_graph(sell=False), CEILING)[2]
    check(pay(lo["cap"], CN) == 0.0 and any(it.deferred for it in lo["cap"].items if it.jur == CN) and pay(hi["cap"], CN) == 100.0
          and pay(lo["cap"], HK) == pay(hi["cap"], HK) == 0.0 and pay(lo["cap"], CN, "stamp", "payer") == 0.25,
          "capitalisation (decision D46): 1000 of retained earnings — a dividend on the decision, 5%% withheld and deferred as reinvested "
          "in OP (102号 第二条（一）1; the ceiling: GAAR denies the deferral, the PPT the 5%%), nothing received in Hong Kong "
          "(s15H(5); ARC 75); OP's books stamp "
          "0.025%% x 1000 = 0.25 (got CN %s / %s, HK %s, stamp %s)" % (pay(lo["cap"], CN), pay(hi["cap"], CN), pay(hi["cap"], HK),
                                                                      pay(lo["cap"], CN, "stamp", "payer")))
    lo, hi = run(cap_graph(), FLOOR)[2], run(cap_graph(), CEILING)[2]
    check(pay(lo["cap"], CN) == 50.0 and pay(hi["cap"], CN) == 100.0 and pay(lo["exit"], CN) == pay(hi["exit"], CN) == 200.0
          and not any(it.deferred for it in lo["cap"].items),
          "capitalisation, then H sells OP: the deferral ends — 5%% x 1000 = 50 within 7 days of the proceeds (102号 第六条); "
          "the Mainland basis is 2000 + 1000: 10%% x (5000 - 3000) = 200 (79号 第四条; 37号 第三条) (got %s / %s, exit %s / %s)"
          % (pay(lo["cap"], CN), pay(hi["cap"], CN), pay(lo["exit"], CN), pay(hi["exit"], CN)))
    due = lo["cap"].deadlines.get("recapture")
    check(due == date(2026, 9, 22) and "recapture" not in hi["cap"].deadlines,
          "capitalisation, withdrawn: the deferred tax is due 7 days after the proceeds of 2026-09-15 — 2026-09-22; under the "
          "ceiling's GAAR there was no deferral to end (got %s)" % (due,))
    lo, hi = run(cap_graph("share_premium"), FLOOR)[2], run(cap_graph("share_premium"), CEILING)[2]
    check(pay(lo["cap"], CN) == pay(hi["cap"], CN) == 0.0 and pay(hi["cap"], CN, "stamp") == 0.0 and pay(hi["exit"], CN) == 300.0,
          "capitalisation of share premium: no dividend, no stamp (the books total unchanged), no basis: 10%% x (5000 - 2000) = 300 "
          "(79号 第四条第二款; 印花税法 第十一条) (got %s, %s, %s)" % (pay(hi["cap"], CN), pay(hi["cap"], CN, "stamp"), pay(hi["exit"], CN)))
    lo = run(cap_graph(sell=False, parent=CN), FLOOR)[2]
    lo2 = run(cap_graph("share_premium", sell=False, parent=CN), FLOOR)[2]
    check(pay(lo["cap"], CN) == 250.0 and pay(lo2["cap"], CN) == 0.0,
          "a Mainland parent's Hong Kong subsidiary capitalises 1000: of retained earnings the parent's dividend, 25%% = 250 (no "
          "underlying tax); of share premium nothing — 79号 第四条 speaks of any investee (got %s, %s)" % (pay(lo["cap"], CN), pay(lo2["cap"], CN)))
    g = cap_graph(cap_attrs={"capitalised": False, "reinvested_in_cn": True, "reinvestment_form": "capital_increase",
                             "direct_payment": True, "reinvestment_from_distributed_profit": True})
    groups = run(g, FLOOR)[1]
    asked = sorted({n.key for v in groups.values() for n in v if str(n.key).endswith("reinvested_into")})
    check(bool(asked), "a cash dividend reinvested somewhere in the Mainland, H later selling OP: whether the deferred investment "
          "went with the sale turns on where it was made — asked (got %s)" % asked)

    # ---- decision D47: branches. H (with a subsidiary at home) has a branch in another jurisdiction whose year, ending
    #      2026-12-31, made 1000
    def br(ho, j, profit=1000.0, **attrs):
        h = dict({"managed_from": ho, "residence_cert": True, "branch_profit_" + j.lower(): profit,
                  "branch_period_end_" + j.lower(): date(2026, 12, 31)}, **attrs)
        return Graph({"H": Entity("H", ho, attrs=h), "S": Entity("S", ho, attrs={"managed_from": ho})},
                     [HoldEdge("H", "S", 100.0, date(2020, 1, 1), 1.0)], [])
    def br_tax(g, bound, jur=None):
        lb = run(g, bound)[2]
        fid = [k for k in lb if k.startswith("branch:")]
        return round(sum(lb[k].flow.amount * it.effective / 100.0 for k in fid for it in lb[k].items
                         if it.levy == "income" and (jur is None or it.jur == jur)), 2) if fid else None
    g = br(CN, HK)
    check(br_tax(g, FLOOR) == br_tax(g, CEILING) == 250.0 and br_tax(g, CEILING, HK) in (0.0, 165.0),
          "branch (decision D47): a Mainland company's Hong Kong branch made 1000 — the Mainland charges 25%% remitted or not, less the "
          "Hong Kong tax where its profit arises there (s14, a judgement): 250 in all (125号 第三条（一）; EIT art 23) (got %s, %s)"
          % (br_tax(g, FLOOR), br_tax(g, CEILING)))
    g = br(HK, CN)
    check(br_tax(g, FLOOR, CN) == br_tax(g, CEILING, CN) == 250.0 and br_tax(g, FLOOR, HK) == br_tax(g, CEILING, HK) == 0.0,
          "branch: a Hong Kong company's Mainland establishment — 25%% of 1000 (EIT art 3(2)), nothing withheld; Hong Kong 0 (offshore, "
          "or credited under the Arrangement at the ceiling) (got %s, %s)" % (br_tax(g, CEILING, CN), br_tax(g, CEILING, HK)))
    g, g2 = br(SG, CN, branch_receipt_cn="REMITTED"), br(SG, CN, branch_receipt_cn="NONE")
    check(br_tax(g, FLOOR, SG) == br_tax(g, CEILING, SG) == 0.0 and br_tax(g2, CEILING, SG) == 0.0 and br_tax(g, CEILING, CN) == 250.0,
          "branch: a Singapore company's Mainland branch, its profit remitted — exempt (s13(8)(b): taxed there at a headline 25%%), at "
          "the ceiling credited (s50); not remitted: not received (got %s, %s)" % (br_tax(g, FLOOR, SG), br_tax(g, CEILING, SG)))
    g = br(HK, SG)
    check(br_tax(g, FLOOR) == 0.0 and br_tax(g, CEILING) == 335.0,
          "branch: a Hong Kong company's Singapore branch — Singapore 17%% if its trade is there, Hong Kong 16.5%% if the profit arises "
          "in Hong Kong, two judgements; no unilateral credit for a profit charged under s14 (Sch 54 Pt 2 s2(1)): 0 .. 335 (got %s, %s)"
          % (br_tax(g, FLOOR), br_tax(g, CEILING)))
    g = br(CN, HK, profit=-500.0)
    check(br_tax(g, CEILING) is None, "branch: a loss places nothing — it does not reach the Mainland profit (EIT art 17)")
    from .facts import facts_for as _ff3

    def scope_facts(ents, holds, payee):
        g = Graph(dict(ents, X=Entity("X", CN, attrs={"managed_from": CN})), holds,
                  [FlowEdge("i", "X", payee, INTEREST, 100.0, ON, attrs={"receipt_kind": "REMITTED"})])
        return _ff3(g, g.flows[0])
    one = scope_facts({"A": Entity("A", SG, attrs={"fixed_place_in_cn": True, "fixed_place_in_hk": False})}, [], "A")
    two = scope_facts({"A": Entity("A", SG, attrs={"fixed_place_in_cn": True, "fixed_place_in_hk": False}),
                       "B": Entity("B", SG, attrs={"fixed_place_in_cn": False, "fixed_place_in_hk": False})},
                      [HoldEdge("A", "B", 100.0, date(2020, 1, 1), 1.0)], "A")
    hk1 = scope_facts({"A": Entity("A", HK, attrs={"fixed_place_in_cn": True, "fixed_place_in_sg": False})}, [], "A")
    check(one[("payee", "is_relevant_group_entity")] is False and two[("payee", "is_relevant_group_entity")] is True
          and one[("payee", "is_mne_member")] is True and hk1[("payee", "is_mne_member")] is True,
          "places of business abroad (decision D47): a single Singapore company with a Mainland branch is no relevant group (e-Tax "
          "Guide 10L para 5.5), two Singapore companies, one with it, are (5.6; s10L(5)(b)(ii)); a stand-alone entity with a "
          "permanent establishment abroad is an MNE entity (s15H(1))")

    # ---- decision D48: a sale of land or a building. S sells to an outside B for 10,000 (VAT exclusive) on 2026-06-30 what it
    #      bought on 2018-01-15 for 6,000 (invoice; deed tax 180 paid; basis 6,000); both general taxpayers in a city district
    def prop(seller=CN, loc=CN, amount=10000.0, **fa):
        base = {"vat_general_taxpayer": True, "ucmt_location": "urban", "residence_cert": True}
        ents = {"S": Entity("S", seller, attrs=dict(base, managed_from=seller)), "B": Entity("B", loc, attrs=dict(base, managed_from=loc)),
                "U": Entity("U", seller, attrs={"managed_from": seller})}
        attrs = dict({"property_loc": loc, "property_use": "non_residential", "acquired_on": date(2018, 1, 15), "acquisition_price": 6000.0,
                      "cost_basis": 6000.0, "self_built": False, "deed_paid_on_acquisition": 180.0, "price_includes_vat": False,
                      "input_vat_documents_kept": True, "receipt_kind": "REMITTED", "held_as_trading_stock": False}, **fa)
        return Graph(ents, [HoldEdge("U", "S", 100.0, date(2015, 1, 1), 1.0)],
                     [FlowEdge("sale", "B", "S", "PROPERTY_TRANSFER", amount, date(2026, 6, 30), attrs=attrs)])
    lv = lambda g, bound, levy, jur=CN, who=None: round(sum(run(g, bound)[2]["sale"].flow.amount * it.effective / 100.0
                                                            for it in run(g, bound)[2]["sale"].items
                                                            if it.levy == levy and it.jur == jur and (who is None or it.borne_by == who)), 2)
    g = prop()
    check(lv(g, FLOOR, "vat", who="payee") == 900.0 and lv(g, FLOOR, "vat", who="payer") == -900.0
          and lv(g, FLOOR, "surcharge", who="payee") == 81.0 and lv(g, FLOOR, "surcharge", who="payer") == -81.0
          and lv(g, FLOOR, "stamp", who="payee") == 5.0 and lv(g, FLOOR, "lat") == 400.2
          and lv(g, FLOOR, "deed") == 300.0 and lv(g, CEILING, "deed") == 500.0 and lv(g, FLOOR, "income") == 878.45,
          "property (decision D48): a Mainland building sold for 10,000 — VAT 9% (增值税法 第十条), the buyer's credit; city "
          "maintenance 7% and local education 2% on each side's VAT (公告2021年第28号); LAT on 10,000 less 6,000 x "
          "(1 + 5% x 8 years) and 266 of taxes = 1,334 x 30% = 400.2 (21号; 220号 第七条; 细则 第十条); deed tax 3%-5% unknown "
          "province (契税法 第三条); stamp 0.05% each; the resident's gain 25% x (10,000 - 6,000 - 486.2) = 878.45")
    g = prop(seller=HK)
    check(lv(g, FLOOR, "income") == 400.0 and lv(g, FLOOR, "lat") == 400.2 and lv(g, FLOOR, "income", HK) == 0.0
          and lv(g, CEILING, "income", HK) == 260.0,
          "property: a Hong Kong seller of the Mainland building — 10% on the gain 4,000 (EIT art 19(2); 实施条例 第七条（三）), the "
          "same LAT; Hong Kong FSIE on the non-IP disposal gain at the ceiling, 16.5% x 4,000 less 400 (Sch 56; s50)")
    g, g2 = prop(acquired_on=date(2015, 6, 30)), prop(acquired_on=date(2015, 6, 30), vat_simplified_elected=True)
    check(lv(g2, FLOOR, "vat", who="payee") == lv(g2, CEILING, "vat", who="payee") == 214.29 and lv(g, CEILING, "vat", who="payee") == 900.0
          and lv(g, FLOOR, "vat", who="payee") == 214.29,
          "property bought before 2016-05-01: the 5% simplified method on the price less the purchase, 5% x (10,500 - 6,000) / "
          "1.05 = 214.29 when elected (公告2026年第10号 三（二）4、四（八）); the election open: either end")
    ss = prop()
    ss.entities["S"].attrs["vat_general_taxpayer"] = False
    check(lv(ss, FLOOR, "vat", who="payee") == 125.24,
          "property sold by a small-scale taxpayer: 3% x (10,300 - 6,000) / 1.03 = 125.24 (增值税法 第十一条; 四（八）)")
    ap = prop(lat_appraised_value=7000.0)
    check(lv(ap, FLOOR, "lat") == 874.2,
          "property with an appraisal: 10,000 less 7,000 and 86 of taxes = 2,914 x 30% = 874.2 (细则 第七条（四）)")
    big = prop(amount=20000.0)
    check(lv(big, FLOOR, "lat") == 4311.2,
          "property sold for 20,000: the value added 11,248 is 128.5% of the deductions 8,752 — 50% x 11,248 - 15% x 8,752 = 4,311.2")
    hk = prop(seller=HK, loc=HK, amount=10000000.0, currency="HKD", stamp_borne_by="payer", acquisition_price=6000000.0, cost_basis=6000000.0)
    check(lv(hk, FLOOR, "stamp", HK, "payer") == 370000.0 and lv(hk, FLOOR, "income", HK) == 0.0 and lv(hk, CEILING, "income", HK) == 660000.0,
          "property in Hong Kong for HK$10,000,000: Scale 1 — the lesser of 3.75% and 270,000 + 10% of the excess over "
          "9,000,000 = 370,000 (Cap 117 First Schedule head 1(1)); the gain charged only if not capital (s14): 0 .. 660,000")
    sgp = prop(seller=SG, loc=SG, amount=10000000.0, currency="SGD", property_use="residential", acquired_on=date(2025, 8, 1),
               acquisition_price=6000000.0, cost_basis=6000000.0)
    check(lv(sgp, FLOOR, "stamp", SG, "payer") == 539600.0 + 6500000.0 and lv(sgp, FLOOR, "stamp", SG, "payee") == 1600000.0
          and lv(sgp, FLOOR, "vat", SG) == 0.0,
          "property in Singapore, residential, bought 2025-08-01 and sold within a year for S$10,000,000: BSD 539,600, the "
          "entity's ABSD 65%, the seller's SSD 16% (First Schedule Article 3(a)(iv), (bi)(xix), (bj)); no GST (residential)")
    sgc = prop(seller=SG, loc=SG, amount=10000000.0, currency="SGD", acquisition_price=6000000.0, cost_basis=6000000.0)
    sgc.entities["S"].attrs["gst_registered"] = True
    sgc.entities["B"].attrs["gst_input_fully_recoverable"] = True
    check(lv(sgc, FLOOR, "vat", SG, "payee") == 900000.0 and lv(sgc, FLOOR, "vat", SG, "payer") == -900000.0
          and lv(sgc, FLOOR, "stamp", SG, "payer") == 469600.0 and lv(sgc, FLOOR, "stamp", SG, "payee") == 0.0,
          "property in Singapore, non-residential, a registered seller: GST 9% and the buyer's input tax; BSD on the non-residential "
          "scale 469,600; no seller's duty (no SSD on commercial property)")
    # the surcharges on the VAT the model already computed: a foreign servicer's withheld VAT carries none (城市维护建设税法
    # 第三条); the Mainland payer's credit for it lowers its own
    gsvc = Graph({"P": Entity("P", CN, attrs={"vat_general_taxpayer": True, "ucmt_location": "urban", "managed_from": CN}),
                  "V": Entity("V", SG, attrs={"managed_from": SG, "residence_cert": True})}, [],
                 [FlowEdge("svc", "P", "V", SERVICE_FEE, 1000.0, date(2026, 6, 30),
                           attrs={"service_location": CN, "price_includes_vat": False, "input_vat_documents_kept": True, "receipt_kind": "NONE",
                                  "service_days_12m": 30, "profit_margin": 20})])
    sv = run(gsvc, FLOOR)[2]["svc"]
    sur = {}
    for it in sv.items:
        if it.levy == "surcharge":
            sur[it.borne_by] = round(sur.get(it.borne_by, 0.0) + 1000.0 * it.effective / 100.0, 2)
    check(sur.get("payee") is None and sur.get("payer") == -5.4,
          "surcharges (decision D48): none on a foreign servicer's withheld VAT 60 (城市维护建设税法 第三条); the payer's credit of it lowers "
          "its own: -9%% x 60 = -5.4 (公告2021年第28号) (got %s)" % sur)

    # ---- decision D49: the rent of land or a building. O lets to an outside tenant T where the property lies, 1,000 a year
    #      (VAT exclusive), 40% of it O's profit; a 3-year lease
    def lease(owner=CN, loc=CN, amount=1000.0, **fa):
        base = {"vat_general_taxpayer": True, "ucmt_location": "urban", "residence_cert": True}
        ents = {"O": Entity("O", owner, attrs=dict(base, managed_from=owner)), "T": Entity("T", loc, attrs=dict(base, managed_from=loc)),
                "U": Entity("U", owner, attrs={"managed_from": owner})}
        attrs = dict({"property_loc": loc, "property_use": "non_residential", "acquired_on": date(2018, 1, 15), "price_includes_vat": False,
                      "input_vat_documents_kept": True, "receipt_kind": "REMITTED", "profit_margin": 40, "lease_term_months": 36,
                      "property_tax_area": True, "stamp_borne_by": "payer"}, **fa)
        return Graph(ents, [HoldEdge("U", "O", 100.0, date(2015, 1, 1), 1.0)],
                     [FlowEdge("rent", "T", "O", "PROPERTY_RENT", amount, date(2026, 6, 30), attrs=attrs)])
    rl = lambda g, bound, levy, jur=CN, who=None: round(sum(run(g, bound)[2]["rent"].flow.amount * it.effective / 100.0
                                                            for it in run(g, bound)[2]["rent"].items
                                                            if it.levy == levy and it.jur == jur and (who is None or it.borne_by == who)), 2)
    g = lease()
    check(rl(g, FLOOR, "vat", who="payee") == 90.0 and rl(g, FLOOR, "property") == 120.0 and rl(g, FLOOR, "stamp", who="payee") == 1.0
          and rl(g, FLOOR, "income", who="payee") == 100.0 and rl(g, FLOOR, "income", who="payer") == -250.0
          and rl(g, FLOOR, "surcharge", who="payee") == 8.1,
          "rent (decision D49): a Mainland building let for 1,000 — VAT 9% (增值税法 第十条), property tax (房产税) 12% of the rent (条例 第四条), "
          "stamp 0.1% each (租赁合同); the lessor's income 25% x 40% = 100, the tenant deducts 250 (实施条例 第四十七条); "
          "surcharges 9% x 90 = 8.1")
    g = lease(owner=HK)
    check(rl(g, FLOOR, "income", who="payee") == 100.0 and rl(g, FLOOR, "surcharge", who="payee") == 0.0 and rl(g, FLOOR, "property") == 120.0,
          "rent: a Hong Kong owner of the Mainland building — 10% withheld on the rent (EIT art 19(1)); its VAT carries no "
          "surcharge (城市维护建设税法 第三条: a foreign seller of a service); property tax the same")
    hk = lease(owner=HK, loc=HK)
    hko = lease(owner=CN, loc=HK)
    check(rl(hk, FLOOR, "income", HK, "payee") == 66.0 and rl(hk, FLOOR, "property", HK) == 0.0 and rl(hk, FLOOR, "stamp", HK, "payer") == 5.0
          and rl(hko, FLOOR, "property", HK) == 0.0 and rl(hko, CEILING, "property", HK) == 120.0,
          "rent in Hong Kong: a Hong Kong company's — profits tax 16.5% x 40% = 66, its property tax set off (s25); the lease "
          "of 3 years stamped at 0.5% of the yearly rent, here the tenant's (head 1(2)(b)(iii)); a foreign owner's property tax "
          "15% x 80% = 12% of the rent unless the rent is part of a business it carries on here (a judgement)")
    sg = lease(owner=SG, loc=SG, currency="SGD", annual_value=900.0)
    check(rl(sg, FLOOR, "income", SG, "payee") == 68.0 and rl(sg, FLOOR, "property", SG) == 90.0 and rl(sg, FLOOR, "stamp", SG, "payer") == 4.0,
          "rent in Singapore: income 17% x 40% = 68 (s10(1)(f)); property tax 10% of the annual value 900 (non-residential; IRAS); "
          "the lessee's duty 0.4% of the year's rent within 4 years (Article 8(aa))")
    sgr = lease(owner=SG, loc=SG, currency="SGD", annual_value=50000.0, property_use="residential", amount=60000.0)
    check(rl(sgr, FLOOR, "property", SG) == 8000.0,
          "rent of a let residence in Singapore: 12% of 30,000 + 20% of 15,000 + 28% of 5,000 = 8,000 on the annual value 50,000")

    # decision D43: across the border. OP's goods (applicable VAT 13%, refund 9%, no export duty) shipped to the customer
    levy = lambda labs, fid, kind, who=None: round(sum(labs[fid].flow.amount * it.effective / 100.0 for it in labs[fid].items
                                                      if it.levy == kind and (who is None or it.borne_by == who)), 2)
    rates = {"goods_vat_rate": 13.0, "export_refund_rate": 9.0, "export_duty_rate": 0.0}
    c = trade_case(None, SG)
    c.flows["sale"].update(rates, delivered_to=SG)
    lo, hi = (run(TRADING.build(tev, {TRADER: None, "payment": False}, c), b)[2] for b in (FLOOR, CEILING))
    check(levy(lo, "sale", "vat", "payee") == 40.0 == levy(hi, "sale", "vat", "payee") and levy(hi, "sale", "vat", "payer") == 90.0,
          "goods (decision D43): exported to Singapore — zero-rated, the refund 9%% short of the 13%% input VAT: 4%% x 1000 = 40, a cost "
          "of OP (公告2026年第11号 第五条); the customer's import GST 9%% x 1000 = 90 when it recovers none is its own (got %s, %s)"
          % (levy(lo, "sale", "vat", "payee"), levy(hi, "sale", "vat", "payer")))
    c = trade_case(HK, SG, purchase_effected_in_hk=False, sale_effected_in_hk=False, routed_via_trader=False, delivered_to=SG)
    c.flows["supply"].update(rates)
    lo = run(TRADING.build(tev, {TRADER: HK, "payment": False}, c), FLOOR)[2]
    check(levy(lo, "supply", "vat", "payee") == 32.0 and levy(lo, "resale", "vat", "payee") == 0.0,
          "goods: through a Hong Kong trader, shipped straight to Singapore — OP exports at 800: 4%% x 800 = 32; the trader "
          "pays no Mainland VAT (got %s, %s)" % (levy(lo, "supply", "vat", "payee"), levy(lo, "resale", "vat", "payee")))
    c = trade_case(CN, SG, routed_via_trader=False, delivered_to=SG, goods_vat_rate=13.0, export_refund_rate=9.0, export_duty_rate=0.0)
    lo = run(TRADING.build(tev, {TRADER: CN, "payment": False}, c), FLOOR)[2]
    check(levy(lo, "supply", "vat") == 0.0 and levy(lo, "resale", "vat", "payee") == 32.0,
          "goods: a Mainland trader buys at home and exports itself (免退): 4%% x its purchase 800 = 32, none on OP's domestic "
          "sale (got %s, %s)" % (levy(lo, "supply", "vat"), levy(lo, "resale", "vat", "payee")))
    c = trade_case(None, SG)
    c.flows["sale"].update(delivered_to=SG, export_duty_rate=0.0)
    lo, hi = (run(TRADING.build(tev, {TRADER: None, "payment": False}, c), b)[2] for b in (FLOOR, CEILING))
    check(levy(lo, "sale", "vat", "payee") == 0.0 and levy(hi, "sale", "vat", "payee") == 130.0,
          "goods: the VAT and refund rates not given — none, or 13%% with no refund (got %s, %s)"
          % (levy(lo, "sale", "vat", "payee"), levy(hi, "sale", "vat", "payee")))
    gi = Graph({"S": Entity("S", SG, attrs=dict(nofix, managed_from=SG)), "B": Entity("B", CN, attrs={"managed_from": CN, "vat_general_taxpayer": True}),
                "U": Entity("U", CN)},
               [HoldEdge("U", "S", 100.0, date(2020, 1, 1), 1.0), HoldEdge("U", "B", 100.0, date(2020, 1, 1), 1.0)],
               [FlowEdge("buy", "B", "S", "GOODS", 1000.0, ON, attrs={"cost_basis": 900.0, "delivered_to": CN, "shipped_from": SG,
                                                                   "goods_vat_rate": 13.0, "import_duty_rate": 10.0})])
    lo = run(gi, FLOOR)[2]
    check(levy(lo, "buy", "customs") == 100.0 and levy(lo, "buy", "vat") == 0.0
          and any(it.levy == "vat" and it.deduction for it in lo["buy"].items),
          "goods: a Mainland group company imports — duty 10%% x 1000 = 100 (关税法 第二十三条), import VAT 13%% x 1100 credited "
          "as input tax (got %s, %s)" % (levy(lo, "buy", "customs"), levy(lo, "buy", "vat")))
    del gi.flows[0].attrs["import_duty_rate"]
    check(("data.import_duty_rate", "buy") in run(gi, CEILING)[1], "goods: the import duty rate not given — asked of a group importer")
    c = trade_case(None, SG)
    del c.flows["sale"]["cost_basis"]
    g = TRADING.build(tev, {TRADER: None, "payment": False}, c)
    lo, hi = run(g, FLOOR)[2], run(g, CEILING)
    check(tax_of(lo, CN) == 0.0 and tax_of(hi[2], CN) == 250.0 and any(n.key.endswith("cost_basis") for ns in hi[1].values() for n in ns),
          "goods: the cost of the goods unknown — none or the whole price at the two ends, asked (got %s, %s)"
          % (tax_of(lo, CN), tax_of(hi[2], CN)))

    # ---- several activities in one case (scenarios.composite): one group, the chain part deciding who holds OP
    from .scenarios import IPCO, composite
    hip = composite(["ip", "holding"])
    c = reorg_case(CN, HK)
    c.flows["roy"] = {"receipt_kind": "NONE"}
    g = hip.build(replace(ev, royalty=500.0), {HOLD: HK, IPCO: SG, "financing": "EQUITY", "payment": False, "exit_route": "DIRECT"}, c)
    check(hip.name == "holding+ip" and sorted((h.holder, h.held) for h in g.holds) == [(HOLD, OP), (ULT, HOLD), (ULT, IPCO)]
          and sorted(f.id for f in g.flows) == ["exit", "iptx", "reorg", "roy", "up1", "up2"],
          "composite: holding + ip — OP held through HOLD only, the royalty to IPCO beside the chain, the IP moved to it (got %s)"
          % sorted(f.id for f in g.flows))
    try:
        composite(["holding", "repatriation"])
        ok_ = False
    except ValueError:
        ok_ = True
    check(ok_, "composite: holding and repatriation both distribute OP's profit: not combinable")

    # ---- decision D20: the income inclusion rule — a Hong Kong or Singapore parent pays its share of the top-up of a Mainland
    #      entity taxed below 15% (HK Sch 60 Art 2.1-2.3; SG MEMTA s11-s15); qualified status from the OECD central record
    low_cn = {"globe_income": 1000.0, "covered_taxes_other": 50.0, "sbie": 0.0, "p2_qualified_cbcr_cn": False,
              "p2_dm_avg_revenue_eur_cn": 1e9, "p2_dm_avg_income_eur_cn": 1e9, "managed_from": CN}
    quiet = lambda loc: {"globe_income": 0.0, "covered_taxes_other": 0.0, "sbie": 0.0, "managed_from": loc, "group_revenue_eur": 1e9}

    def iir_run(ents, holds):
        g = Graph({k: Entity(k, loc, attrs=dict(a)) for k, (loc, a) in ents.items()}, holds,
                  [FlowEdge("d", "OP", holds[-1].holder, DIVIDEND, 100.0, ON, attrs={"receipt_kind": "NONE"})])
        lb = run(g, FLOOR, EX_ANTE)[2]
        return {k: round(x.flow.amount * sum(it.effective for it in x.items if it.levy == "income") / 100.0, 2)
                for k, x in lb.items() if k.startswith("iir:")}

    got = iir_run({"OP": (CN, low_cn), "ULT": (SG, quiet(SG))}, [HoldEdge("ULT", "OP", 100.0, date(2020, 1, 1), 1.0)])
    check(got == {"iir:OP>ULT": 100.0},
          "IIR: a Singapore ultimate parent pays the MTT on a Mainland entity at 5%%: (15%% - 5%%) x 1000 = 100 (got %s)" % got)
    got = iir_run({"OP": (CN, low_cn), "HOLD": (HK, quiet(HK)), "ULT": (CN, quiet(CN))},
                  [HoldEdge("ULT", "HOLD", 100.0, date(2020, 1, 1), 1.0), HoldEdge("HOLD", "OP", 100.0, date(2020, 1, 1), 1.0)])
    check(got == {"iir:OP>HOLD": 100.0},
          "IIR: a Mainland ultimate parent applies none, so the Hong Kong intermediate parent does (Art 2.1.2): 100 (got %s)" % got)
    got = iir_run({"OP": (CN, low_cn), "HOLD": (HK, quiet(HK)), "ULT": (SG, quiet(SG))},
                  [HoldEdge("ULT", "HOLD", 100.0, date(2020, 1, 1), 1.0), HoldEdge("HOLD", "OP", 100.0, date(2020, 1, 1), 1.0)])
    check(got == {"iir:OP>ULT": 100.0},
          "IIR: a Singapore ultimate parent applies a qualified IIR, so the Hong Kong intermediate parent does not (Art 2.1.3(a)) (got %s)" % got)
    got = iir_run({"OP": (CN, low_cn), "HOLD": (HK, quiet(HK)), "ULT": (CN, quiet(CN))},
                  [HoldEdge("ULT", "HOLD", 60.0, date(2020, 1, 1), 1.0), HoldEdge("HOLD", "OP", 100.0, date(2020, 1, 1), 1.0)])
    check(got == {"iir:OP>HOLD": 100.0},
          "IIR: a partially-owned Hong Kong parent (40%% held outside) applies it in its own right on all it owns (Art 2.1.4) (got %s)" % got)
    got = iir_run({"OP": (SG, dict(quiet(SG), covered_taxes_other=0.0, globe_income=1000.0)), "ULT": (HK, quiet(HK))},
                  [HoldEdge("ULT", "OP", 100.0, date(2020, 1, 1), 1.0)])
    check(got == {}, "IIR: a Singapore entity has its qualified domestic top-up — no IIR top-up remains (got %s)" % got)

    # ---- decision D19: the client's own holding company leaves the chain — no CN / HK / SG law lets a company move its
    #      place of incorporation out, so it passes its stake on (to ULT, or to a new company) and is wound up
    from .cases import SCENARIOS
    from .facts import facts_for
    from .scenarios import IP, NEW, REPATRIATION, SERVICER, SERVICES
    _, cA, eA = SCENARIOS["A"]
    base = {"financing": "EQUITY", "payment": False, "exit_route": "DIRECT"}
    g = HOLDING.build(eA, dict(base, **{HOLD: None}), cA)
    un, wd, up = next((f for f in g.flows if f.id == "unwind"), None), next((f for f in g.flows if f.id == "wind"), None), g.holding(ULT, OP)
    check(un is not None and (un.payer, un.payee, un.target, un.amount) == (ULT, HOLD, OP, 5000.0) and wd is not None
          and (wd.payer, wd.payee, wd.income, wd.amount) == (HOLD, ULT, "LIQUIDATION", 5000.0)
          and up is not None and (up.ratio, up.since, up.cost) == (100.0, None, 5000.0) and g.entities[HOLD].attrs.get("wound_up_by_plan"),
          "unwinding: HOLD dissolved — its stake in OP to ULT at market value, then its liquidation to ULT; ULT holds OP from the step")
    lo, hi = run(g, FLOOR, EX_ANTE)[2], run(g, CEILING, EX_ANTE)[2]
    cn = lambda lb, amt: round(sum(amt * it.effective / 100.0 for it in lb.items if it.jur == CN and it.levy == "income" and not it.deferred), 2)
    check(cn(lo["unwind"], 5000.0) == 200.0 == cn(hi["unwind"], 5000.0) and cn(lo["exit"], 5000.0) == 0.0,
          "unwinding: no special reorganisation fits — 10%% x (5000 - 3000) in the Mainland on the step, the exit's basis is 5000 (got %s, %s, exit %s)"
          % (cn(lo["unwind"], 5000.0), cn(hi["unwind"], 5000.0), cn(lo["exit"], 5000.0)))
    g = HOLDING.build(eA, dict(base, **{HOLD: SG}), cA)
    new = HOLD + NEW
    flow = {f.id: f for f in g.flows}
    check(new in g.entities and g.entities[new].loc == SG and g.entities[new].attrs.get("created_by_plan") and g.holding(ULT, new).designed
          and g.holding(new, OP).cost == 5000.0 and g.holding(HOLD, OP) is None and flow["unwind"].payer == new
          and flow["up1"].payee == new and flow["up2"].payer == new and flow["exit"].payee == new,
          "unwinding: HOLD moved to Singapore — a new HOLD_NEW buys the stake at market value and holds it; HOLD is wound up")
    c2 = replace(cA, flows={k: {f: v for f, v in fs.items() if f != "amount"} for k, fs in cA.flows.items()})
    grp = run(HOLDING.build(eA, dict(base, **{HOLD: None}), c2), FLOOR, EX_ANTE)[1]
    check(("data.amount", "unwind") in grp and ("data.amount", "wind") in grp,
          "unwinding: the stake's market value and the liquidation distribution unknown: asked (unbounded without them)")
    _, cB, eB = SCENARIOS["B"]
    kept = run(HOLDING.build(eB, dict(base, **{HOLD: HK}), cB), FLOOR, EX_ANTE)[2]
    gone = run(HOLDING.build(eB, dict(base, **{HOLD: None}), cB), FLOOR, EX_ANTE)[2]
    check(any(k.startswith("cfc:HOLD") for k in kept) and not any(k.startswith("cfc:HOLD") for k in gone),
          "unwinding: a holding company wound up in the horizon has distributed its profits — no CFC inclusion (there is one while kept)")
    _, cE, eE = SCENARIOS["E"]
    lb = run(REPATRIATION.build(eE, {HOLD: HK, "repatriation": "LIQUIDATION", "payment": False}, cE), CEILING, EX_ANTE)[2]
    st = [(k, it.jur) for k, x in lb.items() for it in x.items if it.levy == "stamp" and it.effective]
    check(not st, "a liquidation cancels the shares: its disposal part passes by no transfer instrument, no stamp duty (got %s)" % st)
    # what the structure's own later flows break is a fact, not a plan item: the transferee sold out of the group within
    # 2 years (HK SDO s45(5A)); the asset disposed of within 2 years (SG 2014 Rules r 7(1)(b)); the transferor's shares
    # in the transferee sold within 12 months / 3 years (59号 §5(5), §7(1))
    g = HOLDING.build(ev, {HOLD: SG, "financing": "EQUITY", "payment": False, "exit_route": "INDIRECT"}, reorg_case(HK, CN, reorg_facts=met))
    fx = facts_for(g, next(f for f in g.flows if f.id == "reorg"))
    check(fx.get(("flow", "clawback_event_within_2y")) is True and fx.get(("flow", "reorg_commitment_3y")) is False
          and fx.get(("flow", "reorg_shares_kept_12m")) is False,
          "own flows: ULT sells the new HOLD 9 months after the step — the HK s45 relief is withdrawn, the 59号 commitments are broken")
    hk_ = lambda lb: round(sum(4000.0 * it.effective / 100.0 for it in lb.items if it.jur == HK and it.levy == "stamp"), 2)
    check(hk_(run(g, FLOOR, EX_ANTE)[2]["reorg"]) == 8.0, "own flows: so the step's HK stamp duty stands even at the floor: 0.1% x 2 x 4000")
    g = HOLDING.build(ev, {HOLD: HK, "financing": "EQUITY", "payment": False, "exit_route": "DIRECT"}, reorg_case(SG, CN, reorg_facts=met))
    fx = facts_for(g, next(f for f in g.flows if f.id == "reorg"))
    sg_ = lambda lb: round(sum(4000.0 * it.effective / 100.0 for it in lb.items if it.jur == SG and it.levy == "stamp"), 2)
    check(fx.get(("flow", "asset_disposed_within_2y")) is True and fx.get(("flow", "clawback_event_within_2y")) is None
          and sg_(run(g, FLOOR, EX_ANTE)[2]["reorg"]) == 8.0,
          "own flows: HOLD sells the SG shares it took over within 2 years — the SG relief is withdrawn (r 7(1)(b)): 0.2% x 4000 at the floor")
    # ---- decision D22: the IP transfer step — the candidate's owner buys the IP from the present one; every jurisdiction's tax
    from copy import deepcopy
    _, cC, eC = SCENARIOS["C"]
    gs = {x: IP.build(eC, {IPCO: x, "payment": False}, cC) for x in (None, HK, SG, CN)}
    tx = {x: [(f.payer, f.payee, f.amount) for f in g.flows if f.id == "iptx"] for x, g in gs.items()}
    check(tx[HK] == [] and tx[None] == [(OP, IPCO, 400.0)] and tx[SG] == [(IPCO + NEW, IPCO, 400.0)]
          and tx[CN] == [(IPCO + NEW, IPCO, 400.0)] and all(not g.unmodelled for g in gs.values()),
          "IP transfer: the candidate's owner buys the IP from the present one at the stated value; no step unmodelled (got %s)" % tx)

    def ctx_t(t):
        return lambda facts: CaseCtx(facts, t, EX_ANTE, ADJUSTABLE)

    def tax(lb, jur, levy="income", who=None):
        return round(sum(lb.flow.amount * it.effective / 100.0 for it in lb.items if it.jur == jur and it.levy == levy
                         and (who is None or (lb.flow.payer if it.borne_by == "payer" else lb.flow.payee) == who)), 2)

    def iptx(g, bound, t=None):
        return engine(g, ctx_t(t or {}), bound)[2]["iptx"]

    lo, hi = iptx(gs[None], FLOOR), iptx(gs[None], CEILING)
    check(tax(lo, CN, who=IPCO) == 0.0 and tax(hi, CN, who=IPCO) == 30.0,
          "IP transfer: a non-resident's gain — Mainland source the authority's judgement (实施条例 第七条): 0 .. 10%% x (400 - 100) = 30 "
          "(got %s, %s)" % (tax(lo, CN, who=IPCO), tax(hi, CN, who=IPCO)))
    src_cn = {Need(DISCRETION, "flow.ip_transfer_gain_sourced_in_cn"): True, Need(DISCRETION, "payee.ppt"): False}
    c2 = deepcopy(cC)
    c2.roles[IPCO].attrs["fixed_place_in_cn"] = False
    c3 = deepcopy(c2)
    c3.roles[IPCO].attrs["residence_cert"] = False
    t2 = tax(iptx(IP.build(eC, {IPCO: None, "payment": False}, c2), CEILING, src_cn), CN, who=IPCO)
    t3 = tax(iptx(IP.build(eC, {IPCO: None, "payment": False}, c3), CEILING, src_cn), CN, who=IPCO)
    check(t2 == 0.0 and t3 == 30.0, "IP transfer: judged Mainland-sourced, the Arrangement still leaves the gain to Hong Kong (Art 13(7)) — "
          "not without the residence certificate (got %s, %s)" % (t2, t3))
    off = {Need(DISCRETION, "flow.ip_gain_sourced_in_hk"): False, Need(DISCRETION, "flow.ip_transfer_gain_sourced_in_cn"): False}
    hk_f = tax(iptx(gs[None], CEILING, off), HK)
    check(abs(hk_f - 17.325) < 0.01, "IP transfer: an offshore gain received in Hong Kong is an IP disposal gain (s15I) less the R&D fraction "
          "65%% (Sch 17FC): 16.5%% x 300 x 35%% = 17.33 (got %s)" % hk_f)
    c4 = deepcopy(cC)
    c4.flows["iptx"]["ip_allowances_claimed"] = 100.0
    on_cap = {Need(DISCRETION, "flow.ip_gain_sourced_in_hk"): True, Need(DISCRETION, "flow.ip_held_as_capital_asset"): True,
              Need(DISCRETION, "flow.ip_transfer_gain_sourced_in_cn"): False}
    hk_r = tax(iptx(IP.build(eC, {IPCO: None, "payment": False}, c4), CEILING, on_cap), HK)
    check(hk_r == 16.5, "IP transfer: a capital gain arising in Hong Kong — only the deductions allowed come back (s16E(3)): "
          "16.5%% x min(400 - 100, 100) = 16.5 (got %s)" % hk_r)
    cR = Case(roles={OP: RoleFacts(CN, {"vat_general_taxpayer": True}), ULT: RoleFacts(SG, {"managed_from": SG})},
              holds={(ULT, OP): HoldEdge(ULT, OP, 100.0, date(2020, 1, 1), 3000.0)},
              flows={"roy": {"is_equipment_lease": False, "is_aircraft_or_ship_lease": False, "receipt_kind": "NONE"},
                     "iptx": {"amount": 8_000_000.0, "ip_kind": "PATENT", "cost_basis": 1_000_000.0, "cny_rate": 1.0,
                              "price_includes_vat": False, "instrument_used_in_cn": True}})
    gR = IP.build(eC, {IPCO: HK, "payment": False}, cR)
    rl, rh = tax(iptx(gR, FLOOR), CN, who=OP), tax(iptx(gR, CEILING), CN, who=OP)
    check(rl == 250000.0 and rh == 1750000.0, "IP transfer: a resident's technology transfer — 5 million yuan exempt, the rest halved "
          "(第九十条): 25%% x (7m - 5m) x 50%% = 250,000; sisters both wholly held by ULT (111号 第四条 silent): up to 25%% x 7m (got %s, %s)" % (rl, rh))
    cT = deepcopy(cR)
    cT.flows["iptx"]["ip_kind"] = "TRADEMARK"
    lT = iptx(IP.build(eC, {IPCO: HK, "payment": False}, cT), FLOOR)
    check(tax(lT, CN, who=OP) == 1750000.0 and tax(lT, CN, "vat", who=OP) == 480000.0,
          "IP transfer: a trademark is no technology — the whole gain at 25%%, and the sale bears 6%% VAT (销售方为境内单位) the foreign "
          "buyer cannot credit: 480,000 (got %s, %s)" % (tax(lT, CN, who=OP), tax(lT, CN, "vat", who=OP)))
    gx = deepcopy(gR)
    sell, buy = [f for f in gx.flows if f.id == "iptx"][0], None
    held = facts_for(Graph(gx.entities, gx.holds + [HoldEdge(IPCO, OP, 100.0, date(2020, 1, 1), 1.0)], gx.flows), sell)
    check(held[("flow", "ip_parties_100pct_held")] is True and facts_for(gR, sell)[("flow", "ip_parties_100pct_sisters")] is True,
          "IP transfer: one company wholly holding the other is derived (111号 第四条: no reduction); wholly held sisters are flagged for the judgement")
    c5 = deepcopy(cC)
    c5.flows["iptx"]["ip_kind"] = "TRADEMARK"
    c5.roles[OP].attrs["vat_general_taxpayer"] = True
    g5 = IP.build(eC, {IPCO: None, "payment": False}, c5)
    lo5, hi5 = iptx(g5, FLOOR), iptx(g5, CEILING)
    check(tax(lo5, CN, "vat") == 0.0 and tax(lo5, CN, "vat", who=IPCO) == 24.0 and tax(hi5, CN, "vat") == 24.0,
          "IP transfer: a foreign seller's IP is consumed in the Mainland (实施条例 第四条): 6%% x 400 = 24 withheld, credited by OP holding "
          "the contract, payment proof and invoice (公告2026年第13号) — not at the ceiling (got %s, %s)" % (tax(lo5, CN, "vat"), tax(hi5, CN, "vat")))
    c6 = deepcopy(cC)
    c6.flows["iptx"]["instrument_used_in_cn"] = False
    s1, s0 = tax(iptx(gs[SG], FLOOR), CN, "stamp"), tax(iptx(IP.build(eC, {IPCO: SG, "payment": False}, c6), CEILING), CN, "stamp")
    check(s1 == 0.24 and s0 == 0.0, "IP transfer: Hong Kong to Singapore — Mainland stamp duty 0.03%% from each party only if the instrument "
          "is used in the Mainland (印花税法 第一条) (got %s, %s)" % (s1, s0))
    w1 = tax(iptx(gs[SG], FLOOR), SG)
    w0 = tax(iptx(IP.build(replace(eC, on=date(2028, 1, 31)), {IPCO: SG, "payment": False}, cC), FLOOR), SG)
    check(w1 == -13.6 and w0 == 0.0, "IP transfer: the Singapore buyer writes the price down over 5 years (s19B(1AA)): 17%% x 400 / 5 = 13.6 "
          "in the year; none for rights acquired after the basis period for YA 2028 (s19B(10)(aa)) (got %s, %s)" % (w1, w0))
    c7 = deepcopy(cC)
    c7.flows["iptx"]["ip_useful_life_years"] = 5
    am = tax(iptx(IP.build(replace(eC, years=2), {IPCO: None, "payment": False}, c7), FLOOR), CN, who=OP)
    check(am == -40.0, "IP transfer: OP amortises the price over the agreed 5-year life (实施条例 第六十七条): 25%% x 400 x 2/5 = 40 in the "
          "two modelled years (got %s)" % am)
    from .engine import cfc_flows, p2_income
    from .params import Params
    cU = deepcopy(cC)
    cU.roles[ULT] = RoleFacts(CN, {"managed_from": CN})
    cU.roles[IPCO].attrs.update(after_tax_profit=0.0, globe_income=1000.0)
    gU = IP.build(eC, {IPCO: None, "payment": False}, cU)
    labU = engine(gU, ctx_t({}), FLOOR)[2]
    inc = [f.amount for f in cfc_flows(gU, Params(), {}, labU) if f.payer == IPCO]
    check(inc == [300.0] and p2_income(gU, gU.entities[IPCO], 2026, Params()) == 1300.0,
          "IP transfer: the seller keeps the proceeds — its book gain 400 - 100 joins the profit a Mainland parent's CFC rules "
          "see (after the tax on it, nil at the floor) and its GloBE income of the year (got %s)" % inc)
    from .engine import step_income
    cN = deepcopy(cU)
    del cN.flows["iptx"]["amount"]
    gN = IP.build(eC, {IPCO: None, "payment": False}, cN)
    check(step_income(gN, IPCO) == (0.0, ["flow:iptx.amount"]) and p2_income(gN, gN.entities[IPCO], 2026, Params()) is None,
          "IP transfer: no price stated — no gain is counted (never 0 less the carrying amount); the price is asked (got %s)"
          % (step_income(gN, IPCO),))
    # decision D27: the buyer's book amortisation (40 a year, stated) in its GloBE income; the Singapore allowance in covered
    # taxes with the deferred tax recast at 15% (Art 4.4.1): -17% x 80 + 15% x (80 - 40) = -7.6
    from .engine import designed_globe_income, p2_step_tax
    labS = engine(gs[SG], ctx_t({}), FLOOR)[2]
    gi, st = designed_globe_income(gs[SG], IPCO + NEW, 2026, Params()), round(p2_step_tax(labS, IPCO + NEW, 2026, Params()), 2)
    c8 = deepcopy(cC)
    del c8.flows["iptx"]["ip_book_amortization"]
    g8 = IP.build(eC, {IPCO: SG, "payment": False}, c8)
    gv = designed_globe_income(gs[SG], IPCO + NEW, 2026, Params(), labS)
    check(gv == 431.7, "accounts (decision D29): the new IP company's GloBE income leaves out the VAT taken from its VAT-inclusive "
          "royalty, 460 - 500 x 6/106 = 431.70 (got %s)" % gv)
    check(gi == 460.0 and st == -7.6 and designed_globe_income(g8, IPCO + NEW, 2026, Params()) is None,
          "IP transfer (decision D27): the new IP company's GloBE income is its royalty less its book amortisation, 500 - 40 = 460; "
          "its 5-year allowance with deferred tax recast at 15%%: -7.6 in covered taxes; no amortisation stated: asked "
          "(got %s, %s)" % (gi, st))
    fr = facts_for(gs[SG], next(f for f in gs[SG].flows if f.id == "roy"))
    check(fr[("flow", "qualifying_rd_expenditure")] == 0.0 and fr[("flow", "non_qualifying_expenditure")] == 400.0,
          "IP transfer: a new IP company bought its IP — its R&D fraction is nil (Sch 17FC s5(3)(c)), never asked")

    # ---- decision D28: OP and a new IP company both held wholly by a Mainland parent — the IP may move at book value (109号
    #      第三条): no gain for OP, the buyer amortises OP's tax basis; if the treatment fails, a deemed sale at fair value
    cB = Case(roles={OP: RoleFacts(CN, {"vat_general_taxpayer": True}), ULT: RoleFacts(CN, {"managed_from": CN})},
              holds={(ULT, OP): HoldEdge(ULT, OP, 100.0, date(2020, 1, 1), 3000.0)},
              flows={"roy": {"is_equipment_lease": False, "is_aircraft_or_ship_lease": False, "receipt_kind": "NONE"},
                     "iptx": {"amount": 400.0, "ip_kind": "TRADEMARK", "cost_basis": 100.0, "ip_book_value": 100.0,
                              "ip_book_amortization": 40.0, "instrument_used_in_cn": True, "ip_useful_life_years": 10,
                              "price_includes_vat": False}})
    book, book_hk = {IPCO: CN, "payment": False, "ip_transfer": "BOOK"}, {IPCO: HK, "payment": False, "ip_transfer": "BOOK"}
    check(not IP.infeasible(eC, book, cB) and IP.infeasible(eC, book_hk, cB) and IP.infeasible(eC, book, cC),
          "book value (decision D28): offered only between Mainland companies wholly held by the same Mainland parent")
    gB, gM = IP.build(eC, book, cB), IP.build(eC, dict(book, ip_transfer="MARKET"), cB)
    cI = deepcopy(cB)
    cI.flows["iptx"]["price_includes_vat"] = True
    mi = iptx(IP.build(eC, dict(book, ip_transfer="MARKET"), cI), CEILING)
    check(tax(mi, CN, who=OP) == 69.34 and tax(mi, CN, "vat", who=OP) == 22.64,
          "IP sale (decision D29): a VAT-inclusive 400 — OP's VAT 400 x 6/106 = 22.64, and its gain is the net 377.36 less the "
          "basis 100: 25%% x 277.36 = 69.34 (got %s, %s)" % (tax(mi, CN, who=OP), tax(mi, CN, "vat", who=OP)))
    bl, bh, ml = iptx(gB, FLOOR), iptx(gB, CEILING), iptx(gM, FLOOR)
    got = (tax(bl, CN, who=OP), tax(bl, CN, who=IPCO), tax(bh, CN, who=OP), tax(bh, CN, who=IPCO), tax(ml, CN, who=OP), tax(bl, CN, "vat"))
    check(got == (0.0, -2.5, 75.0, -10.0, 75.0, 0.0),
          "book value (decision D28): no gain for OP and the new company amortises OP's basis, 25%% x 100 / 10 = 2.5; if the "
          "treatment fails, 25%% x 300 and 25%% x 400 / 10 (a deemed sale, 公告2015年第40号 第八条) as at market value; the "
          "deemed sale's 6%% VAT on 400 is credited by the buyer (got %s)" % (got,))

    # ---- decision D24: a Singapore IP company's royalty from the Mainland — judged derived from Singapore, charged whether remitted
    #      or not (s10(1)), the Agreement's 10% credited; judged foreign-sourced and not remitted, nothing
    sg_roy = lambda t, b: tax(engine(gs[SG], ctx_t(t), b)[2]["roy"], SG)
    yes_sg = {Need(DISCRETION, "payee.income_sourced_in_sg"): True}
    no_sg = {Need(DISCRETION, "payee.income_sourced_in_sg"): False}
    r1, r0 = sg_roy(yes_sg, FLOOR), sg_roy(no_sg, FLOOR)
    check(r1 == 37.83 and r0 == 0.0, "SG source (decision D24): a royalty derived from a licensing business run in Singapore is charged "
          "on accrual: 17%% x 500 less the Mainland's 10%% of the VAT-net 500 / 1.06 = 37.83; foreign-sourced and kept abroad: 0 "
          "(got %s, %s)" % (r1, r0))
    dl = [d for d in engine(gs[SG], ctx_t({}), CEILING)[2]["iptx"].deadlines]
    check(not any(k == "filing" for k in dl), "SG s45: an IP bought outright is not withheld, so no s45 filing clock (got %s)" % dl)

    # ---- decision D25: interest is a loan service — 6% withheld from a foreign lender, charged to a Mainland lender, never credited;
    #      decision D26: the non-resident's withholding base (and the treaty cap's) is the interest net of the VAT
    def int_items(on, lender_loc, **attrs):
        g = Graph({"OP": Entity("OP", CN, attrs={"vat_general_taxpayer": True}), "ULT": Entity("ULT", SG, attrs={"managed_from": SG}),
                   "L": Entity("L", lender_loc, attrs={"managed_from": lender_loc, "residence_cert": True, "bo_safe_harbour": True,
                                                        "vat_general_taxpayer": True})},
                  [HoldEdge("ULT", "OP", 100.0, date(2020, 1, 1), 1.0), HoldEdge("ULT", "L", 100.0, date(2020, 1, 1), 1.0)],
                  [FlowEdge("i", "OP", "L", INTEREST, 1060.0, on, attrs=dict({"interest_rate": 5.0, "benchmark_rate": 5.0,
                                                                              "receipt_kind": "NONE"}, **attrs))])
        lb = engine(g, ctx_t({Need(DISCRETION, "payee.no_adverse_bo_factors"): True, Need(DISCRETION, "payee.ppt"): False}), CEILING)[2]["i"]
        return tax(lb, CN, "vat"), tax(lb, CN, who="L")
    v_ex, v_in, v_cn = int_items(ON, SG, price_includes_vat=False), int_items(ON, SG, price_includes_vat=True), \
        int_items(ON, CN, price_includes_vat=False)
    v_un = int_items(ON, SG, price_includes_vat=False, unified_borrowing_relending=True)
    check(v_ex == (63.6, 106.0) and v_in == (60.0, 100.0),
          "interest VAT (decision D25, D26): a Singapore lender's 1060 — 6%% withheld = 63.6 and never credited, 10%% withholding on 1060; "
          "a VAT-inclusive price: 60 and the withholding on the net 1000 = 100 (got %s, %s)" % (v_ex, v_in))
    check(v_cn[0] == 63.6 and v_un[0] == 0.0,
          "interest VAT: a Mainland lender pays 6%% on it, no credit for the borrower (63.6); 统借统还 on-lending is exempt "
          "(got %s, %s)" % (v_cn, v_un))
    # decision D29: a Mainland lender's interest at a VAT-inclusive price — 6/106 VAT, and its income is the price net of it:
    # 25% x 1000 = 250 (the borrower's VAT is not creditable: its deduction stays on the 1060 it pays)
    v_ci = int_items(ON, CN, price_includes_vat=True)
    check(v_ci == (60.0, 250.0), "resident's interest (decision D29): VAT-inclusive 1060 — VAT 60 and 25%% on the net 1000 = 250 "
          "(got %s)" % (v_ci,))

    # decision D30: in 2025 the Mainland VAT is not the VAT Law's, and the library keeps current law only — the levy is outside
    # it (never nil), and so is the withholding base that turns on it (公告2013年第9号); a group company bears both here, so
    # the candidate is no plan; with a lender outside the group they are its own, a note
    def int_label(lender_in_group):
        g = Graph({"OP": Entity("OP", CN), "ULT": Entity("ULT", SG, attrs={"managed_from": SG}),
                   "L": Entity("L", SG, attrs={"managed_from": SG, "residence_cert": True, "bo_safe_harbour": True})},
                  [HoldEdge("ULT", "OP", 100.0, date(2020, 1, 1), 1.0)]
                  + ([HoldEdge("ULT", "L", 100.0, date(2020, 1, 1), 1.0)] if lender_in_group else []),
                  [FlowEdge("i", "OP", "L", INTEREST, 1060.0, date(2025, 6, 30),
                            attrs={"interest_rate": 5.0, "benchmark_rate": 5.0, "receipt_kind": "NONE"})])
        labels = engine(g, ctx_t({Need(DISCRETION, "payee.no_adverse_bo_factors"): True, Need(DISCRETION, "payee.ppt"): False}),
                        CEILING)[2]
        return g, labels

    from types import SimpleNamespace
    from .engine import outside_steps
    g_in, lab_in = int_label(True)
    g_out, lab_out = int_label(False)
    st_in, st_out = outside_steps(SimpleNamespace(L_hi=lab_in), g_in), outside_steps(SimpleNamespace(L_hi=lab_out), g_out)
    check(tax(lab_in["i"], CN, "vat") == 0.0 and sorted(lab_in["i"].outside) == [(CN, "income", "L"), (CN, "vat", "L")]
          and sorted(x[5] for x in st_in[0]) == sorted(["income tax", "VAT"]) and st_in[0][0][3:5] == ("增值税法", "2026-01-01")
          and not st_in[1] and not st_out[0] and len(st_out[1]) == 2,
          "before the VAT Law (decision D30): no VAT computed and none assumed — the VAT and the withholding base that turns on it "
          "are outside the library; borne in the group: no plan; borne by an outside lender: a note (got %s, %s, %s)"
          % (sorted(lab_in["i"].outside), st_in, st_out))

    # decision D31: a Hong Kong company the effective-management variant makes a Mainland resident is still established in
    # Hong Kong (82号 第二条 is about income tax) — the interest it receives from its Hong Kong subsidiary bears the
    # Mainland's income tax but no Mainland VAT; an IP it sells to that subsidiary, no Mainland VAT or stamp duty
    from .engine import residence_graph
    gP = Graph({"ULT": Entity("ULT", CN), "H": Entity("H", HK, attrs={"managed_from": CN}), "O": Entity("O", HK)},
               [HoldEdge("ULT", "H", 100.0, date(2020, 1, 1), 1.0), HoldEdge("H", "O", 100.0, date(2020, 1, 1), 1.0)],
               [FlowEdge("i", "O", "H", INTEREST, 1000.0, ON, attrs={"interest_rate": 5.0, "benchmark_rate": 5.0,
                                                                    "receipt_kind": "NONE", "price_includes_vat": False}),
                FlowEdge("x", "O", "H", "IP_TRANSFER", 400.0, ON, attrs={"ip_kind": "TRADEMARK", "cost_basis": 100.0,
                                                                       "price_includes_vat": False, "instrument_used_in_cn": False})])
    labP = engine(residence_graph(gP, {"H"}), ctx_t({}), CEILING)[2]
    levies = [(fid, it.levy, it.cites[0]) for fid, lb in labP.items() for it in lb.items
              if it.jur == CN and it.levy != "income" and abs(it.effective) > 1e-12]
    inc = tax(labP["i"], CN, who="H")
    check(levies == [] and inc == 250.0,
          "effective management (decision D31): a Hong Kong company resident in the Mainland by its management pays the "
          "Mainland's 25%% on its interest (250) but no Mainland VAT, and its IP sale to a Hong Kong company no VAT or stamp "
          "duty — it is established in Hong Kong (got %s, %s)" % (levies, inc))

    # the flow cache keys on the seats too: a share transfer whose target the management test moves to the Mainland is
    # stamped where the target is established — a Hong Kong target's evaluation must never answer for a Singapore one
    from . import engine as E

    def st_levies(tloc):
        g = residence_graph(Graph({"ULT": Entity("ULT", CN), "B": Entity("B", CN), "T": Entity("T", tloc, attrs={"managed_from": CN})},
                                  [HoldEdge("ULT", "T", 100.0, date(2020, 1, 1), 400.0)],
                                  [FlowEdge("s", "B", "ULT", SHARE_TRANSFER, 1000.0, ON, target="T", attrs={"cost_basis": 400.0})]),
                            {"T"})
        return sorted((it.jur, it.cites[0]) for it in engine(g, ctx_t({}), CEILING)[2]["s"].items if it.levy == "stamp")

    E._FLOW_CACHE.clear()
    hk_first, sg_after = st_levies(HK), st_levies(SG)
    E._FLOW_CACHE.clear()
    sg_fresh = st_levies(SG)
    check(sg_after == sg_fresh and any(j == HK for j, _ in hk_first) and any(j == SG for j, _ in sg_fresh)
          and not any(j == HK for j, _ in sg_fresh),
          "flow cache (decision D31): the same share transfer of a Mainland-managed target — Hong Kong stamp duty for a Hong Kong "
          "target, Singapore's for a Singapore one, whatever the process evaluated before (got %s, %s, %s)"
          % (hk_first, sg_after, sg_fresh))
    roy_net = tax(engine(IP.build(eC, {IPCO: HK, "payment": False}, cC), ctx_t({}), FLOOR)[2]["roy"], CN, who=IPCO)
    check(roy_net == 33.02, "royalty (decision D26): the Arrangement's 7%% applies to the royalty net of the VAT, 500 / 1.06: 33.02 "
          "(got %s)" % roy_net)

    # ---- decision D23: the VAT Law from 2026-01-01 — 6% of the sales amount; before it outside the library (decision D30)
    def roy_vat(on, **attrs):
        g = Graph({"OP": Entity("OP", CN, attrs={"vat_general_taxpayer": True}), "ULT": Entity("ULT", SG, attrs={"managed_from": SG}),
                   "S": Entity("S", SG, attrs={"managed_from": SG, "residence_cert": True, "bo_safe_harbour": True})},
                  [HoldEdge("ULT", "OP", 100.0, date(2020, 1, 1), 1.0), HoldEdge("ULT", "S", 100.0, date(2020, 1, 1), 1.0)],
                  [FlowEdge("r", "OP", "S", ROYALTY, 1060.0, on, attrs=dict({"is_equipment_lease": False, "is_aircraft_or_ship_lease": False,
                                                                           "receipt_kind": "NONE"}, **attrs))])
        lb = run(g, CEILING, EX_ANTE)[2]["r"]
        return [(it.cites[0], round(1060.0 * it.effective / 100.0, 2)) for it in lb.items if it.levy == "vat" and it.borne_by == "payee"]
    v0, v1, v2 = roy_vat(date(2025, 12, 31)), roy_vat(date(2026, 1, 1), price_includes_vat=False), roy_vat(date(2026, 1, 1), price_includes_vat=True)
    check(v0 == [] and v1 == [("cn.vat.law.royalty", 63.6)] and v2 == [("cn.vat.law.royalty", 60.0)],
          "VAT Law: on 2025-12-31 no VAT is computed (decision D30: outside the library); from 2026-01-01 6%% of the sales amount — "
          "63.6 on a price without VAT, 60 on one with it (实施条例 第十六条) (got %s, %s, %s)" % (v0, v1, v2))
    _, cD, eD = SCENARIOS["D"]
    g = SERVICES.build(eD, {SERVICER: HK, "payment": False}, cD)
    check(SERVICER + NEW in g.entities and SERVICER not in g.entities and g.entities[SERVICER + NEW].attrs.get("created_by_plan")
          and not g.unmodelled, "services elsewhere: a new servicer takes the service over, no asset moves, no step")

    # ---- decision D21: the case's flow facts describe the parties of its own structure; a company the plan creates gets its
    #      side from the law (headline rate), from its design (not listed, ordinary shares) or from answers of its own
    from .planner import Answers, apply_data
    from .regions import absolute_key
    _, cA, eA = SCENARIOS["A"]
    rel = {x: HOLDING.build(eA, dict(base, **{HOLD: x}), cA) for x in (HK, SG, CN)}
    up2 = {x: next(f for f in g.flows if f.id == "up2") for x, g in rel.items()}
    check(up2[HK].attrs.get("fact_key") is None and up2[HK].attrs.get("foreign_taxed") is True
          and up2[SG].attrs.get("fact_key") == "up2~HOLD_NEW-SG" and "foreign_taxed" not in up2[SG].attrs
          and up2[SG].attrs.get("receipt_kind") == "REMITTED",
          "new company: the client's HOLD keeps its stated up2 facts; HOLD_NEW's side of up2 is not carried (ULT's side is)")
    fx = facts_for(rel[SG], up2[SG])
    check(fx[("flow", "foreign_headline_rate")] == 17.0 and fx[("flow", "listed_market_trade")] is False
          and fx[("flow", "deductible_at_payer")] is False and fx[("_meta", "flow")] == "up2~HOLD_NEW-SG",
          "new company: Singapore's statutory 17% is its headline rate; not listed, its dividend not deductible (design)")
    check(absolute_key("flow.foreign_taxed", up2[SG]) == "flow:up2~HOLD_NEW-SG.foreign_taxed"
          and absolute_key("flow.foreign_taxed", up2[HK]) == "flow:up2.foreign_taxed",
          "new company: a question about its side has its own address")
    ans = Answers()
    ans.data["flow:up2~HOLD_NEW-SG.foreign_taxed"] = False
    c3 = apply_data(cA, ans)
    got = {x: next(f for f in HOLDING.build(eA, dict(base, **{HOLD: x}), c3).flows if f.id == "up2").attrs.get("foreign_taxed")
           for x in (HK, SG, CN)}
    check(got == {HK: True, SG: False, CN: None},
          "new company: an answer about HOLD_NEW in Singapore reaches only that candidate, never the client's own HOLD (got %s)" % got)

    # ---- domestic flows are charged and deducted by the statutes: a 15% high-tech payer and a 25% recipient leave 10% in the
    #      group; a dividend between residents is exempt (EIT art 26(2))
    g = Graph({"OP": Entity("OP", CN, attrs={"cit_rate": 15.0}), "FIN": Entity("FIN", CN), "ULT": Entity("ULT", SG, attrs={"managed_from": SG})},
              [HoldEdge("ULT", "OP", 100.0, date(2020, 1, 1), 1.0), HoldEdge("ULT", "FIN", 100.0, date(2020, 1, 1), 1.0)],
              [FlowEdge("i", "OP", "FIN", INTEREST, 1000.0, ON, attrs={"interest_rate": 5.0, "benchmark_rate": 5.0}),
               FlowEdge("d", "OP", "FIN", DIVIDEND, 1000.0, ON, attrs={"listed_market_trade": False})])
    lo = run(g, FLOOR, EX_ANTE)[2]
    check(abs(lo["i"].tax - 100.0) < 1e-6, "domestic interest: 25%% charged on the recipient, 15%% deducted by the high-tech payer = 100 (got %.2f)" % lo["i"].tax)
    check(lo["d"].tax == 0.0, "domestic dividend between residents: exempt (got %.2f)" % lo["d"].tax)
    # the GST reverse charge costs the unrecoverable share: 60% recoverable -> 9% x 40% x 1000 = 36
    g = Graph({"P": Entity("P", SG, attrs={"managed_from": SG, "gst_input_fully_recoverable": False, "gst_recovery_ratio": 60.0}),
               "U": Entity("U", SG, attrs={"managed_from": SG}), "V": Entity("V", HK, attrs={"managed_from": HK, "residence_cert": True, "fixed_place_in_sg": False})},
              [HoldEdge("U", "P", 100.0, date(2020, 1, 1), 1.0), HoldEdge("U", "V", 100.0, date(2020, 1, 1), 1.0)],
              [FlowEdge("f", "P", "V", SERVICE_FEE, 1000.0, ON, attrs={"service_location": HK, "service_days_12m": 0, "profit_margin": 20})])
    lb = run(g, FLOOR)[2]["f"]
    gst = [round(1000.0 * it.effective / 100.0, 2) for it in lb.items if it.levy == "vat" and it.borne_by == "payer"]
    check(gst == [36.0], "SG GST: 9%% x (1 - 60%%) x 1000 = 36 unrecoverable (got %s)" % gst)

    # ---- recurring years: a two-year event repeats the recurring flows, the exit once
    g = HOLDING.build(replace(EVENT_A, years=2), BASE_A, CASE_A)
    check(sorted(f.id for f in g.flows) == ["exit", "up1", "up1@2027", "up2", "up2@2027"], "years: recurring flows repeat with the year in their id (%s)" % sorted(f.id for f in g.flows))
    b = bounds(g, lambda facts: CaseCtx(facts, {}, EX_ANTE, ADJUSTABLE))
    check(b.lo <= b.hi, "years: two-year bounds hold (%.2f, %.2f)" % (b.lo, b.hi))

    # ---- a group the case declares takes in the companies the plan creates (found on K4-freetech-2024: with members
    #      ULT and OP, a new holding company sold OP outside the objective and the candidate looked tax-free)
    declared = replace(CASE_A, members={ULT, OP}, holds={k: v for k, v in CASE_A.holds.items() if HOLD not in k},
                       roles={k: v for k, v in CASE_A.roles.items() if k != HOLD})
    g = HOLDING.build(EVENT_A, dict(BASE_A, **{HOLD: CN}), declared)
    check(HOLD in g.group() and BUYER not in g.group() and {ULT, OP} <= g.group(),
          "declared members: a holding company the plan creates is the group's, an outside buyer is not (group %s)"
          % sorted(g.group()))

    # ---- decision D33: a Hong Kong company's royalty for IP used in Hong Kong — s14 when its profits arise here (a judgement),
    #      otherwise s15(1)(b) deems it a receipt here and s21A takes 30% of it (100% from an associate)
    def hk_roy(assoc, bound):
        g = Graph({"P": Entity("P", HK, attrs={"managed_from": HK}), "R": Entity("R", HK, attrs={"managed_from": HK, "payee_is_associate": assoc})},
                  [], [FlowEdge("r", "P", "R", ROYALTY, 1000.0, ON, attrs={"ip_used_in_hk": True, "royalty_deductible_in_hk": True,
                                                                         "ip_never_owned_by_hk_business": False})])
        return round(sum(1000.0 * it.effective / 100.0 for it in run(g, bound, EX_ANTE)[2]["r"].items
                         if it.jur == HK and it.levy == "income" and not it.deduction), 2)
    got = [hk_roy(False, FLOOR), hk_roy(True, FLOOR), hk_roy(False, CEILING)]
    check(got == [49.5, 165.0, 165.0], "HK royalty (decision D33): s15(1)(b) with s21A at the floor — 16.5%% x 30%% = 49.5, from an "
          "associate 16.5%% x 100%% = 165; s14 at the ceiling 165 (got %s)" % got)

    # ---- decision D51: losses — a company's taxable income by year where it sits, the losses carried between years
    def gross(labs, jur, who, levy="income"):
        return round(sum(lb.flow.amount * it.effective / 100.0 for lb in labs.values() for it in lb.items
                         if it.jur == jur and it.levy == levy and (lb.flow.payer if it.borne_by == "payer" else lb.flow.payee) == who), 2)
    loan = {"interest_rate": 5.0, "benchmark_rate": 5.0, "price_includes_vat": False}

    def cn_bf(code):
        attrs = {"loss_brought_forward": [[2020, 300.0], [2023, 200.0]], "taxable_income_other": 0.0}
        if code:
            attrs["cn_loss_type"] = code
        return Graph({"C": Entity("C", CN, attrs=attrs), "D": Entity("D", CN), "U": Entity("U", SG, attrs={"managed_from": SG})},
                     [HoldEdge("U", "C", 100.0, date(2020, 1, 1), 1.0)], [FlowEdge("i", "D", "C", INTEREST, 1000.0, ON, attrs=dict(loan))])
    got = [gross(run(cn_bf("100"), FLOOR)[2], CN, "C"), gross(run(cn_bf("200"), FLOOR)[2], CN, "C")]
    lo, hi = run(cn_bf(None), FLOOR), run(cn_bf(None), CEILING)
    check(got == [200.0, 125.0] and gross(lo[2], CN, "C") == 125.0 and gross(hi[2], CN, "C") == 200.0
          and ("cn.loss.carryforward", "entity:C") in hi[1],
          "losses (decision D51): a Mainland company's 2020 loss of 300 is spent by 2025 (EIT art 18: five years); its 2023 loss of 200 "
          "sets off the 1,000 of 2026: 25%% x 800 = 200; a high-tech type (A106000 code 200) carries ten years, the soonest to "
          "expire first: 25%% x 500 = 125; the type not stated: 125 to 200, asked (got %s, %s, %s)"
          % (got, gross(lo[2], CN, "C"), gross(hi[2], CN, "C")))
    gd = lambda **a: Graph({"OP": Entity("OP", CN, attrs=dict({"cit_rate": 15.0}, **a)), "FIN": Entity("FIN", CN, attrs={"taxable_income_other": 0.0}),
                            "ULT": Entity("ULT", SG, attrs={"managed_from": SG})},
                           [HoldEdge("ULT", "OP", 100.0, date(2020, 1, 1), 1.0), HoldEdge("ULT", "FIN", 100.0, date(2020, 1, 1), 1.0)],
                           [FlowEdge("i", "OP", "FIN", INTEREST, 1000.0, ON, attrs={"interest_rate": 5.0, "benchmark_rate": 5.0})])
    ctx_a = lambda facts: CaseCtx(facts, {}, EX_ANTE, ADJUSTABLE)
    grp = ("cn.loss.carryforward", "entity:OP")
    lo = engine(gd(), ctx_a, FLOOR)
    lost = engine(gd(), ctx_a, FLOOR, force={grp: "unfav"})[2]["i"].tax
    stated = engine(gd(taxable_income_other=2000.0), ctx_a, FLOOR, force={grp: "unfav"})
    check(lo[2]["i"].tax == 100.0 and grp in lo[1] and lost == 250.0 and stated[2]["i"].tax == 100.0 and grp not in stated[1],
          "losses: OP deducts the 1,000 it pays at 15%% only against income the case does not show — absorbed at the floor (100 "
          "in the group), not if it has none (250), asked; its other taxable income stated: 100 (got %s, %s, %s)"
          % (lo[2]["i"].tax, lost, stated[2]["i"].tax))
    sgint = {"interest_rate": 5.0, "benchmark_rate": 5.0, "residence_cert": True, "price_includes_vat": False}

    def offset(stated=None):
        attrs = {"taxable_income_other": -100.0}
        if stated is not None:
            attrs["cn_foreign_loss_offset"] = stated
        return Graph({"C": Entity("C", CN, attrs=attrs), "S": Entity("S", SG, attrs={"managed_from": SG, "taxable_income_other": 1000.0}),
                      "U": Entity("U", CN)},
                     [HoldEdge("U", "C", 100.0, date(2020, 1, 1), 1.0), HoldEdge("U", "S", 100.0, date(2020, 1, 1), 1.0)],
                     [FlowEdge("i", "S", "C", INTEREST, 100.0, ON, attrs=dict(sgint))])
    got = [gross(run(offset(st), b, m)[2], CN, "C") for st, b, m in ((None, FLOOR, EX_ANTE), (None, CEILING, EX_ANTE), (None, FLOOR, EX_POST),
                                                                     (None, CEILING, EX_POST), (False, FLOOR, EX_POST), (True, FLOOR, EX_POST))]
    check(got == [0.0, 0.0, 0.0, 8.0, 15.0, 0.0] and ("cn.loss.foreign_offset", "entity:C") in run(offset(), CEILING)[1],
          "losses: a Mainland company with its own loss of 100 and Singapore interest of 100 — offsetting the loss with the foreign "
          "income is the enterprise's choice (A100000 第23行): ex ante it offsets (no Mainland tax, the limit nil); a past "
          "return's choice not stated: 0 to 25 - 17 = 8, asked; not offset: 25 - 10 = 15 (got %s)" % got)
    c5 = Entity("C", CN, attrs={"taxable_income_other": {"2026": -100.0, "2027": 100.0}, "cn_foreign_loss_offset": True, "cn_loss_type": "100"})
    g5 = Graph({"C": c5, "S": Entity("S", SG, attrs={"managed_from": SG, "taxable_income_other": 1000.0}), "U": Entity("U", SG, attrs={"managed_from": SG})},
               [HoldEdge("U", "C", 100.0, date(2020, 1, 1), 1.0), HoldEdge("U", "S", 100.0, date(2020, 1, 1), 1.0)],
               [FlowEdge("i1", "S", "C", INTEREST, 100.0, date(2026, 6, 30), attrs=dict(sgint)),
                FlowEdge("i2", "S", "C", INTEREST, 100.0, date(2027, 6, 30), attrs=dict(sgint))])
    l5 = run(g5, FLOOR)[2]
    i1, i2 = ([it for it in l5[k].items if it.jur == CN and it.levy == "income" and not it.deduction][0] for k in ("i1", "i2"))
    got = (round(i1.base_share, 4), round(i1.effective, 2), round(i2.credit, 2), round(i2.effective, 2))
    check(got == (0.0, 25.0, 20.0, 5.0),
          "losses (操作指南 ¶27, 示例八): the 2026 interest offsets the domestic loss — its limit nil, the 10 withheld carries "
          "forward; the loss it took is the 2027 domestic income's no more: 25 there; in 2027 the credit 10 + 10 = 20 against "
          "25: 5 (got %s)" % (got,))
    sale = FlowEdge("sale", "B", "U", SHARE_TRANSFER, 5000.0, date(2026, 1, 15), target="O", attrs={"cost_basis": 1000.0})
    hkl = lease(owner=HK, loc=HK)
    hkl.entities["O"].attrs.update(loss_brought_forward=[[2010, 300.0]], taxable_income_other=0.0)
    hks = lease(owner=HK, loc=HK)
    hks.entities["O"].attrs.update(loss_brought_forward=[[2010, 300.0]], taxable_income_other=0.0)
    hks.entities["B"] = Entity("B", HK, attrs={"managed_from": HK})
    hks.flows.append(sale)
    lessor = lambda g, bound, jur: round(sum(lb.flow.amount * it.effective / 100.0 for lb in [run(g, bound)[2]["rent"]] for it in lb.items
                                             if it.levy == "income" and it.jur == jur and it.borne_by == "payee"), 2)
    got = [lessor(hkl, FLOOR, HK), lessor(hkl, CEILING, HK), lessor(hks, FLOOR, HK), lessor(hks, CEILING, HK)]
    check(got == [16.5, 16.5, 16.5, 66.0] and ("hk.loss.change", "entity:O") in run(hks, CEILING)[1],
          "losses: a Hong Kong lessor's 2010 loss of 300 carries without limit (s19C(4)): 16.5%% x (400 - 300) = 16.5; its "
          "shares sold before the rent, s61B is the Commissioner's view — 16.5 to 66 (got %s)" % got)
    from .engine import p2_tax
    from .params import Params
    check(round(p2_tax(run(hkl, FLOOR)[2], hkl, "O", 2026, Params()), 2) == 61.5,
          "losses (GloBE Art 4.4.1): the loss used carries deferred tax at 15%%, so the covered taxes are 16.5 + 49.5 x 15/16.5 = 61.5")
    sgl = lambda **a: lease(owner=SG, loc=SG, currency="SGD", annual_value=900.0)
    s1, s2 = sgl(), sgl()
    s1.entities["O"].attrs.update(loss_brought_forward=[[2024, 300.0]], taxable_income_other=0.0, sg_loss_shareholders_same=True)
    s2.entities["O"].attrs.update(loss_brought_forward=[[2024, 300.0]], taxable_income_other=0.0)
    got = [lessor(s1, FLOOR, SG), lessor(s1, CEILING, SG), lessor(s2, FLOOR, SG), lessor(s2, CEILING, SG)]
    check(got == [17.0, 17.0, 17.0, 68.0] and ("sg.loss.continuity", "entity:O") in run(s2, CEILING)[1],
          "losses: a Singapore lessor's 2024 loss of 300 sets off its rent profit, 17%% x (400 - 300) = 17, when its shareholders "
          "are substantially the same (s37(12), (14)); not stated: 17 to 68, asked (got %s)" % got)

    def relief(parent, mode):
        ents = {"A": Entity("A", SG, attrs={"managed_from": SG, "taxable_income_other": 0.0}),
                "Bc": Entity("Bc", SG, attrs={"managed_from": SG, "taxable_income_other": 5000.0}),
                "P": Entity("P", parent, attrs={"managed_from": parent}), "L": Entity("L", SG, attrs={"managed_from": SG})}
        g = Graph(ents, [HoldEdge("P", "A", 100.0, date(2015, 1, 1), 1.0), HoldEdge("P", "Bc", 100.0, date(2015, 1, 1), 1.0)],
                  [FlowEdge("i", "A", "L", INTEREST, 1000.0, ON, attrs={"interest_rate": 5.0, "benchmark_rate": 5.0})])
        r = run(g, FLOOR, mode)
        return gross(r[2], SG, "A"), ("sg.loss.group_relief", "entity:A") in r[1]
    got = [relief(SG, EX_ANTE), relief(SG, EX_POST), relief(HK, EX_ANTE)]
    check(got == [(-170.0, False), (-170.0, True), (0.0, False)],
          "losses: a Singapore company's interest of 1,000 with no income of its own — transferred to its sister with income "
          "(s37B: 75%% held by a third Singapore company; both elect when it saves): 17%% x 1,000 = 170 saved; a past year's "
          "election not stated: asked; under a Hong Kong parent no group (s37B(3)(b)): carried forward, nothing in the "
          "modelled year (got %s)" % got)

    out.write("%d checks, %d failures\n" % (n, bad))
    out.flush()
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
