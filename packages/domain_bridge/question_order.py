"""Select follow-ups only when their factual prerequisites are established.

This affects interviewing, never the engine's tax rules or unresolved bounds.
"""
REINVESTMENT_DETAILS = frozenset({
    'reinvestment_from_distributed_profit', 'reinvestment_form',
    'direct_payment', 'investee_encouraged_industry', 'planned_holding_months',
})


def eligible(question, doc):
    key = question['key']
    scope, _, field = key.rpartition('.')
    if scope.startswith('flow:') and field in REINVESTMENT_DETAILS:
        record = doc.get('canonical_fact_records', {}).get(scope + '.reinvested_in_cn', {})
        # Unknown, absent, conflicting and deferred facts never unlock a branch.
        return record.get('value') is True and record.get('status') not in ('unknown', 'conflict', 'deferred')
    return True


def next_question(questions, doc, facts_hash):
    def order(q):
        field = q['key'].rsplit('.', 1)[-1]
        priority = 0 if field == 'reinvested_in_cn' else 1 if q['kind'] == 'blocking' else 2
        return priority, q['key'], q['kind']
    return next((q for q in sorted(questions, key=order)
                 if q['kind'] in ('data', 'blocking', 'joint', 'action')
                 and doc.get('domain_deferred', {}).get(q['key']) != facts_hash
                 and eligible(q, doc)), None)
