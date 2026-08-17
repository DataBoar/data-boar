"""Cloudflare GraphQL Analytics → normalized edge metrics (#1599).

Server-side only. Never embeds tokens in browser code. Does **not** emit
distributed traces — aggregate edge counters only, with ``service.name=cloudflare-edge``.

Dataset: ``httpRequestsAdaptiveGroups`` (current Cloudflare GraphQL Analytics node).
"""

from __future__ import annotations

import json
import logging
import os
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

GRAPHQL_URL_DEFAULT = "https://api.cloudflare.com/client/v4/graphql"
SERVICE_NAME = "cloudflare-edge"
QUERY_VERSION = "httpRequestsAdaptiveGroups.v1"

# Documented eyeball filter excludes Cloudflare-internal activity.
# Dimensions chosen for bounded cardinality (no path/query/IP/referrer/UA).
QUERY_HTTP_REQUESTS_ADAPTIVE_V1 = """
query DataBoarCfEdgeMetricsV1(
  $zoneTag: string
  $start: Time
  $end: Time
  $limit: int64!
) {
  viewer {
    zones(filter: { zoneTag: $zoneTag }) {
      series: httpRequestsAdaptiveGroups(
        filter: {
          datetime_geq: $start
          datetime_lt: $end
          requestSource: "eyeball"
        }
        limit: $limit
        orderBy: [datetimeHour_ASC]
      ) {
        count
        sum {
          visits
          edgeResponseBytes
        }
        dimensions {
          datetimeHour
          clientRequestHTTPHost
          cacheStatus
          edgeResponseStatus
        }
      }
    }
  }
}
""".strip()

# Allowlisted cache labels; everything else collapses to OTHER.
_CACHE_ALLOWLIST = frozenset(
    {
        "HIT",
        "MISS",
        "EXPIRED",
        "BYPASS",
        "REVALIDATED",
        "UPDATING",
        "DYNAMIC",
        "NONE",
        "UNKNOWN",
    }
)

_ENV_TOKEN = "CLOUDFLARE_API_TOKEN"
_ENV_ZONE = "CLOUDFLARE_ZONE_ID"
_ENV_URL = "CLOUDFLARE_GRAPHQL_URL"
_ENV_ALLOW_ALL_ZONES = "CLOUDFLARE_ALLOW_ALL_ZONES_FOR_LOCAL_TEST"


@dataclass(frozen=True)
class MetricPoint:
    """One privacy-safe aggregate point for OTLP counters."""

    metric: str
    value: float
    attributes: dict[str, str]
    timestamp: datetime | None = None


@dataclass
class ExportWindow:
    start: datetime
    end: datetime
    overlap: timedelta
    lag: timedelta


@dataclass
class NormalizedBatch:
    query_version: str
    window: ExportWindow
    points: list[MetricPoint] = field(default_factory=list)
    raw_group_count: int = 0
    dropped_hostname_count: int = 0


def status_class(status: int | None) -> str:
    """Map HTTP status to a bounded class label."""
    if status is None:
        return "unknown"
    if 200 <= status < 300:
        return "2xx"
    if 300 <= status < 400:
        return "3xx"
    if 400 <= status < 500:
        return "4xx"
    if 500 <= status < 600:
        return "5xx"
    return "other"


def normalize_cache_status(raw: str | None) -> str:
    value = (raw or "UNKNOWN").strip().upper() or "UNKNOWN"
    return value if value in _CACHE_ALLOWLIST else "OTHER"


def parse_hostname_allowlist(raw: str | None) -> frozenset[str] | None:
    """Comma-separated hostnames; empty/None means no allowlist (still capped by GraphQL limit)."""
    if raw is None:
        return None
    items = {h.strip().lower() for h in raw.split(",") if h.strip()}
    return frozenset(items) if items else None


def compute_window(
    *,
    now: datetime | None = None,
    lookback: timedelta = timedelta(hours=1),
    overlap: timedelta = timedelta(0),
    lag: timedelta = timedelta(minutes=5),
    watermark: datetime | None = None,
) -> ExportWindow:
    """Half-open [start, end) with Cloudflare analytics lag and optional watermark overlap.

    Default overlap is **zero** so OTLP **counters** do not double-count when the
    watermark advances. Non-zero overlap is for deliberate gap-fill / rebuilds —
    callers must accept duplicate counter adds for overlapped buckets.
    """
    now_utc = now or datetime.now(UTC)
    if now_utc.tzinfo is None:
        now_utc = now_utc.replace(tzinfo=UTC)
    end = now_utc - lag
    if watermark is not None:
        wm = watermark if watermark.tzinfo else watermark.replace(tzinfo=UTC)
        start = wm - overlap
    else:
        start = end - lookback
    if start >= end:
        start = end - lookback
    return ExportWindow(start=start, end=end, overlap=overlap, lag=lag)


def read_watermark(path: Path) -> datetime | None:
    if not path.is_file():
        return None
    text = path.read_text(encoding="utf-8").strip()
    if not text:
        return None
    return datetime.fromisoformat(text.replace("Z", "+00:00"))


def write_watermark(path: Path, end: datetime) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    iso = end.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    path.write_text(iso + "\n", encoding="utf-8")


def build_variables(
    *,
    zone_id: str,
    window: ExportWindow,
    limit: int = 1000,
    eyeball_only: bool = True,
) -> dict[str, Any]:
    """Build GraphQL variables. ``eyeball_only=False`` is unsupported in v1 query (eyeball baked in)."""
    if not eyeball_only:
        raise ValueError(
            "QUERY_HTTP_REQUESTS_ADAPTIVE_V1 always filters requestSource=eyeball; "
            "omit --include-non-eyeball or extend the query version"
        )
    return {
        "zoneTag": zone_id,
        "start": window.start.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "end": window.end.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "limit": int(limit),
    }


def redact_headers_for_log(headers: dict[str, str]) -> dict[str, str]:
    """Never echo Authorization / cookies / tokens."""
    out: dict[str, str] = {}
    for key, value in headers.items():
        lk = key.lower()
        if lk in {"authorization", "cookie", "set-cookie", "x-auth-token"}:
            out[key] = "<redacted>"
        else:
            out[key] = value
    return out


def post_graphql(
    *,
    query: str,
    variables: dict[str, Any],
    token: str,
    url: str = GRAPHQL_URL_DEFAULT,
    timeout_s: float = 60.0,
    max_retries: int = 4,
    sleep_fn: Any = time.sleep,
) -> dict[str, Any]:
    """POST GraphQL with retries on 429/5xx. Token never logged."""
    if not token or not token.strip():
        raise ValueError("CLOUDFLARE_API_TOKEN is required for live GraphQL calls")
    body = json.dumps({"query": query, "variables": variables}).encode("utf-8")
    headers = {
        "Authorization": f"Bearer {token.strip()}",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "DataBoar-CloudflareEdgeExporter/1.0",
    }
    last_err: Exception | None = None
    for attempt in range(max_retries + 1):
        req = urllib.request.Request(url, data=body, headers=headers, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=timeout_s) as resp:  # noqa: S310 — URL from env/default HTTPS
                raw = resp.read().decode("utf-8")
                payload = json.loads(raw)
        except urllib.error.HTTPError as exc:
            last_err = exc
            retryable = exc.code == 429 or 500 <= exc.code < 600
            retry_after = exc.headers.get("Retry-After") if exc.headers else None
            logger.warning(
                "Cloudflare GraphQL HTTP %s (attempt %s/%s) headers=%s",
                exc.code,
                attempt + 1,
                max_retries + 1,
                redact_headers_for_log(
                    dict(exc.headers.items()) if exc.headers else {}
                ),
            )
            if not retryable or attempt >= max_retries:
                raise
            delay = (
                float(retry_after)
                if retry_after and str(retry_after).isdigit()
                else 2.0**attempt
            )
            sleep_fn(delay)
            continue
        except (TimeoutError, urllib.error.URLError, json.JSONDecodeError) as exc:
            last_err = exc
            logger.warning(
                "Cloudflare GraphQL transport error (attempt %s): %s",
                attempt + 1,
                type(exc).__name__,
            )
            if attempt >= max_retries:
                raise
            sleep_fn(2.0**attempt)
            continue

        if payload.get("errors"):
            # GraphQL may return 200 with errors — surface without dumping secrets.
            raise RuntimeError(f"Cloudflare GraphQL errors: {payload['errors']!r}")
        return payload
    assert last_err is not None
    raise last_err


def load_fixture(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def extract_series(payload: dict[str, Any]) -> list[dict[str, Any]]:
    zones = (((payload.get("data") or {}).get("viewer") or {}).get("zones")) or []
    series: list[dict[str, Any]] = []
    for zone in zones:
        series.extend(zone.get("series") or [])
    return series


def normalize_series(
    series: list[dict[str, Any]],
    *,
    window: ExportWindow,
    hostname_allowlist: frozenset[str] | None = None,
    max_hostnames: int = 32,
) -> NormalizedBatch:
    """Convert GraphQL groups into bounded-label metric points (no PII fields)."""
    batch = NormalizedBatch(query_version=QUERY_VERSION, window=window)
    seen_hosts: set[str] = set()
    for row in series:
        batch.raw_group_count += 1
        dims = row.get("dimensions") or {}
        host = (
            dims.get("clientRequestHTTPHost") or "unknown"
        ).strip().lower() or "unknown"
        if hostname_allowlist is not None and host not in hostname_allowlist:
            batch.dropped_hostname_count += 1
            continue
        if host not in seen_hosts and len(seen_hosts) >= max_hostnames:
            batch.dropped_hostname_count += 1
            continue
        seen_hosts.add(host)

        status_raw = dims.get("edgeResponseStatus")
        try:
            status_i = int(status_raw) if status_raw is not None else None
        except (TypeError, ValueError):
            status_i = None
        cache = normalize_cache_status(dims.get("cacheStatus"))
        ts_raw = dims.get("datetimeHour")
        ts: datetime | None = None
        hour_label = "unknown"
        if isinstance(ts_raw, str) and ts_raw:
            hour_label = ts_raw.strip() or "unknown"
            try:
                ts = datetime.fromisoformat(ts_raw.replace("Z", "+00:00"))
            except ValueError:
                ts = None
        attrs = {
            "service.name": SERVICE_NAME,
            "cloudflare.zone_scope": "configured",
            "http.host": host,
            "http.status_class": status_class(status_i),
            "cloudflare.cache_status": cache,
            # Preserve Analytics hour bucket as a label (OTLP Counter.add is wall-clock).
            "cloudflare.datetime_hour": hour_label,
            "telemetry.source": "cloudflare-graphql",
            "telemetry.signal": "edge-aggregate",
        }
        # Strip any accidental high-cardinality keys if callers pass extras later.
        attrs = {
            k: v
            for k, v in attrs.items()
            if k not in {"http.url", "url", "client.ip", "referer", "cookie"}
        }

        count = float(row.get("count") or 0)
        sums = row.get("sum") or {}
        visits = float(sums.get("visits") or 0)
        bytes_ = float(sums.get("edgeResponseBytes") or 0)

        if count:
            batch.points.append(
                MetricPoint("cloudflare.edge.http.requests", count, attrs, ts)
            )
        if visits:
            batch.points.append(
                MetricPoint("cloudflare.edge.http.visits", visits, attrs, ts)
            )
        if bytes_:
            batch.points.append(
                MetricPoint("cloudflare.edge.http.response_bytes", bytes_, attrs, ts)
            )
    return batch


def resolve_credentials_from_env(
    environ: dict[str, str] | None = None,
) -> tuple[str, str]:
    """Return (token, zone_id). Refuse all-zones production path."""
    env = environ if environ is not None else dict(os.environ)
    token = (env.get(_ENV_TOKEN) or "").strip()
    zone = (env.get(_ENV_ZONE) or "").strip()
    allow_all = (env.get(_ENV_ALLOW_ALL_ZONES) or "").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }
    if not zone:
        if allow_all:
            raise ValueError(
                "CLOUDFLARE_ALLOW_ALL_ZONES_FOR_LOCAL_TEST is set but zone-less "
                "GraphQL export is not implemented — use CLOUDFLARE_ZONE_ID or --fixture"
            )
        raise ValueError(
            "CLOUDFLARE_ZONE_ID is required (zone-scoped Analytics Read token)"
        )
    if not token:
        raise ValueError("CLOUDFLARE_API_TOKEN is required for live export")
    return token, zone


def graphql_url_from_env(environ: dict[str, str] | None = None) -> str:
    """Return GraphQL URL; only the official Cloudflare HTTPS endpoint is allowed."""
    env = environ if environ is not None else dict(os.environ)
    raw = (env.get(_ENV_URL) or "").strip() or GRAPHQL_URL_DEFAULT
    return validate_cloudflare_graphql_url(raw)


def validate_cloudflare_graphql_url(url: str) -> str:
    """Refuse non-HTTPS or non-Cloudflare hosts so the bearer token is not exfiltrated."""
    from urllib.parse import urlparse

    parsed = urlparse(url.strip())
    scheme = (parsed.scheme or "").lower()
    host = (parsed.hostname or "").lower()
    path = (parsed.path or "").rstrip("/") or "/"
    if scheme != "https":
        raise ValueError("CLOUDFLARE_GRAPHQL_URL must use https")
    if host != "api.cloudflare.com":
        raise ValueError(
            "CLOUDFLARE_GRAPHQL_URL host must be api.cloudflare.com "
            "(refusing alternate hosts to protect the API token)"
        )
    if path != "/client/v4/graphql":
        raise ValueError("CLOUDFLARE_GRAPHQL_URL path must be /client/v4/graphql")
    if parsed.username or parsed.password:
        raise ValueError("CLOUDFLARE_GRAPHQL_URL must not embed credentials")
    return "https://api.cloudflare.com/client/v4/graphql"


def points_as_jsonable(batch: NormalizedBatch) -> dict[str, Any]:
    return {
        "query_version": batch.query_version,
        "service_name": SERVICE_NAME,
        "window": {
            "start": batch.window.start.astimezone(UTC).isoformat(),
            "end": batch.window.end.astimezone(UTC).isoformat(),
        },
        "raw_group_count": batch.raw_group_count,
        "dropped_hostname_count": batch.dropped_hostname_count,
        "points": [
            {
                "metric": p.metric,
                "value": p.value,
                "attributes": p.attributes,
                "timestamp": p.timestamp.astimezone(UTC).isoformat()
                if p.timestamp
                else None,
            }
            for p in batch.points
        ],
        "note": (
            "Aggregate Cloudflare edge metrics only — not distributed traces; "
            "orthogonal to DataBoar Site / Faro browser RUM."
        ),
    }


def emit_otlp_metrics(batch: NormalizedBatch, *, endpoint: str | None = None) -> bool:
    """Best-effort OTLP metrics export. Returns False if OTel packages missing."""
    try:
        from opentelemetry import metrics
        from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import (
            OTLPMetricExporter,
        )
        from opentelemetry.sdk.metrics import MeterProvider
        from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
        from opentelemetry.sdk.resources import Resource
    except ImportError:
        logger.error("OpenTelemetry packages missing — install optional [otel] extra")
        return False

    from core.otel_setup import (
        otlp_insecure_for_endpoint,
        sanitize_otlp_endpoint_for_log,
    )

    ep = (
        endpoint
        or os.environ.get("OTEL_EXPORTER_OTLP_METRICS_ENDPOINT")
        or os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT")
        or "http://127.0.0.1:4317"
    ).strip()
    logger.info(
        "Exporting Cloudflare edge metrics to %s", sanitize_otlp_endpoint_for_log(ep)
    )

    resource = Resource.create(
        {
            "service.name": SERVICE_NAME,
            "telemetry.sdk.language": "python",
            "cloudflare.export.query_version": QUERY_VERSION,
        }
    )
    exporter = OTLPMetricExporter(endpoint=ep, insecure=otlp_insecure_for_endpoint(ep))
    reader = PeriodicExportingMetricReader(exporter, export_interval_millis=60_000)
    provider = MeterProvider(resource=resource, metric_readers=[reader])
    metrics.set_meter_provider(provider)
    meter = metrics.get_meter("data-boar.cloudflare-edge", version=QUERY_VERSION)

    counters: dict[str, Any] = {}
    for name in (
        "cloudflare.edge.http.requests",
        "cloudflare.edge.http.visits",
        "cloudflare.edge.http.response_bytes",
    ):
        counters[name] = meter.create_counter(
            name,
            description=f"Cloudflare GraphQL Adaptive Groups aggregate ({name})",
        )

    for point in batch.points:
        counter = counters.get(point.metric)
        if counter is None:
            continue
        # Drop service.name from attributes — already on Resource.
        attrs = {k: v for k, v in point.attributes.items() if k != "service.name"}
        counter.add(point.value, attributes=attrs)

    flushed = provider.force_flush(timeout_millis=15_000)
    provider.shutdown(timeout_millis=5_000)
    if not flushed:
        logger.error(
            "OTLP force_flush reported failure — not treating export as success"
        )
        return False
    return True
