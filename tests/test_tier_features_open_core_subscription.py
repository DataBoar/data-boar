"""Open core vs subscription tier matrix (no secrets; deterministic)."""

from __future__ import annotations

import pytest

from core.licensing.guard import reset_license_guard_for_tests

from core.licensing.runtime_feature_tier import (
    get_runtime_tier_for_features,
    map_dbtier_string_to_tier,
)
from core.licensing.tier_features import (
    Tier,
    features_for_tier,
    is_feature_available,
)


@pytest.fixture(autouse=True)
def _reset_license_guard_between_tests():
    reset_license_guard_for_tests()
    yield
    reset_license_guard_for_tests()


@pytest.mark.parametrize(
    ("feature", "expected_community"),
    [
        ("scan_filesystem", True),
        ("report_html", True),
        ("report_pdf", False),
        ("maturity_self_assessment_poc", False),
        ("pdf_digital_signature", False),
    ],
)
def test_community_tier_feature_gates(feature: str, expected_community: bool):
    assert is_feature_available(feature, Tier.COMMUNITY) is expected_community


def test_open_tier_bypasses_feature_gates():
    """OPEN is lab / enforcement-off: all registered features allowed."""
    assert is_feature_available("maturity_self_assessment_poc", Tier.OPEN)
    assert is_feature_available("report_pdf", Tier.OPEN)
    assert is_feature_available("pdf_digital_signature", Tier.OPEN)
    assert is_feature_available("governance_lens_pro", Tier.OPEN)
    assert is_feature_available("governance_lens_enterprise", Tier.OPEN)


def test_pro_tier_includes_maturity_poc_and_pdf_report():
    assert is_feature_available("maturity_self_assessment_poc", Tier.PRO)
    assert is_feature_available("report_pdf", Tier.PRO)
    assert not is_feature_available("pdf_digital_signature", Tier.PRO)


def test_enterprise_tier_includes_pdf_signature():
    assert is_feature_available("pdf_digital_signature", Tier.ENTERPRISE)


def test_features_for_tier_includes_maturity_only_from_pro_up():
    comm = features_for_tier(Tier.COMMUNITY)
    pro = features_for_tier(Tier.PRO)
    assert "maturity_self_assessment_poc" not in comm
    assert "maturity_self_assessment_poc" in pro


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("", Tier.OPEN),
        ("pro", Tier.PRO),
        ("PRO", Tier.PRO),
        ("enterprise", Tier.ENTERPRISE),
        ("open_core", Tier.COMMUNITY),
        ("community", Tier.COMMUNITY),
        ("unknown_label", Tier.COMMUNITY),
    ],
)
def test_map_dbtier_string_to_tier(raw: str, expected: Tier):
    assert map_dbtier_string_to_tier(raw) == expected


def test_runtime_tier_open_when_no_effective_tier_and_open_license():
    cfg: dict = {
        "licensing": {"mode": "open", "effective_tier": ""},
        "api": {},
    }
    assert get_runtime_tier_for_features(cfg) == Tier.OPEN


def test_runtime_tier_from_yaml_effective_tier():
    cfg: dict = {
        "licensing": {"mode": "open", "effective_tier": "pro"},
        "api": {},
    }
    assert get_runtime_tier_for_features(cfg) == Tier.PRO


def test_runtime_tier_env_override_removed(monkeypatch):
    """#719: env override removed — YAML effective_tier wins even with dev env vars."""
    monkeypatch.setenv("DATA_BOAR_TIER_OVERRIDE", "enterprise")
    monkeypatch.setenv("DATA_BOAR_ENV", "ci")
    reset_license_guard_for_tests()
    cfg: dict = {
        "licensing": {"mode": "open", "effective_tier": "community"},
        "api": {},
    }
    assert get_runtime_tier_for_features(cfg) == Tier.COMMUNITY
