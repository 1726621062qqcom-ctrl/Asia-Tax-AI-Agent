# -*- coding: utf-8 -*-
"""案例校验 (案例采集.md §3, step 5): a case file before it is used.

    python -m tax_graph.verify.casecheck CASE.json [CASE.json ...]

- format: the file loads, its template builds the present structure and every candidate;
- provenance (案例采集.md §4.2): every stated value has one — disclosed (with a quote), derived (with a formula),
  synthetic (test only, K3), missing (then the value is absent); a real case (K4-K6) carries no synthetic value;
- dates against law versions: each flow's date against the current rules that speak to it. Before a law the library
  starts from (口径 D30) the levy is outside the library; before any other rule's commencement the rule is either a regime
  that did not exist yet or a version the library does not keep — listed for a person to settle;
- the registry (cases/registry.csv): the case is registered and its id is unique.
Exit 1 when any case has an error."""
import csv
import io
import json
import re
import sys
from pathlib import Path

from ..engine import RULES, flow_of
from ..facts import facts_for
from ..rules.eval import levy_view, matches, seen_by
from ..quotes import loose
from ..run import load_case

ROOT = Path(__file__).resolve().parents[2]
REGISTRY = ROOT / "cases" / "registry.csv"
KINDS = {"K3": "半合成结构", "K4": "交易通函", "K5": "机关公布的脱敏案例", "K6": "私有案例"}
PROV_KINDS = ("disclosed", "derived", "synthetic", "missing")


_SOURCES = {}


def source_text(source):
    """The archived text of a source (cases/sources/<source>/source.txt), loosely normalised; None when not archived."""
    if source not in _SOURCES:
        p = ROOT / "cases" / "sources" / source / "source.txt"
        _SOURCES[source] = loose(p.read_text(encoding="utf-8")) if source and p.exists() else None
    return _SOURCES[source]


def stated_paths(d):
    """Every value the case states, as the provenance path that names it."""
    out = {}
    for role, rf in d.get("roles", {}).items():
        out["roles.%s.loc" % role] = rf.get("loc")
        for k, v in rf.get("attrs", {}).items():
            out["roles.%s.attrs.%s" % (role, k)] = v
    for h in d.get("holds", []):
        for k in ("ratio", "since", "cost"):
            if h.get(k) is not None:
                out["holds.%s>%s.%s" % (h["holder"], h["held"], k)] = h[k]
    for fid, facts in d.get("flows", {}).items():
        for k, v in facts.items():
            out["flows.%s.%s" % (fid, k)] = v
    for k, v in d.get("event", {}).items():
        out["event.%s" % k] = v
    for fid, paid in d.get("settled", {}).items():
        for jur, v in paid.items():
            out["settled.%s.%s" % (fid, jur)] = v
    for k, v in d.get("present", {}).items():
        out["present.%s" % k] = v
    return out


def check(path, registry):
    d = json.loads(Path(path).read_text(encoding="utf-8"))
    cid = d.get("case_id") or Path(path).stem
    errors, warns, notes = [], [], []
    kind = d.get("kind")
    if kind not in KINDS:
        warns.append("未标案例种类（K3–K6，案例采集.md §1）")
    # format and template fit
    try:
        template, case, event, subject, ticks, _ = load_case(path)
        graphs = [template.build(event, case.present, case)] if case.present else []
        graphs += [template.build(event, a, case) for a in template.candidates(event, case)]
    except Exception as e:                                  # noqa: BLE001 — any failure here is a format error
        errors.append("读不进来或模板装不下：%s: %s" % (type(e).__name__, e))
        return cid, errors, warns, notes
    notes.append("模板 %s，候选 %d 个" % (template.name, len(graphs)))
    # provenance
    prov = d.get("provenance") or {}
    stated = stated_paths(d)
    if kind in KINDS:
        bare = sorted(p for p in stated if p not in prov)
        if bare:
            errors.append("%d 个陈述的值没有出处：%s" % (len(bare), "、".join(bare[:8]) + ("…" if len(bare) > 8 else "")))
        unarchived = {}
        # every quote, whatever the kind, must be in the archived source (cases/sources/<source>); so must the quote
        # behind the company's own estimate, which the case is compared with (案例采集.md §7)
        quoted = [(p, e) for p, e in prov.items() if (e or {}).get("quote")]
        est = d.get("company_estimate") or {}
        if est.get("quote"):
            srcs = [e.get("source") for e in prov.values() if (e or {}).get("source")]
            quoted.append(("company_estimate", dict(est, source=est.get("source") or max(set(srcs), key=srcs.count, default=""))))
        for p, e in quoted:
            text = source_text(e.get("source", ""))
            if text is None:
                unarchived.setdefault(e.get("source"), []).append(p)
            elif loose(e["quote"]) not in text:
                errors.append("%s 的引文在来源 %s 里找不到" % (p, e.get("source")))
        for src, ps in sorted(unarchived.items(), key=lambda x: str(x[0])):
            warns.append("来源 %s 没有存档（cases/sources/），%d 条引文未核：%s" % (src, len(ps), "、".join(ps[:4]) + ("…" if len(ps) > 4 else "")))
        for p, e in prov.items():
            k = (e or {}).get("kind")
            if k not in PROV_KINDS:
                errors.append("%s 的出处种类无效：%s" % (p, k))
            elif k == "disclosed" and not e.get("quote"):
                errors.append("%s 标为披露但没有引文" % p)
            elif k == "derived" and not e.get("formula"):
                errors.append("%s 标为推导但没有算式" % p)
            elif k == "synthetic" and kind != "K3":
                errors.append("%s 是合成值，真实案例（%s）不能有合成值" % (p, kind))
            elif k == "missing" and p in stated:
                errors.append("%s 标为缺失却给了值" % p)
        syn = sum(1 for p in stated if (prov.get(p) or {}).get("kind") == "synthetic")
        if kind == "K3":
            notes.append("合成值 %d/%d（%.0f%%）" % (syn, len(stated), 100.0 * syn / max(1, len(stated))))
            if d.get("synthetic_share") is not None and abs(float(d["synthetic_share"]) - syn / max(1, len(stated))) > 0.01:
                warns.append("synthetic_share 与实际合成比例不符")
    # dates against law versions
    outside, unsure = set(), set()
    for g in graphs:
        for f in g.flows:
            if f.on is None or f.payer not in g.entities or f.payee not in g.entities:
                continue
            fl = flow_of(g, f, facts_for(g, f))
            lv = levy_view(fl)
            for r in RULES:
                lo = r.valid[0]
                if lo is not None and f.on < lo and matches(r.scope, seen_by(r, fl, lv)):
                    (outside if r.before else unsure).add((f.id, f.on.isoformat(), r.id, lo.isoformat()))
    if outside:
        warns.append("早于所依法律施行日、税项在库外（口径 D30）：%s" % "；".join(
            "%s（%s）%s 自 %s" % x for x in sorted(outside)[:6]))
    if unsure:
        warns.append("早于这些现行规则的施行日，需确认是当时尚无此制度还是旧版本未入库：%s" % "；".join(
            "%s（%s）%s 自 %s" % x for x in sorted(unsure)[:6]) + ("…" if len(unsure) > 6 else ""))
    # registry
    rows = [r for r in registry if r["case_id"] == cid]
    if not rows:
        warns.append("未在 cases/registry.csv 登记")
    elif len(rows) > 1:
        errors.append("cases/registry.csv 里 case_id 重复")
    return cid, errors, warns, notes


def main(argv):
    out = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    registry = []
    if REGISTRY.exists():
        with open(str(REGISTRY), encoding="utf-8-sig", newline="") as f:
            registry = list(csv.DictReader(f))
    bad = 0
    for path in argv[1:]:
        cid, errors, warns, notes = check(path, registry)
        bad += bool(errors)
        out.write("%s %s（%s）\n" % ("错误" if errors else "通过", cid, "；".join(notes)))
        for e in errors:
            out.write("  错误：%s\n" % e)
        for w in warns:
            out.write("  警示：%s\n" % w)
    out.flush()
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
