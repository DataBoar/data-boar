"""Tests for SQL column sampling helpers (non-null filter, env cap, dialect SQL shape)."""

from sqlalchemy.sql.elements import quoted_name

from connectors.sql_sampling import (
    SamplingManager,
    SqlColumnSampleQueryBuilder,
    TableSamplingMetadata,
    column_sample_sql_for_cursor,
    oracle_sql_identifier,
    resolve_sql_sample_limit,
    resolve_statement_timeout_ms_for_sampling,
)


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
