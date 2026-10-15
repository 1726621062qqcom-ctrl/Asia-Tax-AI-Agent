"""Round 3: the production extraction boundary after the 2026-10-14 changes (quotes.loose, samples=2, meaning + guard
in the read prompt, non-strict JSON, failures as notes) and the production DeepSeek adapter, on the same ten cases
and gold as extract_eval.py. Harness-owned field meanings for the CORE paths; cost and headline-rate meanings
sharpened to mirror data/field_gloss.csv.

    python extract_eval2.py OUT_DIR [--models deepseek-flash] [--cases ...] [--jobs 10] [--samples 2]
"""
import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from pathlib import Path

ROOT = Path(r"C:\Coding\Projects\TUM\project_study_self")
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from tax_graph.llm.deepseek import DeepSeek            # noqa: E402
from tax_graph.llm.extract import BOOL, DATE, ENUM, NUMBER, FieldSpec, extract, field_specs   # noqa: E402
import extract_eval as E                               # noqa: E402  (CASES, SKIP, gold_value, same, describe)


def describe(path, cur, kind):
    k, allowed, meaning = E.describe(path, cur, kind)
    name = path.split(".")[-1]
    if name == "cost":
        a, b = path.split(".")[1].split(">")
        meaning = ("the acquisition cost of %s's equity in %s: what %s actually paid or paid in for it; registered, "
                   "subscribed or nominal capital is not it unless stated as paid in by %s" % (a, b, a, a))
    if name == "foreign_headline_rate":
        meaning = "the standard corporate income tax rate for resident enterprises in the payer's jurisdiction, in percent; not a withholding, treaty or non-resident rate"
    return k, allowed, meaning


def run_one(model_id, cid, samples):
    file, src, cur, roles = E.CASES[cid]
    case = json.loads((ROOT / file).read_text(encoding="utf-8"))
    docs = {src: (ROOT / "cases/sources" / src / "source.txt").read_text(encoding="utf-8")}
    specs, gold = {}, {}
    for path, pv in case["provenance"].items():
        if path in E.SKIP or "%s@%s" % (path, cid) in E.SKIP:
            continue
        kind = pv.get("kind")
        k, allowed, meaning = describe(path, cur, kind)
        specs[path] = FieldSpec(path, k, (), "", allowed, meaning, "")
        gold[path] = (kind, E.gold_value(case, path) if kind in ("disclosed", "derived") else None)
    brief = ("CASE ROLES: %s Amounts are plain numbers in full units of %s (71099000, not 71.1 million or RMB'000). "
             "Ratios and rates are in percent." % (roles, cur))
    ds = DeepSeek(model_id)
    t0 = time.time()
    ex = extract(docs, list(specs), lambda p: ds(brief + "\n\n" + p), specs, samples=samples)
    reasons = dict(ex.rejected)
    rows = []
    for path, (kind, g) in gold.items():
        elem, name = path.split(".", 1)
        v = ex.facts.get((elem, name))
        ev = ex.evidence.get((elem, name))
        why = reasons.get(path)
        if kind in ("disclosed", "derived"):
            status = "correct" if v is not None and E.same(path, g, v) else ("wrong" if v is not None else
                     ("disagree" if why and why.startswith("samples disagree") else ("rejected" if why else "null")))
        else:
            status = "abstained" if v is None else "false_fill"
        rows.append({"path": path, "kind": kind, "gold": str(g) if isinstance(g, date) else g,
                     "value": v.isoformat() if isinstance(v, date) else v, "status": status,
                     "quote": ev[1][:300] if ev else None, "rejected": [why] if why else []})
    return {"model": model_id, "case": cid, "samples": samples, "rows": rows, "usage": ds.usage, "wall": round(time.time() - t0, 1),
            "error": None, "notes": ex.notes}


def main(argv):
    out = Path(argv[1])
    out.mkdir(parents=True, exist_ok=True)
    models = (argv[argv.index("--models") + 1] if "--models" in argv else "deepseek-flash").split(",")
    cases = (argv[argv.index("--cases") + 1].split(",") if "--cases" in argv else list(E.CASES))
    jobs = int(argv[argv.index("--jobs") + 1]) if "--jobs" in argv else 10
    samples = int(argv[argv.index("--samples") + 1]) if "--samples" in argv else 2
    todo = [(m, c) for c in cases for m in models if not (out / ("%s__%s.json" % (m, c))).exists()]
    print("jobs:", len(todo), flush=True)

    def work(mc):
        try:
            res = run_one(mc[0], mc[1], samples)
        except Exception as e:
            print("%-16s %-20s FAILED %s: %s" % (mc[0], mc[1], type(e).__name__, e), flush=True)
            return
        (out / ("%s__%s.json" % mc)).write_text(json.dumps(res, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
        c = {}
        for r in res["rows"]:
            c[r["status"]] = c.get(r["status"], 0) + 1
        print("%-16s %-20s %6.0fs %s notes=%d" % (mc[0], mc[1], res["wall"], c, len(res["notes"])), flush=True)

    with ThreadPoolExecutor(jobs) as pool:
        list(pool.map(work, todo))


if __name__ == "__main__":
    main(sys.argv)
