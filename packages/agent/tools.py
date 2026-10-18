"""Finite business tool surface. No model-supplied identity or write authority."""
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, model_validator

ToolName = Literal['finish', 'read_case_facts', 'check_fact_gaps', 'search_law',
                   'search_guidance', 'search_rulings', 'search_cases', 'prepare_analysis']
SEARCH_KINDS = {'search_law': 'law', 'search_guidance': 'guidance', 'search_rulings': 'ruling'}
DESCRIPTIONS = {
    'read_case_facts': '只读整理当前授权对话中的用户陈述；case_state已含字段状态，仅需要详细整理时调用，不确认事实。',
    'check_fact_gaps': '只读检查当前问题相关事实缺口，区分结论阻断项和可稍后补充项，不批准部分分析。',
    'search_law': '查询固定版本官方库的香港法条；只返回证据，保留地区、日期、编号，不推进访谈。',
    'search_guidance': '查询云端已登记的香港FSIE官方指引、FAQ及示例；不以法条或裁定代替指引。',
    'search_rulings': '查询PostgreSQL中登记的官方税务裁定，保留案件背景；不判断案例相似性或直接套用结论。',
    'finish': '结束本轮资料收集。说明已完成、依据不足或需要补充事实；不能确认事实或批准结论。',
    'prepare_analysis': '仅在用户明确要求且最新事实已经确认时生成待最终复核的内部稿。',
}


class ToolDecision(BaseModel):
    model_config = ConfigDict(extra='forbid')
    tool: ToolName
    query: str = Field(default='', max_length=500)
    reason: str = Field(default='', max_length=240)
    finish_reason: Literal['completed', 'evidence_gap', 'needs_user'] = 'completed'

    @model_validator(mode='after')
    def arguments(self):
        # Accept historical scripted decisions, expose only the accurate public name.
        if self.tool == 'search_cases':
            self.tool = 'search_rulings'
        self.query = self.query.strip()
        if self.tool in SEARCH_KINDS and len(self.query) < 2:
            raise ValueError('Search requires a query')
        if self.tool not in SEARCH_KINDS and self.query:
            raise ValueError('Read/control tools do not accept search arguments')
        return self


def tool_catalog(names):
    """Expose only capabilities allowed for this turn, with argument schemas."""
    return [{'name': name, 'description': DESCRIPTIONS[name],
             'arguments': {'query': 'string 2..500'} if name in SEARCH_KINDS else
             {'finish_reason': 'completed|evidence_gap|needs_user'} if name == 'finish' else {}}
            for name in names if name in DESCRIPTIONS]


def allowed_tools(workflow, state):
    from packages.agent.hybrid import requested_analysis
    from packages.agent.analysis_policy import analysis_eligibility
    tools = ['read_case_facts', 'check_fact_gaps']
    if workflow.scope(state, state['job']) == 'HK' and state['job'].get('query'):
        tools += list(SEARCH_KINDS)
    if (requested_analysis(state['text']) and not state['patch']
            and not analysis_eligibility(workflow.projected(state))):
        tools.append('prepare_analysis')
    return tools + ['finish']


def validate_call(workflow, state, decision, seen):
    from packages.agent.policy import rewrite_preserves_scope
    if decision.tool not in allowed_tools(workflow, state):
        return 'tool_not_allowed'
    if decision.tool in SEARCH_KINDS:
        original = state['job'].get('query') or state['turn']['query']
        job = {**state['job'], 'query': decision.query}
        if workflow.scope(state, job) != 'HK' or not rewrite_preserves_scope(original, decision.query):
            return 'tool_scope_rejected'
        if (('股息' in original or 'dividend' in original.casefold())
                and not ('股息' in decision.query or 'dividend' in decision.query.casefold())):
            return 'tool_scope_rejected'
        if 'fsie' in original.casefold() and 'fsie' not in decision.query.casefold():
            return 'tool_scope_rejected'
        rewrites = {query for tool, query in seen if tool == decision.tool and query != original}
        if decision.query != original and rewrites and decision.query not in rewrites:
            return 'rewrite_limit'
    if (decision.tool, decision.query) in seen:
        return 'duplicate_tool_call'
    return None
