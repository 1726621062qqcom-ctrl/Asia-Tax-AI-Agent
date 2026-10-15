"""Checks of the extraction boundary without a live model: a scripted responder stands in for the LLM, and the
program's own guarantees are what is tested — field specs come from the rules and the dictionary, a quote must be
found in the document, values are typed and unit-checked, unsupported fields stay missing, two readings must agree,
and nothing the model does (a failed call, a reply that is not JSON, a control character) stops the program.

    python -m tax_graph.check_extract          (conda env "pytorch")
"""
import io
import json
import sys
from datetime import date

from .llm.extract import BOOL, DATE, ENUM, NUMBER, Extraction, extract, field_specs, fill, provenance

DOCS = {
    "cor-2026": "Certificate of Resident Status. This is to certify that Holdco Ltd is a resident of Hong Kong for the year 2026.",
    "loan": "Loan agreement dated 2026-03-31. Interest is payable annually on 31 March. The lender holds 100% of the borrower's shares.",
    "accounts": 'Balance sheet 2025: related-party debt 4,000; equity 1,000. Receipt of the dividend was remitted ("remitted")\n'
                'to Singapore. The standard rate of corporate income tax in the PRC is 25%; non-resident\nenterprises pay 20%.',
}

SCRIPT = {   # what the stand-in model says; the checks below are about what the program does with it
    "payee.residence_cert": ({"doc": "cor-2026", "quote": "is a resident of Hong Kong for the year 2026"}, ["yes"]),
    "payer.related_party_debt_equity_ratio": ({"doc": "accounts", "quote": "related-party debt 4,000; equity 1,000"}, ["400%"]),
    "flow.receipt_kind": ({"doc": "accounts", "quote": "was remitted (“remitted”) to Singapore"}, ["REMITTED"]),   # curly quotes, line break
    "flow.payable_on": ({"doc": "loan", "quote": "Interest is payable annually on 31 March"}, ["2026-03-31"]),
    "payee.bo_safe_harbour": ({"doc": "cor-2026", "quote": "this passage is not in the certificate"}, ["true"]),   # fabricated quote
    "flow.is_equipment_lease": ({"doc": "loan", "quote": "Loan agreement dated 2026-03-31"}, ["maybe"]),           # not a boolean
    "flow.foreign_headline_rate": ({"doc": "accounts", "quote": "The standard rate of corporate income tax in the PRC is 25%"}, [25, 20]),  # samples disagree
    "flow.foreign_taxed": ({"doc": "accounts", "quote": "non-resident enterprises pay 20%"}, [True, None]),          # one sample unsure
    "flow.underlying_profits_taxed": ({"doc": "accounts", "quote": "The standard rate of corporate income tax"}, "RAISE"),   # the call fails
    "flow.deductible_at_payer": ({"doc": "accounts", "quote": "Balance sheet 2025"}, "GARBAGE"),                      # reply is not JSON
    "flow.holding_months": ({"doc": "loan", "quote": "The lender holds 100% of the borrower's shares"}, "CONTROL"),  # raw control char in JSON
}


def make_responder(log):
    calls = {}

    def responder(prompt: str) -> str:
        log.append(prompt)
        if prompt.startswith("For each field"):
            return json.dumps({key: [passage] for key, (passage, _) in SCRIPT.items() if "- %s " % key in prompt})
        key = prompt.split("FIELD: ", 1)[1].splitlines()[0].strip()
        passage, values = SCRIPT[key]
        n = calls[key] = calls.get(key, 0) + 1
        if values == "RAISE":
            raise ConnectionError("simulated outage")
        if values == "GARBAGE":
            return "I cannot answer in JSON"
        if values == "CONTROL":
            return '{"value": 13, "doc": "loan", "quote": "The lender holds 100%\tof the borrower\'s shares"}'
        v = values[(n - 1) % len(values)]
        return json.dumps({"value": v, "doc": passage["doc"], "quote": passage["quote"]})
    return responder


def main():
    out = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    specs = field_specs()
    results = []

    def check(ok, text):
        results.append(ok)
        out.write("%-4s %s\n" % ("ok" if ok else "FAIL", text))

    check(specs["payee.residence_cert"].kind == BOOL, "residence_cert is typed bool from its is_true predicate")
    check(specs["payer.related_party_debt_equity_ratio"].kind == NUMBER, "debt/equity ratio is typed number from its le predicate")
    check(specs["flow.receipt_kind"].kind == ENUM and "REMITTED" in specs["flow.receipt_kind"].allowed,
          "receipt_kind is an enum whose values come from the param (%s)" % "/".join(specs["flow.receipt_kind"].allowed))
    check(specs["flow.payable_on"].kind == DATE, "payable_on is a date")
    check(all(s.hint for s in specs.values() if s.key.split(".", 1)[1] in ("residence_cert", "receipt_kind")),
          "evidence hints come from 信息收集.md")
    check("居民企业" in specs["flow.foreign_headline_rate"].gloss and specs["flow.foreign_headline_rate"].unit == "%",
          "meaning and unit come from data/field_gloss.csv (foreign_headline_rate: %s)" % specs["flow.foreign_headline_rate"].gloss[:30])
    check(specs["payee.residence_cert_2026"].gloss == specs["payee.residence_cert"].gloss if "payee.residence_cert_2026" in specs else True,
          "a year-suffixed field reads its base field's gloss")

    log = []
    keys = list(SCRIPT) + ["flow.immovable_ratio"]            # the last one: no passage at all
    ex = extract(DOCS, keys, make_responder(log), specs)
    reasons = dict(ex.rejected)
    check(ex.facts.get(("payee", "residence_cert")) is True, "'yes' on a bool field becomes True, with its quote kept")
    check(ex.evidence.get(("payee", "residence_cert")) == ("cor-2026", "is a resident of Hong Kong for the year 2026"), "evidence = (doc, quote)")
    check(ex.facts.get(("payer", "related_party_debt_equity_ratio")) == 400.0, "'400%' becomes 400.0 (ratio facts are percent)")
    check(ex.facts.get(("flow", "receipt_kind")) == "REMITTED", "a quote with typographic quote marks across a line break is found (quotes.loose)")
    check(ex.facts.get(("flow", "payable_on")) == date(2026, 3, 31), "ISO date parsed")
    check(("payee", "bo_safe_harbour") not in ex.facts and "payee.bo_safe_harbour" in ex.missing,
          "a quote not found in the document is not evidence: the field stays missing (P4)")
    check(("flow", "is_equipment_lease") not in ex.facts and reasons.get("flow.is_equipment_lease") == "not a boolean",
          "'maybe' on a bool field is rejected, not guessed")
    check("flow.immovable_ratio" in ex.missing, "a field without passages is missing, not invented")
    check(("flow", "foreign_headline_rate") not in ex.facts and reasons.get("flow.foreign_headline_rate", "").startswith("samples disagree: 25.0 / 20.0"),
          "two readings that disagree leave the field missing, with both values recorded (%s)" % reasons.get("flow.foreign_headline_rate"))
    check(("flow", "foreign_taxed") not in ex.facts and reasons.get("flow.foreign_taxed", "").startswith("samples disagree: True / null"),
          "a reading that is sure and one that is not: missing (%s)" % reasons.get("flow.foreign_taxed"))
    check(("flow", "underlying_profits_taxed") not in ex.facts and reasons.get("flow.underlying_profits_taxed") == "model call failed"
          and any("ConnectionError" in n for n in ex.notes), "a call that raises: the field is missing, the exception is a note, the run goes on")
    check(("flow", "deductible_at_payer") not in ex.facts and reasons.get("flow.deductible_at_payer") == "reply is not JSON",
          "a reply that is not JSON is rejected with the reason")
    check(ex.facts.get(("flow", "holding_months")) == 13.0, "a raw control character inside a JSON string does not break the reading")
    reads = [p for p in log if p.startswith("Read the value")]
    check(sum(1 for p in reads if "FIELD: payee.residence_cert" in p) == 2, "a field is read twice by default (samples=2)")
    check(all("MEANING:" in p and "Answer null unless" in p for p in reads), "the read prompt carries the field's meaning and the guard")
    one = extract(DOCS, ["flow.foreign_headline_rate"], make_responder([]), specs, samples=1)
    check(one.facts.get(("flow", "foreign_headline_rate")) == 25.0, "samples=1 takes the single reading")

    dead = extract(DOCS, ["payee.residence_cert"], lambda p: "no json here", specs)
    check(dead.missing == ["payee.residence_cert"] and any("not JSON" in n for n in dead.notes),
          "a locate reply that is not JSON: every field missing, noted, no exception")
    down = extract(DOCS, ["payee.residence_cert"], lambda p: (_ for _ in ()).throw(TimeoutError("down")), specs)
    check(down.missing == ["payee.residence_cert"] and any("TimeoutError" in n for n in down.notes),
          "a locate call that raises: every field missing, noted, no exception")

    prov = provenance(ex, lambda k: "flows.up1.%s" % k[1] if k[0] == "flow" else "roles.%s.attrs.%s" % (k[0].upper(), k[1]))
    check(prov.get("roles.PAYEE.attrs.residence_cert") == {"kind": "disclosed", "source": "cor-2026", "quote": "is a resident of Hong Kong for the year 2026"},
          "provenance rows follow 案例采集.md §4.2 (disclosed, source, quote)")
    case = {"roles": {"ULT": {"loc": "HK", "attrs": {"residence_cert": False}}}, "flows": {"up1": {}}, "provenance": {}, "notes": []}
    filled = fill(case, {"facts": {"roles.ULT.attrs.residence_cert": True, "flows.up1.receipt_kind": "REMITTED"},
                         "provenance": {"flows.up1.receipt_kind": prov["flows.up1.receipt_kind"]}, "model": "stub", "docs": ["accounts"]})
    check(filled["roles"]["ULT"]["attrs"]["residence_cert"] is False and filled["flows"]["up1"]["receipt_kind"] == "REMITTED"
          and case["flows"]["up1"] == {} and len(filled["notes"]) == 1, "fill() keeps stated values, adds the rest with a review note, never edits in place")

    out.write("%d checks, %d failures\n" % (len(results), results.count(False)))
    out.flush()
    return 1 if False in results else 0


if __name__ == "__main__":
    sys.exit(main())
