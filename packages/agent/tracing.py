"""Bounded per-turn execution telemetry, never private chain-of-thought or prompts."""
from contextlib import contextmanager
from contextvars import ContextVar
from copy import deepcopy
from datetime import datetime, timezone
from functools import wraps
import re
from time import monotonic
from uuid import uuid4

current_trace = ContextVar('agent_execution_trace', default=None)
current_span = ContextVar('agent_execution_span', default=None)


def clean(value):
    """Known metadata only reaches here; redact credentials and contact details too."""
    if isinstance(value, dict):
        return {str(k)[:80]: clean(v) for k, v in list(value.items())[:40]
                if (str(k) in ('prompt_tokens', 'completion_tokens', 'total_tokens') and isinstance(v, int))
                or not re.search(r'password|secret|token|api_key|authorization|database_url', str(k), re.I)}
    if isinstance(value, (list, tuple)):
        return [clean(v) for v in value[:50]]
    if isinstance(value, str):
        value = re.sub(r'(?:postgres(?:ql)?(?:\+\w+)?|https?)://[^\s]+', '[redacted URL]', value)
        value = re.sub(r'\b(?:sk-|sb_secret_)[A-Za-z0-9_-]+', '[redacted credential]', value)
        value = re.sub(r'(?:password|api[_ -]?key|token|secret|密码|密钥)\s*[:=：]\s*\S+', '[redacted credential]', value, flags=re.I)
        value = re.sub(r'[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}', '[redacted email]', value)
        value = re.sub(r'(?<!\d)1[3-9]\d{9}(?!\d)', '[redacted phone]', value)
        return value[:600]
    return value if value is None or isinstance(value, (bool, int, float)) else type(value).__name__


class ExecutionTrace:
    def __init__(self, case_id, request_id):
        self.trace_id = str(uuid4())
        self.case_id, self.request_id = str(case_id), str(request_id)
        self.started = monotonic()
        self.events = []
        self.dropped = 0

    def emit(self, name, status='info', **data):
        if len(self.events) >= 250 and status != 'error':
            self.dropped += 1
            return
        event = {'seq': len(self.events) + 1, 'at': datetime.now(timezone.utc).isoformat(),
            'elapsed_ms': round((monotonic()-self.started)*1000, 2), 'name': name,
            'status': status, 'parent_span_id': current_span.get(), 'data': clean(data)}
        self.events.append(event)
        from packages.agent.logs import append
        append('events', {'version': '2.0', 'kind': 'event', 'trace_id': self.trace_id,
                         'case_id': self.case_id, 'request_id': self.request_id, **event})

    def snapshot(self):
        return {'version': '1.0', 'trace_id': self.trace_id, 'case_id': self.case_id,
                'request_id': self.request_id, 'dropped_events': self.dropped, 'events': deepcopy(self.events)}


def emit(name, status='info', **data):
    trace = current_trace.get()
    if trace:
        trace.emit(name, status, **data)


def trace_id():
    trace = current_trace.get()
    return trace.trace_id if trace else str(uuid4())


@contextmanager
def span(name, **data):
    started, span_id = monotonic(), str(uuid4())
    emit(name, 'started', span_id=span_id, **data)
    token = current_span.set(span_id)
    try:
        yield
    except BaseException as exc:
        emit(name, 'error', span_id=span_id, duration_ms=round((monotonic()-started)*1000, 2),
             error_type=type(exc).__name__, error_code=getattr(exc, 'code', None))
        raise
    else:
        emit(name, 'completed', span_id=span_id, duration_ms=round((monotonic()-started)*1000, 2))
    finally:
        current_span.reset(token)


def state_summary(state):
    turn, workflow = state.get('turn', {}), state.get('workflow', {})
    return {'intent': turn.get('intent'), 'action': turn.get('action'),
            'decision_summary': turn.get('decision_summary'),
            'task': state.get('job', {}).get('kind'), 'query': turn.get('query'),
            'fact_fields': sorted(state.get('patch', turn.get('facts', {}))),
            'conflict_fields': sorted(state.get('conflicts', {})),
            'status': workflow.get('status'), 'reason_code': workflow.get('reason_code'),
            'next_action': state.get('next_action'), 'has_question': bool(state.get('question'))}


def node(name, callback, state):
    with span('node.' + name, input=state_summary(state)):
        result = callback(state)
        emit('node.result', node=name, output=state_summary({**state, **result}))
        return result


def instrument(name):
    def decorate(callback):
        @wraps(callback)
        def wrapped(*args, **kwargs):
            with span(name):
                return callback(*args, **kwargs)
        return wrapped
    return decorate


def export(trace):
    from packages.agent.logs import append, summarize
    append('runs', summarize(trace.snapshot()))
