"""registry (抽取改造.md §1 channel B, §7): official company registers as a program source, and the cross-checks they allow.

    lookup(jur, name)                  -> [record, ...]   from the file drop (cases/registry/<JUR>/*.json) and, for SG, ACRA live
    cross_check(g, case, names, found) -> (facts, provenance, conflicts, violations, notes) for an extraction result

A record is one dict, whatever its source:
    {"jur": "SG", "id": "202035461K", "name": "MIRXEA PTE. LTD.", "former_names": [], "status": "Live Company",
     "type": "Local Company", "incorporated_on": "2020-11-04", "address": "...", "source": "<url or document>",
     "retrieved_at": "2026-10-15T.."}

Sources, by what exists (checked 2026-10-15):
    SG  ACRA's "Information on Corporate Entities" on data.gov.sg (free, monthly, 27 files by first letter; exact-name
        filter over the datastore API): tax_graph/registry/sg.py, dataset ids in data/registry_sg_datasets.json.
    HK  the Companies Registry's e-Services Portal has company search behind a login and a fee; data.cr.gov.hk shows no
        API. A person saves the company particulars as a record in cases/registry/HK/ (see cases/registry/README.md).
    CN  国家企业信用信息公示系统 (gsxt.gov.cn) has no API; a person saves the 基本信息 (basic information) page as a record in cases/registry/CN/.

What the register settles and what it cannot: it states where and when a company was incorporated, its status and
its names; it does not state shareholdings (SG: gazetted columns removed; HK/CN: on the particulars page, a person
copies them if needed). So the cross-checks are: the case's jurisdiction for the party against the register the
party is found in; a holding's `since` against the held company's incorporation date (a holding cannot predate
the company); the party's name against the register's name and former names; a status other than live. Every
difference is reported with the record as its quote; the program never prefers the register over the document.
"""
from datetime import date
from typing import Dict, List, Optional, Tuple

from ..llm.patterns import names_match
from . import files, sg

LIVE = {"SG": sg.lookup}                      # jurisdiction -> live provider; others: file drop only
ACTIVE = {"live company", "live", "existing", "在营", "存续", "在业", "开业"}


def first_alias(name: str) -> str:
    return (name or "").split("|")[0].split("/")[0].strip()


def lookup(jur: str, name: str, live: bool = True, root=None) -> List[dict]:
    """Records for the party `name` (a case `names` entry: aliases after " / ") in jurisdiction `jur`'s register:
    the file drop first, then the live provider when there is one and `live` is set."""
    recs = files.lookup(jur, name, root)
    if live and jur in LIVE and not recs:
        recs += LIVE[jur](first_alias(name))
    return recs


def _date(s) -> Optional[date]:
    if isinstance(s, date):
        return s
    try:
        y, m, d = str(s)[:10].split("-")
        return date(int(y), int(m), int(d))
    except (ValueError, AttributeError):
        return None


def cross_check(g, case, names: Dict[str, str], found: Dict[str, dict]) -> Tuple[dict, dict, dict, list, list]:
    """found: role -> the record a person or the live provider matched. Returns what the extraction result carries:
    facts (path -> value) with provenance rows (kind "registry"), conflicts (path -> [entry]), violations ([path, why])
    and notes — every one of them with the record as the quote; nothing is decided."""
    facts, prov, conflicts, violations, notes = {}, {}, {}, [], []
    for role, rec in found.items():
        ent = g.entities.get(role)
        if ent is None:
            continue
        quote = "%s (%s %s) incorporated %s, status %s" % (rec.get("name"), rec.get("jur"), rec.get("id"), rec.get("incorporated_on"), rec.get("status"))
        row = {"kind": "registry", "source": rec.get("source", ""), "quote": quote, "retrieved_at": rec.get("retrieved_at", "")}
        if rec.get("jur") and rec["jur"] != ent.loc:
            conflicts.setdefault("roles.%s.loc" % role, []).append({"value": rec["jur"], "doc": "registry", "quote": quote, "origin": "registry",
                                                                   "modality": "registry", "kind": "enum", "explicit": True})
            violations.append(["roles.%s.loc" % role, "the case says %s, the register lists a company of this name in %s" % (ent.loc, rec["jur"])])
        else:
            facts["roles.%s.attrs.incorporated_in" % role] = rec["jur"]
            prov["roles.%s.attrs.incorporated_in" % role] = row
        sim = max([names_match(first_alias(names.get(role, "")), rec.get("name", ""))] + [names_match(first_alias(names.get(role, "")), x) for x in rec.get("former_names", [])])
        if sim < 0.9:
            notes.append("registry: %s: registered name %r vs case name %r, similarity %.2f; a person must confirm they are the same company" % (role, rec.get("name"), first_alias(names.get(role, "")), sim))
        inc = _date(rec.get("incorporated_on"))
        for (holder, held), h in getattr(case, "holds", {}).items():
            since = _date(getattr(h, "since", None))
            if held == role and inc and since and since < inc:
                violations.append(["holds.%s>%s.since" % (holder, held), "acquisition date %s is earlier than the held company's registered incorporation date %s (registry)" % (since, inc)])
        if rec.get("status") and str(rec["status"]).strip().lower() not in ACTIVE:
            notes.append("registry: %s: registered status is %r" % (role, rec["status"]))
    return facts, prov, conflicts, violations, notes


def public(rec: dict) -> dict:
    """A record without its raw payload, for result files."""
    return {k: v for k, v in rec.items() if k != "raw"}
