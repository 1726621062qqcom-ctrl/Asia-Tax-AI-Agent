#!/usr/bin/env python
"""Build literature/manifest.csv and literature/STATUS.md from literature/_work/items/<ID>.json.

Checks on the way: every list entry (sections A-G of paper_list.txt) has a record, every recorded file exists
and its sha256 matches, no two items share a file. Problems are printed and listed in STATUS.md.

Usage (conda env "pytorch", Python 3.9), from the project root:
  python literature/tools/build_manifest.py
"""
import csv
import hashlib
import io
import json
import re
import sys
from collections import Counter
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parents[1]          # literature/
PROJECT = ROOT.parent
ITEMS = ROOT / "_work" / "items"
FIELDS = ["id", "star", "list_mark", "status", "version", "source", "failure_kind", "title", "authors", "year", "venue",
          "vol_issue_pages", "publisher", "doi", "doi_url", "stable_url", "other_ids", "oa", "file", "bytes",
          "sha256", "pdf_pages", "source_url", "version_evidence", "attempts", "extra", "corrections", "notes",
          "list_entry"]
KIND_ZH = {"paywall": "paywall", "human_verification": "human verification", "blocked": "other block",
           "no_online_copy": "no online full text", "not_found": "dead link", "other": "other", "none": ""}


def list_entries():
    """Entries of paper_list.txt sections A-G: id -> (star, mark, text)."""
    out, cur = {}, None
    for ln in (PROJECT / "paper_list.txt").read_text(encoding="utf-8").split("\n"):
        m = re.match(r"^\[([A-H]\d+)\]\s*(★)?\s*\[(V|M)\]\s*(.*)$", ln)
        if m:
            cur = m.group(1)
            out[cur] = {"star": "★" if m.group(2) else "", "mark": m.group(3), "text": m.group(4).strip()}
        elif cur and ln.strip() and not ln.startswith("====") and not ln.strip().startswith("用途"):
            out[cur]["text"] += " / " + ln.strip()
        elif not ln.strip():
            cur = None
    return {k: v for k, v in out.items() if not k.startswith("H")}


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def order(item_id):
    return (item_id[0], int(item_id[1:]))


def link(rec):
    return rec.get("doi_url") or rec.get("stable_url") or ""


def main():
    entries = list_entries()
    recs = {}
    for f in sorted(ITEMS.glob("*.json")):
        r = json.loads(f.read_text(encoding="utf-8"))
        recs[r["id"]] = r
    problems = []
    for i in entries:
        if i not in recs:
            problems.append("%s: no record" % i)
    for i in recs:
        if i not in entries:
            problems.append("%s: record without a list entry" % i)
    seen_files = Counter()
    rows = []
    for i in sorted(recs, key=order):
        r = recs[i]
        e = entries.get(i, {"star": "", "mark": "", "text": ""})
        size = ""
        files = [("main", r.get("file") or "", r.get("sha256") or "")]
        files += [(x.get("file_key", "extra"), x.get("file") or "", "") for x in (r.get("extra") or [])]
        for key, rel, want in files:
            if not rel:
                continue
            seen_files[rel] += 1
            p = PROJECT / rel
            if not p.exists():
                problems.append("%s/%s: file missing: %s" % (i, key, rel))
                continue
            if key == "main":
                size = p.stat().st_size
                got = sha256(p)
                if want and got != want:
                    problems.append("%s: sha256 mismatch (record %s..., file %s...)" % (i, want[:12], got[:12]))
        if r.get("status") == "downloaded" and not r.get("file"):
            problems.append("%s: status downloaded but no file" % i)
        if r.get("status") != "downloaded" and r.get("file"):
            problems.append("%s: status %s but a file is recorded" % (i, r.get("status")))
        if r.get("doi") and r.get("doi_url") != "https://doi.org/" + r["doi"]:
            problems.append("%s: doi_url %r does not match doi %r" % (i, r.get("doi_url"), r["doi"]))
        rows.append({
            "id": i, "star": e["star"], "list_mark": e["mark"], "status": r.get("status", ""),
            "version": r.get("version", ""), "source": r.get("source", ""),
            "failure_kind": r.get("failure_kind", ""), "title": r.get("title", ""),
            "authors": "; ".join(r.get("authors") or []), "year": r.get("year", ""), "venue": r.get("venue", ""),
            "vol_issue_pages": r.get("vol_issue_pages", ""), "publisher": r.get("publisher", ""),
            "doi": r.get("doi", ""), "doi_url": r.get("doi_url", ""), "stable_url": r.get("stable_url", ""),
            "other_ids": r.get("other_ids", ""), "oa": r.get("oa", ""), "file": r.get("file", ""), "bytes": size,
            "sha256": r.get("sha256", ""), "pdf_pages": r.get("pdf_pages", ""), "source_url": r.get("source_url", ""),
            "version_evidence": r.get("version_evidence", ""), "attempts": r.get("attempts", ""),
            "extra": json.dumps(r.get("extra") or [], ensure_ascii=False) if r.get("extra") else "",
            "corrections": " | ".join(r.get("corrections") or []), "notes": r.get("notes", ""),
            "list_entry": e["text"]})
    for rel, n in seen_files.items():
        if n > 1:
            problems.append("file used by %d items: %s" % (n, rel))

    with (ROOT / "manifest.csv").open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows)

    st = Counter(r["status"] for r in rows)
    fk = Counter(r["failure_kind"] for r in rows if r["status"] == "failed")
    have = [r for r in rows if r["status"] == "downloaded"]
    vc = Counter(r["version"] for r in have)
    md = ["# STATUS", "", "Generated by `tools/build_manifest.py`; do not edit by hand. Per-item details are in `manifest.csv`, paper cards in `paper_cards/`.", "",
          "| item | count |", "|---|---|",
          "| list entries (A–G) | %d |" % len(entries),
          "| with a file | %d |" % len(have),
          "| &nbsp;&nbsp;of which published version | %d |" % vc["published"],
          "| &nbsp;&nbsp;of which preprint or working paper | %d |" % vc["preprint"],
          "| &nbsp;&nbsp;of which downloaded manually by the user | %d |" % sum(1 for r in have if r["source"].startswith("user")),
          "| missing | %d |" % (st["failed"] + st["preprint_only"]),
          "| check problems | %d |" % len(problems), ""]

    md += ["## Missing", "", "| id | title | note | link |", "|---|---|---|---|"]
    for r in rows:
        if r["status"] in ("failed", "preprint_only"):
            md.append("| %s%s | %s | %s | %s |" % (r["id"], " ★" if r["star"] else "", r["title"].replace("|", "/"),
                                                  r["notes"].replace("|", "/").replace("\n", " "), link(recs[r["id"]])))
    md += ["", "## Preprints or working papers (not the published version)", "", "| id | file | pages | note |", "|---|---|---|---|"]
    for r in have:
        if r["version"] == "preprint":
            md.append("| %s%s | `%s` | %s | %s |" % (r["id"], " ★" if r["star"] else "", Path(r["file"]).name,
                                                    r["pdf_pages"], r["notes"].replace("|", "/")))
    md += ["", "## Published versions", "", "| id | file | pages | source | link |", "|---|---|---|---|---|"]
    for r in have:
        if r["version"] != "preprint":
            md.append("| %s%s | `%s` | %s | %s | %s |" % (r["id"], " ★" if r["star"] else "", Path(r["file"]).name,
                                                         r["pdf_pages"], "user" if r["source"].startswith("user") else "script",
                                                         link(recs[r["id"]])))
            for x in recs[r["id"]].get("extra") or []:
                if x.get("file"):
                    md.append("| %s | `%s` | | script | %s |" % (r["id"], Path(x["file"]).name,
                                                            ("https://doi.org/" + x["doi"]) if x.get("doi") else ""))
    md += ["", "## Differences from the list", ""]
    for r in rows:
        if r["corrections"]:
            md.append("- **%s**: %s" % (r["id"], r["corrections"].replace(" | ", "; ")))
    md += ["", "## Check problems", ""]
    md += ["- " + p for p in problems] or ["none"]
    (ROOT / "STATUS.md").write_text("\n".join(md) + "\n", encoding="utf-8")

    print("records %d / entries %d; %s" % (len(recs), len(entries), dict(st)))
    print("failure kinds: %s" % dict(fk))
    print("problems: %d" % len(problems))
    for p in problems:
        print("  " + p)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
