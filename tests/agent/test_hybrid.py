"""Hybrid behavior tests: controlled model outputs isolate the business contract."""
from copy import deepcopy
from uuid import uuid4
import json

import pytest
from fastapi.testclient import TestClient

from packages.agent.providers import MockKnowledgeProvider
from packages.agent.budget import RunBudget, BudgetedProvider, BudgetExceeded
from packages.agent.hybrid import SHORTCUTS
from packages.agent.knowledge import retrieve, compose_answer
from packages.agent.contracts import SearchRequest, TrustedContext
from packages.agent.analysis_policy import analysis_eligibility
from packages.chat.service import ChatService, WorkflowError, turn_prompt
from packages.chat.store import ChatStore, RevisionConflict


def parsed(intent='intake', facts=None, **kwargs):
    return {'intent': intent, 'facts': facts or {}, 'reply': '已收到信息。',
            'query': '香港股息FSIE规定' if intent == 'research' else '', **kwargs}


class RecordingProvider(MockKnowledgeProvider):
    def __init__(self, scenario='MOCK-01'):
        super().__init__(scenario)
        self.searches, self.reads = [], []

    def search_evidence(self, request, context):
        self.searches.append((request, context))
        return super().search_evidence(request, context)

    def get_evidence(self, reference, purpose, context):
        self.reads.append((reference, purpose, context))
        return super().get_evidence(reference, purpose, context)


@pytest.fixture
def chat(tmp_path):
    store = ChatStore(f'sqlite:///{tmp_path}/hybrid.sqlite')
    service = ChatService(store, provider=RecordingProvider(), orchestration='hybrid',
                          turner=lambda *_: parsed())
    yield service
    store.engine.dispose()


def send(service, doc, turn=None, text='我的案件描述', **kwargs):
    if turn is not None:
        service.turner = lambda *_: deepcopy(turn)
    return service.message('owner', doc['id'], doc['revision'], str(uuid4()), text, True, **kwargs)


def edit(service, doc, facts):
    return service.edit('owner', doc['id'], doc['revision'], str(uuid4()), facts)


BASE = {'recipient_type': 'company', 'income_type': 'dividend', 'analysis_jurisdiction': 'HK',
        'consultation_goal': 'scope', 'payer_jurisdiction': '新加坡'}


@pytest.mark.parametrize('text,kind', [(text, kind) for text, (kind, _) in SHORTCUTS.items()
                                     if kind != 'consultation'])
@pytest.mark.parametrize('locale', ['zh', 'en'])
def test_fact_and_reference_shortcuts_start_their_own_workflows(chat, text, kind, locale):
    chat.turner = lambda *_: pytest.fail('Starting a selected task must not depend on model routing')
    doc = send(chat, chat.store.create('owner'), text=text, entry_hint=kind, locale=locale)
    message = doc['messages'][-1]
    assert doc['workflow']['effective_task'] == kind
    assert doc['workflow']['trace'] == ['route', 'facts', kind, 'observe', 'validate']
    assert doc['facts'] == {} and not chat.provider.searches and not doc['analyses']
    assert message['kind'] == 'intake' and 'research' not in message
    assert message['question']['field'] == ('recipient_type' if kind == 'fact_intake' else None)
    assert message['question']['task_id'] == doc['orchestration']['active_task']['id']
    assert doc['dialogue']['pending'] == message['question']
    assert doc['orchestration']['active_task']['status'] == doc['workflow']['status'] == 'waiting_user'
    assert doc['orchestration']['active_task']['uses_case'] == (kind == 'fact_intake')
    assert 'li|' not in message['text']
    if kind == 'reference_lookup':
        assert doc['dialogue']['pending']['id'].startswith('hybrid:reference:')
        assert ('Which rule or official case' if message['reply_locale'] == 'en' else '你想查哪项规定') in message['text']


def test_reference_question_resumes_as_independent_lookup_without_rewriting_facts(chat):
    doc = edit(chat, chat.store.create('owner'), {**BASE, 'accrual_date': '2025-04-10',
                                                'income_event_status': 'occurred'})
    doc = chat.confirm('owner', doc['id'], doc['revision'], str(uuid4()))
    facts, confirmed = deepcopy(doc['facts']), doc['confirmed_revision']
    doc = send(chat, doc, text='我想查香港境外股息的法规或官方案例，请帮我找到依据。',
               entry_hint='reference_lookup')
    qid, task_id = doc['dialogue']['pending']['id'], doc['orchestration']['active_task']['id']
    doc = chat.store.get('owner', doc['id'])
    doc = send(chat, doc, parsed('research', query='Case 68', uses_case=False),
               text='Case 68', reply_to_question_id=qid)
    assert doc['messages'][-1]['kind'] == 'research'
    assert doc['orchestration']['active_task']['id'] == task_id
    assert doc['orchestration']['active_task']['status'] == 'completed'
    assert doc['facts'] == facts and doc['confirmed_revision'] == confirmed
    request, context = chat.provider.searches[-1]
    assert request.query == 'Case 68' and request.kind == 'ruling'
    assert request.date_status == 'not_needed' and request.fact_filters == []
    assert context.case_id is None
    with pytest.raises(WorkflowError, match='question_changed'):
        send(chat, doc, text='Case 69', reply_to_question_id=qid)


def test_reference_unknown_pause_and_resume_do_not_start_fact_interview(chat):
    doc = send(chat, chat.store.create('owner'), text='研究境外股息的 FSIE 处理，应当查阅哪些官方资料？',
               entry_hint='reference_lookup')
    task_id = doc['orchestration']['active_task']['id']
    for control in ('不知道', '暂时没有资料', '暂停', '继续案件'):
        doc = send(chat, doc, text=control)
        assert not doc['facts'] and not chat.provider.searches
        assert doc['orchestration']['active_task']['id'] == task_id
        assert doc['orchestration']['active_task']['kind'] == 'reference_lookup'
        assert doc['dialogue']['pending']['id'].startswith('hybrid:reference:')
        assert doc['dialogue']['pending']['field'] is None
    assert doc['workflow']['status'] == 'waiting_user'


def test_fact_shortcut_continues_existing_intake_without_reasking_known_fields(chat):
    doc = edit(chat, chat.store.create('owner'), BASE)
    doc = send(chat, doc, text='请带我逐步整理这笔股息的事实，并指出还缺哪些信息。',
               entry_hint='fact_intake')
    assert doc['dialogue']['pending']['field'] == 'entity_hk_business_status'
    task_id = doc['orchestration']['active_task']['id']
    doc = send(chat, doc, text='有', reply_to_question_id=doc['dialogue']['pending']['id'])
    assert doc['facts']['entity_hk_business_status']['value'] == 'yes'
    assert doc['orchestration']['active_task']['id'] == task_id
    assert not chat.provider.searches and not doc['analyses']


@pytest.mark.parametrize('text', [text for text, (kind, _) in SHORTCUTS.items() if kind == 'consultation'])
@pytest.mark.parametrize('locale', ['zh', 'en'])
def test_dividend_shortcut_starts_consultation_without_model_or_lookup(chat, text, locale):
    chat.turner = lambda *_: pytest.fail('The selected consultation must not depend on model routing')
    doc = send(chat, chat.store.create('owner'), text=text,
               entry_hint='dividend_consultation', locale=locale)
    message = doc['messages'][-1]
    assert doc['workflow']['trace'] == ['route', 'facts', 'consultation', 'observe', 'validate']
    assert doc['workflow']['effective_task'] == 'consultation'
    assert doc['workflow']['status'] == 'waiting_user'
    assert doc['facts'] == {} and not chat.provider.searches and not doc['analyses']
    assert doc['confirmed_facts'] is None
    assert message['kind'] == 'intake' and 'research' not in message
    assert message['question']['field'] == 'recipient_type'
    assert doc['dialogue']['pending'] == message['question']
    assert message['question']['task_id'] == doc['orchestration']['active_task']['id']
    assert doc['orchestration']['active_task']['status'] == 'waiting_user'
    assert 'li|' not in message['text']
    if doc['messages'][-1]['reply_locale'] == 'en':
        assert 'Please clarify:' in message['text']
    assert chat.store.get('owner', doc['id'])['dialogue']['pending'] == message['question']


def test_consultation_continues_after_reload_and_rejects_stale_question(chat):
    doc = send(chat, chat.store.create('owner'), text=next(iter(SHORTCUTS)),
               entry_hint='dividend_consultation')
    task_id = doc['orchestration']['active_task']['id']
    question_id = doc['dialogue']['pending']['id']
    doc = chat.store.get('owner', doc['id'])
    doc = send(chat, doc, text='公司', reply_to_question_id=question_id)
    assert doc['facts']['recipient_type']['value'] == 'company'
    assert doc['dialogue']['pending']['field'] == 'income_type'
    assert doc['orchestration']['active_task']['id'] == task_id
    assert not chat.provider.searches
    before = chat.store.get('owner', doc['id'])
    with pytest.raises(WorkflowError, match='question_changed'):
        send(chat, doc, text='个人', reply_to_question_id=question_id)
    assert chat.store.get('owner', doc['id']) == before


def test_consultation_uses_existing_facts_and_keeps_confirmation_gate(chat):
    doc = edit(chat, chat.store.create('owner'), BASE)
    doc = send(chat, doc, text=next(iter(SHORTCUTS)), entry_hint='dividend_consultation')
    assert doc['dialogue']['pending']['field'] == 'entity_hk_business_status'
    assert {key: value['value'] for key, value in doc['facts'].items()} == BASE
    assert not chat.provider.searches and not doc['analyses']
    with pytest.raises(WorkflowError, match='confirmation_required'):
        chat.run('owner', doc['id'], doc['revision'], str(uuid4()))


def test_preparation_question_in_auto_remains_independent_research(chat):
    doc = send(chat, chat.store.create('owner'), parsed('research', uses_case=False),
               text=next(iter(SHORTCUTS)))
    assert doc['messages'][-1]['kind'] == 'research'
    assert not doc['messages'][-1]['question'] and not doc['facts']
    assert doc['workflow']['effective_task'] == 'reference_lookup'
    assert chat.provider.searches[0][1].case_id is None


def test_mismatched_shortcut_hint_does_not_force_consultation(chat):
    doc = send(chat, chat.store.create('owner'), parsed('research', uses_case=False),
               text=next(iter(SHORTCUTS)), entry_hint='reference_lookup')
    assert doc['workflow']['effective_task'] == 'reference_lookup'
    assert doc['messages'][-1]['kind'] == 'research' and not doc['messages'][-1]['question']


@pytest.mark.parametrize('sse', [False, True])
@pytest.mark.parametrize('hint,text,kind,field', [
    ('dividend_consultation', '分析境外股息的 FSIE 处理，需要先确认哪些事实？', 'consultation', 'recipient_type'),
    ('fact_intake', '请带我逐步整理这笔股息的事实，并指出还缺哪些信息。', 'fact_intake', 'recipient_type'),
    ('reference_lookup', '我想查香港境外股息的法规或官方案例，请帮我找到依据。', 'reference_lookup', None),
])
def test_shortcut_api_starts_own_workflow_and_replays_once(chat, sse, hint, text, kind, field):
    from apps.api.main import app
    from apps.api.auth import optional_user
    from apps.api.chat import get_service
    app.dependency_overrides[optional_user] = lambda: {'id': 'fixture', 'email': 'fixture@example.invalid'}
    app.dependency_overrides[get_service] = lambda: chat
    chat.turner = lambda *_: pytest.fail('No model is needed to start the selected consultation')
    try:
        with TestClient(app) as client:
            headers = {'x-asiatax-request': '1'}
            original = client.post('/api/cases', headers=headers).json()
            path = f"/api/cases/{original['id']}/messages"
            payload = {'text': text, 'revision': original['revision'],
                       'request_id': str(uuid4()), 'data_approved': True,
                       'entry_hint': hint}
            response = client.post(path, headers={**headers, **({'accept': 'text/event-stream'} if sse else {})}, json=payload)
            assert response.status_code == 200
            if sse:
                events = [json.loads(line[6:]) for line in response.text.splitlines() if line.startswith('data: ')]
                assert [event['type'] for event in events] == ['done']
                result = events[0]['case']
            else:
                result = response.json()
            assert result['workflow']['effective_task'] == kind
            assert result['workflow']['status'] == 'waiting_user'
            assert result['messages'][-1]['question']['field'] == field
            replay = client.post(path, headers=headers, json=payload)
            assert replay.status_code == 200 and replay.json() == result
            assert len(result['messages']) == 2 and not chat.provider.searches
    finally:
        app.dependency_overrides.clear()


def test_fixed_hint_and_auto_share_fact_policy(chat):
    a = send(chat, chat.store.create('owner'), parsed(facts=BASE), entry_hint='fact_intake')
    b = send(chat, chat.store.create('owner'), parsed(facts=BASE))
    assert a['messages'][-1]['question']['field'] == b['messages'][-1]['question']['field']
    assert {k: v['value'] for k, v in a['facts'].items()} == {k: v['value'] for k, v in b['facts'].items()}
    assert not chat.provider.searches


def test_task_pending_unknown_multiple_facts_and_resume(chat):
    doc = send(chat, chat.store.create('owner'), parsed(facts={'income_type': 'dividend'}), entry_hint='fact_intake')
    task_id = doc['orchestration']['active_task']['id']
    qid = doc['messages'][-1]['question']['id']
    doc = send(chat, doc, text='公司', reply_to_question_id=qid)
    assert doc['facts']['recipient_type']['value'] == 'company'
    assert doc['orchestration']['active_task']['id'] == task_id
    doc = send(chat, doc, text='不知道')
    assert doc['facts']['analysis_jurisdiction']['value'] == 'unknown'
    assert doc['messages'][-1]['question']['kind'] == 'choice'
    doc = send(chat, doc, text='继续补充')
    pending = deepcopy(doc['dialogue']['pending'])
    doc = send(chat, doc, text='暂停')
    doc = send(chat, doc, text='是')
    assert 'consultation_goal' not in doc['facts']
    doc = send(chat, doc, text='继续案件')
    assert doc['messages'][-1]['question']['field'] == pending['field']


def test_stale_question_and_payload_reuse_do_not_mutate(chat):
    doc = send(chat, chat.store.create('owner'), parsed(facts={'income_type': 'dividend'}))
    before = chat.store.get('owner', doc['id'])
    with pytest.raises(WorkflowError, match='question_changed'):
        send(chat, doc, text='公司', reply_to_question_id='old-question')
    assert chat.store.get('owner', doc['id']) == before
    rid = str(uuid4())
    result = chat.message('owner', doc['id'], doc['revision'], rid, '公司', True, 'auto')
    assert chat.message('owner', doc['id'], doc['revision'], rid, '公司', True, 'auto') == result
    with pytest.raises(WorkflowError, match='request_payload_conflict'):
        chat.message('owner', doc['id'], doc['revision'], rid, '公司', True, 'fact_intake')


def test_independent_query_does_not_inherit_case_date_and_filters(chat):
    doc = edit(chat, chat.store.create('owner'), {**BASE, 'accrual_date': '2024-06-01', 'income_event_status': 'occurred', 'dividend_amount': 'conflict'})
    doc = send(chat, doc, parsed('research', uses_case=False), '查香港官方指引')
    req, ctx = chat.provider.searches[-1]
    assert req.fact_filters == [] and req.applicable_date is None and req.date_status == 'not_needed'
    assert ctx.case_id is None
    assert doc['facts']['dividend_amount']['value'] == 'conflict'


def test_mixed_conflict_only_blocks_dependent_lookup(chat):
    doc = edit(chat, chat.store.create('owner'), {**BASE, 'dividend_amount': 100})
    doc = send(chat, doc, parsed('research', {'dividend_amount': 200}, uses_case=False), '金额200，另外查香港官方资料')
    assert doc['facts']['dividend_amount']['value'] == 'conflict'
    assert chat.provider.searches
    assert doc['messages'][-1]['question']['field'] == 'dividend_amount'
    assert doc['workflow']['status'] == 'waiting_user'
    calls = len(chat.provider.searches)
    doc = send(chat, doc, parsed('research', uses_case=True), '按我的情况查适用条件')
    assert len(chat.provider.searches) == calls
    assert doc['dialogue']['deferred_query']


def test_correction_saved_on_failure_and_retry_keeps_independent_scope(chat):
    doc = edit(chat, chat.store.create('owner'), {'dividend_amount': 100})
    chat.provider = RecordingProvider('MOCK-04')
    doc = send(chat, doc, parsed('research', {'dividend_amount': 200}, uses_case=False,
              corrections={'dividend_amount': '金额刚才说错了，应为200'}), '金额刚才说错了，应为200，另查香港股息规定')
    assert doc['facts']['dividend_amount']['value'] == 200
    assert doc['workflow']['status'] == 'partial_failure'
    assert doc['workflow']['error_code'] == 'knowledge_unavailable'
    chat.provider = RecordingProvider()
    doc = send(chat, doc, text='重试检索')
    assert doc['facts']['dividend_amount']['value'] == 200
    assert chat.provider.searches[0][0].fact_filters == []


def test_ordinary_chat_suspends_task_and_switching_restores(chat):
    doc = send(chat, chat.store.create('owner'), parsed(facts=BASE), entry_hint='fact_intake')
    old_id = doc['orchestration']['active_task']['id']
    doc = send(chat, doc, parsed('chat'), '你好')
    assert doc['orchestration']['active_task']['status'] == 'paused'
    doc = send(chat, doc, parsed('research', uses_case=False), '查香港官方指引')
    assert doc['orchestration']['suspended_task']['id'] == old_id
    doc = send(chat, doc, text='继续案件')
    assert doc['orchestration']['active_task']['id'] == old_id
    assert doc['messages'][-1]['question']['field'] == 'entity_hk_business_status'


@pytest.mark.parametrize('query,jurisdiction', [('新加坡税务股息', None), ('美国税率', None), ('香港股息', 'SG')])
def test_outside_provider_scope_is_not_silently_hk(chat, query, jurisdiction):
    tasks = [{'kind': 'reference_lookup', 'query': query, 'uses_case': False, 'jurisdiction': jurisdiction}]
    doc = send(chat, chat.store.create('owner'), parsed('research', query=query, tasks=tasks), query)
    assert not chat.provider.searches
    assert doc['workflow']['status'] == 'unsupported'


def test_missing_lookup_scope_asks_region_then_query_continues(chat):
    doc = send(chat, chat.store.create('owner'), parsed('research', query='股息规定'), '查股息规定')
    assert doc['messages'][-1]['question']['field'] is None and not chat.provider.searches
    doc = send(chat, doc, text='香港')
    assert len(chat.provider.searches) == 1 and not doc['facts']
    assert '股息规定' in chat.provider.searches[0][0].query


def test_two_independent_tasks_execute_with_global_budget(chat):
    tasks = [dict(kind='reference_lookup', query='香港股息收取FSIE规定', uses_case=False),
             dict(kind='reference_lookup', query='香港参股FSIE规定', uses_case=False)]
    doc = send(chat, chat.store.create('owner'), parsed('research', tasks=tasks), '查收取，再查参股规定')
    assert len(chat.provider.searches) == 2
    assert len(doc['workflow']['task_results']) == 2
    assert doc['workflow']['budget']['action'] == 2
    assert doc['orchestration']['queued_tasks'] == []


def test_no_match_dynamic_rewrite_then_finish(chat):
    class Sequence(RecordingProvider):
        def search_evidence(self, request, context):
            if not self.searches:
                self.searches.append((request, context))
                return MockKnowledgeProvider('MOCK-02').search_evidence(request, context)
            return super().search_evidence(request, context)
    chat.provider = Sequence()
    chat.dynamic_planner = True
    seen = []
    def planner(doc, observation):
        seen.append(observation)
        return {'action': 'lookup_reference', 'query': '香港FSIE境外股息官方指引'}
    chat.planner = planner
    doc = send(chat, chat.store.create('owner'), parsed('research'), '查香港股息')
    assert len(chat.provider.searches) == 2 and len(seen) == 1
    assert 'text' not in seen[0]['result']
    assert doc['workflow']['budget']['model'] == 2
    assert doc['workflow']['task_results'][-1]['reason_code'] == 'evidence_available'
    assert '没有找到匹配' not in doc['messages'][-1]['text']


@pytest.mark.parametrize('proposal', [
    {'action': 'approve', 'query': ''},
    {'action': 'lookup_reference', 'query': '美国税率'},
    {'action': 'lookup_reference', 'query': '香港股息FSIE规定'},
    {'action': 'lookup_reference', 'query': '香港股息2025'},
])
def test_planner_invalid_duplicate_scope_or_year_never_escalates(chat, proposal):
    chat.provider = RecordingProvider('MOCK-02')
    chat.dynamic_planner, chat.planner = True, lambda *_: proposal
    query = '香港股息2024' if proposal['query'].endswith('2025') else '香港股息FSIE规定'
    doc = send(chat, chat.store.create('owner'), parsed('research', query=query), query)
    assert len(chat.provider.searches) == 1
    assert doc['analyses'] == []


def test_provider_dedup_scoped_by_owner_and_nested_limits():
    original = RecordingProvider()
    budget = RunBudget(search_limit=1, evidence_limit=1)
    provider = BudgetedProvider(original, budget)
    a = SearchRequest(request_id='a', trace_id='a', query='香港股息')
    b = a.model_copy(update={'request_id': 'b', 'trace_id': 'b'})
    context = TrustedContext(owner='owner')
    result = provider.search_evidence(a, context)
    assert provider.search_evidence(b, context).request_id == 'b'
    assert len(original.searches) == 1
    with pytest.raises(BudgetExceeded):
        provider.search_evidence(b, TrustedContext(owner='another'))
    ref = result.evidence[0].reference()
    provider.get_evidence(ref, 'display', context)
    provider.get_evidence(ref, 'display', context)
    assert len(original.reads) == 1
    with pytest.raises(BudgetExceeded):
        provider.get_evidence(ref, 'model', context)


def test_display_denied_model_allowed_never_leaks_excerpt():
    provider = MockKnowledgeProvider()
    for evidence in provider.fixture['search_response']['evidence']:
        evidence['display_use'] = 'denied'
        evidence['display_ref'] = None
    bundle = retrieve(provider, SearchRequest(request_id='a', trace_id='a', query='香港股息'), TrustedContext(owner='owner'))
    answer = compose_answer(bundle)
    assert not bundle['passages']
    assert answer['claims'] == []
    assert all(e['text'] not in answer['text'] for e in bundle['model_evidence'])


def test_display_only_material_never_in_planner_or_history(chat):
    chat.provider = RecordingProvider('MOCK-03')
    chat.dynamic_planner = True
    chat.planner = lambda *_: pytest.fail('Restricted evidence must not cause planner retry')
    doc = send(chat, chat.store.create('owner'), parsed('research'), '查香港股息')
    _, prompt = turn_prompt(doc, '继续')
    for passage in doc['messages'][-1]['research']['passages']:
        assert passage['text'] not in prompt


def test_prepare_analysis_never_confirms_and_partial_gate_is_shared(chat):
    doc = edit(chat, chat.store.create('owner'), BASE)
    doc = send(chat, doc, parsed(), '开始分析')
    assert doc['confirmed_revision'] is None and not doc['analyses']
    assert doc['workflow']['reason_code'] == 'confirmation_required'
    doc = chat.confirm('owner', doc['id'], doc['revision'], str(uuid4()))
    doc = send(chat, doc, parsed(), '开始分析')
    assert doc['workflow']['reason_code'] == analysis_eligibility(doc) == 'partial_confirmation_required'
    doc = send(chat, doc, text='先看部分整理')
    doc = chat.confirm('owner', doc['id'], doc['revision'], str(uuid4()))
    doc = send(chat, doc, parsed(), '开始分析')
    assert len(doc['analyses']) == 1
    assert doc['analyses'][0]['review']['status'] == 'pending_final_review'
    assert doc['analyses'][0]['evidence_gate'] == 'insufficient'
    assert doc['state'] == 'review_required'


def test_failed_pure_retrieval_does_not_write_or_fallback(chat):
    chat.provider = RecordingProvider('MOCK-04')
    doc = chat.store.create('owner')
    with pytest.raises(WorkflowError, match='knowledge_unavailable'):
        send(chat, doc, parsed('research'), '查香港股息')
    assert chat.store.get('owner', doc['id']) == doc


def test_same_request_and_new_mode_old_case_compatibility(chat):
    doc = chat.store.create('owner')
    assert 'orchestration' not in doc
    doc = send(chat, doc, parsed(facts=BASE))
    assert doc['orchestration']['active_task']
    old_facts = deepcopy(doc['facts'])
    chat.orchestration = 'legacy'
    doc = send(chat, doc, parsed('chat'), '你好')
    assert doc['facts'] == old_facts


def test_json_and_sse_use_same_hint_question_and_payload(chat):
    from apps.api.main import app
    from apps.api.auth import optional_user
    from apps.api.chat import get_service
    app.dependency_overrides[optional_user] = lambda: {'id': 'fixture', 'email': 'fixture@example.invalid'}
    app.dependency_overrides[get_service] = lambda: chat
    try:
        with TestClient(app) as client:
            headers = {'x-asiatax-request': '1'}
            a = client.post('/api/cases', headers=headers).json()
            b = client.post('/api/cases', headers=headers).json()
            chat.turner = lambda *_: parsed(facts=BASE)
            def body(doc):
                return {'text': '我的案件', 'revision': doc['revision'], 'request_id': str(uuid4()),
                        'data_approved': True, 'entry_hint': 'fact_intake'}
            payload = body(a)
            resp = client.post(f"/api/cases/{a['id']}/messages", headers={**headers, 'accept': 'text/event-stream'}, json=payload)
            events = [json.loads(line[6:]) for line in resp.text.splitlines() if line.startswith('data: ')]
            result = events[-1]['case']
            other = client.post(f"/api/cases/{b['id']}/messages", headers=headers, json=body(b)).json()
            assert result['workflow']['effective_task'] == other['workflow']['effective_task'] == 'fact_intake'
            assert result['messages'][-1]['question']['field'] == other['messages'][-1]['question']['field']
            bad = client.post(f"/api/cases/{a['id']}/messages", headers=headers, json={**payload, 'entry_hint': 'auto'})
            assert bad.status_code == 409 and bad.json()['detail'] == 'request_payload_conflict'
    finally:
        app.dependency_overrides.clear()


@pytest.mark.parametrize('facts', [
    {'recipient_type': 'individual'}, {'income_type': 'interest'}, {'analysis_jurisdiction': 'SG'}])
def test_unsupported_case_never_runs_rules_or_lookup(chat, facts):
    doc = send(chat, chat.store.create('owner'), parsed(facts=facts))
    assert doc['workflow']['status'] == 'unsupported'
    assert doc['analyses'] == [] and chat.provider.searches == []


def test_new_transaction_does_not_overwrite_current_case(chat):
    doc = send(chat, chat.store.create('owner'), parsed(facts=BASE))
    previous = deepcopy(doc['facts'])
    doc = send(chat, doc, parsed(facts={'dividend_amount': 99}, action='new_case'), '另一个客户')
    assert doc['facts'] == previous
    assert '新对话' in doc['messages'][-1]['text']


def test_unknown_conflict_and_unavailable_keep_distinct_states(chat):
    doc = edit(chat, chat.store.create('owner'), {'dividend_amount': 100})
    doc = send(chat, doc, parsed(facts={'dividend_amount': 200}), '金额200')
    doc = send(chat, doc, text='不知道')
    assert doc['facts']['dividend_amount']['value'] == 'conflict'
    assert doc['fact_conflicts']['dividend_amount'] == {'previous': 100, 'candidate': 200}
    doc = send(chat, doc, text='继续补充')
    doc = send(chat, doc, text='暂时没有资料')
    assert doc['facts']['dividend_amount']['value'] == 'conflict'


def test_partial_consent_cannot_be_created_by_task_or_model_guess(chat):
    doc = send(chat, chat.store.create('owner'), parsed(facts=BASE))
    doc = send(chat, doc, parsed(action='partial'), '谢谢')
    assert 'partial_consent' not in doc['dialogue']
    doc = send(chat, doc, text='先看部分整理')
    assert doc['dialogue']['partial_consent']
    doc = send(chat, doc, parsed(facts={'dividend_amount': 100}), '金额100')
    assert 'partial_consent' not in doc['dialogue']


def test_repeated_question_choice_without_infinite_loop(chat):
    doc = send(chat, chat.store.create('owner'), parsed(facts={'income_type': 'dividend'}))
    doc = send(chat, doc, parsed(), '没有回答这个问题')
    assert doc['messages'][-1]['question']['attempt'] == 2
    doc = send(chat, doc, parsed(), '仍然没有回答')
    assert doc['messages'][-1]['question']['kind'] == 'choice'
    assert doc['workflow']['budget']['model'] == 1


def test_non_cash_planned_case_uses_existing_field_rules(chat):
    doc = send(chat, chat.store.create('owner'), parsed(facts={**BASE, 'consultation_goal': 'receipt',
        'dividend_form': 'in_kind', 'income_event_status': 'planned'}))
    from packages.agent.dialogue import required_fields
    fields = required_fields(doc)
    assert 'transaction_flow_description' in fields and 'bank_or_account_path' not in fields
    assert 'receipt_date' not in fields


def test_full_fact_patch_is_written_once_and_concurrent_update_rejected(chat):
    doc = chat.store.create('owner')
    prepared = chat.prepare_turn('owner', doc, 'first', '我的案情', parsed(facts=BASE))
    updated = edit(chat, doc, {'dividend_amount': 5})
    with pytest.raises(RevisionConflict):
        chat.commit_prepared('owner', doc, 0, 'first', '我的案情', prepared)
    assert chat.store.get('owner', doc['id'])['facts'] == updated['facts']


def test_initial_invalid_model_turn_has_no_side_effect(chat):
    chat.turner = lambda *_: {'intent': 'chat', 'facts': {'dividend_amount': 5}, 'reply': 'x', 'query': ''}
    doc = chat.store.create('owner')
    with pytest.raises(WorkflowError, match='model_failed'):
        send(chat, doc)
    assert chat.store.get('owner', doc['id']) == doc


def test_budget_zero_cannot_call_model_or_commit(chat, monkeypatch):
    from packages.agent import hybrid
    monkeypatch.setattr(hybrid, 'RunBudget', lambda: RunBudget(seconds=0))
    chat.turner = lambda *_: pytest.fail('No budget to call model')
    doc = chat.store.create('owner')
    with pytest.raises(WorkflowError, match='execution_budget_exhausted'):
        send(chat, doc)
    assert chat.store.get('owner', doc['id']) == doc


def test_action_budget_caps_nested_queue_and_preserves_unfinished_task(chat, monkeypatch):
    from packages.agent import hybrid
    monkeypatch.setattr(hybrid, 'RunBudget', lambda: RunBudget(action_limit=1))
    tasks = [dict(kind='reference_lookup', query='香港股息收取', uses_case=False),
             dict(kind='reference_lookup', query='香港股息参股', uses_case=False)]
    doc = send(chat, chat.store.create('owner'), parsed('research', tasks=tasks), '查收取和参股')
    assert len(chat.provider.searches) == 1
    assert doc['workflow']['pending_tasks'] == 1
    assert len(doc['orchestration']['queued_tasks']) == 1
    assert '未完成' in doc['messages'][-1]['text']


def test_model_budget_already_used_ends_with_verified_result(chat, monkeypatch):
    from packages.agent import hybrid
    monkeypatch.setattr(hybrid, 'RunBudget', lambda: RunBudget(model_limit=1))
    chat.provider = RecordingProvider('MOCK-02')
    chat.dynamic_planner = True
    chat.planner = lambda *_: pytest.fail('Budget forbids planner')
    doc = send(chat, chat.store.create('owner'), parsed('research'), '查香港股息')
    assert len(chat.provider.searches) == 1
    assert doc['workflow']['status'] == 'partial_failure'
    assert '部分查询还未完成' in doc['messages'][-1]['text']


def test_model_planner_receives_only_safe_metadata_even_after_display_history(chat):
    doc = chat.store.create('owner')
    doc['messages'] = [{'role': 'assistant', 'kind': 'research', 'text': 'DISPLAY_SENTINEL',
                        'research': {'query': '香港股息', 'status': 'available',
                                     'passages': [{'text': 'DISPLAY_SENTINEL'}]}}]
    chat.store.save('owner', doc, 0)
    doc = chat.store.get('owner', doc['id'])
    chat.provider = RecordingProvider('MOCK-02')
    chat.dynamic_planner = True
    def planner(safe_doc, observation):
        assert 'DISPLAY_SENTINEL' not in json.dumps([safe_doc, observation])
        return {'action': 'finish', 'query': ''}
    chat.planner = planner
    send(chat, doc, parsed('research'), '查香港股息')


def test_provider_transport_retry_and_rewrite_share_total_call_limit(chat):
    class Flaky(RecordingProvider):
        def search_evidence(self, request, context):
            self.searches.append((request, context))
            scenario = 'MOCK-04' if len(self.searches) == 1 else 'MOCK-02'
            return MockKnowledgeProvider(scenario).search_evidence(request, context)
    chat.provider = Flaky()
    chat.dynamic_planner = True
    chat.planner = lambda *_: {'action': 'lookup_reference', 'query': '香港FSIE官方股息指引'}
    doc = send(chat, chat.store.create('owner'), parsed('research'), '查香港股息')
    assert len(chat.provider.searches) == 3
    assert doc['workflow']['budget']['search'] == 3


def test_fail_second_task_keeps_first_result_and_clear_failure(chat):
    class Flaky(RecordingProvider):
        def search_evidence(self, request, context):
            if self.searches:
                self.searches.append((request, context))
                return MockKnowledgeProvider('MOCK-04').search_evidence(request, context)
            return super().search_evidence(request, context)
    chat.provider = Flaky()
    tasks = [dict(kind='reference_lookup', query='香港股息收取', uses_case=False),
             dict(kind='reference_lookup', query='香港股息参股', uses_case=False)]
    doc = send(chat, chat.store.create('owner'), parsed('research', tasks=tasks), '查两项规定')
    assert doc['workflow']['status'] == 'partial_failure'
    assert len(doc['messages'][-1]['research_results']) == 2
    assert doc['workflow']['task_results'][0]['reason_code'] == 'evidence_available'
    assert doc['workflow']['task_results'][1]['reason_code'] == 'retrieval_failed'


def test_task_queue_max_three_not_silently_truncated(chat):
    doc = chat.store.create('owner')
    tasks = [dict(kind='reference_lookup', query='香港股息', uses_case=False)] * 4
    with pytest.raises(WorkflowError, match='model_failed'):
        send(chat, doc, parsed('research', tasks=tasks))
    assert chat.store.get('owner', doc['id']) == doc


def test_third_persistent_task_requires_focus_instead_of_losing_suspended_task(chat):
    doc = send(chat, chat.store.create('owner'), parsed(facts=BASE), entry_hint='fact_intake')
    doc = send(chat, doc, parsed('research', query='股息规定'), '查股息规定')
    previous = chat.store.get('owner', doc['id'])
    with pytest.raises(WorkflowError, match='task_focus_required'):
        send(chat, doc, parsed(task_kind='consultation'), '分析我自己的情况')
    assert chat.store.get('owner', doc['id']) == previous


def test_queued_query_resumes_after_budget_stop(chat, monkeypatch):
    from packages.agent import hybrid
    original_budget = hybrid.RunBudget
    monkeypatch.setattr(hybrid, 'RunBudget', lambda: RunBudget(action_limit=1))
    tasks = [dict(kind='reference_lookup', query='香港股息收取', uses_case=False),
             dict(kind='reference_lookup', query='香港股息参股', uses_case=False)]
    doc = send(chat, chat.store.create('owner'), parsed('research', tasks=tasks), '查两项规定')
    monkeypatch.setattr(hybrid, 'RunBudget', original_budget)
    doc = send(chat, doc, text='继续案件')
    assert len(chat.provider.searches) == 2
    assert chat.provider.searches[-1][0].query == '香港股息参股'
    assert doc['orchestration']['queued_tasks'] == []
    assert doc['facts'] == {}


def test_rewrite_of_second_task_does_not_drop_first_reply(chat):
    class Sequence(RecordingProvider):
        def search_evidence(self, request, context):
            if len(self.searches) == 1:
                self.searches.append((request, context))
                return MockKnowledgeProvider('MOCK-02').search_evidence(request, context)
            return super().search_evidence(request, context)
    chat.provider = Sequence()
    chat.dynamic_planner = True
    chat.planner = lambda *_: {'action': 'lookup_reference', 'query': '香港股息参股FSIE官方指引'}
    tasks = [dict(kind='reference_lookup', query='香港股息收取', uses_case=False),
             dict(kind='reference_lookup', query='香港股息参股', uses_case=False)]
    doc = send(chat, chat.store.create('owner'), parsed('research', tasks=tasks), '查收取和参股')
    assert len(chat.provider.searches) == 3
    assert doc['messages'][-1]['text'].count('模拟联调资料，不是真实税务依据') == 1
    assert len(doc['messages'][-1]['research_results']) == 3
    assert len(doc['messages'][-1]['research_results']) == 3


@pytest.mark.parametrize('old,new', [
    ('香港股息2024年6月', '香港股息2024年8月'),
    ('香港股息2024-06-01', '香港股息2024-08-01'),
    ('香港股息', '香港股息2026'),
    ('香港Case 68', '香港Case 69'),
])
def test_rewrite_cannot_change_period_or_reference(old, new):
    from packages.agent.policy import rewrite_preserves_scope
    assert not rewrite_preserves_scope(old, new)


def test_rollback_does_not_bind_yes_to_hybrid_scope_question(chat):
    doc = send(chat, chat.store.create('owner'), parsed('research', query='股息规定'), '查股息规定')
    chat.orchestration = 'legacy'
    doc = send(chat, doc, text='是')
    assert doc['facts'] == {}
    assert '暂停保留' in doc['messages'][-1]['text']
    chat.orchestration = 'hybrid'
    doc = send(chat, doc, text='继续案件')
    assert doc['orchestration']['active_task']['kind'] == 'reference_lookup'
    assert '哪个地区' in doc['messages'][-1]['text']
    assert doc['facts'] == {}


def test_chat_misclassification_cannot_output_concrete_tax_claim(chat):
    doc = send(chat, chat.store.create('owner'), parsed('chat', reply='香港股息税率为0%，可以免税。'), '香港股息税率是什么')
    assert chat.provider.searches
    assert '股息税率为0%' not in doc['messages'][-1]['text']


def test_chat_cannot_claim_report_approval(chat):
    doc = send(chat, chat.store.create('owner'), parsed('chat', reply='报告已批准。'), '批准一下')
    assert not doc['analyses'] and '须由有权限的顾问' in doc['messages'][-1]['text']
