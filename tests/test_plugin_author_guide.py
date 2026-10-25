"""Guards for PLUGIN_AUTHOR_GUIDE (#836): YAML patterns vs remediation SDK."""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DOCS = REPO_ROOT / "docs"
SCHEMA = REPO_ROOT / "config" / "plugin_schema.yaml"
GUIDE_EN = DOCS / "PLUGIN_AUTHOR_GUIDE.md"
GUIDE_PT = DOCS / "PLUGIN_AUTHOR_GUIDE.pt_BR.md"
SDK_EN = DOCS / "PLUGIN_SDK.md"
README_EN = DOCS / "README.md"
README_PT = DOCS / "README.pt_BR.md"
PLAN_LINK_RE = re.compile(r"\[[^\]]*\]\(([^)]+)\)")


def test_author_guide_files_exist() -> None:
    assert GUIDE_EN.is_file()
    assert GUIDE_PT.is_file()
    assert SCHEMA.is_file()


def test_guide_distinguishes_yaml_patterns_from_remediation() -> None:
    en = GUIDE_EN.read_text(encoding="utf-8")
    pt = GUIDE_PT.read_text(encoding="utf-8")
    for text in (en, pt):
        assert "PLUGIN_SDK" in text
        assert "patterns_plugin_file" in text
        assert "regex_overrides_file" in text
        assert "plugin_schema.yaml" in text
        assert "ADR-0052" in text
        assert "ReDoS" in text or "redos" in text.lower()
        assert "#829" in text
        assert "validate-plugin" in text
        assert "custom_detectors" in text
        assert "remediation_plugin" in text
        assert "dga_classification" in text
        assert "iso27001_controls" in text
        assert "dmbok_area" in text
        assert "HEALTH_PLAN_ID" in text
        assert "no_sharing" in text
        assert "seguranca_dados" in text


def test_guide_does_not_claim_enterprise_gate_on_yaml_files() -> None:
    """FEATURE_TIER_MAP custom_detectors is reserved; YAML files are not gated today."""
    from core.licensing.tier_features import FEATURE_TIER_MAP, Tier

    assert FEATURE_TIER_MAP["custom_detectors"] is Tier.ENTERPRISE
    needle_dq = 'require_feature("custom_detectors")'
    needle_sq = "require_feature('custom_detectors')"
    callers: list[Path] = []
    for root in (REPO_ROOT / "core", REPO_ROOT / "config", REPO_ROOT / "api"):
        for path in root.rglob("*.py"):
            blob = path.read_text(encoding="utf-8")
            if needle_dq in blob or needle_sq in blob:
                callers.append(path)
    assert callers == []

    en = GUIDE_EN.read_text(encoding="utf-8")
    assert "**not** the gate" in en


def test_redos_guard_matches_guide_examples() -> None:
    from config.plugin_validator import _has_nested_quantifier

    assert _has_nested_quantifier("(a+)+") is True
    assert _has_nested_quantifier(r"(\w*)*") is True
    assert _has_nested_quantifier(r"(\\+55\\s?)?") is False
    assert _has_nested_quantifier(r"[+*]") is False


def test_guides_have_language_switchers() -> None:
    en = GUIDE_EN.read_text(encoding="utf-8")
    pt = GUIDE_PT.read_text(encoding="utf-8")
    assert "PLUGIN_AUTHOR_GUIDE.pt_BR.md" in en
    assert "PLUGIN_AUTHOR_GUIDE.md" in pt
    assert en.lstrip().startswith("# ")
    assert pt.lstrip().startswith("# ")


def test_readme_indexes_both_locales() -> None:
    en = README_EN.read_text(encoding="utf-8")
    pt = README_PT.read_text(encoding="utf-8")
    assert "PLUGIN_AUTHOR_GUIDE.md" in en
    assert "PLUGIN_AUTHOR_GUIDE.pt_BR.md" in en
    assert "PLUGIN_AUTHOR_GUIDE.md" in pt
    assert "PLUGIN_AUTHOR_GUIDE.pt_BR.md" in pt


def test_plugin_sdk_points_at_author_guide() -> None:
    sdk = SDK_EN.read_text(encoding="utf-8")
    assert "PLUGIN_AUTHOR_GUIDE.md" in sdk


def test_author_guides_have_no_plan_markdown_links() -> None:
    for path in (GUIDE_EN, GUIDE_PT):
        text = path.read_text(encoding="utf-8")
        for url in PLAN_LINK_RE.findall(text):
            raw = url.strip().split()[0].strip("<>")
            low = raw.lower()
            assert "/plans/" not in low
            assert not low.startswith("plans/")
            assert ".cursor/plans" not in low


def test_guide_grc_example_validates_as_unified_plugin(tmp_path) -> None:
    """Copy-paste HEALTH_PLAN_ID example from PLUGIN_AUTHOR_GUIDE must validate."""
    from config.plugin_validator import validate_plugin_file

    path = tmp_path / "grc_example.yaml"
    path.write_text(
        """
regex_patterns:
  - name: "HEALTH_PLAN_ID"
    pattern: "\\\\bHP-\\\\d{8}\\\\b"
    norm_tag: "LGPD Art. 5 II"
    dga_classification: no_sharing
    iso27001_controls:
      - A.5.33
      - A.8.11
    dmbok_area: seguranca_dados
""".strip()
        + "\n",
        encoding="utf-8",
    )
    result = validate_plugin_file(str(path), plugin_type="unified_plugin_file")
    assert result.valid is True, result.issues
