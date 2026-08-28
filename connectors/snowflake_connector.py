"""
Snowflake connector: optional, requires snowflake-connector-python (.[bigdata] extra).
Uses Snowflake's Python connector directly (no SQLAlchemy) to discover tables/columns,
sample rows, run sensitivity detection, and save findings as database metadata.

Target config (type: database, driver: snowflake):

  - name: "Warehouse_LGPD"
    type: database
    driver: snowflake
    account: "xy12345.us-east-1"
    user: "AUDIT_USER"
    pass: "secret"
    database: "COMPLIANCE_DB"
    schema: "PUBLIC"
    warehouse: "AUDIT_WH"
    role: "ANALYST"           # optional
"""

import time
from typing import Any

from connectors.sample_value_dedup import (
    join_distinct_sample,
    resolve_fetch_row_budget,
)
from connectors.sql_connector import (
    _get_skip_schemas,
    _resolve_sample_statement_timeout_ms,
    _should_skip_schema,
)
from connectors.sql_sampling import (
    column_sample_sql_for_cursor,
    resolve_sql_sample_limit,
)
from core.connector_registry import register
from core.sampling import SamplingPolicy
from core.suggested_review import (
    SUGGESTED_REVIEW_PATTERN,
    augment_low_id_like_for_persist,
)

try:
    import snowflake.connector  # type: ignore[import]

    _SNOWFLAKE_AVAILABLE = True
except ImportError:
    _SNOWFLAKE_AVAILABLE = False
    snowflake = None  # type: ignore[assignment]


class SnowflakeConnector:
    """
    Connect to Snowflake via snowflake-connector-python, discover tables/columns, sample
    content, run sensitivity detection, and save findings (metadata only).
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
        self.sample_limit = max(int(sample_limit or 5), 1)
        self.sampling_policy = sampling_policy
        self.detection_config = detection_config or {}
        self._conn = None
        self._sql_sampling_audit_key: str | None = None
        self._sample_statement_timeout_ms = _resolve_sample_statement_timeout_ms(
            self.config
        )
        self._inter_query_delay_s = max(
            0.0, float(self.config.get("inter_query_delay_ms", 0) or 0) / 1000.0
        )
        self._scan_progress = target_config.get("_scan_progress")

    def connect(self) -> None:
        if not _SNOWFLAKE_AVAILABLE:
            raise RuntimeError(
                "snowflake-connector-python is required for Snowflake targets. "
                'Install with: uv pip install -e ".[bigdata]"'
            )
        cfg = self.config
        user = cfg.get("user") or cfg.get("username", "")
        password = cfg.get("pass") or cfg.get("password", "")
        account = cfg.get("account", "")
        warehouse = cfg.get("warehouse")
        database = cfg.get("database")
        schema = cfg.get("schema")
        role = cfg.get("role")
        connect_s = max(1, int(cfg.get("connect_timeout_seconds", 25)))
        read_s = max(1, int(cfg.get("read_timeout_seconds", 90)))
        params: dict[str, Any] = {
            "user": user,
            "password": password,
            "account": account,
            "connection_timeout": connect_s,
            "network_timeout": read_s,
        }
        if warehouse:
            params["warehouse"] = warehouse
        if database:
            params["database"] = database
        if schema:
            params["schema"] = schema
        if role:
            params["role"] = role
        self._conn = snowflake.connector.connect(**params)  # type: ignore[operator]

    def close(self) -> None:
        if self._conn is not None:
            try:
                self._conn.close()
            except Exception:
                pass
            self._conn = None

    def _execute(self, sql: str, params: tuple[Any, ...] | None = None) -> list[tuple]:
        if self._conn is None:
            return []
        cur = self._conn.cursor()
        try:
            cur.execute(sql, params or ())
            return cur.fetchall()
        finally:
            try:
                cur.close()
            except Exception:
                pass

    def _list_tables(self) -> list[dict[str, str]]:
        """
        Return list of {schema, table} for base tables in the current database.
        """
        rows = self._execute(
            """
            SELECT table_schema, table_name
            FROM information_schema.tables
            WHERE table_type = 'BASE TABLE'
            ORDER BY table_schema, table_name
            """
        )
        skip = _get_skip_schemas("snowflake")
        out: list[dict[str, str]] = []
        for schema, table in rows:
            s = str(schema or "")
            if _should_skip_schema(s, "snowflake", skip):
                continue
            out.append({"schema": s, "table": str(table or "")})
        return out

    def _get_columns(self, schema: str, table: str) -> list[dict[str, str]]:
        """
        Return list of {name, type} for columns in the given table.
        """
        rows = self._execute(
            """
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_schema = %s AND table_name = %s
            ORDER BY ordinal_position
            """,
            (schema, table),
        )
        out: list[dict[str, str]] = []
        for name, dtype in rows:
            out.append({"name": str(name or ""), "type": str(dtype or "")})
        return out

    def _sample_column(self, schema: str, table: str, column: str) -> str:
        """
        Fetch up to sample_limit values from column; return concatenated string for detection.
        Does not persist any raw content.
        """
        if self._conn is None:
            return ""

        # Identifier escaping matches SamplingManager / SQLAlchemy path (names from information_schema).
        safe_col = column.replace('"', '""')
        safe_table = table.replace('"', '""')
        safe_schema = (schema or "").replace('"', '""')
        base = int(self.sample_limit)
        if self.sampling_policy is not None:
            base = self.sampling_policy.get_effective_sample_limit(
                target_name=str(self.config.get("name") or "database"),
                schema=schema or "",
                table=table,
                global_limit=base,
            )
        lim = resolve_sql_sample_limit(base)
        fetch_budget = resolve_fetch_row_budget(lim)
        sql, _binds, strategy_label, _notes, human = column_sample_sql_for_cursor(
            "snowflake",
            safe_col=safe_col,
            safe_table=safe_table,
            safe_schema=safe_schema,
            schema=schema or None,
            limit=fetch_budget,
            table_metadata=None,
            statement_timeout_ms=self._sample_statement_timeout_ms,
        )
        audit_key = f"{schema}.{table}"
        if self._sql_sampling_audit_key != audit_key:
            self._sql_sampling_audit_key = audit_key
            try:
                from utils.logger import get_logger

                get_logger().info(
                    "Sampling %s using %s strategy (label=%s dialect=snowflake)",
                    audit_key,
                    human,
                    strategy_label,
                )
            except Exception:
                pass
        cur = self._conn.cursor()
        try:
            cur.execute(sql)
            rows = cur.fetchmany(fetch_budget)
            return join_distinct_sample(
                (row[0] for row in rows if row), distinct_cap=lim
            )
        except Exception:
            return ""
        finally:
            try:
                cur.close()
            except Exception:
                pass

    def run(self) -> None:
        from utils.audit_log_display import audit_log_target_label

        target_name = self.config.get("name", "Snowflake")
        audit_name = audit_log_target_label(self.config, default="Snowflake")
        account = self.config.get("account", "")
        try:
            self.connect()
        except Exception as e:
            self.db_manager.save_failure(target_name, "unreachable", str(e))
            return
        try:
            try:
                from utils.logger import log_connection

                log_connection(audit_name, "database", account or "snowflake")
            except Exception:
                pass
            tables = self._list_tables()
            progress = self._scan_progress
            if progress is not None and getattr(progress, "enabled", False):
                progress.set_tables_total(len(tables), target_name=target_name)
            completed_tables: set[tuple[str, str]] = set()
            from core.database import LocalDBManager

            if isinstance(self.db_manager, LocalDBManager):
                completed_tables = self.db_manager.list_completed_sql_tables(
                    target_name
                )
            for table_index, t in enumerate(tables, start=1):
                schema = t["schema"]
                table = t["table"]
                table_key = ((schema or "").strip(), table)
                if table_key in completed_tables:
                    continue
                table_label = f"{schema}.{table}" if schema else table
                if progress is not None and getattr(progress, "enabled", False):
                    progress.advance_table(
                        table_index,
                        table_label=table_label,
                        target_name=target_name,
                    )
                if isinstance(self.db_manager, LocalDBManager):
                    self.db_manager.mark_sql_table_in_progress(
                        target_name, schema, table
                    )
                columns = self._get_columns(schema, table)
                for col in columns:
                    if self._inter_query_delay_s > 0:
                        time.sleep(self._inter_query_delay_s)
                    cname = col["name"]
                    ctype = col["type"]
                    sample = self._sample_column(schema, table, cname)
                    res = self.scanner.scan_column(
                        cname, sample, connector_data_type=ctype
                    )
                    res = augment_low_id_like_for_persist(
                        res, cname, self.detection_config
                    )
                    if (
                        res.get("sensitivity_level") == "LOW"
                        and res.get("pattern_detected") != SUGGESTED_REVIEW_PATTERN
                    ):
                        continue
                    self.db_manager.save_finding(
                        source_type="database",
                        target_name=target_name,
                        server_ip=account or "snowflake",
                        engine_details="snowflake",
                        schema_name=schema,
                        table_name=table,
                        column_name=cname,
                        data_type=ctype,
                        sensitivity_level=res.get("sensitivity_level", "MEDIUM"),
                        pattern_detected=res.get("pattern_detected", ""),
                        norm_tag=res.get("norm_tag", ""),
                        ml_confidence=res.get("ml_confidence", 0),
                    )
                    try:
                        from utils.logger import log_finding

                        location = (
                            f"{schema}.{table}.{cname}"
                            if schema
                            else f"{table}.{cname}"
                        )
                        log_finding(
                            "database",
                            audit_name,
                            location,
                            res.get("sensitivity_level", ""),
                            res.get("pattern_detected", ""),
                        )
                    except Exception:
                        pass
                if isinstance(self.db_manager, LocalDBManager):
                    self.db_manager.mark_sql_table_completed(target_name, schema, table)
        except Exception as e:
            self.db_manager.save_failure(target_name, "error", str(e))
        finally:
            self.close()


if _SNOWFLAKE_AVAILABLE:
    register(
        "snowflake",
        SnowflakeConnector,
        ["name", "type", "account", "user", "database", "warehouse"],
    )
