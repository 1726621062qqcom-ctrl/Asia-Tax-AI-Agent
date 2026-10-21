"""The income-only scope (scope.py): the table against the library, and the gates that use it.

    python -m tax_graph.check_income_only          (conda env "pytorch")
"""
import io
import sys
from datetime import date

from . import scope
from .data.domain import ADJUSTABLE
from .engine import EX_ANTE, CaseCtx, engine
from .ex_ante import ex_ante
from .flow_tax import RULES
from .model import CN, DIVIDEND, HK, INTEREST, SERVICE_FEE, SG, SHARE_TRANSFER, Entity, FlowEdge, Graph, HoldEdge
from .rules.compile import INCOMES, JURISDICTIONS
from .rules.tri import FLOOR

ON = date(2026, 6, 30)
NON_INCOME = {"STAMP": "stamp", "VAT": "vat", "CUSTOMS": "customs", "SURCHARGE": "vat", "LAT": "lat", "DEED": "deed", "PROPERTY_TAX": "property"}


def graph(income, payer_loc, payee_loc, target_loc=None, attrs=None, payee_type="COMPANY"):
    ents = {"P": Entity("P", payer_loc), "R": Entity("R", payee_loc, type=payee_type)}
    holds = [HoldEdge("R", "P", 100.0, date(2020, 1, 1), 100.0)]
    target = None
    if target_loc:
        ents["T"] = Entity("T", target_loc)
        holds.append(HoldEdge("R", "T", 100.0, date(2020, 1, 1), 100.0))
        target = "T"
    return Graph(ents, holds, [FlowEdge("f", "P", "R", income, 1000.0, ON, target=target, attrs=dict(attrs or {}))])


def main():
    out = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    bad = n = 0

    def check(ok, text):
        nonlocal bad, n
        bad += 0 if ok else 1
        n += 1
        out.write("%-4s %s\n" % ("ok" if ok else "FAIL", text))

    # 1. every (kind, jurisdiction) cell is declared: a levy with its provision, or a reason for none
    rows = scope.table()
    check(set(scope.KINDS) == set(INCOMES), "the scope table covers the library's income kinds")
    check(all(r["declared"] for r in rows), "every kind x jurisdiction cell is declared (%d cells)" % len(rows))
    # 2. the library's non-income rules all fall on cells the table names (the table is written from the law, not the library)
    gaps = []
    for r in RULES:
        if r.effect.value not in NON_INCOME:
            continue
        kinds = tuple(INCOMES) if r.scope.income == "ALL" else (r.scope.income if isinstance(r.scope.income, tuple) else (r.scope.income,))
        for k in kinds:
            if r.scope.income == "ALL":
                continue                                   # the surcharges ride on VAT: present wherever VAT is
            levies = {"vat" if l.levy == "gst" else l.levy for l in scope.OTHER_LEVIES.get((k, r.scope.taxing), ())}   # Effect.VAT covers GST
            if NON_INCOME[r.effect.value] not in levies:
                gaps.append("%s on %s in %s" % (r.id, k, r.scope.taxing))
    check(not gaps, "every library rule for another levy sits on a cell the table names (%s)" % (", ".join(gaps) or "none missing"))
    # 3. admitted and refused graphs
    check(not scope.outside(graph(DIVIDEND, CN, HK)), "a cash dividend from the Mainland to Hong Kong is admitted")
    check(not scope.outside(graph(INTEREST, HK, SG)), "interest between Hong Kong and Singapore is admitted")
    check([x.levy for x in scope.outside(graph(INTEREST, CN, HK))] == ["vat"], "interest paid from the Mainland attracts VAT: refused")
    check(scope.outside(graph(INTEREST, HK, CN, payee_type="BANK_FI")) and any(x.levy == "stamp" for x in scope.outside(graph(INTEREST, HK, CN, payee_type="BANK_FI"))),
          "a loan from a Mainland bank adds the loan-contract stamp duty")
    check([x.levy for x in scope.outside(graph(SERVICE_FEE, HK, HK))] == ["paused"], "a service fee is a paused kind even between Hong Kong companies")
    check({j for j, _ in scope.levies_of(graph(SHARE_TRANSFER, HK, HK, target_loc=CN).flows[0], graph(SHARE_TRANSFER, HK, HK, target_loc=CN))} == {HK, CN}, "a share transfer touches the target's jurisdiction too")
    check([x.levy for x in scope.outside(graph(DIVIDEND, CN, HK, attrs={"capitalised": True}))] == ["stamp"], "a capitalised Mainland dividend attracts the account-book stamp duty")
    # 4. the engine emits income items only on an admitted graph
    g = graph(DIVIDEND, CN, HK)
    labels = engine(g, lambda facts: CaseCtx(facts, {}, EX_ANTE, ADJUSTABLE), FLOOR)[2]
    levies = {it.levy for lb in labels.values() for it in lb.items if it.effective}
    check(levies <= {"income"}, "an admitted graph yields income-tax items only (got %s)" % sorted(levies))
    # 5. the message names the flow, the levy and the provision; the switch turns it off
    try:
        scope.check(graph(SERVICE_FEE, CN, SG))
        msg = ""
    except scope.OutOfScope as e:
        msg = str(e)
    check("f (service fee" in msg and "paused" in msg, "the refusal names the flow and says the kind is paused")
    try:
        scope.check(graph(INTEREST, CN, SG))
        msg = ""
    except scope.OutOfScope as e:
        msg = str(e)
    check("VAT in Mainland China" in msg and "增值税法" in msg, "the refusal names the levy and the provision")
    check(scope.check(graph(SERVICE_FEE, CN, SG), scope=scope.ALL) is not None, "scope=ALL admits everything (the whole library)")
    # 6. the planner leaves out the structures that would add a levy and says so
    from .cases import CASE_E, EVENT_E
    from .planner import Answers, plan
    from .scenarios import HOLDING
    o = plan(HOLDING, EVENT_E, CASE_E, Answers())
    left = [e for e in o.evaluations if e.out_of_scope]
    check(left and all("stamp" in w.levy or "vat" in w.levy for e in left for w in e.out_of_scope), "holding: candidates that insert a holding company (a share transfer) or lend (Mainland VAT) are left out")
    check(o.scope.get("excluded") and len(o.scope["excluded"]) == len(left), "the outcome lists the structures left out with their reasons")
    res = ex_ante(HOLDING, EVENT_E, CASE_E)
    check(res.out_of_scope and all(not scope.outside(r.graph) for r in res.table), "the candidate table holds admitted structures only")
    out.write("%d checks, %d failures\n" % (n, bad))
    out.flush()
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
