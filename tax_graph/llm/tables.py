"""tables (抽取改造.md §1 channel C, §7): financial-statement rows read by program from a PDF's text.

The PDF text of a circular or prospectus lays a table out one cell per line: a run of year lines ("2021", "2022",
"2023"), a scale line ("(RMB’000)", "(RMB in millions)", "S$’000"), perhaps "(unaudited)" or "Note", then for each
row a label line ("Revenue", "Cost of sales . . . ."), perhaps a dot-leader line, then one number per column
("1,583,082", "(548.8)", "—"). Some tables keep a row on one line ("Revenue 5 675,345 768,482 1,583,082"). Both are
read here; nothing else is interpreted.

    rows(text)                       -> every row with its header: label, values by year, scale, currency, offsets, verbatim quotes
    find_rows(text, label_re, year)  -> the rows whose label matches, holding that year
    table_candidates(name, docs)     -> candidate passages (header + row) for a field with a known row label, for the reader
    revenue(docs, year)              -> the program's own reading of consolidated revenue for a year: one value when every
                                        revenue row agrees (rounding across scales allowed), else the distinct values
    to_eur(value, currency, on)      -> (eur, rate record) by the library's central-parity table, or (None, why)
"""
import csv
import re
from datetime import date
from pathlib import Path
from typing import Dict, List, Optional

ROOT = Path(__file__).resolve().parents[2]
FX = ROOT / "official" / "fx" / "cny_central_parity.csv"

YEAR = re.compile(r"^(?:FY)?\s*((?:19|20)\d\d)\s*[A-Z]?\s*$")
UNIT = re.compile(r"^\(?\s*(?P<cur>RMB|HK\$|HKD|US\$|USD|S\$|SGD|SGD\$|EUR|€|人民币|港元|港币|美元|新元|新加坡元)?\s*(?:in\s+)?(?P<unit>[’'`]\s*000|[’'`]?\s*(?:thousands?|millions?|billions?)|千元|百万元|百万|亿元|亿|万元|元)?\s*\)?$", re.I)
PCT = re.compile(r"^\(?%\)?$")
FILLER = re.compile(r"^\(?(?:un)?audited\)?$|^notes?$|^\(?restated\)?$|^\(?note\)?$", re.I)
NUM = re.compile(r"^\(?-?\d{1,3}(?:,\d{3})*(?:\.\d+)?\)?%?$|^\(?-?\d+(?:\.\d+)?\)?%?$|^[—–\-]+$|^N/?A$|^nil$", re.I)
DOTS = re.compile(r"^[\s\.·…]+$")
LABEL = re.compile(r"^(?P<label>[A-Za-z一-鿿(][^\d\n]{0,90}?)\s*(?:[\.·…]\s*){0,60}$")
ROWLINE = re.compile(r"^(?P<label>[A-Za-z一-鿿][A-Za-z一-鿿 ,&/'’()\-]{1,80}?)(?:\s*[\.·…]+)*\s+(?P<nums>(?:\(?-?[\d,]+(?:\.\d+)?\)?%?|[—–]+)(?:\s+(?:\(?-?[\d,]+(?:\.\d+)?\)?%?|[—–]+)){1,})\s*$")
SCALE = {"000": 1e3, "thousand": 1e3, "thousands": 1e3, "million": 1e6, "millions": 1e6, "billion": 1e9, "billions": 1e9,
         "千元": 1e3, "百万元": 1e6, "百万": 1e6, "亿元": 1e8, "亿": 1e8, "万元": 1e4, "元": 1.0}


def _scale_of(unit: str) -> float:
    return SCALE.get(re.sub(r"[’'`\s]", "", unit or "").lower(), 1.0)
CUR = {"RMB": "CNY", "人民币": "CNY", "HK$": "HKD", "HKD": "HKD", "港元": "HKD", "港币": "HKD", "US$": "USD", "USD": "USD", "美元": "USD",
       "S$": "SGD", "SGD": "SGD", "SGD$": "SGD", "新元": "SGD", "新加坡元": "SGD", "EUR": "EUR", "€": "EUR"}


def _num(tok: str) -> Optional[float]:
    t = tok.strip()
    if not t or re.fullmatch(r"[—–\-]+|N/?A|nil", t, re.I):
        return None
    neg = t.startswith("(") and t.endswith(")")
    t = t.strip("()").rstrip("%").replace(",", "")
    try:
        v = float(t)
    except ValueError:
        return None
    return -v if neg else v


YEARS_LINE = re.compile(r"^[^\d\n]*(?:(?:19|20)\d\d[A-Z]?[\s,]*){2,}[^\d\n]*$")


def _year_run(ls, k) -> bool:
    """Lines k and k+1 are both years: the start of a table header, not a row's figures."""
    return bool(YEAR.match(ls[k][2].strip()) and k + 1 < len(ls) and YEAR.match(ls[k + 1][2].strip()))


def _lines(text: str):
    pos = 0
    for line in text.split("\n"):
        yield pos, pos + len(line), line
        pos += len(line) + 1


def rows(text: str) -> List[dict]:
    """Every table row the text states, each with the header it falls under."""
    ls = list(_lines(text))
    n = len(ls)
    out, header, i = [], None, 0
    while i < n:
        s = ls[i][2].strip()
        if YEAR.match(s) and i + 1 < n and YEAR.match(ls[i + 1][2].strip()):
            years, j = [], i
            while j < n and YEAR.match(ls[j][2].strip()):
                years.append(int(YEAR.match(ls[j][2].strip()).group(1)))
                j += 1
            cols, k, scale, cur = [], j, 1.0, None
            while k < n and k < j + 2 * len(years) + 4:
                t = ls[k][2].strip()
                m = UNIT.match(t)
                if m and (m.group("cur") or m.group("unit")):
                    scale = _scale_of(m.group("unit")) if m.group("unit") else scale
                    cur = CUR.get(m.group("cur") or "", cur)
                    cols.append("amount")
                elif PCT.match(t):
                    cols.append("pct")
                elif FILLER.match(t) or not t:
                    pass
                elif len(t) < 60 and _UNIT_ANYWHERE.search(t):   # "As at 31 December (RMB’ million)"
                    um = _UNIT_ANYWHERE.search(t)
                    scale = _scale_of(um.group("unit"))
                    cur = CUR.get((um.group("cur") or "").upper(), CUR.get(um.group("cur") or "", cur))
                else:
                    break
                k += 1
            header = _header(text, ls, i, k, years, cols, scale, cur)
            i = k
            continue
        if YEARS_LINE.match(s):                                  # a header with the years on one line: "2023 2024 2025"
            years = [int(y) for y in re.findall(r"(?:19|20)\d\d", s)]
            cols, k, scale, cur = [], i + 1, 1.0, None
            while k < n and k <= i + 3:
                toks = ls[k][2].split()
                if not toks or not all(UNIT.match(t) and (UNIT.match(t).group("cur") or UNIT.match(t).group("unit")) or PCT.match(t) or FILLER.match(t) for t in toks):
                    break
                for t in toks:
                    m = UNIT.match(t)
                    if m and (m.group("cur") or m.group("unit")):
                        scale = _scale_of(m.group("unit")) if m.group("unit") else scale
                        cur = CUR.get(m.group("cur") or "", cur)
                        cols.append("amount")
                    elif PCT.match(t):
                        cols.append("pct")
                k += 1
            header = _header(text, ls, i, k, years, cols, scale, cur)
            i = k
            continue
        if header is not None:
            um = UNIT.match(s)
            if um and (um.group("cur") or um.group("unit")) and len(s) < 40:   # a unit line inside the table: the rows below it are in that unit
                header = dict(header, scale=_scale_of(um.group("unit")) if um.group("unit") else header["scale"],
                              currency=CUR.get(um.group("cur") or "", header["currency"]), unit_stated=True)
                i += 1
                continue
            m = ROWLINE.match(s)
            if m and not YEAR.match(s):
                toks = m.group("nums").split()
                row = _row(header, m.group("label"), toks, ls[i][0], ls[i][1], text)
                if row:
                    out.append(row)
                    i += 1
                    continue
            lm = LABEL.match(s)
            if lm and len(s) < 100 and not UNIT.match(s) and not FILLER.match(s):
                j = i + 1
                if j < n and DOTS.match(ls[j][2].strip() or "x"):
                    j += 1
                toks, k = [], j
                while k < n and NUM.match(ls[k][2].strip()) and not _year_run(ls, k):
                    toks.append(ls[k][2].strip())
                    k += 1
                if len(toks) >= 2:
                    row = _row(header, lm.group("label"), toks, ls[i][0], ls[k - 1][1], text)
                    if row:
                        out.append(row)
                        i = k
                        continue
        i += 1
    return out


_UNIT_ANYWHERE = re.compile(r"(?P<cur>RMB|HK\$|US\$|S\$|SGD|USD|HKD|EUR|人民币|港元|美元|新元)?\s*(?:in\s+)?(?P<unit>[’'`]000|thousands?|millions?|billions?|千元|百万元|百万|亿元|万元)", re.I)


def _header(text: str, ls, i: int, k: int, years, cols, scale, cur) -> dict:
    """The header record: years, columns, scale and currency — the unit stated after the years, or, when the lines
    after the years carry none, in the three lines before them ("(RMB in thousands)" above the year line)."""
    unit_stated = scale != 1.0 or cur is not None
    if scale == 1.0:                                             # no scale after the years: perhaps "(RMB in thousands)" above them
        for b in range(max(0, i - 3), i):
            m = _UNIT_ANYWHERE.search(ls[b][2])
            if m:
                scale = _scale_of(m.group("unit"))
                cur = CUR.get((m.group("cur") or "").upper(), CUR.get(m.group("cur") or "", cur))
                unit_stated = True
    a = ls[i][0]
    interim_from, seen = None, set()                             # "2021 2022 2023 | 2023 2024": a year that repeats opens the months-ended columns
    for idx, y in enumerate(years):
        if y in seen:
            interim_from = idx
            break
        seen.add(y)
    return {"years": years, "cols": cols or ["amount"] * len(years), "scale": scale, "currency": cur, "unit_stated": unit_stated, "interim_from": interim_from,
            "start": a, "end": ls[k - 1][1], "quote": text[a:ls[k - 1][1]], "context": text[max(0, a - 400):a]}


def _row(header: dict, label: str, toks: List[str], start: int, end: int, text: str) -> Optional[dict]:
    years, cols = header["years"], header["cols"]
    amounts = [c for c in cols if c == "amount"]
    want = len(cols)
    if len(toks) == want + 1 and re.fullmatch(r"\d{1,2}[a-z]?", toks[0]) and want >= 2:
        toks = toks[1:]                                          # a note reference before the figures
    if len(toks) != want:
        if len(toks) == len(years) and want != len(years):
            cols, want = ["amount"] * len(years), len(years)
        else:
            return None
    label = " ".join(re.sub(r"[\.·…]+$", "", label).split())
    if not label or len(amounts) == 0:
        return None
    values, columns, raw_by_year = {}, [], {}
    per_year = max(1, len(cols) // max(1, len(years))) if len(cols) >= len(years) else 1
    for ci, (c, tok) in enumerate(zip(cols, toks)):
        if c != "amount":
            continue
        yi = min(len(years) - 1, ci // per_year) if per_year else 0
        y = years[yi]
        v = _num(tok)
        interim = header.get("interim_from") is not None and yi >= header["interim_from"]
        columns.append((y, None if v is None else v * header["scale"], "interim" if interim else "year"))
        if not interim and y not in values:                       # full-year columns only; months-ended columns stay in `columns`
            values[y] = None if v is None else v * header["scale"]
            raw_by_year[y] = tok
    return {"label": label, "values": values, "columns": columns, "raw": toks, "raw_by_year": raw_by_year, "scale": header["scale"], "currency": header["currency"], "years": years,
            "unit_stated": header.get("unit_stated", False), "context": header.get("context", ""),
            "start": start, "end": end, "quote": text[start:end], "header_quote": header["quote"], "header_start": header["start"]}


def find_rows(text: str, label_re: str, year: Optional[int] = None) -> List[dict]:
    pat = re.compile(label_re, re.I)
    return [r for r in rows(text) if pat.search(r["label"]) and (year is None or year in r["values"])]


FIELD_ROWS = {   # field name -> the statement row it is read from (抽取改造.md §1 channel C)
    "gross_revenue": r"^(?:total\s+)?revenues?$|^turnover$|^营业收入$|^收入$|^营业总收入$",
    "group_revenue": r"^(?:total\s+)?revenues?$|^turnover$|^营业收入$|^收入$|^营业总收入$",
    "operating_costs": r"^(?:total\s+)?operating\s+(?:costs|expenses)$|^cost\s+of\s+sales$|^营业成本$",
    "total_assets": r"^total\s+assets$|^资产总计$|^资产总额$",
    "employees": r"^(?:total\s+)?(?:number\s+of\s+)?employees$|^员工总数$",
}


CURRENCY_BEFORE = re.compile(r"(RMB|HK\$|US\$|S\$|SGD|USD|HKD|EUR|€|人民币|港元|美元|新元)\s*(?:approximately\s*|about\s*)?$", re.I)   # ends right before the figure


def currency_in(quote: str, value: float) -> Optional[str]:
    """The currency written immediately before the figure that states `value` in the quote (program-read; the model
    is not asked for a currency), or None."""
    from .extract import numbers_in, _NUM
    for m in _NUM.finditer(quote):
        if any(abs(x - value) <= 1e-6 * max(1.0, abs(value)) for x in numbers_in(m.group(0))):
            before = quote[max(0, m.start() - 24):m.start()]
            c = CURRENCY_BEFORE.search(before)
            if c:
                return CUR.get(c.group(1).upper(), CUR.get(c.group(1)))
            return None
    return None


def table_candidates(name: str, docs: Dict[str, str], year: Optional[int] = None, limit: int = 4) -> List[dict]:
    """Candidate passages for the reader: the header and the row, for a field with a known row label."""
    pat = FIELD_ROWS.get(name)
    if pat is None:
        return []
    out = []
    for did, text in docs.items():
        for r in find_rows(text, pat, year):
            out.append({"doc": did, "quote": r["header_quote"] + "\n…\n" + r["quote"], "score": 1.0, "channels": ["table"], "row": r["quote"],
                        "scale": r["scale"], "currency": r["currency"]})
    return out[:limit]


def _close(a: float, b: float, tol: float = 1e-3) -> bool:
    return abs(a - b) <= tol * max(abs(a), abs(b), 1.0)


def revenue(docs: Dict[str, str], year: int) -> dict:
    """The program's reading of consolidated revenue for `year`: every revenue row holding that year; one value when
    they agree up to rounding across scales (the finest-scale row is kept), else all distinct values for a person."""
    found = []
    for did, text in docs.items():
        for r in find_rows(text, FIELD_ROWS["group_revenue"], year):
            v = r["values"].get(year)
            if v is not None and v > 0:
                found.append((v, did, r))
    stated = [t for t in found if t[2]["unit_stated"]]           # a row under a header without a unit cannot be an amount
    if stated:
        found = stated
    cons = [t for t in found if CONSOLIDATED.search(t[2]["context"])]   # the group's own statement before a segment, an associate, a note
    if cons:
        found = cons
    distinct = []
    for v, did, r in found:
        for d in distinct:
            same_digits = r["raw_by_year"].get(year) == d["row"]["raw_by_year"].get(year)
            if same_digits and r["scale"] != d["scale"]:          # one figure, one header states the scale, the other does not
                if d["scale"] == 1.0 and r["scale"] != 1.0:
                    d.update(value=v, doc=did, row=r, scale=r["scale"], currency=r["currency"] or d["currency"])
                d["n"] += 1
                break
            if _close(v, d["value"]) and (d["currency"] in (None, r["currency"]) or r["currency"] is None):
                if r["scale"] < d["scale"]:
                    d.update(value=v, doc=did, row=r, scale=r["scale"], currency=r["currency"] or d["currency"])
                d["n"] += 1
                break
        else:
            distinct.append({"value": v, "doc": did, "row": r, "scale": r["scale"], "currency": r["currency"], "n": 1})
    return {"year": year, "rows": len(found), "distinct": distinct, "value": distinct[0]["value"] if len(distinct) == 1 else None,
            "currency": distinct[0]["currency"] if len(distinct) == 1 else None}


CONSOLIDATED = re.compile(r"consolidated\s+(?:statements?|income|financial)|summary\s+(?:of\s+)?consolidated|综合损益|合并利润|合并损益|综合收益", re.I)


def fx_rates(path: Path = FX) -> List[dict]:
    with open(str(path), encoding="utf-8-sig") as f:
        return [r for r in csv.DictReader(f) if (r.get("rate") or "").strip()]


def year_end_rate_date(year: int, path: Path = FX) -> Optional[date]:
    """The latest day of `year` the central-parity table has an EUR/CNY rate for (the year-end fixing), or None."""
    days = sorted(r["date"] for r in fx_rates(path) if r["pair"] == "EUR/CNY" and r["date"].startswith("%d-" % year))
    if not days:
        return None
    y, m, d = map(int, days[-1].split("-"))
    return date(y, m, d)


def to_eur(value: float, currency: str, on: date, path: Path = FX):
    """value in `currency` -> EUR by the central-parity table at `on` (EUR/CNY, with X/CNY for a non-CNY currency);
    (None, why) when the table has no rate for that day."""
    rates = {(r["date"], r["pair"]): float(r["rate"]) for r in fx_rates(path)}
    day = on.isoformat()
    eur_cny = rates.get((day, "EUR/CNY"))
    if eur_cny is None:
        return None, "no EUR/CNY central parity for %s (official/fx/cny_central_parity.csv)" % day
    if currency in (None, "CNY"):
        return value / eur_cny, {"date": day, "pairs": {"EUR/CNY": eur_cny}}
    x_cny = rates.get((day, "%s/CNY" % currency))
    if x_cny is None:
        return None, "no central parity for %s: %s/CNY" % (day, currency)
    return value * x_cny / eur_cny, {"date": day, "pairs": {"EUR/CNY": eur_cny, "%s/CNY" % currency: x_cny}}
