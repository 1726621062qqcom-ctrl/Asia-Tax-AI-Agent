"""The file drop: records a person saved from a register that has no API (HK e-Services Portal, the CN 公示系统 at gsxt.gov.cn), or from
any register for a case that must work offline. One JSON file per company under cases/registry/<JUR>/, in the
record form of registry/__init__.py, with "source" (the URL or document the person copied from) and "retrieved_at".
"""
import json
from pathlib import Path
from typing import List, Optional

from ..llm.patterns import names_match

ROOT = Path(__file__).resolve().parents[2]
DROP = ROOT / "cases" / "registry"


def records(jur: str, root: Optional[Path] = None) -> List[dict]:
    d = (root or DROP) / jur
    out = []
    for f in sorted(d.glob("*.json")) if d.exists() else []:
        try:
            rec = json.loads(f.read_text(encoding="utf-8"))
        except ValueError:
            continue
        rec.setdefault("jur", jur)
        rec.setdefault("source", str(f))
        out.append(rec)
    return out


def lookup(jur: str, name: str, root: Optional[Path] = None, threshold: float = 0.9) -> List[dict]:
    """Records whose name or a former name matches any alias of `name` (aliases after " / ")."""
    aliases = [x.strip() for x in (name or "").split("|")[0].split("/") if x.strip()]
    out = []
    for rec in records(jur, root):
        cands = [rec.get("name", "")] + list(rec.get("former_names", []) or [])
        if any(names_match(a, c) >= threshold for a in aliases for c in cands if c):
            out.append(rec)
    return out
