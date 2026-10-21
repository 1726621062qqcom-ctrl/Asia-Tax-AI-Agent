"""Conversational intake (界面.md: strategy mode). The client describes the case in words; the model reads the structure
out of it — companies, where they are, who holds whom, each payment — quoting the sentence for every value; the program
parses amounts, dates and percentages from the quotes, keeps only what the quotes support, and hands the result to the
structure form as a prefilled draft that the client confirms. Nothing the model says enters the case without a quote
that states it and the client's confirmation.
"""
import json
import re
from datetime import date

from ..llm.deepseek import DeepSeek
from ..llm.extract import dates_in, numbers_in
from ..scope import ADMITTED_KINDS
from .intake import TRANSACTION_TYPES

JUR_WORDS = {"CN": ("mainland", "china", "prc", "shanghai", "beijing", "shenzhen", "guangzhou", "hangzhou", "内地", "中国", "大陆", "上海", "北京", "深圳"),
             "HK": ("hong kong", "hongkong", "香港"), "SG": ("singapore", "新加坡")}

GUIDE = ("Describe the companies (name and where each is incorporated: Mainland China, Hong Kong or Singapore), who holds what "
         "percentage of whom and since when, and each payment separately: who pays whom, what kind (dividend, interest, capital "
         "reduction, liquidation distribution), the amount with its currency, and the date. Add any income tax already paid on a "
         "payment, and name the documents you have. Do not state tax conclusions; the rules decide those.")

PROMPT = """Read the client's description of a cross-border situation and extract its structure. Jurisdictions handled: Mainland China (CN), Hong Kong (HK), Singapore (SG). Payment kinds handled: DIVIDEND, INTEREST, CAPITAL_REDUCTION, LIQUIDATION. Other kinds are listed as "other" with their words.

Answer with JSON only:
{{"companies": [{{"name": "<as written>", "loc": "CN|HK|SG|?", "quote": "<the sentence that says where it is>"}}],
 "ownership": [{{"holder": "<company name>", "held": "<company name>", "ratio": <percent or null>, "since": "<YYYY-MM-DD or null>", "cost": <number or null>, "quote": "<sentence>"}}],
 "transactions": [{{"payer": "<company name>", "payee": "<company name>", "kind": "DIVIDEND|INTEREST|CAPITAL_REDUCTION|LIQUIDATION|other", "kind_words": "<the client's words for the kind>", "amount": <number or null>, "currency": "<ISO code or null>", "on": "<YYYY-MM-DD or null>", "paid": [{{"jurisdiction": "CN|HK|SG", "amount": <number>, "quote": "<sentence>"}}], "quote": "<the sentence that states this payment>"}}],
 "as_at": "<assessment date YYYY-MM-DD or null>", "currency": "<the single currency the client uses, or null>", "documents": ["<document names mentioned>"], "unclear": ["<anything you could not place>"]}}

Rules: copy quotes verbatim from the description; a number or date you cannot find in a sentence is null; never infer a jurisdiction from a name alone (then "?"); never add companies or payments that are not described; the company whose tax the client cares about is not for you to decide.

Description:
{text}"""


def _json(text):
    m = re.search(r"\{.*\}", text or "", re.S)
    try:
        return json.loads(m.group(0)) if m else {}
    except ValueError:
        return {}


def _norm(s):
    return re.sub(r"[^0-9a-z一-鿿]+", "", str(s or "").lower())


def _quoted(quote, text):
    return bool(quote) and _norm(quote) in _norm(text)


def _ident(name, used):
    base = re.sub(r"[^A-Z]+", "_", str(name or "").upper()).strip("_")[:24] or "COMPANY"
    cand, k = base, 2
    while cand in used:
        cand, k = "%s_%d" % (base, k), k + 1
    used.add(cand)
    return cand


def read_case(text: str, model: str = "deepseek-flash") -> dict:
    """The structure form's draft from a description, each value backed by a quote the program checked, plus what is missing."""
    text = (text or "").strip()
    if len(text) < 20:
        raise ValueError("Describe the case in a few sentences first")
    if len(text) > 20000:
        raise ValueError("Keep the description under 20,000 characters; attach long documents after the case is created")
    llm = DeepSeek(model or "deepseek-flash", temperature=0.0)
    d = _json(llm(PROMPT.format(text=text)))
    missing, rejected, quotes = [], [], {}
    ids, by_name = set(), {}
    companies = []
    for c in d.get("companies") or []:
        name = str(c.get("name") or "").strip()
        if not name or name in by_name:
            continue
        loc = str(c.get("loc") or "?").upper()
        q = str(c.get("quote") or "")
        if loc in ("CN", "HK", "SG") and not (_quoted(q, text) and any(w in q.lower() for w in JUR_WORDS[loc])):
            rejected.append("%s: jurisdiction %s is not stated in a quoted sentence" % (name, loc))
            loc = ""
        elif loc not in ("CN", "HK", "SG"):
            loc = ""
        if not loc:
            missing.append("Jurisdiction of %s" % name)
        cid = _ident(name, ids)
        by_name[name] = cid
        companies.append({"id": cid, "name": name, "loc": loc, "member": True})
        quotes["companies.%s.loc" % cid] = q if loc else ""
    if not companies:
        missing.append("The companies involved (name and jurisdiction)")

    def resolve(name):
        name = str(name or "").strip()
        if name in by_name:
            return by_name[name]
        low = name.lower()
        hits = [cid for n, cid in by_name.items() if low and (low in n.lower() or n.lower() in low)]
        return hits[0] if len(hits) == 1 else ""

    ownership = []
    for h in d.get("ownership") or []:
        a, b, q = resolve(h.get("holder")), resolve(h.get("held")), str(h.get("quote") or "")
        if not a or not b or a == b or not _quoted(q, text):
            rejected.append("ownership link %s -> %s: parties or quote not found" % (h.get("holder"), h.get("held")))
            continue
        nums = numbers_in(q)
        ratio = h.get("ratio") if isinstance(h.get("ratio"), (int, float)) and any(abs(float(h["ratio"]) - n) < 1e-6 for n in nums) else None
        if ratio is None:
            missing.append("Ownership percentage: %s in %s" % (h.get("holder"), h.get("held")))
        row = {"holder": a, "held": b, "ratio": ratio if ratio is not None else ""}
        since = str(h.get("since") or "")
        if since and any(x.isoformat() == since for x in dates_in(q)):
            row["since"] = since
        if isinstance(h.get("cost"), (int, float)) and any(abs(float(h["cost"]) - n) < 1e-6 for n in nums):
            row["cost"] = h["cost"]
        ownership.append(row)
        quotes["ownership.%s>%s" % (a, b)] = q

    transactions, n = [], 0
    for t in d.get("transactions") or []:
        q = str(t.get("quote") or "")
        payer, payee = resolve(t.get("payer")), resolve(t.get("payee"))
        kind = str(t.get("kind") or "other").upper()
        if not _quoted(q, text):
            rejected.append("payment %s -> %s: the quoted sentence is not in the description" % (t.get("payer"), t.get("payee")))
            continue
        if kind not in ADMITTED_KINDS or kind not in TRANSACTION_TYPES:
            rejected.append("payment %s -> %s (%s): not a kind this program handles (dividend, interest, capital reduction, liquidation distribution)" % (
                t.get("payer"), t.get("payee"), t.get("kind_words") or kind))
            continue
        n += 1
        fid = "payment_%d" % n
        nums = numbers_in(q)
        amount = t.get("amount") if isinstance(t.get("amount"), (int, float)) and any(abs(float(t["amount"]) - x) < 1e-6 for x in nums) else ""
        on = str(t.get("on") or "")
        on = on if on and any(x.isoformat() == on for x in dates_in(q)) else ""
        if not payer or not payee:
            missing.append("Payer and recipient of %s" % (t.get("kind_words") or kind.lower()))
        if amount == "":
            missing.append("Amount of %s %s -> %s" % (kind.lower(), t.get("payer"), t.get("payee")))
        if not on:
            missing.append("Date of %s %s -> %s" % (kind.lower(), t.get("payer"), t.get("payee")))
        paid = {}
        for p in t.get("paid") or []:
            pq, j = str(p.get("quote") or ""), str(p.get("jurisdiction") or "").upper()
            if j in ("CN", "HK", "SG") and _quoted(pq, text) and isinstance(p.get("amount"), (int, float)) and any(abs(float(p["amount"]) - x) < 1e-6 for x in numbers_in(pq)):
                paid[j] = p["amount"]
            else:
                rejected.append("tax paid on %s: not supported by a quoted figure" % fid)
        transactions.append({"id": fid, "income": kind, "payer": payer, "payee": payee, "amount": amount, "on": on, "paid": paid})
        quotes["transactions.%s" % fid] = q
    if not transactions:
        missing.append("At least one payment this program handles (dividend, interest, capital reduction, liquidation distribution)")
    currency = str(d.get("currency") or "").upper()
    if currency not in ("CNY", "HKD", "SGD", "USD", "EUR"):
        currency = ""
        missing.append("The single currency for all amounts")
    as_at = str(d.get("as_at") or "")
    try:
        date.fromisoformat(as_at)
    except ValueError:
        as_at = ""
    draft = {"case_id": "", "currency": currency, "as_at": as_at, "source": "Client's description (strategy mode), " + date.today().isoformat(),
             "companies": companies or [{"id": "COMPANY_A", "name": "", "loc": "", "member": True}],
             "ownership": ownership, "transactions": transactions or [{"id": "payment_1", "income": "", "payer": "", "payee": "", "amount": "", "on": "", "paid": {}}]}
    return {"draft": draft, "quotes": quotes, "missing": list(dict.fromkeys(missing)), "rejected": rejected,
            "documents": [str(x) for x in (d.get("documents") or [])], "unclear": [str(x) for x in (d.get("unclear") or [])],
            "usage": llm.usage, "model": llm.model}
