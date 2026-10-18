"""Versioned research navigation, not tax rules or a professional coverage verdict.

Reuse Git rule navigation while rule_nodes is not the chat runtime's rule source.
Case state comes from the authorized chat document, never an arbitrary facts SQL query.
"""
import re
from packages.agent import dialogue

VERSION = 'fsie-research-navigation-2'
ISSUES = {
    'scope': (r'适用范围|主体|mne|scope|recipient', dialogue.IDENTIFICATION),
    'receipt': (r'收取|收款|汇入|received|receipt|remit', dialogue.RECEIPT),
    'economic_substance': (r'经济实质|經濟實質|substance|employees|staff', dialogue.SUBSTANCE),
    'participation_basic': (r'参与|參與|持股|participation|holding|shareholding', dialogue.PARTICIPATION[:4]),
    'foreign_tax_switchover': (r'境外.{0,5}税|外国税|抵免|foreign tax|tax paid|subject.to.tax|credit', ('foreign_tax_description',)),
    'anti_hybrid': (r'反混合|anti.hybrid|hybrid mismatch', ('underlying_tax_deductible_status',)),
    'main_purpose': (r'主要目的|main purpose|commercial rationale', ('commercial_rationale',)),
    'compliance_filing': (r'申报|记录保存|filing|record.keep', ('evidence_inventory',)),
}


def explanatory_request(text):
    """Recognize an explicit request to explain rules alongside case facts.

    A fact answer, pause, summary or request for a guided interview stays intake.
    This only selects research; it grants no permission to confirm a tax conclusion.
    """
    return bool(re.search(r'FSIE|dividend|股息|税务|稅務', text, re.I) and re.search(
        r'which.{0,80}conditions|what.{0,60}(?:check|establish)|I want to understand|'
        r'please (?:help|answer|first distinguish)|documents? (?:we should|to|needed)|'
        r'请.{0,40}(?:解释|分析|区分|列出)|需要核对|哪些.{0,15}(?:条件|材料)', text, re.I))


def issues_for(text):
    found = [key for key, (pattern, _) in ISSUES.items() if re.search(pattern, text or '', re.I)]
    core = ['scope', 'receipt', 'economic_substance', 'participation_basic', 'foreign_tax_switchover']
    if explanatory_request(text) and len(text) > 500:
        return list(dict.fromkeys(core + found))
    return found or core


def law_navigation(text):
    """Use existing versioned locators for the user's original question, not LLM guesses."""
    from packages.chat.knowledge import references, topic_locators
    from packages.chat.analysis import NODE_LOCATORS
    explicit, rulings = references(text)
    if explicit or rulings:
        return explicit
    if explanatory_request(text) and len(text) > 500:
        return list(dict.fromkeys(ref for issue in issues_for(text) for ref in NODE_LOCATORS.get(issue, [])))
    return topic_locators(text)


def required_search_kinds(text):
    patterns = {
        'law': r'法条|法例|法规|法律|legislation|ordinance|statut|\blaw\b|s\.\s*15',
        'guidance': r'指引|官方解释|FAQ|guidance|\bIRD\b|Inland Revenue Department|official sources|官方资料',
        'ruling': r'裁定|官方案例|official cases?|ruling|\bcase\s*(?:no\.?\s*)?\d+',
    }
    kinds, excluded = [], []
    for kind, pattern in patterns.items():
        negative = r"(?:不要|不用|无需|不需要|do not|don't|without|no need to)[^,，;。\n]{0,24}(?:" + pattern + ')'
        if re.search(negative, text, re.I):
            excluded.append(kind)
        elif re.search(pattern, text, re.I):
            kinds.append(kind)
    return kinds or ([] if excluded else ['law', 'guidance'] if explanatory_request(text) and len(text) > 500 else ['law'])


def fact_view(doc, text):
    facts = dialogue.values(doc)
    relevant = set(dialogue.IDENTIFICATION)
    for issue in issues_for(text):
        relevant.update(ISSUES[issue][1])
    known_gaps = {gap['field']: gap for gap in dialogue.gaps(doc)}
    missing = [known_gaps.get(key, {'field': key,
                'reason': 'conflict' if facts.get(key) == 'conflict' else 'unknown' if key in facts else 'missing',
                'impact': dialogue.PROMPTS.get(key, ('', 'Requires confirmation for a case conclusion.', ''))[1]})
               for key in sorted(relevant) if not dialogue.resolved(facts.get(key))]
    conflicts = [gap for gap in missing if gap['reason'] == 'conflict']
    # Conflicts prevent a case conclusion; absent facts do not block explaining the law.
    return {'fact_fields': sorted(facts),
            'fact_states': {key: ('conflict' if value == 'conflict' else 'unknown' if not dialogue.resolved(value) else 'recorded')
                            for key, value in facts.items()},
            'confirmed_revision': doc.get('confirmed_revision'),
            'blocking_fact_gaps': conflicts,
            'nonblocking_fact_gaps': [gap for gap in missing if gap not in conflicts],
            'deferred_fact_fields': [gap['field'] for gap in dialogue.gaps(doc) if gap['field'] not in relevant],
            'requested_issues': issues_for(text), 'navigation_version': VERSION}


def evidence_observation(bundle, text):
    from packages.chat.analysis import NODE_LOCATORS
    passages = bundle.get('passages', [])
    locators = {p.get('locator') for p in passages}
    wanted = issues_for(text)
    located = [issue for issue in wanted if any(
        loc == ref or (loc and loc.startswith(ref + '('))
        for loc in locators for ref in NODE_LOCATORS.get(issue, []))]
    return {'evidence_count': len(passages),
            'unique_source_count': len({p.get('source_id') for p in passages}),
            'evidence_refs': [{'evidence_id': p['evidence_id'], 'source_version_id': p.get('source_version_id'),
                               'locator': p.get('locator')} for p in passages[:20]],
            'source_types': sorted({p['source_type'] for p in passages if p.get('source_type')}),
            'located_issues': located, 'unlocated_issues': [issue for issue in wanted if issue not in located],
            'coverage_basis': 'versioned_locator_navigation_only',
            'professional_validation': 'pending_review',
            'date_applicability': 'date_supplied' if bundle.get('query_context', {}).get('applicable_date') else 'not_established',
            'gaps': bundle.get('reason_code'), 'retrieval_gaps': bundle.get('gaps', [])[:10],
            'navigation_version': VERSION}
