"""B owns the transaction; tax engine returns proposals bound to the same fact snapshot."""
from copy import deepcopy
from functools import wraps
from hashlib import sha256
from datetime import date, datetime
from math import isfinite
from uuid import uuid4
from zoneinfo import ZoneInfo

from packages.domain_bridge import state
from packages.domain_bridge.bridge import DomainCase, DomainError, run_plan, run_domain
from packages.chat.store import now


def error(code):
    from packages.chat.service import WorkflowError
    raise WorkflowError(code)


def bounded(method):
    @wraps(method)
    def invoke(*args, **kwargs):
        from packages.agent.budget import RunBudget, current_budget, BudgetExceeded
        if current_budget.get():
            return method(*args, **kwargs)
        token = current_budget.set(RunBudget(evidence_limit=35 if method.__name__ == 'domain_report' else 14,
                                                   search_limit=10 if method.__name__ == 'domain_report' else 3))
        try:
            return method(*args, **kwargs)
        except BudgetExceeded:
            error('execution_budget_exhausted')
        finally:
            current_budget.reset(token)
    return invoke


class DomainCoordinator:
    def domain_load(self, owner, case_id, revision, request_id, operation, payload):
        doc, duplicate = self.load(owner, case_id, revision, request_id)
        signature = state.digest({'operation': operation, 'payload': payload})
        old = doc.get('domain_payloads', {}).get(request_id)
        if duplicate and old != signature:
            error('request_payload_conflict')
        if not duplicate:
            doc.setdefault('domain_payloads', {})[request_id] = signature
        return doc, duplicate

    def domain_setup(self, owner, case_id, revision, request_id, case_input, data_approved,
                     mode='plan_structure', bindings=None):
        from packages.chat.service import invalidate, public
        if mode not in ('plan_structure', 'assess_current', 'review_paid'):
            error('unsupported_domain_mode')
        doc, duplicate = self.domain_load(owner, case_id, revision, request_id, 'setup',
                                         [case_input, data_approved, mode, bindings or {}])
        if duplicate:
            return public(doc)
        if not (doc.get('data_approved') or data_approved):
            error('data_confirmation_required')
        case = DomainCase.model_validate(case_input)
        if not case.currency:
            error('currency_required')
        invalidate(doc)
        state.install(doc, case.model_dump(mode='json'), bindings or {})
        doc['data_approved'] = True
        doc['domain_answers'] = {'data': {}, 'actions': {}, 'rulings': {}, 'library': {}}
        doc['domain_outcome'] = None
        doc['domain_today'] = None
        doc['domain_confirmation'] = None
        doc['domain_workflow'] = {'mode': mode, 'status': 'active', 'pending_question_id': None}
        return self.finish(owner, doc, revision, request_id)

    def _domain_execute(self, doc, request_id):
        from packages.agent.budget import current_budget
        workflow = doc.get('domain_workflow') or {'mode': 'plan_structure', 'status': 'active'}
        if workflow['status'] == 'paused':
            error('domain_paused')
        case = DomainCase.model_validate(state.project_case(doc))
        today = doc.get('domain_today') or datetime.now(ZoneInfo('Asia/Shanghai')).date().isoformat()
        inputs = state.answers(doc)
        try:
            result = run_plan(case, inputs, today=today) if workflow['mode'] == 'plan_structure' else \
                run_domain(case, inputs, today=today, mode=workflow['mode'])
        except DomainError as exc:
            error(exc.code)
        result.setdefault('input_hash', state.digest([case.model_dump(mode='json'), inputs, today, workflow['mode']]))
        result['facts_hash'] = self.domain_fingerprint(doc)
        result['map_version'] = state.MAP_VERSION
        result['based_on_revision'] = doc['revision'] + 1
        for question in result['questions']:
            question['id'] = 'domain:' + state.digest([result['input_hash'], question['kind'], question['key']])[:24]
            question['based_on_revision'] = doc['revision'] + 1
            question['input_hash'] = result['input_hash']
        pending = next((q for q in result['questions'] if q['kind'] in ('data', 'blocking', 'joint', 'action')
                        and doc.get('domain_deferred', {}).get(q['key']) != result['facts_hash']), None)
        workflow.update(status='active', pending_question_id=pending['id'] if pending else None)
        doc['domain_workflow'] = workflow
        doc['domain_today'] = today
        doc['domain_outcome'] = result
        if len(doc['messages']) >= 200:
            error('case_limit')
        text = '结构计算：' + result['status'] + '。'
        if pending:
            text += '\n下一项：' + pending['prompt'] + '\n请在结构分析面板回答；也可用“结构答复：答案”回复此题。'
        else:
            text += '\n请查看结构分析面板中的结果、专业问题和未建模事项。'
        doc['messages'].append({'id': str(uuid4()), 'role': 'assistant', 'kind': 'chat',
                                'text': text, 'created_at': now()})
        run = {'run_id': str(uuid4()), 'request_id': request_id, 'case_revision': doc['revision'] + 1,
               'mode': workflow['mode'], 'facts_hash': result['facts_hash'], 'input_hash': result['input_hash'],
               'release': result['release'], 'map_version': state.MAP_VERSION, 'today': today,
               'input': {'case': case.model_dump(mode='json'), 'answers': inputs}, 'output': deepcopy(result),
               'budget': current_budget.get().snapshot() if current_budget.get() else {}, 'at': now()}
        doc.setdefault('integration_runs', []).append(run)
        if len(doc['integration_runs']) > 100:
            error('case_limit')
        return result

    @staticmethod
    def domain_fingerprint(doc):
        return state.digest([state.project_case(doc), state.answers(doc),
                             (doc.get('domain_workflow') or {}).get('mode', 'plan_structure')])

    @bounded
    def domain_plan(self, owner, case_id, revision, request_id):
        from packages.chat.service import public
        from packages.agent.budget import RunBudget, current_budget
        doc, duplicate = self.domain_load(owner, case_id, revision, request_id, 'plan', {})
        if duplicate:
            return public(doc)
        if not doc.get('domain_definition'):
            error('domain_case_required')
        token = current_budget.set(RunBudget())
        try:
            self._domain_execute(doc, request_id)
        finally:
            current_budget.reset(token)
        return self.finish(owner, doc, revision, request_id)

    @bounded
    def domain_answer(self, owner, case_id, revision, request_id, key, kind, value, question_id=None,
                      disposition='answer', source='user', chat_text=None):
        from packages.chat.service import public, invalidate
        doc, duplicate = self.domain_load(owner, case_id, revision, request_id, 'answer',
                                         [key, kind, value, question_id, disposition, source, chat_text])
        if duplicate:
            return public(doc)
        if (doc.get('domain_workflow') or {}).get('status') == 'paused':
            error('domain_paused')
        if chat_text:
            doc.setdefault('domain_chat_payloads', {})[request_id] = {'text': chat_text, 'key': key, 'kind': kind,
                'value': value, 'question_id': question_id, 'disposition': disposition}
            doc['messages'].append({'id': str(uuid4()), 'role': 'user', 'text': chat_text, 'created_at': now()})
        prior = doc.get('domain_outcome') or {}
        if prior.get('stale') or prior.get('facts_hash') != self.domain_fingerprint(doc):
            error('question_changed')
        question = next((q for q in prior.get('questions', []) if q['key'] == key and q['kind'] == kind), None)
        if not question or (question_id and question['id'] != question_id):
            error('question_changed')
        if kind not in ('data', 'blocking', 'joint', 'action'):
            error('domain_answer_restricted')
        if disposition == 'defer':
            doc.setdefault('domain_deferred', {})[key] = prior['facts_hash']
            pending = next((q for q in prior['questions'] if q['kind'] in ('data', 'blocking', 'joint', 'action')
                            and doc['domain_deferred'].get(q['key']) != prior['facts_hash']), None)
            doc['domain_workflow']['pending_question_id'] = pending['id'] if pending else None
            return self.finish(owner, doc, revision, request_id)
        schema = question.get('answer_schema', {}).get('type', 'text')
        if kind == 'action':
            if value not in ('yes', 'no'):
                error('invalid_domain_answer')
        elif value != 'unknown':
            if isinstance(value, str):
                value = value.strip()
                if not value or len(value) > 1000:
                    error('invalid_domain_answer')
                if schema == 'boolean':
                    if value.casefold() not in ('true', 'false', 'yes', 'no', '是', '否'):
                        error('invalid_domain_answer')
                    value = value.casefold() in ('true', 'yes', '是')
                elif schema == 'date':
                    try:
                        date.fromisoformat(value)
                    except ValueError:
                        error('invalid_domain_answer')
                elif schema == 'number':
                    try:
                        value = float(value)
                    except ValueError:
                        error('invalid_domain_answer')
            if schema == 'number' and (isinstance(value, bool) or not isinstance(value, (float, int)) or not isfinite(value) or value < 0):
                error('invalid_domain_answer')
            if schema in ('date', 'text') and not isinstance(value, str):
                error('invalid_domain_answer')
            if schema == 'boolean' and not isinstance(value, bool):
                error('invalid_domain_answer')
        invalidate(doc, clear_domain_actions=kind != 'action', clear_domain_professional=kind != 'action')
        if kind == 'action':
            doc['domain_answers']['actions'][key] = value
        else:
            state.write(doc, key, value, source)
            state.sync(doc)
        doc.get('domain_deferred', {}).pop(key, None)
        self._domain_execute(doc, request_id)
        return self.finish(owner, doc, revision, request_id)

    @bounded
    def domain_control(self, owner, case_id, revision, request_id, action):
        from packages.chat.service import public
        doc, duplicate = self.domain_load(owner, case_id, revision, request_id, 'control', action)
        if duplicate:
            return public(doc)
        if not doc.get('domain_workflow'):
            error('domain_case_required')
        doc['domain_workflow']['status'] = 'paused' if action == 'pause' else 'active'
        if action == 'resume':
            doc['domain_deferred'] = {}
            self._domain_execute(doc, request_id)
        return self.finish(owner, doc, revision, request_id)

    def domain_confirm(self, owner, case_id, revision, request_id):
        from packages.chat.service import public
        doc, duplicate = self.domain_load(owner, case_id, revision, request_id, 'confirm', {})
        if duplicate:
            return public(doc)
        if not doc.get('domain_definition') or any(r['status'] == 'conflict' for r in doc['canonical_fact_records'].values()):
            error('resolve_conflicts')
        state.confirm(doc)
        doc['domain_confirmation'] = {'facts_hash': self.domain_fingerprint(doc), 'revision': revision + 1}
        return self.finish(owner, doc, revision, request_id)

    @bounded
    def domain_report(self, owner, case_id, revision, request_id, allow_partial=False):
        from packages.chat.service import public
        from packages.domain_bridge.reporting import build_report
        doc, duplicate = self.domain_load(owner, case_id, revision, request_id, 'report', allow_partial)
        if duplicate:
            return public(doc)
        current = self.domain_fingerprint(doc)
        if (doc.get('domain_confirmation') or {}).get('facts_hash') != current:
            error('confirmation_required')
        outcome = doc.get('domain_outcome') or {}
        if outcome.get('stale') or outcome.get('facts_hash') != current:
            error('domain_result_stale')
        if outcome.get('status') in ('unsupported', 'blocked') or (outcome.get('status') != 'ready' and not allow_partial):
            error('partial_confirmation_required')
        report = build_report(doc, owner, self.provider, allow_partial)
        doc['analyses'].append(report)
        doc['messages'].append({'id': str(uuid4()), 'role': 'assistant', 'kind': 'analysis',
                                'analysis_id': report['id'], 'created_at': now()})
        doc['state'] = 'review_required'
        return self.finish(owner, doc, revision, request_id)

    @bounded
    def domain_professional(self, owner, case_id, revision, request_id, question_id, value, reference, reviewer):
        from packages.agent.providers import ProviderSettings
        from packages.agent.contracts import Reference, TrustedContext
        from packages.chat.service import public, invalidate
        if reviewer not in ProviderSettings().reviewer_ids:
            error('review_forbidden')
        doc, duplicate = self.domain_load(owner, case_id, revision, request_id, 'professional',
                                         [question_id, value, reference, reviewer])
        if duplicate:
            return public(doc)
        prior = doc.get('domain_outcome') or {}
        q = next((q for q in prior.get('questions', []) if q['id'] == question_id), None)
        if not q or q['kind'] not in ('ruling', 'library') or prior.get('stale') or prior.get('facts_hash') != self.domain_fingerprint(doc):
            error('question_changed')
        if (doc.get('domain_workflow') or {}).get('status') == 'paused':
            error('domain_paused')
        if q['kind'] == 'ruling' and value != 'yes':
            error('unsupported_adverse_ruling')
        evidence = self.provider.get_evidence(Reference.model_validate(reference), 'display', TrustedContext(owner=owner, case_id=case_id))
        if evidence.status != 'ok' or not evidence.text or sha256(evidence.text.encode()).hexdigest() != evidence.content_hash:
            error('evidence_required')
        if q['kind'] == 'library':
            if not isinstance(value, list) or len(value) > 366:
                error('invalid_domain_answer')
            for day in value:
                date.fromisoformat(day)
        invalidate(doc, clear_domain_professional=False)
        bucket = 'rulings' if q['kind'] == 'ruling' else 'library'
        doc['domain_answers'][bucket][q['key']] = value
        doc.setdefault('domain_professional_history', []).append({'question': q, 'value': value,
                    'reference': reference, 'text_hash': evidence.content_hash, 'reviewer': reviewer, 'at': now()})
        self._domain_execute(doc, request_id)
        return self.finish(owner, doc, revision, request_id)

    def domain_message(self, owner, case_id, revision, request_id, text, question_id=None):
        doc = self.store.get(owner, case_id)
        saved = doc.get('domain_chat_payloads', {}).get(request_id)
        if saved:
            if saved['text'] != text or (question_id and question_id != saved['question_id']):
                error('request_payload_conflict')
            return self.domain_answer(owner, case_id, revision, request_id, saved['key'], saved['kind'],
                saved['value'], saved['question_id'], saved['disposition'], chat_text=text)
        pending = (doc.get('domain_workflow') or {}).get('pending_question_id')
        qid = question_id or pending
        q = next((q for q in (doc.get('domain_outcome') or {}).get('questions', []) if q['id'] == qid), None)
        # For a retry, require an explicit ID so payload identity can be checked.
        if not q:
            error('question_changed')
        value = text.partition('：')[2].strip() if text.startswith('结构答复：') else text.strip()
        if value in ('不知道', '未知', '不清楚'):
            value = 'unknown'
        if q['kind'] == 'action':
            value = {'是': 'yes', '否': 'no'}.get(value, value)
        return self.domain_answer(owner, case_id, revision, request_id, q['key'], q['kind'],
                                  value, qid, 'defer' if value == '暂缓' else 'answer', chat_text=text)
