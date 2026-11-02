"""#2168 — invert #1262/#2165 RECORD auto-upgrade tests.

Local wheel RECORD / distribution metadata are not the trust root.
A matching signed manifest validates. Hash drift, unsigned trees, and
downgrade stay tampered. ``re-baseline-auto-upgrade`` is gone.
"""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError

from tests.integrity_manifest_helpers import (
    install_matching_signed_manifest,
    reset_signed_manifest_pins,
)

from core.integrity_anchor import (
    alpha_version_suffix,
    compute_module_hashes,
    ensure_integrity_anchor,
    is_tampered,
    list_integrity_events,
    reset_integrity_anchor_for_tests,
)


def _cfg(tmp_path) -> dict:
    return {"sqlite_path": str(tmp_path / "audit.db")}


def test_legitimate_upgrade_signed_manifest_validates_without_sqlite_match(
    tmp_path, monkeypatch
) -> None:
    """Invert RECORD auto-rebaseline: signed match validates; SQLite hashes ignored."""
    cfg = _cfg(tmp_path)
    monkeypatch.setattr("core.integrity_anchor._release_label", lambda: "1.8.0")
    reset_integrity_anchor_for_tests()
    snap = ensure_integrity_anchor(cfg)
    assert snap["integrity_state"] == "validated"
    assert snap["trust_level"] == "expected"
    assert snap["release_label"] == "1.8.0"
    assert snap["mismatched_files"] == []
    assert is_tampered() is False
    assert alpha_version_suffix() == ""
    assert not any(
        e["event_type"] == "re-baseline-auto-upgrade"
        for e in list_integrity_events(cfg)
    )


def test_same_version_casual_edit_stays_tampered(tmp_path, monkeypatch) -> None:
    cfg = _cfg(tmp_path)
    current = compute_module_hashes()
    drifted = dict(current)
    drifted["core/engine.py"] = "a" * 64
    monkeypatch.setattr("core.integrity_anchor.compute_module_hashes", lambda: drifted)
    monkeypatch.setattr("core.integrity_anchor._release_label", lambda: "1.8.0")
    reset_integrity_anchor_for_tests()
    snap = ensure_integrity_anchor(cfg)
    assert snap["integrity_state"] == "tampered"
    assert "core/engine.py" in snap["mismatched_files"]
    assert is_tampered() is True
    assert alpha_version_suffix() == "-alpha"
    assert not any(
        e["event_type"] == "re-baseline-auto-upgrade"
        for e in list_integrity_events(cfg)
    )


def test_newer_version_with_signed_manifest_hash_mismatch_stays_tampered(
    tmp_path, monkeypatch
) -> None:
    """Invert RECORD-mismatch test: hash miss vs signed files stays tampered."""
    cfg = _cfg(tmp_path)
    current = compute_module_hashes()
    drifted = dict(current)
    drifted["main.py"] = "b" * 64
    monkeypatch.setattr("core.integrity_anchor.compute_module_hashes", lambda: drifted)
    monkeypatch.setattr("core.integrity_anchor._release_label", lambda: "1.8.0")
    reset_integrity_anchor_for_tests()
    snap = ensure_integrity_anchor(cfg)
    assert snap["integrity_state"] == "tampered"
    assert "main.py" in snap["mismatched_files"]
    assert not any(
        e["event_type"] == "re-baseline-auto-upgrade"
        for e in list_integrity_events(cfg)
    )


def test_downgrade_with_hash_match_stays_tampered(tmp_path, monkeypatch) -> None:
    cfg = _cfg(tmp_path)
    monkeypatch.setattr("core.integrity_anchor._release_label", lambda: "1.8.0")
    ensure_integrity_anchor(cfg)
    monkeypatch.setattr("core.integrity_anchor._release_label", lambda: "1.7.4")
    reset_integrity_anchor_for_tests()
    snap = ensure_integrity_anchor(cfg)
    assert snap["integrity_state"] == "tampered"
    assert not any(
        e["event_type"] == "re-baseline-auto-upgrade"
        for e in list_integrity_events(cfg)
    )


def test_missing_distribution_metadata_does_not_block_signed_match(
    tmp_path, monkeypatch
) -> None:
    """Invert RECORD/metadata test: missing importlib metadata is not the arbiter."""
    cfg = _cfg(tmp_path)

    def _missing(_name: str) -> str:
        raise PackageNotFoundError("data-boar")

    monkeypatch.setattr("importlib.metadata.version", _missing)
    monkeypatch.setattr("core.integrity_anchor._release_label", lambda: "1.8.0")
    reset_integrity_anchor_for_tests()
    snap = ensure_integrity_anchor(cfg)
    assert snap["integrity_state"] == "validated"
    assert not any(
        e["event_type"] == "re-baseline-auto-upgrade"
        for e in list_integrity_events(cfg)
    )


def test_unsigned_tree_stays_tampered_after_metadata_only_upgrade(
    tmp_path, monkeypatch
) -> None:
    reset_signed_manifest_pins()
    cfg = _cfg(tmp_path)
    monkeypatch.setattr("core.integrity_anchor._release_label", lambda: "1.8.0")
    reset_integrity_anchor_for_tests()
    snap = ensure_integrity_anchor(cfg)
    assert snap["integrity_state"] == "tampered"
    install_matching_signed_manifest(tmp_path, release_label="1.8.0")
    reset_integrity_anchor_for_tests()
    snap = ensure_integrity_anchor(cfg)
    assert snap["integrity_state"] == "validated"
