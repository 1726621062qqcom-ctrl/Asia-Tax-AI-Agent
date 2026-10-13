"""State, transaction and user/professional boundaries for the merged workflows."""
from copy import deepcopy
import json
from pathlib import Path
from unittest.mock import patch
from uuid import uuid4

import pytest

from packages.chat.service import ChatService, WorkflowError
from packages.chat.store import ChatStore, CaseNotFound, RevisionConflict
from packages.domain_bridge import state
from packages.domain_bridge.bridge import DomainCase, DomainError, release_path, verify_release, run_domain
from packages.agent.providers import MockKnowledgeProvider
from packages.agent.review import report_hash

FIXTURE = json.loads((Path(__file__).parent / 'fixtures/holding.synthetic.json').read_text(encoding='utf-8'))
OWNER = 'user:test'


def rid(): return str(uuid4())


@pytest.fixture
def service(tmp_path):
    store = ChatStore(f'sqlite:///{tmp_path}/cases.sqlite')
    yield ChatService(store, provider=MockKnowledgeProvider('MOCK-01'))
    store.engine.dispose()


@pytest.fixture
def real_release():
    try:
        verify_release(release_path())
    except DomainError:
        pytest.skip('Install pinned release with scripts/install_li_release.py')


def setup(service, mode='assess_current', bindings=None, doc=None):
    doc = doc or service.store.create(OWNER)
    return service.domain_setup(OWNER, doc['id'], doc['revision'], rid(), deepcopy(FIXTURE), True, mode, bindings)


def result(doc):
    return {'status': 'needs_input', 'release': '771e452', 'input_hash': state.digest(doc), 'mode': 'assess_current',
            'currency': 'CNY', 'candidate_count': 1, 'questions': [{'kind': 'data', 'key': 'OP.group_rev',
            'prompt': '集团收入？', 'answer_schema': {'type': 'number'}, 'region': ['CN']}], 'citations': []}


def run_fake(service, doc):
    with patch('packages.domain_bridge.coordinator.run_domain', return_value=result(doc)):
        return service.domain_plan(OWNER, doc['id'], doc['revision'], rid())


def test_v1_migration_and_entity_binding_roundtrip(service):
    doc = service.store.create(OWNER)
    doc = service.edit(OWNER, doc['id'], 0, rid(), {'income_type': 'dividend', 'dividend_amount': 1000000,
                       'dividend_currency': 'CNY', 'payer_jurisdiction': 'CN', 'analysis_jurisdiction': 'HK'})
    assert doc['schema_version'] == '2.0.0' and doc['migration']['from'] == '1'
    bindings = {'dividend_amount': 'event.dividend', 'dividend_currency': 'case.currency', 'payer_jurisdiction': 'OP.loc'}
    doc = setup(service, bindings=bindings, doc=doc)
    assert 'legacy.dividend_amount' not in doc['canonical_fact_records']
    doc = service.edit(OWNER, doc['id'], doc['revision'], rid(), {'dividend_amount': 2000000})
    assert doc['domain_case']['event']['dividend'] == 2000000
    assert doc['canonical_fact_records']['event.dividend']['value'] == doc['facts']['dividend_amount']['value']
    changed = deepcopy(doc['domain_case']); changed['event']['dividend'] = 3000000
    doc = service.domain_setup(OWNER, doc['id'], doc['revision'], rid(), changed, True, 'assess_current', bindings)
    assert doc['facts']['dividend_amount']['value'] == 3000000
    assert doc['domain_answers']['data'].get('OP.group_rev') is None


def test_unknown_false_and_separate_entities():
    doc = {'revision': 0, 'facts': {}}
    state.ensure(doc); state.install(doc, FIXTURE, {})
    state.write(doc, 'OP.qualifying', False, 'user'); state.write(doc, 'ULT.qualifying', 'unknown', 'user')
    state.sync(doc)
    assert state.project_case(doc)['roles']['OP']['attrs']['qualifying'] is False
    assert 'qualifying' not in state.project_case(doc)['roles']['ULT']['attrs']
    assert state.answers(doc)['data']['ULT.qualifying'] == 'unknown'
    assert state.answers(doc)['data']['OP.qualifying']['value'] is False


def test_binding_conflict_is_atomic(service):
    doc = service.store.create(OWNER)
    doc = service.edit(OWNER, doc['id'], 0, rid(), {'dividend_amount': 12})
    with pytest.raises(ValueError): setup(service, doc=doc, bindings={'dividend_amount': 'event.dividend'})
    assert service.store.get(OWNER, doc['id'])['revision'] == doc['revision']


def test_idempotence_payload_conflict_revision_and_owner(service):
    doc = service.store.create(OWNER); request = rid()
    doc = service.domain_setup(OWNER, doc['id'], 0, request, FIXTURE, True, 'assess_current')
    assert service.domain_setup(OWNER, doc['id'], 0, request, FIXTURE, True, 'assess_current') == doc
    with pytest.raises(WorkflowError) as exc:
        service.domain_setup(OWNER, doc['id'], 0, request, FIXTURE, True, 'plan_structure')
    assert exc.value.code == 'request_payload_conflict'
    with pytest.raises(RevisionConflict): service.domain_plan(OWNER, doc['id'], 0, rid())
    with pytest.raises(CaseNotFound): service.domain_plan('user:other', doc['id'], doc['revision'], rid())


@pytest.mark.parametrize('code', ['domain_timeout', 'domain_execution_failed'])
def test_worker_failure_never_commits_answer(service, code):
    doc = run_fake(service, setup(service)); q = doc['domain_outcome']['questions'][0]
    with patch('packages.domain_bridge.coordinator.run_domain', side_effect=DomainError(code)):
        with pytest.raises(WorkflowError) as exc:
            service.domain_answer(OWNER, doc['id'], doc['revision'], rid(), q['key'], q['kind'], '123', q['id'])
    assert exc.value.code == code
    saved = service.store.get(OWNER, doc['id'])
    assert saved['revision'] == doc['revision'] and 'OP.group_rev' not in saved['canonical_fact_records']


def test_defer_pause_and_stale_question(service):
    doc = run_fake(service, setup(service)); q = doc['domain_outcome']['questions'][0]
    doc = service.domain_answer(OWNER, doc['id'], doc['revision'], rid(), q['key'], q['kind'], '', q['id'], 'defer')
    assert doc['domain_workflow']['pending_question_id'] is None
    doc = service.domain_control(OWNER, doc['id'], doc['revision'], rid(), 'pause')
    with pytest.raises(WorkflowError) as exc: service.domain_answer(OWNER, doc['id'], doc['revision'], rid(), q['key'], q['kind'], '1', q['id'])
    assert exc.value.code == 'domain_paused'
    doc = service.edit(OWNER, doc['id'], doc['revision'], rid(), {'income_type': 'dividend'})
    assert doc['domain_outcome']['stale']


def test_chat_answer_and_retry_share_transaction(service):
    doc = run_fake(service, setup(service)); q = doc['domain_outcome']['questions'][0]; request = rid()
    with patch('packages.domain_bridge.coordinator.run_domain', return_value=result(doc)):
        updated = service.message(OWNER, doc['id'], doc['revision'], request, '结构答复：123', True, reply_to_question_id=q['id'])
    replay = service.message(OWNER, doc['id'], doc['revision'], request, '结构答复：123', True, reply_to_question_id=q['id'])
    assert replay == updated
    assert updated['canonical_fact_records']['OP.group_rev']['value'] == 123
    assert sum(m.get('text') == '结构答复：123' for m in updated['messages']) == 1
    with pytest.raises(WorkflowError) as exc:
        service.message(OWNER, doc['id'], doc['revision'], request, '结构答复：124', True, reply_to_question_id=q['id'])
    assert exc.value.code == 'request_payload_conflict'


def test_report_requires_confirmation_partial_consent_and_freezes(service):
    doc = run_fake(service, setup(service))
    with pytest.raises(WorkflowError) as exc: service.domain_report(OWNER, doc['id'], doc['revision'], rid(), True)
    assert exc.value.code == 'confirmation_required'
    doc = service.domain_confirm(OWNER, doc['id'], doc['revision'], rid())
    with pytest.raises(WorkflowError) as exc: service.domain_report(OWNER, doc['id'], doc['revision'], rid())
    assert exc.value.code == 'partial_confirmation_required'
    request = rid(); saved = service.domain_report(OWNER, doc['id'], doc['revision'], request, True)
    report = saved['analyses'][-1]
    assert report['report_hash'] == report_hash(report)
    assert report['evidence_gate'] == 'insufficient' and report['blockers']
    assert report['markdown'] and report['canonical_snapshot']
    assert service.domain_report(OWNER, doc['id'], doc['revision'], request, True) == saved
    changed = service.edit(OWNER, doc['id'], saved['revision'], rid(), {'income_type': 'dividend'})
    assert changed['analyses'][-1]['stale']


def test_professional_endpoint_requires_role(service, monkeypatch):
    monkeypatch.setenv('FSIE_AGENT_REVIEWER_IDS', '[]')
    doc = setup(service)
    with pytest.raises(WorkflowError) as exc:
        service.domain_professional(OWNER, doc['id'], doc['revision'], rid(), 'li:fake', 'yes', {}, 'ordinary-user')
    assert exc.value.code == 'review_forbidden'


def test_real_fixed_does_not_design_new_companies(real_release):
    out = run_domain(DomainCase.model_validate(FIXTURE), {}, today='2026-10-11', mode='assess_current')
    assert out['candidate_count'] == 1 and out['status'] == 'needs_input'
    assert {e[0] for e in out['structure']['entities']} == {'OP', 'ULT'}
    assert out['citations'] and out['upper']['status'] == 'finite'
    assert any(q['kind'] == 'ruling' for q in out['questions'])


def test_real_two_rounds_planner_persist_and_reload(service, real_release):
    doc = setup(service, 'plan_structure'); doc = service.domain_plan(OWNER, doc['id'], doc['revision'], rid())
    for _ in range(2):
        q = next(q for q in doc['domain_outcome']['questions'] if q['id'] == doc['domain_workflow']['pending_question_id'])
        doc = service.domain_answer(OWNER, doc['id'], doc['revision'], rid(), q['key'], q['kind'], 'unknown', q['id'])
    assert len(doc['integration_runs']) == 3
    assert service.store.get(OWNER, doc['id'])['canonical_fact_records'] == doc['canonical_fact_records']
    assert sum(r['status'] == 'unknown' for r in doc['canonical_fact_records'].values()) == 2
    assert doc['domain_outcome']['status'] == 'blocked'
    assert 'unbounded' in doc['domain_outcome']['note']


def test_currency_missing_rejected_non_cny_explicitly_unsupported(service):
    doc = service.store.create(OWNER); case = deepcopy(FIXTURE); case.pop('currency')
    with pytest.raises(WorkflowError) as exc: service.domain_setup(OWNER, doc['id'], 0, rid(), case, True)
    assert exc.value.code == 'currency_required'
    case['currency'] = 'SGD'
    doc = service.domain_setup(OWNER, doc['id'], 0, rid(), case, True)
    doc = service.domain_plan(OWNER, doc['id'], doc['revision'], rid())
    assert doc['domain_outcome']['status'] == 'unsupported' and not doc['domain_outcome']['questions']


def test_fact_change_revokes_professional_answers(service):
    doc = setup(service)
    raw = service.store.get(OWNER, doc['id'])
    raw['domain_answers']['rulings']['ULT.some_professional_judgment'] = 'yes'
    raw['domain_professional_history'] = [{'reviewer': 'expert', 'at': 'test'}]
    raw = service.store.save(OWNER, raw, doc['revision'])
    doc = service.edit(OWNER, doc['id'], raw['revision'], rid(), {'dividend_amount': 100})
    assert doc['domain_answers']['rulings'] == {}
    assert doc['domain_professional_history'][0]['stale']
