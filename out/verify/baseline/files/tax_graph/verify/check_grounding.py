# -*- coding: utf-8 -*-
"""Does the 依据核对 notice a missing basis? Gold case A is traced as it is (no failure), then once per seeded fault in
a copy of the library or the parameters — a quote that no longer occurs in its clause, a cited clause gone from the
clause layer (superseded or repealed), a parameter expired before the flow's date, a judgement's clause gone, a 口径
anchor broken — and each must come out as a failure.

    python -m tax_graph.verify.check_grounding
"""
import copy
import io
import sys

from ..cases import SCENARIOS
from ..engine import RULES_BY_ID
from ..params import Params
from ..planner import Answers
from ..rules.model import Discretion, leaves
from ..scenarios import TEMPLATES
from .grounding import Library, check_case


def fails(recs):
    return [r for r in recs if r["status"] == "fail"]


def main():
    out = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    tname, case, event = SCENARIOS["A"]
    template = TEMPLATES[tname]
    lib0, P0 = Library(), Params()

    def run(lib, P):
        return check_case("check_A", template, case, event, Answers(), lib, P)[1]

    base = run(lib0, P0)
    results = [("as it is: no failure", not fails(base), len(fails(base)))]
    rate = RULES_BY_ID["cn.wht.reduced"].value                  # the 10% the plan's dividend withholding is charged at
    cite = P0.rows[rate]["cite_id"]
    gaar = next(c for x in leaves(RULES_BY_ID["cn.gaar"].cond) if isinstance(x, Discretion) for c in x.cites)
    did = next(d for r in base if r["check_id"] == "G-rule" for d in lib0.decisions_for(r["subject"].split("@")[0]))

    def seeded(label, mutate):
        lib, P = copy.deepcopy(lib0), copy.deepcopy(P0)
        mutate(lib, P)
        got = fails(run(lib, P))
        results.append((label, bool(got), len(got)))

    seeded("a parameter's quote no longer in its clause",
           lambda lib, P: P.rows[rate].update(quote="这句话不在条文里"))
    seeded("the clause a parameter cites gone from the clause layer",
           lambda lib, P: lib.clauses.pop(cite))
    seeded("a parameter expired before the flow's date",
           lambda lib, P: P.rows[rate].update(effective_to="2020-12-31"))
    seeded("a judgement's clause gone from the clause layer",
           lambda lib, P: lib.clauses.pop(gaar))
    seeded("a 口径 anchor's quote broken",
           lambda lib, P: lib.decisions[did]["anchors"].__setitem__(0, (lib.decisions[did]["anchors"][0][0], "这句话不在条文里")))
    bad = 0
    for label, ok, n in results:
        bad += not ok
        out.write("%-4s %s (failures: %d)\n" % ("ok" if ok else "FAIL", label, n))
    out.write("%d checks, %d failures\n" % (len(results), bad))
    out.flush()
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
