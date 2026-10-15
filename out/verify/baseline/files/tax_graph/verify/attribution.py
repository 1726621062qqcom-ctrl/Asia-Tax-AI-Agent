"""变化归因 (C 层, 测试系统.md §2; L12 delta debugging): every case whose fingerprint differs from the accepted baseline
must be explained by a minimal set of the files changed since that baseline.

    baseline   out/verify/baseline/: the fingerprints of all battery cases and a copy of every file of the snapshot sets
               (results.SNAPSHOT_SETS), stored by `python -m tax_graph.verify --baseline` after a run was accepted
    changes    the files whose bytes differ from the copy (added, removed, modified) — the change units
    test(S)    a scratch tree holds the current version of the files in S and the baseline version of the rest; the
               differing cases are fingerprinted there. Per case: FAIL = the current result is reproduced, PASS = the
               baseline result is reproduced, UNRESOLVED = neither, or the run broke (L12: three outcomes)
    ddmin      Zeller & Hildebrandt's minimising delta debugging over the change units, per case, with the tests memoised
               across cases; the result is a 1-minimal set of files that alone reproduces the new result
    cancelling the complement of that set is tested too: if it also moves the result, the changes may cancel or there
               is more than one cause (L12's monotonicity assumption does not hold) and the row says so
    口径       the "口径 Dnn" tokens in the changed lines of the attributed files, so the change is named by decision

A case attributed to a set of files is a `warn` (the change is explained, the baseline is not yet re-accepted); a case
no set explains is a `fail` (门禁 §4: 回归变化未能归因). Runs after the instability check: an unstable engine cannot be
attributed (L13 p.3, L12 p.16).
"""
import difflib
import json
import os
import re
import shutil
import time
from pathlib import Path

from .fp import changed_files, diff, load_baseline, run_fingerprint
from .results import ROOT, RUNTIME_SETS, files_of

KOUJING = re.compile(r"口径\s*D\d+")
BUDGET = 160                                                # fingerprint runs per attribution, all cases together
FAIL, PASS, UNRESOLVED = "FAIL", "PASS", "UNRESOLVED"


def fingerprint_rows(ctx):
    fps, meta = ctx["fingerprint"]()
    errors = sorted(n for n, v in fps.items() if "error" in v)
    rel = Path(meta["out"]).relative_to(ctx["root"]).as_posix() if meta.get("out") else ""
    rows = [{"layer": "C", "check_id": "C-fingerprint", "subject": "系统/fingerprint", "status": "pass" if not errors else "fail",
             "measured": "%d cases, %d errors, %.0f s, hashseed %s" % (len(fps), len(errors), meta["seconds"], meta["hashseed"]),
             "expected": "0 errors", "oracle": "快照", "evidence": rel}]
    for n in errors:
        rows.append({"layer": "C", "check_id": "C-fingerprint", "subject": "案例/" + n, "status": "fail", "measured": fps[n]["error"][:300],
                     "expected": "a table", "oracle": "快照", "evidence": rel})
    base = load_baseline()
    if base is None:
        rows.append({"layer": "C", "check_id": "C-fingerprint", "subject": "系统/baseline", "status": "na",
                     "measured": "no baseline yet", "expected": "python -m tax_graph.verify --tier mid --baseline", "oracle": "快照", "evidence": "out/verify/baseline/"})
    else:
        d = diff(base["fingerprint"], fps)
        rows.append({"layer": "C", "check_id": "C-fingerprint", "subject": "系统/since baseline %s" % base["meta"]["run_id"],
                     "status": "pass" if not d else "warn", "measured": "%d of %d cases differ" % (len(d), len(set(fps) | set(base["fingerprint"]))),
                     "expected": "0, or every difference attributed (C-attribution)", "oracle": "快照",
                     "evidence": "baseline version %s, now %s" % (base["meta"]["version"]["short"], ctx["version"]["short"])})
    return rows


def _scratch(ctx):
    root = ctx["dir"] / "scratch"
    if root.exists():
        shutil.rmtree(root)
    for rel in files_of(RUNTIME_SETS):
        dst = root / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / rel, dst)
    return root


def _apply(scratch, base, changed, subset):
    for rel, kind in changed:
        dst = scratch / rel
        if rel in subset:
            src = None if kind == "removed" else ROOT / rel
        else:
            src = None if kind == "added" else base["files"] / rel
        if src is None:
            if dst.exists():
                dst.unlink()
        else:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(src, dst)


def ddmin(items, test, budget):
    """1-minimal subset of `items` for which test() is FAIL (test(items) is FAIL); None when the budget runs out."""
    c, n, used = list(items), 2, [0]

    def t(s):
        used[0] += 1
        if used[0] > budget:
            raise RuntimeError("budget")
        return test(s)

    try:
        while len(c) >= 2:
            size = -(-len(c) // n)
            subsets = [c[i:i + size] for i in range(0, len(c), size)]
            found = False
            for s in subsets:
                if t(s) == FAIL:
                    c, n, found = s, 2, True
                    break
            if found:
                continue
            for s in subsets:
                comp = [x for x in c if x not in s]
                if comp and t(comp) == FAIL:
                    c, n, found = comp, max(n - 1, 2), True
                    break
            if found:
                continue
            if n >= len(c):
                break
            n = min(len(c), 2 * n)
    except RuntimeError:
        return None
    return c


def _koujing(base, rels_kinds):
    found = set()
    for rel, kind in rels_kinds:
        try:
            now = (ROOT / rel).read_text(encoding="utf-8").splitlines() if kind != "removed" else []
            was = (base["files"] / rel).read_text(encoding="utf-8").splitlines() if kind != "added" else []
        except (UnicodeDecodeError, OSError):
            continue
        for line in difflib.unified_diff(was, now, n=0, lineterm=""):
            if (line.startswith("+") or line.startswith("-")) and not line.startswith(("+++", "---")):
                found.update(KOUJING.findall(line))
    return sorted(found, key=lambda s: int(re.sub(r"\D", "", s)))


def attribution_rows(ctx):
    fps, meta = ctx["fingerprint"]()
    base = load_baseline()
    cid = "C-attribution"
    if base is None:
        return [{"layer": "C", "check_id": cid, "subject": "系统/baseline", "status": "na", "measured": "no baseline yet",
                 "expected": "python -m tax_graph.verify --tier mid --baseline", "oracle": "快照", "evidence": "out/verify/baseline/"}]
    cur, old = fps, base["fingerprint"]
    d = diff(old, cur)
    ev = "baseline %s (%s) -> now %s" % (base["meta"]["run_id"], base["meta"]["version"]["short"], ctx["version"]["short"])
    if cur and all("error" in v for v in cur.values()):
        return [{"layer": "C", "check_id": cid, "subject": "系统/changes since baseline", "status": "na",
                 "measured": "the current fingerprint is all errors (the tree does not run): nothing to attribute, see C-fingerprint",
                 "expected": "a current state that runs", "oracle": "快照", "evidence": ev}]
    if not d:
        return [{"layer": "C", "check_id": cid, "subject": "系统/changes since baseline", "status": "pass",
                 "measured": "0 cases differ", "expected": "0", "oracle": "快照", "evidence": ev}]
    changed = changed_files(base)
    if not changed:
        rows = [{"layer": "C", "check_id": cid, "subject": "系统/changes since baseline", "status": "fail",
                 "measured": "%d cases differ but no file of the snapshot sets changed: non-determinism, or a dependency outside the sets" % len(d),
                 "expected": "every difference attributed to a changed file", "oracle": "快照", "evidence": ev}]
        rows += [{"layer": "C", "check_id": cid, "subject": "案例/" + c, "status": "fail", "measured": "differs, no file change", "expected": "",
                  "oracle": "快照", "evidence": ev} for c in d]
        return rows
    scratch = _scratch(ctx)
    names = [c + ".json" for c in d]
    memo, log = {}, []

    def test(subset):
        key = frozenset(subset)
        if key in memo:
            return memo[key]
        _apply(scratch, base, changed, key)
        got, m = run_fingerprint(names, jobs=min(ctx["jobs"], len(names)), hashseed=0, workdir=scratch)
        out = {}
        for c in d:
            v = got.get(c)
            if m["returncode"] != 0 or v is None:
                out[c] = UNRESOLVED
            elif v == cur.get(c):                        # also when the current state is an error: that error reproduced
                out[c] = FAIL
            elif v == old.get(c):
                out[c] = PASS
            else:
                out[c] = UNRESOLVED
        memo[key] = out
        log.append({"subset": sorted(key), "outcome": out, "seconds": m["seconds"], "returncode": m["returncode"],
                    "stderr": m["stderr"][-300:], "got": {c: got.get(c) for c in d if out[c] == UNRESOLVED}})
        return out

    rels = [rel for rel, _ in changed]
    kinds = dict(changed)
    t0 = time.time()
    full, empty = test(rels), test([])
    rows, attributed, unattributed = [], 0, 0
    for c in d:
        if full[c] != FAIL or empty[c] != PASS:
            unattributed += 1
            rows.append({"layer": "C", "check_id": cid, "subject": "案例/" + c, "status": "fail",
                         "measured": "the scratch tree reproduces neither end (all changes: %s, no change: %s): a dependency outside the snapshot sets, or non-determinism" % (full[c], empty[c]),
                         "expected": "attributed", "oracle": "快照", "evidence": ev})
            continue
        m = ddmin(rels, lambda s: test(s)[c], BUDGET - len(log))
        if m is None:
            unattributed += 1
            rows.append({"layer": "C", "check_id": cid, "subject": "案例/" + c, "status": "fail", "measured": "dd budget of %d tests exhausted" % BUDGET,
                         "expected": "attributed", "oracle": "快照", "evidence": ev})
            continue
        comp = test([x for x in rels if x not in m])[c]
        kj = _koujing(base, [(x, kinds[x]) for x in m])
        attributed += 1
        note = "" if comp == PASS else "; the other changes alone also move it (%s): 可能相互抵消或多因" % comp
        rows.append({"layer": "C", "check_id": cid, "subject": "案例/" + c, "status": "warn",
                     "measured": "files: %s; 口径: %s%s" % (", ".join(m), ", ".join(kj) or "none named", note),
                     "expected": "re-accept with --baseline once the change is deliberate", "oracle": "快照", "evidence": ev})
    (ctx["dir"] / "attribution.json").write_text(json.dumps({"changed": changed, "differ": d, "tests": log}, ensure_ascii=False, indent=1), encoding="utf-8")
    if not os.environ.get("VERIFY_KEEP"):
        shutil.rmtree(scratch, ignore_errors=True)
    rows.insert(0, {"layer": "C", "check_id": cid, "subject": "系统/changes since baseline", "status": "fail" if unattributed else "warn",
                    "measured": "%d cases differ; attributed %d, unattributed %d; changed files %d; %d fingerprint runs, %.0f s"
                                % (len(d), attributed, unattributed, len(changed), len(log), time.time() - t0),
                    "expected": "every difference attributed", "oracle": "快照",
                    "evidence": ev + " | " + ", ".join("%s(%s)" % (r, k[0]) for r, k in changed[:12])})
    return rows
