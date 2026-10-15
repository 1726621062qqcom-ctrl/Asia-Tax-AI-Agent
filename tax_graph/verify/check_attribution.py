# -*- coding: utf-8 -*-
"""Does the attribution (attribution.py) name the right files? A scratch project (the runtime files and a sample of the
battery) gets a baseline; then three seeded changes: the Mainland withholding rate in params.csv, one case's dividend
amount in its json, and an inert comment carrying a seeded decision token (D plus 99, written split so the library scan does not take it for a real reference) in a module the fingerprint never imports. Every case that
differs must be attributed to params.csv or to the changed case file, never to the inert module, and the changed case
must be attributed to its own file; a run without changes must report no difference.

    python -m tax_graph.verify.check_attribution
"""
import csv
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from .fp import battery_cases
from .results import ROOT, RUNTIME_SETS, files_of

PY = sys.executable


def run_verify(proj, args):
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    env.pop("VERIFY_FAULT", None)
    r = subprocess.run([PY, "-m", "tax_graph.verify"] + args, cwd=str(proj), env=env, capture_output=True, text=True,
                       encoding="utf-8", errors="replace", timeout=3600)
    runs = sorted((proj / "out" / "verify").glob("*-mid.jsonl"))
    rows = []
    if runs:
        with open(str(runs[-1]), encoding="utf-8") as f:
            rows = [json.loads(line) for line in f if line.strip()]
    return r.returncode, r.stdout + r.stderr, rows


def main():
    out = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    proj = Path(tempfile.mkdtemp(prefix="chk_attr_"))
    grid = [n for n in battery_cases() if "__" not in n]
    sample = [n for n in grid if n.startswith("holding_OPCN")][:6] + [n for n in grid if not n.startswith("holding_OPCN")][::60][:6]
    for rel in files_of(RUNTIME_SETS):
        if rel.startswith("cases/battery/") and Path(rel).name not in sample:
            continue
        dst = proj / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / rel, dst)
    results = []

    rc, text, rows = run_verify(proj, ["--tier", "mid", "--only", "C-fingerprint", "--baseline", "--jobs", "3", "--note", "check_attribution"])
    results.append(("baseline stored in the scratch project", "baseline stored" in text, text.strip().splitlines()[-2:]))

    rc, text, rows = run_verify(proj, ["--tier", "mid", "--only", "C-fingerprint,C-attribution", "--jobs", "3"])
    att = [r for r in rows if r["check_id"] == "C-attribution"]
    results.append(("no change: 0 cases differ", any(r["subject"].startswith("system") and r["status"] == "pass" and "0 cases differ" in r["measured"] for r in att), [r["measured"] for r in att][:2]))

    # seeded changes
    params = proj / "official" / "params.csv"
    with open(str(params), encoding="utf-8-sig", newline="") as f:
        rd = csv.DictReader(f)
        fields, prow = rd.fieldnames, list(rd)
    for r in prow:
        if r["param_id"] == "cn.wht.rate":               # the compiler requires the value to occur in the quote: change both
            old_v, new_v = r["value"], "9"
            assert old_v in r["quote"], "cn.wht.rate value %r not in its quote" % old_v
            r["value"], r["quote"] = new_v, r["quote"].replace(old_v, new_v, 1)
    with open(str(params), "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(prow)
    changed_case = sample[0]
    cpath = proj / "cases" / "battery" / changed_case
    d = json.loads(cpath.read_text(encoding="utf-8"))
    d["event"]["dividend"] = float(d["event"]["dividend"]) * 2
    cpath.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
    inert = proj / "tax_graph" / "verify" / "casecheck.py"
    inert.write_text(inert.read_text(encoding="utf-8") + "\n# seeded inert change (decision D" + "99)\n", encoding="utf-8")

    rc, text, rows = run_verify(proj, ["--tier", "mid", "--only", "C-fingerprint,C-attribution", "--jobs", "3"])
    att = [r for r in rows if r["check_id"] == "C-attribution"]
    cases = [r for r in att if r["subject"].startswith("case/")]
    files_of_case = {}
    for r in cases:
        m = r["measured"]
        files_of_case[r["subject"][len("case/"):]] = set(x.strip() for x in m.split("files: ", 1)[1].split(";")[0].split(",")) if "files: " in m else set()
    results.append(("some cases differ after the seeded changes", bool(cases), [r["measured"] for r in att if r["subject"].startswith("system")]))
    results.append(("every differing case attributed (none failed)", bool(cases) and all(r["status"] == "warn" for r in cases),
                    [r["subject"] + ": " + r["measured"][:80] for r in cases if r["status"] != "warn"][:3]))
    results.append(("the inert module is never named", all("tax_graph/verify/casecheck.py" not in fs for fs in files_of_case.values()),
                    [c for c, fs in files_of_case.items() if "tax_graph/verify/casecheck.py" in fs][:3]))
    results.append(("the seeded decision of the inert module never named", all("D99" not in r["measured"] for r in cases), []))
    stem = changed_case[:-5]
    results.append(("the changed case is attributed to its own file", "cases/battery/" + changed_case in files_of_case.get(stem, set()),
                    sorted(files_of_case.get(stem, set()))))
    others = {c: fs for c, fs in files_of_case.items() if c != stem}
    results.append(("the other differing cases are attributed to params.csv alone", bool(others) and all(fs == {"official/params.csv"} for fs in others.values()),
                    [(c, sorted(fs)) for c, fs in others.items() if fs != {"official/params.csv"}][:3]))
    bad = 0
    for label, ok, detail in results:
        bad += not ok
        out.write("%-4s %s%s\n" % ("ok" if ok else "FAIL", label, ("  %s" % (detail,)) if (not ok and detail) else ""))
    out.write("%d checks, %d failures\n" % (len(results), bad))
    if os.environ.get("VERIFY_KEEP"):
        out.write("scratch project kept: %s\n" % proj)
    else:
        shutil.rmtree(proj, ignore_errors=True)
    out.flush()
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
