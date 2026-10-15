"""Typed UI inputs. The rule field dictionary remains the source of field types."""
import math
import re
from datetime import date
from functools import lru_cache


TEMPLATES = {
    "holding": {"label": "Holding and share disposal", "roles": ["OP", "ULT"], "amounts": ["dividend", "exit"]},
    "repatriation": {"label": "Profit repatriation", "roles": ["OP", "ULT"], "amounts": ["dividend"]},
    "ip": {"label": "Intellectual property", "roles": ["OP", "ULT"], "amounts": ["royalty"]},
    "services": {"label": "Group services", "roles": ["OP", "ULT", "SERVICER"], "amounts": ["service_fee"]},
    "inbound_services": {"label": "Services to an external client", "roles": ["SERVICER", "CLIENT"], "amounts": ["service_fee"]},
    "financing": {"label": "External financing", "roles": ["OP", "ULT", "LENDER"], "amounts": ["interest"]},
    "trading": {"label": "Goods trading", "roles": ["OP", "ULT", "CUSTOMER"], "amounts": ["goods_sale", "goods_supply"]},
    "property": {"label": "Property sale or letting", "roles": ["OWNER", "ULT"], "amounts": ["property_sale", "property_rent"]},
}
ROLE_LABELS = {"OP": "Operating company", "ULT": "Parent company", "HOLD": "Intermediate holding company", "BUYER": "Buyer",
               "IPCO": "IP company", "SERVICER": "Service provider", "CLIENT": "External client", "LENDER": "Lender",
               "TRADER": "Trading company", "CUSTOMER": "Customer", "OWNER": "Property owner", "TENANT": "Tenant"}
ENUM_LABELS = {"REMITTED": "Remitted into the jurisdiction", "NONE": "Not received in the jurisdiction",
               "DEBT_SETTLED": "Used to settle local business debts", "MOVABLE_PROPERTY": "Used to purchase movable property brought in",
               "CN": "Mainland China", "HK": "Hong Kong", "SG": "Singapore"}


@lru_cache(maxsize=1)
def schemas():
    from ..llm.extract import field_specs, _glosses, UNIT_KIND
    fields = {}
    for key, s in field_specs().items():
        name = key.split(".", 1)[1]
        row = fields.setdefault(name, {"kind": s.kind, "label": s.gloss or name.replace("_", " "), "unit": s.unit,
                                       "options": [], "source_hint": s.hint})
        row["options"] = sorted(set(row["options"]) | set(s.allowed))
    # Derived and year-specific inputs may be read by procedures rather than condition leaves.
    for name, g in _glosses().items():
        fields.setdefault(name, {"kind": UNIT_KIND.get(g.get("value", ""), "text"), "label": g.get("gloss") or name.replace("_", " "),
                                 "unit": g.get("value", ""), "options": [], "source_hint": g.get("source_hint", "")})
    # Membership predicates list the qualifying values only. NONE is the explicit non-receipt fact used by the engine.
    if "receipt_kind" in fields:
        fields["receipt_kind"]["options"].append("NONE")
    for name, row in fields.items():
        if name.endswith("_eur") and row["kind"] == "number":
            row["unit"] = "EUR"
    return {"templates": TEMPLATES, "roles": ROLE_LABELS, "fields": fields, "option_labels": ENUM_LABELS}


def field_schema(key, hint=""):
    from ..llm.extract import UNIT_KIND
    name = key.rsplit(".", 1)[-1]
    base = re.sub(r"_(?:cn|hk|sg|\d{4})$", "", name)
    s = dict(schemas()["fields"].get(name) or schemas()["fields"].get(base) or
             {"kind": "number" if name == "amount" else "any", "label": name.replace("_", " "), "options": [], "unit": "amount" if name == "amount" else ""})
    if s["kind"] == "any" and hint:
        s.update(kind=UNIT_KIND.get(hint, "text"), unit=hint)
    return s


def typed_value(key, value, hint=""):
    s = field_schema(key, hint)
    kind = s["kind"]
    if value == "unknown":
        return value
    if kind == "bool":
        if type(value) is not bool:
            raise ValueError("%s: choose Yes, No or Unknown" % s["label"])
    elif s["options"]:
        if not isinstance(value, str) or value not in s["options"]:
            raise ValueError("%s: choose one of the available options" % s["label"])
    elif kind == "number":
        if type(value) not in (int, float) or not math.isfinite(value):
            raise ValueError("%s: enter a finite number" % s["label"])
    elif kind == "date":
        if not isinstance(value, str):
            raise ValueError("%s: enter a date" % s["label"])
        date.fromisoformat(value)
    elif kind == "any":
        if not isinstance(value, (str, bool, int, float)) or (type(value) in (int, float) and not math.isfinite(value)):
            raise ValueError("Enter a supported scalar value")
    elif not isinstance(value, str):
        raise ValueError("%s: enter text" % s["label"])
    return value


def validate_answers(answers, questions=None):
    hints = {q["key"]: q.get("value", "") for q in questions or []}
    for section, rows in answers.items():
        if section not in ("data", "actions", "rulings", "library") or not isinstance(rows, dict):
            raise ValueError("Invalid answer section")
        for key, item in rows.items():
            if section in ("actions", "rulings"):
                if item not in ("yes", "no", "unknown"):
                    raise ValueError("Choose Yes, No or Unknown")
            elif section == "data":
                if item == "unknown":
                    continue
                if not isinstance(item, dict) or "value" not in item:
                    raise ValueError("An answer needs a value and its source")
                typed_value(key, item["value"], hints.get(key, ""))
                if not str(item.get("source") or "").strip():
                    raise ValueError("Please provide a source for each known fact")
    for q in questions or []:
        sec = {"action": "actions", "ruling": "rulings", "library": "library"}.get(q["kind"], "data")
        if q["key"] not in answers.get(sec, {}):
            raise ValueError("Answer every question, or explicitly choose Unknown")


def build_case(body):
    """Build only facts supplied by the user; no copied example facts or invented tax attributes."""
    template = body.get("template")
    if template not in TEMPLATES:
        raise ValueError("Choose a supported analysis type")
    case_id = str(body.get("case_id") or "").strip()
    if not case_id:
        raise ValueError("Enter a case name")
    currency = body.get("currency")
    if currency not in ("CNY", "HKD", "SGD", "USD", "EUR"):
        raise ValueError("Choose the currency used for all case amounts")
    event = {"on": body.get("on"), "as_at": body.get("as_at")}
    for k in ("on", "as_at"):
        date.fromisoformat(event[k] or "")
    years = body.get("years", 1)
    if type(years) is not int or not 1 <= years <= 30:
        raise ValueError("The modelling period must be 1–30 years")
    event["years"] = years
    for k in TEMPLATES[template]["amounts"]:
        v = body.get("amounts", {}).get(k)
        if v is not None:
            if type(v) not in (int, float) or not math.isfinite(v) or v <= 0:
                raise ValueError("%s must be a positive amount" % k.replace("_", " "))
            event[k] = v
    if not any(k in event for k in TEMPLATES[template]["amounts"] if k != "goods_supply"):
        raise ValueError("Enter at least one transaction amount")
    required = list(TEMPLATES[template]["roles"])
    if event.get("exit") or event.get("property_sale"):
        required.append("BUYER")
    if event.get("property_rent"):
        required.append("TENANT")
    roles, names = {}, {}
    for role in required:
        v = body.get("roles", {}).get(role, {})
        if v.get("loc") not in ("CN", "HK", "SG") or not str(v.get("name") or "").strip():
            raise ValueError("Provide a company name and jurisdiction for %s" % ROLE_LABELS[role])
        roles[role] = {"loc": v["loc"], "attrs": {}}
        names[role] = v["name"].strip()
    present = {"holding": {"HOLD": None, "financing": "EQUITY", "exit_route": "DIRECT", "payment": False},
               "repatriation": {"HOLD": None, "repatriation": "DIVIDEND", "payment": False},
               "ip": {"IPCO": None, "payment": False, "ip_transfer": "MARKET"}, "services": {"SERVICER": roles.get("SERVICER", {}).get("loc"), "payment": False},
               "financing": {"LENDER": roles.get("LENDER", {}).get("loc"), "payment": False}, "trading": {"TRADER": None, "payment": False}}.get(template, {})
    holds = []
    if "ULT" in roles:
        for held in ("OP", "OWNER", "SERVICER"):
            if held not in roles:
                continue
            stake = body.get("holdings", {}).get(held, {})
            ratio = stake.get("ratio")
            if type(ratio) not in (int, float) or not math.isfinite(ratio) or not 0 < ratio <= 100:
                raise ValueError("Provide the parent's ownership percentage in %s" % ROLE_LABELS[held])
            h = {"holder": "ULT", "held": held, "ratio": ratio}
            if stake.get("since"):
                date.fromisoformat(stake["since"])
                h["since"] = stake["since"]
            if stake.get("cost") is not None:
                cost = stake["cost"]
                if type(cost) not in (int, float) or not math.isfinite(cost) or cost < 0:
                    raise ValueError("Acquisition cost must be zero or positive")
                h["cost"] = cost
            holds.append(h)
    source = str(body.get("source") or "").strip()
    if not source:
        raise ValueError("State the source of the facts you entered")
    prov = {"event." + k: {"kind": "reviewed", "source": source, "quote": ""} for k in event}
    for k in present:
        prov["present." + k] = {"kind": "reviewed", "source": source, "quote": ""}
    for r in roles:
        prov["roles.%s.loc" % r] = {"kind": "reviewed", "source": source, "quote": ""}
    for h in holds:
        for k in ("ratio", "since", "cost"):
            if k in h:
                prov["holds.ULT>%s.%s" % (h["held"], k)] = {"kind": "reviewed", "source": source, "quote": ""}
    return {"case_id": case_id, "kind": "K6", "template": template, "currency": currency, "subject": "GROUP", "roles": roles,
            "names": names, "holds": holds, "flows": {}, "present": present, "settled": {}, "event": event, "provenance": prov,
            "notes": [], "documents": []}
