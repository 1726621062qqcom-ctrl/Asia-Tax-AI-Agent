# -*- coding: utf-8 -*-
"""ui (界面.md): a local page over the artefacts the program already writes — cases, pipeline runs, their gates, the
quality rows — and the two things a person writes back: review.json and the answers file.

    python -m tax_graph.ui                     http://127.0.0.1:8765  (conda env "pytorch"; standard library only)
    python -m tax_graph.ui --port 8800

Everything the page shows is read from files under the project (cases/, out/pipeline/, out/verify/, out/extract_eval_*);
nothing is computed here. The page can start a pipeline run (a subprocess of tax_graph.pipeline) and save a review or
an answers file; it cannot change a rule, a parameter or a case value without a provenance row. Binds to localhost only.
"""
import io
import base64
import csv
import hashlib
import json
import mimetypes
import re
import shutil
import subprocess
import sys
import threading
import time
import urllib.parse
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from .forms import build_case, field_schema, schemas, typed_value, validate_answers
from .intake import build_recorded_case, collection_preview, TRANSACTION_TYPES
from ..engine import Reject
from ..scope import POLICY as SCOPE_POLICY, check as scope_check, kinds as scope_kinds
from .describe import GUIDE as DESCRIBE_GUIDE, read_case as describe_case

ROOT = Path(__file__).resolve().parents[2]
STATIC = Path(__file__).resolve().parent / "static"
PY = sys.executable
CASE_DIRS = ("cases", "cases/real", "cases/semisynth", "cases/v2", "cases/private", "cases/intake")
JOBS = {}                                            # run key -> {"proc", "started", "argv"}
_LOCK = threading.RLock()


def _inside(p: Path) -> Path:
    p = (ROOT / p).resolve() if not Path(p).is_absolute() else Path(p).resolve()
    if ROOT.resolve() not in p.parents and p != ROOT.resolve():
        raise PermissionError("outside the project: %s" % p)
    return p


def _read_json(p: Path, default=None):
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return default


def _rel(p: Path) -> str:
    return p.resolve().relative_to(ROOT.resolve()).as_posix()


def _signature(case):
    c = _read_json(case, {})
    paths = list(c.get("documents", []))
    for row in (c.get("provenance") or {}).values():
        src = (row or {}).get("source")
        if src:
            p = ROOT / "cases" / "sources" / src / "source.txt"
            if p.exists():
                paths.append(_rel(p))
    material = [(p, hashlib.sha256(_inside(Path(p)).read_bytes()).hexdigest() if _inside(Path(p)).exists() else "missing") for p in sorted(set(paths))]
    return hashlib.sha256(json.dumps([c, material], sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()


def _answers_signature(path):
    p = _inside(Path(path))
    return hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else "missing"


# ---------------------------------------------------------------- data views
def cases():
    out = []
    for d in CASE_DIRS:
        for f in sorted((ROOT / d).glob("*.json")):
            if f.name.endswith((".answers.json", ".extracted.json", ".filled.json")):
                continue
            c = _read_json(f, {})
            if not isinstance(c, dict) or "roles" not in c:
                continue
            prov = c.get("provenance") or {}
            kinds = {}
            for pv in prov.values():
                k = (pv or {}).get("kind", "?")
                kinds[k] = kinds.get(k, 0) + 1
            runs = sorted((ROOT / "out" / "pipeline" / f.stem).glob("*/manifest.json")) if (ROOT / "out" / "pipeline" / f.stem).exists() else []
            out.append({"path": _rel(f), "case_id": c.get("case_id") or f.stem, "kind": c.get("kind"), "template": c.get("template"), "subject": c.get("subject"),
                        "roles": {r: v.get("loc") for r, v in c.get("roles", {}).items()}, "flows": list(c.get("flows", {})), "event": c.get("event"),
                        "names": c.get("names") or {}, "currency": c.get("currency"), "provenance": kinds, "runs": len(runs), "status": _status_of(f),
                        "answers": (f.with_suffix("").as_posix() + ".answers.json") if Path(f.with_suffix("").as_posix() + ".answers.json").exists() else None})
    return out


def _status_of(f: Path) -> str:
    try:
        return workspace(_rel(f))["status"]
    except Exception:
        return "error"


def case_detail(path: str):
    f = _inside(Path(path))
    c = _read_json(f, {})
    ans = Path(f.with_suffix("").as_posix() + ".answers.json")
    return {"path": _rel(f), "case": c, "answers": _read_json(ans) if ans.exists() else None, "answers_path": _rel(ans)}


def runs(case_stem=None):
    out = []
    base = ROOT / "out" / "pipeline"
    for m in sorted(base.glob("*/*/manifest.json"), key=lambda p: p.stat().st_mtime, reverse=True):
        if case_stem and m.parent.parent.name != case_stem:
            continue
        man = _read_json(m, {})
        out.append({"dir": _rel(m.parent), "case": man.get("case"), "case_stem": m.parent.parent.name, "run_id": man.get("run_id", m.parent.name),
                    "status": man.get("status"), "started": man.get("started"), "finished": man.get("finished"),
                    "stages": {k: v.get("status") for k, v in man.get("stages", {}).items()}, "todo": man.get("todo"), "next": man.get("next"),
                    "model": (man.get("options") or {}).get("model"), "running": _rel(m.parent) in JOBS and JOBS[_rel(m.parent)]["proc"].poll() is None})
    return out


def run_detail(d: str):
    p = _inside(Path(d))
    art = {}
    for name in ("manifest.json", "intake.json", "todo.json", "questions.json", "review.json", "reviewed.json", "filled.json"):
        art[name] = _read_json(p / name)
    ext = _read_json(p / "extracted.json")
    if ext:
        art["extracted.json"] = {k: ext.get(k) for k in ("facts", "provenance", "conflicts", "violations", "missing", "rejected", "notes", "features",
                                                           "registry", "registry_unmatched", "external", "derived_inputs", "untyped", "usage", "model", "prompt_version", "k", "locate")}
    for name in ("report.md", "table.md", "REVIEW.md", "casecheck.txt"):
        art[name] = (p / name).read_text(encoding="utf-8") if (p / name).exists() else None
    rows = []
    if (p / "results.jsonl").exists():
        rows = [json.loads(l) for l in (p / "results.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    errors = {e.name: e.read_text(encoding="utf-8")[-3000:] for e in p.glob("*.error.txt")}
    job = JOBS.get(_rel(p))
    return {"dir": _rel(p), "artefacts": art, "rows": rows, "errors": errors,
            "job": {"running": job["proc"].poll() is None, "started": job["started"], "argv": job["argv"], "log": _tail(job["log"])} if job else None}


def _tail(path: Path, n=4000):
    try:
        return path.read_text(encoding="utf-8", errors="replace")[-n:]
    except OSError:
        return ""


def verify_index():
    idx = _read_json(ROOT / "out" / "verify" / "index.json", {"runs": []})
    runs_ = idx.get("runs", [])
    out = []
    for r in runs_[-60:]:
        out.append({k: r.get(k) for k in ("run_id", "tier", "started", "seconds", "version", "counts", "note")})
        checks = r.get("checks") or []
        if isinstance(checks, dict):
            checks = [dict(v, check_id=k) for k, v in checks.items()]
        out[-1]["checks"] = [({"check_id": c.get("check_id") or c.get("id"), "status": c.get("status"), "seconds": c.get("seconds"), "layer": c.get("layer")}
                              if isinstance(c, dict) else {"check_id": str(c)}) for c in checks]
    return {"runs": out, "format": idx.get("format")}


def verify_run(run_id: str):
    f = ROOT / "out" / "verify" / (run_id + ".jsonl")
    _inside(f)
    rows = [json.loads(l) for l in f.read_text(encoding="utf-8").splitlines() if l.strip()] if f.exists() else []
    return {"run_id": run_id, "rows": rows[:5000]}


def evals():
    d = ROOT / "out" / "extract_eval_deepseek"
    out = {}
    for name in ("README.md", "round4_summary.txt", "round4_qwen_summary.txt", "round4_recall.txt", "round4_channels.txt"):
        if (d / name).exists():
            out[name] = (d / name).read_text(encoding="utf-8")
    return out


def docs():
    out = {}
    for name in ("端到端.md", "抽取改造.md", "信息收集.md", "案例采集.md", "测试系统.md", "优化方案.md", "界面.md"):
        if (ROOT / name).exists():
            out[name] = (ROOT / name).read_text(encoding="utf-8")
    return out


# ---------------------------------------------------------------- the case page: the case, its latest run, the next step
def latest_run(stem: str, case=None):
    base = ROOT / "out" / "pipeline" / stem
    ms = sorted(base.glob("*/manifest.json"), key=lambda p: p.stat().st_mtime, reverse=True) if base.exists() else []
    for m in ms:
        source = _read_json(m, {}).get("case")
        if case is None or (source and _inside(Path(source)) == case):
            return m.parent
    return None


def _candidates(table_md):
    """(candidate, lo, hi) rows of the candidate table."""
    out = []
    for line in (table_md or "").splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) >= 3:
            try:
                out.append({"candidate": cells[0], "lo": float(cells[1]), "hi": float(cells[2]), "dominated": len(cells) > 8 and cells[8] not in ("", "—")})
            except ValueError:
                pass
    return out


def workspace(path: str):
    f = _inside(Path(path))
    c = _read_json(f, {})
    if not c.get("roles"):
        raise ValueError("Case not found")
    d = latest_run(f.stem, f)
    # A launched job is visible immediately, before the pipeline writes its first manifest.
    active = [(key, j) for key, j in list(JOBS.items()) if j.get("case") == _rel(f) and j["proc"].poll() is None]
    if active:
        d = _inside(Path(active[-1][0]))
    ws = {"path": _rel(f), "case": c, "input_case": c, "input_revision": _signature(f), "status": "none", "run": None,
          "materials": [{"path": p, "name": (_read_json(_inside(Path(p)).with_suffix(".meta.json"), {}) or {}).get("name", Path(p).name)} for p in c.get("documents", [])]}
    if d is None:
        return ws
    man = _read_json(d / "manifest.json", {})
    job = JOBS.get(_rel(d))
    running = bool(job and job["proc"].poll() is None)
    stages = man.get("stages", {})
    q = _read_json(d / "questions.json") or {}
    ext = _read_json(d / "extracted.json") or {}
    todo = _read_json(d / "todo.json") or []
    ws["run"] = {"dir": _rel(d), "run_id": man.get("run_id", d.name), "finished": man.get("finished"), "answers_file": q.get("answers_file") or man.get("options", {}).get("answers")}
    snap = _read_json(d / "ui-input.json", {})
    ws["freshness"] = "current" if snap else "unverified"
    answers_changed = bool(snap.get("answers_path") and snap.get("answers_signature") != _answers_signature(snap["answers_path"]))
    if snap and (snap.get("signature") != ws["input_revision"] or answers_changed):
        ws.update(status="stale", freshness="stale", questions=[], plan=None, candidates=[])
        return ws
    failed = next(((k, v) for k, v in stages.items() if v.get("status") == "fail"), None)
    if running:
        ws["status"] = "running"
    elif failed:
        ws["status"] = "error"
        ws["error"] = {"stage": failed[0], "message": failed[1].get("note") or (q.get("note") if failed[0] == "plan" else "") or ""}
        if failed[0] == "verify" and (d / "casecheck.txt").exists():
            ws["error"]["message"] = (d / "casecheck.txt").read_text(encoding="utf-8").strip()[-1500:]
    elif stages.get("review", {}).get("status") == "waiting":
        ws["status"] = "review"
    elif stages.get("plan", {}).get("status") == "pass":
        ws["status"] = "questions" if q.get("questions") else ("plan" if q.get("plan") else "error")
        if ws["status"] == "error":
            ws["error"] = {"stage": "plan", "message": q.get("note", "")}
    else:
        ws["status"] = "stopped"
    ws["read"] = [{"path": p_, "value": v, "quote": (ext.get("provenance") or {}).get(p_, {}).get("quote", ""), "source": (ext.get("provenance") or {}).get(p_, {}).get("source", ""),
                   "kind": (ext.get("provenance") or {}).get(p_, {}).get("kind", "")} for p_, v in (ext.get("facts") or {}).items()]
    ws["conflicts"] = [t for t in todo if t.get("kind") == "conflict"]
    ws["violations"] = [t for t in todo if t.get("kind") == "violation"]
    ws["review_data"] = _read_json(d / "review.json", {})
    ws["questions"] = [dict(x, schema=field_schema(x["key"], x.get("value", ""))) for x in q.get("questions") or []]
    ws["plan"] = q.get("plan")
    ws["candidates"] = _candidates((d / "table.md").read_text(encoding="utf-8")) if (d / "table.md").exists() else []
    effective = _read_json(d / "reviewed.json")
    if effective and not running and ws["status"] != "review":
        ws["case"] = effective
    if ws["status"] == "plan" and ws.get("plan", {}).get("structure") and not ws["plan"].get("strategies") and (ws["plan"].get("execution") or {}).get("version", 0) < 2:   # older single workpacks are regenerated, the tax unchanged
        # Add a workpack to older results without changing facts, answers or computed tax.
        from ..execution import build_execution
        ws["plan"]["execution"] = build_execution(ws["plan"], ws["case"], len(ws.get("candidates", [])))
    ws["report_available"] = (d / "report.md").exists() and ws["status"] == "plan"
    return ws


def proceed(path: str, body: dict):
    """The one button of the case page: confirm what was read (writes review.json, continues from the review gate), or
    save the answers to the planner's questions (merges into the answers file, recomputes from the plan stage)."""
    f = _inside(Path(path))
    ws = workspace(path)
    opts = dict(body.get("options") or {})
    if body.get("run_id") and (not ws.get("run") or body["run_id"] != ws["run"]["run_id"]):
        raise ValueError("The analysis changed. Reload this case before submitting the review")
    if body.get("revision") and body["revision"] != ws["input_revision"]:
        raise ValueError("The case inputs changed. Reload before submitting")
    if ws.get("run"):
        previous = _read_json(_inside(Path(ws["run"]["dir"])) / "manifest.json", {}).get("options") or {}
        if previous.get("docs"):
            opts["docs"] = previous["docs"]
        opts["answers"] = ws["run"]["answers_file"] or (f.with_suffix("").as_posix() + ".answers.json")
    if ws["status"] == "review" or (body.get("review") and ws["status"] in ("questions", "plan")):
        save_review(ws["run"]["dir"], {"data": body.get("data") or {}, "notes": body.get("notes") or [], "decisions": body.get("decisions") or {}})
        if ws["status"] in ("questions", "plan"):
            # Earlier answers must not overwrite a correction or rejection when review is reopened.
            opts["answers"] = str(_inside(Path(ws["run"]["dir"])) / ("answers-review-" + uuid.uuid4().hex[:10] + ".json"))
        opts.update(run_id=ws["run"]["run_id"], **{"from": "review"})
    elif ws["status"] in ("questions", "plan"):
        validate_answers(body.get("answers") or {}, ws.get("questions"))
        save_answers(ws["run"]["answers_file"] or (f.with_suffix("").as_posix() + ".answers.json"), body.get("answers") or {})
        opts.update(run_id=ws["run"]["run_id"], **{"from": "plan"})
    return start_pipeline(path, opts)


# ---------------------------------------------------------------- actions
def save_review(d: str, review: dict):
    p = _inside(Path(d))
    if not (p / "todo.json").exists():
        raise FileNotFoundError("not a pipeline run: %s" % d)
    data = dict(review.get("data") or {})
    for key, item in data.items():
        unknown = item == "unknown" or isinstance(item, dict) and item.get("value") in (None, "unknown")
        if unknown and (key.endswith(".loc") or key.startswith(("event.", "transactions.")) or (key.startswith("holds.") and key.endswith(".ratio"))):
            raise ValueError("A core transaction or company value must be corrected in the case structure before continuing")
        if not unknown:
            if item.get("accepted_extracted") or "provenance" in item:
                raise ValueError("Use Accept finding to keep extracted evidence")
            typed_value(key, item["value"])
            if not str(item.get("source") or "").strip():
                raise ValueError("State the source for each corrected value")
    previous = _read_json(p / "review.json", {})
    merged = dict(previous.get("data") or {})
    merged.update(data)
    ext = _read_json(p / "extracted.json", {})
    decisions = dict(previous.get("decisions") or {})
    decisions.update(review.get("decisions") or {})
    for key, decision in (review.get("decisions") or {}).items():
        if decision == "keep":
            merged.pop(key, None)
        elif decision == "accept":
            if key not in ext.get("facts", {}):
                raise ValueError("This finding is no longer available. Reload the review")
            pv = (ext.get("provenance") or {}).get(key, {})
            merged[key] = {"value": ext["facts"][key], "source": pv.get("source", ""), "quote": pv.get("quote", ""),
                           "provenance": pv, "accepted_extracted": True}
    notes = list(dict.fromkeys((previous.get("notes") or []) + (review.get("notes") or [])))
    if not all(isinstance(n, str) for n in notes):
        raise ValueError("Review notes must be text")
    body = {"data": merged, "decisions": decisions, "notes": notes, "saved_at": time.strftime("%Y-%m-%dT%H:%M:%S")}
    (p / "review.json").write_text(json.dumps(body, ensure_ascii=False, indent=1), encoding="utf-8")
    return {"saved": _rel(p / "review.json"), "items": len(body["data"])}


def save_answers(path: str, answers: dict):
    p = _inside(Path(path))
    validate_answers(answers)
    p.parent.mkdir(parents=True, exist_ok=True)
    cur = _read_json(p, {"data": {}, "actions": {}, "rulings": {}, "library": {}}) if p.exists() else {"data": {}, "actions": {}, "rulings": {}, "library": {}}
    for sec in ("data", "actions", "rulings", "library"):
        cur.setdefault(sec, {}).update(answers.get(sec, {}) or {})
    p.write_text(json.dumps(cur, ensure_ascii=False, indent=1), encoding="utf-8")
    return {"saved": _rel(p), "counts": {sec: len(cur.get(sec, {})) for sec in ("data", "actions", "rulings", "library")}}


def save_case(path: str, case: dict):
    """A case file a person edits in the page: validated by the same loader the pipeline uses before it is written."""
    p = _inside(Path(path))
    if any(j.get("case") == _rel(p) and j["proc"].poll() is None for j in list(JOBS.values())):
        raise ValueError("Wait for the current analysis to finish before changing facts")
    if not p.suffix == ".json" or ".." in p.name:
        raise ValueError("case path")
    import tempfile
    from ..ex_ante import validate_core
    from ..run import load_case
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td) / p.name
        tmp.write_text(json.dumps(case, ensure_ascii=False, indent=1), encoding="utf-8")
        template, c, event, subject, ticks, notes = load_case(tmp)
        missing = template.check_case(event, c)
        if missing:
            raise ValueError("Missing parties: %s" % ", ".join(missing))
        g = template.build(event, c.present, c)
        validate_core(g)
        try:
            scope_check(g, names=case.get("names"))             # decision D52: income tax only
        except Reject as e:
            raise ValueError(str(e))
    # Capture legacy input before the first edit so an old result can never appear current after a change.
    if p.exists():
        old_run = latest_run(p.stem, p)
        if old_run and not (old_run / "ui-input.json").exists():
            (old_run / "ui-input.json").write_text(json.dumps({"signature": _signature(p)}), encoding="utf-8")
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(case, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return {"saved": _rel(p), "template": template.name}


def create_case(body):
    c = build_recorded_case(body) if "companies" in body else build_case(body)
    slug = re.sub(r"[^a-zA-Z0-9_-]+", "-", c["case_id"]).strip("-")[:50] or "case"
    return save_case("cases/private/%s-%s.json" % (slug, uuid.uuid4().hex[:8]), c)


def save_structure(body):
    p = _inside(Path(body["path"]))
    c = _read_json(p, {})
    if c.get("template") != "recorded":
        raise ValueError("This editor applies to recorded transaction assessments")
    if body.get("revision") != _signature(p):
        raise ValueError("This case changed in another view. Reload before saving the structure")
    return save_case(_rel(p), build_recorded_case(body, c))


def upload_material(body):
    p = _inside(Path(body["path"]))
    c = _read_json(p)
    if not c or not c.get("roles"):
        raise ValueError("Save the case before adding documents")
    if workspace(_rel(p))["status"] == "running":
        raise ValueError("Wait for the current analysis to finish before changing documents")
    name = Path(body["name"]).name
    raw = base64.b64decode(body["content"], validate=True)
    if len(raw) > 15 * 1024 * 1024:
        raise ValueError("Choose a document smaller than 15 MB")
    ext = Path(name).suffix.lower()
    if ext in (".txt", ".md"):
        content = raw.decode("utf-8-sig")
    elif ext == ".pdf":
        import tempfile
        converter = shutil.which("pdftotext")
        if not converter:
            raise ValueError("PDF text extraction is unavailable; upload a UTF-8 text version")
        with tempfile.TemporaryDirectory() as td:
            src = Path(td) / "document.pdf"
            src.write_bytes(raw)
            result = subprocess.run([converter, "-layout", "-enc", "UTF-8", str(src), "-"], capture_output=True, timeout=60)
            if result.returncode:
                raise ValueError("Could not read this PDF; upload a text version")
            content = result.stdout.decode("utf-8")
    else:
        raise ValueError("Supported documents: PDF, UTF-8 TXT and Markdown")
    if len(content.strip()) < 20:
        raise ValueError("No usable text found. For scanned PDFs, run OCR first and upload the text")
    folder = ROOT / "cases" / "ui_materials" / hashlib.sha256(_rel(p).encode()).hexdigest()[:16]
    folder.mkdir(parents=True, exist_ok=True)
    key = re.sub(r"[^a-zA-Z0-9_-]", "-", Path(name).stem)[:40] or "document"
    dest = folder / (key + "-" + hashlib.sha256(raw).hexdigest()[:12] + ".txt")
    dest.write_text(content, encoding="utf-8")
    dest.with_suffix(".meta.json").write_text(json.dumps({"name": name}), encoding="utf-8")
    c.setdefault("documents", [])
    if _rel(dest) not in c["documents"]:
        c["documents"].append(_rel(dest))
    save_case(_rel(p), c)
    return {"saved": _rel(dest), "name": name, "characters": len(content)}


def evidence(rule_id):
    from ..engine import RULES
    from ..params import Params
    csv.field_size_limit(20 * 1024 * 1024)
    r = next((r for r in RULES if r.id == rule_id), None)
    params = Params().rows
    sources = list(r.sources) if r else [rule_id]
    cites = {params[s]["cite_id"] if s in params else s for s in sources}
    with (ROOT / "official" / "manifest.csv").open(encoding="utf-8-sig", newline="") as f:
        docs_ = {x["id"]: x for x in csv.DictReader(f)}
    with (ROOT / "official" / "clauses.csv").open(encoding="utf-8-sig", newline="") as f:
        rows = [x for x in csv.DictReader(f) if x["cite_id"] in cites]
    return {"rule": rule_id, "effect": r.effect.value.replace("_", " ").title() if r else "Legal provision",
            "valid_from": str(r.valid[0] or "") if r else "", "valid_to": str(r.valid[1] or "") if r else "",
            "sources": [{"cite_id": x["cite_id"], "label": x["label"], "text": x["text"],
                         "excerpts": list(dict.fromkeys(params[s]["quote"] for s in sources if s in params and params[s]["cite_id"] == x["cite_id"] and params[s].get("quote"))),
                         "title": docs_.get(x["doc_id"], {}).get("title", x["doc_id"]),
                         "url": docs_.get(x["doc_id"], {}).get("url", "")} for x in rows]}


def delete_case(path: str):
    """A conversation and what belongs to it: the case file, its answers, its uploaded materials, its runs. Only under cases/private."""
    p = _inside(Path(path))
    if _rel(p).replace("\\", "/").rsplit("/", 1)[0] != "cases/private" or p.suffix != ".json":
        raise ValueError("Only conversations under cases/private can be deleted here")
    if any(j.get("case") == _rel(p) and j["proc"].poll() is None for j in list(JOBS.values())):
        raise ValueError("Wait for the current analysis to finish")
    removed = []
    for f in (p, p.with_suffix("").with_name(p.stem + ".answers.json")):
        if f.exists():
            f.unlink(); removed.append(_rel(f))
    scope_ = hashlib.sha256(_rel(p).encode()).hexdigest()[:16]
    for d in (ROOT / "cases" / "ui_materials" / scope_, ROOT / "out" / "pipeline" / p.stem, ROOT / "out" / "ui_answers" / scope_):
        if d.exists():
            shutil.rmtree(str(d), ignore_errors=True); removed.append(_rel(d))
    return {"removed": removed}


def _agent_setup(body: dict):
    ws = workspace(body["path"])
    if ws.get("status") != "plan" or not ws.get("plan"):
        raise ValueError("The assistant needs a completed plan")
    plan = ws["plan"]
    strategies = plan.get("strategies") or []
    sid = body.get("strategy")
    strategy = next((s for s in strategies if s.get("id") == sid), strategies[0] if strategies else {"id": 1, "guaranteed": plan.get("guaranteed"), "best": plan.get("best"), "cand": plan.get("cand"), "assumes_favourable": [], "labels": {}, "plan": plan})
    return ws, plan, strategy, _inside(Path(ws["run"]["dir"]))


def agent_reply(body: dict, on_event=None):
    """One turn of the strategy assistant: scoped to the case's current plan and the chosen strategy (优化方案.md §6)."""
    from .agent import chat
    ws, plan, strategy, run_dir = _agent_setup(body)
    message = str(body.get("message") or "").strip()
    if not message or len(message) > 4000:
        raise ValueError("Write a message of up to 4000 characters")
    model = str((body.get("options") or {}).get("model") or "deepseek-flash")
    return chat(ws["case"], plan, strategy, message, model, run_dir, on_event)


def agent_thread(path: str, strategy):
    from .agent import load_thread
    ws, plan, st, run_dir = _agent_setup({"path": path, "strategy": strategy})
    return {"strategy": st.get("id"), "messages": load_thread(run_dir, st.get("id"))}


def start_pipeline(case: str, opts: dict):
    with _LOCK:
        return _start_pipeline(case, opts)


def _start_pipeline(case: str, opts: dict):
    p = _inside(Path(case))
    opts = dict(opts)
    if not p.exists() or not _read_json(p, {}).get("roles"):
        raise ValueError("Save a valid case first")
    if _read_json(p, {}).get("template") == "recorded" and not opts.get("answers"):
        scope = hashlib.sha256(_rel(p).encode("utf-8")).hexdigest()[:16]
        opts["answers"] = str(ROOT / "out" / "ui_answers" / scope / (_signature(p)[:20] + ".json"))
    if any(j.get("case") == _rel(p) and j["proc"].poll() is None for j in list(JOBS.values())):
        raise ValueError("This case already has an analysis in progress")
    run_id = opts.get("run_id") or (time.strftime("%Y%m%dT%H%M%S") + "-" + uuid.uuid4().hex[:6])
    if not re.fullmatch(r"[A-Za-z0-9_-]+", run_id):
        raise ValueError("Invalid analysis identifier")
    argv = [PY, "-X", "utf8", "-m", "tax_graph.pipeline", str(p), "--run-id", run_id]
    for flag in ("model", "registry", "from", "until", "k", "timeout", "answers"):
        if opts.get(flag):
            argv += ["--" + flag, str(opts[flag])]
    for doc in opts.get("docs") or []:
        argv += ["--docs", str(_inside(Path(doc))) ]
    for flag in ("auto", "no-dense", "no-patterns"):
        if opts.get(flag):
            argv.append("--" + flag)
    d = ROOT / "out" / "pipeline" / p.stem / run_id
    d.mkdir(parents=True, exist_ok=True)
    answer_path = opts.get("answers") or (p.with_suffix("").as_posix() + ".answers.json")
    (d / "ui-input.json").write_text(json.dumps({"signature": _signature(p), "answers_path": answer_path,
                                               "answers_signature": _answers_signature(answer_path)}), encoding="utf-8")
    log = d / "ui.log"
    f = open(str(log), "ab")
    proc = subprocess.Popen(argv, cwd=str(ROOT), stdout=f, stderr=subprocess.STDOUT)
    f.close()
    with _LOCK:
        JOBS[_rel(d)] = {"proc": proc, "case": _rel(p), "started": time.strftime("%Y-%m-%dT%H:%M:%S"), "argv": argv[3:], "log": log}
    return {"dir": _rel(d), "run_id": run_id, "argv": argv[3:]}


# ---------------------------------------------------------------- http
class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):                        # quiet
        pass

    def _send(self, code, body, ctype="application/json; charset=utf-8"):
        data = body if isinstance(body, bytes) else json.dumps(body, ensure_ascii=False, default=str).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        u = urllib.parse.urlparse(self.path)
        q = {k: v[0] for k, v in urllib.parse.parse_qs(u.query).items()}
        try:
            if u.path in ("/", "/index.html"):
                return self._send(200, (STATIC / "index.html").read_bytes(), "text/html; charset=utf-8")
            if u.path.startswith("/static/"):
                f = (STATIC / u.path[len("/static/"):]).resolve()
                if STATIC.resolve() not in f.parents or not f.exists():
                    return self._send(404, {"error": "not found"})
                return self._send(200, f.read_bytes(), mimetypes.guess_type(str(f))[0] or "application/octet-stream")
            if u.path == "/api/cases":
                return self._send(200, cases())
            if u.path == "/api/schema":
                return self._send(200, dict(schemas(), transaction_types=TRANSACTION_TYPES, scope={"policy": SCOPE_POLICY, "kinds": scope_kinds()}, describe_guide=DESCRIBE_GUIDE))
            if u.path == "/api/evidence":
                return self._send(200, evidence(q["rule"]))
            if u.path == "/api/agent/thread":
                return self._send(200, agent_thread(q["path"], int(q.get("strategy") or 1)))
            if u.path == "/api/report":
                ws = workspace(q["path"])
                if ws["status"] != "plan" or not ws.get("report_available"):
                    return self._send(409, {"error": "A current completed analysis is required"})
                from ..execution import render_execution
                if q.get("strategy"):                                              # one strategy's own report
                    sts = (ws["plan"] or {}).get("strategies") or []
                    st = next((s for s in sts if str(s.get("id")) == q["strategy"]), None)
                    plan_ = (st.get("plan") if st else None) or ws["plan"]
                    if not plan_.get("execution"):
                        return self._send(404, {"error": "no such strategy"})
                    taken = ("rulings taken as favourable on this path: " + "; ".join(st["labels"].get(k, k) for k in st["assumes_favourable"])) if st and st.get("assumes_favourable") else "every open ruling taken against the taxpayer (baseline)"
                    report = "# %s: strategy #%s\n\nGuaranteed tax %s, best case %s; %s.\n\n%s\n" % (
                        ws["case"].get("case_id", ""), q["strategy"], (st or plan_).get("guaranteed"), (st or plan_).get("best"), taken, render_execution(plan_["execution"]))
                    name = "strategy-%s.md" % q["strategy"]
                else:
                    report = (_inside(Path(ws["run"]["dir"])) / "report.md").read_text(encoding="utf-8")
                    if "## Implementation plan" not in report and ws["plan"].get("execution"):
                        report += "\n\n" + render_execution(ws["plan"]["execution"]) + "\n"
                    name = "tax-analysis.md"
                self.send_response(200)
                self.send_header("Content-Type", "text/markdown; charset=utf-8")
                self.send_header("Content-Disposition", 'attachment; filename="%s"' % name)
                self.end_headers()
                self.wfile.write(report.encode("utf-8"))
                return
            if u.path == "/api/workspace":
                return self._send(200, workspace(q["path"]))
            if u.path == "/api/case":
                return self._send(200, case_detail(q["path"]))
            if u.path == "/api/runs":
                return self._send(200, runs(q.get("case")))
            if u.path == "/api/run":
                return self._send(200, run_detail(q["dir"]))
            if u.path == "/api/verify":
                return self._send(200, verify_index())
            if u.path == "/api/verify/run":
                return self._send(200, verify_run(q["run_id"]))
            if u.path == "/api/evals":
                return self._send(200, evals())
            if u.path == "/api/docs":
                return self._send(200, docs())
            return self._send(404, {"error": "no such route"})
        except Exception as e:
            return self._send(500, {"error": "%s: %s" % (type(e).__name__, e)})

    def do_POST(self):
        u = urllib.parse.urlparse(self.path)
        n = int(self.headers.get("Content-Length") or 0)
        try:
            if n > 22 * 1024 * 1024:
                return self._send(413, {"error": "The upload is too large"})
            body = json.loads(self.rfile.read(n).decode("utf-8")) if n else {}
            if u.path == "/api/case/create":
                return self._send(200, create_case(body))
            if u.path == "/api/intake/preview":
                original = _read_json(_inside(Path(body["path"])), {}) if body.get("path") else None
                return self._send(200, collection_preview(body, original))
            if u.path == "/api/case/structure":
                return self._send(200, save_structure(body))
            if u.path == "/api/materials":
                return self._send(200, upload_material(body))
            if u.path == "/api/review":
                return self._send(200, save_review(body["dir"], body))
            if u.path == "/api/answers":
                return self._send(200, save_answers(body["path"], body.get("answers", {})))
            if u.path == "/api/case/save":
                return self._send(200, save_case(body["path"], body["case"]))
            if u.path == "/api/proceed":
                return self._send(200, proceed(body["path"], body))
            if u.path == "/api/pipeline/run":
                return self._send(200, start_pipeline(body["case"], body.get("options", {})))
            if u.path == "/api/agent/stream":
                self.send_response(200)
                self.send_header("Content-Type", "text/event-stream; charset=utf-8")
                self.send_header("Cache-Control", "no-cache")
                self.end_headers()

                def emit(kind, data):
                    try:
                        self.wfile.write(("event: %s\ndata: %s\n\n" % (kind, json.dumps(data, ensure_ascii=False))).encode("utf-8"))
                        self.wfile.flush()
                    except Exception:                                 # noqa: BLE001  a closed stream must not become a second response
                        pass
                try:
                    agent_reply(body, emit)
                except Exception as e:                              # noqa: BLE001
                    emit("error", {"error": "%s: %s" % (type(e).__name__, e)})
                return
            if u.path == "/api/case/delete":
                return self._send(200, delete_case(body["path"]))
            if u.path == "/api/describe":
                return self._send(200, describe_case(body.get("text", ""), str((body.get("options") or {}).get("model") or "deepseek-flash")))
            return self._send(404, {"error": "no such route"})
        except Exception as e:
            return self._send(400, {"error": "%s: %s" % (type(e).__name__, e)})


def main(argv):
    port = int(argv[argv.index("--port") + 1]) if "--port" in argv else 8765
    srv = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    out = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    out.write("tax_graph ui: http://127.0.0.1:%d  (Ctrl+C to stop)\n" % port)
    out.flush()
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
