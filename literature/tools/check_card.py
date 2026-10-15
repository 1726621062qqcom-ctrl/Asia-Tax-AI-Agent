#!/usr/bin/env python
"""Check paper cards in literature/paper_cards/ against the rules in paper_cards/README.md.

Errors (must be 0): missing front matter keys or sections, leftover placeholders, quotes not found on the cited
pages, result bullets without a page reference, page references outside the PDF, references to the project.
Warnings: evaluative words outside quotes, quotes matched only approximately, long quotes, many quotes, odd length.
Quotes are compared on letters and digits only, against the cited pages plus one page either side, so OCR word
breaks, ligatures, hyphenation and punctuation do not matter.

Usage (conda env "pytorch", Python 3.9), from the project root:
  python literature/tools/check_card.py A1 [B3 ...]
  python literature/tools/check_card.py --all [--quiet]
"""
import difflib
import io
import json
import re
import sys
import unicodedata
from pathlib import Path

if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parents[1]          # literature/
CARDS = ROOT / "paper_cards"
ITEMS = ROOT / "_work" / "items"
TEXT = ROOT / "_work" / "text"

SECTIONS = {
    "research": ["## 1. 研究问题与作者主张", "## 2. 方法", "## 3. 数据与范围", "## 4. 结果",
                 "## 5. 作者陈述的局限与前提", "## 6. 关键术语", "## 7. 原文摘录", "## 8. 卡片说明"],
    "official": ["## 1. 文件性质与目的", "## 2. 结构", "## 3. 主要内容", "## 4. 适用范围、生效与例外",
                 "## 5. 关键术语", "## 6. 原文摘录", "## 7. 卡片说明"],
}
RESULTS = {"research": "## 4. 结果", "official": "## 3. 主要内容"}
QUOTES = {"research": ("## 7. 原文摘录", 4, 8), "official": ("## 6. 原文摘录", 4, 10)}
OFFICIAL = {"G1", "G2", "G3", "G4"}
FM_KEYS = ["id", "title", "authors", "year", "venue", "doi", "link", "file", "version", "doc_type", "pdf_pages",
           "page_ref", "read_scope", "card_status"]
FORBIDDEN = ["本项目", "我们的项目", "本课题", "本研究项目", "对我们", "我们的设计", "清单用途", "paper_list", "（待填）"]
EVALUATIVE = ["开创", "突破性", "里程碑", "重要贡献", "意义重大", "非常重要", "十分重要", "极其", "出色", "优秀", "卓越",
              "令人信服", "有力地", "有力的", "遗憾", "不足之处", "值得注意", "显然", "无疑", "完美", "新颖", "巧妙", "精彩",
              "impressive", "groundbreaking", "seminal", "compelling", "elegant", "remarkable", "excellent"]
REF = re.compile(r"\[(corr\.)?pp?\.\s*(\d+)(?:\s*[–-]\s*(\d+))?\]")
QUOTE = re.compile(r"[\"“]([^\"“”]{8,}?)[\"”]\s*(\[(?:corr\.)?pp?\.\s*\d+(?:\s*[–-]\s*\d+)?\])")


def doc_type_of(item_id):
    return "official" if item_id in OFFICIAL else "research"


def alnum(s):
    return re.sub(r"[^a-z0-9]", "", unicodedata.normalize("NFKC", s).lower())


def load_pages(name):
    p = TEXT / (name + ".txt")
    if not p.exists():
        return None
    pages, cur, buf = {}, None, []
    for line in p.read_text(encoding="utf-8").split("\n"):
        m = re.match(r"^=== \[p\.(\d+)\] ===$", line)
        if m:
            if cur is not None:
                pages[cur] = "\n".join(buf)
            cur, buf = int(m.group(1)), []
        else:
            buf.append(line)
    if cur is not None:
        pages[cur] = "\n".join(buf)
    return pages


def find(fragment, hay):
    """'exact', 'fuzzy' (>= 92 % of the fragment's characters matched in order) or None."""
    a = alnum(fragment)
    if a in hay:
        return "exact"
    n = len(a)
    step = max(5, n // 10)
    for i in range(0, max(1, len(hay) - n + 1), step):
        sm = difflib.SequenceMatcher(None, a, hay[i:i + n + step], autojunk=False)
        if sm.real_quick_ratio() < 0.9 or sm.quick_ratio() < 0.9:
            continue
        if sum(b.size for b in sm.get_matching_blocks()) / float(n) >= 0.92:
            return "fuzzy"
    return None


def parse(text):
    fm, body = {}, text
    m = re.match(r"^---\n(.*?)\n---\n", text.replace("\r\n", "\n"), re.S)
    if m:
        for line in m.group(1).split("\n"):
            k, sep, v = line.partition(":")
            if not sep:
                continue
            v = v.strip()
            try:
                v = json.loads(v) if v.startswith('"') else v
            except ValueError:
                pass
            fm[k.strip()] = v
        body = text.replace("\r\n", "\n")[m.end():]
    order, sec, cur = [], {}, None
    for line in body.split("\n"):
        if line.startswith("## "):
            cur = line.strip()
            order.append(cur)
            sec[cur] = []
        elif cur:
            sec[cur].append(line)
    return fm, body, order, {k: "\n".join(v).strip() for k, v in sec.items()}


def check(item_id):
    errs, warns, stats = [], [], {"quotes": 0, "exact": 0, "fuzzy": 0}
    card = CARDS / (item_id + ".md")
    if not card.exists():
        return ["no card"], warns, stats
    rec = json.loads((ITEMS / (item_id + ".json")).read_text(encoding="utf-8"))
    fm, body, order, sec = parse(card.read_text(encoding="utf-8"))
    for k in FM_KEYS:
        if k not in fm:
            errs.append("front matter: missing %s" % k)
    if fm.get("id") != item_id:
        errs.append("front matter: id %r" % fm.get("id"))
    if fm.get("file") != rec.get("file"):
        errs.append("front matter: file %r differs from the record" % fm.get("file"))
    if fm.get("card_status") not in ("filled", "accepted"):
        errs.append("front matter: card_status is %r, expected filled" % fm.get("card_status"))
    if fm.get("read_scope") not in ("full", "partial"):
        errs.append("front matter: read_scope must be full or partial")
    dt = doc_type_of(item_id)
    if order != SECTIONS[dt]:
        errs.append("sections: expected %s, got %s" % (SECTIONS[dt], order))
    for h in SECTIONS[dt]:
        if not sec.get(h) or sec[h] == "（待填）":
            errs.append("section empty: %s" % h)
    unquoted = QUOTE.sub(" ", body)
    for w in FORBIDDEN:
        if w in unquoted:
            errs.append("forbidden phrase: %s" % w)
    low = unquoted.lower()
    for w in EVALUATIVE:
        if w.lower() in low:
            warns.append("evaluative word outside quotes: %s" % w)
    for line in sec.get(RESULTS[dt], "").split("\n"):
        if line.startswith("- ") and not REF.search(line):
            errs.append("result bullet without page ref: %s" % line[:70])
    pages = load_pages(item_id) or {}
    corr = load_pages(item_id + "__correction") or {}
    if not pages:
        errs.append("no text file _work/text/%s.txt" % item_id)
    for m in REF.finditer(body):
        lo, hi = int(m.group(2)), int(m.group(3) or m.group(2))
        n = len(corr) if m.group(1) else rec["pdf_pages"]
        if lo < 1 or hi > n or hi < lo:
            errs.append("page ref out of range (1..%d): %s" % (n, m.group(0)))
    for quote, ref in QUOTE.findall(body):
        stats["quotes"] += 1
        m = REF.match(ref)
        src = corr if m.group(1) else pages
        lo, hi = int(m.group(2)), int(m.group(3) or m.group(2))
        hay = alnum(" ".join(src.get(i, "") for i in range(lo - 1, hi + 2)))
        if len(quote.split()) > 55:
            warns.append("quote longer than 50 words on %s" % ref)
        frags = [f for f in re.split(r"\.\.\.|…", quote) if len(alnum(f)) >= 12]
        if not frags:
            warns.append("quote too short to verify on %s: %s" % (ref, quote[:50]))
        worst = "exact"
        for f in frags:
            r = find(f, hay)
            if r is None:
                errs.append("quote not found on %s (or the page either side): %s" % (ref, f.strip()[:80]))
                worst = None
                break
            if r == "fuzzy":
                worst = "fuzzy"
        if worst == "exact":
            stats["exact"] += 1
        elif worst == "fuzzy":
            stats["fuzzy"] += 1
            warns.append("quote matched only approximately on %s: %s" % (ref, quote[:60]))
    qh, qlo, qhi = QUOTES[dt]
    nq = len(QUOTE.findall(sec.get(qh, "")))
    if nq < qlo:
        errs.append("%s: %d quotes, need at least %d" % (qh, nq, qlo))
    elif nq > qhi:
        warns.append("%s: %d quotes, at most %d expected" % (qh, nq, qhi))
    if not 1500 <= len(body) <= 14000:
        warns.append("card body has %d characters (expected 1500-14000)" % len(body))
    return errs, warns, stats


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    quiet = "--quiet" in sys.argv
    ids = sorted((p.stem for p in CARDS.glob("*.md") if re.match(r"^[A-G]\d+$", p.stem)),
                 key=lambda s: (s[0], int(s[1:]))) if "--all" in sys.argv else args
    bad = 0
    for i in ids:
        errs, warns, st = check(i)
        bad += bool(errs)
        print("%-4s %s  errors %d  warnings %d  quotes %d (exact %d, fuzzy %d)" % (
            i, "FAIL" if errs else "ok  ", len(errs), len(warns), st["quotes"], st["exact"], st["fuzzy"]))
        if not quiet:
            for e in errs:
                print("     E " + e)
            for w in warns:
                print("     W " + w)
    if len(ids) > 1:
        print("%d cards, %d with errors" % (len(ids), bad))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
