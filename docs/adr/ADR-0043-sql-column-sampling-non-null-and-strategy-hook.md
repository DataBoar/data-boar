# ADR 0043: SQL column sampling — non-null filter and strategy hook

## Context

SQL and Snowflake connectors sample up to **`file_scan.sample_limit`** cell values per column to feed regex / ML / DL detection. The legacy pattern was effectively **TOP-N without `ORDER BY`**, which is gentle on production I/O but:

- Wastes sample slots on **`NULL`**-heavy (sparse) columns, often returning **empty** concatenated text so the detector sees no value evidence.
- Does not claim statistical coverage of large tables; that remains a **documentation and reporting** honesty problem for compliance stakeholders.

Operators also need a **break-glass** way to cap reads without editing YAML during incidents or peak traffic.

## Decision

1. **Always apply `WHERE <column> IS NOT NULL`** in the generated column-sample SQL (SQLite, MySQL/MariaDB, PostgreSQL-style `LIMIT`, Oracle `ROWNUM` subquery, SQL Server `TOP (n)`), before applying the row cap.
2. **Centralise** sampling SQL in **`connectors/sql_sampling.py`** via **`SqlColumnSampleQueryBuilder`**, so future dialect strategies (e.g. `TABLESAMPLE`) plug in behind one API without duplicating identifier escaping rules in `sql_connector.py`.
3. **Optional process environment variable `DATA_BOAR_SQL_SAMPLE_LIMIT`**: when set to an integer, it **replaces** the configured limit for SQLAlchemy-backed SQL targets and Snowflake, clamped to **`1`..`10000`**; invalid values are ignored.

## Consequences

- **Positive:** Better detector input on sparse columns without increasing the nominal row cap; MSSQL gets syntactically valid **`TOP`** sampling; one module owns evolution toward metadata-first / statistical sampling ([`PLAN_SQL_SAMPLING_SRE_AND_AUDIT_EVIDENCE.md`](../plans/PLAN_SQL_SAMPLING_SRE_AND_AUDIT_EVIDENCE.md)).
- **Trade-off:** `WHERE col IS NOT NULL` can still force a scan on some engines if the optimiser cannot short-circuit; the default **small *n*** keeps this aligned with the existing “light probe” contract.
- **Compliance:** Outputs are still **sample-based**, not exhaustive; reports should continue to state incomplete-population limits (existing generator strings and [`PLAN_ADDITIONAL_DETECTION_TECHNIQUES_AND_FN_REDUCTION.md`](../plans/PLAN_ADDITIONAL_DETECTION_TECHNIQUES_AND_FN_REDUCTION.md)).

## References

- [`connectors/sql_sampling.py`](../../connectors/sql_sampling.py)
- [`docs/USAGE.md`](../USAGE.md) — *Global options* (relational database sampling paragraph)
