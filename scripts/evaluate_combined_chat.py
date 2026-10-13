"""Run synthetic streaming chat cases against real C HTTP and cloud rulings."""
import argparse
import asyncio
from hashlib import sha256
import json
import os
from pathlib import Path
import re

from scripts.combined_runtime import knowledge_server
from scripts.evaluate_chat import evaluate


def verify_report(path: Path) -> bool:
    report = json.loads(path.read_text(encoding='utf-8'))
    positives = {'T05', 'T06', 'T07', 'T08', 'T09', 'T10', 'T11'}
    negatives = {'T16'}
    checks = []
    for row in report['rows']:
        messages = row.get('messages') or []
        if row.get('status') != 'completed' or len(messages) != 1:
            checks.append({'id': row['id'], 'passed': False, 'reason': 'chat_not_completed'})
            continue
        message = messages[0]
        research = message.get('research') or {}
        passages = research.get('passages') or []
        cited = re.findall(r'依据摘录 \[([^\]]+)\]', message.get('text') or '')
        IDs = {passage['evidence_id'] for passage in passages}
        hashes_ok = all(sha256(p['text'].encode()).hexdigest() == p['text_sha256'] for p in passages)
        if row['id'] in positives:
            passed = (bool(passages) and bool(cited) and set(cited) <= IDs and hashes_ok
                      and message['workflow']['status'] == 'draft_ready'
                      and research['reason_code'] == 'evidence_available')
        elif row['id'] in negatives:
            passed = (not passages and not cited and message['workflow']['status'] == 'paused_gap'
                      and research['reason_code'] == 'no_match')
        else:
            passed = False
        checks.append({'id': row['id'], 'passed': passed, 'passages': len(passages),
                       'cited_evidence_ids': cited, 'passage_hashes_valid': hashes_ok,
                       'reason_code': research.get('reason_code')})
    report['trace_checks'] = checks
    report['trace_summary'] = {'passed': sum(c['passed'] for c in checks), 'total': len(checks),
                               'positive': sum(c['passed'] for c in checks if c['id'] in positives),
                               'negative': sum(c['passed'] for c in checks if c['id'] in negatives)}
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report['trace_summary']))
    return bool(checks) and all(c['passed'] for c in checks)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--only', default='T05,T06,T07,T08,T09,T10,T11,T16')
    parser.add_argument('--verify-existing', action='store_true', help='Check a previously saved report without model calls')
    args = parser.parse_args()
    if args.verify_existing:
        return 0 if verify_report(args.output) else 1
    with knowledge_server() as (url, token):
        os.environ.update(FSIE_AGENT_ORCHESTRATION='hybrid', FSIE_AGENT_PROVIDER='combined',
                          FSIE_AGENT_C_URL=url, FSIE_AGENT_C_TOKEN=token)
        success = asyncio.run(evaluate(args.output, args.only))
    return 0 if success and verify_report(args.output) else 1


if __name__ == '__main__':
    raise SystemExit(main())
