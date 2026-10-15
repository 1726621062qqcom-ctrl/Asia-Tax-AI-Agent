"""Round 4 (抽取改造.md §5–§7): the production boundary after the transformation — patterns before the model, candidate
passages by retrieval (BM25 + BGE-M3 + RRF, k per field) instead of one long-context locate call, every passage read
on its own (differing values are a conflict, never adjudicated), numbers and dates parsed by the program from the
quote, a table's RMB'000 applied, the temperature set and the prompt version recorded, per-field features kept.
Same ten cases and gold as rounds 1–3 (extract_eval.py: CASES, SKIP, gold_value, same; extract_eval2.py: describe).

    python extract_eval3.py OUT_DIR [--models deepseek-flash] [--cases a,b] [--jobs 4] [--samples 2] [--k 3]
                                    [--locate retrieval|llm|both] [--no-patterns] [--no-dense] [--temperature 0.7] [--meta]

--meta runs the metamorphic tests (抽取改造.md §5 E) on the K4 cases, one extraction per perturbed field, and writes
OUT_DIR/meta__<case>.json: a disclosed figure substituted everywhere in the document (the value must follow it or go
missing; the old value back means the model remembered, not read), a disclosed boolean's sentence negated (the value
must flip or go missing). Candidate order needs no test: each passage is read in a prompt of its own, so the order
of candidates cannot reach the model. Replies go through the adapter's cache, so a rerun costs nothing.
"""
import json
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from pathlib import Path

ROOT = Path(r"C:\Coding\Projects\TUM\project_study_self")
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from tax_graph.llm.deepseek import DeepSeek                                                           # noqa: E402
from tax_graph.llm.extract import BOOL, NUMBER, PROMPT_VERSION, FieldSpec, _NUM, _gloss_row, _glosses, extract, numbers_in   # noqa: E402
from tax_graph.llm.locate import PassageIndex, query_for                                                # noqa: E402
from tax_graph.quotes import loose                                                                      # noqa: E402
import extract_eval as E                                                                               # noqa: E402
import extract_eval2 as E2                                                                             # noqa: E402

GLOSS = _glosses()

NAMES = {   # role -> how the documents name the party (defined term / full name; " / " between aliases), as a person
            # writes `names` in a case file (抽取改造.md §2): the program ties a pattern's sentence to a party by these
    "K4-freetech-2024": {"ULT": "Freetech Smart Road Recycling Engineering Investment Limited / Vendor", "OP": "Target Company",
                         "BUYER": "Tianjin Expressway Group Company Limited / Purchaser"},
    "K4-shuion-kic-2024": {"ULT": "Top Victory Development Limited / Top Victory", "OP": "Shanghai Knowledge and Innovation Community Development Co., Ltd. / KIC",
                           "BUYER": "Limited Partnership"},
    "K4-shuion-ypu-2024": {"ULT": "Bright Continental Limited / Bright Continental", "OP": "Shanghai Yang Pu Centre Development Co., Ltd. / YPU",
                           "BUYER": "Limited Partnership"},
    "K4-smit-2026": {"ULT": "Vendor", "OP": "Shenzhen Giga", "BUYER": "Purchaser"},
    "K3-carote-2026": {"ULT": "Carote Group Limited / Carote Group", "HOLD": "Carote (Singapore) Management",
                       "OP": "Zhejiang Carote Industry & Trade Co., Ltd. / Zhejiang Carote"},
    "K3-ekh-2026": {"ULT": "EKH Limited / our Company", "HOLD": "Best China Development Limited / Best China",
                    "OP": "Shanghai Anxin Rong Cheng Container Logistics Co., Ltd. / SH Anxin"},
    "K3-jst-2026": {"ULT": "Hong Kong True Value Limited / HK True Value", "OP": "Shanghai Jushuitan Network Technology Co., Ltd. / Shanghai Jushuitan"},
    "K3-mirxes-2026": {"ULT": "MiRXEA Pte. Ltd. / MiRXEA", "HOLD": "Huzhou Mirui", "OP": "Hangzhou Miwei"},
    "K3-shein-2026": {"ULT": "Roadget Business Pte. Ltd. / Roadget", "OP": "Guangzhou Shein International Import & Export Co., Ltd. / Guangzhou Shein"},
    "K3-sunsine-2026": {"ULT": "China Sunsine Chemical Holdings Ltd. / the Company", "OP": "Shandong Sunsine Chemical Co., Ltd. / Shandong Sunsine"},
}


def spec_for(path, cur, kind, names):
    k, allowed, meaning = E2.describe(path, cur, kind)
    parts = path.split(".")
    g = _gloss_row(parts[-1], GLOSS)
    if parts[0] == "roles":
        about = names.get(parts[1], "")
    elif parts[0] == "holds":                       # a holding is about both parties: holder | held
        a, b = parts[1].split(">")
        about = " | ".join(x for x in (names.get(a, ""), names.get(b, "")) if x)
    else:
        about = ""
    return FieldSpec(path, k, (), "", allowed, meaning, g.get("value", ""), g.get("channel", ""), g.get("examples", ""), about)


def load(cid):
    file, src, cur, roles = E.CASES[cid]
    case = json.loads((ROOT / file).read_text(encoding="utf-8"))
    docs = {src: (ROOT / "cases/sources" / src / "source.txt").read_text(encoding="utf-8")}
    names = NAMES[cid]
    specs, gold = {}, {}
    for path, pv in case["provenance"].items():
        if path in E.SKIP or "%s@%s" % (path, cid) in E.SKIP:
            continue
        kind = pv.get("kind")
        specs[path] = spec_for(path, cur, kind, names)
        gold[path] = (kind, E.gold_value(case, path) if kind in ("disclosed", "derived") else None, pv.get("quote") or "")
    brief = ("CASE ROLES: %s Amounts are plain numbers in full units of %s (71099000, not 71.1 million or RMB'000). "
             "Ratios and rates are in percent." % (roles, cur))
    return docs, specs, gold, brief


def gold_ranks(docs, specs, gold, k, dense):
    """path -> rank (0-based) of the first top-k candidate holding the gold quote's head; -1 when the quote lies in no
    passage at all (spans two, or is not verbatim); None when it lies in a passage outside the top k."""
    idx = PassageIndex(docs, dense=dense)
    normed = [loose(t) for t in idx.texts]
    out = {}
    for path, (kind, g, quote) in gold.items():
        if kind != "disclosed" or not quote:
            continue
        head = loose(quote[:80])
        if not head or not any(head in t for t in normed):
            out[path] = -1
            continue
        hits = idx.search(query_for(specs[path]), k=k)
        out[path] = next((r for r, h in enumerate(hits) if head in loose(h["quote"])), None)
    return out


def status_of(path, kind, g, ex):
    elem, name = path.split(".", 1)
    v = ex.facts.get((elem, name))
    why = dict(ex.rejected).get(path)
    if kind in ("disclosed", "derived"):
        if v is not None:
            return "correct" if E.same(path, g, v) else "wrong", v, why
        if why and why.startswith("conflict"):
            return "conflict", None, why
        if why and why.startswith("samples disagree"):
            return "disagree", None, why
        return ("rejected" if why else "null"), None, why
    return ("abstained" if v is None else "false_fill"), v, why


def plain(v):
    return v.isoformat() if isinstance(v, date) else v


def run_case(model_id, cid, o):
    docs, specs, gold, brief = load(cid)
    ds = DeepSeek(model_id, temperature=o["temperature"])
    t0 = time.time()
    ex = extract(docs, list(specs), lambda p: ds(brief + "\n\n" + p), specs, samples=o["samples"], locate=o["locate"], k=o["k"],
                 dense=o["dense"], patterns=o["patterns"])
    ranks = gold_ranks(docs, specs, gold, o["k"], o["dense"]) if o["locate"] != "llm" else {}
    rows = []
    for path, (kind, g, _) in gold.items():
        elem, name = path.split(".", 1)
        status, v, why = status_of(path, kind, g, ex)
        ev = ex.evidence.get((elem, name))
        feat = ex.features.get(path, {})
        rows.append({"path": path, "kind": kind, "gold": plain(g), "value": plain(v), "status": status,
                     "means": "pattern-sentence" if "pattern" in feat.get("channels", []) else "retrieved", "quote": ev[1][:300] if ev else None,
                     "rejected": [why] if why else [], "conflict": ex.conflicts.get(path), "features": feat,
                     "gold_rank": ranks.get(path, "n/a")})
    return {"model": model_id, "case": cid, "samples": o["samples"], "k": o["k"], "locate": o["locate"], "patterns": o["patterns"],
            "dense": o["dense"], "temperature": o["temperature"], "prompt_version": PROMPT_VERSION, "rows": rows,
            "usage": dict(ds.usage), "wall": round(time.time() - t0, 1), "error": None, "notes": ex.notes}


# ---------------------------------------------------------------- metamorphic tests (抽取改造.md §5 E)
def perturb_number(quote, gold):
    """(old token, new token, expected value): the figure in the gold quote that states the gold, with its leading digit changed."""
    for m in _NUM.finditer(quote):
        tok, raw = m.group(0).rstrip(), m.group(1)
        vals = numbers_in(tok)
        idx = next((i for i, x in enumerate(vals) if abs(x - gold) <= 1e-6 * max(1.0, abs(gold))), None)
        if idx is None or (len(raw) < 4 and not tok.endswith("%")):
            continue
        new = str(int(raw[0]) % 9 + 1) + tok[1:]
        return tok, new, numbers_in(new)[idx]
    return None


def negate(sentence):
    for verb in (" is ", " are ", " has ", " have ", " will ", " was ", " were ", " shall ", " may ", " does ", " did "):
        if verb in sentence:
            return sentence.replace(verb, verb + "not ", 1)
    return None


def run_meta(model_id, cid, o):
    docs, specs, gold, brief = load(cid)
    (did, text), = docs.items()
    ds = DeepSeek(model_id, temperature=o["temperature"])
    tests = []
    for path, (kind, g, quote) in gold.items():
        if kind != "disclosed" or not quote:
            continue
        s = specs[path]
        if s.kind == NUMBER and isinstance(g, (int, float)):
            p = perturb_number(quote, float(g))
            if p is None:
                tests.append({"path": path, "test": "substitute", "status": "skipped: no figure of the gold in the quote"})
                continue
            tok, new, expected = p
            pat = re.compile("(?<![0-9.])%s(?![0-9.])" % re.escape(tok))
            text2, n = pat.subn(new, text)
            if n == 0:
                tests.append({"path": path, "test": "substitute", "status": "skipped: figure not found verbatim in the document"})
                continue
            ex = extract({did: text2}, [path], lambda pr: ds(brief + "\n\n" + pr), specs, samples=o["samples"], locate=o["locate"], k=o["k"],
                         dense=o["dense"], patterns=o["patterns"])
            v = ex.facts.get(tuple(path.split(".", 1)))
            why = dict(ex.rejected).get(path)
            ev = ex.evidence.get(tuple(path.split(".", 1)))
            if v is None:
                st = "missing"
            elif E.same(path, expected, v):
                st = "follows"
            elif E.same(path, g, v):                     # the old figure: by construction only from a quote that states it
                st = "old figure stated elsewhere" if ev and any(E.same(path, g, x) for x in numbers_in(ev[1])) else "memorised"
            else:
                st = "other"
            tests.append({"path": path, "test": "substitute", "token": tok, "new": new, "replaced": n, "gold": g, "expected": expected,
                          "value": plain(v), "status": st, "why": why, "quote": ev[1][:300] if ev else None, "conflict": ex.conflicts.get(path)})
        elif s.kind == BOOL and isinstance(g, bool):
            pos = text.find(quote)
            neg = negate(quote) if pos >= 0 else None
            if neg is None:
                tests.append({"path": path, "test": "negate", "status": "skipped: quote not verbatim or no verb to negate"})
                continue
            text2 = text[:pos] + neg + text[pos + len(quote):]
            ex = extract({did: text2}, [path], lambda pr: ds(brief + "\n\n" + pr), specs, samples=o["samples"], locate=o["locate"], k=o["k"],
                         dense=o["dense"], patterns=o["patterns"])
            v = ex.facts.get(tuple(path.split(".", 1)))
            why = dict(ex.rejected).get(path)
            st = "missing" if v is None else ("flips" if v is (not g) else "unchanged")
            tests.append({"path": path, "test": "negate", "sentence": neg[:200], "gold": g, "value": plain(v), "status": st, "why": why})
    return {"model": model_id, "case": cid, "tests": tests, "usage": dict(ds.usage), "prompt_version": PROMPT_VERSION}


def main(argv):
    out = Path(argv[1])
    out.mkdir(parents=True, exist_ok=True)
    opt = lambda flag, default: argv[argv.index(flag) + 1] if flag in argv else default
    models = opt("--models", "deepseek-flash").split(",")
    cases = opt("--cases", ",".join(E.CASES)).split(",")
    o = {"samples": int(opt("--samples", 2)), "k": int(opt("--k", 3)), "locate": opt("--locate", "retrieval"), "patterns": "--no-patterns" not in argv,
         "dense": "--no-dense" not in argv, "temperature": float(opt("--temperature", 0.7))}
    meta = "--meta" in argv
    if meta:
        cases = [c for c in cases if c.startswith("K4-")]
    todo = [(m, c) for c in cases for m in models if not (out / ("%s%s__%s.json" % ("meta__" if meta else "", m, c))).exists()]
    print("jobs:", len(todo), o, flush=True)

    def work(mc):
        try:
            res = run_meta(mc[0], mc[1], o) if meta else run_case(mc[0], mc[1], o)
        except Exception as e:
            import traceback
            traceback.print_exc()
            print("%-16s %-20s FAILED %s: %s" % (mc[0], mc[1], type(e).__name__, e), flush=True)
            return
        (out / ("%s%s__%s.json" % ("meta__" if meta else "", mc[0], mc[1]))).write_text(json.dumps(res, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
        c = {}
        for r in res["tests" if meta else "rows"]:
            c[r["status"].split(":")[0]] = c.get(r["status"].split(":")[0], 0) + 1
        print("%-16s %-20s %6.0fs %s calls=%d cached=%d" % (mc[0], mc[1], res.get("wall", 0), c, res["usage"]["calls"], res["usage"]["cached"]), flush=True)

    with ThreadPoolExecutor(int(opt("--jobs", 4))) as pool:
        list(pool.map(work, todo))


if __name__ == "__main__":
    main(sys.argv)
