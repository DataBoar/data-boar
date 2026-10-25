"""
Canonical scope-import CSV to Data Boar config fragments (targets only).

See docs/plans/PLAN_SCOPE_IMPORT_FROM_EXPORTS.md. Emits YAML for operator review;
merge into config.yaml under ``targets:`` (never overwrites secrets silently).
"""

from __future__ import annotations

import csv
import io
import re
from typing import Any

import yaml

# Hard cap to avoid accidental huge pastes.
_MAX_DATA_ROWS = 5000

_MERGE_HINT = """# Data Boar scope import fragment (targets only)
# Merge: paste under ``targets:`` in your config, or include this file from tooling you trust.
# Review before scan: paths, hosts, and credential env refs. Do not put live secrets in CSV.
# Exports may contain sensitive infrastructure metadata — treat like config (permissions, no public commits).
"""


def _strip_leading_garbage(text: str) -> str:
    """Drop leading blank lines and full-line ``#`` comments (before the header row)."""
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        s = lines[i].strip()
        if not s:
            i += 1
            continue
        if s.startswith("#"):
            i += 1
            continue
        break
    return "\n".join(lines[i:])


def _norm_header(h: str) -> str:
    return (h or "").strip().lower().replace(" ", "_")


def _parse_bool(raw: str | None, default: bool = True) -> bool:
    if raw is None or str(raw).strip() == "":
        return default
    s = str(raw).strip().lower()
    if s in ("1", "true", "yes", "y", "on"):
        return True
    if s in ("0", "false", "no", "n", "off"):
        return False
    return default


def _split_multi(raw: str | None) -> list[str]:
    if raw is None:
        return []
    s = str(raw).strip()
    if not s:
        return []
    if "|" in s:
        return [x.strip() for x in s.split("|") if x.strip()]
    if ";" in s:
        return [x.strip() for x in s.split(";") if x.strip()]
    return [s]


def _empty_row(row: dict[str, str]) -> bool:
    return not any((v or "").strip() for v in row.values())


def _resolve_type_and_driver(
    type_raw: str,
    driver_col: str,
) -> tuple[str, str | None]:
    """Return (canonical_type, driver or None)."""
    t = type_raw.strip().lower()
    d = (driver_col or "").strip()

    aliases_db = {
        "postgres": "postgresql",
        "postgresql": "postgresql",
        "pg": "postgresql",
        "mysql": "mysql",
        "mariadb": "mysql",
        "mssql": "mssql",
        "sqlserver": "mssql",
        "sqlite": "sqlite",
        "oracle": "oracle",
    }
    if t in aliases_db:
        base = aliases_db[t]
        if d:
            return "database", d
        if base == "postgresql":
            return "database", "postgresql"
        if base == "mysql":
            return "database", "mysql"
        if base == "mssql":
            return "database", "mssql"
        if base == "sqlite":
            return "database", "sqlite"
        if base == "oracle":
            return "database", "oracle"

    if t in ("fs", "file", "filesystem", "path"):
        return "filesystem", None
    if t in ("smb", "cifs"):
        return "smb", None
    if t == "nfs":
        return "nfs", None
    if t == "database" or t == "db":
        return "database", d or None

    return t, None


def _int_or_none(raw: str | None) -> int | None:
    if raw is None or str(raw).strip() == "":
        return None
    try:
        return int(str(raw).strip(), 10)
    except ValueError:
        return None


def _scope_meta(row: dict[str, str]) -> dict[str, Any] | None:
    meta: dict[str, Any] = {}
    aid = (row.get("asset_id") or "").strip()
    if aid:
        meta["asset_id"] = aid
    hostn = (row.get("hostname") or "").strip()
    if hostn:
        meta["hostname"] = hostn
    ip = (row.get("ip") or "").strip()
    if ip:
        meta["ip"] = ip
    tags = _split_multi(row.get("tags"))
    if tags:
        meta["tags"] = tags
    ph = _split_multi(row.get("path_hints"))
    if ph:
        meta["path_hints"] = ph
    pp = _split_multi(row.get("port_hints"))
    if pp:
        meta["port_hints"] = pp
    src = (row.get("source_system") or "").strip()
    if src:
        meta["source_system"] = src
    ex = (row.get("source_export_type") or "").strip()
    if ex:
        meta["source_export_type"] = ex
    conf = (row.get("confidence") or "").strip()
    if conf:
        meta["confidence"] = conf
    return meta or None


def _default_name(
    row: dict[str, str],
    canonical: str,
    data_index: int,
) -> str:
    for key in ("name", "asset_id", "hostname", "host", "path"):
        v = (row.get(key) or "").strip()
        if v:
            safe = re.sub(r"[^\w.\-]+", "_", v)[:120]
            if safe:
                return safe
    return f"import-{canonical}-{data_index}"


def _row_to_target(row: dict[str, str], data_index: int) -> dict[str, Any]:
    """Build one target dict from a normalized CSV row (keys lowercased)."""
    type_raw = (row.get("type") or "").strip()
    if not type_raw:
        raise ValueError("missing required column value: type")

    canonical, driver = _resolve_type_and_driver(type_raw, row.get("driver") or "")

    name = (row.get("name") or "").strip() or _default_name(row, canonical, data_index)

    meta = _scope_meta(row)
    port = _int_or_none(row.get("port"))

    target: dict[str, Any] = {"name": name, "type": canonical}

    if canonical == "filesystem":
        path = (row.get("path") or "").strip()
        if not path:
            raise ValueError("type filesystem requires path")
        target["path"] = path
        target["recursive"] = _parse_bool(row.get("recursive"), True)
    elif canonical == "database":
        if not driver:
            raise ValueError(
                "type database requires driver (or use alias postgresql/mysql/...)"
            )
        target["driver"] = driver
        host = (row.get("host") or "").strip()
        if not host:
            raise ValueError("type database requires host")
        target["host"] = host
        if port is not None:
            target["port"] = port
        dbname = (row.get("database") or row.get("db") or "").strip()
        if not dbname:
            raise ValueError("type database requires database")
        target["database"] = dbname
        user = (row.get("user") or row.get("username") or "").strip()
        if user:
            target["user"] = user
        pfe = (row.get("pass_from_env") or row.get("password_from_env") or "").strip()
        if pfe:
            target["pass_from_env"] = pfe
        ufe = (row.get("user_from_env") or "").strip()
        if ufe:
            target["user_from_env"] = ufe
    elif canonical == "smb":
        host = (row.get("host") or "").strip()
        if not host:
            raise ValueError("type smb requires host")
        target["host"] = host
        share = (row.get("share") or "").strip()
        if not share:
            raise ValueError("type smb requires share")
        target["share"] = share
        if port is not None:
            target["port"] = port
        sub = (row.get("path") or "").strip()
        if sub:
            target["path"] = sub
        user = (row.get("user") or row.get("username") or "").strip()
        if user:
            target["user"] = user
        pfe = (row.get("pass_from_env") or row.get("password_from_env") or "").strip()
        if pfe:
            target["pass_from_env"] = pfe
        dom = (row.get("domain") or "").strip()
        if dom:
            target["domain"] = dom
        target["recursive"] = _parse_bool(row.get("recursive"), True)
    elif canonical == "nfs":
        path = (row.get("path") or "").strip()
        if not path:
            raise ValueError("type nfs requires path (local mount point)")
        target["path"] = path
        host = (row.get("host") or row.get("server") or "").strip()
        if host:
            target["host"] = host
        exp = (row.get("export_path") or "").strip()
        if exp:
            target["export_path"] = exp
        target["recursive"] = _parse_bool(row.get("recursive"), True)
    else:
        raise ValueError(
            f"unsupported type for scope import v1: {canonical!r} "
            f"(use filesystem, database, postgresql, mysql, smb, nfs)"
        )

    if meta:
        target["scope_import"] = meta
    return target


def parse_scope_import_csv(text: str) -> list[dict[str, str]]:
    """
    Parse CSV text; return list of rows as dicts with lowercased keys.
    Skips blank rows and full-line # comments (after stripping comment lines).
    """
    cleaned = _strip_leading_garbage(text)
    if not cleaned.strip():
        return []

    f = io.StringIO(cleaned)
    reader = csv.DictReader(f)
    if reader.fieldnames is None:
        return []

    norm_headers = {_norm_header(str(h)) for h in reader.fieldnames if h is not None}
    if "type" not in norm_headers:
        raise ValueError("CSV header must include a column named 'type'")

    rows_out: list[dict[str, str]] = []
    for raw in reader:
        row: dict[str, str] = {}
        for k, v in raw.items():
            if k is None:
                continue
            nk = _norm_header(str(k))
            if not nk:
                continue
            row[nk] = (v or "").strip()
        if _empty_row(row):
            continue
        rows_out.append(row)

    if len(rows_out) > _MAX_DATA_ROWS:
        raise ValueError(f"too many data rows (max {_MAX_DATA_ROWS})")

    return rows_out


def rows_to_targets(rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    """Turn normalized CSV rows into Data Boar target dicts."""
    targets: list[dict[str, Any]] = []
    for i, row in enumerate(rows, start=1):
        targets.append(_row_to_target(row, i))
    return targets


def emit_scope_fragment_yaml(
    targets: list[dict[str, Any]], *, merge_hint: bool = True
) -> str:
    """YAML document with a single ``targets:`` list (fragment)."""
    payload = {"targets": targets}
    body = yaml.safe_dump(
        payload,
        sort_keys=False,
        allow_unicode=True,
        default_flow_style=False,
    )
    if merge_hint:
        return _MERGE_HINT + "\n" + body
    return body


def csv_to_fragment_yaml(text: str, *, merge_hint: bool = True) -> str:
    """Parse canonical CSV and return a YAML config fragment."""
    rows = parse_scope_import_csv(text)
    targets = rows_to_targets(rows)
    return emit_scope_fragment_yaml(targets, merge_hint=merge_hint)
