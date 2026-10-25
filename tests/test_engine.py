"""AuditEngine orchestration (connector resolution, instantiation, run)."""

from __future__ import annotations

import threading
from typing import Any

import pytest

from core.engine import AuditEngine


def test_run_target_instantiation_error_records_save_failure_sequential(
    tmp_path, monkeypatch
) -> None:
    """Sequential mode must not let __init__ exceptions escape without save_failure (#513)."""
    config: dict[str, Any] = {
        "targets": [
            {
                "name": "bad-target",
                "type": "database",
                "driver": "postgresql",
            }
        ],
        "file_scan": {
            "sample_limit": 5,
            "extensions": [".txt"],
        },
        "detection": {},
    }
    eng = AuditEngine(config, db_path=str(tmp_path / "audit.db"))
    recorded: list[tuple[str, str, str]] = []

    def capture_save_failure(name: str, reason: str, detail: str) -> None:
        recorded.append((name, reason, detail))

    monkeypatch.setattr(eng.db_manager, "save_failure", capture_save_failure)

    class BoomInit:
        def __init__(self, *_a: object, **_k: object) -> None:
            raise RuntimeError("connector init failed")

        def run(self) -> None:
            raise AssertionError("run should not be reached")

    def fake_resolve(_target: dict[str, Any]) -> tuple[type, list[str]]:
        return BoomInit, []

    monkeypatch.setattr("core.engine.connector_for_target", fake_resolve)

    eng._run_target(config["targets"][0])

    assert len(recorded) == 1
    assert recorded[0][0] == "bad-target"
    assert recorded[0][1] == "error"
    assert "init failed" in recorded[0][2]


def test_run_target_run_error_still_records_save_failure(tmp_path, monkeypatch) -> None:
    config: dict[str, Any] = {
        "targets": [{"name": "run-fail", "type": "database", "driver": "postgresql"}],
        "file_scan": {"sample_limit": 5, "extensions": [".txt"]},
        "detection": {},
    }
    eng = AuditEngine(config, db_path=str(tmp_path / "audit2.db"))
    recorded: list[tuple[str, str, str]] = []

    monkeypatch.setattr(
        eng.db_manager,
        "save_failure",
        lambda n, r, d: recorded.append((n, r, d)),
    )

    class RunFails:
        def __init__(self, *_a: object, **_k: object) -> None:
            pass

        def run(self) -> None:
            raise ValueError("run exploded")

    monkeypatch.setattr(
        "core.engine.connector_for_target",
        lambda _t: (RunFails, []),
    )

    eng._run_target(config["targets"][0])

    assert len(recorded) == 1
    assert recorded[0][0] == "run-fail"
    assert "exploded" in recorded[0][2]


def test_unknown_target_type_creates_failure(tmp_path, monkeypatch) -> None:
    """Unknown target type must record scan_failures (ADR-0049, #416)."""
    config: dict[str, Any] = {
        "targets": [{"name": "snow", "type": "unknowntype_xyz"}],
        "file_scan": {"sample_limit": 5, "extensions": [".txt"]},
        "detection": {},
    }
    eng = AuditEngine(config, db_path=str(tmp_path / "audit3.db"))
    recorded: list[tuple[str, str, str]] = []

    monkeypatch.setattr(
        eng.db_manager,
        "save_failure",
        lambda n, r, d: recorded.append((n, r, d)),
    )
    monkeypatch.setattr("core.engine.connector_for_target", lambda _t: None)

    eng._run_target(config["targets"][0])

    assert len(recorded) == 1
    assert recorded[0][0] == "snow"
    assert recorded[0][1] == "unknown_connector_type"
    assert "unknowntype_xyz" in recorded[0][2]
    assert "typo" in recorded[0][2].lower()


def _minimal_engine_config() -> dict[str, Any]:
    return {
        "targets": [],
        "file_scan": {"sample_limit": 5, "extensions": [".txt"]},
        "detection": {},
    }


def test_try_claim_running_is_exclusive(tmp_path) -> None:
    """Compare-and-set: only one caller owns the process-wide run slot (#415)."""
    eng = AuditEngine(_minimal_engine_config(), db_path=str(tmp_path / "claim.db"))
    assert eng.try_claim_running() is True
    assert eng.is_running is True
    assert eng.try_claim_running() is False
    eng.clear_running()
    assert eng.is_running is False
    assert eng.try_claim_running() is True
    eng.clear_running()


def test_try_claim_running_exclusive_under_threads(tmp_path) -> None:
    eng = AuditEngine(_minimal_engine_config(), db_path=str(tmp_path / "claim-t.db"))
    wins: list[bool] = []
    barrier = threading.Barrier(16)

    def worker() -> None:
        barrier.wait()
        wins.append(eng.try_claim_running())

    threads = [threading.Thread(target=worker) for _ in range(16)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert sum(wins) == 1
    assert eng.is_running is True
    eng.clear_running()


def test_start_audit_raises_when_slot_already_claimed(tmp_path) -> None:
    eng = AuditEngine(
        _minimal_engine_config(), db_path=str(tmp_path / "claim-start.db")
    )
    assert eng.try_claim_running() is True
    with pytest.raises(RuntimeError, match="already in progress"):
        eng.start_audit()
    eng.clear_running()
