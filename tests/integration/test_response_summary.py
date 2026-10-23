from copy import deepcopy
from packages.domain_bridge.response_summary import summary


def sample():
    return {'status': 'needs_input', 'mode': 'assess_current', 'currency': 'CNY',
            'lower': {'status': 'finite', 'value': 100000}, 'upper': {'status': 'finite', 'value': 330000},
            'regions': [{'best': [['up1', 'CN', 'income', 'ULT', 100000, [], True]],
                         'guaranteed': [['up1', 'CN', 'income', 'ULT', 200000, [], True],
                                        ['up1', 'HK', 'income', 'ULT', 130000, [], True]]}],
            'structure': {'entities': [['OP', 'CN'], ['ULT', 'HK']],
                          'flows': [['up1', 'DIVIDEND', 'OP', 'ULT', 2000000, '2026-11-15']],
                          'holds': [['ULT', 'OP', 100, '案例陈述']]},
            'questions': [{'key': 'ULT.adequate_substance', 'kind': 'ruling', 'region': ['HK']} ]}


def test_scenario_components_and_review_materials_are_explicit():
    text = summary(sample())
    assert '中国内地所得税 200,000.00 CNY + 香港所得税 130,000.00 CNY = **330,000.00 CNY**' in text
    assert '经济实质说明材料' in text
    assert 'ULT.adequate_substance' not in text
    assert '单独影响' in text


def test_non_reconciling_components_are_not_explained_as_totals():
    result = sample()
    result['lower']['value'] = 90000
    result['upper']['value'] = 300000
    text = summary(result)
    assert '不推测上下限' in text
    assert ' = **' not in text
    result['mode'] = 'plan_structure'
    assert ' = **' not in summary(result)


def test_recorded_facts_are_scoped_and_unknown_is_not_no():
    doc = {'canonical_fact_records': {
        'flow:up1.reinvested_in_cn': {'value': False, 'status': 'user_entered'},
        'hold:ULT>OP.since': {'value': '2020-01-01', 'status': 'candidate'}}}
    text = summary(sample(), doc=doc)
    assert '跳过再投资细节' in text
    assert '2020-01-01' in text
    unknown = deepcopy(doc)
    unknown['canonical_fact_records']['flow:up1.reinvested_in_cn'] = {'value': 'unknown', 'status': 'unknown'}
    assert '跳过再投资细节' not in summary(sample(), doc=unknown)
    assert '跳过再投资细节' not in summary(sample())


def test_english_labels_and_unavailable_bounds():
    result = sample()
    text = summary(result, True)
    assert 'Hong Kong income tax 130,000.00 CNY' in text
    assert 'Economic substance documentation' in text
    result['lower'] = {'status': 'unknown', 'value': None}
    assert 'not determined' in summary(result, True)
