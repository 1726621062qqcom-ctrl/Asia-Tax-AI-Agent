"""Validate the case boundary and execute one pinned tax engine planning round."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from time import monotonic
from typing import Any, Literal

from pydantic import AliasChoices, BaseModel, ConfigDict, Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT = Path(__file__).resolve().parents[2]
PINNED_DB_SHA256 = '2756d2862330cb746d4103f0e690182fdc9fe7b2436a4ac738b156416aeca143'
PINNED_SOURCE_SHA256 = 'd4c5495302fc9c755eb750d70fc181dc99f58e6905a79709e93845ea7b5d37e9'
PINNED_COMMIT = '771e4524961bcc36718db1c9331e7a5f4cda0ce7'


class DomainError(Exception):
    def __init__(self, code: str):
        self.code = code


class Strict(BaseModel):
    model_config = ConfigDict(extra='forbid')


class Role(Strict):
    loc: Literal['CN', 'HK', 'SG']
    type: str = 'COMPANY'
    attrs: dict[str, Any] = Field(default_factory=dict)


class Holding(Strict):
    holder: str
    held: str
    ratio: float | None = Field(default=None, ge=0, le=100)
    since: str | None = None
    cost: float | None = Field(default=None, ge=0)


class DomainCase(Strict):
    template: str = Field(max_length=60)
    currency: str | None = Field(default=None, pattern=r'^[A-Z]{3}$')
    roles: dict[str, Role] = Field(min_length=1, max_length=12)
    holds: list[Holding] = Field(default_factory=list, max_length=20)
    flows: dict[str, dict[str, Any]] = Field(default_factory=dict)
    event: dict[str, Any]
    present: dict[str, Any] = Field(default_factory=dict)
    members: list[str] | None = None
    settled: dict[str, dict[str, float]] = Field(default_factory=dict)
    closed: list[list[str]] = Field(default_factory=list)
    subject: str = 'GROUP'
    notes: list[str] = Field(default_factory=list)

    @model_validator(mode='after')
    def check_shape(self):
        from datetime import date
        from math import isfinite
        parts = self.template.split('+')
        if len(parts) > 2 or len(set(parts)) != len(parts) or not set(parts) <= {'holding', 'ip', 'services', 'repatriation', 'financing', 'inbound_services'}:
            raise ValueError('unsupported template')
        if 'holding' in parts and not {'OP', 'ULT'} <= set(self.roles):
            raise ValueError('holding requires OP and ULT')
        if self.template == 'inbound_services' and not {'SERVICER', 'CLIENT'} <= set(self.roles):
            raise ValueError('inbound_services requires SERVICER and CLIENT')
        allowed_event = {'dividend', 'onward', 'exit', 'exit_on', 'royalty', 'service_fee',
                         'interest', 'on', 'as_at', 'years', 'horizon_years'}
        if set(self.event) - allowed_event:
            raise ValueError('unsupported event fields')
        if not isinstance(self.event.get('on'), str):
            raise ValueError('event.on is required')
        date.fromisoformat(self.event['on'])
        if self.event.get('as_at') is not None:
            date.fromisoformat(self.event['as_at'])
        if self.event.get('exit_on') is not None:
            date.fromisoformat(self.event['exit_on'])
        for key in ('dividend', 'onward', 'exit', 'royalty', 'service_fee', 'interest'):
            value = self.event.get(key)
            if value is not None and (isinstance(value, bool) or not isinstance(value, (int, float)) or
                                      not isfinite(value) or value < 0):
                raise ValueError('event amount must be a nonnegative finite number')
        for key in ('years', 'horizon_years'):
            value = self.event.get(key, 1)
            if isinstance(value, bool) or not isinstance(value, int) or not 1 <= value <= 5:
                raise ValueError('event year count must be between 1 and 5')
        for hold in self.holds:
            if hold.holder not in self.roles or hold.held not in self.roles or hold.holder == hold.held:
                raise ValueError('hold endpoints must be distinct existing roles')
            if hold.since:
                date.fromisoformat(hold.since)
        if self.members is not None and not set(self.members) <= set(self.roles):
            raise ValueError('members must be existing roles')
        if len({(h.holder, h.held) for h in self.holds}) != len(self.holds):
            raise ValueError('duplicate holding')
        edges = {role: [h.held for h in self.holds if h.holder == role] for role in self.roles}
        def visit(role, path):
            if role in path:
                raise ValueError('holding cycle')
            for held in edges[role]:
                visit(held, path | {role})
        for role in self.roles:
            visit(role, set())
        if len(json.dumps(self.model_dump(mode='json'), ensure_ascii=False)) > 50_000:
            raise ValueError('domain case too large')
        return self


class DomainSettings(BaseSettings):
    # Legacy aliases only support existing deployments; new configuration uses TAX_ENGINE.
    release_dir: str = Field(default='', validation_alias=AliasChoices('FSIE_TAX_ENGINE_RELEASE_DIR', 'FSIE_LI_RELEASE_DIR'))
    timeout_seconds: int = Field(default=40, ge=1, le=60, validation_alias=AliasChoices('FSIE_TAX_ENGINE_TIMEOUT_SECONDS', 'FSIE_LI_TIMEOUT_SECONDS'))
    model_config = SettingsConfigDict(env_prefix='FSIE_TAX_ENGINE_', env_file=ROOT / '.env', extra='ignore', populate_by_name=True)


def release_path(settings: DomainSettings | None = None) -> Path:
    config = settings or DomainSettings()
    path = Path(config.release_dir or ROOT / 'data/tax_engine/releases' / PINNED_COMMIT).resolve()
    # A previous deployment may explicitly configure the former default path.
    old_default = ROOT / 'data/li/releases' / PINNED_COMMIT
    new_default = ROOT / 'data/tax_engine/releases' / PINNED_COMMIT
    if path == old_default.resolve() and not path.exists() and new_default.exists():
        path = new_default.resolve()
    # Read existing local installations during the naming migration.
    if not config.release_dir and not path.exists():
        legacy = ROOT / 'data/li/releases' / PINNED_COMMIT
        if legacy.exists():
            path = legacy.resolve()
    if not (path / 'tax_graph/planner.py').is_file() or not (path / 'official/official.sqlite').is_file():
        raise DomainError('domain_unavailable')
    return path


def verify_release(path: Path) -> None:
    digest = hashlib.sha256()
    with (path / 'official/official.sqlite').open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    if digest.hexdigest() != PINNED_DB_SHA256:
        raise DomainError('release_hash_mismatch')
    files = sorted({*path.glob('tax_graph/**/*.py'), *path.glob('tax_graph/**/*.csv'),
                    *path.glob('tax_graph/**/*.json'), *path.glob('official/tools/**/*.py'),
                    *path.glob('official/**/*.csv')}, key=lambda file: file.relative_to(path).as_posix())
    source = hashlib.sha256()
    for file in files:
        source.update(file.relative_to(path).as_posix().encode() + b'\0')
        source.update(hashlib.sha256(file.read_bytes()).digest())
    if source.hexdigest() != PINNED_SOURCE_SHA256:
        raise DomainError('release_hash_mismatch')


def run_plan(case: DomainCase, answers: dict, *, today: str, settings: DomainSettings | None = None) -> dict:
    return run_domain(case, answers, today=today, mode='plan_structure', settings=settings)


def run_domain(case: DomainCase, answers: dict, *, today: str, mode: str,
               settings: DomainSettings | None = None) -> dict:
    from datetime import date
    date.fromisoformat(today)
    config = settings or DomainSettings()
    if mode not in ('plan_structure', 'assess_current', 'review_paid'):
        raise DomainError('unsupported_domain_mode')
    if not case.currency:
        raise DomainError('currency_required')
    if case.currency != 'CNY':
        return {'status': 'unsupported', 'questions': [], 'candidate_count': 0, 'currency': case.currency,
                'mode': mode, 'release': PINNED_COMMIT, 'today': today,
                'note': '当前已验证的计算单位为 CNY；其他币种需要明确汇率来源和税额折算规则，未执行计算。'}
    path = release_path(config)
    payload = {'case': case.model_dump(mode='json'), 'answers': answers, 'today': today, 'mode': mode,
               'release': PINNED_COMMIT}
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(',', ':'))
    facts_hash = hashlib.sha256(raw.encode()).hexdigest()
    env = {key: os.environ[key] for key in ('PATH', 'LANG', 'LC_ALL', 'SYSTEMROOT') if key in os.environ}
    env.update({'FSIE_TAX_ENGINE_RELEASE_DIR': str(path), 'PYTHONIOENCODING': 'utf-8',
                'PYTHONPATH': str(ROOT) + os.pathsep + str(path)})
    from packages.agent.budget import current_budget
    budget = current_budget.get()
    timeout = min(config.timeout_seconds, budget.remaining()) if budget else config.timeout_seconds
    if timeout <= 0:
        raise DomainError('domain_timeout')
    started = monotonic()
    try:
        result = subprocess.run([sys.executable, '-m', 'packages.domain_bridge.worker'], input=raw,
                                text=True, encoding='utf-8', capture_output=True, cwd=path, env=env,
                                timeout=timeout, check=False)
    except subprocess.TimeoutExpired:
        raise DomainError('domain_timeout') from None
    if result.returncode or len(result.stdout) > 500_000:
        raise DomainError('domain_execution_failed')
    try:
        outcome = json.loads(result.stdout)
    except (ValueError, TypeError):
        raise DomainError('domain_execution_failed') from None
    if outcome.get('status') not in ('needs_input', 'ready', 'blocked', 'unsupported'):
        raise DomainError('domain_execution_failed')
    return {'release': PINNED_COMMIT, 'database_hash': PINNED_DB_SHA256, 'source_hash': PINNED_SOURCE_SHA256,
            'input_hash': facts_hash, 'today': today, 'mode': mode, 'currency': case.currency,
            'timings_ms': {'domain': round((monotonic() - started) * 1000, 2)}, **outcome}
