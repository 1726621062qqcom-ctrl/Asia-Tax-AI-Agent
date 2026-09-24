import copy
import json
from pathlib import Path

import pytest

from packages.consultation.facts import local_candidates, merge_facts
from packages.consultation.knowledge import KnowledgeBase
from packages.consultation.schemas import Draft, FactCandidate
from packages.consultation.service import ConsultationService, validate_draft
from packages.consultation.sessions import SessionStore

SCENARIOS=json.loads((Path(__file__).parent/'scenarios.json').read_text())['scenarios']


@pytest.mark.parametrize('scenario',SCENARIOS,ids=lambda s:s['id'])
def test_representative_conversations(scenario):
    service=ConsultationService()
    facts=[];history=[]
    for i,message in enumerate(scenario['messages'],1):
        answer=service.reply(message,facts,history,i,synthetic_acknowledged=True)
        history.append(message);facts=answer.facts
    assert answer.intent==scenario['intent']
    assert answer.research_only is True
    assert answer.mode=='local_research'
    topics={service.knowledge.by_id[c.id]['topic'] for c in answer.citations}
    assert set(scenario['required_topics'])<=topics
    assert bool(answer.questions)==scenario['questions']
    if scenario['intent'] in ('out_of_scope','unknown'):
        assert not answer.citations
    ids={c.id for c in answer.citations}
    assert all(set(p.citations)<=ids for s in answer.sections for p in s.paragraphs)
    if scenario['id']=='historical':
        assert any('年份' in w for w in answer.warnings)


def test_fact_correction_preserves_evidence_and_history():
    original='假设我们是一家香港公司，持有境外子公司60%股份，计划收取现金股息。'
    facts=merge_facts([],local_candidates(original),original,1)
    correction='刚才说错了，分派的是股份，不是现金。'
    changed=merge_facts(facts,local_candidates(correction),correction,2)
    form=next(f for f in changed if f.key=='distribution_form')
    assert form.status=='user_stated' and '股份' in form.value
    assert form.previous[0]['turn']==1
    assert form.quote in correction
    # Unrelated fields must not keep a full stale sentence about cash.
    assert all('现金' not in f.value for f in changed if f.key!='distribution_form')


def test_new_assertion_without_correction_is_a_conflict():
    f=merge_facts([], [FactCandidate(key='holding_percentage',value='60%',quote='持股60%')],'持股60%',1)
    changed=merge_facts(f,[FactCandidate(key='holding_percentage',value='20%',quote='持股20%')],'持股20%',2)
    assert changed[0].status=='conflict'


def test_holding_shares_is_not_in_kind_distribution():
    facts=local_candidates('假设我们持有海外子公司60%股份。')
    assert 'distribution_form' not in [f.key for f in facts]


def test_questions_are_not_facts():
    assert not local_candidates('持股60%是否满足条件？')


def test_fabricated_fact_quote_rejected():
    with pytest.raises(ValueError):
        merge_facts([],[FactCandidate(key='holding_percentage',value='60%',quote='invented')],'hello',1)


class StubClient:
    class config:
        model_name='stub'
    def __init__(self,responses):
        self.responses=iter(responses);self.calls=[]
    def chat_json(self,system,user,**kwargs):
        self.calls.append((system,user))
        result=next(self.responses)
        if isinstance(result,Exception): raise result
        return result


def valid_draft(cid='ird-fsie-participation'):
    return {'sections':[{'title':'参与条件','paragraphs':[{'text':'需按全部条件核对，不能仅根据持股比例下结论。','citations':[cid]}]}],'questions':[]}


def test_model_path_and_allowlisted_citations():
    stub=StubClient([{'intent':'law','facts':[],'search_terms':'participation'},valid_draft()])
    answer=ConsultationService(client=stub).reply('香港FSIE参与豁免有哪些条件？',[],[],1,synthetic_acknowledged=True)
    assert answer.mode=='model_research'
    assert [c.id for c in answer.citations]==['ird-fsie-participation']
    payload=json.loads(stub.calls[1][1])
    assert all('advance74' not in s['text'] for s in payload['sources'])


@pytest.mark.parametrize('bad',[
    valid_draft('invented'),
    {'sections':[{'title':'结论','paragraphs':[{'text':'一定免税','citations':['ird-fsie-participation']}]}]},
    {'sections':[{'title':'结论','paragraphs':[{'text':'参见 https://evil.example','citations':['ird-fsie-participation']}]}]},
    {'sections':[{'title':'结论','paragraphs':[{'text':'没有引用','citations':[]}]}]},
])
def test_invalid_model_answer_falls_back_without_promoting_status(bad):
    stub=StubClient([{'intent':'law','facts':[],'search_terms':'participation'},bad])
    answer=ConsultationService(client=stub).reply('香港FSIE参与豁免有哪些条件？',[],[],1,synthetic_acknowledged=True)
    assert answer.mode=='model_fallback'
    assert answer.research_only
    assert all(c.id!='invented' for c in answer.citations)


def test_provider_error_does_not_leak():
    stub=StubClient([RuntimeError('SECRET_PROVIDER_BODY')])
    answer=ConsultationService(client=stub).reply('香港FSIE股息有哪些规定？',[],[],1,synthetic_acknowledged=True)
    assert answer.mode=='model_fallback'
    assert 'SECRET_PROVIDER_BODY' not in answer.model_dump_json()


def test_no_model_call_without_data_acknowledgement():
    stub=StubClient([])
    with pytest.raises(ValueError):
        ConsultationService(client=stub).reply('股息问题',[],[],1,synthetic_acknowledged=False)
    assert not stub.calls


def test_out_of_scope_does_not_call_model():
    stub=StubClient([])
    answer=ConsultationService(client=stub).reply('日本消费税怎么处理？',[],[],1,synthetic_acknowledged=True)
    assert answer.intent=='out_of_scope' and not stub.calls


def test_evasion_is_redirected_to_compliance_without_model():
    stub=StubClient([])
    answer=ConsultationService(client=stub).reply('如何隐瞒境外股息逃税？',[],[],1,synthetic_acknowledged=True)
    assert not stub.calls
    assert '不能帮助' in answer.sections[0].paragraphs[0].text


def test_corpus_tamper_is_rejected(tmp_path):
    kb=KnowledgeBase();data=copy.deepcopy(kb.data)
    data['units'][0]['text']='edited'
    path=tmp_path/'corpus.json';path.write_text(json.dumps(data))
    with pytest.raises(ValueError,match='hash'):
        KnowledgeBase(path)


def test_session_expiry_capacity_and_isolation():
    clock=[10.0];store=SessionStore(ttl=60,capacity=2,clock=lambda:clock[0])
    first=store.create(True);second=store.create(True)
    first.messages.append('private A')
    assert second.messages==[]
    with pytest.raises(OverflowError):store.create(True)
    clock[0]=71
    with pytest.raises(KeyError):store.get(first.token)
    assert store.create(True)
    store.delete(second.token)
    with pytest.raises(KeyError):store.get(second.token)


def test_specific_statute_retrieves_primary_text_and_anti_abuse_context():
    service=ConsultationService()
    answer=service.reply('请解释第15M(2)条的参与条件',[],[],1,synthetic_acknowledged=True)
    by_id={c.id:c for c in answer.citations}
    assert by_id['cap112-15M'].source_type=='primary_legislation'
    assert 'not less than 5%' in by_id['cap112-15M'].excerpt
    assert 'cap112-15N' in by_id


@pytest.mark.parametrize('question',['请解释香港税法第999条','请解释第15M(999)条','请解释s.15Z'])
def test_unknown_provision_is_not_fabricated(question):
    answer=ConsultationService().reply(question,[],[],1,synthetic_acknowledged=True)
    assert answer.intent=='unknown' and not answer.citations
