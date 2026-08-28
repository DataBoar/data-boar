"""Scan plan preview (``--plan``): catalog scope + TCP RTT floor, no column sampling.

Cost model (must match ``SQLConnector.run`` / ``_process_one_finding`` / ``sample``):

* ``discover()`` loads schemas/tables and ``get_columns`` per table (catalog only;
  this is what ``--plan`` uses — no ``sample()`` / no detector).
* The live scan then samples **each column in its own query** (one round-trip per
  column, plus query time on the server).
* The **first** sample on a table also runs ``estimate_table_rows`` (cached on
  ``_table_row_cache``), i.e. **one extra query per table**.
* Optional ``inter_query_delay_ms`` sleeps **per column** before sampling.

RTT-floor for a subsequent SQL scan (not wall-clock):

    round_trips ≈ n_columns + 2 * n_tables
        (column samples + row estimates + catalog ``get_columns``)
    estimated_s = round_trips * rtt_s + n_columns * inter_query_delay_s

The issue #1329 field case (53 min vs 4257×140 ms ≈ 10 min) is expected: the
floor is **latency only**. Query execution, pooling, and discovery extras sit
on top. ``--plan`` **warns**; it does **not** abort.

Latency classes (explicit ruler):

* **local** — loopback host, or measured TCP connect RTT **< 5 ms**
* **lan** — RTT in **[5 ms, 20 ms)**
* **remote** — RTT **≥ 20 ms**
* **unknown** — no TCP peer or connect failed

Slow warning (still no abort) when **either**:

* RTT-floor **≥ 600 s** (10 min), or
* class **remote**, RTT **≥ 50 ms**, and **≥ 200** columns
"""

from __future__ import annotations

import ipaddress
import socket
import time
from collections.abc import Callable
from typing import Any
from urllib.parse import urlparse

# Engines whose live scan is table/column sampling (SQLAlchemy or Snowflake).
SQL_CATALOG_ENGINES = frozenset(
    {
        "postgresql",
        "mysql",
        "mariadb",
        "sqlite",
        "mssql",
        "oracle",
        "snowflake",
    }
)

DEFAULT_TCP_PORTS: dict[str, int] = {
    "postgresql": 5432,
    "mysql": 3306,
    "mariadb": 3306,
    "mssql": 1433,
    "oracle": 1521,
    "mongodb": 27017,
    "redis": 6379,
    "snowflake": 443,
    "smb": 445,
    "cifs": 445,
    "nfs": 2049,
}

LOCAL_RTT_MS = 5.0
REMOTE_RTT_MS = 20.0
SLOW_RTT_FLOOR_SECONDS = 600.0
WARN_REMOTE_RTT_MS = 50.0
WARN_REMOTE_MIN_COLUMNS = 200

MeasureRttFn = Callable[[str, int], float | None]
EnumerateSqlFn = Callable[[dict[str, Any]], tuple[int | None, int | None, str | None]]


def rtt_peer_guard(
    target: dict[str, Any], host: str, port: int
) -> tuple[str | None, str | None]:
    """Same SSRF gate + TCP pin as live SQL/Mongo/Redis (#832 / #1586).

    Live connectors call ``resolve_and_validate_outbound_url`` then connect
    to ``primary_pin_str(ips)`` (or an equivalent driver pin). ``--plan``
    must not probe RTT (or catalog-connect) when the guard refuses the
    target, and must not pass the original hostname to
    ``socket.create_connection`` (DNS rebinding TOCTOU).
    """
    from connectors.tcp_pin import primary_pin_str
    from connectors.url_guard import (
        resolve_and_validate_outbound_url,
        target_allows_private,
    )

    err, ips = resolve_and_validate_outbound_url(
        f"{host}:{int(port)}",
        allow_private=target_allows_private(target),
        label="host",
    )
    if err:
        return err, None
    if not ips:
        return (
            (
                "host rejected: no pin IPs after outbound validation. "
                "Fail-closed — refusing RTT probe. (#1586)"
            ),
            None,
        )
    return None, primary_pin_str(ips)


def measure_tcp_rtt_ms(
    host: str,
    port: int,
    *,
    timeout_s: float = 2.0,
) -> float | None:
    """One TCP connect RTT in milliseconds, or None on failure.

    *host* must be a **literal IP** already approved by
    :func:`rtt_peer_guard` (same pin as live connectors, #1586). Passing a
    DNS name would re-resolve and reopen DNS rebinding. Completes the
    handshake and closes. Injectable in tests — do not call this against
    external hosts from CI.
    """
    from connectors.tcp_pin import is_ip_literal

    if not host or not port:
        return None
    if not is_ip_literal(host):
        return None
    try:
        port_i = int(port)
    except (TypeError, ValueError):
        return None
    if port_i <= 0 or port_i > 65535:
        return None
    start = time.monotonic()
    try:
        with socket.create_connection((host, port_i), timeout=timeout_s):
            pass
    except OSError:
        return None
    return (time.monotonic() - start) * 1000.0


def is_loopback_host(host: str | None) -> bool:
    if not host:
        return False
    h = host.strip().lower().strip("[]")
    if h in {"localhost", "localhost.localdomain"}:
        return True
    try:
        return ipaddress.ip_address(h).is_loopback
    except ValueError:
        return False


def classify_latency(host: str | None, rtt_ms: float | None) -> str:
    """Return local | lan | remote | unknown. See module docstring for thresholds."""
    if is_loopback_host(host):
        return "local"
    if rtt_ms is None:
        return "unknown"
    if rtt_ms < LOCAL_RTT_MS:
        return "local"
    if rtt_ms >= REMOTE_RTT_MS:
        return "remote"
    return "lan"


def estimate_sql_rtt_floor_seconds(
    *,
    n_tables: int,
    n_columns: int,
    rtt_ms: float | None,
    inter_query_delay_s: float = 0.0,
    include_table_row_estimate: bool = True,
) -> float | None:
    """Latency floor for a SQL/Snowflake column-sampling scan. None if no RTT.

    SQLAlchemy ``sample()`` runs ``estimate_table_rows`` once per table
    (``include_table_row_estimate=True`` → ``n_columns + 2 * n_tables``).
    Snowflake samples per column and lists columns per table but has no
    row-estimate query (``False`` → ``n_columns + n_tables``).
    """
    if rtt_ms is None:
        return None
    n_tables_i = max(0, int(n_tables))
    n_columns_i = max(0, int(n_columns))
    round_trips = n_columns_i + n_tables_i
    if include_table_row_estimate:
        round_trips += n_tables_i
    return (round_trips * (float(rtt_ms) / 1000.0)) + (
        n_columns_i * max(0.0, float(inter_query_delay_s))
    )


def should_warn_slow(
    *,
    classification: str,
    rtt_ms: float | None,
    n_columns: int | None,
    estimated_s: float | None,
) -> bool:
    if estimated_s is not None and estimated_s >= SLOW_RTT_FLOOR_SECONDS:
        return True
    cols = int(n_columns or 0)
    return (
        classification == "remote"
        and rtt_ms is not None
        and rtt_ms >= WARN_REMOTE_RTT_MS
        and cols >= WARN_REMOTE_MIN_COLUMNS
    )


def sql_engine_key(target: dict[str, Any]) -> str | None:
    t = str(target.get("type") or "").strip().lower()
    driver = str(target.get("driver") or "").split("+")[0].strip().lower()
    if t in SQL_CATALOG_ENGINES:
        return t
    if t == "database" and driver in SQL_CATALOG_ENGINES:
        return driver
    if driver in SQL_CATALOG_ENGINES:
        return driver
    return None


def resolve_tcp_peer(target: dict[str, Any]) -> tuple[str, int] | None:
    """Host/port for a TCP connect probe. None for sqlite files or missing peer."""
    engine = sql_engine_key(target)
    if engine == "sqlite":
        return None
    host = str(target.get("host") or "").strip()
    raw_port = target.get("port")
    typ = str(target.get("type") or "").strip().lower()
    driver = str(target.get("driver") or "").split("+")[0].strip().lower()
    key = engine or (typ if typ in DEFAULT_TCP_PORTS else driver)
    if not host:
        url = str(target.get("url") or target.get("base_url") or "").strip()
        if url:
            parsed = urlparse(url if "://" in url else f"//{url}", scheme="http")
            host = (parsed.hostname or "").strip()
            if raw_port is None and parsed.port:
                raw_port = parsed.port
    if not host:
        return None
    if raw_port is not None and str(raw_port).strip() != "":
        try:
            port = int(raw_port)
        except (TypeError, ValueError):
            return None
    else:
        default = DEFAULT_TCP_PORTS.get(key or "")
        if default is None:
            return None
        port = default
    return host, port


def default_enumerate_sql_scope(
    target: dict[str, Any],
) -> tuple[int | None, int | None, str | None]:
    """Connect + ``discover()`` only (no ``sample()``). Returns tables, columns, error."""
    engine = sql_engine_key(target)
    if engine is None:
        return None, None, None
    if engine == "snowflake":
        try:
            from connectors.snowflake_connector import SnowflakeConnector
        except ImportError as exc:
            return None, None, f"snowflake catalog unavailable: {exc}"
        conn: Any = SnowflakeConnector(target, scanner=None, db_manager=None)
        try:
            conn.connect()
            tables = conn._list_tables()
            n_tables = len(tables)
            n_columns = 0
            for item in tables:
                cols = conn._get_columns(
                    item.get("schema") or "", item.get("table") or ""
                )
                n_columns += len(cols)
            return n_tables, n_columns, None
        except Exception as exc:  # noqa: BLE001 — catalog errors become plan rows
            return None, None, f"{type(exc).__name__}: {exc}"
        finally:
            try:
                conn.close()
            except Exception:  # noqa: BLE001, S110 — best-effort close
                pass
    from connectors.sql_connector import SQLConnector

    conn = SQLConnector(target, scanner=None, db_manager=None)
    try:
        conn.connect()
        discovered = conn.discover()
    except Exception as exc:  # noqa: BLE001 — catalog errors become plan rows
        return None, None, f"{type(exc).__name__}: {exc}"
    finally:
        try:
            conn.close()
        except Exception:  # noqa: BLE001, S110 — best-effort close
            pass
    if not isinstance(discovered, list):
        return None, None, "discover() did not return a table list"
    n_tables = len(discovered)
    n_columns = 0
    for item in discovered:
        cols = item.get("columns") if isinstance(item, dict) else None
        n_columns += len(cols) if isinstance(cols, list) else 0
    return n_tables, n_columns, None


def _inter_query_delay_s(target: dict[str, Any]) -> float:
    try:
        return max(0.0, float(target.get("inter_query_delay_ms", 0) or 0) / 1000.0)
    except (TypeError, ValueError):
        return 0.0


def format_duration_seconds(seconds: float) -> str:
    if seconds < 1:
        return f"{seconds * 1000:.0f} ms"
    if seconds < 90:
        return f"{seconds:.0f} s"
    minutes = seconds / 60.0
    if minutes < 90:
        return f"{minutes:.0f} min"
    return f"{minutes / 60.0:.1f} h"


def format_scan_plan_report(target_rows: list[dict[str, Any]]) -> str:
    lines = [
        "Scan plan (catalog + TCP RTT only — no column sampling, no findings)",
        "",
        (
            "Cost model: SQL scan ≈ 1 sample query/column + 1 row-estimate/table "
            "+ catalog get_columns/table. Estimate is an RTT floor; wall-clock is higher."
        ),
        "Latency: local = loopback or RTT < 5 ms; lan = 5–20 ms; remote = RTT ≥ 20 ms.",
        "Warn (does not abort) if RTT-floor ≥ 10 min, or remote RTT ≥ 50 ms with ≥ 200 columns.",
        "",
    ]
    any_warn = False
    for row in target_rows:
        name = row.get("name") or "(unnamed)"
        typ = row.get("type") or "?"
        lines.append(f"Target: {name} ({typ})")
        peer = row.get("peer")
        if peer:
            lines.append(f"  Peer: {peer}")
        rtt = row.get("rtt_ms")
        klass = row.get("classification") or "unknown"
        skip = row.get("rtt_skip_reason")
        if skip:
            lines.append(
                "  RTT: skipped (network policy — same SSRF guard as live scan)"
            )
            lines.append(f"  Skip: {skip}")
        elif rtt is None:
            lines.append(f"  RTT: not measured ({klass})")
        else:
            lines.append(f"  RTT: {rtt:.0f} ms ({klass})")
        n_tables = row.get("n_tables")
        n_columns = row.get("n_columns")
        enum_note = row.get("enum_note")
        if n_tables is not None and n_columns is not None:
            lines.append(
                f"  Scope: {n_tables} tables, {n_columns} columns (catalog only)"
            )
        elif enum_note:
            lines.append(f"  Scope: {enum_note}")
        else:
            lines.append(
                "  Scope: not a SQL/Snowflake catalog target "
                "(no table/column enumeration)"
            )
        err = row.get("enum_error")
        if err:
            lines.append(f"  Catalog error: {err}")
        est = row.get("estimated_s")
        if est is not None:
            n_t = int(n_tables or 0)
            n_c = int(n_columns or 0)
            rt = n_c + n_t
            if row.get("include_table_row_estimate", True):
                rt += n_t
            lines.append(
                f"  Estimated RTT-floor: ~{format_duration_seconds(est)} "
                f"({rt} round-trips × RTT"
                + (
                    f" + inter_query_delay × {int(n_columns or 0)} columns"
                    if row.get("inter_query_delay_s")
                    else ""
                )
                + ")"
            )
        if row.get("warn"):
            any_warn = True
            lines.append(
                "  WARN: likely slow/remote. Re-scope schemas or run in-region "
                "before a live scan. --plan does not abort."
            )
        lines.append("")
    if any_warn:
        lines.append(
            "One or more targets look expensive. Review the WARN lines, then run "
            "without --plan when you are ready."
        )
    else:
        lines.append("No slow/remote WARN. Proceed without --plan when you are ready.")
    return "\n".join(lines).rstrip() + "\n"


def plan_one_target(
    target: dict[str, Any],
    *,
    measure_rtt: MeasureRttFn = measure_tcp_rtt_ms,
    enumerate_sql: EnumerateSqlFn = default_enumerate_sql_scope,
) -> dict[str, Any]:
    name = target.get("name") or ""
    typ = target.get("type") or ""
    peer_t = resolve_tcp_peer(target)
    rtt_ms: float | None = None
    peer_s: str | None = None
    host: str | None = None
    rtt_skip_reason: str | None = None
    if peer_t:
        host, port = peer_t
        peer_s = f"{host}:{port}"
        rtt_skip_reason, pin_host = rtt_peer_guard(target, host, port)
        if rtt_skip_reason is None and pin_host:
            rtt_ms = measure_rtt(pin_host, port)
    classification = classify_latency(host, rtt_ms)
    engine = sql_engine_key(target)
    n_tables: int | None = None
    n_columns: int | None = None
    enum_error: str | None = None
    if engine and rtt_skip_reason is None:
        n_tables, n_columns, enum_error = enumerate_sql(target)
        if engine == "sqlite":
            classification = "local"
    delay_s = _inter_query_delay_s(target)
    estimated_s = None
    include_row_est = engine != "snowflake"
    if n_tables is not None and n_columns is not None:
        rtt_for_floor = (
            0.0 if (classification == "local" and rtt_ms is None) else rtt_ms
        )
        estimated_s = estimate_sql_rtt_floor_seconds(
            n_tables=n_tables,
            n_columns=n_columns,
            rtt_ms=rtt_for_floor,
            inter_query_delay_s=delay_s,
            include_table_row_estimate=include_row_est,
        )
    warn = should_warn_slow(
        classification=classification,
        rtt_ms=rtt_ms,
        n_columns=n_columns,
        estimated_s=estimated_s,
    )
    return {
        "name": name,
        "type": typ,
        "peer": peer_s,
        "rtt_ms": rtt_ms,
        "classification": classification,
        "n_tables": n_tables,
        "n_columns": n_columns,
        "enum_error": enum_error,
        "rtt_skip_reason": rtt_skip_reason,
        "estimated_s": estimated_s,
        "inter_query_delay_s": delay_s,
        "include_table_row_estimate": include_row_est,
        "warn": warn,
    }


def run_scan_plan(
    config: dict[str, Any],
    *,
    measure_rtt: MeasureRttFn = measure_tcp_rtt_ms,
    enumerate_sql: EnumerateSqlFn = default_enumerate_sql_scope,
) -> str:
    targets = config.get("targets") or []
    if not isinstance(targets, list) or not targets:
        return "Scan plan: no targets in config. Add targets, then re-run --plan.\n"
    rows = [
        plan_one_target(t, measure_rtt=measure_rtt, enumerate_sql=enumerate_sql)
        for t in targets
        if isinstance(t, dict)
    ]
    return format_scan_plan_report(rows)
