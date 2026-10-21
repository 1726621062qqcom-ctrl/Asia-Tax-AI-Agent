"""Compare the legacy and combined knowledge paths on the same synthetic questions.

Runs real cloud reads and a real loopback C HTTP service; no model calls or
customer sessions. The corpus differs by provider, so this is a product-path
comparison, not a causal estimate of one retrieval algorithm's improvement.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import statistics
import subprocess
import sys
from time import monotonic
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from packages.agent.contracts import SearchRequest, TrustedContext
from packages.agent.knowledge import retrieve
from packages.agent.providers import CKnowledgeProvider, LegacyKnowledgeProvider, RoutedKnowledgeProvider
from packages.chat.knowledge import references
from packages.domain_bridge.bridge import PINNED_COMMIT, PINNED_DB_SHA256, PINNED_SOURCE_SHA256
from scripts.combined_runtime import knowledge_server


def requests_for(case):
    locators, rulings = references(case['query'])
    parts = []
    if locators:
        # A bare section asks for its subsections; forcing an exact parent
        # locator would unfairly prevent the legacy path from expanding it.
        parts.append(('law', locators if all('(' in locator for locator in locators) else []))
    if rulings:
        parts.append(('ruling', []))
    if not parts:
        parts.append(('all', []))
    return parts


def evaluate(case, provider):
    started = monotonic()
    bundles = []
    for kind, locators in requests_for(case):
        request = SearchRequest(request_id=str(uuid4()), trace_id=str(uuid4()),
                                query=case['query'], kind=kind, locators=locators,
                                deadline_ms=10000)
        bundles.append(retrieve(provider, request, TrustedContext(owner='evaluation:synthetic')))
    passages = list({p['unit_id']: p for bundle in bundles for p in bundle['passages']}.values())
    found = {
        'expected_locators': {p.get('locator') for p in passages},
        'expected_units': {p.get('unit_id') for p in passages},
        'expected_sources': {p.get('source_id') for p in passages},
    }
    missing = {key: sorted(set(case.get(key, [])) - found[key]) for key in found}
    missing = {key: value for key, value in missing.items() if value}
    status = [b['status'] for b in bundles]
    passed = (not passages and all(s == 'no_matching_units' for s in status)) if case.get('expect_empty') else (
        bool(passages) and not missing and 'unavailable' not in status)
    return {
        'passed': passed, 'status': status, 'seconds': round(monotonic() - started, 3),
        'missing': missing, 'passage_count': len(passages),
        'gaps': [gap for bundle in bundles for gap in bundle['gaps']],
        'errors': [b['error']['code'] for b in bundles if b['error']],
        'traces': [{'unit_id': p['unit_id'], 'source_id': p['source_id'],
                    'locator': p.get('locator'), 'text_sha256': p['text_sha256'],
                    'source_version_id': p['source_version_id'],
                    'model_use': p['model_use'], 'drift': p['drift']} for p in passages],
    }


def summary(rows, path):
    results = [row[path] for row in rows]
    seconds = sorted(result['seconds'] for result in results)
    return {
        'passed': sum(result['passed'] for result in results), 'total': len(results),
        'positive_passed': sum(result['passed'] for row, result in zip(rows, results) if not row['expect_empty']),
        'positive_total': sum(not row['expect_empty'] for row in rows),
        'negative_passed': sum(result['passed'] for row, result in zip(rows, results) if row['expect_empty']),
        'negative_total': sum(row['expect_empty'] for row in rows),
        'unavailable': sum('unavailable' in result['status'] for result in results),
        'median_seconds': round(statistics.median(seconds), 3),
        'p95_seconds': seconds[max(0, (95 * len(seconds) + 99) // 100 - 1)],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--only', help='Comma-separated case IDs for a focused rerun')
    args = parser.parse_args()
    cases = json.loads((ROOT / 'tests/chat/retrieval_cases.json').read_text(encoding='utf-8'))['cases']
    if args.only:
        selected = set(args.only.split(','))
        unknown = selected - {case['id'] for case in cases}
        if unknown:
            parser.error('unknown case IDs: ' + ', '.join(sorted(unknown)))
        cases = [case for case in cases if case['id'] in selected]
    revision = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True, encoding='utf-8').strip()
    report = {'at': datetime.now(timezone.utc).isoformat(), 'revision': revision,
              'dataset': 'tests/chat/retrieval_cases.json', 'synthetic': True,
              'model_calls': 0, 'old_path': 'LegacyKnowledgeProvider + cloud PostgreSQL',
              'new_path': 'RoutedKnowledgeProvider + real C loopback HTTP (law) + legacy cloud rulings',
              'tax_engine_release': PINNED_COMMIT, 'tax_engine_database_sha256': PINNED_DB_SHA256,
              'tax_engine_source_sha256': PINNED_SOURCE_SHA256, 'rows': []}
    with knowledge_server() as (url, token):
        law = CKnowledgeProvider(url, token)
        try:
            providers = {'old': LegacyKnowledgeProvider(),
                         'new': RoutedKnowledgeProvider(law, LegacyKnowledgeProvider())}
            for index, case in enumerate(cases):
                row = {'id': case['id'], 'query': case['query'], 'expect_empty': bool(case.get('expect_empty')),
                       'expected_locators': case.get('expected_locators', []),
                       'expected_units': case.get('expected_units', []),
                       'expected_sources': case.get('expected_sources', [])}
                for name in ('old', 'new') if index % 2 == 0 else ('new', 'old'):
                    row[name] = evaluate(case, providers[name])
                report['rows'].append(row)
                print(case['id'], 'old=' + str(row['old']['passed']),
                      'new=' + str(row['new']['passed']), flush=True)
        finally:
            law.close()
    report['summary'] = {name: summary(report['rows'], name) for name in ('old', 'new')}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report['summary'], ensure_ascii=False))
    return 0 if report['summary']['new']['passed'] == report['summary']['new']['total'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
