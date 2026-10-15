#!/usr/bin/env python
"""Fetch the published version of a paper into literature/, under the user's fetch policy.

Policy (set by the user on 2026-10-04): published versions only, no preprints for now.
Per file at most three download attempts, then the failure is recorded and left alone:
  attempt 1  curl     plain HTTP client, browser headers, cookie jar
  attempt 2  cffi     curl_cffi with Chrome TLS impersonation; visits --landing first for cookies
  attempt 3  browser  "virtual web": headless Chrome over CDP opens --landing (or the URL),
                      fetches the PDF inside the page, then falls back to a browser download
Metadata lookups (`meta`) and page inspection (`probe`) are discovery, not attempts.

Usage (conda env "pytorch", Python 3.9), from the project root:
  python literature/tools/fetch_lit.py meta --doi 10.1145/3473582
  python literature/tools/fetch_lit.py meta --title "Catala: A Programming Language for the Law"
  python literature/tools/fetch_lit.py probe URL [--browser]
  python literature/tools/fetch_lit.py fetch --id A1 --out literature/A1_Merigoux2021_Catala.pdf \
      --url https://dl.acm.org/doi/pdf/10.1145/3473582 --landing https://dl.acm.org/doi/10.1145/3473582 \
      --expect "Catala" [--expect "for the Law"] [--url2 URL] [--file-key main] [--web-article]
  python literature/tools/fetch_lit.py check PATH [--expect TEXT ...]
  python literature/tools/fetch_lit.py render PATH [--pages 1]
  python literature/tools/fetch_lit.py attempts --id A1 [--file-key main]
  python literature/tools/fetch_lit.py reject --id A1 --reason "accepted manuscript, not the version of record"

Exit codes: 0 success, 2 failure or budget exhausted, 1 usage error.
"""
import argparse
import base64
import hashlib
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

ROOT = Path(os.environ.get("LIT_ROOT") or Path(__file__).resolve().parents[1])   # literature/
WORK = ROOT / "_work"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36")
HDRS = {"User-Agent": UA,
        "Accept": "application/pdf,text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9"}
CHROMES = [r"C:\Program Files\Google\Chrome\Application\chrome.exe",
           r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"]
METHODS = {1: "curl", 2: "cffi", 3: "browser"}
MAX_ATTEMPTS = 3
ARXIV_STAMP = re.compile(r"arXiv:\s?\d{4}\.\d{4,5}(v\d+)?\s*\[[a-zA-Z\-\.]+\]")
SOFT_FLAGS = [("preprint", r"\bpre-?print\b"), ("under_review", r"\bunder review\b"),
              ("submitted_to", r"\bsubmitted to\b"), ("accepted_manuscript", r"accepted (author )?manuscript"),
              ("author_version", r"author'?s? (final |accepted )?(version|copy)"),
              ("draft", r"\bdraft\b"), ("working_paper", r"\bworking paper\b")]


def now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def rel(path):
    """Path relative to the project root, with forward slashes."""
    path = Path(path)
    try:
        return path.resolve().relative_to(ROOT.parent.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def key_of(item_id, file_key):
    return "%s__%s" % (item_id, file_key)


def log_path(item_id, file_key):
    return WORK / "log" / (key_of(item_id, file_key) + ".jsonl")


def read_attempts(item_id, file_key):
    p = log_path(item_id, file_key)
    if not p.exists():
        return []
    return [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x.strip()]


def append_attempt(item_id, file_key, rec):
    p = log_path(item_id, file_key)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def norm(s):
    s = unicodedata.normalize("NFKC", s or "").lower()
    s = s.replace("\u2019", "'").replace("\u2018", "'").replace("\u201c", '"').replace("\u201d", '"')
    s = re.sub(r"-\s*\n\s*", "", s)                     # undo hyphenation at line ends
    s = re.sub(r"[\u00ad]", "", s)
    return re.sub(r"\s+", " ", s).strip()


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


# --------------------------------------------------------------------------- inspection

def inspect_pdf(path, expects=()):
    """Validate a candidate file. Returns a dict; 'ok' is False when it is not a usable PDF."""
    out = {"ok": False, "pdf": False, "pages": 0, "bytes": 0, "text_chars_p1": 0,
           "expect_hits": [], "expect_miss": [], "flags": [], "reason": ""}
    path = Path(path)
    if not path.exists():
        out["reason"] = "no file"
        return out
    data = path.read_bytes()
    out["bytes"] = len(data)
    if b"%PDF" not in data[:1024]:
        head = data[:600].decode("utf-8", "replace")
        title = re.search(r"<title[^>]*>(.*?)</title>", head + data[600:20000].decode("utf-8", "replace"),
                          re.I | re.S)
        out["reason"] = "not a PDF (%s bytes; title=%r)" % (len(data), (title.group(1).strip()[:120] if title else
                                                                         head[:120].replace("\n", " ")))
        return out
    out["pdf"] = True
    try:
        import fitz
        doc = fitz.open(str(path))
        out["pages"] = doc.page_count
        texts = [doc[i].get_text() for i in range(min(3, doc.page_count))]
        meta = doc.metadata or {}
        out["pdf_meta"] = {k: (meta.get(k) or "")[:160] for k in ("title", "author", "creator", "producer")}
        doc.close()
    except Exception as e:                                   # broken or truncated file
        out["reason"] = "PDF does not open: %s" % e
        return out
    if out["pages"] < 1:
        out["reason"] = "PDF has no pages"
        return out
    p1 = texts[0] if texts else ""
    out["text_chars_p1"] = len(p1.strip())
    head_text = norm("\n".join(texts))
    out["first_page_excerpt"] = re.sub(r"\s+", " ", p1.strip())[:400]
    if ARXIV_STAMP.search(p1 if p1 else ""):
        out["flags"].append("arxiv_stamp")
    p1n = norm(p1)
    for name, rx in SOFT_FLAGS:
        if re.search(rx, p1n):
            out["flags"].append(name)
    for e in expects:
        (out["expect_hits"] if norm(e) in head_text else out["expect_miss"]).append(e)
    if not head_text.strip():
        out["flags"].append("no_text_layer")
    if "arxiv_stamp" in out["flags"]:
        out["reason"] = "arXiv preprint stamp on page 1 (not the published version)"
        return out
    if expects and head_text.strip() and not out["expect_hits"]:
        out["reason"] = "content mismatch: none of %r found in pages 1-3" % (list(expects),)
        return out
    if expects and out["expect_miss"] and out["expect_hits"]:
        out["flags"].append("partial_expect")
    out["ok"] = True
    return out


# --------------------------------------------------------------------------- attempt 1: curl

def attempt_curl(url, dest, referer=None):
    jar = str(dest) + ".cookies"
    cmd = ["curl", "-sS", "-L", "--compressed", "--max-time", "180", "--connect-timeout", "30",
           "-A", UA, "-H", "Accept: " + HDRS["Accept"], "-H", "Accept-Language: " + HDRS["Accept-Language"],
           "-c", jar, "-b", jar, "-o", str(dest), "-w", "%{http_code}\t%{content_type}\t%{url_effective}"]
    if referer:
        cmd += ["-e", referer]
    cmd.append(quote(url, safe=":/?&=%#+;,@~!$*'()"))
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    code, ctype, final = (r.stdout.split("\t") + ["", "", ""])[:3]
    try:
        os.remove(jar)
    except OSError:
        pass
    return {"http": code, "ctype": ctype.split(";")[0].strip(), "final_url": final,
            "error": (r.stderr or "").strip()[:300] if r.returncode else ""}


# --------------------------------------------------------------------------- attempt 2: curl_cffi

def attempt_cffi(url, dest, landing=None):
    from curl_cffi import requests as creq
    info = {"http": "", "ctype": "", "final_url": "", "error": ""}
    try:
        s = creq.Session(impersonate="chrome")
        ref = None
        if landing:
            try:
                lr = s.get(landing, timeout=60, allow_redirects=True)
                ref = str(lr.url)
                info["landing_http"] = lr.status_code
            except Exception as e:
                info["landing_error"] = str(e)[:200]
            time.sleep(1.5)
        r = s.get(url, timeout=180, allow_redirects=True, headers={"Referer": ref} if ref else None)
        info.update(http=str(r.status_code), ctype=(r.headers.get("content-type") or "").split(";")[0].strip(),
                    final_url=str(r.url))
        Path(dest).write_bytes(r.content)
    except Exception as e:
        info["error"] = ("%s: %s" % (type(e).__name__, e))[:300]
    return info


# --------------------------------------------------------------------------- attempt 3: headless Chrome via CDP

class CDP(object):
    def __init__(self, ws_url):
        from websocket import create_connection
        self.ws = create_connection(ws_url, timeout=60, suppress_origin=True, max_size=None) \
            if "max_size" in create_connection.__code__.co_varnames else \
            create_connection(ws_url, timeout=60, suppress_origin=True)
        self.n = 0
        self.events = []

    def send(self, method, params=None, session=None, timeout=60):
        self.n += 1
        mid = self.n
        msg = {"id": mid, "method": method, "params": params or {}}
        if session:
            msg["sessionId"] = session
        self.ws.send(json.dumps(msg))
        end = time.time() + timeout
        while time.time() < end:
            self.ws.settimeout(max(0.2, end - time.time()))
            data = json.loads(self.ws.recv())
            if data.get("id") == mid:
                if "error" in data:
                    raise RuntimeError("%s: %s" % (method, data["error"].get("message")))
                return data.get("result", {})
            self.events.append(data)
        raise TimeoutError(method)

    def pump(self, seconds):
        end = time.time() + seconds
        while time.time() < end:
            self.ws.settimeout(max(0.2, end - time.time()))
            try:
                self.events.append(json.loads(self.ws.recv()))
            except Exception:
                break

    def close(self):
        try:
            self.ws.close()
        except Exception:
            pass


CHALLENGE = re.compile(r"^\s*$|just a moment|attention required|checking your browser|verify you are human|"
                       r"not a bot|please wait|ddos|security check|cloudflare|access denied|client challenge", re.I)

FETCH_JS = r"""
(async () => {
  try {
    const r = await fetch(%s, {credentials: 'include', redirect: 'follow'});
    const ct = r.headers.get('content-type') || '';
    const b = new Uint8Array(await r.arrayBuffer());
    let s = ''; const CH = 0x8000;
    for (let i = 0; i < b.length; i += CH) s += String.fromCharCode.apply(null, b.subarray(i, i + CH));
    return JSON.stringify({status: r.status, ct: ct, url: r.url, b64: btoa(s)});
  } catch (e) { return JSON.stringify({error: String(e)}); }
})()
"""


class Browser(object):
    """Headless Chrome over CDP, the "virtual web" route. It runs pages the way a browser does and waits
    for automatic checks to finish; it never clicks or solves a human-verification check."""

    def __init__(self):
        self.proc = self.udd = self.cdp = None

    def __enter__(self):
        exe = next((c for c in CHROMES if os.path.exists(c)), None)
        if not exe:
            raise RuntimeError("no Chrome/Edge found")
        self.udd = Path(tempfile.mkdtemp(prefix="litcdp_"))
        self.dl = self.udd / "dl"
        (self.udd / "Default").mkdir(parents=True)
        self.dl.mkdir()
        prefs = {"plugins": {"always_open_pdf_externally": True},
                 "download": {"default_directory": str(self.dl), "prompt_for_download": False,
                              "directory_upgrade": True}}
        (self.udd / "Default" / "Preferences").write_text(json.dumps(prefs), encoding="utf-8")
        args = [exe, "--headless=new", "--remote-debugging-port=0", "--remote-allow-origins=*",
                "--user-data-dir=%s" % self.udd, "--no-first-run", "--no-default-browser-check", "--disable-gpu",
                "--window-size=1366,900", "--disable-blink-features=AutomationControlled", "--lang=en-US",
                "about:blank"]
        self.proc = subprocess.Popen(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        pf = self.udd / "DevToolsActivePort"
        for _ in range(300):
            if pf.exists() and pf.stat().st_size > 0:
                break
            time.sleep(0.1)
        lines = pf.read_text().split("\n")
        self.cdp = CDP("ws://127.0.0.1:%s%s" % (lines[0].strip(), lines[1].strip()))
        ver = self.cdp.send("Browser.getVersion")
        ua = ver.get("userAgent", UA).replace("HeadlessChrome", "Chrome")
        full = ver.get("product", "Chrome/140.0.0.0").split("/")[-1]
        major = full.split(".")[0]
        uameta = {"brands": [{"brand": "Chromium", "version": major}, {"brand": "Google Chrome", "version": major},
                             {"brand": "Not=A?Brand", "version": "24"}],
                  "fullVersionList": [{"brand": "Chromium", "version": full},
                                      {"brand": "Google Chrome", "version": full},
                                      {"brand": "Not=A?Brand", "version": "24.0.0.0"}],
                  "platform": "Windows", "platformVersion": "19.0.0", "architecture": "x86", "model": "",
                  "mobile": False, "bitness": "64", "wow64": False}
        self.cdp.send("Browser.setDownloadBehavior", {"behavior": "allowAndName", "downloadPath": str(self.dl),
                                                      "eventsEnabled": True})
        tid = self.cdp.send("Target.createTarget", {"url": "about:blank"})["targetId"]
        self.sid = self.cdp.send("Target.attachToTarget", {"targetId": tid, "flatten": True})["sessionId"]
        for m, prm in (("Page.enable", {}), ("Network.enable", {}),
                       ("Network.setUserAgentOverride", {"userAgent": ua, "acceptLanguage": "en-US,en;q=0.9",
                                                         "platform": "Win32", "userAgentMetadata": uameta}),
                       ("Page.addScriptToEvaluateOnNewDocument",
                        {"source": "Object.defineProperty(navigator,'webdriver',{get:()=>undefined});"})):
            self.cdp.send(m, prm, session=self.sid)
        return self

    def __exit__(self, *exc):
        if self.cdp is not None:
            try:
                self.cdp.send("Browser.close", timeout=5)
            except Exception:
                pass
            self.cdp.close()
        if self.proc is not None:
            try:
                self.proc.wait(timeout=10)
            except Exception:
                self.proc.kill()
        if self.udd is not None:
            shutil.rmtree(str(self.udd), ignore_errors=True)
        return False

    def eval(self, expr, timeout=60, await_promise=False):
        r = self.cdp.send("Runtime.evaluate", {"expression": expr, "returnByValue": True,
                                               "awaitPromise": await_promise}, session=self.sid, timeout=timeout)
        return r.get("result", {}).get("value")

    def title(self):
        return self.eval("document.title + ' || ' + location.href") or ""

    def open(self, url, max_wait=40):
        """Navigate and wait until the page is no longer a check page. Returns 'title || url'."""
        self.cdp.send("Page.navigate", {"url": url}, session=self.sid)
        end = time.time() + max_wait
        time.sleep(3)
        while time.time() < end:
            t = self.title()
            if not CHALLENGE.search(t.split(" || ")[0]):
                return t
            self.cdp.pump(2)
        return self.title()

    def html(self):
        return self.eval("document.documentElement.outerHTML") or ""

    def text(self):
        return self.eval("document.body ? document.body.innerText : ''") or ""

    def fetch_in_page(self, url):
        return json.loads(self.eval(FETCH_JS % json.dumps(url), timeout=200, await_promise=True) or "{}")

    def download(self, url, wait=120):
        """Navigate to url and wait for a browser download. Returns (file or None, last 'title || url')."""
        before = self.eval("location.href") or ""
        self.cdp.send("Page.navigate", {"url": url}, session=self.sid)
        end = time.time() + wait
        settled = None
        while time.time() < end:
            self.cdp.pump(2)
            files = list(self.dl.iterdir())
            done = [f for f in files if not f.name.endswith(".crdownload") and f.stat().st_size > 0]
            if done:
                time.sleep(1)
                return done[0], ""
            if any(f.name.endswith(".crdownload") for f in files):
                continue
            t = self.title()
            if t.split(" || ")[-1] != before and not CHALLENGE.search(t.split(" || ")[0]):
                settled = settled or time.time()
                if time.time() - settled > 15:          # an HTML page stayed and no download started
                    return None, t
        return None, self.title()

    def print_pdf(self, dest):
        r = self.cdp.send("Page.printToPDF", {"printBackground": True}, session=self.sid, timeout=120)
        Path(dest).write_bytes(base64.b64decode(r["data"]))


def attempt_browser(url, dest, landing=None, web_article=False, expects=()):
    info = {"http": "", "ctype": "", "final_url": "", "error": "", "steps": []}
    try:
        with Browser() as b:
            if web_article:
                t = b.open(url)
                info["steps"].append("page: " + t[:200])
                txt = norm(b.text())
                miss = [e for e in expects if norm(e) not in txt]
                if CHALLENGE.search(t.split(" || ")[0]) or (expects and len(miss) == len(expects)):
                    Path(dest).write_text(b.html()[:500000], encoding="utf-8")
                    info["error"] = "page not usable: %s; missing %r" % (t[:120], miss)
                    return info
                b.print_pdf(dest)
                info.update(http="200", ctype="application/pdf (page printed by the browser)",
                            final_url=t.split(" || ")[-1])
                return info
            if landing:
                t = b.open(landing)
                info["steps"].append("landing: " + t[:200])
                res = b.fetch_in_page(url)
                if res.get("b64"):
                    body = base64.b64decode(res["b64"])
                    info["steps"].append("in-page fetch: HTTP %s %s %s bytes" % (res.get("status"), res.get("ct"),
                                                                                 len(body)))
                    if body[:1024].find(b"%PDF") >= 0:
                        Path(dest).write_bytes(body)
                        info.update(http=str(res.get("status")), ctype=res.get("ct", "").split(";")[0],
                                    final_url=res.get("url", ""))
                        return info
                else:
                    info["steps"].append("in-page fetch error: %s" % res.get("error"))
            f, t = b.download(url)
            if f is not None:
                shutil.copyfile(str(f), str(dest))
                info.update(http="200", ctype="(browser download)", final_url=url)
                info["steps"].append("browser download: %s bytes" % f.stat().st_size)
                return info
            info["steps"].append("no download; page: " + t[:200])
            Path(dest).write_text(b.html()[:500000], encoding="utf-8")
            info["error"] = "browser: no PDF; last page: " + t[:200]
    except Exception as e:
        info["error"] = ("%s: %s" % (type(e).__name__, e))[:300]
    return info


def inspect_html(path, expects=()):
    """For web-native articles: an HTML page counts only if it is not a check page and shows the expected text."""
    from bs4 import BeautifulSoup
    out = {"ok": False, "pdf": False, "pages": 0, "bytes": 0, "flags": ["html"], "expect_hits": [],
           "expect_miss": [], "reason": ""}
    path = Path(path)
    if not path.exists() or not path.stat().st_size:
        out["reason"] = "no file"
        return out
    raw = path.read_bytes()
    out["bytes"] = len(raw)
    if b"%PDF" in raw[:1024]:
        out["reason"] = "is a PDF"
        return out
    soup = BeautifulSoup(raw.decode("utf-8", "replace"), "lxml")
    title = (soup.title.string or "").strip() if soup.title and soup.title.string else ""
    if CHALLENGE.search(title):
        out["reason"] = "check page (title=%r)" % title[:120]
        return out
    txt = norm(soup.get_text(" "))
    for e in expects:
        (out["expect_hits"] if norm(e) in txt else out["expect_miss"]).append(e)
    if not expects or out["expect_miss"]:
        out["reason"] = "expected text missing: %r (title=%r)" % (out["expect_miss"], title[:120])
        return out
    out["ok"] = True
    out["first_page_excerpt"] = title
    return out


def parse_html_meta(html):
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html, "lxml")
    out = {"title": (soup.title.string or "").strip()[:200] if soup.title and soup.title.string else ""}
    metas = {}
    for m in soup.find_all("meta"):
        n = (m.get("name") or m.get("property") or "").lower()
        if n.startswith(("citation_", "dc.", "prism.", "og:title")) and m.get("content"):
            metas.setdefault(n, [])
            if len(metas[n]) < 4:
                metas[n].append(m["content"][:200])
    out["meta"] = metas
    links = []
    for x in soup.find_all("a", href=True):
        h = x["href"]
        if re.search(r"\.pdf($|\?)|/pdf/|/pdfdirect/|pdfft|download|epdf|fulltext|viewcontent", h, re.I):
            links.append((x.get_text(" ", strip=True)[:60], h[:300]))
    out["pdf_like_links"] = links[:30]
    return out


# --------------------------------------------------------------------------- commands

def accepted(records):
    """The last successful attempt that was not rejected afterwards, or None."""
    last = None
    for r in records:
        if r.get("attempt") and r.get("ok"):
            last = r
        elif r.get("rejected") and last is not None and r.get("attempt_ref") == last.get("attempt"):
            last = None
    return last


def cmd_fetch(a):
    done = read_attempts(a.id, a.file_key)
    out = Path(a.out)
    if not out.is_absolute():
        out = Path.cwd() / out
    acc = accepted(done)
    if acc is not None and (ROOT.parent / acc.get("file", "")).exists():
        print(json.dumps({"id": a.id, "file_key": a.file_key, "status": "already_ok", "file": acc["file"]},
                         ensure_ascii=False))
        return 0
    start = sum(1 for r in done if r.get("attempt")) + 1
    if start > MAX_ATTEMPTS:
        print(json.dumps({"id": a.id, "file_key": a.file_key, "status": "budget_exhausted",
                          "attempts": done}, ensure_ascii=False, indent=1))
        return 2
    tmpdir = Path(tempfile.mkdtemp(prefix="litfetch_"))
    result = None
    for n in range(start, MAX_ATTEMPTS + 1):
        if n > start:
            time.sleep(3)
        method = METHODS[n]
        url = a.url2 if (n == 2 and a.url2) else a.url
        tmp = tmpdir / ("a%d.bin" % n)
        t0 = time.time()
        if method == "curl":
            info = attempt_curl(url, tmp, referer=a.landing)
        elif method == "cffi":
            info = attempt_cffi(url, tmp, landing=a.landing)
        else:
            info = attempt_browser(a.url3 or a.url, tmp, landing=a.landing or None, web_article=a.web_article,
                                   expects=a.expect)
        chk = inspect_pdf(tmp, a.expect)
        target = out
        if a.web_article and not chk["ok"] and method != "browser":
            hchk = inspect_html(tmp, a.expect)
            if hchk["ok"]:
                chk, target = hchk, out.with_suffix(".html")
        rec = {"at": now(), "id": a.id, "file_key": a.file_key, "attempt": n, "method": method,
               "url": a.url3 if (n == 3 and a.url3) else url, "landing": a.landing or "",
               "secs": round(time.time() - t0, 1), "ok": chk["ok"]}
        rec.update(info)
        rec.update({k: chk[k] for k in ("pages", "bytes", "flags", "expect_hits", "expect_miss", "reason")})
        if chk["ok"]:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(str(tmp), str(target))
            rec.update(file=rel(target), sha256=sha256(target), first_page_excerpt=chk.get("first_page_excerpt", ""),
                       pdf_meta=chk.get("pdf_meta", {}))
            append_attempt(a.id, a.file_key, rec)
            result = rec
            break
        if tmp.exists() and tmp.stat().st_size:
            q = WORK / "quarantine"
            q.mkdir(parents=True, exist_ok=True)
            ext = "pdf" if chk["pdf"] else "html"
            qf = q / ("%s__a%d.%s" % (key_of(a.id, a.file_key), n, ext))
            shutil.copyfile(str(tmp), str(qf))
            rec["quarantine"] = rel(qf)
        append_attempt(a.id, a.file_key, rec)
        result = rec
    shutil.rmtree(str(tmpdir), ignore_errors=True)
    status = "ok" if result and result.get("ok") else "failed"
    summary = {"id": a.id, "file_key": a.file_key, "status": status, "attempts": read_attempts(a.id, a.file_key)}
    res_dir = WORK / "result"
    res_dir.mkdir(parents=True, exist_ok=True)
    (res_dir / (key_of(a.id, a.file_key) + ".json")).write_text(json.dumps(summary, ensure_ascii=False, indent=1),
                                                                 encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=1))
    return 0 if status == "ok" else 2


def cmd_check(a):
    r = inspect_pdf(a.path, a.expect)
    if r.get("pdf"):
        r["sha256"] = sha256(a.path)
    print(json.dumps(r, ensure_ascii=False, indent=1))
    return 0 if r["ok"] else 2


def cmd_render(a):
    import fitz
    doc = fitz.open(a.path)
    outdir = WORK / "render"
    outdir.mkdir(parents=True, exist_ok=True)
    stem = Path(a.path).stem
    pages = [int(x) for x in a.pages.split(",")]
    for p in pages:
        if 1 <= p <= doc.page_count:
            pix = doc[p - 1].get_pixmap(dpi=a.dpi)
            f = outdir / ("%s_p%d.png" % (stem, p))
            pix.save(str(f))
            print(f)
    print("pages_total=%d" % doc.page_count)
    return 0


def cmd_reject(a):
    """Mark the accepted download as wrong (wrong paper / not the version of record) and quarantine it."""
    done = read_attempts(a.id, a.file_key)
    acc = accepted(done)
    if acc is None:
        print("nothing accepted for %s/%s" % (a.id, a.file_key))
        return 2
    f = ROOT.parent / acc["file"] if not Path(acc["file"]).is_absolute() else Path(acc["file"])
    rec = {"at": now(), "id": a.id, "file_key": a.file_key, "rejected": True, "attempt_ref": acc["attempt"],
           "reason": a.reason}
    if f.exists():
        q = WORK / "quarantine"
        q.mkdir(parents=True, exist_ok=True)
        qf = q / ("%s__a%d__rejected.pdf" % (key_of(a.id, a.file_key), acc["attempt"]))
        shutil.move(str(f), str(qf))
        rec["quarantine"] = str(qf)
    append_attempt(a.id, a.file_key, rec)
    used = sum(1 for r in done if r.get("attempt"))
    print(json.dumps({"rejected": rec, "attempts_used": used, "attempts_left": MAX_ATTEMPTS - used},
                     ensure_ascii=False, indent=1))
    return 0


def cmd_attempts(a):
    print(json.dumps(read_attempts(a.id, a.file_key), ensure_ascii=False, indent=1))
    return 0


def _get_json(url, timeout=40):
    from curl_cffi import requests as creq
    r = creq.get(url, timeout=timeout, impersonate="chrome", headers={"Accept": "application/json"})
    if r.status_code != 200:
        return {"_http": r.status_code}
    return r.json()


def _crossref(doi):
    j = _get_json("https://api.crossref.org/works/" + quote(doi, safe="/"))
    m = j.get("message") if isinstance(j, dict) else None
    if not m:
        return {"_error": j}
    return {"doi": m.get("DOI"), "type": m.get("type"), "title": (m.get("title") or [""])[0],
            "subtitle": (m.get("subtitle") or [""])[:1],
            "authors": ["%s %s" % (x.get("given", ""), x.get("family", x.get("name", ""))) for x in
                        m.get("author", [])],
            "container": (m.get("container-title") or [""])[0], "publisher": m.get("publisher"),
            "issued": (m.get("issued", {}).get("date-parts") or [[None]])[0],
            "volume": m.get("volume"), "issue": m.get("issue"), "page": m.get("page"),
            "article_number": m.get("article-number"), "url": m.get("URL"),
            "license": [x.get("URL") for x in m.get("license", [])],
            "links": [(x.get("content-type"), x.get("URL"), x.get("intended-application")) for x in m.get("link", [])],
            "relation": m.get("relation"), "update_to": m.get("update-to"),
            "updated_by": m.get("updated-by")}


def _openalex_work(w):
    locs = []
    for l in (w.get("locations") or []):
        src = (l.get("source") or {})
        locs.append({"source": src.get("display_name"), "landing": l.get("landing_page_url"),
                     "pdf": l.get("pdf_url"), "version": l.get("version"), "is_oa": l.get("is_oa"),
                     "license": l.get("license")})
    pl = (w.get("primary_location") or {})
    return {"openalex": w.get("id"), "doi": w.get("doi"), "title": w.get("title"), "year": w.get("publication_year"),
            "type": w.get("type"), "venue": ((pl.get("source") or {}).get("display_name")),
            "authors": [x.get("author", {}).get("display_name") for x in (w.get("authorships") or [])],
            "oa": w.get("open_access"), "locations": locs,
            "biblio": w.get("biblio")}


def cmd_meta(a):
    out = {}
    if a.doi:
        doi = a.doi.replace("https://doi.org/", "").strip()
        out["crossref"] = _crossref(doi)
        j = _get_json("https://api.openalex.org/works/doi:" + quote(doi, safe="/"))
        out["openalex"] = _openalex_work(j) if j.get("id") else j
    if a.title:
        j = _get_json("https://api.openalex.org/works?per-page=6&search=" + quote(a.title))
        out["openalex_search"] = [_openalex_work(w) for w in (j.get("results") or [])]
        j = _get_json("https://api.crossref.org/works?rows=6&query.bibliographic=" + quote(a.title))
        items = ((j.get("message") or {}).get("items") or []) if isinstance(j, dict) else []
        out["crossref_search"] = [{"doi": m.get("DOI"), "type": m.get("type"), "title": (m.get("title") or [""])[0],
                                   "container": (m.get("container-title") or [""])[0],
                                   "issued": (m.get("issued", {}).get("date-parts") or [[None]])[0],
                                   "authors": ["%s %s" % (x.get("given", ""), x.get("family", "")) for x in
                                               m.get("author", [])][:8]} for m in items]
        j = _get_json("https://dblp.org/search/publ/api?format=json&h=6&q=" + quote(a.title))
        hits = (((j.get("result") or {}).get("hits") or {}).get("hit") or []) if isinstance(j, dict) else []
        out["dblp_search"] = [{"title": h["info"].get("title"), "venue": h["info"].get("venue"),
                               "year": h["info"].get("year"), "type": h["info"].get("type"),
                               "doi": h["info"].get("doi"), "ee": h["info"].get("ee")} for h in hits]
    print(json.dumps(out, ensure_ascii=False, indent=1))
    return 0


def cmd_probe(a):
    if a.browser:
        with Browser() as b:
            t = b.open(a.url, max_wait=45)
            html = b.html()
        out = {"via": "browser", "title || url": t}
        out.update(parse_html_meta(html))
        print(json.dumps(out, ensure_ascii=False, indent=1))
        return 0
    from curl_cffi import requests as creq
    s = creq.Session(impersonate="chrome")
    r = s.get(a.url, timeout=60, allow_redirects=True)
    ct = r.headers.get("content-type", "")
    out = {"via": "curl_cffi", "http": r.status_code, "final_url": str(r.url), "ctype": ct, "bytes": len(r.content)}
    if "html" in ct:
        out.update(parse_html_meta(r.text))
    elif r.content[:4] == b"%PDF":
        out["note"] = "URL serves a PDF directly"
    print(json.dumps(out, ensure_ascii=False, indent=1))
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd")
    f = sub.add_parser("fetch")
    f.add_argument("--id", required=True)
    f.add_argument("--file-key", default="main")
    f.add_argument("--out", required=True)
    f.add_argument("--url", required=True, help="PDF URL of the published version")
    f.add_argument("--url2", default="", help="alternate PDF URL for attempt 2 (default: --url)")
    f.add_argument("--url3", default="", help="PDF URL for the browser attempt (default: --url)")
    f.add_argument("--landing", default="", help="landing page (DOI page) to visit first")
    f.add_argument("--expect", action="append", default=[], help="text that must appear on pages 1-3")
    f.add_argument("--web-article", action="store_true",
                   help="web-native article: attempts 1-2 may keep the HTML page, attempt 3 prints the page to PDF")
    c = sub.add_parser("check")
    c.add_argument("path")
    c.add_argument("--expect", action="append", default=[])
    r = sub.add_parser("render")
    r.add_argument("path")
    r.add_argument("--pages", default="1")
    r.add_argument("--dpi", type=int, default=90)
    t = sub.add_parser("attempts")
    t.add_argument("--id", required=True)
    t.add_argument("--file-key", default="main")
    j = sub.add_parser("reject")
    j.add_argument("--id", required=True)
    j.add_argument("--file-key", default="main")
    j.add_argument("--reason", required=True)
    m = sub.add_parser("meta")
    m.add_argument("--doi", default="")
    m.add_argument("--title", default="")
    p = sub.add_parser("probe")
    p.add_argument("url")
    p.add_argument("--browser", action="store_true", help="load the page in headless Chrome (discovery only)")
    a = ap.parse_args()
    fn = {"fetch": cmd_fetch, "check": cmd_check, "render": cmd_render, "attempts": cmd_attempts,
          "reject": cmd_reject,
          "meta": cmd_meta, "probe": cmd_probe}.get(a.cmd)
    if not fn:
        ap.print_help()
        return 1
    return fn(a)


if __name__ == "__main__":
    sys.exit(main())
