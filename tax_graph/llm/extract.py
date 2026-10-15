"""extract (信息收集.md P1–P4, §8; 抽取改造.md §5, §7): documents -> facts for the fields a case needs, each with its quote.

Order of means, cheapest and most inspectable first; a model is the last resort:

    pattern  a regular expression over the whole document (llm/patterns.py) for fields with fixed wordings — place of
             incorporation, a percentage holding — gives the sentences near which the party is named as the first
             candidate passages. It locates; it never settles a value (measured: other parties' sentences).
    table    a financial-statement row (llm/tables.py: years, unit, label, figures) with its header as a candidate passage;
             fields in EUR are derived by the program from the revenue row and the library's fx table (_derive_eur).
    locate   candidate passages per field — by retrieval over the documents' passages (llm/locate.py: BM25 + BGE-M3
             + RRF), by one long-context model call with the field list before and after the documents, or both.
    read     one typed value per field from a passage, with the verbatim quote behind it. Each candidate passage is
             read on its own; a single passage is read `samples` times. The readings must agree, or the field stays
             missing: readings of different passages that disagree are a CONFLICT of the documents (reported with
             every value and quote), readings of one passage that disagree are an unstable model (reported as such).
    parse    a number or a date is accepted only if the program finds it in the quote itself (units million / 亿 / 万 /
             % resolved by the program, a table header's "RMB'000" nearby too); the model names the sentence, the
             program reads the figure.

The model is a parameter: any callable prompt -> text (JSON). Everything around it is program: the field
specifications come from the compiled rules (predicate -> type, enum params -> allowed values) and the field
dictionary (data/field_gloss.csv: meaning, unit, channel, example phrasings) plus the evidence column of 信息收集.md;
replies are validated against them; a quote that is not found in the document (quotes.loose) is not evidence, so the
field stays missing (P4). The model cannot stop the program: a call that fails, a reply that is not JSON, a value of
the wrong type, a value not in its quote, readings that disagree — each leaves the field missing with the reason
recorded, and a missing field is a question for a person, never a value. Nothing here decides tax.

    python -m tax_graph.llm.extract CASE.json --docs DIR|FILE [--model deepseek-flash] [--samples 2] [--k 3]
                                    [--locate retrieval|llm|both] [--channels E,C] [--temperature 0.7] [--flow ID]
                                    [--no-patterns] [--no-dense] [--no-cache] [--jobs 4] [--registry off|file|live] [--timeout 900] [--write]

reads the fields the rules would read on the case's present structure and the case does not state
(fields.missing_fields), keeps only the channels the model is for (E: free text; C: statements when no structured
source is at hand), lists the rest for a person (A: derived, its inputs missing; B: registries; D: authority
documents), extracts from the documents and writes CASE.extracted.json: values, their quotes as case-file provenance
(案例采集.md §4.2), conflicts, what stayed missing and why, and per-field features for a later calibrator.
--write also writes CASE.filled.json (stated values kept, a review note added) for a person to review and the case
check to verify before it is used.
"""
import csv
import json
import re
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple

from ..engine import RULES
from ..model import JURISDICTIONS
from ..params import Params
from ..quotes import found, loose
from ..rules.model import And, Leaf, Not, Or, eq, ge, gt, is_false, is_in, is_true, le, lt
from .patterns import pattern_candidates, scale_hint
from .tables import currency_in, revenue as table_revenue, table_candidates, to_eur, year_end_rate_date

ROOT = Path(__file__).resolve().parents[2]
DOC = ROOT / "信息收集.md"
GLOSS_FILE = ROOT / "tax_graph" / "data" / "field_gloss.csv"
BOOL, NUMBER, ENUM, DATE, TEXT = "bool", "number", "enum", "date", "text"
SAMPLES = 2
K = 3                                                 # candidate passages per field from retrieval
JOBS = 4                                              # fields read concurrently (one model call at a time per field)
ASK_CHANNELS = ("E", "C")                             # what the model is for (抽取改造.md §1); "" = no channel known
UNIT_KIND = {"yes/no": "bool", "derived or yes/no": "bool", "date": "date", "jurisdiction code": "enum", "jurisdiction": "enum", "amount": "number",
             "%": "number", "months": "number", "years": "number", "days": "number", "number": "number", "ratio": "number",
             "amount (per year)": "number"}     # data/field_gloss.csv value column -> type
PROMPT_VERSION = "2026-10-15-en"


@dataclass(frozen=True)
class FieldSpec:
    key: str                              # "payee.residence_cert"
    kind: str                             # bool | number | enum | date | text
    rules: Tuple[str, ...]                # rule ids that read it
    hint: str = ""                        # evidence column of 信息收集.md for the field's group
    allowed: Tuple[str, ...] = ()         # enum values, from the param the predicate compares with
    gloss: str = ""                       # meaning, from data/field_gloss.csv
    unit: str = ""                        # unit / value kind, from data/field_gloss.csv
    channel: str = ""                     # A derived | B registry | C statements | D authority documents | E free text
    examples: str = ""                    # how documents phrase it, from case provenance (data/field_gloss.csv)
    about: str = ""                       # the party a pattern must mention (a name or role), when known


@dataclass
class Extraction:
    facts: Dict[Tuple[str, str], object] = field(default_factory=dict)       # (elem, field) -> value
    evidence: Dict[Tuple[str, str], Tuple[str, str]] = field(default_factory=dict)   # -> (doc id, quote)
    missing: List[str] = field(default_factory=list)                          # keys with no accepted value
    rejected: List[Tuple[str, str]] = field(default_factory=list)             # (key, why) — a reply the program refused
    conflicts: Dict[str, list] = field(default_factory=dict)                  # key -> [{"value", "doc", "quote", "origin"}, ...]
    notes: List[str] = field(default_factory=list)                            # what went wrong with the model itself
    features: Dict[str, dict] = field(default_factory=dict)                   # key -> per-field numbers for a calibrator


# ---------------------------------------------------------------- field specifications, from the rules and the dictionary
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
    the param's values, comparisons -> number; else the dictionary's unit; *_on fields are dates; else text."""
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
        g = _gloss_row(name, gloss)
        kind = kinds.get(key) or UNIT_KIND.get(g.get("value", "")) or (DATE if name.endswith("_on") else TEXT)
        opts = allowed.get(key, ()) or (JURISDICTIONS if g.get("value") in ("jurisdiction code", "jurisdiction") else ())
        specs[key] = FieldSpec(key, kind, tuple(sorted(rids)), hints.get(name, ""), tuple(opts), g.get("gloss", ""),
                               g.get("value", ""), g.get("channel", ""), g.get("examples", ""))
    return specs


# ---------------------------------------------------------------- prompts
def _describe(s: FieldSpec) -> str:
    parts = [s.kind + (" of " + "/".join(s.allowed) if s.allowed else "")]
    if s.gloss:
        parts.append(s.gloss + (" [%s]" % s.unit if s.unit else ""))
    if s.examples:
        parts.append("documents say e.g.: " + s.examples)
    if s.hint:
        parts.append("evidence: " + s.hint)
    return "; ".join(parts)


def _field_list(specs):
    return "\n".join("- %s (%s)" % (s.key, _describe(s)) for s in specs)


def _prompt_locate(specs: List[FieldSpec], docs: Dict[str, str]) -> str:
    """The field list is given before and after the documents (query-aware contextualisation, M3)."""
    lines = ["For each field below, list the passages of the documents that bear on it. Answer with JSON only:",
             '{"<field key>": [{"doc": "<doc id>", "quote": "<verbatim passage>"}], ...}. Quote verbatim; an empty list',
             "when the documents say nothing about the field.", "", "FIELDS", _field_list(specs), "", "DOCUMENTS"]
    for did, text in docs.items():
        lines.append("### %s\n%s" % (did, text))
    lines += ["", "FIELDS (again)", _field_list(specs)]
    return "\n".join(lines)


GUARD = ("Answer null unless a passage states this very quantity for this very party. A related quantity is not it: "
         "a percentage or a ratio where an amount is asked; registered, subscribed or nominal capital where a cost or a "
         "price actually paid is asked; a withholding, treaty or non-resident rate where a jurisdiction's standard "
         "corporate rate is asked; another company's or another year's figure. Do not compute, convert or infer. "
         "For a number or a date, the quote must contain that number or date as written.")


def _prompt_read(spec: FieldSpec, passages: List[dict]) -> str:
    unit = {BOOL: "true or false", NUMBER: "a number: ratios and rates in percent, periods in whole months, amounts in full units of the currency (never thousands or millions)",
            ENUM: "one of " + "/".join(spec.allowed), DATE: "an ISO date YYYY-MM-DD", TEXT: "a short string"}[spec.kind]
    lines = ["Read the value of one field from the passages. Answer with JSON only:",
             '{"value": <%s>, "doc": "<doc id>", "quote": "<the verbatim sentence the value rests on>"}' % unit,
             'or {"value": null} if the passages do not settle it.', GUARD, "",
             "FIELD: %s" % spec.key, "MEANING: %s" % _describe(spec), "PASSAGES"]
    for p in passages:
        lines.append("- [%s] %s" % (p.get("doc", ""), p.get("quote", "")))
    return "\n".join(lines)


def _json(text: Optional[str]):
    """The first {...} of a reply as JSON, read non-strictly; None when there is none or it does not parse."""
    m = re.search(r"\{.*\}", text or "", re.S)
    if not m:
        return None
    try:
        return json.loads(m.group(0), strict=False)
    except ValueError:
        return None


# ---------------------------------------------------------------- the program reads the figure (抽取改造.md §5 C)
_SCALE = {"thousand": 1e3, "k": 1e3, "million": 1e6, "mn": 1e6, "m": 1e6, "billion": 1e9, "bn": 1e9, "b": 1e9,
          "万": 1e4, "亿": 1e8, "千": 1e3, "百万": 1e6, "千万": 1e7, "trillion": 1e12}
_NUM = re.compile(r"(?<![\d.])(\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+(?:\.\d+)?)\s*(%|percent|per cent|百分之|trillion|billion|million|thousand|bn|mn|k|m|b|万|亿|千万|百万|千)?(?![\w])", re.I)


_WORDS = [(re.compile(r"wholly[- ]owned|wholly\s+subscribed|entire\s+(?:issued\s+)?(?:share\s+capital|equity|interest)|sole\s+shareholder|all\s+of\s+the\s+(?:issued\s+)?(?:shares|equity)|全資|全资|全部股权|全部股權|唯一股东|唯一股東", re.I), 100.0),
          (re.compile(r"\bhalf\b|一半", re.I), 50.0), (re.compile(r"\bone[- ]third\b|三分之一", re.I), 100.0 / 3), (re.compile(r"\btwo[- ]thirds\b|三分之二", re.I), 200.0 / 3),
          (re.compile(r"\b(?:a|one)[- ]quarter\b|四分之一", re.I), 25.0)]


def numbers_in(text: str, scale: Optional[float] = None) -> List[float]:
    """Every figure a quote states, with its scale word applied; "46.8 million" gives 46.8 and 46,800,000. A table
    scale (1000 for "RMB'000") adds the scaled reading of each bare figure. A holding stated in words ("wholly
    owned", "sole shareholder", "half") counts as its percentage."""
    out = [v for pat, v in _WORDS if pat.search(text)]
    for raw, unit in _NUM.findall(text):
        v = float(raw.replace(",", ""))
        out.append(v)
        s = (unit or "").lower()
        if s in _SCALE:
            out.append(v * _SCALE[s])
        elif scale and not s:
            out.append(v * scale)
    return out


_MONTHS = {m: i + 1 for i, m in enumerate(["january", "february", "march", "april", "may", "june", "july", "august",
                                            "september", "october", "november", "december"])}
_MONTHS.update({m[:3]: i for m, i in list(_MONTHS.items())})
_MONTHS["sept"] = 9
_DATE_PATTERNS = [
    (re.compile(r"(\d{4})-(\d{1,2})-(\d{1,2})"), lambda m: (int(m[1]), int(m[2]), int(m[3]))),
    (re.compile(r"(\d{4})年(\d{1,2})月(\d{1,2})日"), lambda m: (int(m[1]), int(m[2]), int(m[3]))),
    (re.compile(r"(\d{1,2})(?:st|nd|rd|th)?\s+([A-Za-z]{3,9})\.?,?\s+(\d{4})"), lambda m: (int(m[3]), _MONTHS.get(m[2].lower(), 0), int(m[1]))),
    (re.compile(r"([A-Za-z]{3,9})\.?\s+(\d{1,2})(?:st|nd|rd|th)?,?\s+(\d{4})"), lambda m: (int(m[3]), _MONTHS.get(m[1].lower(), 0), int(m[2]))),
]


def dates_in(text: str) -> List[date]:
    out = []
    for pat, f in _DATE_PATTERNS:
        for m in pat.finditer(text):
            y, mo, d = f(m)
            try:
                out.append(date(y, mo, d))
            except ValueError:
                pass
    return out


def _close(a: float, b: float) -> bool:
    return abs(a - b) <= max(1e-6, 1e-4 * max(abs(a), abs(b)))


def _in_quote(spec: FieldSpec, value, quote: str, scale: Optional[float] = None) -> Optional[str]:
    """None when the quote states the value; else the reason it does not."""
    if spec.kind == NUMBER:
        nums = numbers_in(quote, scale)
        if not nums:
            return "no figure in the quote"
        return None if any(_close(value, n) for n in nums) else "value not in the quote (quote states %s)" % ", ".join("%g" % n for n in nums[:6])
    if spec.kind == DATE:
        ds = dates_in(quote)
        if not ds:
            return "no date in the quote"
        return None if value in ds else "date not in the quote (quote states %s)" % ", ".join(d.isoformat() for d in ds[:4])
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


def _canon(spec: FieldSpec, v):
    if spec.kind == NUMBER:
        return round(float(v), 6)
    return v.isoformat() if isinstance(v, date) else v


def _supported(quote, doc_id, normed):
    """P4: a quote is evidence only if it is found in the named document (quotes.loose on both sides)."""
    return doc_id in normed and found(quote, normed[doc_id])


def _scale_near(docs, doc_id, quote) -> Optional[float]:
    """A table header's scale ("RMB'000") in the 1,500 characters before the quote, when the quote is found verbatim."""
    text = docs.get(doc_id, "")
    pos = text.find(quote[:60])
    return scale_hint(text, pos) if pos >= 0 else None


# ---------------------------------------------------------------- reading
_WORDY = re.compile(r"[A-Za-z]{2,}|[一-鿿]{2,}")


def _read_once(spec, passages, ask, normed, docs):
    """One model reading over a set of passages -> ("value", (v, doc, quote)) | ("null", None) | ("reject", why) | ("fail", why)."""
    reply = ask(_prompt_read(spec, passages), "read %s" % spec.key)
    if reply is None:
        return "fail", "model call failed"
    r = _json(reply)
    if not isinstance(r, dict):
        return "fail", "reply is not JSON"
    if r.get("value") is None:
        return "null", None
    if not _supported(r.get("quote"), r.get("doc"), normed):
        return "reject", "quote not found in the document"
    if not _WORDY.search(r["quote"]):                             # a bare figure from a table cannot show what quantity it is
        return "reject", "quote is a bare figure, not a sentence"
    v, why = _coerce(spec, r["value"])
    if why:
        return "reject", why
    why = _in_quote(spec, v, r["quote"], _scale_near(docs, r["doc"], r["quote"]) if spec.kind == NUMBER else None)
    if why:
        return "reject", why
    return "value", (v, r["doc"], r["quote"])


def _conflict(out: Extraction, spec: FieldSpec, groups, origin=None):
    """Record distinct values of one field read from different places; the field stays missing."""
    out.conflicts[spec.key] = [{"value": _plain(v), "doc": doc, "quote": quote,
                                "origin": origin or ("same document" if len({d for _, d, _ in groups}) == 1 else "different documents"),
                                "modality": "table" if _tabular(quote) else "text", "kind": spec.kind, "explicit": True}
                               for v, doc, quote in groups]
    out.rejected.append((spec.key, "conflict: " + " / ".join(str(v) for v, _, _ in groups)))


def _read(spec, passages, ask, normed, docs, samples, out: Extraction):
    """Every candidate passage on its own; one passage `samples` times. Returns (value, doc, quote) or None; records why."""
    key = spec.key
    reads = []                                                   # (passage index, status, payload)
    if len(passages) == 1:
        for _ in range(max(1, samples)):
            reads.append((0, *_read_once(spec, passages, ask, normed, docs)))
    else:
        for i, p in enumerate(passages):
            reads.append((i, *_read_once(spec, [p], ask, normed, docs)))
    values = [(i, pay) for i, st, pay in reads if st == "value"]
    fails = [why for _, st, why in reads if st == "fail"]
    rejects = [why for _, st, why in reads if st == "reject"]
    nulls = sum(1 for _, st, _ in reads if st == "null")
    feat = out.features.setdefault(key, {})
    feat.update({"passages": len(passages), "reads": len(reads), "values": len(values), "nulls": nulls, "rejects": len(rejects)})
    if fails:
        out.rejected.append((key, fails[0]))
        return None
    if not values:
        if rejects:
            out.rejected.append((key, rejects[0]))
        return None                                              # every reading: the passages do not settle it
    distinct = {}
    for i, (v, doc, quote) in values:
        distinct.setdefault(_canon(spec, v), []).append((i, v, doc, quote))
    feat["agree"] = round(max(len(g) for g in distinct.values()) / len(reads), 3)
    if len(passages) == 1:                                       # one passage read `samples` times: unanimous or missing
        if rejects:
            out.rejected.append((key, rejects[0]))
            return None
        if nulls:
            out.rejected.append((key, "samples disagree: %s / null" % values[0][1][0]))
            return None
        if len(distinct) > 1:
            out.rejected.append((key, "samples disagree: " + " / ".join(str(g[0][1]) for g in distinct.values())))
            return None
    elif len(distinct) > 1:                                      # different passages, different values: the documents conflict
        _conflict(out, spec, [(g[0][1], g[0][2], g[0][3]) for g in distinct.values()])
        return None
    elif rejects:                                                # a passage not about the field, misread: the verified reading stands
        out.notes.append("%s: a reading of another passage was refused (%s); the accepted reading stands on its verified quote" % (key, rejects[0]))
    i, v, doc, quote = values[0][0], *values[0][1]
    feat.update({"quote_len": len(quote), "figures_in_quote": len(numbers_in(quote)), "score": passages[i].get("score", 0.0),
                 "channels": passages[i].get("channels", [])})
    return v, doc, quote


def _tabular(quote: str) -> bool:
    lines = [l for l in quote.splitlines() if l.strip()]
    return len(numbers_in(quote)) >= 4 and (len(lines) >= 3 and sum(len(l) for l in lines) / len(lines) < 40)


def _plain(v):
    return v.isoformat() if isinstance(v, date) else v


# ---------------------------------------------------------------- locating
def _locate_llm(wanted, docs, normed, ask, out):
    reply = ask(_prompt_locate(wanted, docs), "locate")
    located = _json(reply)
    if not isinstance(located, dict):
        if reply is not None:
            out.notes.append("locate: reply is not JSON")
        return None
    return {s.key: [dict(p, score=0.0, channels=["llm"]) for p in (located.get(s.key) or [])
                    if isinstance(p, dict) and _supported(p.get("quote"), p.get("doc"), normed)] for s in wanted}


def _locate_retrieval(wanted, docs, k, dense):
    from .locate import PassageIndex, query_for
    index = PassageIndex(docs, dense=dense)
    return {s.key: index.search(query_for(s), k=k) for s in wanted}


def _by_pattern(spec: FieldSpec, docs, out: Extraction) -> List[dict]:
    """Candidate passages a pattern finds for the field: the sentences with the field's fixed wording near which the
    party is named (llm/patterns.py). They go in front of the retrieved candidates; the reader says whether each
    states the field for the party, and the program compares the readings as for any passages. A pattern never
    settles a value by itself (measured: wrong on other parties' sentences, see patterns.py). No party named, no
    pattern, no hit: nothing."""
    name = spec.key.rsplit(".", 1)[-1]
    if not spec.about:
        return []
    hits = pattern_candidates(name, docs, spec.about)
    if hits:
        out.features[spec.key] = {"pattern_hits": len(hits), "pattern_values": len({_canon(spec, _coerce(spec, h["value"])[0]) for h in hits if _coerce(spec, h["value"])[1] is None})}
    return [{"doc": h["doc"], "quote": h["quote"], "score": 1.0, "channels": ["pattern"]} for h in hits]


def _by_table(spec: FieldSpec, docs, out: Extraction) -> List[dict]:
    """Candidate passages from the financial statements (llm/tables.py): the table header and the row whose label is
    the field's, for fields read from a statement row. The reader picks the column; the program checks the figure."""
    name = spec.key.rsplit(".", 1)[-1]
    cands = table_candidates(name, docs)
    if cands:
        out.features.setdefault(spec.key, {})["table_rows"] = len(cands)
    return cands


def extract(docs: Dict[str, str], keys: List[str], model: Callable[[str], str], specs=None, samples=SAMPLES,
            locate="retrieval", k=K, dense=True, patterns=True, jobs=JOBS) -> Extraction:
    """docs: document id -> text. keys: the (flow or entity) fields wanted, as "elem.field". Returns facts with evidence;
    whatever the documents do not settle stays missing, and the rules treat it as U(MISSING)."""
    specs = specs or field_specs()
    wanted = [specs[kk] if kk in specs else FieldSpec(kk, TEXT, ()) for kk in keys]
    normed = {d: loose(t) for d, t in docs.items()}
    out = Extraction()

    def ask(prompt, what):
        try:
            return model(prompt)
        except Exception as e:                                   # the model's failure is a note, never a stop
            out.notes.append("%s: model call failed: %s: %s" % (what, type(e).__name__, e))
            return None

    def settle(s, value, doc, quote):
        elem, name = s.key.split(".", 1)
        out.facts[(elem, name)] = value
        out.evidence[(elem, name)] = (doc, quote)

    todo = list(wanted)
    cands = {s.key: ((_by_pattern(s, docs, out) + _by_table(s, docs, out)) if patterns else []) for s in todo}   # program-located first
    if todo and locate in ("retrieval", "both"):
        for kk, ps in _locate_retrieval(todo, docs, k, dense).items():
            seen = {loose(p["quote"]) for p in cands[kk]}
            cands[kk].extend(p for p in ps if loose(p["quote"]) not in seen)
    if todo and locate in ("llm", "both"):
        got = _locate_llm(todo, docs, normed, ask, out)
        if got is None and locate == "llm":
            out.missing.extend(s.key for s in todo)
            return out
        for kk, ps in (got or {}).items():
            seen = {loose(p["quote"]) for p in cands[kk]}
            cands[kk].extend(p for p in ps if loose(p["quote"]) not in seen)
    def work(s):
        if not cands[s.key]:
            out.features[s.key] = {"passages": 0}
            return None
        return _read(s, cands[s.key], ask, normed, docs, samples, out)

    with ThreadPoolExecutor(max(1, jobs)) as pool:                 # fields in parallel; one field's readings in sequence
        for s, got in zip(todo, pool.map(work, todo)):
            if got is None:
                out.missing.append(s.key)
            else:
                settle(s, *got)
    out.rejected.sort(key=lambda r: r[0])
    return out


def apply(extraction: Extraction, attrs_of: Dict[str, dict]):
    """Merge extracted facts into attrs dicts keyed by elem ("payer" | "payee" | "flow"); stated values are kept."""
    for (elem, name), v in extraction.facts.items():
        attrs_of.setdefault(elem, {}).setdefault(name, v)
    return attrs_of


def provenance(extraction: Extraction, path_of: Callable[[Tuple[str, str]], str]) -> Dict[str, dict]:
    """Case-file provenance rows (案例采集.md §4.2) for the extracted facts: disclosed, with the quote and its source."""
    return {path_of(kk): {"kind": "disclosed", "source": doc, "quote": quote} for kk, (doc, quote) in extraction.evidence.items()}


# ---------------------------------------------------------------- constraints the program checks (抽取改造.md §5 D)
def constraints(specs: Dict[str, FieldSpec], facts: Dict[Tuple[str, str], object]) -> List[Tuple[str, str]]:
    """Denial constraints over typed values: a percentage lies in [0, 100], a count or an amount is not negative, a
    date is in [1900, 2100]. Violations are reported, never repaired."""
    out = []
    for (elem, name), v in facts.items():
        s = specs.get("%s.%s" % (elem, name))
        if s is None:
            continue
        if s.kind == NUMBER and s.unit == "%" and not (0 <= v <= 100):
            out.append(("%s.%s" % (elem, name), "percentage outside [0, 100]: %g" % v))
        if s.kind == NUMBER and s.unit in ("months", "days", "years", "amount") and v < 0:
            out.append(("%s.%s" % (elem, name), "negative where a count or an amount is expected: %g" % v))
        if s.kind == DATE and not (1900 <= v.year <= 2100):
            out.append(("%s.%s" % (elem, name), "date outside [1900, 2100]: %s" % v))
    return out


def relations(g, case, event, facts_by_path: Dict[str, object], found: Dict[str, dict]) -> List[list]:
    """Cross-field relations the program checks over the case and what was read (抽取改造.md §5 D): holdings into one
    company sum to at most 100%; a holding's `since` is not after the event; a holding does not predate the held
    company's incorporation when the register states it; an acquisition date is not after the flow that disposes of
    it. Reported, never repaired."""
    out = []
    holds = getattr(case, "holds", {}) or {}
    by_held = {}
    for (holder, held), h in holds.items():
        by_held[held] = by_held.get(held, 0.0) + float(getattr(h, "ratio", 0.0) or 0.0)
    for held, s in by_held.items():
        if s > 100.05:
            out.append(["holds.*>%s.ratio" % held, "holdings sum to %.2f%% > 100%%" % s])
    event_on = getattr(event, "on", None)
    for (holder, held), h in holds.items():
        since = getattr(h, "since", None)
        if since and event_on and since > event_on:
            out.append(["holds.%s>%s.since" % (holder, held), "acquisition date %s is later than the event date %s" % (since, event_on)])
    for f in g.flows:
        acq = facts_by_path.get("flows.%s.acquired_on" % f.id) or f.attrs.get("acquired_on")
        if isinstance(acq, str):
            try:
                acq = date(*map(int, acq[:10].split("-")))
            except ValueError:
                acq = None
        if acq and f.on and acq > f.on:
            out.append(["flows.%s.acquired_on" % f.id, "acquisition date %s is later than the transaction date %s" % (acq, f.on)])
    return out


def _derive_eur(f, g, docs, keys, result, path_of, model=None, samples=SAMPLES, locate="retrieval", k=K, dense=True, jobs=JOBS):
    """Fields in EUR (payee.group_revenue_eur) are not read from a document that states another currency: the
    program reads the consolidated revenue row for the latest full financial year before the flow (llm/tables.py),
    or, when the statements are not in the documents, has the model read the revenue sentence (the program parses
    the figure and the currency written before it), and converts with the library's central-parity rate at that
    year's end — a substitute, noted as such, for the group's own conversion rate that decision D17 asks for when the
    case does not give one."""
    for key in keys:
        p = path_of(tuple(key.split(".", 1)))
        rate_given = f.attrs.get("p2_eur_rate") or g.entities[f.payee].attrs.get("p2_eur_rate")
        got = None
        for y in range(f.on.year - 1, f.on.year - 6, -1):
            r = table_revenue(docs, y)
            if r["rows"]:
                got = r
                break
        if got is None and model is not None:                    # prose: "net revenues were US$41.8 billion in 2025"
            for y in range(f.on.year - 1, f.on.year - 4, -1):
                base = key.rsplit("_eur", 1)[0]
                spec = FieldSpec(base, NUMBER, (), "", (), "the group's consolidated revenue for the financial year ended in %d, as stated, full amount in the currency written" % y, "amount", "C",
                                 "revenue was; net revenues were; total revenue of; recognised revenue of; turnover amounted to")   # example phrasings: retrieval needs them (M1)
                ex = extract(docs, [base], model, {base: spec}, samples=samples, locate=locate, k=k, dense=dense, patterns=False, jobs=jobs)
                v = ex.facts.get(tuple(base.split(".", 1)))
                if v is not None:
                    doc, quote = ex.evidence[tuple(base.split(".", 1))]
                    cur = currency_in(quote, v)
                    if cur is None:
                        result["notes"].append("%s: %s: revenue for %d read as %g, but no currency precedes the figure in the quote; not converted" % (f.id, key, y, v))
                        break
                    got = {"year": y, "rows": 1, "distinct": [{"value": v, "doc": doc, "row": {"quote": quote, "header_quote": "(prose sentence, named by the model; figure and currency parsed by the program)"}, "scale": 1.0, "currency": cur, "n": 1}],
                           "value": v, "currency": cur}
                    break
                for kk, why in ex.rejected:
                    result["notes"].append("%s: %s (%d): %s" % (f.id, key, y, why))
        if got is None:
            result["missing"].append("%s:%s" % (f.id, key))
            result["notes"].append("%s: %s: the documents have no readable consolidated revenue row or revenue sentence" % (f.id, key))
            continue
        result["features"][p] = {"table_rows": got["rows"], "table_values": len(got["distinct"]), "year": got["year"]}
        if got["value"] is None:
            result["conflicts"][p] = [{"value": d["value"], "doc": d["doc"], "quote": d["row"]["quote"], "origin": "same document", "modality": "table",
                                       "kind": NUMBER, "explicit": True} for d in got["distinct"]]
            result["rejected"].append(["%s:%s" % (f.id, key), "conflict: " + " / ".join("%g" % d["value"] for d in got["distinct"])])
            result["missing"].append("%s:%s" % (f.id, key))
            continue
        d = got["distinct"][0]
        if rate_given:
            eur, how = d["value"] / float(rate_given), {"date": "case", "pairs": {"EUR/%s" % (got["currency"] or "CNY"): float(rate_given)}}
            why = "conversion rate %s given by the case (decision D17)" % rate_given
        else:
            on = year_end_rate_date(got["year"])
            eur, how = (None, "no year-end rate for %d" % got["year"]) if on is None else to_eur(d["value"], got["currency"] or "CNY", on)
            why = "conversion rate substituted by the library's central parity of %s (decision D17 asks for the group's own conversion rate, which the case does not give)" % (on.isoformat() if on else "?")
        if eur is None:
            result["missing"].append("%s:%s" % (f.id, key))
            result["notes"].append("%s: %s: revenue %g %s read, but %s" % (f.id, key, d["value"], got["currency"] or "CNY", how))
            continue
        result["facts"][p] = round(eur, 2)
        result["provenance"][p] = {"kind": "derived", "source": d["doc"], "quote": d["row"]["quote"][:300],
                                   "formula": "consolidated revenue %d: %s %s (header %s) ÷ %s = EUR %.2f; %s" % (
                                       got["year"], "{:,.0f}".format(d["value"]), got["currency"] or "CNY", " ".join(d["row"]["header_quote"].split())[:80],
                                       " × ".join("%s %s" % (k, v) for k, v in how["pairs"].items()), eur, why)}


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
    def path(kk):
        elem, name = kk
        if elem == "flow":
            return "flows.%s.%s" % (fid, name)
        return "roles.%s.attrs.%s" % (payer if elem == "payer" else payee, name)
    return path


def extract_case(path, docs, model, samples=SAMPLES, only_flow=None, names=None, channels=ASK_CHANNELS, locate="retrieval",
                 k=K, dense=True, registry=None, patterns=True, jobs=JOBS, registry_mode="file"):
    """The fields the rules read on the case's present structure and the case does not state, flow by flow; only the
    channels the model is for are asked of it, the rest are listed for a person. Fields in EUR are derived by the
    program from the statements (tables) and the fx table; the registers (registry_mode: off | file | live) are
    looked up for every named role and cross-checked; cross-field relations are checked last."""
    from ..fields import DERIVED, missing_fields
    from ..run import load_case
    template, case, event, _, _, _ = load_case(path)
    g = template.build(event, case.present, case)
    names, registry = names or {}, registry or {}
    specs = field_specs()
    wanted, derived, external, untyped = {}, [], [], []
    for fid, key in sorted(missing_fields(g)):
        if only_flow is not None and fid != only_flow:
            continue
        sp = specs.get(key)
        name = key.split(".", 1)[1]
        if name in DERIVED or (sp is not None and sp.channel == "A"):
            derived.append("%s:%s" % (fid, key))                 # the program derives it: what is missing is an input
        elif sp is None or (sp.kind == TEXT and not sp.allowed):
            untyped.append("%s:%s" % (fid, key))                 # nothing to validate a reply against: a person collects it
        elif sp.channel and sp.channel not in channels:
            external.append(["%s:%s" % (fid, key), sp.channel, sp.hint])   # registry (B) or authority document (D)
        else:
            wanted.setdefault(fid, []).append(key)
    result = {"case": str(path), "model": getattr(model, "model", type(model).__name__), "temperature": getattr(model, "temperature", None),
              "prompt_version": PROMPT_VERSION, "samples": samples, "locate": locate, "k": k, "patterns": patterns, "docs": sorted(docs),
              "facts": {}, "provenance": {}, "conflicts": {}, "violations": [], "missing": [], "rejected": [], "notes": [],
              "features": {}, "derived_inputs": derived, "external": external, "untyped": untyped}
    for f in g.flows:
        if f.id not in wanted:
            continue
        who = lambda e: "%s (%s%s)" % (e, g.entities[e].loc, ", " + names[e] if e in names else "")
        brief = ("CASE: flow %s is %s of %s %s on %s, paid by %s to %s%s. Fields named payer.* are about %s, payee.* about %s, "
                 "flow.* about this payment. Amounts are plain numbers in full units of %s, not thousands or millions." % (
                     f.id, f.income, f.amount, f.currency, f.on, who(f.payer), who(f.payee),
                     " for the equity of %s" % who(f.target) if f.target else "", f.payer, f.payee, f.currency))
        eur_keys = [kk for kk in wanted[f.id] if kk.endswith("_eur")]
        for kk in eur_keys:
            wanted[f.id].remove(kk)
        flow_specs = dict(specs)
        for key in wanted[f.id]:                                  # a pattern must speak of the right party
            elem = key.split(".", 1)[0]
            party = f.payer if elem == "payer" else f.payee if elem == "payee" else None
            if party and party in names:
                flow_specs[key] = FieldSpec(**dict(specs[key].__dict__, about=names[party]))
        ex = extract(docs, wanted[f.id], lambda p: model(brief + "\n\n" + p), flow_specs, samples=samples, locate=locate, k=k,
                     dense=dense, patterns=patterns, jobs=jobs)
        path_of = _path_of(f.id, f.payer, f.payee)
        _derive_eur(f, g, docs, eur_keys, result, path_of, (lambda p: model(brief + "\n\n" + p)) if eur_keys else None, samples, locate, k, dense, jobs)
        result["facts"].update({path_of(kk): _plain(v) for kk, v in ex.facts.items()})
        result["provenance"].update(provenance(ex, path_of))
        result["conflicts"].update({path_of(tuple(kk.split(".", 1))): v for kk, v in ex.conflicts.items()})
        result["violations"].extend(["%s:%s" % (f.id, kk), why] for kk, why in constraints(specs, ex.facts))
        result["missing"].extend("%s:%s" % (f.id, kk) for kk in ex.missing)
        result["rejected"].extend(["%s:%s" % (f.id, kk), why] for kk, why in ex.rejected)
        result["notes"].extend("%s: %s" % (f.id, n) for n in ex.notes)
        result["features"].update({path_of(tuple(kk.split(".", 1))): v for kk, v in ex.features.items()})
        for kk, v in ex.facts.items():                          # registry values in hand: a matching dependency (M6)
            p = path_of(kk)
            if p in registry and _canon(specs["%s.%s" % kk], v) != _canon(specs["%s.%s" % kk], registry[p]):
                result["conflicts"].setdefault(p, []).append({"value": registry[p], "doc": "registry", "quote": "", "origin": "registry",
                                                             "modality": "registry", "kind": specs["%s.%s" % kk].kind, "explicit": True})
                result["violations"].append([p, "differs from the registry: %s vs %s" % (_plain(v), registry[p])])
    found = {}
    if registry_mode != "off" and names:
        from ..registry import cross_check, lookup as registry_lookup, public
        for role, nm in names.items():
            if role not in g.entities:
                continue
            try:
                recs = registry_lookup(g.entities[role].loc, nm, live=(registry_mode == "live"))
            except Exception as e:                               # a register that cannot be reached is a note, never a stop
                result["notes"].append("registry: %s: %s: %s" % (role, type(e).__name__, e))
                continue
            if recs:
                found[role] = recs[0]
                if len(recs) > 1:
                    result["notes"].append("registry: %s matched %d records, taking %s; a person must confirm" % (role, len(recs), recs[0].get("id")))
        rf, rp, rc, rv, rn = cross_check(g, case, names, found)
        for p, v in rf.items():
            if p not in result["facts"]:
                result["facts"][p], result["provenance"][p] = v, rp[p]
            elif result["facts"][p] != v:
                result["conflicts"].setdefault(p, []).append({"value": v, "doc": "registry", "quote": rp[p]["quote"], "origin": "registry",
                                                             "modality": "registry", "kind": ENUM, "explicit": True})
                result["violations"].append([p, "documents read %s, the register says %s" % (result["facts"][p], v)])
        for p, cs in rc.items():
            result["conflicts"].setdefault(p, []).extend(cs)
        result["violations"].extend(rv)
        result["notes"].extend(rn)
        result["registry"] = {r: public(rec) for r, rec in found.items()}
        result["registry_unmatched"] = [r for r in names if r in g.entities and r not in found]
    result["violations"].extend(relations(g, case, event, result["facts"], found))
    if hasattr(model, "usage"):
        result["usage"] = dict(model.usage)
    return result


def fill(case_json: dict, result: dict) -> dict:
    """The case with the extracted values and their provenance merged in; stated values and their provenance are kept.
    A value a constraint or the registry contradicts is not merged."""
    d = json.loads(json.dumps(case_json))
    bad = {p for p, _ in result.get("violations", [])}
    for p, v in result["facts"].items():
        if p in bad:
            continue
        parts = p.split(".")
        if parts[0] == "roles":
            d["roles"].setdefault(parts[1], {}).setdefault("attrs", {}).setdefault(parts[3], v)
        else:
            d.setdefault("flows", {}).setdefault(parts[1], {}).setdefault(parts[2], v)
    prov = d.setdefault("provenance", {})
    for p, e in result["provenance"].items():
        if p not in bad:
            prov.setdefault(p, e)
    d.setdefault("notes", []).append("%d fields read by %s from %s (%s, prompt %s); quotes verified verbatim, numbers and dates parsed by the program from the quote; %d conflicts and %d constraint violations left unfilled; a person must review before use, then run tax_graph.verify.casecheck." % (
        len(result["facts"]), result["model"], ", ".join(result["docs"]), date.today().isoformat(), result.get("prompt_version", "?"),
        len(result.get("conflicts", {})), len(result.get("violations", []))))
    return d


def main(argv):
    import io
    import sys
    out = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    path = Path(argv[1])
    docs = load_docs(Path(argv[argv.index("--docs") + 1]))
    opt = lambda flag, default: argv[argv.index(flag) + 1] if flag in argv else default
    from .deepseek import CACHE, DeepSeek
    model = DeepSeek(opt("--model", None) or "deepseek-flash", temperature=float(opt("--temperature", "0.7")), cache=None if "--no-cache" in argv else CACHE,
                     timeout=int(opt("--timeout", 900)))
    case_json = json.loads(path.read_text(encoding="utf-8"))
    result = extract_case(path, docs, model, int(opt("--samples", SAMPLES)), opt("--flow", None), case_json.get("names"),
                          tuple(opt("--channels", ",".join(ASK_CHANNELS)).split(",")), opt("--locate", "retrieval"), int(opt("--k", K)),
                          dense="--no-dense" not in argv, registry=case_json.get("registry"), patterns="--no-patterns" not in argv,
                          jobs=int(opt("--jobs", JOBS)), registry_mode=opt("--registry", "file"))
    dst = path.with_suffix(".extracted.json")
    dst.write_text(json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8")
    out.write("%d values read; %d missing (%d refused by the program, %d of them conflicts); %d constraint violations; %d model events\n" % (
        len(result["facts"]), len(result["missing"]), len(result["rejected"]), len(result["conflicts"]), len(result["violations"]), len(result["notes"])))
    for p, v in sorted(result["facts"].items()):
        e = result["provenance"][p]
        out.write("  %-48s %-14s %s: %s\n" % (p, v, e["source"], e["quote"][:90].replace("\n", " ")))
    for p, cs in result["conflicts"].items():
        out.write("  conflict  %-44s %s\n" % (p, " / ".join("%s (%s: %s)" % (c["value"], c["doc"], (c["quote"] or "")[:60].replace("\n", " ")) for c in cs)))
    for kk, why in result["rejected"]:
        if not why.startswith("conflict"):
            out.write("  rejected  %-44s %s\n" % (kk, why))
    for kk, why in result["violations"]:
        out.write("  violation %-44s %s\n" % (kk, why))
    for n in result["notes"]:
        out.write("  event %s\n" % n)
    if result["derived_inputs"]:
        out.write("  derived by the program, inputs missing (%d): %s\n" % (len(result["derived_inputs"]), ", ".join(result["derived_inputs"])))
    if result["external"]:
        out.write("  from a register / official document (%d): %s\n" % (len(result["external"]), ", ".join("%s[%s]" % (kk, ch) for kk, ch, _ in result["external"])))
    if result["untyped"]:
        out.write("  not asked of the model (no type to check against, left to a person): %s\n" % ", ".join(result["untyped"]))
    for r, rec in result.get("registry", {}).items():
        out.write("  register %-6s %s (%s %s) incorporated %s status %s\n" % (r, rec.get("name"), rec.get("jur"), rec.get("id"), rec.get("incorporated_on"), rec.get("status")))
    if result.get("registry_unmatched"):
        out.write("  register unmatched: %s\n" % ", ".join(result["registry_unmatched"]))
    if "usage" in result:
        out.write("  usage %s\n" % result["usage"])
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
