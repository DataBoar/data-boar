# Plan: DB per-table parallelism (worker pool inside one SQL target)

**Status:** Active (per-table pool + resume without duplicates; batch-per-table sampling, per-column work items and Snowflake are roadmap)
**Date:** 2026-11-14
**Authors:** Fabio Leitao
**Priority:** H1 / U1 (GitHub milestone v1.8.2 after the #2240 renumbering; pulled forward by operator order on 2026-11-14, same epic as #1820)
**GitHub:** [#1322](https://github.com/DataBoar/data-boar/issues/1322) (pair of [#1820](https://github.com/DataBoar/data-boar/issues/1820) on the filesystem axis; cap from [#551](https://github.com/DataBoar/data-boar/issues/551); resume from [#1330](https://github.com/DataBoar/data-boar/issues/1330); throttling from [#1320](https://github.com/DataBoar/data-boar/issues/1320))

<!-- plans-hub-summary: Worker pool inside one SQL target (pure-Python threads, one pooled connection per worker, tier cap from #551, no new cap): workers sample and detect one table each, the target thread persists in table order for exact serial parity and checkpoints a table only after its writes; --resume replaces the partial findings of an interrupted table (no duplicates); batch-per-table sampling and Snowflake stay roadmap (#1322). -->
<!-- plans-hub-related: PLAN_FILESYSTEM_INTRA_TARGET_PARALLELISM.md, PLAN_DATABASE_COMPAT_MATRIX.md -->

**Synced with:** [PLANS_TODO.md](PLANS_TODO.md)

## Motivation

Measured on a real engagement (issue #1322: remote RDS SQL Server, RTT ~140 ms): `AuditEngine` parallelised only **across targets**, and `SQLConnector.run` sampled one column at a time, one round trip each. Three databases meant three concurrent queries whatever `scan.max_workers` said; the scanner sat at 0 % CPU, every thread waiting on the network, while the server stayed at 7–11 % CPU. The bottleneck is latency × granularity, not CPU, GIL, bandwidth or the server.

## Decisions (operator, 2026-11-14 — not reopened here)

1. **Same pattern as the filesystem pool (#1820).** Pure Python, `concurrent.futures.ThreadPoolExecutor`, no native extension.
2. **No new cap.** The pool size comes from `scan.max_workers` **after** the existing clamp in `AuditEngine.start_audit` (`LicenseGuard.worker_cap()`: `dbmax_workers` claim, then Community 2, Std 2, Pro 4, Pro+ 8, Enterprise / Partner unlimited; open mode clamp 2, #856), split across the targets that run together (`outer × inner ≤ max_workers`, `_intra_target_worker_budget`).
3. **`max_workers: 1` (default) is the serial path**, no pool.
4. **Checkpoint only after the writes** (`ScanTableCheckpoint`, #1330).

## Design

| Piece | Where | What |
| ----- | ----- | ---- |
| Budget | `core/engine.py` `_intra_target_worker_budget` (shared with #1820) | Same split; injected as `_intra_target_workers` into every target whose connector is a `SQLConnector` (any `type`, including `database`). |
| Brakes | `core/engine.py`, `SQLConnector.intra_target_workers()` | Target stays serial when `scan.adaptive_rate_limit` is on (#1320 measures per-target latency) or `inter_query_delay_ms > 0` (a politeness delay per query; a pool would multiply the query rate by N). |
| Connections | `SQLConnector.connect` | `create_engine(..., pool_size=workers)` only when workers > 1, so every worker checks out its **own** connection and none waits for `pool_timeout` (SQLAlchemy's default `QueuePool` is 5 + 10 overflow; a timeout would surface as a `sampling_error` and silently cut recall). Nothing is shared between workers but the thread-safe `Engine`. A pool that is not a `QueuePool` (SQLite `:memory:` uses one connection per thread, so each worker would see an empty database) forces the serial path. |
| Work item | `SQLConnector._run_table_pool` | One **table** (all its columns, in catalog order) per work item. Workers only sample and detect; their writes (`save_finding`, `sampling_error` from `sample()`, audit log lines) go to a per-table recording sink through a thread-local, never to `db_manager`. |
| Persist | target thread, `_drain_oldest` | Tables are drained **in discovery order**: `mark_sql_table_in_progress`, replay of the recorded writes in order, `mark_sql_table_completed`. Persisted rows, failures and checkpoint rows are identical to the serial run. In-flight window: 4 × workers tables. |
| Resume | `LocalDBManager.mark_sql_table_in_progress(..., replace=True)` | A table that is `in_progress` in the resumed session (started, never completed) has its earlier findings in the session deleted, by equality on `(session, target, schema, table)` (no `LIKE`, names match literally), in the same transaction that re-marks it. Fixes the duplicate findings the serial resume already produced (#1330 re-scanned the partial table on top of its committed columns). |
| Errors | as serial | A sampling failure is already isolated per column (`ColumnSampleError` → `sampling_error`, next column). An unexpected exception keeps today's semantics: the writes recorded before it are kept, the table stays `in_progress`, the target aborts at the **same ordered position** (`error` failure from `run()`); results of later tables already read are discarded. |
| Stop | `threading.Event` + `pool.shutdown(wait=True, cancel_futures=True)` | When the **target thread** leaves the pool (an exception or interrupt raised in a worker or while persisting), it sets the stop event; workers check it before every column, so the pool stops after at most one column per worker instead of finishing tables of hundreds of columns. No pool thread outlives `run()`. Thread names start with `databoar-sql-intra`. **Limit (pre-existing engine behaviour, see below):** a Ctrl+C / SIGTERM does not reach this path while the pool runs. |
| Sampling audit log | `sample()` | The "Sampling X using Y strategy" line is deduplicated per worker thread (thread-local key) instead of one shared slot, so it still prints once per table. |

### SQLite as a source

The scanned SQLite file is only **read**; several connections reading one file is fine. The single-writer constraint applies to the **results** database (`LocalDBManager`, `NullPool`): only the target thread writes, as in #1820. Expect little gain on a local SQLite source (no network wait; with the GIL the detection does not run in parallel).

## Tests (TDD, synthetic data only)

`tests/test_sql_intra_target_parallelism.py` (items `d1322_a` … `d1322_f`), on a synthetic SQLite file with 14 tables (including `z%b`, `z_b`, `zxb` and a name with a quote and `%`), marker / e-mail / all-NULL columns and, where needed, one phantom table injected into discovery whose sample fails (a phantom *column* would not fail on SQLite, which reads an unknown double-quoted identifier as a string literal):

- **(a)** exact parity of findings, `scan_failures` and table checkpoints (same rows, same fields, same order) for 2/4/8 workers; same write stream with a plain test double; real `DataScanner`; DB writes only on the target thread.
- **(b)** `workers = 1` builds no pool; no key means serial.
- **(c)** observed concurrency equals the budget (barrier, no sleeps), including 16 workers (above the default connection pool); engine end-to-end per tier with enforced test JWTs (Community 2, Pro 4, Pro+ 8, claim 3, Enterprise 6, Community with `max_workers: 1`), open-mode clamp, two targets split 2 + 2 under Pro; `:memory:`, `inter_query_delay_ms` and adaptive rate limit stay serial.
- **(d)** interrupt inside a worker, and a simulated hard kill after the first finding of a table was written, then resume (serial, 2 and 4 workers): completed tables are not re-scanned, the interrupted table is, and findings, failures and checkpoints are **identical** to an uninterrupted run; engine end-to-end `interrupted` → `start_audit(resume_session_id=…)` → `completed`.
- **(e)** a sampling failure keeps every other finding; an unexpected detector error aborts at the serial position with identical persisted state.
- **(f)** interrupt on the target thread or inside a worker leaves no pool thread alive; the stop event ends the run without finishing in-flight tables.

Red at `9e23932f` (22 failed, 13 passed: the passing ones pin today's serial semantics); green from `3385e86b`.

### Interrupt and resume through `main.py` (evidence, 2026-11-14)

Synthetic source of 400 tables × 6 columns (2 400 findings), one `database` target, `python main.py --config … --resume <session>`, open mode (pool of 2 with `max_workers: 4`). Findings compared by `(table, column, sensitivity, pattern, norm, confidence)` in id order (md5 of the ordered dump):

| Run | Session after the signal | Rows before resume | After `--resume` | Identical to uninterrupted |
| --- | ------------------------ | ------------------ | ---------------- | -------------------------- |
| SIGKILL at 3 s, pool | `running` (109 completed, 1 `in_progress`) | 657 | 2 400 (`completed`) | yes |
| SIGTERM at 3 s, serial (×5) | `interrupted` | 735–831 (partial table included) | 2 400 (`completed`) | yes |
| SIGTERM at 2.5 s, pool | `interrupted`, but **all 400 tables completed** | 2 400 | — | — |

**Pre-existing limit found here (not introduced by #1322, also true for the #1820 filesystem pool and for multi-target runs):** with `scan.max_workers > 1` the engine runs targets on its own `ThreadPoolExecutor`; SIGTERM / Ctrl+C becomes a `KeyboardInterrupt` in the main thread, and leaving the `with ThreadPoolExecutor(...)` block waits for every running target to finish. Measured: the process exited 4.7 s (SQL target) and 5.1 s (filesystem target, 3 000 files) after SIGTERM, with the whole target scanned. Data stay correct (session `interrupted`, resume is a no-op on finished tables), but a stop is not prompt. Fixing it means an engine-level stop event set inside that block and checked by the connectors — a change to interrupt semantics in a `CRITICAL_MODULE`, left to the project-manager / operator decision.

Also observed while collecting the evidence: if a second process resumes a session while the original process is still alive, both write to it and findings duplicate (`--resume` does not check whether the session owner PID is alive). Pre-existing; not changed here.

## Measurement

_Pending (measurement window on the dev workstation)._ Runner in the format of `tests/benchmarks/run_filesystem_intra_target_bench.py`: serial vs 2 / 4 / 8 workers, N ≥ 5, median, exact parity, host / GIL / commit in the header, load < 1.5, on 3.14t (GIL off) and 3.14 (GIL). Profiles: local SQLite file, and a **simulated** per-query latency (fixture, not a real network). No gain is claimed here until it is measured.

## Risks

| Risk | Mitigation / status |
| ---- | ------------------- |
| Order of findings changes | Replay in table order on the target thread (tested, ordered comparison). Audit log lines are replayed with them. |
| Connection exhaustion / `pool_timeout` | Pool sized to the worker count; test with 16 workers. Customer-side `max_connections` is not checked: N workers open up to N connections per target. |
| Load on the customer database | Pool only with `max_workers ≥ 2` inside the tier cap; `inter_query_delay_ms` and adaptive rate limit keep the target serial. |
| SQLite `:memory:` | Forced serial (non-`QueuePool`). |
| Driver thread safety (pyodbc, oracledb, psycopg, PyMySQL) | One connection per worker, never shared; all these DB-API drivers allow one connection per thread (threadsafety ≥ 1). Only SQLite is exercised by the tests; SQL Server / Oracle / PostgreSQL / MySQL are unverified here. |
| MySQL DNS pin, Postgres `hostaddr`, MSSQL / Oracle TCP pins | Applied once at `connect()`; every pooled connection reuses the pinned URL / connect args. |
| Row-estimate cache (`_table_row_cache`) | Keyed by table; each table is handled by one worker. |
| `DataScanner` shared state | The Pro scan path keeps a per-call `_pending` slot on the scanner (not thread-safe), but it is off behind `PRO_SCAN_PATH_ZERO_REGRESSION_LATCH`; lifting that latch needs a thread-local first (applies to #1820 and multi-target runs too). |
| Integrity manifest | `connectors/sql_connector.py`, `core/engine.py`, `core/database.py` are `CRITICAL_MODULES`: the operator re-signs the manifest for the release. |

## Out of scope (this plan)

- **Batch per table** (`SELECT TOP N *` and local per-column detection, per-column `IS NOT NULL` fallback for all-NULL columns): the issue's largest gain on high latency, but it changes what is sampled (rows instead of non-NULL values per column), so it cannot keep exact parity with today's findings; needs the recall gate of #1338 first.
- **Per-column work items:** more parallelism for few wide tables, at the cost of a shared row-estimate cache and of draining partial tables; revisit with the batch-per-table work.
- **Snowflake:** separate connector (`SnowflakeConnector`) with the same serial loop and the same duplicate-on-resume of a partial table; no driver in the test environment.
- Replacing `scan_failures` rows of a re-scanned table: they carry no table column (only formatted `details`); a partial table's sampling failures can repeat after resume. With the per-table drain this only happens for a table interrupted mid-replay.
- MongoDB, Redis and the other non-SQL connectors.

## Phases

| Phase | Status |
| ----- | ------ |
| Plan + red tests | ✅ |
| Per-table pool + budget injection + connection pool sizing | ✅ |
| Resume replace of partial tables | ✅ |
| Prompt stop on SIGTERM with `max_workers > 1` (engine) | ⬜ decision pending (pre-existing) |
| Pinned benchmark (3.14t vs 3.14 GIL, dev workstation) | ⬜ |
| Batch per table (needs #1338 recall gate) | ⬜ roadmap |
| Snowflake per-table pool | ⬜ roadmap |
