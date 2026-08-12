"""Regression for optional OpenTelemetry gate (#1500 / #1529 / #1535)."""

from __future__ import annotations

import os

import pytest

import core.otel_setup as otel_setup
from core.otel_setup import (
    get_tracer,
    maybe_setup_otel,
    otel_enabled,
    otel_endpoint,
    otel_span,
    otlp_insecure_for_endpoint,
    sanitize_otlp_endpoint_for_log,
)


@pytest.fixture(autouse=True)
def _reset_otel_module_state() -> None:
    """Keep module-level OTel flags isolated across tests in this file."""
    otel_setup._otel_providers_ready = False
    otel_setup._fastapi_instrumented = False
    # Leave logging handlers list alone if already attached (process-wide);
    # clear so LoggingHandler can be re-asserted when packages are present.
    root = __import__("logging").getLogger()
    for handler in list(otel_setup._otel_logging_handlers):
        try:
            root.removeHandler(handler)
        except Exception:  # noqa: BLE001
            pass
    otel_setup._otel_logging_handlers.clear()
    yield


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


@pytest.mark.parametrize(
    ("endpoint", "expect_insecure"),
    [
        ("http://127.0.0.1:4317", True),
        ("http://localhost:4317", True),
        ("http://[::1]:4317", True),
        ("https://otel.example.com:4317", False),
        ("http://otel.example.com:4317", False),
    ],
)
def test_otlp_insecure_only_for_loopback(endpoint: str, expect_insecure: bool) -> None:
    assert otlp_insecure_for_endpoint(endpoint) is expect_insecure


@pytest.mark.parametrize(
    ("endpoint", "expected"),
    [
        (
            "https://user:secret@otel.example.com:4317/v1/traces?token=abc",
            "https://otel.example.com:4317",
        ),
        ("http://127.0.0.1:4317", "http://127.0.0.1:4317"),
        ("http://[::1]:4317", "http://[::1]:4317"),
        ("https://otel.example.com", "https://otel.example.com"),
        ("not-a-url", "<invalid-endpoint>"),
    ],
)
def test_sanitize_otlp_endpoint_for_log(endpoint: str, expected: str) -> None:
    assert sanitize_otlp_endpoint_for_log(endpoint) == expected


def test_otel_enabled_call_does_not_raise(monkeypatch: pytest.MonkeyPatch) -> None:
    """Enabled path must never crash startup (True if packages present, else False)."""
    monkeypatch.setenv("DATA_BOAR_OTEL_ENABLED", "1")
    monkeypatch.setenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://127.0.0.1:4317")
    # maybe_setup_otel never raises by contract — assign before assert (CodeQL).
    result = maybe_setup_otel(app=None)
    assert result in {True, False}
    monkeypatch.delenv("DATA_BOAR_OTEL_ENABLED", raising=False)
    assert maybe_setup_otel(app=None) is False
    assert os.environ.get("DATA_BOAR_OTEL_ENABLED") in (None, "")


def test_otel_cli_early_setup_app_none_idempotent(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """#1535: early CLI call with app=None; second call stays True when packages present."""
    monkeypatch.setenv("DATA_BOAR_OTEL_ENABLED", "1")
    monkeypatch.setenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://127.0.0.1:4317")
    first = maybe_setup_otel(app=None)
    second = maybe_setup_otel(app=None)
    assert first in {True, False}
    assert second == first
    if first:
        assert otel_setup._otel_providers_ready is True


def test_otel_span_noop_when_providers_not_ready(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Manual spans must not raise when OTel is off."""
    monkeypatch.delenv("DATA_BOAR_OTEL_ENABLED", raising=False)
    assert maybe_setup_otel(app=None) is False
    with otel_span("scan", mode="oneshot") as span:
        assert span is None
    tracer = get_tracer()
    with tracer.start_as_current_span("noop"):
        pass


def test_otel_logger_provider_and_stdlib_bridge(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """#1529: when otel extra is installed, enable path wires LoggerProvider + root handler."""
    pytest.importorskip("opentelemetry.sdk._logs")
    pytest.importorskip("opentelemetry.instrumentation.logging.handler")

    import logging

    from opentelemetry._logs import get_logger_provider
    from opentelemetry.instrumentation.logging.handler import LoggingHandler
    from opentelemetry.sdk._logs import LoggerProvider

    monkeypatch.setenv("DATA_BOAR_OTEL_ENABLED", "1")
    monkeypatch.setenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://127.0.0.1:4317")
    monkeypatch.setenv("OTEL_SERVICE_NAME", "data-boar-test-1529")

    assert maybe_setup_otel(app=None) is True
    provider = get_logger_provider()
    assert isinstance(provider, LoggerProvider)

    handlers = logging.getLogger().handlers
    assert any(isinstance(h, LoggingHandler) for h in handlers), (
        "stdlib root logger must get OTel LoggingHandler when OTel is enabled"
    )
