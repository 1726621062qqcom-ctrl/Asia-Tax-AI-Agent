"""Plan/guard/execute/observe loop on the existing LangGraph runtime."""
from copy import deepcopy
from time import monotonic
from typing import TypedDict
from langgraph.graph import StateGraph, START, END
from packages.agent.tools import ToolDecision, SEARCH_KINDS, allowed_tools, tool_catalog, validate_call
from packages.agent.budget import BudgetExceeded, model_call
from packages.agent.tracing import instrument, emit
from packages.agent.research_context import fact_view, evidence_observation, required_search_kinds


class LoopState(TypedDict, total=False):
    payload: dict
    seen: list
    observations: list
    calls: list
    decision: dict
    stop: str | None


class ToolHarness:
    def __init__(self, workflow, planner=None):
        self.workflow = workflow
        from packages.agent.harness import plan_tool
        self.planner = planner or plan_tool
        graph = StateGraph(LoopState)
        graph.add_node('plan', self.plan)
        graph.add_node('execute', self.execute)
        graph.add_edge(START, 'plan')
        graph.add_conditional_edges('plan', lambda s: END if s.get('stop') else 'execute')
        graph.add_conditional_edges('execute', lambda s: END if s.get('stop') else 'plan')
        self.graph = graph.compile()

    def invoke(self, state):
        result = self.graph.invoke({'payload': deepcopy(state), 'seen': [], 'observations': [],
                                    'calls': [], 'stop': None}, {'recursion_limit': 12})
        payload = result['payload']
        emit('tool.loop_finished', stop_reason=result['stop'], tool_count=len(result['calls']))
        meta = deepcopy(payload['workflow'])
        meta.update(harness_version='1.1', harness_stop=result['stop'], tool_calls=result['calls'])
        if result['stop'] not in ('finished', 'waiting_user', 'analysis_ready'):
            meta.update(status='partial_failure' if payload['task_results'] else 'paused_gap',
                        reason_code=meta.get('reason_code') if meta.get('error_code') else result['stop'])
            if result['stop'] in ('planner_failed', 'tool_failed'):
                meta.setdefault('error_code', 'model_failed' if result['stop'] == 'planner_failed' else 'tool_failed')
                meta['retryable'] = True
                if not payload['task_results'] and not payload['patch']:
                    from packages.chat.service import WorkflowError
                    raise WorkflowError(meta['error_code'])
        if not payload['task_results']:
            payload['turn']['reply'] = ('I could not complete this lookup. You can narrow the question or provide a section or case number.'
                if payload['doc'].get('_ui_locale') == 'en' else '这次还没能完成查询。你可以缩小问题范围，或提供要核对的条文、案例编号。')
        payload['workflow'] = meta
        return payload

    def observation(self, state):
        payload = state['payload']
        view = fact_view(self.workflow.projected(payload), payload['text'])
        view.update(has_conflicts=bool(payload['conflicts']), has_pending_question=bool(payload.get('question')))
        return {'latest_user_message': payload['text'],
                'task': {k: payload['job'].get(k) for k in ('kind', 'query', 'uses_case')},
                'tools': tool_catalog(allowed_tools(self.workflow, payload)),
                'case_state': view,
                'required_search_kinds': required_search_kinds(payload['text']),
                'observations': state['observations'], 'budget': self.workflow.budget.snapshot()}

    def coverage(self, state):
        passages = [p for b in state['payload'].get('research_results', []) for p in b.get('passages', [])]
        return evidence_observation({'passages': passages}, state['payload']['text'])

    def finish(self, state):
        payload = state['payload']
        incomplete = self.coverage(state)['unlocated_issues']
        reason = 'evidence_gap' if incomplete or any(
            b['reason_code'] != 'evidence_available' for b in payload.get('research_results', [])) else 'completed'
        emit('tool.finish', reason_code=reason, unlocated_issues=incomplete, summary_source='server_rule')
        return {'stop': 'finished'}

    def pending_search(self, state):
        payload = state['payload']
        if not payload['job'].get('query'):
            return None
        attempted = {SEARCH_KINDS[c['tool']] for c in state['calls']
                     if c.get('tool') in SEARCH_KINDS and c.get('status') != 'rejected'}
        available = allowed_tools(self.workflow, payload)
        for kind in required_search_kinds(payload['text']):
            tool = next(name for name, value in SEARCH_KINDS.items() if value == kind)
            if kind not in attempted and tool in available:
                return ToolDecision(tool=tool, query=payload['job']['query'])
        return None

    @instrument('tool.plan')
    def plan(self, state):
        from packages.agent.harness import plan_tool
        from packages.chat.service import WorkflowError
        budget = self.workflow.budget
        # Known source coverage and explicit material types can end research without
        # another model proposal. Coverage is locator navigation, not a tax verdict.
        if (self.workflow.responder and state['payload'].get('research_results')
                and not self.pending_search(state) and not self.coverage(state)['unlocated_issues']):
            return self.finish(state)
        if budget.remaining() <= 0 or budget.counts.get('action', 0) >= budget.action_limit:
            return {'stop': 'budget_exhausted'}
        if self.workflow.responder and state['calls'] and (
                budget.counts.get('model', 0) >= budget.model_limit - 2 or budget.remaining() < 10):
            pending = self.pending_search(state)
            if pending and budget.remaining() >= 5:
                emit('tool.overridden', effective_tool=pending.tool, query=pending.query,
                     reason_code='reserve_answer_budget', summary_source='server_rule')
                return {'decision': pending.model_dump()}
            if not pending:
                return self.finish(state)
            return {'stop': 'budget_exhausted'}
        observation = self.observation(state)
        emit('tool.options', available_tools=[t['name'] for t in observation['tools']],
             task=observation['task'], observations=observation['observations'], budget=observation['budget'])
        try:
            proposal = self.planner({}, observation) if self.planner is plan_tool else model_call(self.planner, {}, observation)
            decision = ToolDecision.model_validate(proposal)
            emit('tool.proposed', tool=decision.tool, query=decision.query, decision_summary=decision.reason,
                 summary_source='model' if decision.reason else 'not_provided')
        except BudgetExceeded:
            return {'stop': 'budget_exhausted'}
        except WorkflowError as exc:
            payload = deepcopy(state['payload'])
            payload['workflow'].update(error_code=exc.code, retryable=True)
            return {'payload': payload, 'stop': 'planner_failed'}
        except Exception as exc:
            emit('tool.proposal_invalid', 'rejected', error_type=type(exc).__name__, reason_code='invalid_tool_proposal')
            return {'stop': 'planner_failed'}
        # Complete requested source types before optional material or an already
        # successful search. Missing primary law is not filled by unrelated rulings.
        pending = self.pending_search(state) if self.workflow.responder else None
        successful = any(c.get('tool') == decision.tool and c.get('reason_code') == 'evidence_available'
                         for c in state['calls'])
        if pending and decision.tool in SEARCH_KINDS and (
                successful or (decision.tool == 'search_rulings' and 'ruling' not in required_search_kinds(state['payload']['text']))):
            emit('tool.overridden', proposed_tool=decision.tool, effective_tool=pending.tool,
                 reason_code='prioritize_requested_sources', summary_source='server_rule')
            decision = pending
        elif self.workflow.responder and successful and not pending:
            emit('tool.overridden', proposed_tool=decision.tool, effective_tool='finish',
                 reason_code='avoid_redundant_search', summary_source='server_rule')
            return self.finish(state)
        if decision.tool == 'finish':
            payload = state['payload']
            query = payload['job'].get('query') or payload['turn'].get('query')
            pending = self.pending_search(state) if self.workflow.responder else None
            if pending:
                decision = pending
                emit('tool.overridden', proposed_tool='finish', effective_tool=decision.tool, query=query,
                     reason_code='lookup_requires_actual_search', summary_source='server_rule')
            else:
                if self.workflow.responder and state['payload'].get('research_results'):
                    return self.finish(state)
                emit('tool.finish', reason_code=decision.finish_reason, decision_summary=decision.reason)
                return {'stop': 'finished' if state['calls'] else 'no_tool_result'}
        reason = validate_call(self.workflow, state['payload'], decision, state['seen'])
        emit('tool.guard', 'rejected' if reason else 'accepted', tool=decision.tool,
             query=decision.query, reason_code=reason)
        if reason:
            # A malformed search proposal may fall back once to the original,
            # already-scoped task query. The rejected proposal never executes.
            original = state['payload']['job'].get('query') or state['payload']['turn']['query']
            repair = ToolDecision(tool=decision.tool, query=original) if decision.tool in SEARCH_KINDS and original else None
            if (self.workflow.responder and reason == 'tool_scope_rejected' and repair
                    and not any(c.get('repair') for c in state['calls'])
                    and not validate_call(self.workflow, state['payload'], repair, state['seen'])):
                emit('tool.repaired', tool=repair.tool, query=repair.query, reason_code='original_scoped_query')
                return {'decision': repair.model_dump(), 'calls': state['calls'] + [{
                    'tool': decision.tool, 'status': 'rejected', 'reason_code': reason,
                    'proposed_query': decision.query, 'query': original, 'repair': 'original_scoped_query'}]}
            return {'stop': reason, 'calls': state['calls'] + [
                {'tool': decision.tool, 'status': 'rejected', 'reason_code': reason, 'proposed_query': decision.query}]}
        return {'decision': decision.model_dump()}

    @instrument('tool.execute')
    def execute(self, state):
        from packages.agent import dialogue
        from packages.chat.service import WorkflowError
        payload = deepcopy(state['payload'])
        decision = ToolDecision.model_validate(state['decision'])
        emit('tool.executing', tool=decision.tool, query=decision.query)
        # Recheck immediately before execution, even after schema validation.
        rejection = validate_call(self.workflow, payload, decision, state['seen'])
        if rejection:
            emit('tool.guard', 'rejected', tool=decision.tool, reason_code=rejection, phase='before_execution')
            return {'stop': rejection}
        started = monotonic()
        try:
            if decision.tool in SEARCH_KINDS:
                job = {**payload['job'], 'kind': 'reference_lookup', 'query': decision.query,
                       'tool_kind': SEARCH_KINDS[decision.tool]}
                # Preserve all scope and case linkage from the original task.
                turn = {**payload['turn'], 'intent': 'research', 'query': decision.query}
                update = self.workflow.execute({**payload, 'job': job, 'turn': turn, 'research_only': True})
            elif decision.tool == 'prepare_analysis':
                update = self.workflow.execute({**payload, 'job': {**payload['job'], 'kind': 'consultation'}})
            else:
                self.workflow.budget.consume('action')
                doc = self.workflow.projected(payload)
                if decision.tool == 'read_case_facts':
                    reply = dialogue.summary_text(doc, doc.get('_ui_locale', 'zh'))
                else:
                    view = fact_view(doc, payload['text'])
                    gaps = view['blocking_fact_gaps'] + view['nonblocking_fact_gaps']
                    reply = ('Information still needed:\n' if doc.get('_ui_locale') == 'en' else '还需补充的信息：\n') + '\n'.join(
                        dialogue.gap_line(g, doc.get('_ui_locale', 'zh')) for g in gaps)
                    if not gaps:
                        reply += ('The requested facts are recorded; their legal effect still needs review.' if doc.get('_ui_locale') == 'en' else
                                  '当前访谈必需项已记录；仍需核对事实和法源，不代表已满足免税条件。')
                if self.workflow.responder:
                    reply = ''  # Read-only materials are rendered once at finalization.
                meta = {**payload['workflow'], 'status': 'completed', 'reason_code': 'read_only_result'}
                update = self.workflow.result(payload, {**payload['turn'], 'reply': reply}, meta,
                                              payload['job'], 'read_only_result')
            payload.update(update)
        except BudgetExceeded:
            emit('tool.result', 'error', tool=decision.tool, reason_code='budget_exhausted')
            return {'stop': 'budget_exhausted'}
        except Exception as exc:
            emit('tool.result', 'error', tool=decision.tool, error_type=type(exc).__name__, error_code=getattr(exc, 'code', None))
            # Do not send exception text, source originals or credentials to planner.
            meta = deepcopy(payload['workflow'])
            meta.update(status='partial_failure', reason_code='retrieval_failed' if
                        isinstance(exc, WorkflowError) and exc.code == 'knowledge_unavailable' else 'tool_failed',
                        error_code=exc.code if isinstance(exc, WorkflowError) else 'tool_failed', retryable=True)
            payload['workflow'] = meta
            return {'payload': payload, 'stop': 'tool_failed', 'calls': state['calls'] + [
                {'tool': decision.tool, 'status': 'failed', 'reason_code': 'tool_failed'}]}
        call_id = f'tool-{len(state["calls"]) + 1}'
        payload['task_results'][-1]['tool_call_id'] = call_id
        reason = payload['workflow'].get('reason_code')
        result = {'tool': decision.tool, 'status': payload['workflow']['status'], 'reason_code': reason,
                  'query': decision.query,
                  'duration_ms': round((monotonic() - started) * 1000, 2)}
        emit('tool.result', **result)
        # Planner sees metadata only. Never copy payload['turn']['reply'] or bundle text.
        observation = {'tool': decision.tool, 'query': decision.query, 'reason_code': reason}
        if decision.tool in SEARCH_KINDS:
            bundle = payload.get('research') or {}
            observation.update(evidence_observation(bundle, payload['text']))
            observation['cumulative_coverage'] = self.coverage({'payload': payload})
            emit('tool.coverage', tool=decision.tool, **evidence_observation(bundle, payload['text']))
        elif decision.tool == 'check_fact_gaps':
            view = fact_view(self.workflow.projected(payload), payload['text'])
            observation.update(view)
            observation['missing_fields'] = [g['field'] for g in view['blocking_fact_gaps'] + view['nonblocking_fact_gaps']]
        # Missing case facts constrain a conclusion, not the remaining source searches.
        stop = 'analysis_ready' if payload.get('analysis_result') else \
            'tool_failed' if payload['workflow'].get('error_code') else \
            'budget_exhausted' if reason == 'budget_exhausted' else None
        if stop == 'budget_exhausted':
            emit('tool.finish', reason_code=stop, summary_source='server_rule')
        return {'payload': payload, 'seen': state['seen'] + [(decision.tool, decision.query)],
                'calls': state['calls'] + [result], 'observations': state['observations'] + [observation], 'stop': stop}
