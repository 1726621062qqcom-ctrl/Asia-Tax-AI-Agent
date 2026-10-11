"""Real loopback C HTTP + real Li + temporary case SQLite; no model substitute claims."""
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
from tempfile import TemporaryDirectory
from time import monotonic, sleep
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main():
    import httpx
    from packages.chat.service import ChatService
    from packages.chat.store import ChatStore
    from packages.domain_bridge.bridge import release_path, verify_release
    from packages.agent.providers import CKnowledgeProvider, RoutedKnowledgeProvider, LegacyKnowledgeProvider
    from packages.agent.review import report_hash
    verify_release(release_path())
    with socket.socket() as sock:
        sock.bind(('127.0.0.1', 0)); port = sock.getsockname()[1]
    env = dict(os.environ); env['FSIE_AGENT_C_TOKEN'] = ''
    process = subprocess.Popen([sys.executable, '-m', 'uvicorn', 'apps.knowledge_api.main:app', '--host',
                                '127.0.0.1', '--port', str(port), '--log-level', 'error'],
                               cwd=ROOT, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    results = {'database': 'isolated_sqlite', 'model': 'not_called', 'knowledge_transport': 'real_loopback_http', 'checks': {}}
    try:
        start = monotonic()
        while True:
            try:
                if httpx.get(f'http://127.0.0.1:{port}/health', timeout=2).json().get('knowledge_ready'): break
            except httpx.HTTPError: pass
            if process.poll() is not None or monotonic() - start > 15: raise RuntimeError('knowledge_server_unavailable')
            sleep(.1)
        with TemporaryDirectory(prefix='combined-http-') as directory:
            store = ChatStore('sqlite:///' + str(Path(directory) / 'case.sqlite'))
            try:
                # Synthetic ruling reader validates explicit source routing only;
                # it does not establish availability of the cloud ruling corpus.
                provider = RoutedKnowledgeProvider(CKnowledgeProvider(f'http://127.0.0.1:{port}'),
                                                    LegacyKnowledgeProvider(lambda _: {'status': 'no_matching_units', 'passages': []}))
                service = ChatService(store, provider=provider); owner = 'user:http-smoke'
                doc = store.create(owner)
                doc = service.edit(owner, doc['id'], 0, str(uuid4()), {'dividend_amount': 1000000,
                    'dividend_currency': 'CNY', 'payer_jurisdiction': 'CN', 'income_type': 'dividend',
                    'receipt_date': '2026-10-11'})
                case = json.loads((ROOT / 'tests/integration/fixtures/holding.synthetic.json').read_text())
                bindings = {'dividend_amount': 'event.dividend', 'dividend_currency': 'case.currency',
                            'payer_jurisdiction': 'OP.loc', 'receipt_date': 'event.on'}
                doc = service.domain_setup(owner, doc['id'], doc['revision'], str(uuid4()), case, True, 'assess_current', bindings)
                doc = service.domain_plan(owner, doc['id'], doc['revision'], str(uuid4()))
                doc = service.domain_confirm(owner, doc['id'], doc['revision'], str(uuid4()))
                doc = service.domain_report(owner, doc['id'], doc['revision'], str(uuid4()), True)
                report = doc['analyses'][-1]
                results['checks']['report_frozen'] = report_hash(report) == report['report_hash']
                results['checks']['fsie_locators'] = len({p['locator'] for p in report['fsie_assessment']['passages']})
                results['checks']['evidence_reads'] = report['budget'].get('evidence', 0)
                results['checks']['current_entities'] = [e[0] for e in report['outcome']['structure']['entities']]
                results['checks']['missing_domain_citations'] = len(report['missing_locators'])
                results['checks']['reload'] = store.get(owner, doc['id'])['revision'] == doc['revision']
                results['status'] = 'passed' if results['checks']['report_frozen'] and results['checks']['fsie_locators'] == 21 and results['checks']['reload'] else 'failed'
            finally: store.engine.dispose()
    finally:
        process.terminate()
        try: process.wait(timeout=5)
        except subprocess.TimeoutExpired: process.kill(); process.wait()
    print(json.dumps(results, ensure_ascii=False))
    return 0 if results['status'] == 'passed' else 1


if __name__ == '__main__':
    raise SystemExit(main())
