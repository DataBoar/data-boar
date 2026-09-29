# ADR 9999 — Synthetic T7 positive fixture (not a real ADR)

- **Date (UTC):** 2026-01-01
- **Authors:** governance test harness
- **Deciders:** governance test harness

## Status

Proposed

## Context

RegexSet probe on a pinned workload failed the performance gate (~**4.7×** slower than a cached
`Regex` loop; wall time ~**99.7%** in matching on the declared profile). Do not paste raw JSON here.

Pinned artifacts live under `tests/benchmarks/rust_prefilter_hotspot.json` and
`tests/benchmarks/filesystem_phase_breakdown.json`. Reproduction steps are tracked in GitHub
issue #1078 (public tracker id only — no private lab hostnames).

## Decision

1. Ship the cached-`Regex` path; link evidence, never embed runner output in this ADR.
