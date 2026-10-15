# -*- coding: utf-8 -*-
"""Does tax_graph.precedent force what the formal account says? The running example of Prakken's analysis of Horty's
models (literature/notes/K1.md, pp. 4-6: trade secrets, factors π1 deceived, π2 bribed, π3 measures, δ1 obtainable
elsewhere, δ2 reverse-engineerable, δ3 disclosed; precedents c1 for the plaintiff, c2 for the defendant), with "true" =
the plaintiff wins; then the three-valued cases this project adds (an unknown factor counts against the side forced).

    python -m tax_graph.check_precedent
"""
import io
import sys

from .precedent import Factor, Precedent, analyse

ISSUE = "trade_secret_misused"
FACTORS = {ISSUE: {fid: Factor(ISSUE, fid, "flow", fid, "is_true", side, ("K1#p.4",)) for fid, side in
                   (("pi1", "true"), ("pi2", "true"), ("pi3", "true"), ("d1", "false"), ("d2", "false"), ("d3", "false"))}}


def case_base(reason_c1=()):
    return {ISSUE: [Precedent("c1", ISSUE, "-", "-", "binding", "-", "true", {"true": ("pi1", "pi3"), "false": ("d1", "d3")}, reason_c1),
                    Precedent("c2", ISSUE, "-", "-", "binding", "-", "false", {"true": ("pi2",), "false": ("d1", "d3")})]}


def facts(present, absent=(), unknown=()):
    f = {("flow", x): True for x in present}
    f.update({("flow", x): False for x in absent})
    return f                                                # unknown factors are simply not stated


def main():
    out = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    all_ = ("pi1", "pi2", "pi3", "d1", "d2", "d3")
    known = lambda present: facts(present, [x for x in all_ if x not in present])
    checks = []
    a = analyse(ISSUE, known(("pi2", "pi3", "d2", "d3")), FACTORS, case_base())
    checks.append(("p.4: F1 = {π2, π3, δ2, δ3} is forced for neither side", a.forced is None and not a.conflict))
    checks.append(("p.6: F1 differs from c1 by {π1, δ2} (what is missing, what is in the way)",
                   a.nearest["true"] == ("c1", ["pi1"], ["d2"])))
    a = analyse(ISSUE, known(("pi1", "pi3", "d1")), FACTORS, case_base())
    checks.append(("p.4: at least {π1, π3} and at most {δ1, δ3}: the plaintiff is forced by c1", (a.forced, a.by) == ("true", "c1")))
    a = analyse(ISSUE, known(("pi2", "d1", "d3")), FACTORS, case_base())
    checks.append(("p.4: at least {δ1, δ3} and at most {π2}: the defendant is forced by c2", (a.forced, a.by) == ("false", "c2")))
    a = analyse(ISSUE, known(("pi1", "d1")), FACTORS, case_base(reason_c1=("pi1",)))
    checks.append(("p.5: reason model, c1's rule {π1}: {π1, δ1} is forced for the plaintiff", (a.forced, a.by) == ("true", "c1")))
    a = analyse(ISSUE, known(("pi1", "d1")), FACTORS, case_base())
    checks.append(("result model: {π1, δ1} lacks π3, not forced", a.forced is None))
    a = analyse(ISSUE, facts(("pi1", "d1"), ("pi2", "d2", "d3")), FACTORS, case_base())
    checks.append(("unknown π3 counts as absent for the plaintiff: not forced", a.forced is None))
    a = analyse(ISSUE, facts(("pi1", "pi3", "d1"), ("pi2", "d3")), FACTORS, case_base())
    checks.append(("unknown δ2 (not in c1) counts as present against the plaintiff: not forced, δ2 in the way",
                   a.forced is None and a.nearest["true"] == ("c1", [], ["d2"])))
    persuasive = {ISSUE: [Precedent("c1", ISSUE, "-", "-", "persuasive", "-", "true", {"true": ("pi1", "pi3"), "false": ("d1", "d3")})]}
    a = analyse(ISSUE, known(("pi1", "pi3")), FACTORS, persuasive)
    checks.append(("a persuasive decision never forces, but still shows the nearest", a.forced is None and a.nearest["true"][0] == "c1"))
    bad = 0
    for text, ok in checks:
        bad += not ok
        out.write("%-4s %s\n" % ("ok" if ok else "FAIL", text))
    out.write("%d checks, %d failures\n" % (len(checks), bad))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
