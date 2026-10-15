"""Channel C by program: the consolidated revenue of each K3 case read by tax_graph.llm.tables alone (no model),
the way the entry point does it — the latest full financial year before the event that the documents state, the
library's year-end central parity — against the case's own gold (group_revenue_eur). No key, no network.

    python tables_check.py
"""
import json
import sys
from pathlib import Path

ROOT = Path(r"C:\Coding\Projects\TUM\project_study_self")
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from tax_graph.llm.tables import revenue, to_eur, year_end_rate_date   # noqa: E402
import extract_eval as E                                                 # noqa: E402

ok = n = 0
for cid, (file, src, cur, roles) in E.CASES.items():
    case = json.loads((ROOT / file).read_text(encoding="utf-8"))
    pv = case.get("provenance", {}).get("roles.ULT.attrs.group_revenue_eur")
    if not pv:
        continue
    n += 1
    gold = case["roles"]["ULT"]["attrs"].get("group_revenue_eur")
    event_year = int(case["event"]["on"][:4])
    docs = {src: (ROOT / "cases/sources" / src / "source.txt").read_text(encoding="utf-8")}
    r, year = {"rows": 0, "distinct": [], "value": None, "currency": None}, None
    for y in range(event_year - 1, event_year - 6, -1):
        rr = revenue(docs, y)
        if rr["rows"]:
            r, year = rr, y
            break
    eur, how = (None, "no value")
    if r["value"] is not None:
        on = year_end_rate_date(year)
        eur, how = to_eur(r["value"], r["currency"] or "CNY", on) if on else (None, "no year-end rate for %s" % year)
    status = "match" if eur is not None and gold and abs(eur - gold) <= 0.002 * gold else ("conflict" if len(r["distinct"]) > 1 else ("missing" if r["value"] is None else "differs"))
    ok += status == "match"
    print("%-16s year=%s rows=%d distinct=%d value=%s %s -> EUR %s | gold %s | %s" % (
        cid, year, r["rows"], len(r["distinct"]), "{:,.0f}".format(r["value"]) if r["value"] else None, r["currency"], "{:,.2f}".format(eur) if eur else how, gold, status))
    for d in r["distinct"][:4]:
        print("     %-18s scale=%-8g %s | %s" % ("{:,.0f}".format(d["value"]), d["scale"], d["doc"], " ".join(d["row"]["quote"].split())[:100]))
    if status == "missing":
        print("     gold quote (what the document says): %s" % (pv.get("quote") or "")[:120].replace("\n", " "))
print("%d/%d match by program alone; the rest fall to the model's reading of the revenue sentence (extract._derive_eur)" % (ok, n))
