# Plan: SQL column sampling — SRE posture, audit evidence, and statistical “pre-wiring”

**Status:** Completed (archived under `docs/plans/completed/`)
**Date:** 2026-04-26
**Authors:** Fabio Leitao
**Priority:** H2
**Depends on:** ADR-0043

**Synced with:** [PLANS_TODO.md](../PLANS_TODO.md) (*Integration / active threads*), [ADR 0043](../../adr/ADR-0043-sql-column-sampling-non-null-and-strategy-hook.md)

<!-- plans-hub-summary: SRE-safe SQL column sampling: non-null TOP/LIMIT today; roadmap for metadata-driven caps, TABLESAMPLE, audit coverage signals. -->
<!-- plans-hub-related: PLAN_ADDITIONAL_DETECTION_TECHNIQUES_AND_FN_REDUCTION.md, ../../TOPOLOGY.md -->

## Purpose

Relational connectors historically used **TOP-N** reads without `ORDER BY` (cheap for production databases, predictable I/O). That pattern has two well-known gaps for **compliance interpretation**:

1. **Sparse columns** — `LIMIT n` on mostly-`NULL` data can return **no** cell values, leaving the detector with an empty string (weak evidence, not the same as “safe”).
2. **Physical / plan bias** — without random sampling, “first *n* rows” are not a statistical draw across table history.

Data Boar must remain the **SRE-responsible** scanner: no default path that runs heavy `ORDER BY RANDOM()` or aggressive `TABLESAMPLE` on production during peak load. The mature approach is **pre-wiring**: one internal API (`SqlColumnSampleQueryBuilder` + optional metadata inputs) so **statistical** strategies become a **plug-in** later, behind config and tests.

## Slices (sequencing)

| Slice | Focus | Delivers |
| ----- | ----- | -------- |
| **1 — Pragmatism (shipped)** | Non-null filter + ops cap + architecture hook | `WHERE <column> IS NOT NULL` before row cap for SQLAlchemy SQL + Snowflake; **`DATA_BOAR_SQL_SAMPLE_LIMIT`** (1–10000) overrides `file_scan.sample_limit` when set; `connectors/sql_sampling.py` centralises SQL text; MSSQL uses **`TOP (n) … WITH (NOLOCK)`** (compliance read posture); PostgreSQL uses **`TABLESAMPLE SYSTEM (p)`** when `TableSamplingMetadata` marks a large table (`p` from **`DATA_BOAR_PG_TABLESAMPLE_SYSTEM_PERCENT`**); Snowflake **`SAMPLE (n ROWS)`** on non-null inline view; dialect schema blacklists in **`sql_connector`** / Snowflake list; per-table **INFO** log line includes human-readable strategy. Docs: [USAGE.md](../USAGE.md), [SENSITIVITY_DETECTION.md](../SENSITIVITY_DETECTION.md). |
| **1b — Config cascade (shipped)** | Hierarchical caps without connector forks | Optional YAML `sql_sampling.overrides`: per-target `sample_limit`, per-target `tables` (`schema.table` or bare table name), then global `patterns` (`fnmatch` on table name), then `file_scan.sample_limit`. Optional **`sql_sampling_file`** / **`sql_sampling_files`** merge fragments from disk (paths relative to the main config; inline `sql_sampling` wins on conflicts). **`core/sampling.SamplingPolicy`** resolves the cap; **`SQLConnector`** / **Snowflake** consume it before `resolve_sql_sample_limit`. Per-statement `execution_options(timeout=...)` remains **follow-up** (sync driver matrix + existing `read_timeout_seconds` / PostgreSQL `statement_timeout` on connect). |
| **2 — Infrastructure awareness (in progress)** | Metadata-first decisions | **Shipped (partial):** `connectors/sql_table_row_estimate.py` reads approximate row counts from **dictionary stats** (PostgreSQL `pg_class.reltuples`, SQL Server `sys.partitions`, Oracle `ALL_TABLES.NUM_ROWS`, MySQL `information_schema.tables.TABLE_ROWS`) — never `COUNT(*)` on the business table; `SQLConnector` caches one estimate per table to feed `TableSamplingMetadata`. **Still next:** egress-aware caps, optional heavier strategies, richer throttles beyond **`inter_query_delay_ms`**. |
| **3 — Statistical power (future)** | Dialect plug-ins | `TABLESAMPLE BERNOULLI` (PostgreSQL), `TABLESAMPLE` (SQL Server), Oracle `SAMPLE` / block sampling where appropriate — **off by default** or low fixed rates; golden tests per dialect. **Drift / cursor** sampling across weekly runs (persisted watermark) only if product + privacy review clear. |
| **4 — Reporting (future)** | Honest evidence strength | **Coverage / confidence** metadata separate from ML scores: e.g. `sample_rows` vs `table_estimate_rows` so DPOs see **evidence depth**, not false certainty. |

## Code map

- **`connectors/sql_sampling.py`** — `SamplingManager.build_column_sample`, `resolve_sql_sample_limit`, `SqlColumnSampleQueryBuilder.build(...)` (dialect SQL + **`IS NOT NULL`**).
- **`core/sampling_policy.py`** — `SamplingPolicy`: YAML cascade for numeric caps (table → target → pattern → global).
- **`core/sampling.py`** — facade: `SamplingProvider` is an alias of `SamplingPolicy` (policy only; no raw SQL strings here).
- **`config/loader.py`** — `sql_sampling` normalization; optional **`sql_sampling_file`** / **`sql_sampling_files`** merge (see [USAGE.md](../USAGE.md)); `load_config` / `normalize_config(..., config_path=...)` expand fragments.
- **`core/engine.py`** — `AuditEngine` builds `SamplingPolicy.from_config(config)` once; passes `sampling_policy` into **SQL** / **Snowflake** connectors only (`connector_class.__name__` guard).
- **`connectors/sql_connector.py`** — `SQLConnector.sample` resolves the cap via policy, then **`SamplingManager.build_column_sample`** for the executable `text(...)`.
- **`connectors/snowflake_connector.py`** — `_sample_column`: same cap resolution + `column_sample_sql_for_cursor` (non-null + dialect).

## PoC integration map (copy-paste context for assistants)

Use this block when scoping refactors or demos so paths match the repo (not hypothetical `core/config.py` or `connectors/sql.py`).

**Injection (already wired):** `AuditEngine` receives the normalized config dict (from **`config/loader.load_config`** or API save + **`normalize_config(..., config_path=...)`**). It instantiates **`SamplingPolicy.from_config(config)`** (exposed as **`SamplingProvider`** in **`core/sampling.py`**) and passes **`sampling_policy=`** into **`SQLConnector`** and **`SnowflakeConnector`** in **`core/engine.py`** (`_run_target`). Other database drivers do not receive the kwarg.

**Config surface (not `sampling_overrides` at root):** hierarchical overrides live under **`sql_sampling.overrides`** (targets / tables / patterns). Optional modular files: **`sql_sampling_file`**, **`sql_sampling_files`**. Global row-style default remains **`file_scan.sample_limit`** until **`DATA_BOAR_SQL_SAMPLE_LIMIT`** clamps at the connector.

**“`get_query`” equivalent:** policy returns an **integer cap**; dialect SQL is **`SamplingManager.build_column_sample(...)`** in **`connectors/sql_sampling.py`** (always includes non-null filter for supported dialects). Connectors stay “dumb executors”: resolve limit → build plan → execute.

**PoC narrative:** YAML tuning per target/pattern reduces load on slow DBs without code forks; non-null sampling improves detector input on sparse columns; architecture is “policy in core + one SQL sampling module,” not string SQL scattered per connector.

## Operator notes

- **Break-glass:** set **`DATA_BOAR_SQL_SAMPLE_LIMIT`** in the process environment to tighten reads without editing YAML (still clamped to **10000**).
- **Black Friday / peak:** keep defaults; use smaller caps and narrower target lists — heavy statistical sampling stays **Slice 3** and must remain **opt-in**.

## References

- [ADR 0043](../../adr/ADR-0043-sql-column-sampling-non-null-and-strategy-hook.md) — decision record.
- [PLAN_ADDITIONAL_DETECTION_TECHNIQUES_AND_FN_REDUCTION.md](../PLAN_ADDITIONAL_DETECTION_TECHNIQUES_AND_FN_REDUCTION.md) — FN / incomplete-sample narrative.
