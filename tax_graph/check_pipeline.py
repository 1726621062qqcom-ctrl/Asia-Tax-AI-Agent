# -*- coding: utf-8 -*-
"""Checks of the end-to-end pipeline without a live model or network: a scripted model that reads nothing, the register
off, the review gate both waiting and answered, the case check and the planner on the result, the artefacts and the
unified rows a panel would read.

    python -m tax_graph.check_pipeline          (conda env "pytorch"; ~1 min: the planner runs on one case)
"""
import io
import json
import shutil
import sys
import tempfile
from pathlib import Path

from .pipeline import OUT, apply_review, build_todo, run_pipeline

ROOT = Path(__file__).resolve().parents[1]
CASE = ROOT / "cases" / "semisynth" / "K3-mirxes-2026.json"


def main():
    out = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    results = []

    def check(ok, text):
        results.append(ok)
        out.write("%-4s %s\n" % ("ok" if ok else "FAIL", text))
        out.flush()

    silent = lambda prompt: '{"value": null}'                       # a model that never reads anything: every gap is a person's
    run_id = "check-" + tempfile.mkdtemp(prefix="", dir=None).split("tmp")[-1][-6:]
    opts = {"model_callable": silent, "registry": "off", "no_dense": True, "k": 2, "samples": 1, "jobs": 2}

    # 1. intake -> extract -> review gate waits
    ctx = run_pipeline(CASE, dict(opts, run_id=run_id))
    st = ctx.manifest["stages"]
    check(st["intake"]["status"] == "pass" and ctx.art("intake.json").exists() and json.loads(ctx.art("intake.json").read_text(encoding="utf-8"))["docs"],
          "intake: the form loads, its core validates, the documents are found from the provenance's sources")
    check(st["extract"]["status"] == "pass" and ctx.art("extracted.json").exists() and ctx.art("todo.json").exists() and ctx.art("filled.json").exists(),
          "extract: extracted.json, todo.json and filled.json are written")
    todo = json.loads(ctx.art("todo.json").read_text(encoding="utf-8"))
    kinds = {t["kind"] for t in todo}
    check("missing" in kinds and "external" in kinds and all(t.get("path") or t.get("text") for t in todo) and all(t.get("ask") or t["kind"] == "note" for t in todo),
          "todo: every gap is an item with its path, kind and what is asked of the person (%s)" % sorted(kinds))
    check(st["review"]["status"] == "waiting" and ctx.manifest["status"] == "waiting" and ctx.art("REVIEW.md").exists() and "verify" not in st,
          "review gate: without review.json the run stops as waiting, REVIEW.md tells the person what to do, later stages do not run")
    rows = [json.loads(l) for l in ctx.art("results.jsonl").read_text(encoding="utf-8").splitlines()]
    check(all({"run_id", "layer", "check_id", "subject", "status", "version"} <= set(r) for r in rows) and any(r["check_id"] == "review.gate" and r["status"] == "warn" for r in rows),
          "rows: unified result format (测试系统.md §5) with the version fingerprint; the gate is a warn row")

    # 2. the person answers: a value with its source, a conflict resolved, an unknown
    missing = next(t for t in todo if t["kind"] == "missing" and t["path"].startswith("flows."))
    review = {"data": {missing["path"]: {"value": True if missing.get("unit") in ("yes/no", "") else 1, "source": "filled by a person (check)", "quote": ""},
                       "roles.ULT.attrs.residence_cert": "unknown"}, "notes": ["review for the check"]}
    filled = json.loads(ctx.art("filled.json").read_text(encoding="utf-8"))
    reviewed, applied = apply_review(filled, review)
    fid, name = missing["path"].split(".")[1], missing["path"].split(".")[2]
    check(applied == [missing["path"]] and reviewed["flows"][fid][name] is not None and reviewed["provenance"][missing["path"]]["kind"] == "reviewed"
          and "residence_cert" not in reviewed["roles"]["ULT"]["attrs"] and any(n.startswith("review: ") for n in reviewed["notes"]),
          "apply_review: a value lands at its path with a provenance row, unknown leaves the gap, notes are kept")
    ctx.art("review.json").write_text(json.dumps({"data": {missing["path"]: "unknown"}, "notes": ["nothing to add"]}, ensure_ascii=False), encoding="utf-8")

    # 3. resume from the gate: verify and plan
    ctx2 = run_pipeline(CASE, dict(opts, run_id=run_id, from_stage="review"))
    st2 = ctx2.manifest["stages"]
    check(st2["review"]["status"] == "pass" and ctx2.art("reviewed.json").exists(), "resume: with review.json the gate passes and reviewed.json is written")
    check(st2["verify"]["status"] == "pass" and "PASS" in ctx2.art("casecheck.txt").read_text(encoding="utf-8"), "verify: the case check passes on the reviewed case")
    check(st2["plan"]["status"] == "pass" and ctx2.art("report.md").exists() and ctx2.art("questions.json").exists(),
          "plan: the planner writes report.md and questions.json (%s)" % ctx2.manifest.get("next", "")[:60])
    q = json.loads(ctx2.art("questions.json").read_text(encoding="utf-8"))
    report = ctx2.art("report.md").read_text(encoding="utf-8")
    check((q["questions"] and report.startswith("# Question sheet")) or (q["plan"] and report.startswith("# Plan")), "the report is a question sheet or a plan, matching questions.json")
    check(ctx2.manifest["status"] == "done" and all(s["status"] == "pass" for s in st2.values()), "manifest: every stage passed, status done")

    # 4. --until and --auto
    ctx3 = run_pipeline(CASE, dict(opts, run_id=run_id + "-auto", auto=True, until="verify"))
    check(ctx3.manifest["status"] == "done" and ctx3.manifest["stages"]["review"]["status"] == "pass" and "plan" not in ctx3.manifest["stages"]
          and any("not reviewed by a person" in n for n in json.loads(ctx3.art("reviewed.json").read_text(encoding="utf-8"))["notes"]),
          "--auto passes the gate and says so in the case; --until stops after the named stage")
    for d in (ctx.run, ctx3.run):
        shutil.rmtree(d, ignore_errors=True)
    out.write("%d checks, %d failures\n" % (len(results), results.count(False)))
    out.flush()
    return 1 if False in results else 0


if __name__ == "__main__":
    sys.exit(main())
