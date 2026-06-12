"""
Anti-regression tests for the ReDoS guard on third-party regex overrides (#829).

Threat model (operator decision on #829): ReDoS is an EXTERNAL-input vector.
Enforcement happens at the trust boundary — `_load_regex_overrides` (plugin /
override path) — while curated built-in DEFAULT_PATTERNS are exempt. The
calibration tests below keep the heuristic honest: every built-in must pass
the guard, so the heuristic never drifts into rejecting curated patterns
(the PHONE_BR false-positive regression).

Validates that:
- _has_nested_quantifier (star height > 1 scanner, escape/class-aware)
  identifies dangerous shapes and allows curated ones.
- _validate_item emits an issue for patterns with nested quantifiers.
- SensitivityDetector skips override patterns with nested quantifiers or
  invalid regex, with a warning — never crashing the scan.
- All built-in DEFAULT_PATTERNS pass the guard and compile (calibration).
"""

import re
import warnings
from pathlib import Path


def test_has_nested_quantifier_detects_dangerous_patterns() -> None:
    """ReDoS guard: nested quantifier detector catches known-dangerous patterns."""
    from config.plugin_validator import _has_nested_quantifier

    dangerous = [
        r"(a+)+",
        r"(\w*)*",
        r"([a-z]+)*",
        r"(x{2,})+",
        r"((a+)b)+",  # unbounded content propagates to enclosing group
    ]
    for pat in dangerous:
        assert _has_nested_quantifier(pat), (
            f"Expected _has_nested_quantifier to flag {pat!r} as dangerous (#829)"
        )


def test_has_nested_quantifier_allows_safe_patterns() -> None:
    """ReDoS guard: safe patterns are not rejected."""
    from config.plugin_validator import _has_nested_quantifier

    safe = [
        r"\d{3}\.?\d{3}\.?\d{3}-?\d{2}",  # CPF
        r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",  # e-mail
        r"(a+)b*",  # quantifier after group, not nested
        r"(\d+)\s+\w+",
        r"(\+55\s?)?(\(?\d{2}\)?\s?)?\d{4,5}-?\d{4}",  # PHONE_BR: escaped \+ \( \) are literals
        r"(a?)+",  # bounded ? inside — CPython empty-match protection, no blowup
        r"([+*]\d)+",  # quantifier chars inside a character class are literals
        r"(a{2,5})+",  # bounded brace repetition inside
    ]
    for pat in safe:
        assert not _has_nested_quantifier(pat), (
            f"Expected _has_nested_quantifier to allow safe pattern {pat!r} (#829)"
        )


def test_validate_item_rejects_nested_quantifier_pattern() -> None:
    """plugin_validator._validate_item must issue an error for nested-quantifier patterns."""
    from config.plugin_validator import _validate_item

    item = {"name": "BAD_REDOS", "pattern": r"(a+)+", "norm_tag": "Custom"}
    # Minimal field definitions matching the regex_patterns schema.
    item_fields = {
        "name": {"required": True, "type": "string"},
        "pattern": {"required": True, "type": "string"},
        "norm_tag": {"required": False, "type": "string"},
    }
    issues = _validate_item(item, 0, item_fields)
    redos_issues = [i for i in issues if "ReDoS" in i or "nested quantif" in i]
    assert redos_issues, (
        "Expected _validate_item to produce a ReDoS issue for (a+)+ pattern (#829)"
    )


def test_validate_item_accepts_safe_pattern() -> None:
    """plugin_validator._validate_item must not flag safe patterns as ReDoS risks."""
    from config.plugin_validator import _validate_item

    item = {"name": "SAFE", "pattern": r"\d{11}", "norm_tag": "CPF"}
    item_fields = {
        "name": {"required": True, "type": "string"},
        "pattern": {"required": True, "type": "string"},
        "norm_tag": {"required": False, "type": "string"},
    }
    issues = _validate_item(item, 0, item_fields)
    redos_issues = [i for i in issues if "ReDoS" in i or "nested quantif" in i]
    assert not redos_issues, (
        "Expected no ReDoS issue for a safe pattern, got: %r" % redos_issues
    )


def test_detector_warns_and_skips_nested_quantifier_override(tmp_path: Path) -> None:
    """SensitivityDetector must warn and skip OVERRIDE patterns with nested quantifiers.

    Enforcement at the trust boundary (#829): the dangerous pattern never reaches
    `_compiled`, the scan continues, and the good pattern in the same file loads.
    """
    import yaml

    from core.detector import SensitivityDetector

    bad_plugin = tmp_path / "bad_patterns.yaml"
    bad_plugin.write_text(
        yaml.dump(
            [
                {"name": "BAD_REDOS", "pattern": r"(a+)+", "norm_tag": "Custom"},
                {"name": "GOOD_CUSTOM", "pattern": r"\d{5}", "norm_tag": "Custom"},
            ]
        ),
        encoding="utf-8",
    )
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        det = SensitivityDetector(regex_overrides_path=str(bad_plugin))
    warning_messages = [str(w.message) for w in caught]
    redos_warnings = [
        m for m in warning_messages if "ReDoS" in m or "nested quantif" in m
    ]
    assert redos_warnings, (
        "Expected SensitivityDetector to warn about nested quantifier in plugin (#829). "
        f"Got warnings: {warning_messages}"
    )
    assert "BAD_REDOS" not in det._compiled, (
        "SensitivityDetector must not include the dangerous pattern in _compiled (#829)"
    )
    assert "GOOD_CUSTOM" in det._compiled, (
        "A safe pattern in the same plugin file must still load — skip is per-item, "
        "not per-file (#829)"
    )


def test_detector_warns_and_skips_invalid_regex_override(tmp_path: Path) -> None:
    """SensitivityDetector must warn and skip override patterns that fail re.compile."""
    import yaml

    from core.detector import SensitivityDetector

    bad_plugin = tmp_path / "invalid_patterns.yaml"
    bad_plugin.write_text(
        yaml.dump(
            [{"name": "BAD_SYNTAX", "pattern": r"(unclosed", "norm_tag": "Custom"}]
        ),
        encoding="utf-8",
    )
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        det = SensitivityDetector(regex_overrides_path=str(bad_plugin))
    warning_messages = [str(w.message) for w in caught]
    invalid_warnings = [m for m in warning_messages if "invalid regex" in m]
    assert invalid_warnings, (
        "Expected SensitivityDetector to warn about invalid regex in plugin (#829). "
        f"Got warnings: {warning_messages}"
    )
    assert "BAD_SYNTAX" not in det._compiled, (
        "SensitivityDetector must not include the invalid pattern in _compiled (#829)"
    )


def test_default_patterns_pass_redos_guard() -> None:
    """Calibration (#829): built-ins are EXEMPT from runtime enforcement, but every
    DEFAULT_PATTERN must still pass the heuristic — if a curated pattern fails it,
    the heuristic regressed (the PHONE_BR false-positive class), not the pattern.
    """
    from config.plugin_validator import _has_nested_quantifier
    from core.detector import DEFAULT_PATTERNS

    dangerous = [
        name
        for name, (pat, _) in DEFAULT_PATTERNS.items()
        if _has_nested_quantifier(pat)
    ]
    assert not dangerous, (
        f"ReDoS heuristic flagged curated built-in patterns — recalibrate the "
        f"heuristic, do not weaken the patterns (#829): {dangerous}"
    )


def test_default_patterns_all_compile() -> None:
    """All built-in DEFAULT_PATTERNS must compile without re.error."""
    from core.detector import DEFAULT_PATTERNS

    bad = []
    for name, (pat, _) in DEFAULT_PATTERNS.items():
        try:
            re.compile(pat)
        except re.error as exc:
            bad.append((name, str(exc)))
    assert not bad, f"DEFAULT_PATTERNS with re.error: {bad}"
