#!/usr/bin/env python
"""Write literature/_work/items/<ID>.json from the curated facts in items_src.json plus the attempt logs.

items_src.json holds what a person checked: the version-of-record DOI (or, without a DOI, title, authors, venue),
status overrides (preprint_only, no fetch made), a file named directly (supplied by the user, or renamed) with its
version (published / preprint) and source, open-access status, corrections against paper_list.txt, notes.
Bibliographic fields of DOI items come from Crossref; file, sha256, pages, source and attempts come from the logs.

Usage (conda env "pytorch", Python 3.9), from the project root:
  python literature/tools/make_items.py            # all items
  python literature/tools/make_items.py A1 B3      # some items
"""
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import fetch_lit as F                                    # noqa: E402  (also sets utf-8 stdout)

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "tools" / "items_src.json"
OUT = ROOT / "_work" / "items"
CACHE = ROOT / "_work" / "crossref_cache.json"


def crossref(doi, cache):
    if doi in cache:
        return cache[doi]
    from curl_cffi import requests as creq
    from urllib.parse import quote
    r = creq.get("https://api.crossref.org/works/" + quote(doi, safe="/"), timeout=40, impersonate="chrome")
    m = r.json()["message"] if r.status_code == 200 else {}
    cache[doi] = m
    time.sleep(0.3)
    return m


def year_of(m):
    for k in ("published-print", "journal-issue", "issued", "published-online"):
        v = m.get(k)
        if k == "journal-issue":
            v = (v or {}).get("published-print")
        parts = ((v or {}).get("date-parts") or [[None]])[0]
        if parts and parts[0]:
            return str(parts[0])
    return ""


def vip(m):
    s = []
    if m.get("volume"):
        s.append(m["volume"] + ("(%s)" % m["issue"] if m.get("issue") else ""))
    if m.get("article-number"):
        s.append("art. " + m["article-number"])
    if m.get("page") and m.get("page") != m.get("article-number"):
        s.append(m["page"].replace("-", "–"))
    return ", ".join(s)


def from_logs(iid, key="main"):
    recs = F.read_attempts(iid, key)
    acc = F.accepted(recs)
    tries = []
    for r in recs:
        if r.get("rejected"):
            tries.append("rejected attempt %s: %s" % (r.get("attempt_ref"), r.get("reason", "")))
            continue
        if not r.get("attempt"):
            continue
        what = "ok" if r.get("ok") else (r.get("reason") or r.get("error") or "failed")
        host = (r.get("url") or "").split("/")[2] if "://" in (r.get("url") or "") else ""
        tries.append("%s %s %s HTTP %s: %s" % (r["attempt"], r["method"], host, r.get("http", ""), what[:120]))
    return acc, "; ".join(tries), len([r for r in recs if r.get("attempt")])


def main():
    src = json.loads(SRC.read_text(encoding="utf-8"))
    cache = json.loads(CACHE.read_text(encoding="utf-8")) if CACHE.exists() else {}
    want = set(sys.argv[1:])
    OUT.mkdir(parents=True, exist_ok=True)
    for iid, s in src.items():
        if want and iid not in want:
            continue
        rec = {k: "" for k in ("title", "year", "venue", "vol_issue_pages", "publisher", "doi", "doi_url", "stable_url",
                               "other_ids", "oa", "file", "sha256", "source_url", "version_evidence", "attempts", "notes")}
        rec.update(id=iid, authors=[], extra=[], corrections=[], pdf_pages=0, status="", failure_kind="none")
        doi = s.get("doi", "")
        if doi:
            m = crossref(doi, cache)
            title = " ".join((m.get("title") or [""])[0].split())
            sub = " ".join((m.get("subtitle") or [""])[0].split())
            if sub and sub.lower() not in title.lower():
                title = "%s: %s" % (title, sub)
            rec.update(title=title,
                       authors=[("%s %s" % (a.get("given", ""), a.get("family", a.get("name", "")))).strip()
                                for a in m.get("author", [])],
                       year=year_of(m), venue=(m.get("container-title") or [""])[0], vol_issue_pages=vip(m),
                       publisher=m.get("publisher", ""), doi=doi, doi_url="https://doi.org/" + doi)
        for k in ("title", "authors", "year", "venue", "vol_issue_pages", "publisher", "stable_url", "other_ids", "oa",
                  "corrections", "notes", "failure_kind", "version_evidence"):
            if k in s:
                rec[k] = s[k]
        acc, tries, n = from_logs(iid)
        rec.update(version="", source="")
        if s.get("file"):
            # a file named in items_src: supplied by the user, or a logged download that was renamed later
            p = F.ROOT.parent / s["file"]
            chk = F.inspect_pdf(p)
            user = s.get("source", "").startswith("user")
            rec.update(status="downloaded", failure_kind="none", file=s["file"], sha256=F.sha256(p),
                       pdf_pages=chk.get("pages", 0), version=s.get("version", "published"),
                       source=s.get("source") or "fetch_lit.py",
                       source_url=s.get("source_url") or ("" if user else (acc or {}).get("final_url", "")),
                       attempts="; ".join(x for x in (tries, "supplied by the user on 2026-10-05" if user else "") if x))
            if not rec["version_evidence"]:
                rec["version_evidence"] = "page 1: " + chk.get("first_page_excerpt", "")[:220]
        elif s.get("status") == "preprint_only":
            rec.update(status="preprint_only", attempts="none: no published version, preprints are out of scope")
        elif acc:
            p = F.ROOT.parent / acc["file"]
            chk = F.inspect_pdf(p) if p.suffix == ".pdf" else {"pages": 0}
            rec.update(status="downloaded", failure_kind="none", file=acc["file"], sha256=F.sha256(p),
                       pdf_pages=chk.get("pages", 0), source_url=acc.get("final_url") or acc.get("url"),
                       attempts=tries, version="published", source="fetch_lit.py")
            if not rec["version_evidence"]:
                rec["version_evidence"] = "page 1: " + (acc.get("first_page_excerpt") or "")[:220]
        else:
            rec.update(status="failed", attempts=tries or s.get("attempts", "none"))
            if rec["failure_kind"] == "none":
                rec["failure_kind"] = "other"
        for x in s.get("extra", []):
            xa, xt, _ = from_logs(iid, x["file_key"])
            x = dict(x)
            x.update(file=xa["file"] if xa else "", status="downloaded" if xa else "failed", attempts=xt)
            rec["extra"].append(x)
        if not rec["stable_url"]:
            rec["stable_url"] = rec["doi_url"]
        (OUT / (iid + ".json")).write_text(json.dumps(rec, ensure_ascii=False, indent=1), encoding="utf-8")
        print("%-4s %-13s %-18s %s" % (iid, rec["status"], rec["failure_kind"], rec["doi_url"] or rec["stable_url"]))
    CACHE.write_text(json.dumps(cache, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    sys.exit(main())
