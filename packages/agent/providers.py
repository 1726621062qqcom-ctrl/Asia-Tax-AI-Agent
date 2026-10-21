"""Replaceable providers. No automatic real-to-mock fallback."""
from __future__ import annotations
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
from typing import Literal
from urllib.parse import urlsplit
from time import monotonic
from queue import Queue, Empty
from threading import BoundedSemaphore, Thread

import httpx
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from packages.agent.contracts import (SearchRequest, SearchResult, TrustedContext, Reference,
                                      EvidenceResult, Evidence, Coverage, ProviderError)
from packages.agent.source_policy import public_hk_official

ROOT = Path(__file__).resolve().parents[2]
# Bound outstanding read-only database workers even if the OS stalls a socket.
# Timed-out work never writes case state or starts models, and late results are ignored.
_DATABASE_READ_SLOTS = BoundedSemaphore(2)


def failure(request, provider, code, retryable=False):
    return SearchResult(request_id=request.request_id, trace_id=request.trace_id,
                        retrieval_id=request.request_id, provider=provider, is_synthetic=provider == 'mock',
                        corpus_version='unknown', status='error',
                        error=ProviderError(code=code, message='Knowledge request failed', retryable=retryable))


class MockKnowledgeProvider:
    def __init__(self, scenario='MOCK-01', path=None):
        fixtures = json.loads((Path(path) if path else ROOT / 'docs/architecture/knowledge_provider_mock_fixtures.v0.1.json').read_text(encoding='utf-8'))
        self.fixture = next(f for f in fixtures['fixtures'] if f['scenario_id'] == scenario)

    def search_evidence(self, request, context):
        result = deepcopy(self.fixture['search_response'])
        result.update(request_id=request.request_id, trace_id=request.trace_id)
        return SearchResult.model_validate(result)

    def get_evidence(self, reference, purpose, context):
        evidence = next((e for e in self.fixture['search_response']['evidence'] if e['evidence_id'] == reference.evidence_id), None)
        if evidence is None:
            return EvidenceResult(status='not_found', reference=reference)
        if Evidence.model_validate(evidence).reference() != reference:
            return EvidenceResult(status='version_unavailable', reference=reference)
        if evidence[purpose + '_use'] != 'allowed':
            return EvidenceResult(status='restricted', reference=reference)
        item = next((r for r in self.fixture['display_store'] if r['reference'] == reference.model_dump()), None)
        if item is None:
            return EvidenceResult(status='not_found', reference=reference)
        return EvidenceResult(status='ok', reference=reference, text=item['text'], content_hash=item['content_hash'])


class LegacyKnowledgeProvider:
    """PostgreSQL sources/legal_units adapter, scoped by the approved FSIE manifest."""
    def __init__(self, searcher=None):
        self.searcher = searcher
        self._snapshot = {}

    def for_request(self):
        return LegacyKnowledgeProvider(self.searcher)

    def _documents(self, request):
        from packages.chat.knowledge import search, read_documents
        if self.searcher:
            return self.searcher(request.query)
        if request.locators:
            docs = read_documents(locators=request.locators, kind=request.kind)
            docs = [d for d in docs if d.get('locator') in request.locators][:50]
            return {'status': 'available' if docs else 'no_matching_units', 'passages': docs}
        if request.kind == 'ruling':
            from packages.chat.knowledge import rank_documents
            docs = read_documents(kind='ruling')
            ranked = rank_documents(docs, request.query, 'ruling', request.limit)
            ids = list(dict.fromkeys(d['source_id'] for d in ranked))[:1]
            passages = [d for d in docs if d['source_id'] in ids][:request.limit]
            return {'status': 'available' if passages else 'no_matching_units', 'passages': passages}
        return search(request.query, request.kind, request.limit)

    def search_evidence(self, request, context):
        # DB connect/statement timeouts do not bound a stale TLS socket or pool
        # pre-ping. Enforce the entire adapter call's deadline at its boundary.
        deadline = monotonic() + request.deadline_ms / 1000
        if not _DATABASE_READ_SLOTS.acquire(timeout=max(0, deadline - monotonic())):
            return failure(request, 'legacy', 'TIMEOUT', True)
        result = Queue(maxsize=1)
        def read():
            try:
                result.put(self._search_evidence(request, context))
            finally:
                _DATABASE_READ_SLOTS.release()
        Thread(target=read, name='knowledge-read', daemon=True).start()
        try:
            return result.get(timeout=max(0, deadline - monotonic()))
        except Empty:
            return failure(request, 'legacy', 'TIMEOUT', True)

    def _search_evidence(self, request, context):
        try:
            raw = self._documents(request)
            if raw['status'] == 'unavailable':
                return failure(request, 'legacy', 'UNAVAILABLE', True)
            evidence = []
            for item in raw.get('passages', []):
                digest = sha256(item['text'].encode()).hexdigest()
                version = item.get('snapshot_sha256') or digest
                self._snapshot[(context.owner, item['unit_id'], version)] = deepcopy(item)
                ref = Reference(evidence_id=item['unit_id'], source_version_id=version, unit_id=item['unit_id'])
                official_for_model = public_hk_official(item['source_id'], item.get('url'))
                evidence.append(Evidence(**ref.model_dump(), source_id=item['source_id'],
                    content_hash=digest, title=item.get('title') or item['source_id'],
                    source_type=item.get('source_type') or 'legacy_reference', locator=item.get('locator'), url=item.get('url'),
                    jurisdiction=item.get('jurisdiction') or 'HK', topic='dividend',
                    effective_from=item.get('effective_from'), effective_to=item.get('effective_to'), model_use='allowed' if official_for_model else 'denied',
                    model_text=item['text'] if official_for_model else None, display_use='allowed',
                    drift=bool(item.get('drift')), heading=item.get('heading'), retrieved_at=item.get('retrieved_at'),
                    coverage_cutoff=item.get('coverage_cutoff'), snapshot_sha256=item.get('snapshot_sha256'),
                    policy_version='public-hk-official-v1' if official_for_model else 'legacy-display-only-v1', display_ref=ref))
            return SearchResult(request_id=request.request_id, trace_id=request.trace_id,
                retrieval_id=request.request_id, provider='legacy', is_synthetic=False,
                corpus_version='legacy-unversioned', status='ok' if evidence else 'no_match', evidence=evidence,
                coverage=Coverage(status='partial' if raw.get('truncated') else 'unchecked',
                    scope='Existing reference search; applicability unverified', truncated=bool(raw.get('truncated')),
                    missing_requirements=['本次只返回部分相关条款，未覆盖的条件须继续查证。'] if raw.get('truncated') else []))
        except Exception:
            return failure(request, 'legacy', 'UNAVAILABLE', True)

    def get_evidence(self, reference, purpose, context):
        if purpose not in ('display', 'model'):
            return EvidenceResult(status='restricted', reference=reference)
        try:
            from packages.chat.knowledge import read_documents
            item = self._snapshot.get((context.owner, reference.unit_id, reference.source_version_id))
            docs = [item] if item else read_documents(unit_id=reference.unit_id)
            for item in docs:
                if item['unit_id'] == reference.unit_id == reference.evidence_id:
                    digest = sha256(item['text'].encode()).hexdigest()
                    if (item.get('snapshot_sha256') or digest) != reference.source_version_id:
                        return EvidenceResult(status='version_unavailable', reference=reference)
                    if purpose == 'model' and not public_hk_official(item['source_id'], item.get('url')):
                        return EvidenceResult(status='restricted', reference=reference)
                    return EvidenceResult(status='ok', reference=reference, text=item['text'], content_hash=digest)
            return EvidenceResult(status='not_found', reference=reference)
        except Exception:
            return EvidenceResult(status='error', reference=reference)


class CKnowledgeProvider:
    """Proposed HTTP wire contract: POST /search and POST /evidence, JSON models."""
    def __init__(self, base_url, token='', transport=None):
        parsed = urlsplit(base_url)
        if parsed.scheme != 'https' and not (parsed.scheme == 'http' and parsed.hostname in ('localhost', '127.0.0.1')):
            raise ValueError('C provider requires HTTPS or a loopback development endpoint')
        if parsed.username or parsed.password or parsed.query or parsed.fragment:
            raise ValueError('Invalid C endpoint')
        self.base_url, self.token, self.transport = base_url.rstrip('/'), token, transport
        # Reuse the loopback connection for the search followed by bounded
        # evidence reads. Recreating a client for each read can exhaust the
        # per-request deadline before any citation is verified on Windows.
        self._client = httpx.Client(follow_redirects=False, transport=transport,
                                    trust_env=parsed.hostname not in ('localhost', '127.0.0.1'))

    def close(self):
        self._client.close()

    def _post(self, path, payload, timeout):
        started = monotonic()
        with self._client.stream('POST', self.base_url + path, json=payload, timeout=timeout,
                                 headers={'Authorization': 'Bearer ' + self.token} if self.token else {}) as response:
            response.raise_for_status()
            chunks, size = [], 0
            for chunk in response.iter_bytes():
                if monotonic() - started >= timeout:
                    raise httpx.TimeoutException('Knowledge total deadline exceeded')
                size += len(chunk)
                if size > 2_000_000:
                    raise ValueError('Excessive provider response')
                chunks.append(chunk)
            if monotonic() - started >= timeout:
                raise httpx.TimeoutException('Knowledge total deadline exceeded')
            return json.loads(b''.join(chunks))

    def search_evidence(self, request, context):
        try:
            data = self._post('/search', {'request': request.model_dump(mode='json'),
                                         'trusted_context': context.model_dump()}, request.deadline_ms / 1000)
            result = SearchResult.model_validate(data)
            if result.provider != 'c' or result.request_id != request.request_id or result.trace_id != request.trace_id:
                raise ValueError('Provider/request identity mismatch')
            return result
        except httpx.TimeoutException:
            return failure(request, 'c', 'TIMEOUT', True)
        except httpx.HTTPStatusError as exc:
            status = exc.response.status_code
            return failure(request, 'c', 'ACCESS_DENIED' if status in (401, 403) else 'HTTP_ERROR', status == 429 or status >= 500)
        except httpx.TransportError:
            return failure(request, 'c', 'UNAVAILABLE', True)
        except (ValueError, TypeError):
            return failure(request, 'c', 'INVALID_RESPONSE')

    def get_evidence(self, reference, purpose, context):
        return self.get_evidence_bounded(reference, purpose, context, 1)

    def get_evidence_bounded(self, reference, purpose, context, timeout):
        try:
            data = self._post('/evidence', {'reference': reference.model_dump(), 'purpose': purpose,
                                           'trusted_context': context.model_dump()}, max(.001, timeout))
            result = EvidenceResult.model_validate(data)
            if result.reference != reference:
                raise ValueError('Reference mismatch')
            return result
        except (httpx.HTTPError, ValueError, TypeError):
            return EvidenceResult(status='error', reference=reference)


class RoutedKnowledgeProvider:
    """Route by source kind: fixed SQLite law, PostgreSQL FSIE guidance/rulings.

    Technical failure is returned to the caller, never masked by another corpus.
    """
    def __init__(self, law, rulings, guidance=None):
        # Fixed SQLite supplies legislation; PostgreSQL supplies FSIE guidance and rulings.
        self.law, self.rulings, self.guidance = law, rulings, guidance or rulings

    def for_request(self):
        return RoutedKnowledgeProvider(self.law,
            self.rulings.for_request() if hasattr(self.rulings, 'for_request') else self.rulings,
            self.guidance.for_request() if hasattr(self.guidance, 'for_request') else self.guidance)

    def search_evidence(self, request, context):
        provider = self.rulings if request.kind == 'ruling' else self.guidance if request.kind == 'guidance' else self.law
        return provider.search_evidence(request, context)

    def get_evidence(self, reference, purpose, context):
        return self._reference_provider(reference).get_evidence(reference, purpose, context)

    def _reference_provider(self, reference):
        if reference.unit_id.startswith(('law|', 'li|')):
            return self.law
        if reference.unit_id.startswith('hk_ird_advance_'):
            return self.rulings
        return self.guidance

    def get_evidence_bounded(self, reference, purpose, context, timeout):
        provider = self._reference_provider(reference)
        return provider.get_evidence_bounded(reference, purpose, context, timeout) if hasattr(provider, 'get_evidence_bounded') else provider.get_evidence(reference, purpose, context)


class ProviderSettings(BaseSettings):
    provider: Literal['legacy', 'mock', 'c', 'combined'] = 'legacy'
    mock_scenario: str = 'MOCK-01'
    c_url: str = ''
    c_token: str = Field(default='', repr=False)
    reviewer_ids: list[str] = Field(default_factory=list)
    model_config = SettingsConfigDict(env_prefix='FSIE_AGENT_', env_file=ROOT / '.env', extra='ignore')


def configured_provider():
    config = ProviderSettings()
    if config.provider == 'mock':
        return MockKnowledgeProvider(config.mock_scenario)
    if config.provider == 'c':
        return CKnowledgeProvider(config.c_url, config.c_token)
    if config.provider == 'combined':
        return RoutedKnowledgeProvider(CKnowledgeProvider(config.c_url, config.c_token), LegacyKnowledgeProvider())
    return LegacyKnowledgeProvider()
