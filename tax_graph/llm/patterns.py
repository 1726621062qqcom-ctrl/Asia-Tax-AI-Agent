"""patterns (抽取改造.md §7, engineering means): deterministic locators that run before any model, and name normalisation.

Several facts have fixed wordings in the documents this library reads (HKEX circulars and prospectuses, SGX
reports): a company's place of incorporation ("a company incorporated in Hong Kong with limited liability"), a
percentage holding ("owned as to 55% by the Vendor"), the scale of a table ("RMB'000"), the defined terms at the
front of a circular. A regular expression over the whole document finds every mention with its sentence, and the
sentences near which the party is named become candidate passages for the reader — ahead of retrieval, so the
right sentence is in front of the model even when retrieval misses it. The pattern does not settle a value: on
the ten evaluation cases (out/extract_eval_deepseek/round4a_patterns_raw, round4_k5) a pattern that decided on its
own was wrong twice and blocked 21 fields with spurious conflicts (other companies' incorporations and holdings
in the same window), while the model reading each sentence separately told them apart. So: pattern locates,
model reads, program compares (extract._read).

    pattern_candidates(name, docs, about)  -> [{"value", "doc", "quote", "start", "distance"}, ...] nearest-party first
    scale_hint(text, pos)                  -> 1000 / 1000000 when a table header nearby says the figures are in thousands / millions
    defined_terms(text)                    -> {"Vendor": "Freetech ... Limited, a company incorporated in Hong Kong ...", ...}
    norm_name / names_match / mentions     -> company names compared without legal-form suffixes and punctuation
"""
import difflib
import re
from typing import Dict, List, Optional

JUR_WORDS = [
    ("HK", r"Hong\s+Kong(?:\s+SAR)?|香港"),
    ("SG", r"(?:the\s+)?Republic\s+of\s+Singapore|Singapore|新加坡"),
    ("CN", r"(?:the\s+)?(?:People'?s\s+Republic\s+of\s+China|PRC|Chinese\s+mainland|Mainland\s+China|China)|中国|中華人民共和國|中华人民共和国"),
    ("VN", r"Vietnam|Viet\s+Nam|越南"),
    ("KY", r"(?:the\s+)?Cayman\s+Islands|開曼|开曼"),
    ("VG", r"(?:the\s+)?British\s+Virgin\s+Islands|BVI|英屬維爾京|英属维尔京"),
]
_PLACES = "|".join(words for _, words in JUR_WORDS)
_INCORP = re.compile(r"(?:incorporated|established|registered|organi[sz]ed|formed)\s+(?:in|under\s+the\s+laws\s+of)\s+(?:the\s+)?(?P<place>" + _PLACES + r")(?![A-Za-z])")
_INCORP_CJK = re.compile(r"(?:于|於|在)(?P<place>香港|新加坡|中国|中國|中华人民共和国|中華人民共和國|越南|開曼群島|开曼群岛|英屬維爾京群島|英属维尔京群岛)(?:成立|註冊|注册|设立|設立)")
_PCT = re.compile(r"(?:owned\s+as\s+to|holds?|holding|held\s+as\s+to|representing|interest\s+of|owns)\s+(?:approximately\s+)?(\d{1,3}(?:\.\d+)?)\s*%", re.I)
_SCALE = [(re.compile(r"'000|’000|in\s+thousands|（千元）|\(千元\)|千元", re.I), 1e3),
          (re.compile(r"in\s+millions|（百万元）|\(百万元\)|百万元|\bmillions?\b\)", re.I), 1e6)]
_TERM = re.compile(r"[“‘\"']{1,2}(?P<term>[A-Z][A-Za-z0-9 &\-\.]{1,40}?)[”’\"']{1,2}\s*\n?\s*(?P<def>(?:means\s+|refers\s+to\s+)?[^\n]{10,400}(?:\n[^\n‘“\"]{3,200}){0,3})")
_LEGAL = re.compile(r"\b(limited|ltd\.?|co\.?,?\s*ltd\.?|company|corporation|corp\.?|inc\.?|plc|pte\.?|holdings?|group|co\.)\b", re.I)
# a sentence ends at a full stop followed by whitespace, a blank line, a page marker, or where the next defined term
# of a definitions list begins (“Term” / ‘‘Term’’ / "Term")
_SENT_END = re.compile(r"(?<=[.。!！?？;；])\s+|\n\s*\n|=== \[pdf p\.\d+\] ===|\s+(?=(?:“|‘‘|\")[A-Z(])")


def jurisdiction_code(place: str) -> Optional[str]:
    for code, words in JUR_WORDS:
        if re.fullmatch(r"(?:the\s+)?(?:%s)\.?" % words, place.strip(), re.I):
            return code
    return None


def sentence_at(text: str, pos: int, limit: int = 500) -> str:
    """The sentence around pos (between sentence ends, see _SENT_END). A span longer than `limit` characters (a
    table, a list without full stops) is cut to the `limit` characters around pos at word boundaries."""
    a = 0
    for m in _SENT_END.finditer(text, max(0, pos - 3000), pos):
        a = m.end()
    m = _SENT_END.search(text, pos)
    b = m.start() if m else len(text)
    if b - a > limit:
        a2, b2 = max(a, pos - limit // 2), min(b, pos + limit // 2)
        while a2 > a and not text[a2 - 1].isspace():
            a2 -= 1
        while b2 < b and not text[b2].isspace():
            b2 += 1
        a, b = a2, b2
    return text[a:b].strip()


def jurisdictions(text: str) -> List[dict]:
    out = []
    for pat in (_INCORP, _INCORP_CJK):
        for m in pat.finditer(text):
            code = jurisdiction_code(m.group("place"))
            if code:
                out.append({"value": code, "quote": sentence_at(text, m.start()), "start": m.start()})
    return out


def percentages(text: str) -> List[dict]:
    return [{"value": float(m.group(1)), "quote": sentence_at(text, m.start()), "start": m.start()} for m in _PCT.finditer(text)]


def scale_hint(text: str, pos: int, window: int = 1500) -> Optional[float]:
    """The scale a table header near pos announces for its figures, if any."""
    head = text[max(0, pos - window):pos]
    for pat, scale in _SCALE:
        if pat.search(head):
            return scale
    return None


def defined_terms(text: str, limit: int = 400) -> Dict[str, str]:
    """The definitions section of a circular: term -> definition text (first occurrence wins)."""
    out = {}
    for m in _TERM.finditer(text[:200000]):
        term = " ".join(m.group("term").split())
        if term not in out and len(out) < limit:
            out[term] = " ".join(m.group("def").split())
    return out


def norm_name(s: str) -> str:
    s = re.sub(r"[（(].*?[)）]", " ", s or "")
    s = _LEGAL.sub(" ", s.lower())
    s = re.sub(r"有限公司|股份有限公司|有限責任公司|有限责任公司|公司", " ", s)
    return " ".join(re.sub(r"[^0-9a-z一-鿿 ]", " ", s).split())


def names_match(a: str, b: str) -> float:
    na, nb = norm_name(a), norm_name(b)
    if not na or not nb:
        return 0.0
    if na == nb or na in nb or nb in na:
        return 1.0
    return difflib.SequenceMatcher(None, na, nb).ratio()


def _party_distance(window: str, centre: int, party: str) -> Optional[int]:
    """Distance (in normalised characters) from the centre of `window` to the nearest mention of any alias of the
    party (aliases separated by " / "); None when the party is not mentioned."""
    nw = norm_name(window)
    scale = len(nw) / max(1, len(window))
    c = int(centre * scale)
    best = None
    for alias in (x.strip() for x in party.split("/")):
        for needle in {norm_name(alias), alias.lower()}:
            if not needle:
                continue
            hay = nw if needle == norm_name(alias) else window.lower()
            cc = c if hay is nw else centre
            i = hay.find(needle)
            while i >= 0:
                d = abs(i - cc)
                best = d if best is None or d < best else best
                i = hay.find(needle, i + 1)
    return best


def mentions(quote: str, about: str) -> bool:
    """Every party named in `about` is in the quote. Parties are separated by " | " (all required), a party's aliases
    by " / " (any one suffices); names compare without legal-form suffixes (norm_name) or as written, case-blind."""
    return all(_party_distance(quote, 0, party) is not None for party in about.split("|") if party.strip())


# ---------------------------------------------------------------- field name -> locator
FIELD_PATTERNS = {
    "incorporated_in": jurisdictions,
    "loc": jurisdictions,
    "ratio": percentages,
    "direct_ratio": percentages,
}


def pattern_candidates(name: str, docs: Dict[str, str], about: Optional[str] = None, near: int = 200, limit: int = 4) -> List[dict]:
    """Candidate sentences a pattern finds for field `name` across the documents. With `about` (parties separated by
    " | ", aliases by " / "), only hits with every party named within `near` characters count, nearest party first,
    at most `limit`; the reader then says whether the sentence states the field for that party."""
    f = FIELD_PATTERNS.get(name)
    if f is None:
        return []
    out, seen = [], set()
    for did, text in docs.items():
        for hit in f(text):
            key = (did, hit["value"], hit["quote"])
            if key in seen:
                continue
            seen.add(key)
            distance = 0
            if about:
                s = hit["start"]
                window = text[max(0, s - near):s + near]
                ds = [_party_distance(window, min(s, near), party) for party in about.split("|") if party.strip()]
                if any(d is None for d in ds):
                    continue
                distance = max(ds) if ds else 0
            out.append({"value": hit["value"], "doc": did, "quote": hit["quote"], "start": hit["start"], "distance": distance})
    out.sort(key=lambda h: (h["distance"], h["start"]))
    return out[:limit] if about else out
