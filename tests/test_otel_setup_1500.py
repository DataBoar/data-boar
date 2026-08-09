"""Regression for optional OpenTelemetry gate (#1500)."""

from __future__ import annotations

import os

import pytest

from core.otel_setup import maybe_setup_otel, otel_enabled, otel_endpoint


def test_otel_disabled_by_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DATA_BOAR_OTEL_ENABLED", raising=False)
    assert otel_enabled() is False
    assert maybe_setup_otel(app=None) is False


@pytest.mark.parametrize("truthy", ["1", "true", "YES", "on"])
def test_otel_enabled_truthy(monkeypatch: pytest.MonkeyPatch, truthy: str) -> None:
    monkeypatch.setenv("DATA_BOAR_OTEL_ENABLED", truthy)
    assert otel_enabled() is True


def test_otel_endpoint_default_and_override(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OTEL_EXPORTER_OTLP_ENDPOINT", raising=False)
    assert otel_endpoint() == "http://127.0.0.1:4317"
    monkeypatch.setenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://example.invalid:4317")
    assert otel_endpoint() == "http://example.invalid:4317"


def test_otel_enabled_call_does_not_raise(monkeypatch: pytest.MonkeyPatch) -> None:
    """Enabled path must never crash startup (True if packages present, else False)."""
    monkeypatch.setenv("DATA_BOAR_OTEL_ENABLED", "1")
    monkeypatch.setenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://127.0.0.1:4317")
    try:
        result = maybe_setup_otel(app=None)
    except Exception as exc:  # pragma: no cover
        pytest.fail(f"maybe_setup_otel raised: {exc}")
    assert result in {True, False}
    monkeypatch.delenv("DATA_BOAR_OTEL_ENABLED", raising=False)
    assert maybe_setup_otel(app=None) is False
    assert os.environ.get("DATA_BOAR_OTEL_ENABLED") in (None, "")
