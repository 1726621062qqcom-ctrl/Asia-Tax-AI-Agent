"""Fingerprints under controlled conditions (layer C, 测试系统.md §2): the ex-ante table of every case (fingerprint.py's
record), computed by worker processes that each take one contiguous slice of the case list in the given order, with the
hash seed fixed, and with the engine's flow cache on or off. The driver runs the computation in a subprocess so that
PYTHONHASHSEED and the working tree (attribution.py's scratch copy) can be chosen per run.

    python -m tax_graph.verify.fp --list CASES.json --out FP.json [--jobs N] [--no-cache]

Also the baseline store (out/verify/baseline/): the fingerprint of every battery case plus a copy of every file of the
snapshot sets (results.SNAPSHOT_SETS), taken when results were last accepted; attribution.py diffs the tree against it.
"""
import json
import os
import random
import shutil
import subprocess
import sys
import tempfile
import time
from multiprocessing import Process
from pathlib import Path

from .results import OUT, ROOT, snapshot_files, version

BASELINE = OUT / "baseline"
PY = sys.executable
CASE_DIR = ROOT / "cases" / "battery"


def battery_cases():
    return sorted(p.name for p in CASE_DIR.glob("*.json"))


# ---------------------------------------------------------------- worker side
def _slice_main(names, dest, no_cache, workdir):
    import io
    import traceback
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    os.chdir(workdir)
    try:
        from .. import engine as E
        from ..fingerprint import fingerprint_case
    except Exception:                                      # noqa: BLE001 — the tree does not even import: say why per case
        err = traceback.format_exc().splitlines()[-1]
        Path(dest).write_text(json.dumps({n[:-5]: {"error": "import: " + err} for n in names}, ensure_ascii=False), encoding="utf-8")
        return
    if no_cache:
        E._CACHE_MAX = 0                                   # every insert clears: no result is ever served from the cache
        E._FLOW_CACHE.clear()
    fault = os.environ.get("VERIFY_FAULT", "")             # check_stability.py seeds an instability the check must notice
    res = {}
    for i, n in enumerate(names):
        try:
            res[n[:-5]] = fingerprint_case(Path("cases") / "battery" / n)
        except Exception as e:                             # noqa: BLE001
            res[n[:-5]] = {"error": "%s: %s" % (type(e).__name__, e)}
        if fault == "order" and i == 0:
            res[n[:-5]]["_seeded"] = "first in its worker"  # depends on the order: the first case of a worker is marked
        elif fault == "hash":
            res[n[:-5]]["_seeded"] = hash("seeded") % 1000  # depends on PYTHONHASHSEED
        elif fault == "random":
            res[n[:-5]]["_seeded"] = random.random()        # depends on nothing reproducible
        elif fault == "cache" and not no_cache and i > 0:
            res[n[:-5]]["_seeded"] = "served after another case"   # present only when the cache is on and warm
    Path(dest).write_text(json.dumps(res, ensure_ascii=False, sort_keys=True), encoding="utf-8")


def compute(names, jobs, no_cache=False, workdir=None):
    """names in the order they are to be processed; worker k takes names[k::jobs] in that order (striped: a case list
    sorted by template does not put every expensive template on one worker), one process per worker."""
    workdir = str(workdir or os.getcwd())
    jobs = max(1, min(jobs, len(names)))
    slices = [names[k::jobs] for k in range(jobs)]
    tmp = tempfile.mkdtemp(prefix="fp_")
    procs = []
    for i, sl in enumerate(slices):
        p = Process(target=_slice_main, args=(sl, os.path.join(tmp, "%d.json" % i), no_cache, workdir))
        p.start()
        procs.append(p)
    res = {}
    for i, p in enumerate(procs):
        p.join()
        f = os.path.join(tmp, "%d.json" % i)
        if p.exitcode == 0 and os.path.exists(f):
            res.update(json.loads(Path(f).read_text(encoding="utf-8")))
        else:
            for n in slices[i]:
                res[n[:-5]] = {"error": "worker exit %s" % p.exitcode}
    shutil.rmtree(tmp, ignore_errors=True)
    return res


# ---------------------------------------------------------------- driver side
def ordered(names, order="default", seed=None):
    names = list(names)
    if order == "reverse":
        names.reverse()
    elif order == "random":
        random.Random(seed).shuffle(names)
    return names


def run_fingerprint(names, jobs=4, order="default", seed=None, hashseed=0, no_cache=False, workdir=None, out_path=None,
                    timeout=7200):
    """Runs the computation in a fresh interpreter. Returns (fingerprints, meta); meta records the exact order, the
    seeds and the command so that a difference can be replayed."""
    workdir = Path(workdir or ROOT)
    names = ordered(names, order, seed)
    tmp = Path(tempfile.mkdtemp(prefix="fplist_"))
    lst, dest = tmp / "cases.json", Path(out_path) if out_path else tmp / "fp.json"
    lst.write_text(json.dumps(names), encoding="utf-8")
    cmd = [PY, "-m", "tax_graph.verify.fp", "--list", str(lst), "--out", str(dest), "--jobs", str(jobs)] + (["--no-cache"] if no_cache else [])
    env = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONHASHSEED=str(hashseed))
    t0 = time.time()
    r = subprocess.run(cmd, cwd=str(workdir), env=env, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout)
    meta = {"order": order, "seed": seed, "hashseed": hashseed, "no_cache": no_cache, "jobs": jobs, "workdir": str(workdir),
            "cases": names, "seconds": round(time.time() - t0, 1), "returncode": r.returncode,
            "command": "PYTHONHASHSEED=%s %s" % (hashseed, " ".join(cmd)), "stderr": r.stderr[-2000:]}
    fps = json.loads(dest.read_text(encoding="utf-8")) if dest.exists() else {}
    if not out_path:
        shutil.rmtree(tmp, ignore_errors=True)
    return fps, meta


def diff(a, b, names=None):
    """Case stems whose fingerprints differ; `names` may be file names (x.json) or stems."""
    keys = [n[:-5] if n.endswith(".json") else n for n in names] if names else sorted(set(a) | set(b))
    return [n for n in keys if a.get(n) != b.get(n)]


# ---------------------------------------------------------------- baseline store
def take_baseline(run_id, jobs=4, note=""):
    """Copies the snapshot files first, then fingerprints every battery case *in the copy* (its tax_graph, official and
    cases directories form a runnable tree), so the stored fingerprints and files always describe one state even when
    the project tree is being edited meanwhile."""
    if BASELINE.exists():
        shutil.rmtree(BASELINE)
    files = BASELINE / "files"
    files.mkdir(parents=True)
    rels = snapshot_files()
    for rel in rels:
        dst = files / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / rel, dst)
    names = sorted(p.name for p in (files / "cases" / "battery").glob("*.json"))
    fps, m = run_fingerprint(names, jobs=jobs, hashseed=0, workdir=files)
    errors = sorted(n for n, v in fps.items() if "error" in v)
    (BASELINE / "fingerprint.json").write_text(json.dumps(fps, ensure_ascii=False, sort_keys=True), encoding="utf-8")
    meta = {"run_id": run_id, "time": time.strftime("%Y-%m-%dT%H:%M:%S"), "version": version(files), "files": len(rels),
            "cases": len(fps), "errors": errors[:20], "seconds": m["seconds"], "note": note}
    (BASELINE / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding="utf-8")
    return meta


def load_baseline():
    if not (BASELINE / "fingerprint.json").exists():
        return None
    return {"fingerprint": json.loads((BASELINE / "fingerprint.json").read_text(encoding="utf-8")),
            "meta": json.loads((BASELINE / "meta.json").read_text(encoding="utf-8")),
            "files": BASELINE / "files"}


def changed_files(base):
    """[(rel, kind)] — kind added | removed | modified — between the baseline copy and the tree now."""
    now = set(snapshot_files())
    then = {p.relative_to(base["files"]).as_posix() for p in base["files"].rglob("*") if p.is_file()}
    out = []
    for rel in sorted(now | then):
        if rel not in then:
            out.append((rel, "added"))
        elif rel not in now:
            out.append((rel, "removed"))
        elif (ROOT / rel).read_bytes() != (base["files"] / rel).read_bytes():
            out.append((rel, "modified"))
    return out


def main(argv):
    lst = Path(argv[argv.index("--list") + 1])
    dest = argv[argv.index("--out") + 1]
    jobs = int(argv[argv.index("--jobs") + 1]) if "--jobs" in argv else 1
    names = json.loads(lst.read_text(encoding="utf-8"))
    res = compute(names, jobs, no_cache="--no-cache" in argv, workdir=os.getcwd())
    Path(dest).write_text(json.dumps(res, ensure_ascii=False, sort_keys=True), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
