"""The checks the runner (python -m tax_graph.verify) runs, by layer and tier (测试系统.md §2, §5).

Each entry names the layer, the oracle kind and the tiers it belongs to, and returns rows in the unified format
(results.py; run_id, version and seconds are stamped by the runner). Existing modules run in their own interpreter
(`python -m tax_graph.<module>`): their stdout lines "ok ..." / "FAIL ..." / "DIFF ..." become one row each, the exit
code one row for the module (subject system/<module>). Nothing here decides anything a check did not.

Tiers (§5): fast — every change, a few minutes; mid — after a feature; full — before leaving.
"""
import json
import os
import re
import sqlite3
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Tuple

from .results import OUT, ROOT

PY = sys.executable
ITEM = re.compile(r"^(ok|FAIL|DIFF|CHANGED|GONE)\s+(.+?)\s*$")
SUMMARY = re.compile(r"\b\d+ (checks|labels|candidates|cells|rows|rules|cases|defects|differ)\b")
FAST, MID, FULL = "fast", "mid", "full"
TIERS = (FAST, MID, FULL)
ALL = (FAST, MID, FULL)


@dataclass
class Check:
    id: str
    layer: str
    oracle: str
    tiers: Tuple[str, ...]
    run: Callable
    group: str = "module"                    # stratum for the runner's random order (module -> check -> case)
    note: str = ""
    needs: Tuple[str, ...] = field(default_factory=tuple)


def run_python(args, timeout=3600, cwd=None, env=None):
    """A python subprocess with utf-8 stdout; returns (returncode, stdout+stderr)."""
    e = dict(os.environ, PYTHONIOENCODING="utf-8")
    if env:
        e.update(env)
    r = subprocess.run([PY] + list(args), cwd=str(cwd or ROOT), env=e, capture_output=True, text=True,
                       encoding="utf-8", errors="replace", timeout=timeout)
    return r.returncode, (r.stdout or "") + (("\n" + r.stderr) if r.stderr else "")


def summary_line(text):
    lines = [x.strip() for x in text.splitlines() if x.strip()]
    for line in reversed(lines):
        if SUMMARY.search(line):
            return line
    return lines[-1] if lines else ""


def module_rows(cid, layer, oracle, module, rc, text, items=True, warn_rc=False, fail_pattern=None):
    """One row per "ok|FAIL|DIFF" line (when `items`) and one system row from the exit code."""
    rows = []
    if items:
        for line in text.splitlines():
            m = ITEM.match(line)
            if m:
                subject, measured = m.group(2), ""
                if m.group(1) == "CHANGED" and " was " in subject:            # data.gold: "CHANGED <key> was <row>"
                    subject, measured = subject.split(" was ", 1)
                    measured = "was " + measured
                rows.append({"layer": layer, "check_id": cid, "subject": subject.strip()[:160],
                             "status": "pass" if m.group(1) == "ok" else "fail", "measured": measured[:300], "expected": "",
                             "oracle": oracle, "evidence": "python -m tax_graph." + module})
    status = "pass" if rc == 0 else ("warn" if warn_rc else "fail")
    if fail_pattern and re.search(fail_pattern, text):
        status = "fail"
    if "Traceback (most recent call last)" in text:
        status = "fail"
    rows.append({"layer": layer, "check_id": cid, "subject": "system/" + module, "status": status,
                 "measured": summary_line(text)[:300], "expected": "exit 0", "oracle": oracle,
                 "evidence": "python -m tax_graph." + module})
    return rows


def module_check(cid, layer, oracle, module, tiers, args=(), timeout=3600, items=True, warn_rc=False, group="module",
                 fail_pattern=None, post=None, note=""):
    def run(ctx):
        rc, text = run_python(["-m", "tax_graph." + module] + list(args), timeout=timeout)
        rows = module_rows(cid, layer, oracle, module, rc, text, items=items, warn_rc=warn_rc, fail_pattern=fail_pattern)
        (ctx["dir"] / (module + ".txt")).write_text(text, encoding="utf-8")
        if post:
            rows += post(ctx, rc, text)
        return rows
    return Check(cid, layer, oracle, tiers, run, group=group, note=note)


# ---------------------------------------------------------------- A library and rules
def library_constraints(ctx):
    """E01–E07 / W01–W07 as the last build of official/official.sqlite recorded them (graph.py CONSTRAINTS)."""
    db = ROOT / "official" / "official.sqlite"
    rows = []
    if not db.exists():
        return [{"layer": "A", "check_id": "A-constraints", "subject": "system/official.sqlite", "status": "na",
                 "measured": "official.sqlite missing", "expected": "", "oracle": "invariant", "evidence": "official/tools/graph.py"}]
    newest = max((ROOT / "official" / n).stat().st_mtime for n in ("params.csv", "clauses.csv", "decisions.csv") if (ROOT / "official" / n).exists())
    stale = db.stat().st_mtime < newest
    con = sqlite3.connect(str(db))
    try:
        res = con.execute("SELECT id, severity, description, violations, sample FROM constraint_result ORDER BY id").fetchall()
    finally:
        con.close()
    for cid_, sev, what, n, sample in res:
        status = "pass" if not n else ("fail" if sev == "Error" else "warn")
        rows.append({"layer": "A", "check_id": "A-constraints", "subject": "rule/%s %s" % (cid_, what), "status": status,
                     "measured": str(n), "expected": "0", "oracle": "invariant", "evidence": (sample or "")[:300]})
    rows.append({"layer": "A", "check_id": "A-constraints", "subject": "system/official.sqlite", "status": "warn" if stale else "pass",
                 "measured": "index older than params/clauses/decisions.csv: rebuild" if stale else "index current",
                 "expected": "python official/tools/graph.py after a library change", "oracle": "invariant",
                 "evidence": time.strftime("%Y-%m-%d %H:%M", time.localtime(db.stat().st_mtime))})
    return rows


def rules_post(ctx, rc, text):
    m = re.search(r"orphan rate/condition parameters in scope: (\d+)", text)
    n = int(m.group(1)) if m else -1
    return [{"layer": "A", "check_id": "A-rules", "subject": "rule/orphan parameters", "status": "pass" if n == 0 else "warn",
             "measured": str(n), "expected": "0", "oracle": "invariant", "evidence": "python -m tax_graph.rules"}]


def coverage_post(ctx, rc, text):
    m = re.search(r"(\d+) cells, (\d+) missing", text)
    missing = int(m.group(2)) if m else -1
    return [{"layer": "A", "check_id": "A-coverage", "subject": "rule/coverage matrix", "status": "pass" if missing == 0 else "warn",
             "measured": "%s missing" % missing, "expected": "0 missing", "oracle": "invariant", "evidence": "python -m tax_graph.check_coverage"}]


# ---------------------------------------------------------------- B computational correctness
def battery_post(ctx, rc, text):
    rows = []
    m = re.search(r"cases: (\d+), clean: (\d+), with defects: (\d+)", text)
    if m:
        defects = int(m.group(3))
        rows.append({"layer": "B", "check_id": "B-battery", "subject": "system/battery cases", "status": "pass" if defects == 0 else "fail",
                     "measured": "cases %s, clean %s, defects %s" % m.groups(), "expected": "0 defects", "oracle": "invariant",
                     "evidence": "out/battery_report.md"})
    rep = ROOT / "out" / "battery_report.md"
    if rep.exists():
        sect, case = None, None
        for line in rep.read_text(encoding="utf-8").splitlines():
            if line.startswith("## "):
                sect = line[3:].strip()
                continue
            if sect == "defects" and line.startswith("- **"):
                case = line[4:].split("**")[0]
            elif sect == "defects" and line.startswith("  - ") and case:
                rows.append({"layer": "B", "check_id": "B-battery", "subject": "case/" + case, "status": "fail", "measured": line[4:][:300],
                             "expected": "", "oracle": "invariant", "evidence": "out/battery_report.md"})
    m = re.search(r"rules never fired: (\d+) of (\d+)", text)
    if m:
        never, total = int(m.group(1)), int(m.group(2))
        rows.append({"layer": "adequacy", "check_id": "adequacy-fired", "subject": "rule/never fired in the battery", "status": "pass" if never == 0 else "warn",
                     "measured": "%d of %d" % (never, total), "expected": "0 (sg.s10l.not_in_force is covered by K2.SGL1)",
                     "oracle": "invariant", "evidence": "out/battery_report.md"})
    m = re.search(r"thresholds live (\d+) of (\d+) tried", text)
    if m:
        rows.append({"layer": "adequacy", "check_id": "adequacy-thresholds", "subject": "rule/boundary values", "status": "pass",
                     "measured": "live %s of %s tried" % m.groups(), "expected": "", "oracle": "invariant", "evidence": "out/battery_report.md"})
    return rows


def real_cases():
    """The real (K4) and semi-synthetic (K3) case files of phase 1 (cases/v2 is phase 2)."""
    return sorted(p for d in ("real", "semisynth") for p in (ROOT / "cases" / d).glob("*.json") if not p.name.endswith(".answers.json"))


def grounding_run(ctx, cid, args, label):
    """Grounding check: runs grounding.py and ingests the rows it wrote (they are already in the unified format)."""
    t0 = time.time()
    rc, text = run_python(["-m", "tax_graph.verify.grounding"] + list(args), timeout=4 * 3600)
    (ctx["dir"] / (cid + ".txt")).write_text(text, encoding="utf-8")
    rows = []
    for p in sorted(OUT.glob("grounding_*.jsonl")):
        if p.stat().st_mtime < t0 - 1:
            continue
        with open(str(p), encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    r = json.loads(line)
                    if r.get("status") == "info":
                        r["status"] = "pass"
                    rows.append({"layer": "grounding", "check_id": "grounding-" + r["check_id"], "subject": r["subject"], "status": r["status"],
                                 "measured": r.get("measured", ""), "expected": r.get("expected", ""), "oracle": "official",
                                 "evidence": r.get("evidence", "")})
    rows.append({"layer": "grounding", "check_id": cid, "subject": "system/" + label, "status": "pass" if rc == 0 and rows else "fail",
                 "measured": summary_line(text)[:300], "expected": "exit 0", "oracle": "official",
                 "evidence": "python -m tax_graph.verify.grounding " + " ".join(str(a) for a in args)[:200]})
    return rows


def grounding_gold(ctx):
    return grounding_run(ctx, "grounding-gold", ["--gold"], "grounding --gold")


def grounding_real(ctx):
    return grounding_run(ctx, "grounding-real", [str(p) for p in real_cases()], "grounding of the real and semi-synthetic cases")


def casecheck_real(ctx):
    """Case check (案例采集.md §3 step 5) of every real and semi-synthetic case file."""
    paths = real_cases()
    rc, text = run_python(["-m", "tax_graph.verify.casecheck"] + [str(p) for p in paths], timeout=3600)
    (ctx["dir"] / "casecheck.txt").write_text(text, encoding="utf-8")
    rows = []
    for line in text.splitlines():
        m = re.match(r"^(PASS|ERROR)\s+(\S+)", line)
        if m:
            rows.append({"layer": "grounding", "check_id": "grounding-casecheck", "subject": "case/" + m.group(2), "status": "pass" if m.group(1) == "PASS" else "fail",
                         "measured": line[:300], "expected": "", "oracle": "invariant", "evidence": "python -m tax_graph.verify.casecheck"})
    rows.append({"layer": "grounding", "check_id": "grounding-casecheck", "subject": "system/casecheck %d cases" % len(paths), "status": "pass" if rc == 0 else "fail",
                 "measured": "%d cases, %d with errors" % (len(paths), sum(r["status"] == "fail" for r in rows)), "expected": "exit 0",
                 "oracle": "invariant", "evidence": "python -m tax_graph.verify.casecheck"})
    return rows


# ---------------------------------------------------------------- D / adequacy
def planner_post(ctx, rc, text):
    rows = []
    m = re.search(r"(\d+) defects", text)
    if m:
        rows.append({"layer": "D", "check_id": "D-planner", "subject": "system/planner contract", "status": "pass" if m.group(1) == "0" else "fail",
                     "measured": summary_line(text)[:300], "expected": "0 defects", "oracle": "derived", "evidence": "python -m tax_graph.check_planner"})
    return rows


def mutation_post(ctx, rc, text):
    rows = []
    p = ROOT / "out" / "mutation.json"
    if p.exists():
        m = json.loads(p.read_text(encoding="utf-8"))
        rows.append({"layer": "adequacy", "check_id": "adequacy-mutation", "subject": "system/mutation score", "status": "pass",
                     "measured": "killed %d of %d (rejected %d) on %d cases" % (m["killed"], m["total"], m.get("rejected", 0), m["cases"]),
                     "expected": "", "oracle": "invariant", "evidence": "out/mutation_report.md"})
        for s in m.get("survivors", []):
            rows.append({"layer": "adequacy", "check_id": "adequacy-mutation", "subject": "rule/" + s, "status": "warn", "measured": "survived",
                         "expected": "killed", "oracle": "invariant", "evidence": "out/mutation_report.md"})
    return rows


def _fp_check(ctx):
    from .attribution import fingerprint_rows
    return fingerprint_rows(ctx)


def _attrib_check(ctx):
    from .attribution import attribution_rows
    return attribution_rows(ctx)


def _stability_check(ctx):
    from .stability import stability_rows
    return stability_rows(ctx)


REGISTRY = [
    # A library and rules
    Check("A-constraints", "A", "invariant", ALL, library_constraints, group="library"),
    module_check("A-rules", "A", "invariant", "rules", ALL, items=False, post=rules_post),
    module_check("A-coverage", "A", "invariant", "check_coverage", ALL, items=False, post=coverage_post),
    module_check("A-fields", "A", "invariant", "check_fields", ALL, items=False),
    # B computational correctness — the check modules
    module_check("B-scope", "B", "statute", "check_scope", ALL),
    module_check("B-engine", "B", "invariant", "check_engine", ALL),
    module_check("B-entity", "B", "statute", "check_entity", ALL),
    module_check("B-flow_tax", "B", "statute", "check_flow_tax", ALL),
    module_check("B-hk_tax", "B", "statute", "check_hk_tax", ALL),
    module_check("B-cn_wht", "B", "statute", "check_cn_wht", ALL),
    module_check("B-sg_s45", "B", "official", "check_sg_s45", ALL),
    module_check("B-examples", "B", "official", "check_examples", ALL),
    module_check("B-extract", "B", "invariant", "check_extract", ALL),
    module_check("B-pipeline", "B", "invariant", "check_pipeline", (MID, FULL), note="端到端.md: scripted model, register off, gates, resume, case check, planning"),
    module_check("B-ui", "B", "invariant", "check_ui", ALL, note="界面.md: routes of the local page, path restrictions, review and answer write-back"),
    module_check("B-precedent", "B", "derived", "check_precedent", ALL),
    module_check("grounding-selfcheck", "grounding", "invariant", "verify.check_grounding", ALL, items=True),
    Check("grounding-gold", "grounding", "official", (MID, FULL), grounding_gold, group="grounding"),
    Check("grounding-casecheck", "grounding", "invariant", (MID, FULL), casecheck_real, group="grounding"),
    Check("grounding-real", "grounding", "official", (FULL,), grounding_real, group="grounding"),
    # the tests of the tests: seeded faults the C-layer checks must notice
    module_check("C-selfcheck", "C", "invariant", "verify.check_stability", (FULL,), items=True, group="selfcheck",
                 note="seeded order / hash-seed / cache / random instabilities are detected and classified"),
    module_check("C-selfcheck-attr", "C", "invariant", "verify.check_attribution", (FULL,), items=True, group="selfcheck",
                 note="seeded changes (a parameter, a case file, an inert comment) are attributed to the right files"),
    module_check("B-battery", "B", "invariant", "battery", (MID, FULL), args=("--run-only",), items=False, post=battery_post, group="battery"),
    # C result stability
    module_check("C-gold", "C", "snapshot", "data.gold", ALL, items=True),
    Check("C-fingerprint", "C", "snapshot", (MID, FULL), _fp_check, group="fingerprint"),
    Check("C-attribution", "C", "snapshot", (MID, FULL), _attrib_check, group="fingerprint", needs=("C-fingerprint",)),
    Check("C-stability", "C", "invariant", (MID, FULL), _stability_check, group="fingerprint", needs=("C-fingerprint",)),
    # D plan superiority
    module_check("D-planner", "D", "derived", "check_planner", (FULL,), items=False, post=planner_post, group="planner", timeout=4 * 3600),
    # adequacy
    module_check("adequacy-mutation", "adequacy", "invariant", "mutation", (FULL,), items=False, post=mutation_post, group="mutation", timeout=4 * 3600),
]

# modules that take --jobs
PARALLEL = {"B-battery": "battery", "D-planner": "check_planner", "adequacy-mutation": "mutation"}


def with_jobs(check, jobs):
    """The same check with --jobs appended (battery, planner, mutation)."""
    if check.id not in PARALLEL or jobs <= 1:
        return check
    module = PARALLEL[check.id]
    base = dict(cid=check.id, layer=check.layer, oracle=check.oracle, module=module, tiers=check.tiers, items=False, group=check.group)
    post = {"B-battery": battery_post, "D-planner": planner_post, "adequacy-mutation": mutation_post}[check.id]
    args = ("--run-only", "--jobs", str(jobs)) if check.id == "B-battery" else ("--jobs", str(jobs))
    return module_check(args=args, post=post, timeout=4 * 3600, **base)
