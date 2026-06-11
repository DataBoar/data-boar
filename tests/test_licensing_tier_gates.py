"""Tier licensing fixtures and graceful feature denial (#559)."""

from __future__ import annotations

import os

import pytest

from core.licensing.guard import LicenseGuard, reset_license_guard_for_tests
from core.licensing.runtime_feature_tier import get_runtime_tier_for_features
from core.licensing.tier_features import Tier


def _guard_for_effective_tier(tier: str) -> LicenseGuard:
    reset_license_guard_for_tests()
    return LicenseGuard({"licensing": {"mode": "open", "effective_tier": tier}})


@pytest.fixture
def community_guard():
    return _guard_for_effective_tier("community")


@pytest.fixture
def pro_guard():
    return _guard_for_effective_tier("pro")


@pytest.fixture
def enterprise_guard():
    return _guard_for_effective_tier("enterprise")


@pytest.fixture(autouse=True)
def _clean_license_env():
    reset_license_guard_for_tests()
    keys = (
        "DATA_BOAR_TIER_OVERRIDE",
        "DATA_BOAR_ENV",
        "DEBUG",
        "DATA_BOAR_LICENSE_MODE",
    )
    saved = {k: os.environ.get(k) for k in keys}
    yield
    reset_license_guard_for_tests()
    for k, v in saved.items():
        if v is None:
            os.environ.pop(k, None)
        else:
            os.environ[k] = v


def test_scheduler_allowed_pro(pro_guard):
    assert pro_guard.is_allowed("scan_scheduler_pro")


def test_scheduler_allowed_enterprise(enterprise_guard):
    assert enterprise_guard.is_allowed("scan_scheduler_pro")


def test_governance_lens_allowed_pro(pro_guard):
    assert pro_guard.is_allowed("governance_lens_pro")


def test_governance_lens_enterprise_allowed(enterprise_guard):
    assert enterprise_guard.is_allowed("governance_lens_enterprise")


def test_scheduler_denied_community(community_guard):
    result = community_guard.check_feature("scan_scheduler_pro")
    assert not result.allowed
    assert result.reason
    assert "Pro" in result.reason or "upgrade" in result.reason.lower()


def test_governance_lens_denied_community(community_guard):
    result = community_guard.check_feature("governance_lens_pro")
    assert not result.allowed
    assert result.reason


def test_governance_lens_enterprise_denied_pro(pro_guard):
    result = pro_guard.check_feature("governance_lens_enterprise")
    assert not result.allowed


def test_findings_sink_sql_denied_community(community_guard):
    result = community_guard.check_feature("findings_sink_sql")
    assert not result.allowed


def test_scan_max_workers_enterprise_denied_pro(pro_guard):
    result = pro_guard.check_feature("scan_max_workers_enterprise")
    assert not result.allowed


def test_tier_override_env_removed_no_bypass(monkeypatch):
    """#719: DATA_BOAR_TIER_OVERRIDE no longer exists — env never changes tier."""
    monkeypatch.setenv("DATA_BOAR_TIER_OVERRIDE", "community")
    monkeypatch.setenv("DATA_BOAR_ENV", "development")
    reset_license_guard_for_tests()
    cfg = {"licensing": {"mode": "open", "effective_tier": "pro"}}
    assert get_runtime_tier_for_features(cfg) == Tier.PRO
    g = LicenseGuard(cfg)
    assert g.is_allowed("governance_lens_pro")
