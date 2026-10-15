"""Summarise a round-4 directory: status counts per gold kind and per means (pattern / model), usage, every non-correct
row with its conflict, the coverage–error curve over the per-field features, and the metamorphic tests.

    python eval_summary3.py OUT_DIR
"""
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

d = Path(sys.argv[1])
res = [json.loads(p.read_text(encoding="utf-8")) for p in sorted(d.glob("*.json")) if not p.name.startswith("meta__")]
meta = [json.loads(p.read_text(encoding="utf-8")) for p in sorted(d.glob("meta__*.json"))]
by, means, use = defaultdict(Counter), defaultdict(Counter), defaultdict(Counter)
wall = defaultdict(float)
for r in res:
    for row in r["rows"]:
        k = "value" if row["kind"] == "disclosed" else ("derived" if row["kind"] == "derived" else "null-expected")
        by[(r["model"], k)][row["status"]] += 1
        means[(r["model"], row["means"])][row["status"]] += 1
    for x in ("calls", "cached", "prompt_tokens", "completion_tokens", "cache_hit_tokens", "retries"):
        use[r["model"]][x] += r["usage"].get(x, 0)
    use[r["model"]]["seconds"] += r["usage"]["seconds"]
    wall[r["model"]] = max(wall[r["model"]], r["wall"])
print("cases per model:", dict(Counter(r["model"] for r in res)), "| settings:", {k: res[0][k] for k in ("samples", "k", "locate", "patterns", "dense", "temperature", "prompt_version")} if res else {})
for (m, k), c in sorted(by.items()):
    print("%-16s %-14s %s" % (m, k, dict(c)))
for (m, k), c in sorted(means.items()):
    print("%-16s by %-11s %s" % (m, k, dict(c)))
for m, u in use.items():
    print(m, {k: round(v) for k, v in u.items()}, "max case wall %.0fs" % wall[m])
print()
print("NON-CORRECT ROWS")
for r in res:
    for row in r["rows"]:
        if row["status"] in ("correct", "abstained"):
            continue
        print("(%s, %s, %s, gold=%r)" % (r["case"], row["path"], row["kind"], row["gold"]))
        print("    %-10s %r %s | %s %s" % (row["status"], row["value"], row["means"], (row.get("quote") or "")[:120].replace("\n", " "), row.get("rejected") or ""))
        for c in row.get("conflict") or []:
            print("        conflict %r (%s, %s): %s" % (c["value"], c["doc"], c["origin"], (c["quote"] or "")[:110].replace("\n", " ")))
print()
print("DISCLOSED ROWS WITHOUT A VALUE, BY WHERE THE GOLD QUOTE WAS (rank among the k candidates; None = outside; -1 = in no passage)")
c = Counter()
for r in res:
    for row in r["rows"]:
        if row["kind"] == "disclosed" and row["status"] != "correct":
            c[(row["status"], row["means"], str(row.get("gold_rank", "n/a")))] += 1
for (st, means, rank), k in sorted(c.items()):
    print("  %-10s %-8s gold_rank=%-5s %d" % (st, means, rank, k))
print()
print("COVERAGE–ERROR (fields with a value, ordered by agreement then retrieval score; error = wrong + false_fill)")
valued = [(row["features"].get("agree", 1.0), row["features"].get("score", 0.0), row["status"]) for r in res for row in r["rows"] if row["value"] is not None]
valued.sort(key=lambda t: (-t[0], -t[1]))
n = len(valued)
for frac in (0.25, 0.5, 0.75, 1.0):
    top = valued[:max(1, round(n * frac))]
    err = sum(1 for _, _, s in top if s in ("wrong", "false_fill"))
    print("  coverage %3.0f%%  n=%3d  errors=%2d  (%.1f%%)" % (frac * 100, len(top), err, 100.0 * err / len(top) if top else 0))
print("  feature spread: agree", dict(Counter(round(a, 2) for a, _, _ in valued)))
if meta:
    print()
    print("METAMORPHIC TESTS (K4)")
    c = Counter()
    for r in meta:
        for t in r["tests"]:
            c[(t["test"], t["status"].split(":")[0])] += 1
            if t["status"].split(":")[0] not in ("follows", "flips", "skipped"):
                print("  %-18s %-36s %-10s %s -> %s expected %s got %r %s" % (r["case"], t["path"], t["test"], t.get("token") or t.get("gold"),
                                                                            t.get("new") or "", t.get("expected"), t.get("value"), t["status"] + (" " + t["why"] if t.get("why") else "")))
    for (test, st), k in sorted(c.items()):
        print("  %-10s %-10s %d" % (test, st, k))
