"""不稳定检查 (C 层, 测试系统.md §2; L9–L11): the same cases fingerprinted under other conditions must give the same
tables. Variants against the run's reference fingerprint (default order, hash seed 0, cache on):

    reverse    the case list reversed (cheapest order check, L10)
    random     a seeded random order (the seed is recorded; L11 records every order so it can be replayed)
    hashseed   another PYTHONHASHSEED (set and dict iteration order: L9's "unordered collections")
    nocache    the engine's flow cache disabled (the 2026-10-09 defect: results depended on what a worker had cached)

A difference is re-run once under the same variant: the same difference again = deterministic (order dependence or
cache dependence, OD); a different outcome = non-determinism (NOD). The two are counted separately (L10 p.10). Every
variant's order, seeds and command are written to out/verify/<run_id>/stability_<variant>.json for replay.
"""
import json
import random

from .fp import diff, run_fingerprint


def _rel(path, root):
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return str(path)


def _sample(names, fraction):
    if fraction >= 1:
        return list(names)
    k = max(1, int(round(1 / fraction)))
    return list(names)[::k]


def stability_rows(ctx):
    ref, ref_meta = ctx["fingerprint"]()
    names = ref_meta["cases"]
    if ref and all("error" in v for v in ref.values()):
        return [{"layer": "C", "check_id": "C-stability", "subject": "系统/unstable items", "status": "na",
                 "measured": "the reference fingerprint is all errors (the tree does not run): nothing to compare, see C-fingerprint",
                 "expected": "a reference without errors", "oracle": "不变式", "evidence": next(iter(ref.values()))["error"][:200]}]
    sample = _sample(names, ctx.get("sample", 1.0))
    rnd = random.Random(ctx.get("seed"))
    variants = [("reverse", dict(order="reverse")),
                ("random", dict(order="random", seed=rnd.randrange(1 << 30))),
                ("hashseed", dict(hashseed=rnd.randrange(1, 1 << 30))),
                ("nocache", dict(no_cache=True))]
    rows, kinds = [], {"order": set(), "cache": set(), "hash": set(), "NOD": set()}
    kind_of = {"reverse": "order", "random": "order", "nocache": "cache", "hashseed": "hash"}
    for name, kw in variants:
        kw = dict(dict(order="default", seed=None, hashseed=0, no_cache=False), **kw)
        fps, meta = run_fingerprint(sample, jobs=ctx["jobs"], **kw)
        d = diff(ref, fps, sample)
        verdict, d2 = "", []
        if d:
            fps2, meta2 = run_fingerprint(sample, jobs=ctx["jobs"], **kw)
            d2 = diff(ref, fps2, sample)
            same = d2 == d and all(fps.get(c) == fps2.get(c) for c in d)
            verdict = "deterministic" if same else "nondeterministic"
            for c in d:
                kinds[kind_of[name] if same else "NOD"].add(c)
        rec = {"variant": name, **{k: v for k, v in kw.items()}, "sample": len(sample), "differ": d, "rerun_differ": d2,
               "verdict": verdict, "meta": {k: v for k, v in meta.items() if k != "cases"}, "order": meta["cases"]}
        path = ctx["dir"] / ("stability_%s.json" % name)
        path.write_text(json.dumps(rec, ensure_ascii=False, indent=1), encoding="utf-8")
        rows.append({"layer": "C", "check_id": "C-stability", "subject": "系统/variant %s" % name, "status": "pass" if not d else "fail",
                     "measured": "%d of %d differ%s" % (len(d), len(sample), (" (%s)" % verdict) if d else ""),
                     "expected": "0 differ", "oracle": "不变式", "evidence": _rel(path, ctx["root"]) + " | " + meta["command"][:200]})
        for c in d:
            rows.append({"layer": "C", "check_id": "C-stability", "subject": "案例/" + c, "status": "fail", "measured": "differs under %s (%s)" % (name, verdict),
                         "expected": "same table as the reference run", "oracle": "不变式", "evidence": _rel(path, ctx["root"])})
    rows.append({"layer": "C", "check_id": "C-stability", "subject": "系统/unstable items", "status": "pass" if not any(kinds.values()) else "fail",
                 "measured": "order-dependent %d, cache-dependent %d, hash-seed-dependent %d, non-deterministic %d (sample %d of %d cases)"
                             % (len(kinds["order"]), len(kinds["cache"]), len(kinds["hash"]), len(kinds["NOD"]), len(sample), len(names)),
                 "expected": "0 / 0 / 0 / 0", "oracle": "不变式", "evidence": "tax_graph/verify/stability.py"})
    ctx["stability_kinds"] = {k: sorted(v) for k, v in kinds.items()}
    return rows
