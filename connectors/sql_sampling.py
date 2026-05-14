"""
Column sampling SQL for relational connectors: SRE-first defaults and a single
place to evolve dialect-specific strategies (TABLESAMPLE, metadata-driven caps).

**Dialect notes (production temperament):**

- **Oracle:** ``ROWNUM`` applies to the *outer* result; the inner query filters
  ``IS NOT NULL`` first so the engine does not feed the outer row limit with
  null-only rows (classic subquery shape).
- **Snowflake:** ``SAMPLE (n ROWS)`` on a non-null-filtered inline view for
  warehouse/cost-aware reads (multi-column / single-round-trip remains future).
- **SQL Server:** ``SELECT TOP (n) … FROM … WITH (NOLOCK)`` for compliance-style
  reads that avoid blocking on long writers (dirty/non-repeatable reads are
  acceptable for sampling-only detection; not for transactional guarantees).
- **PostgreSQL:** ``LIMIT`` by default; when table metadata marks a **large**
  table (row-count hint), ``TABLESAMPLE SYSTEM (p)`` plus ``LIMIT`` reduces
  sequential bias on huge heaps (``p`` via ``DATA_BOAR_PG_TABLESAMPLE_SYSTEM_PERCENT``).
  DuckDB/Cockroach keep ``LIMIT`` only (dialect differences).

Identifiers passed into `SamplingManager.build_column_sample` (and the legacy
`SqlColumnSampleQueryBuilder.build`) must already be dialect-escaped (see
`sql_connector.sample`); this module only composes SQL shape.

Architecture (orchestrator vs fixed strings):
- `SamplingManager` picks a **strategy label** and builds a `TextClause` from
  dialect + optional `TableSamplingMetadata` (row-count hints reserved for
  future prudent modes).
- Connectors ask the manager for a **plan** (query + label) and may log the
  label once per table for audit traceability.

**SRE posture (no accidental ``ORDER BY`` on auto-sampling):** sampling SQL must
not introduce ``ORDER BY`` (sorts can force full-table plans). Prefer dialect
caps (``TOP`` / ``LIMIT`` / ``ROWNUM`` / ``SAMPLE``) and dictionary row hints only.

**DBA attribution:** every emitted statement starts with the line comment
``-- Data Boar Compliance Scan`` so operators can grep activity views.

Doctrinal references (behaviour-preserving comments — do not remove in refactors):

- ``docs/ops/inspirations/DEFENSIVE_SCANNING_MANIFESTO.md`` (NASA SEL,
  Cloudflare engineering, Steve Gibson) — *test what you fly*; sampling caps,
  statement timeouts, ``WITH (NOLOCK)``, and the leading SQL comment are
  contractual, not micro-optimisations.
- ``docs/ops/inspirations/THE_ART_OF_THE_FALLBACK.md`` (Usagi Electric,
  The 8-Bit Guy) — strategy labels (``parser_sql`` -> ``regex`` ->
  ``raw_string_heuristic``) and ``audit_notes`` exist so a degraded path
  never falls through silently. Skipping levels hides bugs.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

from sqlalchemy import text
from sqlalchemy.sql.elements import TextClause

# Leading comment on all generated sampling SQL (pg_stat_activity / DMVs).
#
# Doctrine: the leading comment is the DBA-grep contract from
# DEFENSIVE_SCANNING_MANIFESTO.md section 4. Tailing pg_stat_activity / DMVs
# must be enough to identify Data Boar without paging the operator. Removing
# this constant would silently violate the contract; tests in
# tests/test_sql_sampling.py guard the prefix.
_COMPLIANCE_SCAN_LEADING = "-- Data Boar Compliance Scan\n"


def _tag_sql(body: str) -> str:
    return _COMPLIANCE_SCAN_LEADING + body


# Ops break-glass: tighten or cap row reads without editing YAML (still bounded).
_ENV_SQL_SAMPLE_LIMIT = "DATA_BOAR_SQL_SAMPLE_LIMIT"
# PostgreSQL TABLESAMPLE SYSTEM argument: percentage of relation (0.01–100).
_ENV_PG_TABLESAMPLE_SYSTEM_PERCENT = "DATA_BOAR_PG_TABLESAMPLE_SYSTEM_PERCENT"
# SQL Server TABLESAMPLE SYSTEM percentage when metadata marks a huge table.
_ENV_MSSQL_TABLESAMPLE_PERCENT = "DATA_BOAR_MSSQL_TABLESAMPLE_SYSTEM_PERCENT"
# Optional per-statement cap hint. Currently emitted only on **MySQL/MariaDB**
# (``/*+ MAX_EXECUTION_TIME(N) */``) and as ``SET LOCAL statement_timeout`` on
# **PostgreSQL** (applied at the connector layer, not the SQL string). SQL
# Server has no equivalent query-level time hint, so the value is recorded in
# the audit log but **not** inlined into MSSQL sample SQL — see ADR / RCA in
# this module's history.
_ENV_SAMPLE_STMT_TIMEOUT_MS = "DATA_BOAR_SAMPLE_STATEMENT_TIMEOUT_MS"
_HARD_MAX_SAMPLE = 10_000

# Threshold for metadata-driven behaviour (TABLESAMPLE on PostgreSQL, label hints).
_LARGE_TABLE_ROW_HINT = 1_000_000


def resolve_sql_sample_limit(config_limit: int) -> int:
    """
    Effective per-column sample size.

    - Baseline: ``max(1, min(config_limit, _HARD_MAX_SAMPLE))``.
    - If ``DATA_BOAR_SQL_SAMPLE_LIMIT`` is set to an integer, it **replaces** the
      baseline (still clamped to ``1.._HARD_MAX_SAMPLE``). Invalid env values are ignored.

    Doctrine (DEFENSIVE_SCANNING_MANIFESTO.md section 2): the cap is a *relief
    valve*, not a knob. Operators can tune; the runtime always clamps. Removing
    the ``min(..., _HARD_MAX_SAMPLE)`` here would let bad YAML or env values
    flood the customer DB with unbounded reads -- breaking the "guest in the
    customer database" contract. The clamp test lives in
    ``tests/test_sql_sampling.py``.
    """
    base = max(1, min(int(config_limit), _HARD_MAX_SAMPLE))
    raw = os.environ.get(_ENV_SQL_SAMPLE_LIMIT, "").strip()
    if not raw:
        return base
    try:
        env_v = int(raw)
    except ValueError:
        return base
    return max(1, min(env_v, _HARD_MAX_SAMPLE))


def _pg_tablesample_system_percent() -> float:
    """
    Percentage argument for PostgreSQL ``TABLESAMPLE SYSTEM`` on large tables.

    Clamped to ``0.01..100.0``; invalid env values fall back to ``1.0``.
    """
    raw = os.environ.get(_ENV_PG_TABLESAMPLE_SYSTEM_PERCENT, "").strip()
    if not raw:
        return 1.0
    try:
        v = float(raw)
    except ValueError:
        return 1.0
    return max(0.01, min(v, 100.0))


def _mssql_tablesample_system_percent() -> float:
    raw = os.environ.get(_ENV_MSSQL_TABLESAMPLE_PERCENT, "").strip()
    if not raw:
        return 10.0
    try:
        v = float(raw)
    except ValueError:
        return 10.0
    return max(0.01, min(v, 100.0))


def resolve_statement_timeout_ms_for_sampling(explicit: int | None) -> int | None:
    """
    Per-sample statement budget in milliseconds (SQL Server ``OPTION`` / MySQL hint).

    - If ``explicit`` is ``<= 0``, sampling hints are disabled.
    - If ``explicit`` is ``None``, read ``DATA_BOAR_SAMPLE_STATEMENT_TIMEOUT_MS``;
      empty env means **no** driver-level hint in generated SQL (connectors may
      still apply ``SET LOCAL`` on PostgreSQL).

    Doctrine (DEFENSIVE_SCANNING_MANIFESTO.md section 2): statement timeouts
    are clamped to ``250..60_000`` ms in code. Without this clamp, a misfilled
    YAML or env variable could pin a customer-side session indefinitely --
    incompatible with the *no exclusive locks* / *no surprise side effects*
    clauses of the customer-database contract. The 60_000 ms ceiling is the
    relief valve quoted in the executive report's Methodology-of-Safety block.
    """
    if explicit is not None:
        if explicit <= 0:
            return None
        return max(250, min(int(explicit), 60_000))
    raw = os.environ.get(_ENV_SAMPLE_STMT_TIMEOUT_MS, "").strip()
    if not raw:
        return None
    try:
        v = int(raw)
    except ValueError:
        return None
    if v <= 0:
        return None
    return max(250, min(v, 60_000))


@dataclass(frozen=True)
class TableSamplingMetadata:
    """
    Optional table-level hints for strategy selection (pre-scan insights).

    When ``estimated_row_count`` exceeds ``_LARGE_TABLE_ROW_HINT``, the manager
    appends a suffix to ``ColumnSamplePlan.strategy_label`` and sets
    ``audit_notes``. On **PostgreSQL** only, SQL switches to
    ``TABLESAMPLE SYSTEM`` plus ``LIMIT``; other dialects may only change labels
    until wired.
    """

    estimated_row_count: int | None = None


@dataclass(frozen=True)
class ColumnSamplePlan:
    """Executable sampling intent: SQLAlchemy ``TextClause`` plus audit label."""

    query: TextClause
    strategy_label: str
    audit_notes: str = ""
    #: Short phrase for operator logs (e.g. ``TABLESAMPLE SYSTEM (PostgreSQL)``).
    human_strategy: str = ""


def _clamp_limit(limit: int) -> int:
    return max(1, min(int(limit), _HARD_MAX_SAMPLE))


def _mysql_table_ref(safe_schema: str, safe_table: str, schema: str | None) -> str:
    def _bk(s: str) -> str:
        return s.replace("`", "``")

    if schema:
        return f"`{_bk(safe_schema)}`.`{_bk(safe_table)}`"
    return f"`{_bk(safe_table)}`"


def _ansi_quoted_table(safe_schema: str, safe_table: str, schema: str | None) -> str:
    return f'"{safe_schema}"."{safe_table}"' if schema else f'"{safe_table}"'


def _large_table_flags(
    table_metadata: TableSamplingMetadata | None,
) -> tuple[bool, str]:
    large = (
        table_metadata is not None
        and table_metadata.estimated_row_count is not None
        and table_metadata.estimated_row_count > _LARGE_TABLE_ROW_HINT
    )
    audit_notes = (
        f"estimated_rows={table_metadata.estimated_row_count} exceeds_hint={_LARGE_TABLE_ROW_HINT}"
        if large
        else ""
    )
    return large, audit_notes


def _with_large_suffix(base: str, large: bool) -> str:
    return f"{base}{'_large_table_metadata' if large else ''}"


def _plan_sqlite_column_sample(
    safe_col: str, safe_table: str, lim: int, large: bool, audit_notes: str
) -> ColumnSamplePlan:
    label = _with_large_suffix("non_null_limit_sqlite", large)
    q = text(
        _tag_sql(
            f'SELECT "{safe_col}" FROM "{safe_table}" '  # nosec B608 -- identifiers from DB schema introspection; ANSI-quoted '""'-escape (sql_connector.py:394-396)
            f'WHERE "{safe_col}" IS NOT NULL LIMIT {lim}'
        )
    )
    return ColumnSamplePlan(
        query=q,
        strategy_label=label,
        audit_notes=audit_notes,
        human_strategy="LIMIT (SQLite)",
    )


def _plan_mysql_column_sample(
    safe_col: str,
    safe_schema: str,
    safe_table: str,
    schema: str | None,
    lim: int,
    large: bool,
    audit_notes: str,
    statement_timeout_ms: int | None,
) -> ColumnSamplePlan:
    label = _with_large_suffix("non_null_limit_mysql", large)
    t = _mysql_table_ref(safe_schema, safe_table, schema)

    def _bk(s: str) -> str:
        return s.replace("`", "``")

    cc = _bk(safe_col)
    hint = ""
    if statement_timeout_ms and statement_timeout_ms > 0:
        hint = f"/*+ MAX_EXECUTION_TIME({int(statement_timeout_ms)}) */ "
    q = text(
        _tag_sql(f"SELECT {hint}`{cc}` FROM {t} WHERE `{cc}` IS NOT NULL LIMIT {lim}")  # nosec B608 -- identifiers from DB schema introspection; backtick-quoted '``'-escape via _bk()
    )
    return ColumnSamplePlan(
        query=q,
        strategy_label=label,
        audit_notes=audit_notes,
        human_strategy="LIMIT (MySQL)",
    )


def _plan_oracle_column_sample(
    safe_col: str,
    safe_schema: str,
    safe_table: str,
    schema: str | None,
    lim: int,
    large: bool,
    audit_notes: str,
) -> ColumnSamplePlan:
    label = _with_large_suffix("non_null_rownum_oracle", large)
    t = _ansi_quoted_table(safe_schema, safe_table, schema)
    # Inner filter first: ROWNUM on the outer query caps non-null rows only.
    q = text(
        _tag_sql(
            f'SELECT * FROM (SELECT "{safe_col}" FROM {t} '  # nosec B608 -- identifiers from DB schema introspection; ANSI-quoted '""'-escape (sql_connector.py:394-396)
            f'WHERE "{safe_col}" IS NOT NULL) WHERE ROWNUM <= :lim'
        )
    ).bindparams(lim=lim)
    return ColumnSamplePlan(
        query=q,
        strategy_label=label,
        audit_notes=audit_notes,
        human_strategy="ROWNUM inner filter (Oracle)",
    )


def _plan_snowflake_column_sample(
    safe_col: str,
    safe_schema: str,
    safe_table: str,
    schema: str | None,
    lim: int,
    large: bool,
    audit_notes: str,
) -> ColumnSamplePlan:
    """
    Snowflake: fixed-row ``SAMPLE (n ROWS)`` on a non-null-filtered inline view.

    Keeps compliance sampling meaningful on sparse columns while using Snowflake's
    row-oriented sample (see Snowflake ``SAMPLE`` / ``LIMIT`` product notes).
    """
    label = _with_large_suffix("non_null_sample_rows_snowflake", large)
    t = _ansi_quoted_table(safe_schema, safe_table, schema)
    lim_v = _clamp_limit(lim)
    q = text(
        _tag_sql(
            f'SELECT "{safe_col}" FROM ('  # nosec B608 -- identifiers from DB schema introspection; ANSI-quoted '""'-escape (sql_connector.py:394-396)
            f'SELECT "{safe_col}" FROM {t} WHERE "{safe_col}" IS NOT NULL'
            f") _db_sf_nonnull SAMPLE ({lim_v} ROWS)"
        )
    )
    return ColumnSamplePlan(
        query=q,
        strategy_label=label,
        audit_notes=audit_notes,
        human_strategy="SAMPLE ROWS (Snowflake)",
    )


def _plan_mssql_column_sample(
    safe_col: str,
    safe_schema: str,
    safe_table: str,
    schema: str | None,
    lim: int,
    large: bool,
    audit_notes: str,
    statement_timeout_ms: int | None,
) -> ColumnSamplePlan:
    # SQL Server has **no** query-level execution-time hint equivalent to
    # MySQL's ``/*+ MAX_EXECUTION_TIME(N) */``; ``OPTION (MAX_EXECUTION_TIME = …)``
    # is *not* valid T-SQL and emitting it makes every sample fail with a
    # syntax error -- which the connector's broad ``except Exception`` then
    # swallows, returning empty samples and producing **silent zero-finding
    # scans** on every SQL Server target. Statement-time bounds for MSSQL
    # come from the SQLAlchemy connection-level ``connect_timeout`` (set via
    # ``_connect_args_from_target``); for finer per-statement budgets a
    # dedicated ADR + driver-level ``LOCK_TIMEOUT`` or session option is the
    # right surface, never an invented OPTION clause.
    _ = statement_timeout_ms  # accepted for API parity; not emitted into SQL
    t = _ansi_quoted_table(safe_schema, safe_table, schema)
    ts_clause = ""
    if large:
        pct = _mssql_tablesample_system_percent()
        pct_s = f"{pct:g}"
        ts_clause = f" TABLESAMPLE SYSTEM ({pct_s} PERCENT)"
    base_label = (
        "non_null_top_nolock_tablesample_mssql"
        if large
        else "non_null_top_nolock_mssql"
    )
    label = _with_large_suffix(base_label, large)
    q = text(
        _tag_sql(
            f'SELECT TOP ({lim}) "{safe_col}" FROM {t}{ts_clause} WITH (NOLOCK) '  # nosec B608 -- identifiers from DB schema introspection; ANSI-quoted '""'-escape (sql_connector.py:394-396)
            f'WHERE "{safe_col}" IS NOT NULL'
        )
    )
    return ColumnSamplePlan(
        query=q,
        strategy_label=label,
        audit_notes=audit_notes,
        human_strategy="TOP + NOLOCK (SQL Server)",
    )


def _plan_postgresql_column_sample(
    safe_col: str,
    safe_schema: str,
    safe_table: str,
    schema: str | None,
    lim: int,
    large: bool,
    audit_notes: str,
) -> ColumnSamplePlan:
    """PostgreSQL: LIMIT, or TABLESAMPLE SYSTEM on large-table metadata hint."""
    t = _ansi_quoted_table(safe_schema, safe_table, schema)
    if large:
        pct = _pg_tablesample_system_percent()
        pct_s = f"{pct:g}"
        label = _with_large_suffix("non_null_tablesample_system_postgresql", large)
        q = text(
            _tag_sql(
                f'SELECT "{safe_col}" FROM {t} TABLESAMPLE SYSTEM ({pct_s}) '  # nosec B608 -- identifiers from DB schema introspection; ANSI-quoted '""'-escape (sql_connector.py:394-396)
                f'WHERE "{safe_col}" IS NOT NULL LIMIT {lim}'
            )
        )
        human = "TABLESAMPLE SYSTEM (PostgreSQL)"
    else:
        label = _with_large_suffix("non_null_limit_postgresql", large)
        q = text(
            _tag_sql(
                f'SELECT "{safe_col}" FROM {t} WHERE "{safe_col}" IS NOT NULL LIMIT {lim}'  # nosec B608 -- identifiers from DB schema introspection; ANSI-quoted '""'-escape (sql_connector.py:394-396)
            )
        )
        human = "LIMIT (PostgreSQL)"
    return ColumnSamplePlan(
        query=q,
        strategy_label=label,
        audit_notes=audit_notes,
        human_strategy=human,
    )


def _plan_postgres_like_column_sample(
    safe_col: str,
    safe_schema: str,
    safe_table: str,
    schema: str | None,
    lim: int,
    large: bool,
    audit_notes: str,
    *,
    flavor: str,
    human_strategy: str,
) -> ColumnSamplePlan:
    label = _with_large_suffix(f"non_null_limit_{flavor}", large)
    t = _ansi_quoted_table(safe_schema, safe_table, schema)
    q = text(
        _tag_sql(
            f'SELECT "{safe_col}" FROM {t} WHERE "{safe_col}" IS NOT NULL LIMIT {lim}'  # nosec B608 -- identifiers from DB schema introspection; ANSI-quoted '""'-escape (sql_connector.py:394-396)
        )
    )
    return ColumnSamplePlan(
        query=q,
        strategy_label=label,
        audit_notes=audit_notes,
        human_strategy=human_strategy,
    )


def _plan_default_column_sample(
    dialect: str,
    safe_col: str,
    safe_schema: str,
    safe_table: str,
    schema: str | None,
    lim: int,
    large: bool,
    audit_notes: str,
) -> ColumnSamplePlan:
    label = _with_large_suffix(f"non_null_limit_default_{dialect or 'unknown'}", large)
    t = _ansi_quoted_table(safe_schema, safe_table, schema)
    q = text(
        _tag_sql(
            f'SELECT "{safe_col}" FROM {t} WHERE "{safe_col}" IS NOT NULL LIMIT {lim}'  # nosec B608 -- identifiers from DB schema introspection; ANSI-quoted '""'-escape (sql_connector.py:394-396)
        )
    )
    return ColumnSamplePlan(
        query=q,
        strategy_label=label,
        audit_notes=audit_notes,
        human_strategy="LIMIT (ANSI-style)",
    )


class SamplingManager:
    """
    Orchestrates column sampling SQL: dialect, non-null filter, LIMIT/TOP/ROWNUM.

    Future hooks (pre-wired in comments below):
    - Oracle: optional ``SAMPLE BLOCK`` / DBMS_STATS approximations when wired.
    - **Cost / round-trips:** optional batched multi-column sample (one query per
      table slice) for Snowflake-class warehouses — see plan backlog narrative.
    """

    @staticmethod
    def build_column_sample(
        dialect: str,
        *,
        safe_col: str,
        safe_table: str,
        safe_schema: str,
        schema: str | None,
        limit: int,
        table_metadata: TableSamplingMetadata | None = None,
        statement_timeout_ms: int | None = None,
    ) -> ColumnSamplePlan:
        lim = _clamp_limit(limit)
        d = (dialect or "").lower()
        large, audit_notes = _large_table_flags(table_metadata)
        to = statement_timeout_ms

        if d == "sqlite":
            return _plan_sqlite_column_sample(
                safe_col, safe_table, lim, large, audit_notes
            )
        if d in ("mysql", "mariadb"):
            return _plan_mysql_column_sample(
                safe_col,
                safe_schema,
                safe_table,
                schema,
                lim,
                large,
                audit_notes,
                to,
            )
        if d == "oracle":
            return _plan_oracle_column_sample(
                safe_col, safe_schema, safe_table, schema, lim, large, audit_notes
            )
        if d in ("mssql", "microsoft sql server"):
            return _plan_mssql_column_sample(
                safe_col,
                safe_schema,
                safe_table,
                schema,
                lim,
                large,
                audit_notes,
                to,
            )
        if d == "snowflake":
            return _plan_snowflake_column_sample(
                safe_col,
                safe_schema,
                safe_table,
                schema,
                lim,
                large,
                audit_notes,
            )
        if d in ("postgresql", "postgres"):
            return _plan_postgresql_column_sample(
                safe_col,
                safe_schema,
                safe_table,
                schema,
                lim,
                large,
                audit_notes,
            )
        if d == "duckdb":
            return _plan_postgres_like_column_sample(
                safe_col,
                safe_schema,
                safe_table,
                schema,
                lim,
                large,
                audit_notes,
                flavor="duckdb",
                human_strategy="LIMIT (DuckDB)",
            )
        if d == "cockroachdb":
            return _plan_postgres_like_column_sample(
                safe_col,
                safe_schema,
                safe_table,
                schema,
                lim,
                large,
                audit_notes,
                flavor="cockroachdb",
                human_strategy="LIMIT (CockroachDB)",
            )
        return _plan_default_column_sample(
            d, safe_col, safe_schema, safe_table, schema, lim, large, audit_notes
        )


class SqlColumnSampleQueryBuilder:
    """
    Legacy static entry point: delegates to :class:`SamplingManager`.

    Portable sampling: ``WHERE <col> IS NOT NULL`` so TOP/LIMIT slots are not
    wasted on sparse columns (compliance blind spot on empty detector input).
    """

    @staticmethod
    def build(
        dialect: str,
        *,
        safe_col: str,
        safe_table: str,
        safe_schema: str,
        schema: str | None,
        limit: int,
        table_metadata: TableSamplingMetadata | None = None,
        statement_timeout_ms: int | None = None,
    ) -> TextClause:
        return SamplingManager.build_column_sample(
            dialect,
            safe_col=safe_col,
            safe_table=safe_table,
            safe_schema=safe_schema,
            schema=schema,
            limit=limit,
            table_metadata=table_metadata,
            statement_timeout_ms=statement_timeout_ms,
        ).query


def column_sample_sql_for_cursor(
    dialect: str,
    *,
    safe_col: str,
    safe_table: str,
    safe_schema: str,
    schema: str | None,
    limit: int,
    table_metadata: TableSamplingMetadata | None = None,
    statement_timeout_ms: int | None = None,
) -> tuple[str, dict[str, object], str, str, str]:
    """
    For DB-API drivers without SQLAlchemy execution (e.g. Snowflake connector).

    Returns ``(sql_string, bind_params, strategy_label, audit_notes, human_strategy)``.
    ``human_strategy`` is a short log phrase (e.g. ``SAMPLE ROWS (Snowflake)``).
    ``bind_params`` is always empty here: Oracle ROWNUM uses a literal ``lim``
    (still clamped) so Snowflake-style cursors never see ``:lim`` binds.
    """
    to = resolve_statement_timeout_ms_for_sampling(statement_timeout_ms)
    plan = SamplingManager.build_column_sample(
        dialect,
        safe_col=safe_col,
        safe_table=safe_table,
        safe_schema=safe_schema,
        schema=schema,
        limit=limit,
        table_metadata=table_metadata,
        statement_timeout_ms=to,
    )
    d = (dialect or "").lower()
    if d == "oracle":
        lim_v = _clamp_limit(limit)
        t = _ansi_quoted_table(safe_schema, safe_table, schema)
        sql = _tag_sql(
            f'SELECT * FROM (SELECT "{safe_col}" FROM {t} '  # nosec B608 -- identifiers from DB schema introspection; ANSI-quoted '""'-escape (sql_connector.py:394-396)
            f'WHERE "{safe_col}" IS NOT NULL) WHERE ROWNUM <= {lim_v}'
        )
        human = plan.human_strategy or plan.strategy_label
        return sql, {}, plan.strategy_label, plan.audit_notes, human
    compiled = plan.query.compile(compile_kwargs={"literal_binds": True})
    human = plan.human_strategy or plan.strategy_label
    return str(compiled), {}, plan.strategy_label, plan.audit_notes, human
