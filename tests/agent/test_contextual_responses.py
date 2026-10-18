from copy import deepcopy
from uuid import uuid4

import pytest

from packages.agent.contracts import SearchRequest, TrustedContext
from packages.agent.knowledge import retrieve, compose_answer, validate_answer, append_followup
from packages.agent.providers import MockKnowledgeProvider
from packages.chat.service import ChatService
from packages.chat.store import ChatStore
from packages.chat.knowledge import topic_locators


def turn(facts=None, **kwargs):
    return {'intent': 'intake', 'facts': facts or {}, 'query': '', 'reply': 'received', **kwargs}


@pytest.mark.parametrize('orchestration', ['legacy', 'hybrid'])
@pytest.mark.parametrize('locale', ['zh', 'en'])
@pytest.mark.parametrize('facts,label', [({'recipient_type': 'individual'}, '个人'),
                                       ({'income_type': 'interest'}, '利息'),
                                       ({'analysis_jurisdiction': 'JP'}, 'JP')])
def test_boundary_explains_actual_fact_and_can_resume_as_reference(tmp_path, orchestration, locale, facts, label):
    store = ChatStore(f'sqlite:///{tmp_path}/case.sqlite')
    service = ChatService(store, provider=MockKnowledgeProvider(), orchestration=orchestration,
                          turner=lambda *_: turn(facts))
    try:
        doc = store.create('owner')
        doc = service.message('owner', doc['id'], doc['revision'], str(uuid4()), label, True, locale=locale)
        message = doc['messages'][-1]
        assert doc['workflow']['reason_code'] == 'out_of_scope'
        assert not doc['analyses'] and 'research' not in message
        assert ('个人' if locale == 'zh' else 'individual') in message['text'] if label == '个人' else True
        assert ('利息' if locale == 'zh' else 'interest') in message['text'] if label == '利息' else True
        assert '已记录范围缺口' not in message['text']
        assert ('工具' if locale == 'zh' else 'tool') in message['text']
        assert message['question']['id'].startswith('boundary:scope:')
        before = deepcopy(doc['facts'])
        doc = store.get('owner', doc['id'])
        service.turner = lambda *_: pytest.fail('Exact scope choice should resume without routing')
        doc = service.message('owner', doc['id'], doc['revision'], str(uuid4()),
                              '查适用范围', True, reply_to_question_id=message['question']['id'], locale=locale)
        assert doc['messages'][-1]['kind'] == 'research'
        assert doc['facts'] == before and not doc['analyses']
        assert doc['messages'][-1]['research']['query_context']['uses_case'] is False
        if label == '个人':
            assert '个人' in doc['messages'][-1]['research']['query']
    finally:
        store.engine.dispose()


def bundle(scenario='MOCK-01'):
    data = retrieve(MockKnowledgeProvider(scenario), SearchRequest(request_id='r', trace_id='t', query='香港 FSIE',
                    **({'applicable_date': '2026-10-02', 'date_status': 'actual'} if scenario == 'MOCK-07' else {})),
                    TrustedContext(owner='test'))
    data['is_synthetic'] = False  # Unit-test composition switch; no real external call.
    return data


def response(data, text='针对你问的适用范围，这里是有依据的解释。'):
    evidence = data['model_evidence'][0]
    return {'paragraphs': [{'text': text, 'evidence': [
        {'evidence_id': evidence['evidence_id'], 'quote': evidence['text'][:20]}]}], 'missing_info': []}


def test_explanation_uses_actual_question_and_deduplicates_before_final_references():
    data, seen = bundle(), []
    def responder(payload):
        seen.append(payload)
        result = response(data)
        result['paragraphs'] *= 2
        return result
    result = compose_answer(data, question='个人是否在适用范围内？', responder=responder)
    validate_answer(result, data)
    assert seen[0]['question'] == '个人是否在适用范围内？'
    assert seen[0]['sources'] == data['model_evidence']
    assert result['composition'] == 'grounded'
    assert result['text'].count('这里是有依据的解释') == 1
    assert result['text'].index('法规及官方依据：') > result['text'].index('有依据的解释')
    assert 'mock-evidence-1' not in result['text']
    extended = append_followup(result['text'], '请确认收款日期。')
    assert extended.index('请确认收款日期') < extended.index('法规及官方依据：')


@pytest.mark.parametrize('invalid', ['quote', 'id', 'empty', 'error'])
def test_unverified_model_reply_falls_back_to_verified_excerpts(invalid):
    data = bundle()
    def responder(_):
        result = response(data, 'THIS MUST NOT BE DISPLAYED')
        if invalid == 'quote':
            result['paragraphs'][0]['evidence'][0]['quote'] = 'invented quotation'
        elif invalid == 'id':
            result['paragraphs'][0]['evidence'][0]['evidence_id'] = 'unrelated-source'
        elif invalid == 'empty':
            result['paragraphs'][0]['evidence'] = []
        else:
            raise RuntimeError('private provider details')
        return result
    answer = compose_answer(data, responder=responder)
    validate_answer(answer, data)
    assert answer['composition'] == 'extractive_fallback'
    assert 'THIS MUST NOT BE DISPLAYED' not in answer['text']
    assert 'private provider details' not in str(answer)


@pytest.mark.parametrize('scenario', ['MOCK-02', 'MOCK-03', 'MOCK-04', 'MOCK-06', 'MOCK-07'])
def test_no_permitted_evidence_never_enters_model(scenario):
    data = bundle(scenario)
    answer = compose_answer(data, responder=lambda _: pytest.fail('No authorized evidence'))
    validate_answer(answer, data)


def test_internal_diagnostics_are_deduplicated_but_retained_for_audit():
    data = bundle('MOCK-07')
    data['gaps'] = ['资料法域、主题或适用日期不匹配：li|private:1',
                    '资料法域、主题或适用日期不匹配：li|private:2', '原文版本不可用或校验失败：secret-id']
    text = compose_answer(data)['text']
    assert 'li|' not in text and 'secret-id' not in text
    assert text.count('部分检索结果') == 1
    assert 'li|private:1' in data['gaps'][0]


def test_general_fsie_query_uses_relevant_statute_navigation():
    assert topic_locators('香港境外股息FSIE案例事实及证据要求') == ['s.15H(1)', 's.15I(1)', 's.15I(3)']
    assert topic_locators('香港经济实质') == ['s.15K(1)', 's.15K(2)', 's.15K(3)']
    assert topic_locators('unrelated text') == []


@pytest.mark.parametrize('orchestration', ['legacy', 'hybrid'])
def test_production_router_connects_grounded_composer_without_external_calls(tmp_path, monkeypatch, orchestration):
    from packages.chat import service as module
    from packages.agent import grounded
    from packages.model_adapter.client import OpenAICompatibleClient
    provider = MockKnowledgeProvider()
    provider.fixture = deepcopy(provider.fixture)
    provider.fixture['search_response']['is_synthetic'] = False
    provider.fixture['search_response']['provider'] = 'legacy'
    for evidence in provider.fixture['search_response']['evidence']:
        evidence['is_synthetic'] = False
    monkeypatch.setattr(OpenAICompatibleClient, 'chat_json', lambda *_args, **_kwargs:
                        turn(intent='research', query='香港 FSIE 适用范围', uses_case=False))
    seen = []
    def explain(payload):
        seen.append(payload)
        evidence = payload['sources'][0]
        return {'paragraphs': [{'text': 'This is the source-supported response.', 'evidence': [
            {'evidence_id': evidence['evidence_id'], 'quote': evidence['text'][:20]}]}], 'missing_info': ['Irrelevant case interview question']}
    monkeypatch.setattr(grounded, 'respond', explain)
    store = ChatStore(f'sqlite:///{tmp_path}/wire.sqlite')
    chat = ChatService(store, provider=provider, orchestration=orchestration, turner=module.plan_turn)
    try:
        doc = store.create('owner')
        doc = chat.message('owner', doc['id'], 0, str(uuid4()), '个人是否属于香港 FSIE 范围？', True)
        assert seen[0]['question'] == '个人是否属于香港 FSIE 范围？'
        assert seen[0]['case_facts_for_context_only'] == {}
        assert doc['messages'][-1]['answer']['composition'] == 'grounded'
        assert doc['messages'][-1]['answer']['missing_info'] == []
    finally:
        store.engine.dispose()


def test_model_parent_section_never_gets_mislabeled_as_last_child():
    data = bundle()
    parent = data['passages'][0]
    data['model_evidence'][0]['locator'] = 's.15H'
    data['passages'] = [{**parent, 'locator': 's.15H(1)'}, {**parent, 'locator': 's.15H(7)'}]
    text = compose_answer(data)['text']
    footer = text.split('法规及官方依据：')[1]
    assert 's.15H' in footer and 's.15H(7)' not in footer


def test_multiple_task_answers_have_one_deduplicated_reference_footer():
    from packages.agent.knowledge import join_answers
    text = join_answers(['Shared condition.\n\nFirst result.\n\nReferences:\n- source A',
                         'Shared condition.\n\nSecond result.\n\nReferences:\n- source A\n- source B'], 'en')
    assert text.count('Shared condition.') == 1
    assert text.count('References:') == text.count('- source A') == 1
    assert 'First result.' in text and 'Second result.' in text and text.endswith('- source B')


@pytest.mark.parametrize('region', ['HK', '香港', 'Hong Kong'])
def test_known_hk_region_does_not_trigger_another_jurisdiction_question(region):
    from packages.agent.policy import scope
    assert scope('境外股息', {'uses_case': True}, {'analysis_jurisdiction': region}, 'auto') == 'HK'


def test_legal_question_with_unknown_facts_is_not_a_summary_command():
    from packages.agent import dialogue
    question = '香港公司收到新加坡子公司的境外股息，应核对哪些 FSIE 条件？请用中文分点解释，列出对应法条和官方来源，未知事实不要当作已满足。'
    assert dialogue.deterministic_turn({}, question) is None
    assert dialogue.explicit_summary_request('把我已经提供的信息列出来，并说还缺哪些关键资料')


def test_multiple_requested_topics_are_represented_before_limit():
    refs = topic_locators('香港 FSIE 适用范围、经济实质和参股豁免')[:7]
    assert 's.15H(1)' in refs and 's.15I(1)' in refs
    assert 's.15K(2)' in refs and 's.15M(2)' in refs


def test_explanation_cites_each_point_and_fallback_does_not_dump_raw_law():
    data = bundle()
    answer = compose_answer(data, responder=lambda _: response(data))
    assert '依据：' in answer['text']
    fallback = compose_answer(data, responder=lambda _: {'invalid': True})
    assert fallback['composition_error'] == 'answer_shape'
    assert fallback['claims'][0]['text'] not in fallback['text']
    assert '法规原文' in fallback['text']


def test_quote_whitespace_is_canonicalized_but_changed_words_are_rejected():
    from packages.agent.grounded import claims_from_result
    evidence = [{'evidence_id': 'law:1', 'text': '(1)The applicable requirement is met.'}]
    result = {'paragraphs': [{'text': 'This is a supported explanation.', 'evidence': [
        {'evidence_id': 'law:1', 'quote': '(1) The applicable requirement is met.'}]}], 'missing_info': []}
    claims, _ = claims_from_result(result, evidence)
    assert claims[0]['supports'][0]['quote'] == evidence[0]['text']
    result['paragraphs'][0]['evidence'][0]['quote'] = '(1)The applicable requirement is not met.'
    with pytest.raises(ValueError, match='unsupported_citation'):
        claims_from_result(result, evidence)


@pytest.mark.parametrize('orchestration', ['legacy', 'hybrid'])
def test_model_cannot_narrow_lookup_with_invented_statute_numbers(tmp_path, orchestration):
    from packages.chat.knowledge import references
    seen = []
    class RecordingProvider(MockKnowledgeProvider):
        def search_evidence(self, request, context):
            seen.append(request)
            return super().search_evidence(request, context)
    store = ChatStore(f'sqlite:///{tmp_path}/query.sqlite')
    service = ChatService(store, provider=RecordingProvider(), orchestration=orchestration,
        turner=lambda *_: turn(intent='research', query='香港 FSIE 适用范围 经济实质 参股豁免 s.15H s.15K s.15N', uses_case=False))
    try:
        doc = store.create('owner')
        service.message('owner', doc['id'], 0, str(uuid4()), '请解释香港 FSIE 股息的适用范围、经济实质和参股豁免。', True)
        assert seen and references(seen[0].query) == ([], [])
        assert '参股豁免' in seen[0].query
    finally:
        store.engine.dispose()
