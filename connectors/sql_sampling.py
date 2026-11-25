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
`sql_connector.sample`); this module only composes SQL shape. **Oracle** is the
exception: pass optional ``raw_col`` / ``raw_table`` / ``raw_schema`` from
discovery (may be ``quoted_name``) so case-sensitive quoted objects are preserved;
simple unquoted dictionary names are emitted without double quotes
(uppercase); any other catalog name is quoted.

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
import re
from dataclasses import dataclass
from typing import Any, Union

from sqlalchemy import (
    Column,
    MetaData,
    String,
    Table,
    bindparam,
    column,
    event,
    func,
    select,
    table,
    text,
)
from sqlalchemy import exc as sa_exc
from sqlalchemy.dialects import mssql as sa_mssql
from sqlalchemy.dialects import mysql as sa_mysql
from sqlalchemy.dialects import oracle as sa_oracle
from sqlalchemy.dialects import postgresql as sa_postgresql
from sqlalchemy.dialects import sqlite as sa_sqlite
from sqlalchemy.dialects.mssql import base as mssql_base
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.sql import literal_column
from sqlalchemy.sql.elements import TextClause, quoted_name
from sqlalchemy.sql.functions import GenericFunction
from sqlalchemy.sql.selectable import Select
from sqlalchemy.types import LargeBinary

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

PREFIX_PROBE_DIALECTS: frozenset[str] = frozenset(
    {
        "sqlite",
        "postgresql",
        "postgres",
        "mysql",
        "mariadb",
        "mssql",
        "microsoft sql server",
        "oracle",
    }
)
DEFAULT_PREFIX_PROBE_BYTES = 64


def supports_prefix_probe(dialect: str) -> bool:
    return (dialect or "").lower() in PREFIX_PROBE_DIALECTS


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


ColumnSampleExecutable = Union[TextClause, Select]


@dataclass(frozen=True)
class ColumnSamplePlan:
    """Executable sampling intent: SQLAlchemy ``TextClause`` or Core ``Select``."""

    query: ColumnSampleExecutable
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


# Unquoted Oracle identifiers are uppercase and start with a letter (#2094).
_ORACLE_SIMPLE_IDENTIFIER = re.compile(r"^[A-Z][A-Z0-9_$#]*$")


def oracle_sql_identifier(name: Any) -> str:
    """
    Render an Oracle SQL identifier from a discovery/reflection name.

    SQLAlchemy reflects unquoted Oracle objects as lowercase strings; wrapping
    those in double quotes forces case-sensitive resolution and yields ORA-00942.
    Objects created with quoted lowercase identifiers are reflected as
    ``quoted_name(..., quote=True)`` and must keep exact case inside quotes.
    Any other name that is not a simple unquoted identifier (``[A-Z][A-Z0-9_$#]*``)
    is emitted quoted, with embedded ``"`` doubled, so catalog syntax cannot
    splice into the sampling statement.
    """
    raw = str(name)
    safe = raw.replace('"', '""')
    if isinstance(name, quoted_name) and getattr(name, "quote", False):
        return f'"{safe}"'
    if raw != raw.lower() and raw != raw.upper():
        return f'"{safe}"'
    upper = safe.upper()
    if _ORACLE_SIMPLE_IDENTIFIER.fullmatch(upper):
        return upper
    return f'"{safe}"'


def _oracle_table_ref(schema_name: Any, table_name: Any, schema: str | None) -> str:
    if schema:
        return (
            f"{oracle_sql_identifier(schema_name)}.{oracle_sql_identifier(table_name)}"
        )
    return oracle_sql_identifier(table_name)


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
            f'SELECT "{safe_col}" FROM "{safe_table}" '  # nosec B608
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
        _tag_sql(f"SELECT {hint}`{cc}` FROM {t} WHERE `{cc}` IS NOT NULL LIMIT {lim}")  # nosec B608
    )
    return ColumnSamplePlan(
        query=q,
        strategy_label=label,
        audit_notes=audit_notes,
        human_strategy="LIMIT (MySQL)",
    )


def _plan_oracle_column_sample(
    col: Any,
    schema_name: Any,
    table_name: Any,
    schema: str | None,
    lim: int,
    large: bool,
    audit_notes: str,
) -> ColumnSamplePlan:
    label = _with_large_suffix("non_null_rownum_oracle", large)
    t = _oracle_table_ref(schema_name, table_name, schema)
    col_sql = oracle_sql_identifier(col)
    # Inner filter first: ROWNUM on the outer query caps non-null rows only.
    q = text(
        _tag_sql(
            f"SELECT * FROM (SELECT {col_sql} FROM {t} "  # nosec B608
            f"WHERE {col_sql} IS NOT NULL) WHERE ROWNUM <= :lim"
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
            f'SELECT "{safe_col}" FROM ('  # nosec B608
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
    # syntax error -- the connector records ``scan_failures`` (reason
    # ``sampling_error``) and skips detection for that column (#1140). Statement-time bounds for MSSQL
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
            f'SELECT TOP ({lim}) "{safe_col}" FROM {t}{ts_clause} WITH (NOLOCK) '  # nosec B608
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
                f'SELECT "{safe_col}" FROM {t} TABLESAMPLE SYSTEM ({pct_s}) '  # nosec B608
                f'WHERE "{safe_col}" IS NOT NULL LIMIT {lim}'
            )
        )
        human = "TABLESAMPLE SYSTEM (PostgreSQL)"
    else:
        label = _with_large_suffix("non_null_limit_postgresql", large)
        q = text(
            _tag_sql(
                f'SELECT "{safe_col}" FROM {t} WHERE "{safe_col}" IS NOT NULL LIMIT {lim}'  # nosec B608
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
            f'SELECT "{safe_col}" FROM {t} WHERE "{safe_col}" IS NOT NULL LIMIT {lim}'  # nosec B608
        )
    )
    return ColumnSamplePlan(
        query=q,
        strategy_label=label,
        audit_notes=audit_notes,
        human_strategy=human_strategy,
    )


def _clamp_prefix_bytes(prefix_bytes: int) -> int:
    return max(1, min(int(prefix_bytes), DEFAULT_PREFIX_PROBE_BYTES))


class _OracleUtlRawSubstr(GenericFunction):
    type = LargeBinary()
    name = "UTL_RAW.SUBSTR"
    inherit_cache = True


class _OracleDbmsLobSubstr(GenericFunction):
    type = LargeBinary()
    name = "DBMS_LOB.SUBSTR"
    inherit_cache = True


class _OracleUtlRawLength(GenericFunction):
    type = LargeBinary()
    name = "UTL_RAW.LENGTH"
    inherit_cache = True


def _oracle_substr_sql_arg(clause, compiler, **kw) -> str:
    bound = getattr(clause, "value", None)
    if bound is not None and isinstance(bound, (int, float)):
        return str(int(bound))
    return compiler.process(clause, **kw)


@compiles(_OracleUtlRawSubstr, "oracle")
def _compile_oracle_utl_raw_substr(element, compiler, **kw):
    return "%s(%s)" % (
        element.name,
        ", ".join(_oracle_substr_sql_arg(c, compiler, **kw) for c in element.clauses),
    )


@compiles(_OracleDbmsLobSubstr, "oracle")
def _compile_oracle_dbms_lob_substr(element, compiler, **kw):
    return "%s(%s)" % (
        element.name,
        ", ".join(_oracle_substr_sql_arg(c, compiler, **kw) for c in element.clauses),
    )


@compiles(_OracleUtlRawLength, "oracle")
def _compile_oracle_utl_raw_length(element, compiler, **kw):
    return "%s(%s)" % (
        element.name,
        ", ".join(_oracle_substr_sql_arg(c, compiler, **kw) for c in element.clauses),
    )


class _MssqlAnsiQuotedPreparer(mssql_base.MSIdentifierPreparer):
    """SQL Server sampling uses ANSI double quotes (``QUOTED_IDENTIFIER`` ON)."""

    def quote(self, ident, force=None):
        if not isinstance(ident, str):
            ident = str(ident)
        return '"' + ident.replace('"', '""') + '"'


class _MssqlAnsiQuotedDialect(sa_mssql.dialect):
    preparer = _MssqlAnsiQuotedPreparer


_MSSQL_PREFIX_DIALECT = _MssqlAnsiQuotedDialect()


def _quoted_from_safe(safe: str) -> quoted_name:
    return quoted_name(safe.replace('""', '"'), quote=True)


def _mysql_quoted_from_safe(safe: str) -> quoted_name:
    """MySQL column/table names keep dialect-escaped ``safe_*`` (ANSI-style doubling)."""
    return quoted_name(safe, quote=True)


def _oracle_quoted_from_catalog(name: Any) -> quoted_name:
    rendered = oracle_sql_identifier(name)
    if rendered.startswith('"'):
        inner = rendered[1:-1].replace('""', '"')
        return quoted_name(inner, quote=True)
    return quoted_name(rendered, quote=False)


def _sqlalchemy_sampling_dialect(dialect: str):
    d = (dialect or "").lower()
    if d == "sqlite":
        return sa_sqlite.dialect()
    if d in ("postgresql", "postgres"):
        return sa_postgresql.dialect()
    if d in ("mysql", "mariadb"):
        return sa_mysql.dialect()
    if d in ("mssql", "microsoft sql server"):
        return _MSSQL_PREFIX_DIALECT
    if d == "oracle":
        return sa_oracle.dialect()
    raise ValueError(f"unsupported sampling dialect {dialect!r}")


def _dbapi_sampling_dialect(dialect: str):
    d = (dialect or "").lower()
    if d in ("postgresql", "postgres"):
        from sqlalchemy.dialects.postgresql import psycopg2 as pg

        return pg.dialect()
    if d in ("mysql", "mariadb"):
        from sqlalchemy.dialects.mysql import pymysql as pym

        return pym.dialect()
    return _sqlalchemy_sampling_dialect(dialect)


def _prefix_probe_compliance(stmt: Select) -> Select:
    """Select probes get the compliance leading comment at execute time (#2373 B4)."""
    return stmt


def _compliance_label_on_driver(statement: str) -> bool:
    return statement.lstrip().startswith(_COMPLIANCE_SCAN_LEADING.strip())


def _prepend_compliance_label_for_driver_sql(
    _conn,
    _cursor,
    statement,
    parameters,
    _context,
    _executemany,
):
    if isinstance(statement, bytes):
        text_stmt = statement.decode("utf-8", errors="replace")
    else:
        text_stmt = str(statement)
    if _compliance_label_on_driver(text_stmt):
        return statement, parameters
    return f"{_COMPLIANCE_SCAN_LEADING.strip()}\n{text_stmt}", parameters


def _unde_double_percent_in_quoted_identifiers(sql: str) -> str:
    """Undo SQLAlchemy pyformat ``%%`` inside quoted identifiers for audit parity with ``text()`` SQL."""

    def _fix_double(m: re.Match[str]) -> str:
        return m.group(0).replace("%%", "%")

    s = re.sub(r'"(?:[^"]|"")*"', _fix_double, sql)
    return re.sub(r"`(?:``|[^`])*`", _fix_double, s)


def compile_column_sample_plan_sql(
    plan: ColumnSamplePlan,
    dialect: str,
    *,
    dbapi: bool = False,
) -> str:
    """Render plan SQL for audit/tests; optional DBAPI dialect (psycopg2/pymysql)."""
    q = plan.query
    if isinstance(q, TextClause):
        return str(q)
    if not isinstance(q, Select):
        raise TypeError(f"unexpected query type {type(q)!r}")
    d = (
        _dbapi_sampling_dialect(dialect)
        if dbapi
        else _sqlalchemy_sampling_dialect(dialect)
    )
    compile_kw: dict[str, object] = {}
    dlow = (dialect or "").lower()
    if dlow == "oracle" and plan.strategy_label.startswith("prefix_probe_oracle"):
        compile_kw = {}
    else:
        compile_kw["literal_binds"] = True
    body = " ".join(str(q.compile(dialect=d, compile_kwargs=compile_kw)).split())
    if body.endswith(" OFFSET 0"):
        body = body[: -len(" OFFSET 0")]
    body = _unde_double_percent_in_quoted_identifiers(body)
    return _tag_sql(body)


def _execute_select_with_compliance_label(connection, q: Select):
    """Run a Core ``Select`` with the DBA grep leading comment on the driver SQL."""
    hook_target = None
    for target in (connection, getattr(connection, "engine", None)):
        if target is None:
            continue
        try:
            event.listen(
                target,
                "before_cursor_execute",
                _prepend_compliance_label_for_driver_sql,
                retval=True,
            )
            hook_target = target
            break
        except sa_exc.InvalidRequestError:
            continue
    if hook_target is not None:
        try:
            return connection.execute(q).fetchall()
        finally:
            event.remove(
                hook_target,
                "before_cursor_execute",
                _prepend_compliance_label_for_driver_sql,
            )
    # SQLAlchemy MockEngine: no cursor events — compile once and prepend (tests only).
    compiled = q.compile(dialect=connection.dialect)
    sql = " ".join(str(compiled).split())
    if not _compliance_label_on_driver(sql):
        sql = f"{_COMPLIANCE_SCAN_LEADING.strip()}\n{sql}"
    sql = _unde_double_percent_in_quoted_identifiers(sql)
    result = connection.execute(text(sql), dict(compiled.params))
    if result is None:
        return []
    return result.fetchall()


def execute_column_sample_plan(connection, plan: ColumnSamplePlan):
    """Run a column sample plan (``TextClause`` or Core ``Select``)."""
    q = plan.query
    if isinstance(q, Select):
        return _execute_select_with_compliance_label(connection, q)
    return connection.execute(q).fetchall()


def _mssql_prefix_table(
    safe_schema: str, safe_table: str, schema: str | None, safe_col: str
) -> Table:
    meta = MetaData()
    col_name = safe_col.replace('""', '"')
    tbl_name = safe_table.replace('""', '"')
    schema_name = safe_schema.replace('""', '"') if schema else None
    tbl_col = Column(col_name, String, quote=True)
    return Table(
        tbl_name,
        meta,
        tbl_col,
        schema=schema_name,
        quote=True,
        quote_schema=bool(schema),
    )


def _plan_prefix_sqlite(
    safe_col: str, safe_table: str, lim: int, prefix_bytes: int
) -> ColumnSamplePlan:
    pb = _clamp_prefix_bytes(prefix_bytes)
    col_q = _quoted_from_safe(safe_col)
    col_sel = column(col_q)
    col_where = column(col_q)
    tbl = table(_quoted_from_safe(safe_table))
    stmt = _prefix_probe_compliance(
        select(func.substr(col_sel, 1, pb))
        .select_from(tbl)
        .where(col_where.isnot(None))
        .limit(lim)
    )
    return ColumnSamplePlan(
        query=stmt,
        strategy_label="prefix_probe_sqlite",
        human_strategy="SUBSTR prefix (SQLite)",
    )


def _plan_prefix_postgresql(
    safe_col: str,
    safe_schema: str,
    safe_table: str,
    schema: str | None,
    lim: int,
    prefix_bytes: int,
) -> ColumnSamplePlan:
    pb = _clamp_prefix_bytes(prefix_bytes)
    col_q = _quoted_from_safe(safe_col)
    col_sel = column(col_q)
    col_where = column(col_q)
    tbl = table(
        _quoted_from_safe(safe_table),
        schema=_quoted_from_safe(safe_schema) if schema else None,
    )
    stmt = _prefix_probe_compliance(
        select(func.substring(col_sel, 1, pb))
        .select_from(tbl)
        .where(col_where.isnot(None))
        .limit(lim)
    )
    return ColumnSamplePlan(
        query=stmt,
        strategy_label="prefix_probe_postgresql",
        human_strategy="SUBSTRING prefix (PostgreSQL)",
    )


def _plan_prefix_mysql(
    safe_col: str,
    safe_schema: str,
    safe_table: str,
    schema: str | None,
    lim: int,
    prefix_bytes: int,
    statement_timeout_ms: int | None,
) -> ColumnSamplePlan:
    pb = _clamp_prefix_bytes(prefix_bytes)
    col_q = _mysql_quoted_from_safe(safe_col)
    col_sel = column(col_q)
    col_where = column(col_q)
    tbl = table(
        _mysql_quoted_from_safe(safe_table),
        schema=_mysql_quoted_from_safe(safe_schema) if schema else None,
    )
    stmt = (
        select(func.substring(col_sel, 1, pb))
        .select_from(tbl)
        .where(col_where.isnot(None))
        .limit(lim)
    )
    if statement_timeout_ms and statement_timeout_ms > 0:
        ms = int(statement_timeout_ms)
        stmt = stmt.prefix_with(
            "/*+ MAX_EXECUTION_TIME(" + str(ms) + ") */", dialect="mysql"
        )
    stmt = _prefix_probe_compliance(stmt)
    return ColumnSamplePlan(
        query=stmt,
        strategy_label="prefix_probe_mysql",
        human_strategy="SUBSTRING prefix (MySQL)",
    )


def _plan_prefix_mssql(
    safe_col: str,
    safe_schema: str,
    safe_table: str,
    schema: str | None,
    lim: int,
    prefix_bytes: int,
) -> ColumnSamplePlan:
    pb = _clamp_prefix_bytes(prefix_bytes)
    tbl = _mssql_prefix_table(safe_schema, safe_table, schema, safe_col)
    col_q = _quoted_from_safe(safe_col)
    col_sel = column(col_q)
    col_where = column(col_q)
    stmt = _prefix_probe_compliance(
        select(func.substring(col_sel, 1, pb))
        .select_from(tbl)
        .where(col_where.isnot(None))
        .limit(lim)
        .with_hint(tbl, "WITH (NOLOCK)", dialect_name="mssql")
    )
    return ColumnSamplePlan(
        query=stmt,
        strategy_label="prefix_probe_mssql",
        human_strategy="SUBSTRING prefix (SQL Server)",
    )


def _plan_prefix_oracle(
    col: Any,
    schema_name: Any,
    table_name: Any,
    schema: str | None,
    lim: int,
    prefix_bytes: int,
    *,
    oracle_lob: bool,
) -> ColumnSamplePlan:
    pb = _clamp_prefix_bytes(prefix_bytes)
    col_ident = literal_column(oracle_sql_identifier(col))
    tbl = table(
        _oracle_quoted_from_catalog(table_name),
        schema=_oracle_quoted_from_catalog(schema_name) if schema else None,
    )
    if oracle_lob:
        probe_expr = _OracleDbmsLobSubstr(col_ident, pb, 1)
        label = "prefix_probe_oracle_lob"
        human = "LOB SUBSTR prefix (Oracle)"
    else:
        # RAW columns: read only the first bytes, never the whole column (#2370 S11).
        pb_param = bindparam("prefix_bytes", pb)
        raw_len = func.least(_OracleUtlRawLength(col_ident), pb_param)
        probe_expr = _OracleUtlRawSubstr(col_ident, 1, raw_len)
        label = "prefix_probe_oracle_raw"
        human = "RAW prefix (Oracle)"
    inner = select(probe_expr).select_from(tbl).where(col_ident.isnot(None))
    stmt = _prefix_probe_compliance(
        select(literal_column("*"))
        .select_from(inner.subquery())
        .where(literal_column("ROWNUM") <= bindparam("lim", lim))
    )
    return ColumnSamplePlan(
        query=stmt,
        strategy_label=label,
        human_strategy=human,
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
            f'SELECT "{safe_col}" FROM {t} WHERE "{safe_col}" IS NOT NULL LIMIT {lim}'  # nosec B608
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
        raw_col: Any | None = None,
        raw_table: Any | None = None,
        raw_schema: Any | None = None,
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
                raw_col if raw_col is not None else safe_col,
                raw_schema if raw_schema is not None else safe_schema,
                raw_table if raw_table is not None else safe_table,
                schema,
                lim,
                large,
                audit_notes,
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

    @staticmethod
    def build_column_prefix_sample(
        dialect: str,
        *,
        safe_col: str,
        safe_table: str,
        safe_schema: str,
        schema: str | None,
        limit: int,
        prefix_bytes: int = DEFAULT_PREFIX_PROBE_BYTES,
        oracle_lob: bool = True,
        statement_timeout_ms: int | None = None,
        raw_col: Any | None = None,
        raw_table: Any | None = None,
        raw_schema: Any | None = None,
    ) -> ColumnSamplePlan:
        d = (dialect or "").lower()
        if not supports_prefix_probe(d):
            raise ValueError(f"prefix probe not supported for dialect {d!r}")
        lim = _clamp_limit(limit)
        if d == "sqlite":
            return _plan_prefix_sqlite(safe_col, safe_table, lim, prefix_bytes)
        if d in ("mysql", "mariadb"):
            return _plan_prefix_mysql(
                safe_col,
                safe_schema,
                safe_table,
                schema,
                lim,
                prefix_bytes,
                statement_timeout_ms,
            )
        if d == "oracle":
            return _plan_prefix_oracle(
                raw_col if raw_col is not None else safe_col,
                raw_schema if raw_schema is not None else safe_schema,
                raw_table if raw_table is not None else safe_table,
                schema,
                lim,
                prefix_bytes,
                oracle_lob=oracle_lob,
            )
        if d in ("mssql", "microsoft sql server"):
            return _plan_prefix_mssql(
                safe_col, safe_schema, safe_table, schema, lim, prefix_bytes
            )
        if d in ("postgresql", "postgres"):
            return _plan_prefix_postgresql(
                safe_col, safe_schema, safe_table, schema, lim, prefix_bytes
            )
        raise ValueError(f"prefix probe not supported for dialect {d!r}")


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
        raw_col: Any | None = None,
        raw_table: Any | None = None,
        raw_schema: Any | None = None,
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
            raw_col=raw_col,
            raw_table=raw_table,
            raw_schema=raw_schema,
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
    raw_col: Any | None = None,
    raw_table: Any | None = None,
    raw_schema: Any | None = None,
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
        raw_col=raw_col,
        raw_table=raw_table,
        raw_schema=raw_schema,
    )
    d = (dialect or "").lower()
    if d == "oracle":
        lim_v = _clamp_limit(limit)
        col = raw_col if raw_col is not None else safe_col
        sch = raw_schema if raw_schema is not None else safe_schema
        tbl = raw_table if raw_table is not None else safe_table
        t = _oracle_table_ref(sch, tbl, schema)
        col_sql = oracle_sql_identifier(col)
        sql = _tag_sql(
            f"SELECT * FROM (SELECT {col_sql} FROM {t} "  # nosec B608
            f"WHERE {col_sql} IS NOT NULL) WHERE ROWNUM <= {lim_v}"
        )
        human = plan.human_strategy or plan.strategy_label
        return sql, {}, plan.strategy_label, plan.audit_notes, human
    compiled = plan.query.compile(compile_kwargs={"literal_binds": True})
    human = plan.human_strategy or plan.strategy_label
    return str(compiled), {}, plan.strategy_label, plan.audit_notes, human
