# Plan: Locust load test integration with Maestro

**Status:** Pending
**Date:** 2026-05-12
**Authors:** Fabio Leitao
**Priority:** H2
**Depends on:** PLAN_MAESTRO_BENCHMARK_METRICS_AND_FIX.md, PLAN_SYNTHETIC_DATA_AND_CONFIDENCE_VALIDATION.md

<!-- plans-hub-summary: Locust HTTP load testing wired into Maestro's web persona pipeline; tests API scan, health, dashboard endpoints against synthetic lab targets. -->
<!-- plans-hub-related: PLAN_MAESTRO_BENCHMARK_METRICS_AND_FIX.md, PLAN_SELENIUM_QA_TEST_SUITE.md -->

## Context

`Handle-web.ps1` line 11–12 already documents its own gap:

> *"sendo uma etapa crucial antes que **scripts de teste de carga ou API (que estão na esteira)** tentem se comunicar com o serviço"*

The Maestro was designed anticipating load test scripts downstream of the health check. The benchmark A/B infrastructure (`--bench-track`, `--bench-run-id`, `maestro-benchmark-ab.ps1`) already provides the scaffolding. Locust is the natural next step — it is pure Python, fits the existing stack, and can run against the synthetic lab DB targets that `--lab-stack-up` already spins up.

## Architecture fit

```
Maestro.ps1 -Deep
  → Handle-web.ps1  (health OK → return)
  → Handle-loadtest.ps1 (NEW persona)
      → locust --headless -f tests/locustfile.py
               --host http://$nodeIp:$webPort
               --users 10 --spawn-rate 2
               --run-time 60s
               --csv /tmp/databoar_bench/$track/locust_$runId
      → Collect-Artifacts.ps1 picks up CSV from /tmp/databoar_bench/$track/
```

Locust personas fit the existing `--bench-track stable/beta` model exactly:
- stable track → port 18088 → locust hits stable API
- beta track → port 28088 → locust hits rc API
- A/B delta = `maestro-benchmark-ab.ps1 -BenchCompare` → compare stable CSV vs beta CSV

## Slices

| Slice | Focus | Delivers |
| ----- | ----- | -------- |
| **1 — Minimal locustfile** | API endpoints only | `tests/locustfile.py`: `/health` (weight 3), `/api/scan` POST with minimal filesystem config (weight 1), `/api/status` GET (weight 2). Headless only. No Locust web UI in CI. |
| **2 — Handle-loadtest persona** | Maestro integration | `scripts/maestro/handlers/Handle-loadtest.ps1`: runs locust via SSH on the lab host after web health passes. Emits CSV to `/tmp/databoar_bench/$track/locust_$runId_stats.csv`. `Collect-Artifacts.ps1` extension to pull CSVs. |
| **3 — A/B delta reporting** | Comparative metrics | Post-test: compare stable vs beta Locust CSVs for RPS, p50/p95 latency, failure rate. Output: `docs/private/homelab/reports/LOCUST_AB_$runId.md` via `maestro-benchmark-ab.ps1`. |
| **4 — Scan endpoint load** | Real scan stress | Locust task that POSTs to `/api/scan` with `benchmark-rc.yaml` targets (synthetic filesystem + lab DBs when `--lab-stack-up`). Measures time-to-report, report size, findings count consistency under concurrent load. |
| **5 — Rust core comparison** | boar_fast_filter timing | Locust with scan tasks where both tracks differ only in `rust_fast_filter: true/false`; measures wall-clock delta on identical synthetic corpus. This is the missing measurement from `hybrid-173`. |

## Integration with `lab-completao-host-smoke.sh`

Locust runs **on the lab host** (not the Windows dev PC), driven via SSH injection same as baremetal/docker handlers. The smoke script already has `_lc_capture_metrics_snapshot` (vmstat, iostat, free, ps) — Locust results from `/tmp/databoar_bench/$track/` are collected alongside these by `Collect-Artifacts.ps1`.

## Acceptance criteria (Slice 1)

- [ ] `tests/locustfile.py` passes `uv run locust --list` on the dev PC.
- [ ] `Handle-loadtest.ps1` emits `[SUCCESS]` or `[ERROR]` (no silent skip).
- [ ] Locust CSV collected under `docs/private/homelab/reports/` after a `-Collect` pass.
- [ ] `PLAN_MAESTRO_BENCHMARK_METRICS_AND_FIX.md` SSH timeout fix applied before this slice runs (prerequisite: no infinite-hang SSH).

## Prerequisite

**Do not implement Slice 2+ until `PLAN_MAESTRO_BENCHMARK_METRICS_AND_FIX.md` Bug 1 (SSH ConnectTimeout) is fixed.** A hanging SSH in `Handle-loadtest.ps1` would reproduce the 9-hour wait-state exactly.

## Notes

- Locust added to `[project.optional-dependencies]` as `loadtest = ["locust"]` — not a default dep.
- `tests/locustfile.py` excluded from standard pytest run (`conftest.py` or `pyproject.toml` ignore).
- No Locust web UI in automated runs; `--headless --csv` only.
