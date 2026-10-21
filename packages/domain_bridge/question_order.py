"""Audited interviewing policy, independent of the immutable tax calculation.

Logical AND siblings are not automatically factual prerequisites. Only reviewed
existence/scope dependencies below gate questions; other active engine questions
remain available and carry a neutral explanation of why they are being asked.
"""
from copy import deepcopy
import json
from pathlib import Path
import re

CATALOG = json.loads(Path(__file__).with_name('interview_catalog.json').read_text())
POLICY_VERSION = 'interview-2026-10-21-v2'
REINVESTMENT_DETAILS = frozenset({'reinvestment_from_distributed_profit', 'reinvestment_form',
                                'direct_payment', 'investee_encouraged_industry', 'planned_holding_months'})
PILLAR_FIELDS = {f for f, v in CATALOG.items() if v['family'] == 'pillar_two'} - {'group_revenue_eur'}
# Observational gates have no tax-engine semantics. Their answers never become
# a tax exemption, a professional ruling, or an invented zero/date.
EVENT_GATES = {
    'assessment_notice_on': ('assessment_received', '是否已收到这笔事项的评税或核定通知？', 'Have you received an assessment notice for this matter?'),
    'determination_on': ('determination_received', '这笔事项是否已有税务机关作出的决定？', 'Has the tax authority issued a decision on this matter?'),
    'first_notification_on': ('notification_received', '是否已收到或知悉这笔事项涉及的税务通知？', 'Have you received or become aware of the relevant tax notification?'),
    'tax_paid_on': ('tax_paid', '这笔事项是否已实际缴纳税款？', 'Has tax actually been paid on this matter?'),
    'remitted_on': ('tax_remitted', '这笔事项的代扣税款是否已解缴？', 'Has the withheld tax for this matter been remitted?'),
    'tp_adjustment_amount': ('tp_adjusted', '这笔事项是否已发生转让定价调整？', 'Has a transfer-pricing adjustment been made for this matter?'),
    'tp_adjustment_tax': ('tp_adjusted', '这笔事项是否已发生转让定价调整？', 'Has a transfer-pricing adjustment been made for this matter?'),
    'tp_adjustment_paid_on': ('tp_adjustment_paid', '转让定价调整的税款是否已经实际缴纳？', 'Has the tax arising from the transfer-pricing adjustment actually been paid?'),
    'pboc_benchmark_rate': ('tp_adjusted', '这笔事项是否已发生转让定价调整？', 'Has a transfer-pricing adjustment been made for this matter?'),
}
# Same-object dependencies. No answers from another flow/entity can unlock them.
GATES = {f: ('reinvested_in_cn', True) for f in REINVESTMENT_DETAILS}
GATES.update({
    'foreign_tax_rate': ('foreign_taxed', True),
    'underlying_tax_share': ('underlying_profits_taxed', True),
    'gst_recovery_ratio': ('gst_input_fully_recoverable', False),
    'clawback_event_within_2y': ('stamp_relief_claimed', True),
    'asset_disposed_within_2y': ('stamp_relief_claimed', True),
    'government_exempt_condition_met': ('payee_is_government', True),
    'registration_filing_compliant': ('pure_equity_holding', True),
    'cn_asset_ratio': ('indirect_cn_target', True),
    'cn_income_ratio': ('indirect_cn_target', True),
    'cn_value_ratio': ('indirect_cn_target', True),
    'limited_functions_and_risks': ('indirect_cn_target', True),
    'foreign_tax_lower_than_cn': ('indirect_cn_target', True),
    'no_reasonable_commercial_purpose': ('indirect_cn_target', True),
})
FAMILY_NAMES = {
    'reinvestment': ('再投资安排', 'reinvestment arrangements'),
    'foreign_tax': ('境外所得及已缴税款', 'foreign income and taxes paid'),
    'substance': ('收款及经营活动', 'receipt and business activities'),
    'procedure': ('实际发生的税务手续', 'tax procedures that have actually occurred'),
    'pillar_two': ('集团补足税的适用范围', 'the scope of group top-up tax'),
    'cfc': ('境外被控企业相关规则', 'rules for controlled foreign companies'),
    'treaty': ('协定待遇的适用条件', 'eligibility for treaty treatment'),
    'restructuring': ('股权转让或重组方案', 'share transfer or restructuring arrangements'),
    'vat': ('增值税或消费税', 'VAT or GST'), 'interest': ('借款及利息', 'loans and interest'),
    'service': ('服务的履行情况', 'the performance of services'), 'royalty': ('许可及特许权收入', 'licensing and royalty income'),
    'residence': ('公司的居民身份', 'company residence'), 'indirect_transfer': ('间接股权转让', 'indirect share transfers'),
    'share_transfer': ('股权或资产处置', 'share or asset disposals'), 'ownership': ('持股和关联关系', 'ownership and related-party relationships'),
    'pricing': ('交易定价及相关资料', 'transaction pricing and supporting records'),
    'ip': ('知识产权安排', 'intellectual property arrangements'), 'core': ('这笔交易的计算条件', 'the calculation inputs for this transaction'),
}


def parts(key):
    scope, _, raw = key.rpartition('.')
    raw = raw.split(':', 1)[0]  # action predicates are not different fields
    field = raw if raw in CATALOG else re.sub(r'_(?:cn|hk|sg|\d{4})$', '', raw)
    return scope, raw, field


def _value(doc, key):
    if key.startswith('interview:'):
        return doc.get('domain_interview', {}).get(key, {}).get('value')
    # In comparison mode a feasible planned action can unlock planned details,
    # but it must never become an observation in an existing/paid case.
    if (doc.get('domain_workflow') or {}).get('mode') == 'plan_structure':
        actions = (doc.get('domain_answers') or {}).get('actions', {})
        for predicate, truth in (('is_true', True), ('is_false', False)):
            answer = actions.get(key + ':' + predicate)
            if answer in ('yes', 'no'):
                return truth if answer == 'yes' else not truth
    record = doc.get('canonical_fact_records', {}).get(key)
    if record is not None:
        if record.get('status') == 'unknown':
            return 'unknown'
        return record.get('value') if record.get('status') not in ('unknown', 'conflict', 'deferred') else None
    if key.startswith('group.'):
        field = key.partition('.')[2]
        # Mirror group propagation, but conservatively withhold conflicting values.
        members = (doc.get('domain_case') or {}).get('members') or list((doc.get('domain_case') or {}).get('roles', {}))
        vals = [r.get('value') for k, r in doc.get('canonical_fact_records', {}).items()
                if k.partition('.')[0] in members and k.endswith('.' + field)
                and r.get('status') not in ('unknown', 'conflict', 'deferred')]
        return vals[0] if vals and all(type(v) is type(vals[0]) and v == vals[0] for v in vals) else None
    return None


def requirements(question, doc, parameters=None):
    scope, raw, field = parts(question['key'])
    if question['key'].startswith('interview:'):
        return question.get('requirements', [])
    reqs = []
    if field in GATES:
        parent, expected = GATES[field]
        reqs.append({'key': scope + '.' + parent, 'op': 'eq', 'value': expected})
    if field in PILLAR_FIELDS:
        threshold = (parameters or (doc.get('domain_outcome') or {}).get('interview_parameters') or {}).get('pillar_revenue_min')
        reqs.append({'key': 'group.group_revenue_eur', 'op': 'ge', 'value': threshold})
        if field in ('p2_cbcr_revenue', 'p2_cbcr_pbt', 'p2_cbcr_simplified_taxes'):
            suffix = raw[len(field):]
            reqs.append({'key': scope + '.p2_qualified_cbcr' + suffix, 'op': 'eq', 'value': True})
    if field in EVENT_GATES:
        event, _, _ = EVENT_GATES[field]
        reqs.append({'key': 'interview:' + scope + '.' + event, 'op': 'eq', 'value': True})
    return reqs


def requirement_state(req, doc):
    value = _value(doc, req['key'])
    if value is None or value in ('unknown', 'conflict'):
        return 'waiting'
    if req['op'] == 'ge':
        if isinstance(value, bool) or not isinstance(value, (float, int)) or req['value'] is None:
            return 'waiting'
        passed = value >= req['value']
    else:
        if type(value) is not type(req['value']):
            return 'waiting'
        passed = value == req['value']
    return 'ready' if passed else 'not_applicable'


def interview_status(question, doc, parameters=None):
    field = parts(question['key'])[2]
    if not question['key'].startswith(('interview:', 'calendar:')) and field not in CATALOG:
        return 'needs_policy_review'
    states = [requirement_state(r, doc) for r in requirements(question, doc, parameters)]
    return 'not_applicable' if 'not_applicable' in states else 'waiting' if 'waiting' in states else 'ready'


def eligible(question, doc):
    return interview_status(question, doc) == 'ready'


def _parent(key, child):
    _, raw, field = parts(key)
    if key.startswith('interview:'):
        event = next(v for v in EVENT_GATES.values() if v[0] == raw)
        zh, en, hint, source = event[1], event[2], '是/否', ''
    else:
        meta = CATALOG.get(field)
        if not meta:
            return None
        zh, en, hint, source = meta['zh'], meta['en'], meta['hint'], meta['source_zh']
        suffix = raw[len(field):]
        region = {'_cn': ('中国内地', 'Mainland China'), '_hk': ('香港', 'Hong Kong'), '_sg': ('新加坡', 'Singapore')}.get(suffix)
        if region:
            zh, en = region[0] + '：' + zh, region[1] + ': ' + en
    kind = 'boolean' if hint == '是/否' else 'number' if hint in ('金额', '%', '数值', '比率', '月数', '天数', '比值') else 'date' if hint == '日期' else 'text'
    return {'key': key, 'kind': 'data', 'prompt': zh, 'prompt_en': en, 'region': child.get('region', []),
            'source_hint': source, 'answer_schema': {'type': kind, 'hint': hint}, 'why': child.get('why', []),
            'interview_prerequisite': True}


def prepare_questions(result, doc):
    """Preserve raw engine needs and bounds; add only interview prerequisites."""
    parameters = result.get('interview_parameters', {})
    questions = deepcopy(result.get('questions', []))
    by_key = {q['key']: q for q in questions}
    for q in questions:  # append recursively; dependency cycles are checked by tests
        for req in requirements(q, doc, parameters):
            if req['key'] in by_key or _value(doc, req['key']) is not None:
                continue
            parent = _parent(req['key'], q)
            if parent:
                by_key[parent['key']] = parent
                questions.append(parent)
    for q in questions:
        q['requirements'] = requirements(q, doc, parameters)
        q['interview_status'] = interview_status(q, doc, parameters)
        meta = CATALOG.get(parts(q['key'])[2])
        if meta:
            zh, en = FAMILY_NAMES[meta['family']]
            plan = (doc.get('domain_workflow') or {}).get('mode') == 'plan_structure'
            q['context_zh'] = ('为比较候选方案，需核对' if plan else '为核对') + zh + '；这项提问不代表已认定相关安排或优惠适用。'
            q['context_en'] = ('To compare candidate arrangements, we need to check ' if plan else 'To check ') + en + '; asking does not establish that the arrangement or relief applies.'
    result['engine_question_count'] = result.get('question_count', len(result.get('questions', [])))
    result['questions'] = questions
    result['question_count'] = len(questions)
    result['interview_policy_version'] = POLICY_VERSION
    result['interview_counts'] = {status: sum(q['interview_status'] == status for q in questions)
                                  for status in ('ready', 'waiting', 'not_applicable', 'needs_policy_review')}


def next_question(questions, doc, facts_hash):
    parents = {r['key'] for q in questions for r in requirements(q, doc)}
    def order(q):
        _, _, field = parts(q['key'])
        priority = 0 if field == 'reinvested_in_cn' else 1 if q['key'] in parents else 2 if q['kind'] == 'blocking' else 3
        return priority, q['key'], q['kind']
    return next((q for q in sorted(questions, key=order)
                 if q['kind'] in ('data', 'blocking', 'joint', 'action')
                 and doc.get('domain_deferred', {}).get(q['key']) != facts_hash and eligible(q, doc)), None)
