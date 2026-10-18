"""Shared eligibility and pure report proposal for HTTP and graph execution."""
from copy import deepcopy
from packages.agent.dialogue import gaps, fingerprint, supported, identification
from packages.agent.contracts import TrustedContext
from packages.agent.review import freeze
from packages.agent.tracing import instrument, emit


def analysis_eligibility(doc):
    if doc.get('fact_context', {}).get('transaction_scope', {}).get('status') == 'multiple_unbound':
        return 'confirmation_required'
    if doc['state'] != 'confirmed' or doc.get('confirmed_facts') is None:
        return 'confirmation_required'
    if not supported(doc['confirmed_facts']):
        return 'out_of_scope'
    if gaps(doc) and doc.get('dialogue', {}).get('partial_consent', {}).get('facts_hash') != fingerprint(doc):
        return 'partial_confirmation_required'
    return None


@instrument('analysis.prepare')
def report_proposal(doc, analyzer, provider, owner):
    from packages.chat.analysis import analyze
    from packages.chat.service import WorkflowError
    reason = analysis_eligibility(doc)
    if reason:
        emit('analysis.guard', 'rejected', reason_code=reason)
        raise WorkflowError(reason)
    if analyzer is analyze:
        result = analyzer(doc['id'], deepcopy(doc['confirmed_facts']), doc['confirmed_revision'],
                          provider=provider, context=TrustedContext(owner=owner, case_id=doc['id']))
    else:
        result = analyzer(doc['id'], deepcopy(doc['confirmed_facts']), doc['confirmed_revision'])
    for rule in result.get('nodes', []):
        emit('analysis.rule_result', node=rule.get('node'), output=rule.get('output'),
             observation_source='returned_rule_result')
    result['intake_gaps'] = gaps(doc)
    result['identification'] = identification(doc)
    result['partial_output_authorized'] = bool(doc.get('dialogue', {}).get('partial_consent'))
    if result['intake_gaps']:
        result['evidence_gate'] = 'insufficient'
    return freeze(result)
