"""The strategy assistant (优化方案.md §6): a conversation scoped to one strategy of one case, with the library, the rule
evidence, the forms and the web as tools, through the provider's own function calling. It helps the client carry the
strategy out: explains steps, finds and quotes provisions, fills forms from the case, checks dates, drafts. It never
changes an amount, never answers a ruling for the client and never switches strategies: those happen through the
answers and a rerun. The thread of each strategy is kept in <run dir>/agent/strategy-<id>.json and reloaded when the
strategy is opened; every exchange with its tool calls is also appended to strategy-<id>.jsonl.
"""
import csv
import json
import re
import sys
import time
import urllib.request
from pathlib import Path

from ..llm.deepseek import DeepSeek

ROOT = Path(__file__).resolve().parents[2]
MAX_TOOL_ROUNDS = 6
FETCH_CHARS = 6000
HISTORY_TURNS = 20

SYSTEM = """You are the client's adviser for carrying out one tax strategy that a rule-based program produced. Talk the way a good adviser talks: direct, concrete, in the client's language, in short paragraphs or lists; use Markdown.

Your context is this strategy only. You can:
- explain what a step means and how to do it, list the documents to prepare, check dates and deadlines, draft letters and checklists;
- look things up: the official law library (Mainland China, Hong Kong, Singapore), the provisions behind a rule the plan cites, the official forms with the case's values filled in, and web pages;
- tell the client what to do when a ruling fails (continue with the fallback strategy the plan names: answer that ruling No and reassess).

Two limits, because the program's numbers and the client's own declarations must stay theirs:
- You never change a tax amount, never say that a relief, ruling or certificate HAS BEEN granted, never answer a ruling on the client's behalf. Helping the client apply for one is your job on every path, including the baseline ("taken against the taxpayer" only means the guaranteed tax does not count on it until it is granted).
- A statement about the law carries weight only with a provision you retrieved (a library clause id, or a web page you fetched, with its URL). Without one, say that you have not checked it; do not give a rate, threshold, date, form number or form field from memory. You decide when to look things up.

When a form is open in your context (the program opens the matching form for a form question), answer from it field by field: the value and where it came from, "fill in from your records", or "not collected: please provide". The client checks and submits.

End with the sources you used (clause ids or URLs) on one line starting with "Sources:"; if none, say so."""

TOOLS_SCHEMA = [
    {"type": "function", "function": {"name": "search_library", "description": "Search the official law library of Mainland China, Hong Kong and Singapore (statutes, regulations, treaties, guidance) and get clause ids with excerpts. Query in the law's language (Chinese for the Mainland).",
                                      "parameters": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}}},
    {"type": "function", "function": {"name": "rule", "description": "The provisions behind a rule the plan cites (a rule id from a step's references), with their text and the quoted parameters.",
                                      "parameters": {"type": "object", "properties": {"id": {"type": "string"}}, "required": ["id"]}}},
    {"type": "function", "function": {"name": "fetch_url", "description": "Fetch a web page and get its text (any site; official sources are more reliable).",
                                      "parameters": {"type": "object", "properties": {"url": {"type": "string"}}, "required": ["url"]}}},
    {"type": "function", "function": {"name": "forms", "description": "The official forms the library holds (applications for a certificate of resident status, treaty-benefit reports, withholding reports, returns), optionally filtered by a keyword.",
                                      "parameters": {"type": "object", "properties": {"keyword": {"type": "string"}}}}},
    {"type": "function", "function": {"name": "form", "description": "One form's fields with the values the case can already fill in and what the client must add.",
                                      "parameters": {"type": "object", "properties": {"id": {"type": "string"}}, "required": ["id"]}}},
]


# ---------------------------------------------------------------- context
def _context(case: dict, plan: dict, strategy: dict) -> str:
    names = case.get("names") or {}
    nm = lambda r: names.get(r, r)
    L = ["Case: %s. Currency %s. Assessment date %s." % (case.get("case_id"), case.get("currency"), (case.get("event") or {}).get("as_at"))]
    L.append("Companies: " + "; ".join("%s (%s, %s)" % (nm(r), r, v.get("loc")) for r, v in (case.get("roles") or {}).items()))
    st = strategy or {}
    L.append("Strategy #%s: guaranteed tax %s, best case %s, structure %s." % (st.get("id", 1), st.get("guaranteed", plan.get("guaranteed")), st.get("best", plan.get("best")),
                                                                              ", ".join("%s=%s" % kv for kv in (st.get("cand") or plan.get("cand") or {}).items()) or "the only structure"))
    if st.get("assumes_favourable"):
        L.append("On this path these rulings are taken as favourable (branch labels, not facts): " + "; ".join("%s (%s)" % (st.get("labels", {}).get(k, k), k) for k in st["assumes_favourable"]))
    else:
        L.append("This path takes every open ruling against the taxpayer (baseline).")
    if st.get("fallback"):
        L.append("If one of them fails: continue with strategy #%s." % st["fallback"])
    ex = (st.get("plan") or plan).get("execution") or {}
    L.append("Aim: " + (ex.get("recommended_course") or ""))
    num = {s["id"]: i for i, s in enumerate(ex.get("steps", []), 1)}
    for s in ex.get("steps", []):
        L.append("Step %d [%s, %s]: %s. Why: %s Action: %s Documents: %s. Complete when: %s.%s%s%s" % (
            num[s["id"]], s.get("phase", ""), s.get("status", ""), s.get("title", ""), s.get("why", ""), s.get("action", ""),
            "; ".join(s.get("documents") or []), s.get("completion", ""),
            (" Date: %s." % s["due"]) if s.get("due") else "", (" After steps %s." % ", ".join(str(num.get(d, d)) for d in s["depends_on"])) if s.get("depends_on") else "",
            (" Rule references: %s." % ", ".join(s["basis"])) if s.get("basis") else ""))
    for d in ex.get("decision_paths", []):
        L.append("Conditional decision: %s — if supported: %s Otherwise: %s" % (d.get("condition"), d.get("if_supported"), d.get("otherwise")))
    return "\n".join(L)


# ---------------------------------------------------------------- tools
def _library():
    sys.path.insert(0, str(ROOT / "official" / "tools"))
    from search import Library
    return Library()


def tool_search(query: str) -> dict:
    if not (query or "").strip():
        return {"error": "give the query"}
    try:
        hits = _library().search(query, k=5)
    except Exception as e:                                   # noqa: BLE001
        return {"error": "library search unavailable: %s" % e}
    if not isinstance(hits, list):
        return {"error": str(getattr(hits, "reason", hits))}
    return {"hits": [{"cite_id": h.cite_id, "title": h.title, "excerpt": h.snippet, "valid_from": h.valid_from, "valid_to": h.valid_to} for h in hits]}


def tool_rule(rule_id: str) -> dict:
    from .server import evidence
    if not (rule_id or "").strip():
        return {"error": "give the rule id"}
    try:
        ev = evidence(rule_id)
    except Exception as e:                                   # noqa: BLE001
        return {"error": "no evidence for %s: %s" % (rule_id, e)}
    return {"effect": ev.get("effect"), "sources": [{"cite_id": s.get("cite_id"), "label": s.get("label"), "title": s.get("title"), "url": s.get("url"),
                                                     "quotes": s.get("excerpts") or [], "text": (s.get("text") or "")[:3000]} for s in ev.get("sources", [])]}


def tool_fetch(url: str) -> dict:
    if not re.match(r"^https?://", url or ""):
        return {"error": "not a web address"}
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (tax-graph strategy assistant)"})
        with urllib.request.urlopen(req, timeout=25) as r:
            raw = r.read(2_000_000)
            ctype = r.headers.get("Content-Type", "")
    except Exception as e:                                   # noqa: BLE001
        return {"error": "fetch failed: %s" % e}
    text = raw.decode("utf-8", "replace")
    if "html" in ctype or text.lstrip()[:1] == "<":
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(text, "html.parser")
            for t in soup(["script", "style", "nav", "footer"]):
                t.decompose()
            text = soup.get_text("\n")
        except Exception:                                    # noqa: BLE001
            text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\n\s*\n+", "\n", text).strip()
    return {"url": url, "text": text[:FETCH_CHARS], "truncated": len(text) > FETCH_CHARS}


def _form_rows():
    csv.field_size_limit(10**9)
    with open(str(ROOT / "official" / "form_fields.csv"), encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    with open(str(ROOT / "official" / "manifest.csv"), encoding="utf-8-sig", newline="") as f:
        docs = {d["id"]: d for d in csv.DictReader(f)}
    return rows, docs


def tool_forms(keyword: str = "") -> dict:
    rows, docs = _form_rows()
    mapped = {}
    for r in rows:
        mapped[r["form_id"]] = mapped.get(r["form_id"], 0) + 1
    out = [{"form_id": fid, "jurisdiction": d.get("jur"), "title": d.get("title"), "url": d.get("url"), "mapped_fields": mapped.get(fid, 0)}
           for fid, d in docs.items() if fid in mapped or d.get("type") == "form" or ".forms." in fid]
    kw = (keyword or "").lower().strip()
    if kw:
        out = [x for x in out if kw in (x["title"] or "").lower() or kw in x["form_id"].lower() or kw in (x["jurisdiction"] or "")]
    return {"forms": sorted(out, key=lambda x: (-x["mapped_fields"], x["form_id"]))}


def _case_values(case: dict, plan: dict):
    names = case.get("names") or {}
    nm = lambda r: names.get(r, r)
    companies = {r: dict(v.get("attrs") or {}, incorporated_in=v.get("loc"), name=nm(r)) for r, v in (case.get("roles") or {}).items()}
    for k, v, src in (plan.get("data_used") or []):
        if isinstance(k, str) and "." in k and not k.startswith(("flow:", "hold:", "group.")):
            role, field_ = k.split(".", 1)
            if role in companies and v not in (None, "unknown"):
                companies[role][field_] = v
    payments = {}
    for fid, t in (case.get("transactions") or {}).items():
        p = dict(case.get("flows", {}).get(fid) or {})
        p.update(payer=nm(t["payer"]), payee=nm(t["payee"]), income=t["income"], amount=t["amount"], on=t["on"], currency=case.get("currency"))
        for j, v in (case.get("settled", {}).get(fid) or {}).items():
            p["withheld_%s" % j] = v
        payments[fid] = p
    for k, v, src in (plan.get("data_used") or []):
        if isinstance(k, str) and k.startswith("flow:") and v not in (None, "unknown"):
            fid, field_ = k[5:].split(".", 1)
            if fid in payments:
                payments[fid][field_.split(":")[0]] = v
    holdings = [{"holder": nm(h["holder"]), "held": nm(h["held"]), "ratio": h.get("ratio"), "since": h.get("since"), "cost": h.get("cost")} for h in (case.get("holds") or [])]
    return companies, payments, holdings


def tool_form(form_id: str, case: dict, plan: dict, applicant: str = "") -> dict:
    rows, docs = _form_rows()
    mine = [r for r in rows if r["form_id"] == form_id]
    if not mine:
        return {"error": "no field mapping for %s" % form_id, "known_forms": [f["form_id"] for f in tool_forms()["forms"] if f["mapped_fields"]]}
    companies, payments, holdings = _case_values(case, plan)
    fields = []
    for r in mine:
        m = r["maps_to"]
        entry = {"seq": r["seq"], "section": r["section"], "label": r["label"], "maps_to": m, "kind": r["kind"], "note": r["note"]}
        if m in ("NONE", "id") or r["kind"] == "admin":
            entry["value"] = "fill in from the company's records (identifier, address, contact)"
        elif m.startswith("NEW:"):
            entry["value"] = "not collected by the program: ask the client"
        elif m in ("payer", "payee", "income", "amount", "on", "currency", "withheld", "withheld_on", "foreign_tax_paid", "foreign_taxed",
                   "payee_taxed", "received_locally", "treaty_form_filed", "withholding_agent", "foreign_headline_rate", "tax_filed", "filed_on"):
            entry["value"] = {fid: p.get(m if m != "withheld" else next((k for k in p if k.startswith("withheld_")), "withheld")) for fid, p in payments.items()}
        elif m in ("holder", "held", "since", "HOLD.ratio", "indirect_ratio") or m.endswith(".ratio") or m.endswith(".holding_months"):
            entry["value"] = holdings
        elif m == "flows":
            entry["value"] = {fid: "%s pays %s %s %s on %s" % (p["payer"], p["payee"], p["income"].lower(), p["amount"], p["on"]) for fid, p in payments.items()}
        else:
            vals = {c["name"]: c.get(m) for c in companies.values() if c.get(m) not in (None, "")}
            if applicant and applicant in vals:
                vals = {applicant: vals[applicant]}
            entry["value"] = vals or ("not stated for %s: ask the client" % applicant if applicant else "not stated in the case: ask the client")
        fields.append(entry)
    d = docs.get(form_id, {})
    return {"form_id": form_id, "title": d.get("title"), "url": d.get("url"), "applicant": applicant or None, "fields": fields,
            "companies": {c["name"]: {"jurisdiction": c.get("incorporated_in")} for c in companies.values()},
            "note": "values come from the case and the client's answers; the client checks every field against the records and submits; the program does not file"}


FORM_WORDS = re.compile(r"\b(form|forms|apply|application|applying|file|filing|return|certificate|declaration|claim)\b|表|申请|申报|证明|填", re.I)
FORM_HINTS = [
    (r"hong ?kong|香港|hk\b", r"resident|residen|居民|certificate|证明", "hk.form.ir1313a"),
    (r"(chinese|china|mainland|prc) (tax )?residen|中国税收居民|内地税收居民|居民身份证明.*(内地|中国)|(内地|中国).*居民身份证明", r".", "cn.sta.2025-04.a02"),
    (r"singapore|新加坡|sg\b", r"resident|residen|居民|certificate|证明|cor\b", "sg.iras.forms.cor-specimen"),
    (r"treaty|协定|arrangement|安排", r"benefit|relief|待遇|report|报告|claim|rate|税率", "cn.sta.2019-35.a01"),
    (r"withhold|扣缴|预提", r"mainland|china|内地|中国|report|报告表", "cn.sta.2019-16.a08"),
    (r"withhold|扣缴|s45|ir37", r"singapore|新加坡", "sg.iras.forms.wht"),
    (r"13\(12\)|s13|foreign.sourced|境外所得", r"singapore|新加坡|declar|申报|exempt|免税", "sg.iras.forms.s13-12"),
    (r"advance ruling|预先裁定|ir1297", r".", "hk.fsie.forms.ir1297"),
    (r"mutual agreement|map\b|相互协商|ir1454", r".", "hk.form.ir1454"),
]


def _applicant(message: str, case: dict) -> str:
    low = message.lower()
    found = {}
    for n in (case.get("names") or {}).values():
        pos = [low.find(w.lower()) for w in re.split(r"[\s/]+", n or "")[:2] if len(w) >= 4 and w.lower() in low]
        if pos:
            found[n] = min(pos)
    return sorted(found, key=found.get)[0] if found else ""


def _preload_forms(message: str, case: dict, plan: dict):
    """A form question opens the matching form before the model speaks (the program's filling, not the model's)."""
    low = message.lower()
    picks = list(dict.fromkeys(fid for a, b, fid in FORM_HINTS if re.search(a, low) and re.search(b, low)))[:2]
    who = _applicant(message, case)
    return [{"tool": "form", "args": {"id": fid}, "result": tool_form(fid, case, plan, who), "preloaded": True} for fid in picks]


def _render_form(f: dict) -> str:
    def val(v):
        if isinstance(v, dict):
            items = [(k, x) for k, x in v.items() if x not in (None, "")]
            return "; ".join("%s: %s" % (k, x) for k, x in items) if items else "not stated in the case: please provide"
        if isinstance(v, list):
            return "; ".join(", ".join("%s %s" % (k, x) for k, x in h.items() if x not in (None, "")) for h in v) or "not stated in the case: please provide"
        return str(v)
    L = ["**Form %s — %s**%s" % (f["form_id"], f.get("title") or "", (" ([link](%s))" % f["url"]) if f.get("url") else ""),
         "Filled from the case%s; check every line against your records before submitting." % ((" for " + f["applicant"]) if f.get("applicant") else "")]
    section = None
    for x in f["fields"]:
        if x.get("section") and x["section"] != section:
            section = x["section"]
            L.append("")
            L.append("**%s**" % section)
        L.append("- %s %s: %s" % (x["seq"], x["label"], val(x["value"])))
    return "\n".join(L)


def run_tool(name, args, case, plan):
    if name == "search_library":
        return tool_search(args.get("query", ""))
    if name == "rule":
        return tool_rule(args.get("id", ""))
    if name == "fetch_url":
        return tool_fetch(args.get("url", ""))
    if name == "forms":
        return tool_forms(args.get("keyword", ""))
    if name == "form":
        return tool_form(args.get("id", ""), case, plan)
    return {"error": "unknown tool %s" % name}


# ---------------------------------------------------------------- the thread
def thread_path(run_dir: Path, strategy_id) -> Path:
    return Path(run_dir) / "agent" / ("strategy-%s.json" % strategy_id)


def load_thread(run_dir: Path, strategy_id) -> list:
    p = thread_path(run_dir, strategy_id)
    if p.exists():
        try:
            return json.loads(p.read_text(encoding="utf-8")).get("messages", [])
        except ValueError:
            return []
    return []


def _save_thread(run_dir: Path, strategy_id, messages: list):
    p = thread_path(run_dir, strategy_id)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps({"messages": messages}, ensure_ascii=False, indent=1), encoding="utf-8")


def chat(case: dict, plan: dict, strategy: dict, message: str, model: str, run_dir: Path, on_event=None) -> dict:
    """One client turn. on_event(kind, data) streams progress: ("delta", text), ("tool", {name, args, done}), ("done", result)."""
    emit = on_event or (lambda k, d: None)
    sid = (strategy or {}).get("id", 1)
    thread = load_thread(run_dir, sid)
    llm = DeepSeek(model or "deepseek-flash", temperature=0.3, cache=None)
    sp = (strategy or {}).get("plan") or plan
    messages = [{"role": "system", "content": SYSTEM}, {"role": "system", "content": "Strategy context:\n" + _context(case, plan, strategy)}]
    for h in thread[-HISTORY_TURNS:]:
        messages.append({"role": "user" if h.get("role") == "user" else "assistant", "content": str(h.get("text", ""))})
    trace = []
    if FORM_WORDS.search(message):
        for t in _preload_forms(message, case, sp):
            trace.append(t)
            emit("tool", {"name": "form", "args": t["args"], "done": True})
            messages.append({"role": "system", "content": "Form opened by the program for this question (answer from it field by field):\n" + json.dumps(t["result"], ensure_ascii=False)[:14000]})
    messages.append({"role": "user", "content": message})
    content = ""
    for _ in range(MAX_TOOL_ROUNDS + 1):
        res = llm.chat(messages, tools=TOOLS_SCHEMA if len(trace) < MAX_TOOL_ROUNDS + 2 else None, on_delta=lambda t: emit("delta", t))
        if res["tool_calls"] and len(trace) < MAX_TOOL_ROUNDS + 2:
            messages.append({"role": "assistant", "content": res["content"] or None,
                             "tool_calls": [{"id": c["id"] or "call_%d" % i, "type": "function", "function": {"name": c["name"], "arguments": c["arguments"]}} for i, c in enumerate(res["tool_calls"])]})
            for i, c in enumerate(res["tool_calls"]):
                try:
                    args = json.loads(c["arguments"] or "{}")
                except ValueError:
                    args = {}
                emit("tool", {"name": c["name"], "args": args, "done": False})
                result = run_tool(c["name"], args, case, sp)
                trace.append({"tool": c["name"], "args": args, "result": result})
                emit("tool", {"name": c["name"], "args": args, "done": True, "ok": "error" not in result})
                messages.append({"role": "tool", "tool_call_id": c["id"] or "call_%d" % i, "content": json.dumps(result, ensure_ascii=False)[:12000]})
            continue
        content = (res["content"] or "").strip()
        break
    if not content:
        found = []
        for t in trace:
            r = t["result"]
            if "hits" in r:
                found += ["%s — %s: %s" % (h["cite_id"], h.get("title") or "", (h.get("excerpt") or "")[:300]) for h in r["hits"][:3]]
            elif "sources" in r:
                found += ["%s (%s): %s" % (s_.get("cite_id"), s_.get("title") or "", "; ".join(s_.get("quotes") or [])[:300] or (s_.get("text") or "")[:300]) for s_ in r["sources"][:3]]
            elif "text" in r:
                found.append("%s: %s" % (r.get("url"), r["text"][:300]))
        content = ("I did not get to an answer. What I retrieved:\n- " + "\n- ".join(found)) if found else "I could not answer that; please ask again more specifically."
    forms_opened = [t["result"] for t in trace if t.get("preloaded") and "fields" in t["result"]]   # the program's filling is shown as such; a form the model opened itself is in its own words
    if forms_opened:
        content = "\n\n".join(_render_form(f) for f in forms_opened) + "\n\n" + content
    m = re.search(r"(?im)^\s*\**sources?\**\s*[:：]\s*(.+)$", content)
    sources = [s.strip(" .;`*") for s in re.split(r"[;,]\s*|\s+\|\s+", m.group(1))] if m else []
    sources = list(dict.fromkeys([f["form_id"] for f in forms_opened] + [s for s in sources if s and s.lower() not in ("none", "none.")]))
    tools = [{"tool": t["tool"], "args": t["args"], "ok": "error" not in t["result"]} for t in trace]
    at = time.strftime("%Y-%m-%dT%H:%M:%S")
    thread += [{"role": "user", "text": message, "at": at}, {"role": "assistant", "text": content, "sources": sources, "tools": tools, "at": at}]
    _save_thread(run_dir, sid, thread)
    log = Path(run_dir) / "agent"
    with open(str(log / ("strategy-%s.jsonl" % sid)), "a", encoding="utf-8") as f:
        f.write(json.dumps({"at": at, "message": message, "trace": trace, "answer": content, "model": llm.model, "usage": llm.usage}, ensure_ascii=False) + "\n")
    out = {"answer": content, "sources": sources, "tools": tools, "usage": llm.usage, "model": llm.model}
    emit("done", out)
    return out
