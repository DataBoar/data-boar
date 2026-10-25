"""Runtime tier resolution including TAMPERED state (ADR-0066, #712)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from core.licensing.guard import reset_license_guard_for_tests
from core.licensing.runtime_feature_tier import get_runtime_tier_for_features
from core.licensing.tier_features import Tier


@pytest.fixture(autouse=True)
def _reset_guard():
    reset_license_guard_for_tests()
    yield
    reset_license_guard_for_tests()


def _tampered_guard(mode: str) -> MagicMock:
    ctx = MagicMock()
    ctx.state = "TAMPERED"
    ctx.detail = "tampered_build"
    guard = MagicMock()
    guard.mode = mode
    guard.context = ctx
    return guard


@patch("core.licensing.guard.get_license_guard")
def test_tampered_enforced_returns_community(mock_get_guard):
    mock_get_guard.return_value = _tampered_guard("enforced")
    cfg = {"licensing": {"mode": "enforced", "effective_tier": "enterprise"}}
    assert get_runtime_tier_for_features(cfg) == Tier.COMMUNITY


@patch("core.licensing.guard.get_license_guard")
def test_tampered_open_returns_open_and_logs_critical(mock_get_guard, caplog):
    mock_get_guard.return_value = _tampered_guard("open")
    cfg = {"licensing": {"mode": "open"}}
    with caplog.at_level("CRITICAL", logger="data_boar.licensing"):
        assert get_runtime_tier_for_features(cfg) == Tier.OPEN
    assert any(
        "TAMPERED" in rec.message and "open mode" in rec.message
        for rec in caplog.records
    )
