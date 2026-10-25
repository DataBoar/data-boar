"""Tests for scan config scope digest (audit metadata; PBKDF2 for CodeQL weak-sensitive-hash posture)."""

from core.engine import _compute_config_scope_hash


def test_config_scope_hash_stable_for_same_scope():
    cfg = {
        "targets": [{"name": "db_a", "type": "database"}],
        "file_scan": {"extensions": [".csv", ".txt"]},
    }
    a = _compute_config_scope_hash(cfg)
    b = _compute_config_scope_hash(cfg)
    assert a == b
    assert len(a) == 64


def test_config_scope_hash_changes_when_scope_changes():
    base = {"targets": [{"name": "x", "type": "y"}], "file_scan": {}}
    other = {"targets": [{"name": "x", "type": "z"}], "file_scan": {}}
    assert _compute_config_scope_hash(base) != _compute_config_scope_hash(other)
