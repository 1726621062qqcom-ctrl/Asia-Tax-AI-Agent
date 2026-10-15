#!/usr/bin/env python
"""Write the text layer of every library PDF to literature/_work/text/<ID>.txt with page markers.

Each page starts with a line "=== [p.N] ===", N being the 1-based PDF page. Paper cards cite these page numbers and
check_card.py verifies quotes against these files. A second file of an item (e.g. B3's correction) goes to
<ID>__<file_key>.txt. Documents over 40 pages also get <ID>.outline.txt with the first lines of every page.

Usage (conda env "pytorch", Python 3.9), from the project root:
  python literature/tools/extract_text.py            # all items with a file
  python literature/tools/extract_text.py A1 B3      # some items
"""
import json
import sys
from pathlib import Path

import fitz

ROOT = Path(__file__).resolve().parents[1]          # literature/
ITEMS = ROOT / "_work" / "items"
OUT = ROOT / "_work" / "text"


def dump(pdf, dest):
    doc = fitz.open(str(pdf))
    parts, empty, outline = [], [], []
    for i in range(doc.page_count):
        t = doc[i].get_text()
        if len(t.strip()) < 20:
            empty.append(i + 1)
        parts.append("=== [p.%d] ===\n%s" % (i + 1, t.rstrip()))
        head = [x.strip()[:90] for x in t.split("\n") if x.strip()][:3]
        outline.append("[p.%d] %s" % (i + 1, " | ".join(head)))
    dest.write_text("\n".join(parts) + "\n", encoding="utf-8")
    if doc.page_count > 40:
        # long documents also get an outline (first lines of every page) to plan what to read
        dest.with_suffix(".outline.txt").write_text("\n".join(outline) + "\n", encoding="utf-8")
    return doc.page_count, empty


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    want = set(sys.argv[1:])
    for f in sorted(ITEMS.glob("*.json")):
        r = json.loads(f.read_text(encoding="utf-8"))
        if r.get("status") != "downloaded" or (want and r["id"] not in want):
            continue
        files = [(r["id"], r["file"])] + [("%s__%s" % (r["id"], x["file_key"]), x["file"])
                                         for x in r.get("extra") or [] if x.get("file")]
        for name, rel in files:
            pages, empty = dump(ROOT.parent / rel, OUT / (name + ".txt"))
            print("%-16s %4d pages%s" % (name, pages, ("; pages without text: %s" % empty) if empty else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
