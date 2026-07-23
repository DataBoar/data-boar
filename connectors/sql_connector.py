"""
SQL connector: connect via SQLAlchemy, discover schemas/tables/columns, sample rows (no raw storage),
run detector, save_finding. Supports PostgreSQL, MySQL, MariaDB, SQLite, MSSQL, Oracle via driver.
"""

from collections.abc import Set
import json
import os
import time
from typing import Any
from urllib.parse import quote

from sqlalchemy import create_engine, inspect, text

from connectors.sql_driver_deps import ensure_sql_driver_available
from connectors.sql_sampling import (
    SamplingManager,
    TableSamplingMetadata,
    resolve_sql_sample_limit,
)
from core.connector_registry import register
from core.sampling import SamplingPolicy
from core.suggested_review import (
    SUGGESTED_REVIEW_PATTERN,
    augment_low_id_like_for_persist,
)

# Driver to SQLAlchemy drivername mapping (driver in config may be e.g. postgresql+psycopg2)
DRIVER_MAP = {
    "postgresql": "postgresql+psycopg2",
    "mysql": "mysql+pymysql",
    "mariadb": "mariadb+mariadbconnector",
    "sqlite": "sqlite",
    "mssql": "mssql+pymssql",
    "oracle": "oracle+oracledb",
}

# Oracle system schemas to skip when discovering (credential sees only accessible schemas; skip Oracle-maintained)
ORACLE_SYSTEM_SCHEMAS = frozenset(
    {
        "SYS",
        "SYSTEM",
        "OUTLN",
        "DBSNMP",
        "DIP",
        "ORACLE_OCM",
        "APPQOSSYS",
        "WMSYS",
        "EXFSYS",
        "CTXSYS",
        "XDB",
        "ANONYMOUS",
        "MDSYS",
        "OLAPSYS",
        "ORDSYS",
        "ORDDATA",
        "SI_INFORMTN_SCHEMA",
        "LBACSYS",
        "DVF",
        "DVSYS",
        "GSMADMIN_INTERNAL",
        "OJVMSYS",
        "GSMCATUSER",
        "GSMUSER",
        "MDDATA",
        "REMOTE_SCHEDULER_AGENT",
        "DBSFWUSER",
        # 12c+/19c/23c Oracle-maintained (issue #1315; AUDSYS = unified audit trail noise)
        "AUDSYS",
        "SYS$UMF",
        "GGSYS",
        "SYSBACKUP",
        "SYSDG",
        "SYSKM",
        "SYSRAC",
        "PDBADMIN",
    }
)

_DEFAULT_SKIP_SCHEMAS: frozenset[str] = frozenset(
    {
        "information_schema",
        "sys",
        "pg_catalog",
        "performance_schema",
        # MySQL system schema (catalog noise in PoCs)
        "mysql",
    }
)

# SQL Server: system / pseudo-schemas (NOLOCK sampling targets user tables only).
_MSSQL_SKIP_SCHEMAS: frozenset[str] = frozenset(
    {
        "SYS",
        "INFORMATION_SCHEMA",
        "GUEST",
    }
)

# Snowflake account-level noise (uppercase match in _should_skip_schema).
_SNOWFLAKE_SKIP_SCHEMAS: frozenset[str] = frozenset(
    {
        "INFORMATION_SCHEMA",
        "ACCOUNT_USAGE",
        "READER_ACCOUNT_USAGE",
        "SNOWFLAKE",
    }
)

# scan_failures reason for column sampling errors (#1140; taxonomy shared with #828).
SCAN_FAILURE_REASON_SAMPLING_ERROR = "sampling_error"


class ColumnSampleError(RuntimeError):
    """Column sampling failed; the connector persisted a scan_failures row."""


def format_column_sample_failure_details(
    *,
    schema: str,
    table: str,
    column_name: str,
    dialect: str,
    exc: BaseException,
) -> str:
    """Stable detail string for scan_failures when SQL column sampling fails."""
    loc = f"{schema}.{table}.{column_name}" if schema else f"{table}.{column_name}"
    return f"{loc} dialect={dialect}: {type(exc).__name__}: {exc}"


def _get_skip_schemas(dialect: str) -> frozenset[str]:
    """Return schema names to skip when discovering (dialect-specific blacklist)."""
    d = (dialect or "").lower()
    if d == "oracle":
        return ORACLE_SYSTEM_SCHEMAS
    if d in ("mssql", "microsoft sql server"):
        return _MSSQL_SKIP_SCHEMAS
    if d == "snowflake":
        return _SNOWFLAKE_SKIP_SCHEMAS
    return _DEFAULT_SKIP_SCHEMAS


def _should_skip_schema(
    schema: str | None, dialect: str, skip_schemas: Set[str] | frozenset[str]
) -> bool:
    """True if schema should be skipped (empty or in skip_schemas)."""
    if not schema:
        return True
    d = (dialect or "").lower()
    if d in ("oracle", "mssql", "microsoft sql server", "snowflake"):
        key = schema.upper()
    else:
        key = schema.lower()
    return key in skip_schemas


def _tables_from_schema(inspector: Any, schema: str) -> list[dict[str, Any]]:
    """Return list of {schema, table, columns} for the given schema; empty list on error."""
    out = []
    try:
        for table in inspector.get_table_names(schema=schema):
            columns = inspector.get_columns(table, schema=schema)
            out.append(
                {
                    "schema": schema or "",
                    "table": table,
                    "columns": [
                        {"name": c["name"], "type": str(c["type"])} for c in columns
                    ],
                }
            )
    except Exception:
        pass
    return out


def _discover_fallback_no_schemas(inspector: Any) -> list[dict[str, Any]]:
    """When no schemas (e.g. SQLite), get tables without schema."""
    out = []
    if not hasattr(inspector, "get_table_names"):
        return out
    try:
        for table in inspector.get_table_names():
            columns = inspector.get_columns(table)
            out.append(
                {
                    "schema": "",
                    "table": table,
                    "columns": [
                        {"name": c["name"], "type": str(c["type"])} for c in columns
                    ],
                }
            )
    except Exception:
        pass
    return out


def _resolve_driver(target_driver: str | None) -> tuple[str, str]:
    """
    Return (sqlalchemy_drivername, base_engine_key) from config driver.

    When the config includes a dialect+driver suffix (e.g. ``mssql+pymssql``),
    the full string is used as the SQLAlchemy drivername. Bare engine keys
    (e.g. ``mssql``) resolve through DRIVER_MAP.
    """
    raw = (target_driver or "postgresql").strip()
    if "+" in raw:
        base = raw.split("+", 1)[0].lower()
        drivername = raw.lower()
    else:
        base = raw.lower()
        drivername = DRIVER_MAP.get(base, base)
    return drivername, base


def _quote_userinfo(value: str) -> str:
    """URL-encode user or password for use in connection URL userinfo. Prevents special chars (@, :, /, #) from breaking URL parsing."""
    if not value:
        return ""
    return quote(str(value), safe="")


def _build_url(target: dict[str, Any]) -> str:
    """Build SQLAlchemy URL from target config. User and password are URL-encoded to avoid injection or misparsing when they contain @, :, /, #."""
    drivername, base = _resolve_driver(target.get("driver"))
    # Allow full URL override
    if target.get("url"):
        return target["url"]
    if base == "sqlite":
        return f"sqlite:///{target.get('database', 'audit.db')}"
    user = _quote_userinfo(target.get("user", ""))
    password = _quote_userinfo(target.get("pass", target.get("password", "")))
    host = target.get("host", "localhost")
    port = target.get("port", 5432)
    database = target.get("database", "")
    if "oracle" in drivername:
        return (
            f"{drivername}://{user}:{password}@{host}:{port}/?service_name={database}"
        )
    return f"{drivername}://{user}:{password}@{host}:{port}/{database}"


def _connect_args_from_target(target: dict[str, Any]) -> dict[str, Any]:
    """
    Build SQLAlchemy ``connect_args`` from target timeouts (config loader merges global + per-target).

    Uses ``connect_timeout_seconds`` for connect; ``read_timeout_seconds`` for statement_timeout
    (PostgreSQL), SQLite lock wait, or pymssql query ``timeout``.

    Branch on the **resolved SQLAlchemy drivername** from ``_resolve_driver`` (not bare
    ``base == "mssql"`` alone): ``mssql+pymssql`` and ``mssql+pyodbc`` share base ``mssql``
    but accept different connect kwargs (#1302).

    Driver → connect_args mapping::

        postgresql[+…]       connect_timeout, options=-c statement_timeout=… (ms)
        mysql[+…] / mariadb  connect_timeout
        sqlite               timeout  (lock wait; read_timeout_seconds)
        mssql+pymssql        login_timeout, timeout  (#1297; bare ``mssql`` maps here)
        mssql+pyodbc         timeout only  (pyodbc.connect accepts ``timeout``; not login_timeout)
        oracle+oracledb      tcp_connect_timeout  (oracledb; not connect_timeout)
        other                connect_timeout  (best-effort)
    """
    connect_s = int(target.get("connect_timeout_seconds", 25))
    read_s = int(target.get("read_timeout_seconds", 90))
    drivername, base = _resolve_driver(target.get("driver"))
    connect_s = max(1, connect_s)
    read_s = max(1, read_s)
    if base == "sqlite":
        return {"timeout": read_s}
    if base == "postgresql":
        # statement_timeout in PostgreSQL is in milliseconds
        return {
            "connect_timeout": connect_s,
            "options": f"-c statement_timeout={read_s * 1000}",
        }
    if base in ("mysql", "mariadb"):
        return {"connect_timeout": connect_s}
    if base == "mssql":
        if drivername.endswith("+pyodbc"):
            # pyodbc.connect(..., timeout=seconds) — no login_timeout kwarg
            return {"timeout": connect_s}
        # mssql+pymssql (default via DRIVER_MAP) and other mssql+* pymssql-style
        return {"login_timeout": connect_s, "timeout": read_s}
    if base == "oracle":
        return {"tcp_connect_timeout": connect_s}
    return {"connect_timeout": connect_s}


def _resolve_sample_statement_timeout_ms(target: dict[str, Any]) -> int | None:
    """
    Per-target sampling statement budget (ms). Env overrides YAML.

    ``<= 0`` disables hints / ``SET LOCAL`` for that target (operator choice).
    Default when unset: **5000** ms.
    """
    raw_env = os.environ.get("DATA_BOAR_SAMPLE_STATEMENT_TIMEOUT_MS", "").strip()
    if raw_env:
        try:
            v = int(raw_env)
            return None if v <= 0 else max(250, min(v, 60_000))
        except ValueError:
            pass
    v = target.get("sample_statement_timeout_ms")
    if v is None and target.get("sample_statement_timeout_seconds") is not None:
        v = int(float(target["sample_statement_timeout_seconds"])) * 1000
    if v is None:
        return 5000
    vi = int(v)
    return None if vi <= 0 else max(250, min(vi, 60_000))


class SQLConnector:
    """
    Connect to a SQL database, discover tables/columns, sample content, run sensitivity detection,
    save findings (metadata only). Implements connect, discover, sample, close.
    """

    def __init__(
        self,
        target_config: dict[str, Any],
        scanner: Any,
        db_manager: Any,
        sample_limit: int = 5,
        detection_config: dict[str, Any] | None = None,
        sampling_policy: SamplingPolicy | None = None,
    ):
        self.config = target_config
        self.scanner = scanner
        self.db_manager = db_manager
        self.sample_limit = sample_limit
        self.sampling_policy = sampling_policy
        self.detection_config = detection_config or {}
        self.engine = None
        # Compatibility shim: legacy tests/helpers may still patch this attribute.
        self._connection = None
        self._sql_sampling_audit_key: str | None = None
        self._table_row_cache: dict[tuple[str, str], int | None] = {}
        self._sample_statement_timeout_ms = _resolve_sample_statement_timeout_ms(
            self.config
        )
        self._inter_query_delay_s = max(
            0.0, float(self.config.get("inter_query_delay_ms", 0) or 0) / 1000.0
        )

    def connect(self) -> None:
        ensure_sql_driver_available(self.config.get("driver"))
        url = _build_url(self.config)
        connect_args = _connect_args_from_target(self.config)
        self.engine = create_engine(url, pool_pre_ping=True, connect_args=connect_args)
        self._table_row_cache = {}

    def close(self) -> None:
        if self._connection:
            try:
                self._connection.close()
            except Exception:
                pass
            self._connection = None
        if self.engine:
            self.engine.dispose()
            self.engine = None

    def discover(self) -> list[dict[str, Any]]:
        """Return list of {schema, table, columns: [{name, type}]}. For Oracle, skips system schemas."""
        inspector = inspect(self.engine)
        dialect = self.engine.dialect.name if self.engine else ""
        skip_schemas = _get_skip_schemas(dialect)
        result = []
        for schema in inspector.get_schema_names():
            if _should_skip_schema(schema, dialect, skip_schemas):
                continue
            result.extend(_tables_from_schema(inspector, schema))
        if not result:
            result = _discover_fallback_no_schemas(inspector)
        return result

    def _process_one_finding(
        self,
        target_name: str,
        server_ip: str,
        engine_name: str,
        schema: str,
        table: str,
        cname: str,
        ctype: str,
        *,
        audit_log_name: str | None = None,
    ) -> None:
        """Sample column, run detection, optionally full-scan for minor; save finding and log."""
        if self._inter_query_delay_s > 0:
            time.sleep(self._inter_query_delay_s)
        try:
            sample = self.sample(schema, table, cname)
        except ColumnSampleError:
            return
        res = self.scanner.scan_column(cname, sample, connector_data_type=ctype)
        res = augment_low_id_like_for_persist(res, cname, self.detection_config)
        if (
            res["sensitivity_level"] == "LOW"
            and res.get("pattern_detected") != SUGGESTED_REVIEW_PATTERN
        ):
            return
        norm_tag = res.get("norm_tag", "")
        if "DOB_POSSIBLE_MINOR" in (
            res.get("pattern_detected") or ""
        ) and self.detection_config.get("minor_full_scan"):
            full_scan_limit = self.detection_config.get("minor_full_scan_limit", 100)
            try:
                full_sample = self.sample(schema, table, cname, limit=full_scan_limit)
            except ColumnSampleError:
                pass
            else:
                full_res = self.scanner.scan_column(
                    cname, full_sample, connector_data_type=ctype
                )
                if "DOB_POSSIBLE_MINOR" in (full_res.get("pattern_detected") or ""):
                    res = full_res
                    suffix = " (full-scan confirmed)"
                    norm_tag = (
                        (norm_tag or "").rstrip() + suffix
                        if norm_tag
                        else suffix.lstrip()
                    )
        self.db_manager.save_finding(
            source_type="database",
            target_name=target_name,
            server_ip=server_ip,
            engine_details=engine_name,
            schema_name=schema,
            table_name=table,
            column_name=cname,
            data_type=ctype,
            sensitivity_level=res["sensitivity_level"],
            pattern_detected=res["pattern_detected"],
            norm_tag=norm_tag,
            ml_confidence=res.get("ml_confidence", 0),
        )
        try:
            from utils.logger import log_finding

            log_label = audit_log_name or target_name
            log_finding(
                "database",
                log_label,
                f"{schema}.{table}.{cname}",
                res["sensitivity_level"],
                res["pattern_detected"],
            )
        except Exception:
            pass

    def sample(
        self, schema: str, table: str, column_name: str, limit: int | None = None
    ) -> str:
        """Fetch up to limit (or sample_limit) values from column; return concatenated string for detection (not stored)."""
        if limit is not None:
            use_limit = resolve_sql_sample_limit(limit)
        else:
            base = int(self.sample_limit)
            if self.sampling_policy is not None:
                base = self.sampling_policy.get_effective_sample_limit(
                    target_name=str(self.config.get("name") or "database"),
                    schema=schema or "",
                    table=table,
                    global_limit=base,
                )
            use_limit = resolve_sql_sample_limit(base)
        dialect = self.engine.dialect.name if self.engine else ""
        # Escape identifier per dialect to prevent SQL injection (identifiers come from discover(), not user input).
        # Double-quote for SQLite/Postgres/Oracle; backtick for MySQL.
        safe_col = column_name.replace('"', '""')
        safe_table = table.replace('"', '""')
        safe_schema = (schema or "").replace('"', '""')
        tkey = (schema or "", table)
        to = self._sample_statement_timeout_ms
        audit_key = f"{schema or ''}.{table}"
        try:
            with self.engine.connect() as conn:
                with conn.begin():
                    if tkey not in self._table_row_cache:
                        try:
                            from connectors.sql_table_row_estimate import (
                                estimate_table_rows,
                            )

                            self._table_row_cache[tkey] = estimate_table_rows(
                                conn, dialect, schema or "", table
                            )
                        except Exception:
                            self._table_row_cache[tkey] = None
                    est = self._table_row_cache[tkey]
                    table_meta = TableSamplingMetadata(estimated_row_count=est)
                    plan = SamplingManager.build_column_sample(
                        dialect,
                        safe_col=safe_col,
                        safe_table=safe_table,
                        safe_schema=safe_schema,
                        schema=schema,
                        limit=use_limit,
                        table_metadata=table_meta,
                        statement_timeout_ms=to,
                    )
                    if self._sql_sampling_audit_key != audit_key:
                        self._sql_sampling_audit_key = audit_key
                        try:
                            from utils.logger import get_logger

                            human = plan.human_strategy or plan.strategy_label
                            msg = (
                                "Sampling %s using %s strategy (label=%s dialect=%s)"
                                % (
                                    audit_key,
                                    human,
                                    plan.strategy_label,
                                    dialect,
                                )
                            )
                            if plan.audit_notes:
                                msg += " notes=%s" % (plan.audit_notes,)
                            get_logger().info(msg)
                        except Exception:
                            pass  # best-effort audit logging — never break sampling for a log line
                    if dialect in ("postgresql", "postgres") and to:
                        conn.execute(
                            text("SET LOCAL statement_timeout = :mt").bindparams(
                                mt=int(to)
                            )
                        )
                    rows = conn.execute(plan.query).fetchall()
        except Exception as e:
            target_name = str(self.config.get("name") or "database")
            details = format_column_sample_failure_details(
                schema=schema or "",
                table=table,
                column_name=column_name,
                dialect=dialect,
                exc=e,
            )
            self.db_manager.save_failure(
                target_name, SCAN_FAILURE_REASON_SAMPLING_ERROR, details
            )
            try:
                from utils.logger import get_logger

                get_logger().warning(
                    "sample_failed schema=%s table=%s col=%s dialect=%s err=%s",
                    schema or "",
                    table,
                    column_name,
                    dialect,
                    str(e)[:200],
                )
            except Exception:
                pass
            raise ColumnSampleError from e
        parts = [str(r[0])[:200] for r in rows if r[0] is not None]
        return " ".join(parts)

    def _probe_product_version(self, engine_name: str) -> str | None:
        if not self.engine:
            return None
        probe_sql = {
            "postgresql": text("SELECT version()"),
            "mysql": text("SELECT VERSION()"),
            "mariadb": text("SELECT VERSION()"),
            "sqlite": text("SELECT sqlite_version()"),
            "mssql": text("SELECT @@VERSION"),
            "oracle": text("SELECT banner FROM v$version WHERE ROWNUM = 1"),
        }
        stmt = probe_sql.get(engine_name)
        if stmt is None:
            return None
        try:
            # Keep probe transaction scope local so sampling starts from a clean connection state.
            with self.engine.connect() as conn:
                with conn.begin():
                    value = conn.execute(stmt).scalar()
            return str(value or "")
        except Exception:
            return None

    def _save_inventory_snapshot(self, target_name: str, engine_name: str) -> None:
        """
        Persist one best-effort inventory row (product/version/protocol/transport).

        Phase 1 intentionally keeps this lightweight and resilient: failures here must not
        break scanning.
        """
        if not hasattr(self.db_manager, "save_data_source_inventory"):
            return
        product_version = self._probe_product_version(engine_name)
        raw_details: dict[str, str] = {}
        raw_details["driver"] = (self.config.get("driver") or "").strip()
        if product_version:
            raw_details["version_probe"] = product_version[:500]

        sslmode = str(self.config.get("sslmode") or "").strip().lower()
        if sslmode:
            transport_security = f"sslmode={sslmode}"
        elif "sslmode=" in str(self.config.get("url") or "").lower():
            transport_security = "sslmode(from-url)"
        else:
            transport_security = "unknown"

        try:
            self.db_manager.save_data_source_inventory(
                target_name=target_name,
                source_type="database",
                product=engine_name,
                product_version=product_version,
                protocol_or_api_version=engine_name,
                transport_security=transport_security,
                raw_details=json.dumps(raw_details, ensure_ascii=False),
            )
        except Exception:
            # Never fail a scan because inventory persistence failed.
            pass

    def run(self) -> None:
        """Connect, discover, sample each column, detect, save_finding; on error save_failure."""
        from utils.audit_log_display import audit_log_target_label

        target_name = self.config.get("name", "database")
        audit_name = audit_log_target_label(self.config, default="database")
        server_ip = self.config.get("host", "localhost")
        try:
            self.connect()
        except Exception as e:
            self.db_manager.save_failure(target_name, "unreachable", str(e))
            return
        try:
            from utils.logger import log_connection

            log_connection(audit_name, "database", server_ip or "local")
            engine_name = self.engine.dialect.name if self.engine else "sql"
            self._save_inventory_snapshot(target_name, engine_name)
            for item in self.discover():
                schema = item["schema"]
                table = item["table"]
                for col in item["columns"]:
                    self._process_one_finding(
                        target_name,
                        server_ip,
                        engine_name,
                        schema,
                        table,
                        col["name"],
                        col["type"],
                        audit_log_name=audit_name,
                    )
        except Exception as e:
            self.db_manager.save_failure(target_name, "error", str(e))
        finally:
            self.close()


# Register for common SQL engines
for _t in ("postgresql", "mysql", "mariadb", "sqlite", "mssql", "oracle"):
    register(_t, SQLConnector, ["name", "type"])
