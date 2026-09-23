#!/usr/bin/env python3
"""Post-scan sentinel for Maestro RC profiles (benchmark-rc-v2).

Validates SQLite findings for required patterns and runs static negative SSRF/auth
guard cases. Exit 0 = pass, 1 = sentinel fail, 2 = usage/config error.

Refs: maestro#82, data-boar#1980 (gap report §E).
"""

from __future__ import annotations

import argparse
import importlib.util
import re
import socket
import sqlite3
import sys
from pathlib import Path
from typing import Any

import yaml

_REPO_ROOT = Path(__file__).resolve().parents[1]


def _load_yaml(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise FileNotFoundError(path)
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"expected mapping in {path}")
    return data


def _default_sentinel_path(config_path: Path) -> Path:
    stem = config_path.name
    if stem.endswith(".yaml"):
        stem = stem[:-5]
    return config_path.with_name(f"{stem}.sentinel.yaml")


def _default_negative_path() -> Path:
    return _REPO_ROOT / "tests/config/benchmark-rc-ssrf-negative.yaml"


def _sqlite_path_from_config(config: dict[str, Any]) -> Path:
    raw = (config.get("sqlite_path") or "audit_results.db").strip()
    return (_REPO_ROOT / raw).resolve()


def _probe_reachable(spec: str, timeout: float = 2.0) -> bool:
    if not spec or not spec.startswith("tcp:"):
        return True
    rest = spec[4:]
    if rest.count(":") == 1:
        host, port_s = rest.rsplit(":", 1)
        port = int(port_s)
    else:
        host, port_s = rest, "443"
        port = int(port_s)
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def _safe_table(name: str) -> str:
    if not re.fullmatch(r"[a-z_]+", name):
        raise ValueError(f"unsafe table name: {name!r}")
    return name


def _count_pattern(
    conn: sqlite3.Connection,
    table: str,
    session_id: str,
    pattern: str,
    target_prefix: str | None = None,
) -> int:
    table_id = _safe_table(table)
    if table_id == "filesystem_findings":
        q = (
            f"SELECT COUNT(*) FROM {table_id} "
            "WHERE session_id = ? AND pattern_detected LIKE ?"
        )
        params: list[Any] = [session_id, f"%{pattern}%"]
        if target_prefix:
            q += " AND target_name LIKE ?"
            params.append(f"{target_prefix}%")
    elif table_id in ("database_findings", "application_findings"):
        q = (
            f"SELECT COUNT(*) FROM {table_id} "
            "WHERE session_id = ? AND pattern_detected LIKE ?"
        )
        params = [session_id, f"%{pattern}%"]
        if target_prefix:
            q += " AND target_name LIKE ?"
            params.append(f"{target_prefix}%")
    else:
        raise ValueError(f"unsupported table: {table}")
    row = conn.execute(q, params).fetchone()
    return int(row[0]) if row else 0


def _count_rows(conn: sqlite3.Connection, table: str, session_id: str) -> int:
    table_id = _safe_table(table)
    row = conn.execute(
        f"SELECT COUNT(*) FROM {table_id} WHERE session_id = ?",
        (session_id,),
    ).fetchone()
    return int(row[0]) if row else 0


def _latest_session_id(conn: sqlite3.Connection) -> str | None:
    row = conn.execute(
        "SELECT session_id FROM scan_sessions ORDER BY started_at DESC LIMIT 1"
    ).fetchone()
    return str(row[0]) if row else None


def _check_findings_sentinel(
    config_path: Path,
    sentinel_path: Path,
    sqlite_path: Path,
) -> list[str]:
    errors: list[str] = []
    sentinel = _load_yaml(sentinel_path)
    if not sqlite_path.is_file():
        return [f"sqlite missing: {sqlite_path} (run main.py --config first)"]

    conn = sqlite3.connect(str(sqlite_path))
    try:
        session_id = _latest_session_id(conn)
        if not session_id:
            return ["no scan_sessions row in sqlite"]

        total = sum(
            _count_rows(conn, t, session_id)
            for t in (
                "filesystem_findings",
                "database_findings",
                "application_findings",
            )
        )
        min_total = int(sentinel.get("min_total_findings") or 0)
        if total < min_total:
            errors.append(
                f"total_findings={total} < min_total_findings={min_total} "
                f"(session={session_id})"
            )

        for req in sentinel.get("required_patterns") or []:
            if not isinstance(req, dict):
                continue
            pattern = str(req.get("pattern") or "")
            min_count = int(req.get("min_count") or 1)
            tables = req.get("tables") or ["filesystem_findings"]
            got = 0
            for table in tables:
                got += _count_pattern(conn, str(table), session_id, pattern)
            if got < min_count:
                errors.append(
                    f"{req.get('id', pattern)}: count={got} < min_count={min_count}"
                )

        for opt in sentinel.get("optional_connectors") or []:
            if not isinstance(opt, dict):
                continue
            probe = str(opt.get("probe") or "")
            if probe and not _probe_reachable(probe):
                print(
                    f"SKIP optional {opt.get('id')}: probe unreachable ({probe})",
                    file=sys.stderr,
                )
                continue
            prefix = str(opt.get("target_name_prefix") or "")
            pattern = opt.get("pattern")
            if pattern:
                min_count = int(opt.get("min_count") or 1)
                tables = opt.get("tables") or ["database_findings"]
                got = 0
                for table in tables:
                    got += _count_pattern(
                        conn, str(table), session_id, str(pattern), prefix or None
                    )
                if got < min_count:
                    errors.append(
                        f"optional {opt.get('id')}: pattern count={got} < {min_count}"
                    )
            min_app = opt.get("min_application_findings")
            if min_app is not None:
                if prefix:
                    row = conn.execute(
                        "SELECT COUNT(*) FROM application_findings "
                        "WHERE session_id = ? AND target_name LIKE ?",
                        (session_id, f"{prefix}%"),
                    ).fetchone()
                    got = int(row[0]) if row else 0
                else:
                    got = _count_rows(conn, "application_findings", session_id)
                if got < int(min_app):
                    errors.append(
                        f"optional {opt.get('id')}: application_findings={got} "
                        f"< {min_app}"
                    )
    finally:
        conn.close()

    if errors:
        print(f"config={config_path}", file=sys.stderr)
    return errors


def _match_error(exc: BaseException, substrings: list[str]) -> bool:
    text = str(exc)
    return any(s in text for s in substrings)


def _check_negative_ssrf(negative_path: Path) -> list[str]:
    errors: list[str] = []
    if importlib.util.find_spec("httpx") is None:
        return ["httpx not installed — cannot run negative SSRF cases"]

    from connectors.rest_connector import RESTConnector

    data = _load_yaml(negative_path)
    for case in data.get("cases") or []:
        if not isinstance(case, dict):
            continue
        case_id = str(case.get("id") or "case")
        target = case.get("target")
        if not isinstance(target, dict):
            errors.append(f"{case_id}: missing target dict")
            continue
        match_subs = [str(s) for s in (case.get("match_substrings") or [])]
        conn = RESTConnector(target, scanner=None, db_manager=None)
        try:
            conn.connect()
        except ValueError as exc:
            if not match_subs or _match_error(exc, match_subs):
                print(f"NEGATIVE_OK {case_id}: {exc}")
                continue
            errors.append(f"{case_id}: ValueError but no match: {exc}")
        except Exception as exc:
            if match_subs and _match_error(exc, match_subs):
                print(f"NEGATIVE_OK {case_id}: {exc}")
                continue
            errors.append(
                f"{case_id}: expected failure, got {type(exc).__name__}: {exc}"
            )
        else:
            conn.close()
            errors.append(f"{case_id}: connect succeeded (expected failure)")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config",
        type=Path,
        default=_REPO_ROOT / "tests/config/benchmark-rc-v2.yaml",
        help="RC YAML used for the scan (default: benchmark-rc-v2.yaml)",
    )
    parser.add_argument(
        "--sentinel",
        type=Path,
        default=None,
        help="Sentinel thresholds YAML (default: <config>.sentinel.yaml)",
    )
    parser.add_argument(
        "--sqlite",
        type=Path,
        default=None,
        help="SQLite path override (default: sqlite_path from loaded config)",
    )
    parser.add_argument(
        "--negative-ssrf",
        type=Path,
        default=_default_negative_path(),
        help="Negative SSRF/auth fixture YAML",
    )
    parser.add_argument(
        "--skip-negative-ssrf",
        action="store_true",
        help="Only run findings sentinel (no static negative cases)",
    )
    parser.add_argument(
        "--skip-findings",
        action="store_true",
        help="Only run negative SSRF cases",
    )
    args = parser.parse_args()

    config_path = args.config.resolve()
    if not config_path.is_file():
        print(f"missing config: {config_path}", file=sys.stderr)
        return 2

    sentinel_path = (args.sentinel or _default_sentinel_path(config_path)).resolve()
    boar_config = _load_yaml(config_path)
    sqlite_path = (args.sqlite or _sqlite_path_from_config(boar_config)).resolve()

    failures: list[str] = []
    if not args.skip_findings:
        failures.extend(
            _check_findings_sentinel(config_path, sentinel_path, sqlite_path)
        )
    if not args.skip_negative_ssrf:
        failures.extend(_check_negative_ssrf(args.negative_ssrf.resolve()))

    if failures:
        for line in failures:
            print(f"SENTINEL_FAIL: {line}", file=sys.stderr)
        return 1

    print("SENTINEL_OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
