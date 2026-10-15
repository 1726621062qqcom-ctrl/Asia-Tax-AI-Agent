"""Summarise eval_full/*.json: per model, per gold kind, status counts; usage; every non-correct row."""
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

d = Path(sys.argv[1])
res = [json.loads(p.read_text(encoding="utf-8")) for p in sorted(d.glob("*.json"))]
by = defaultdict(Counter)
use = defaultdict(Counter)
wall = defaultdict(float)
errs = []
for r in res:
    for row in r["rows"]:
        k = "value" if row["kind"] in ("disclosed",) else ("derived" if row["kind"] == "derived" else "null-expected")
        by[(r["model"], k)][row["status"]] += 1
    for x in ("calls", "prompt_tokens", "completion_tokens", "cache_hit_tokens"):
        use[r["model"]][x] += r["usage"][x]
    use[r["model"]]["seconds"] += r["usage"]["seconds"]
    wall[r["model"]] = max(wall[r["model"]], r["wall"])
    if r["error"]:
        errs.append((r["model"], r["case"], r["error"]))
print("cases per model:", Counter(r["model"] for r in res))
for (m, k), c in sorted(by.items()):
    print("%-16s %-14s %s" % (m, k, dict(c)))
for m, u in use.items():
    print(m, dict(u), "max case wall %.0fs" % wall[m])
print("errors:", errs)
print()
print("NON-CORRECT ROWS")
rows = defaultdict(dict)
for r in res:
    for row in r["rows"]:
        rows[(r["case"], row["path"], row["kind"], str(row["gold"]))][r["model"]] = (row["status"], row["value"], (row.get("quote") or "")[:140], row.get("rejected"))
for key, per in sorted(rows.items()):
    if all(s[0] in ("correct", "abstained") for s in per.values()):
        continue
    print(key)
    for m, s in sorted(per.items()):
        print("    %-16s %-10s %r  | %s %s" % (m, s[0], s[1], s[2], s[3] or ""))
