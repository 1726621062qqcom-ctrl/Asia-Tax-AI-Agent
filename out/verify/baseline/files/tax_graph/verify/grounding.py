# -*- coding: utf-8 -*-
"""依据核对 — the 测试系统 (测试系统.md) in miniature: every step of the plan the planner produces, traced to its basis.

    python -m tax_graph.verify.grounding CASE.json [CASE.json ...] [--answers ANSWERS.json] [--gold]

Steps: each tax item on both ends of the chosen plan, each plan action, judgement and deadline it relies on; for a
question sheet, the same for the candidate the planner would choose so far, and each question. A step's basis: the
rules that make it; their parameters — in params.csv, in force on the flow's date, the quote found verbatim in the cited
clause of the current clause layer; the clauses their judgements and evaluators cite and the law they start from
(口径 D30); the 口径 decisions that read the rule, their anchors found verbatim; and the facts the rules read, by where
each came from. The totals are re-added from the items and recomputed once. Everything is read from the files, not
taken from the engine's or the build's own checks. Writes out/<name>.grounding.md and out/verify/grounding_<name>.jsonl
(one result per line, 测试系统.md §5)."""
import csv
import hashlib
import io
import json
import re
import sys
import time
from fnmatch import fnmatch
from pathlib import Path

from .. import engine as E
from ..cases import SCENARIOS
from ..engine import PEM_RULE, RULES, RULES_BY_ID, bounds, flow_name, outside_steps
from ..facts import facts_for
from ..params import Params
from ..planner import Answers, _ctx_of, _field_of, _key, plan
from ..precedent import analyse, load as precedent_cards
from ..rules.eval import INCLUSIVE_BY_FACT, PROCEDURE_MODULES, SHARED_GROUPS, levy_view, matches, seen_by, valid_on
from ..rules.model import PROCEDURE, Discretion, Leaf, leaves
from ..rules.tri import DISCRETION, PLAN, STRUCTURAL
from ..run import load_case
from ..scenarios import TEMPLATES

ROOT = Path(__file__).resolve().parents[2]
OFF, OUT = ROOT / "official", ROOT / "out"
EPS = 0.01
RANK = {"pass": 0, "info": 0, "warn": 1, "fail": 2}
WORD = {"pass": "通过", "info": "说明", "warn": "警示", "fail": "失败"}
# the clauses a decision without a rule of its own rests on
GROUP_CLAUSES = {PEM_RULE: ("cn.gsf.2009-82#i2",)}             # 国税发〔2009〕82号 第二条: residence by effective management


def norm(s):
    return re.sub(r"\s+", "", s or "")


def worst(statuses):
    return max(statuses, key=lambda s: RANK[s], default="pass")


def _csv(path):
    csv.field_size_limit(10 ** 9)
    with open(str(path), encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def short(s, n=36):
    s = " ".join((s or "").split())
    return s if len(s) <= n else s[:n] + "…"


class Library:
    """What the checks read, straight from the files: the current clause layer, the documents, the 口径 decisions,
    the rules seen only in official tools."""

    def __init__(self):
        self.clauses = {r["cite_id"]: r for r in _csv(OFF / "clauses.csv")}
        self.docs = {r["id"]: r for r in _csv(OFF / "manifest.csv")}
        self.decisions = {}
        for r in _csv(OFF / "decisions.csv"):
            d = self.decisions.setdefault(r["id"], {"used_in": "", "anchors": []})
            d["used_in"] = d["used_in"] or r.get("used_in", "")
            d["anchors"].append((r["cite_id"], r["quote"]))
        self.observed = {r["rule_id"] for r in _csv(OFF / "labels" / "observed_rules.csv")}

    def title(self, doc_id):
        d = self.docs.get(doc_id, {})
        return "%s %s" % (d.get("title", doc_id), d.get("doc_no", "")) if d else doc_id

    def decisions_for(self, rid):
        """口径 decisions whose used_in names the rule in a spec file (an id, or a pattern such as cn.vat.law.*)."""
        out = []
        for did, d in self.decisions.items():
            for part in d["used_in"].split(";"):
                path, _, names = part.strip().partition(":")
                if "rules/spec" in path and any(n.strip() == rid or ("*" in n and fnmatch(rid, n.strip())) for n in names.split(",")):
                    out.append(did)
                    break
        return sorted(out)


REG_CITES = {rid: tuple(entry[2]) for m in PROCEDURE_MODULES for rid, entry in m.REGISTRY.items() if len(entry) > 2 and entry[2]}


class Basis:
    """A rule's basis on a date: each part with a status. Memoised per (rule, date)."""

    def __init__(self, lib, P):
        self.lib, self.P, self.memo = lib, P, {}

    def clause(self, cid, kind):
        cl = self.lib.clauses.get(cid)
        if cl is None:
            return {"kind": kind, "id": cid, "status": "fail", "note": "不在现行条款层（不存在、已被取代或已废止）"}
        return {"kind": kind, "id": cid, "status": "pass", "note": self.lib.title(cl["doc_id"])}

    def param(self, pid, role, on):
        row = self.P.rows.get(pid)
        if row is None:
            return {"kind": "参数", "id": pid, "status": "fail", "note": "不在 params.csv"}
        cid, q = row.get("cite_id", ""), row.get("quote", "")
        cl = self.lib.clauses.get(cid)
        if cl is None:
            return {"kind": "参数", "id": pid, "status": "fail", "note": "所引条款 %s 不在现行条款层" % cid}
        if q and norm(q) not in norm(cl["text"]):
            return {"kind": "参数", "id": pid, "status": "fail", "note": "引文在 %s 里找不到" % cid}
        lo, hi, d = row.get("effective_from") or "", row.get("effective_to") or "", on.isoformat() if on else ""
        if d and ((lo and d < lo) or (hi and d > hi)):
            return {"kind": "参数", "id": pid, "status": "warn" if role == "uses" else "fail",
                    "note": "%s 不在其有效期 %s～%s" % (d, lo or "…", hi or "…")}
        return {"kind": "参数", "id": pid, "status": "pass",
                "note": "%s = %s %s；%s（%s）「%s」" % (role, row.get("value"), row.get("unit"), cid, self.lib.title(cl["doc_id"]), short(q))}

    def decision(self, did):
        anchors = self.lib.decisions[did]["anchors"]
        bad = [cid for cid, q in anchors
               if cid not in self.lib.clauses or (q and norm(q) not in norm(self.lib.clauses[cid]["text"]))]
        return {"kind": "口径", "id": did, "status": "fail" if bad else "pass",
                "note": "锚点 %d/%d 找到原文%s" % (len(anchors) - len(bad), len(anchors), ("；找不到：" + "、".join(bad)) if bad else "")}

    def rule(self, r, on):
        key = (r.id, on)
        if key in self.memo:
            return self.memo[key]
        parts = []
        lo, hi = r.valid
        if on is not None and ((lo and on < lo) or (hi and on > hi)):
            parts.append({"kind": "有效期", "id": r.id, "status": "fail", "note": "%s 不在规则有效期 %s～%s" % (on, lo or "…", hi or "…")})
        if r.value and r.value.startswith("observed:"):
            oid = r.value.split(":", 1)[1]
            parts.append({"kind": "官方工具观察", "id": oid, "status": "pass" if oid in self.lib.observed else "fail",
                          "note": "labels/observed_rules.csv"})
        elif r.value:
            parts.append(self.param(r.value, "value", on))
        for c in (r.cond,) + tuple(r.readings):
            for x in leaves(c):
                if isinstance(x, Leaf) and x.param:
                    parts.append(self.param(x.param, "threshold", on))
                elif isinstance(x, Discretion):
                    if not x.cites:
                        parts.append({"kind": "判断出处", "id": x.key, "status": "warn", "note": "该判断未引条款"})
                    parts += [self.clause(cid, "判断出处") for cid in x.cites]
        parts += [self.param(pid, "uses", on) for pid in r.uses]
        parts += [self.clause(cid, "求值器出处") for cid in REG_CITES.get(r.id, ())]
        if r.before:
            parts.append(self.clause(r.before[1], "所依法律的施行条款"))
        parts += [self.decision(did) for did in self.lib.decisions_for(r.id)]
        seen, uniq = set(), []
        for p in parts:
            if (p["kind"], p["id"]) not in seen:
                seen.add((p["kind"], p["id"]))
                uniq.append(p)
        if not uniq:
            uniq.append({"kind": "依据", "id": r.id, "status": "warn", "note": "规则没有参数、条款或口径"})
        self.memo[key] = (worst(p["status"] for p in uniq), uniq)
        return self.memo[key]


def group_rules(grp):
    """The rules behind a decision group: its own rule; for the shared price decision the rules reading it; for an
    engine-stage group the rules of that stage; a datum (an amount, a holding) has none of its own."""
    rid = grp[0]
    if rid in RULES_BY_ID:
        return [RULES_BY_ID[rid]]
    if rid in SHARED_GROUPS:
        return [r for r in RULES if any(m in r.uses for m in INCLUSIVE_BY_FACT)]
    if rid == "data.cfc_profit":
        return [RULES_BY_ID["cn.cfc.charge"]]
    if rid.startswith("data.p2"):
        rs = [r for r in RULES if ".p2." in r.id and r.scope.taxing == grp[1]]
        return rs or [r for r in RULES if ".p2." in r.id]
    return []


def version():
    h = hashlib.sha256()
    for p in sorted((ROOT / "tax_graph").rglob("*.py")):
        h.update(p.read_bytes())
    for name in ("params.csv", "clauses.csv", "decisions.csv"):
        h.update((OFF / name).read_bytes())
    return h.hexdigest()[:12]


def check_case(name, template, case, event, answers, lib, P, provenance=None):
    """Runs the planner on the case and traces its plan (or its best candidate so far). Returns (report, records)."""
    t0 = time.time()
    ver, run_id = version(), time.strftime("%Y%m%dT%H%M%S") + "-" + name
    recs, issues = [], []
    basis = Basis(lib, P)

    def rec(check_id, subject, status, measured="", expected="", evidence="", msg=""):
        recs.append({"run_id": run_id, "layer": "依据", "check_id": check_id, "subject": subject, "status": status,
                     "measured": measured, "expected": expected, "oracle": "official", "evidence": evidence, "version": ver})
        if status in ("warn", "fail"):
            issues.append((status, subject, msg or ("%s（应为 %s）" % (measured, expected) if expected else measured)))

    outcome = plan(template, event, case, answers, P)
    if outcome.plan is not None:
        best, mode = next(e for e in outcome.evaluations if e.cand == outcome.plan["cand"]), "方案"
    else:
        open_ = [e for e in outcome.evaluations if not e.excluded]
        best, mode = (min(open_, key=_key) if open_ else None), "问卷"
    L = ["# 依据核对：%s" % name, ""]
    if best is None:
        rec("G-plan", name, "fail", outcome.note or "没有可评估的候选")
        L += ["没有可评估的候选：%s" % (outcome.note or "")]
        return "\n".join(L) + "\n", recs
    g = best.graph
    members = g.group()
    # 1. recompute the chosen candidate once, recording the facts each flow was evaluated with
    seen = {}
    real = E.cached_evaluate

    def spy(rules, ctx, flow, bound, P_, force, amount):
        seen.setdefault(flow.id, {}).update(ctx.facts)
        return real(rules, ctx, flow, bound, P_, force, amount)

    E.cached_evaluate = spy
    try:
        b = bounds(g, _ctx_of(best.ticks), P, settled=case.settled, as_at=event.as_at, closed=case.closed, ticks=best.ticks)
    finally:
        E.cached_evaluate = real
    same = abs(b.hi - best.b.hi) <= EPS and abs(b.lo - best.b.lo) <= EPS
    rec("G-recompute", name, "pass" if same else "fail", "%.2f / %.2f" % (b.hi, b.lo), "%.2f / %.2f" % (best.b.hi, best.b.lo))
    if mode == "方案":
        steps = list(g.unmodelled) + outside_steps(b, g)[0]
        rec("G-modelled", name, "fail" if steps else "pass", "；".join(str(x) for x in steps) or "无未建模步骤、无库外税项")
    # 2. tax items, both ends; the totals re-added from them
    rules_used, item_rows = {}, []
    for side, labels, total in (("保证", b.L_hi, b.hi), ("最好", b.L_lo, b.lo)):
        added = 0.0
        for fid, lb in labels.items():
            for it in lb.items:
                if not it.effective or it.deferred:
                    continue
                amt = lb.flow.amount * it.effective / 100.0
                who = lb.flow.payer if it.borne_by == "payer" else lb.flow.payee
                if who in members:
                    added += amt
                rids = list(dict.fromkeys(c for c in it.cites if c in RULES_BY_ID))
                odd = [c for c in dict.fromkeys(it.cites) if c not in RULES_BY_ID]
                sts = [basis.rule(RULES_BY_ID[c], lb.flow.on)[0] for c in rids]
                st = worst(sts + (["fail"] if not rids or odd else []))
                for c in rids:
                    rules_used.setdefault(c, set()).add(lb.flow.on)
                subj = "%s/%s/%s/%s/%s" % (side, fid, it.jur, it.levy, who)
                rec("G-item", subj, st, "%.2f" % amt, "", "、".join(rids + odd))
                if side == "保证":
                    item_rows.append((fid, it.jur, it.levy, who if who in members else who + "（集团外）", "%.2f" % amt,
                                      "、".join(rids + ["未知引用 " + c for c in odd]), WORD[st]))
        ok = abs(added - total) <= EPS
        rec("G-total", "%s/%s" % (name, side), "pass" if ok else "fail", "%.2f" % added, "%.2f" % total)
    # 3. plan actions, judgements, deadlines
    act_rows, judge_rows, dl_rows = [], [], []
    cards = precedent_cards()

    def precedent_text(r, key, fid):
        """案例采集.md §5: what the precedents say on this judgement, on the facts the flow was evaluated with."""
        if r is None:
            return "—"
        issue = "%s:%s" % (r.scope.taxing, _field_of(key))
        if issue not in cards[1]:
            return "无先例卡"
        a = analyse(issue, seen.get(fid, {}), *cards)
        rec("G-precedent", "%s@%s" % (issue, fid), "info", a.forced or ("冲突" if a.conflict else "未被压住"), "", a.by)
        if a.forced:
            return "被先例 %s 压住：%s" % (a.by, "成立" if a.forced == "true" else "不成立")
        parts = ["%s最近的先例 %s（还差 %s%s）" % ("成立" if side == "true" else "不成立", pid, "、".join(miss) or "无",
                                            "；多出不利 " + "、".join(way) if way else "")
                 for side, (pid, miss, way) in sorted(a.nearest.items())]
        return ("先例冲突；" if a.conflict else "未被压住；") + "；".join(parts)

    def group_basis(grp):
        on = (b.L_hi.get(grp[1]).flow.on if isinstance(grp[1], str) and grp[1] in b.L_hi else event.on)
        rs = group_rules(grp)
        sts = []
        for r in rs:
            sts.append(basis.rule(r, on)[0])
            rules_used.setdefault(r.id, set()).add(on)
        sts += [basis.clause(cid, "条款")["status"] for cid in GROUP_CLAUSES.get(grp[0], ())]
        return worst(sts) if sts else "info", "、".join([r.id for r in rs] + list(GROUP_CLAUSES.get(grp[0], ()))) or "数据（由流本身的规则要求）"

    for ak, (grp, n) in sorted(best.plan_keys.items()):
        if (PLAN, ak) not in {(t.source, t.key) for t in best.ticks}:
            continue
        st, why = group_basis(grp)
        rec("G-action", ak, st, "", "", why)
        act_rows.append((ak, why, WORD[st]))
    done = set()
    for grp, ns in sorted(b.groups.items(), key=lambda kv: (str(kv[0][0]), str(kv[0][1]))):
        for n in ns:
            if n.source != DISCRETION or (grp[0], n.key) in done:
                continue
            done.add((grp[0], n.key))
            st, why = group_basis(grp)
            r = RULES_BY_ID.get(grp[0])
            cites = list(dict.fromkeys(c for x in (leaves(r.cond) if r else []) if isinstance(x, Discretion)
                                       and x.key == _field_of(n.key) for c in x.cites))
            if r is not None and not cites:
                st = worst([st, "warn"])
            rec("G-judgement", "%s@%s" % (n.key, grp[1]), st, "", "", "、".join(cites) or why,
                msg="" if cites or r is None else "判断事项没有引条款")
            judge_rows.append((n.key, grp[1], "、".join(cites) or "—", why, WORD[st], precedent_text(r, n.key, grp[1])))
    for fid, lb in b.L_hi.items():
        for rid in dict.fromkeys(lb.applied):
            r = RULES_BY_ID.get(rid)
            if r is None or r.effect not in PROCEDURE:
                continue
            st = basis.rule(r, lb.flow.on)[0]
            rules_used.setdefault(rid, set()).add(lb.flow.on)
            rec("G-deadline", "%s/%s" % (fid, rid), st, "", "", rid)
            dl_rows.append((fid, rid, WORD[st]))
        for nm, gap in (lb.gaps or {}).items():
            rec("G-calendar", "%s/%s" % (fid, nm), "warn", "缺 %s %d 年的假期表，期限按名义日期" % gap,
                msg="期限按名义日期：库里缺 %s %d 年的公众假期表" % gap)
    # 4. questions of a question sheet
    q_rows = []
    for q in outcome.questions:
        rs = list({r.id: r for x in q.why for r in group_rules((x, None))}.values())
        sts = [basis.rule(r, event.on)[0] for r in rs]
        st = worst(sts) if sts else "info"
        rec("G-question", q.key, st, q.kind, "", "、".join(x for x in q.why))
        q_rows.append((q.kind, q.key, "、".join(q.why) or "—", WORD[st]))
    # 5. the facts the applied rules read, by where each came from
    stated_n = provenanced = 0
    fact_rows = []
    open_by_flow = {}
    for grp, ns in b.groups.items():
        open_by_flow.setdefault(grp[1], set()).update(_field_of(n.key) for n in ns)
    ticked = {_field_of(t.key) for t in best.ticks if t.source == PLAN}
    for fid, lb in sorted(b.L_hi.items()):
        f = lb.flow
        if f is None or f.payer not in g.entities or f.payee not in g.entities:
            continue
        try:
            static = facts_for(g, f)
        except Exception:                                     # noqa: BLE001 — a pseudo-flow the facts reader does not serve
            static = {}
        fk = f.attrs.get("fact_key") or flow_name(f.id)
        by_cls = {}
        # every rule that speaks to this flow on its date reads them — those that did not apply too: what kept a rule
        # from applying is as much a basis of the result as what made another apply
        fl = E.flow_of(g, f, seen.get(f.id) or static)
        lv = levy_view(fl)
        reads = sorted({fp for r in RULES if matches(r.scope, seen_by(r, fl, lv)) and valid_on(r, f.on) for fp in r.reads})
        for fp in reads:
            on_, _, fld = fp.partition(".")
            ent = g.entities.get(f.payer if on_ == "payer" else f.payee) if on_ in ("payer", "payee") else None
            akeys = ({"flow:%s.%s" % (fk, fld), "flow:%s.%s" % (flow_name(f.id), fld)} if on_ == "flow"
                     else {"%s.%s" % (ent.id, fld), "group.%s" % fld} if ent is not None else set())
            if fld in ticked:
                cls = "方案动作"
            elif fld in open_by_flow.get(f.id, ()):
                cls = "未定（按两端计）"
            elif akeys & set(answers.data):
                cls = "答复"
            elif (on_ == "flow" and fld in case.flows.get(fk, case.flows.get(flow_name(f.id), {}))) or \
                    (ent is not None and ent.id in case.roles and fld in case.roles[ent.id].attrs):
                stated_n += 1
                path = ("flows.%s.%s" % (fk, fld)) if on_ == "flow" else "roles.%s.attrs.%s" % (ent.id, fld)
                if provenance and path in provenance:
                    provenanced += 1
                    cls = "陈述（有出处）"
                else:
                    cls = "陈述"
            elif (ent is not None and ent.attrs.get("placed_by_plan") and fld in ent.attrs) or (on_ == "flow" and fld in f.attrs):
                cls = "设计或模板设定"
            elif (on_, fld) in static:
                cls = "推导（facts.py）"
            elif (on_, fld) in seen.get(f.id, {}):
                cls = "推导（引擎）"
            elif fld in STRUCTURAL:
                cls = "结构性缺省（按否）"
            else:
                cls = "未给出（规则判为不影响结果）"
            by_cls.setdefault(cls, []).append(fp)
        for cls, fps in sorted(by_cls.items()):
            rec("G-fact", "%s/%s" % (fid, cls), "info", str(len(fps)), "", "、".join(fps))
        fact_rows.append((fid, by_cls))
    rec("G-provenance", name, "info" if stated_n == 0 or provenanced == stated_n else "warn",
        "%d/%d" % (provenanced, stated_n), "陈述的事实都附出处（案例采集.md §4.2）",
        msg="案例陈述的事实 %d 个，附出处的 %d 个（案例文件没有 provenance，见 案例采集.md §4.2）" % (stated_n, provenanced))
    # 6. the rules this plan uses, with their basis
    rule_rows = []
    for rid in sorted(rules_used):
        for on in sorted(d for d in rules_used[rid] if d is not None) or [None]:
            st, parts = basis.rule(RULES_BY_ID[rid], on)
            rec("G-rule", "%s@%s" % (rid, on), st, "", "", "；".join("%s %s" % (p["kind"], p["id"]) for p in parts))
            rule_rows.append((rid, on, RULES_BY_ID[rid].grade.name if RULES_BY_ID[rid].grade else "", st, parts))
    secs = time.time() - t0
    for r in recs:
        r["seconds"] = round(secs, 1)
    # report
    n_by = {s: sum(1 for r in recs if r["status"] == s) for s in ("pass", "info", "warn", "fail")}
    legal = [r for r in recs if r["check_id"] not in ("G-fact", "G-provenance", "G-calendar")]
    L += ["运行 %s，版本 %s。%s；核对 %d 项：通过 %d，说明 %d，警示 %d，失败 %d。" % (
        run_id, ver, "规划器给出了方案" if mode == "方案" else "规划器给出的是问卷（下面核对的是目前最优的候选）",
        len(recs), n_by["pass"], n_by["info"], n_by["warn"], n_by["fail"]), ""]
    L += ["**结论**：%s；%s。" % (
        "每一步都落到现行条文的原文" if not any(r["status"] == "fail" for r in legal) else "有步骤缺少现行条文依据（见下）",
        "没有用到案例陈述的事实" if stated_n == 0 else "陈述的事实都附出处" if stated_n == provenanced
        else "陈述的事实未附出处（%d/%d）" % (provenanced, stated_n)), ""]
    L += ["候选 %s；保证税额 %.2f，最好情形 %.2f；重算%s。" % (best.cand, b.hi, b.lo, "一致" if same else "不一致"), ""]
    if issues:
        L += ["## 需要处理的", ""] + ["- %s：%s %s" % (WORD[s], subj, short(m, 120)) for s, subj, m in issues] + [""]
    L += ["## 税项（保证税额一端）", "", "| 流 | 法域 | 税种 | 承担方 | 金额 | 规则 | 依据 |", "|---|---|---|---|---|---|---|"]
    L += ["| %s |" % " | ".join(row) for row in item_rows] + [""]
    if act_rows:
        L += ["## 方案动作", "", "| 动作 | 依据所在的规则 | 依据 |", "|---|---|---|"] + ["| %s |" % " | ".join(r) for r in act_rows] + [""]
    if judge_rows:
        L += ["## 待机关认可的判断", "", "| 事项 | 流 | 判断所引条款 | 规则 | 依据 | 先例（案例采集.md §5） |", "|---|---|---|---|---|---|"]
        L += ["| %s |" % " | ".join(str(x) for x in r) for r in judge_rows] + [""]
    if dl_rows:
        L += ["## 期限与罚款", "", "| 流 | 规则 | 依据 |", "|---|---|---|"] + ["| %s |" % " | ".join(r) for r in dl_rows] + [""]
    if q_rows:
        L += ["## 问卷的每个问题", "", "| 类别 | 问题 | 由哪条规则提出 | 依据 |", "|---|---|---|---|"]
        L += ["| %s |" % " | ".join(r) for r in q_rows] + [""]
    L += ["## 规则依据（本方案用到的 %d 条规则）" % len(rules_used), ""]
    for rid, on, grade, st, parts in rule_rows:
        L.append("- **%s**（%s，%s）%s" % (rid, grade, on or "—", WORD[st]))
        L += ["  - %s %s：%s%s" % (p["kind"], p["id"], p["note"], "" if p["status"] == "pass" else "（%s）" % WORD[p["status"]])
              for p in parts]
    L += ["", "## 事实来源（规则读到的事实，按流）", ""]
    for fid, by_cls in fact_rows:
        L.append("- %s：%s" % (fid, "；".join("%s %d（%s）" % (cls, len(v), "、".join(x.split(".", 1)[1] for x in v[:6]) + ("…" if len(v) > 6 else ""))
                                             for cls, v in sorted(by_cls.items()))))
    L += ["", "陈述的事实 %d 个，附出处 %d 个。" % (stated_n, provenanced)]
    return "\n".join(L) + "\n", recs


def main(argv):
    out_ = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    lib, P = Library(), Params()
    jobs = []
    if "--gold" in argv:
        for k, (tname, case, event) in SCENARIOS.items():
            jobs.append(("gold_" + k, TEMPLATES[tname], case, event, Answers(), None))
    skip = {argv.index("--answers") + 1} if "--answers" in argv else set()
    for i, a in enumerate(argv[1:], 1):
        if a.startswith("--") or i in skip:
            continue
        template, case, event, subject, ticks, notes = load_case(a)
        ans = argv[argv.index("--answers") + 1] if "--answers" in argv else str(Path(a).with_suffix("")) + ".answers.json"
        prov = json.loads(Path(a).read_text(encoding="utf-8")).get("provenance")
        jobs.append((Path(a).stem, template, case, event, Answers.load(ans), prov))
    (OUT / "verify").mkdir(parents=True, exist_ok=True)
    bad = 0
    for name, template, case, event, answers, prov in jobs:
        text, recs = check_case(name, template, case, event, answers, lib, P, prov)
        (OUT / (name + ".grounding.md")).write_text(text, encoding="utf-8")
        with open(str(OUT / "verify" / ("grounding_%s.jsonl" % name)), "w", encoding="utf-8") as f:
            for r in recs:
                f.write(json.dumps(r, ensure_ascii=False, default=str) + "\n")
        n = {s: sum(1 for r in recs if r["status"] == s) for s in ("pass", "info", "warn", "fail")}
        bad += n["fail"] > 0
        out_.write("%-28s %4d checks: pass %d, info %d, warn %d, fail %d -> out/%s.grounding.md\n"
                   % (name, len(recs), n["pass"], n["info"], n["warn"], n["fail"], name))
    out_.flush()
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
