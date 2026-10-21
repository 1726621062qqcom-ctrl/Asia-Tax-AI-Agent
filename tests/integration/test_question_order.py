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

import json
from copy import deepcopy
from pathlib import Path
import pytest
from packages.domain_bridge.question_order import (
    CATALOG, GATES, EVENT_GATES, PILLAR_FIELDS, parts, eligible,
    requirements, prepare_questions, interview_status,
)


def record(value, status='user_entered'):
    return {'value': value, 'status': status, 'origin': 'user'}


@pytest.mark.parametrize('field,parent,expected', [(f, *gate) for f, gate in GATES.items()])
@pytest.mark.parametrize('predicate', ['', ':is_true', ':is_in'])
def test_every_reviewed_dependency_handles_unknown_no_yes_and_predicate_keys(field, parent, expected, predicate):
    question = q(field + predicate)
    state = {'canonical_fact_records': {}}
    assert not eligible(question, state)
    state['canonical_fact_records']['flow:up1.' + parent] = record(not expected)
    assert not eligible(question, state)
    state['canonical_fact_records']['flow:up1.' + parent] = record('unknown', 'unknown')
    assert not eligible(question, state)
    state['canonical_fact_records']['flow:up1.' + parent] = record(expected)
    assert eligible(question, state)
    assert not eligible(q(field + predicate, 'up2'), state)
    # A year-specific flow must not inherit another year's observation.
    assert not eligible(q(field + predicate, 'up1@2027'), state)


@pytest.mark.parametrize('field', sorted(PILLAR_FIELDS))
def test_all_pillar_details_wait_for_scope_without_filling_missing_numbers(field):
    question = {'key': 'ULT.' + field, 'kind': 'data'}
    state = {'canonical_fact_records': {}, 'domain_outcome': {'interview_parameters': {'pillar_revenue_min': 750000000}}}
    assert not eligible(question, state)
    state['canonical_fact_records']['group.group_revenue_eur'] = record(1000000)
    assert interview_status(question, state) == 'not_applicable'
    state['canonical_fact_records']['group.group_revenue_eur'] = record(900000000)
    if field.startswith('p2_cbcr_'):
        assert not eligible(question, state)
        state['canonical_fact_records']['ULT.p2_qualified_cbcr'] = record(True)
    assert eligible(question, state)


def test_jurisdiction_suffix_does_not_strip_real_field_names_or_mix_reports():
    assert parts('flow:up1.reinvested_in_cn')[2] == 'reinvested_in_cn'
    assert parts('group.p2_cbcr_pbt_hk:is_true')[2] == 'p2_cbcr_pbt'
    assert parts('group.p2_eur_rate_2027')[2] == 'p2_eur_rate'
    state = {'canonical_fact_records': {'group.group_revenue_eur': record(900000000),
                                        'group.p2_qualified_cbcr_hk': record(True)},
             'domain_outcome': {'interview_parameters': {'pillar_revenue_min': 750000000}}}
    assert eligible({'key': 'group.p2_cbcr_pbt_hk', 'kind': 'data'}, state)
    assert not eligible({'key': 'group.p2_cbcr_pbt_sg', 'kind': 'data'}, state)


@pytest.mark.parametrize('field', sorted(EVENT_GATES))
def test_dates_and_adjustment_amounts_do_not_assume_the_event_occurred(field):
    raw = {'questions': [q(field)], 'upper': {'status': 'finite', 'value': 123}, 'lower': {'status': 'finite', 'value': 0}}
    original = deepcopy(raw)
    state = {'canonical_fact_records': {}, 'domain_interview': {}}
    prepare_questions(raw, state)
    parent = next_question(raw['questions'], state, 'hash')
    assert parent['key'].startswith('interview:')
    assert parent['answer_schema']['type'] == 'boolean'
    assert raw['upper'] == original['upper'] and raw['lower'] == original['lower']
    for value in (False, 'unknown'):
        state['domain_interview'][parent['key']] = {'value': value}
        assert not eligible(raw['questions'][0], state)
        updated = deepcopy(original)
        prepare_questions(updated, state)
        assert not any(q['key'] == parent['key'] for q in updated['questions'])
    state['domain_interview'][parent['key']] = {'value': True}
    assert eligible(raw['questions'][0], state)


def test_missing_parent_is_added_without_inventing_a_fact_and_can_be_deferred():
    result = {'questions': [q('reinvestment_form')]}
    state = {'canonical_fact_records': {}}
    prepare_questions(result, state)
    parent = next_question(result['questions'], state, 'hash')
    assert parent['key'] == 'flow:up1.reinvested_in_cn'
    assert state['canonical_fact_records'] == {}
    state['domain_deferred'] = {parent['key']: 'hash'}
    assert next_question(result['questions'], state, 'hash') is None


def test_unreviewed_new_field_is_withheld_instead_of_guessed():
    result = {'questions': [q('new_unreviewed_field')]}
    state = {'canonical_fact_records': {}}
    prepare_questions(result, state)
    assert result['interview_counts']['needs_policy_review'] == 1
    assert next_question(result['questions'], state, 'hash') is None


def test_every_audited_field_has_family_context_and_acyclic_dependencies():
    for field in CATALOG:
        result = {'questions': [q(field)], 'interview_parameters': {'pillar_revenue_min': 750000000}}
        state = {'canonical_fact_records': {}}
        prepare_questions(result, state)
        assert result['questions'][0]['context_zh']
        assert result['questions'][0]['context_en']
        assert result['questions'][0]['interview_status'] != 'needs_policy_review'
        assert len(result['questions']) < 6
        edges = {item['key']: [r['key'] for r in item['requirements']] for item in result['questions']}
        def visit(key, path):
            assert key not in path
            for parent in edges.get(key, []):
                visit(parent, path | {key})
        visit(result['questions'][0]['key'], set())


def test_planned_action_does_not_become_an_observed_fact():
    question = q('reinvestment_form')
    state = {'canonical_fact_records': {}, 'domain_answers': {'actions': {'flow:up1.reinvested_in_cn:is_true': 'yes'}},
             'domain_workflow': {'mode': 'plan_structure'}}
    assert eligible(question, state)
    assert state['canonical_fact_records'] == {}
    for mode in ('assess_current', 'review_paid'):
        state['domain_workflow']['mode'] = mode
        assert not eligible(question, state)
