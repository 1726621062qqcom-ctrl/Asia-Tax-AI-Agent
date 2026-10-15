#!/usr/bin/env python
"""Acceptance aid: list numbers in a card's results and data sections that do not appear on the cited pages.

For every bullet with a page reference, each number with a decimal point, or of 10 or more, is looked up in the
text of the cited pages (one page either side). Numbers written differently in the paper (".83" for "0.83",
"1,234" for "1234") are accepted. Output is a review list, not a verdict.

Usage (conda env "pytorch", Python 3.9), from the project root:
  python literature/tools/audit_cards.py A1 [B3 ...]
  python literature/tools/audit_cards.py --all
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from check_card import CARDS, ITEMS, QUOTE, REF, RESULTS, doc_type_of, load_pages, parse   # noqa: E402

NUM = re.compile(r"(?<![\w.])(\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+\.\d+|\d+)(?![\w])")
DATA = {"research": "## 3. 数据与范围", "official": "## 4. 适用范围、生效与例外"}


def variants(n):
    plain = n.replace(",", "")
    out = {n, plain, n.replace(",", ", ")}                 # some tables print "19, 936"
    if plain.startswith("0."):
        out.add(plain[1:])
    if "." not in plain and len(plain) > 3:
        out.add("{:,}".format(int(plain)))
    return out


def audit(item_id):
    fm, body, order, sec = parse((CARDS / (item_id + ".md")).read_text(encoding="utf-8"))
    pages = load_pages(item_id) or {}
    corr = load_pages(item_id + "__correction") or {}
    dt = doc_type_of(item_id)
    misses, checked = [], 0
    for h in (RESULTS[dt], DATA[dt]):
        for line in sec.get(h, "").split("\n"):
            refs = list(REF.finditer(line))
            if not refs:
                continue
            hay = ""
            for m in refs:
                src = corr if m.group(1) else pages
                lo, hi = int(m.group(2)), int(m.group(3) or m.group(2))
                hay += " ".join(src.get(i, "") for i in range(lo - 1, hi + 2))
            hay = re.sub(r"\s+", " ", hay)
            text = QUOTE.sub(" ", REF.sub(" ", line))
            for n in NUM.findall(text):
                plain = n.replace(",", "")
                if "." not in plain and int(plain) < 10:
                    continue
                checked += 1
                if not any(re.search(r"(?<![\d.])" + re.escape(v) + r"(?!\d)", hay) for v in variants(n)):
                    misses.append((n, line.strip()[:110]))
    return checked, misses


def main():
    ids = sorted((p.stem for p in CARDS.glob("*.md") if re.match(r"^[A-G]\d+$", p.stem)),
                 key=lambda s: (s[0], int(s[1:]))) if "--all" in sys.argv else [a for a in sys.argv[1:]]
    for i in ids:
        checked, misses = audit(i)
        print("%-4s numbers checked %3d, not found on cited pages %d" % (i, checked, len(misses)))
        for n, line in misses:
            print("     %s  <- %s" % (n, line))
    return 0


if __name__ == "__main__":
    sys.exit(main())
