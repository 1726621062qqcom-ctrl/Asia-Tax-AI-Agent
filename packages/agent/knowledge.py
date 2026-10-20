"""Retrieve, authorize and project evidence before any answer is constructed."""
from __future__ import annotations
from hashlib import sha256
from copy import deepcopy
from time import monotonic
import re
from urllib.parse import urlsplit

from packages.agent.contracts import SearchRequest, SearchResult, TrustedContext
from packages.agent.providers import failure
from packages.agent.budget import BudgetExceeded
from packages.agent.tracing import instrument, emit


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


@instrument('knowledge.retrieve')
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
    retrieval_stop = None
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
                retrieval_stop = 'budget_exhausted'
                gaps.append('原文读取预算已用尽，部分资料尚未取得')
                break
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
                'locator': evidence.locator, 'source_type': evidence.source_type, 'text': display.text, 'title': evidence.title, 'url': url,
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
                'title': evidence.title, 'url': evidence.url,
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
    emit('evidence.admission', reason_code=reason, model_evidence_count=len(evidence_for_model),
         display_passage_count=len(passages), verified_count=len(verified_ids), gap_count=len(gaps),
         source_locators=[e.get('locator') for e in evidence_for_model])
    return {
        'retrieval_stop': retrieval_stop,
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


def citation_lines(bundle, evidence_ids, locale='zh', supports=None):
    passages = {p['evidence_id']: p for p in bundle['passages']}
    originals = {e['evidence_id']: e for e in bundle['model_evidence']}
    lines, seen = [], set()
    for evidence_id in evidence_ids:
        passage = passages.get(evidence_id)
        if not passage:
            continue
        # A parent source may support several conditions. Keep its verified
        # identity; a selected quote alone does not prove subsection-level scope.
        original = originals.get(evidence_id, {})
        label = original.get('locator') or passage.get('locator') or passage.get('title') or 'Official source'
        if not original.get('locator'):
            title = passage.get('title', '').casefold()
            if 'faq' in title:
                label = 'IRD FSIE FAQ' if locale == 'en' else '税务局 FSIE 常见问题'
            elif 'example' in title:
                label = 'IRD FSIE examples' if locale == 'en' else '税务局 FSIE 示例'
            elif 'fsie' in title or 'foreign-sourced' in title:
                label = 'IRD FSIE guidance' if locale == 'en' else '税务局 FSIE 指引'
        label = re.sub(r'[\[\]\n<>]', '', label)
        if locale == 'en' and re.search(r'[\u3400-\u9fff]', label):
            label = f'Official source {list(passages).index(evidence_id) + 1}'
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


def merge_bundles(bundles, question, case_context=None):
    """Union already-authorized evidence; never upgrade a source's permissions."""
    merged = deepcopy(bundles[0])
    merged.update(query=bundles[0]['query'] if len(bundles) == 1 else question, passages=[], model_evidence=[], gaps=[], verified_evidence_ids=[])
    for field in ('passages', 'model_evidence', 'gaps', 'verified_evidence_ids'):
        seen = set()
        groups = [bundle.get(field, []) for bundle in bundles]
        # The final model has seven source slots: interleave independent searches
        # so the first law search cannot consume every slot before guidance/rulings.
        if field == 'model_evidence':
            groups = [[group[index] for group in groups if index < len(group)]
                      for index in range(max(map(len, groups), default=0))]
        for group in groups:
            for item in group:
                if field == 'passages':
                    key = (item['evidence_id'], item.get('source_version_id'), item.get('locator'), item['text_sha256'])
                elif field == 'model_evidence':
                    key = (item['evidence_id'], item.get('source_version_id'), item['content_hash'])
                else:
                    key = item
                if key not in seen:
                    merged[field].append(deepcopy(item))
                    seen.add(key)
    # Keep the required primary sections in the final source window. A long FAQ
    # must not push the last primary section out merely by returning more chunks.
    merged['model_evidence'].sort(key=lambda e: 0 if (e.get('locator') or '').startswith('s.') else 1)
    merged['retrieval_stop'] = next((b['retrieval_stop'] for b in bundles if b.get('retrieval_stop')), None)
    # An ID must identify exactly one version in the final evidence namespace.
    versions = {}
    for evidence in merged['model_evidence']:
        versions.setdefault(evidence['evidence_id'], set()).add((evidence['source_version_id'], evidence['content_hash']))
    ambiguous = {key for key, values in versions.items() if len(values) > 1}
    merged['model_evidence'] = [e for e in merged['model_evidence'] if e['evidence_id'] not in ambiguous]
    merged['passages'] = [p for p in merged['passages'] if p['evidence_id'] not in ambiguous]
    if ambiguous:
        merged['gaps'].append('原文版本不可用或校验失败')
    merged['is_synthetic'] = any(b.get('is_synthetic') for b in bundles)
    merged['status'] = 'available' if merged['passages'] else 'no_matching_units'
    merged['reason_code'] = ('evidence_insufficient' if merged['gaps'] or any(b['reason_code'] != 'evidence_available' for b in bundles)
                             else 'evidence_available') if merged['model_evidence'] else bundles[-1]['reason_code']
    merged['task_contexts'] = [{'query': b['query'], 'reason_code': b['reason_code'],
                               'uses_case': b.get('query_context', {}).get('uses_case', False)} for b in bundles]
    merged['query_context'] = deepcopy(case_context or bundles[-1].get('query_context', {}))
    return merged


def relevant_excerpt(text, question):
    """Choose a contiguous source passage; never cut a sentence at character 500."""
    patterns = []
    for key, pattern in (
        (r'持股|持有期|participation|holding', r'12 months|5%|participation requirement'),
        (r'日期|date', r'\b\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}\b'),
        (r'外包|outsourc', r'arranged by|outsourc'),
        (r'抵免|credit', r'credit'),
        (r'收到|收取|汇回|received', r'remitted|satisfaction of any debt|received in Hong Kong'),
    ):
        if re.search(key, question, re.I):
            patterns.append(pattern)
    match = re.search('|'.join(patterns), text, re.I) if patterns else None
    start = max(0, text.rfind('\n\n', 0, match.start()) + 2) if match else 0
    if len(text) - start <= 1600:
        return text[start:].strip()
    end = text.find('\n\n', start + 600)
    if end < 0 or end - start > 2000:
        # Select complete source lines instead of truncating inside a line.
        end = text.find('\n', start + 600)
    if end < 0:
        end = len(text)
    return text[start:end].strip()


@instrument('answer.compose')
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
        answer['limitations'].append('No matching source was found for the requested issue.' if english else '未匹配的查询：' + bundle['query'])
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
        text = relevant_excerpt(evidence['text'], question or bundle['query'])
        if text not in {claim['text'] for claim in answer['claims']}:
            answer['claims'].append({'text': text, 'evidence_ids': [evidence['evidence_id']], 'kind': 'excerpt'})
    if responder and bundle['model_evidence'] and not bundle['is_synthetic'] and reason != 'retrieval_failed':
        from packages.agent.grounded import claims_from_result
        permitted = [e for e in bundle['model_evidence'] if e.get('display_allowed', True)]
        payload = {'question': question or bundle['query'], 'query': bundle['query'], 'locale': locale, 'coverage': reason,
                   'uses_case': context.get('uses_case', False), 'case_facts_for_context_only': context.get('case_facts', {}),
                   'case_context': context.get('fact_context', {}), 'task_results': bundle.get('task_contexts', []),
                   'sources': permitted[:7]}
        from packages.agent.budget import current_budget
        budget = current_budget.get()
        verified_candidate = None
        def room():
            return budget is None or (budget.counts.get('model', 0) < budget.model_limit and budget.remaining() > 3)
        for attempt in range(2):
            try:
                emit('answer.attempt', attempt=attempt+1, language=locale, source_count=len(permitted[:7]),
                     mode='quality_review' if 'quality_review' in payload else 'repair' if 'validation_feedback' in payload else 'initial')
                draft = responder(payload)
                claims, missing = claims_from_result(draft, permitted[:7], locale=locale)
                if context.get('uses_case'):
                    from packages.agent.grounded import validate_case_claims
                    validate_case_claims(claims, context.get('case_facts', {}), payload['question'])
                if locale == 'en':
                    from packages.chat.language import english_text
                    if any(not english_text(item) for item in missing):
                        raise ValueError('reply_language')
                if context.get('uses_case') is False:
                    missing = []
                # Complex exemption/credit questions get one bounded re-reading,
                # sharing the original evidence and the same execution budget.
                if attempt == 0 and room() and (re.search(r'抵免|双重征税|credit|double tax', payload['question'], re.I)
                                                or context.get('uses_case') and len(payload['question']) > 600):
                    verified_candidate = (claims, missing)
                    payload.update(previous_answer=draft, quality_review=(
                        'Recheck the direction and prerequisites of each exemption and tax-credit rule. '
                        'Do not say that failure of economic substance establishes or prevents participation exemption or credits. '
                        'State only relationships established by the quoted source; say when general credit conditions are not covered. '
                        'Keep the full answer around 350 English words or 700 Chinese characters, using short headings and lists. '
                        'Remove missing_info items already requested in the documents section. '
                        'Do not calculate an exact or approximate holding duration from month-only dates; the legal accrual date may be unknown. '
                        'Do not assert source, business-in-Hong-Kong, residence or entity classification as established unless the user explicitly stated it. '
                        'A year such as 2027 is not a month. A planned payment and an unmade resolution are not actual events.'))
                    continue
                answer.update(claims=claims, summary=claims[0]['text'], composition='grounded', missing_info=missing,
                              composition_attempts=attempt + 1)
                break
            except Exception as exc:
                emit('answer.validation', 'rejected', attempt=attempt+1, error_type=type(exc).__name__,
                     reason_code=str(exc) if isinstance(exc, ValueError) and str(exc) in (
                         'unsupported_citation', 'reply_language', 'answer_shape', 'paragraphs', 'missing_info',
                         'paragraph', 'citations_required', 'citation_shape', 'unconfirmed_entity_classification',
                         'unconfirmed_date_precision', 'unconfirmed_accrual', 'unconfirmed_holding_duration') else 'explanation_unavailable')
                if isinstance(locals().get('draft'), dict):
                    # Structural diagnostics only; never persist rejected prose or source text.
                    answer['composition_diagnostic'] = [
                        {'keys': sorted(p), 'text_length': len(p.get('text', '')) if isinstance(p.get('text'), str) else None,
                         'evidence_count': len(p.get('evidence', [])) if isinstance(p.get('evidence', []), list) else None}
                        for p in draft.get('paragraphs', []) if isinstance(p, dict)] if isinstance(draft.get('paragraphs'), list) else []
                code = str(exc) if isinstance(exc, ValueError) and str(exc) in (
                    'unsupported_citation', 'reply_language', 'answer_shape', 'paragraphs', 'missing_info',
                    'paragraph', 'citations_required', 'citation_shape', 'unconfirmed_entity_classification',
                         'unconfirmed_date_precision', 'unconfirmed_accrual', 'unconfirmed_holding_duration') else 'explanation_unavailable'
                if attempt == 0 and room():
                    payload.update(previous_answer=locals().get('draft'), validation_feedback={
                        'error': code, 'case_guard': ('Treat years as years and months as months. Do not calculate holding duration without verified accrual and acquisition dates. An unmade resolution does not establish a legal accrual finding. Describe planned events as uncompleted and accrual as unconfirmed.' if code.startswith('unconfirmed_') else ''), 'instruction': 'Return the required JSON in the requested language. Each paragraph MUST have exactly text and evidence keys, no heading/title/kind keys. Put short Markdown headings INSIDE text. Each text must be at most 1500 characters with no URLs. EVERY paragraph must contain at least one valid evidence_id/span_id pair from sources, including any fact summaries or document checklists: integrate them with the related legal reason rather than writing unsupported standalone paragraphs. Entity classification is unconfirmed unless explicitly present in case facts; explain conditional alternatives instead. Keep the whole answer concise.'})
                    continue
                if verified_candidate:
                    claims, missing = verified_candidate
                    answer.update(claims=claims, summary=claims[0]['text'], composition='grounded',
                                  missing_info=missing, composition_attempts=attempt + 1, quality_review_error=code)
                else:
                    answer.update(composition='extractive_fallback', composition_error=code, composition_attempts=attempt + 1)
                break  # No further model attempt after an exhausted budget or failed final repair.
    lines = [answer['summary'], '\n' + ('Conditions: ' if english else '适用条件：') + ('; ' if english else '；').join(answer['conditions'])]
    if answer.get('composition') == 'grounded':
        # A document checklist already is the next-step list. Keep machine-readable
        # missing_info, but do not print a second near-identical checklist below it.
        answer['next_steps_in_body'] = any(re.search(
            r'(?:\*\*|^|\n)(?:Documents? to (?:request|assemble|gather)|Next steps?|优先材料|材料清单|需.{0,3}材料|下一步)',
            claim['text'], re.I) for claim in answer['claims'])
        def display_text(text):
            if english or re.search(r'原文|逐字|quote|exact wording', question, re.I):
                return text
            # Translate generated terminology only; official quotations and links stay intact.
            text = re.sub(r'\bunderlying profits\b', '用于分红的基础利润', text, flags=re.I)
            return re.sub(r'(?<![A-Za-z])FSIE(?![A-Za-z])(?:制度)?', '境外收入豁免制度', text, flags=re.I)
        lines = [re.sub(r'\s*[•●]\s*', '\n- ', display_text(claim['text'])) + ' ' + ' · '.join(
            link.removeprefix('- ') for link in citation_lines(bundle, claim['evidence_ids'], locale, claim.get('supports')))
                 for claim in answer['claims']]
        if bundle['is_synthetic']:
            lines.insert(0, '[Synthetic test data, not an official tax source]' if english else '【模拟联调资料，不是真实税务依据】')
        if answer['missing_info'] and not answer['next_steps_in_body']:
            lines.append(('To confirm first:\n' if english else '优先确认：\n') +
                         '\n'.join('- ' + display_text(item) for item in answer['missing_info'][:3]))
            remaining = len(answer['missing_info']) - 3
            if remaining > 0:
                lines.append(f'{remaining} further conditions remain unverified; this is not a complete conclusion.'
                             if english else f'另有 {remaining} 项条件尚未核实；先确认以上问题，再继续梳理，当前不是完整结论。')
    else:
        if answer.get('composition') == 'extractive_fallback':
            lines = ['I found source material, but could not verify a reliable explanation for this question. The original sources are available below.' if english else
                     '已找到相关资料，但这次还未能形成可核实的解释。你可以先核对下方原文依据。']
        show_excerpts = answer.get('composition') != 'extractive_fallback' or bool(re.search(r'原文|逐字|quote|exact wording|text of', question, re.I))
        for index, claim in enumerate(answer['claims'][:2] if show_excerpts else [], 1):
            lines.append(('\nSource excerpt [' if english else '\n依据摘录 [') + str(index) + (']:\n' if english else ']：\n') + claim['text'])
    if answer['limitations']:
        lines.append(('\nGaps: ' if english else '\n还不能确认的部分：') + ('; ' if english else '；').join(answer['limitations']))
    references = citation_lines(bundle, [ref for claim in answer['claims'] for ref in claim['evidence_ids']], locale)
    if not references and bundle['passages']:
        references = citation_lines(bundle, [p['evidence_id'] for p in bundle['passages']], locale)
    if references and answer.get('composition') != 'grounded':
        lines.append(('References:\n' if english else '法规及官方依据：\n') + '\n'.join(references))
    answer['text'] = '\n\n'.join(lines)
    emit('answer.result', composition=answer.get('composition', 'extractive'),
         attempts=answer.get('composition_attempts', 0), claim_count=len(answer['claims']),
         missing_count=len(answer.get('missing_info', [])), reason_code=answer.get('composition_error'),
         quality_review_error=answer.get('quality_review_error'), language=locale)
    return answer


@instrument('answer.validate')
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
