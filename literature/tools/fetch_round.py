#!/usr/bin/env python
"""Fetch a reading round's papers into literature/ and write their page-marked text, recording every attempt.

Round M (2026-10-14, the extraction boundary). Input: a JSON list of items
  {"id": "M1", "author": "Sainz", "year": 2024, "short": "GoLLIE", "venue": "...",
   "urls": [["https://...pdf", "published"], ["https://arxiv.org/pdf/...", "preprint"]]}
Per URL at most two curl attempts; the first URL that yields a PDF wins. The file is named
<ID>_<Author><Year>_<Short>[_preprint].pdf, its text goes to _work/text/<ID>.txt with "=== [p.N] ===" page markers
(the format check_notes.py reads), and _work/round_index.json gets the attempts, file, version and page count.
Downloads land in _work/dl/<ID>/ first (untrusted data in its own directory) and are copied once they parse as PDF.
Usage (conda env "pytorch", Python 3.9), from the project root:
  python literature/tools/fetch_round.py ITEMS.json [--only M1,M2]
"""
import io
import json
import shutil
import subprocess
import sys
from pathlib import Path

import fitz

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
ROOT = Path(__file__).resolve().parents[1]          # literature/
INDEX = ROOT / "_work" / "round_index.json"
TEXT = ROOT / "_work" / "text"
DL = ROOT / "_work" / "dl"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"


def curl(url, dest):
    r = subprocess.run(["curl", "-sSL", "--max-time", "120", "-A", UA, "-o", str(dest), "-w", "%{http_code}", url],
                       capture_output=True, text=True)
    code = r.stdout.strip()[-3:]
    ok = r.returncode == 0 and code == "200" and dest.exists() and dest.read_bytes()[:5] == b"%PDF-"
    return ok, code or ("curl " + str(r.returncode))


def dump(pdf, dest):
    doc = fitz.open(str(pdf))
    with open(str(dest), "w", encoding="utf-8", newline="\n") as f:
        for i, page in enumerate(doc):
            f.write("=== [p.%d] ===\n" % (i + 1))
            f.write(page.get_text())
            f.write("\n")
    return doc.page_count


def main(argv):
    items = json.loads(Path(argv[1]).read_text(encoding="utf-8"))
    only = set(argv[argv.index("--only") + 1].split(",")) if "--only" in argv else None
    index = json.loads(INDEX.read_text(encoding="utf-8")) if INDEX.exists() else {}
    for it in items:
        pid = it["id"]
        if only and pid not in only:
            continue
        if pid in index and index[pid].get("file") and (ROOT.parent / index[pid]["file"]).exists():
            print(pid, "already fetched:", index[pid]["file"])
            continue
        attempts, got = [], None
        for url, version in it["urls"]:
            for _ in range(2):
                d = DL / pid
                d.mkdir(parents=True, exist_ok=True)
                tmp = d / "download.pdf"
                ok, code = curl(url, tmp)
                attempts.append({"url": url, "version": version, "http": code, "ok": ok, "via": "curl"})
                if ok:
                    got = (url, version, tmp)
                    break
            if got:
                break
        rec = {"venue": it["venue"], "attempts": attempts}
        if got:
            url, version, tmp = got
            name = "%s_%s%d_%s%s.pdf" % (pid, it["author"], it["year"], it["short"], "" if version == "published" else "_" + version)
            dest = ROOT / name
            shutil.copyfile(str(tmp), str(dest))
            TEXT.mkdir(parents=True, exist_ok=True)
            pages = dump(dest, TEXT / ("%s.txt" % pid))
            rec.update({"file": "literature/" + name, "version": version, "url": url, "pages": pages})
            print(pid, "ok", name, pages, "pages")
        else:
            print(pid, "FAILED", [a["http"] for a in attempts])
        index[pid] = rec
        INDEX.write_text(json.dumps(index, ensure_ascii=False, indent=1), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
