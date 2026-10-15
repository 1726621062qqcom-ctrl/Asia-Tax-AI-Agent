# -*- coding: utf-8 -*-
"""pipeline (端到端.md): the collection form in, the question sheet or the plan out, with a person's gates in between.

    python -m tax_graph.pipeline CASE.json [--docs DIR|FILE ...] [--model deepseek-flash] [--registry file|live|off]
                                           [--until intake|extract|review|verify|plan] [--auto] [--review FILE]
                                           [--answers FILE] [--run-id ID] [--from STAGE] [--k 5] [--samples 2]
                                           [--timeout 900] [--jobs 4] [--no-dense] [--no-patterns]
    python -m tax_graph.pipeline --batch DIR [same options]        every *.json in DIR, one run each

Stages, in order; each writes its artefacts under out/pipeline/<case>/<run_id>/ and one row per finding in the unified
result format of 测试系统.md §5 (results.jsonl, with the code / library / case fingerprints), and the manifest
(manifest.json) records every stage's status, seconds and artefacts so a run can be resumed, shown or attributed:

    intake   the collection form (案例采集.md §8 → the case JSON, with `names`) is loaded, its core validated
             (ex_ante.validate_core), its documents found (--docs, or cases/sources/<source>/source.txt for every
             source its provenance names).                                              → intake.json
    extract  tax_graph.llm.extract.extract_case: patterns and statement tables locate, retrieval ranks, the model
             reads, the program parses, compares, checks the registers and the cross-field relations.
             → extracted.json (facts with quotes, conflicts, violations, missing with reasons), todo.json (what a
             person must settle, by kind and source, 抽取改造.md §3), filled.json (fill(): stated values kept)
    review   GATE. The person's answers to todo.json go into review.json ({"data": {path: {"value", "source", "quote"}
             | "unknown"}}); they are merged with provenance → reviewed.json. Without review.json the run stops
             ("waiting"); --auto goes on with the unreviewed filled case and says so in every artefact.
    verify   tax_graph.verify.casecheck on the reviewed case: must pass; its warnings are recorded.  → casecheck.txt
    plan     tax_graph.planner.plan with the answers file (CASE.answers.json, or --answers): the question sheet or
             the plan (report.md), the candidate table (table.md), the questions as data (questions.json).
             A question sheet is the next gate: answers in the answers file, then rerun from `plan`.

The pipeline decides nothing: every value a stage adds carries its quote or its formula, every gap is a question
with its reason, and a person's answer is the only way a gap closes. Extension room (端到端.md §3): STAGES is a
registry a panel or the verify runner can call one stage at a time; artefacts are JSON a panel can render; gates
are files a form or an expert pack can write; the case schema (roles with types, jurisdictions, holdings, flows) is
read as given, so v2 roles (individuals, Vietnam, third-jurisdiction nodes) pass through; --batch runs many cases.
"""
import io
import json
import subprocess
import sys
import time
import traceback
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Callable, Dict, List, Optional

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "out" / "pipeline"
STAGES = ("intake", "extract", "review", "verify", "plan")
PY = sys.executable


def _plain(o):
    if isinstance(o, date):
        return o.isoformat()
    if isinstance(o, (set, frozenset)):
        return sorted(o)
    if hasattr(o, "__dict__"):
        return o.__dict__
    return str(o)


def _dump(path: Path, obj):
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=1, default=_plain), encoding="utf-8")


@dataclass
class Ctx:
    case: Path                                     # the collection form (case JSON)
    run: Path                                      # out/pipeline/<case>/<run_id>/
    opts: dict
    case_json: dict = field(default_factory=dict)
    docs: Dict[str, str] = field(default_factory=dict)
    manifest: dict = field(default_factory=dict)
    rows: List[dict] = field(default_factory=list)
    version: dict = field(default_factory=dict)

    @property
    def case_id(self):
        return self.case_json.get("case_id") or self.case.stem

    def art(self, name: str) -> Path:
        return self.run / name

    def row(self, check_id, status, measured="", expected="", evidence="", seconds=0.0, oracle="pipeline"):
        self.rows.append({"run_id": self.run.name, "layer": "pipeline", "check_id": check_id, "subject": self.case_id, "status": status,
                          "measured": measured, "expected": expected, "oracle": oracle, "evidence": evidence,
                          "version": self.version.get("short", ""), "seconds": round(seconds, 3)})

    def save(self):
        _dump(self.art("manifest.json"), self.manifest)
        with open(str(self.art("results.jsonl")), "w", encoding="utf-8") as f:
            for r in self.rows:
                f.write(json.dumps(r, ensure_ascii=False, default=_plain) + "\n")


# ---------------------------------------------------------------- intake
def find_docs(case_json: dict, docs_opt: Optional[List[str]]) -> Dict[str, str]:
    """--docs paths (dirs of *.txt or files), else cases/sources/<source>/source.txt for every source the provenance names."""
    from .llm.extract import load_docs
    docs = {}
    if docs_opt:
        for d in docs_opt:
            docs.update(load_docs(Path(d)))
        return docs
    for pv in (case_json.get("provenance") or {}).values():
        src = (pv or {}).get("source")
        if src and src not in docs:
            p = ROOT / "cases" / "sources" / src / "source.txt"
            if p.exists():
                docs[src] = p.read_text(encoding="utf-8")
    for name in case_json.get("documents", []):
        p = (ROOT / name).resolve()
        if ROOT.resolve() not in p.parents or p.suffix != ".txt":
            raise ValueError("Invalid case document path")
        docs.update(load_docs(p))
    return docs


def st_intake(ctx: Ctx) -> str:
    from .ex_ante import validate_core
    from .run import load_case
    ctx.case_json = json.loads(ctx.case.read_text(encoding="utf-8"))
    template, case, event, subject, ticks, notes = load_case(ctx.case)
    g = template.build(event, case.present, case)
    validate_core(g)                                                   # Reject -> the stage fails with the reason
    ctx.docs = find_docs(ctx.case_json, ctx.opts.get("docs"))
    names = ctx.case_json.get("names") or {}
    info = {"case_id": ctx.case_id, "kind": ctx.case_json.get("kind"), "template": template.name, "subject": subject,
            "roles": {r: {"loc": e.loc, "type": e.type} for r, e in g.entities.items()}, "flows": [f.id for f in g.flows],
            "event": event.__dict__, "names": names, "docs": {d: len(t) for d, t in ctx.docs.items()}, "version": ctx.version,
            "answers": str(ctx.opts.get("answers") or ctx.case.with_suffix("").as_posix() + ".answers.json")}
    _dump(ctx.art("intake.json"), info)
    ctx.row("intake.core", "pass", measured="%d roles, %d flows" % (len(g.entities), len(g.flows)))
    ctx.row("intake.docs", "pass" if ctx.docs else "warn", measured=", ".join(ctx.docs) or "none", expected="documents for the sources the provenance names",
            evidence="without documents the extraction only checks the registers and the relations; everything else is listed for a person")
    ctx.row("intake.names", "pass" if names else "warn", measured="%d roles named" % len(names), expected="names for every role",
            evidence="without names the patterns do not locate and retrieval recall drops (抽取改造.md §8)")
    return "pass"


# ---------------------------------------------------------------- extract
def _spec_hint(key: str, specs) -> dict:
    s = specs.get(key)
    return {"channel": s.channel, "source_hint": s.hint, "gloss": s.gloss, "unit": s.unit} if s else {}


def build_todo(result: dict, g, specs) -> List[dict]:
    """What a person must settle, from an extraction result, each item with its reason and where it comes from."""
    flows = {f.id: f for f in g.flows}

    def path_of(item: str) -> str:
        fid, key = item.split(":", 1)
        elem, name = key.split(".", 1)
        f = flows.get(fid)
        if elem == "flow" or f is None:
            return "flows.%s.%s" % (fid, name)
        return "roles.%s.attrs.%s" % (f.payer if elem == "payer" else f.payee, name)

    todo, seen = [], set()
    for p, cs in result.get("conflicts", {}).items():
        todo.append({"kind": "conflict", "path": p, "ask": "the documents give two values: choose one and state the basis, or enter unknown",
                     "options": [{"value": c["value"], "doc": c["doc"], "quote": c["quote"], "origin": c["origin"]} for c in cs]})
        seen.add(p)
    for p, why in result.get("violations", []):
        todo.append({"kind": "violation", "path": p, "why": why, "ask": "check, then correct the value or explain"})
    rejected = dict((k, v) for k, v in result.get("rejected", []))
    for item in result.get("missing", []):
        p = path_of(item)
        if p in seen:
            continue
        why = rejected.get(item, "not stated in the documents, or not recalled by retrieval")
        if why.startswith("conflict"):
            continue
        todo.append(dict({"kind": "missing", "path": p, "why": why, "ask": "enter the value with its source, or unknown"}, **_spec_hint(item.split(":", 1)[1], specs)))
    for item, channel, hint in result.get("external", []):
        todo.append({"kind": "external", "path": path_of(item), "channel": channel, "source_hint": hint,
                     "ask": "to be provided from a register / an authority's document / the counterparty's confirmation" if channel in ("B", "D") else "to be provided from a structured source"})
    for item in result.get("derived_inputs", []):
        todo.append({"kind": "derived_input", "path": path_of(item), "ask": "the program derives this item; what is missing is its input: complete the corresponding core fields of the collection form"})
    for item in result.get("untyped", []):
        todo.append({"kind": "untyped", "path": path_of(item), "ask": "free text the program cannot check; a person fills it in"})
    for role in result.get("registry_unmatched", []):
        todo.append({"kind": "registry", "path": "roles.%s" % role, "ask": "not found in the register: copy a record per cases/registry/README.md, or confirm the name"})
    for n in result.get("notes", []):
        todo.append({"kind": "note", "text": n})
    return todo


def st_extract(ctx: Ctx) -> str:
    from .llm.extract import ASK_CHANNELS, K, SAMPLES, JOBS, extract_case, field_specs, fill
    from .run import load_case
    o = ctx.opts
    model = o.get("model_callable")
    if model is None:
        from .llm.deepseek import DeepSeek
        model = DeepSeek(o.get("model") or "deepseek-flash", temperature=float(o.get("temperature", 0.7)), timeout=int(o.get("timeout", 900)))
    t0 = time.time()
    result = extract_case(ctx.case, ctx.docs, model, int(o.get("samples", SAMPLES)), None, ctx.case_json.get("names"),
                          tuple(o.get("channels") or ASK_CHANNELS), o.get("locate", "retrieval"), int(o.get("k", K)),
                          dense=not o.get("no_dense"), registry=ctx.case_json.get("registry"), patterns=not o.get("no_patterns"),
                          jobs=int(o.get("jobs", JOBS)), registry_mode=o.get("registry", "file"))
    _dump(ctx.art("extracted.json"), result)
    template, case, event, _, _, _ = load_case(ctx.case)
    g = template.build(event, case.present, case)
    todo = build_todo(result, g, field_specs())
    _dump(ctx.art("todo.json"), todo)
    _dump(ctx.art("filled.json"), fill(ctx.case_json, result))
    secs = time.time() - t0
    ctx.row("extract.facts", "pass", measured="%d values with quotes" % len(result["facts"]), evidence="extracted.json", seconds=secs)
    ctx.row("extract.conflicts", "warn" if result["conflicts"] else "pass", measured="%d" % len(result["conflicts"]), expected="0", evidence="todo.json")
    ctx.row("extract.violations", "warn" if result["violations"] else "pass", measured="%d" % len(result["violations"]), expected="0", evidence="todo.json")
    ctx.row("extract.missing", "warn" if result["missing"] else "pass", measured="%d" % len(result["missing"]), evidence="todo.json")
    ctx.row("extract.model", "pass" if not result["notes"] else "warn", measured="%s, %s" % (result["model"], result.get("usage", {}).get("calls", 0)),
            evidence="; ".join(result["notes"][:3]))
    ctx.manifest["todo"] = {"items": len(todo), "by_kind": _count(t["kind"] for t in todo)}
    return "pass"


def _count(it):
    c = {}
    for x in it:
        c[x] = c.get(x, 0) + 1
    return c


# ---------------------------------------------------------------- review (gate)
def apply_review(case_json: dict, review: dict) -> dict:
    """The person's answers merged into the case with provenance: {"data": {path: {"value", "source", "quote"} | "unknown"}}.
    Paths are the case paths of todo.json (roles.R.attrs.f, flows.F.f, holds.A>B.attr). "unknown" leaves the gap."""
    d = json.loads(json.dumps(case_json))
    applied = []
    for path, raw in (review.get("data") or {}).items():
        if raw == "unknown" or raw is None or (isinstance(raw, dict) and raw.get("value") in (None, "unknown")):
            parts = path.split(".")
            parent = d
            removed = False
            if parts[0] == "holds" and len(parts) == 3:
                a, b = parts[1].split(">")
                parent = next((h for h in d.get("holds", []) if h["holder"] == a and h["held"] == b), {})
                removed = parts[2] in parent
                parent.pop(parts[2], None)
            else:
                for part in parts[:-1]:
                    parent = parent.get(part, {}) if isinstance(parent, dict) else {}
                if isinstance(parent, dict):
                    removed = parts[-1] in parent
                    parent.pop(parts[-1], None)
            d.setdefault("provenance", {})[path] = {"kind": "missing", "source": "", "quote": ""}
            if removed:
                applied.append(path)
            continue
        v = raw.get("value") if isinstance(raw, dict) else raw
        src = raw.get("source", "") if isinstance(raw, dict) else ""
        quote = raw.get("quote", "") if isinstance(raw, dict) else ""
        parts = path.split(".")
        if parts[0] == "roles" and len(parts) >= 4:
            d["roles"].setdefault(parts[1], {}).setdefault("attrs", {})[parts[3]] = v
        elif parts[0] == "roles" and len(parts) == 3:
            d["roles"].setdefault(parts[1], {})[parts[2]] = v
        elif parts[0] == "flows":
            d.setdefault("flows", {}).setdefault(parts[1], {})[parts[2]] = v
        elif parts[0] == "holds":
            a, b = parts[1].split(">")
            h = next((h for h in d.setdefault("holds", []) if h["holder"] == a and h["held"] == b), None)
            if h is None:
                h = {"holder": a, "held": b}
                d["holds"].append(h)
            h[parts[2]] = v
        elif parts[0] == "event":
            d.setdefault("event", {})[parts[1]] = v
        else:
            continue
        d.setdefault("provenance", {})[path] = (dict(raw["provenance"]) if isinstance(raw, dict) and raw.get("accepted_extracted") else
                                                {"kind": "disclosed" if quote else "reviewed", "source": src, "quote": quote})
        applied.append(path)
    for n in review.get("notes") or []:
        d.setdefault("notes", []).append("review: " + n)
    return d, applied


def st_review(ctx: Ctx) -> str:
    filled = json.loads(ctx.art("filled.json").read_text(encoding="utf-8"))
    rv = ctx.opts.get("review")
    if rv and Path(rv).exists() and not ctx.art("review.json").exists():
        ctx.art("review.json").write_text(Path(rv).read_text(encoding="utf-8"), encoding="utf-8")
    if ctx.art("review.json").exists():
        review = json.loads(ctx.art("review.json").read_text(encoding="utf-8"))
        reviewed, applied = apply_review(filled, review)
        reviewed.setdefault("notes", []).append("reviewed by a person (%s, %d items applied from review.json)" % (date.today().isoformat(), len(applied)))
        _dump(ctx.art("reviewed.json"), reviewed)
        ctx.row("review.applied", "pass", measured="%d answers applied" % len(applied), evidence="review.json")
        return "pass"
    if ctx.opts.get("auto"):
        filled.setdefault("notes", []).append("not reviewed by a person (--auto, %s): the to-do list todo.json was not handled; conflicts and missing items are computed as missing" % date.today().isoformat())
        _dump(ctx.art("reviewed.json"), filled)
        ctx.row("review.gate", "warn", measured="skipped by --auto", expected="review.json", evidence="todo.json")
        return "pass"
    todo = json.loads(ctx.art("todo.json").read_text(encoding="utf-8"))
    ctx.art("REVIEW.md").write_text(_review_text(ctx, todo), encoding="utf-8")
    ctx.row("review.gate", "warn", measured="waiting for review.json", expected="review.json", evidence="REVIEW.md")
    return "waiting"


def _review_text(ctx: Ctx, todo: List[dict]) -> str:
    L = ["# To-do: %s (run %s)" % (ctx.case_id, ctx.run.name), "",
         "Extraction done; the items below are for a person to settle. Write the answers into `review.json` in this directory: `{\"data\": {\"<path>\": {\"value\": ..., \"source\": \"...\", \"quote\": \"...\"} | \"unknown\"}, \"notes\": [...]}`, "
         "then rerun `python -m tax_graph.pipeline %s --run-id %s --from review`. Unanswered items are computed as missing, never filled in." % (ctx.case.as_posix(), ctx.run.name), ""]
    kinds = {"conflict": "conflicts (two values in the documents)", "violation": "constraint violations", "missing": "missing", "external": "from a register / an official document", "derived_input": "derived by the program, input missing",
             "untyped": "free text", "registry": "register unmatched", "note": "events"}
    for kind, title in kinds.items():
        items = [t for t in todo if t["kind"] == kind]
        if not items:
            continue
        L += ["## %s (%d)" % (title, len(items)), ""]
        for t in items:
            if kind == "conflict":
                L.append("- `%s`: %s" % (t["path"], " / ".join("%s (%s: %s)" % (o["value"], o["doc"], " ".join(str(o["quote"]).split())[:100]) for o in t["options"])))
            elif kind == "note":
                L.append("- %s" % t["text"])
            else:
                L.append("- `%s`: %s%s" % (t["path"], t.get("why", t.get("ask", "")), ("; usual source: " + t["source_hint"]) if t.get("source_hint") else ""))
        L.append("")
    return "\n".join(L)


# ---------------------------------------------------------------- verify
def st_verify(ctx: Ctx) -> str:
    src = ctx.art("reviewed.json")
    t0 = time.time()
    r = subprocess.run([PY, "-X", "utf8", "-m", "tax_graph.verify.casecheck", str(src)], cwd=str(ROOT), capture_output=True)
    text = (r.stdout + r.stderr).decode("utf-8", "replace")
    ctx.art("casecheck.txt").write_text(text, encoding="utf-8")
    warns = [l.strip() for l in text.splitlines() if "warning:" in l]
    ctx.row("verify.casecheck", "pass" if r.returncode == 0 else "fail", measured="exit %d, %d warnings" % (r.returncode, len(warns)), expected="exit 0",
            evidence="casecheck.txt", seconds=time.time() - t0)
    for w in warns:
        ctx.row("verify.warn", "warn", measured=w[:200], evidence="casecheck.txt")
    return "pass" if r.returncode == 0 else "fail"


# ---------------------------------------------------------------- plan
def plan_json(p):
    """The planner's plan as JSON: regions keyed by their name (they are sets of jurisdictions in the planner)."""
    if p is None:
        return None
    from .regions import name as region_name
    def keys(o):                                        # any other set-keyed mapping (totals by region): the region's name
        if isinstance(o, dict):
            return {(region_name(k) if isinstance(k, (set, frozenset)) else k): keys(v) for k, v in o.items()}
        if isinstance(o, (list, tuple)):
            return [keys(x) for x in o]
        return o
    out = dict(p)
    out["regions"] = [{"region": region_name(rg), "jurisdictions": sorted(rg), **d} for rg, d in (p.get("regions") or {}).items()]
    return json.loads(json.dumps(keys(out), default=_plain))


def st_plan(ctx: Ctx) -> str:
    from .ex_ante import ex_ante
    from .planner import Answers, plan, render
    from .run import load_case, render as render_table
    src = ctx.art("reviewed.json")
    template, case, event, subject, ticks, notes = load_case(src)
    answers_path = ctx.opts.get("answers") or (ctx.case.with_suffix("").as_posix() + ".answers.json")
    answers = Answers.load(answers_path)
    t0 = time.time()
    outcome = plan(template, event, case, answers)
    secs = time.time() - t0
    ctx.art("report.md").write_text(render(template, event, outcome, ctx.case_id), encoding="utf-8")
    qs = [{"key": q.key, "kind": q.kind, "region": sorted(q.region), "prompt": q.prompt, "value": q.value, "source_hint": q.source_hint,
           "impact": q.impact, "why": q.why, "forms": q.forms} for q in outcome.questions]
    _dump(ctx.art("questions.json"), {"answers_file": answers_path, "questions": qs, "plan": plan_json(outcome.plan), "note": outcome.note})
    try:
        out = ex_ante(template, event, case, ticks=ticks or None, subject=subject)
        ctx.art("table.md").write_text(render_table(template, case, event, subject, out, None, notes), encoding="utf-8")
        ctx.row("plan.table", "pass", measured="%d candidates" % len(out.table), evidence="table.md")
    except Exception as e:                                          # the table is a view; its failure does not void the plan
        ctx.row("plan.table", "warn", measured="%s: %s" % (type(e).__name__, str(e)[:160]))
    if outcome.questions:
        ctx.row("plan.questions", "warn", measured="%d questions (%d blocking)" % (len(qs), sum(1 for q in qs if q["kind"] in ("blocking", "joint"))),
                expected="0", evidence="report.md; answers -> %s" % answers_path, seconds=secs)
        ctx.manifest["next"] = "answer the question sheet in %s, then rerun --from plan" % answers_path
    elif outcome.plan:
        p = outcome.plan
        ctx.row("plan.plan", "pass", measured="guaranteed %.2f / best %.2f" % (p["guaranteed"], p["best"]), evidence="report.md", seconds=secs)
        ctx.manifest["next"] = "done: plan in report.md"
    else:
        ctx.row("plan.none", "fail", measured=outcome.note[:200], evidence="report.md", seconds=secs)
        return "fail"
    return "pass"


STAGE_FUNCS: Dict[str, Callable[[Ctx], str]] = {"intake": st_intake, "extract": st_extract, "review": st_review, "verify": st_verify, "plan": st_plan}
ARTEFACT = {"intake": "intake.json", "extract": "filled.json", "review": "reviewed.json", "verify": "casecheck.txt", "plan": "report.md"}


# ---------------------------------------------------------------- the run
def run_pipeline(case: Path, opts: dict) -> Ctx:
    from .verify.results import version
    run_id = opts.get("run_id") or time.strftime("%Y%m%dT%H%M%S")
    run = OUT / case.stem / run_id
    run.mkdir(parents=True, exist_ok=True)
    ctx = Ctx(case=case, run=run, opts=opts, version=version())
    mpath = run / "manifest.json"
    if mpath.exists():
        ctx.manifest = json.loads(mpath.read_text(encoding="utf-8"))
        rpath = run / "results.jsonl"
        if rpath.exists():
            ctx.rows = [json.loads(l) for l in rpath.read_text(encoding="utf-8").splitlines() if l.strip()]
    ctx.manifest.update({"case": str(case), "run_id": run_id, "version": ctx.version, "options": {k: v for k, v in opts.items() if k != "model_callable"},
                         "started": ctx.manifest.get("started") or time.strftime("%Y-%m-%dT%H:%M:%S")})
    stages = ctx.manifest.setdefault("stages", {})
    until = opts.get("until") or "plan"
    start = opts.get("from_stage")
    restart = start is None
    for name in STAGES:
        if start == name:
            restart = True
        done = stages.get(name, {}).get("status") == "pass" and (run / ARTEFACT[name]).exists()
        if not restart and done:
            if name == "intake":                                   # the context the later stages need
                ctx.case_json = json.loads(case.read_text(encoding="utf-8"))
                ctx.docs = find_docs(ctx.case_json, opts.get("docs"))
            continue
        if name != "intake" and not ctx.case_json:
            ctx.case_json = json.loads(case.read_text(encoding="utf-8"))
            ctx.docs = find_docs(ctx.case_json, opts.get("docs"))
        ctx.rows = [r for r in ctx.rows if not r["check_id"].startswith(name + ".")]
        t0 = time.time()
        try:
            status = STAGE_FUNCS[name](ctx)
            note = ""
        except Exception as e:
            status, note = "fail", "%s: %s" % (type(e).__name__, e)
            (run / ("%s.error.txt" % name)).write_text(traceback.format_exc(), encoding="utf-8")
            ctx.row("%s.error" % name, "fail", measured=note[:200], evidence="%s.error.txt" % name)
        stages[name] = {"status": status, "seconds": round(time.time() - t0, 3), "artefact": ARTEFACT[name], "note": note}
        ctx.manifest["status"] = status if status != "pass" else ("done" if name == until else "running")
        ctx.save()
        if status != "pass" or name == until:
            break
    if ctx.manifest.get("status") == "running":
        ctx.manifest["status"] = "done"
    ctx.manifest["finished"] = time.strftime("%Y-%m-%dT%H:%M:%S")
    ctx.save()
    return ctx


def summary(ctx: Ctx) -> str:
    L = ["[%s] %s  run %s  status %s" % (ctx.case_id, ctx.case, ctx.run.name, ctx.manifest.get("status"))]
    for name, st in ctx.manifest.get("stages", {}).items():
        L.append("  %-8s %-8s %6.1fs  %s %s" % (name, st["status"], st["seconds"], st["artefact"], st.get("note", "")))
    if ctx.manifest.get("todo"):
        L.append("  todo: %s" % ctx.manifest["todo"]["by_kind"])
    if ctx.manifest.get("next"):
        L.append("  next: %s" % ctx.manifest["next"])
    L.append("  artefacts: %s" % ctx.run)
    return "\n".join(L)


def main(argv):
    out = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    opt = lambda flag, default=None: argv[argv.index(flag) + 1] if flag in argv else default
    opts = {"docs": [argv[i + 1] for i, a in enumerate(argv) if a == "--docs"] or None, "model": opt("--model"), "registry": opt("--registry", "file"),
            "until": opt("--until"), "auto": "--auto" in argv, "review": opt("--review"), "answers": opt("--answers"), "run_id": opt("--run-id"),
            "from_stage": opt("--from"), "k": opt("--k", 5), "samples": opt("--samples", 2), "timeout": opt("--timeout", 900), "jobs": opt("--jobs", 4),
            "temperature": opt("--temperature", 0.7), "no_dense": "--no-dense" in argv, "no_patterns": "--no-patterns" in argv}
    cases = sorted(Path(opt("--batch")).glob("*.json")) if "--batch" in argv else [Path(argv[1])]
    cases = [c for c in cases if not c.name.endswith((".answers.json", ".extracted.json", ".filled.json"))]
    code = 0
    for c in cases:
        ctx = run_pipeline(c, dict(opts))
        out.write(summary(ctx) + "\n")
        if ctx.manifest.get("status") == "fail":
            code = 1
    out.flush()
    return code


if __name__ == "__main__":
    sys.exit(main(sys.argv))
