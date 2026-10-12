"""Read-only Li release audit. Usage: python audit_release.py SNAPSHOT OUTPUT_DIR."""
import csv
import hashlib
import json
import re
import sqlite3
import sys
from pathlib import Path

root = Path(sys.argv[1]).resolve()
out = Path(sys.argv[2]).resolve()
out.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(root))
sys.path.insert(0, str(root / "official/tools"))
from tax_graph.params import Params
from tax_graph.rules.compile import CompileError, compile_rules
from tax_graph.rules.spec import SPEC
from search import Library

csv.field_size_limit(10**9)
def csv_rows(name):
    with (root / "official" / name).open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))

db = root / "official/official.sqlite"
con = sqlite3.connect(db.as_uri() + "?mode=ro", uri=True)
con.row_factory = sqlite3.Row
counts = {t: con.execute('SELECT COUNT(*) FROM "' + t + '"').fetchone()[0]
          for t in ("doc", "clause", "param", "form_field", "unit", "edge", "decision", "decision_ref", "unit_vec")}
integrity = [x[0] for x in con.execute("PRAGMA integrity_check")]
P = Params()
try:
    rules = compile_rules(SPEC, P)
    errors = []
except CompileError as exc:
    errors = str(exc).splitlines()

missing = {"parameter": {}, "clause": {}}
other_errors = []
for line in errors:
    m = re.match(r"(.+?): parameter not in params\.csv: (\S+)$", line)
    kind = "parameter"
    if not m:
        m = re.match(r"(.+?): (?:clause not in library|evaluator cites a clause not in the library): (\S+)$", line)
        kind = "clause"
    if m:
        missing[kind].setdefault(m[2], set()).add(m[1])
    else:
        other_errors.append(line)
missing = {k: {ref: sorted(ids) for ref, ids in sorted(v.items())} for k, v in missing.items()}
csv_params = {r["param_id"]: r for r in csv_rows("params.csv")}
db_params = {r["param_id"]: dict(r) for r in con.execute("SELECT * FROM param")}
csv_clauses = {r["cite_id"] for r in csv_rows("clauses.csv")}
db_clauses = {r[0] for r in con.execute("SELECT cite_id FROM clause")}
decisions = {r[0] for r in con.execute("SELECT DISTINCT id FROM decision")}
code_decisions = set()
for path in (root / "tax_graph").rglob("*.py"):
    code_decisions.update(re.findall(r"口径\s+(D\d+)", path.read_text(encoding="utf-8")))

# Library only reads during initialization; enforce read-only queries for probes too.
lib = Library(db)
lib.con.execute("PRAGMA query_only = ON")
probes = []
for query, channels in [("hk.cap112.en#s15H", ("exact",)),
                        ("foreign-sourced income exemption", ("bm25",))]:
    hits = lib.search(query, k=3, jur="HK", channels=channels, today="2026-10-11")
    result = {"query": query, "channels": list(channels), "hit_count": len(hits), "hits": []}
    for h in hits:
        ground = lib.ground(h.snippet, h.cite_id)
        result["hits"].append({"cite_id": h.cite_id, "span": list(h.span),
                               "ground_ok": ground["ok"], "occurrences": ground.get("occurrences"),
                               "snippet_sha256": hashlib.sha256(h.snippet.encode()).hexdigest()})
    probes.append(result)
lib.con.close()

report = {
    "commit": "c8a4cf7a59ef9d8895cd115ce2e4df66850b30e2",
    "snapshot": str(root), "audit_date": "2026-10-11", "python": sys.version,
    "database_bytes": db.stat().st_size,
    "database_sha256": hashlib.sha256(db.read_bytes()).hexdigest(),
    "integrity_check": integrity, "row_counts": counts,
    "spec_rule_count": len(SPEC), "compile_passed": not errors,
    "compile_error_lines": len(errors),
    "affected_rule_count": len({line.split(": ", 1)[0] for line in errors}),
    "missing_parameter_count": len(missing["parameter"]),
    "missing_clause_count": len(missing["clause"]),
    "missing_references": missing, "other_compile_errors": other_errors,
    "params_csv_database_rows_equal": csv_params == db_params,
    "clause_id_sets_equal": csv_clauses == db_clauses,
    "missing_compile_clauses_also_absent_from_csv": sorted(set(missing["clause"]) - csv_clauses),
    "database_decisions": sorted(decisions),
    "code_decisions_absent_from_database": sorted(code_decisions - decisions),
    "extraction_document_present": (root / "信息收集.md").exists(),
    "battery_json_count": len(list((root / "cases/battery").glob("*.json"))),
    "battery_generator_present": (root / "tax_graph/battery.py").exists(),
    "builtin_gold_files": sorted(str(p.relative_to(root)) for p in (root / "tax_graph/data/gold").glob("*.json")),
    "search_probes": probes,
    "limits": ["No end-to-end planner execution: engine imports fail at rule compilation.",
               "Search probes do not establish scenario coverage, legal correctness, or HTTP integration.",
               "Dense retrieval, full battery, PostgreSQL, UI, and live LLM were not tested."]
}
con.close()
(out / "release_audit.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
(out / "compile_errors.txt").write_text("\n".join(errors) + "\n", encoding="utf-8")
with (out / "missing_references.csv").open("w", encoding="utf-8", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["kind", "reference", "affected_rules"])
    for kind, refs in missing.items():
        for ref, rules in refs.items():
            writer.writerow([kind, ref, ";".join(rules)])
print(json.dumps({k: v for k, v in report.items() if k not in ("missing_references", "python")}, ensure_ascii=False, indent=2))
