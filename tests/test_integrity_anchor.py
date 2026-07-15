"""
#856 — Phase E: SQLite integrity anchor + startup re-verify + TINTED/-alpha.

Contract under test:

1. First run creates the ``build_integrity_anchor`` row + a ``validation``
   event; state = validated / trust expected.
2. Re-run with unchanged modules → re-verify ok (``re-verify`` event).
3. Tamper (hash drift) → ``integrity_state=tampered`` /
   ``trust_level=adulterated`` + append-only ``tamper`` event + CRITICAL log.
   Runs in ANY mode (no licensing config needed = open mode).
4. The anchor and ``integrity_events`` SURVIVE ``wipe_all_data()``
   (``--reset-data`` semantics).
5. TINTED surfaces: ``get_about_info()`` forces the ``-alpha`` label and
   exposes ``build_trust`` / ``integrity_state``; enterprise surface posture
   goes ``elevated`` with reason ``integrity_tampered``.
6. Open-mode worker clamp: engine caps ``scan.max_workers`` at
   ``OPEN_MODE_WORKER_CAP=2`` in open mode; enforced mode keeps licensing
   caps (#551) instead.
7. Fail-soft: unwritable anchor path → state ``unknown``, no crash
   (never ``validated`` / ``expected``).
8. ``build_digest_matched`` (#1211): True only when expected digest set and
   matches; unset env → False (no signature overclaim).
9. Legacy DB column ``signature_ok`` migrates to ``build_digest_matched``.
10. Release upgrade (#1262): ``release_label`` change re-baselines; same-label
    hash drift still tampers.
"""

from __future__ import annotations

import contextlib
import json
import logging
import sqlite3
from datetime import datetime, timezone

import pytest

from core.integrity_anchor import (
    ANCHOR_VERSION,
    OPEN_MODE_WORKER_CAP,
    VALIDATOR_VERSION,
    _manifest_content_hash,
    compute_module_hashes,
    ensure_integrity_anchor,
    get_integrity_snapshot,
    list_integrity_events,
    reset_integrity_anchor_for_tests,
)

AUDIT_LOGGER = "data_boar.licensing.audit"


@pytest.fixture(autouse=True)
def _clean_snapshot():
    reset_integrity_anchor_for_tests()
    yield
    reset_integrity_anchor_for_tests()


def _cfg(tmp_path) -> dict:
    return {"sqlite_path": str(tmp_path / "audit.db")}


# --- 1./2. first run + re-verify ------------------------------------------------


def test_first_run_creates_anchor_and_validation_event(tmp_path, monkeypatch):
    monkeypatch.delenv("DATA_BOAR_EXPECTED_BUILD_DIGEST", raising=False)
    cfg = _cfg(tmp_path)
    snap = ensure_integrity_anchor(cfg)
    assert snap["integrity_state"] == "validated"
    assert snap["trust_level"] == "expected"
    assert snap["release_label"] not in ("", "unknown")
    assert snap["validated_at"]
    assert snap["mismatched_files"] == []
    assert snap["build_digest_matched"] is False
    assert "signature_ok" not in snap

    with contextlib.closing(sqlite3.connect(cfg["sqlite_path"])) as conn:
        row = conn.execute(
            "SELECT release_label, validator_version, build_digest_matched "
            "FROM build_integrity_anchor"
        ).fetchone()
        cols = {
            r[1]
            for r in conn.execute(
                "PRAGMA table_info(build_integrity_anchor)"
            ).fetchall()
        }
    assert row is not None
    assert row[2] == 0
    assert "build_digest_matched" in cols
    assert "signature_ok" not in cols

    events = list_integrity_events(cfg)
    assert events[-1]["event_type"] == "validation"
    assert "build_digest_matched=" in events[-1]["detail"]


def test_second_run_reverifies_ok(tmp_path):
    cfg = _cfg(tmp_path)
    ensure_integrity_anchor(cfg)
    snap = ensure_integrity_anchor(cfg)
    assert snap["integrity_state"] == "validated"
    types = [e["event_type"] for e in list_integrity_events(cfg)]
    assert "re-verify" in types


def test_hashes_cover_behaviour_critical_modules():
    hashes = compute_module_hashes()
    for rel in (
        "main.py",
        "core/detector.py",
        "core/engine.py",
        "core/integrity_anchor.py",
        "core/licensing/guard.py",
        "api/routes.py",
    ):
        assert rel in hashes
        assert hashes[rel] != "missing"


# --- 3. tamper detection ---------------------------------------------------------


def _tamper(monkeypatch):
    """Simulate post-anchor module drift (e.g. clamp removed from engine.py)."""
    drifted = compute_module_hashes()
    drifted["core/engine.py"] = "0" * 64
    monkeypatch.setattr("core.integrity_anchor.compute_module_hashes", lambda: drifted)


def test_tamper_marks_adulterated_with_event_and_critical_log(
    tmp_path, monkeypatch, caplog
):
    cfg = _cfg(tmp_path)
    ensure_integrity_anchor(cfg)
    _tamper(monkeypatch)
    with caplog.at_level(logging.DEBUG, logger="core.integrity_anchor"):
        snap = ensure_integrity_anchor(cfg)
    assert snap["integrity_state"] == "tampered"
    assert snap["trust_level"] == "adulterated"
    assert snap["mismatched_files"] == ["core/engine.py"]
    events = list_integrity_events(cfg)
    assert events[0]["event_type"] == "tamper"
    assert "core/engine.py" in events[0]["detail"]
    assert any(r.levelno == logging.CRITICAL for r in caplog.records)


def test_tamper_detected_in_open_mode_without_licensing_config(tmp_path, monkeypatch):
    """E.3: re-verify runs in ANY mode — open mode (no licensing block) included."""
    cfg = _cfg(tmp_path)  # no licensing: key at all
    ensure_integrity_anchor(cfg)
    _tamper(monkeypatch)
    assert ensure_integrity_anchor(cfg)["integrity_state"] == "tampered"


def test_release_upgrade_rebaselines_without_tamper(tmp_path, monkeypatch):
    """#1262: release_label change + new hashes → re-baseline, not tampered."""
    cfg = _cfg(tmp_path)
    monkeypatch.setattr("core.integrity_anchor._release_label", lambda: "1.7.4.post4")
    ensure_integrity_anchor(cfg)

    drifted = compute_module_hashes()
    drifted["core/engine.py"] = "a" * 64
    monkeypatch.setattr("core.integrity_anchor.compute_module_hashes", lambda: drifted)
    monkeypatch.setattr("core.integrity_anchor._release_label", lambda: "1.7.4.post5")
    snap = ensure_integrity_anchor(cfg)
    assert snap["integrity_state"] == "validated"
    assert snap["trust_level"] == "expected"
    assert snap["release_label"] == "1.7.4.post5"
    assert snap["mismatched_files"] == []

    with contextlib.closing(sqlite3.connect(cfg["sqlite_path"])) as conn:
        rows = conn.execute(
            "SELECT release_label, file_hashes_json FROM build_integrity_anchor"
        ).fetchall()
    assert len(rows) == 1
    assert rows[0][0] == "1.7.4.post5"
    stored = json.loads(rows[0][1])
    assert stored["core/engine.py"] == "a" * 64

    events = list_integrity_events(cfg)
    assert any(e["event_type"] == "re-baseline" for e in events)
    re_bl = next(e for e in events if e["event_type"] == "re-baseline")
    assert "1.7.4.post4 -> 1.7.4.post5" in re_bl["detail"]
    assert not any(e["event_type"] == "tamper" for e in events)


def test_same_release_label_still_detects_tamper(tmp_path, monkeypatch):
    """#1262 regression: same label + hash drift remains tampered (not softened)."""
    cfg = _cfg(tmp_path)
    monkeypatch.setattr("core.integrity_anchor._release_label", lambda: "1.7.4.post5")
    ensure_integrity_anchor(cfg)
    _tamper(monkeypatch)
    monkeypatch.setattr("core.integrity_anchor._release_label", lambda: "1.7.4.post5")
    snap = ensure_integrity_anchor(cfg)
    assert snap["integrity_state"] == "tampered"
    assert snap["trust_level"] == "adulterated"
    assert "core/engine.py" in snap["mismatched_files"]
    assert any(e["event_type"] == "tamper" for e in list_integrity_events(cfg))
    assert not any(e["event_type"] == "re-baseline" for e in list_integrity_events(cfg))


# --- 4. survives wipe_all_data (--reset-data) ------------------------------------


def test_anchor_and_events_survive_wipe_all_data(tmp_path, monkeypatch):
    from core.database import LocalDBManager

    cfg = _cfg(tmp_path)
    ensure_integrity_anchor(cfg)
    db = LocalDBManager(cfg["sqlite_path"])
    try:
        db.wipe_all_data("test --reset-data semantics (#856)")
    finally:
        db.dispose()

    with contextlib.closing(sqlite3.connect(cfg["sqlite_path"])) as conn:
        anchor = conn.execute("SELECT COUNT(*) FROM build_integrity_anchor").fetchone()
        events = conn.execute("SELECT COUNT(*) FROM integrity_events").fetchone()
    assert anchor[0] == 1
    assert events[0] >= 1

    # And the re-verify still works against the surviving anchor.
    _tamper(monkeypatch)
    assert ensure_integrity_anchor(cfg)["integrity_state"] == "tampered"


# --- 5. TINTED surfaces ------------------------------------------------------------


def test_about_info_forces_alpha_label_when_tampered(tmp_path, monkeypatch):
    from core.about import get_about_info

    cfg = _cfg(tmp_path)
    ensure_integrity_anchor(cfg)
    info = get_about_info()
    assert "-alpha" not in info["version"]
    assert info["integrity_state"] == "validated"
    assert info["build_trust"] == "expected"

    _tamper(monkeypatch)
    ensure_integrity_anchor(cfg)
    info = get_about_info()
    assert "-alpha" in info["version"]
    assert "not CI-validated" in info["version"]
    assert info["integrity_state"] == "tampered"
    assert info["build_trust"] == "adulterated"


def test_enterprise_surface_goes_elevated_on_tamper(tmp_path, monkeypatch):
    from core.enterprise_surface_posture import get_enterprise_surface_posture

    cfg = _cfg(tmp_path)
    ensure_integrity_anchor(cfg)
    _tamper(monkeypatch)
    ensure_integrity_anchor(cfg)
    posture = get_enterprise_surface_posture({})
    assert "integrity_tampered" in posture["reasons"]
    assert posture["severity"] == "elevated"


def test_report_info_sheet_carries_build_trust_rows(tmp_path, monkeypatch):
    """E.9: report Info sheet rows include Build trust / Integrity state."""
    from core.about import get_about_info
    from report.generator import _build_report_info

    cfg = _cfg(tmp_path)
    ensure_integrity_anchor(cfg)
    _tamper(monkeypatch)
    ensure_integrity_anchor(cfg)
    rows = _build_report_info(
        session_id="s-1",
        meta={
            "started_at": "",
            "tenant_name": "",
            "technician_name": "",
            "config_scope_hash": "",
        },
        about=get_about_info(),
        db_rows=[],
        fs_rows=[],
        license_ctx=None,
        config={},
    )
    fields = {r["Field"]: r["Value"] for r in rows}
    assert fields["Build trust"] == "adulterated"
    assert fields["Integrity state"] == "tampered"
    assert "-alpha" in fields["Version"]


# --- 6. open-mode worker clamp -------------------------------------------------------


def _engine(tmp_path, max_workers: int):
    from core.engine import AuditEngine
    from core.licensing.guard import reset_license_guard_for_tests

    reset_license_guard_for_tests()
    cfg: dict = {
        "targets": [],
        "scan": {"max_workers": max_workers},
        "sqlite_path": str(tmp_path / "audit.db"),
    }
    return AuditEngine(cfg, db_path=str(tmp_path / "audit.db"))


def test_open_mode_clamps_workers_to_cap(tmp_path, caplog):
    engine = _engine(tmp_path, max_workers=16)
    with caplog.at_level(logging.DEBUG, logger=AUDIT_LOGGER):
        engine.start_audit()
    assert engine._max_workers == OPEN_MODE_WORKER_CAP
    assert any(
        "open-mode clamp #856" in r.message
        for r in caplog.records
        if r.name == AUDIT_LOGGER
    )


def test_open_mode_below_cap_untouched(tmp_path, caplog):
    engine = _engine(tmp_path, max_workers=1)
    with caplog.at_level(logging.DEBUG, logger=AUDIT_LOGGER):
        engine.start_audit()
    assert engine._max_workers == 1
    assert not any(
        "workers_clamped" in r.message for r in caplog.records if r.name == AUDIT_LOGGER
    )


# --- 7. fail-soft / fail-closed (#1211) -------------------------------------------


def test_unwritable_anchor_path_is_fail_soft(tmp_path):
    bad = tmp_path / "no-such-dir-file" / "x.db"
    bad.parent.write_text("not a directory", encoding="utf-8")  # block mkdir
    snap = ensure_integrity_anchor({"sqlite_path": str(bad)})
    assert snap["integrity_state"] == "unknown"
    assert snap["trust_level"] == "unknown"
    assert snap["build_digest_matched"] is False
    assert snap["integrity_state"] not in ("validated", "tampered")
    assert snap["trust_level"] not in ("expected", "adulterated")
    cached = get_integrity_snapshot()
    assert cached["integrity_state"] == "unknown"
    assert cached["trust_level"] == "unknown"
    assert cached["build_digest_matched"] is False


def test_sqlite_error_on_ensure_never_looks_trusted(tmp_path, monkeypatch):
    """Error path must never surface validated/expected (fail-closed honesty)."""
    cfg = _cfg(tmp_path)

    def _boom(*_a, **_k):
        raise sqlite3.OperationalError("simulated db failure")

    monkeypatch.setattr("core.integrity_anchor.sqlite3.connect", _boom)
    snap = ensure_integrity_anchor(cfg)
    assert snap["integrity_state"] == "unknown"
    assert snap["trust_level"] == "unknown"
    assert snap["build_digest_matched"] is False
    assert "error" in snap


def test_list_integrity_events_fail_closed_on_error(tmp_path, monkeypatch):
    def _boom(*_a, **_k):
        raise OSError("simulated open failure")

    monkeypatch.setattr("core.integrity_anchor.sqlite3.connect", _boom)
    assert list_integrity_events(_cfg(tmp_path)) == []


# --- 8. build_digest_matched honesty (#1211) --------------------------------------


def test_build_digest_matched_false_when_no_expected_digest(tmp_path, monkeypatch):
    monkeypatch.delenv("DATA_BOAR_EXPECTED_BUILD_DIGEST", raising=False)
    snap = ensure_integrity_anchor(_cfg(tmp_path))
    assert snap["build_digest_matched"] is False


def test_build_digest_matched_true_on_match(tmp_path, monkeypatch):
    from core.licensing.integrity import _embedded_build_digest

    dig = _embedded_build_digest()
    monkeypatch.setenv("DATA_BOAR_EXPECTED_BUILD_DIGEST", dig)
    snap = ensure_integrity_anchor(_cfg(tmp_path))
    assert snap["build_digest_matched"] is True


def test_build_digest_matched_false_on_mismatch(tmp_path, monkeypatch):
    monkeypatch.setenv(
        "DATA_BOAR_EXPECTED_BUILD_DIGEST",
        "deadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeef",
    )
    snap = ensure_integrity_anchor(_cfg(tmp_path))
    assert snap["build_digest_matched"] is False


# --- 9. legacy signature_ok → build_digest_matched migration ----------------------


def test_migrates_legacy_signature_ok_column(tmp_path):
    db = tmp_path / "legacy.db"
    hashes = compute_module_hashes()
    now = datetime.now(timezone.utc).isoformat()
    with contextlib.closing(sqlite3.connect(db)) as conn:
        conn.execute(
            """
            CREATE TABLE build_integrity_anchor (
                anchor_version INTEGER PRIMARY KEY,
                release_label TEXT NOT NULL,
                manifest_content_hash TEXT NOT NULL,
                file_hashes_json TEXT NOT NULL,
                validated_at TEXT NOT NULL,
                signature_ok INTEGER NOT NULL,
                validator_version TEXT NOT NULL
            )
            """
        )
        conn.execute(
            "INSERT INTO build_integrity_anchor (anchor_version, release_label, "
            "manifest_content_hash, file_hashes_json, validated_at, signature_ok, "
            "validator_version) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                ANCHOR_VERSION,
                "1.0.0-test",
                _manifest_content_hash(hashes),
                json.dumps(hashes, sort_keys=True),
                now,
                1,
                VALIDATOR_VERSION,
            ),
        )
        conn.execute(
            """
            CREATE TABLE integrity_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                event_type TEXT NOT NULL,
                detail TEXT NOT NULL
            )
            """
        )
        conn.execute(
            "INSERT INTO integrity_events (created_at, event_type, detail) "
            "VALUES (?, ?, ?)",
            (now, "validation", "legacy seed"),
        )
        conn.commit()

    snap = ensure_integrity_anchor({"sqlite_path": str(db)})
    assert snap["integrity_state"] == "validated"
    assert snap["trust_level"] == "expected"
    assert "build_digest_matched" in snap
    # Rename alone would keep the legacy overclaim bit (1); migration must
    # zero it — under-claim until an honest re-baseline.
    assert snap["build_digest_matched"] is False
    assert "signature_ok" not in snap
    assert snap["mismatched_files"] == []  # module-hash baseline intact

    with contextlib.closing(sqlite3.connect(db)) as conn:
        cols = {
            r[1]
            for r in conn.execute(
                "PRAGMA table_info(build_integrity_anchor)"
            ).fetchall()
        }
        bit = conn.execute(
            "SELECT build_digest_matched FROM build_integrity_anchor "
            "WHERE anchor_version = ?",
            (ANCHOR_VERSION,),
        ).fetchone()
        event_count = conn.execute("SELECT COUNT(*) FROM integrity_events").fetchone()[
            0
        ]
    assert "build_digest_matched" in cols
    assert "signature_ok" not in cols
    assert bit is not None and bit[0] == 0
    assert event_count >= 1  # integrity_events preserved across migration
