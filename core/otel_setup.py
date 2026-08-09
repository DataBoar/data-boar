"""Optional OpenTelemetry setup for FastAPI + SQLAlchemy (issue #1500).

Opt-in only. When disabled or packages missing, this module is a no-op so
``python main.py`` never depends on OTel.
"""

from __future__ import annotations

import logging
import os
from typing import Any
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

_ENV_ENABLED = "DATA_BOAR_OTEL_ENABLED"
_ENV_ENDPOINT = "OTEL_EXPORTER_OTLP_ENDPOINT"
_DEFAULT_ENDPOINT = "http://127.0.0.1:4317"
_LOOPBACK_HOSTS = frozenset({"127.0.0.1", "localhost", "::1"})


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


def maybe_setup_otel(app: Any | None = None) -> bool:
    """Initialize OTel exporters + instrument FastAPI (and SQLAlchemy when available).

    Returns True if instrumentation was applied; False when skipped (default).
    Never raises into the caller for missing optional deps or setup failures.
    """
    if not otel_enabled():
        return False

    endpoint = otel_endpoint()
    try:
        from opentelemetry import metrics, trace
        from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import (
            OTLPMetricExporter,
        )
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import (
            OTLPSpanExporter,
        )
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
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

        if app is not None:
            FastAPIInstrumentor.instrument_app(app)

        try:
            from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor

            SQLAlchemyInstrumentor().instrument()
        except Exception as sqlalchemy_exc:  # noqa: BLE001 — optional path
            logger.info("OTel SQLAlchemy instrumentation skipped: %s", sqlalchemy_exc)

        logger.info(
            "OpenTelemetry enabled (endpoint=%s, insecure=%s). Set %s=0 to disable.",
            endpoint,
            insecure,
            _ENV_ENABLED,
        )
        return True
    except Exception as exc:  # noqa: BLE001 — never block app start
        logger.warning("OpenTelemetry setup failed (continuing without OTel): %s", exc)
        return False
