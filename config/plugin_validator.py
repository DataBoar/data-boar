"""Plugin file validator — reads config/plugin_schema.yaml and checks operator-provided
pattern files before the scan engine loads them.

Usage (library)
---------------
    from config.plugin_validator import validate_plugin_file, PluginValidationResult

    result = validate_plugin_file("/path/to/my_patterns.yaml", plugin_type="regex_patterns")
    if not result.valid:
        for issue in result.issues:
            warnings.warn(issue, PluginValidationWarning)

Design constraints (ADR-0052)
------------------------------
- Zero third-party runtime dependencies (no jsonschema, no pydantic).
- ``config/plugin_schema.yaml`` is the single source of truth; this module reads it.
- Returns structured results so callers decide whether to warn or raise.
- All existing example files in the repo must pass validation.
"""

from __future__ import annotations

import warnings
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

_SCHEMA_PATH = Path(__file__).parent / "plugin_schema.yaml"

_VALID_PLUGIN_TYPES = frozenset(
    ("regex_patterns", "ml_patterns", "dl_patterns", "unified_plugin_file")
)

# Field types understood by the lightweight validator.
_TYPE_CHECK: dict[str, type | tuple[type, ...]] = {
    "string": str,
    "string_or_int": (str, int),
}

# Top-level keys that a unified plugin file may have.
_UNIFIED_SECTION_KEYS = frozenset(("regex_patterns", "ml_patterns", "dl_patterns"))


class PluginValidationWarning(UserWarning):
    """Raised (via warnings.warn) when a plugin file contains items that do not
    conform to the canonical schema in config/plugin_schema.yaml.
    """


@dataclass(frozen=True)
class PluginValidationResult:
    """Result of a plugin file validation pass.

    ``valid`` is True only when no issues were found (not even warnings).
    ``issues`` is a list of human-readable strings describing each problem found.
    Items that fail validation are *skipped* by the loader; the scan continues.
    """

    valid: bool
    issues: list[str] = field(default_factory=list)


def _load_schema() -> dict[str, Any]:
    """Load the canonical plugin schema from config/plugin_schema.yaml.

    Returns an empty dict and emits a warning when the file is missing so
    downstream callers degrade gracefully.
    """
    if not _SCHEMA_PATH.exists():
        warnings.warn(
            f"Plugin schema file not found: {_SCHEMA_PATH}. Validation skipped.",
            PluginValidationWarning,
            stacklevel=3,
        )
        return {}
    with _SCHEMA_PATH.open(encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


def validate_plugin_file(
    path: str | None,
    plugin_type: str,
) -> PluginValidationResult:
    """Validate *path* against the canonical schema for *plugin_type*.

    Parameters
    ----------
    path:
        Filesystem path to the operator-provided YAML (or JSON) plugin file.
        Returns a passing result immediately when ``None`` or when the file
        does not exist (the loaders handle missing-file logic separately).
    plugin_type:
        One of ``regex_patterns``, ``ml_patterns``, ``dl_patterns``, or
        ``unified_plugin_file``.  Determines which section of the schema is used.

    Returns
    -------
    PluginValidationResult
        ``valid=True`` when every item in the file conforms to the schema.
    """
    if not path:
        return PluginValidationResult(valid=True)

    plugin_path = Path(path)
    if not plugin_path.exists():
        return PluginValidationResult(valid=True)

    if plugin_type not in _VALID_PLUGIN_TYPES:
        return PluginValidationResult(
            valid=False,
            issues=[
                f"Unknown plugin_type '{plugin_type}'. "
                f"Must be one of: {sorted(_VALID_PLUGIN_TYPES)}."
            ],
        )

    schema = _load_schema()
    if not schema:
        return PluginValidationResult(valid=True)

    try:
        raw_text = plugin_path.read_text(encoding="utf-8")
        if plugin_path.suffix.lower() in (".yaml", ".yml"):
            data = yaml.safe_load(raw_text)
        else:
            import json

            data = json.loads(raw_text)
    except Exception as exc:  # noqa: BLE001
        return PluginValidationResult(
            valid=False, issues=[f"Failed to parse plugin file: {exc}"]
        )

    if plugin_type == "unified_plugin_file":
        return _validate_unified(data, schema)

    return _validate_typed_list(data, plugin_type, schema)


def _validate_typed_list(
    data: Any,
    plugin_type: str,
    schema: dict[str, Any],
) -> PluginValidationResult:
    """Validate a flat list plugin file (regex_patterns, ml_patterns, or dl_patterns)."""
    type_schema = schema.get(plugin_type, {})
    item_fields: dict[str, Any] = type_schema.get("item_fields", {})

    # Accept top-level list or dict. Legacy compliance files use ``regex`` for regex
    # overrides and ``terms`` for ML terms in the *same* file; pick the list that matches
    # ``plugin_type`` (do not read ``terms`` when validating ``regex_patterns``).
    if isinstance(data, dict):
        if plugin_type == "regex_patterns":
            items = data.get(
                "patterns", data.get("regex", data.get("regex_patterns", []))
            )
        elif plugin_type in ("ml_patterns", "dl_patterns"):
            items = data.get("patterns", data.get("terms", data.get(plugin_type, [])))
        else:
            items = []
    elif isinstance(data, list):
        items = data
    else:
        return PluginValidationResult(
            valid=False,
            issues=[
                f"Plugin file root must be a list or mapping; got {type(data).__name__}."
            ],
        )

    issues: list[str] = []
    for idx, item in enumerate(items):
        if not isinstance(item, dict):
            issues.append(
                f"Item #{idx}: expected a mapping (dict), got {type(item).__name__}."
            )
            continue
        item_issues = _validate_item(item, idx, item_fields)
        issues.extend(item_issues)

    return PluginValidationResult(valid=len(issues) == 0, issues=issues)


def _validate_unified(
    data: Any,
    schema: dict[str, Any],
) -> PluginValidationResult:
    """Validate a unified plugin file that may have multiple sections."""
    if not isinstance(data, dict):
        return PluginValidationResult(
            valid=False,
            issues=[
                f"Unified plugin file root must be a mapping; got {type(data).__name__}."
            ],
        )

    unknown_keys = set(data.keys()) - _UNIFIED_SECTION_KEYS
    issues: list[str] = []
    for k in sorted(unknown_keys):
        issues.append(
            f"Unknown top-level key '{k}' in unified plugin file. "
            f"Allowed keys: {sorted(_UNIFIED_SECTION_KEYS)}."
        )

    for section_key in _UNIFIED_SECTION_KEYS:
        if section_key not in data:
            continue
        section_data = data[section_key]
        if not isinstance(section_data, list):
            issues.append(
                f"Section '{section_key}' must be a list; got {type(section_data).__name__}."
            )
            continue
        type_schema = schema.get(section_key, {})
        item_fields: dict[str, Any] = type_schema.get("item_fields", {})
        for idx, item in enumerate(section_data):
            if not isinstance(item, dict):
                issues.append(
                    f"Section '{section_key}', item #{idx}: "
                    f"expected mapping, got {type(item).__name__}."
                )
                continue
            section_issues = _validate_item(item, idx, item_fields, prefix=section_key)
            issues.extend(section_issues)

    return PluginValidationResult(valid=len(issues) == 0, issues=issues)


def _validate_item(
    item: dict[str, Any],
    idx: int,
    item_fields: dict[str, Any],
    prefix: str = "",
) -> list[str]:
    """Validate a single item dict against field definitions from the schema."""
    issues: list[str] = []
    location = f"{'Section ' + prefix + ', i' if prefix else 'I'}tem #{idx}"

    for field_name, field_def in item_fields.items():
        required: bool = field_def.get("required", False)
        value = item.get(field_name)

        if value is None:
            if required:
                issues.append(f"{location}: missing required field '{field_name}'.")
            continue

        field_type = field_def.get("type", "string")
        expected_type = _TYPE_CHECK.get(field_type, str)
        if not isinstance(value, expected_type):
            issues.append(
                f"{location}, field '{field_name}': expected {field_type}, "
                f"got {type(value).__name__} (value={value!r})."
            )
            continue

        allowed: list[Any] | None = field_def.get("allowed_values")
        if allowed is not None and value not in allowed:
            issues.append(
                f"{location}, field '{field_name}': value {value!r} not in "
                f"allowed values {allowed}."
            )

    return issues
