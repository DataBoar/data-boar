"""L3 transformed_rows producer — grant-scoped real-data plane (#1334).

Canonical schema: DataBoar/data-boar-sdk ``schema/transformed_rows.schema.json``.
INPUT rows carry raw ``value`` by contract. Protection is **scope** (never the
whole table) plus **ephemerality** (stdout/pipe unless ``--l3-persist``).

This is the inverse of L1: do not forbid ``value``; forbid unbounded projection
and accidental disk writes. Audit records grant id, columns, and row counts —
never cell contents.
"""

from __future__ import annotations

import json
import os
import re
import stat
import subprocess
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

from core.l1_metadata_manifest import sdk_schema_check_enabled

L3_FEATURE = "l3_transformed_rows_export"
L3_RAW_FIELD = "sample_value"
L3_DEFAULT_MAX_ROWS = 100
L3_HARD_MAX_ROWS = 10_000
L3_GRANT_SCOPED_PATTERN = "grant_scoped"

_IDENT_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
_GRANT_ID_RE = re.compile(r"^[A-Za-z0-9_.:#-]+$")
_FINDING_ID_RE = re.compile(r"^[A-Za-z0-9_.:#-]+$")
_CLASSIFIER_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_-]*$")


class L3ExportError(Exception):
    """Base L3 failure. ``exit_code`` is mapped by the CLI."""

    exit_code = 1


class L3GrantMissingError(L3ExportError):
    """No usable grant (Ferret-aligned exit 3)."""

    exit_code = 3


class L3ScopeError(L3ExportError):
    """Column/table outside grant or whole-table request (Ferret-aligned exit 4)."""

    exit_code = 4


class L3ContractError(L3ExportError):
    """Pinned schema / producer invariant violated (exit 1, fail-closed)."""

    exit_code = 1


class L3ContainmentError(L3ExportError):
    """Persist path is not proven owner-contained (Ferret-aligned exit 5)."""

    exit_code = 5


CONTAINMENT_OWNER_ONLY = "owner_only"
CONTAINMENT_OWNER_PLUS_PRIVILEGED = "owner_plus_privileged"
CONTAINMENT_NOT_ENFORCED = "not_enforced"

# Honest Windows invariant — match by SID, never by localized display name.
# icacls apply still uses the tool; verification reads Get-Acl SIDs. GitHub
# runners and pt-BR operator boxes emit different names for the same SIDs
# (SYSTEM vs SISTEMA, OWNER RIGHTS vs DIREITOS DO PROPRIETÁRIO). Name
# matching would fail-closed on the wrong thing (exit 5) on a safe DACL.
#
# S-1-5-18 / S-1-5-32-544 typically remain after icacls /inheritance:r;
# stripping them is not practical. They are privileged, not "other users".
# S-1-3-4 (OWNER RIGHTS) and S-1-3-0 (CREATOR OWNER) are *owner-equivalent*,
# not privileged: owner + OWNER RIGHTS only is still CONTAINMENT_OWNER_ONLY.
SID_NT_AUTHORITY_SYSTEM = "S-1-5-18"
SID_BUILTIN_ADMINISTRATORS = "S-1-5-32-544"
SID_OWNER_RIGHTS = "S-1-3-4"
SID_CREATOR_OWNER = "S-1-3-0"
_WINDOWS_PRIVILEGED_SIDS = frozenset(
    {
        SID_NT_AUTHORITY_SYSTEM,
        SID_BUILTIN_ADMINISTRATORS,
    }
)
_WINDOWS_OWNER_EQUIVALENT_SIDS = frozenset(
    {
        SID_OWNER_RIGHTS,
        SID_CREATOR_OWNER,
    }
)


@dataclass(frozen=True)
class L3Grant:
    grant_id: str
    target: str
    table: str
    schema: str
    columns: tuple[str, ...]
    request_columns: tuple[str, ...] | None


def schema_pin_paths() -> tuple[Path, Path]:
    """Return (schema.json, pin.json) from the clone or the packaged wheel copy."""
    repo_root = Path(__file__).resolve().parents[1]
    repo_schema = repo_root / "docs" / "sdk" / "transformed_rows.schema.json"
    repo_pin = repo_root / "docs" / "sdk" / "transformed_rows.pin.json"
    pkg_dir = Path(__file__).resolve().parent / "data"
    pkg_schema = pkg_dir / "transformed_rows.schema.json"
    pkg_pin = pkg_dir / "transformed_rows.pin.json"
    if repo_schema.is_file() and repo_pin.is_file():
        return repo_schema, repo_pin
    if pkg_schema.is_file() and pkg_pin.is_file():
        return pkg_schema, pkg_pin
    raise L3ContractError(
        "L3 transformed_rows schema pin not found "
        "(docs/sdk/ in clone or packaged core/data/)."
    )


@lru_cache(maxsize=1)
def load_pin_metadata() -> dict[str, Any]:
    _schema, pin_path = schema_pin_paths()
    return json.loads(pin_path.read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def load_l3_schema() -> dict[str, Any]:
    schema_path, _pin = schema_pin_paths()
    return json.loads(schema_path.read_text(encoding="utf-8"))


def clamp_max_rows(raw: int) -> int:
    n = int(raw)
    if n < 1:
        raise L3ScopeError("L3: --l3-max-rows must be >= 1")
    return min(n, L3_HARD_MAX_ROWS)


def _require_ident(name: str, *, field: str) -> str:
    text = (name or "").strip()
    if text in {"*", ""}:
        raise L3ScopeError(
            f"L3: {field} must be an explicit identifier (whole-table / * refused)"
        )
    if not _IDENT_RE.fullmatch(text) or len(text) > 64:
        raise L3ScopeError(f"L3: invalid {field} identifier")
    return text


def _require_grant_id(raw: str) -> str:
    text = (raw or "").strip()
    if not text or not _GRANT_ID_RE.fullmatch(text) or len(text) > 128:
        raise L3GrantMissingError("L3: grant_id missing or invalid")
    return text


def parse_grant_document(doc: Any) -> L3Grant:
    if not isinstance(doc, dict):
        raise L3GrantMissingError("L3: grant document must be a JSON object")
    grant_id = _require_grant_id(str(doc.get("grant_id") or ""))
    target = str(doc.get("target") or "").strip()
    if not target or len(target) > 100:
        raise L3GrantMissingError("L3: grant.target is required")
    table = _require_ident(str(doc.get("table") or ""), field="table")
    schema_raw = doc.get("schema")
    schema = ""
    if schema_raw not in (None, ""):
        schema = _require_ident(str(schema_raw), field="schema")
    cols_raw = doc.get("columns")
    if not isinstance(cols_raw, list) or not cols_raw:
        raise L3ScopeError(
            "L3: grant.columns must be a non-empty list (never implicit table)"
        )
    columns: list[str] = []
    seen: set[str] = set()
    for item in cols_raw:
        ident = _require_ident(str(item), field="column")
        key = ident.casefold()
        if key in seen:
            continue
        seen.add(key)
        columns.append(ident)
    req_raw = doc.get("request_columns")
    request_columns: tuple[str, ...] | None = None
    if req_raw is not None:
        if not isinstance(req_raw, list) or not req_raw:
            raise L3ScopeError("L3: grant.request_columns must be a non-empty list")
        request_columns = tuple(
            _require_ident(str(item), field="request_column") for item in req_raw
        )
        _assert_subset(request_columns, columns)
    return L3Grant(
        grant_id=grant_id,
        target=target,
        table=table,
        schema=schema,
        columns=tuple(columns),
        request_columns=request_columns,
    )


def load_grant_file(path: str | Path) -> L3Grant:
    grant_path = Path(path)
    if not grant_path.is_file():
        raise L3GrantMissingError("L3: grant file not found")
    try:
        doc = json.loads(grant_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        raise L3GrantMissingError("L3: grant file is not valid JSON") from None
    return parse_grant_document(doc)


def _assert_subset(
    requested: tuple[str, ...] | list[str], allowed: tuple[str, ...]
) -> None:
    allowed_cf = {c.casefold() for c in allowed}
    for name in requested:
        if name.casefold() not in allowed_cf:
            raise L3ScopeError(
                f"L3: column {name!r} is outside the grant (Ferret-aligned refuse)"
            )


def resolve_projection_columns(
    grant: L3Grant, cli_columns: list[str] | None
) -> tuple[str, ...]:
    if cli_columns:
        names = tuple(_require_ident(c, field="column") for c in cli_columns)
        _assert_subset(names, grant.columns)
        return names
    if grant.request_columns is not None:
        return grant.request_columns
    return grant.columns


def dumps_l3_rows(rows: list[dict[str, Any]]) -> str:
    return json.dumps(rows, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def dumps_l3_audit(audit: dict[str, Any]) -> str:
    """One-line JSON. Callers must never put cell values in *audit*."""
    if "value" in audit:
        raise L3ContractError("L3 audit must not contain a value field")
    return json.dumps(audit, sort_keys=True, ensure_ascii=False) + "\n"


def assert_l3_contract(rows: list[dict[str, Any]]) -> None:
    try:
        from jsonschema import Draft202012Validator
    except ImportError as exc:
        raise L3ContractError(
            "L3 contract: jsonschema is required to fail-closed-validate the pin"
        ) from exc
    if not isinstance(rows, list):
        raise L3ContractError("L3 contract: payload must be a JSON array")
    schema = load_l3_schema()
    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(rows), key=lambda e: list(e.path))
    if errors:
        first = errors[0]
        path = ".".join(str(p) for p in first.path) or "<root>"
        raise L3ContractError(
            f"L3 contract: schema violation at {path}: {first.message}"
        )
    for row in rows:
        if not isinstance(row, dict):
            raise L3ContractError("L3 contract: row must be an object")
        if row.get("raw_field") != L3_RAW_FIELD:
            raise L3ContractError("L3 contract: raw_field must be sample_value")
        value = row.get("value")
        if not isinstance(value, str) or value == "":
            raise L3ContractError("L3 contract: value must be a non-empty string")


def _slug_pattern(raw: str | None) -> str:
    text = (raw or "").strip() or L3_GRANT_SCOPED_PATTERN
    if _CLASSIFIER_RE.fullmatch(text) and len(text) <= 64:
        return text
    cleaned = re.sub(r"[^A-Za-z0-9_-]+", "_", text).strip("_")
    if cleaned and cleaned[0].isdigit():
        cleaned = f"p_{cleaned}"
    if not cleaned or not cleaned[0].isalpha():
        return L3_GRANT_SCOPED_PATTERN
    return cleaned[:64]


def _table_matches(grant: L3Grant, row: dict[str, Any]) -> bool:
    table = str(row.get("table_name") or "")
    if table.casefold() != grant.table.casefold():
        return False
    target = str(row.get("target_name") or "")
    if target != grant.target:
        return False
    if not grant.schema:
        schema = str(row.get("schema_name") or "").casefold()
        return schema in {"", "main"}
    return str(row.get("schema_name") or "").casefold() == grant.schema.casefold()


def _pattern_for_column(
    db_rows: list[dict[str, Any]], grant: L3Grant, column: str
) -> str:
    col_cf = column.casefold()
    for row in db_rows:
        if not _table_matches(grant, row):
            continue
        if str(row.get("column_name") or "").casefold() == col_cf:
            return _slug_pattern(row.get("pattern_detected"))
    return L3_GRANT_SCOPED_PATTERN


def _sql_target(config: dict[str, Any], name: str) -> dict[str, Any]:
    for target in config.get("targets") or []:
        if not isinstance(target, dict):
            continue
        if str(target.get("name") or "") != name:
            continue
        if str(target.get("type") or "").strip().lower() != "database":
            raise L3ContractError("L3: grant target is not a database")
        return target
    raise L3ContractError("L3: grant target is not listed in config")


def build_l3_transformed_rows(
    db_manager: Any,
    *,
    session_id: str,
    grant: L3Grant,
    config: dict[str, Any],
    projection_columns: tuple[str, ...],
    max_rows: int,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Project grant-scoped cells. Does not write files."""
    sid = (session_id or "").strip()
    if not sid:
        raise L3ContractError("L3: session_id is required")
    pin = load_pin_metadata()
    if not pin.get("contract_version"):
        raise L3ContractError("L3 contract: pin missing contract_version")
    use_limit = clamp_max_rows(max_rows)
    _assert_subset(projection_columns, grant.columns)

    db_rows, _fs, _app, _fail = db_manager.get_findings(sid)
    target_cfg = _sql_target(config, grant.target)

    from connectors.sql_connector import SQLConnector

    connector = SQLConnector(target_cfg, scanner=None, db_manager=db_manager)
    rows: list[dict[str, Any]] = []
    try:
        connector.connect()
        for column in projection_columns:
            pattern = _pattern_for_column(db_rows, grant, column)
            cells = connector.fetch_column_values(
                grant.schema,
                grant.table,
                column,
                limit=use_limit,
            )
            for index, cell in enumerate(cells):
                finding_id = f"l3:{grant.grant_id}:{grant.table}:{column}#{index}"
                if not _FINDING_ID_RE.fullmatch(finding_id) or len(finding_id) > 128:
                    raise L3ContractError("L3 contract: cannot project finding_id")
                rows.append(
                    {
                        "finding_id": finding_id,
                        "source_type": "database",
                        "pattern": pattern,
                        "raw_field": L3_RAW_FIELD,
                        "value": cell,
                    }
                )
    finally:
        connector.close()

    assert_l3_contract(rows)
    audit = {
        "event": "l3_export_audit",
        "grant_id": grant.grant_id,
        "target": grant.target,
        "table": grant.table,
        "schema": grant.schema or None,
        "columns": list(projection_columns),
        "row_count": len(rows),
        "max_rows": use_limit,
        "session_id": sid,
        "persisted": False,
    }
    return rows, audit


def _normalize_sid(raw: str) -> str:
    return (raw or "").strip().upper()


def _decode_console(blob: bytes) -> str:
    if not blob:
        return ""
    if blob[:2] in (b"\xff\xfe", b"\xfe\xff") or b"\x00" in blob[:16]:
        try:
            return blob.decode("utf-16")
        except UnicodeDecodeError:
            pass
    for encoding in ("utf-8", "mbcs", "oem"):
        try:
            return blob.decode(encoding)
        except (LookupError, UnicodeDecodeError):
            continue
    return blob.decode("utf-8", errors="replace")


def _run_icacls(args: list[str]) -> subprocess.CompletedProcess[bytes]:
    try:
        return subprocess.run(
            ["icacls", *args],
            capture_output=True,
            check=False,
            timeout=30,
        )
    except FileNotFoundError as exc:
        raise L3ContainmentError(
            "L3 persist: icacls is not available (containment cannot be proven)"
        ) from exc
    except subprocess.TimeoutExpired as exc:
        raise L3ContainmentError("L3 persist: icacls timed out") from exc


_PS_READ_ACL_SIDS = r"""
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8
$path = $env:DATA_BOAR_L3_ACL_PATH
if ([string]::IsNullOrWhiteSpace($path)) { throw 'L3 ACL path missing' }
$acl = Get-Acl -LiteralPath $path
$current = [System.Security.Principal.WindowsIdentity]::GetCurrent().User.Value
if ([string]::IsNullOrWhiteSpace($current)) { throw 'L3 current user SID missing' }
$aces = New-Object System.Collections.Generic.List[object]
foreach ($ace in $acl.Access) {
  $ref = $ace.IdentityReference
  $sid = $null
  try {
    if ($ref -is [System.Security.Principal.SecurityIdentifier]) {
      $sid = $ref.Value
    } else {
      $sid = $ref.Translate([System.Security.Principal.SecurityIdentifier]).Value
    }
  } catch {
    throw "L3 SID translate failed: $($_.Exception.Message)"
  }
  if ([string]::IsNullOrWhiteSpace($sid)) { throw 'L3 SID translate empty' }
  $aces.Add(@{ Sid = $sid; Inherited = [bool]$ace.IsInherited }) | Out-Null
}
@{ CurrentUserSid = $current; Aces = @($aces.ToArray()) } | ConvertTo-Json -Compress -Depth 5
"""

_PS_CURRENT_USER_SID = (
    "[Console]::OutputEncoding = [System.Text.Encoding]::UTF8; "
    "[System.Security.Principal.WindowsIdentity]::GetCurrent().User.Value"
)


def _run_powershell(script: str, *, extra_env: dict[str, str] | None = None) -> str:
    merged = os.environ.copy()
    if extra_env:
        merged.update(extra_env)
    try:
        proc = subprocess.run(
            [
                "powershell.exe",
                "-NoProfile",
                "-NonInteractive",
                "-ExecutionPolicy",
                "Bypass",
                "-Command",
                script,
            ],
            capture_output=True,
            check=False,
            timeout=30,
            env=merged,
        )
    except FileNotFoundError as exc:
        raise L3ContainmentError(
            "L3 persist: powershell.exe is not available (containment cannot be proven)"
        ) from exc
    except subprocess.TimeoutExpired as exc:
        raise L3ContainmentError("L3 persist: powershell timed out") from exc
    if proc.returncode != 0:
        err = (
            _decode_console(proc.stderr).strip() or _decode_console(proc.stdout).strip()
        )
        raise L3ContainmentError(
            f"L3 persist: PowerShell ACL/SID failed (exit {proc.returncode}): {err}"
        )
    text = _decode_console(proc.stdout).strip().lstrip("\ufeff")
    if not text:
        raise L3ContainmentError("L3 persist: PowerShell returned empty SID output")
    return text


def _windows_current_user_sid() -> str:
    sid = _normalize_sid(_run_powershell(_PS_CURRENT_USER_SID))
    if not sid.startswith("S-1-"):
        raise L3ContainmentError("L3 persist: current user SID is not a SID string")
    return sid


def _windows_acl_sid_snapshot(path: Path) -> tuple[str, list[tuple[str, bool]]]:
    raw = _run_powershell(
        _PS_READ_ACL_SIDS,
        extra_env={"DATA_BOAR_L3_ACL_PATH": str(path)},
    )
    try:
        data = json.loads(raw.lstrip("\ufeff"))
    except json.JSONDecodeError as exc:
        raise L3ContainmentError(
            "L3 persist: PowerShell ACL JSON is not parseable (containment not proven)"
        ) from exc
    if not isinstance(data, dict):
        raise L3ContainmentError("L3 persist: PowerShell ACL JSON must be an object")
    current = _normalize_sid(str(data.get("CurrentUserSid") or ""))
    if not current.startswith("S-1-"):
        raise L3ContainmentError(
            "L3 persist: current user SID missing from ACL snapshot"
        )
    aces_raw = data.get("Aces")
    if aces_raw is None:
        raise L3ContainmentError("L3 persist: ACL snapshot has no Aces")
    if isinstance(aces_raw, dict):
        aces_raw = [aces_raw]
    if not isinstance(aces_raw, list):
        raise L3ContainmentError("L3 persist: Aces is not a list")
    aces: list[tuple[str, bool]] = []
    for item in aces_raw:
        if not isinstance(item, dict):
            raise L3ContainmentError("L3 persist: ACE entry is not an object")
        sid = _normalize_sid(str(item.get("Sid") or ""))
        if not sid.startswith("S-1-"):
            raise L3ContainmentError(
                "L3 persist: ACE SID missing or untranslated (containment not proven)"
            )
        inherited = bool(item.get("Inherited"))
        aces.append((sid, inherited))
    return current, aces


def classify_windows_acl_sids(
    aces: list[tuple[str, bool]], current_user_sid: str
) -> str:
    """Prove DACL containment from SIDs only (locale-independent).

    Each ACE is ``(sid, inherited)``. Returns the honest audit label.
    """
    owner = _normalize_sid(current_user_sid)
    if not owner.startswith("S-1-"):
        raise L3ContainmentError("L3 persist: cannot determine Windows owner SID")
    if not aces:
        raise L3ContainmentError(
            "L3 persist: ACL listed no ACEs (cannot prove containment)"
        )
    saw_owner = False
    saw_privileged = False
    for sid_raw, inherited in aces:
        sid = _normalize_sid(sid_raw)
        if inherited:
            raise L3ContainmentError(
                f"L3 persist: inherited ACE remains for SID {sid} (need /inheritance:r)"
            )
        if sid == owner or sid in _WINDOWS_OWNER_EQUIVALENT_SIDS:
            saw_owner = True
            continue
        if sid in _WINDOWS_PRIVILEGED_SIDS:
            saw_privileged = True
            continue
        raise L3ContainmentError(
            f"L3 persist: non-owner unprivileged SID {sid} (containment not proven)"
        )
    if not saw_owner:
        raise L3ContainmentError(
            "L3 persist: owner ACE missing after restriction (containment not proven)"
        )
    if saw_privileged:
        return CONTAINMENT_OWNER_PLUS_PRIVILEGED
    return CONTAINMENT_OWNER_ONLY


def verify_owner_containment(path: Path) -> str:
    """Prove owner containment. Returns the honest audit label."""
    if os.name == "nt":
        current, aces = _windows_acl_sid_snapshot(path)
        return classify_windows_acl_sids(aces, current)
    st = path.stat()
    if st.st_mode & (stat.S_IRWXG | stat.S_IRWXO):
        raise L3ContainmentError(
            f"L3 persist: POSIX mode {stat.filemode(st.st_mode)} is not owner-only"
        )
    if hasattr(os, "getuid") and st.st_uid != os.getuid():
        raise L3ContainmentError("L3 persist: file owner is not the current user")
    return CONTAINMENT_OWNER_ONLY


def _restrict_to_owner(path: Path) -> None:
    """Apply owner-only policy. Does not invent POSIX mode on Windows."""
    if os.name == "nt":
        sid = _windows_current_user_sid()
        grant = f"*{sid}:(F)"
        granted = _run_icacls([str(path), "/grant:r", grant])
        if granted.returncode != 0:
            err = _decode_console(granted.stderr).strip()
            raise L3ContainmentError(
                f"L3 persist: icacls /grant failed (exit {granted.returncode}): {err}"
            )
        stripped = _run_icacls([str(path), "/inheritance:r"])
        if stripped.returncode != 0:
            err = _decode_console(stripped.stderr).strip()
            raise L3ContainmentError(
                f"L3 persist: icacls /inheritance:r failed "
                f"(exit {stripped.returncode}): {err}"
            )
        return
    # POSIX: os.open(..., 0o600) already requested owner rw; verify is the proof.


def persist_l3_body(path: Path, body: str, *, allow_unprotected: bool = False) -> str:
    """Write L3 JSON only when the operator passed an explicit persist path.

    Returns a containment label for the stderr audit record. On failure the
    file is unlinked unless ``allow_unprotected`` is set (declared degradation).
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(
        path,
        os.O_WRONLY | os.O_CREAT | os.O_TRUNC,
        0o600,
    )
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        handle.write(body)
    try:
        _restrict_to_owner(path)
        return verify_owner_containment(path)
    except L3ContainmentError:
        if allow_unprotected:
            return CONTAINMENT_NOT_ENFORCED
        try:
            path.unlink(missing_ok=True)
        except OSError:
            pass
        raise


# Re-export for pin canary tests that share the L1 env gate.
__all__ = [
    "CONTAINMENT_NOT_ENFORCED",
    "CONTAINMENT_OWNER_ONLY",
    "CONTAINMENT_OWNER_PLUS_PRIVILEGED",
    "L3_FEATURE",
    "L3ContainmentError",
    "L3ContractError",
    "L3ExportError",
    "L3Grant",
    "L3GrantMissingError",
    "L3ScopeError",
    "SID_BUILTIN_ADMINISTRATORS",
    "SID_CREATOR_OWNER",
    "SID_NT_AUTHORITY_SYSTEM",
    "SID_OWNER_RIGHTS",
    "assert_l3_contract",
    "build_l3_transformed_rows",
    "clamp_max_rows",
    "classify_windows_acl_sids",
    "dumps_l3_audit",
    "dumps_l3_rows",
    "load_grant_file",
    "load_l3_schema",
    "load_pin_metadata",
    "parse_grant_document",
    "persist_l3_body",
    "resolve_projection_columns",
    "schema_pin_paths",
    "sdk_schema_check_enabled",
    "verify_owner_containment",
]
