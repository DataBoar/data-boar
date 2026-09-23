#!/usr/bin/env python3
"""Post-scan sentinel for Maestro RC profiles (benchmark-rc-v3).

Validates SQLite findings for required patterns (min_count / max_count), optional
connector probes, forbidden pattern substrings, and static negative SSRF/auth cases.
Exit 0 = pass, 1 = sentinel fail, 2 = usage/config error.

Refs: maestro#82, maestro#86, data-boar#1980 (gap report §E), data-boar#1985.
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

# Sentinel YAML only references these SQLite tables (validated before query build).
_SENTINEL_TABLES = frozenset(
    {"filesystem_findings", "database_findings", "application_findings"}
)

_LIKE_ESCAPE_CHAR = "\\"


def _like_prefix_param(prefix: str) -> str:
    """Literal prefix for SQL LIKE … ESCAPE '\\' (SQLite _/% are not wildcards)."""
    escaped = (
        prefix.replace(_LIKE_ESCAPE_CHAR, _LIKE_ESCAPE_CHAR * 2)
        .replace("%", _LIKE_ESCAPE_CHAR + "%")
        .replace("_", _LIKE_ESCAPE_CHAR + "_")
    )
    return f"{escaped}%"


def _target_name_prefix_clause() -> str:
    return f" AND target_name LIKE ? ESCAPE '{_LIKE_ESCAPE_CHAR}'"


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
    if table_id not in _SENTINEL_TABLES:
        raise ValueError(f"unsupported table: {table}")
    base = {
        "filesystem_findings": (
            "SELECT COUNT(*) FROM filesystem_findings "
            "WHERE session_id = ? AND pattern_detected LIKE ?"
        ),
        "database_findings": (
            "SELECT COUNT(*) FROM database_findings "
            "WHERE session_id = ? AND pattern_detected LIKE ?"
        ),
        "application_findings": (
            "SELECT COUNT(*) FROM application_findings "
            "WHERE session_id = ? AND pattern_detected LIKE ?"
        ),
    }[table_id]
    params: list[Any] = [session_id, f"%{pattern}%"]
    q = base
    if target_prefix:
        q += _target_name_prefix_clause()
        params.append(_like_prefix_param(target_prefix))
    row = conn.execute(q, params).fetchone()
    return int(row[0]) if row else 0


def _count_rows_in_target_scope(
    conn: sqlite3.Connection,
    table: str,
    session_id: str,
    target_prefix: str,
) -> int:
    table_id = _safe_table(table)
    if table_id not in _SENTINEL_TABLES:
        raise ValueError(f"unsupported table: {table}")
    row = conn.execute(
        f"SELECT COUNT(*) FROM {table_id} WHERE session_id = ?"
        + _target_name_prefix_clause(),
        (session_id, _like_prefix_param(target_prefix)),
    ).fetchone()
    return int(row[0]) if row else 0


def _scope_rows_for_tables(
    conn: sqlite3.Connection,
    session_id: str,
    tables: list[Any],
    target_prefix: str,
) -> int:
    return sum(
        _count_rows_in_target_scope(conn, str(table), session_id, target_prefix)
        for table in tables
    )


def _append_scope_empty_error(
    errors: list[str],
    rule_id: str,
    target_prefix: str,
    *,
    xfail: bool,
) -> None:
    msg = (
        f"{rule_id}: scope_empty (no findings rows for "
        f"target_name_prefix={target_prefix!r})"
    )
    if xfail:
        print(f"XFAIL_OK {msg}", file=sys.stderr)
    else:
        errors.append(msg)


def _count_forbidden_substrings(
    conn: sqlite3.Connection,
    table: str,
    session_id: str,
    substrings: list[str],
    target_prefix: str | None = None,
) -> int:
    if not substrings:
        return 0
    table_id = _safe_table(table)
    if table_id not in _SENTINEL_TABLES:
        raise ValueError(f"unsupported table: {table}")
    hits = 0
    q = f"SELECT pattern_detected FROM {table_id} WHERE session_id = ?"
    params: list[Any] = [session_id]
    if target_prefix:
        q += _target_name_prefix_clause()
        params.append(_like_prefix_param(target_prefix))
    for (pattern_detected,) in conn.execute(q, params):
        text = str(pattern_detected or "")
        if any(sub in text for sub in substrings):
            hits += 1
    return hits


def _append_pattern_bound_errors(
    errors: list[str],
    rule_id: str,
    got: int,
    *,
    min_count: int | None,
    max_count: int | None,
    xfail: bool,
) -> None:
    if min_count is not None and got < min_count:
        msg = f"{rule_id}: count={got} < min_count={min_count}"
    elif max_count is not None and got > max_count:
        msg = f"{rule_id}: count={got} > max_count={max_count}"
    else:
        return
    if xfail:
        print(f"XFAIL_OK {msg}", file=sys.stderr)
        return
    errors.append(msg)


def _count_rows(conn: sqlite3.Connection, table: str, session_id: str) -> int:
    table_id = _safe_table(table)
    if table_id not in _SENTINEL_TABLES:
        raise ValueError(f"unsupported table: {table}")
    queries = {
        "filesystem_findings": (
            "SELECT COUNT(*) FROM filesystem_findings WHERE session_id = ?"
        ),
        "database_findings": (
            "SELECT COUNT(*) FROM database_findings WHERE session_id = ?"
        ),
        "application_findings": (
            "SELECT COUNT(*) FROM application_findings WHERE session_id = ?"
        ),
    }
    row = conn.execute(queries[table_id], (session_id,)).fetchone()
    return int(row[0]) if row else 0


def _count_scan_failures(
    conn: sqlite3.Connection,
    session_id: str,
    target_prefix: str | None = None,
) -> int:
    if target_prefix:
        # B608 FP: table name is the literal scan_failures. The only append is
        # _target_name_prefix_clause() (no parameters, constant SQL). The prefix
        # value is bound via ? in _like_prefix_param(), never concatenated.
        row = conn.execute(
            "SELECT COUNT(*) FROM scan_failures "  # nosec B608
            "WHERE session_id = ?" + _target_name_prefix_clause(),
            (session_id, _like_prefix_param(target_prefix)),
        ).fetchone()
    else:
        row = conn.execute(
            "SELECT COUNT(*) FROM scan_failures WHERE session_id = ?",
            (session_id,),
        ).fetchone()
    return int(row[0]) if row else 0


def _latest_session_id(conn: sqlite3.Connection) -> tuple[str | None, str | None]:
    """Latest scan by started_at; only status=completed is acceptable evidence."""
    row = conn.execute(
        "SELECT session_id, status FROM scan_sessions ORDER BY started_at DESC LIMIT 1"
    ).fetchone()
    if not row:
        return None, "no scan_sessions row in sqlite"
    session_id = str(row[0])
    status = str(row[1] if row[1] is not None else "")
    if status != "completed":
        return None, (
            f"latest scan_sessions row has status={status!r}, expected 'completed' "
            f"(session_id={session_id})"
        )
    return session_id, None


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
        session_id, session_err = _latest_session_id(conn)
        if session_err:
            return [session_err]

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
            if not pattern:
                continue
            min_count = req.get("min_count")
            max_count = req.get("max_count")
            min_n = int(min_count) if min_count is not None else None
            max_n = int(max_count) if max_count is not None else None
            if min_n is None and max_n is None:
                min_n = 1
            tables = req.get("tables") or ["filesystem_findings"]
            prefix = str(req.get("target_name_prefix") or "") or None
            rule_label = str(req.get("id", pattern))
            xfail_req = bool(req.get("xfail"))
            if prefix:
                if _scope_rows_for_tables(conn, session_id, tables, prefix) == 0:
                    _append_scope_empty_error(
                        errors, rule_label, prefix, xfail=xfail_req
                    )
                    continue
            got = 0
            for table in tables:
                got += _count_pattern(conn, str(table), session_id, pattern, prefix)
            _append_pattern_bound_errors(
                errors,
                rule_label,
                got,
                min_count=min_n,
                max_count=max_n,
                xfail=xfail_req,
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
            rule_id = f"optional {opt.get('id')}"
            xfail = bool(opt.get("xfail"))
            tables_for_scope = list(opt.get("tables") or ["database_findings"])
            forbidden = [
                str(s) for s in (opt.get("forbidden_pattern_substrings") or [])
            ]
            require_clean_scan = bool(opt.get("require_no_scan_failure"))
            scope_has_rows = True
            # scope_empty only when bounds need evidence rows; require_no_scan_failure
            # already proves reachability + clean scan (#1983 / Bugbot #1981).
            if prefix and (pattern or forbidden) and not require_clean_scan:
                scope_has_rows = (
                    _scope_rows_for_tables(conn, session_id, tables_for_scope, prefix)
                    > 0
                )
                if not scope_has_rows:
                    _append_scope_empty_error(errors, rule_id, prefix, xfail=xfail)
            if pattern and scope_has_rows:
                min_count = opt.get("min_count")
                max_count = opt.get("max_count")
                min_n = int(min_count) if min_count is not None else None
                max_n = int(max_count) if max_count is not None else None
                if min_n is None and max_n is None:
                    min_n = 1
                got = 0
                for table in tables_for_scope:
                    got += _count_pattern(
                        conn,
                        str(table),
                        session_id,
                        str(pattern),
                        prefix or None,
                    )
                _append_pattern_bound_errors(
                    errors,
                    rule_id,
                    got,
                    min_count=min_n,
                    max_count=max_n,
                    xfail=xfail,
                )
            if forbidden and (scope_has_rows or require_clean_scan):
                max_forbidden = opt.get("max_forbidden_matches")
                cap = int(max_forbidden) if max_forbidden is not None else 0
                got_forbidden = 0
                for table in tables_for_scope:
                    got_forbidden += _count_forbidden_substrings(
                        conn,
                        str(table),
                        session_id,
                        forbidden,
                        prefix or None,
                    )
                if got_forbidden > cap:
                    msg = (
                        f"{rule_id}: forbidden_pattern_substrings matches="
                        f"{got_forbidden} > max_forbidden_matches={cap}"
                    )
                    if xfail:
                        print(f"XFAIL_OK {msg}", file=sys.stderr)
                    else:
                        errors.append(msg)
            if opt.get("require_no_scan_failure"):
                fail_n = _count_scan_failures(conn, session_id, prefix or None)
                if fail_n > 0:
                    errors.append(
                        f"optional {opt.get('id')}: scan_failures={fail_n} "
                        f"for target prefix {prefix!r}"
                    )
            min_app = opt.get("min_application_findings")
            if min_app is not None:
                if prefix:
                    # B608 FP: table name is the literal application_findings.
                    # Same constant clause and bound LIKE prefix as scan_failures.
                    row = conn.execute(
                        "SELECT COUNT(*) FROM application_findings "  # nosec B608
                        "WHERE session_id = ?" + _target_name_prefix_clause(),
                        (session_id, _like_prefix_param(prefix)),
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
        default=_REPO_ROOT / "tests/config/benchmark-rc-v3.yaml",
        help="RC YAML used for the scan (default: benchmark-rc-v3.yaml)",
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
