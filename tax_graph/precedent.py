# -*- coding: utf-8 -*-
"""Precedential constraint (案例采集.md §5; literature/notes/K1.md): when do binding precedents settle a judgement?

A judgement is a Discretion key of the rule layer (e.g. income_sourced_in_hk); its precedents say whether the key held
("true") or not ("false") on their facts. Factors (official/labels/factors.csv) are facts that favour one side, each
with the clauses it rests on; precedents (official/labels/precedents.csv) list the factors present on each side, the
outcome, whether the decision binds, and — when the decision states one — its reason (the subset of the winning side's
factors it held sufficient).

Forcing follows Horty's models as Prakken formalises them: a decision for side s is forced when some binding precedent
with outcome s has no relevant difference from the new facts — every factor of its reason (the result model: every
factor it had for s) is present, and no factor for the other side is present that the precedent did not have. Facts
are three-valued here: an unknown factor counts against the side being forced, so the decision is forced only if it
would be whatever the unknown facts turn out to be. The relevant differences of the nearest precedent for each side are
what the facts would need to change to be covered.

    python -m tax_graph.precedent --check                       check the cards against the clause layer
    python -m tax_graph.precedent ISSUE FACTS.json              analyse one fact situation ({"flow.x": true, ...})
"""
import csv
import io
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

ROOT = Path(__file__).resolve().parents[1]
LABELS = ROOT / "official" / "labels"
SIDES = ("true", "false")
BINDING = ("binding",)                         # only these decide; "persuasive" and "practice" are factor sources


@dataclass
class Factor:
    issue: str
    factor_id: str
    elem: str                                  # flow | payer | payee
    field: str
    test: str                                  # is_true | is_false | eq:<v> | ge:<n> | le:<n>
    favours: str                               # true | false: the side of the judgement it supports
    cites: Tuple[str, ...]
    quote: str = ""                            # verbatim from one of the cited clauses (checked like a parameter's)
    note: str = ""

    def state(self, facts) -> Optional[bool]:
        """Present (True), absent (False) or unknown (None) on these facts ({(elem, field): value})."""
        v = facts.get((self.elem, self.field))
        if v is None:
            return None
        op, _, arg = self.test.partition(":")
        if op == "is_true":
            return v is True
        if op == "is_false":
            return v is False
        if op == "eq":
            return str(v) == arg
        if op in ("ge", "le"):
            return float(v) >= float(arg) if op == "ge" else float(v) <= float(arg)
        raise ValueError("unknown factor test %r" % self.test)


@dataclass
class Precedent:
    precedent_id: str
    issue: str
    jur: str
    forum: str
    binding: str                               # binding | persuasive | practice
    date: str
    outcome: str                               # true | false
    factors: Dict[str, Tuple[str, ...]]        # side -> factor ids present for that side
    reason: Tuple[str, ...] = ()               # the winning side's factors the decision held sufficient, if stated
    cites: Tuple[str, ...] = ()
    quote: str = ""                            # the holding, verbatim from one of the cited clauses
    note: str = ""

    def needed(self):
        """What a new case must have for the outcome: the stated reason (reason model) or all winning factors."""
        return self.reason or self.factors.get(self.outcome, ())


@dataclass
class Analysis:
    issue: str
    forced: Optional[str]                      # true | false | None
    by: str = ""                               # the precedent that forces it
    conflict: bool = False                     # both sides forced: the binding precedents disagree on these facts
    nearest: Dict[str, Tuple[str, List[str], List[str]]] = field(default_factory=dict)
    # side -> (precedent id, factors still missing for it, factors against it it did not have)


def _split(s):
    return tuple(x.strip() for x in (s or "").replace("；", ";").split(";") if x.strip())


def load(labels=LABELS):
    factors, precedents = {}, {}
    fp, pp = labels / "factors.csv", labels / "precedents.csv"
    if fp.exists():
        with open(str(fp), encoding="utf-8-sig", newline="") as f:
            for r in csv.DictReader(f):
                factors.setdefault(r["issue_key"], {})[r["factor_id"]] = Factor(
                    r["issue_key"], r["factor_id"], r["elem"], r["field"], r["test"], r["favours"], _split(r["cites"]),
                    r.get("quote", ""), r.get("note", ""))
    if pp.exists():
        with open(str(pp), encoding="utf-8-sig", newline="") as f:
            for r in csv.DictReader(f):
                precedents.setdefault(r["issue_key"], []).append(Precedent(
                    r["precedent_id"], r["issue_key"], r["jur"], r["forum"], r["binding"], r["date"], r["outcome"],
                    {"true": _split(r["factors_true"]), "false": _split(r["factors_false"])}, _split(r.get("reason", "")),
                    _split(r["cites"]), r.get("quote", ""), r.get("note", "")))
    return factors, precedents


def norm(s):
    return re.sub(r"\s+", "", s or "")


def analyse(issue, facts, factors, precedents) -> Analysis:
    """Which side, if any, the binding precedents force on these three-valued facts; and for each side the nearest
    precedent with what is missing (its needed factors not surely present) and what is in the way (factors for the
    other side possibly present that the precedent did not have)."""
    fs = factors.get(issue, {})
    state = {fid: f.state(facts) for fid, f in fs.items()}
    out = Analysis(issue, None)
    forced = []
    for side in SIDES:
        other = "false" if side == "true" else "true"
        best = None
        for p in precedents.get(issue, []):
            if p.outcome != side:
                continue
            missing = [fid for fid in p.needed() if state.get(fid) is not True]
            in_way = [fid for fid, f in fs.items() if f.favours == other and state[fid] is not False
                      and fid not in p.factors.get(other, ())]
            if p.binding in BINDING and not missing and not in_way:
                forced.append((side, p.precedent_id))
            size = len(missing) + len(in_way)
            if best is None or size < best[0]:
                best = (size, p.precedent_id, missing, in_way)
        if best is not None:
            out.nearest[side] = (best[1], best[2], best[3])
    sides = {s for s, _ in forced}
    if len(sides) == 1:
        out.forced, out.by = forced[0]
    elif len(sides) == 2:
        out.conflict = True
    return out


def check_cards(factors, precedents, clauses):
    """clauses: cite id -> text of the current clause layer. Every cited clause is there and every quote is found
    verbatim in one of its cited clauses; every factor a precedent lists is declared for its issue and favours the side
    it is listed under; outcomes and binding levels are known values."""
    errors = []

    def quoted(owner, cites, quote):
        if quote and not any(norm(quote) in norm(clauses.get(c, "")) for c in cites):
            errors.append("%s: quote not found verbatim in %s" % (owner, ", ".join(cites)))

    for issue, fs in factors.items():
        for f in fs.values():
            if f.favours not in SIDES:
                errors.append("factor %s: favours %r" % (f.factor_id, f.favours))
            if not f.cites:
                errors.append("factor %s: no clause" % f.factor_id)
            errors += ["factor %s: clause not in the library: %s" % (f.factor_id, c) for c in f.cites if c not in clauses]
            quoted("factor " + f.factor_id, f.cites, f.quote)
    for issue, ps in precedents.items():
        for p in ps:
            if p.outcome not in SIDES or p.binding not in ("binding", "persuasive", "practice"):
                errors.append("precedent %s: outcome %r / binding %r" % (p.precedent_id, p.outcome, p.binding))
            for side, fids in p.factors.items():
                for fid in fids:
                    f = factors.get(issue, {}).get(fid)
                    if f is None:
                        errors.append("precedent %s: factor %s not declared for %s" % (p.precedent_id, fid, issue))
                    elif f.favours != side:
                        errors.append("precedent %s: factor %s listed for %s but favours %s" % (p.precedent_id, fid, side, f.favours))
            if any(fid not in p.factors.get(p.outcome, ()) for fid in p.reason):
                errors.append("precedent %s: its reason has factors not on the winning side" % p.precedent_id)
            errors += ["precedent %s: clause not in the library: %s" % (p.precedent_id, c) for c in p.cites if c not in clauses]
            quoted("precedent " + p.precedent_id, p.cites, p.quote)
    return errors


def main(argv):
    out = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    factors, precedents = load()
    if "--check" in argv:
        csv.field_size_limit(10 ** 9)
        with open(str(ROOT / "official" / "clauses.csv"), encoding="utf-8-sig", newline="") as f:
            clauses = {r["cite_id"]: r["text"] for r in csv.DictReader(f)}
        errors = check_cards(factors, precedents, clauses)
        out.write("%d issues, %d factors, %d precedents (%d binding); %d errors\n" % (
            len(set(factors) | set(precedents)), sum(len(v) for v in factors.values()), sum(len(v) for v in precedents.values()),
            sum(1 for v in precedents.values() for p in v if p.binding in BINDING), len(errors)))
        for e in errors:
            out.write("  " + e + "\n")
        return 1 if errors else 0
    issue, path = argv[1], argv[2]
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    facts = {tuple(k.split(".", 1)): v for k, v in raw.items()}
    a = analyse(issue, facts, factors, precedents)
    out.write("%s: %s\n" % (issue, ("forced %s by %s" % (a.forced, a.by)) if a.forced else ("conflict" if a.conflict else "not forced")))
    for side, (pid, missing, in_way) in a.nearest.items():
        out.write("  nearest for %s: %s; missing %s; in the way %s\n" % (side, pid, missing or "—", in_way or "—"))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
