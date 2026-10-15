"""Singapore: ACRA "Information on Corporate Entities" on data.gov.sg (collection 2; free, updated monthly).

    lookup("MiRXEA Pte. Ltd.") -> [{"jur": "SG", "id": "202035461K", "name": "MIRXEA PTE. LTD.", "incorporated_on": "2020-11-04", ...}]

The datastore API filters on the exact entity name (upper case, as ACRA writes it), so the name is tried in its
ACRA spellings (PTE. LTD. / PTE LTD / LIMITED / LTD.) in the file of its first letter; the free-text `q` search is
only a fallback, filtered by name similarity. Replies are cached in out/registry_cache.sqlite with the time of
retrieval, so a case is looked up once and the record's date is known. No key, no login.
"""
import json
import re
import sqlite3
import ssl
import time
import urllib.parse
import urllib.request
from pathlib import Path
from typing import List

import certifi

from ..llm.patterns import names_match

ROOT = Path(__file__).resolve().parents[2]
DATASETS = json.loads((ROOT / "tax_graph" / "data" / "registry_sg_datasets.json").read_text(encoding="utf-8"))
API = "https://data.gov.sg/api/action/datastore_search"
CACHE = ROOT / "out" / "registry_cache.sqlite"
_CTX = ssl.create_default_context(cafile=certifi.where())
FIELDS = ("uen", "entity_name", "entity_type_description", "company_type_description", "entity_status_description",
          "registration_incorporation_date", "uen_issue_date", "block", "street_name", "level_no", "unit_no", "building_name",
          "postal_code", "primary_ssic_description", "former_entity_name1", "former_entity_name2", "former_entity_name3")


def variants(name: str) -> List[str]:
    n = " ".join((name or "").upper().replace("，", ",").split())
    n = re.sub(r"\s*\(.*?\)\s*$", "", n).strip().rstrip(".")
    base = re.sub(r"\b(PTE\.?\s*LTD\.?|PRIVATE\s+LIMITED|LIMITED|LTD\.?)\s*$", "", n).strip().rstrip(",").strip()
    out = [n, n + ".", base + " PTE. LTD.", base + " PTE LTD", base + " PRIVATE LIMITED", base + " LIMITED", base + " LTD.", base + " LTD"]
    seen, uniq = set(), []
    for v in out:
        v = " ".join(v.split())
        if v and v not in seen:
            seen.add(v)
            uniq.append(v)
    return uniq


def dataset_for(name: str) -> str:
    c = (name or "").strip()[:1].upper()
    key = c if c in DATASETS["datasets"] else "Others"
    return DATASETS["datasets"][key]["dataset_id"]


def _get(url: str, timeout: int = 60, retries: int = 1):
    last = None
    for attempt in range(retries + 1):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "tax-graph/1.0"}), timeout=timeout, context=_CTX) as r:
                return json.loads(r.read().decode("utf-8"))
        except Exception as e:                                   # network: retried once, then reported, never raised into extraction
            last = e
            time.sleep(3)
    raise RuntimeError("data.gov.sg: %s: %s" % (type(last).__name__, last))


def _record(x: dict, url: str, retrieved_at: str) -> dict:
    addr = " ".join(str(x.get(k) or "") for k in ("block", "street_name", "level_no", "unit_no", "building_name", "postal_code") if x.get(k) and x.get(k) != "na")
    former = [x.get(k) for k in ("former_entity_name1", "former_entity_name2", "former_entity_name3") if x.get(k) and x.get(k) != "na"]
    return {"jur": "SG", "id": x.get("uen"), "name": x.get("entity_name"), "former_names": former, "status": x.get("entity_status_description"),
            "type": x.get("company_type_description") or x.get("entity_type_description"), "incorporated_on": x.get("registration_incorporation_date"),
            "address": addr, "source": url, "retrieved_at": retrieved_at, "raw": {k: x.get(k) for k in FIELDS}}


def lookup(name: str, cache: Path = CACHE, timeout: int = 60) -> List[dict]:
    key = "SG|" + " ".join((name or "").upper().split())
    if cache:
        cache.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(str(cache)) as con:
            con.execute("CREATE TABLE IF NOT EXISTS rec (key TEXT PRIMARY KEY, retrieved_at TEXT, records TEXT)")
            row = con.execute("SELECT records FROM rec WHERE key = ?", (key,)).fetchone()
        if row:
            return json.loads(row[0])
    retrieved_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    out, seen = [], set()
    ds = dataset_for(name)
    for v in variants(name):
        url = "%s?resource_id=%s&filters=%s&limit=10" % (API, ds, urllib.parse.quote(json.dumps({"entity_name": v})))
        for x in _get(url, timeout).get("result", {}).get("records", []):
            if x.get("uen") not in seen:
                seen.add(x.get("uen"))
                out.append(_record(x, url, retrieved_at))
        if out:
            break
    if not out:                                                  # fallback: free text, kept only when the name really matches
        v = variants(name)[0]
        url = "%s?resource_id=%s&q=%s&limit=50" % (API, ds, urllib.parse.quote(v))
        for x in _get(url, timeout).get("result", {}).get("records", []):
            if names_match(v, x.get("entity_name", "")) >= 0.9 and x.get("uen") not in seen:
                seen.add(x.get("uen"))
                out.append(_record(x, url, retrieved_at))
    if cache:
        with sqlite3.connect(str(cache)) as con:
            con.execute("INSERT OR REPLACE INTO rec VALUES (?,?,?)", (key, retrieved_at, json.dumps(out, ensure_ascii=False)))
    return out
