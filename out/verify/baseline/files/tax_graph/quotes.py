"""Quote normalisation shared by the extraction boundary (llm/extract.py) and the case check (verify/casecheck.py).

A quote is evidence when it occurs in its source after this normalisation — letters, digits and CJK only, lower case —
so the line breaks, hyphenation and typographic quote marks of a PDF do not count, and nothing else is forgiven: a
word changed, added or dropped is still not the document's text. One definition, so a quote the extraction accepts is
a quote the case check accepts."""
import re

_DROP = re.compile(r"[^0-9a-z一-鿿]")


def loose(s):
    return _DROP.sub("", (s or "").lower())


def found(quote, text):
    """True when the normalised quote is non-empty and occurs in the (already normalised) text."""
    q = loose(quote)
    return bool(q) and q in text
