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
    state = {'canonical_fact_records': {}, 'domain_interview': {}}
    if field == 'reinvestment_withdrawn_on':
        state['canonical_fact_records']['flow:up1.reinvested_in_cn'] = record(True)
    if field.startswith('sg_loss_'):
        state['domain_interview']['interview:flow:up1.losses_exist'] = {'value': True}
        if field == 'sg_loss_same_trade':
            state['canonical_fact_records']['flow:up1.sg_loss_shareholders_same'] = record(False)
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
    # Multi-stage prerequisites require each step, not just the first question.
    state['domain_interview'][parent['key']] = {'value': True}
    if field == 'tp_adjustment_paid_on':
        assert not eligible(raw['questions'][0], state)
        state['domain_interview']['interview:flow:up1.tp_adjustment_paid'] = {'value': True}
    if field.startswith('sg_loss_'):
        state['canonical_fact_records']['flow:up1.sg_loss_shareholders_same'] = record(False)
        if field == 'sg_loss_same_trade':
            state['canonical_fact_records']['flow:up1.sg_loss_continuity_waived'] = record(True)
    if CATALOG[field].get('handling') == 'structured_review':
        assert interview_status(raw['questions'][0], state) == 'needs_policy_review'
    else:
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
        if not CATALOG[field].get('handling'):
            assert result['questions'][0]['interview_status'] != 'needs_policy_review'
        else:
            assert result['questions'][0].get('review_reason')
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


def test_withdrawal_date_requires_all_ancestors_even_if_withdrawal_was_recorded():
    question = q('reinvestment_withdrawn_on')
    state = {'canonical_fact_records': {'flow:up1.reinvestment_withdrawn': record(True)}}
    result = {'questions': [question]}
    prepare_questions(result, state)
    assert next_question(result['questions'], state, 'hash')['key'] == 'flow:up1.reinvested_in_cn'
    for value in (False, 'unknown'):
        state['canonical_fact_records']['flow:up1.reinvested_in_cn'] = record(value)
        assert not eligible(question, state)
    state['canonical_fact_records']['flow:up1.reinvested_in_cn'] = record(True)
    assert eligible(question, state)


def test_negative_root_does_not_generate_irrelevant_intermediate_questions():
    state = doc(False)
    result = {'questions': [q('reinvestment_withdrawn_on')]}
    prepare_questions(result, state)
    assert result['questions'][0]['interview_status'] == 'not_applicable'
    assert len(result['questions']) == 1
    assert next_question(result['questions'], state, 'hash') is None


def test_shared_clawback_field_does_not_confuse_income_relief_and_stamp_relief():
    state = {'canonical_fact_records': {'flow:up1.stamp_relief_claimed': record(False)},
             'domain_interview': {'interview:flow:up1.transfer_relief': {'value': True}}}
    stamp = {**q('clawback_event_within_2y'), 'why': ['sg.stamp.relief']}
    income = {**q('clawback_event_within_2y'), 'why': ['hk.fsie.intragroup']}
    mixed = {**income, 'why': stamp['why'] + income['why']}
    assert not eligible(stamp, state)
    assert eligible(income, state)
    assert eligible(mixed, state)


def test_branch_existence_is_separate_for_each_company_and_jurisdiction():
    question = {'key': 'ULT.branch_profit_hk', 'kind': 'data'}
    state = {'domain_interview': {}}
    result = {'questions': [question]}
    prepare_questions(result, state)
    parent = next_question(result['questions'], state, 'hash')
    assert parent['key'] == 'interview:ULT.branch_exists_hk'
    state['domain_interview'][parent['key']] = {'value': True}
    assert eligible(question, state)
    assert not eligible({'key': 'OP.branch_profit_hk', 'kind': 'data'}, state)
    assert not eligible({'key': 'ULT.branch_profit_sg', 'kind': 'data'}, state)


def test_loss_waiver_chain_never_presupposes_losses_or_a_waiver():
    question = {'key': 'ULT.sg_loss_same_trade', 'kind': 'data'}
    state = {'canonical_fact_records': {'ULT.sg_loss_continuity_waived': record(True),
                                        'ULT.sg_loss_shareholders_same': record(False)}, 'domain_interview': {}}
    assert not eligible(question, state)
    state['domain_interview']['interview:ULT.losses_exist'] = {'value': True}
    assert eligible(question, state)
    state['canonical_fact_records']['ULT.sg_loss_shareholders_same'] = record(True)
    assert not eligible(question, state)


def test_planned_yes_cannot_override_explicit_no_or_conflict():
    state = doc(False)
    state.update(domain_workflow={'mode': 'plan_structure'}, domain_answers={'actions': {'flow:up1.reinvested_in_cn:is_true': 'yes'}})
    assert not eligible(q('reinvestment_form'), state)
    state['canonical_fact_records']['flow:up1.reinvested_in_cn'] = record(True, 'conflict')
    assert not eligible(q('reinvestment_form'), state)


def test_missing_parent_does_not_duplicate_an_existing_action_question():
    result = {'questions': [{**q('reinvested_in_cn:is_true'), 'kind': 'action'}, q('reinvestment_form')]}
    prepare_questions(result, {})
    assert len(result['questions']) == 2


def test_group_scope_cannot_ignore_a_conflicting_member():
    state = {'domain_case': {'roles': {'ULT': {}, 'OP': {}}},
             'canonical_fact_records': {'ULT.group_revenue_eur': record(900000000),
                                        'OP.group_revenue_eur': record(1000000, 'conflict')},
             'domain_outcome': {'interview_parameters': {'pillar_revenue_min': 750000000}}}
    assert not eligible({'key': 'group.p2_etr', 'kind': 'data'}, state)


def test_event_observation_expires_when_transaction_identity_changes():
    from packages.domain_bridge.question_order import interview_context
    state = {'canonical_fact_records': {'event.on': record('2026-01-01')}}
    state['domain_interview'] = {'interview:flow:up1.tax_paid': {'value': True, 'context': interview_context(state)}}
    assert eligible(q('tax_paid_on'), state)
    state['canonical_fact_records']['event.on'] = record('2027-01-01')
    assert not eligible(q('tax_paid_on'), state)


def test_all_reviewed_ancestor_chains_reject_false_and_unknown_roots():
    from packages.domain_bridge.question_order import requirements
    for field, meta in CATALOG.items():
        if meta.get('handling'):
            continue
        question = q(field)
        reqs = {}
        queue = [question]
        parameters = {'pillar_revenue_min': 750000000}
        while queue:
            for req in requirements(queue.pop(), {}, parameters):
                if req['key'] not in reqs:
                    reqs[req['key']] = req
                    queue.append({'key': req['key'], 'kind': 'data'})
        state = {'canonical_fact_records': {}, 'domain_interview': {}, 'domain_outcome': {'interview_parameters': parameters}}
        def write(key, value):
            target = state['domain_interview'] if key.startswith('interview:') else state['canonical_fact_records']
            target[key] = record(value)
        for key, req in reqs.items():
            write(key, req['value'])
        assert eligible(question, state), field
        for key, req in reqs.items():
            for value in ('unknown', None, (req['value'] - 1 if req['op'] == 'ge' else not req['value'])):
                write(key, value)
                assert not eligible(question, state), (field, key, value)
            write(key, req['value'])
