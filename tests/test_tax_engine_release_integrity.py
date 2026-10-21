"""The pinned source digest must be portable and reject changed release files."""
import hashlib

import pytest

from packages.domain_bridge import bridge


def test_release_source_digest_uses_portable_paths_and_rejects_tampering(tmp_path, monkeypatch):
    database = tmp_path / 'official/official.sqlite'
    database.parent.mkdir(parents=True)
    database.write_bytes(b'fixture database')
    source = tmp_path / 'tax_graph/a.py'
    source.parent.mkdir(parents=True)
    source.write_bytes(b'x=1\n')
    labels = tmp_path / 'official/labels/observed_rules.csv'
    labels.parent.mkdir(parents=True)
    labels.write_bytes(b'rule_id\nR1\n')

    monkeypatch.setattr(bridge, 'PINNED_DB_SHA256', hashlib.sha256(database.read_bytes()).hexdigest())
    # Independent digest for the canonical POSIX relative paths, including a nested CSV.
    monkeypatch.setattr(bridge, 'PINNED_SOURCE_SHA256',
                        '807b8d60f4f4ef9f3a6f24a315a45550404275e8dab6cd33715b20a88932d950')
    bridge.verify_release(tmp_path)

    labels.write_bytes(b'rule_id\nR2\n')
    with pytest.raises(bridge.DomainError, match='release_hash_mismatch'):
        bridge.verify_release(tmp_path)


def test_settings_accept_legacy_environment_and_prefer_neutral_names(monkeypatch):
    monkeypatch.setenv('FSIE_LI_RELEASE_DIR', '/legacy/release')
    monkeypatch.setenv('FSIE_LI_TIMEOUT_SECONDS', '25')
    monkeypatch.delenv('FSIE_TAX_ENGINE_RELEASE_DIR', raising=False)
    monkeypatch.delenv('FSIE_TAX_ENGINE_TIMEOUT_SECONDS', raising=False)
    settings = bridge.DomainSettings(_env_file=None)
    assert settings.release_dir == '/legacy/release'
    assert settings.timeout_seconds == 25
    monkeypatch.setenv('FSIE_TAX_ENGINE_RELEASE_DIR', '/current/release')
    monkeypatch.setenv('FSIE_TAX_ENGINE_TIMEOUT_SECONDS', '30')
    settings = bridge.DomainSettings(_env_file=None)
    assert settings.release_dir == '/current/release'
    assert settings.timeout_seconds == 30


def test_default_release_path_reads_old_installation_then_prefers_new(tmp_path, monkeypatch):
    monkeypatch.setattr(bridge, 'ROOT', tmp_path)
    config = bridge.DomainSettings(release_dir='', _env_file=None)
    for folder in ('li', 'tax_engine'):
        release = tmp_path / 'data' / folder / 'releases' / bridge.PINNED_COMMIT
        for relative in ('tax_graph/planner.py', 'official/official.sqlite'):
            target = release / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.touch()
        assert bridge.release_path(config) == release


@pytest.mark.parametrize('prefix', ['law', 'li'])
def test_saved_legal_references_remain_readable(prefix):
    from apps.knowledge_api.main import _reference, _span
    from packages.agent.contracts import Reference
    current = _reference('hk.cap112.en#s15M', 2, 50)
    assert current.unit_id.startswith('law|')
    unit = f'{prefix}|hk.cap112.en#s15M|2|50'
    saved = Reference(unit_id=unit, evidence_id=unit, source_version_id=current.source_version_id)
    assert _span(saved) == ('hk.cap112.en#s15M', 2, 50)


def test_previous_explicit_default_works_after_new_install(tmp_path, monkeypatch):
    monkeypatch.setattr(bridge, 'ROOT', tmp_path)
    old = tmp_path / 'data/li/releases' / bridge.PINNED_COMMIT
    new = tmp_path / 'data/tax_engine/releases' / bridge.PINNED_COMMIT
    for relative in ('tax_graph/planner.py', 'official/official.sqlite'):
        target = new / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.touch()
    assert bridge.release_path(bridge.DomainSettings(release_dir=str(old), _env_file=None)) == new


@pytest.mark.parametrize('prefix', ['domain', 'li'])
def test_saved_structure_question_replies_still_route_to_domain(prefix):
    from packages.chat.service import ChatService
    class Service(ChatService):
        def __init__(self):
            pass
        def domain_message(self, *args):
            return args[-1]
    question = f'{prefix}:saved-question'
    assert Service().message('owner', 'case', 1, 'request', 'yes', True,
                             reply_to_question_id=question) == question
