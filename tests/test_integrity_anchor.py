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
7. Fail-soft: unwritable anchor path → state ``unknown``, no crash.
"""

from __future__ import annotations

import contextlib
import logging
import sqlite3

import pytest

from core.integrity_anchor import (
    OPEN_MODE_WORKER_CAP,
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


def test_first_run_creates_anchor_and_validation_event(tmp_path):
    cfg = _cfg(tmp_path)
    snap = ensure_integrity_anchor(cfg)
    assert snap["integrity_state"] == "validated"
    assert snap["trust_level"] == "expected"
    assert snap["release_label"] not in ("", "unknown")
    assert snap["validated_at"]
    assert snap["mismatched_files"] == []

    with contextlib.closing(sqlite3.connect(cfg["sqlite_path"])) as conn:
        row = conn.execute(
            "SELECT release_label, validator_version FROM build_integrity_anchor"
        ).fetchone()
    assert row is not None

    events = list_integrity_events(cfg)
    assert events[-1]["event_type"] == "validation"


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


# --- 7. fail-soft -----------------------------------------------------------------


def test_unwritable_anchor_path_is_fail_soft(tmp_path):
    bad = tmp_path / "no-such-dir-file" / "x.db"
    bad.parent.write_text("not a directory", encoding="utf-8")  # block mkdir
    snap = ensure_integrity_anchor({"sqlite_path": str(bad)})
    assert snap["integrity_state"] == "unknown"
    assert get_integrity_snapshot()["integrity_state"] == "unknown"
