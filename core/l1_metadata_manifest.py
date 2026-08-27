"""L1 metadata_manifest export from SQLite (SDK contract pin, fail-closed).

Canonical schema: DataBoar/data-boar-sdk ``schema/metadata_manifest.schema.json``.
This producer validates against the local pin (``docs/sdk/`` in a clone, packaged
copy in the wheel). Drift vs SDK ``main`` is a canary (``DATA_BOAR_SDK_SCHEMA_CHECK``),
never a degraded emit.
"""

from __future__ import annotations

import json
import os
import re
from functools import lru_cache
from pathlib import Path
from typing import Any

from core.about import get_about_info

RAW_VALUE_FIELDS = frozenset({"sample_value", "sample_content", "raw_sample", "value"})

_SOURCE_TYPE_MAP = {
    "database": "database",
    "filesystem": "filesystem",
    "application": "application",
    "api": "application",
    "crm": "application",
    "saas": "application",
}

_SENSITIVITY_MAP = {
    "high": "high",
    "medium": "medium",
    "low": "low",
}

_EMAIL_RE = re.compile(r"[^\s@]+@[^\s@]+\.[^\s@]+")
_SSN_RE = re.compile(r"\d{3}-\d{2}-\d{4}")
_CPF_RE = re.compile(r"\d{3}\.?\d{3}\.?\d{3}-\d{2}")
# Same digit-run shape as SDK piiShapedString pan arm: 13–19 digits, optional space/hyphen.
_PAN_RUN_RE = re.compile(r"\d(?:[ -]?\d){12,18}")
_CLASSIFIER_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_-]*$")
_COLUMN_ID_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_.]*$")
_FINDING_ID_RE = re.compile(r"^[A-Za-z0-9_.:#-]+$")
_NORM_TAG_RE = re.compile(r"^[a-z][a-z0-9_]*$")

SELECTION_RULE = (
    "all sqlite finding rows for the session "
    "(database filesystem application); no silent truncation; "
    "co_occurrence omitted pending sdk41"
)

_SCHEMA_CHECK_TRUTH = frozenset({"1", "true", "yes", "on"})


class L1ContractError(Exception):
    """Projection would violate the pinned L1 metadata_manifest contract."""


def schema_pin_paths() -> tuple[Path, Path]:
    """Return (schema.json, pin.json) from the clone or the packaged wheel copy."""
    repo_root = Path(__file__).resolve().parents[1]
    repo_schema = repo_root / "docs" / "sdk" / "metadata_manifest.schema.json"
    repo_pin = repo_root / "docs" / "sdk" / "metadata_manifest.pin.json"
    pkg_dir = Path(__file__).resolve().parent / "data"
    pkg_schema = pkg_dir / "metadata_manifest.schema.json"
    pkg_pin = pkg_dir / "metadata_manifest.pin.json"
    if repo_schema.is_file() and repo_pin.is_file():
        return repo_schema, repo_pin
    if pkg_schema.is_file() and pkg_pin.is_file():
        return pkg_schema, pkg_pin
    raise L1ContractError(
        "L1 metadata_manifest schema pin not found "
        "(docs/sdk/ in clone or packaged core/data/)."
    )


@lru_cache(maxsize=1)
def load_pin_metadata() -> dict[str, Any]:
    _schema, pin_path = schema_pin_paths()
    return json.loads(pin_path.read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def load_l1_schema() -> dict[str, Any]:
    schema_path, _pin = schema_pin_paths()
    return json.loads(schema_path.read_text(encoding="utf-8"))


def sanitize_locator(text: str | None) -> str | None:
    """Strip PII-shaped *content* from a locator while keeping its role as a name."""
    if text is None:
        return None
    s = str(text)
    s = _EMAIL_RE.sub("redacted_email", s)
    s = _SSN_RE.sub("redacted_ssn", s)
    s = _CPF_RE.sub("redacted_cpf", s)

    def _pan_repl(match: re.Match[str]) -> str:
        digits = re.sub(r"\D", "", match.group(0))
        n = len(digits)
        if 13 <= n <= 19:
            return f"d{n}"
        return match.group(0)

    return _PAN_RUN_RE.sub(_pan_repl, s)


def _slug_classifier(raw: str | None, *, field: str) -> str:
    text = (raw or "").strip()
    if not text:
        raise L1ContractError(f"L1 contract: empty {field}")
    if _CLASSIFIER_RE.fullmatch(text) and len(text) <= 64:
        return text
    cleaned = re.sub(r"[^A-Za-z0-9_-]+", "_", text).strip("_")
    if cleaned and cleaned[0].isdigit():
        cleaned = f"p_{cleaned}"
    if not cleaned or not cleaned[0].isalpha():
        raise L1ContractError(f"L1 contract: cannot project {field} {raw!r}")
    cleaned = cleaned[:64]
    if not _CLASSIFIER_RE.fullmatch(cleaned):
        raise L1ContractError(f"L1 contract: cannot project {field} {raw!r}")
    return cleaned


def _slug_norm_tag(raw: str | None) -> str | None:
    text = (raw or "").strip()
    if not text:
        return None
    lowered = text.lower()
    cleaned = re.sub(r"[^a-z0-9_]+", "_", lowered).strip("_")
    if not cleaned:
        return None
    if cleaned[0].isdigit():
        cleaned = f"n_{cleaned}"
    cleaned = cleaned[:32]
    if not _NORM_TAG_RE.fullmatch(cleaned):
        return None
    return cleaned


def _slug_column_id(raw: str | None) -> str | None:
    text = (raw or "").strip()
    if not text:
        return None
    if _COLUMN_ID_RE.fullmatch(text) and len(text) <= 128:
        return text
    cleaned = re.sub(r"[^A-Za-z0-9_.]+", "_", text).strip("._")
    if not cleaned:
        return None
    if cleaned[0].isdigit() or not (cleaned[0].isalpha() or cleaned[0] == "_"):
        cleaned = f"c_{cleaned}"
    cleaned = cleaned[:128]
    if not _COLUMN_ID_RE.fullmatch(cleaned):
        raise L1ContractError(f"L1 contract: cannot project raw_field {raw!r}")
    return cleaned


def _map_sensitivity(raw: Any) -> str | None:
    if raw is None:
        return None
    key = str(raw).strip().lower()
    return _SENSITIVITY_MAP.get(key)


def _location_for_row(source_kind: str, row: dict[str, Any]) -> str | None:
    if source_kind == "database":
        parts = [row.get("schema_name"), row.get("table_name"), row.get("column_name")]
        loc = ".".join(str(p) for p in parts if p)
        return loc or None
    path = row.get("path")
    file_name = row.get("file_name")
    if path and file_name:
        joined = f"{path.rstrip('/')}/{file_name}"
        return joined
    return path or file_name


def _raw_field_for_row(source_kind: str, row: dict[str, Any]) -> str | None:
    if source_kind == "database":
        return row.get("column_name")
    return row.get("file_name")


def _sort_key(source_kind: str, row: dict[str, Any]) -> tuple[str, ...]:
    loc = _location_for_row(source_kind, row) or ""
    pattern = str(row.get("pattern_detected") or "")
    target = str(row.get("target_name") or "")
    return (source_kind, target, loc, pattern, str(row.get("id") or ""))


def _contains_raw_value_fields(obj: Any) -> bool:
    if isinstance(obj, dict):
        if RAW_VALUE_FIELDS.intersection(obj.keys()):
            return True
        return any(_contains_raw_value_fields(v) for v in obj.values())
    if isinstance(obj, list):
        return any(_contains_raw_value_fields(v) for v in obj)
    return False


def assert_l1_contract(payload: dict[str, Any]) -> None:
    """Fail-closed: abort if the document would violate the pinned schema."""
    if _contains_raw_value_fields(payload):
        raise L1ContractError(
            "L1 contract: payload contains a forbidden raw-value field "
            f"({', '.join(sorted(RAW_VALUE_FIELDS))})"
        )
    try:
        from jsonschema import Draft202012Validator
    except ImportError as exc:
        raise L1ContractError(
            "L1 contract: jsonschema is required to fail-closed-validate the pin"
        ) from exc
    schema = load_l1_schema()
    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(payload), key=lambda e: list(e.path))
    if errors:
        first = errors[0]
        path = ".".join(str(p) for p in first.path) or "<root>"
        raise L1ContractError(
            f"L1 contract: schema violation at {path}: {first.message}"
        )
    if payload.get("kind") != "metadata_manifest" or payload.get("plane") != "L1":
        raise L1ContractError("L1 contract: kind/plane mismatch")


def dumps_l1_manifest(payload: dict[str, Any]) -> str:
    """Deterministic JSON (sorted keys, 2-space indent). Same session → same bytes."""
    return json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def build_l1_metadata_manifest(db_manager: Any, *, session_id: str) -> dict[str, Any]:
    """Project SQLite findings for one session into a metadata-only L1 document."""
    sid = (session_id or "").strip()
    pin = load_pin_metadata()
    contract_version = str(pin.get("contract_version") or "")
    if not contract_version:
        raise L1ContractError("L1 contract: pin missing contract_version")

    db_rows, fs_rows, app_rows, _failures = db_manager.get_findings(sid)
    work: list[tuple[str, dict[str, Any]]] = []
    work.extend(("database", r) for r in db_rows)
    work.extend(("filesystem", r) for r in fs_rows)
    work.extend(("application", r) for r in app_rows)
    work.sort(key=lambda item: _sort_key(item[0], item[1]))

    findings: list[dict[str, Any]] = []
    for index, (source_kind, row) in enumerate(work):
        mapped_source = _SOURCE_TYPE_MAP.get(source_kind)
        if mapped_source is None:
            raise L1ContractError(f"L1 contract: unknown source_type {source_kind!r}")
        pattern = _slug_classifier(row.get("pattern_detected"), field="pattern")
        loc = sanitize_locator(_location_for_row(source_kind, row))
        if loc is not None and len(loc) > 512:
            raise L1ContractError("L1 contract: location exceeds 512 characters")
        raw_field = _slug_column_id(
            sanitize_locator(_raw_field_for_row(source_kind, row))
        )
        finding_id = f"{mapped_source}#{index}"
        if not _FINDING_ID_RE.fullmatch(finding_id) or len(finding_id) > 128:
            raise L1ContractError(
                f"L1 contract: cannot project finding_id {finding_id!r}"
            )
        findings.append(
            {
                "finding_id": finding_id,
                "source_type": mapped_source,
                "sensitivity": _map_sensitivity(row.get("sensitivity_level")),
                "pattern": pattern,
                "norm_tag": _slug_norm_tag(row.get("norm_tag")),
                "location": loc,
                "raw_field": raw_field,
                "value_length": None,
            }
        )

    about = get_about_info()
    payload: dict[str, Any] = {
        "contract_version": contract_version,
        "kind": "metadata_manifest",
        "plane": "L1",
        "application": {
            "name": about["name"],
            "version": about["version"],
        },
        "summary": {
            "selection_rule": SELECTION_RULE,
            "excluded_count": 0,
            "total_findings": len(findings),
        },
        "findings": findings,
    }
    assert_l1_contract(payload)
    return payload


def sdk_schema_check_enabled(env: dict[str, str] | None = None) -> bool:
    """True when the optional network canary should run."""
    source = env if env is not None else os.environ
    raw = str(source.get("DATA_BOAR_SDK_SCHEMA_CHECK") or "").strip().lower()
    return raw in _SCHEMA_CHECK_TRUTH
