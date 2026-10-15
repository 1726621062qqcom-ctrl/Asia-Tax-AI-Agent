"""K2 官方算例 (案例采集.md §1, 测试系统.md §3.1): the official worked examples as labels.

    python -m tax_graph.check_examples          (conda env "pytorch")

official/labels/k2_examples.csv lists every worked example of the inventoried guides with a status:
    run           an engine check below reproduces the outcome the example states
    out_of_model  the engine does not model what the example turns on (the reason is in the note)
    superseded    the rule the example applies has changed since (the current rule is in the note)
    inconsistent  the example contradicts itself (the clash is in the note)
    pending       modelled, the check not yet built
official/labels/k2_quotes.csv holds the example's words: every quote must stand in the cited clause (whitespace aside).
A mismatch is traced to a clause, a missing rule or a 口径 — never fixed by moving a parameter (测试系统.md §3.1)."""
import csv
import io
import json
import re
import sys
from datetime import date
from pathlib import Path

from .data.domain import ADJUSTABLE
from .engine import EX_ANTE, EX_POST, CaseCtx, cn_tiers, engine
from .facts import facts_for, hk_associated as associated_15oc, params, sg_same_group
from .model import CN, HK, SG, DIVIDEND, INTEREST, SHARE_TRANSFER, Entity, FlowEdge, Graph, HoldEdge
from .rules.procedure_hk import nexus_taxable_share
from .rules.tri import CEILING, DISCRETION, FLOOR, Need

ROOT = Path(__file__).resolve().parents[1]
LABELS = ROOT / "official" / "labels" / "k2_examples.csv"
QUOTES = ROOT / "official" / "labels" / "k2_quotes.csv"
CLAUSES = ROOT / "official" / "clauses.csv"
STATUSES = ("run", "out_of_model", "superseded", "inconsistent", "pending")
NO_RELIEF = {"p2_qualified_cbcr_hk": False, "p2_qualified_cbcr_sg": False, "p2_dm_avg_revenue_eur_hk": 1e9, "p2_dm_avg_income_eur_hk": 1e9,
             "p2_dm_avg_revenue_eur_sg": 1e9, "p2_dm_avg_income_eur_sg": 1e9}


def run(g, bound, ticks=None, mode=EX_POST):
    return engine(g, lambda facts: CaseCtx(facts, dict(ticks or {}), mode, ADJUSTABLE), bound)[2]


def tax(labels, fid, jur, levy="income"):
    lb = labels.get(fid)
    if lb is None:
        return 0.0
    return round(sum(lb.flow.amount * it.effective / 100.0 for it in lb.items if it.jur == jur and it.levy == levy and not it.deferred), 2)


# ---- 财税〔2009〕125号 第六条 / 84号 第二条 with 操作指南 第21段: who stands behind a resident's foreign dividends (口径 D05)
def cn_tiers_check(inputs):
    ents = {"A": Entity("A", CN)}
    for k, loc in inputs["foreign"].items():
        ents[k] = Entity(k, loc)
    holds = [HoldEdge(h, d, float(r), date(2020, 1, 1), 1.0) for h, d, r in inputs["holds"]]
    tiers = cn_tiers(Graph(ents, holds, []), "A", params())
    got = {k: v for k, v in tiers.items() if k not in inputs.get("not_compared", [])}
    return got


# ---- HK FSIE (Cap 112 Part 4, Sch 55)
HK_PAYEE = {"is_mne_member": True, "managed_from": HK, "residence_cert": True, "hk_resident_or_pe": True, "pure_equity_holding": True,
            "registration_filing_compliant": True}


def ticks_of(spec):
    """{"payee.adequate_substance": false, ...} -> the engine's answers to those judgements."""
    return {Need(DISCRETION, k): bool(v) for k, v in (spec or {}).items()}


def hk_inbound(income, amount, on, accrued_on=None, flow=None, holding_since=date(2020, 1, 1), cost=0.0):
    """An item from a Mainland company (the examples' Jurisdiction F) to an HK company holding it wholly since 2020; a
    share transfer's buyer is a Singapore company. The examples give the gain, not price and cost: the cost is nil."""
    attrs = dict({"foreign_headline_rate": 25, "foreign_taxed": True, "deductible_at_payer": False}, **(flow or {}))
    if accrued_on:
        attrs["accrued_on"] = date.fromisoformat(accrued_on)
    ents = {"HKCO": Entity("HKCO", HK, attrs=dict(HK_PAYEE)), "F": Entity("F", CN, attrs={"managed_from": CN})}
    holds = [HoldEdge("HKCO", "F", 100.0, holding_since, cost)]
    if income == SHARE_TRANSFER:
        ents["X"] = Entity("X", SG, attrs={"managed_from": SG})
        f = FlowEdge("f", "X", "HKCO", SHARE_TRANSFER, amount, date.fromisoformat(on), target="F", attrs=attrs)
    else:
        f = FlowEdge("f", "F", "HKCO", income, amount, date.fromisoformat(on), attrs=attrs)
    return Graph(ents, holds, [f])


def hk_fsie_cases(inputs):
    """Each case: whether Hong Kong taxes the item at the ceiling — every judgement unfavourable unless the case answers it."""
    out = {}
    for name, c in inputs["cases"].items():
        g = hk_inbound(c.get("income", DIVIDEND), float(c["amount"]), c["on"], c.get("accrued_on"), c.get("flow"))
        out[name] = "charged" if tax(run(g, CEILING, ticks_of(c.get("ticks"))), "f", HK) > 0 else "not charged"
    return out


def hk_associated(inputs):
    """s15OC (口径 D44): the association the intra-group transfer relief reads (facts.hk_associated)."""
    ents = {k: Entity(k, HK, attrs={"managed_from": HK}) for k in inputs["entities"]}
    g = Graph(ents, [HoldEdge(h, d, float(r), date(2020, 1, 1), 1.0) for h, d, r in inputs["holds"]], [])
    return {"%s-%s" % (a, b): "associated" if associated_15oc(g, a, b, params()) else "not associated" for a, b in inputs["pairs"]}


def hk_intragroup(inputs):
    """s15OA (口径 D44). S held ratio% of the Mainland F (the examples' Jurisdiction F) since seller_since at seller_cost
    and sold it to A, its associate (both wholly held by U), on transfer_on for transfer_price, claiming the relief; A
    sells it to an outside buyer on resale_on for resale_price. Reports whether the relief applied, A's gain for the
    FSIE regime (the base of its Hong Kong item) and whether the participation exemption holds — substance answered
    no and the main-purpose test answered yes, so that only the participation requirements decide."""
    d = date.fromisoformat
    hk = dict(HK_PAYEE, fixed_place_in_cn=False, bo_safe_harbour=True, substance_ruled_adequate=False)   # no ruling either
    ents = {k: Entity(k, HK, attrs=dict(hk)) for k in ("U", "S", "A")}
    ents.update(F=Entity("F", CN, attrs={"managed_from": CN}), X=Entity("X", SG, attrs={"managed_from": SG}))
    ratio, price = float(inputs["ratio"]), float(inputs["transfer_price"])
    holds = [HoldEdge("U", "S", 100.0, date(2020, 1, 1), 1.0), HoldEdge("U", "A", 100.0, date(2020, 1, 1), 1.0),
             HoldEdge("S", "F", ratio, d(inputs["seller_since"]), float(inputs["seller_cost"])),
             HoldEdge("A", "F", ratio, d(inputs["transfer_on"]), price)]
    gain = {"receipt_kind": "REMITTED", "foreign_headline_rate": 25, "deductible_at_payer": False, "listed_market_trade": False,
            "immovable_ratio": 0, "underlying_profits_taxed": False}
    flows = [FlowEdge("r", "A", "S", SHARE_TRANSFER, price, d(inputs["transfer_on"]), target="F",
                      attrs=dict(gain, acquirer_chargeable_in_hk=True, clawback_event_within_2y=False)),
             FlowEdge("g", "X", "A", SHARE_TRANSFER, float(inputs["resale_price"]), d(inputs["resale_on"]), target="F",
                      attrs=dict(gain, **inputs.get("resale", {})))]
    g = Graph(ents, holds, flows)
    ticks = ticks_of({"payee.adequate_substance": False, "payee.no_main_purpose_of_tax_benefit": True})
    hi, lo = run(g, CEILING, ticks), run(g, FLOOR, ticks)
    out = {"relief": "applied" if "hk.fsie.intragroup_relief" in hi["r"].applied else "not applied",
           "participation": "met" if tax(lo, "g", HK) == 0 else "not met"}
    base = [it.base_share for it in hi["g"].items if it.jur == HK and it.levy == "income"]
    if "gain" in inputs.get("report", []) and base:
        out["gain"] = round(base[0] * float(inputs["resale_price"]), 2)
    return out


def cn_dividend_year(inputs):
    """实施条例 第十七条 (口径 D50): the Mainland year a dividend falls in — that of the distribution decision, whenever paid."""
    from .engine import tax_year
    f = FlowEdge("d", "F", "P", DIVIDEND, 2000.0, date.fromisoformat(inputs["on"]),
                 attrs={"declared_on": date.fromisoformat(inputs["declared_on"])})
    return {"mainland_year": tax_year(f, CN)}


def hk_substance_year(inputs):
    """Cap 112 s15K(2) (口径 D50): economic substance for the year the dividend accrues. A dividend from the Mainland F
    (the participation exemption out of reach: the profits behind it untaxed), the substance found year by year; each
    case whether Hong Kong charges it at the ceiling."""
    out = {}
    for name, c in inputs["cases"].items():
        g = hk_inbound(DIVIDEND, 10.0, c["on"], c.get("accrued_on"),
                       {"foreign_taxed": False, "underlying_profits_taxed": False, "receipt_kind": "REMITTED"})
        g.entities["HKCO"].attrs["substance_ruled_adequate"] = dict(inputs["years"])
        out[name] = "charged" if tax(run(g, CEILING), "f", HK) > 0 else "not charged"
    return out


def cn_branch_year(inputs):
    """财税〔2009〕125号 第十一条 (口径 D47): the Mainland year a foreign branch's year falls in — the year in which it ends
    (engine.branch_flows places the branch's profit on that day)."""
    from .engine import branch_flows
    end = date.fromisoformat(inputs["period_end"])
    g = Graph({"H": Entity("H", CN, attrs={"managed_from": CN, "branch_profit_hk": 100.0, "branch_period_end_hk": end})}, [], [])
    return {"mainland_year": [f for f in branch_flows(g).flows if f.income == "BRANCH_PROFIT"][0].on.year}


def sg_relevant_group(inputs):
    """s10L(5)(b) (口径 D47): whether the seller belongs to a relevant group — a single company with a foreign branch is no
    group (e-Tax Guide para 5.5); two Singapore companies, one with a foreign branch, are one (5.6)."""
    ents = {k: Entity(k, SG, attrs={"fixed_place_in_cn": k in inputs.get("branch_in_cn", ()), "fixed_place_in_hk": False})
            for k in inputs["entities"]}
    ents["X"] = Entity("X", HK, attrs={"managed_from": HK})
    g = Graph(ents, [HoldEdge(h, d, float(r), date(2020, 1, 1), 1.0) for h, d, r in inputs.get("holds", [])],
              [FlowEdge("i", "X", inputs["seller"], INTEREST, 100.0, date(2026, 6, 1), attrs={"receipt_kind": "REMITTED"})])
    return {"relevant_group": "yes" if facts_for(g, g.flows[0])[("payee", "is_relevant_group_entity")] else "no"}


def sg_s13w_group(inputs):
    """s13W(1C)(b), (1D) (口径 D45): whether two companies are in the same group (Annex A2-1); an entity typed LLP (the
    examples' B LLP) is no company and a chain does not pass it."""
    ents = {k: Entity(k, SG, type=t) for k, t in inputs["entities"].items()}
    g = Graph(ents, [HoldEdge(h, d, float(r), date(2020, 1, 1), 1.0) for h, d, r in inputs["holds"]], [])
    return {"%s-%s" % (a, b): "same group" if sg_same_group(g, a, b, params()) else "not same group" for a, b in inputs["pairs"]}


class _Asked:
    def missing(self, *keys):
        return False


def hk_nexus(inputs):
    P = params()
    out = []
    for qe, ne in inputs["cumulative"]:
        facts = {("flow", "qualifying_rd_expenditure"): float(qe), ("flow", "non_qualifying_expenditure"): float(ne)}
        out.append(round(1.0 - nexus_taxable_share(facts, P, _Asked()), 2))
    return out


# ---- SG s13(8)-(9) headline rate; s10L commencement
SG_PAYEE = {"managed_from": SG, "residence_cert": True, "is_relevant_group_entity": True, "is_mne_member": True}


def sg_inbound(income, amount, on, flow, target_loc=CN, cost=0.0):
    """An item from a Mainland company to a Singapore company of a relevant group holding it wholly since 2015; a share
    transfer's buyer is an HK company, its cost nil (the example states the gain)."""
    ents = {"SGCO": Entity("SGCO", SG, attrs=dict(SG_PAYEE)), "F": Entity("F", target_loc, attrs={"managed_from": target_loc})}
    holds = [HoldEdge("SGCO", "F", 100.0, date(2015, 1, 1), cost)]
    if income == SHARE_TRANSFER:
        ents["X"] = Entity("X", HK, attrs={"managed_from": HK})
        f = FlowEdge("f", "X", "SGCO", SHARE_TRANSFER, amount, date.fromisoformat(on), target="F", attrs=dict(flow))
    else:
        f = FlowEdge("f", "F", "SGCO", income, amount, date.fromisoformat(on), attrs=dict(flow))
    return Graph(ents, holds, [f])


def sg_cases(inputs):
    """Each case: the Singapore tax on the item at the stated bound — charged or not."""
    out = {}
    for name, c in inputs["cases"].items():
        g = sg_inbound(c.get("income", DIVIDEND), float(c["amount"]), c["on"], c["flow"])
        bound = FLOOR if c.get("bound", "floor") == "floor" else CEILING
        out[name] = "charged" if tax(run(g, bound, ticks_of(c.get("ticks"))), "f", SG) > 0 else "not charged"
    return out


# ---- Pillar Two (HK Cap 112 Part 4AA and Sch 61-63 construed per the OECD GloBE rules guidance, s26AF; SG MMT Act)
def p2_topups(inputs):
    """The top-up tax per constituent entity, for each jurisdiction the example is run in (2026, no safe harbour)."""
    out = {}
    for loc in inputs["jurisdictions"]:
        extra = inputs.get("attrs", {}).get(loc, {})
        ents = {k: Entity(k, loc, attrs=dict({**NO_RELIEF, "group_revenue_eur": 1e9, "sbie": 0.0, "managed_from": loc,
                                               "globe_income": float(inc), "covered_taxes_other": float(t)}, **extra))
                for k, inc, t in inputs["entities"]}
        ents["U"] = Entity("U", CN)
        first = inputs["entities"][0][0]
        g = Graph(ents, [HoldEdge("U", k, 100.0, date(2020, 1, 1), 100.0) for k, _, _ in inputs["entities"]],
                  [FlowEdge("d", first, "U", DIVIDEND, 100.0, date(2026, 3, 31), attrs={"receipt_kind": "NONE"})])
        lo = run(g, FLOOR)
        out[loc] = {k: round(lo["p2:%s" % k].tax, 2) if "p2:%s" % k in lo else 0.0 for k, _, _ in inputs["entities"]}
    return out


def p2_params(inputs):
    """The rate tables the examples quote, read from params.csv (only rates in force: 口径 D30)."""
    P = params()
    out = {}
    for key, year in inputs["lookups"]:
        v = P[key]
        if year is not None:
            table = dict(x.split(":") for x in str(v).split(";"))
            v = table.get(str(year))
        out["%s@%s" % (key, year) if year is not None else key] = float(v)
    return out


CHECKS = {"cn_tiers": cn_tiers_check, "hk_fsie_cases": hk_fsie_cases, "hk_associated": hk_associated, "hk_nexus": hk_nexus,
          "hk_intragroup": hk_intragroup, "sg_s13w_group": sg_s13w_group,
          "cn_branch_year": cn_branch_year, "sg_relevant_group": sg_relevant_group,
          "cn_dividend_year": cn_dividend_year, "hk_substance_year": hk_substance_year,
          "sg_cases": sg_cases, "p2_topups": p2_topups, "p2_params": p2_params}


def loose(s):
    return re.sub(r"\s+", "", s or "")


def clause_texts(cites):
    csv.field_size_limit(10 ** 9)
    out = {}
    with open(CLAUSES, encoding="utf-8-sig", newline="") as fh:
        for r in csv.DictReader(fh):
            if r["cite_id"] in cites:
                out[r["cite_id"]] = loose(r["text"])
    return out


def same(got, want):
    if isinstance(want, float) or isinstance(got, float):
        return abs(float(got) - float(want)) < 0.005
    if isinstance(want, dict):
        return isinstance(got, dict) and set(got) == set(want) and all(same(got[k], want[k]) for k in want)
    if isinstance(want, list):
        return isinstance(got, list) and len(got) == len(want) and all(same(a, b) for a, b in zip(got, want))
    return got == want


def main(argv=()):
    out = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    with open(LABELS, encoding="utf-8-sig", newline="") as fh:
        labels = list(csv.DictReader(fh))
    with open(QUOTES, encoding="utf-8-sig", newline="") as fh:
        quotes = list(csv.DictReader(fh))
    bad = 0
    ids = {r["label_id"] for r in labels}
    texts = clause_texts({q["cite_id"] for q in quotes})
    for q in quotes:
        if q["label_id"] not in ids:
            bad += 1
            out.write("FAIL quote of unknown label %s\n" % q["label_id"])
        elif loose(q["quote"]) not in texts.get(q["cite_id"], ""):
            bad += 1
            out.write("FAIL %s: quote not in %s: %s\n" % (q["label_id"], q["cite_id"], q["quote"][:80]))
    quoted = {q["label_id"] for q in quotes}
    counts = {s: 0 for s in STATUSES}
    for r in labels:
        st = r["status"]
        if st not in STATUSES:
            bad += 1
            out.write("FAIL %s: status %r\n" % (r["label_id"], st))
            continue
        counts[st] += 1
        if r["label_id"] not in quoted:
            bad += 1
            out.write("FAIL %s: no quote\n" % r["label_id"])
        if st != "run":
            if not r["note"].strip():
                bad += 1
                out.write("FAIL %s: %s without a reason\n" % (r["label_id"], st))
            continue
        fn = CHECKS.get(r["check"])
        if fn is None:
            bad += 1
            out.write("FAIL %s: no check %r\n" % (r["label_id"], r["check"]))
            continue
        want = json.loads(r["expected"])
        try:
            got = fn(json.loads(r["inputs"]))
        except Exception as e:                                   # a check that cannot run is a failure, not a skip
            got = "error: %s: %s" % (type(e).__name__, e)
        ok = same(got, want)
        bad += 0 if ok else 1
        out.write("%-4s %s %s — %s%s\n" % ("ok" if ok else "FAIL", r["label_id"], r["example"], r["check"],
                                           "" if ok else " (want %s, got %s)" % (json.dumps(want, ensure_ascii=False), got)))
    out.write("%d labels (%s), %d quotes; %d failures\n" % (len(labels), ", ".join("%s %d" % kv for kv in counts.items()), len(quotes), bad))
    out.flush()
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
