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
