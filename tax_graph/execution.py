"""Turn a computed plan into an ordered, evidence-based implementation workpack.

This layer schedules work against the chosen flows, rule conditions and clocks. It
does not invent tax treatments, change the bounds, or treat a work item as filed.
"""
import copy
import csv
from pathlib import Path

JUR = {"CN": "Mainland China", "HK": "Hong Kong", "SG": "Singapore"}
TRANSACTIONS = {
    "SERVICE_FEE": ("service fee", "Prepare the service treatment file",
                    ["Signed service contract, deliverables and contractual tax allocation", "Timesheets and work locations", "Project revenue and cost ledger"],
                    "Reconcile the service scope, performance locations, onshore share, project margin and who contractually bears each tax with the invoice, payment and modelled tax items before using the amounts for filing."),
    "DIVIDEND": ("dividend", "Prepare the dividend distribution file",
                 ["Dividend resolution and accounts of distributable profits", "Share register and acquisition dates", "Evidence of underlying profit taxes and bank remittance"],
                 "Match this dividend to its own resolution, recipient, holding period and underlying profits; keep each distribution separate."),
    "SHARE_TRANSFER": ("share disposal", "Prepare the share disposal file",
                       ["Share sale agreement and completion statement", "Historical share register and actual acquisition cost ledger", "Valuation and property composition evidence"],
                       "Reconcile the buyer, seller, target, stake sold, consideration and tax basis; distinguish the gross sale price from the gain."),
    "INTEREST": ("interest", "Prepare the financing and interest file",
                 ["Loan agreement and interest schedule", "Use of funds and lender details", "Interest benchmark and related-party pricing support"],
                 "Match the interest to the borrowing period, loan purpose, rate and contractual allocation of withholding tax."),
    "ROYALTY": ("royalty", "Prepare the licence and royalty file",
                ["Licence agreement and rights granted", "IP ownership and substance records", "Royalty pricing and payment ledger"],
                "Identify the licensed rights, owner, actual functions and payment basis before applying the modelled royalty treatment."),
    "GOODS": ("goods sale", "Prepare the trading transaction file",
              ["Sales and purchase contracts", "Inventory cost, shipping and delivery records", "Related-party pricing support, if applicable"],
              "Reconcile the seller's cost and margin, supply and resale legs, delivery locations and payment; customs duties remain outside current coverage."),
    "CAPITAL_REDUCTION": ("capital reduction", "Prepare the capital reduction file",
                          ["Approved reduction resolution and share register", "Paid-in capital and tax basis ledger", "Accumulated profits and distribution calculation"],
                          "Separate the capital return from the profit distribution using supported accounts and the actual reduction ratio."),
    "LIQUIDATION": ("liquidation distribution", "Prepare the liquidation distribution file",
                    ["Liquidation resolution and final accounts", "Shareholder tax basis and share cancellation records", "Residual profit and distribution calculation"],
                    "Reconcile residual assets, accumulated profits, returned capital and cancelled shares before using the modelled split."),
    "IP_TRANSFER": ("IP ownership transfer", "Prepare the IP transfer file",
                    ["IP assignment agreement and valuation", "Tax basis, amortisation and allowances ledger", "Technology and ownership transfer records"],
                    "Distinguish an ownership transfer from a licence; verify the seller's remaining tax basis and any prior allowances."),
    "PROPERTY_TRANSFER": ("property sale", "Prepare the property sale file",
                          ["Property sale agreement and title", "Property location, use and valuation", "Acquisition cost and tax basis ledger"],
                          "Verify the property's location, use, consideration and tax basis; resolve any taxes the model identifies as unmodelled before completion."),
    "PROPERTY_RENT": ("property rent", "Prepare the property letting file",
                      ["Lease and property title", "Property location and use", "Rent period, receipts and expense ledger"],
                      "Match the rental period and gross rent to the lease and property location; reconcile the modelled deductions with evidence."),
}


def _iso(value):
    return value.isoformat() if hasattr(value, "isoformat") else str(value or "")


def context_from_graph(case, event, graph):
    return {"template": "", "currency": case.currency, "names": getattr(case, "names", {}),
            "roles": {k: {"loc": e.loc, "attrs": dict(e.attrs)} for k, e in graph.entities.items()},
            "flows": {f.id: dict(f.attrs) for f in graph.flows},
            "members": sorted(graph.group()), "settled": case.settled,
            "event": {"as_at": _iso(event.as_at or event.on)}}


def build_execution(plan, context, candidate_count=None):
    """Accept either the planner's region map or its serialized region list.

    data_used supplies answered values for older saved plans. Existing transaction
    facts remain authoritative; unknown answers never become positive evidence.
    """
    c = copy.deepcopy(context)
    p = plan
    for key, value, source in p.get("data_used", []):
        if value is None or value == "unknown":
            continue
        if key.startswith("flow:"):
            fid, field = key[5:].rsplit(".", 1)
            c.setdefault("flows", {}).setdefault(fid, {})[field] = value
        elif key.startswith("group."):
            continue
        elif "." in key:
            role, field = key.split(".", 1)
            c.setdefault("roles", {}).setdefault(role, {}).setdefault("attrs", {})[field] = value
    names = c.get("names") or {}
    company = lambda role: names.get(role, role)
    currency = c.get("currency") or "CNY"
    as_at = _iso((c.get("event") or {}).get("as_at"))
    regions = p.get("regions") or []
    if isinstance(regions, dict):
        regions = [{"jurisdictions": sorted(k), **v} for k, v in regions.items()]
    members = set(c.get("members") or [x[0] for x in p["structure"]["entities"] if not x[2].startswith("outside")])
    steps, paths, known, exclusions = [], [], [], []

    def add(kind, title, owner, action, documents, done, status="todo", flows=(), basis=(), due="", depends=()):
        sid = "step-%d" % (len(steps) + 1)
        steps.append({"id": sid, "kind": kind, "title": title, "owner": owner, "action": action,
                      "documents": list(documents), "completion": done, "status": status,
                      "flows": list(flows), "basis": list(dict.fromkeys(basis)), "due": due,
                      "depends_on": list(depends)})
        return sid

    by_flow = {}
    for fid, income, payer, payee, amount, on in p["structure"]["flows"]:
        if income not in TRANSACTIONS:  # deemed inclusions and top-up items are not new cash payments
            continue
        label, title, docs, instruction = TRANSACTIONS[income]
        desc = "%s pays %s %s %s for %s on %s." % (company(payer), company(payee), currency, format(amount, ",.2f"), label, on)
        sid = add("evidence", title, "%s finance, with %s finance" % (company(payee), company(payer)),
                  desc + " " + instruction, docs,
                  "A reconciled transaction workpaper with the supporting documents and a named reviewer.", flows=[fid])
        by_flow[fid] = {"payer": payer, "payee": payee, "income": income, "first": sid}
        facts = c.get("flows", {}).get(fid, {})
        for field, text, unit in (("service_days_12m", "Mainland service days", "days"),
                                  ("service_onshore_share", "Service performed in the Mainland", "%"),
                                  ("profit_margin", "Service profit margin", "%"),
                                  ("cost_basis", "Tax cost basis", currency)):
            if facts.get(field) is not None:
                known.append({"flow": fid, "label": text, "value": facts[field], "unit": unit})

    # Structural steps selected by the planner remain part of the execution order.
    for region in regions:
        for text, status, worth in region.get("actions", []):
            add("structure", "Complete the selected structural or tax action", "Group tax lead and the affected company directors",
                text, ["Approved transaction documents", "Evidence supporting the selected action"],
                "The named action has been completed and its evidence checked; rerun if its premises change.",
                status="confirmed_input" if status == "confirmed" else "todo")

    gloss_path = Path(__file__).resolve().parent / "data" / "field_gloss.csv"
    with gloss_path.open(encoding="utf-8-sig") as f:
        gloss = {r["field"]: r for r in csv.DictReader(f)}
    unknown = [(key, gloss.get(key.rsplit(".", 1)[-1], {}).get("gloss", key))
               for key, value, source in p.get("data_used", []) if value is None or value == "unknown"]
    if unknown:
        add("missing_evidence", "Resolve unknown facts before adopting a lower estimate", "Assessment owner's tax lead",
            "Obtain supporting records for: %s. Until supported answers are entered and reassessed, keep these facts Unknown and retain the conservative treatment." % "; ".join(text for key, text in unknown),
            [gloss.get(key.rsplit(".", 1)[-1], {}).get("source_hint") or "Source record for " + text for key, text in unknown],
            "Each available fact has a reviewed source and the assessment is rerun; unavailable facts remain explicitly Unknown.", status="conditional")
    seen = set()
    for region in regions:
        for key, description, rule, impact in region.get("conditions", []):
            if key in seen:
                continue
            seen.add(key)
            target, field = key.rsplit(".", 1)
            field = field.split(":", 1)[0]
            if not target.startswith("flow:") and target not in members and not impact:
                continue  # a counterparty's deduction is not a condition for the client's plan
            relevant = [fid for fid, tx in by_flow.items() if target in (tx["payee"], tx["payer"], "flow:" + fid)]
            docs = [gloss.get(field, {}).get("source_hint") or "Documents supporting the stated tax condition",
                    "Written treatment analysis and any relevant authority correspondence"]
            title = "Resolve the outstanding tax treatment"
            action = "Prepare a supported position on: %s. Record the conclusion and any authority response." % description
            if field == "service_fee_is_royalty_for_know_how":
                title = "Resolve service versus know-how royalty treatment"
                action = ("Review the contract and technology delivered to distinguish project services from rights to use know-how. "
                          "Prepare a classification memo; if the treatment is disputed, obtain the relevant authority response before relying on the favourable modelled outcome.")
                docs = ["Signed contract and technical deliverables", "Rights granted and know-how access terms", "Classification memo and relevant authority correspondence"]
            elif field == "ppt":
                title = "Document commercial purpose and treaty eligibility"
                action = ("Document the commercial reasons for the arrangement, verify the recipient's residence evidence and assess the treaty anti-abuse condition. "
                          "Record unresolved issues; do not treat an Unknown answer as treaty clearance.")
                docs = ["Commercial purpose statement and decision records", "Tax residence certificate for the payment year", "Treaty eligibility analysis and relevant authority correspondence"]
            elif field == "beneficial_owner":
                title = "Substantiate beneficial ownership of the income"
                docs += ["Ownership chart, functions and income onward-payment records"]
            elif field == "substance_ruled_adequate":
                title = "Resolve the Hong Kong substance condition"
                docs += ["Local activity, people and expenditure records", "Relevant Hong Kong IRD determination"]
            sid = add("condition", title, "%s tax lead and tax adviser" % company(target) if target in c.get("roles", {}) else "Transaction tax lead and tax adviser",
                      action, docs, "A reviewed treatment memo with evidence; any required authority acceptance is recorded separately.",
                      status="conditional", flows=relevant, basis=[rule], depends=[by_flow[f]["first"] for f in relevant])
            paths.append({"step": sid, "condition": description, "impact": impact, "basis": [rule],
                          "if_supported": "Record the supported conclusion and reassess. Use a favourable amount only if the recomputed assessment supports it; evidence can also confirm an unfavourable treatment.",
                          "otherwise": "Keep the conservative treatment and reserve; do not record an unapproved saving."})

    # Dates come only from the engine. A passed clock calls for verification, not a claim that a filing was missed.
    seen_dates = set()
    for region in regions:
        for fid, clock, due, note in region.get("deadlines", []):
            if not due or (fid, clock, due) in seen_dates:
                continue
            seen_dates.add((fid, clock, due))
            tx = by_flow.get(fid, {})
            past = bool(as_at and due < as_at)
            title = "Verify the passed filing or payment date" if past else "Prepare the filing or payment package"
            clock_label = {"remit": "tax payment / remittance", "filing": "tax filing", "refund": "refund application", "map": "mutual agreement procedure", "objection": "objection"}.get(clock, clock.replace("_", " "))
            transaction_label = ("the %s from %s to %s" % (TRANSACTIONS[tx["income"]][0], company(tx["payer"]), company(tx["payee"]))) if tx else "the modelled tax item"
            action = ("The modelled %s date for %s is %s%s. " % (clock_label, transaction_label, due, "; " + note if note else ""))
            action += ("Check whether the obligation was completed and obtain the receipt; if evidence is absent, ask the responsible tax team to determine outstanding steps and any late consequences."
                       if past else "Confirm the applicable calendar and obligation with the responsible tax team, then arrange submission and payment by the confirmed date.")
            basis = [rule for row in region.get("guaranteed", []) if row[0] == fid for rule in row[5]]
            add("deadline", title, "%s tax team, with %s tax team" % (company(tx.get("payer", "Payer")), company(tx.get("payee", "Recipient"))),
                action, ["Tax computation and filing package", "Submission acknowledgement and tax payment receipt"],
                "The applicable obligation and date are verified, and completion or remediation is documented.",
                status="check_now" if past else "todo", flows=[fid], basis=basis, due=due,
                depends=[tx["first"]] if tx and not past else [])

    for claim in p.get("claims", []):
        fid, jurisdiction, actual, lo, hi, confirmed, potential, shortfall, clocks, routes = claim
        if actual is None:
            exclusions.append("%s / %s: the model marks the settled item closed; no open recovery route is recommended." % (fid, JUR.get(jurisdiction, jurisdiction)))
            continue
        tx = by_flow.get(fid, {})
        open_clocks = {k: v for k, v in (clocks or {}).items() if v and (not as_at or v >= as_at)}
        recovery = bool(potential and potential > 0 and open_clocks)
        add("recovery" if recovery else "settlement", "Review the supported recovery route" if recovery else "Reconcile income tax already paid",
            "%s tax lead and local tax adviser" % company(tx.get("payee", "Recipient")),
            ("Reconcile %s %s actually paid in %s with the modelled exposure. " % (currency, format(actual, ",.2f"), JUR.get(jurisdiction, jurisdiction))) +
            (("Review eligibility and the open deadlines for %s; submit only after the evidence supports the claim. " % ", ".join(routes)) if recovery else
             "Check for a supported shortfall or correction; the current output does not establish an actionable recovery route. ") +
            "Potential recovery is not an approved or paid refund.",
            ["Withholding or income tax payment receipt", "Original assessment and computation", "Evidence supporting the claim and applicable deadline"],
            "Paid tax is reconciled and any supported claim or shortfall has a documented decision and submission record.",
            status="conditional" if recovery else "todo", flows=[fid], due=min(open_clocks.values()) if recovery else "")

    # Each relevant jurisdiction gets a concrete reconciliation task, including zero local tax where a condition controls it.
    for region in regions:
        jurisdictions = region.get("jurisdictions", [])
        rows = [r for side in ("guaranteed", "best") for r in region.get(side, []) if r[6]]
        if not rows or len(jurisdictions) != 1:
            continue
        jurisdiction = jurisdictions[0]
        owners = sorted({company(r[3]) for r in rows})
        basis = sorted({rule for row in rows for rule in row[5]})
        add("reconciliation", "Reconcile the %s tax position" % JUR.get(jurisdiction, jurisdiction), ", ".join(owners) + " finance and local tax adviser",
            "Reconcile the selected transaction income, costs, taxes and any credit with the local accounts and actual payment evidence. Use the conservative estimate for unresolved treatment; verify credit entitlement separately from proof that tax was paid.",
            ["Transaction tax workpaper and local return", "Income and expense ledger", "Foreign tax assessment and receipts, if a credit is claimed"],
            "The local return position, reserve and any permitted credit are approved by the responsible reviewer.",
            flows=sorted({r[0] for r in rows}), basis=basis, depends=[x["id"] for x in steps if x["kind"] in ("condition", "deadline")])

    exclusions += ["%s: %s" % (cand, why) for cand, why, *rest in p.get("unmodelled", [])]
    signoff = add("signoff", "Approve the workpack and retain the audit trail", "Assessment owner's finance lead",
                  "Assign each work item, review the conditional decisions and reserve, and retain contracts, computations, approvals and submission receipts. Rerun the assessment when a material fact or treatment changes.",
                  ["Reviewed transaction workpapers", "Signed decision log", "Filing acknowledgements and payment receipts, where applicable"],
                  "The responsible reviewer signs the workpack; unresolved treatments and remaining actions are explicitly recorded.",
                  depends=[s["id"] for s in steps])
    conditional = any(s["status"] == "conditional" for s in steps) or (p.get("best") is not None and p.get("guaranteed") is not None and p["best"] < p["guaranteed"] - 0.005)
    urgent = any(s["status"] == "check_now" for s in steps)
    mode = c.get("template") == "recorded"
    comparison = ("The recorded arrangement is retained. Alternative structures were not compared; this plan implements and resolves the entered transactions."
                  if mode else "Implement the selected structure and transactions. The comparison covers only candidates represented by the selected planning template.")
    treatment = any(s["kind"] == "condition" for s in steps)
    course = ("Retain the recorded parties and transaction dates" if mode else "Adopt the selected structure and payment arrangement")
    course += "; resolve the identified tax treatments and complete the local filing and reconciliation work." if treatment else "; complete the transaction evidence, local compliance and settlement work."
    if not mode and p.get("cand"):
        course += " Selected choices: " + "; ".join("%s = %s" % item for item in p["cand"].items()) + "."
    if len(by_flow) == 1:
        fid = next(iter(by_flow))
        row = next(f for f in p["structure"]["flows"] if f[0] == fid)
        course = "For the %s %s %s from %s to %s: " % (currency, format(row[4], ",.2f"), TRANSACTIONS[row[1]][0], company(row[2]), company(row[3])) + course[0].lower() + course[1:]
    positions = [{"title": "Conservative implementation path", "amount": p.get("guaranteed"),
                  "when": "Use the current supported facts and required actions, with unresolved treatment taken conservatively. Verify the liability and actual payments before filing.",
                  "steps": [s["id"] for s in steps if s["kind"] != "signoff"]}]
    if p.get("best") is not None and p.get("guaranteed") is not None and p["best"] < p["guaranteed"] - 0.005:
        positions.append({"title": "Conditional treatment path", "amount": p["best"],
                          "when": "Use only after the missing facts and favourable treatment are supported and a new assessment confirms the result. This is a conditional modelled outcome, not an approved saving.",
                          "steps": [s["id"] for s in steps if s["kind"] in ("condition", "missing_evidence", "recovery")]})
    return {"version": 1, "title": "Implementation plan", "status": "conditional" if conditional or urgent else "ready_for_review",
            "recommended_course": course, "treatment_paths": positions,
            "summary": ("Complete the tax treatment and compliance work for the recorded transactions." if mode else "Implement the selected arrangement with the steps below."),
            "comparison": comparison, "candidate_count": candidate_count, "as_at": as_at, "currency": currency,
            "next_action": next((s["id"] for s in steps if s["status"] == "check_now"), steps[0]["id"] if steps else signoff),
            "known_facts": known, "steps": steps, "decision_paths": paths, "exclusions": exclusions,
            "completion_note": "Ready for review means the workpack is generated. It does not mean documents have been approved, filings submitted, taxes paid or authority acceptance obtained."}


def render_execution(execution):
    e = execution
    lines = ["## Implementation plan", "", "**Recommended course:** " + e["recommended_course"], "", e["comparison"], "",
             "Status: %s. Assessment date: %s. Currency: %s." % (e["status"], e["as_at"], e["currency"]), "", e["completion_note"], ""]
    for path in e["treatment_paths"]:
        lines += ["**%s: %s %s.** %s" % (path["title"], e["currency"], format(path["amount"], ",.2f") if path["amount"] is not None else "not computed", path["when"]), ""]
    for i, step in enumerate(e["steps"], 1):
        lines += ["### %d. %s" % (i, step["title"]), "", "Owner: %s. Status: %s." % (step["owner"], step["status"]), "", step["action"], "",
                  "Evidence: " + "; ".join(step["documents"]), "", "Completion: " + step["completion"], ""]
        if step["depends_on"]:
            lines += ["Depends on: " + ", ".join(step["depends_on"]), ""]
        if step["due"]:
            lines += ["Modelled date: " + step["due"], ""]
        if step["basis"]:
            lines += ["Rule references: " + ", ".join(step["basis"]), ""]
    if e["decision_paths"]:
        lines += ["### Conditional decisions", ""]
        for path in e["decision_paths"]:
            lines += ["- %s: %s Otherwise: %s" % (path["condition"], path["if_supported"], path["otherwise"])]
        lines += ["", "Condition impacts may overlap and must not be added as separate savings.", ""]
    if e["exclusions"]:
        lines += ["### Scope limits", ""] + ["- " + x for x in e["exclusions"]] + [""]
    return "\n".join(lines)
