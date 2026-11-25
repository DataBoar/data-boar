"""Tests for SQL column sampling helpers (non-null filter, env cap, dialect SQL shape)."""

import re

import pytest
from sqlalchemy.sql.elements import quoted_name

from connectors.sql_sampling import (
    PREFIX_PROBE_DIALECTS,
    SamplingManager,
    SqlColumnSampleQueryBuilder,
    TableSamplingMetadata,
    _ansi_quoted_table,
    _mysql_table_ref,
    _oracle_table_ref,
    column_sample_sql_for_cursor,
    oracle_sql_identifier,
    resolve_sql_sample_limit,
    resolve_statement_timeout_ms_for_sampling,
    supports_prefix_probe,
)

_COMPLIANCE_PREFIX = "-- Data Boar Compliance Scan\n"


def _sql_body(plan) -> str:
    s = str(plan.query)
    assert s.startswith(_COMPLIANCE_PREFIX)
    return s[len(_COMPLIANCE_PREFIX) :]


def test_resolve_sql_sample_limit_uses_config_when_env_unset():
    assert resolve_sql_sample_limit(7) == 7
    assert resolve_sql_sample_limit(1) == 1


def test_resolve_sql_sample_limit_env_override(monkeypatch):
    monkeypatch.setenv("DATA_BOAR_SQL_SAMPLE_LIMIT", "3")
    assert resolve_sql_sample_limit(99) == 3


def test_resolve_sql_sample_limit_env_invalid_ignored(monkeypatch):
    monkeypatch.setenv("DATA_BOAR_SQL_SAMPLE_LIMIT", "not-int")
    assert resolve_sql_sample_limit(8) == 8


def test_resolve_sql_sample_limit_clamped(monkeypatch):
    monkeypatch.setenv("DATA_BOAR_SQL_SAMPLE_LIMIT", "0")
    assert resolve_sql_sample_limit(5) == 1
    monkeypatch.setenv("DATA_BOAR_SQL_SAMPLE_LIMIT", "999999")
    assert resolve_sql_sample_limit(5) == 10_000


def test_build_sqlite_contains_is_not_null():
    q = SqlColumnSampleQueryBuilder.build(
        "sqlite",
        safe_col="c",
        safe_table="t",
        safe_schema="",
        schema=None,
        limit=5,
    )
    s = str(q)
    assert s.startswith("-- Data Boar Compliance Scan\n")
    assert "IS NOT NULL" in s
    assert "LIMIT 5" in s


def test_build_postgresql_contains_is_not_null():
    q = SqlColumnSampleQueryBuilder.build(
        "postgresql",
        safe_col="c",
        safe_table="tbl",
        safe_schema="pub",
        schema="pub",
        limit=10,
    )
    s = str(q)
    assert '"pub"."tbl"' in s
    assert '"c" IS NOT NULL' in s
    assert "LIMIT 10" in s


def test_build_oracle_subquery_rownum():
    q = SqlColumnSampleQueryBuilder.build(
        "oracle",
        safe_col="C",
        safe_table="T",
        safe_schema="S",
        schema="S",
        limit=4,
    )
    s = str(q)
    assert "IS NOT NULL" in s
    assert "ROWNUM" in s
    assert "S.T" in s
    assert '"' not in s
    assert q.compile().params.get("lim") == 4


def test_oracle_sql_identifier_reflected_lowercase_unquoted():
    assert oracle_sql_identifier("lab_customers") == "LAB_CUSTOMERS"
    assert oracle_sql_identifier("id") == "ID"
    assert oracle_sql_identifier("LAB_CUSTOMERS") == "LAB_CUSTOMERS"


def test_oracle_sql_identifier_quoted_lowercase_preserved():
    qn = quoted_name("lab_customers", quote=True)
    assert oracle_sql_identifier(qn) == '"lab_customers"'


def test_oracle_sql_identifier_mixed_case_quoted():
    assert oracle_sql_identifier("Lab_Customers") == '"Lab_Customers"'


def test_oracle_sql_identifier_quotes_uppercase_names_with_sql_syntax():
    """#2094: quote catalog names that are not a simple unquoted Oracle identifier."""
    assert oracle_sql_identifier("ATTACKER.EVIL()") == '"ATTACKER.EVIL()"'
    assert oracle_sql_identifier('SAY "HI"') == '"SAY ""HI"""'
    assert oracle_sql_identifier("COL$ID") == "COL$ID"
    assert oracle_sql_identifier("A#1") == "A#1"


def test_build_oracle_reflected_lowercase_emits_unquoted_upper():
    """Regression #1370: quoted lowercase breaks ORA-00942 on default Oracle objects."""
    q = SqlColumnSampleQueryBuilder.build(
        "oracle",
        safe_col="id",
        safe_table="lab_customers",
        safe_schema="lab_smoke",
        schema="lab_smoke",
        limit=4,
    )
    s = str(q)
    assert '"lab_smoke"' not in s
    assert '"lab_customers"' not in s
    assert '"id"' not in s
    assert "LAB_SMOKE.LAB_CUSTOMERS" in s
    assert "ID IS NOT NULL" in s


def test_build_oracle_quoted_lowercase_table_preserved():
    qn_table = quoted_name("lab_customers", quote=True)
    q = SqlColumnSampleQueryBuilder.build(
        "oracle",
        safe_col="national_id",
        safe_table="lab_customers",
        safe_schema="lab_smoke",
        schema="lab_smoke",
        limit=2,
        raw_table=qn_table,
    )
    s = str(q)
    assert '"lab_customers"' in s
    assert "LAB_SMOKE" in s
    assert "NATIONAL_ID IS NOT NULL" in s


def test_build_mssql_top_nolock():
    q = SqlColumnSampleQueryBuilder.build(
        "mssql",
        safe_col="c",
        safe_table="t",
        safe_schema="dbo",
        schema="dbo",
        limit=6,
    )
    s = str(q)
    assert s.startswith("-- Data Boar Compliance Scan\n")
    assert "TOP (6)" in s
    assert "WITH (NOLOCK)" in s
    assert "IS NOT NULL" in s
    assert "OPTION (MAX_EXECUTION_TIME" not in s


def test_build_mssql_never_emits_option_max_execution_time():
    """
    Regression: SQL Server has no ``OPTION (MAX_EXECUTION_TIME = N)`` query
    hint (MAX_EXECUTION_TIME is MySQL-only). Emitting it produced syntax
    errors swallowed by the connector and silent zero-finding scans on every
    MSSQL target. The MSSQL plan must remain TOP + NOLOCK + IS NOT NULL even
    when an explicit per-target timeout is set.
    """
    q = SqlColumnSampleQueryBuilder.build(
        "mssql",
        safe_col="c",
        safe_table="t",
        safe_schema="dbo",
        schema="dbo",
        limit=3,
        statement_timeout_ms=2500,
    )
    s = str(q)
    assert "OPTION" not in s
    assert "MAX_EXECUTION_TIME" not in s
    assert "TOP (3)" in s
    assert "WITH (NOLOCK)" in s
    assert '"c" IS NOT NULL' in s


def test_build_mssql_tablesample_when_large(monkeypatch):
    monkeypatch.setenv("DATA_BOAR_MSSQL_TABLESAMPLE_SYSTEM_PERCENT", "7")
    meta = TableSamplingMetadata(estimated_row_count=2_000_000)
    plan = SamplingManager.build_column_sample(
        "mssql",
        safe_col="c",
        safe_table="t",
        safe_schema="dbo",
        schema="dbo",
        limit=4,
        table_metadata=meta,
        statement_timeout_ms=None,
    )
    sql = str(plan.query)
    assert "TABLESAMPLE SYSTEM (7 PERCENT)" in sql
    assert "WITH (NOLOCK)" in sql


def test_resolve_statement_timeout_env(monkeypatch):
    monkeypatch.setenv("DATA_BOAR_SAMPLE_STATEMENT_TIMEOUT_MS", "3200")
    assert resolve_statement_timeout_ms_for_sampling(None) == 3200
    monkeypatch.setenv("DATA_BOAR_SAMPLE_STATEMENT_TIMEOUT_MS", "0")
    assert resolve_statement_timeout_ms_for_sampling(None) is None


def test_build_mysql_backticks():
    q = SqlColumnSampleQueryBuilder.build(
        "mysql",
        safe_col="phone",
        safe_table="users",
        safe_schema="app",
        schema="app",
        limit=2,
    )
    s = str(q)
    assert "`app`.`users`" in s
    assert "`phone` IS NOT NULL" in s


def test_sampling_manager_strategy_label_postgresql():
    plan = SamplingManager.build_column_sample(
        "postgresql",
        safe_col="c",
        safe_table="t",
        safe_schema="pub",
        schema="pub",
        limit=3,
        table_metadata=None,
    )
    assert plan.strategy_label == "non_null_limit_postgresql"
    assert "IS NOT NULL" in str(plan.query)


def test_sampling_manager_large_table_metadata_suffix_postgres_tablesample():
    meta = TableSamplingMetadata(estimated_row_count=2_000_000)
    plan = SamplingManager.build_column_sample(
        "postgresql",
        safe_col="c",
        safe_table="t",
        safe_schema="pub",
        schema="pub",
        limit=3,
        table_metadata=meta,
    )
    assert (
        plan.strategy_label
        == "non_null_tablesample_system_postgresql_large_table_metadata"
    )
    assert "TABLESAMPLE SYSTEM" in str(plan.query)
    assert "LIMIT 3" in str(plan.query)
    assert "2000000" in plan.audit_notes


def test_sampling_manager_postgres_tablesample_percent_env(monkeypatch):
    monkeypatch.setenv("DATA_BOAR_PG_TABLESAMPLE_SYSTEM_PERCENT", "2.5")
    meta = TableSamplingMetadata(estimated_row_count=2_000_000)
    plan = SamplingManager.build_column_sample(
        "postgresql",
        safe_col="c",
        safe_table="t",
        safe_schema="pub",
        schema="pub",
        limit=5,
        table_metadata=meta,
    )
    assert "TABLESAMPLE SYSTEM (2.5)" in str(plan.query)


def test_column_sample_sql_for_cursor_snowflake():
    sql, binds, label, _notes, human = column_sample_sql_for_cursor(
        "snowflake",
        safe_col="c",
        safe_table="t",
        safe_schema="pub",
        schema="pub",
        limit=7,
        table_metadata=None,
    )
    assert binds == {}
    assert label == "non_null_sample_rows_snowflake"
    assert human == "SAMPLE ROWS (Snowflake)"
    assert "SAMPLE (7 ROWS)" in sql
    assert '"c" IS NOT NULL' in sql


def test_column_sample_sql_for_cursor_oracle_literal_rownum():
    sql, binds, label, _notes, human = column_sample_sql_for_cursor(
        "oracle",
        safe_col="C",
        safe_table="T",
        safe_schema="S",
        schema="S",
        limit=5,
        table_metadata=None,
    )
    assert binds == {}
    assert sql.startswith("-- Data Boar Compliance Scan\n")
    assert "ROWNUM" in sql
    assert "<= 5" in sql
    assert "S.T" in sql
    assert '"s"' not in sql
    assert label == "non_null_rownum_oracle"
    assert human == "ROWNUM inner filter (Oracle)"


def test_d2362_10_prefix_probe_dialects_frozen():
    # D2362-10: dialects with prefix probe support
    assert "postgresql" in PREFIX_PROBE_DIALECTS
    assert "mysql" in PREFIX_PROBE_DIALECTS
    assert supports_prefix_probe("PostgreSQL")
    assert supports_prefix_probe("mysql")
    assert not supports_prefix_probe("snowflake")
    assert not supports_prefix_probe("duckdb")


def test_d2362_11_prefix_probe_sqlite_postgres_mysql():
    # D2362-11: prefix sampling SQL shape (body without compliance tag)
    p_sqlite = SamplingManager.build_column_prefix_sample(
        "sqlite",
        safe_col="col_blob",
        safe_table="t_img",
        safe_schema="",
        schema=None,
        limit=5,
        prefix_bytes=64,
    )
    assert p_sqlite.strategy_label == "prefix_probe_sqlite"
    body = _sql_body(p_sqlite)
    assert 'substr("col_blob", 1, 64)' in body
    assert '"t_img"' in body
    assert "IS NOT NULL" in body
    assert "LIMIT 5" in body

    p_pg = SamplingManager.build_column_prefix_sample(
        "postgresql",
        safe_col="c",
        safe_table="t",
        safe_schema="pub",
        schema="pub",
        limit=5,
        prefix_bytes=64,
    )
    assert p_pg.strategy_label == "prefix_probe_postgresql"
    body_pg = _sql_body(p_pg)
    assert 'SUBSTRING("c" FROM 1 FOR 64)' in body_pg
    assert '"pub"."t"' in body_pg

    p_my = SamplingManager.build_column_prefix_sample(
        "mysql",
        safe_col="c",
        safe_table="t",
        safe_schema="db",
        schema="db",
        limit=5,
        prefix_bytes=64,
    )
    body_my = _sql_body(p_my)
    assert "substring(`c`, 1, 64)" in body_my
    assert "`db`.`t`" in body_my


def test_d2362_11_quoted_identifiers_match_column_sample():
    # D2362-11: prefix SQL cites identifiers the same way as build_column_sample
    tricky = 'a"b'
    safe_col = tricky.replace('"', '""')
    p_pref = SamplingManager.build_column_prefix_sample(
        "sqlite",
        safe_col=safe_col,
        safe_table="t",
        safe_schema="",
        schema=None,
        limit=5,
    )
    p_full = SamplingManager.build_column_sample(
        "sqlite",
        safe_col=safe_col,
        safe_table="t",
        safe_schema="",
        schema=None,
        limit=5,
    )
    where_pref = _sql_body(p_pref).split(" WHERE ", 1)[1]
    where_full = _sql_body(p_full).split(" WHERE ", 1)[1]
    assert where_pref == where_full

    p_pg = SamplingManager.build_column_prefix_sample(
        "postgresql",
        safe_col=safe_col,
        safe_table="t",
        safe_schema="pub",
        schema="pub",
        limit=5,
    )
    full_pg = SamplingManager.build_column_sample(
        "postgresql",
        safe_col=safe_col,
        safe_table="t",
        safe_schema="pub",
        schema="pub",
        limit=5,
    )
    assert f'"{safe_col}"' in _sql_body(p_pg)
    assert f'"{safe_col}"' in str(full_pg.query)


def test_d2362_12_duckdb_not_supported():
    # D2362-12
    assert supports_prefix_probe("duckdb") is False
    with pytest.raises(ValueError, match="prefix probe not supported"):
        SamplingManager.build_column_prefix_sample(
            "duckdb",
            safe_col="c",
            safe_table="t",
            safe_schema="",
            schema=None,
            limit=5,
        )


def test_d2362_12_prefix_probe_mssql_oracle():
    # D2362-12: MSSQL SUBSTRING + TOP; Oracle ROWNUM binds
    p_ms = SamplingManager.build_column_prefix_sample(
        "mssql",
        safe_col="c",
        safe_table="t",
        safe_schema="dbo",
        schema="dbo",
        limit=5,
        prefix_bytes=64,
    )
    body_ms = _sql_body(p_ms)
    assert body_ms.startswith("SELECT TOP 5 substring(")
    assert "WITH (NOLOCK)" in body_ms
    assert ", 64)" in body_ms

    p_ora = SamplingManager.build_column_prefix_sample(
        "oracle",
        safe_col="BLOBCOL",
        safe_table="T",
        safe_schema="S",
        schema="S",
        limit=5,
        prefix_bytes=64,
    )
    body_ora = _sql_body(p_ora)
    assert "ROWNUM <= :lim" in body_ora
    compiled = p_ora.query.compile()
    assert compiled.params.get("lim") == 5


def test_d2362_12b_oracle_lob_and_raw_labels():
    p_lob = SamplingManager.build_column_prefix_sample(
        "oracle",
        safe_col="BLOBCOL",
        safe_table="T",
        safe_schema="S",
        schema="S",
        limit=5,
        prefix_bytes=64,
        oracle_lob=True,
    )
    assert p_lob.strategy_label == "prefix_probe_oracle_lob"
    assert "DBMS_LOB.SUBSTR" in _sql_body(p_lob)
    p_raw = SamplingManager.build_column_prefix_sample(
        "oracle",
        safe_col="RAWCOL",
        safe_table="T",
        safe_schema="S",
        schema="S",
        limit=5,
        oracle_lob=False,
    )
    assert p_raw.strategy_label == "prefix_probe_oracle_raw"
    assert "DBMS_LOB.SUBSTR" not in _sql_body(p_raw)
    # #2370 S11: the RAW path reads only the first bytes too, never the whole column.
    assert "UTL_RAW.SUBSTR" in _sql_body(p_raw)
    assert ", 1, 64)" in _sql_body(p_raw)


def _unquoted_sql_fragments(sql: str) -> str:
    """Remove dialect-quoted identifiers so hostile names cannot hide in literals."""
    s = sql
    s = re.sub(r'"(?:[^"]|"")*"', " ", s)
    s = re.sub(r"`(?:``|[^`])*`", " ", s)
    return s


def _where_col_token(body: str, dialect: str) -> str:
    d = dialect.lower()
    pat_is_null = r'WHERE ("(?:[^"]|"")+"|\S+) IS NOT NULL'
    if d in ("mysql", "mariadb"):
        m = re.search(r"WHERE (`(?:``|[^`])+`) IS NOT NULL", body, re.IGNORECASE)
        assert m, f"no WHERE col token in: {body!r}"
        return m.group(1)
    if d == "oracle":
        matches = list(re.finditer(pat_is_null, body, re.IGNORECASE))
        assert matches, f"no WHERE col token in: {body!r}"
        return matches[0].group(1)
    m = re.search(r'WHERE ("(?:[^"]|"")+") IS NOT NULL', body, re.IGNORECASE)
    assert m, f"no WHERE col token in: {body!r}"
    return m.group(1)


def _expected_table_ref(
    dialect: str,
    *,
    safe_schema: str,
    safe_table: str,
    schema: str | None,
    table_raw: str,
) -> str:
    if dialect in ("mysql", "mariadb"):
        return _mysql_table_ref(safe_schema, safe_table, schema)
    if dialect == "oracle":
        schema_key = schema or safe_schema
        return _oracle_table_ref(schema_key, table_raw, schema)
    return _ansi_quoted_table(safe_schema, safe_table, schema)


def _oracle_kwargs(col_raw: str, table_raw: str, schema: str) -> dict:
    return {
        "raw_col": col_raw,
        "raw_table": table_raw,
        "raw_schema": schema,
    }


_PREFIX_HOSTILE_DIALECTS = (
    "sqlite",
    "postgresql",
    "mysql",
    "mariadb",
    "mssql",
    "oracle",
)

_PREFIX_HOSTILE_IDENTIFIERS = (
    ('a"b', "t1"),
    ("a'b", "t2"),
    ("a;b", "t3"),
    ("col space", "tb space"),
    ("select", "order"),
    ("SeLeCt", "TbLe"),
)


@pytest.mark.parametrize("dialect", _PREFIX_HOSTILE_DIALECTS)
@pytest.mark.parametrize("col_raw,table_raw", _PREFIX_HOSTILE_IDENTIFIERS)
def test_d2362_prefix_probe_hostile_identifiers_match_sampler(
    dialect: str, col_raw: str, table_raw: str
):
    # Prefix-read SQL must quote identifiers like build_column_sample (no raw splice).
    schema = "pub" if dialect != "sqlite" else None
    safe_col = col_raw.replace('"', '""')
    safe_table = table_raw.replace('"', '""')
    safe_schema = (schema or "").replace('"', '""')
    extra = (
        _oracle_kwargs(col_raw, table_raw, schema or "") if dialect == "oracle" else {}
    )
    pref = SamplingManager.build_column_prefix_sample(
        dialect,
        safe_col=safe_col,
        safe_table=safe_table,
        safe_schema=safe_schema,
        schema=schema,
        limit=4,
        prefix_bytes=32,
        **extra,
    )
    full = SamplingManager.build_column_sample(
        dialect,
        safe_col=safe_col,
        safe_table=safe_table,
        safe_schema=safe_schema,
        schema=schema,
        limit=4,
        **extra,
    )
    body_pref = _sql_body(pref)
    body_full = _sql_body(full)
    assert _where_col_token(body_pref, dialect) == _where_col_token(body_full, dialect)
    tref = _expected_table_ref(
        dialect,
        safe_schema=safe_schema,
        safe_table=safe_table,
        schema=schema,
        table_raw=table_raw,
    )
    assert tref in body_pref
    assert tref in body_full
    if dialect == "oracle":
        col_ref = oracle_sql_identifier(col_raw)
        assert col_ref in body_pref
        assert col_ref in body_full
    unq = _unquoted_sql_fragments(body_pref)
    assert col_raw not in unq
    assert table_raw not in unq
    if dialect == "sqlite":
        assert (
            f'substr("{safe_col}"' in body_pref or f'substr("{safe_col}",' in body_pref
        )
