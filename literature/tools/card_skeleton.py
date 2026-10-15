#!/usr/bin/env python
"""Create literature/paper_cards/<ID>.md skeletons: front matter from _work/items/<ID>.json, empty sections.

Existing cards are left alone unless --force is given. Section lists are defined in check_card.py.

Usage (conda env "pytorch", Python 3.9), from the project root:
  python literature/tools/card_skeleton.py [--force] [ID ...]
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from check_card import CARDS, ITEMS, SECTIONS, doc_type_of     # noqa: E402

PLACEHOLDER = "（待填）"


def q(s):
    return json.dumps(s, ensure_ascii=False)


def skeleton(r):
    venue = r["venue"] + (", " + r["vol_issue_pages"] if r.get("vol_issue_pages") else "")
    dt = doc_type_of(r["id"])
    fm = ["---",
          "id: %s" % r["id"],
          "title: %s" % q(r["title"]),
          "authors: %s" % q("; ".join(r["authors"])),
          "year: %s" % q(r["year"]),
          "venue: %s" % q(venue),
          "doi: %s" % q(r["doi"]),
          "link: %s" % q(r["doi_url"] or r["stable_url"]),
          "file: %s" % q(r["file"]),
          "version: %s" % r["version"],
          "doc_type: %s" % dt,
          "pdf_pages: %d" % r["pdf_pages"],
          'page_ref: "[p.N] = PDF 第 N 页，从 1 数，含封面页"',
          'read_scope: ""',
          "card_status: draft",
          "---", "", "# %s" % r["title"], ""]
    body = []
    for h in SECTIONS[dt]:
        body += [h, "", PLACEHOLDER, ""]
    return "\n".join(fm + body)


def main():
    force = "--force" in sys.argv
    want = {a for a in sys.argv[1:] if not a.startswith("--")}
    CARDS.mkdir(parents=True, exist_ok=True)
    n = 0
    for f in sorted(ITEMS.glob("*.json")):
        r = json.loads(f.read_text(encoding="utf-8"))
        if r.get("status") != "downloaded" or (want and r["id"] not in want):
            continue
        dest = CARDS / (r["id"] + ".md")
        if dest.exists() and not force:
            continue
        dest.write_text(skeleton(r), encoding="utf-8")
        n += 1
    print("wrote %d skeletons" % n)
    return 0


if __name__ == "__main__":
    sys.exit(main())
