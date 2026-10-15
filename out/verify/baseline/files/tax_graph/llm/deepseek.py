"""DeepSeek as the extraction model: a callable prompt -> text over the chat completions API.

    model = DeepSeek()                 # deepseek-flash (DeepSeek-V4.1-Flash); key from .env (api_key=) or DEEPSEEK_API_KEY
    text = model("...")                # model.usage accumulates calls, tokens and seconds

Chosen on 2026-10-14 against deepseek-v4-pro on ten provenance-marked cases (out/extract_eval_deepseek/): flash read
every disclosed value, pro misread three and normalised the source's quote marks. Transient failures (network, time-out,
HTTP 5xx and 429) are retried twice with a pause; anything else is raised, and extract() records the exception as a
note and leaves the field missing. Nothing about the reply is interpreted here, and the key is never printed.
"""
import json
import os
import ssl
import time
import urllib.error
import urllib.request
from pathlib import Path

import certifi

API = "https://api.deepseek.com/chat/completions"
ROOT = Path(__file__).resolve().parents[2]
FLASH, PRO = "deepseek-flash", "deepseek-v4-pro"


def api_key(env=ROOT / ".env"):
    k = os.environ.get("DEEPSEEK_API_KEY")
    if k:
        return k
    if env.exists():
        for line in env.read_text(encoding="utf-8").splitlines():
            name, _, val = line.partition("=")
            if name.strip().lower() in ("api_key", "deepseek_api_key"):
                return val.strip().strip('"').strip("'")
    raise RuntimeError("no DeepSeek key: put api_key=... in .env or set DEEPSEEK_API_KEY")


class DeepSeek:
    def __init__(self, model=FLASH, key=None, timeout=900, retries=2, max_tokens=65536):
        self.model, self.timeout, self.retries, self.max_tokens = model, timeout, retries, max_tokens
        self._key = key or api_key()
        self._ctx = ssl.create_default_context(cafile=certifi.where())
        self.usage = {"calls": 0, "prompt_tokens": 0, "completion_tokens": 0, "cache_hit_tokens": 0, "seconds": 0.0, "retries": 0}

    def __call__(self, prompt: str) -> str:
        body = json.dumps({"model": self.model, "messages": [{"role": "user", "content": prompt}],
                           "max_tokens": self.max_tokens, "stream": False}).encode("utf-8")
        last = None
        for attempt in range(self.retries + 1):
            t0 = time.time()
            try:
                req = urllib.request.Request(API, data=body, headers={"Authorization": "Bearer " + self._key,
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
