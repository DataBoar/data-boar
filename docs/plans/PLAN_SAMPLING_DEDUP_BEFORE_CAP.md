# Plan: Sampling dedup before cap (distinct values)

**Status:** Active
**Date:** 2026-07-27
**Authors:** Fabio Leitao
**Priority:** H1 / U2
**GitHub:** [#1337](https://github.com/DataBoar/data-boar/issues/1337) (depends on [#1338](https://github.com/DataBoar/data-boar/issues/1338) safe-axis gate — merged)

<!-- plans-hub-summary: Deduplicate column samples client-side before spending sample_limit — fetch N×k rows with unchanged LIMIT/TOP SQL, cap distinct values; improves recall on low-cardinality columns without SELECT DISTINCT sort cost (#1337). -->
<!-- plans-hub-related: PLAN_BENCHMARK_SAFE_AXIS.md, PLAN_SYNTHETIC_DATA_AND_CONFIDENCE_VALIDATION.md, connectors/sql_sampling.py -->

**Synced with:** [PLANS_TODO.md](PLANS_TODO.md)

## Motivation

Per-column `sample_limit` caps **rows fetched**, not **distinct values**. A `status` column with 500k rows and three distinct values can yield five identical samples (`ATIVO` × 5), exhausting the detection window before a rare value (or embedded PII in a minority status) is seen.

`SELECT DISTINCT` in SQL fixes recall but can force sort/hash plans on large heaps — **slower** than a simple `LIMIT` read. This plan chooses a strategy with **measured** cost, not opinion.

## Strategy evaluation (measured 2026-07-27, Linux primary dev workstation)

Synthetic SQLite table: skewed column (`ATIVO` dominant, one `RARO <CPF>`, nine `INATIVO`), `sample_limit=5`, multiplier **10** (`fetch_budget=50`).

| Strategy | Mechanism | 5k rows (ms) | 50k rows (ms) | 500k rows (ms) | Rare CPF in sample? |
| -------- | --------- | ------------ | ------------- | -------------- | ------------------- |
| **(a) SQL DISTINCT** | `SELECT DISTINCT … LIMIT 5` | **0.422** | **4.112** | **29.686** | Yes |
| **(b) Client dedup** | `SELECT … LIMIT 50` + ordered dedup → cap 5 | **0.054** | **0.053** | **0.059** | Yes |
| **(c) Conditional** | (b) + when `estimated_row_count < fetch_budget`, fetch only estimate | Same as (b) on large tables; **12 rows** when table has 12 rows (no over-read) | — | — | Yes |

**Ratio client / DISTINCT (lower = client wins):** 0.127 (5k) · 0.013 (50k) · **0.002** (500k).

**Decision:** ship **(b)** as default, with **(c)** via `resolve_fetch_row_budget(..., estimated_row_count=…)` already wired in `sql_connector.sample()`. **Reject (a)** for default path — on 500k rows DISTINCT is **~503× slower** than client dedup in this fixture.

Env knobs: `DATA_BOAR_SAMPLE_FETCH_MULTIPLIER` (default **10**, clamped 1–100); existing `DATA_BOAR_SQL_SAMPLE_LIMIT` still caps distinct values.

## Implementation map

| Location | Role |
| -------- | ---- |
| `connectors/sample_value_dedup.py` | `resolve_fetch_row_budget`, `distinct_values_capped`, `join_distinct_sample` |
| `connectors/sql_connector.py` | Fetch `budget` rows; return distinct cap |
| `connectors/snowflake_connector.py` | Same via `column_sample_sql_for_cursor` + `fetchmany(budget)` |
| `connectors/filesystem_connector.py` | `_scan_sqlite_file_as_db` uses dedup path |
| `connectors/nfs_connector.py` | **No separate sampling** — delegates to `FilesystemConnector` (`self._fs.run()`, `sample_limit` passed in `__init__`) |
| `connectors/mongodb_connector.py` | `find().limit(budget)` + per-field distinct cap |

Dialect SQL shape unchanged (TOP / ROWNUM / TABLESAMPLE / LIMIT per `sql_sampling.py` header).

## Safe-axis proof (#1338)

After this change, official benchmark gate at **200k** synthetic rows:

| Metric | Value |
| ------ | ----- |
| `opencore_hits` | 100 000 |
| `pro_hits` | 100 000 |
| `expected` | 100 000 |
| `opencore_seconds` | 0.1962 |
| `pro_seconds` | 0.0326 |
| `speed_axis` | PASS |
| `safe_axis` | PASS |

Command: `uv run python tests/benchmarks/run_official_bench.py --rows 200000 --workers 4`

Regression: `tests/test_sampling_dedup_before_cap.py::test_safe_axis_gate_passes_on_official_corpus`

## No raw persistence

Sampling returns ephemeral strings for `scan_column` only. Snowflake `_sample_column` docstring: *"Does not persist any raw content."* Covered by `test_snowflake_sample_does_not_persist_raw` (no `save_finding` on sample path).

## Phases

| # | Phase | Status |
| - | ----- | ------ |
| 1 | Strategy measurement + PLAN | ✅ Done |
| 2 | `sample_value_dedup.py` + SQL/Snowflake/FS/Mongo wiring | ✅ Done |
| 3 | Tests (rare PII, safe axis, no-persist) | ✅ Done |
| 4 | Hub sync + PLANS_TODO | ✅ Done |

## Acceptance (#1337)

- [x] `docs/plans/PLAN_SAMPLING_DEDUP_BEFORE_CAP.md` with `plans-hub-summary`
- [x] `python scripts/plans_hub_sync.py --write`
- [x] Entry in `docs/plans/PLANS_TODO.md`
- [x] Strategy chosen with **measured** cost table above
- [x] Mongo + NFS (via filesystem delegation) covered
- [x] Test: low-cardinality column, rare CPF found after dedup
- [x] Safe-axis gate pass on synthetic 200k corpus
- [x] No raw sample persistence on Snowflake sample path

## Operator commands

```bash
uv run pytest tests/test_sampling_dedup_before_cap.py -v
uv run python tests/benchmarks/run_official_bench.py --rows 200000 --workers 4
./scripts/check-all.sh --enforced
```
