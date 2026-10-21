"""Offline contracts for actionable workpacks, without a model or network."""
import copy
from .execution import TRANSACTIONS, build_execution, for_strategy, render_execution


def main():
    count = 0

    def check(ok, description):
        nonlocal count
        assert ok, description
        count += 1
        print("ok", description)

    context = {"template": "recorded", "currency": "SGD", "event": {"as_at": "2026-10-15"},
               "names": {"A": "Client Seller", "B": "External Buyer"}, "members": ["A"],
               "roles": {"A": {"loc": "SG", "attrs": {}}, "B": {"loc": "CN", "attrs": {}}}}
    base = {"structure": {"entities": [("A", "SG", "existing"), ("B", "CN", "outside the group")],
                          "flows": [("fee", "SERVICE_FEE", "B", "A", 500000, "2026-09-15")]},
            "regions": [{"jurisdictions": ["CN"], "actions": [],
                         "guaranteed": [("fee", "CN", "income", "A", 50000, ["cn.wht.service_as_royalty"], True)],
                         "best": [], "conditions": [("A.service_fee_is_royalty_for_know_how", "Service classification", "cn.wht.service_as_royalty", 1000),
                                                     ("A.ppt", "Treaty anti-abuse condition", "cn-sg.ppt@cn", 0),
                                                     ("B.reasonable_service_fee", "Counterparty deduction", "cn.deduct.service", 0)],
                         "deadlines": [("fee", "remit", "2026-09-22", "")]}],
            "data_used": [("flow:fee.service_onshore_share", 30, "Timesheets"), ("flow:fee.profit_margin", "unknown", "")],
            "claims": [], "unmodelled": [], "guaranteed": 50000, "best": 10000}
    before = copy.deepcopy(base), copy.deepcopy(context)
    e = build_execution(base, context, 1)
    check((base, context) == before, "workpack generation never changes saved facts or computed tax")
    check(e["status"] == "conditional" and len(e["decision_paths"]) == 2, "unknown classification and treaty treatment stay conditional; outside deductions are excluded")
    check("Alternative structures were not compared" in e["comparison"], "recorded transactions do not claim structural optimisation")
    check(any(s["status"] == "check_now" and s["due"] == "2026-09-22" for s in e["steps"]), "a passed engine clock triggers verification, not a fabricated missed-filing finding")
    start = next(s for s in e["steps"] if s["id"] == e["next_action"])
    check(start["kind"] == "deadline" and not start["depends_on"], "urgent verification can start without waiting for other work items")
    check(e["known_facts"] == [{"flow": "fee", "label": "Service performed in the Mainland", "value": 30, "unit": "%"}], "supported answers populate facts; unknown values are not evidence")
    check(any(s["kind"] == "missing_evidence" for s in e["steps"]), "explicitly unknown answers create evidence tasks rather than disappearing")
    check(len(e["treatment_paths"]) == 2 and "recomputed" in e["decision_paths"][0]["if_supported"], "conservative and conditional paths never equate a positive finding with favourable tax treatment")
    prior = set()
    for s in e["steps"]:
        check(set(s["depends_on"]) <= prior and s["owner"] and s["documents"] and s["completion"], "step %s has an owner, evidence, completion criterion and preceding dependencies" % s["id"])
        prior.add(s["id"])
    check("SGD" in e["steps"][0]["action"] and "Client Seller" in e["steps"][0]["owner"], "amount currency and actual party names survive into the plan")
    check("## Implementation plan" in render_execution(e) and "Conditional decisions" in render_execution(e), "downloadable workpacks include ordered steps and conditional decisions")
    st = for_strategy(e, {"id": 2, "guaranteed": 50000, "assumes_favourable": ["A.ppt"], "labels": {"A.ppt": "principal purpose test"}, "fallback": 3, "fallback_guaranteed": 60000})
    check(len(st["treatment_paths"]) == 1 and "It can fall to" not in st["recommended_course"] and st["strategy"]["id"] == 2 and "strategy #3" in render_execution(st),
          "a strategy's workpack keeps one path, no conditional sentence, and names its fallback")
    check(len(for_strategy({k: v for k, v in e.items() if k != "course_parts"}, {"id": 1, "guaranteed": 1, "assumes_favourable": [], "labels": {}, "fallback": None, "fallback_guaranteed": None})["treatment_paths"]) == 1,
          "a workpack regenerated without course parts is still reduced for a strategy")
    kinds = set()
    for income in TRANSACTIONS:
        p = copy.deepcopy(base)
        p["structure"]["flows"] = [("tx", income, "B", "A", 500000, "2026-11-01")]
        p["regions"] = []
        p["data_used"] = []
        out = build_execution(p, context)
        kinds.add(out["steps"][0]["title"])
        assert out["steps"][0]["flows"] == ["tx"]
    check(len(kinds) == 11, "all 11 transaction types receive distinct transaction workpapers")
    p = copy.deepcopy(base)
    p["regions"][0]["conditions"] = []
    p["regions"][0]["deadlines"] = [("fee", "remit", "2026-11-22", "")]
    p["data_used"] = [base["data_used"][0]]
    p["best"] = p["guaranteed"]
    out = build_execution(p, context)
    check(out["status"] == "ready_for_review" and all(s["status"] != "check_now" for s in out["steps"]), "future clocks stay scheduled; workpack readiness never means filed or paid")
    p["claims"] = [("fee", "CN", 50000, 10000, 50000, 0, 40000, [0, 0], {"refund": "2026-12-31"}, ["refund"])]
    out = build_execution(p, context)
    check(any(s["kind"] == "recovery" and s["status"] == "conditional" for s in out["steps"]), "an open potential recovery creates an evidence-gated claim review")
    p["claims"][0] = ("fee", "CN", 50000, 10000, 50000, 0, 40000, [0, 0], {"refund": "2025-12-31"}, ["refund"])
    out = build_execution(p, context)
    check(not any(s["kind"] == "recovery" for s in out["steps"]), "expired routes are never recommended as open recovery actions")
    p["claims"] = [("fee", "CN", None, None, None, None, None, None, {}, ["closed"])]
    out = build_execution(p, context)
    check(out["exclusions"] and not any(s["kind"] == "recovery" for s in out["steps"]), "closed settled items are explicitly excluded")
    p["regions"] = {frozenset({"CN"}): base["regions"][0]}
    check(build_execution(p, context)["steps"], "native and serialized region representations both produce a workpack")
    # the plan states its aim and the reason for each step, in the order the work is done
    e = build_execution(base, context, 1)
    order = [ph for ph, _ in __import__("tax_graph.execution", fromlist=["PHASES"]).PHASES]
    check([order.index(s["phase"]) for s in e["steps"]] == sorted(order.index(s["phase"]) for s in e["steps"]), "steps run phase by phase: structure, facts, treatments, filing, closing")
    check(all(s.get("why") for s in e["steps"]), "every step states why it exists")
    check(abs(sum(t["conservative"] for t in e["tax_position"]) - 50000) < 0.01 and "income tax" in e["tax_position"][0]["items"], "the tax position adds up to the conservative tax and names its items")
    check("SGD 50,000.00" in e["recommended_course"] and "SGD 10,000.00" in e["recommended_course"] and "“Service classification”" in e["recommended_course"],
          "the head of the plan says what it achieves: the conservative tax, the lower amount and the treatment it needs")
    check([l["condition"] for l in e["levers"]][:1] == ["Service classification"] and e["levers"][0]["alone"] and not e["levers"][1]["alone"], "levers are ranked by what each is worth on its own")
    cond = next(s for s in e["steps"] if s["kind"] == "condition" and "Treaty" in s["why"])
    check("does not lower the conservative estimate" in cond["why"], "a treatment worth nothing on its own says so instead of implying a saving")
    planning = copy.deepcopy(base)
    planning["regions"][0]["actions"] = [("HOLD (SG) · new holding company established", "designed", 12000)]
    planning["cand"] = {"HOLD": "SG"}
    pe = build_execution(planning, dict(context, template="planning"), 4)
    first_tx = next(i for i, s in enumerate(pe["steps"]) if s["kind"] == "evidence")
    check(pe["steps"][0]["kind"] == "structure" and pe["steps"][0]["id"] in pe["steps"][first_tx]["depends_on"] and "SGD 12,000.00" in pe["steps"][0]["why"],
          "in a planning case the structure comes first, the payments depend on it, and its value is stated")
    check("lowest guaranteed tax among the 4 compared" in pe["objective"] and "HOLD = SG" in pe["objective"], "a planning objective names the chosen structure and how many were compared")
    print("%s execution checks passed" % count)


if __name__ == "__main__":
    main()
