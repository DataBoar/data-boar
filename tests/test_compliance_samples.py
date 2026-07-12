"""
Tests for docs/compliance-samples/compliance-sample-*.yaml files.

Validates that each compliance sample YAML has the structure expected by the
detector (regex, terms) and report generator (recommendation_overrides), and
that the detector can load each sample without error.

Encoding: detector must load samples with UTF-8 Unicode content (multilingual terms)
without regression; see test_compliance_sample_unicode_terms_loadable.
"""

import tempfile
from pathlib import Path

import pytest
import yaml

# Repo root: tests/ -> parent -> parent
REPO_ROOT = Path(__file__).resolve().parent.parent
COMPLIANCE_SAMPLES_DIR = REPO_ROOT / "docs" / "compliance-samples"


def _compliance_sample_yaml_files():
    """All compliance-sample-*.yaml files in docs/compliance-samples/."""
    if not COMPLIANCE_SAMPLES_DIR.is_dir():
        return []
    return sorted(COMPLIANCE_SAMPLES_DIR.glob("compliance-sample-*.yaml"))


@pytest.fixture
def sample_files():
    """List of paths to compliance-sample-*.yaml files."""
    return _compliance_sample_yaml_files()


def test_compliance_sample_yaml_files_exist():
    """At least one compliance sample YAML exists (UK GDPR or more)."""
    files = _compliance_sample_yaml_files()
    assert len(files) >= 1, (
        "Expected at least one docs/compliance-samples/compliance-sample-*.yaml"
    )


def _validate_regex_section(data: dict, sample_name: str) -> None:
    """Assert regex/patterns list has items with name, pattern, norm_tag."""
    regex_items = data.get("regex") or data.get("patterns")
    if regex_items is None:
        return
    assert isinstance(regex_items, list), (
        f"{sample_name}: regex/patterns must be a list"
    )
    for i, item in enumerate(regex_items):
        assert isinstance(item, dict), f"{sample_name}: regex item {i} must be a dict"
        assert "name" in item and item.get("name"), (
            f"{sample_name}: regex item {i} must have non-empty name"
        )
        assert "pattern" in item and item.get("pattern"), (
            f"{sample_name}: regex item {i} must have non-empty pattern"
        )
        assert "norm_tag" in item, f"{sample_name}: regex item {i} must have norm_tag"


def _validate_terms_section(data: dict, sample_name: str) -> None:
    """Assert terms list has items with text and label."""
    terms_items = data.get("terms") or (
        data.get("patterns") if "regex" in data else None
    )
    if terms_items is None:
        return
    assert isinstance(terms_items, list), f"{sample_name}: terms must be a list"
    for i, item in enumerate(terms_items):
        assert isinstance(item, dict), f"{sample_name}: terms item {i} must be a dict"
        assert "text" in item and (item.get("text") or "").strip(), (
            f"{sample_name}: terms item {i} must have non-empty text"
        )
        assert "label" in item, f"{sample_name}: terms item {i} must have label"


def _validate_recommendation_overrides_section(data: dict, sample_name: str) -> None:
    """Assert recommendation_overrides list has items with required keys."""
    overrides = data.get("recommendation_overrides")
    if overrides is None:
        return
    assert isinstance(overrides, list), (
        f"{sample_name}: recommendation_overrides must be a list"
    )
    required_keys = (
        "norm_tag_pattern",
        "base_legal",
        "risk",
        "recommendation",
        "priority",
        "relevant_for",
    )
    for i, item in enumerate(overrides):
        assert isinstance(item, dict), (
            f"{sample_name}: recommendation_overrides item {i} must be a dict"
        )
        for key in required_keys:
            assert key in item, (
                f"{sample_name}: recommendation_overrides item {i} must have {key}"
            )


@pytest.mark.parametrize(
    "sample_path", _compliance_sample_yaml_files(), ids=lambda p: p.name
)
def test_compliance_sample_yaml_structure(sample_path):
    """
    Each compliance-sample-*.yaml has valid structure:
    - regex (or patterns): list of { name, pattern, norm_tag }
    - terms (or patterns for ML): list of { text, label }
    - recommendation_overrides: list of { norm_tag_pattern, base_legal, risk, recommendation, priority, relevant_for }
    """
    raw = sample_path.read_text(encoding="utf-8")
    data = yaml.safe_load(raw)
    assert isinstance(data, dict), f"{sample_path.name}: root must be a YAML mapping"

    _validate_regex_section(data, sample_path.name)
    _validate_terms_section(data, sample_path.name)
    _validate_recommendation_overrides_section(data, sample_path.name)

    has_regex = (data.get("regex") or data.get("patterns")) is not None
    has_terms = data.get("terms") is not None
    has_overrides = data.get("recommendation_overrides") is not None
    assert has_regex or has_terms or has_overrides, (
        f"{sample_path.name}: must contain at least one of regex, terms, or recommendation_overrides"
    )


@pytest.mark.parametrize(
    "sample_path", _compliance_sample_yaml_files(), ids=lambda p: p.name
)
def test_compliance_sample_loadable_by_detector(sample_path):
    """Detector can load each sample as regex_overrides_file and ml_patterns_file without error."""
    from core.scanner import DataScanner

    path_str = str(sample_path.resolve())
    scanner = DataScanner(
        regex_overrides_path=path_str,
        ml_patterns_path=path_str,
    )
    # Trigger a minimal analysis to ensure loader ran (no exception)
    result = scanner.scan_column("test_column", "some sample text")
    assert "sensitivity_level" in result
    assert "norm_tag" in result


def test_compliance_sample_unicode_terms_loadable():
    """Detector loads a compliance-style YAML with UTF-8 Unicode terms (multilingual support)."""
    from core.scanner import DataScanner

    sample = {
        "terms": [
            {"text": "personal information", "label": "sensitive"},
            {"text": "renseignements personnels", "label": "sensitive"},
            {"text": "個人情報", "label": "sensitive"},
        ],
        "recommendation_overrides": [
            {
                "norm_tag_pattern": "PIPEDA",
                "base_legal": "PIPEDA s. 2",
                "risk": "Risque",
                "recommendation": "Recomendação",
                "priority": "ALTA",
                "relevant_for": "DPO",
            },
        ],
    }
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".yaml", encoding="utf-8", delete=False
    ) as f:
        path = Path(f.name)
    try:
        path.write_text(
            yaml.dump(
                sample, default_flow_style=False, allow_unicode=True, sort_keys=False
            ),
            encoding="utf-8",
        )
        scanner = DataScanner(
            ml_patterns_path=str(path),
            file_encoding="utf-8",
        )
        result = scanner.scan_column("個人情報", "sample")
        assert "sensitivity_level" in result
    finally:
        path.unlink(missing_ok=True)


def test_single_class_compliance_terms_detect_declared_exact_term():
    """
    Regression #1195: one-class compliance terms must still detect exact declared terms.

    This test intentionally uses only ``sensitive`` labels to exercise the previous
    single-class ``predict_proba`` shape trap.
    """
    from core.scanner import DataScanner

    sample = {
        "terms": [
            {"text": "個人情報", "label": "sensitive"},
            {"text": "renseignements personnels", "label": "sensitive"},
        ]
    }
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".yaml", encoding="utf-8", delete=False
    ) as f:
        path = Path(f.name)
    try:
        path.write_text(
            yaml.dump(
                sample, default_flow_style=False, allow_unicode=True, sort_keys=False
            ),
            encoding="utf-8",
        )
        scanner = DataScanner(
            ml_patterns_path=str(path),
            file_encoding="utf-8",
        )
        result = scanner.scan_column("notes", "個人情報")
        assert result["sensitivity_level"] in ("MEDIUM", "HIGH")
        assert result["pattern_detected"] != "GENERAL"
    finally:
        path.unlink(missing_ok=True)


def test_ml_patterns_file_is_merged_with_default_terms():
    """Regression #1195: profile ml_patterns must extend defaults, not replace them."""
    from core.detector import _ml_terms_from_inline_or_file

    sample = {"terms": [{"text": "個人情報", "label": "sensitive"}]}
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".yaml", encoding="utf-8", delete=False
    ) as f:
        path = Path(f.name)
    try:
        path.write_text(
            yaml.dump(
                sample, default_flow_style=False, allow_unicode=True, sort_keys=False
            ),
            encoding="utf-8",
        )
        terms = _ml_terms_from_inline_or_file(None, str(path), encoding="utf-8")
        assert ("個人情報", 1) in terms
        assert ("email", 1) in terms
    finally:
        path.unlink(missing_ok=True)
