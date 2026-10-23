"""Chat adapter for the existing deterministic tax engine; no arithmetic by the LLM."""
from copy import deepcopy
import math
import re
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from packages.domain_bridge import state
from packages.domain_bridge.coordinator import DomainCoordinator
from packages.domain_bridge.response_summary import summary
from packages.agent.budget import current_budget, model_call
from packages.agent.tools import ToolDecision, tool_catalog


class InputFact(BaseModel):
    model_config = ConfigDict(extra='forbid')
    value: str | float | bool
    quote: str = Field(min_length=1, max_length=1000)


class CalculationProposal(BaseModel):
    model_config = ConfigDict(extra='forbid')
    action: Literal['calculate', 'answer', 'cancel'] = 'calculate'
    use_saved_case: bool = False
    inputs: dict[str, InputFact] = Field(default_factory=dict, max_length=12)
    answer: InputFact | None = None


FIELDS = {
    'payer': ('付款公司地区（CN/HK/SG）', 'payer country (CN/HK/SG)'),
    'recipient': ('收款公司地区（CN/HK/SG）', 'recipient country (CN/HK/SG)'),
    'recipient_type': ('收款人是公司还是个人', 'whether the recipient is a company or individual'),
    'income': ('收入是否为公司股息', 'whether this is a company dividend'),
    'direct': ('是否由收款公司直接持有付款公司股份', 'whether the recipient directly holds the payer'),
    'amount': ('本笔股息金额', 'the dividend amount'),
    'currency': ('币种', 'currency'),
    'ratio': ('直接持股比例（%）', 'direct holding percentage'),
    'since': ('取得股份的完整日期（YYYY-MM-DD）', 'full acquisition date (YYYY-MM-DD)'),
    'on': ('股息支付的完整日期（YYYY-MM-DD）', 'full dividend payment date (YYYY-MM-DD)'),
}
PERSISTED = ('schema_version', 'migration', 'canonical_fact_records', 'legacy_bindings', 'facts',
             'domain_definition', 'domain_case', 'domain_interview', 'domain_answers', 'domain_outcome', 'domain_today',
             'domain_confirmation', 'domain_workflow', 'domain_deferred', 'integration_runs', 'analyses',
             'fact_history', 'fact_context', 'confirmed_revision', 'confirmed_facts', 'domain_professional_history')

PROMPT = '''用户要求计算税额、估算税款或继续补充计算资料时，intent用calculation，facts={}，query=""，reply只说明下一步，不自行算税。
额外返回calculation对象：{"action":"calculate|answer|cancel","use_saved_case":false,"inputs":{},"answer":null}。
inputs只允许以下字段，payer和recipient都表示地区代码（CN/HK/SG），不能填公司名称；income（dividend/other），recipient_type（company/individual），direct（boolean），amount（number），currency（CNY/HKD/SGD等），ratio（0..100），since和on（完整YYYY-MM-DD）。
since专指取得股份日期，on专指股息支付日期，两个日期同时出现必须分别提取。用户说香港公司时recipient_type=company。完整示例字段：payer="CN", recipient="HK", recipient_type="company", income="dividend", direct=true, amount=1000000, currency="CNY", ratio=100, since="2020-01-01", on="2026-10-11"。示例仅说明类型，不是本案事实。
每个字段必须为{"value":值,"quote":"本轮用户原文中的连续引用"}。只提取本轮明确提供的信息，没说就省略，不从历史、旧研究回复或常识补值。不把个人投资套作公司股息，不把售股收益当股息。
用户只说直接持股不能推定100%，不能把只有年份的日期补成1月1日。
使用已经保存的结构时use_saved_case=true，不重新构造公司关系。涉及多笔款项、间接持股或多个结构不能混入一个inputs，请让用户先选一笔或完善结构。
calculation_context提供计算草稿；在草稿等待补充时，将本轮回答提取到对应inputs，可继续calculate。只有本轮仍在请求计算或回答计算问题才用calculation；解释规则、查法条、闲聊仍走原来的intent。
calculation_pending提供引擎当前问题。回答这个问题时action=answer，answer={"value":值,"quote":"本轮原文引用"}，不传问题key、权限、规则、税率。用户暂停或取消计算action=cancel。'''


def supported_value(key, fact, text):
    """Require a literal source span and mechanically check numeric/date/enum values."""
    q, v = fact.quote, fact.value
    if q not in text or key not in FIELDS:
        return False
    if key in ('since', 'on'):
        from packages.agent.fact_context import date_span
        return isinstance(v, str) and bool(date_span(v, q))
    if key in ('amount', 'ratio'):
        if isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) or v < 0:
            return False
        if key == 'ratio' and v > 100:
            return False
        if re.search(r'[-−]\s*\d', q):
            return False
        numbers = re.findall(r'(\d[\d,]*(?:\.\d+)?)\s*(亿|万|million|thousand)?', q, re.I)
        factors = {'亿': 1e8, '万': 1e4, 'million': 1e6, 'thousand': 1e3, '': 1}
        return any(abs(float(n.replace(',', '')) * factors[u.lower()] - v) < .000001 for n, u in numbers)
    aliases = {
        'payer': {'CN': r'中国|内地|大陆|China|mainland|\bCN\b', 'HK': r'香港|Hong Kong|\bHK\b', 'SG': r'新加坡|Singapore|\bSG\b'},
        'currency': {'CNY': r'人民币|CNY|RMB', 'HKD': r'港币|港元|HKD', 'SGD': r'新币|新加坡元|SGD', 'USD': r'美元|USD', 'EUR': r'欧元|EUR', 'JPY': r'日元|JPY'},
        'recipient_type': {'company': r'公司|企业|company|corporation', 'individual': r'个人|自然人|individual|personally'},
        'income': {'dividend': r'股息|分红|dividend', 'other': r'卖|出售|售股|sale|interest|利息|royalty|特许权'},
    }
    aliases['recipient'] = aliases['payer']
    if key in aliases:
        return isinstance(v, str) and v in aliases[key] and bool(re.search(aliases[key][v], q, re.I))
    if key == 'direct':
        if not isinstance(v, bool):
            return False
        yes = r'直接持|直接拥有|direct(?:ly)? (?:hold|own)|\bdirect\b'
        no = r'间接|不直接|indirect'
        return bool(re.search(no if not v else yes, q, re.I)) and (not v or not re.search(no, q, re.I))
    return False


def saved_inputs(doc):
    """Reuse existing case facts without having the model re-extract past answers."""
    if doc.get('fact_context', {}).get('transaction_scope', {}).get('status') == 'multiple_unbound':
        return {}
    mapping = {'payer': 'payer_jurisdiction', 'income': 'income_type', 'recipient_type': 'recipient_type',
               'direct': 'direct_or_indirect_holding', 'amount': 'dividend_amount', 'currency': 'dividend_currency',
               'ratio': 'holding_percentage_pct', 'since': 'acquisition_date', 'on': 'receipt_date'}
    output = {}
    for key, field in mapping.items():
        record = doc.get('facts', {}).get(field) or {}
        value = record.get('value')
        if value is None or value in ('unknown', 'conflict') or record.get('status') in ('unknown', 'conflict', 'deferred'):
            continue
        if field in doc.get('fact_context', {}).get('partial_dates', {}):
            continue
        if key == 'direct':
            if value not in ('direct', 'indirect'):
                continue
            value = value == 'direct'
        if key == 'income' and value != 'dividend':
            value = 'other'
        output[key] = {'value': value, 'quote': '', 'saved_field': field, 'revision': record.get('revision')}
    # The legal jurisdiction under review does not establish the recipient's location.
    return output


def current_question(doc):
    outcome = doc.get('domain_outcome') or {}
    if outcome.get('stale') or not doc.get('domain_definition'):
        return None
    if outcome.get('facts_hash') != DomainCoordinator.domain_fingerprint(doc):
        return None
    from packages.domain_bridge.question_order import eligible
    qid = (doc.get('domain_workflow') or {}).get('pending_question_id')
    return next((q for q in outcome.get('questions', []) if q['id'] == qid and eligible(q, doc)), None)


class DraftCoordinator(DomainCoordinator):
    """Reuse engine orchestration on a private copy; ChatService commits once."""
    def __init__(self, doc):
        self.doc = doc

    def domain_load(self, *args):
        return self.doc, False

    def finish(self, owner, doc, revision, request_id):
        return doc


def prepare(workflow, graph):
    from packages.chat.service import invalidate, apply_facts
    from packages.agent.tracing import emit
    doc, text = deepcopy(graph['doc']), graph['text']
    from packages.chat.attachments import attachment_source
    source = attachment_source(text)
    if source is not None:
        text = source
    english = doc.get('_ui_locale') == 'en'
    proposal = CalculationProposal.model_validate(graph['turn'].get('calculation') or {})
    context = deepcopy(doc.get('calculation_context') or {'inputs': saved_inputs(doc)})
    previous_saved_inputs = deepcopy(context.get('inputs', {}))
    if source is not None:
        context['inputs'] = {}
    context.setdefault('inputs', {})
    context['active'] = True
    update = {}
    result = None
    tool_calls = []
    status = 'waiting_user'
    reply = ''
    if proposal.action == 'cancel':
        context['active'] = False
        reply = 'Calculation paused.' if english else '已暂停计算。'
        if doc.get('domain_workflow'):
            doc['domain_workflow']['status'] = 'paused'
            update['domain_workflow'] = doc['domain_workflow']
    elif proposal.action == 'answer':
        q = current_question(doc)
        answer = proposal.answer
        if not q or not answer or answer.quote not in text or q['kind'] not in ('data', 'blocking', 'joint', 'action'):
            reply = 'I could not match this message to a valid pending question. Please open Case details to review the current information, or state what you want analyzed.' if english else '这条消息未能对应到有效的待答问题。请打开案例细节核对当前信息，或直接说明本次希望分析的内容；本轮没有记录答案。'
        else:
            v = answer.value
            schema = q.get('answer_schema', {}).get('type', 'text')
            yes = bool(re.fullmatch(r'(?:是|是的|有|已满足|yes|true)(?:[，,。.!！ ].*)?', answer.quote.strip(), re.I))
            no = bool(re.fullmatch(r'(?:否|不是|没有|不满足|no|false)(?:[，,。.!！ ].*)?', answer.quote.strip(), re.I))
            valid = (schema in ('boolean', 'action') and (yes or no)) or (schema == 'number' and supported_value('amount', answer, text)) or (schema == 'date' and supported_value('on', answer, text)) or (schema == 'text' and str(v) == answer.quote)
            if q['kind'] != 'action' and str(v) == 'unknown' and re.fullmatch(r'不知道|未知|不清楚|unknown|not sure', answer.quote, re.I):
                valid = True
            elif schema in ('boolean', 'action'):
                v = ('yes' if yes else 'no') if q['kind'] == 'action' else yes
            if not valid:
                reply = 'Please give a clear yes/no, number, date or the requested text.' if english else '请直接提供本题需要的“是/否”、数字、完整日期或原文；无法可靠识别时不会替你填写。'
            else:
                workflow.budget.consume('action')
                emit('tool.executing', tool='calculate_tax', operation='answer')
                DraftCoordinator(doc).domain_answer(graph['owner'], doc['id'], doc['revision'], graph['request_id'], q['key'], q['kind'], v, q['id'])
                result = doc['domain_outcome']
                tool_calls.append({'tool': 'calculate_tax', 'status': 'completed', 'reason_code': 'answer_and_recalculate'})
    else:
        rejected = []
        previous_inputs = deepcopy(previous_saved_inputs if source is not None else context['inputs'])
        for key, fact in proposal.inputs.items():
            if isinstance(fact.value, str) and key in ('amount', 'ratio') and re.fullmatch(r'\d+(?:\.\d+)?', fact.value):
                fact = fact.model_copy(update={'value': float(fact.value)})
            if isinstance(fact.value, str) and key == 'direct' and fact.value.lower() in ('true', 'false'):
                fact = fact.model_copy(update={'value': fact.value.lower() == 'true'})
            if key in ('payer', 'recipient') and isinstance(fact.value, str):
                normalized = {'中国': 'CN', '中国公司': 'CN', '中国内地': 'CN', '中国大陆': 'CN', '香港': 'HK', '香港公司': 'HK', '新加坡': 'SG', '新加坡公司': 'SG'}.get(fact.value)
                if normalized:
                    fact = fact.model_copy(update={'value': normalized})
            if supported_value(key, fact, text):
                context['inputs'][key] = fact.model_dump()
            else:
                context['inputs'].pop(key, None)
                rejected.append(key)
        if context['inputs'] != previous_inputs and doc.get('domain_outcome'):
            stale = deepcopy(doc['domain_outcome'])
            stale['stale'] = True
            update.update(domain_outcome=stale, domain_confirmation=None)
        values = {k: v['value'] for k, v in context['inputs'].items()}
        use_saved = proposal.use_saved_case and not proposal.inputs
        missing = [k for k in FIELDS if k not in values]
        if values.get('recipient_type') == 'individual' or re.search(r'我个人|个人投资|个人持有|自然人|personally|individual investor', text, re.I):
            context['inputs'] = {}
            reply = 'Personal tax calculations are outside this company engine.' if english else '当前引擎计算的是公司结构，不能把个人投资套成公司股息。个人税款本轮未计算。'
        elif re.search(r'两笔|多笔|(?:两家|多家).*分别.*(?:股息|分红)|two dividends|multiple (?:dividends|transactions)', text, re.I):
            context['inputs'] = {}
            reply = 'Please select one transaction and restate its facts.' if english else '这里有多笔交易，请先选定一笔并明确它的金额、公司关系和日期，避免混算。'
        elif source is not None and any(k in previous_saved_inputs and previous_saved_inputs[k]['value'] != v['value'] for k, v in context['inputs'].items()):
            changed = [FIELDS[k][english] for k, v in context['inputs'].items() if k in previous_saved_inputs and previous_saved_inputs[k]['value'] != v['value']]
            reply = ('The attachment differs from the saved case in: ' if english else '附件与当前案例的以下信息不一致：') + '、'.join(changed) + ('。请确认是在更正当前案例，还是另一笔交易；本轮未覆盖旧事实或计算税额。' if not english else '. Please confirm whether this corrects the current case or describes another transaction. No saved facts were overwritten and no tax was calculated.')
            context['inputs'] = previous_saved_inputs
            update = {}
        elif rejected:
            reply = ('I could not verify these inputs against your message: ' if english else '以下信息无法从你的原话可靠核对，请明确补充：') + ', '.join(FIELDS.get(k, (k, k))[english] for k in rejected)
        elif not use_saved and (values.get('income') == 'other' or values.get('direct') is False):
            reply = ('This chat intake supports direct corporate dividends. For other income or indirect structures, save the full structure first and ask me to calculate it.' if english else '聊天中新建计算目前支持公司直接持股的股息。其他收入或间接结构需要先保存完整结构，再在聊天中要求计算，不能套用这条股息路径。')
        elif not use_saved and missing:
            reply = ('To calculate, please provide:\n' if english else '可以调用计算引擎，还需要以下信息：\n') + '\n'.join('- ' + FIELDS[k][english] for k in missing)
        elif not use_saved and (values['since'] > values['on'] or values['ratio'] <= 0):
            reply = 'Check the acquisition/payment dates and the positive holding percentage before calculation.' if english else '请核对持股比例和日期：直接持股比例需大于0，取得股份日期不能晚于本笔股息支付日期。'
        elif use_saved and not doc.get('domain_definition'):
            reply = 'No structure has been saved yet.' if english else '当前还没有保存可计算的结构，请先提供这笔交易的信息。'
        elif doc.get('fact_conflicts') or any(r.get('status') == 'conflict' for r in doc.get('canonical_fact_records', {}).values()):
            reply = 'Resolve the conflicting facts before calculating.' if english else '案情仍有相互冲突的信息，请先明确采用哪个值，再计算。'
        elif not use_saved and doc.get('domain_definition') and context.get('installed_hash') != DomainCoordinator.domain_fingerprint(doc):
            reply = 'The saved structure has changed. Ask to calculate the saved structure, or start a new conversation for this transaction.' if english else '已保存结构与聊天草稿不同。请明确使用已保存结构计算，或为这笔交易新建对话，避免覆盖已有结构。'
        else:
            observation = {'latest_user_message': text, 'task': {'kind': 'calculation', 'query': '', 'uses_case': True},
                           'tools': tool_catalog(['calculate_tax', 'finish']), 'case_state': {'calculation_inputs_ready': True},
                           'observations': [], 'budget': workflow.budget.snapshot()}
            from packages.agent.harness import plan_tool
            planner = workflow.tool_planner or plan_tool
            proposed = planner({}, observation) if planner is plan_tool else model_call(planner, {}, observation)
            decision = ToolDecision.model_validate(proposed)
            emit('tool.proposed', tool=decision.tool, reason=decision.reason)
            if decision.tool != 'calculate_tax':
                reply = 'The calculation has not run. Ask to calculate when ready.' if english else '本轮尚未执行计算；确认需要时可以继续说“计算税额”。'
            else:
                workflow.budget.consume('action')
                emit('tool.executing', tool='calculate_tax', operation='calculate')
                if not use_saved:
                    case = {'template': 'holding', 'currency': values['currency'],
                            'roles': {'OP': {'loc': values['payer']}, 'ULT': {'loc': values['recipient']}},
                            'holds': [{'holder': 'ULT', 'held': 'OP', 'ratio': values['ratio'], 'since': values['since']}],
                            'flows': {'up1': {}}, 'present': {'HOLD': None, 'financing': 'EQUITY', 'payment': False},
                            'event': {'dividend': values['amount'], 'on': values['on'], 'as_at': values['on']}, 'members': ['OP', 'ULT']}
                    # Engine 'financing' chooses dividend versus interest, not the
                    # shareholder's funding source. 'payment' shifts dates by a year.
                    # This adapter preserves the explicit dividend and stated date.
                    retained = {k: deepcopy(v) for k, v in doc.get('canonical_fact_records', {}).items()
                                if not k.startswith('legacy.') and v.get('origin') != 'model'} if all(
                                    (previous_inputs.get(k) or {}).get('value') == (context['inputs'].get(k) or {}).get('value') for k in FIELDS if k != 'amount') else {}
                    invalidate(doc)
                    mapping = {'payer_jurisdiction': ('payer', 'OP.loc'),
                               'holding_percentage_pct': ('ratio', 'hold:ULT>OP.ratio'),
                               'acquisition_date': ('since', 'hold:ULT>OP.since'),
                               'dividend_amount': ('amount', 'event.dividend'),
                               'dividend_currency': ('currency', 'case.currency'),
                               'receipt_date': ('on', 'event.on')}
                    apply_facts(doc, {**{field: values[key] for field, (key, _) in mapping.items()},
                                     'income_type': 'dividend', 'recipient_type': 'company',
                                     'direct_or_indirect_holding': 'direct'}, 'model')
                    for field in ('receipt_date', 'acquisition_date'):
                        doc.get('fact_context', {}).get('partial_dates', {}).pop(field, None)
                    previous_interview = deepcopy(doc.get('domain_interview', {}))
                    previous_deferred = deepcopy(doc.get('domain_deferred', {}))
                    state.install(doc, case, {field: address for field, (_, address) in mapping.items()})
                    for record in doc['canonical_fact_records'].values():
                        if not record['address'].startswith('legacy.'):
                            record.update(origin='model', status='candidate', confirmed_at=None)
                    for key, record in retained.items():
                        if key not in doc['canonical_fact_records']:
                            state.write(doc, key, record['value'], record['origin'], metadata={**record, 'confirmed_at': None})
                    state.sync(doc)
                    doc['domain_answers'] = {'data': {}, 'actions': {}, 'rulings': {}, 'library': {}}
                    doc['domain_workflow'] = {'mode': 'assess_current', 'status': 'active', 'pending_question_id': None}
                    doc['domain_confirmation'] = None
                    # Retain interview memory; context checks invalidate it when
                    # the transaction changes, not merely on recalculation.
                    doc['domain_interview'] = previous_interview
                    doc['domain_deferred'] = previous_deferred
                    doc['domain_today'] = None
                # An explicit new calculation request resumes a saved calculation.
                doc['domain_workflow']['status'] = 'active'
                DraftCoordinator(doc)._domain_execute(doc, graph['request_id'])
                result = doc['domain_outcome']
                tool_calls.append({'tool': 'calculate_tax', 'status': 'completed', 'reason_code': result['status']})
    if result:
        emit('tool.result', tool='calculate_tax', status=result['status'], release=result.get('release'), input_hash=result.get('input_hash'))
        update = {k: doc[k] for k in PERSISTED if k in doc}
        context['installed_hash'] = DomainCoordinator.domain_fingerprint(doc)
        context['active'] = result['status'] == 'needs_input'
        status = 'completed' if result['status'] == 'ready' else 'waiting_user'
        reply = summary(result, english, doc)
        pending = current_question(doc)
        if pending:
            reply += ('\n\n### 5. Complete the case details\n\nYou can fill in the available missing information together in Case details and submit it once to update the estimate. Choose “Unknown” where needed. The current estimate remains conditional; you can also add information in chat.' if english else
                      '\n\n### 5. 集中补充案例信息\n\n请打开“案例细节”，一次填写当前可补充的信息，提交后统一更新试算。不清楚的项目可选“暂不清楚”。当前结果仍保留条件，也可以继续在聊天中补充资料。')
        elif result.get('interview_counts', {}).get('waiting') or result.get('interview_counts', {}).get('needs_policy_review'):
            reply += ('\n\nSome questions depend on unresolved prerequisites or require review. No missing facts have been assumed; the estimate remains conditional.' if english else '\n\n部分问题因前提尚不明确或需要复核而暂不追问。缺失信息仍保留为未知，当前试算不是最终税额。')
    meta = {**graph['workflow'], 'effective_task': 'calculation', 'status': status,
            'reason_code': 'calculation_result' if result else 'calculation_input_required',
            'tool_calls': tool_calls, 'budget': workflow.budget.snapshot()}
    return {'turn': {'intent': 'chat', 'facts': {}, 'query': '', 'reply': reply},
            'patch': {}, 'conflicts': {}, 'research': None, 'answer': None, 'question': None,
            'dialogue': {**doc.get('dialogue', {}), 'status': 'suspended', 'pending': None},
            'workflow': meta, 'calculation_context': context, 'calculation_update': update}
