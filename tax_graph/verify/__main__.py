# -*- coding: utf-8 -*-
"""The runner (测试系统.md §5): one command runs every check of a tier, writes the rows in the unified format to
out/verify/<run_id>.jsonl, the module outputs and replay files to out/verify/<run_id>/, and updates out/verify/index.json.

    python -m tax_graph.verify --tier fast            every change: library constraints, rule compile, the check modules,
                                                      the grounding self-check, the gold snapshot (a few minutes)
    python -m tax_graph.verify --tier mid             after a feature: + battery, grounding of the gold cases, fingerprint,
                                                      attribution against the baseline, the instability sample
    python -m tax_graph.verify --tier full            before leaving: + planner contract, mutation score, instability on all cases
    python -m tax_graph.verify --tier mid --baseline  accept the current results: copy the snapshot files and fingerprint
                                                      that copy as the baseline later runs are attributed against
    python -m tax_graph.verify --only none --baseline take the baseline alone (no checks)
    python -m tax_graph.verify --list                 the registry
    options: --jobs N  --only id,id  --skip id,id  --order default|reverse|random [--seed S]  --sample F  --force

Exit code 1 when any row failed. The order of the checks is recorded with the run (L11): checks are independent
processes, so the order matters only through files they share; the case-level order checks are in stability.py.
"""
import argparse
import io
import os
import random
import sys
import time
import traceback

from . import registry as R
from .fp import battery_cases, run_fingerprint, take_baseline
from .results import OUT, ROOT, Run, version


def order_checks(checks, order, seed):
    if order == "reverse":
        return list(reversed(checks))
    if order == "random":
        rnd = random.Random(seed)
        groups = []
        for c in checks:
            if c.group not in groups:
                groups.append(c.group)
        rnd.shuffle(groups)
        out = []
        for g in groups:                                     # shuffle the groups, then within each group (L11's stratified order)
            members = [c for c in checks if c.group == g]
            rnd.shuffle(members)
            out += members
        return out
    return list(checks)


def main(argv):
    out = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(prog="python -m tax_graph.verify")
    ap.add_argument("--tier", choices=R.TIERS, default=R.FAST)
    ap.add_argument("--jobs", type=int, default=min(12, os.cpu_count() or 4))
    ap.add_argument("--only", default="")
    ap.add_argument("--skip", default="")
    ap.add_argument("--order", choices=("default", "reverse", "random"), default="default")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--sample", type=float, default=None, help="fraction of the battery the instability variants use (mid 0.25, full 1)")
    ap.add_argument("--baseline", action="store_true", help="store the fingerprints and snapshot files as the baseline")
    ap.add_argument("--force", action="store_true", help="store the baseline even when a row failed")
    ap.add_argument("--note", default="")
    ap.add_argument("--list", action="store_true")
    a = ap.parse_args(argv)
    if a.list:
        for c in R.REGISTRY:
            out.write("%-20s %-9s %-9s %-14s %s\n" % (c.id, c.layer, c.oracle, "/".join(c.tiers), c.note))
        out.flush()
        return 0
    seed = a.seed if a.seed is not None else random.randrange(1 << 30)
    sample = a.sample if a.sample is not None else (1.0 if a.tier == R.FULL else 0.25)
    run = Run(a.tier)
    rdir = OUT / run.run_id
    rdir.mkdir(parents=True, exist_ok=True)
    run.meta = {"order": a.order, "seed": seed, "jobs": a.jobs, "sample": sample, "note": a.note, "argv": argv}
    ctx = {"jobs": a.jobs, "tier": a.tier, "dir": rdir, "root": ROOT, "seed": seed, "sample": sample, "version": run.version}
    memo = {}

    def fingerprint():
        if "fp" not in memo:
            dest = rdir / "fingerprint.json"
            fps, meta = run_fingerprint(battery_cases(), jobs=a.jobs, hashseed=0, out_path=dest)
            meta["out"] = str(dest)
            memo["fp"] = (fps, meta)
        return memo["fp"]
    ctx["fingerprint"] = fingerprint

    checks = [R.with_jobs(c, a.jobs) for c in R.REGISTRY if a.tier in c.tiers]
    if a.only:
        want = set(a.only.split(","))                      # "--only none --baseline" takes a baseline without running checks
        checks = [c for c in checks if c.id in want]
    if a.skip:
        skip = set(a.skip.split(","))
        checks = [c for c in checks if c.id not in skip]
    checks = order_checks(checks, a.order, seed)
    run.meta["checks"] = [c.id for c in checks]
    out.write("run %s  tier %s  version %s  jobs %d  order %s seed %d\n" % (run.run_id, a.tier, run.version["short"], a.jobs, a.order, seed))
    out.flush()
    for c in checks:
        t0 = time.time()
        try:
            rows = c.run(ctx)
        except Exception:                                    # noqa: BLE001 — a check that cannot run is a failure, not a skip
            rows = [{"layer": c.layer, "check_id": c.id, "subject": "system/" + c.id, "status": "fail",
                     "measured": traceback.format_exc().splitlines()[-1][:300], "expected": "", "oracle": c.oracle, "evidence": "runner"}]
        secs = time.time() - t0
        run.extend(rows, seconds=round(secs, 1))
        worst = run.by_check().get(c.id, {})
        sysrow = next((r for r in rows if r["subject"].startswith("system")), rows[-1] if rows else {})
        out.write("%-20s %-4s %7.1fs  %s\n" % (c.id, worst.get("status", "?"), secs, sysrow.get("measured", "")[:110]))
        out.flush()
    now = version()
    if now != run.version:                                   # the tree changed while the checks ran: the rows are not one state
        changed = [k for k in ("code", "library", "cases") if now[k] != run.version[k]]
        run.add("C", "C-run", "system/tree changed during the run", "warn",
                measured="%s changed between the start (%s) and the end (%s) of the run" % (", ".join(changed), run.version["short"], now["short"]),
                expected="one version for all rows", oracle="snapshot", evidence="results.version()")
        out.write("warning: the %s changed during the run (%s -> %s): rows do not describe one state\n" % (", ".join(changed), run.version["short"], now["short"]))
    counts = run.counts()
    if a.baseline:
        if counts["fail"] and not a.force:
            out.write("baseline NOT stored: %d rows failed (use --force to store anyway)\n" % counts["fail"])
        else:
            meta = take_baseline(run.run_id, jobs=a.jobs, note=a.note)
            run.meta["baseline_stored"] = meta
            out.write("baseline stored: %d cases (%d errors), %d files, version %s, %.0f s\n" % (
                meta["cases"], len(meta["errors"]), meta["files"], meta["version"]["short"], meta["seconds"]))
    path = run.finish()
    out.write("%d rows: pass %d, warn %d, fail %d, na %d  (%.0f s) -> %s\n" % (
        len(run.records), counts["pass"], counts["warn"], counts["fail"], counts["na"], time.time() - run.started, path.relative_to(ROOT).as_posix()))
    out.flush()
    return 1 if counts["fail"] else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
