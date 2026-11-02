"""#1262 — auto re-baseline only on a proven legitimate upgrade."""

from __future__ import annotations

import contextlib
import json
import sqlite3
from datetime import datetime, timezone
from importlib.metadata import PackageNotFoundError

from core.integrity_anchor import (
    ANCHOR_VERSION,
    VALIDATOR_VERSION,
    _manifest_content_hash,
    alpha_version_suffix,
    compute_module_hashes,
    ensure_integrity_anchor,
    is_tampered,
    list_integrity_events,
    reset_integrity_anchor_for_tests,
)


def _cfg(tmp_path) -> dict:
    return {"sqlite_path": str(tmp_path / "audit.db")}


def _seed_anchor(db_path: str, *, label: str, hashes: dict[str, str]) -> None:
    now = datetime.now(timezone.utc).isoformat()
    with contextlib.closing(sqlite3.connect(db_path)) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS build_integrity_anchor (
                anchor_version INTEGER PRIMARY KEY,
                release_label TEXT NOT NULL,
                manifest_content_hash TEXT NOT NULL,
                file_hashes_json TEXT NOT NULL,
                validated_at TEXT NOT NULL,
                build_digest_matched INTEGER NOT NULL,
                validator_version TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS integrity_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                event_type TEXT NOT NULL,
                detail TEXT NOT NULL
            )
            """
        )
        conn.execute(
            "INSERT INTO build_integrity_anchor (anchor_version, release_label, "
            "manifest_content_hash, file_hashes_json, validated_at, "
            "build_digest_matched, validator_version) VALUES (?, ?, ?, ?, ?, 0, ?)",
            (
                ANCHOR_VERSION,
                label,
                _manifest_content_hash(hashes),
                json.dumps(hashes, sort_keys=True),
                now,
                VALIDATOR_VERSION,
            ),
        )
        conn.commit()


def test_legitimate_upgrade_auto_rebaselines_and_records_event(
    tmp_path, monkeypatch
) -> None:
    cfg = _cfg(tmp_path)
    current = compute_module_hashes()
    stale = {path: "0" * 64 for path in current}
    _seed_anchor(cfg["sqlite_path"], label="1.7.4.post12", hashes=stale)
    monkeypatch.setattr("core.integrity_anchor._release_label", lambda: "1.8.0")
    monkeypatch.setattr(
        "core.integrity_anchor.critical_modules_match_installed_record",
        lambda: True,
    )
    reset_integrity_anchor_for_tests()
    snap = ensure_integrity_anchor(cfg)
    assert snap["integrity_state"] == "validated"
    assert snap["trust_level"] == "expected"
    assert snap["release_label"] == "1.8.0"
    assert snap["mismatched_files"] == []
    assert is_tampered() is False
    assert alpha_version_suffix() == ""
    events = list_integrity_events(cfg)
    auto = next(e for e in events if e["event_type"] == "re-baseline-auto-upgrade")
    assert "1.7.4.post12" in auto["detail"]
    assert "1.8.0" in auto["detail"]


def test_same_version_casual_edit_stays_tampered(tmp_path, monkeypatch) -> None:
    cfg = _cfg(tmp_path)
    current = compute_module_hashes()
    _seed_anchor(cfg["sqlite_path"], label="1.8.0", hashes=current)
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


def test_newer_version_with_record_mismatch_stays_tampered(
    tmp_path, monkeypatch
) -> None:
    cfg = _cfg(tmp_path)
    current = compute_module_hashes()
    stale = {path: "0" * 64 for path in current}
    _seed_anchor(cfg["sqlite_path"], label="1.7.4", hashes=stale)
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


def test_downgrade_with_hash_drift_stays_tampered(tmp_path, monkeypatch) -> None:
    cfg = _cfg(tmp_path)
    current = compute_module_hashes()
    stale = {path: "0" * 64 for path in current}
    _seed_anchor(cfg["sqlite_path"], label="1.8.0", hashes=stale)
    monkeypatch.setattr("importlib.metadata.version", lambda _name: "1.7.4")
    monkeypatch.setattr("core.integrity_anchor._release_label", lambda: "1.7.4")
    reset_integrity_anchor_for_tests()
    snap = ensure_integrity_anchor(cfg)
    assert snap["integrity_state"] == "tampered"
    assert not any(
        e["event_type"] == "re-baseline-auto-upgrade"
        for e in list_integrity_events(cfg)
    )


def test_missing_distribution_metadata_keeps_current_tamper_behavior(
    tmp_path, monkeypatch
) -> None:
    cfg = _cfg(tmp_path)
    current = compute_module_hashes()
    stale = {path: "0" * 64 for path in current}
    _seed_anchor(cfg["sqlite_path"], label="1.7.4", hashes=stale)

    def _missing(_name: str) -> str:
        raise PackageNotFoundError("data-boar")

    monkeypatch.setattr("importlib.metadata.version", _missing)
    monkeypatch.setattr("core.integrity_anchor._release_label", lambda: "1.8.0")
    reset_integrity_anchor_for_tests()
    snap = ensure_integrity_anchor(cfg)
    assert snap["integrity_state"] == "tampered"
    assert not any(
        e["event_type"] == "re-baseline-auto-upgrade"
        for e in list_integrity_events(cfg)
    )
