"""Checks of the extraction boundary without a live model: a scripted responder stands in for the LLM, and the
program's own guarantees are what is tested — field specs come from the rules and the dictionary, a quote must be
found in the document, a number or a date must be in its quote, readings of one passage must agree, readings of
different passages that differ are a conflict, patterns settle fixed wordings before any model, channels not meant
for the model are listed for a person, and nothing the model does (a failed call, a reply that is not JSON, a control
character) stops the program.

    python -m tax_graph.check_extract          (conda env "pytorch")
"""
import io
import json
import sys
from datetime import date
from pathlib import Path

from .llm.extract import (ASK_CHANNELS, BOOL, DATE, ENUM, NUMBER, FieldSpec, _in_quote, _prompt_locate, constraints, dates_in,
                          extract, extract_case, field_specs, fill, numbers_in, provenance)
from .llm.locate import PassageIndex, query_for
from .llm.patterns import defined_terms, names_match, pattern_candidates, scale_hint
from .llm.tables import revenue, rows, table_candidates, to_eur, year_end_rate_date
from .registry import cross_check, files as registry_files
from .fields import DERIVED

DOCS = {
    "cor-2026": "Certificate of Resident Status. This is to certify that Holdco Ltd is a resident of Hong Kong for the year 2026.\n\n"
                "Tax residence certificate issued by the Inland Revenue Department on 22 November 2026.",
    "loan": "Loan agreement dated 2026-03-31. Interest is payable annually on 31 March. The lender holds 100% of the borrower's shares.\n\n"
            "The loan term is 13 months. Interest accrues at 5% per annum. The borrower, Opco Limited, is a company incorporated in "
            "Hong Kong with limited liability.",
    "accounts": 'Balance sheet 2025: related-party debt 4,000; equity 1,000. Receipt of the dividend was remitted ("remitted")\n'
                'to Singapore. The standard rate of corporate income tax in the PRC is 25%; non-resident\nenterprises pay 20%.\n\n'
                "The consideration for the acquisition was RMB68,000,000. Opco Limited, a company incorporated in the Cayman Islands, "
                "is the vendor.\n\n(RMB'000)\nRevenue 1,234\nCost of sales 567",
    "report": "Accountants' report. The consideration paid for the Target was RMB67,731,000. Target Co was established in the PRC on "
              "5 May 2023.",
}


def P(doc, quote):
    return {"doc": doc, "quote": quote}


SCRIPT = {   # field -> [(passage the locate step names, what the read step answers for that passage), ...]
    "payee.residence_cert": [(P("cor-2026", "is a resident of Hong Kong for the year 2026"), ["yes"])],
    "payer.related_party_debt_equity_ratio": [(P("accounts", "related-party debt 4,000; equity 1,000"), ["400%"])],   # computed, not stated
    "flow.receipt_kind": [(P("accounts", "was remitted (“remitted”) to Singapore"), ["REMITTED"])],          # curly quotes, line break
    "flow.payable_on": [(P("loan", "Loan agreement dated 2026-03-31. Interest is payable annually on 31 March."), ["2026-03-31"])],
    "payee.bo_safe_harbour": [(P("cor-2026", "This is to certify that Holdco Ltd is a resident of Hong Kong"),
                               [{"value": True, "quote": "this passage is not in the certificate"}])],          # fabricated quote
    "flow.is_equipment_lease": [(P("loan", "Loan agreement dated 2026-03-31"), ["maybe"])],                      # not a boolean
    "flow.foreign_headline_rate": [(P("accounts", "The standard rate of corporate income tax in the PRC is 25%; non-resident\nenterprises pay 20%"),
                                    [25, 20])],                                                                  # samples disagree
    "flow.foreign_taxed": [(P("accounts", "non-resident enterprises pay 20%"), [True, None])],                   # one sample unsure
    "flow.underlying_profits_taxed": [(P("accounts", "The standard rate of corporate income tax"), "RAISE")],    # the call fails
    "flow.deductible_at_payer": [(P("accounts", "Balance sheet 2025"), "GARBAGE")],                              # reply is not JSON
    "flow.holding_months": [(P("loan", "The loan term is 13 months"), "CONTROL")],                               # raw control char in JSON
    "flow.cost_basis": [(P("accounts", "equity 1,000"), ["approximately RMB1,000 thousand"])],                   # prose on a number field
    "payer.gross_revenue": [(P("accounts", "Revenue 1,234"), [1234000])],                                        # table in RMB'000
    "flow.operating_costs": [(P("accounts", "Cost of sales 567"), [{"value": 567, "quote": "567"}])],               # a bare figure as the quote
    "flow.arms_length_value": [(P("accounts", "The consideration for the acquisition was RMB68,000,000."), [68000000]),
                               (P("report", "The consideration paid for the Target was RMB67,731,000."), [67731000])],   # two passages, two values
    "flow.interest_rate": [(P("loan", "Interest accrues at 5% per annum."), [5]),
                           (P("accounts", "Balance sheet 2025: related-party debt 4,000; equity 1,000."), [None])],      # one passage not about it
}


def make_responder(log):
    calls = {}

    def responder(prompt: str) -> str:
        log.append(prompt)
        if "For each field below" in prompt:
            return json.dumps({key: [p for p, _ in entries] for key, entries in SCRIPT.items() if "- %s (" % key in prompt})
        key = prompt.split("FIELD: ", 1)[1].splitlines()[0].strip()
        if key.endswith(".incorporated_in"):                       # read the jurisdiction the passage itself states
            passage = prompt.split("PASSAGES", 1)[1]
            v = "HK" if "incorporated in Hong Kong" in passage else "KY" if "Cayman" in passage else "CN" if "the PRC" in passage else None
            quote = {"HK": "Opco Limited, is a company incorporated in Hong Kong with limited liability", "KY": "Opco Limited, a company incorporated in the Cayman Islands, is the vendor",
                     "CN": "Target Co was established in the PRC on 5 May 2023."}.get(v, "")
            return json.dumps({"value": v, "doc": {"HK": "loan", "KY": "accounts", "CN": "report"}.get(v), "quote": quote})
        entries = SCRIPT.get(key)
        if not entries:
            return json.dumps({"value": None})
        for passage, values in entries:
            if passage["quote"][:40] in prompt:
                break
        else:
            passage, values = entries[0]                        # retrieval passages: the script answers all the same
        n = calls[(key, passage["doc"])] = calls.get((key, passage["doc"]), 0) + 1
        if values == "RAISE":
            raise ConnectionError("simulated outage")
        if values == "GARBAGE":
            return "I cannot answer in JSON"
        if values == "CONTROL":
            return '{"value": 13, "doc": "loan", "quote": "The loan\tterm is 13 months"}'
        v = values[(n - 1) % len(values)]
        reply = {"value": v, "doc": passage["doc"], "quote": passage["quote"]}
        if isinstance(v, dict):
            reply.update(v)
        return json.dumps(reply)
    return responder


def main():
    out = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    specs = field_specs()
    results = []

    def check(ok, text):
        results.append(ok)
        out.write("%-4s %s\n" % ("ok" if ok else "FAIL", text))

    # ---------------------------------------------------------------- specs
    check(specs["payee.residence_cert"].kind == BOOL, "residence_cert is typed bool from its is_true predicate")
    check(specs["payer.related_party_debt_equity_ratio"].kind == NUMBER, "debt/equity ratio is typed number from its le predicate")
    check(specs["flow.receipt_kind"].kind == ENUM and "REMITTED" in specs["flow.receipt_kind"].allowed,
          "receipt_kind is an enum whose values come from the param (%s)" % "/".join(specs["flow.receipt_kind"].allowed))
    check(specs["flow.payable_on"].kind == DATE, "payable_on is a date")
    check(all(s.hint for s in specs.values() if s.key.split(".", 1)[1] in ("residence_cert", "receipt_kind")), "evidence hints come from 信息收集.md")
    check("resident enterprises" in specs["flow.foreign_headline_rate"].gloss and specs["flow.foreign_headline_rate"].unit == "%",
          "meaning and unit come from data/field_gloss.csv (foreign_headline_rate: %s)" % specs["flow.foreign_headline_rate"].gloss[:30])
    check(specs["flow.cost_basis"].kind == NUMBER and specs["flow.arms_length_value"].kind == NUMBER,
          "a field no predicate compares is typed from its gloss unit (cost_basis, arms_length_value: amount -> number), not text")
    check(all(s.channel in ("A", "B", "C", "D", "E", "X", "") for s in specs.values()) and sum(1 for s in specs.values() if s.channel == "E") > 40,
          "channels come from the dictionary (%d fields in E)" % sum(1 for s in specs.values() if s.channel == "E"))
    check(specs["flow.receipt_kind"].examples and specs["flow.receipt_kind"].examples in query_for(specs["flow.receipt_kind"])
          and "receipt kind" in query_for(specs["flow.receipt_kind"]), "the retrieval query carries the field's name words and example phrasings")

    # ---------------------------------------------------------------- the program reads figures and dates
    check(numbers_in("RMB46.8 million") == [46.8, 46800000.0] and 266200000.0 in numbers_in("约 2.662 亿") and numbers_in("12,345") == [12345.0]
          and numbers_in("25%") == [25.0] and 1234000.0 in numbers_in("Revenue 1,234", 1000) and 30000000.0 in numbers_in("US$30,000,000"),
          "numbers_in resolves million / 亿 / thousands separators / % / a table scale")
    check(dates_in("on 22 November 2024") == [date(2024, 11, 22)] and dates_in("May 5, 2023") == [date(2023, 5, 5)]
          and dates_in("2024年11月22日") == [date(2024, 11, 22)] and dates_in("dated 2026-03-31") == [date(2026, 3, 31)] and dates_in("on 31 March") == [],
          "dates_in reads ISO, Chinese, '22 November 2024' and 'May 5, 2023'; a day and month without a year is no date")
    check(_in_quote(specs["flow.payable_on"], date(2026, 3, 31), "Interest is payable annually on 31 March") == "no date in the quote"
          and _in_quote(specs["flow.cost_basis"], 46800000.0, "consideration of RMB46.8 million") is None
          and (_in_quote(specs["flow.cost_basis"], 46800000.0, "the consideration") or "").startswith("no figure"),
          "a number or a date is accepted only when the quote states it")
    check(scale_hint("Results\n(RMB'000)\nRevenue 1,234", 20) == 1000 and scale_hint("Revenue 1,234", 8) is None, "a table header's RMB'000 is read as a scale")

    # ---------------------------------------------------------------- patterns before any model
    hits = pattern_candidates("incorporated_in", DOCS)
    check({h["value"] for h in hits} == {"HK", "KY", "CN"} and all(h["quote"] in DOCS[h["doc"]] for h in hits),
          "the incorporation pattern finds every mention with its verbatim sentence (%d hits)" % len(hits))
    check([h["value"] for h in pattern_candidates("incorporated_in", DOCS, about="Target Co")] == ["CN"], "`about` keeps the sentences that name the party")
    check(pattern_candidates("ratio", DOCS)[0]["value"] == 100.0, "'holds 100%' is read as a percentage by the pattern")
    check(names_match("Freetech Smart Road Recycling Engineering Investment Limited", "Freetech Smart Road Recycling Engineering Investment Ltd.") == 1.0
          and names_match("Tianjin Expressway Group Company Limited", "Holdco Ltd") < 0.5, "company names match without legal-form suffixes")
    terms = defined_terms('“Vendor” means Freetech Smart Road Recycling Engineering Investment Limited, a company incorporated in Hong Kong\n“Purchaser” Tianjin Expressway Group Company Limited, a company established in the PRC')
    check(terms.get("Vendor", "").startswith("means Freetech") and "Purchaser" in terms, "a definitions section parses into term -> definition")

    # ---------------------------------------------------------------- tables: statement rows read by program
    FS = ("Summary consolidated statements\nYear ended 31 December\n2023\n2024\nRMB’000\nRMB’000\n(unaudited)\nRevenue\n. . . . . . .\n1,583,082\n2,000,000\n"
          "Cost of sales . . . . .\n(1,018,000)\n(1,200,000)\nGross profit 5 565,082 800,000\n\nSummary in millions\n2023\n2024\n(RMB in millions)\nRevenue\n1,583.1\n2,000.0\n")
    rs = rows(FS)
    check(len(rs) == 4 and rs[0]["label"] == "Revenue" and rs[0]["values"] == {2023: 1583082000.0, 2024: 2000000000.0} and rs[0]["currency"] == "CNY"
          and rs[1]["values"][2023] == -1018000000.0 and rs[2]["label"] == "Gross profit" and rs[2]["values"][2024] == 800000000.0 and FS[rs[0]["start"]:rs[0]["end"]] == rs[0]["quote"]
          and rs[3]["values"][2023] == 1583100000.0,
          "a cell-per-line table and a row-on-one-line (with a note reference) parse into rows with the header's years, scale and currency; quotes are verbatim (%d rows)" % len(rs))
    dup = rows("Year ended 31 December Six months ended 30 June\n2023\n2024\n2024\n2025\nRMB’000\nRMB’000\nRMB’000\nRMB’000\n(Unaudited)\nRevenue\n6\n697,191\n909,750\n420,973\n523,642\n")
    check(len(dup) == 1 and dup[0]["values"] == {2023: 697191000.0, 2024: 909750000.0} and dup[0]["columns"][2] == (2024, 420973000.0, "interim")
          and dup[0]["columns"][3] == (2025, 523642000.0, "interim"),
          "a year that repeats opens the months-ended columns: full-year values only, the interim columns stay in `columns`")
    back = rows("(RMB in thousands, except percentages)\n2023 2024 2025\nRMB % RMB % RMB %\nRevenue 697,191 100.0 909,750 100.0 523,642 100.0\n")
    check(len(back) == 1 and back[0]["unit_stated"] and back[0]["values"][2024] == 909750000.0 and back[0]["currency"] == "CNY",
          "years on one line with the unit stated above them: the unit is read from the lines before the years")
    rv = revenue({"fs": FS}, 2024)
    check(rv["rows"] == 2 and rv["value"] == 2000000000.0 and len(rv["distinct"]) == 1 and rv["distinct"][0]["scale"] == 1000.0,
          "two revenue rows that agree across scales (RMB'000 vs millions) give one value, the finer scale kept")
    tc = table_candidates("gross_revenue", {"fs": FS})
    check(len(tc) == 2 and tc[0]["channels"] == ["table"] and "2023" in tc[0]["quote"] and "1,583,082" in tc[0]["quote"], "a statement row with its header is a candidate passage for the reader")
    on = year_end_rate_date(2024)
    eur, how = to_eur(2000000000.0, "CNY", on) if on else (None, "no rate")
    check(on == date(2024, 12, 31) and eur is not None and abs(eur - 2000000000.0 / 7.5257) < 1 and how["pairs"]["EUR/CNY"] == 7.5257,
          "revenue converts to EUR by the library's year-end central parity (2024-12-31 EUR/CNY 7.5257)")

    # ---------------------------------------------------------------- a field in EUR: the program derives it (table, or the model's sentence + program-read currency)
    from .llm.extract import _derive_eur, _path_of
    from .run import load_case as _load_case
    _t, _c, _e, _, _, _ = _load_case(Path(__file__).resolve().parents[1] / "cases" / "meridian.json")
    _g = _t.build(_e, _c.present, _c)
    _f = _g.flows[0]
    res = {"facts": {}, "provenance": {}, "conflicts": {}, "violations": [], "missing": [], "rejected": [], "notes": [], "features": {}}
    _derive_eur(_f, _g, {"fs": FS}, ["payee.group_revenue_eur"], res, _path_of(_f.id, _f.payer, _f.payee))
    p = _path_of(_f.id, _f.payer, _f.payee)(("payee", "group_revenue_eur"))
    y = _f.on.year - 1
    want = 2000000000.0 / 7.5257 if y == 2024 else None
    check(want is not None and abs(res["facts"].get(p, 0) - want) < 1 and res["provenance"][p]["kind"] == "derived" and "D17" in res["provenance"][p]["formula"],
          "payee.group_revenue_eur is derived by program from the revenue row of %d and the year-end rate, the D17 substitution noted (%s)" % (y, res["facts"].get(p)))

    def prose_model(prompt):
        if "FIELD: payee.group_revenue" in prompt:
            return json.dumps({"value": 41800000000, "doc": "p", "quote": "Our net revenue was US$41.8 billion in 2024."})
        return json.dumps({"value": None})
    res = {"facts": {}, "provenance": {}, "conflicts": {}, "violations": [], "missing": [], "rejected": [], "notes": [], "features": {}}
    _derive_eur(_f, _g, {"p": "Annual letter.\n\nOur net revenue was US$41.8 billion in 2024."}, ["payee.group_revenue_eur"], res, _path_of(_f.id, _f.payer, _f.payee),
                prose_model, samples=1, locate="retrieval", k=3, dense=False)
    check(abs(res["facts"].get(p, 0) - 41800000000 * 7.1884 / 7.5257) < 1 and "USD" in res["provenance"][p]["formula"] and "named by the model" in res["provenance"][p]["quote"] + res["provenance"][p]["formula"],
          "with no statement table, the model names the revenue sentence; the program parses 41.8 billion and the US$ before it and converts (%s)" % res["facts"].get(p))

    # ---------------------------------------------------------------- registry: file drop and cross-checks
    import tempfile
    drop = Path(tempfile.mkdtemp()) / "registry"
    (drop / "HK").mkdir(parents=True)
    (drop / "HK" / "x.json").write_text(json.dumps({"id": "1234567", "name": "TOP VICTORY DEVELOPMENT LIMITED", "status": "Live", "incorporated_on": "2009-03-18",
                                                     "source": "copied from e-Services", "retrieved_at": "2026-10-15"}), encoding="utf-8")
    recs = registry_files.lookup("HK", "Top Victory Development Ltd / Top Victory", drop)
    check(len(recs) == 1 and recs[0]["jur"] == "HK" and recs[0]["id"] == "1234567", "a record a person dropped in cases/registry/HK is found by name (legal suffixes ignored)")
    from .run import load_case
    template, mcase, mevent, _, _, _ = load_case(Path(__file__).resolve().parents[1] / "cases" / "meridian.json")
    mg = template.build(mevent, mcase.present, mcase)
    role = next(iter(mg.entities))
    rec = {"jur": "HK" if mg.entities[role].loc != "HK" else "SG", "id": "1", "name": "Some Other Name Ltd", "status": "Dissolved", "incorporated_on": "2099-01-01", "source": "s", "retrieved_at": "t"}
    rf, rp, rc, rv, rn = cross_check(mg, mcase, {role: "Meridian Holdings Limited"}, {role: rec})
    check(not rf and ("roles.%s.loc" % role) in rc and any(p == "roles.%s.loc" % role for p, _ in rv) and any("similarity" in n for n in rn) and any("registered status" in n for n in rn),
          "a record in another register than the case's jurisdiction is a conflict and a violation; name similarity and non-live status are notes")

    # ---------------------------------------------------------------- extract with a scripted model, locate by the model
    jur = ("CN", "HK", "SG", "KY", "VG", "VN")
    specs2 = dict(specs)
    specs2["payer.incorporated_in"] = FieldSpec("payer.incorporated_in", ENUM, (), allowed=jur, about="Target Co")
    specs2["payee.incorporated_in"] = FieldSpec("payee.incorporated_in", ENUM, (), allowed=jur, about="Opco Limited")
    log = []
    keys = list(SCRIPT) + ["flow.immovable_ratio", "payer.incorporated_in", "payee.incorporated_in"]   # immovable_ratio: no passage at all
    ex = extract(DOCS, keys, make_responder(log), specs2, locate="llm")
    reasons = dict(ex.rejected)
    check(ex.facts.get(("payee", "residence_cert")) is True, "'yes' on a bool field becomes True, with its quote kept")
    check(ex.evidence.get(("payee", "residence_cert")) == ("cor-2026", "is a resident of Hong Kong for the year 2026"), "evidence = (doc, quote)")
    check(("payer", "related_party_debt_equity_ratio") not in ex.facts and reasons.get("payer.related_party_debt_equity_ratio", "").startswith("value not in the quote"),
          "a computed ratio (400 from 4,000 / 1,000) is refused: the quote does not state it (%s)" % reasons.get("payer.related_party_debt_equity_ratio"))
    check(ex.facts.get(("flow", "receipt_kind")) == "REMITTED", "a quote with typographic quote marks across a line break is found (quotes.loose)")
    check(ex.facts.get(("flow", "payable_on")) == date(2026, 3, 31), "an ISO date stated in the quote is accepted")
    check(("payee", "bo_safe_harbour") not in ex.facts and reasons.get("payee.bo_safe_harbour") == "quote not found in the document",
          "a quote not found in the document is not evidence: the field stays missing (P4)")
    check(("flow", "is_equipment_lease") not in ex.facts and reasons.get("flow.is_equipment_lease") == "not a boolean", "'maybe' on a bool field is rejected, not guessed")
    check("flow.immovable_ratio" in ex.missing and ex.features["flow.immovable_ratio"] == {"passages": 0}, "a field without passages is missing, not invented")
    check(("flow", "foreign_headline_rate") not in ex.facts and reasons.get("flow.foreign_headline_rate", "").startswith("samples disagree: 25.0 / 20.0"),
          "two readings of one passage that disagree leave the field missing, both values recorded (%s)" % reasons.get("flow.foreign_headline_rate"))
    check(("flow", "foreign_taxed") not in ex.facts and reasons.get("flow.foreign_taxed", "").startswith("samples disagree: True / null"),
          "a reading that is sure and one that is not: missing (%s)" % reasons.get("flow.foreign_taxed"))
    check(("flow", "underlying_profits_taxed") not in ex.facts and reasons.get("flow.underlying_profits_taxed") == "model call failed"
          and any("ConnectionError" in n for n in ex.notes), "a call that raises: the field is missing, the exception is a note, the run goes on")
    check(("flow", "deductible_at_payer") not in ex.facts and reasons.get("flow.deductible_at_payer") == "reply is not JSON", "a reply that is not JSON is rejected with the reason")
    check(ex.facts.get(("flow", "holding_months")) == 13.0, "a raw control character inside a JSON string does not break the reading")
    check(("flow", "cost_basis") not in ex.facts and reasons.get("flow.cost_basis") == "not a number", "an amount written as prose on a number field is rejected, not stored as text")
    check(ex.facts.get(("payer", "gross_revenue")) == 1234000.0, "1,234 under an RMB'000 header is accepted as 1,234,000 (the program applies the table scale)")
    check(("flow", "operating_costs") not in ex.facts and reasons.get("flow.operating_costs", "").startswith("quote is a bare figure"),
          "a quote that is only a figure (a table cell) is not evidence: rejected")
    cf = ex.conflicts.get("flow.arms_length_value", [])
    check(("flow", "arms_length_value") not in ex.facts and len(cf) == 2 and {c["value"] for c in cf} == {68000000.0, 67731000.0}
          and {c["doc"] for c in cf} == {"accounts", "report"} and cf[0]["origin"] == "different documents" and cf[0]["kind"] == NUMBER
          and reasons.get("flow.arms_length_value", "").startswith("conflict:"),
          "two passages read separately with different values: a conflict, both values with their quotes, no value taken")
    check(ex.facts.get(("flow", "interest_rate")) == 5.0, "a passage that does not settle the field beside one that does is not a disagreement")
    check(ex.facts.get(("payer", "incorporated_in")) == "CN" and ex.evidence[("payer", "incorporated_in")][0] == "report"
          and sum(1 for p in log if "FIELD: payer.incorporated_in" in p) == 2 and ex.features["payer.incorporated_in"]["pattern_hits"] == 1
          and ex.features["payer.incorporated_in"]["channels"] == ["pattern"],
          "a pattern's sentence near the party's name is a candidate the model reads (twice, as the only passage); the value comes from the reading")
    pc = ex.conflicts.get("payee.incorporated_in", [])
    check(("payee", "incorporated_in") not in ex.facts and {c["value"] for c in pc} == {"HK", "KY"} and "payee.incorporated_in" in ex.missing
          and ex.features["payee.incorporated_in"]["pattern_hits"] == 2 and sum(1 for p in log if "FIELD: payee.incorporated_in" in p) == 2,
          "two pattern sentences about one party (loan: Hong Kong, accounts: Cayman) are read separately: a conflict, not a choice")
    check(pattern_candidates("incorporated_in", DOCS, about="Holdco Ltd") == [], "a pattern sentence that does not name the party nearby is no candidate")
    check(100.0 in numbers_in("Huzhou Mirui was wholly owned by MiRXEA Pte. Ltd.") and 50.0 in numbers_in("held half of the shares"),
          "a holding stated in words (wholly owned, half) counts as its percentage")
    reads = [p for p in log if p.startswith("Read the value")]
    check(sum(1 for p in reads if "FIELD: payee.residence_cert" in p) == 2, "one passage is read twice by default (samples=2)")
    check(sum(1 for p in reads if "FIELD: flow.arms_length_value" in p) == 2 and all(p.count("\n- [") == 1 for p in reads if "FIELD: flow.arms_length_value" in p),
          "two passages are read once each, separately")
    check(all("MEANING:" in p and "Answer null unless" in p and "the quote must contain that number or date" in p for p in reads),
          "the read prompt carries the field's meaning and the guard")
    loc = [p for p in log if "For each field below" in p]
    check(len(loc) == 1 and loc[0].count("- payee.residence_cert (") == 2 and loc[0].index("DOCUMENTS") < loc[0].index("FIELDS (again)"),
          "the locate prompt lists the fields before and after the documents")
    f = ex.features["payee.residence_cert"]
    check(f["passages"] == 1 and f["reads"] == 2 and f["agree"] == 1.0 and "quote_len" in f and "figures_in_quote" in f and "score" in f,
          "per-field features for a calibrator: passages, reads, agreement, quote length, figures, retrieval score")
    one = extract(DOCS, ["flow.foreign_headline_rate"], make_responder([]), specs, samples=1, locate="llm")
    check(one.facts.get(("flow", "foreign_headline_rate")) == 25.0, "samples=1 takes the single reading")

    dead = extract(DOCS, ["payee.residence_cert"], lambda p: "no json here", specs, locate="llm")
    check(dead.missing == ["payee.residence_cert"] and any("not JSON" in n for n in dead.notes), "a locate reply that is not JSON: every field missing, noted, no exception")
    down = extract(DOCS, ["payee.residence_cert"], lambda p: (_ for _ in ()).throw(TimeoutError("down")), specs, locate="llm")
    check(down.missing == ["payee.residence_cert"] and any("TimeoutError" in n for n in down.notes), "a locate call that raises: every field missing, noted, no exception")

    # ---------------------------------------------------------------- locate by retrieval (BM25 here; the dense channel needs the cached model)
    idx = PassageIndex(DOCS, dense=False)
    hits = idx.search("residence certificate Hong Kong", k=2)
    check(hits and hits[0]["doc"] == "cor-2026" and all(DOCS[h["doc"]][h["start"]:h["end"]] == h["quote"] for h in hits) and hits[0]["channels"] == ["bm25"],
          "retrieval returns verbatim spans with offsets, ranked (top: %s)" % (hits[0]["doc"] if hits else None))
    log2 = []
    rx = extract(DOCS, ["flow.receipt_kind"], make_responder(log2), specs, locate="retrieval", dense=False)
    fr = rx.features["flow.receipt_kind"]
    check(rx.facts.get(("flow", "receipt_kind")) == "REMITTED" and fr["passages"] >= 1 and fr["reads"] >= 1 and not any("For each field" in p for p in log2),
          "with locate=retrieval the model only reads candidate passages (%d passages, %d reads)" % (fr["passages"], fr["reads"]))

    # ---------------------------------------------------------------- constraints, provenance, fill
    viol = dict(constraints(specs, {("flow", "foreign_headline_rate"): 130.0, ("flow", "payable_on"): date(1800, 1, 1), ("flow", "cost_basis"): -5.0}))
    check(viol.get("flow.foreign_headline_rate", "").startswith("percentage outside") and viol.get("flow.payable_on", "").startswith("date outside")
          and viol.get("flow.cost_basis", "").startswith("negative"), "denial constraints: percent in [0, 100], date in [1900, 2100], amount not negative")
    prov = provenance(ex, lambda k: "flows.up1.%s" % k[1] if k[0] == "flow" else "roles.%s.attrs.%s" % (k[0].upper(), k[1]))
    check(prov.get("roles.PAYEE.attrs.residence_cert") == {"kind": "disclosed", "source": "cor-2026", "quote": "is a resident of Hong Kong for the year 2026"},
          "provenance rows follow 案例采集.md §4.2 (disclosed, source, quote)")
    case = {"roles": {"ULT": {"loc": "HK", "attrs": {"residence_cert": False}}}, "flows": {"up1": {}}, "provenance": {}, "notes": []}
    filled = fill(case, {"facts": {"roles.ULT.attrs.residence_cert": True, "flows.up1.receipt_kind": "REMITTED", "flows.up1.foreign_headline_rate": 130.0},
                         "provenance": {"flows.up1.receipt_kind": prov["flows.up1.receipt_kind"]}, "model": "stub", "docs": ["accounts"],
                         "violations": [["flows.up1.foreign_headline_rate", "percentage outside [0, 100]: 130"]]})
    check(filled["roles"]["ULT"]["attrs"]["residence_cert"] is False and filled["flows"]["up1"] == {"receipt_kind": "REMITTED"}
          and case["flows"]["up1"] == {} and len(filled["notes"]) == 1,
          "fill() keeps stated values, skips a value a constraint refuses, adds the rest with a review note, never edits in place")

    # ---------------------------------------------------------------- extract_case: channels, derived inputs, registry
    case = Path(__file__).resolve().parents[1] / "cases" / "meridian.json"
    res = extract_case(case, {"d": "nothing here"}, lambda p: "{}", samples=1, locate="llm", registry_mode="off")
    asked = [k for k in res["missing"]]
    check(not res["facts"] and "fee:payee.ucmt_location" in res["untyped"] and not any(k.endswith("ucmt_location") for k in asked),
          "extract_case asks the model only for typed fields; untyped ones are listed for a person (%d untyped)" % len(res["untyped"]))
    check(all(specs[k.split(":", 1)[1]].channel in ASK_CHANNELS + ("",) for k in asked) and all(ch in ("B", "D") for _, ch, _ in res["external"])
          and all(k.split(".", 1)[1] in DERIVED or specs[k.split(":", 1)[1]].channel == "A" for k in res["derived_inputs"]),
          "channels: the model is asked E/C fields only (%d); B/D listed for a person (%d); derived ones listed as missing inputs (%d)" % (
              len(asked), len(res["external"]), len(res["derived_inputs"])))
    check(res["prompt_version"] and res["locate"] == "llm" and "temperature" in res and "features" in res, "the result records prompt version, locate mode, temperature and features")
    field = next(k for k in asked if specs[k.split(":", 1)[1]].kind == NUMBER)
    fid, key = field.split(":", 1)
    doc = {"d": "The %s was set at 1,000,000 under the agreement." % key.split(".", 1)[1].replace("_", " ")}

    def registry_model(prompt):
        if "For each field below" in prompt:
            return json.dumps({key: [{"doc": "d", "quote": doc["d"]}]})
        return json.dumps({"value": 1000000, "doc": "d", "quote": doc["d"]}) if "FIELD: %s" % key in prompt else json.dumps({"value": None})
    path = "flows.%s.%s" % (fid, key.split(".", 1)[1]) if key.startswith("flow.") else None
    res2 = extract_case(case, doc, registry_model, samples=1, only_flow=fid, locate="llm", registry={path: 900000} if path else None, registry_mode="off")
    check(path is not None and res2["facts"].get(path) == 1000000.0 and any(c["origin"] == "registry" for c in res2["conflicts"].get(path, []))
          and any(p == path and "registry" in why for p, why in res2["violations"]),
          "a registry value in hand that differs from the reading is a conflict and a violation (%s)" % path)
    out.write("%d checks, %d failures\n" % (len(results), results.count(False)))
    out.flush()
    return 1 if False in results else 0


if __name__ == "__main__":
    sys.exit(main())
