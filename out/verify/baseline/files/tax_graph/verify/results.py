"""统一结果格式 (测试系统.md §5): every check writes rows of the same eleven fields, one run = one jsonl file under
out/verify/, plus an index (out/verify/index.json) the UI reads; history is kept so trends can be drawn.

    run_id    <YYYYMMDDTHHMMSS>-<tier>
    layer     A 资料与规则 | B 计算正确性 | C 结果稳定性 | D 方案优越性 | 充分性 | 依据 (grounding, see grounding.py)
    check_id  the check (one registry entry may write several rows)
    subject   系统 | 案例 | 方案 | 规则 | 条款 — what the row is about
    status    pass | fail | warn | na
    measured / expected
    oracle    官方 (labels, worked examples) | 推导 (metamorphic relations, independent recomputation, formal accounts)
              | 不变式 (defects, crashes, library constraints) | 快照 (gold, fingerprint, attribution)
              | 条文 (expected values hand-read from the cited provisions by the check's author — not an official
              calculator and not a derived relation; the scenario checks say so in their docstrings)
    evidence  clauses, files, commands
    version   code and library fingerprint (see version())
    seconds   wall time of the check that produced the row

The version is a hash over the snapshot sets below (code, library data the engine reads, labels, cases); the same sets
are what a baseline copies (fp.py) so that a later change can be attributed to files (attribution.py).
"""
import hashlib
import json
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "out" / "verify"
FIELDS = ("run_id", "layer", "check_id", "subject", "status", "measured", "expected", "oracle", "evidence", "version", "seconds")
STATUSES = ("pass", "fail", "warn", "na")
LAYERS = ("A", "B", "C", "D", "充分性", "依据")
ORACLES = ("官方", "推导", "不变式", "快照", "条文")

# (directory under ROOT, glob) — relative paths, __pycache__ excluded
SNAPSHOT_SETS = {
    "code": [("tax_graph", "**/*.py")],
    "library": [("official", "params.csv"), ("official", "clauses.csv"), ("official", "decisions.csv"),
                ("official", "form_fields.csv"), ("official", "currency.csv"), ("official/calendars", "*.csv"),
                ("official/labels", "*.csv")],
    "cases": [("cases", "**/*.json")],
}
# what a fingerprint run needs at runtime (the scratch tree of attribution.py copies these): the rule compiler reads
# clauses.csv and labels/observed_rules.csv to check the cites, the procedures read the calendars
RUNTIME_SETS = [("tax_graph", "**/*.py"), ("official", "params.csv"), ("official", "clauses.csv"), ("official", "form_fields.csv"),
                ("official", "currency.csv"), ("official/calendars", "*.csv"), ("official/labels", "*.csv"), ("cases/battery", "*.json")]


def files_of(sets, root=None):
    """Sorted relative paths (posix) of the files the sets name, under `root` (the project by default)."""
    root = Path(root or ROOT)
    out = set()
    for d, pat in sets:
        base = root / d
        if not base.exists():
            continue
        for p in base.glob(pat):
            if p.is_file() and "__pycache__" not in p.parts:
                out.add(p.relative_to(root).as_posix())
    return sorted(out)


def snapshot_files(root=None):
    return files_of([x for s in SNAPSHOT_SETS.values() for x in s], root)


def _digest(rels, root=None):
    root = Path(root or ROOT)
    h = hashlib.sha256()
    for rel in rels:
        h.update(rel.encode("utf-8"))
        h.update(b"\0")
        h.update((root / rel).read_bytes())
        h.update(b"\0")
    return h.hexdigest()


def version(root=None):
    """{"code": ..., "library": ..., "cases": ..., "short": "<code8>-<library8>"}; each a sha256 prefix over the set,
    of the project tree or of another tree (a baseline copy) holding the same layout."""
    parts = {k: _digest(files_of(v, root), root)[:12] for k, v in SNAPSHOT_SETS.items()}
    parts["short"] = parts["code"][:8] + "-" + parts["library"][:8]
    return parts


class Run:
    """Collects the rows of one run; finish() writes out/verify/<run_id>.jsonl and updates the index."""

    def __init__(self, tier, run_id=None):
        self.tier = tier
        self.started = time.time()
        self.run_id = run_id or (time.strftime("%Y%m%dT%H%M%S") + "-" + tier)
        self.version = version()
        self.records = []
        self.meta = {}
        OUT.mkdir(parents=True, exist_ok=True)
        self.path = OUT / (self.run_id + ".jsonl")
        self.path.write_text("", encoding="utf-8")       # rows are appended as they come: a killed run still leaves its rows

    def add(self, layer, check_id, subject, status, measured="", expected="", oracle="", evidence="", seconds=0.0):
        if status not in STATUSES:
            raise ValueError("status %r" % status)
        if layer not in LAYERS:
            raise ValueError("layer %r" % layer)
        rec = {"run_id": self.run_id, "layer": layer, "check_id": check_id, "subject": str(subject)[:200], "status": status,
               "measured": str(measured)[:400], "expected": str(expected)[:200], "oracle": oracle, "evidence": str(evidence)[:400],
               "version": self.version["short"], "seconds": round(float(seconds), 1)}
        self.records.append(rec)
        with open(str(self.path), "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        return rec

    def extend(self, recs, seconds=None):
        """Rows a check returned (dicts without run_id / version); `seconds` stamps them all."""
        for r in recs:
            r = dict(r)
            if seconds is not None:
                r["seconds"] = seconds
            r.pop("run_id", None)
            r.pop("version", None)
            self.add(**r)

    def counts(self):
        c = {s: 0 for s in STATUSES}
        for r in self.records:
            c[r["status"]] += 1
        return c

    def by_check(self):
        """check_id -> worst status, the system-level row's measured value, seconds."""
        rank = {"fail": 3, "warn": 2, "na": 1, "pass": 0}
        out = {}
        for r in self.records:
            cur = out.setdefault(r["check_id"], {"status": "pass", "measured": "", "seconds": r["seconds"], "rows": 0})
            cur["rows"] += 1
            if rank[r["status"]] > rank[cur["status"]]:
                cur["status"] = r["status"]
            if r["subject"].startswith("系统") or not cur["measured"]:
                cur["measured"] = r["measured"]
            cur["seconds"] = max(cur["seconds"], r["seconds"])
        return out

    def finish(self, extra=None):
        path = self.path
        entry = {"run_id": self.run_id, "tier": self.tier, "started": time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(self.started)),
                 "seconds": round(time.time() - self.started, 1), "version": self.version, "counts": self.counts(),
                 "checks": self.by_check(), "file": path.name}
        entry.update(self.meta)
        if extra:
            entry.update(extra)
        index = load_index()
        index["runs"] = [e for e in index["runs"] if e["run_id"] != self.run_id] + [entry]
        (OUT / "index.json").write_text(json.dumps(index, ensure_ascii=False, indent=1), encoding="utf-8")
        return path


def load_index():
    p = OUT / "index.json"
    if p.exists():
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except ValueError:
            pass
    return {"format": FIELDS, "runs": []}


def read_run(path):
    with open(str(path), encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]
