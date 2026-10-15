"""Channel B by program: every Singapore party of the ten cases looked up in ACRA's register (data.gov.sg) by the name
a person wrote (extract_eval3.NAMES), against what the document says about it (the gold loc / incorporated_in and
the incorporation date in the gold quote), and the holding-vs-incorporation relation. Network, no key.

    python registry_check.py
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(r"C:\Coding\Projects\TUM\project_study_self")
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from tax_graph.llm.extract import dates_in          # noqa: E402
from tax_graph.registry import lookup, first_alias  # noqa: E402
import extract_eval as E                             # noqa: E402
from extract_eval3 import NAMES                      # noqa: E402

found = total = 0
for cid, (file, src, cur, roles) in E.CASES.items():
    case = json.loads((ROOT / file).read_text(encoding="utf-8"))
    for role, name in NAMES[cid].items():
        loc = case["roles"].get(role, {}).get("loc")
        if loc != "SG":
            continue
        total += 1
        try:
            recs = lookup("SG", name, live=True)
        except Exception as e:
            print("%-16s %-5s %-45s ERROR %s" % (cid, role, first_alias(name), e))
            continue
        pv = case.get("provenance", {}).get("roles.%s.attrs.incorporated_in" % role) or case.get("provenance", {}).get("roles.%s.loc" % role) or {}
        doc_dates = dates_in(pv.get("quote") or "")
        if not recs:
            print("%-16s %-5s %-45s not found" % (cid, role, first_alias(name)))
            continue
        found += 1
        r = recs[0]
        agree = "" if not doc_dates else ("date agrees" if any(d.isoformat() == r.get("incorporated_on") for d in doc_dates) else "date differs from document %s" % [d.isoformat() for d in doc_dates])
        since = [h.get("since") for h in case.get("holds", []) if h.get("held") == role]
        rel = ["since %s < incorporated %s !" % (s, r["incorporated_on"]) for s in since if s and r.get("incorporated_on") and s < r["incorporated_on"]]
        print("%-16s %-5s %-45s %s %s %s inc %s | %s %s" % (cid, role, first_alias(name), r["id"], r["name"], r["status"], r["incorporated_on"], agree, " ".join(rel)))
print("%d/%d Singapore parties found in ACRA" % (found, total))
