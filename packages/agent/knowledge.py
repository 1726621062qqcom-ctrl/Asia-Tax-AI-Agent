"""Retrieve, authorize and project evidence before any answer is constructed."""
from __future__ import annotations
from hashlib import sha256
from time import monotonic
import re
from urllib.parse import urlsplit

from packages.agent.contracts import SearchRequest, SearchResult, TrustedContext
from packages.agent.providers import failure
from packages.agent.budget import BudgetExceeded


def applicable(evidence, request):
    if request.jurisdiction and evidence.jurisdiction != request.jurisdiction:
        return False
    if request.topic and evidence.topic != request.topic:
        return False
    when = request.applicable_date
    if when and ((evidence.effective_from and when < evidence.effective_from) or
                 (evidence.effective_to and when > evidence.effective_to)):
        return False
    return True


def retrieve(provider, request: SearchRequest, context: TrustedContext):
    if hasattr(provider, "for_request"):
        provider = provider.for_request()
    started = monotonic()
    calls = 0
    while True:
        calls += 1
        remaining = request.deadline_ms - int((monotonic() - started) * 1000)
        try:
            result = provider.search_evidence(request.model_copy(update={'deadline_ms': max(1, remaining)}), context)
            result = SearchResult.model_validate(result)
            if result.request_id != request.request_id or result.trace_id != request.trace_id:
                raise ValueError('Retrieval response identity mismatch')
        except BudgetExceeded:
            raise
        except Exception:
            result = failure(request, 'c', 'INVALID_RESPONSE')
        if result.status != 'error' or not result.error.retryable or result.error.code not in ('TIMEOUT', 'UNAVAILABLE', 'HTTP_ERROR') or calls >= 2 or remaining <= 1:
            break
        if (monotonic() - started) * 1000 >= request.deadline_ms:
            break
    evidence_for_model, passages, gaps = [], [], list(result.coverage.missing_requirements)
    verified_ids = []
    rejected = False
    for evidence in result.evidence[:request.limit if not request.locators else 50]:
        if not applicable(evidence, request):
            gaps.append('资料法域、主题或适用日期不匹配：' + evidence.evidence_id)
            rejected = True
            continue
        display = None
        if evidence.display_use == 'allowed' and evidence.display_ref:
            if (monotonic() - started) * 1000 >= request.deadline_ms:
                gaps.append('读取原文预算已用尽')
                break
            try:
                display = provider.get_evidence(evidence.display_ref, 'display', context)
            except BudgetExceeded:
                raise
            except Exception:
                display = None
            if (display is None or display.status != 'ok' or display.reference != evidence.reference() or
                display.content_hash != evidence.content_hash or
                sha256((display.text or '').encode()).hexdigest() != evidence.content_hash):
                display = None
                gaps.append('原文版本不可用或校验失败：' + evidence.evidence_id)
        if display is not None:
            if (evidence.verification_status == 'verified' and not evidence.is_synthetic and not result.is_synthetic
                and not evidence.drift and evidence.effective_from and request.applicable_date):
                verified_ids.append(evidence.evidence_id)
            url = evidence.url
            if url and urlsplit(url).scheme not in ('https', 'http'):
                url = None
            passage = {'unit_id': evidence.unit_id, 'source_id': evidence.source_id,
                'evidence_id': evidence.evidence_id, 'source_version_id': evidence.source_version_id,
                'locator': evidence.locator, 'text': display.text, 'title': evidence.title, 'url': url,
                'text_sha256': evidence.content_hash, 'is_synthetic': evidence.is_synthetic or result.is_synthetic,
                'model_use': evidence.model_use, 'policy_version': evidence.policy_version,
                'drift': evidence.drift, 'heading': evidence.heading, 'retrieved_at': evidence.retrieved_at,
                'snapshot_sha256': evidence.snapshot_sha256, 'coverage_cutoff': evidence.coverage_cutoff,
                'reference': evidence.reference().model_dump(), 'mapping_version': evidence.mapping_version}
            if evidence.locator_spans:
                for span in evidence.locator_spans:
                    text = display.text or ''
                    if span.end <= span.start or span.end > len(text) or sha256(text[span.start:span.end].encode()).hexdigest() != span.content_hash:
                        gaps.append('子条款定位校验失败：' + span.locator)
                        continue
                    passages.append({**passage, 'unit_id': evidence.unit_id + ':' + span.locator,
                                     'locator': span.locator, 'text': text[span.start:span.end],
                                     'text_sha256': span.content_hash, 'parent_content_hash': evidence.content_hash,
                                     'parent_span': [span.start, span.end]})
            else:
                passages.append(passage)
        # Permission to model alone is NOT permission to disclose a derived answer.
        if evidence.model_use == 'allowed' and evidence.display_use == 'allowed' and display is not None and evidence.model_text:
            if sha256(evidence.model_text.encode()).hexdigest() != evidence.content_hash:
                gaps.append('入模文本校验失败：' + evidence.evidence_id)
                continue
            evidence_for_model.append({'evidence_id': evidence.evidence_id,
                'text': evidence.model_text, 'source_version_id': evidence.source_version_id,
                'locator': evidence.locator, 'content_hash': evidence.content_hash,
                'display_allowed': evidence.display_use == 'allowed'})
    if result.status == 'error':
        reason = 'retrieval_failed'
    elif result.status == 'no_match':
        reason = 'no_match'
    elif rejected or gaps or result.status == 'partial' or result.coverage.truncated:
        reason = 'evidence_insufficient'
    elif not evidence_for_model:
        reason = 'evidence_restricted'
    else:
        reason = 'evidence_available'
    return {
        'status': 'unavailable' if result.status == 'error' else 'available' if passages else 'no_matching_units',
        'method': 'knowledge_provider_v0.1', 'query': request.query, 'provider': result.provider,
        'is_synthetic': result.is_synthetic, 'corpus_version': result.corpus_version,
        'retrieval_id': result.retrieval_id, 'reason_code': reason, 'passages': passages,
        'error': {'code': result.error.code, 'retryable': result.error.retryable} if result.error else None,
        'coverage': result.coverage.model_dump(), 'gaps': gaps, 'verified_evidence_ids': verified_ids,
        'model_evidence': evidence_for_model, 'retrieval_calls': calls,
        'timings_ms': {**result.timings_ms.model_dump(), 'total': round((monotonic() - started) * 1000, 2)},
    }


def display_result(bundle):
    """Separate frontend wire payload from the model-only projection."""
    return {k: v for k, v in bundle.items() if k != 'model_evidence'}


def public_gaps(gaps, english=False):
    """Keep diagnostic IDs in retrieval metadata, not in the conversation."""
    messages = []
    for gap in gaps:
        if '不匹配' in gap:
            message = 'Some results do not match the requested jurisdiction, topic or period.' if english else '部分检索结果与所问的地区、主题或期间不符，已排除。'
        elif any(word in gap for word in ('校验', '版本不可用', '未定位')):
            message = 'Some source passages could not be verified and were excluded.' if english else '部分原文未能核实，本次没有用来支持回答。'
        elif any(word in gap for word in ('预算', '只返回', 'truncat')):
            message = 'Only part of the relevant material was retrieved; narrow the search to continue.' if english else '本次只取得部分资料，可以缩小问题后继续查找。'
        else:
            message = 'The available sources do not fully cover this question.' if english else '现有资料还不能完整覆盖这个问题。'
        if message not in messages:
            messages.append(message)
    return messages[:3]


def citation_lines(bundle, evidence_ids):
    passages = {p['evidence_id']: p for p in bundle['passages']}
    originals = {e['evidence_id']: e for e in bundle['model_evidence']}
    lines, seen = [], set()
    for evidence_id in evidence_ids:
        passage = passages.get(evidence_id)
        if not passage:
            continue
        # Model text can cover a parent section with several display spans.
        label = originals.get(evidence_id, {}).get('locator') or passage.get('locator') or passage.get('title') or 'Official source'
        label = re.sub(r'[\[\]\n<>]', '', label)
        if label.startswith('hk.cap112.') and '#' in label:
            label = 'IRO ' + label.split('#', 1)[1].replace('s', 's.', 1)
        url = passage.get('url')
        item = f'[{label}]({url})' if url and urlsplit(url).scheme in ('https', 'http') else label
        if item not in seen:
            lines.append('- ' + item)
            seen.add(item)
    return lines


def append_followup(text, followup):
    for heading in ('法规及官方依据：\n', 'References:\n'):
        if heading in text:
            body, references = text.rsplit(heading, 1)
            return body.rstrip() + '\n\n' + followup + '\n\n' + heading + references
    return text + '\n\n' + followup


def join_answers(answers, locale='zh'):
    """Merge task answers once, retaining distinct content and final citations."""
    paragraphs, references = [], []
    for answer in answers:
        body = answer
        for heading in ('法规及官方依据：\n', 'References:\n'):
            if heading in body:
                body, footer = body.rsplit(heading, 1)
                references.extend(line for line in footer.splitlines() if line.strip())
                break
        paragraphs.extend(part.strip() for part in body.split('\n\n') if part.strip())
    body = '\n\n'.join(dict.fromkeys(paragraphs))
    if references:
        body += '\n\n' + ('References:\n' if locale == 'en' else '法规及官方依据：\n') + '\n'.join(dict.fromkeys(references))
    return body


def compose_answer(bundle, locale='zh', question='', responder=None):
    reason = bundle['reason_code']
    summaries = {
        'no_match': '本次查询未找到匹配依据，不能据此认定相关规定不存在，也不能形成税务结论。',
        'evidence_restricted': '资料未获准用于模型分析。已获展示许可的原文列在下方，供核对；当前不生成税务判断。',
        'evidence_insufficient': '依据覆盖不完整，以下仅列出可核对的资料，缺失条件暂不判断。',
        'retrieval_failed': '资料服务暂时不可用，请稍后重试。',
        'evidence_available': '已找到可用资料。以下为依据摘录及适用条件提示，具体案件仍需最终复核。',
    }
    english_summaries = {
        'no_match': 'No matching source was found for this query. This does not mean the rule does not exist, and no tax conclusion can be drawn.',
        'evidence_restricted': 'These materials are not approved for model analysis. Permitted source excerpts appear below for checking; no tax conclusion is generated.',
        'evidence_insufficient': 'Source coverage is incomplete. The following excerpts can be checked, but missing conditions remain unresolved.',
        'retrieval_failed': 'The source service is temporarily unavailable. Please try again later.',
        'evidence_available': 'Relevant sources were found. The excerpts and conditions below still require review against the facts of the case.',
    }
    english = locale == 'en'
    answer = {'summary': (english_summaries if english else summaries)[reason], 'conditions': [
        'Only within the scope of this query; verify the date, entity and case facts.' if english else
        '仅适用于本次查询范围；日期、主体及具体事实仍须核对。'],
              'claims': [], 'limitations': public_gaps(bundle['gaps'], english), 'review_status': 'pending_final_review'}
    context = bundle.get('query_context', {})
    if reason == 'no_match':
        answer['limitations'].append(('Unmatched query: ' if english else '未匹配的查询：') + bundle['query'])
        if context.get('applicable_date'):
            answer['limitations'].append(('Check sources for the applicable period: ' if english else '需核对适用期间的依据：') + str(context['applicable_date']))
        elif context.get('uses_case'):
            answer['limitations'].append('The accrual date and actual or planned status are unconfirmed, so the applicable rule version cannot be verified.' if english else '尚未确认累算日期及其实际/计划状态，不能核实个案适用的规则版本。')
        answer['limitations'].append('Add a section or ruling number, or refine the search terms. Known facts need not be re-entered.' if english else '可补充条文/案例编号或调整检索关键词；已知事实无需重新填写。')
    if bundle['is_synthetic']:
        answer['summary'] = ('[Synthetic test data, not an official tax source] ' if english else '【模拟联调资料，不是真实税务依据】') + answer['summary']
        answer['limitations'].append('Synthetic sources only verify the workflow and cannot support a real tax conclusion.' if english else '模拟资料仅验证流程，不能用于实际税务结论。')
    # Safe extractive fallback when the model is unavailable or citations fail.
    for evidence in bundle['model_evidence'][:7]:
        if not evidence.get('display_allowed', True):
            continue
        text = evidence['text'][:500]
        if text not in {claim['text'] for claim in answer['claims']}:
            answer['claims'].append({'text': text, 'evidence_ids': [evidence['evidence_id']], 'kind': 'excerpt'})
    if responder and bundle['model_evidence'] and not bundle['is_synthetic'] and reason != 'retrieval_failed':
        from packages.agent.grounded import claims_from_result
        permitted = [e for e in bundle['model_evidence'] if e.get('display_allowed', True)]
        try:
            claims, missing = claims_from_result(responder({'question': question or bundle['query'],
                'query': bundle['query'], 'locale': locale, 'coverage': reason,
                'uses_case': bundle.get('query_context', {}).get('uses_case', False),
                'case_facts_for_context_only': bundle.get('query_context', {}).get('case_facts', {}),
                'sources': permitted[:7]}), permitted[:7])
            if bundle.get('query_context', {}).get('uses_case') is False:
                # An independent rule lookup must not restart a case interview.
                missing = []
            answer.update(claims=claims, summary=claims[0]['text'], composition='grounded', missing_info=missing)
        except Exception:
            answer['composition'] = 'extractive_fallback'
    lines = [answer['summary'], '\n' + ('Conditions: ' if english else '适用条件：') + ('; ' if english else '；').join(answer['conditions'])]
    if answer.get('composition') == 'grounded':
        lines = [claim['text'] for claim in answer['claims']]
        if bundle['is_synthetic']:
            lines.insert(0, '[Synthetic test data, not an official tax source]' if english else '【模拟联调资料，不是真实税务依据】')
        if answer['missing_info']:
            lines.append(('To confirm:\n' if english else '还需确认：\n') + '\n'.join('- ' + item for item in answer['missing_info']))
    else:
        if answer.get('composition') == 'extractive_fallback':
            lines.append('The explanation could not be verified; the excerpts below are for checking.' if english else '这次解释未通过核验，下面保留可核对的原文摘录。')
        for index, claim in enumerate(answer['claims'], 1):
            lines.append(('\nSource excerpt [' if english else '\n依据摘录 [') + str(index) + (']:\n' if english else ']：\n') + claim['text'])
    if answer['limitations']:
        lines.append(('\nGaps: ' if english else '\n还不能确认的部分：') + ('; ' if english else '；').join(answer['limitations']))
    references = citation_lines(bundle, [ref for claim in answer['claims'] for ref in claim['evidence_ids']])
    if not references and bundle['passages']:
        references = citation_lines(bundle, [p['evidence_id'] for p in bundle['passages']])
    if references:
        lines.append(('References:\n' if english else '法规及官方依据：\n') + '\n'.join(references))
    answer['text'] = '\n\n'.join(lines)
    return answer


def validate_answer(answer, bundle):
    permitted = {e['evidence_id']: e for e in bundle['model_evidence']}
    for claim in answer['claims']:
        if not claim['evidence_ids'] or any(ref not in permitted for ref in claim['evidence_ids']):
            raise ValueError('Unknown or unauthorized citation')
        if claim.get('kind') == 'grounded_summary':
            from packages.agent.grounded import claims_from_result
            checked, _ = claims_from_result({'paragraphs': [{'text': claim['text'], 'evidence': claim.get('supports')}],
                                             'missing_info': []}, list(permitted.values()))
            if checked[0]['evidence_ids'] != claim['evidence_ids']:
                raise ValueError('Citation mismatch')
        elif claim.get('kind') != 'excerpt' or not any(claim['text'] in permitted[ref]['text'] for ref in claim['evidence_ids']):
            raise ValueError('Unsupported claim')
    if answer['review_status'] != 'pending_final_review':
        raise ValueError('Agent cannot approve')
