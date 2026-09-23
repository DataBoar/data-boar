# Plan: RC sentinel upper-bound schema (`max_count` / forbidden substrings)

<!-- plans-hub-summary: RC sentinel upper-bound — max_count, forbidden_pattern_substrings, xfail hook for documented detector gaps (#1985) -->

**Status:** Active (implementation slice on `feat/86-rc-v3-sentinel-schema`)
**Date:** 2026-09-22
**Authors:** Fabio Leitao
**Priority:** H1
**GitHub:** [data-boar#1985](https://github.com/DataBoar/data-boar/issues/1985), [maestro#86](https://github.com/DataBoar/maestro/issues/86)
**Related:** [PLAN_TWO_WEEK_EXECUTION_NO_REGRESSION.md](PLAN_TWO_WEEK_EXECUTION_NO_REGRESSION.md), data-boar#1983 (RC v2 sentinel baseline), data-boar#1984 (Amex/Diners gap)

**Synced with:** [PLANS_TODO.md](PLANS_TODO.md)

---

## Context

`scripts/benchmark_rc_sentinel_check.py` originally expressed **lower bounds** only (`min_count`, `min_application_findings`). Lab RC gates also need **upper bounds** (false-positive ceilings, PII-free REST controls) and optional **`xfail`** for documented detector gaps without weakening CI on unrelated rules.

---

## Decision

1. Extend sentinel YAML (`version: 2`) with per-rule **`max_count`**, optional **`forbidden_pattern_substrings`** + **`max_forbidden_matches`**, and **`xfail`** (failed bound → `XFAIL_OK` on stderr, not exit 1).
2. Ship with **`benchmark-rc-v3.yaml`** / **`.sentinel.yaml`** (maestro#86 SQL/NFS/SMB targets + postgres `#1332` `max_count: 0` on `CREDIT_CARD` when lab SQL is up).
3. **#1984** Amex/Diners: pytest `xfail` on golden PAN cases on the v3/sentinel PR; release-note honesty + milestone **v1.8.1** ship in a **separate** docs PR ([#1984](https://github.com/DataBoar/data-boar/issues/1984)).

---

## Phase table

| Phase | Item | Status |
| ----- | ---- | ------ |
| 1 | `max_count` / forbidden substrings in checker | ✅ |
| 2 | v3 profile + sentinel thresholds | ✅ |
| 3 | Unit tests + `test_maestro_scripts` v3 guard | ✅ |
| 4 | Maestro consumer default → v3 (separate maestro PR) | ⬜ |
