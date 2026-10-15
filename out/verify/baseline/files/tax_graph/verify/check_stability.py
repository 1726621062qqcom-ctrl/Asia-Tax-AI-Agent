# -*- coding: utf-8 -*-
"""Does the 不稳定检查 (stability.py) notice a seeded instability, and classify it? The fingerprint workers (fp.py) read
VERIFY_FAULT and, when it is set, mark their results so that they depend on the order (the first case of a worker),
on PYTHONHASHSEED, on the engine's flow cache being warm, or on nothing reproducible. Without a fault nothing may be
flagged; with each fault the matching kind must be flagged. A small sample of the battery, read only.

    python -m tax_graph.verify.check_stability
"""
import io
import os
import shutil
import sys
import tempfile
from pathlib import Path

from .fp import battery_cases, run_fingerprint
from .results import ROOT
from .stability import stability_rows

EXPECT = [("no fault: nothing flagged", "", None),
          ("order dependence (first case of a worker marked)", "order", "order"),
          ("hash-seed dependence", "hash", "hash"),
          ("cache dependence (marked when served after another case)", "cache", "cache"),
          ("non-determinism (a random value)", "random", "NOD")]


def main():
    out = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    names = battery_cases()[::120][:8]
    jobs, bad = 2, 0
    tmp = Path(tempfile.mkdtemp(prefix="chk_stab_"))
    for label, fault, kind in EXPECT:
        if fault:
            os.environ["VERIFY_FAULT"] = fault
        else:
            os.environ.pop("VERIFY_FAULT", None)
        ref = run_fingerprint(names, jobs=jobs, hashseed=0)
        d = tmp / (fault or "none")
        d.mkdir(exist_ok=True)
        ctx = {"fingerprint": lambda: ref, "jobs": jobs, "sample": 1.0, "seed": 7, "dir": d, "root": ROOT}
        stability_rows(ctx)
        kinds = ctx["stability_kinds"]
        flagged = {k: len(v) for k, v in kinds.items() if v}
        if kind is None:
            ok = not flagged
        elif kind == "NOD":
            ok = bool(kinds["NOD"]) and not (kinds["order"] or kinds["cache"] or kinds["hash"])
        else:
            ok = bool(kinds[kind]) and not kinds["NOD"]
        bad += not ok
        out.write("%-4s %s (flagged: %s)\n" % ("ok" if ok else "FAIL", label, flagged or "none"))
    os.environ.pop("VERIFY_FAULT", None)
    shutil.rmtree(tmp, ignore_errors=True)
    out.write("%d checks, %d failures\n" % (len(EXPECT), bad))
    out.flush()
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
