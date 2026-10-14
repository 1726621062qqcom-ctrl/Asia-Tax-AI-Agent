"""Run three synthetic FSIE consultations through chat and fact-editor service paths.

Uses the configured model and cloud knowledge, but a temporary SQLite case store.
Raw results go to ignored reports/; no credentials or private user cases are read.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import re
import tempfile
import time
from pathlib import Path
from uuid import uuid4

from packages.chat.service import ChatService, WorkflowError, current_model_config
from packages.chat.store import ChatStore
from packages.chat.streaming import events


ROOT = Path(__file__).resolve().parents[1]
CASES = ROOT / "docs/product/HK_FSIE_USER_CASE_TEMPLATES.md"

FORM_FACTS = [
    {
        "recipient_type": "company", "analysis_jurisdiction": "HK",
        "consultation_goal": "full_analysis", "income_event_status": "occurred",
        "entity_hk_business_status": "yes", "mne_group_status": "yes",
        "group_structure_description": "Hong Kong group company directly owns 35% of a Singapore subsidiary.",
        "payer_entity": "Singapore subsidiary", "payer_jurisdiction": "SG",
        "income_type": "dividend", "dividend_amount": 1800000,
        "dividend_currency": "SGD", "dividend_form": "cash",
        "bank_or_account_path": "Singapore subsidiary paid into the Hong Kong company's Hong Kong bank account in August 2025; exact day unverified.",
        "direct_or_indirect_holding": "direct", "holding_percentage_pct": 35,
        "entity_activity_profile": "Regional procurement, contract management and group financial coordination in Hong Kong.",
        "hk_staff_description": "Three full-time Hong Kong employees; their duties require verification.",
        "hk_premises_description": "Leased office in Hong Kong.",
        "foreign_tax_description": "Finance colleague says related profits were dealt with for tax in Singapore; no complete tax proof yet.",
        "evidence_inventory": ["Dividend resolution", "shareholding records", "Hong Kong bank credit record", "Singapore financial statements", "foreign tax proof missing"],
    },
    {
        "recipient_type": "company", "analysis_jurisdiction": "HK",
        "consultation_goal": "full_analysis", "income_event_status": "occurred",
        "mne_group_status": "yes",
        "group_structure_description": "Group Hong Kong investment holding company holds 8% of a Mainland China project company; direct/indirect route unverified.",
        "payer_entity": "Mainland China project company", "payer_jurisdiction": "CN",
        "income_type": "dividend", "dividend_amount": 5000000,
        "dividend_currency": "CNY", "dividend_form": "cash",
        "bank_or_account_path": "Mainland project company paid into Hong Kong company bank account in Hong Kong in February 2026; exact day unverified.",
        "holding_percentage_pct": 8,
        "hk_staff_description": "No dedicated investment team; staff of other group companies assist. Hong Kong directors participated in decisions.",
        "hk_premises_description": "No separately leased office; arrangements for premises are unverified.",
        "entity_activity_profile": "Hong Kong directors participated in investment approval and subsequent decisions; some group employees assisted.",
        "foreign_tax_description": "A Mainland tax document exists but tax type, taxpayer and relationship to dividend/underlying profits are unverified.",
        "evidence_inventory": ["Investment agreement", "dividend notice", "bank statements", "Mainland tax document unreviewed", "some meeting records available"],
    },
    {
        "recipient_type": "company", "analysis_jurisdiction": "HK",
        "consultation_goal": "full_analysis", "income_event_status": "planned",
        "group_structure_description": "Hong Kong company owns 100% of Singapore holding company; Singapore company owns 22% of Japanese operating company. Japan-to-Singapore and possible Singapore-to-Hong-Kong dividends are separate transactions; some holdings changed in 2026.",
        "payer_entity": "Singapore holding company (proposed direct payer to Hong Kong company)",
        "payer_jurisdiction": "SG", "income_type": "dividend",
        "direct_or_indirect_holding": "direct", "holding_percentage_pct": 100,
        "entity_activity_profile": "Hong Kong company has employees and office; Japanese team operates Japanese project day to day. Detailed duties unverified.",
        "hk_staff_description": "Hong Kong employees exist; number and duties unverified.",
        "hk_premises_description": "Hong Kong office exists; usage unverified.",
        "commercial_rationale": "Group changed some holdings in 2026; commercial rationale memo can be supplied but is not final.",
        "evidence_inventory": ["Before-and-after group charts not final", "acquisition documents not final", "commercial rationale memo not final", "dividend resolutions not yet made"],
    },
]


def prompts() -> list[str]:
    text = CASES.read_text(encoding="utf-8")
    sections = re.split(r"(?=^### 案例[一二三]：)", text, flags=re.M)
    result = []
    for section in sections[1:4]:
        block = section.split("**预期检验点：**", 1)[0]
        lines = [line[2:].strip() for line in block.splitlines() if line.startswith("> ")]
        result.append("\n\n".join(lines))
    if len(result) != 3 or any(not x for x in result):
        raise ValueError("Expected three nonempty Chinese consultation prompts")
    return result


async def chat_trial(service: ChatService, owner: str, prompt: str) -> dict:
    doc = service.store.create(owner)
    started = time.perf_counter()
    events_seen: list[str] = []
    result = None

    async def connected() -> bool:
        return False

    try:
        async with asyncio.timeout(110):
            async for event in events(service, doc, owner, doc["revision"], str(uuid4()), prompt, connected,
                                      entry_hint="dividend_consultation", data_approved=True, locale="zh"):
                events_seen.append(event["type"])
                if event["type"] == "done":
                    result = event["case"]
                if event["type"] == "error":
                    raise RuntimeError(event.get("code", "stream_error"))
        if result is None:
            raise RuntimeError("no_final_case")
        assistants = [m for m in result["messages"] if m["role"] == "assistant"]
        return {
            "status": "completed", "seconds": round(time.perf_counter() - started, 2),
            "state": result["state"], "facts": result["facts"],
            "questions": result.get("questions"), "fact_gaps": result.get("fact_gaps"),
            "assistant_messages": assistants, "event_types": sorted(set(events_seen)),
        }
    except Exception as exc:
        return {"status": "failed", "seconds": round(time.perf_counter() - started, 2),
                "error": getattr(exc, "code", type(exc).__name__), "event_types": sorted(set(events_seen))}


def form_trial(service: ChatService, owner: str, facts: dict) -> dict:
    doc = service.store.create(owner)
    started = time.perf_counter()
    record: dict = {"entered_facts": facts, "path": []}
    try:
        edited = service.edit(owner, doc["id"], doc["revision"], str(uuid4()), facts)
        record["path"].append("edit")
        record["saved_facts"] = edited["facts"]
        confirmed = service.confirm(owner, doc["id"], edited["revision"], str(uuid4()))
        record["path"].append("confirm")
        record["confirmed_facts"] = confirmed["confirmed_facts"]
        try:
            final = service.run(owner, doc["id"], confirmed["revision"], str(uuid4()))
            record["path"].append("analyze")
        except WorkflowError as exc:
            record["first_analysis_blocker"] = exc.code
            if exc.code != "partial_confirmation_required":
                raise
            # This is the user's explicit request to view a partial research draft.
            partial = service.message(owner, doc["id"], confirmed["revision"], str(uuid4()),
                                      "先看部分整理", True, "fact_intake", None, "zh")
            record["path"].append("explicit_partial_request")
            record["partial_response"] = [m for m in partial["messages"] if m["role"] == "assistant"][-1:]
            if partial["state"] != "confirmed":
                partial = service.confirm(owner, doc["id"], partial["revision"], str(uuid4()))
                record["path"].append("reconfirm")
            final = service.run(owner, doc["id"], partial["revision"], str(uuid4()))
            record["path"].append("analyze")
        analysis = final["analyses"][-1]
        record.update(status="completed", state=final["state"],
                      analysis={k: v for k, v in analysis.items() if k not in ("passages",)},
                      passages=[{k: p.get(k) for k in ("unit_id", "source_id", "title", "locator", "url")}
                                for p in analysis.get("passages", [])])
    except Exception as exc:
        record.update(status="failed", error=getattr(exc, "code", type(exc).__name__))
    record["seconds"] = round(time.perf_counter() - started, 2)
    return record


async def main(output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    report = {"method": "Three real-model synthetic chat consultations and three fact-edit/confirm/analyze trials; temporary SQLite cases, configured cloud knowledge; no browser/auth or expert tax sign-off.",
              "model": current_model_config().model_name, "cases": []}
    owner = "evaluation:" + str(uuid4())
    with tempfile.TemporaryDirectory(prefix="taxora-fsie-user-") as directory:
        store = ChatStore("sqlite:///" + Path(directory, "sessions.sqlite").as_posix())
        service = ChatService(store)
        try:
            for index, (prompt, facts) in enumerate(zip(prompts(), FORM_FACTS), 1):
                row = {"case": index, "prompt": prompt}
                report["cases"].append(row)
                row["chat"] = await chat_trial(service, owner, prompt)
                output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
                print(f"case {index} chat: {row['chat']['status']}", flush=True)
                row["form"] = await asyncio.to_thread(form_trial, service, owner, facts)
                output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
                print(f"case {index} form: {row['form']['status']}", flush=True)
        finally:
            store.engine.dispose()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "reports/fsie-user-six-experiments.json")
    arguments = parser.parse_args()
    asyncio.run(main(arguments.output))
