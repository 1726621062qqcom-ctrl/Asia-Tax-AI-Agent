# -*- coding: utf-8 -*-
"""Checks of the local page's server (界面.md) without a browser: the server starts on a free port, every route answers
JSON of the expected shape, paths outside the project are refused, a review and an answers file are written where the
pipeline and the planner read them, and the English workspace serves its scripts and styles.

    python -m tax_graph.check_ui          (conda env "pytorch")
"""
import io
import json
import re
import shutil
import sys
import tempfile
import threading
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path

from .ui.server import Handler, ROOT, STATIC


def main():
    out = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    results = []

    def check(ok, text):
        results.append(ok)
        out.write("%-4s %s\n" % ("ok" if ok else "FAIL", text))
        out.flush()

    srv = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    port = srv.server_address[1]
    th = threading.Thread(target=srv.serve_forever, daemon=True)
    th.start()
    base = "http://127.0.0.1:%d" % port

    def get(path):
        try:
            with urllib.request.urlopen(base + path, timeout=120) as r:
                return r.status, r.read()
        except urllib.error.HTTPError as e:
            return e.code, e.read()

    def post(path, body):
        req = urllib.request.Request(base + path, data=json.dumps(body).encode("utf-8"), headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return r.status, json.loads(r.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            return e.code, json.loads(e.read().decode("utf-8"))

    try:
        code, page = get("/")
        html = page.decode("utf-8")
        check(code == 200 and "<title>" in html and '/static/app.js' in html and 'lang="en"' in html and 'l-zh' not in html, "the page serves the English workspace and external assets")
        code, js_body = get("/static/app.js")
        js = js_body.decode("utf-8")
        for asset in ("intake.js", "review.js", "execution.js"):
            asset_code, asset_body = get("/static/" + asset)
            check(asset_code == 200, "the workspace serves " + asset)
            js += "\n" + asset_body.decode("utf-8")
        node = shutil.which("node")
        if node:
            import subprocess
            jsf = ROOT / "out" / "_check_ui.js"
            jsf.write_text(js, encoding="utf-8")
            r = subprocess.run([node, "--check", str(jsf)], capture_output=True, text=True)
            jsf.unlink()
            check(r.returncode == 0, "the page's script parses (node --check)%s" % ("" if r.returncode == 0 else ": " + r.stderr[:300]))
        else:
            check(True, "the page's script: node not installed, syntax not checked here")
        code, body = get("/api/cases")
        cases = json.loads(body)
        check(code == 200 and cases and all({"path", "case_id", "roles", "flows", "provenance"} <= set(c) for c in cases), "/api/cases lists every case file with roles, flows and provenance counts (%d)" % len(cases))
        c0 = next(c for c in cases if c["case_id"] == "K3-mirxes-2026")
        code, body = get("/api/case?path=" + c0["path"])
        d = json.loads(body)
        check(code == 200 and d["case"]["roles"] and "answers_path" in d, "/api/case returns the case file and where its answers go")
        code, body = get("/api/runs")
        runs = json.loads(body)
        check(code == 200 and isinstance(runs, list) and all({"dir", "status", "stages"} <= set(r) for r in runs), "/api/runs lists pipeline runs with their stage statuses (%d)" % len(runs))
        if runs:
            code, body = get("/api/run?dir=" + runs[0]["dir"])
            rd = json.loads(body)
            check(code == 200 and "manifest.json" in rd["artefacts"] and "rows" in rd, "/api/run returns the run's artefacts and result rows")
        code, body = get("/api/verify")
        v = json.loads(body)
        check(code == 200 and "runs" in v and all({"run_id", "tier", "counts"} <= set(r) for r in v["runs"]), "/api/verify lists the verification runs with counts (%d)" % len(v["runs"]))
        if v["runs"]:
            code, body = get("/api/verify/run?run_id=" + v["runs"][-1]["run_id"])
            vr = json.loads(body)
            check(code == 200 and all({"check_id", "status", "layer"} <= set(r) for r in vr["rows"][:50]), "/api/verify/run returns the unified rows of one run")
        code, body = get("/api/docs")
        check(code == 200 and "端到端.md" in json.loads(body), "/api/docs serves the design documents")
        code, body = get("/api/case?path=../../etc/passwd")
        check(code == 500 and "outside the project" in body.decode("utf-8"), "a path outside the project is refused")
        tmp = ROOT / "out" / "pipeline" / "_check_ui" / "run"
        tmp.mkdir(parents=True, exist_ok=True)
        (tmp / "todo.json").write_text("[]", encoding="utf-8")
        code, r = post("/api/review", {"dir": "out/pipeline/_check_ui/run", "data": {"flows.up1.receipt_kind": {"value": "REMITTED", "source": "s", "quote": ""}, "roles.ULT.attrs.x": "unknown"}, "notes": ["n"]})
        saved = json.loads((tmp / "review.json").read_text(encoding="utf-8"))
        check(code == 200 and saved["data"]["flows.up1.receipt_kind"]["value"] == "REMITTED" and saved["data"]["roles.ULT.attrs.x"] == "unknown" and saved["notes"] == ["n"],
              "POST /api/review writes review.json in the pipeline's shape (value with source, unknown, notes)")
        ans = ROOT / "out" / "pipeline" / "_check_ui" / "x.answers.json"
        code, r = post("/api/answers", {"path": "out/pipeline/_check_ui/x.answers.json", "answers": {"data": {"ULT.bo_safe_harbour": {"value": False, "source": "s"}}, "actions": {"a": "yes"}}})
        a = json.loads(ans.read_text(encoding="utf-8"))
        check(code == 200 and a["data"]["ULT.bo_safe_harbour"]["value"] is False and a["actions"]["a"] == "yes" and "rulings" in a, "POST /api/answers merges into the planner's answers file (data / actions / rulings / library)")
        code, r = post("/api/case/save", {"path": "out/pipeline/_check_ui/bad.json", "case": {"template": "holding", "roles": {}}})
        check(code == 400 and "error" in r and not (ROOT / "out" / "pipeline" / "_check_ui" / "bad.json").exists(), "POST /api/case/save refuses a case the loader rejects and writes nothing")
        code, r = post("/api/case/save", {"path": "out/pipeline/_check_ui/good.json", "case": d["case"]})
        check(code == 200 and (ROOT / "out" / "pipeline" / "_check_ui" / "good.json").exists() and r["template"] == "holding", "POST /api/case/save writes a case the loader and the core validation accept")
        code, body = get("/api/schema")
        schema = json.loads(body)
        check(code == 200 and schema["fields"]["receipt_kind"]["kind"] == "enum" and "REMITTED" in schema["fields"]["receipt_kind"]["options"] and "NONE" in schema["fields"]["receipt_kind"]["options"], "receipt answers expose exact qualifying and non-receipt codes")
        before = ans.read_bytes()
        code, r = post("/api/answers", {"path": str(ans), "answers": {"data": {"flow:up1.receipt_kind": {"value": "remitted", "source": "bank record"}}}})
        check(code == 400 and ans.read_bytes() == before, "invalid enum text is rejected without changing stored answers")
        code, r = post("/api/answers", {"path": str(ans), "answers": {"data": {"ULT.residence_cert": {"value": "yes", "source": "certificate"}}}})
        check(code == 400 and ans.read_bytes() == before, "boolean strings cannot silently become tax facts")
        from .ui.forms import build_case, validate_answers
        from .ui.server import workspace, _signature
        from .pipeline import find_docs
        sample = {"case_id": "UI isolated case", "template": "holding", "currency": "SGD", "on": "2026-10-15", "as_at": "2026-10-15", "years": 1,
                  "amounts": {"dividend": 5000}, "roles": {"OP": {"name": "New subsidiary", "loc": "CN"}, "ULT": {"name": "New parent", "loc": "SG"}},
                  "holdings": {"OP": {"ratio": 100}}, "source": "Client board resolution"}
        blank = build_case(sample)
        check(blank["settled"] == {} and blank["flows"] == {} and all(v["attrs"] == {} for v in blank["roles"].values()) and blank["event"]["dividend"] == 5000,
              "new cases contain only supplied facts, without copied tax attributes or paid amounts")
        try:
            validate_answers({}, [{"kind": "data", "key": "flow:up1.receipt_kind"}])
            complete = False
        except ValueError:
            complete = True
        check(complete, "a missing answer requires an explicit Unknown rather than silent omission")
        from .ui.forms import field_schema
        check(field_schema("flow:reorg.amount")["kind"] == "number" and field_schema("ULT.p2_eur_rate_2027")["kind"] == "number",
              "step considerations and year-specific facts retain numeric input types")
        check(field_schema("group.group_revenue_eur")["unit"] == "EUR", "EUR-denominated collection fields never inherit the transaction currency label")
        test_case = ROOT / "out" / "pipeline" / "_check_ui" / "ui-state.json"
        post("/api/case/save", {"path": str(test_case), "case": blank})
        from .run import load_case
        currency_template, currency_case, currency_event, _, _, _ = load_case(test_case)
        check(all(f.currency == "SGD" for f in currency_template.build(currency_event, currency_case.present, currency_case).flows),
              "planning scenario flows retain the currency entered in the form")
        from .verify.casecheck import check as check_case
        _, errors, _, _ = check_case(test_case, [])
        check(not errors, "a newly created case passes the provenance gate, including its current structure")
        missing_source = json.loads(json.dumps(blank))
        missing_source["provenance"]["event.dividend"]["source"] = ""
        bad_source = test_case.with_name("bad-source.json")
        bad_source.write_text(json.dumps(missing_source), encoding="utf-8")
        _, errors, _, _ = check_case(bad_source, [])
        check(any("no source" in e for e in errors), "a reviewed fact without a source is still rejected by the provenance gate")
        run = ROOT / "out" / "pipeline" / test_case.stem / "check"
        run.mkdir(parents=True, exist_ok=True)
        (run / "manifest.json").write_text(json.dumps({"case": str(test_case), "stages": {"plan": {"status": "pass"}}}), encoding="utf-8")
        saved_plan = {"guaranteed": 50, "best": 20,
                      "structure": {"entities": [("ULT", "SG", "existing"), ("OP", "CN", "existing")],
                                    "flows": [("up1", "DIVIDEND", "OP", "ULT", 5000, "2026-10-15")]}, "regions": []}
        (run / "questions.json").write_text(json.dumps({"plan": saved_plan, "questions": []}), encoding="utf-8")
        (run / "report.md").write_text("# Saved analysis\nTax: 50\n", encoding="utf-8")
        (run / "ui-input.json").write_text(json.dumps({"signature": _signature(test_case)}), encoding="utf-8")
        check(workspace(str(test_case))["status"] == "plan", "an unchanged input retains its completed result")
        current = workspace(str(test_case))
        check(current["plan"]["execution"]["steps"] and current["plan"]["guaranteed"] == 50,
              "older completed plans gain execution steps without changing the saved tax")
        code, report = get("/api/report?path=" + urllib.parse.quote(str(test_case)))
        check(code == 200 and b"## Implementation plan" in report and b"Owner:" in report and b"Tax: 50" in report,
              "older report downloads include the same implementation workpack and original analysis")
        changed = dict(blank, currency="CNY")
        post("/api/case/save", {"path": str(test_case), "case": changed})
        state = workspace(str(test_case))
        check(state["status"] == "stale" and state["plan"] is None, "changing saved input invalidates the old result and removes its actionable plan")
        # A resumed question sheet must read the very answers file it just saved, including a custom path.
        from unittest.mock import patch
        from .ui.server import proceed
        custom = ROOT / "out" / "pipeline" / "_check_ui" / "custom.answers.json"
        (run / "ui-input.json").unlink()
        (run / "questions.json").write_text(json.dumps({"answers_file": str(custom), "questions": [{"key": "flow:up1.receipt_kind", "kind": "data"}], "plan": None}), encoding="utf-8")
        with patch("tax_graph.ui.server.start_pipeline", return_value={"started": True}) as launch:
            proceed(str(test_case), {"answers": {"data": {"flow:up1.receipt_kind": {"value": "NONE", "source": "bank confirmation"}}}})
            check(launch.call_args[0][1]["answers"] == str(custom) and launch.call_args[0][1]["from"] == "plan" and custom.exists(),
                  "resuming the planner preserves the custom answer file that was saved")
        import base64
        code, r = post("/api/materials", {"path": str(test_case), "name": "board-resolution.txt", "content": base64.b64encode(b"Board resolution: a dividend of SGD 5000 is approved.").decode()})
        attached = json.loads(test_case.read_text(encoding="utf-8"))
        check(code == 200 and any("SGD 5000" in t for t in find_docs(attached, None).values()), "uploaded text reaches the same document loader used by extraction")
        material_path = ROOT / r["saved"]
        quote_case = json.loads(json.dumps(attached))
        quote_case["currency"] = "SGD"
        quote_case["provenance"]["event.dividend"] = {"kind": "disclosed", "source": material_path.stem, "quote": "a dividend of SGD 5000 is approved"}
        quote_path = test_case.with_name("quote-case.json")
        quote_path.write_text(json.dumps(quote_case), encoding="utf-8")
        _, errors, _, _ = check_case(quote_path, [])
        check(not errors, "quotes from uploaded documents are checked against the attached text")
        quote_case["provenance"]["event.dividend"]["quote"] = "a dividend of SGD 9000 is approved"
        quote_path.write_text(json.dumps(quote_case), encoding="utf-8")
        _, errors, _, _ = check_case(quote_path, [])
        check(any("not found" in e for e in errors), "a quote that is absent from the uploaded source is rejected")
        shutil.rmtree(str(material_path.parent))
        code, body = get("/api/evidence?rule=cn.eit.nonresident")
        ev = json.loads(body)
        # A stable provision identifier also works when the caller has a citation rather than a compiled rule id.
        code, body = get("/api/evidence?rule=treaty.cn-hk.2006.zh%2310.2")
        ev = json.loads(body)
        check(code == 200 and ev["sources"] and ev["sources"][0]["text"] and ev["sources"][0]["url"].startswith("https://"), "legal evidence includes the original clause and official publication link")
        code, body = get("/api/evidence?rule=cn.stamp.seller")
        ev = json.loads(body)
        check(code == 200 and ev["sources"], "compiled rule parameters resolve to their original legal clauses")
        from .ui import server
        from types import SimpleNamespace
        with patch("tax_graph.ui.server.subprocess.Popen", return_value=SimpleNamespace(poll=lambda: None)):
            launched = server.start_pipeline(str(test_case), {"run_id": "launch", "answers": str(custom)})
            check(server.workspace(str(test_case))["status"] == "running", "a launched analysis appears immediately before its manifest exists")
            try:
                server.start_pipeline(str(test_case), {"run_id": "duplicate"})
                duplicate = False
            except ValueError:
                duplicate = True
            check(duplicate, "a duplicate analysis cannot start while the same case is running")
            del server.JOBS[launched["dir"]]
        from .ui.intake import build_recorded_case, collection_preview
        recorded_body = {"case_id": "Recorded test", "currency": "CNY", "as_at": "2026-10-15", "source": "Fictional test record",
            "companies": [{"id": "COMPANY_A", "name": "SG lender", "loc": "SG", "member": True},
                          {"id": "COMPANY_B", "name": "HK borrower", "loc": "HK", "member": False},
                          {"id": "COMPANY_C", "name": "HK parent", "loc": "HK", "member": True}],
            "ownership": [{"holder": "COMPANY_C", "held": "COMPANY_A", "ratio": 100}],
            "transactions": [{"id": "fee_one", "income": "INTEREST", "payer": "COMPANY_B", "payee": "COMPANY_A", "amount": 1000000, "on": "2026-10-15", "paid": {"SG": 10000}},
                             {"id": "dividend_two", "income": "DIVIDEND", "payer": "COMPANY_A", "payee": "COMPANY_C", "amount": 200000, "on": "2026-12-15"}]}
        recorded = build_recorded_case(recorded_body)
        recorded_path = test_case.with_name("recorded.json")
        post("/api/case/save", {"path": str(recorded_path), "case": recorded})
        from .run import load_case
        t, ca, ev, _, _, _ = load_case(recorded_path)
        graph = t.build(ev, {}, ca)
        check(len(graph.flows) == 2 and graph.flows[1].on.isoformat() == "2026-12-15" and graph.members == {"COMPANY_A", "COMPANY_C"}, "recorded intake preserves multiple companies, payment dates and assessment membership")
        _, errors, _, _ = check_case(recorded_path, [])
        check(not errors and recorded["settled"]["fee_one"]["SG"] == 10000, "recorded transactions and paid tax pass provenance validation")
        out_body = json.loads(json.dumps(recorded_body))                          # interest paid from the Mainland attracts VAT
        out_body["companies"][1].update(loc="CN", name="CN borrower")
        out_path = test_case.with_name("out-of-scope.json")
        code, r = post("/api/case/save", {"path": str(out_path), "case": build_recorded_case(out_body)})
        check(code == 400 and "income tax only" in r.get("error", "") and "VAT" in r.get("error", "") and not out_path.exists(),
              "a recorded case that attracts VAT is refused at save with the scope message and nothing is written (decision D52)")
        preview_out = collection_preview(out_body)
        check(preview_out["outside"] and preview_out["outside"][0]["levy"] == "VAT" and not collection_preview(recorded_body)["outside"],
              "the structure preview names the levy that puts a transaction outside the scope, and nothing for an admitted one")
        preview = collection_preview(recorded_body)
        check(preview["collection"] and preview["summary"]["transactions"] == 2, "collection requirements derive from the actual transaction graph")
        cyclic = json.loads(json.dumps(recorded_body))
        cyclic["ownership"].append({"holder": "COMPANY_A", "held": "COMPANY_C", "ratio": 100})
        try:
            build_recorded_case(cyclic)
            rejected = False
        except ValueError:
            rejected = True
        check(rejected, "circular ownership is rejected before graph evaluation")
        from .pipeline import apply_review
        filled = dict(recorded, flows={"fee_one": {"receipt_kind": "REMITTED"}})
        reviewed, _ = apply_review(filled, {"data": {"flows.fee_one.receipt_kind": "unknown"}})
        check("receipt_kind" not in reviewed["flows"]["fee_one"], "rejecting a finding removes the previously filled fact from the calculation")
        (tmp / "extracted.json").write_text(json.dumps({"facts": {"flows.fee_one.receipt_kind": "REMITTED"}, "provenance": {"flows.fee_one.receipt_kind": {"kind": "disclosed", "source": "bank", "quote": "Remitted in"}}}), encoding="utf-8")
        code, result = post("/api/review", {"dir": str(tmp), "decisions": {"flows.fee_one.receipt_kind": "accept"}})
        accepted = json.loads((tmp / "review.json").read_text(encoding="utf-8"))
        reviewed, _ = apply_review(filled, accepted)
        check(code == 200 and reviewed["provenance"]["flows.fee_one.receipt_kind"]["quote"] == "Remitted in", "accepting a finding preserves its original evidence")
        code, result = post("/api/review", {"dir": str(tmp), "data": {"flows.fee_one.receipt_kind": {"value": "NONE", "source": "corrected bank record", "quote": "", "note": "Wrong account"}}, "decisions": {"flows.fee_one.receipt_kind": "correct"}})
        corrected = json.loads((tmp / "review.json").read_text(encoding="utf-8"))
        reviewed, _ = apply_review(filled, corrected)
        check(code == 200 and reviewed["flows"]["fee_one"]["receipt_kind"] == "NONE" and corrected["data"]["flows.fee_one.receipt_kind"]["note"] == "Wrong account", "a correction reaches the reviewed case and keeps its reason")
        code, result = post("/api/review", {"dir": str(tmp), "data": {"roles.COMPANY_A.loc": "unknown"}})
        check(code == 400, "review cannot silently remove a core company jurisdiction")
        code, result = post("/api/review", {"dir": str(tmp), "data": {"flows.fee_one.receipt_kind": {"value": "unknown", "note": "Unsupported by source"}}, "decisions": {"flows.fee_one.receipt_kind": "unknown"}})
        rejected_review = json.loads((tmp / "review.json").read_text(encoding="utf-8"))
        check(code == 200 and rejected_review["data"]["flows.fee_one.receipt_kind"]["note"] == "Unsupported by source", "a rejected finding keeps the reason for later review")
    finally:
        srv.shutdown()
        shutil.rmtree(str(ROOT / "out" / "pipeline" / "_check_ui"), ignore_errors=True)
        shutil.rmtree(str(ROOT / "out" / "pipeline" / "ui-state"), ignore_errors=True)
    out.write("%d checks, %d failures\n" % (len(results), results.count(False)))
    out.flush()
    return 1 if False in results else 0


if __name__ == "__main__":
    sys.exit(main())
