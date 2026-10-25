"""Optional OpenTelemetry setup for FastAPI + SQLAlchemy + CLI (#1500 / #1529 / #1535).

Opt-in only. When disabled or packages missing, this module is a no-op so
``python main.py`` never depends on OTel.

Signals when enabled: traces, metrics, and **logs** (``LoggerProvider`` +
stdlib ``logging`` bridge → OTLP → collector → Loki on the lab LGTM stack).

CLI / oneshot (#1535): call ``maybe_setup_otel(app=None)`` early from ``main.py``;
pass ``app`` later for FastAPI. Setup is idempotent. Short-lived processes
register ``atexit`` force-flush so Batch exporters still ship.
"""

from __future__ import annotations

import atexit
import logging
import os
from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

_ENV_ENABLED = "DATA_BOAR_OTEL_ENABLED"
_ENV_ENDPOINT = "OTEL_EXPORTER_OTLP_ENDPOINT"
_DEFAULT_ENDPOINT = "http://127.0.0.1:4317"
_LOOPBACK_HOSTS = frozenset({"127.0.0.1", "localhost", "::1"})
_TRACER_NAME = "data-boar"

# Root handler attached once per process when OTel logs are enabled (#1529).
_otel_logging_handlers: list[logging.Handler] = []
_otel_providers_ready = False
_fastapi_instrumented = False
_atexit_flush_registered = False


def otel_enabled() -> bool:
    """Return True only when the product gate env is an explicit truthy value."""
    raw = (os.environ.get(_ENV_ENABLED) or "").strip().lower()
    return raw in {"1", "true", "yes", "on"}


def otel_endpoint() -> str:
    """OTLP endpoint; override via ``OTEL_EXPORTER_OTLP_ENDPOINT`` (no lab hostname hardcoded)."""
    return (os.environ.get(_ENV_ENDPOINT) or "").strip() or _DEFAULT_ENDPOINT


def otlp_insecure_for_endpoint(endpoint: str) -> bool:
    """Allow plaintext OTLP only for loopback hosts; remote collectors use TLS."""
    host = (urlparse(endpoint).hostname or "").strip().lower()
    return host in _LOOPBACK_HOSTS


def sanitize_otlp_endpoint_for_log(endpoint: str) -> str:
    """Return scheme://host[:port] only — strip userinfo, path, query, fragment."""
    parsed = urlparse(endpoint)
    scheme = (parsed.scheme or "").strip().lower()
    host = (parsed.hostname or "").strip()
    if not scheme or not host:
        return "<invalid-endpoint>"
    # Bracket IPv6 for unambiguous host:port form.
    if ":" in host and not host.startswith("["):
        host = f"[{host}]"
    if parsed.port is not None:
        return f"{scheme}://{host}:{parsed.port}"
    return f"{scheme}://{host}"


def _emit_boar_fast_filter_status_log() -> None:
    """Emit one structured status line for Loki proof of accelerator presence (#1529)."""
    try:
        from core.pro_scan_path import rust_accelerator_installed

        installed = rust_accelerator_installed()
    except Exception as exc:  # noqa: BLE001 — never block OTel setup
        logger.info(
            "boar_fast_filter status unknown (probe failed: %s)",
            exc,
            extra={"boar_fast_filter_installed": None},
        )
        return
    logger.info(
        "boar_fast_filter status installed=%s",
        installed,
        extra={"boar_fast_filter_installed": installed},
    )


def _force_flush_otel() -> None:
    """Best-effort flush for short-lived CLI processes (#1535)."""
    try:
        from opentelemetry import metrics, trace
        from opentelemetry._logs import get_logger_provider

        tp = trace.get_tracer_provider()
        if hasattr(tp, "force_flush"):
            tp.force_flush()
        mp = metrics.get_meter_provider()
        if hasattr(mp, "force_flush"):
            mp.force_flush()
        lp = get_logger_provider()
        if hasattr(lp, "force_flush"):
            lp.force_flush()
    except Exception:  # noqa: BLE001 — never block process exit
        pass


def get_tracer() -> Any:
    """Return tracer ``data-boar``, or a no-op object when OTel SDK is absent."""
    try:
        from opentelemetry import trace

        return trace.get_tracer(_TRACER_NAME)
    except Exception:  # noqa: BLE001

        class _NoopSpan:
            def __enter__(self) -> _NoopSpan:
                return self

            def __exit__(self, *args: object) -> None:
                return None

            def set_attribute(self, *_a: object, **_k: object) -> None:
                return None

        class _NoopTracer:
            def start_as_current_span(self, *_a: object, **_k: object) -> _NoopSpan:
                return _NoopSpan()

        return _NoopTracer()


@contextmanager
def otel_span(name: str, **attributes: Any) -> Iterator[Any]:
    """Context manager for a manual span; no-op when providers are not ready."""
    if not _otel_providers_ready:
        yield None
        return
    tracer = get_tracer()
    with tracer.start_as_current_span(name) as span:
        if span is not None:
            for key, value in attributes.items():
                if value is not None and hasattr(span, "set_attribute"):
                    try:
                        span.set_attribute(key, value)
                    except Exception:  # noqa: BLE001
                        pass
        yield span


def maybe_setup_otel(app: Any | None = None) -> bool:
    """Initialize OTel exporters + optionally instrument FastAPI.

    Returns True if providers are ready (or already were); False when skipped.
    Never raises into the caller for missing optional deps or setup failures.
    Idempotent: a second call with ``app`` only attaches FastAPI instrumentation.
    """
    global _otel_providers_ready, _fastapi_instrumented, _atexit_flush_registered

    if not otel_enabled():
        return False

    if _otel_providers_ready:
        if app is not None and not _fastapi_instrumented:
            try:
                from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

                FastAPIInstrumentor.instrument_app(app)
                _fastapi_instrumented = True
            except Exception as exc:  # noqa: BLE001
                logger.info("OTel FastAPI instrumentation skipped: %s", exc)
        return True

    endpoint = otel_endpoint()
    try:
        from opentelemetry import metrics, trace
        from opentelemetry._logs import set_logger_provider
        from opentelemetry.exporter.otlp.proto.grpc._log_exporter import (
            OTLPLogExporter,
        )
        from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import (
            OTLPMetricExporter,
        )
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import (
            OTLPSpanExporter,
        )
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
        from opentelemetry.instrumentation.logging.handler import LoggingHandler
        from opentelemetry.sdk._logs import LoggerProvider
        from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
        from opentelemetry.sdk.metrics import MeterProvider
        from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
    except ImportError as exc:
        logger.warning(
            "DATA_BOAR_OTEL_ENABLED set but OpenTelemetry packages missing (%s). "
            "Install optional extra: uv sync --extra otel",
            exc,
        )
        return False

    try:
        resource = Resource.create(
            {
                "service.name": os.environ.get("OTEL_SERVICE_NAME", "data-boar"),
                "service.namespace": "databoar",
            }
        )
        insecure = otlp_insecure_for_endpoint(endpoint)
        tracer_provider = TracerProvider(resource=resource)
        tracer_provider.add_span_processor(
            BatchSpanProcessor(OTLPSpanExporter(endpoint=endpoint, insecure=insecure))
        )
        trace.set_tracer_provider(tracer_provider)

        metric_reader = PeriodicExportingMetricReader(
            OTLPMetricExporter(endpoint=endpoint, insecure=insecure)
        )
        metrics.set_meter_provider(
            MeterProvider(resource=resource, metric_readers=[metric_reader])
        )

        # Logs (#1529): same endpoint/insecure policy as traces/metrics.
        logger_provider = LoggerProvider(resource=resource)
        logger_provider.add_log_record_processor(
            BatchLogRecordProcessor(
                OTLPLogExporter(endpoint=endpoint, insecure=insecure)
            )
        )
        set_logger_provider(logger_provider)
        if not _otel_logging_handlers:
            # Prefer instrumentation LoggingHandler (sdk._logs.LoggingHandler is deprecated).
            handler = LoggingHandler(
                level=logging.INFO,
                logger_provider=logger_provider,
            )
            logging.getLogger().addHandler(handler)
            _otel_logging_handlers.append(handler)

        if app is not None:
            FastAPIInstrumentor.instrument_app(app)
            _fastapi_instrumented = True

        try:
            from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor

            SQLAlchemyInstrumentor().instrument()
        except Exception as sqlalchemy_exc:  # noqa: BLE001 — optional path
            logger.info("OTel SQLAlchemy instrumentation skipped: %s", sqlalchemy_exc)

        _otel_providers_ready = True
        if not _atexit_flush_registered:
            atexit.register(_force_flush_otel)
            _atexit_flush_registered = True

        logger.info(
            "OpenTelemetry enabled (endpoint=%s, insecure=%s, signals=traces+metrics+logs). "
            "Set %s=0 to disable.",
            sanitize_otlp_endpoint_for_log(endpoint),
            insecure,
            _ENV_ENABLED,
        )
        _emit_boar_fast_filter_status_log()
        return True
    except Exception as exc:  # noqa: BLE001 — never block app start
        logger.warning("OpenTelemetry setup failed (continuing without OTel): %s", exc)
        return False
