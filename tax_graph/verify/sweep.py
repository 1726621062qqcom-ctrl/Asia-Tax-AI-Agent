# -*- coding: utf-8 -*-
"""K3 amount sweep (案例采集.md §6): a semi-synthetic case with its synthetic amounts scaled — does the planner's outcome hold?

    python -m tax_graph.verify.sweep CASE.json [CASE.json ...] [--scales 0.5,1,2]

Only amounts the case marks synthetic (provenance kind "synthetic") are scaled — event amounts, money attributes and
holding costs; disclosed and derived values, rates, ratios, dates and the number of years stay as they are. For each
scale: plan or question sheet, the structure chosen (or leading, as the grounding check takes it), its guaranteed tax
and floor, and the question addresses. A change across scales is listed for a person to look at; it is not an error by
itself — thresholds are absolute amounts. Writes out/sweep_<case>.md."""
import io
import json
import re
import sys
import tempfile
from pathlib import Path

from ..planner import Answers, _key, plan
from ..run import load_case

OUT = Path("out")
EVENT_AMOUNTS = {"dividend", "onward", "exit", "interest", "royalty", "fee", "service_fee", "amount", "rent"}
MONEY = re.compile(r"(revenue|income|profit|taxes|payroll|assets|amount|cost)")


def amount_paths(d):
    """(path, value) of every synthetic amount the case states."""
    prov = d.get("provenance") or {}
    out = []
    for p, e in prov.items():
        if (e or {}).get("kind") != "synthetic":
            continue
        parts = p.split(".")
        v = get(d, parts)
        if isinstance(v, bool) or not isinstance(v, (int, float)):
            continue
        last = parts[-1]
        if (parts[0] == "event" and last in EVENT_AMOUNTS) or (parts[0] != "event" and MONEY.search(last)):
            out.append((p, v))
    return out


def get(d, parts):
    if parts[0] == "holds":
        holder, held = parts[1].split(">")
        h = next((x for x in d.get("holds", []) if x["holder"] == holder and x["held"] == held), {})
        return h.get(parts[2])
    node = d
    for k in parts:
        if not isinstance(node, dict) or k not in node:
            return None
        node = node[k]
    return node


def put(d, parts, v):
    if parts[0] == "holds":
        holder, held = parts[1].split(">")
        next(x for x in d["holds"] if x["holder"] == holder and x["held"] == held)[parts[2]] = v
        return
    node = d
    for k in parts[:-1]:
        node = node[k]
    node[parts[-1]] = v


def run(path, scales):
    d0 = json.loads(Path(path).read_text(encoding="utf-8"))
    paths = amount_paths(d0)
    ans = Path(path).with_suffix("")
    answers = Answers.load(str(ans) + ".answers.json")
    rows = []
    with tempfile.TemporaryDirectory() as tmp:
        for k in scales:
            d = json.loads(json.dumps(d0))
            for p, v in paths:
                put(d, p.split("."), round(v * k, 2))
            f = Path(tmp) / Path(path).name
            f.write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")
            template, case, event, subject, ticks, notes = load_case(str(f))
            o = plan(template, event, case, answers)
            if o.plan is not None:
                best, mode = next(e for e in o.evaluations if e.cand == o.plan["cand"]), "plan"
            else:
                open_ = [e for e in o.evaluations if not e.excluded]
                best, mode = (min(open_, key=_key) if open_ else None), "question sheet"
            present = next((e for e in o.evaluations if not e.excluded and all(e.cand.get(x) == y for x, y in case.present.items() if x in e.cand)), None)
            rows.append({"scale": k, "mode": mode, "cand": best.cand if best else None,
                         "hi": round(best.b.hi, 2) if best else None, "lo": round(best.b.lo, 2) if best else None,
                         "present_hi": round(present.b.hi, 2) if present else None,
                         "questions": sorted(q.key for q in o.questions)})
    return paths, rows


def report(name, paths, rows):
    base = next((r for r in rows if r["scale"] == 1), rows[0])
    changes = []
    for r in rows:
        if r is base:
            continue
        if r["mode"] != base["mode"]:
            changes.append("×%s: %s → %s" % (r["scale"], base["mode"], r["mode"]))
        if r["cand"] != base["cand"]:
            changes.append("×%s: chosen structure %s → %s" % (r["scale"], base["cand"], r["cand"]))
        added, gone = sorted(set(r["questions"]) - set(base["questions"])), sorted(set(base["questions"]) - set(r["questions"]))
        if added or gone:
            changes.append("×%s: question sheet gains %s; loses %s" % (r["scale"], ", ".join(added) or "none", ", ".join(gone) or "none"))
    L = ["# Amount sweep: %s" % name, "", "Synthetic values scaled: %s." % (", ".join("%s=%s" % pv for pv in paths) or "(no synthetic amounts)"), "",
         "| Scale | Outcome | Chosen or leading structure | Guaranteed tax | Floor | Guaranteed tax of the present structure | Questions |", "|---|---|---|---|---|---|---|"]
    for r in rows:
        L.append("| ×%s | %s | %s | %s | %s | %s | %d |" % (r["scale"], r["mode"], r["cand"], r["hi"], r["lo"], r["present_hi"], len(r["questions"])))
    L += ["", "**Changes**: " + ("; ".join(changes) if changes else "identical across scales (outcome, structure, question sheet)")]
    return "\n".join(L) + "\n", changes


def main(argv):
    out = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    scales = [0.5, 1, 2]
    if "--scales" in argv:
        scales = [float(x) for x in argv[argv.index("--scales") + 1].split(",")]
    skip = {argv.index("--scales") + 1} if "--scales" in argv else set()
    OUT.mkdir(exist_ok=True)
    for i, a in enumerate(argv[1:], 1):
        if a.startswith("--") or i in skip:
            continue
        name = Path(a).stem
        paths, rows = run(a, scales)
        text, changes = report(name, paths, rows)
        (OUT / ("sweep_%s.md" % name)).write_text(text, encoding="utf-8")
        out.write("%-18s %d synthetic amounts; %s -> out/sweep_%s.md\n" % (name, len(paths), "; ".join(changes) if changes else "identical across scales", name))
    out.flush()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
