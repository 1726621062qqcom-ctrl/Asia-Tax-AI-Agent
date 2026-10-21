"""Contract checks for the independently versioned upstream engine."""
from types import SimpleNamespace
import pytest
from packages.domain_bridge.worker import _question
from packages.domain_bridge.question_order import prepare_questions

@pytest.mark.parametrize('hint, expected', [('yes/no', 'boolean'), ('date', 'date'), ('amount', 'number'), ('ratio', 'number'), ('months', 'number'), ('text', 'text'), ('是/否', 'boolean')])
def test_upstream_answer_types(hint, expected):
    q = SimpleNamespace(value=hint, key='flow:up1.reinvested_in_cn', kind='data', region={'CN'}, prompt='Question', why=[], impact=None, source_hint='', forms=[])
    assert _question(q)['answer_schema']['type'] == expected

def test_upstream_english_question_has_separate_chinese_label():
    result = {'questions': [{'key': 'flow:up1.reinvested_in_cn', 'kind': 'data', 'prompt': 'Please provide: reinvestment', 'region': ['CN']}], 'upper': 165000}
    prepare_questions(result, {})
    q = result['questions'][0]
    assert '再投资' in q['prompt']
    assert q['prompt_en'] and 'Please provide' not in q['prompt']
    assert result['upper'] == 165000

def test_new_unreviewed_fields_cannot_be_asked_automatically():
    result = {'questions': [{'key': 'flow:up1.reinvestment_withdrawn', 'kind': 'data', 'prompt': 'Withdrawal?'}]}
    prepare_questions(result, {})
    assert result['questions'][0]['interview_status'] == 'needs_policy_review'
