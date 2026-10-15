# -*- coding: utf-8 -*-
"""Shared helper for writing precedent cards (案例采集.md K1/K5): find each quote in the library's clause layer by a loose
match (letters, digits and CJK only), store the exact span of the clause text as the quote and the clause id as the
cite; upsert rows into official/labels/factors.csv and precedents.csv. Rows whose quote is not found are reported, not
written."""
import csv
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
LABELS = ROOT / "official" / "labels"
F_COLS = ["issue_key", "factor_id", "elem", "field", "test", "favours", "cites", "quote", "note"]
P_COLS = ["precedent_id", "issue_key", "jur", "forum", "binding", "date", "outcome", "factors_true", "factors_false", "reason",
          "cites", "quote", "note"]
csv.field_size_limit(10 ** 9)
_CLAUSES = None


def clauses():
    global _CLAUSES
    if _CLAUSES is None:
        with open(str(ROOT / "official" / "clauses.csv"), encoding="utf-8-sig", newline="") as f:
            _CLAUSES = [(r["cite_id"], r["doc_id"], r["text"]) for r in csv.DictReader(f)]
    return _CLAUSES


def _loose(s):
    keep = [(i, ch.lower()) for i, ch in enumerate(s) if re.match(r"[0-9A-Za-z\u4e00-\u9fff]", ch)]
    return "".join(c for _, c in keep), [i for i, _ in keep]


def locate(doc, quote):
    """(cite id, exact quote) of the first clause of `doc` holding the quote, or (None, None)."""
    q, _ = _loose(quote)
    for cid, did, text in clauses():
        if did != doc:
            continue
        lt, pos = _loose(text)
        k = lt.find(q)
        if k >= 0 and q:
            a, b = pos[k], pos[k + len(q) - 1] + 1
            return cid, " ".join(text[a:b].split())
    return None, None


def upsert(path, cols, key_cols, rows):
    old = []
    if path.exists():
        with open(str(path), encoding="utf-8-sig", newline="") as f:
            old = list(csv.DictReader(f))
    keys = {tuple(r[k] for k in key_cols) for r in rows}
    merged = [r for r in old if tuple(r[k] for k in key_cols) not in keys] + rows
    with open(str(path), "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(merged)


def write(factors, precedents):
    """factors: (issue, factor_id, elem, field, test, favours, doc, quote, note);
    precedents: (precedent_id, issue, jur, forum, binding, date, outcome, true_ids, false_ids, reason_ids, doc, quote, note)."""
    frows, prows, missing = [], [], []
    for issue, fid, elem, fld, test, fav, doc, quote, note in factors:
        cid, exact = locate(doc, quote)
        if cid is None:
            missing.append("factor %s: not found in %s: %s" % (fid, doc, quote[:60]))
            continue
        frows.append(dict(zip(F_COLS, [issue, fid, elem, fld, test, fav, cid, exact, note])))
    for pid, issue, jur, forum, binding, date, outcome, t, f, reason, doc, quote, note in precedents:
        cid, exact = locate(doc, quote)
        if cid is None:
            missing.append("precedent %s: not found in %s: %s" % (pid, doc, quote[:60]))
            continue
        prows.append(dict(zip(P_COLS, [pid, issue, jur, forum, binding, date, outcome, ";".join(t), ";".join(f), ";".join(reason),
                                       cid, exact, note])))
    upsert(LABELS / "factors.csv", F_COLS, ("issue_key", "factor_id"), frows)
    upsert(LABELS / "precedents.csv", P_COLS, ("precedent_id",), prows)
    return len(frows), len(prows), missing
