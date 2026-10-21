"""Database-source contracts using actual SQL selection and the HTTP boundary."""
import sqlite3
from types import SimpleNamespace
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text

from packages.agent.contracts import SearchRequest, TrustedContext
from packages.agent.providers import RoutedKnowledgeProvider
from packages.agent.source_policy import public_hk_official
from packages.agent.tools import ToolDecision


def test_combined_provider_routes_guidance_and_preserves_reference_reader():
    class Backend:
        def __init__(self, name):
            self.name = name
        def search_evidence(self, request, context):
            return self.name
        def get_evidence(self, reference, purpose, context):
            return self.name
    from packages.agent.contracts import Reference
    provider = RoutedKnowledgeProvider(Backend('sqlite'), Backend('pg-rulings'), Backend('pg-guidance'))
    context = TrustedContext(owner='test')
    for kind, expected in [('law', 'sqlite'), ('guidance', 'pg-guidance'), ('ruling', 'pg-rulings')]:
        assert provider.search_evidence(SearchRequest(request_id='r', trace_id='t', query='HK FSIE', kind=kind), context) == expected
    for unit, expected in [('law|hk.cap112.en#s15M|0|50', 'sqlite'),
                           ('li|hk.cap112.en#s15M|0|50', 'sqlite'),
                           ('hk_ird_advance_68:section1', 'pg-rulings'), ('hk_ird_fsie_faq:item1', 'pg-guidance')]:
        ref = Reference(evidence_id=unit, unit_id=unit, source_version_id='v1')
        assert provider.get_evidence(ref, 'display', context) == expected


def test_postgres_adapter_classifies_faq_by_source_even_with_generic_unit_type(monkeypatch):
    from packages.chat import knowledge
    engine = create_engine('sqlite://')
    with engine.begin() as db:
        db.execute(text('CREATE TABLE sources (id INTEGER PRIMARY KEY, source_id TEXT, l0_in_scope BOOLEAN, parse_status TEXT, actual_sha256 TEXT, manifest_sha256 TEXT, retrieved_at DATETIME, source_type TEXT, jurisdiction TEXT, effective_from DATE, effective_to DATE)'))
        db.execute(text('CREATE TABLE legal_units (source_db_id INTEGER, unit_ref TEXT, statute_locator TEXT, heading TEXT, text TEXT, text_sha256 TEXT, unit_type TEXT, ordinal INTEGER)'))
        for n, sid, kind in [(1, 'law', 'structured_legislation_xml'), (2, 'faq', 'official_faq'), (3, 'ruling', 'official_advance_ruling')]:
            db.execute(text("INSERT INTO sources(id,source_id,l0_in_scope,parse_status,source_type,jurisdiction) VALUES (:n,:sid,1,'parsed',:kind,'HK')"), {'n': n, 'sid': sid, 'kind': kind})
            db.execute(text("INSERT INTO legal_units VALUES (:n,:sid,NULL,'Participation','participation exemption holding','hash',:ut,1)"),
                       {'n': n, 'sid': sid, 'ut': 'ruling_block' if n == 3 else 'guidance_block'})
    monkeypatch.setattr(knowledge, 'knowledge_engine', lambda: engine)
    monkeypatch.setattr(knowledge, 'catalog', lambda: {'allowed_source_domains': ['www.ird.gov.hk'], 'legal_coverage_cutoff': '2026-08-15', 'sources': [
        {'source_id': sid, 'source_type': kind, 'title': sid, 'url': 'https://www.ird.gov.hk/'}
        for sid, kind in [('law', 'structured_legislation_xml'), ('faq', 'official_faq'), ('ruling', 'official_advance_ruling')]]})
    try:
        rows = knowledge.read_documents(query='participation exemption', kind='guidance')
        assert [row['source_id'] for row in rows] == ['faq']
        assert rows[0]['source_type'] == 'official_faq'
        assert rows[0]['effective_from'] is None  # No inferred effective date.
    finally:
        engine.dispose()


def test_sqlite_http_guidance_excludes_statutes_before_limit(monkeypatch):
    from apps.knowledge_api import main
    db = sqlite3.connect(':memory:', check_same_thread=False)
    db.row_factory = sqlite3.Row
    db.executescript('CREATE TABLE doc(id TEXT,url TEXT,type TEXT); CREATE TABLE clause(cite_id TEXT,text TEXT);')
    rows = [('hk.cap112.en', 'https://www.elegislation.gov.hk/hk/cap112!en', 'law', 'law text'),
            ('faq-alias', 'https://www.ird.gov.hk/eng/faq/fsie.htm', 'guidance', 'official guidance text')]
    hits, meta = [], {}
    for expr, url, kind, body in rows:
        cite = expr + '#item1'
        db.execute('INSERT INTO doc VALUES (?,?,?)', (expr, url, kind))
        db.execute('INSERT INTO clause VALUES (?,?)', (cite, body))
        meta[cite] = {'expr_id': expr, 'jur': 'hk'}
        hits.append(SimpleNamespace(cite_id=cite, span=(0, len(body)), snippet=body,
                    valid_from=None, valid_to=None, title=expr, lang='en'))
    monkeypatch.setattr(main, '_library', lambda: SimpleNamespace(con=db, meta=meta, search=lambda *a, **k: hits))
    monkeypatch.setenv('FSIE_AGENT_C_TOKEN', '')
    try:
        with TestClient(main.app) as client:
            req = SearchRequest(request_id=str(uuid4()), trace_id=str(uuid4()), query='FSIE guidance', kind='guidance', limit=1)
            response = client.post('/search', json={'request': req.model_dump(mode='json'), 'trusted_context': {'owner': 'test'}})
            assert response.status_code == 200
            evidence = response.json()['evidence']
            assert len(evidence) == 1 and evidence[0]['source_type'] == 'guidance'
            assert evidence[0]['source_id'] == 'hk_ird_fsie_faq'
            assert evidence[0]['topic'] == 'dividend' and evidence[0]['model_use'] == 'allowed'
    finally:
        db.close()


def test_official_guidance_permission_is_exact_and_old_tool_name_is_compatible():
    assert public_hk_official('hk_ird_fsie_faq', 'https://www.ird.gov.hk/eng/faq/fsie.htm')
    assert not public_hk_official('hk_ird_fsie_faq', 'https://www.ird.gov.hk/other')
    assert not public_hk_official('hk_ird_fsie_faq', 'https://evil.invalid/eng/faq/fsie.htm')
    assert ToolDecision(tool='search_cases', query='HK dividends').tool == 'search_rulings'


def test_final_source_window_retains_each_independent_search():
    from packages.agent.knowledge import merge_bundles
    bundles = []
    for kind in ('law', 'guidance', 'ruling'):
        bundles.append({'query': kind, 'passages': [], 'gaps': [], 'verified_evidence_ids': [],
            'reason_code': 'evidence_available', 'is_synthetic': False,
            'model_evidence': [{'evidence_id': f'{kind}-{n}', 'source_version_id': 'v1', 'content_hash': f'hash-{kind}-{n}'} for n in range(7)]})
    merged = merge_bundles(bundles, 'FSIE sources')
    assert {e['evidence_id'].split('-')[0] for e in merged['model_evidence'][:7]} == {'law', 'guidance', 'ruling'}


def test_source_completion_guard_respects_explicit_exclusions():
    from packages.agent.research_context import required_search_kinds
    assert required_search_kinds("Use legislation and IRD guidance; don't search rulings.") == ['law', 'guidance']
    assert required_search_kinds('不需要裁定，只查官方指引。') == ['guidance']
    assert required_search_kinds('Do not search rulings.') == []


def test_original_case_navigation_keeps_primary_sections_and_requested_source_types():
    from packages.agent.research_context import law_navigation, required_search_kinds
    from pathlib import Path
    import re
    text = Path('docs/product/HK_FSIE_USER_CASE_TEMPLATES.md').read_text()
    # Use the same three blockquote prompts as the webpage evaluation.
    full = []
    for block in re.split(r'(?m)^### Case \d+:', text)[1:]:
        full.append('\n'.join(line[2:] for line in block.splitlines() if line.startswith('> ')))
    assert len(full) == 3
    for case in full:
        refs = law_navigation(case)
        assert {'s.15H(5)', 's.15K(2)', 's.15M(2)', 's.15N(2)'} <= set(refs)
        assert required_search_kinds(case) == ['law', 'guidance']


def test_faq_chunks_do_not_displace_primary_sections_from_final_source_window():
    from packages.agent.knowledge import merge_bundles
    def bundle(kind, refs):
        return {'query': kind, 'passages': [], 'gaps': [], 'verified_evidence_ids': [],
            'reason_code': 'evidence_available', 'is_synthetic': False, 'model_evidence': [
                {'evidence_id': f'{kind}-{n}', 'source_version_id': 'v1', 'content_hash': str(n), 'locator': ref}
                for n, ref in enumerate(refs)]}
    primary = ['s.15H', 's.15I', 's.15K', 's.15M', 's.15N']
    merged = merge_bundles([bundle('law', primary), bundle('guidance', [None] * 7)], 'FSIE')
    window = merged['model_evidence'][:7]
    assert set(primary) <= {e['locator'] for e in window}
    assert any(e['evidence_id'].startswith('guidance') for e in window)


def test_postgres_adapter_deadline_covers_stalled_read_and_does_not_admit_late_results():
    from packages.agent.providers import LegacyKnowledgeProvider
    from threading import Event
    from time import monotonic
    release, entered, finished = Event(), Event(), Event()
    def blocked(_query):
        entered.set()
        release.wait(3)
        finished.set()
        return {'status': 'available', 'passages': []}
    provider = LegacyKnowledgeProvider(searcher=blocked)
    start = monotonic()
    try:
        result = provider.search_evidence(SearchRequest(request_id='r', trace_id='t', query='HK FSIE', deadline_ms=100), TrustedContext(owner='test'))
        assert entered.is_set() and not finished.is_set()
        assert result.status == 'error' and result.error.code == 'TIMEOUT'
        assert not result.evidence and monotonic() - start < 1
    finally:
        release.set()
        assert finished.wait(1)
