"""Tests for the YAML-based plugin system (ADR-0052).

Covers:
- validate_plugin_file() with all three plugin types.
- Valid files pass without issues.
- Missing required fields are reported.
- Wrong types are reported.
- Unknown/extra fields are tolerated (additive schema: no strict rejection of unknown keys).
- Unified plugin file validation.
- patterns_plugin_file config key correctly overrides legacy keys in normalize_config.
- Existing example files (config/regex_overrides.example.yaml) pass validation.
"""

from __future__ import annotations

import textwrap
from pathlib import Path

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _write_yaml(tmp_path: Path, name: str, content: str) -> str:
    p = tmp_path / name
    p.write_text(textwrap.dedent(content), encoding="utf-8")
    return str(p)


# ---------------------------------------------------------------------------
# validate_plugin_file — regex_patterns
# ---------------------------------------------------------------------------


def test_valid_regex_plugin_passes(tmp_path):
    """A well-formed regex plugin file produces no validation issues."""
    from config.plugin_validator import validate_plugin_file

    path = _write_yaml(
        tmp_path,
        "good_regex.yaml",
        """
        - name: "RG_BR"
          pattern: "\\\\b\\\\d{1,2}\\\\.?\\\\d{3}-?[0-9Xx]\\\\b"
          norm_tag: "LGPD Art. 5"
        - name: "PLATE_BR"
          pattern: "\\\\b[A-Z]{3}-?\\\\d{4}\\\\b"
        """,
    )
    result = validate_plugin_file(path, plugin_type="regex_patterns")
    assert result.valid is True
    assert result.issues == []


def test_regex_plugin_missing_required_name(tmp_path):
    """Missing 'name' field is reported as an issue."""
    from config.plugin_validator import validate_plugin_file

    path = _write_yaml(
        tmp_path,
        "bad_regex.yaml",
        """
        - pattern: "\\\\b\\\\d+\\\\b"
          norm_tag: "Custom"
        """,
    )
    result = validate_plugin_file(path, plugin_type="regex_patterns")
    assert result.valid is False
    assert any("name" in issue for issue in result.issues)


def test_regex_plugin_missing_required_pattern(tmp_path):
    """Missing 'pattern' field is reported as an issue."""
    from config.plugin_validator import validate_plugin_file

    path = _write_yaml(
        tmp_path,
        "bad_pattern.yaml",
        """
        - name: "MISSING_PATTERN"
        """,
    )
    result = validate_plugin_file(path, plugin_type="regex_patterns")
    assert result.valid is False
    assert any("pattern" in issue for issue in result.issues)


def test_regex_plugin_wrong_type_for_name(tmp_path):
    """'name' with non-string value is reported."""
    from config.plugin_validator import validate_plugin_file

    path = _write_yaml(
        tmp_path,
        "bad_name_type.yaml",
        """
        - name: 42
          pattern: "\\\\b\\\\d+\\\\b"
        """,
    )
    result = validate_plugin_file(path, plugin_type="regex_patterns")
    assert result.valid is False
    assert any("name" in issue for issue in result.issues)


# ---------------------------------------------------------------------------
# validate_plugin_file — ml_patterns
# ---------------------------------------------------------------------------


def test_valid_ml_plugin_passes(tmp_path):
    """A well-formed ml_patterns file produces no issues."""
    from config.plugin_validator import validate_plugin_file

    path = _write_yaml(
        tmp_path,
        "good_ml.yaml",
        """
        - text: "cpf"
          label: "sensitive"
        - text: "cartão de crédito"
          label: 1
        - text: "código de produto"
          label: "non_sensitive"
        """,
    )
    result = validate_plugin_file(path, plugin_type="ml_patterns")
    assert result.valid is True


def test_ml_plugin_missing_required_text(tmp_path):
    """Missing 'text' field is reported."""
    from config.plugin_validator import validate_plugin_file

    path = _write_yaml(
        tmp_path,
        "bad_ml.yaml",
        """
        - label: "sensitive"
        """,
    )
    result = validate_plugin_file(path, plugin_type="ml_patterns")
    assert result.valid is False
    assert any("text" in issue for issue in result.issues)


def test_ml_plugin_invalid_label_value(tmp_path):
    """An unexpected label value is reported."""
    from config.plugin_validator import validate_plugin_file

    path = _write_yaml(
        tmp_path,
        "bad_label.yaml",
        """
        - text: "salary"
          label: "maybe"
        """,
    )
    result = validate_plugin_file(path, plugin_type="ml_patterns")
    assert result.valid is False
    assert any("label" in issue for issue in result.issues)


# ---------------------------------------------------------------------------
# validate_plugin_file — unified_plugin_file
# ---------------------------------------------------------------------------


def test_valid_unified_plugin_passes(tmp_path):
    """A unified plugin file with all three sections validates cleanly."""
    from config.plugin_validator import validate_plugin_file

    path = _write_yaml(
        tmp_path,
        "unified.yaml",
        """
        regex_patterns:
          - name: "RG_BR"
            pattern: "\\\\b\\\\d{1,2}\\\\.?\\\\d{3}-?[0-9Xx]\\\\b"
            norm_tag: "LGPD Art. 5"
        ml_patterns:
          - text: "cpf"
            label: "sensitive"
        dl_patterns:
          - text: "dado pessoal"
            label: 1
        """,
    )
    result = validate_plugin_file(path, plugin_type="unified_plugin_file")
    assert result.valid is True


def test_unified_plugin_unknown_top_level_key(tmp_path):
    """An unknown top-level key in a unified file is reported."""
    from config.plugin_validator import validate_plugin_file

    path = _write_yaml(
        tmp_path,
        "unified_bad.yaml",
        """
        regex_patterns:
          - name: "PLATE"
            pattern: "\\\\b[A-Z]+\\\\b"
        unknown_section:
          - text: "foo"
        """,
    )
    result = validate_plugin_file(path, plugin_type="unified_plugin_file")
    assert result.valid is False
    assert any("unknown_section" in issue for issue in result.issues)


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------


def test_none_path_returns_valid():
    """None path returns valid=True (no-op)."""
    from config.plugin_validator import validate_plugin_file

    result = validate_plugin_file(None, plugin_type="regex_patterns")
    assert result.valid is True


def test_nonexistent_path_returns_valid(tmp_path):
    """Non-existent path returns valid=True (the loader handles missing files)."""
    from config.plugin_validator import validate_plugin_file

    result = validate_plugin_file(
        str(tmp_path / "not_here.yaml"), plugin_type="regex_patterns"
    )
    assert result.valid is True


def test_unknown_plugin_type_returns_invalid(tmp_path):
    """Unknown plugin_type returns valid=False with a clear message."""
    from config.plugin_validator import validate_plugin_file

    path = _write_yaml(tmp_path, "dummy.yaml", "- name: foo\n  pattern: bar\n")
    result = validate_plugin_file(path, plugin_type="nonexistent_type")
    assert result.valid is False
    assert any("Unknown plugin_type" in issue for issue in result.issues)


# ---------------------------------------------------------------------------
# Existing example files must pass validation
# ---------------------------------------------------------------------------


def test_example_regex_overrides_passes_validation():
    """config/regex_overrides.example.yaml must pass regex_patterns validation."""
    from config.plugin_validator import validate_plugin_file

    example_path = (
        Path(__file__).parent.parent / "config" / "regex_overrides.example.yaml"
    )
    if not example_path.exists():
        pytest.skip("Example file not found")
    result = validate_plugin_file(str(example_path), plugin_type="regex_patterns")
    assert result.valid is True, f"Validation issues: {result.issues}"


# ---------------------------------------------------------------------------
# patterns_plugin_file config key integration
# ---------------------------------------------------------------------------


def test_patterns_plugin_file_overrides_regex_legacy_key(tmp_path):
    """When patterns_plugin_file has regex_patterns and regex_overrides_file is empty,
    normalize_config sets regex_overrides_file to the unified path."""
    import yaml

    from config.loader import normalize_config

    unified_path = _write_yaml(
        tmp_path,
        "my_plugin.yaml",
        """
        regex_patterns:
          - name: "CUSTOM"
            pattern: "\\\\bcustom\\\\b"
            norm_tag: "Custom"
        """,
    )
    raw_config = yaml.safe_load(
        f"""
        targets:
          - name: test
            type: filesystem
            path: /tmp
        patterns_plugin_file: "{unified_path.replace(chr(92), "/")}"
        """
    )
    config = normalize_config(raw_config)
    assert config["patterns_plugin_file"] == unified_path.replace("\\", "/")
    # regex_overrides_file should point to the unified file
    assert config["regex_overrides_file"] == unified_path.replace("\\", "/")
