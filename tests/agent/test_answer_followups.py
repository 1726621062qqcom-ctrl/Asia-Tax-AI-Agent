from copy import deepcopy
import pytest

from packages.agent.fact_context import guard_extraction
from packages.agent.grounded import claims_from_result

TEXT = ('两笔收入：\n第一笔：内地公司派发现金股息人民币50万元，汇入香港银行账户。\n'
        '第二笔：卖股150万元，成本100万元。\n这次请优先分析第一笔50万元股息。')


def test_selected_dividend_keeps_its_own_amount_and_currency():
    patch, context = guard_extraction({'dividend_amount': 500000, 'dividend_currency': 'CNY',
                                      'payer_jurisdiction': 'CN', 'holding_percentage_pct': 100}, TEXT)
    assert patch['dividend_amount'] == 500000
    assert patch['payer_jurisdiction'] == 'CN'
    assert patch['dividend_currency'] == 'CNY'
    assert 'holding_percentage_pct' not in patch
    assert context['transaction_scope']['status'] == 'selected'
    assert '优先分析第一笔' == context['transaction_scope']['selection_quote']


def test_selected_dividend_rejects_amount_from_the_other_transaction():
    patch, _ = guard_extraction({'dividend_amount': 1500000}, TEXT)
    assert 'dividend_amount' not in patch


def test_unselected_transactions_still_require_disambiguation():
    patch, context = guard_extraction({'dividend_amount': 500000}, TEXT.split('这次')[0])
    assert 'dividend_amount' not in patch
    assert context['transaction_scope']['status'] == 'multiple_unbound'


def test_priority_does_not_turn_a_share_sale_into_a_dividend():
    patch, context = guard_extraction({'dividend_amount': 1500000}, TEXT.replace('优先分析第一笔', '优先分析第二笔'))
    assert 'dividend_amount' not in patch
    assert context['transaction_scope']['status'] == 'multiple_unbound'


def test_extra_followups_do_not_discard_supported_explanation_or_unresolved_conditions():
    draft = {'paragraphs': [{'text': 'A supported explanation.', 'evidence': [{'evidence_id': 'law', 'span_id': 'P1'}]}],
             'missing_info': ['Question ' + str(i) for i in range(5)]}
    claims, missing = claims_from_result(draft, [{'evidence_id': 'law', 'text': 'A source passage.'}])
    assert claims and missing == draft['missing_info']
    bad = deepcopy(draft)
    bad['paragraphs'][0]['evidence'][0]['span_id'] = 'P999'
    with pytest.raises(ValueError, match='unsupported_citation'):
        claims_from_result(bad, [{'evidence_id': 'law', 'text': 'A source passage.'}])
    bad = deepcopy(draft)
    bad['missing_info'] = [None]
    with pytest.raises(ValueError, match='missing_info'):
        claims_from_result(bad, [{'evidence_id': 'law', 'text': 'A source passage.'}])
