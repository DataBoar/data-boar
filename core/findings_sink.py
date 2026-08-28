"""Post-scan findings sink: echo SQLite rows to a customer SQL or Mongo store (#552).

Local SQLite remains the engine primary. This module is an optional echo after
``generate_final_reports``. Failures never abort a scan session (warning +
``save_failure(..., "sink_error", ...)``).

Default payload is metadata-only (no ``sample_content``). Opt-in sample export
requires both ``findings_sink.include_sample_content: true`` and an explicit
``--allow-sample-export`` on the CLI (LGPD Art. 46). The post-scan hook never
emits sample columns even when the YAML flag is true.

Finding INSERT/UPDATE SQL interpolates a **fixed column allowlist** only
(never operator identifiers). Bound parameters carry values. Bandit B608
is annotated inline on those builders (same pattern as ``sql_sampling.py``).
"""

from __future__ import annotations

import os
from datetime import UTC, datetime
from typing import Any
from urllib.parse import quote_plus

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from core.about import get_about_info
from core.licensing.feature_gate import require_feature
from core.licensing.runtime_feature_tier import get_runtime_tier_for_features
from core.licensing.tier_features import is_feature_available
from utils.logger import get_logger

_SQL_TYPES = frozenset(
    {"postgresql", "postgres", "mysql", "mariadb", "mssql", "sqlite"}
)
_MONGO_TYPES = frozenset({"mongodb", "mongo"})

_TYPE_ALIASES = {
    "postgres": "postgresql",
    "mariadb": "mysql",
    "mongo": "mongodb",
}

_SQL_URL_PREFIX = {
    "postgresql": "postgresql+psycopg2",
    "mysql": "mysql+pymysql",
    "mssql": "mssql+pymssql",
}

_UNIQUE_KEYS = (
    "session_id",
    "source_type",
    "target_name",
    "table_name",
    "column_name",
    "file_path",
)

_SQLITE_SESSIONS_DDL = """
CREATE TABLE IF NOT EXISTS data_boar_sessions (
    session_id TEXT PRIMARY KEY,
    started_at TEXT,
    finished_at TEXT,
    tool_version TEXT,
    config_hash TEXT,
    total_findings INTEGER,
    exported_at TEXT
)
"""

_SQLITE_FINDINGS_DDL = """
CREATE TABLE IF NOT EXISTS data_boar_findings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    source_type TEXT NOT NULL DEFAULT '',
    target_name TEXT NOT NULL DEFAULT '',
    schema_name TEXT,
    table_name TEXT NOT NULL DEFAULT '',
    column_name TEXT NOT NULL DEFAULT '',
    file_path TEXT NOT NULL DEFAULT '',
    file_name TEXT,
    pattern_detected TEXT,
    norm_tag TEXT,
    occurrences INTEGER,
    risk_level TEXT,
    UNIQUE (session_id, source_type, target_name, table_name, column_name, file_path)
)
"""

SAMPLE_EXPORT_REFUSED = (
    "findings_sink.include_sample_content is true but --allow-sample-export was "
    "not passed. Refusing export (LGPD Art. 46 — sensitive payload must not "
    "land in an external store without an explicit operator acknowledgement)."
)


class SampleExportNotAcknowledged(RuntimeError):
    """CLI refused sample export without ``--allow-sample-export``."""


class FindingsSinkError(RuntimeError):
    """Sink connect / write failure (CLI path; post-scan is fail-soft)."""


def _nz(value: Any) -> str:
    if value is None:
        return ""
    return str(value)


def _sink_block(config: dict[str, Any] | None) -> dict[str, Any]:
    raw = (config or {}).get("findings_sink")
    return raw if isinstance(raw, dict) else {}


def sink_enabled(config: dict[str, Any] | None) -> bool:
    return bool(_sink_block(config).get("enabled"))


def _canonical_type(raw: Any) -> str:
    t = str(raw or "").strip().lower()
    return _TYPE_ALIASES.get(t, t)


def _include_samples_requested(cfg: dict[str, Any]) -> bool:
    return bool(cfg.get("include_sample_content"))


def redacted_sink_label(cfg: dict[str, Any]) -> str:
    """Operator-facing destination without credentials."""
    kind = _canonical_type(cfg.get("type"))
    if kind == "sqlite":
        path = str(cfg.get("sqlite_path") or cfg.get("path") or "").strip()
        return f"sqlite:///{path}" if path else "sqlite"
    host = str(cfg.get("host") or "").strip() or "host"
    port = cfg.get("port")
    db = str(cfg.get("database") or "").strip()
    port_s = f":{port}" if port not in (None, "") else ""
    db_s = f"/{db}" if db else ""
    return f"{kind}://{host}{port_s}{db_s}"


def _env_or_inline(cfg: dict[str, Any], env_key: str, inline_key: str) -> str:
    env_name = str(cfg.get(env_key) or "").strip()
    if env_name:
        return (os.environ.get(env_name) or "").strip()
    return str(cfg.get(inline_key) or "").strip()


def _feature_for_type(kind: str) -> str:
    if kind in _MONGO_TYPES:
        return "findings_sink_mongodb"
    return "findings_sink_sql"


def _require_sink_tier(config: dict[str, Any], kind: str) -> None:
    require_feature(config, _feature_for_type(kind))


def _guard_sql_host(cfg: dict[str, Any]) -> None:
    kind = _canonical_type(cfg.get("type"))
    if kind == "sqlite":
        return
    host = str(cfg.get("host") or "").strip()
    if not host:
        raise FindingsSinkError("findings_sink.host is required for SQL/Mongo sinks")
    port = cfg.get("port")
    target = f"{host}:{port}" if port not in (None, "") else host
    from connectors.url_guard import (
        resolve_and_validate_outbound_url,
        target_allows_private,
    )

    err, _ips = resolve_and_validate_outbound_url(
        target,
        allow_private=target_allows_private(cfg),
        label="findings_sink.host",
    )
    if err:
        raise FindingsSinkError(err)


def _sqlalchemy_url(cfg: dict[str, Any]) -> str:
    kind = _canonical_type(cfg.get("type"))
    if kind == "sqlite":
        path = str(cfg.get("sqlite_path") or cfg.get("path") or "").strip()
        if not path:
            raise FindingsSinkError(
                "findings_sink.sqlite_path is required when type is sqlite"
            )
        return f"sqlite:///{path}"
    prefix = _SQL_URL_PREFIX.get(kind)
    if not prefix:
        raise FindingsSinkError(f"Unsupported findings_sink.type: {kind!r}")
    user = quote_plus(_env_or_inline(cfg, "user_from_env", "user"))
    password = quote_plus(_env_or_inline(cfg, "pass_from_env", "pass"))
    host = str(cfg.get("host") or "").strip()
    port = cfg.get("port")
    database = str(cfg.get("database") or "").strip()
    auth = ""
    if user:
        auth = f"{user}:{password}@" if password else f"{user}@"
    port_s = f":{port}" if port not in (None, "") else ""
    return f"{prefix}://{auth}{host}{port_s}/{database}"


def _ensure_sqlite_schema(engine: Engine, *, include_sample: bool) -> None:
    with engine.begin() as conn:
        conn.execute(text(_SQLITE_SESSIONS_DDL))
        conn.execute(text(_SQLITE_FINDINGS_DDL))
        if include_sample:
            cols = conn.execute(
                text("PRAGMA table_info(data_boar_findings)")
            ).fetchall()
            names = {row[1] for row in cols}
            if "sample_content" not in names:
                conn.execute(
                    text(
                        "ALTER TABLE data_boar_findings ADD COLUMN sample_content TEXT"
                    )
                )


def _session_meta(db_manager: Any, session_id: str) -> dict[str, Any]:
    for row in db_manager.list_sessions() or []:
        if row.get("session_id") == session_id:
            return row
    return {
        "session_id": session_id,
        "started_at": None,
        "finished_at": None,
        "config_scope_hash": None,
        "database_findings": 0,
        "filesystem_findings": 0,
        "application_findings": 0,
    }


def _finding_rows(
    db_manager: Any,
    session_id: str,
    *,
    include_sample: bool,
) -> list[dict[str, Any]]:
    db_rows, fs_rows, app_rows, _fails = db_manager.get_findings(session_id)
    out: list[dict[str, Any]] = []

    def pack(
        source_type: str,
        row: dict[str, Any],
        *,
        table_name: str = "",
        column_name: str = "",
        file_path: str = "",
        file_name: str = "",
        schema_name: str = "",
    ) -> dict[str, Any]:
        packed = {
            "session_id": session_id,
            "source_type": source_type,
            "target_name": _nz(row.get("target_name")),
            "schema_name": _nz(schema_name or row.get("schema_name")),
            "table_name": _nz(table_name or row.get("table_name")),
            "column_name": _nz(column_name or row.get("column_name")),
            "file_path": _nz(file_path or row.get("path")),
            "file_name": _nz(file_name or row.get("file_name")),
            "pattern_detected": row.get("pattern_detected"),
            "norm_tag": row.get("norm_tag"),
            "occurrences": 1,
            "risk_level": row.get("sensitivity_level"),
        }
        if include_sample:
            packed["sample_content"] = row.get("sample_content") or row.get(
                "sample_value"
            )
        return packed

    for row in db_rows:
        out.append(pack("database", row))
    for row in fs_rows:
        out.append(
            pack(
                "filesystem",
                row,
                table_name="",
                column_name="",
                file_path=_nz(row.get("path")),
                file_name=_nz(row.get("file_name")),
            )
        )
    for row in app_rows:
        out.append(
            pack(
                "application",
                row,
                table_name="",
                column_name="",
                file_path=_nz(row.get("path")),
                file_name=_nz(row.get("file_name")),
            )
        )
    return out


def _on_conflict(cfg: dict[str, Any]) -> str:
    mode = str(cfg.get("on_conflict") or "upsert").strip().lower()
    if mode not in {"upsert", "skip", "fail"}:
        return "upsert"
    return mode


def _upsert_session_sql(engine: Engine, meta: dict[str, Any], total: int) -> None:
    now = datetime.now(UTC).isoformat()
    version = get_about_info().get("version")
    payload = {
        "session_id": meta.get("session_id"),
        "started_at": meta.get("started_at"),
        "finished_at": meta.get("finished_at"),
        "tool_version": version,
        "config_hash": meta.get("config_scope_hash"),
        "total_findings": total,
        "exported_at": now,
    }
    dialect = engine.dialect.name
    with engine.begin() as conn:
        if dialect == "sqlite":
            conn.execute(
                text(
                    "INSERT INTO data_boar_sessions "
                    "(session_id, started_at, finished_at, tool_version, "
                    "config_hash, total_findings, exported_at) "
                    "VALUES (:session_id, :started_at, :finished_at, :tool_version, "
                    ":config_hash, :total_findings, :exported_at) "
                    "ON CONFLICT(session_id) DO UPDATE SET "
                    "started_at=excluded.started_at, finished_at=excluded.finished_at, "
                    "tool_version=excluded.tool_version, config_hash=excluded.config_hash, "
                    "total_findings=excluded.total_findings, exported_at=excluded.exported_at"
                ),
                payload,
            )
            return
        if dialect == "postgresql":
            conn.execute(
                text(
                    "INSERT INTO data_boar_sessions "
                    "(session_id, started_at, finished_at, tool_version, "
                    "config_hash, total_findings, exported_at) "
                    "VALUES (:session_id, :started_at, :finished_at, :tool_version, "
                    ":config_hash, :total_findings, :exported_at) "
                    "ON CONFLICT (session_id) DO UPDATE SET "
                    "started_at=EXCLUDED.started_at, finished_at=EXCLUDED.finished_at, "
                    "tool_version=EXCLUDED.tool_version, config_hash=EXCLUDED.config_hash, "
                    "total_findings=EXCLUDED.total_findings, exported_at=EXCLUDED.exported_at"
                ),
                payload,
            )
            return
        if dialect == "mysql":
            conn.execute(
                text(
                    "INSERT INTO data_boar_sessions "
                    "(session_id, started_at, finished_at, tool_version, "
                    "config_hash, total_findings, exported_at) "
                    "VALUES (:session_id, :started_at, :finished_at, :tool_version, "
                    ":config_hash, :total_findings, :exported_at) "
                    "ON DUPLICATE KEY UPDATE "
                    "started_at=VALUES(started_at), finished_at=VALUES(finished_at), "
                    "tool_version=VALUES(tool_version), config_hash=VALUES(config_hash), "
                    "total_findings=VALUES(total_findings), exported_at=VALUES(exported_at)"
                ),
                payload,
            )
            return
        conn.execute(
            text("DELETE FROM data_boar_sessions WHERE session_id = :session_id"),
            {"session_id": payload["session_id"]},
        )
        conn.execute(
            text(
                "INSERT INTO data_boar_sessions "
                "(session_id, started_at, finished_at, tool_version, "
                "config_hash, total_findings, exported_at) "
                "VALUES (:session_id, :started_at, :finished_at, :tool_version, "
                ":config_hash, :total_findings, :exported_at)"
            ),
            payload,
        )


def _finding_insert_sql(include_sample: bool) -> str:
    cols = [
        "session_id",
        "source_type",
        "target_name",
        "schema_name",
        "table_name",
        "column_name",
        "file_path",
        "file_name",
        "pattern_detected",
        "norm_tag",
        "occurrences",
        "risk_level",
    ]
    if include_sample:
        cols.append("sample_content")
    placeholders = ", ".join(f":{c}" for c in cols)
    col_sql = ", ".join(cols)
    return f"INSERT INTO data_boar_findings ({col_sql}) VALUES ({placeholders})"  # nosec B608


def _finding_update_sql(include_sample: bool) -> str:
    sets = [
        "schema_name = :schema_name",
        "file_name = :file_name",
        "pattern_detected = :pattern_detected",
        "norm_tag = :norm_tag",
        "occurrences = :occurrences",
        "risk_level = :risk_level",
    ]
    if include_sample:
        sets.append("sample_content = :sample_content")
    where = " AND ".join(f"{k} = :{k}" for k in _UNIQUE_KEYS)
    return f"UPDATE data_boar_findings SET {', '.join(sets)} WHERE {where}"  # nosec B608


def _sqlite_finding_upsert_sql(include_sample: bool, on_conflict: str) -> str:
    insert = _finding_insert_sql(include_sample)
    conflict = (
        "session_id, source_type, target_name, table_name, column_name, file_path"
    )
    if on_conflict == "skip":
        return f"{insert} ON CONFLICT({conflict}) DO NOTHING"  # nosec B608
    if on_conflict == "fail":
        return insert
    sets = [
        "schema_name=excluded.schema_name",
        "file_name=excluded.file_name",
        "pattern_detected=excluded.pattern_detected",
        "norm_tag=excluded.norm_tag",
        "occurrences=excluded.occurrences",
        "risk_level=excluded.risk_level",
    ]
    if include_sample:
        sets.append("sample_content=excluded.sample_content")
    return f"{insert} ON CONFLICT({conflict}) DO UPDATE SET {', '.join(sets)}"  # nosec B608


def _push_sql(
    engine: Engine,
    meta: dict[str, Any],
    rows: list[dict[str, Any]],
    *,
    on_conflict: str,
    include_sample: bool,
) -> None:
    _upsert_session_sql(engine, meta, len(rows))
    dialect = engine.dialect.name
    if dialect == "sqlite":
        stmt = text(_sqlite_finding_upsert_sql(include_sample, on_conflict))
        with engine.begin() as conn:
            for row in rows:
                conn.execute(stmt, row)
        return
    insert_sql = text(_finding_insert_sql(include_sample))
    update_sql = text(_finding_update_sql(include_sample))
    with engine.begin() as conn:
        for row in rows:
            nested = conn.begin_nested()
            try:
                conn.execute(insert_sql, row)
                nested.commit()
            except IntegrityError:
                nested.rollback()
                if on_conflict == "fail":
                    raise
                if on_conflict == "skip":
                    continue
                conn.execute(update_sql, row)


def _push_mongo(
    cfg: dict[str, Any],
    meta: dict[str, Any],
    rows: list[dict[str, Any]],
    *,
    on_conflict: str,
) -> None:
    try:
        from pymongo import MongoClient
        from pymongo.errors import DuplicateKeyError
    except ImportError as exc:
        raise FindingsSinkError(
            "MongoDB sink requires pymongo (install data-boar[nosql] or pymongo)."
        ) from exc

    user = _env_or_inline(cfg, "user_from_env", "user")
    password = _env_or_inline(cfg, "pass_from_env", "pass")
    host = str(cfg.get("host") or "").strip()
    port = int(cfg.get("port") or 27017)
    database = str(cfg.get("database") or "").strip()
    if not database:
        raise FindingsSinkError("findings_sink.database is required for mongodb")
    auth = ""
    if user:
        auth = (
            f"{quote_plus(user)}:{quote_plus(password)}@"
            if password
            else f"{quote_plus(user)}@"
        )
    uri = f"mongodb://{auth}{host}:{port}"
    client = MongoClient(uri, serverSelectionTimeoutMS=8000)
    try:
        db = client[database]
        now = datetime.now(UTC)
        session_doc = {
            "session_id": meta.get("session_id"),
            "started_at": meta.get("started_at"),
            "finished_at": meta.get("finished_at"),
            "tool_version": get_about_info().get("version"),
            "config_hash": meta.get("config_scope_hash"),
            "total_findings": len(rows),
            "exported_at": now,
        }
        db.data_boar_sessions.update_one(
            {"session_id": session_doc["session_id"]},
            {"$set": session_doc},
            upsert=True,
        )
        for row in rows:
            filt = {k: row.get(k) for k in _UNIQUE_KEYS}
            if on_conflict == "skip":
                if db.data_boar_findings.find_one(filt):
                    continue
                try:
                    db.data_boar_findings.insert_one(dict(row))
                except DuplicateKeyError:
                    continue
            elif on_conflict == "fail":
                db.data_boar_findings.insert_one(dict(row))
            else:
                db.data_boar_findings.replace_one(filt, dict(row), upsert=True)
    finally:
        client.close()


def push_session_to_sink(
    config: dict[str, Any],
    db_manager: Any,
    session_id: str,
    *,
    allow_sample_export: bool = False,
    require_explicit_sample_ack: bool = False,
) -> str:
    """Push one session to the configured sink. Returns a redacted destination label.

    Parameters
    ----------
    require_explicit_sample_ack
        CLI path: ``include_sample_content`` without ``allow_sample_export`` raises
        :class:`SampleExportNotAcknowledged`. The post-scan hook keeps this False
        and never emits sample columns.
    """
    cfg = _sink_block(config)
    if not cfg.get("enabled"):
        raise FindingsSinkError("findings_sink.enabled is false")
    sid = (session_id or "").strip()
    if not sid:
        raise FindingsSinkError("empty session_id")
    kind = _canonical_type(cfg.get("type"))
    if kind not in _SQL_TYPES and kind not in _MONGO_TYPES:
        raise FindingsSinkError(f"Unsupported findings_sink.type: {kind!r}")
    _require_sink_tier(config, kind)
    samples_yaml = _include_samples_requested(cfg)
    if require_explicit_sample_ack and samples_yaml and not allow_sample_export:
        raise SampleExportNotAcknowledged(SAMPLE_EXPORT_REFUSED)
    include_sample = bool(samples_yaml and allow_sample_export)
    _guard_sql_host(cfg)
    meta = _session_meta(db_manager, sid)
    rows = _finding_rows(db_manager, sid, include_sample=include_sample)
    label = redacted_sink_label(cfg)
    if kind in _MONGO_TYPES:
        _push_mongo(cfg, meta, rows, on_conflict=_on_conflict(cfg))
        return label
    engine = create_engine(_sqlalchemy_url(cfg), pool_pre_ping=True)
    try:
        if kind == "sqlite":
            _ensure_sqlite_schema(engine, include_sample=include_sample)
        _push_sql(
            engine,
            meta,
            rows,
            on_conflict=_on_conflict(cfg),
            include_sample=include_sample,
        )
    except SQLAlchemyError as exc:
        raise FindingsSinkError(str(exc)) from exc
    finally:
        engine.dispose()
    return label


def maybe_push_findings_sink(
    config: dict[str, Any],
    db_manager: Any,
    session_id: str,
) -> None:
    """Post-scan hook: no-op when disabled; never raises into the scan."""
    if not sink_enabled(config):
        return
    cfg = _sink_block(config)
    kind = _canonical_type(cfg.get("type"))
    feature = _feature_for_type(kind)
    tier = get_runtime_tier_for_features(config)
    logger = get_logger()
    if not is_feature_available(feature, tier):
        logger.warning(
            "Findings sink skipped — %s is not available for the current license tier",
            feature,
        )
        return
    try:
        db_manager.set_current_session_id(session_id)
        label = push_session_to_sink(
            config,
            db_manager,
            session_id,
            allow_sample_export=False,
            require_explicit_sample_ack=False,
        )
        logger.info("findings exported to %s", label)
    except Exception as exc:
        logger.warning("Findings sink failed (session continues): %s", exc)
        try:
            db_manager.save_failure("findings_sink", "sink_error", str(exc))
        except Exception:
            pass
