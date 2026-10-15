"""extract (信息收集.md P1–P4, §8): documents -> facts for the fields a case needs, each with the quote it rests on.

Two passes, both driven by the field list the rules produce (fields.required_fields), never by a problem type:

    pass 1  locate   for every field, the passages of the documents that bear on it (or none)
    pass 2  read     one typed value per field from its passages, with the verbatim quote behind it — read `samples`
                     times independently; the samples must agree, or the field stays missing

The model is a parameter: any callable prompt -> text (JSON). Everything around it is program: the field
specifications come from the compiled rules (predicate -> type, enum params -> allowed values), the field dictionary
(data/field_gloss.csv: meaning, unit) and the evidence column of 信息收集.md; replies are validated against them; a
quote that is not found in the document (quotes.loose: letters, digits, CJK) is not evidence, so the field stays
missing (P4); units follow the rules (ratios in percent, periods in months, amounts in the flow's currency). The model
cannot stop the program: a call that fails, a reply that is not JSON, a value of the wrong type, two samples that
disagree — each leaves the field missing with the reason recorded, and a missing field is a question for a person,
never a value. Nothing here decides tax; what comes out is Case facts plus evidence.

    python -m tax_graph.llm.extract CASE.json --docs DIR|FILE [--model deepseek-flash] [--samples 2] [--flow ID] [--write]

reads the fields the rules would read on the case's present structure and the case does not state
(fields.missing_fields), extracts them from the documents (a directory of *.txt, or one file; cases/sources/<id>/
source.txt gets the archive's id, so the case check can verify every quote), and writes CASE.extracted.json: the
values, their quotes as case-file provenance (案例采集.md §4.2), what stayed missing and why. --write also writes
CASE.filled.json, the case with those values and provenance merged in (stated values are kept) and a note that it was
machine-read — for a person to review and the case check to verify before it is used.
"""
import csv
import json
import re
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple

from ..engine import RULES
from ..params import Params
from ..quotes import found, loose
from ..rules.model import ALL, And, Discretion, Leaf, Not, Or, eq, ge, gt, is_false, is_in, is_true, le, lt

ROOT = Path(__file__).resolve().parents[2]
DOC = ROOT / "信息收集.md"
GLOSS_FILE = ROOT / "tax_graph" / "data" / "field_gloss.csv"
BOOL, NUMBER, ENUM, DATE, TEXT = "bool", "number", "enum", "date", "text"
SAMPLES = 2


@dataclass(frozen=True)
class FieldSpec:
    key: str                              # "payee.residence_cert"
    kind: str                             # bool | number | enum | date | text
    rules: Tuple[str, ...]                # rule ids that read it
    hint: str = ""                        # evidence column of 信息收集.md for the field's group
    allowed: Tuple[str, ...] = ()         # enum values, from the param the predicate compares with
    gloss: str = ""                       # meaning, from data/field_gloss.csv
    unit: str = ""                        # unit / value kind, from data/field_gloss.csv


@dataclass
class Extraction:
    facts: Dict[Tuple[str, str], object] = field(default_factory=dict)       # (elem, field) -> value
    evidence: Dict[Tuple[str, str], Tuple[str, str]] = field(default_factory=dict)   # -> (doc id, quote)
    missing: List[str] = field(default_factory=list)                          # keys with no accepted value
    rejected: List[Tuple[str, str]] = field(default_factory=list)             # (key, why) — a reply the program refused
    notes: List[str] = field(default_factory=list)                            # what went wrong with the model itself


# ---------------------------------------------------------------- field specifications, from the rules
def _leaves(c, out):
    if isinstance(c, Leaf):
        out.append(c)
    elif isinstance(c, (And, Or)):
        for x in c.xs:
            _leaves(x, out)
    elif isinstance(c, Not):
        _leaves(c.x, out)


def _hints():
    """Field -> the evidence column of its group in 信息收集.md §3–§4 (same parse as check_fields.doc_fields)."""
    text = DOC.read_text(encoding="utf-8")
    sec = text[text.index("## 3. CONDITIONAL"):text.index("## 5. 激活与收集")]
    hints = {}
    for row in sec.splitlines():
        cells = [c.strip() for c in row.split("|")]
        if len(cells) < 6 or not cells[1].startswith("`") or cells[1] == "`mount`":
            continue
        names = [re.sub(r"=.*$", "", n.strip()) for span in re.findall(r"`([^`]*)`", cells[4]) for n in span.split(",")]
        for n in names:
            if re.fullmatch(r"[a-z_][a-z0-9_]*", n):
                hints.setdefault(n, cells[5])
    return hints


def _glosses():
    with open(str(GLOSS_FILE), encoding="utf-8-sig") as f:
        return {r["field"]: r for r in csv.DictReader(f)}


def _gloss_row(name, gloss):
    """As planner._gloss: <name>_hk / _sg / _cn and <name>_<year> read <name>'s row."""
    if name in gloss:
        return gloss[name]
    head, _, suffix = name.rpartition("_")
    if head in gloss and (suffix in ("cn", "hk", "sg") or suffix.isdigit()):
        return gloss[head]
    return {}


def field_specs(rules=None, P=None) -> Dict[str, FieldSpec]:
    """One spec per field the rules read. The predicate fixes the type: is_true/is_false -> bool, is_in -> enum of
    the param's values, comparisons -> number; *_on fields are dates; anything no predicate touches is text."""
    rules, P = rules or RULES, P or Params()
    hints, gloss = _hints(), _glosses()
    kinds, allowed, readers = {}, {}, {}
    for r in rules:
        for key in r.reads:
            readers.setdefault(key, set()).add(r.id)
        leaves = []
        _leaves(r.cond, leaves)
        for lf in leaves:
            key = "%s.%s" % (lf.on, lf.field)
            if lf.pred in (is_true, is_false):
                kinds[key] = BOOL
            elif lf.pred is is_in:
                kinds[key] = ENUM
                if lf.param and lf.param in P.rows:
                    allowed[key] = tuple(str(P.rows[lf.param]["value"]).split(";"))
            elif lf.pred in (ge, gt, le, lt, eq):
                kinds[key] = NUMBER
    specs = {}
    for key, rids in readers.items():
        name = key.split(".", 1)[1]
        kind = kinds.get(key) or (DATE if name.endswith("_on") else TEXT)
        g = _gloss_row(name, gloss)
        specs[key] = FieldSpec(key, kind, tuple(sorted(rids)), hints.get(name, ""), allowed.get(key, ()),
                               g.get("gloss", ""), g.get("value", ""))
    return specs


# ---------------------------------------------------------------- the two passes
def _describe(s: FieldSpec) -> str:
    parts = [s.kind + (" of " + "/".join(s.allowed) if s.allowed else "")]
    if s.gloss:
        parts.append(s.gloss + (" [%s]" % s.unit if s.unit else ""))
    if s.hint:
        parts.append("evidence: " + s.hint)
    return "; ".join(parts)


def _prompt_locate(specs: List[FieldSpec], docs: Dict[str, str]) -> str:
    lines = ["For each field below, list the passages of the documents that bear on it. Answer with JSON only:",
             '{"<field key>": [{"doc": "<doc id>", "quote": "<verbatim passage>"}], ...}. Quote verbatim; an empty list',
             "when the documents say nothing about the field.", "", "FIELDS"]
    for s in specs:
        lines.append("- %s (%s)" % (s.key, _describe(s)))
    lines.append("")
    lines.append("DOCUMENTS")
    for did, text in docs.items():
        lines.append("### %s\n%s" % (did, text))
    return "\n".join(lines)


GUARD = ("Answer null unless a passage states this very quantity for this very party. A related quantity is not it: "
         "a percentage or a ratio where an amount is asked; registered, subscribed or nominal capital where a cost or a "
         "price actually paid is asked; a withholding, treaty or non-resident rate where a jurisdiction's standard "
         "corporate rate is asked; another company's or another year's figure. Do not compute, convert or infer.")


def _prompt_read(spec: FieldSpec, passages: List[dict]) -> str:
    unit = {BOOL: "true or false", NUMBER: "a number; ratios in percent, periods in whole months, amounts as stated",
            ENUM: "one of " + "/".join(spec.allowed), DATE: "an ISO date YYYY-MM-DD", TEXT: "a short string"}[spec.kind]
    lines = ["Read the value of one field from the passages. Answer with JSON only:",
             '{"value": <%s>, "doc": "<doc id>", "quote": "<the verbatim passage the value rests on>"}' % unit,
             'or {"value": null} if the passages do not settle it.', GUARD, "",
             "FIELD: %s" % spec.key, "MEANING: %s" % _describe(spec), "PASSAGES"]
    for p in passages:
        lines.append("- [%s] %s" % (p.get("doc", ""), p.get("quote", "")))
    return "\n".join(lines)


def _json(text: Optional[str]):
    """The first {...} of a reply as JSON, read non-strictly (a raw control character inside a quote is not an
    error); None when there is none or it does not parse."""
    m = re.search(r"\{.*\}", text or "", re.S)
    if not m:
        return None
    try:
        return json.loads(m.group(0), strict=False)
    except ValueError:
        return None


def _coerce(spec: FieldSpec, v):
    """Typed value or (None, reason)."""
    if spec.kind == BOOL:
        if isinstance(v, bool):
            return v, None
        if isinstance(v, str) and v.strip().lower() in ("true", "false", "yes", "no"):
            return v.strip().lower() in ("true", "yes"), None
        return None, "not a boolean"
    if spec.kind == NUMBER:
        if isinstance(v, bool):
            return None, "boolean where a number was expected"
        if isinstance(v, (int, float)):
            return float(v), None
        if isinstance(v, str):
            m = re.fullmatch(r"\s*(-?\d+(?:\.\d+)?)\s*%?\s*", v)
            if m:
                return float(m.group(1)), None
        return None, "not a number"
    if spec.kind == ENUM:
        if isinstance(v, str) and (not spec.allowed or v in spec.allowed):
            return v, None
        return None, "not one of %s" % "/".join(spec.allowed)
    if spec.kind == DATE:
        if isinstance(v, str) and re.fullmatch(r"\d{4}-\d{2}-\d{2}", v):
            y, m, d = map(int, v.split("-"))
            return date(y, m, d), None
        return None, "not an ISO date"
    return (v, None) if isinstance(v, str) else (None, "not text")


def _supported(quote, doc_id, normed):
    """P4: a quote is evidence only if it is found in the named document (quotes.loose on both sides)."""
    return doc_id in normed and found(quote, normed[doc_id])


def _read(spec, passages, ask, normed, samples):
    """One field: `samples` independent readings. Returns (value, doc, quote) or (None, reason-or-None)."""
    got = []
    for _ in range(max(1, samples)):
        reply = ask(_prompt_read(spec, passages), "read %s" % spec.key)
        if reply is None:
            return None, "model call failed"
        r = _json(reply)
        if not isinstance(r, dict):
            return None, "reply is not JSON"
        if r.get("value") is None:
            got.append(None)
            continue
        if not _supported(r.get("quote"), r.get("doc"), normed):
            return None, "quote not found in the document"
        v, why = _coerce(spec, r["value"])
        if why:
            return None, why
        got.append((v, r["doc"], r["quote"]))
    shown = " / ".join("null" if g is None else str(g[0]) for g in got)
    if all(g is None for g in got):
        return None, None                                        # the model says the passages do not settle it
    if any(g is None for g in got) or len({str(g[0]) for g in got}) > 1:
        return None, "samples disagree: " + shown
    return got[0], None


def extract(docs: Dict[str, str], keys: List[str], model: Callable[[str], str], specs=None, samples=SAMPLES) -> Extraction:
    """docs: document id -> text. keys: the (flow or entity) fields wanted, as "elem.field". Returns facts with evidence;
    whatever the documents do not settle stays missing, and the rules treat it as U(MISSING)."""
    specs = specs or field_specs()
    wanted = [specs[k] if k in specs else FieldSpec(k, TEXT, ()) for k in keys]
    normed = {d: loose(t) for d, t in docs.items()}
    out = Extraction()

    def ask(prompt, what):
        try:
            return model(prompt)
        except Exception as e:                                   # the model's failure is a note, never a stop
            out.notes.append("%s: model call failed: %s: %s" % (what, type(e).__name__, e))
            return None

    reply = ask(_prompt_locate(wanted, docs), "locate")
    located = _json(reply)
    if not isinstance(located, dict):
        if reply is not None:
            out.notes.append("locate: reply is not JSON; every field stays missing")
        out.missing.extend(s.key for s in wanted)
        return out
    for s in wanted:
        passages = [p for p in (located.get(s.key) or []) if isinstance(p, dict) and _supported(p.get("quote"), p.get("doc"), normed)]
        if not passages:
            out.missing.append(s.key)
            continue
        got, why = _read(s, passages, ask, normed, samples)
        if got is None:
            if why:
                out.rejected.append((s.key, why))
            out.missing.append(s.key)
            continue
        value, doc, quote = got
        elem, name = s.key.split(".", 1)
        out.facts[(elem, name)] = value
        out.evidence[(elem, name)] = (doc, quote)
    return out


def apply(extraction: Extraction, attrs_of: Dict[str, dict]):
    """Merge extracted facts into attrs dicts keyed by elem ("payer" | "payee" | "flow"); stated values are kept."""
    for (elem, name), v in extraction.facts.items():
        attrs_of.setdefault(elem, {}).setdefault(name, v)
    return attrs_of


def provenance(extraction: Extraction, path_of: Callable[[Tuple[str, str]], str]) -> Dict[str, dict]:
    """Case-file provenance rows (案例采集.md §4.2) for the extracted facts: disclosed, with the quote and its source."""
    return {path_of(k): {"kind": "disclosed", "source": doc, "quote": quote} for k, (doc, quote) in extraction.evidence.items()}


# ---------------------------------------------------------------- a case's missing fields from its documents
def load_docs(where: Path) -> Dict[str, str]:
    """A directory of *.txt (or one file) -> doc id -> text. cases/sources/<id>/source.txt is known as <id>."""
    files = sorted(where.glob("*.txt")) if where.is_dir() else [where]
    docs = {}
    for f in files:
        did = f.parent.name if f.name == "source.txt" else f.stem
        docs[did] = f.read_text(encoding="utf-8")
    return docs


def _path_of(fid, payer, payee):
    def path(k):
        elem, name = k
        if elem == "flow":
            return "flows.%s.%s" % (fid, name)
        return "roles.%s.attrs.%s" % (payer if elem == "payer" else payee, name)
    return path


def _plain(v):
    return v.isoformat() if isinstance(v, date) else v


def extract_case(path, docs, model, samples=SAMPLES, only_flow=None, names=None):
    """The fields the rules read on the case's present structure and the case does not state, flow by flow."""
    from ..fields import missing_fields
    from ..run import load_case
    template, case, event, _, _, _ = load_case(path)
    g = template.build(event, case.present, case)
    names = names or {}
    wanted = {}
    for fid, key in sorted(missing_fields(g)):
        if only_flow is None or fid == only_flow:
            wanted.setdefault(fid, []).append(key)
    result = {"case": str(path), "model": getattr(model, "model", type(model).__name__), "samples": samples, "docs": sorted(docs),
              "facts": {}, "provenance": {}, "missing": [], "rejected": [], "notes": []}
    for f in g.flows:
        if f.id not in wanted:
            continue
        who = lambda e: "%s (%s%s)" % (e, g.entities[e].loc, ", " + names[e] if e in names else "")
        brief = ("CASE: flow %s is %s of %s %s on %s, paid by %s to %s%s. Fields named payer.* are about %s, payee.* about %s, "
                 "flow.* about this payment." % (f.id, f.income, f.amount, f.currency, f.on, who(f.payer), who(f.payee),
                                                 " for the equity of %s" % who(f.target) if f.target else "", f.payer, f.payee))
        ex = extract(docs, wanted[f.id], lambda p: model(brief + "\n\n" + p), samples=samples)
        path_of = _path_of(f.id, f.payer, f.payee)
        result["facts"].update({path_of(k): _plain(v) for k, v in ex.facts.items()})
        result["provenance"].update(provenance(ex, path_of))
        result["missing"].extend("%s:%s" % (f.id, k) for k in ex.missing)
        result["rejected"].extend(["%s:%s" % (f.id, k), why] for k, why in ex.rejected)
        result["notes"].extend("%s: %s" % (f.id, n) for n in ex.notes)
    if hasattr(model, "usage"):
        result["usage"] = dict(model.usage)
    return result


def fill(case_json: dict, result: dict) -> dict:
    """The case with the extracted values and their provenance merged in; stated values and their provenance are kept."""
    d = json.loads(json.dumps(case_json))
    for p, v in result["facts"].items():
        parts = p.split(".")
        if parts[0] == "roles":
            d["roles"].setdefault(parts[1], {}).setdefault("attrs", {}).setdefault(parts[3], v)
        else:
            d.setdefault("flows", {}).setdefault(parts[1], {}).setdefault(parts[2], v)
    prov = d.setdefault("provenance", {})
    for p, e in result["provenance"].items():
        prov.setdefault(p, e)
    d.setdefault("notes", []).append("%d 个字段由 %s 从 %s 读出（%s），引文已逐字核对；用前须有人复核，再跑 tax_graph.verify.casecheck。" % (
        len(result["facts"]), result["model"], "、".join(result["docs"]), date.today().isoformat()))
    return d


def main(argv):
    import io
    import sys
    out = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    path = Path(argv[1])
    docs = load_docs(Path(argv[argv.index("--docs") + 1]))
    model_id = argv[argv.index("--model") + 1] if "--model" in argv else None
    samples = int(argv[argv.index("--samples") + 1]) if "--samples" in argv else SAMPLES
    only = argv[argv.index("--flow") + 1] if "--flow" in argv else None
    from .deepseek import DeepSeek
    model = DeepSeek(model_id) if model_id else DeepSeek()
    case_json = json.loads(path.read_text(encoding="utf-8"))
    result = extract_case(path, docs, model, samples, only, case_json.get("names"))
    dst = path.with_suffix(".extracted.json")
    dst.write_text(json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8")
    out.write("读出 %d 个值，%d 个字段缺失（其中 %d 个因程序拒绝）；模型事件 %d\n" % (
        len(result["facts"]), len(result["missing"]), len(result["rejected"]), len(result["notes"])))
    for p, v in sorted(result["facts"].items()):
        e = result["provenance"][p]
        out.write("  %-48s %-14s %s: %s\n" % (p, v, e["source"], e["quote"][:90].replace("\n", " ")))
    for k, why in result["rejected"]:
        out.write("  拒绝 %-44s %s\n" % (k, why))
    for n in result["notes"]:
        out.write("  事件 %s\n" % n)
    if "usage" in result:
        out.write("  用量 %s\n" % result["usage"])
    out.write("[written to %s]\n" % dst)
    if "--write" in argv:
        filled = path.with_suffix(".filled.json")
        filled.write_text(json.dumps(fill(case_json, result), ensure_ascii=False, indent=1), encoding="utf-8")
        out.write("[written to %s — review, then python -m tax_graph.verify.casecheck %s]\n" % (filled, filled))
    out.flush()
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main(sys.argv))
