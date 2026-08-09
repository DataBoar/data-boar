# Data Boar — OpenTelemetry instrumentation (RED + traces)

**Status:** Done (opt-in shipped on `main` via #1503)
**Date:** 2026-08-09 (closed)
**Authors:** Fabio Leitao
**Priority:** H2 / P2
**Issue:** [#1500](https://github.com/DataBoar/data-boar/issues/1500)

**Related (infra plan, receiving end):** [PLAN_LAB_OP_OBSERVABILITY_STACK.md](../PLAN_LAB_OP_OBSERVABILITY_STACK.md) — Phase **F** (Tempo / OTel). Distinct from GenAI/MCP agent observability ([#1457](https://github.com/DataBoar/data-boar/issues/1457) / [#1455](https://github.com/DataBoar/data-boar/issues/1455)).

## Purpose

Emit classical **RED** signals (request rate / errors / duration) and **distributed traces** from Data Boar’s FastAPI + SQLAlchemy runtime via **OpenTelemetry**, exporting **OTLP** to an operator-chosen collector. The lab receiving stack (collector + Grafana datasources) is outside this repo; this plan covers the **emitting** side only.

## Non-goals

- GenAI / MCP semantic conventions, ADR Sensor, MemPalace/CHIRP (sibling issues).
- Hard dependency on OTel packages for `python main.py` / default CI.
- Hardcoding lab hostnames or LAN IPs in product defaults.

## Package choices (optional extra `[otel]`)

| Package | Role |
| ------- | ---- |
| `opentelemetry-api` / `opentelemetry-sdk` | Tracer + meter providers |
| `opentelemetry-exporter-otlp` | OTLP gRPC/HTTP exporters |
| `opentelemetry-instrumentation-fastapi` | HTTP RED + spans |
| `opentelemetry-instrumentation-sqlalchemy` | DB spans when engines exist |

Install: `uv sync --extra otel` (or `pip install '.[otel]'`).

## Config surface (env)

| Variable | Default | Meaning |
| -------- | ------- | ------- |
| `DATA_BOAR_OTEL_ENABLED` | unset / off | Must be `1` / `true` / `yes` / `on` to initialize |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | `http://127.0.0.1:4317` | Collector endpoint when enabled |
| `OTEL_SERVICE_NAME` | `data-boar` | Resource `service.name` |

**TLS:** OTLP gRPC exporters use **TLS by default**. Plaintext (`insecure=True`) is allowed **only** when the endpoint host is loopback (`127.0.0.1`, `localhost`, `::1`). Remote collectors must present a valid TLS endpoint.

When disabled or packages missing: **no-op** (log warning if enabled-but-missing; never block startup).

## Code hook

- Module: `core/otel_setup.py` (`maybe_setup_otel(app)`).
- Wired after FastAPI app creation in `api/routes.py`.
- Tests: `tests/test_otel_setup_1500.py` (default-off + endpoint override).

## Roll-out

1. **Dev / lab opt-in** — enable env against a local or lab collector; confirm spans/metrics in Tempo/Prometheus.
2. **Docs** — this plan + short USAGE/ops note when operators ask; no change to default install path.
3. **Later** — optional Compose/k8s snippets pointing at customer collectors (not lab-specific).

## Acceptance (issue #1500)

- [x] This plan file
- [x] Lab observability plan status refresh + hub / PLANS_TODO entry
- [x] Opt-in wiring + `[otel]` extra
- [x] E2E evidence — `docs/ops/evidence/otel_1500_smoke_2026-08-09.json` (setup_ok + OTLP HTTP `200` `partialSuccess` on local collector `:4318`)
