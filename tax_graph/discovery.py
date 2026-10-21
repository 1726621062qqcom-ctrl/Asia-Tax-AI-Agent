"""Discovery by vote (自进化.md): three independent readers look for income-tax issues the fixed logic may have missed.

    python -m tax_graph.discovery CASE.json [--run DIR] [--model qwen3.8-flash] [--voters 3]

Each voter reads the case brief (parties, holdings, transactions, stated facts, document excerpts) and lists the income-tax
issues it sees, with the legal basis. The program then shows each voter what the fixed logic did on this case (the rules
that fired, the questions it asked) and asks it to mark each of its own issues as covered or missing. An issue counts as
a gap when a majority of voters mark it missing. Gaps are proposals only: discovery.json / DISCOVERY.md in the run
directory, for a person or, later, a maintenance agent (MAINTENANCE_AGENT = False: nothing is changed by this module).
"""
import csv
import io
import json
import re
import sys
import time
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from .flow_tax import RULES
from .llm.deepseek import DeepSeek

ROOT = Path(__file__).resolve().parents[1]
MAINTENANCE_AGENT = False          # development phase: proposals are written, never applied
EXCERPT = 3500                     # characters of each document the voters see
ANGLES = {                         # three independent readings of the same case
    "source": "You are a tax inspector of the jurisdiction where each payment arises. Look for every income tax or withholding tax that jurisdiction can charge on these payments, and every relief it may deny.",
    "residence": "You are the tax adviser of the recipient of each payment. Look for every income tax the recipient's jurisdiction charges on receipt, every exemption or foreign tax credit available, and every residence or substance condition attached.",
    "treaty": "You are a treaty and anti-avoidance specialist. Look for every treaty article, beneficial-ownership, principal-purpose, controlled-foreign-company, place-of-effective-management or Pillar Two question these payments raise.",
}

ISSUE_PROMPT = """{angle}

Scope: income tax only (corporate income tax, profits tax, withholding tax on income, foreign tax credits, treaty relief, anti-avoidance rules that change an income tax). Ignore VAT, GST, stamp duty, customs and property taxes. Jurisdictions: Mainland China (CN), Hong Kong (HK), Singapore (SG).

Case:
{brief}

List every income-tax issue this case raises. Answer with JSON only: {{"issues": [{{"flow": "<transaction id from the case, or 'entity:<id>' for an entity-level issue>", "jurisdiction": "CN|HK|SG", "kind": "<one of: withholding, residence_taxation, exemption, credit, treaty_relief, anti_abuse, deduction, residence_status, permanent_establishment, pillar_two, cfc, deferral, procedure>", "issue": "<one sentence>", "basis": "<law and article, e.g. 企业所得税法 第三条; IRO s 14; ITA s 10(1)(d); DTA CN-SG Art 10>", "depends_on": "<the fact that decides it, or ''>"}}]}}
Only issues the facts support; no invented facts; no tax amounts."""

MATCH_PROMPT = """Below are the income-tax issues you listed for a case, and what a rule-based program did on the same case: the rules it applied (id, what the rule does, its source) and the questions it asked the client.

Your issues:
{issues}

The program's rules on this case:
{rules}

The program's questions:
{questions}

For each of your issues say whether the program covered it. Answer with JSON only: {{"marks": [{{"n": <issue number>, "covered": true|false, "by": "<rule ids or question keys that cover it, or ''>", "why": "<one sentence>"}}]}}
Mark covered only when a listed rule or question addresses the same tax in the same jurisdiction on the same payment; a related rule on another payment or another jurisdiction does not count."""


def _params():
    csv.field_size_limit(10**9)
    with open(ROOT / "official" / "params.csv", encoding="utf-8-sig") as f:
        return {r["param_id"]: r for r in csv.DictReader(f)}


def rule_text(rid, P):
    r = next((x for x in RULES if x.id == rid), None)
    if r is None:
        return "%s" % rid
    p = P.get(r.value or "", {})
    sc = r.scope
    where = "%s -> %s" % (sc.source, sc.residence or "domestic")
    reads = ", ".join(sorted(x.split(".", 1)[-1] for x in r.reads)) or "no facts"
    return "%s: %s on %s (%s; taxing %s); conditions read: %s; source %s: %s" % (rid, r.effect.value.lower(), sc.income, where, sc.taxing, reads, p.get("cite_id", ""), (p.get("quote") or "")[:120].replace("\n", " "))


def always_checked():
    """Engine-level checks that run on every case whether or not they produce a tax item."""
    ids = sorted(r.id for r in RULES if r.scope.income in ("TOPUP", "CFC_INCLUSION"))
    return ("- Pillar Two top-up (group revenue threshold EUR 750m, QDMTT in HK and SG, IIR): %s\n"
            "- Mainland CFC inclusion for Mainland-controlled low-taxed foreign companies: %s\n"
            "- Place of effective management: a foreign company managed from the Mainland is tried as a Mainland resident (82号文)"
            % (", ".join(i for i in ids if "cfc" not in i) or "p2 rules", ", ".join(i for i in ids if "cfc" in i) or "cfc rules"))


def brief(case: dict, docs: dict, graph=None) -> str:
    names = case.get("names") or {}
    nm = lambda r: "%s (%s)" % (names.get(r, r), r) if names.get(r) else r
    L = ["Currency: %s. Assessment date: %s." % (case.get("currency"), (case.get("event") or {}).get("as_at"))]
    L.append("Parties:")
    for r, v in (case.get("roles") or {}).items():
        facts = ", ".join("%s=%s" % kv for kv in (v.get("attrs") or {}).items())
        L.append("- %s, %s, %s%s" % (nm(r), v.get("loc"), v.get("type", "COMPANY"), ("; facts: " + facts) if facts else ""))
    if case.get("holds"):
        L.append("Ownership:")
        for h in case["holds"]:
            L.append("- %s holds %s%% of %s%s%s" % (nm(h["holder"]), h["ratio"], nm(h["held"]), (" since " + str(h["since"])) if h.get("since") else "", (" at cost " + str(h["cost"])) if h.get("cost") is not None else ""))
    L.append("Transactions:")
    tx = case.get("transactions") or {}
    if tx:
        for fid, t in tx.items():
            facts = ", ".join("%s=%s" % kv for kv in (case.get("flows", {}).get(fid) or {}).items())
            L.append("- %s: %s pays %s %s %s on %s%s%s" % (fid, nm(t["payer"]), nm(t["payee"]), t["income"].lower(), t["amount"], t["on"], (" (target %s)" % nm(t["target"])) if t.get("target") else "", ("; facts: " + facts) if facts else ""))
    elif graph is not None:
        for f in graph.flows:
            facts = ", ".join("%s=%s" % kv for kv in f.attrs.items() if kv[1] is not None)
            L.append("- %s: %s pays %s %s %s on %s%s" % (f.id, nm(f.payer), nm(f.payee), f.income.lower(), f.amount, f.on, ("; facts: " + facts) if facts else ""))
        L.append("(the client's present structure; use these transaction ids)")
    else:
        ev = {k: v for k, v in (case.get("event") or {}).items() if v not in (None, False, 1)}
        L.append("- template %s, event %s, present structure %s" % (case.get("template"), ev, case.get("present")))
        for fid, f in (case.get("flows") or {}).items():
            if f:
                L.append("- flow %s facts: %s" % (fid, ", ".join("%s=%s" % kv for kv in f.items())))
    if case.get("settled"):
        L.append("Tax already paid: %s" % json.dumps(case["settled"], ensure_ascii=False))
    for name, text in docs.items():
        L.append("Document %s (excerpt):\n%s" % (name, text[:EXCERPT]))
    return "\n".join(L)


def fixed_logic(case_path: Path, run_dir: Path):
    """What the program did: rule ids applied on the best candidate (both bounds) and the questions asked."""
    from .ex_ante import ex_ante
    from .run import load_case
    template, case, event, subject, ticks, notes = load_case(run_dir / "reviewed.json" if (run_dir / "reviewed.json").exists() else case_path)
    out = ex_ante(template, event, case, ticks=ticks or None, subject=subject)
    best = out.table[0]
    rids = set()
    for labels in (best.b.L_lo, best.b.L_hi):
        for lb in labels.values():
            rids |= set(lb.applied) | {c for it in lb.items for c in it.cites}
    questions = []
    q = run_dir / "questions.json"
    if q.exists():
        d = json.loads(q.read_text(encoding="utf-8"))
        questions = [(x["key"], x.get("prompt", "")) for x in d.get("questions", [])]
        for rg in (d.get("plan") or {}).get("regions", []):
            for c in rg.get("conditions", []):
                questions.append((c[0], c[1]))
    g = template.build(event, case.present, case) if case.present or not case.transactions else best.graph
    from .rules.tri import DISCRETION
    judgements = sorted({"%s on %s" % (n.key, grp[0]) for grp, ns in best.b.groups.items() for n in ns if n.source == DISCRETION})
    return sorted(r for r in rids if r in {x.id for x in RULES}), questions, g, judgements


def _json(text):
    m = re.search(r"\{.*\}", text, re.S)
    try:
        return json.loads(m.group(0)) if m else {}
    except ValueError:
        return {}


def vote(case_path: Path, run_dir: Path, model="qwen3.8-flash", voters=3, temperature=0.7):
    case = json.loads(case_path.read_text(encoding="utf-8"))
    from .pipeline import find_docs
    docs = find_docs(case, None)
    rids, questions, graph, judgements = fixed_logic(case_path, run_dir)
    b = brief(case, docs, graph)
    P = _params()
    rules_text = ("\n".join("- " + rule_text(r, P) for r in rids) or "- none") + "\nChecked on every case, whether or not they produced a tax here:\n" + always_checked()
    rules_text += "\nJudgements the program leaves to the tax authority on this case (each is a condition of a rule above; the program computes the tax both ways and asks for a ruling):\n" + ("\n".join("- " + j for j in judgements) or "- none")
    q_text = "\n".join("- %s: %s" % kq for kq in questions) or "- none"
    angles = list(ANGLES.items())[:voters]
    llm = DeepSeek(model, temperature=temperature)

    def one(angle):
        name, text = angle
        issues = _json(llm(ISSUE_PROMPT.format(angle=text, brief=b))).get("issues") or []
        issues = [i for i in issues if isinstance(i, dict) and i.get("issue")]
        listed = "\n".join("%d. [%s %s %s] %s (basis: %s)" % (k + 1, i.get("jurisdiction"), i.get("kind"), i.get("flow"), i.get("issue"), i.get("basis")) for k, i in enumerate(issues)) or "none"
        marks = _json(llm(MATCH_PROMPT.format(issues=listed, rules=rules_text, questions=q_text))).get("marks") or []
        by_n = {m.get("n"): m for m in marks if isinstance(m, dict)}
        for k, i in enumerate(issues, 1):
            m = by_n.get(k, {})
            i["covered"] = bool(m.get("covered", False))
            i["by"] = m.get("by", "")
            i["why"] = m.get("why", "")
        return name, issues

    t0 = time.time()
    with ThreadPoolExecutor(max_workers=voters) as pool:
        results = dict(pool.map(one, angles))
    # the vote: a gap is (jurisdiction, kind, flow) marked missing by a majority
    tally = defaultdict(list)
    for name, issues in results.items():
        for i in issues:
            if not i["covered"]:
                tally[(str(i.get("jurisdiction")), str(i.get("kind")), str(i.get("flow")))].append((name, i))
    need = voters // 2 + 1
    gaps = [{"jurisdiction": k[0], "kind": k[1], "flow": k[2], "votes": len(v), "voters": [n for n, _ in v],
             "issues": [{"voter": n, "issue": i["issue"], "basis": i.get("basis", ""), "depends_on": i.get("depends_on", "")} for n, i in v]}
            for k, v in tally.items() if len(v) >= need]
    minority = [{"jurisdiction": k[0], "kind": k[1], "flow": k[2], "votes": len(v), "issues": [i["issue"] for _, i in v]} for k, v in tally.items() if len(v) < need]
    mentioned = {x for issues in results.values() for i in issues for x in re.split(r"[,\s;]+", str(i.get("by", ""))) if x}
    unconfirmed = [r for r in rids if r not in mentioned]
    return {"case": case_path.name, "run": str(run_dir), "model": model, "voters": [n for n, _ in angles], "seconds": round(time.time() - t0, 1),
            "usage": llm.usage, "fixed_logic": {"rules": rids, "questions": [k for k, _ in questions], "judgements": judgements},
            "gaps": sorted(gaps, key=lambda g: -g["votes"]), "minority": minority, "unconfirmed_rules": unconfirmed,
            "readings": {n: issues for n, issues in results.items()},
            "maintenance": {"agent": MAINTENANCE_AGENT, "proposals": [{"what": "rule, parameter or field for %s %s on %s" % (g["jurisdiction"], g["kind"], g["flow"]),
                                                                        "basis": sorted({i["basis"] for i in g["issues"] if i["basis"]}), "status": "proposed"} for g in gaps]}}


def render(d: dict) -> str:
    L = ["# Discovery by vote: %s" % d["case"], "",
         "Model %s, voters %s, %.0f s. Fixed logic: %d rules applied, %d questions." % (d["model"], ", ".join(d["voters"]), d["seconds"], len(d["fixed_logic"]["rules"]), len(d["fixed_logic"]["questions"])), ""]
    L += ["## Gaps (majority says the program did not cover it)", ""]
    for g in d["gaps"]:
        L.append("- **%s %s on %s** (%d of %d votes)" % (g["jurisdiction"], g["kind"], g["flow"], g["votes"], len(d["voters"])))
        for i in g["issues"]:
            L.append("  - %s: %s [%s]%s" % (i["voter"], i["issue"], i["basis"], (" depends on " + i["depends_on"]) if i["depends_on"] else ""))
    if not d["gaps"]:
        L.append("- none")
    L += ["", "## Minority (one voter only; not a gap)", ""] + ["- %s %s on %s: %s" % (m["jurisdiction"], m["kind"], m["flow"], "; ".join(m["issues"])) for m in d["minority"]] or ["- none"]
    L += ["", "## Rules applied that no voter named as covering an issue", ""] + (["- " + r for r in d["unconfirmed_rules"]] or ["- none"])
    L += ["", "## Proposals (maintenance agent %s)" % ("on" if d["maintenance"]["agent"] else "off: written, not applied"), ""]
    L += ["- %s; basis: %s" % (p["what"], "; ".join(p["basis"]) or "none given") for p in d["maintenance"]["proposals"]] or ["- none"]
    return "\n".join(L) + "\n"


def main(argv):
    out = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    opt = lambda k, d=None: argv[argv.index(k) + 1] if k in argv else d
    case_path = Path(argv[1])
    run_dir = Path(opt("--run") or (ROOT / "out" / "pipeline" / case_path.stem / "discovery"))
    run_dir.mkdir(parents=True, exist_ok=True)
    d = vote(case_path, run_dir, model=opt("--model", "qwen3.8-flash"), voters=int(opt("--voters", 3)))
    (run_dir / "discovery.json").write_text(json.dumps(d, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    (run_dir / "DISCOVERY.md").write_text(render(d), encoding="utf-8")
    out.write(render(d))
    out.write("[written to %s]\n" % run_dir)
    out.flush()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
