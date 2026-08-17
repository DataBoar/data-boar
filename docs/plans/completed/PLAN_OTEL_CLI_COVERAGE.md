# Data Boar — OpenTelemetry CLI / oneshot coverage

<!-- plans-hub-summary: Extend opt-in OTel beyond --web: early maybe_setup_otel(app=None), manual spans for oneshot scan + exports; --version/--check-extras/license-only out of scope. Complements #1529 logs and Maestro preflight #1540. -->

**Status:** Done (shipped with [#1535](https://github.com/DataBoar/data-boar/issues/1535))
**Date:** 2026-08-12
**Authors:** Fabio Leitao
**Priority:** H1 / P2
**Issue:** [#1535](https://github.com/DataBoar/data-boar/issues/1535)

**Related:** [PLAN_DATABOAR_OTEL_INSTRUMENTATION.md](completed/PLAN_DATABOAR_OTEL_INSTRUMENTATION.md) (#1500 / #1529) · Maestro preflight plan [#1540](https://github.com/DataBoar/data-boar/issues/1540) (tracked plan lands in a follow-up docs PR)

## Problem

`maybe_setup_otel()` was only invoked from `api/routes.py` when `args.web` is true. Oneshot CLI, exports, and the `--demo` scan (which runs **before** `import api.routes`) emitted no traces/metrics/logs even with `DATA_BOAR_OTEL_ENABLED=1`.

## Decision

| Choice | Detail |
| ------ | ------ |
| API | **Reuse** `maybe_setup_otel(app=None)` — no separate `maybe_setup_otel_cli()` |
| When | Call early from `main.py` after config/runtime-trust for instrumentable modes |
| FastAPI | Still instrumented only when `app` is passed (second call is idempotent) |
| Spans | Manual tracer `data-boar`: `scan` lifecycle + one span per export/regenerate |
| Flush | `atexit` force-flush so short-lived CLI processes export Batch processors |

## Mode coverage

| Mode | Instrumented? | Notes |
| ---- | ------------- | ----- |
| `--web` | Yes | Early setup + FastAPI on `api.routes` import |
| `--demo` (scan + then web) | Yes | Early setup before demo `start_audit` |
| Oneshot CLI scan | Yes | Early setup + `scan` span |
| `--export-dsar` | Yes | Span `export.dsar` |
| `--export-remediation-manifest` | Yes | Span `export.remediation_manifest` |
| `--regenerate-report` | Yes | Span `export.regenerate_report` |
| `--export-audit-trail` | Yes | Span `export.audit_trail` |
| `--version` / `--check-extras` | **Out of scope** | Explicit — no OTel |
| License / runtime-trust alone | **Out of scope** | No dedicated telemetry hook this slice |
| `--reset-data` | Optional setup only | No dedicated span required |

## Relation to sibling issues

- **#1529 (done):** `LoggerProvider` + stdlib bridge — logs reach Loki when setup runs; CLI coverage makes that path actually execute outside `--web`.
- **#1540:** Maestro must **verify** env + invocation mode + endpoint — not assume. After this plan ships, oneshot is “wired” when `DATA_BOAR_OTEL_ENABLED` is set.

## Acceptance (#1535)

- [x] This plan + hub / `PLANS_TODO` entry
- [x] Early `maybe_setup_otel(app=None)` on CLI instrumentable paths
- [x] Manual spans for scan + exports
- [x] Tests for gate-off no-op + idempotent setup with `app=None`
- [x] Operator note (USAGE) that oneshot shares the same opt-in env
