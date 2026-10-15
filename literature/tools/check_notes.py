#!/usr/bin/env python
"""Check reading notes in literature/notes/<ID>.md: every quote line  - "..." [p.N]  must occur in
literature/_work/text/<ID>.txt on page N (one page of slack either side), comparing letters and digits only;
every [p.N] must be a page of the PDF text. Python 3.9, conda env "pytorch".

  python literature/tools/check_notes.py            # all notes
  python literature/tools/check_notes.py I1 I7      # some notes
"""
import io
import re
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
ROOT = Path(__file__).resolve().parents[1]
NOTES, TEXT = ROOT / "notes", ROOT / "_work" / "text"
QUOTE = re.compile(r'^\s*-\s*"(.+)"\s*\[pp?\.(\d+)(?:[–-](\d+))?\]\s*$')
PAGE_REF = re.compile(r"\[pp?\.(\d+)(?:[–-](\d+))?\]")


LIGATURES = str.maketrans({"ﬁ": "fi", "ﬂ": "fl", "ﬀ": "ff", "ﬃ": "ffi", "ﬄ": "ffl", "ﬅ": "st", "ﬆ": "st"})


def norm(s):
    """Letters, digits and CJK only; PDF ligatures (ﬁ, ﬂ, …) are expanded first so "significantly" matches "signiﬁcantly"."""
    return re.sub(r"[^0-9a-z一-鿿]", "", s.translate(LIGATURES).lower())


def pages_of(pid):
    t = (TEXT / ("%s.txt" % pid)).read_text(encoding="utf-8")
    parts = re.split(r"^=== \[p\.(\d+)\] ===$", t, flags=re.M)
    return {int(parts[i]): parts[i + 1] for i in range(1, len(parts) - 1, 2)}


def check(path):
    pid = path.stem
    pages = pages_of(pid)
    errors, n_quotes = [], 0
    for ln_no, line in enumerate(path.read_text(encoding="utf-8").split("\n"), 1):
        for m in PAGE_REF.finditer(line):
            for p in (m.group(1), m.group(2)):
                if p and int(p) not in pages:
                    errors.append("line %d: page %s not in the PDF text" % (ln_no, p))
        q = QUOTE.match(line)
        if not q:
            continue
        n_quotes += 1
        lo = int(q.group(2))
        hi = int(q.group(3) or lo)
        window = "".join(pages.get(p, "") for p in range(lo - 1, hi + 2))
        pieces = [norm(x) for x in q.group(1).split("...") if norm(x)]
        if not pieces or any(p not in norm(window) for p in pieces):
            errors.append("line %d: quote not found on p.%s: %s" % (ln_no, q.group(2), q.group(1)[:80]))
    return n_quotes, errors


def main(ids):
    paths = sorted(NOTES.glob("*.md"))
    paths = [p for p in paths if p.stem != "README" and "_" not in p.stem and (not ids or p.stem in ids)]   # I_综合 etc. are syntheses
    bad = 0
    for p in paths:
        if not (TEXT / ("%s.txt" % p.stem)).exists():
            print("%-5s no text file" % p.stem)
            bad += 1
            continue
        n, errs = check(p)
        print("%-5s quotes %2d  errors %d" % (p.stem, n, len(errs)))
        for e in errs:
            print("      " + e)
        bad += bool(errs) or n == 0
    print("%d notes, %d with problems" % (len(paths), bad))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(set(sys.argv[1:])))
