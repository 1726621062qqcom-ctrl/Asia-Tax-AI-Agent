"""Compare two DeepSeek models on the extraction boundary (tax_graph.llm.extract), against the provenance-marked
facts of the K4 real and K3 semi-synthetic cases.

    python extract_eval.py OUT_DIR [--models deepseek-flash,deepseek-v4-pro] [--cases K4-freetech-2024,...] [--jobs 8]

Gold: every provenance entry of a case file.
  disclosed  -> the value in the case file is expected (quoted in the source)
  derived    -> the value in the case file is expected, but it rests on a formula or a law (reported apart)
  missing    -> null expected (the source does not settle it)
  synthetic  -> null expected (made up for the semi-synthetic case; the source cannot contain it)
Modelling parameters (present.payment, event.years) and synthetic plan choices are left out.
"""
import json
import re
import ssl
import sys
import threading
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from pathlib import Path

import certifi

ROOT = Path(r"C:\Coding\Projects\TUM\project_study_self")
sys.path.insert(0, str(ROOT))
from tax_graph.llm.extract import BOOL, DATE, ENUM, NUMBER, FieldSpec, extract, field_specs  # noqa: E402

API = "https://api.deepseek.com/chat/completions"
KEY = (ROOT / ".env").read_text(encoding="utf-8").split("=", 1)[1].strip().strip('"')
CTX = ssl.create_default_context(cafile=certifi.where())

CASES = {   # case id -> (case file, source dir, currency, role brief)
    "K4-freetech-2024": ("cases/real/K4-freetech-2024.json", "K4-freetech-2024", "RMB",
        "ULT = Freetech Smart Road Recycling Engineering Investment Limited (the Vendor); OP = the Target Company being sold; "
        "BUYER = the Purchaser."),
    "K4-shuion-kic-2024": ("cases/real/K4-shuion-kic-2024.json", "K4-shuion-2024", "RMB",
        "ULT = Top Victory Development Limited (the transferor); OP = Shanghai Knowledge and Innovation Community Development "
        "Co., Ltd. (KIC); BUYER = the Limited Partnership that acquires the KIC equity. Only the KIC equity transfer matters."),
    "K4-shuion-ypu-2024": ("cases/real/K4-shuion-ypu-2024.json", "K4-shuion-2024", "RMB",
        "ULT = Bright Continental Limited (the transferor); OP = Shanghai Yang Pu Centre Development Co., Ltd. (YPU); "
        "BUYER = the Limited Partnership that acquires the YPU equity. Only the YPU equity transfer matters."),
    "K4-smit-2026": ("cases/real/K4-smit-2026.json", "K4-smit-2026", "RMB",
        "ULT = the Vendor (the Company's subsidiary that sells the Target Interest); OP = Shenzhen Giga (the company whose "
        "equity is sold); BUYER = the Purchaser."),
    "K3-carote-2026": ("cases/semisynth/K3-carote-2026.json", "K3-carote-2024", "RMB",
        "ULT = Carote Group Limited (Hong Kong); HOLD = Carote (Singapore) Management Pte. Ltd; OP = Zhejiang Carote Industry & "
        "Trade Co., Ltd. Flow up1 = a dividend paid by OP to its shareholder; flow up2 = a dividend paid by HOLD to ULT."),
    "K3-ekh-2026": ("cases/semisynth/K3-ekh-2026.json", "K3-ekh-2026", "SGD",
        "ULT = EKH Limited (the Company, the listing applicant); HOLD = Best China Development Limited; OP = Shanghai Anxin Rong "
        "Cheng Container Logistics Co., Ltd. (SH Anxin). Flow up1 = a dividend paid by OP to HOLD; flow up2 = a dividend paid "
        "by HOLD to ULT."),
    "K3-jst-2026": ("cases/semisynth/K3-jst-2026.json", "K3-jst-2025", "RMB",
        "ULT = Hong Kong True Value Limited; OP = Shanghai Jushuitan Network Technology Co., Ltd. Flow out = a distribution "
        "(dividend or return of capital) paid by OP to ULT."),
    "K3-mirxes-2026": ("cases/semisynth/K3-mirxes-2026.json", "K3-mirxes-2025", "RMB",
        "ULT = MiRXEA Pte. Ltd.; HOLD = Huzhou Mirui; OP = Hangzhou Miwei. Flow reorg = the transfer of 100% of OP by ULT to HOLD "
        "in June 2023. Flow up1 = a dividend paid by OP to its shareholder; flow up2 = a dividend paid by HOLD to ULT. "
        "'present' fields describe the structure BEFORE the June 2023 transfer."),
    "K3-shein-2026": ("cases/semisynth/K3-shein-2026.json", "K3-shein-2026", "USD",
        "ULT = Roadget Business Pte. Ltd.; OP = Guangzhou Shein International Import & Export Co., Ltd. Flow up1 = a dividend "
        "paid by OP to ULT."),
    "K3-sunsine-2026": ("cases/semisynth/K3-sunsine-2026.json", "K3-sunsine-2024", "RMB",
        "ULT = China Sunsine Chemical Holdings Ltd. (the Company); OP = Shandong Sunsine Chemical Co., Ltd. Flow up1 = a "
        "dividend paid by OP to ULT."),
}
SKIP = {"present.payment", "event.years", "present.repatriation", "flows.out.reduced_capital_ratio",
        "roles.ULT.attrs.group_revenue_eur@K3-sunsine-2026"}
JURS = ("CN", "HK", "SG", "OTHER")


def describe(path, cur, kind_of_gold):
    """FieldSpec kind, allowed values and the meaning of one case path."""
    parts = path.split(".")
    name = parts[-1]
    if path.startswith("roles."):
        r = parts[1]
        if name == "loc":
            return ENUM, JURS, "the jurisdiction where %s is established (CN = Mainland China)" % r
        if name == "incorporated_in":
            return ENUM, JURS, "the jurisdiction where %s is incorporated" % r
        if name == "cit_rate":
            return NUMBER, (), "the enterprise income tax rate actually applicable to %s, including any preferential rate, in percent" % r
        if name == "is_mne_member":
            return BOOL, (), "whether %s belongs to a group that has entities in more than one jurisdiction" % r
        if name == "group_revenue_eur":
            return NUMBER, (), "consolidated revenue of the group %s belongs to, latest full financial year, converted to EUR, full amount" % r
    if path.startswith("holds."):
        a, b = parts[1].split(">")
        if name == "ratio":
            return NUMBER, (), "percentage of %s's equity held directly by %s" % (b, a)
        if name == "since":
            return DATE, (), "the date %s first acquired its shareholding in %s" % (a, b)
        if name == "cost":
            return NUMBER, (), "the total amount %s paid for, or contributed to, its equity in %s (its acquisition cost), full amount in %s" % (a, b, cur)
    if path.startswith("flows."):
        f = parts[1]
        if name == "listed_market_trade":
            return BOOL, (), "whether the disposal (flow %s) is a sale of listed shares on a public stock exchange" % f
        if name == "receipt_kind":
            return ENUM, field_specs()["flow.receipt_kind"].allowed, "how the seller receives the proceeds of flow %s: REMITTED (paid into its account), DEBT_SETTLED (set off against a debt), MOVABLE_PROPERTY (paid in kind)" % f
        if name == "immovable_ratio":
            return NUMBER, (), "percentage of the value of OP's equity that derives from immovable property (land, buildings, property under development), in percent"
        if name == "foreign_taxed":
            return BOOL, (), "whether flow %s is subject to tax (including withholding tax) in the payer's jurisdiction" % f
        if name == "foreign_headline_rate":
            return NUMBER, (), "the statutory corporate income tax rate of the payer's jurisdiction for flow %s, in percent" % f
        if name == "deductible_at_payer":
            return BOOL, (), "whether the payer of flow %s may deduct the payment in computing its taxable income" % f
        if name == "amount":
            return NUMBER, (), "the consideration of flow %s, full amount in %s" % (f, cur)
        if name == "reorg_equity_payment_share":
            return NUMBER, (), "percentage of the consideration of flow %s that is paid in equity of the acquirer, in percent" % f
    if path == "present.HOLD":
        return ENUM, ("CN", "HK", "SG", "OTHER", "NONE"), "the jurisdiction of the intermediate company between ULT and OP (held by ULT, holding OP), or NONE if ULT holds OP directly"
    if path == "present.financing":
        return ENUM, ("EQUITY", "DEBT"), "how ULT funds OP: EQUITY (share capital) or DEBT (intra-group loans)"
    if path == "present.exit_route":
        return ENUM, ("DIRECT", "INDIRECT"), "DIRECT if the seller sells the equity of OP itself, INDIRECT if it sells a company above OP"
    if path == "event.exit":
        return NUMBER, (), "the consideration for the disposal of ULT's equity in OP, full amount in %s" % cur
    if path == "event.on":
        if kind_of_gold == "synthetic":
            return DATE, (), "the payment date of the 2026 distribution by OP that this case is about (a future, planned distribution)"
        return DATE, (), "the date of the disposal (the date the transfer agreement was signed, if completion is not stated)"
    if path == "event.dividend":
        return NUMBER, (), "the amount of the 2026 distribution by OP to its shareholder that this case is about (a future, planned distribution), full amount in %s" % cur
    if path == "event.onward":
        return NUMBER, (), "the amount HOLD passes on to ULT out of the 2026 distribution this case is about (future, planned), full amount in %s" % cur
    raise KeyError(path)


def gold_value(case, path):
    parts = path.split(".")
    if parts[0] == "roles":
        r = case["roles"][parts[1]]
        return r["loc"] if parts[2] == "loc" else r["attrs"].get(parts[3])
    if parts[0] == "holds":
        a, b = parts[1].split(">")
        h = next(h for h in case["holds"] if h["holder"] == a and h["held"] == b)
        return h.get(parts[2])
    if parts[0] == "flows":
        return case["flows"][parts[1]].get(parts[2])
    if parts[0] == "present":
        v = case["present"].get(parts[1])
        return "NONE" if (parts[1] == "HOLD" and v is None) else v
    if parts[0] == "event":
        return case["event"].get(parts[1])
    raise KeyError(path)


def same(path, g, v):
    if isinstance(g, bool) or isinstance(v, bool):
        return g is v
    if isinstance(g, (int, float)) and isinstance(v, (int, float)):
        name = path.split(".")[-1]
        if name in ("ratio", "cit_rate", "foreign_headline_rate", "immovable_ratio", "reorg_equity_payment_share"):
            return abs(g - v) <= 0.5
        tol = 0.05 if name == "group_revenue_eur" else 0.01
        return abs(g - v) <= tol * max(abs(g), 1)
    if isinstance(v, date):
        return str(g) == v.isoformat()
    return str(g) == str(v)


# ---------------------------------------------------------------- the model
USAGE_LOCK = threading.Lock()


def make_model(model_id, brief, log, usage):
    def call(prompt):
        body = json.dumps({"model": model_id, "messages": [{"role": "user", "content": brief + "\n\n" + prompt}],
                           "max_tokens": 65536, "stream": False}).encode("utf-8")
        last = None
        for attempt in range(3):
            t0 = time.time()
            try:
                req = urllib.request.Request(API, data=body, headers={"Authorization": "Bearer " + KEY,
                                                                     "Content-Type": "application/json"})
                with urllib.request.urlopen(req, timeout=1500, context=CTX) as r:
                    d = json.loads(r.read().decode("utf-8"))
                text = d["choices"][0]["message"].get("content") or ""
                u = d.get("usage", {})
                with USAGE_LOCK:
                    usage["calls"] += 1
                    usage["prompt_tokens"] += u.get("prompt_tokens", 0)
                    usage["completion_tokens"] += u.get("completion_tokens", 0)
                    usage["cache_hit_tokens"] += u.get("prompt_cache_hit_tokens", 0)
                    usage["seconds"] += time.time() - t0
                log.append({"prompt_head": prompt[:200], "reply": text[:6000], "usage": u, "seconds": round(time.time() - t0, 1)})
                return text
            except Exception as e:      # transient network / server errors: retry twice
                last = "%s: %s" % (type(e).__name__, getattr(e, "read", lambda: b"")()[:300] or e)
                log.append({"prompt_head": prompt[:200], "error": str(last), "attempt": attempt})
                time.sleep(5 * (attempt + 1))
        raise RuntimeError(last)
    return call


def run_one(model_id, cid):
    file, src, cur, roles = CASES[cid]
    case = json.loads((ROOT / file).read_text(encoding="utf-8"))
    doc = (ROOT / "cases/sources" / src / "source.txt").read_text(encoding="utf-8")
    docs = {src: doc}
    specs, gold = {}, {}
    for path, pv in case["provenance"].items():
        if path in SKIP or "%s@%s" % (path, cid) in SKIP:
            continue
        kind = pv.get("kind")
        k, allowed, meaning = describe(path, cur, kind)
        specs[path] = FieldSpec(path, k, (), meaning, allowed)
        gold[path] = (kind, gold_value(case, path) if kind in ("disclosed", "derived") else None)
    brief = ("CASE ROLES: %s Amounts are plain numbers in full units of %s (71099000, not 71.1 million or RMB'000). "
             "Ratios and rates are in percent." % (roles, cur))
    log, usage = [], {"calls": 0, "prompt_tokens": 0, "completion_tokens": 0, "cache_hit_tokens": 0, "seconds": 0.0}
    t0 = time.time()
    err = None
    try:
        ex = extract(docs, list(specs), make_model(model_id, brief, log, usage), specs)
    except Exception as e:
        ex, err = None, "%s: %s" % (type(e).__name__, e)
    rows = []
    for path, (kind, g) in gold.items():
        if ex is None:
            rows.append({"path": path, "kind": kind, "gold": g, "value": None, "status": "error", "quote": None})
            continue
        elem, name = path.split(".", 1)
        v = ex.facts.get((elem, name))
        ev = ex.evidence.get((elem, name))
        rej = [why for k, why in ex.rejected if k == path]
        if kind in ("disclosed", "derived"):
            status = "correct" if v is not None and same(path, g, v) else ("wrong" if v is not None else ("rejected" if rej else "null"))
        else:
            status = "abstained" if v is None else "false_fill"
        rows.append({"path": path, "kind": kind, "gold": g if not isinstance(g, date) else str(g),
                     "value": v.isoformat() if isinstance(v, date) else v, "status": status,
                     "quote": ev[1][:300] if ev else None, "rejected": rej})
    return {"model": model_id, "case": cid, "rows": rows, "usage": usage, "wall": round(time.time() - t0, 1), "error": err, "log": log}


def relax():
    """Variant: quotes compared after unifying quote marks and dashes; JSON parsed non-strictly (control characters)."""
    import tax_graph.llm.extract as X
    table = str.maketrans({c: '"' for c in "‘’“”′″'`´"})
    table.update(str.maketrans({c: "-" for c in "‐‑‒–—―−"}))

    def norm(x):
        return re.sub(r'"+', '"', re.sub(r"\s+", "", x).translate(table))

    def supported(quote, doc_id, docs):
        return bool(quote) and doc_id in docs and norm(quote) in norm(docs[doc_id])

    def as_json(text):
        m = re.search(r"\{.*\}", text, re.S)
        return json.loads(m.group(0), strict=False) if m else None

    X._supported = supported
    X._json = as_json


def main(argv):
    if "--relaxed" in argv:
        relax()
    out = Path(argv[1])
    out.mkdir(parents=True, exist_ok=True)
    models = (argv[argv.index("--models") + 1] if "--models" in argv else "deepseek-flash,deepseek-v4-pro").split(",")
    cases = (argv[argv.index("--cases") + 1].split(",") if "--cases" in argv else list(CASES))
    jobs = int(argv[argv.index("--jobs") + 1]) if "--jobs" in argv else 8
    todo = [(m, c) for c in cases for m in models if not (out / ("%s__%s.json" % (m, c))).exists()]
    print("jobs:", len(todo), flush=True)

    def work(mc):
        res = run_one(*mc)
        (out / ("%s__%s.json" % mc)).write_text(json.dumps(res, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
        c = {}
        for r in res["rows"]:
            c[r["status"]] = c.get(r["status"], 0) + 1
        print("%-16s %-20s %6.0fs %s %s" % (mc[0], mc[1], res["wall"], c, res["error"] or ""), flush=True)

    with ThreadPoolExecutor(jobs) as pool:
        list(pool.map(work, todo))


if __name__ == "__main__":
    main(sys.argv)
