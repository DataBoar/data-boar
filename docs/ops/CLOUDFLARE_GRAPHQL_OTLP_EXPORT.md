# Cloudflare GraphQL Analytics → OTLP / Grafana (#1599)

**Português (Brasil):** [CLOUDFLARE_GRAPHQL_OTLP_EXPORT.pt_BR.md](CLOUDFLARE_GRAPHQL_OTLP_EXPORT.pt_BR.md)

**Purpose:** Schedule a **server-side** exporter that queries Cloudflare **GraphQL Analytics** (`httpRequestsAdaptiveGroups`) and emits **normalized aggregate metrics** to an operator-owned OTLP collector / Grafana destination.

**Not in scope:** DNS/Workers/Tunnel changes, Google Analytics, browser-side Cloudflare tokens, or claiming these aggregates are **distributed traces**.

**Orthogonal signals:**

| Signal | `service.name` / source | Surface |
| ------ | ----------------------- | ------- |
| Cloudflare **edge** aggregates (this doc) | `cloudflare-edge` | GraphQL → OTLP metrics |
| DataBoar Site **Faro** RUM | browser / Faro | Frontend RUM (separate dashboard) |
| Product Data Boar OTel | `data-boar` (app) | `DATA_BOAR_OTEL_ENABLED` |

Dashboard JSON (edge only): [`dashboards/cloudflare-edge-metrics.json`](dashboards/cloudflare-edge-metrics.json). Do **not** mix with Faro RUM panels.

## Security and privacy

- **Production token:** zone-scoped Cloudflare API token with **Analytics Read** only. Set `CLOUDFLARE_API_TOKEN` + `CLOUDFLARE_ZONE_ID` via operator env / secret injection — **never** commit or print them.
- **Do not** depend on an **all-zones** token for scheduled production export. `CLOUDFLARE_ALLOW_ALL_ZONES_FOR_LOCAL_TEST` exists only to document refusal (zone-less export is **not** implemented); use `--fixture` for local/CI.
- Exporter never requests IP, raw URL/path/query, referrer, User-Agent, or cookies as GraphQL dimensions.
- Labels are bounded: hostname allowlist / max hosts, `http.status_class` (`2xx`…), allowlisted `cloudflare.cache_status`.
- Grafana / OTLP credentials stay on the **collector host** — never in browser HTML/JS.

## Environment

| Variable | Role |
| -------- | ---- |
| `CLOUDFLARE_API_TOKEN` | Zone-scoped Analytics Read (live only) |
| `CLOUDFLARE_ZONE_ID` | Zone tag for GraphQL `zones(filter: { zoneTag })` |
| `CLOUDFLARE_GRAPHQL_URL` | Default `https://api.cloudflare.com/client/v4/graphql` |
| `CLOUDFLARE_HOSTNAME_ALLOWLIST` | Optional comma list (e.g. `databoar.com.br`) |
| `CLOUDFLARE_EXPORT_LOOKBACK_MINUTES` | Default `60` when no watermark |
| `CLOUDFLARE_EXPORT_OVERLAP_MINUTES` | Default `0` (avoid counter double-count). Non-zero re-reads prior buckets — gap-fill only. |
| `CLOUDFLARE_EXPORT_LAG_MINUTES` | Default `5` (analytics freshness lag) |
| `CLOUDFLARE_EXPORT_LIMIT` | GraphQL `limit` (default `1000`, capped at `5000`) |
| `CLOUDFLARE_EXPORT_WATERMARK_PATH` | Default `~/.cache/data-boar/cloudflare_edge_watermark.txt` |
| `OTEL_EXPORTER_OTLP_ENDPOINT` / `OTEL_EXPORTER_OTLP_METRICS_ENDPOINT` | Collector (default loopback `:4317`) |

Optional product OTel extra: `uv sync --extra otel` (same packages as app emit).

## Query contract

- **Dataset:** `httpRequestsAdaptiveGroups` (current Cloudflare GraphQL Analytics node; replaces deprecated colo group nodes).
- **Filter:** `datetime_geq` / `datetime_lt` half-open window + `requestSource: "eyeball"` (end-user traffic; excludes many Cloudflare-internal actions).
- **Dimensions:** `datetimeHour`, `clientRequestHTTPHost`, `cacheStatus`, `edgeResponseStatus` — then mapped to status **class** locally.
- **Measures:** `count`, `sum.visits`, `sum.edgeResponseBytes`.
- **Visits caveat:** Cloudflare defines a visit as a page view whose referer host differs from the hostname (or direct). One visit can span multiple page views — **not** unique visitors.

Query text is versioned in code as `QUERY_VERSION` / `httpRequestsAdaptiveGroups.v1`.

## Run

```bash
# CI / offline (no secrets):
uv run python scripts/cloudflare_graphql_otel_export.py \
  --fixture tests/fixtures/cloudflare/http_requests_adaptive_groups.json \
  --dry-run --no-watermark

# Live dry-run (token in env only):
export CLOUDFLARE_API_TOKEN=...   # do not paste into shell history docs
export CLOUDFLARE_ZONE_ID=...
uv run python scripts/cloudflare_graphql_otel_export.py --dry-run \
  --hostname-allowlist databoar.com.br

# Emit OTLP:
uv sync --extra otel
uv run python scripts/cloudflare_graphql_otel_export.py \
  --hostname-allowlist databoar.com.br
```

Windows: `.\scripts\cloudflare-graphql-otel-export.ps1` (thin wrapper).

### Scheduling

Cron / systemd timer / Task Scheduler: invoke the script every 5–15 minutes. Watermark advances the window start; **default overlap is 0** so OTLP counters are not double-counted. Non-zero overlap is for deliberate rebuilds only. Lag avoids reading incomplete Analytics buckets. Respect Cloudflare **rate limits** (exporter retries on HTTP 429 / 5xx with `Retry-After` when present).

`CLOUDFLARE_GRAPHQL_URL` is optional and **must** remain `https://api.cloudflare.com/client/v4/graphql` (HTTPS + that host/path only) so the bearer token is not sent elsewhere.

### Retention / sampling

- Prefer **hourly** dimensions (exporter default) over per-request logs.
- Keep Grafana retention aligned with your Cloud/stack plan; downsample long-range panels.
- Drop unexpected hostnames via allowlist to control cardinality.

## Disable / rollback

1. Stop the scheduler / timer.
2. Unset `CLOUDFLARE_API_TOKEN` (or rotate/revoke the token in Cloudflare).
3. Remove or ignore the Grafana dashboard; metrics stop when the exporter stops — **no** product code path depends on this job.
4. Delete watermark file if you need a clean re-backfill window (expect overlap double-counts if you re-export without adjusting lookback).

## Metrics emitted

| Metric | Meaning |
| ------ | ------- |
| `cloudflare.edge.http.requests` | Request count (`count`) |
| `cloudflare.edge.http.visits` | Visits (`sum.visits`) — see caveat |
| `cloudflare.edge.http.response_bytes` | Edge response bytes |

Resource: `service.name=cloudflare-edge`. Attributes include `http.host`, `http.status_class`, `cloudflare.cache_status`, `telemetry.source=cloudflare-graphql`.

Prometheus/Grafana name mapping may underscore dots (`cloudflare_edge_http_requests_total`) depending on the collector pipeline — adjust dashboard queries after the first successful export.

## Local collector without production credentials

Use `--fixture` + `--dry-run`, or point OTLP at a local collector with a **test** Grafana/OTLP sink. Fixture tests live in `tests/test_cloudflare_edge_metrics.py` and require **no** live secret.

## References

- Cloudflare GraphQL Analytics: [developers.cloudflare.com/analytics/graphql-api](https://developers.cloudflare.com/analytics/graphql-api/)
- Adaptive groups migration: [migration guide](https://developers.cloudflare.com/analytics/graphql-api/migration-guides/graphql-api-analytics/)
- Cross-surface gates (RUM ≠ edge): [PLAN_CROSS_SURFACE_OBSERVABILITY.md](../plans/PLAN_CROSS_SURFACE_OBSERVABILITY.md)
- Lab receive stack: [PLAN_LAB_OP_OBSERVABILITY_STACK.md](../plans/PLAN_LAB_OP_OBSERVABILITY_STACK.md)
- Grafana Cloud operator notes: [GRAFANA_CLOUD_REACTIVATION.md](GRAFANA_CLOUD_REACTIVATION.md)
