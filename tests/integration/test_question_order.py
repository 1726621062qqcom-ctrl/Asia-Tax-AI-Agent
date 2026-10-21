from itertools import permutations

from packages.domain_bridge.question_order import next_question


def q(field, flow='up1'):
    return {'key': f'flow:{flow}.{field}', 'kind': 'data'}


def doc(value=None, status='candidate'):
    return {'canonical_fact_records': {'flow:up1.reinvested_in_cn': {'value': value, 'status': status}}}


def test_prerequisite_always_precedes_details_regardless_of_engine_order():
    parent = q('reinvested_in_cn')
    for questions in permutations([q('reinvestment_form'), q('reinvestment_from_distributed_profit'), parent]):
        assert next_question(questions, doc(), 'hash') == parent


def test_only_explicit_yes_unlocks_details_for_the_same_flow():
    details = [q('reinvestment_from_distributed_profit')]
    for value in (None, False, 'unknown', 'true', 1):
        assert next_question(details, doc(value), 'hash') is None
    for status in ('unknown', 'conflict', 'deferred'):
        assert next_question(details, doc(True, status), 'hash') is None
    assert next_question(details, doc(True), 'hash') == details[0]
    assert next_question([q('reinvestment_form', 'up2')], doc(True), 'hash') is None


def test_deferring_prerequisite_does_not_unlock_children_or_block_other_questions():
    parent = q('reinvested_in_cn')
    other = q('foreign_taxed')
    state = doc()
    state['domain_deferred'] = {parent['key']: 'hash'}
    assert next_question([parent, q('reinvestment_form'), other], state, 'hash') == other
