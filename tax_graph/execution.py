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


LEVY = {"income": "income tax", "vat": "VAT", "gst": "GST", "stamp": "stamp duty", "surcharge": "surcharges", "customs": "customs duty",
        "lat": "land appreciation tax", "deed": "deed tax", "property": "property tax", "topup": "top-up tax"}
PHASES = [("structure", "Put the structure in place"), ("facts", "Establish the facts behind each payment"),
          ("decide", "Settle the treatments that move the tax"), ("comply", "File, pay and reconcile"), ("close", "Record and close")]


def _money(currency, value):
    return "%s %s" % (currency, format(value, ",.2f"))


def build_execution(plan, context, candidate_count=None):
    """The workpack of a chosen plan: steps by phase, the tax position, the conservative and the conditional path. A
    strategy's workpack is the same reduced by for_strategy (one path, no "it can fall to")."""
    """An ordered workpack for the chosen plan. It explains, never recomputes: every amount comes from the planner's
    bounds, every date from the engine's clocks. The order follows the work: structure before payments, the facts of a
    payment before a treatment that rests on them, treatments before the filing they change, closing last. Each step says
    why it exists (the tax it serves and how much is at stake), and the head of the plan says what the plan achieves.

    Accepts the planner's region map or its serialised region list. data_used supplies answered values for older saved
    plans. Existing transaction facts remain authoritative; unknown answers never become positive evidence.
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
    company = lambda role: (names.get(role) or role).split("/")[0].strip()
    currency = c.get("currency") or "CNY"
    money = lambda v: _money(currency, v)
    jname = lambda j: JUR.get(j, j)
    as_at = _iso((c.get("event") or {}).get("as_at"))
    regions = p.get("regions") or []
    if isinstance(regions, dict):
        regions = [{"jurisdictions": sorted(k), **v} for k, v in regions.items()]
    members = set(c.get("members") or [x[0] for x in p["structure"]["entities"] if not x[2].startswith("outside")])
    mode = c.get("template") == "recorded"
    steps, paths, known, exclusions = [], [], [], []

    def add(kind, phase, title, why, owner, action, documents, done, status="todo", flows=(), basis=(), due="", depends=()):
        sid = "step-%d" % (len(steps) + 1)
        steps.append({"id": sid, "kind": kind, "phase": phase, "title": title, "why": why, "owner": owner, "action": action,
                      "documents": list(documents), "completion": done, "status": status,
                      "flows": list(flows), "basis": list(dict.fromkeys(basis)), "due": due,
                      "depends_on": [d for d in dict.fromkeys(depends) if d]})
        return sid

    # ---- the tax the plan rests on: conservative rows the group bears, by jurisdiction and flow
    cons_rows = [r for reg in regions for r in reg.get("guaranteed", []) if r[6]]
    best_rows = [r for reg in regions for r in reg.get("best", []) if r[6]]

    def items_text(rows):
        agg = {}
        for fid, jur, levy, who, amt, cites, mine in rows:
            agg[(jur, levy)] = agg.get((jur, levy), 0.0) + amt
        return ", ".join("%s %s %s" % (jname(j), LEVY.get(l, l), money(a)) for (j, l), a in sorted(agg.items()) if abs(a) > 0.005)

    by_jur = {}
    for r in cons_rows:
        by_jur.setdefault(r[1], []).append(r)
    by_jur_best = {}
    for r in best_rows:
        by_jur_best.setdefault(r[1], []).append(r)
    tax_position = [{"jurisdiction": j, "label": jname(j), "conservative": round(sum(r[4] for r in by_jur.get(j, [])), 2),
                     "favourable": round(sum(r[4] for r in by_jur_best.get(j, [])), 2),
                     "items": items_text(by_jur.get(j, []))} for j in sorted(set(by_jur) | set(by_jur_best))]

    # ---- levers: the open conditions, with what each is worth on its own (impacts can overlap)
    cond = []
    seen = set()
    for region in regions:
        for key, description, rule, impact in region.get("conditions", []):
            if key in seen:
                continue
            seen.add(key)
            target = key.rsplit(".", 1)[0]
            if not target.startswith("flow:") and target not in members and not impact:
                continue  # a counterparty's deduction is not a condition for the client's plan
            cond.append((key, description, rule, impact or 0.0, region.get("jurisdictions", [])))
    cond.sort(key=lambda x: -x[3])
    levers = [{"condition": d, "impact": i, "jurisdictions": js, "alone": i > 0.005} for k, d, r, i, js in cond]

    # ---- 1. structure (planning mode: the plan's own actions come before any payment under it)
    structure_ids = []
    for region in regions:
        for text, status, worth in region.get("actions", []):
            why = ("Required by the selected structure; without it the conservative estimate rises by %s." % money(worth)) if worth else \
                  "Part of the selected structure: the payments below are assessed on the basis that this is in place."
            structure_ids.append(add("structure", "structure", "Put in place: " + text.split(" · ")[-1].split(";")[0][:90], why,
                                     "Group tax lead and the affected company directors", text,
                                     ["Approved transaction documents", "Evidence that the action is in place (registration, resolution, certificate or dated record)"],
                                     "The action is in place and its evidence is filed; rerun the assessment if its premises change.",
                                     status="confirmed_input" if status == "confirmed" else "todo"))

    # ---- 2. facts behind each payment
    by_flow = {}
    for fid, income, payer, payee, amount, on in p["structure"]["flows"]:
        if income not in TRANSACTIONS:  # deemed inclusions and top-up items are not new cash payments
            continue
        label, title, docs, instruction = TRANSACTIONS[income]
        rows = [r for r in cons_rows if r[0] == fid]
        why = ("The conservative tax on this payment is %s; every later step relies on these facts." % items_text(rows)) if rows and items_text(rows) else \
              "The treatment of this payment rests on these facts, even where no tax is due on the conservative basis."
        desc = "%s pays %s %s for %s on %s." % (company(payer), company(payee), money(amount), label, on)
        sid = add("evidence", "facts", title, why, "%s finance, with %s finance" % (company(payee), company(payer)),
                  desc + " " + instruction, docs,
                  "A reconciled transaction workpaper with the supporting documents and a named reviewer.", flows=[fid], depends=structure_ids)
        by_flow[fid] = {"payer": payer, "payee": payee, "income": income, "first": sid}
        facts = c.get("flows", {}).get(fid, {})
        for field, text, unit in (("service_days_12m", "Mainland service days", "days"),
                                  ("service_onshore_share", "Service performed in the Mainland", "%"),
                                  ("profit_margin", "Service profit margin", "%"),
                                  ("cost_basis", "Tax cost basis", currency)):
            if facts.get(field) is not None:
                known.append({"flow": fid, "label": text, "value": facts[field], "unit": unit})

    gloss_path = Path(__file__).resolve().parent / "data" / "field_gloss.csv"
    with gloss_path.open(encoding="utf-8-sig") as f:
        gloss = {r["field"]: r for r in csv.DictReader(f)}
    unknown = [(key, gloss.get(key.rsplit(".", 1)[-1], {}).get("gloss", key))
               for key, value, source in p.get("data_used", []) if value is None or value == "unknown"]
    if unknown:
        add("missing_evidence", "facts", "Obtain the facts answered Unknown",
            "Unknown facts are taken at their least favourable value, so they hold the conservative estimate up until a supported answer replaces them.",
            "Assessment owner's tax lead",
            "Obtain supporting records for: %s. Until supported answers are entered and reassessed, keep these facts Unknown and retain the conservative treatment." % "; ".join(text for key, text in unknown),
            [gloss.get(key.rsplit(".", 1)[-1], {}).get("source_hint") or "Source record for " + text for key, text in unknown],
            "Each available fact has a reviewed source and the assessment is rerun; unavailable facts remain explicitly Unknown.",
            status="conditional", depends=[x["first"] for x in by_flow.values()])

    # ---- 3. treatments that move the tax, the largest first
    cond_ids = {}
    joint = [d for k, d, r, i, js in cond if i > 0.005]
    for key, description, rule, impact, js in cond:
        target, field = key.rsplit(".", 1)
        field = field.split(":", 1)[0]
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
        where = " / ".join(jname(j) for j in js) or "the affected jurisdiction"
        if impact > 0.005:
            why = ("Decides %s. Supported on its own, it can lower the conservative estimate by up to %s (%s); unsupported, the conservative treatment stays."
                   % (description, money(impact), where))
        else:
            why = ("Decides %s. On its own it does not lower the conservative estimate%s; it matters together with the other open treatments."
                   % (description, (" (other levers: %s)" % "; ".join(x for x in joint if x != description)) if joint else ""))
        sid = add("condition", "decide", title, why,
                  "%s tax lead and tax adviser" % company(target) if target in c.get("roles", {}) else "Transaction tax lead and tax adviser",
                  action, docs, "A reviewed treatment memo with evidence; any required authority acceptance is recorded separately.",
                  status="conditional", flows=relevant, basis=[rule], depends=[by_flow[f]["first"] for f in relevant])
        cond_ids[key] = (sid, relevant, js)
        paths.append({"step": sid, "condition": description, "impact": impact, "basis": [rule],
                      "if_supported": ("Record the conclusion and reassess; the conservative estimate can fall by up to %s, and only the recomputed amount may be used." % money(impact))
                      if impact > 0.005 else "Record the conclusion and reassess; on its own this does not change the conservative estimate.",
                      "otherwise": "Keep the conservative treatment and its reserve; do not record an unapproved saving."})

    # ---- 4. file, pay and reconcile: dates only from the engine; a passed date calls for verification, not a finding
    deadline_ids = {}
    seen_dates = set()
    for region in regions:
        for fid, clock, due, note in region.get("deadlines", []):
            if not due or (fid, clock, due) in seen_dates:
                continue
            seen_dates.add((fid, clock, due))
            tx = by_flow.get(fid, {})
            past = bool(as_at and due < as_at)
            jur = (region.get("jurisdictions") or [""])[0]
            rows = [r for r in cons_rows if r[0] == fid and (not jur or r[1] == jur)]
            clock_label = {"remit": "tax payment / remittance", "filing": "tax filing", "refund": "refund application", "map": "mutual agreement procedure", "objection": "objection"}.get(clock, clock.replace("_", " "))
            transaction_label = ("the %s from %s to %s" % (TRANSACTIONS[tx["income"]][0], company(tx["payer"]), company(tx["payee"]))) if tx else "the modelled tax item"
            title = ("Check that the %s due %s was made" if past else "Prepare the %s due %s") % (clock_label, due)
            why = ("%s falls due on this date for %s (conservative amount: %s)." % (clock_label[0].upper() + clock_label[1:], transaction_label, items_text(rows))) if rows and items_text(rows) else \
                  "%s for %s falls due on this date." % (clock_label[0].upper() + clock_label[1:], transaction_label)
            action = ("The modelled %s date for %s is %s%s. " % (clock_label, transaction_label, due, "; " + note if note else ""))
            action += ("It has already passed: check whether the obligation was completed and obtain the receipt; if evidence is absent, ask the responsible tax team to determine outstanding steps and any late consequences."
                       if past else "Confirm the applicable calendar and obligation with the responsible tax team, then arrange submission and payment by the confirmed date.")
            basis = [rule for row in region.get("guaranteed", []) if row[0] == fid for rule in row[5]]
            sid = add("deadline", "comply", title, why, "%s tax team, with %s tax team" % (company(tx.get("payer", "Payer")), company(tx.get("payee", "Recipient"))),
                      action, ["Tax computation and filing package", "Submission acknowledgement and tax payment receipt"],
                      "The applicable obligation and date are verified, and completion or remediation is documented.",
                      status="check_now" if past else "todo", flows=[fid], basis=basis, due=due,
                      depends=[] if past else [tx.get("first")] + [s for k, (s, fl, js) in cond_ids.items() if fid in fl])
            deadline_ids.setdefault(fid, []).append(sid)

    for claim in p.get("claims", []):
        fid, jurisdiction, actual, lo, hi, confirmed, potential, shortfall, clocks, routes = claim
        if actual is None:
            exclusions.append("%s / %s: the model marks the settled item closed; no open recovery route is recommended." % (fid, jname(jurisdiction)))
            continue
        tx = by_flow.get(fid, {})
        open_clocks = {k: v for k, v in (clocks or {}).items() if v and (not as_at or v >= as_at)}
        recovery = bool(potential and potential > 0 and open_clocks)
        add("recovery" if recovery else "settlement", "comply", "Review the supported recovery route" if recovery else "Reconcile income tax already paid",
            ("%s was paid in %s; up to %s may be recoverable while the route is open." % (money(actual), jname(jurisdiction), money(potential))) if recovery else
            ("%s was paid in %s; the model finds no open recovery route." % (money(actual), jname(jurisdiction))),
            "%s tax lead and local tax adviser" % company(tx.get("payee", "Recipient")),
            ("Reconcile %s actually paid in %s with the modelled exposure. " % (money(actual), jname(jurisdiction))) +
            (("Review eligibility and the open deadlines for %s; submit only after the evidence supports the claim. " % ", ".join(routes)) if recovery else
             "Check for a supported shortfall or correction; the current output does not establish an actionable recovery route. ") +
            "Potential recovery is not an approved or paid refund.",
            ["Withholding or income tax payment receipt", "Original assessment and computation", "Evidence supporting the claim and applicable deadline"],
            "Paid tax is reconciled and any supported claim or shortfall has a documented decision and submission record.",
            status="conditional" if recovery else "todo", flows=[fid], due=min(open_clocks.values()) if recovery else "",
            depends=[tx.get("first")])

    for region in regions:
        jurisdictions = region.get("jurisdictions", [])
        rows = [r for side in ("guaranteed", "best") for r in region.get(side, []) if r[6]]
        if not rows or len(jurisdictions) != 1:
            continue
        j = jurisdictions[0]
        cons = [r for r in region.get("guaranteed", []) if r[6]]
        best = [r for r in region.get("best", []) if r[6]]
        flows_here = sorted({r[0] for r in rows})
        owners = sorted({company(r[3]) for r in rows})
        basis = sorted({rule for row in rows for rule in row[5]})
        affecting = [s for k, (s, fl, js) in cond_ids.items() if set(fl) & set(flows_here) or j in js]
        if cons and items_text(cons):
            title = "Settle the %s tax: %s" % (jname(j), money(sum(r[4] for r in cons)))
            why = "Conservative %s tax: %s." % (jname(j), items_text(cons))
            if best and abs(sum(r[4] for r in best) - sum(r[4] for r in cons)) > 0.005:
                why += " If the open treatments are supported, it becomes %s after reassessment." % money(sum(r[4] for r in best))
        else:
            title = "Confirm the %s position" % jname(j)
            why = "No %s tax on the conservative basis." % jname(j)
            if best and items_text(best):
                why += " If the open treatments are supported, %s arises here (%s)." % (money(sum(r[4] for r in best)), items_text(best))
        add("reconciliation", "comply", title, why, ", ".join(owners) + " finance and local tax adviser",
            "Reconcile the transaction income, costs, taxes and any credit with the local accounts and actual payment evidence. Use the conservative position for unresolved treatment; verify credit entitlement separately from proof that tax was paid.",
            ["Transaction tax workpaper and local return", "Income and expense ledger", "Foreign tax assessment and receipts, if a credit is claimed"],
            "The local return position, reserve and any permitted credit are approved by the responsible reviewer.",
            flows=flows_here, basis=basis,
            depends=[by_flow[f]["first"] for f in flows_here if f in by_flow] + affecting + [d for f in flows_here for d in deadline_ids.get(f, [])])

    exclusions += ["%s: %s" % (cand, why) for cand, why, *rest in p.get("unmodelled", [])]
    # ---- 5. close
    signoff = add("signoff", "close", "Approve the workpack and keep the audit trail",
                  "Closes the plan: who decided what, on which evidence, and what remains open.", "Assessment owner's finance lead",
                  "Assign each work item, review the conditional decisions and reserve, and retain contracts, computations, approvals and submission receipts. Rerun the assessment when a material fact or treatment changes.",
                  ["Reviewed transaction workpapers", "Signed decision log", "Filing acknowledgements and payment receipts, where applicable"],
                  "The responsible reviewer signs the workpack; unresolved treatments and remaining actions are explicitly recorded.",
                  depends=[s["id"] for s in steps if s["kind"] in ("reconciliation", "recovery", "settlement")] or [s["id"] for s in steps])
    # steps in phase order (structure, facts, decide, comply, close); dependencies always point backwards
    order = {ph: i for i, (ph, _) in enumerate(PHASES)}
    steps.sort(key=lambda s: (order[s["phase"]], int(s["id"].split("-")[1])))

    conditional = any(s["status"] == "conditional" for s in steps) or (p.get("best") is not None and p.get("guaranteed") is not None and p["best"] < p["guaranteed"] - 0.005)
    urgent = [s for s in steps if s["status"] == "check_now"]
    comparison = ("The recorded arrangement is retained. Alternative structures were not compared; this plan implements and resolves the entered transactions."
                  if mode else "Implement the selected structure and transactions. The comparison covers only candidates represented by the selected planning template.")
    sc = p.get("scope") or {}
    if sc.get("policy") == "income_only":                        # decision D52
        comparison += " Scope: income tax only; VAT, GST, stamp duty, customs duty and property taxes are not assessed."
        ex = sc.get("excluded") or []
        if ex:
            from .scope import compact
            comparison += " %d candidate structure%s not compared because a step would attract another tax: %s." % (
                len(ex), "" if len(ex) == 1 else "s", compact([w for e in ex for w in e["why"]]))
    # what the plan achieves, in one paragraph
    flows_text = "; ".join("%s %s from %s to %s" % (money(row[4]), TRANSACTIONS[row[1]][0], company(row[2]), company(row[3]))
                           for row in p["structure"]["flows"] if row[1] in TRANSACTIONS)
    objective = ("Settle the tax on %s at the lowest amount the facts support." % flows_text) if mode else \
                ("Adopt the structure with the lowest guaranteed tax among the %s compared%s, and carry out %s." % (
                    candidate_count or "structures", (" (%s)" % "; ".join("%s = %s" % (k, "none" if v is None else v) for k, v in p["cand"].items())) if p.get("cand") else "", flows_text or "its payments"))
    parts = {"objective": objective, "conservative": "", "fall": "", "start": ""}
    if p.get("guaranteed") is not None:
        parts["conservative"] = " Conservative tax: %s%s." % (money(p["guaranteed"]), (" (%s)" % items_text(cons_rows)) if items_text(cons_rows) else "")
    if p.get("best") is not None and p.get("guaranteed") is not None and p["best"] < p["guaranteed"] - 0.005:
        moving = [l for l in levers if l["alone"]]
        parts["fall"] = " It can fall to %s if the favourable treatment is supported on: %s." % (money(p["best"]), "; ".join("“%s”" % l["condition"] for l in moving[:3]) or "the open treatments")
    if urgent:
        parts["start"] = " Start with step %d: %s." % (next(i for i, s in enumerate(steps, 1) if s is urgent[0]), urgent[0]["title"][0].lower() + urgent[0]["title"][1:])
    course = objective + parts["conservative"] + parts["fall"] + parts["start"]
    positions = [{"title": "Conservative implementation path", "amount": p.get("guaranteed"),
                  "when": "Use the current supported facts and required actions, with unresolved treatment taken conservatively. Verify the liability and actual payments before filing.",
                  "steps": [s["id"] for s in steps if s["kind"] != "signoff"]}]
    if p.get("best") is not None and p.get("guaranteed") is not None and p["best"] < p["guaranteed"] - 0.005:
        positions.append({"title": "Conditional treatment path", "amount": p["best"],
                          "when": "Use only after the favourable treatment is supported on %s and a new assessment confirms the result. This is a conditional modelled outcome, not an approved saving." % (
                              "; ".join("“%s”" % l["condition"] for l in levers if l["alone"]) if any(l["alone"] for l in levers) else "the missing facts and open treatments"),
                          "steps": [s["id"] for s in steps if s["kind"] in ("condition", "missing_evidence", "recovery")]})
    return {"version": 2, "title": "Implementation plan", "status": "conditional" if conditional or urgent else "ready_for_review",
            "objective": objective, "recommended_course": course, "course_parts": parts, "tax_position": tax_position, "levers": levers,
            "phases": [{"id": ph, "title": t, "steps": [s["id"] for s in steps if s["phase"] == ph]} for ph, t in PHASES if any(s["phase"] == ph for s in steps)],
            "treatment_paths": positions,
            "summary": ("Complete the tax treatment and compliance work for the recorded transactions." if mode else "Implement the selected arrangement with the steps below."),
            "comparison": comparison, "candidate_count": candidate_count, "as_at": as_at, "currency": currency,
            "next_action": urgent[0]["id"] if urgent else (steps[0]["id"] if steps else signoff),
            "known_facts": known, "steps": steps, "decision_paths": paths, "exclusions": exclusions,
            "completion_note": "Ready for review means the workpack is generated. It does not mean documents have been approved, filings submitted, taxes paid or authority acceptance obtained."}


def for_strategy(execution: dict, strategy: dict) -> dict:
    """A strategy already fixes which rulings it takes as favourable: its workpack keeps one path (the strategy's own
    guaranteed tax) and drops the 'conditional treatment path' and the 'it can fall to' sentence, which the strategy
    list expresses instead. Unknown facts that could still lower the tax stay as evidence steps."""
    e = dict(execution)
    e["strategy"] = strategy
    cp = e.get("course_parts") or {}
    e["recommended_course"] = (cp.get("objective") or e.get("objective") or "") + (cp.get("conservative") or "") + (cp.get("start") or "")
    e["treatment_paths"] = [dict(e["treatment_paths"][0], title="This strategy's path", amount=strategy.get("guaranteed", e["treatment_paths"][0].get("amount")),
                                 when="The guaranteed tax of this strategy, with its rulings taken as the list says. Verify the liability and actual payments before filing.")] if e.get("treatment_paths") else []
    e["comparison"] = (e.get("comparison") or "") + " This window shows strategy #%s of the list; the other strategies are the alternatives." % strategy.get("id")
    return e


def render_execution(execution):
    e = execution
    cur = e["currency"]
    lines = ["## Implementation plan", "", "**Aim and result:** " + e["recommended_course"], "", e["comparison"], ""]
    if e.get("tax_position"):
        lines += ["| Jurisdiction | Conservative | If treatments are supported | Made up of |", "|---|---|---|---|"]
        lines += ["| %s | %s | %s | %s |" % (t["label"], format(t["conservative"], ",.2f"), format(t["favourable"], ",.2f"), t["items"] or "—") for t in e["tax_position"]]
        lines += [""]
    lines += ["Status: %s. Assessment date: %s. Currency: %s." % (e["status"], e["as_at"], cur), "", e["completion_note"], ""]
    for path in e["treatment_paths"]:
        lines += ["**%s: %s %s.** %s" % (path["title"], cur, format(path["amount"], ",.2f") if path["amount"] is not None else "not computed", path["when"]), ""]
    number = {s["id"]: i for i, s in enumerate(e["steps"], 1)}
    phases = e.get("phases") or [{"title": "", "steps": [s["id"] for s in e["steps"]]}]
    by_id = {s["id"]: s for s in e["steps"]}
    for k, ph in enumerate(phases, 1):
        if ph["title"]:
            lines += ["### Phase %d. %s" % (k, ph["title"]), ""]
        for sid in ph["steps"]:
            step = by_id[sid]
            lines += ["#### %d. %s" % (number[sid], step["title"]), ""]
            if step.get("why"):
                lines += ["Why: " + step["why"], ""]
            lines += ["Owner: %s. Status: %s." % (step["owner"], step["status"]), "", step["action"], "",
                      "Evidence: " + "; ".join(step["documents"]), "", "Completion: " + step["completion"], ""]
            if step["depends_on"]:
                lines += ["After steps: " + ", ".join(str(number[d]) for d in step["depends_on"] if d in number), ""]
            if step["due"]:
                lines += ["Modelled date: " + step["due"], ""]
            if step["basis"]:
                lines += ["Rule references: " + ", ".join(step["basis"]), ""]
    if e["decision_paths"]:
        lines += ["### Conditional decisions", ""]
        for path in e["decision_paths"]:
            lines += ["- %s: if supported, %s Otherwise: %s" % (path["condition"], path["if_supported"][0].lower() + path["if_supported"][1:], path["otherwise"])]
        lines += ["", "Condition impacts may overlap and must not be added as separate savings.", ""]
    if e["exclusions"]:
        lines += ["### Scope limits", ""] + ["- " + x for x in e["exclusions"]] + [""]
    st = e.get("strategy")
    if st:
        taken = "; ".join(st["labels"].get(k, k) for k in st["assumes_favourable"]) or "none: every open ruling taken against the taxpayer"
        lines += ["### This path", "", "Rulings taken as favourable on this path: %s." % taken]
        if st.get("fallback"):
            lines += ["If one of them fails in practice, continue with strategy #%d (guaranteed %s %s); answer that ruling No and reassess." % (
                st["fallback"], cur, format(st["fallback_guaranteed"], ",.2f") if st.get("fallback_guaranteed") is not None else "")]
        lines += [""]
    return "\n".join(lines)
