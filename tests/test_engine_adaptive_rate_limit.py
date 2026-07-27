"""AuditEngine adaptive rate limiting (#1320) — production path wiring."""

from __future__ import annotations

import threading
import time
from typing import Any
from unittest.mock import MagicMock

import pytest

from core.engine import AuditEngine


def _filesystem_targets(n: int) -> list[dict[str, Any]]:
    return [
        {"name": f"target-{i}", "type": "filesystem", "path": "/tmp"} for i in range(n)
    ]


def _engine(
    tmp_path, config: dict[str, Any], *, monkeypatch: pytest.MonkeyPatch
) -> AuditEngine:
    eng = AuditEngine(config, db_path=str(tmp_path / "audit.db"))
    monkeypatch.setattr(eng.db_manager, "finish_session", MagicMock())
    eng.db_manager.set_current_session_id("sess-test")
    return eng


def test_engine_adaptive_rate_limit_defaults_off(tmp_path, monkeypatch) -> None:
    eng = _engine(
        tmp_path,
        {"targets": [], "scan": {}, "file_scan": {}, "detection": {}},
        monkeypatch=monkeypatch,
    )
    assert eng._adaptive_rate_limit is False
    assert eng._target_latency_ms == 200.0


def test_engine_fixed_parallel_uses_thread_pool_concurrency(
    tmp_path, monkeypatch
) -> None:
    """Without ARL, max_workers>1 may run multiple targets concurrently."""
    config: dict[str, Any] = {
        "targets": _filesystem_targets(8),
        "scan": {"max_workers": 4, "adaptive_rate_limit": False},
        "file_scan": {},
        "detection": {},
    }
    eng = _engine(tmp_path, config, monkeypatch=monkeypatch)
    active = 0
    max_active = 0
    lock = threading.Lock()

    def _slow_run(_target: dict[str, Any]) -> None:
        nonlocal active, max_active
        with lock:
            active += 1
            max_active = max(max_active, active)
        time.sleep(0.06)
        with lock:
            active -= 1

    monkeypatch.setattr(eng, "_run_target", _slow_run)
    eng._run_audit_targets()
    assert max_active >= 3


def test_engine_adaptive_reduces_concurrency_under_induced_latency(
    tmp_path, monkeypatch
) -> None:
    """ARL on the engine path: slow targets + low target_latency_ms cap in-flight work."""
    config: dict[str, Any] = {
        "targets": _filesystem_targets(10),
        "scan": {
            "max_workers": 8,
            "adaptive_rate_limit": True,
            "target_latency_ms": 1.0,
        },
        "file_scan": {},
        "detection": {},
    }
    eng = _engine(tmp_path, config, monkeypatch=monkeypatch)
    active = 0
    max_active = 0
    lock = threading.Lock()

    def _slow_run(_target: dict[str, Any]) -> None:
        nonlocal active, max_active
        with lock:
            active += 1
            max_active = max(max_active, active)
        time.sleep(0.05)
        with lock:
            active -= 1

    monkeypatch.setattr(eng, "_run_target", _slow_run)
    eng._run_audit_targets()
    assert max_active == 1


def test_engine_adaptive_throttler_ceiling_uses_clamped_max_workers(
    tmp_path, monkeypatch
) -> None:
    """Tier/licensing cap on _max_workers is the hard ceiling passed to BoarThrottler."""
    config: dict[str, Any] = {
        "targets": _filesystem_targets(2),
        "scan": {
            "max_workers": 8,
            "adaptive_rate_limit": True,
            "target_latency_ms": 200.0,
        },
        "file_scan": {},
        "detection": {},
    }
    eng = _engine(tmp_path, config, monkeypatch=monkeypatch)
    eng._max_workers = 2
    monkeypatch.setattr(eng, "_run_target", lambda _t: None)

    captured: list[int] = []

    real_init = None

    def _spy_init(self, *, target_latency_ms=200.0, max_workers=10, **kwargs):
        captured.append(int(max_workers))
        return real_init(
            self,
            target_latency_ms=target_latency_ms,
            max_workers=max_workers,
            **kwargs,
        )

    from core import throttler as throttler_mod

    real_init = throttler_mod.BoarThrottler.__init__
    monkeypatch.setattr(throttler_mod.BoarThrottler, "__init__", _spy_init)
    eng._run_audit_targets()
    assert captured == [2]
