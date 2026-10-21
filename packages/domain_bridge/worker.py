"""One-shot tax engine worker; JSON in/out, no chat DB or network access."""
from __future__ import annotations

from datetime import date
import json
import math
import os
from pathlib import Path
import sys

from packages.domain_bridge.bridge import verify_release


def _dates(value):
    if isinstance(value, dict):
        return {k: _dates(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_dates(x) for x in value]
    if isinstance(value, str) and len(value) == 10 and value[4:5] == '-' and value[7:8] == '-':
        try:
            return date.fromisoformat(value)
        except ValueError:
            pass
    return value


def _number(value):
    if value is None or not math.isfinite(value):
        return {'value': None, 'status': 'unbounded' if value is None or value > 0 else 'negative_unbounded'}
    return {'value': round(float(value), 2), 'status': 'finite'}


def _json_safe(value):
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, float) and not math.isfinite(value):
        return _number(value)
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    if isinstance(value, (set, frozenset)):
        return sorted(_json_safe(item) for item in value)
    return value


def _question(q):
    value = q.value or ''
    kind = 'boolean' if any(x in value.lower() for x in ('是/否', 'yes/no')) else 'date' if any(x in value.lower() for x in ('日期', 'date')) else 'number' if any(x in value.lower() for x in ('金额', '数', '比例', '比值', '%', '率', '月', '天', 'amount', 'number', 'ratio', 'rate', 'months', 'days', 'integer')) else 'text'
    return {'key': q.key, 'kind': q.kind, 'region': sorted(q.region), 'prompt': q.prompt,
            'why': q.why, 'impact': q.impact, 'source_hint': q.source_hint, 'forms': q.forms,
            'answer_schema': {'type': 'action' if q.kind == 'action' else kind, 'hint': value},
            'dependency_group': q.why}


def _attach_legal_refs(output):
    """Native item.cites are rule IDs; resolve their parameter/explicit sources."""
    import re
    from tax_graph.engine import RULES_BY_ID
    from tax_graph.params import Params
    params = Params()
    from tax_graph.engine import P2_THRESHOLD
    output['interview_parameters'] = {'pillar_revenue_min': min(params[pid] for pid in P2_THRESHOLD.values())}
    mapping = {}
    for rule_id in output.get('citations', []):
        rule = RULES_BY_ID.get(rule_id)
        sources = rule.sources if rule else (rule_id,)
        clauses = set()
        for source in sources:
            raw = params.rows[source]['cite_id'] if source in params.rows else source
            clauses.update(re.findall(r'[a-z][a-z0-9.-]+#[A-Za-z0-9()._-]+', raw))
        mapping[rule_id] = sorted(clauses)
    output['rule_citations'] = sorted(mapping)
    output['citation_map'] = mapping
    output['citations'] = sorted({cite for group in mapping.values() for cite in group})
    for region in output.get('regions', []):
        for side in ('guaranteed', 'best'):
            rows = []
            for row in region.get(side, []):
                row = list(row)
                row[5] = sorted({cite for rule_id in row[5] for cite in mapping.get(rule_id, [])})
                rows.append(row)
            region[side] = rows
    return output


def _fixed(template, event, case, answers, mode, today):
    from dataclasses import asdict
    from tax_graph.engine import CaseCtx, EX_POST, Undecidable, bounds
    from tax_graph.ex_ante import validate_core
    from tax_graph.planner import apply_data, _ruling_ticks, _abs, _question_for, _region_of_group
    from tax_graph.rules.tri import DISCRETION, MISSING, DATA
    from tax_graph.claims import claims
    case = apply_data(case, answers)
    missing = [key for key in template.vars(event) if key not in case.present]
    if missing:
        return {'status': 'blocked', 'questions': [], 'candidate_count': 0,
                'note': '现有结构需明确这些安排（不猜默认值）：' + ', '.join(missing)}
    graph = template.build(event, case.present, case)
    validate_core(graph)
    # A fixed assessment must never create/move entities or redesign historical holdings.
    if any(eid not in case.roles or e.attrs.get('placed_by_plan') or e.attrs.get('created_by_plan')
           for eid, e in graph.entities.items()) or any(h.designed for h in graph.holds):
        return {'status': 'blocked', 'questions': [], 'candidate_count': 0,
                'note': '现有结构与安排不一致：本次固定结构分析不允许新增或迁移公司。'}
    ticks = _ruling_ticks(answers)
    try:
        b = bounds(graph, lambda facts: CaseCtx(facts, ticks, EX_POST),
                   settled=case.settled, as_at=event.as_at, closed=case.closed, ticks=ticks)
    except Undecidable as exc:
        return {'status': 'blocked', 'questions': [], 'candidate_count': 1,
                'note': '相互依赖的未决项过多，不能给出精确上下界：' + str(exc)}
    questions = {}
    for group, needs in b.groups.items():
        for need in needs:
            if need.source not in (MISSING, DATA, DISCRETION):
                continue
            key = _abs(need, group, graph, b)
            if answers.answered(key):
                continue
            q = _question_for(key, 'ruling' if need.source == DISCRETION else 'blocking' if need.source == DATA else 'data',
                              _region_of_group(group, graph), [group[0]])
            item = _question(q)
            prior = questions.get(key)
            if prior:
                item['why'] = sorted(set(item['why']) | set(prior['why']))
                item['dependency_group'] = item['why']
                item['region'] = sorted(set(item['region']) | set(prior['region']))
                rank = {'ruling': 0, 'library': 1, 'blocking': 2, 'joint': 3, 'data': 4, 'action': 5}
                if rank[prior['kind']] < rank[item['kind']]:
                    item['kind'] = prior['kind']
            questions[key] = item
    regions = {}
    cites = set()
    for side, labels in (('guaranteed', b.L_hi), ('best', b.L_lo)):
        for flow_id, label in labels.items():
            for item in label.items:
                cites.update(item.cites)
                if item.deferred or not item.effective:
                    continue
                who = label.flow.payer if item.borne_by == 'payer' else label.flow.payee
                region = regions.setdefault(item.jur, {'jurisdictions': [item.jur], 'guaranteed': [], 'best': [],
                                                      'actions': [], 'conditions': sorted({q['key'] for q in questions.values() if item.jur in q['region']}), 'deadlines': []})
                region[side].append([flow_id, item.jur, item.levy, who,
                                     round(label.flow.amount * item.effective / 100, 2), list(item.cites), who in graph.group()])
    cl, archived = claims(b, case.settled, event.as_at, graph) if mode == 'review_paid' else ([], [])
    return {'status': 'needs_input' if questions else 'ready', 'questions': list(questions.values()),
            'question_count': len(questions), 'candidate_count': 1, 'candidate': case.present,
            'objective': 'fixed_current_structure', 'upper': _number(b.hi), 'lower': _number(b.lo),
            'structure': {'entities': [[e.id, e.loc, '现有'] for e in graph.entities.values()],
                          'holds': [[h.holder, h.held, h.ratio, '案例陈述'] for h in graph.holds],
                          'flows': [[f.id, f.income, f.payer, f.payee, f.amount, f.on] for f in graph.flows]},
            'regions': list(regions.values()), 'citations': sorted(cites), 'claims': [asdict(c) for c in cl],
            'archived': archived, 'unmodelled': list(graph.unmodelled), 'notes': [],
            'note': '只分析明确给出的现有结构；未决事实与专业判断保留为条件。'}


def main():
    root = Path(os.environ['FSIE_TAX_ENGINE_RELEASE_DIR']).resolve()
    verify_release(root)
    sys.path.insert(0, str(root))
    from tax_graph.data.domain import Event
    from tax_graph.model import HoldEdge
    from tax_graph.planner import Answers, plan
    from tax_graph.scenarios import Case, RoleFacts, template_of

    request = json.load(sys.stdin)
    data = _dates(request['case'])
    roles = {key: RoleFacts(value['loc'], value.get('attrs', {}), value.get('type', 'COMPANY'))
             for key, value in data['roles'].items()}
    holds = {(h['holder'], h['held']): HoldEdge(h['holder'], h['held'], h['ratio'] if h['ratio'] is not None else 100,
                                             h.get('since'), h.get('cost'), unknown=('ratio',) if h['ratio'] is None else ())
             for h in data.get('holds', [])}
    case = Case(roles=roles, holds=holds, flows=data.get('flows', {}), present=data.get('present', {}),
                settled=data.get('settled', {}), closed=frozenset(tuple(x) for x in data.get('closed', [])),
                members=set(data['members']) if data.get('members') else None)
    a = request['answers']
    answers = Answers(data=_dates(a.get('data', {})), actions=a.get('actions', {}),
                      rulings=a.get('rulings', {}), library=a.get('library', {}))
    template = template_of(data['template'])
    event = Event(**data['event'])
    if template.check_case(event, case):
        output = {'status': 'blocked', 'questions': [], 'candidate_count': 0,
                  'note': '缺少模板要求的主体：' + ', '.join(template.check_case(event, case))}
        sys.stdout.write(json.dumps(output, ensure_ascii=False))
        return
    if request['mode'] != 'plan_structure':
        output = _fixed(template, event, case, answers, request['mode'], date.fromisoformat(request['today']))
        sys.stdout.write(json.dumps(_json_safe(_attach_legal_refs(output)), ensure_ascii=False, allow_nan=False))
        return
    result = plan(template, event, case, answers,
                  today=date.fromisoformat(request['today']))
    if result.questions:
        output = {'status': 'needs_input', 'questions': [_question(q) for q in result.questions[:100]], 'question_count': len(result.questions),
                  'candidate_count': len(result.evaluations), 'note': result.note}
    elif result.plan is None:
        output = {'status': 'blocked', 'questions': [], 'candidate_count': len(result.evaluations),
                  'note': result.note}
    else:
        p = result.plan
        output = {'status': 'ready', 'questions': [], 'candidate_count': len(result.evaluations),
                  'objective': 'minimise_model_tax_upper_bound', 'candidate': p['cand'],
                  'upper': _number(p['guaranteed']), 'lower': _number(p['best']),
                  'structure': p['structure'], 'regions': [
                      {'jurisdictions': sorted(region), **contents} for region, contents in p['regions'].items()],
                  'unmodelled': p['unmodelled'][:20], 'notes': p['notes'][:20],
                  'data_used': p['data_used'][:100], 'claims': p['claims'], 'note': result.note,
                  'citations': sorted({cite for r in p['regions'].values() for side in ('guaranteed', 'best')
                                       for item in r[side] for cite in item[5]})}
    sys.stdout.write(json.dumps(_json_safe(_attach_legal_refs(output)), ensure_ascii=False, allow_nan=False))


if __name__ == '__main__':
    main()
