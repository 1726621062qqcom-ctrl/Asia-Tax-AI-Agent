#!/usr/bin/env python3
"""Reproduce the interview audit against the pinned engine; no network or user data."""
import argparse
from copy import deepcopy
import csv
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from packages.domain_bridge.bridge import DomainCase, release_path, verify_release, run_domain
from packages.domain_bridge import state
from packages.domain_bridge.question_order import CATALOG, GATES, EVENT_GATES, PILLAR_FIELDS, prepare_questions, next_question, eligible


def audit():
    release = release_path()
    verify_release(release)
    sys.path.insert(0, str(release))
    from tax_graph.engine import RULES
    from tax_graph.scenarios import TEMPLATES
    from tax_graph.battery import make_case, make_composite, pack
    fields = list(csv.DictReader((release / 'tax_graph/data/field_gloss.csv').open()))
    assert all(row['field'] in CATALOG for row in fields)
    report = {'rule_count': len(RULES), 'glossary_fields': len(fields), 'audited_fields': len(CATALOG), 'scenarios': []}
    for template in list(TEMPLATES) + ['holding+ip', 'holding+services', 'ip+services']:
        locations = {'SERVICER': 'HK', 'CLIENT': 'CN'} if template == 'inbound_services' else {'OP': 'CN', 'ULT': 'HK'}
        _, case = make_composite(template, locations) if '+' in template else make_case(template, locations, True, 'open', 1)
        case['currency'] = 'CNY'
        # Freeze the selected placements as existing entities for fixed-mode runs.
        for role, loc in case['present'].items():
            if role in ('SERVICER', 'LENDER', 'IPCO', 'HOLD') and loc in ('CN', 'HK', 'SG') and role not in case['roles']:
                case['roles'][role] = {'loc': loc, 'attrs': pack(loc, True)}
        for mode in ('assess_current', 'review_paid', 'plan_structure'):
            doc = {'revision': 0, 'facts': {}, 'domain_workflow': {'mode': mode}}
            state.ensure(doc)
            state.install(doc, case, {})
            result = run_domain(DomainCase.model_validate(case), state.answers(doc), today='2026-10-21', mode=mode)
            unchanged = {k: deepcopy(result.get(k)) for k in ('upper','lower','status','structure','citations')}
            prepare_questions(result, doc)
            doc['domain_outcome'] = result
            pending = next_question(result['questions'], doc, 'audit')
            assert not pending or eligible(pending, doc)
            assert unchanged == {k: result.get(k) for k in unchanged}
            report['scenarios'].append({'template': template, 'mode': mode, 'status': result['status'],
                'questions': len(result['questions']), 'counts': result['interview_counts'],
                'next': pending['key'] if pending else None,
                'unreviewed': [q['key'] for q in result['questions'] if q['interview_status'] == 'needs_policy_review']})
            print(template, mode, result['status'], result['interview_counts'], flush=True)
    report['fields'] = []
    for row in fields:
        field = row['field']
        report['fields'].append({'field':field, 'label':row['gloss'], 'family':CATALOG[field]['family'],
            'policy': 'event prerequisite' if field in EVENT_GATES else 'scope prerequisite' if field in PILLAR_FIELDS else
                      'fact prerequisite' if field in GATES else 'engine-scoped / contextual question',
            'rules': sorted(r.id for r in RULES if any(k.split('.',1)[-1] == field for k in r.reads))})
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    report = audit()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    if any(row['unreviewed'] for row in report['scenarios']):
        raise SystemExit('Unreviewed generated questions need policy review; see output.')
