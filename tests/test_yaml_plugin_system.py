"""CI gate for ADR-0052 plugin_schema vs reference compliance samples (#413)."""

from pathlib import Path

from config.plugin_validator import validate_plugin_file

_REPO = Path(__file__).resolve().parents[1]

# Issue #413 named compliance-sample-us_ccpa.yaml; the CCPA pack on disk is the
# CPRA-amended sample (same California consumer-privacy inventory).
REFERENCE_SAMPLES = (
    _REPO / "docs/compliance-samples/compliance-sample-lgpd.yaml",
    _REPO / "docs/compliance-samples/compliance-sample-eu_gdpr.yaml",
    _REPO / "docs/compliance-samples/compliance-sample-us_ca_cpra.yaml",
)


def test_reference_compliance_samples_valid():
    for path in REFERENCE_SAMPLES:
        assert path.is_file(), f"missing reference sample {path}"
        result = validate_plugin_file(str(path), "compliance")
        assert result.valid, f"{path}: {result.issues}"


def test_compliance_type_allows_recommendation_overrides(tmp_path):
    path = tmp_path / "sample.yaml"
    path.write_text(
        """
regex:
  - name: "HINT"
    pattern: "\\\\bhint\\\\b"
    norm_tag: "Custom"
terms:
  - text: "personal data"
recommendation_overrides:
  HINT: "review with counsel"
""",
        encoding="utf-8",
    )
    result = validate_plugin_file(str(path), "compliance")
    assert result.valid, result.issues


def test_compliance_type_rejects_bad_regex_item(tmp_path):
    path = tmp_path / "bad.yaml"
    path.write_text(
        """
regex:
  - name: "NO_PATTERN"
terms: []
""",
        encoding="utf-8",
    )
    result = validate_plugin_file(str(path), "compliance")
    assert result.valid is False
    assert any("pattern" in issue for issue in result.issues)
