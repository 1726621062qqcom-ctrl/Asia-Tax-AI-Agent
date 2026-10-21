"""Build a business catalogue from existing official sources; no fetch or source rewrite.

    python -m tax_dictionary.build --as-of 2026-10-16
    python -m tax_dictionary.build --as-of 2026-10-16 --check
"""
import argparse
import csv
import hashlib
import io
import json
import re
import sqlite3
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HERE = Path(__file__).resolve().parent
OFFICIAL = ROOT / "official"
JURS = {"CN", "HK", "SG"}

# Explicit identifier vocabulary: classification is reproducible, not an LLM judgement.
FAMILIES = {
    "div": ["withholding"], "int": ["withholding"], "interest": ["withholding"], "roy": ["withholding", "intellectual_property"],
    "wht": ["withholding"], "royalty": ["withholding", "intellectual_property"],
    "eit": ["corporate_income"], "corp": ["corporate_income"], "profits": ["corporate_income"],
    "resident": ["corporate_income"], "domestic": ["corporate_income"], "deduct": ["corporate_income"],
    "goods": ["corporate_income"], "service": ["corporate_income", "withholding"], "charge": ["corporate_income"],
    "source": ["residence_pe"], "nocharge": ["corporate_income"], "foreign_income": ["foreign_income_credit"],
    "gain": ["capital_gains"], "onshore": ["capital_gains"], "onshore_gain": ["capital_gains"],
    "s10l": ["capital_gains", "foreign_income_credit"], "s13w": ["capital_gains"], "indirect": ["capital_gains", "anti_avoidance_substance"],
    "ftc": ["foreign_income_credit"], "fsie": ["foreign_income_credit", "anti_avoidance_substance"], "dtr": ["foreign_income_credit", "administration"],
    "branch": ["foreign_income_credit", "residence_pe"], "cfc": ["cfc"],
    "bo": ["anti_avoidance_substance", "treaties"], "gaar": ["anti_avoidance_substance"], "ppt": ["anti_avoidance_substance", "treaties"],
    "tp": ["transfer_pricing"], "thincap": ["transfer_pricing"],
    "reorg": ["restructuring_distributions"], "reinvest": ["restructuring_distributions"], "capitalisation": ["restructuring_distributions"],
    "liquidation": ["restructuring_distributions"], "capital_reduction": ["restructuring_distributions"],
    "ip": ["intellectual_property"], "tech": ["intellectual_property"],
    "residence": ["residence_pe"], "pe": ["residence_pe", "treaties"],
    "vat": ["vat_gst"], "gst": ["vat_gst"], "stamp": ["stamp_duty"],
    "property": ["property_taxes"], "property_tax": ["property_taxes"], "rent": ["property_taxes"], "lat": ["property_taxes"], "deed": ["property_taxes"],
    "surcharge": ["surcharges"], "ucmt": ["surcharges"], "local_edu": ["surcharges"],
    "customs": ["customs"], "tariff": ["customs"], "p2": ["pillar_two"],
    "loss": ["loss_relief"], "group_relief": ["loss_relief"],
    "treaty": ["treaties", "administration"], "mli": ["treaties", "anti_avoidance_substance"],
    "refund": ["administration"], "map": ["administration", "treaties"], "time": ["administration"],
    "objection": ["administration"], "appeal": ["administration"], "review": ["administration"],
    "cor": ["administration", "residence_pe"], "tca": ["administration"], "holiday": ["administration"]
}
TITLE_TAGS = {
    "treaties": [r"double tax", r"taxation agreement", r"\bdtas?\b", "双重征税", "税收协定", "税收安排", "协定股息", "airline and shipping income agreement", r"\bmli\b"],
    "corporate_income": ["corporate income", "profits tax", "income tax act", "inland revenue ordinance", "企业所得税", "利得税"],
    "personal_income": ["personal income tax", "salaries tax", "个人所得税", "薪俸税"],
    "inheritance_estate_gift": ["estate duty", "inheritance tax", "gift tax", "遗产税", "继承税", "赠与税"],
    "exit_tax": [r"\bexit tax\b", "migration tax", "迁出税", "移居税"],
    "cfc": ["controlled foreign compan", "受控外国企业"],
    "withholding": ["withholding", "non-resident", "非居民", "源泉扣缴", "预提税"],
    "foreign_income_credit": ["foreign tax credit", "foreign-sourced income", "foreign income", "taxation relief", "境外所得", "税收抵免"],
    "capital_gains": ["disposal", "capital gain", "sale of foreign assets", "股权转让", "间接转让"],
    "restructuring_distributions": ["reorganis", "reorganiz", "liquidation", "重组", "清算", "减资", "分配利润", "统借统还"],
    "residence_pe": ["residence", "residency", "resident status", "permanent establishment", "locality of profits", "居民身份", "常设机构", "实际管理机构", "居民企业认定"],
    "transfer_pricing": ["transfer pricing", "关联", "特别纳税调整", "独立交易", "同期资料", "预约定价"],
    "anti_avoidance_substance": ["anti-abuse", "anti-avoidance", "beneficial owner", "substance", "反避税", "受益所有人", "实质重于形式"],
    "intellectual_property": ["royalt", "intellectual property", "software payment", "特许权", "技术转让", "知识产权"],
    "vat_gst": ["value added", "value-added", "goods and services tax", r"\bgst\b", "增值税"],
    "stamp_duty": ["stamp dut", "印花税"],
    "property_taxes": ["property tax", "property owners", "land appreciation", "房产税", "契税", "土地增值税", "产权", "property rates"],
    "surcharges": ["维护建设税", "教育附加", "教育费附加"],
    "customs": ["customs", "tariff", "关税"],
    "pillar_two": ["minimum tax", "minimum top-up", "globe", "pillar two", "最低补足税", "最低税", "支柱二"],
    "loss_relief": ["loss relief", "group relief", "亏损"],
    "administration": ["filing", "refund", "objection", "appeal", "mutual agreement", "public holiday", "holidays act", "form", "税收征管", "征收管理", "申报", "退税", "复议", "相互协商", "汇率", "节假日", "失效废止"],
    "corporate_law": ["companies act", "companies registry", "re-domiciliation", "transfer of registration", "interpretation act", "公司法", "迁册"]
}


def rows(path):
    with Path(path).open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def norm(text):
    return re.sub(r"\s+", "", text or "")


def scope_countries(scope):
    return sorted(set(re.findall(r"(?<![A-Z])(CN|HK|SG)(?![A-Z])", scope or "")))


def identifier_topics(identifier):
    parts = identifier.split(".")
    if parts[0] == "p2":
        return {"pillar_two"}
    topics = set(FAMILIES.get(parts[1].split("@")[0], [])) if len(parts) > 1 else set()
    if parts[0] in {"cn-hk", "cn-sg", "hk-sg"}:
        topics.add("treaties")
    if any(text in identifier for text in (".intragroup", ".stamp.associated", ".stamp.clawback", ".stamp.restructuring")):
        topics.add("restructuring_distributions")
    if ".nocharge.outbound" in identifier or ".nocharge.dividend" in identifier:
        topics.add("withholding")
    return topics


def rule_country(rule):
    taxing = rule.scope.taxing
    if taxing in JURS:
        return taxing
    prefix = rule.id.split(".")[0].upper()
    return prefix if prefix in JURS else None


def treaty_pair(doc_id):
    if "cn-hk" in doc_id:
        return "CN-HK"
    if "cn-sg" in doc_id:
        return "CN-SG"
    if "hk-sg" in doc_id or doc_id == "sg.iras.dta-hk":
        return "HK-SG"
    return None


def collect(as_of):
    from tax_graph.engine import RULES
    from tax_graph.rules.model import Discretion, leaves
    date.fromisoformat(as_of)
    taxonomy, profiles = load_json(HERE / "taxonomy.json"), load_json(HERE / "profiles.json")["profiles"]
    topics = {t["id"]: t for t in taxonomy["topics"]}
    with sqlite3.connect((OFFICIAL / "official.sqlite").as_uri() + "?mode=ro", uri=True) as con:
        con.row_factory = sqlite3.Row
        docs = {r["id"]: dict(r) for r in con.execute("SELECT * FROM doc ORDER BY id")}
        clauses = {r["cite_id"]: dict(r) for r in con.execute("SELECT * FROM clause ORDER BY cite_id")}
        params = {r["param_id"]: dict(r) for r in con.execute("SELECT * FROM param ORDER BY param_id")}
        expressions = {r["expr_id"]: dict(r) for r in con.execute("SELECT * FROM expression")}
        times = {r["cite_id"]: dict(r) for r in con.execute("SELECT * FROM clause_time")}
        work_count = con.execute("SELECT COUNT(*) FROM work").fetchone()[0]
    manifest = {r["id"]: r for r in rows(OFFICIAL / "manifest.csv")}
    assert set(manifest) == set(docs), "Source database and manifest IDs differ; rebuild the official corpus first"
    csv_params = {r["param_id"]: r for r in rows(OFFICIAL / "params.csv")}
    assert csv_params == params, "Source database and parameter CSV differ; rebuild the official corpus first"
    for did, doc in docs.items():
        assert doc == manifest[did], "Source database and manifest metadata differ: " + did
        raw = (OFFICIAL / doc["file"]).resolve()
        assert OFFICIAL.resolve() in raw.parents and raw.is_file(), "Invalid or missing original: " + did
        doc.update(source_jurisdiction=doc["jur"].upper(), country_ids=scope_countries(doc["jur"].upper()), topic_ids=[],
                   work_id=expressions.get(did, {}).get("work_id"), original_fragment=bool(re.search(r"\.frag\d+", did)),
                   expression_status=expressions.get(did, {}).get("status", "not_recorded"),
                   classification_status="needs_review")
        subjects = []
        for subject, pattern in (("COMPANY", r"compan(?:y|ies)|corporat|enterprise|企业|公司"),
                                 ("INDIVIDUAL", r"individual|personal income|salaries tax|个人|薪俸"),
                                 ("PARTNERSHIP", r"partnership|合伙"), ("TRUST", r"\btrust\b|信托")):
            if re.search(pattern, doc["title"], re.IGNORECASE):
                subjects.append(subject)
        mixed = did in {"hk.cap112.en", "hk.cap112.zh", "sg.ita1947", "sg.ita1947.pdf", "sg.ita1947.full"}
        doc.update(subject_focus="COMPANY", source_subject_ids=sorted(set(subjects) | ({"COMPANY", "INDIVIDUAL"} if mixed else set())),
                   source_subject_status="mixed_scope_statute" if mixed else "explicit_title_only" if subjects else "not_reviewed")
        if treaty_pair(did):
            doc["country_ids"] = treaty_pair(did).split("-")
        elif did.startswith("intl.oecd."):
            doc["country_ids"] = sorted({p.upper() for p in did.split(".") if p.upper() in JURS})
        if did in ("cn.guide.hk", "cn.guide.sg"):
            doc["country_ids"] = ["CN", did.rsplit(".", 1)[1].upper()]

    links = set()
    p_usage = defaultdict(set)
    p_rules = defaultdict(set)
    rule_records = []
    observed = {r["rule_id"]: r for r in rows(OFFICIAL / "labels" / "observed_rules.csv")}
    for rule in sorted(RULES, key=lambda r: r.id):
        jur = rule_country(rule)
        assert jur, "Unresolved taxing jurisdiction: " + rule.id
        tags = identifier_topics(rule.id)
        if rule.effect.value in {"DEADLINE", "PENALTY"}:
            tags.add("administration")
        cites, pids, observations = set(), set(), []
        for source in rule.sources:
            if source in params:
                pids.add(source)
                cites.add(params[source]["cite_id"])
                p_usage[source].add(jur)
                p_rules[source].add(rule.id)
            elif source in clauses:
                cites.add(source)
            elif source.startswith("observed:"):
                oid = source.split(":", 1)[1]
                assert oid in observed
                observations.append(observed[oid])
                if observed[oid].get("contrast_cite"):
                    cites.add(observed[oid]["contrast_cite"])
            else:
                raise AssertionError("Unresolved rule source: %s / %s" % (rule.id, source))
        assert tags and tags <= set(topics), "Unclassified rule: " + rule.id
        for cite in cites:
            assert cite in clauses, "Missing rule clause: " + cite
            for tag in tags:
                links.add((clauses[cite]["doc_id"], tag, "compiled_rule", rule.id))
        judgement = [n.key for n in leaves(rule.cond) if isinstance(n, Discretion)]
        if any("restructuring_distributions" in identifier_topics(pid) for pid in pids):
            tags.add("restructuring_distributions")
            for cite in cites:
                links.add((clauses[cite]["doc_id"], "restructuring_distributions", "compiled_rule", rule.id))
        rule_records.append({"rule_id": rule.id, "country_ids": [jur], "topic_ids": sorted(tags),
                             "scope": {"source": rule.scope.source, "residence": rule.scope.residence, "income": rule.scope.income,
                                       "side": rule.scope.side, "mount": rule.scope.mount.value},
                             "effect": rule.effect.value, "grade": rule.grade.name, "parameter_ids": sorted(pids),
                             "source_status": "source_linked" if cites else "no_direct_clause_link",
                             "cite_ids": sorted(cites), "reads": sorted(rule.reads), "judgement_keys": sorted(set(judgement)),
                             "valid_from": rule.valid[0].isoformat() if rule.valid[0] else "",
                             "valid_to": rule.valid[1].isoformat() if rule.valid[1] else "", "practice_evidence": observations,
                             "model_status": "rules_available", "completeness_status": "partial"})

    for pid, p in params.items():
        assert p["cite_id"] in clauses
        if norm(p["quote"]):
            assert norm(p["quote"]) in norm(clauses[p["cite_id"]]["text"]), "Unmatched parameter quote: " + pid
        tags = identifier_topics(pid)
        assert tags and tags <= set(topics), "Unclassified parameter: " + pid
        p.update(topic_ids=sorted(tags), country_ids=scope_countries(p["scope"]),
                 used_by_country_ids=sorted(p_usage[pid]), rule_ids=sorted(p_rules[pid]), quote_verified=bool(norm(p["quote"])),
                 quote_status="verified_verbatim" if norm(p["quote"]) else "no_quote_recorded",
                 date_status=("outside_recorded_interval" if p["effective_from"] and p["effective_from"] > as_of or p["effective_to"] and p["effective_to"] <= as_of
                              else "within_recorded_interval" if p["effective_from"] else "start_date_not_recorded"))
        for tag in tags:
            links.add((clauses[p["cite_id"]]["doc_id"], tag, "parameter", pid))

    # Titles and parent links are catalogue hints only, never proof of tax treatment.
    for did, doc in docs.items():
        title = doc["title"].lower()
        for tag in identifier_topics(did):
            links.add((did, tag, "document_identifier", did))
        for tag, patterns in TITLE_TAGS.items():
            if any(re.search(pattern, title) for pattern in patterns):
                links.add((did, tag, "title_keyword", doc["title"]))
        if doc["type"] == "treaty":
            links.add((did, "treaties", "document_type", "treaty"))
        if did in {"hk.cap112.en", "hk.cap112.zh", "sg.ita1947", "sg.ita1947.pdf", "sg.ita1947.full"}:
            links.add((did, "personal_income", "mixed_scope_statute", "Incidental whole-statute content; individual calculations not implemented"))
        if did.startswith("intl.oecd.globe") or did.startswith("sg.memta2024") or did.startswith("hk.ord.2025-21"):
            links.add((did, "pillar_two", "document_identifier", "minimum_tax_legislation"))
        if did.startswith("sg.sda1929"):
            links.add((did, "stamp_duty", "document_identifier", "stamp_duties_act"))
        if did.startswith("sg.gsta1993"):
            links.add((did, "vat_gst", "document_identifier", "gst_act"))
        if did.startswith("sg.ca1967") or did.startswith("hk.cr.redomiciliation"):
            links.add((did, "corporate_law", "document_identifier", "registration_or_corporate_procedure"))
    for row in rows(OFFICIAL / "labels" / "precedents.csv"):
        issue = row["issue_key"].lower()
        tags = set()
        if "sourced" in issue or "source" in issue or "profits_arise" in issue:
            tags.add("residence_pe")
        if "capital" in issue:
            tags.add("capital_gains")
        if any(t in issue for t in ("ppt", "beneficial", "substance", "purpose", "avoid")):
            tags.add("anti_avoidance_substance")
        if "service_fee" in issue:
            tags.add("corporate_income")
        if "incurred_in_production" in issue:
            tags.add("corporate_income")
        if "royalty" in issue:
            tags.update({"intellectual_property", "transfer_pricing"})
        if "arms_length" in issue:
            tags.add("transfer_pricing")
        for cite in row["cites"].split(";"):
            if cite.strip() in clauses:
                for tag in tags:
                    links.add((clauses[cite.strip()]["doc_id"], tag, "precedent_issue", row["issue_key"]))
    direct = defaultdict(set)
    for did, tag, basis, ref in links:
        assert did in docs
        direct[did].add(tag)
    for _ in range(5):
        changes = 0
        for did, doc in docs.items():
            parent = doc.get("parent") or doc.get("alias_of")
            if not parent and re.search(r"\.frag\d+$", did):
                parent = re.sub(r"\.frag\d+$", "", did)
            for tag in direct.get(parent, set()) - direct[did]:
                links.add((did, tag, "parent_context", parent))
                direct[did].add(tag)
                changes += 1
        if not changes:
            break
    verifications = {r["id"]: r for r in rows(OFFICIAL / "verify.csv")}
    for did, doc in docs.items():
        doc["topic_ids"] = sorted(direct[did])
        bases = {x[2] for x in links if x[0] == did}
        doc["classification_status"] = "reference_linked" if bases & {"parameter", "compiled_rule", "precedent_issue"} else "metadata_inferred" if bases else "needs_review"
        doc["download_verification"] = verifications.get(did, {})
        doc["legal_completeness"] = "not_assessed"

    country_records, coverage = [], []
    for country in taxonomy["jurisdictions"]:
        jur = country["id"]
        for topic in taxonomy["topics"]:
            tid = topic["id"]
            ds = [d for d in docs.values() if jur in d["country_ids"] and tid in d["topic_ids"]]
            ps = [p for p in params.values() if tid in p["topic_ids"] and jur in set(p["country_ids"] + p["used_by_country_ids"])]
            rs = [r for r in rule_records if jur in r["country_ids"] and tid in r["topic_ids"]]
            profile = profiles.get(jur, {}).get(tid, {})
            for pid in profile.get("parameters", []):
                assert pid in params, "Unknown profile parameter: " + pid
            for rid in profile.get("rules", []):
                assert rid in {r["rule_id"] for r in rule_records}, "Unknown profile rule: " + rid
            is_personal = tid == "personal_income"
            state = {"source_status": "incidental_sources_only" if ds and is_personal else "sources_indexed" if ds else "not_indexed",
                     "structure_status": "parameters_linked" if ps else "source_metadata_only" if ds else "not_structured",
                     "model_status": "rules_available" if rs else "not_modelled",
                     "judgement_status": "authority_or_facts_judgement_present" if any(r["judgement_keys"] for r in rs) else "no_discretion_flag_in_linked_rules" if rs else "not_assessed",
                     "completeness_status": "partial" if ds or ps or rs else "not_assessed"}
            sample = []
            for pid in profile.get("parameters", []):
                p = params[pid]
                sample.append({k: p[k] for k in ("param_id", "name", "scope", "value", "unit", "cite_id", "effective_from", "effective_to", "quote", "date_status")})
            cite_ids = sorted({p["cite_id"] for p in ps} | {cite for r in rs for cite in r["cite_ids"]})
            record = {"entry_id": jur + ":" + tid, "country_id": jur, "topic_id": tid, "topic_name": topic["name"],
                      "subject_ids": ["INDIVIDUAL"] if tid in {"personal_income", "inheritance_estate_gift"} else ["COMPANY"], **state,
                      "summary": profile.get("summary") or ("The corpus has indexed material in this topic; use the linked parameters and rules for the precise scope." if ds or ps or rs else "No dedicated coverage has been established for this topic."),
                      "caveat": profile.get("caveat") or "Catalogue tags and rule availability do not establish exhaustive legal coverage or a case-specific tax result.",
                      "document_ids": [d["id"] for d in ds], "parameter_ids": [p["param_id"] for p in ps],
                      "rule_ids": [r["rule_id"] for r in rs], "cite_ids": cite_ids, "sample_parameters": sample,
                      "editorial_status": "source_linked_summary_not_official_text"}
            country_records.append(record)
            coverage.append({"country_id": jur, "topic_id": tid, **state, "document_count": len(ds), "parameter_count": len(ps),
                             "rule_count": len(rs), "judgement_rule_count": sum(bool(r["judgement_keys"]) for r in rs)})

    treaties = []
    for pair in ("CN-HK", "CN-SG", "HK-SG"):
        items = [d for d in docs.values() if treaty_pair(d["id"]) == pair and d["type"] == "treaty"]
        pids = [p["param_id"] for p in params.values() if p["scope"] == "pair(%s,%s)" % tuple(pair.split("-"))]
        treaties.append({"pair_id": pair, "country_ids": pair.split("-"),
                        "instrument_scope": "limited_shipping_air_transport" if pair == "HK-SG" else "comprehensive_income_arrangement_or_agreement",
                        "document_ids": [d["id"] for d in items], "work_ids": sorted({d["work_id"] for d in items if d["work_id"]}),
                        "parameter_ids": pids,
                        "caveat": "Only the limited transport agreement is indexed for this pair; it must not be used as a general dividend, interest or royalty DTA." if pair == "HK-SG" else "Apply the original, protocols, retained provisions and MLI material together; signing, entry into force and tax effectiveness are distinct dates.",
                        "coverage_status": "partial", "historical_completeness": "not_established"})

    inventory = {"as_of": as_of, "source_database": "official/official.sqlite", "documents": len(docs), "works": work_count,
                 "original_fragments": sum(d["original_fragment"] for d in docs.values()), "clauses": len(clauses), "parameters": len(params),
                 "compiled_rules": len(rule_records), "rule_grades": dict(sorted(Counter(r["grade"] for r in rule_records).items())),
                 "classification_status": dict(sorted(Counter(d["classification_status"] for d in docs.values()).items())),
                 "countries": len(taxonomy["jurisdictions"]), "topics": len(topics), "entries": len(country_records),
                 "quote_checks_passed": sum(p["quote_verified"] for p in params.values()),
                 "parameters_without_quote": [p["param_id"] for p in params.values() if not p["quote_verified"]],
                 "download_rechecks_recorded": len(verifications),
                 "document_counts_overlap_across_topics": True, "classification_is_not_legal_verification": True,
                 "source_latest_retrieval": max(d["retrieved_at"] for d in docs.values()),
                 "removed_document_metadata": len(rows(OFFICIAL / "removed.csv")),
                 "supersession_records": len(rows(OFFICIAL / "superseded.csv")),
                 "build_inputs": {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in
                                  ("official/manifest.csv", "official/params.csv", "tax_dictionary/taxonomy.json", "tax_dictionary/profiles.json")}}
    citations = []
    for cid in sorted({p["cite_id"] for p in params.values()} | {cid for r in rule_records for cid in r["cite_ids"]}):
        clause = clauses[cid]
        doc = docs[clause["doc_id"]]
        citations.append({"cite_id": cid, "doc_id": doc["id"], "label": clause["label"], "url": doc["url"],
                          "local_original": "official/" + doc["file"], "time": times.get(cid, {})})
    return {"inventory": inventory, "taxonomy": taxonomy, "documents": list(docs.values()), "parameters": list(params.values()),
            "rules": rule_records, "document_topics": [{"doc_id": a, "topic_id": b, "basis": c, "reference": d} for a, b, c, d in sorted(links)],
            "entries": country_records, "coverage": coverage, "treaties": treaties, "citations": citations}


def json_text(obj):
    return json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def csv_text(items, fields):
    out = io.StringIO(newline="")
    writer = csv.DictWriter(out, fields, lineterminator="\n", extrasaction="ignore")
    writer.writeheader()
    for row in items:
        writer.writerow({k: ";".join(map(str, v)) if isinstance(v, list) else json.dumps(v, ensure_ascii=False, sort_keys=True) if isinstance(v, dict) else v for k, v in row.items() if k in fields})
    return out.getvalue()


def md(value):
    return str(value or "").replace("|", "\\|").replace("\n", " ").replace("\r", " ")


def outputs(bundle):
    b = bundle
    inv = b["inventory"]
    docs = {d["id"]: d for d in b["documents"]}
    citations = {c["cite_id"]: c for c in b["citations"]}
    countries = b["taxonomy"]["jurisdictions"]
    topics = b["taxonomy"]["topics"]
    entries = {(e["country_id"], e["topic_id"]): e for e in b["entries"]}
    result = {}
    for name in ("inventory", "rules", "entries", "treaties", "citations"):
        result["data/" + ("dictionary" if name == "entries" else name) + ".json"] = json_text(b[name])
    result["data/documents.csv"] = csv_text(b["documents"], ["id", "source_jurisdiction", "country_ids", "topic_ids", "subject_focus", "source_subject_ids", "source_subject_status", "type", "title", "work_id", "lang", "original_fragment", "alias_of", "parent", "file", "url", "sha256", "retrieved_at", "effective_from", "effective_to", "currency", "currency_note", "text_status", "clauses", "classification_status", "expression_status", "legal_completeness", "download_verification"])
    result["data/parameters.csv"] = csv_text(b["parameters"], ["param_id", "scope", "country_ids", "used_by_country_ids", "topic_ids", "income", "topic", "name", "value", "unit", "cite_id", "effective_from", "effective_to", "date_status", "quote", "quote_verified", "quote_status", "rule_ids", "status", "note"])
    result["data/document_topics.csv"] = csv_text(b["document_topics"], ["doc_id", "topic_id", "basis", "reference"])
    result["data/coverage.csv"] = csv_text(b["coverage"], ["country_id", "topic_id", "source_status", "structure_status", "model_status", "judgement_status", "completeness_status", "document_count", "parameter_count", "rule_count", "judgement_rule_count"])
    stamp = "Catalogue snapshot: **%s**. This is an index of the retained local corpus, not a fresh verification that every rule is current on this date." % inv["as_of"]
    lines = ["# Country Tax Dictionary — cross-country comparison", "", stamp, "",
             "[Mainland China](countries/CN.md) · [Hong Kong](countries/HK.md) · [Singapore](countries/SG.md) · [Coverage gaps](GAPS.md) · [Source catalogue](SOURCES.md)", "",
             "Values below are source parameters, not unconditional effective tax rates. Read the conditions, original clause and date fields on each country card.", "",
             "| Topic | Mainland China | Hong Kong | Singapore |", "|---|---|---|---|"]
    for topic in topics:
        cells = []
        for country in countries:
            e = entries[country["id"], topic["id"]]
            examples = "; ".join("%s: %s %s" % (p["name"].replace("_", " "), p["value"], p["unit"]) for p in e["sample_parameters"])
            cells.append(md(e["summary"]) + (" **Indexed examples: %s.**" % md(examples) if examples else "") + "<br>" + e["model_status"] + "; " + e["source_status"])
        lines.append("| %s | %s |" % (topic["name"], " | ".join(cells)))
    lines += ["", "## Treaty scope is a separate comparison", "", "| Pair | Indexed scope | Important boundary |", "|---|---|---|"]
    for t in b["treaties"]:
        lines.append("| %s | %s | %s |" % (t["pair_id"], t["instrument_scope"], t["caveat"]))
    lines += ["", "## Reading coverage", "", "`rules_available` means compiled rules exist for specific company scenarios; it does not mean the entire topic is implemented. `not_modelled` is never a zero tax rate.", "",
              "Every jurisdiction/topic entry has independent source, structure, model, judgement and completeness statuses in [coverage.csv](data/coverage.csv). Cross-topic document counts overlap.", ""]
    result["COMPARISON.md"] = "\n".join(lines)

    for country in countries:
        jur = country["id"]
        lines = ["# %s — country tax dictionary" % country["name"], "", stamp, "", "[Comparison](../COMPARISON.md) · [Source catalogue](../SOURCES.md) · [Coverage gaps](../GAPS.md)", "",
                 "Jurisdiction code: **%s**. Local currency: **%s**. Calculation subject: **companies within modelled scenarios**." % (jur, country["currency"]), "",
                 "A parameter's source scope can be a treaty pair or another jurisdiction where the engine shares an input. The original scope is shown; shared use does not make a foreign statute domestic law.", ""]
        for topic in topics:
            e = entries[jur, topic["id"]]
            lines += ["## " + topic["name"], "", e["summary"], "", "**Boundary:** " + e["caveat"], "",
                      "Sources: `%s`; structured: `%s`; model: `%s`; judgement: `%s`; completeness: `%s`." % tuple(e[k] for k in ("source_status", "structure_status", "model_status", "judgement_status", "completeness_status")), "",
                      "Indexed links: %d documents / %d parameters / %d compiled rules. Counts overlap across topics." % (len(e["document_ids"]), len(e["parameter_ids"]), len(e["rule_ids"])), ""]
            if e["sample_parameters"]:
                lines += ["| Rate / condition and source parameter | Value | Source scope | Effective from | Effective to | Clause |", "|---|---|---|---|---|---|"]
                for p in e["sample_parameters"]:
                    citation = citations[p["cite_id"]]
                    lines.append("| %s<br>`%s` | %s %s | %s | %s | %s | [%s](%s) |" % (md(p["name"].replace("_", " ")), p["param_id"], md(p["value"]), md(p["unit"]), p["scope"], p["effective_from"] or "Not recorded", p["effective_to"] or "Open / not recorded", md(p["cite_id"]), citation["url"]))
                lines += [""]
                for p in e["sample_parameters"]:
                    lines += ["Source excerpt for `%s`:" % p["param_id"], "", "> " + p["quote"].strip().replace("\n", "\n> "), ""]
            selected_docs = sorted(e["document_ids"], key=lambda did: (docs[did]["original_fragment"], bool(docs[did]["alias_of"]), docs[did]["type"] not in ("law", "regulation", "treaty"), did))[:5]
            if selected_docs:
                lines += ["Representative archived documents (not an exhaustive reading list):", ""]
                for did in selected_docs:
                    d = docs[did]
                    lines.append("- [%s](%s) · `%s` · [local original](../../official/%s)" % (md(d["title"]), d["url"], did, d["file"]))
                lines += [""]
        result["countries/" + jur + ".md"] = "\n".join(lines)

    lines = ["# Coverage gaps and classification review", "", stamp, "",
             "## Requirement-level gaps", "",
             "- **All tax treaties:** not established. Three bilateral pairs and selected MLI / protocol materials are indexed; treaty listing pages do not equal archived full treaties for every listed country.",
             "- **All income / corporate regulations:** partial company-focused coverage. Whole-statute collection is not a statement that every provision has structured data or executable rules.",
             "- **Inheritance / estate / gift tax:** no dedicated inventory or calculation coverage has been established. This includes the evidence needed to state that a regime was abolished or is not imposed.",
             "- **Exit tax:** a separate inventory is still required. Disposal taxes, reorganisation rules and registration / re-domiciliation procedure material remain separate categories.",
             "- **CFC:** Mainland company CFC rules are linked. No dedicated HK / SG CFC rule is indexed; no legal-absence conclusion is inferred.",
             "- **History and legal currency:** the original library prunes superseded material and has incomplete date fields. It is not a complete historical law archive, and this build performs no new web currency verification.", "",
             "## Work queue", "", "| Priority | Work | Completion evidence |", "|---|---|---|",
             "| P1 | Inheritance / estate / gift tax inventories for each jurisdiction | Primary sources establishing existence, scope, repeal / abolition and relevant dates |",
             "| P1 | Exit / migration taxation separately from disposals | Subject, departure trigger, deemed disposal, asset base, deferral and date sources |",
             "| P1 | Personal income taxonomy and source selection | Tax bands, residence, reliefs, subject boundaries and source dates |",
             "| P1 | Treaty completeness checklist | Per-pair original, protocols, entry-into-force and tax-effective dates; limited / comprehensive / EOI scope |",
             "| P2 | Review inferred document tags | Checked taxonomy links with a reviewer and rationale; no whole-document scope inflation |",
             "| P2 | Legal currency and missing effective dates | Dated official-source review, with repeal / amendment links |", "",
             "## Classification queue", "", "Classification is a catalogue operation. A reference-linked document is not a human-approved legal summary.", "",
             "| State | Documents |", "|---|---|"]
    for state, n in inv["classification_status"].items():
        lines.append("| %s | %s |" % (state, n))
    pending = [d for d in b["documents"] if d["classification_status"] == "needs_review"]
    lines += ["", "### Documents without a topic assignment", ""]
    lines += ["- `%s` — %s" % (d["id"], d["title"]) for d in pending] or ["None. Metadata-inferred assignments still require business review."]
    lines += [""]
    lines += ["### Parameters without a recorded quotation", "",
              "A clause reference without a verbatim supporting quote is not counted as quote-verified. In particular, the scope of a limited treaty alone does not prove that no other comprehensive treaty exists.", ""]
    lines += ["- `%s`" % pid for pid in inv["parameters_without_quote"]] or ["None."]
    lines += [""]
    lines += ["### Compiled rules without a direct clause link", "",
              "These remain visible as model rules; no direct primary-source anchor is invented for them. Review their calculation context and add an explicit source if appropriate.", ""]
    lines += ["- `%s` (%s; %s)" % (r["rule_id"], ", ".join(r["country_ids"]), r["effect"]) for r in b["rules"] if r["source_status"] == "no_direct_clause_link"] or ["None."]
    lines += [""]
    result["GAPS.md"] = "\n".join(lines)
    lines = ["# Classified source catalogue", "", stamp, "",
             "%s archived document records / %s works / %s original fragments. Records include language versions, protocols, aliases and assembled texts; these are not counts of independent tax laws." % (inv["documents"], inv["works"], inv["original_fragments"]), "",
             "Topic tags describe discoverability. For precise evidence use the parameter quote and clause reference; tags are not inherited as legal conclusions for every clause in a large statute.", "",
             "| Document | Related jurisdictions | Topics | Type / language | Classification | Dates / currency | Original |", "|---|---|---|---|---|---|---|"]
    for d in b["documents"]:
        lines.append("| [%s](%s) | %s | %s | %s / %s | %s | %s → %s; %s | [file](../official/%s) |" %
                     (md(d["title"]), d["url"], ", ".join(d["country_ids"]) or "International reference", ", ".join(d["topic_ids"]) or "Needs review", d["type"], d["lang"], d["classification_status"], d["effective_from"] or "?", d["effective_to"] or "?", d["currency"] or "Not recorded", d["file"]))
    result["SOURCES.md"] = "\n".join(lines) + "\n"
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--as-of", required=True, help="Explicit catalogue date; not a legal-currency certification")
    parser.add_argument("--check", action="store_true", help="Verify generated files without writing")
    args = parser.parse_args(argv)
    bundle = collect(args.as_of)
    generated = outputs(bundle)
    for relative, text in generated.items():
        target = HERE / relative
        if args.check:
            if not target.exists() or target.read_text(encoding="utf-8") != text:
                raise SystemExit("Generated file is missing or stale: " + relative)
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            with target.open("w", encoding="utf-8", newline="") as f:
                f.write(text)
    print(("Checked" if args.check else "Built") + " %s files: %s documents, %s parameters, %s rules, %s dictionary entries." %
          (len(generated), bundle["inventory"]["documents"], bundle["inventory"]["parameters"], bundle["inventory"]["compiled_rules"], bundle["inventory"]["entries"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
