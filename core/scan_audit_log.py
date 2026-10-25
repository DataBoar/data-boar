"""
Declarative scan security / sampling posture for API and engine consumers.

This is **not** per-query telemetry: it documents what the product is configured to do
and which dialect-specific behaviours apply when database targets use those engines.

Doctrinal references (behaviour-preserving comments -- do not remove in refactors):

- ``docs/ops/inspirations/DEFENSIVE_SCANNING_MANIFESTO.md`` -- *test what you
  fly*: ``nolock``, ``statement_timeout_ms``, ``leading_sql_comment``, and the
  ``connector_default_statement_timeout_ms_when_unset`` constant below are the
  audit-log echo of the relief valves enforced in
  ``connectors/sql_sampling.py``. Anything ``GET /status`` or the executive
  report claims here must be backed by code that actually clamps.
- ``docs/ops/inspirations/ACTIONABLE_GOVERNANCE_AND_TRUST.md`` -- the
  ``disclaimer`` field below is the Tailscale / Charity Majors discipline:
  the system explains itself instead of pretending guarantees the runtime
  cannot deliver. Do not delete the disclaimer to make the JSON look tidier.
"""

from __future__ import annotations

import os
from typing import Any

from connectors.sql_sampling import (
    resolve_sql_sample_limit,
    resolve_statement_timeout_ms_for_sampling,
)
from core.sampling import SamplingPolicy


def _driver_implies_sql_server(driver: str) -> bool:
    d = (driver or "").lower()
    return "mssql" in d or "sqlserver" in d or "microsoft sql server" in d


def _driver_implies_postgresql(driver: str) -> bool:
    d = (driver or "").lower()
    return "postgres" in d or "psycopg" in d or "+pg" in d


def _database_targets_drivers(config: dict[str, Any]) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    for t in config.get("targets", []) or []:
        if not isinstance(t, dict):
            continue
        if (t.get("type") or "").strip().lower() != "database":
            continue
        name = (t.get("name") or "").strip() or "(unnamed)"
        drv = (t.get("driver") or "").strip()
        out.append((name, drv))
    return out


def _first_database_statement_timeout_explicit_ms(
    config: dict[str, Any],
) -> int | None:
    targets = config.get("targets", []) or []
    if not isinstance(targets, list):
        return None
    for t in targets:
        if (
            not isinstance(t, dict)
            or (t.get("type") or "").strip().lower() != "database"
        ):
            continue
        for key in (
            "sample_statement_timeout_ms",
            "sample_statement_timeout_seconds",
        ):
            if key not in t:
                continue
            v = t.get(key)
            if key.endswith("seconds"):
                try:
                    return int(float(v) * 1000)
                except (TypeError, ValueError):
                    continue
            else:
                try:
                    return int(v)
                except (TypeError, ValueError):
                    continue
    return None


def _sampling_provider_summary(config: dict[str, Any]) -> dict[str, Any]:
    pol = SamplingPolicy.from_config(config)
    targets_out: dict[str, Any] = {}
    for name, tcfg in pol.targets.items():
        if not isinstance(tcfg, dict):
            continue
        slim: dict[str, Any] = {}
        if "sample_limit" in tcfg:
            slim["sample_limit"] = tcfg.get("sample_limit")
        tables = tcfg.get("tables")
        if isinstance(tables, dict) and tables:
            slim["tables_override_count"] = len(tables)
        if slim:
            targets_out[str(name)] = slim
    return {
        "targets_with_overrides": sorted(targets_out.keys()),
        "pattern_globs_count": len(pol.patterns),
    }


def build_scan_audit_log(config: dict[str, Any]) -> dict[str, Any]:
    """
    JSON-serializable ``audit_log`` for ``GET /status`` and engine mirrors.

    ``nolock`` is ``True`` when the loaded config includes at least one database target
    whose driver string implies SQL Server (product uses ``WITH (NOLOCK)`` on sampling
    reads for that dialect).
    """
    file_scan = (
        config.get("file_scan") if isinstance(config.get("file_scan"), dict) else {}
    )
    global_lim = int(file_scan.get("sample_limit") or 1000)
    row_cap = resolve_sql_sample_limit(global_lim)

    explicit_to = _first_database_statement_timeout_explicit_ms(config)
    resolved_hint = resolve_statement_timeout_ms_for_sampling(explicit_to)

    db_drivers = _database_targets_drivers(config)
    nolock = any(_driver_implies_sql_server(d) for _, d in db_drivers)
    postgres = any(_driver_implies_postgresql(d) for _, d in db_drivers)

    timeout_ms = resolved_hint if resolved_hint is not None else explicit_to
    timeout_seconds: float | None
    if timeout_ms is not None and int(timeout_ms) > 0:
        timeout_seconds = round(float(timeout_ms) / 1000.0, 3)
    else:
        timeout_seconds = None

    return {
        "strategy": "sampling",
        "sampling_row_cap_per_column": row_cap,
        "nolock": nolock,
        "statement_timeout_ms": int(timeout_ms) if timeout_ms is not None else None,
        "statement_timeout_seconds": timeout_seconds,
        "connector_default_statement_timeout_ms_when_unset": 5000,
        "sampling_provider": _sampling_provider_summary(config),
        "database_targets_drivers": [{"name": n, "driver": d} for n, d in db_drivers],
        "postgresql_tablesample_on_large_tables": postgres,
        "leading_sql_comment": "-- Data Boar Compliance Scan",
        "env_DATA_BOAR_SQL_SAMPLE_LIMIT_set": bool(
            (os.environ.get("DATA_BOAR_SQL_SAMPLE_LIMIT") or "").strip()
        ),
        "env_DATA_BOAR_SAMPLE_STATEMENT_TIMEOUT_MS_set": bool(
            (os.environ.get("DATA_BOAR_SAMPLE_STATEMENT_TIMEOUT_MS") or "").strip()
        ),
        "disclaimer": (
            "Values describe configured product behaviour for this config, not a guarantee "
            "that every statement hit a given path; confirm with engine telemetry when required."
        ),
    }
