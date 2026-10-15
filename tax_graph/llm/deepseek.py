"""DeepSeek as the extraction model: a callable prompt -> text over the chat completions API.

    model = DeepSeek()                 # deepseek-flash (DeepSeek-V4.1-Flash); key from .env (api_key=) or DEEPSEEK_API_KEY
    text = model("...")                # model.usage accumulates calls, tokens, seconds and cache hits

Chosen on 2026-10-14 against deepseek-v4-pro on ten provenance-marked cases (out/extract_eval_deepseek/): flash read
every disclosed value, pro misread three and normalised the source's quote marks. The sampling temperature is set
explicitly (M9: agreement between readings means nothing without diversity) and recorded with every result.
Replies are cached in out/llm_cache.sqlite by (model, temperature, prompt, n-th call of that prompt in this run),
so a rerun of an evaluation or a case costs nothing and reproduces exactly, while repeated readings of one prompt
within a run still get their own samples. Transient failures (network, time-out, HTTP 5xx and 429) are retried
twice with a pause; anything else is raised, and extract() records the exception as a note and leaves the field
missing. Nothing about the reply is interpreted here, and the key is never printed.
"""
import hashlib
import json
import os
import sqlite3
import ssl
import threading
import time
import urllib.error
import urllib.request
from collections import Counter
from pathlib import Path

import certifi

API = "https://api.deepseek.com/chat/completions"
ROOT = Path(__file__).resolve().parents[2]
FLASH, PRO = "deepseek-flash", "deepseek-v4-pro"
CACHE = ROOT / "out" / "llm_cache.sqlite"
_LOCK = threading.Lock()
PROVIDERS = {   # model id prefix -> (chat completions URL, .env key names, environment variable); the same request shape (OpenAI-compatible)
    "deepseek": (API, ("api_key", "deepseek_api_key"), "DEEPSEEK_API_KEY"),
    "qwen": ("https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions", ("qwen_key", "dashscope_api_key"), "DASHSCOPE_API_KEY"),
}


def provider(model: str):
    for prefix, p in PROVIDERS.items():
        if model.lower().startswith(prefix):
            return p
    return PROVIDERS["deepseek"]


def api_key(env=ROOT / ".env", names=("api_key", "deepseek_api_key"), var="DEEPSEEK_API_KEY"):
    k = os.environ.get(var)
    if k:
        return k
    if env.exists():
        for line in env.read_text(encoding="utf-8").splitlines():
            name, _, val = line.partition("=")
            if name.strip().lower() in names:
                return val.strip().strip('"').strip("'")
    raise RuntimeError("no API key: put %s=... in .env or set %s" % (names[0], var))


class DeepSeek:
    """A chat model behind an OpenAI-compatible endpoint, chosen by the model id: deepseek-* at DeepSeek, qwen* at
    Alibaba's DashScope (compatible mode; thinking switched off, the reply is the JSON asked for)."""

    def __init__(self, model=FLASH, key=None, timeout=900, retries=2, max_tokens=None, temperature=None, cache=CACHE):
        self.model, self.timeout, self.retries, self.temperature = model, timeout, retries, temperature
        self.api, names, var = provider(model)
        self.qwen = model.lower().startswith("qwen")
        self.max_tokens = max_tokens if max_tokens is not None else (8192 if self.qwen else 65536)
        self._key = key or api_key(names=names, var=var)
        self._ctx = ssl.create_default_context(cafile=certifi.where())
        self.usage = {"calls": 0, "prompt_tokens": 0, "completion_tokens": 0, "cache_hit_tokens": 0, "seconds": 0.0, "retries": 0, "cached": 0}
        self.cache = Path(cache) if cache else None
        self._seen = Counter()                          # prompt key -> how many times asked in this run
        if self.cache:
            self.cache.parent.mkdir(parents=True, exist_ok=True)
            with _LOCK, sqlite3.connect(str(self.cache)) as con:
                con.execute("CREATE TABLE IF NOT EXISTS reply (key TEXT, n INTEGER, reply TEXT, PRIMARY KEY (key, n))")

    def _key_of(self, prompt):
        return hashlib.sha1(("%s|%s|%s" % (self.model, self.temperature, prompt)).encode("utf-8")).hexdigest()

    def __call__(self, prompt: str) -> str:
        key = self._key_of(prompt)
        with _LOCK:
            n = self._seen[key]
            self._seen[key] += 1
        if self.cache:
            with _LOCK, sqlite3.connect(str(self.cache)) as con:
                row = con.execute("SELECT reply FROM reply WHERE key = ? AND n = ?", (key, n)).fetchone()
            if row:
                self.usage["cached"] += 1
                return row[0]
        text = self._call(prompt)
        if self.cache:
            with _LOCK, sqlite3.connect(str(self.cache)) as con:
                con.execute("INSERT OR REPLACE INTO reply VALUES (?,?,?)", (key, n, text))
        return text

    def _call(self, prompt: str) -> str:
        req_body = {"model": self.model, "messages": [{"role": "user", "content": prompt}], "max_tokens": self.max_tokens, "stream": False}
        if self.temperature is not None:
            req_body["temperature"] = self.temperature
        if self.qwen:
            req_body["enable_thinking"] = False
        body = json.dumps(req_body).encode("utf-8")
        last = None
        for attempt in range(self.retries + 1):
            t0 = time.time()
            try:
                req = urllib.request.Request(self.api, data=body, headers={"Authorization": "Bearer " + self._key,
                                                                          "Content-Type": "application/json"})
                with urllib.request.urlopen(req, timeout=self.timeout, context=self._ctx) as r:
                    d = json.loads(r.read().decode("utf-8"))
                text = d["choices"][0]["message"].get("content") or ""
                u = d.get("usage", {})
                self.usage["calls"] += 1
                self.usage["prompt_tokens"] += u.get("prompt_tokens", 0)
                self.usage["completion_tokens"] += u.get("completion_tokens", 0)
                self.usage["cache_hit_tokens"] += u.get("prompt_cache_hit_tokens", 0)
                self.usage["seconds"] += time.time() - t0
                return text
            except urllib.error.HTTPError as e:
                detail = e.read()[:300].decode("utf-8", "replace")
                if e.code < 500 and e.code != 429:                   # a bad request or key is not transient
                    raise RuntimeError("DeepSeek HTTP %d: %s" % (e.code, detail))
                last = "HTTP %d: %s" % (e.code, detail)
            except (urllib.error.URLError, OSError, ValueError, KeyError, IndexError) as e:
                last = "%s: %s" % (type(e).__name__, e)
            if attempt < self.retries:
                self.usage["retries"] += 1
                time.sleep(5 * (attempt + 1))
        raise RuntimeError("DeepSeek: %s after %d attempts" % (last, self.retries + 1))
