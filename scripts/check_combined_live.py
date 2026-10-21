"""Opt-in live smoke: configured model + isolated PostgreSQL schema + pinned tax engine.

Only synthetic facts are sent to the model. No URLs, keys, prompts or client data
are printed. A temporary schema is dropped in finally; public knowledge is read.
"""
import argparse
from hashlib import sha256
import json
import os
from pathlib import Path
import sys
import traceback
from time import monotonic
from unittest.mock import patch
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main():
    from sqlalchemy import create_engine, text
    from sqlalchemy.engine import make_url
    from packages.persistence.config import Settings, get_settings
    from packages.model_adapter.client import ModelSettings, ModelConfig
    from packages.chat.service import ChatService, WorkflowError
    from packages.chat.store import ChatStore, CaseNotFound
    from packages.domain_bridge.state import draft_from_legacy
    from packages.agent.providers import CKnowledgeProvider, RoutedKnowledgeProvider, LegacyKnowledgeProvider
    from scripts.combined_runtime import knowledge_server
    parser = argparse.ArgumentParser()
    parser.add_argument('--env-file', type=Path, default=ROOT / '.env')
    parser.add_argument('--model-env-file', type=Path, help='Optional separate local model configuration; database still comes from --env-file')
    parser.add_argument('--system-trust', action='store_true', help='Use OS trusted CA store through installed truststore; never disables TLS verification')
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument('--model-only', action='store_true', help='Real model plus isolated SQLite; PostgreSQL remains untested')
    modes.add_argument('--database-only', action='store_true', help='Real PostgreSQL, tax engine and knowledge; no model call')
    parser.add_argument('--output', type=Path, default=ROOT / 'data/combined-live-result.json')
    args = parser.parse_args()
    if args.system_trust:
        import truststore
        truststore.inject_into_ssl()
    settings = Settings(_env_file=args.env_file)
    model = ModelSettings(_env_file=args.model_env_file or args.env_file)
    if (not args.model_only and not settings.database_url) or (not args.database_only and not (model.base_url and model.api_key and model.name)):
        raise SystemExit('Configure PostgreSQL and model settings in the selected .env first.')
    os.environ['FSIE_DATABASE_URL'] = settings.database_url
    get_settings.cache_clear()
    config = ModelConfig(model.base_url.rstrip('/'), model.api_key, model.name, 45, 0)
    started = monotonic(); results = {'synthetic': True, 'model': 'not_called' if args.database_only else model.name,
                                                'mode': 'database_only' if args.database_only else 'model_only' if args.model_only else 'full', 'checks': {}}
    if args.model_only:
        from tempfile import TemporaryDirectory
        from packages.agent.providers import MockKnowledgeProvider
        results['database'] = 'isolated_sqlite_not_postgresql'
        try:
            with TemporaryDirectory(prefix='combined-model-') as directory:
                store = ChatStore('sqlite:///' + str(Path(directory) / 'test.sqlite'))
                try:
                    service = ChatService(store, provider=MockKnowledgeProvider('MOCK-01'))
                    owner = 'user:model-live'; doc = store.create(owner)
                    with patch('packages.chat.service.current_model_config', return_value=config):
                        doc = service.message(owner, doc['id'], 0, str(uuid4()),
                            '这是合成测试：香港公司直接持有中国内地公司100%股权，2020年1月1日取得。'
                            '金额1000000人民币，实际收款日期2026年10月11日。请记录香港境外股息案情，不补猜其他事实。', True)
                        results['checks']['first_model_fields'] = sorted(doc['facts'])
                        doc = service.message(owner, doc['id'], doc['revision'], str(uuid4()),
                            '更正合成案情：股息金额改成2000000人民币，其他事实不变。', True)
                    results['checks']['corrected_amount'] = doc['facts'].get('dividend_amount', {}).get('value')
                    results['checks']['model_rounds'] = 2
                    fixture = json.loads((ROOT / 'tests/integration/fixtures/holding.synthetic.json').read_text(encoding='utf-8'))
                    bindings = {'dividend_amount': 'event.dividend'} if doc['facts'].get('dividend_amount', {}).get('value') == 2000000 else {}
                    fixture['event']['dividend'] = 2000000
                    doc = service.domain_setup(owner, doc['id'], doc['revision'], str(uuid4()), fixture, True, 'assess_current', bindings)
                    doc = service.domain_plan(owner, doc['id'], doc['revision'], str(uuid4()))
                    results['checks']['tax_engine_fixed_status'] = doc['domain_outcome']['status']
                    results['checks']['tax_engine_entities'] = [row[0] for row in doc['domain_outcome']['structure']['entities']]
                    results['checks']['restored'] = store.get(owner, doc['id'])['canonical_fact_records'] == doc['canonical_fact_records']
                    results['status'] = 'passed' if results['checks']['corrected_amount'] == 2000000 and results['checks']['restored'] else 'failed'
                finally:
                    store.engine.dispose()
        except Exception as exc:
            results.update(status='failed', error=exc.code if isinstance(exc, WorkflowError) else type(exc).__name__)
        results['elapsed_seconds'] = round(monotonic() - started, 2)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(results, ensure_ascii=False, indent=2) + '\n')
        print(json.dumps(results, ensure_ascii=False))
        return 0 if results['status'] == 'passed' else 1
    schema = 'combined_test_' + uuid4().hex
    admin = create_engine(settings.database_url, connect_args={'connect_timeout': 5})
    store = None; created = False
    try:
        with admin.begin() as connection:
            results['database_version'] = connection.execute(text('SHOW server_version')).scalar()
            results['database'] = 'postgresql_random_schema'
            results['knowledge_transport'] = 'real_loopback_http'
            connection.execute(text('CREATE SCHEMA ' + schema)); created = True
        url = make_url(settings.database_url).update_query_dict({'options': '-csearch_path=' + schema})
        store = ChatStore(url.render_as_string(hide_password=False))
        owner = 'user:combined-live'; doc = store.create(owner)
        with knowledge_server() as (knowledge_url, knowledge_token):
            law = CKnowledgeProvider(knowledge_url, knowledge_token)
            service = ChatService(store, provider=RoutedKnowledgeProvider(law, LegacyKnowledgeProvider()))
            required = {'dividend_amount': 1000000, 'dividend_currency': 'CNY', 'payer_jurisdiction': 'CN',
                        'analysis_jurisdiction': 'HK', 'holding_percentage_pct': 100,
                        'receipt_date': '2026-10-11', 'acquisition_date': '2020-01-01', 'income_type': 'dividend'}
            if not args.database_only:
                with patch('packages.chat.service.current_model_config', return_value=config):
                    doc = service.message(owner, doc['id'], doc['revision'], str(uuid4()),
                        '这是合成测试：香港公司直接持有中国内地付款公司100%股权，2020年1月1日取得。'
                        '分析香港境外股息，金额1000000人民币，实际收款日期2026年10月11日。请记录案情，不补猜其他事实。', True)
                results['checks']['real_model_intake'] = bool(doc['facts'])
                results['checks']['model_exact_fields'] = [k for k, v in required.items() if doc['facts'].get(k, {}).get('value') == v]
                results['checks']['model_missing_or_incorrect_fields'] = sorted(set(required) - set(results['checks']['model_exact_fields']))
            else:
                results['checks']['real_model_intake'] = 'not_run'
            # Explicit fixture confirmation is distinct from model extraction.
            doc = service.edit(owner, doc['id'], doc['revision'], str(uuid4()), required)
            draft = draft_from_legacy(doc); case = draft['case']
            case['present'] = {'HOLD': None, 'financing': 'EQUITY', 'payment': False}
            doc = service.domain_setup(owner, doc['id'], doc['revision'], str(uuid4()), case, True, 'assess_current', draft['bindings'])
            doc = service.domain_plan(owner, doc['id'], doc['revision'], str(uuid4()))
            results['checks']['fixed_entities'] = [r[0] for r in doc['domain_outcome']['structure']['entities']]
            q = next(q for q in doc['domain_outcome']['questions'] if q['id'] == doc['domain_workflow']['pending_question_id'])
            doc = service.domain_answer(owner, doc['id'], doc['revision'], str(uuid4()), q['key'], q['kind'], 'unknown', q['id'])
            results['checks']['answer_reload'] = store.get(owner, doc['id'])['canonical_fact_records'] == doc['canonical_fact_records']
            doc = service.domain_confirm(owner, doc['id'], doc['revision'], str(uuid4()))
            doc = service.domain_report(owner, doc['id'], doc['revision'], str(uuid4()), True)
            report = doc['analyses'][-1]
            results['checks']['combined_report'] = bool(report['fsie_assessment'] and report['markdown'])
            results['checks']['law_locators'] = len({p['locator'] for p in report['fsie_assessment']['passages']})
            results['checks']['rulings_status'] = report['fsie_assessment']['related_rulings']['status']
            results['checks']['ruling_passages'] = len(report['fsie_assessment']['related_rulings']['passages'])
            results['checks']['evidence_gate'] = report['evidence_gate']
            from packages.agent.review import report_hash
            results['checks']['report_frozen'] = report_hash(report) == report['report_hash']
            results['checks']['missing_domain_citations'] = len(report['missing_locators'])
            citation_map = report['outcome'].get('citation_map', {})
            read_citations = set(report['domain_citation_coverage']['read'])
            results['checks']['rule_trace_count'] = len(citation_map)
            results['checks']['rules_missing_readable_basis'] = sorted(
                rule for rule, citations in citation_map.items()
                if not citations or not set(citations) <= read_citations)
            all_passages = report['passages'] + report['fsie_assessment']['related_rulings']['passages']
            results['checks']['replayed_passage_count'] = len(all_passages)
            results['checks']['passage_hashes_valid'] = all(
                sha256(p['text'].encode()).hexdigest() == p['text_sha256'] for p in all_passages)
            try:
                store.get('user:other', doc['id'])
                results['checks']['owner_isolation'] = False
            except CaseNotFound:
                results['checks']['owner_isolation'] = True
            planning = store.create(owner)
            fixture = json.loads((ROOT / 'tests/integration/fixtures/holding.synthetic.json').read_text(encoding='utf-8'))
            planning = service.domain_setup(owner, planning['id'], 0, str(uuid4()), fixture, True, 'plan_structure')
            planning = service.domain_plan(owner, planning['id'], planning['revision'], str(uuid4()))
            for _ in range(2):
                q = next(q for q in planning['domain_outcome']['questions'] if q['id'] == planning['domain_workflow']['pending_question_id'])
                planning = service.domain_answer(owner, planning['id'], planning['revision'], str(uuid4()), q['key'], q['kind'], 'unknown', q['id'])
            results['checks']['planning_rounds'] = len(planning['integration_runs'])
            results['checks']['planner_status'] = planning['domain_outcome']['status']
            results['checks']['planner_candidates'] = planning['domain_outcome']['candidate_count']
            results['status'] = 'passed' if all([args.database_only or results['checks']['real_model_intake'] is True, results['checks']['combined_report'],
                results['checks']['answer_reload'], results['checks']['owner_isolation'], results['checks']['law_locators'] == 21,
                results['checks']['rulings_status'] == 'available', results['checks']['ruling_passages'] > 0,
                results['checks']['report_frozen'], results['checks']['missing_domain_citations'] == 0,
                not results['checks']['rules_missing_readable_basis'], results['checks']['passage_hashes_valid'],
                results['checks']['fixed_entities'] == ['OP', 'ULT'], results['checks']['planning_rounds'] == 3]) else 'failed'
    except Exception as exc:
        # Never serialize str(exc): DB/model exception messages may contain secrets.
        results['status'] = 'failed'
        results['error'] = exc.code if isinstance(exc, WorkflowError) else type(exc).__name__
        frames = traceback.extract_tb(exc.__traceback__)
        if frames:
            results['error_site'] = f'{Path(frames[-1].filename).name}:{frames[-1].lineno}'
    finally:
        if store: store.engine.dispose()
        if created:
            with admin.begin() as connection: connection.execute(text('DROP SCHEMA ' + schema + ' CASCADE'))
        admin.dispose()
    results['elapsed_seconds'] = round(monotonic() - started, 2)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(results, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(results, ensure_ascii=False))
    return 0 if results['status'] == 'passed' else 1


if __name__ == '__main__':
    raise SystemExit(main())
