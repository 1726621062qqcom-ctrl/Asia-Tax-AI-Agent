"""Offline integrity and coverage checks for the country tax dictionary."""
import hashlib
import json
import re
from pathlib import Path
from urllib.parse import unquote

from .build import HERE, OFFICIAL, ROOT, collect, identifier_topics, outputs, scope_countries, treaty_pair


def digest(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    count = 0

    def check(ok, text):
        nonlocal count
        assert ok, text
        count += 1
        print("ok", text)

    snapshot = json.loads((HERE / "data" / "inventory.json").read_text(encoding="utf-8"))["as_of"]
    originals = [OFFICIAL / "official.sqlite", OFFICIAL / "manifest.csv", OFFICIAL / "params.csv"]
    before = {p: digest(p) for p in originals}
    bundle = collect(snapshot)
    generated = outputs(bundle)
    docs = {d["id"]: d for d in bundle["documents"]}
    params = {p["param_id"]: p for p in bundle["parameters"]}
    rules = {r["rule_id"]: r for r in bundle["rules"]}
    entries = {e["entry_id"]: e for e in bundle["entries"]}
    citations = {c["cite_id"]: c for c in bundle["citations"]}
    topics = {t["id"] for t in bundle["taxonomy"]["topics"]}
    statuses = bundle["taxonomy"]["status_dimensions"]
    check(len(entries) == len(bundle["taxonomy"]["jurisdictions"]) * len(topics), "every jurisdiction/topic pair has one dictionary entry, including coverage gaps")
    check(len({p["param_id"] for p in bundle["parameters"]}) == len(params), "parameter identifiers remain unique")
    check(all(set(d["topic_ids"]) <= topics for d in docs.values()), "document tags use the controlled taxonomy")
    check(all(set(p["topic_ids"]) <= topics and p["topic_ids"] for p in params.values()), "every parameter has a valid business classification")
    check(all(set(r["topic_ids"]) <= topics and r["topic_ids"] for r in rules.values()), "every compiled rule has a valid business classification")
    check(all(link["doc_id"] in docs and link["topic_id"] in topics for link in bundle["document_topics"]), "classification links never point to missing documents or topics")
    check(all(p["cite_id"] in citations for p in params.values()), "all parameter source references resolve")
    check(all(set(r["cite_ids"]) <= set(citations) and set(r["parameter_ids"]) <= set(params) for r in rules.values()), "all rule and parameter dependencies resolve")
    check(all(e[k] in allowed for e in entries.values() for k, allowed in statuses.items()), "all five coverage dimensions use explicit valid states")
    check(all(e["completeness_status"] != "complete" for e in entries.values()), "partial corpus coverage is never presented as globally complete")
    for jur in ("CN", "HK", "SG"):
        check(entries[jur + ":personal_income"]["model_status"] == "not_modelled", jur + " whole-statute content does not create personal-tax calculation coverage")
        for topic in ("inheritance_estate_gift", "exit_tax"):
            check(entries[jur + ":" + topic]["model_status"] == "not_modelled", jur + " " + topic + " remains separate from corporate disposal rules")
    check(entries["CN:cfc"]["model_status"] == "rules_available" and all(entries[j + ":cfc"]["model_status"] == "not_modelled" for j in ("HK", "SG")), "CFC coverage follows actual jurisdiction rules without false legal-absence findings")
    pairs = {p["pair_id"]: p for p in bundle["treaties"]}
    check(pairs["HK-SG"]["instrument_scope"] == "limited_shipping_air_transport", "limited airline/shipping material is not promoted to a comprehensive DTA")
    check(all(pairs[p]["instrument_scope"] == "comprehensive_income_arrangement_or_agreement" for p in ("CN-HK", "CN-SG")), "the two indexed comprehensive income instruments retain their distinct scope")
    check(treaty_pair("sg.iras.dta-list.data") is None and treaty_pair("sg.iras.dta-hk") == "HK-SG", "a directory of partners is not counted as archived full treaties")
    check(all(set(p["document_ids"]) <= set(docs) and set(p["parameter_ids"]) <= set(params) for p in pairs.values()), "treaty registry references resolve")
    check(all(p["quote_verified"] == bool(p["quote"].strip()) for p in params.values()), "a missing quote is not labelled verbatim verified")
    check(not params["hk-sg.no_comprehensive_dta"]["quote_verified"], "the existing unsupported negative treaty parameter is exposed as a review item")
    check(all(r["source_status"] == "no_direct_clause_link" for r in rules.values() if not r["cite_ids"]), "rules without direct citations are reported without inventing sources")
    check(any(r["grade"] == "B_PRACTICE" and r["practice_evidence"] for r in rules.values()), "administrative-practice evidence remains separate from statutory grade A")
    check(any(r["judgement_keys"] for r in rules.values()), "discretion-dependent rules retain their unresolved judgement keys")
    check("exit_tax" not in identifier_topics("cn.reorg.special") and "capital_gains" in identifier_topics("cn.gain.base"), "reorganisation and disposal identifiers never imply exit/migration tax")
    check("restructuring_distributions" in identifier_topics("hk.fsie.intragroup_relief"), "intragroup relief is discoverable under reorganisation as well as its tax family")
    check(all(entries[j + ":restructuring_distributions"]["model_status"] == "rules_available" for j in ("CN", "HK", "SG")), "specific reorganisation rules are discoverable across all three jurisdictions")
    check(scope_countries("pair(CN,SG)") == ["CN", "SG"] and scope_countries("INTL") == [], "bilateral and international source scope are not conflated")
    check(all(p["effective_from"] or p["date_status"] != "within_recorded_interval" for p in params.values()), "missing start dates are visible rather than silently deemed current")
    check(all(d["legal_completeness"] == "not_assessed" for d in docs.values()), "download or classification status is not a legal completeness certification")
    check(any(d["original_fragment"] for d in docs.values()) and len({d["work_id"] for d in docs.values()}) < len(docs), "document versions and download fragments are not counted as independent laws")
    check(docs["sg.ita1947.full"]["source_subject_status"] == "mixed_scope_statute", "company catalogue focus is separate from a statute's mixed subject scope")
    check(all((HERE / name).exists() and (HERE / name).read_text(encoding="utf-8") == text for name, text in generated.items()), "all generated documents and data match a deterministic fresh build")
    for relative, text in generated.items():
        if relative.endswith(".md"):
            for target in re.findall(r"\]\(([^)]+)\)", text):
                if not target.startswith(("http://", "https://", "#")):
                    assert ((HERE / relative).parent / unquote(target.split("#", 1)[0])).resolve().exists(), (relative, target)
    check(True, "generated local source and navigation links resolve")
    check(before == {p: digest(p) for p in originals}, "catalogue generation does not modify the official database, manifest or parameters")
    print("%s dictionary checks passed" % count)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
