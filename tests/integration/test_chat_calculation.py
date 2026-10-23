"""Chat calculation uses real engine results and the normal atomic chat commit."""
import asyncio
from copy import deepcopy
from uuid import uuid4

import pytest

from packages.chat.service import ChatService, validate_turn, WorkflowError
from packages.chat.store import ChatStore
from packages.domain_bridge.bridge import release_path, DomainError
from packages.domain_bridge.chat_calculation import FIELDS
from packages.agent.providers import MockKnowledgeProvider

OWNER = 'user:calculation-test'
TEXT = '香港公司直接持有中国公司100%股份，取得日2020-01-01，股本融资。这笔股息人民币100万元，拟2026-10-11支付，未支付。请计算税额。'
VALUES = {'recipient_type': ('company', '香港公司'), 'payer': ('CN', '中国公司'), 'recipient': ('HK', '香港公司'), 'income': ('dividend', '股息'),
          'direct': (True, '直接持有'), 'amount': (1000000, '人民币100万元'), 'currency': ('CNY', '人民币'),
          'ratio': (100, '100%'), 'since': ('2020-01-01', '2020-01-01'), 'on': ('2026-10-11', '2026-10-11'),
}


def turn(values=None, **kw):
    return {'intent': 'calculation', 'facts': {}, 'query': '', 'reply': '准备计算。',
            'calculation': {'inputs': {k: {'value': v, 'quote': q} for k, (v, q) in (values or {}).items()}, **kw}}


@pytest.fixture
def service(tmp_path):
    store = ChatStore('sqlite:///' + str(tmp_path / 'chat.sqlite'))
    svc = ChatService(store, turner=lambda doc, text: turn(VALUES), provider=MockKnowledgeProvider(),
                      orchestration='hybrid', dynamic_planner=True, harness_mode='tools',
                      tool_planner=lambda doc, observation: {'tool': 'calculate_tax'})
    yield svc
    store.engine.dispose()


@pytest.fixture
def engine():
    try:
        return release_path()
    except DomainError:
        pytest.skip('Pinned tax engine release is required')


def send(svc, doc, text=TEXT):
    return svc.message(OWNER, doc['id'], doc['revision'], str(uuid4()), text, True)


def test_real_engine_runs_from_chat_and_duplicate_does_not_recalculate(service, engine):
    doc = service.store.create(OWNER)
    req = str(uuid4())
    result = service.message(OWNER, doc['id'], 0, req, TEXT, True)
    assert result['revision'] == 1
    assert len(result['integration_runs']) == 1
    assert result['domain_outcome']['mode'] == 'assess_current'
    assert result['domain_case']['event']['dividend'] == 1000000
    assert result['domain_case']['holds'][0]['ratio'] == 100
    reply = result['messages'][-1]['text']
    assert '试算区间' in reply
    assert '### 1. 税额试算结果' in reply
    assert '### 2. 区间由哪些金额组成' in reply
    assert '### 5. 集中补充案例信息' in reply
    assert '提交后统一更新试算' in reply
    assert '**下一项' not in reply
    assert result['workflow']['tool_calls'][0]['tool'] == 'calculate_tax'
    assert result['domain_confirmation'] is None
    assert all(r['confirmed_at'] is None for r in result['canonical_fact_records'].values())
    duplicate = service.message(OWNER, doc['id'], 0, req, TEXT, True)
    assert duplicate['revision'] == 1 and len(duplicate['integration_runs']) == 1
    with pytest.raises(WorkflowError):
        service.message(OWNER, doc['id'], 0, req, '换一个金额', True)


def test_missing_inputs_are_collected_across_turns(service, engine):
    doc = service.store.create(OWNER)
    service.turner = lambda *_: turn({'amount': VALUES['amount']})
    first = send(service, doc)
    assert not first.get('integration_runs')
    assert '完整日期' in first['messages'][-1]['text']
    service.turner = lambda *_: turn({k: v for k, v in VALUES.items() if k != 'amount'})
    final = send(service, first)
    assert len(final['integration_runs']) == 1


def test_unquoted_or_invented_dates_never_execute(service):
    doc = service.store.create(OWNER)
    values = {**VALUES, 'since': ('2020-01-01', '2020')}
    service.turner = lambda *_: turn(values)
    result = send(service, doc)
    assert not result.get('integration_runs')
    assert 'since' not in result['calculation_context']['inputs']


def test_saved_structure_uses_its_exact_case_and_mode(service, engine):
    first = send(service, service.store.create(OWNER))
    service.turner = lambda *_: turn(use_saved_case=True)
    second = send(service, first, '按保存的结构再计算一次')
    assert second['domain_case'] == first['domain_case']
    assert len(second['integration_runs']) == 2


def test_engine_answer_in_chat_recalculates_without_side_panel(service, engine):
    first = send(service, service.store.create(OWNER))
    from packages.domain_bridge.chat_calculation import current_question
    q = current_question(first)
    assert q
    schema = q['answer_schema']['type']
    value, raw = (True, '是') if schema == 'boolean' else (1, '1') if schema == 'number' else ('2020-01-01', '2020-01-01') if schema == 'date' else ('测试信息', '测试信息')
    service.turner = lambda *_: turn(action='answer', answer={'value': value, 'quote': raw})
    second = send(service, first, raw)
    assert second['revision'] == first['revision'] + 1
    assert len(second['integration_runs']) == 2
    assert second['workflow']['tool_calls'][0]['reason_code'] == 'answer_and_recalculate'


def test_corrected_amount_recomputes_and_invalidates_previous_confirmation(service, engine):
    first = send(service, service.store.create(OWNER))
    service.turner = lambda *_: turn({'amount': (2000000, '200万元')})
    second = send(service, first, '股息金额改成200万元，重新计算')
    assert second['domain_case']['event']['dividend'] == 2000000
    assert second['facts']['dividend_amount']['value'] == 2000000
    assert second['domain_outcome']['input_hash'] != first['domain_outcome']['input_hash']
    assert second['domain_confirmation'] is None


def test_sse_disconnect_does_not_commit_prepared_calculation(service, engine):
    from packages.chat.streaming import events
    doc = service.store.create(OWNER)
    calls = 0
    async def disconnected():
        nonlocal calls
        calls += 1
        return calls >= 2
    async def run():
        return [event async for event in events(service, doc, OWNER, 0, str(uuid4()), TEXT, disconnected)]
    assert asyncio.run(run()) == []
    stored = service.store.get(OWNER, doc['id'])
    assert stored['revision'] == 0 and not stored.get('integration_runs')


def test_no_calculation_for_tool_finish_or_personal_other_income(service):
    doc = service.store.create(OWNER)
    service.tool_planner = lambda *_: {'tool': 'finish'}
    result = send(service, doc)
    assert not result.get('integration_runs')
    service.turner = lambda *_: turn({'income': ('other', '售股')})
    result = send(service, result, '我要计算售股的税')
    assert not result.get('integration_runs')


def test_model_cannot_inject_extra_execution_fields():
    bad = turn(VALUES)
    bad['calculation']['owner'] = 'another user'
    with pytest.raises(ValueError):
        validate_turn(bad)


def test_unsupported_currency_never_becomes_cny(service, engine):
    service.turner = lambda *_: turn({**VALUES, 'currency': ('HKD', '港币'), 'amount': (1000000, '港币100万元')})
    result = send(service, service.store.create(OWNER), TEXT.replace('人民币', '港币'))
    assert result['domain_case']['currency'] == 'HKD'
    assert result['domain_outcome']['status'] == 'unsupported'
    assert '没有计算税额' in result['messages'][-1]['text']
    assert 'upper' not in result['domain_outcome']


def test_engine_failure_is_atomic_and_does_not_save_a_fabricated_answer(service, monkeypatch):
    from packages.domain_bridge import coordinator
    monkeypatch.setattr(coordinator, 'run_domain', lambda *a, **kw: (_ for _ in ()).throw(DomainError('domain_execution_failed')))
    doc = service.store.create(OWNER)
    with pytest.raises(WorkflowError, match='domain_execution_failed'):
        send(service, doc)
    assert service.store.get(OWNER, doc['id'])['revision'] == 0


def test_interleaved_panel_edits_are_not_overwritten_by_old_chat_draft(service, engine):
    first = send(service, service.store.create(OWNER))
    case = deepcopy(first['domain_case'])
    case['event']['dividend'] = 3000000
    panel = service.domain_setup(OWNER, first['id'], first['revision'], str(uuid4()), case, True, 'assess_current')
    service.turner = lambda *_: turn({'amount': (2000000, '200万元')})
    result = send(service, panel, '改成200万元，算一下')
    assert result['domain_case']['event']['dividend'] == 3000000
    assert '避免覆盖' in result['messages'][-1]['text']


def test_other_users_cannot_calculate_this_case(service):
    from packages.chat.store import CaseNotFound
    doc = service.store.create(OWNER)
    with pytest.raises(CaseNotFound):
        service.message('user:other', doc['id'], 0, str(uuid4()), TEXT, True)


def test_personal_and_multiple_transactions_do_not_run_even_if_model_misroutes(service):
    for text in [TEXT + '但是我是个人投资者', TEXT + '还有两笔股息分别计算']:
        result = send(service, service.store.create(OWNER), text)
        assert not result.get('integration_runs')
        assert result['calculation_context']['inputs'] == {}


def test_http_sse_displays_engine_result_and_preserves_revision_guard(service, engine):
    import json
    from fastapi.testclient import TestClient
    from apps.api.main import app
    from apps.api.auth import optional_user
    from apps.api.chat import get_service
    app.dependency_overrides[optional_user] = lambda: {'id': '11111111-1111-1111-1111-111111111111', 'email': 'test@example.invalid'}
    app.dependency_overrides[get_service] = lambda: service
    headers = {'X-AsiaTax-Request': '1', 'Accept': 'text/event-stream'}
    try:
        with TestClient(app) as client:
            doc = client.post('/api/cases', headers=headers).json()
            body = {'revision': 0, 'request_id': str(uuid4()), 'text': TEXT, 'data_approved': True}
            response = client.post(f"/api/cases/{doc['id']}/messages", headers=headers, json=body)
            events = [json.loads(line[6:]) for line in response.text.splitlines() if line.startswith('data: ')]
            final = next(event['case'] for event in events if event['type'] == 'done')
            assert final['revision'] == 1 and final['domain_outcome']['upper']
            assert '试算区间' in final['messages'][-1]['text']
            assert len(final['integration_runs']) == 1
            body['request_id'] = str(uuid4())
            stale = client.post(f"/api/cases/{doc['id']}/messages", headers={'X-AsiaTax-Request': '1'}, json=body)
            assert stale.status_code == 409
    finally:
        app.dependency_overrides.clear()


def test_paid_dividend_and_shareholder_debt_do_not_shift_date_or_change_income(service, engine):
    # Worker payment means a one-year delay; financing chooses the income type.
    # Neither may be inferred from 'already paid' or the shareholder's loan.
    text = TEXT.replace('股本融资', '借款融资').replace('拟2026-10-11支付，未支付', '已于2026-10-11支付')
    result = send(service, service.store.create(OWNER), text)
    flow = result['domain_outcome']['structure']['flows'][0]
    assert flow[1] == 'DIVIDEND' and flow[5] == '2026-10-11'


def test_amount_only_correction_preserves_explicit_engine_answers(service, engine):
    first = send(service, service.store.create(OWNER))
    from packages.domain_bridge.chat_calculation import current_question
    q = current_question(first)
    schema = q['answer_schema']['type']
    value, raw = (False, '否') if schema == 'boolean' else (1, '1') if schema == 'number' else ('2020-01-01', '2020-01-01') if schema == 'date' else ('测试信息', '测试信息')
    service.turner = lambda *_: turn(action='answer', answer={'value': value, 'quote': raw})
    second = send(service, first, raw)
    service.turner = lambda *_: turn({'amount': (2000000, '200万元')})
    third = send(service, second, '改成200万元，重新计算')
    assert third['canonical_fact_records'][q['key']]['value'] == value
    assert third['domain_case']['event']['dividend'] == 2000000


def test_correction_that_needs_more_input_marks_old_result_stale(service, engine):
    first = send(service, service.store.create(OWNER))
    service.turner = lambda *_: turn({'on': ('2027-01-01', '2027')})
    second = send(service, first, '改为2027年支付')
    assert second['domain_outcome']['stale']
    assert len(second['integration_runs']) == 1


def test_invalid_sequence_and_negative_amount_do_not_execute(service):
    for vals, text in [({**VALUES, 'amount': (1000000, '-1000000')}, TEXT + ' -1000000'),
                       ({**VALUES, 'since': ('2027-01-01', '2027-01-01')}, TEXT + ' 2027-01-01')]:
        service.turner = lambda *_, vals=vals: turn(vals)
        result = send(service, service.store.create(OWNER), text)
        assert not result.get('integration_runs')


def test_existing_case_facts_are_reused_but_legal_jurisdiction_is_not_recipient_location(service, engine):
    doc = service.store.create(OWNER)
    fields = {'payer_jurisdiction': 'CN', 'income_type': 'dividend', 'recipient_type': 'company',
              'direct_or_indirect_holding': 'direct', 'dividend_amount': 1000000, 'dividend_currency': 'CNY',
              'holding_percentage_pct': 100, 'acquisition_date': '2020-01-01', 'receipt_date': '2026-10-11',
              'analysis_jurisdiction': 'HK'}
    doc = service.edit(OWNER, doc['id'], 0, str(uuid4()), fields)
    service.turner = lambda *_: turn()
    first = send(service, doc, '请计算这笔股息税额')
    assert not first.get('integration_runs')
    assert 'recipient' not in first['calculation_context']['inputs']
    assert first['calculation_context']['inputs']['amount']['value'] == 1000000
    service.turner = lambda *_: turn({'recipient': ('HK', '香港公司')})
    second = send(service, first, '收款方是香港公司')
    assert len(second['integration_runs']) == 1


def test_two_companies_do_not_imply_multiple_transactions(service, engine):
    result = send(service, service.store.create(OWNER), TEXT + '以上两家公司只有这一笔股息。')
    assert len(result['integration_runs']) == 1

@pytest.mark.parametrize('value,raw', [(False, '否'), ('unknown', '未知'), (True, '是')])
def test_reinvestment_followups_require_explicit_applicability(service, engine, value, raw):
    from packages.domain_bridge.chat_calculation import current_question
    from packages.domain_bridge.question_order import REINVESTMENT_DETAILS
    first = send(service, service.store.create(OWNER))
    assert current_question(first)['key'] == 'flow:up1.reinvested_in_cn'
    service.turner = lambda *_: turn(action='answer', answer={'value': value, 'quote': raw})
    second = send(service, first, raw)
    assert second['canonical_fact_records']['flow:up1.reinvested_in_cn']['value'] == value
    pending = current_question(second)
    if value is not True and pending:
        assert pending['key'].rsplit('.', 1)[-1] not in REINVESTMENT_DETAILS
    assert len(second['integration_runs']) == 2


def test_recalculating_same_case_preserves_interview_and_defer_memory(service, engine):
    from packages.domain_bridge.question_order import interview_context
    from packages.domain_bridge.chat_calculation import current_question
    first = send(service, service.store.create(OWNER))
    pending = current_question(first)
    deferred = service.domain_answer(OWNER, first['id'], first['revision'], str(uuid4()),
                                    pending['key'], pending['kind'], None, pending['id'], disposition='defer')
    assert deferred['domain_deferred'][pending['key']]['context'] == interview_context(deferred)
    service.turner = lambda *_: turn(VALUES)
    repeated = send(service, deferred)
    assert repeated['domain_deferred'] == deferred['domain_deferred']
    assert current_question(repeated)['key'] != pending['key']


def batch_items(doc):
    return [{'key': q['key'], 'kind': q['kind'], 'question_id': q['id'], 'value': 'unknown'}
            for q in doc['domain_outcome']['questions']
            if q.get('interview_status') == 'ready' and q['kind'] in ('data', 'blocking', 'joint')]


def test_batch_answers_commit_once_and_recalculate_once(service, engine):
    doc = send(service, service.store.create(OWNER))
    items = batch_items(doc)
    assert len(items) > 1
    request_id = str(uuid4())
    result = service.domain_answers_batch(OWNER, doc['id'], doc['revision'], request_id, items)
    assert result['revision'] == doc['revision'] + 1
    assert len(result['integration_runs']) == len(doc['integration_runs']) + 1
    assert len(result['messages']) == len(doc['messages']) + 1
    assert service.domain_answers_batch(OWNER, doc['id'], doc['revision'], request_id, items)['revision'] == result['revision']
    for item in items:
        if item['key'].startswith('interview:'):
            assert result['domain_interview'][item['key']]['value'] == 'unknown'
        else:
            assert result['canonical_fact_records'][item['key']]['value'] == 'unknown'


@pytest.mark.parametrize('failure', ['stale_question', 'invalid_value'])
def test_invalid_batch_rolls_back_all_answers(service, engine, failure):
    doc = send(service, service.store.create(OWNER))
    items = batch_items(doc)
    if failure == 'stale_question':
        items[-1]['question_id'] = 'invalid'
    else:
        boolean = next(q for q in doc['domain_outcome']['questions'] if q.get('answer_schema', {}).get('type') == 'boolean' and any(i['question_id'] == q['id'] for i in items))
        item = next(i for i in items if i['question_id'] == boolean['id'])
        items.remove(item)
        items.append({**item, 'value': 'not a boolean'})
    with pytest.raises(WorkflowError):
        service.domain_answers_batch(OWNER, doc['id'], doc['revision'], str(uuid4()), items)
    saved = service.store.get(OWNER, doc['id'])
    assert saved['revision'] == doc['revision']
    assert saved['canonical_fact_records'] == doc['canonical_fact_records']
    assert saved.get('domain_interview') == doc.get('domain_interview')


def test_batch_rejects_hidden_dependent_question(service, engine):
    doc = send(service, service.store.create(OWNER))
    hidden = next(q for q in doc['domain_outcome']['questions'] if q.get('interview_status') == 'waiting')
    with pytest.raises(WorkflowError):
        service.domain_answers_batch(OWNER, doc['id'], doc['revision'], str(uuid4()), [
            {'key': hidden['key'], 'kind': hidden['kind'], 'question_id': hidden['id'], 'value': 'yes'}])


def attached(text, request='请根据附件计算税额'):
    import json
    from packages.chat.attachments import MARKER
    return request + MARKER + json.dumps({'name': 'case.pdf', 'pages': [{'page': 1, 'text': text}]}, ensure_ascii=False)


def test_new_attachment_retries_wrong_answer_route_without_old_question(service, engine):
    first = send(service, service.store.create(OWNER))
    seen = []
    def router(doc, text):
        from packages.domain_bridge.chat_calculation import current_question
        seen.append(current_question(doc))
        return turn(action='answer') if len(seen) == 1 else turn(VALUES)
    service.turner = router
    result = send(service, first, attached(TEXT))
    assert seen == [None, None]
    assert len(result['integration_runs']) == 2
    assert '试算区间' in result['messages'][-1]['text']


def test_new_attachment_does_not_fill_missing_values_from_old_case(service, engine):
    first = send(service, service.store.create(OWNER))
    service.turner = lambda *_: turn({'amount': VALUES['amount']})
    result = send(service, first, attached('人民币100万元'))
    assert len(result['integration_runs']) == 1
    assert '完整日期' in result['messages'][-1]['text']
    assert result['domain_case'] == first['domain_case']


def test_conflicting_attachment_does_not_replace_saved_case(service, engine):
    first = send(service, service.store.create(OWNER))
    values = {**VALUES, 'amount': (2000000, '人民币200万元')}
    service.turner = lambda *_: turn(values)
    result = send(service, first, attached(TEXT.replace('人民币100万元', '人民币200万元')))
    assert len(result['integration_runs']) == 1
    assert '不一致' in result['messages'][-1]['text']
    assert result['canonical_fact_records'] == first['canonical_fact_records']
    assert result['calculation_context']['inputs'] == first['calculation_context']['inputs']


def test_attachment_summary_does_not_answer_old_question(service, engine):
    first = send(service, service.store.create(OWNER))
    service.turner = lambda *_: {'intent': 'chat', 'facts': {}, 'query': '', 'reply': '这是股息资料摘要。'}
    result = send(service, first, attached(TEXT, '只总结附件，先不计算'))
    assert result['messages'][-1]['text'] == '这是股息资料摘要。'
    assert len(result['integration_runs']) == 1


def test_attachment_source_quotes_can_span_newlines():
    from packages.chat.attachments import attachment_source
    from packages.domain_bridge.chat_calculation import InputFact, supported_value
    source = attachment_source(attached('香港公司\n直接持有100%股份'))
    assert supported_value('direct', InputFact(value=True, quote='香港公司\n直接持有'), source)
