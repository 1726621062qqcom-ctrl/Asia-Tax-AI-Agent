"""The new expense corpus must stay separate from FSIE and fail closed."""
import hashlib
from pathlib import Path

from packages.chat import expenses
from packages.knowledge_pipeline.segment import segment_cap112


def test_expense_route_keeps_other_region_and_dividend_out():
    assert expenses.should_handle({}, "香港公司办公租金能扣除吗？")
    assert not expenses.should_handle({}, "中国内地公司的办公租金能扣除吗？")
    assert not expenses.should_handle({}, "香港境外股息 FSIE 如何处理？")
    assert expenses.should_handle({"expense_context": {"pending": True}}, "有发票")


def test_statute_locator_uses_printed_provision_number():
    snapshot = next((Path(__file__).resolve().parents[2] /
                     "knowledge/hong_kong/fsie/raw/hk_hkel_iro_cap112").glob("*.xml"), None)
    if snapshot is None:
        # CI does not carry the immutable official snapshot.
        return
    units = segment_cap112(snapshot.read_bytes(), ["16", "17"])
    refs = [unit.unit_ref for unit in units]
    assert len(refs) == len(set(refs))
    assert "cap112:s16(2CD)" in refs
    assert "cap112:s16(1)" in refs and "cap112:s17(1)" in refs


def test_search_filters_sources_and_hashes(monkeypatch):
    class Row:
        source_id = "hk_ird_profits_tax_deductions"
        url = "https://www.ird.gov.hk/eng/tax/bus_pft.htm"
        actual_sha256 = "a" * 64
        manifest_sha256 = "a" * 64
        retrieved_at = None
        unit_ref = "expense:block001"
        statute_locator = None
        heading = "Rent"
        text = "Rent incurred to produce chargeable profits."
        text_sha256 = hashlib.sha256(text.encode()).hexdigest()
        ordinal = 1

    class Result:
        def all(self):
            return [Row()]

    class Connection:
        def __enter__(self): return self
        def __exit__(self, *args): return False
        def execute(self, statement): return Result()

    class Engine:
        def connect(self): return Connection()

    monkeypatch.setattr(expenses, "knowledge_engine", lambda: Engine())
    monkeypatch.setattr(expenses, "manifest", lambda: {
        "legal_coverage_cutoff": "2026-10-13",
        "sources": [{"source_id": Row.source_id, "url": Row.url,
                     "title": "IRD", "content_sha256": "a" * 64}],
    })
    assert len(expenses.search("rent")["passages"]) == 1
    Row.actual_sha256 = "b" * 64
    assert expenses.search("rent")["status"] == "no_matching_units"
