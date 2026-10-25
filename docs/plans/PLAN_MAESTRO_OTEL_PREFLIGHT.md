# Maestro — OpenTelemetry preflight (trust before deep scan)

<!-- plans-hub-summary: Checkable Maestro preflight for OTel wire-up: env gate, invocation mode wired|not-wired, OTLP endpoint present/parseable; redacted lessons suggest only. Product CLI coverage #1535; Maestro code lives in private repo. -->

**Status:** Active (plan accepted — Maestro implementation TBD in private Maestro repo)
**Date:** 2026-08-12
**Authors:** Fabio Leitao
**Priority:** H2 / P2
**Issue:** [#1540](https://github.com/DataBoar/data-boar/issues/1540)

**Related:** Product emit [PLAN_DATABOAR_OTEL_INSTRUMENTATION.md](completed/PLAN_DATABOAR_OTEL_INSTRUMENTATION.md) · CLI / oneshot coverage [PLAN_OTEL_CLI_COVERAGE.md](completed/PLAN_OTEL_CLI_COVERAGE.md) ([#1535](https://github.com/DataBoar/data-boar/issues/1535) / **#1547**) · Lab receive [PLAN_LAB_OP_OBSERVABILITY_STACK.md](PLAN_LAB_OP_OBSERVABILITY_STACK.md)

## Purpose

Before a Maestro deep / completão-style run, answer **“is this invocation instrumented?”** with a **cheap preflight** — no full scan required. Operators and automation must **verify**, not assume, that OTel will emit for the chosen `main.py` mode.

## Checks (v1)

| # | Check | Pass criteria | Fail / warn |
| - | ----- | ------------- | ----------- |
| 1 | Env gate | `DATA_BOAR_OTEL_ENABLED` is truthy (`1` / `true` / `yes` / `on`) on the **remote host** process env | Report `OTEL: disabled` |
| 2 | Invocation mode | Map Maestro argv / persona to product modes; after #1535, oneshot / exports / `--web` / `--demo` scan are **wired** when gate is on | `OTEL: wired` vs `OTEL: not-wired-for-this-invocation-mode` |
| 3 | Endpoint | `OTEL_EXPORTER_OTLP_ENDPOINT` present and parseable (scheme + host). **No** lab hostname hardcoded in tracked code | Warn if missing (falls back to product default loopback — often wrong on remote hosts) |
| 4 | Lessons | Suggest append to public lab lessons hub (**redacted**) or private session note | **Suggestion only** in v1 — no auto-PR / no auto-append of lab PII |

## Mode mapping (product truth after #1535)

| Invocation | Wired when env enabled? |
| ---------- | ----------------------- |
| Oneshot CLI scan | Yes |
| `--web` | Yes (FastAPI + early setup) |
| `--demo` (scan + web) | Yes |
| `--export-dsar` / remediation / regenerate / audit-trail | Yes |
| `--version` / `--check-extras` | No (explicit product out-of-scope) |

## Implementation locus

| Layer | Where |
| ----- | ----- |
| This plan + hub | **data-boar** (this PR / issue AC) |
| Preflight script / Maestro handler | **[DataBoar/maestro](https://github.com/DataBoar/maestro)** ([#32](https://github.com/DataBoar/maestro/issues/32)) — follow-up, not this PR |
| Product emit | Already in `core/otel_setup.py` + `main.py` (#1500 / #1529 / #1535) |

## Non-goals

- Changing product OTel gate or exporters
- Deploying Graylog / Phase D
- Auto-committing Lessons Learned with hostnames or RFC1918 addresses
- Treating preflight as a substitute for Tempo/Loki smoke evidence

## Acceptance (#1540)

- [x] This plan file with checkable table
- [x] Entry in `PLANS_TODO.md` + `plans_hub_sync.py --write`
- [ ] Maestro handler / script implementation (private repo follow-up)
- [ ] Optional: link follow-up issue once Maestro work is filed

**Close policy:** Landing this plan satisfies the tracked-repo AC for #1540; Maestro code is a separate follow-up.
