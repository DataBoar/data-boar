"""AuditEngine orchestration (connector resolution, instantiation, run)."""

from __future__ import annotations

from typing import Any

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
