"""run (v1 doc §9 entry): a case file in, a readable report out.

    python -m tax_graph.run cases/meridian.json          (conda env "pytorch")

The case file names the template, the subject, the roles with their facts, the holdings, the flow facts, the present
assignment, what has been paid (settled) and the event. The program builds the Case, runs ex_ante (which carries the
ex_post claims of settled items), applies the ticks the file may hold, and renders: the candidate table, the best row's
items by flow and jurisdiction under both bounds, the pending facts and conditions ranked by cost, the claims and the
facts the case did not state. Nothing here decides anything the engine did not."""
import io
import json
import re
import sys
from dataclasses import replace
from datetime import date
from pathlib import Path

from .claims import Claim
from .data.domain import Event
from .ex_ante import ex_ante, finalize
from .fields import missing_fields
from .model import HoldEdge
from .scenarios import GROUP, TEMPLATES, Case, RoleFacts, template_of
from .rules.tri import DISCRETION, MISSING, Need, PLAN

DATE_KEYS = {"on", "since", "as_at", "exit_on"}


ISO = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def _dates(obj):
    """Every ISO date string in the file is a date (facts are typed by their value, not by their key)."""
    if isinstance(obj, dict):
        return {k: (date.fromisoformat(v) if isinstance(v, str) and ISO.match(v) else _dates(v)) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_dates(x) for x in obj]
    return obj


def load_case(path):
    d = _dates(json.loads(Path(path).read_text(encoding="utf-8")))
    roles = {r: RoleFacts(v["loc"], dict(v.get("attrs", {})), v.get("type", "COMPANY")) for r, v in d["roles"].items()}
    holds = {(h["holder"], h["held"]): HoldEdge(h["holder"], h["held"], float(h["ratio"]), h.get("since"), h.get("cost")) for h in d.get("holds", [])}
    case = Case(roles=roles, holds=holds, flows={k: dict(v) for k, v in d.get("flows", {}).items()},
                present=dict(d.get("present", {})), settled={k: dict(v) for k, v in d.get("settled", {}).items()},
                closed=frozenset(tuple(x) for x in d.get("closed", [])), members=set(d["members"]) if d.get("members") else None,
                transactions={k: dict(v) for k, v in d.get("transactions", {}).items()}, currency=d.get("currency", "CNY"), names=d.get("names", {}))
    event = Event(**d["event"])
    ticks = {}
    for k, v in d.get("ticks", {}).items():                   # "DISCRETION:payee.ppt": false
        src, key = k.split(":", 1)
        ticks[Need(src, key)] = bool(v)
    return template_of(d["template"]), case, event, d.get("subject", GROUP), ticks, d.get("notes", [])


def _items(lb):
    return [(it.jur, it.levy, it.borne_by, round(lb.flow.amount * it.effective / 100.0, 2), sorted(set(it.cites))) for it in lb.items if it.effective != 0]


def render(template, case, event, subject, out, finalized=None, notes=()):
    L = []
    w = L.append
    w("# Result: template %s, subject %s, event %s" % (template.name, subject, {k: (v.isoformat() if isinstance(v, date) else v) for k, v in event.__dict__.items() if v not in (None, 1, False)}))
    if notes:
        w("")
        w("Assumptions / gaps noted in the case file:")
        for n in notes:
            w("- " + n)
    vars_ = template.vars(event)
    w("")
    w("## Candidate table (group total tax lo / hi; subject share; discretion count, plan item count, fragility)")
    w("")
    w("| Candidate | lo | hi | share@lo | share@hi | Discretion | Plan items | Fragility | Dominated |")
    w("|---|---|---|---|---|---|---|---|---|")
    for r in out.table:
        w("| %s | %.2f | %.2f | %.2f | %.2f | %d | %d | %.2f | %s |" % ("/".join(str(r.cand.get(k)) for k in vars_) or "the only structure",
          r.b.lo, r.b.hi, r.subject[0], r.subject[1], r.n_discretion, r.n_plan, r.fragility, "yes" if r.dominated else ""))
    best = out.table[0]
    present = next((r for r in out.table if r.cand == case.present), None) if case.present else None
    w("")
    if present is not None and present is best:
        w("**The present structure is optimal**: no structural improvement; any improvement comes only from the pending items below.")
    elif present is not None:
        w("**Best candidate** %s (lo %.2f / hi %.2f); **present structure** lo %.2f / hi %.2f." % (best.cand, best.b.lo, best.b.hi, present.b.lo, present.b.hi))
    elif best.cand:
        w("**Best candidate** %s: lo %.2f / hi %.2f." % (best.cand, best.b.lo, best.b.hi))
    else:
        w("**The only structure**: lo %.2f / hi %.2f (no structural variable; the conclusions lie in the pending items and the settled tax items)." % (best.b.lo, best.b.hi))
    w("")
    w("## Tax items of the best candidate (flow / jurisdiction / levy / bearer / amount / basis)")
    for side, labels in (("lower bound", best.b.L_lo), ("upper bound", best.b.L_hi)):
        w("")
        w("%s:" % side)
        for fid, lb in labels.items():
            for jur, levy, who, amt, cites in _items(lb):
                w("- %s · %s · %s · %s · %.2f · %s" % (fid, jur, levy, who, amt, ", ".join(cites)))
    w("")
    w("## Pending facts (by the cost of losing them)")
    for cost, g, keys in out.needs:
        w("- %.2f  %s  %s" % (cost, g, ", ".join(keys)))
    w("")
    w("## Pending conditions: plan items and discretion items (by cost)")
    for cost, g, keys in out.conditions:
        w("- %.2f  %s  %s" % (cost, g, ", ".join(keys)))
    if out.claims or out.archived:
        w("")
        w("## Settled tax items: recoverable / shortfall risk / routes")
        for c in out.claims:
            w("- %s/%s: paid %.2f, per the rules [%.2f, %.2f]; confirmed recoverable %.2f, potentially recoverable %.2f; shortfall risk [%.2f, %.2f]; clocks %s; routes %s" % (
                c.flow, c.jur, c.actual, c.lo, c.hi, c.confirmed, c.potential, c.shortfall[0], c.shortfall[1],
                {k: (v.isoformat() if isinstance(v, date) else v) for k, v in c.deadlines.items()}, [r[0] for r in c.routes]))
        for a in out.archived:
            w("- %s/%s: closed (every clock has run out, or declared); no claim" % a)
    g = template.build(event, best.cand, case)
    miss = sorted(missing_fields(g))
    w("")
    w("## Fields the rules read but the case does not give (%d)" % len(miss))
    for fid, key in miss:
        w("- %s  %s" % (fid, key))
    if finalized is not None:
        w("")
        w("## Result after the ticks")
        w("Minimum %s: lo %.2f / hi %.2f" % (finalized.cand, finalized.b.lo, finalized.b.hi))
    return "\n".join(L) + "\n"


def main(argv):
    """python -m tax_graph.run CASE.json [--answers ANSWERS.json] [--table]
    Default: the planner (优化方案 v2) — a question sheet, or one concrete plan, by jurisdiction region; answers are read
    from CASE.answers.json next to the case unless --answers names another file. --table: the candidate table instead."""
    path = argv[1]
    if "--table" not in argv:
        from .planner import Answers, plan as _plan, render as _render
        template, case, event, subject, ticks, notes = load_case(path)
        ans_path = argv[argv.index("--answers") + 1] if "--answers" in argv else str(Path(path).with_suffix("")) + ".answers.json"
        outcome = _plan(template, event, case, Answers.load(ans_path))
        text = _render(template, event, outcome, Path(path).stem)
        dst = Path("out") / (Path(path).stem + ".md")
        dst.parent.mkdir(exist_ok=True)
        dst.write_text(text, encoding="utf-8")
        sys.stdout.buffer.write(text.encode("utf-8"))
        sys.stdout.buffer.write(("\n[written to %s; answers read from %s]\n" % (dst, ans_path)).encode("utf-8"))
        return 0
    template, case, event, subject, ticks, notes = load_case(path)
    out = ex_ante(template, event, case, ticks=ticks or None, subject=subject)
    fin = finalize(template, event, case, out.table, ticks, subject=subject) if ticks else None
    text = render(template, case, event, subject, out, fin, notes)
    dst = Path("out") / (Path(path).stem + ".table.md")
    dst.parent.mkdir(exist_ok=True)
    dst.write_text(text, encoding="utf-8")
    sys.stdout.buffer.write(text.encode("utf-8"))
    sys.stdout.buffer.write(("\n[written to %s]\n" % dst).encode("utf-8"))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
