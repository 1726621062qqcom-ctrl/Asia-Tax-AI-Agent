"""Structure-first intake over the existing graph and rule field dependencies."""
import math
import re
from datetime import date

from .forms import field_schema

TRANSACTION_TYPES = {
    "DIVIDEND": "Dividend", "SERVICE_FEE": "Service fee", "INTEREST": "Interest", "ROYALTY": "Royalty",
    "SHARE_TRANSFER": "Share disposal", "GOODS": "Goods sale", "CAPITAL_REDUCTION": "Capital reduction",
    "LIQUIDATION": "Liquidation distribution", "IP_TRANSFER": "IP ownership transfer",
    "PROPERTY_TRANSFER": "Property sale", "PROPERTY_RENT": "Property rent",
}


def _number(value, label, low=0, high=None, inclusive=False):
    if type(value) not in (int, float) or not math.isfinite(value) or (value < low if inclusive else value <= low) or (high is not None and value > high):
        raise ValueError("%s: enter a valid number%s" % (label, " (maximum %s)" % high if high is not None else ""))
    return value


def build_recorded_case(body, original=None):
    companies = body.get("companies") or []
    ownership = body.get("ownership") or []
    transactions = body.get("transactions") or []
    if not companies or not transactions:
        raise ValueError("Add companies and at least one transaction")
    if len(companies) > 50 or len(transactions) > 100:
        raise ValueError("This intake supports up to 50 companies and 100 transactions")
    if body.get("currency") not in ("CNY", "HKD", "SGD", "USD", "EUR"):
        raise ValueError("Choose a single currency for this assessment")
    source = str(body.get("source") or "").strip()
    name = str(body.get("case_id") or "").strip()
    if not source or not name:
        raise ValueError("Enter a case name and the source of the recorded facts")
    date.fromisoformat(body.get("as_at") or "")
    roles, names, members = {}, {}, []
    for co in companies:
        key = co.get("id", "")
        if not re.fullmatch(r"[A-Z_]+", key) or key in roles:
            raise ValueError("Company identifiers must be unique")
        if co.get("loc") not in ("CN", "HK", "SG") or not str(co.get("name") or "").strip():
            raise ValueError("Every company needs a name and a supported jurisdiction")
        if type(co.get("member")) is not bool:
            raise ValueError("Specify whether each company is included in the assessment total")
        prior = (original or {}).get("roles", {}).get(key, {})
        # A company moved across a border cannot silently keep jurisdiction-specific facts.
        attrs = dict(prior.get("attrs") or {}) if prior.get("loc") == co["loc"] and (original or {}).get("currency") == body["currency"] else {}
        roles[key] = {"loc": co["loc"], "attrs": attrs, "type": prior.get("type", "COMPANY")}
        names[key] = co["name"].strip()
        if co["member"]:
            members.append(key)
    if not members:
        raise ValueError("Include at least one company in the assessment total")
    holds, seen = [], set()
    for row in ownership:
        a, b = row.get("holder"), row.get("held")
        if a not in roles or b not in roles or a == b or (a, b) in seen:
            raise ValueError("Each ownership link must connect two different companies and occur only once")
        seen.add((a, b))
        h = {"holder": a, "held": b, "ratio": _number(row.get("ratio"), "Ownership percentage", high=100)}
        if row.get("since"):
            date.fromisoformat(row["since"])
            h["since"] = row["since"]
        if row.get("cost") is not None:
            h["cost"] = _number(row["cost"], "Acquisition cost", inclusive=True)
        holds.append(h)
    for child in roles:
        if sum(h["ratio"] for h in holds if h["held"] == child) > 100.000001:
            raise ValueError("Recorded ownership of %s exceeds 100%%" % names[child])
    visited = set()
    def visit(node, stack):
        if node in stack:
            raise ValueError("Circular ownership needs a separate assessment; remove the cycle from this intake")
        if node in visited:
            return
        for h in holds:
            if h["holder"] == node:
                visit(h["held"], stack | {node})
        visited.add(node)
    for co in roles:
        visit(co, set())
    txs, flows, settled, dates = {}, {}, {}, []
    for row in transactions:
        key = row.get("id", "")
        if not re.fullmatch(r"[a-z][a-z0-9_]*", key) or key in txs:
            raise ValueError("Transaction identifiers must be unique")
        payer, payee = row.get("payer"), row.get("payee")
        if payer not in roles or payee not in roles or payer == payee:
            raise ValueError("Each transaction needs two different companies")
        if row.get("income") not in TRANSACTION_TYPES:
            raise ValueError("Choose a supported transaction type")
        on = date.fromisoformat(row.get("on") or "")
        dates.append(on)
        tx = {"payer": payer, "payee": payee, "income": row["income"], "amount": _number(row.get("amount"), "Transaction amount"), "on": on.isoformat()}
        if tx["income"] == "SHARE_TRANSFER":
            if row.get("target") not in roles or row["target"] in (payer, payee):
                raise ValueError("A share disposal needs the company whose shares are sold")
            tx["target"] = row["target"]
        txs[key] = tx
        old = (original or {}).get("transactions", {}).get(key)
        # Changed parties, type, price or dates invalidate the transaction-specific assertions and paid-tax records.
        if old == tx and (original or {}).get("currency") == body["currency"] and all((original or {}).get("roles", {}).get(r, {}).get("loc") == roles[r]["loc"] for r in (payer, payee)):
            flows[key] = dict((original or {}).get("flows", {}).get(key, {}))
        for jurisdiction, value in (row.get("paid") or {}).items():
            if jurisdiction not in ("CN", "HK", "SG"):
                raise ValueError("Choose a supported jurisdiction for tax already paid")
            settled.setdefault(key, {})[jurisdiction] = _number(value, "Income tax already paid", inclusive=True)
    event = {"on": min(dates).isoformat(), "as_at": body["as_at"], "years": max(d.year for d in dates) - min(d.year for d in dates) + 1}
    c = {"case_id": name, "kind": "K6", "template": "recorded", "subject": "GROUP", "currency": body["currency"],
         "roles": roles, "names": names, "members": members, "holds": holds, "transactions": txs, "flows": flows,
         "present": {}, "settled": settled, "event": event, "documents": list((original or {}).get("documents", [])),
         "notes": ["Assessment of the recorded companies and dated transactions; no alternative structure is inferred."], "provenance": {}}
    from ..verify.casecheck import stated_paths
    old_prov = (original or {}).get("provenance", {})
    for path in stated_paths(c):
        retained = path.startswith("roles.") and ".attrs." in path or path.startswith("flows.") or path.startswith("settled.")
        c["provenance"][path] = old_prov.get(path) if retained and path in old_prov else {"kind": "reviewed", "source": source, "quote": ""}
    return c


def collection_preview(body, original=None):
    c = build_recorded_case(body, original)
    from ..run import _dates
    from ..scenarios import Case, RoleFacts, RECORDED
    from ..model import HoldEdge
    from ..data.domain import Event
    from ..fields import DERIVED, missing_fields
    d = _dates(c)
    case = Case(roles={r: RoleFacts(x["loc"], x["attrs"]) for r, x in d["roles"].items()},
                holds={(h["holder"], h["held"]): HoldEdge(h["holder"], h["held"], h["ratio"], h.get("since"), h.get("cost")) for h in d["holds"]},
                flows=d["flows"], transactions=d["transactions"], currency=d["currency"], members=set(d["members"]))
    g = RECORDED.build(Event(**d["event"]), {}, case)
    collection = {}
    for fid, key in sorted(missing_fields(g)):
        mount, name = key.split(".", 1)
        if name in DERIVED:
            continue
        tx = d["transactions"][fid]
        target = tx["payer"] if mount == "payer" else tx["payee"] if mount == "payee" else fid
        path = "roles.%s.attrs.%s" % (target, name) if mount in ("payer", "payee") else "flows.%s.%s" % (fid, name)
        spec = field_schema(key)
        collection[path] = {"path": path, "company": c["names"].get(target), "transaction": fid, **spec}
    return {"summary": {"companies": len(c["roles"]), "ownership": len(c["holds"]), "transactions": len(c["transactions"]),
                        "types": sorted({TRANSACTION_TYPES[x["income"]] for x in c["transactions"].values()})},
            "collection": list(collection.values()), "scope": "recorded"}
