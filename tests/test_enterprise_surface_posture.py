"""Tests for core.enterprise_surface_posture (transport + trust + access surface bundle)."""

from __future__ import annotations

import core.enterprise_surface_posture as esp_mod


def test_enterprise_surface_nominal_open_core(monkeypatch):
    monkeypatch.setattr(
        esp_mod,
        "get_dashboard_transport_snapshot",
        lambda: {
            "mode": "https",
            "tls_active": True,
            "insecure_http_explicit_opt_in": False,
            "show_insecure_banner": False,
        },
    )
    monkeypatch.setattr(
        esp_mod,
        "get_runtime_trust_snapshot",
        lambda _cfg: {
            "trust_state": "trusted",
            "trust_level": "expected",
            "license_state": "OPEN",
            "license_mode": "open",
        },
    )
    out = esp_mod.get_enterprise_surface_posture({"api": {"require_api_key": False}})
    assert out["severity"] == "nominal"
    assert out["access_surface"]["mode"] == "open_html"
    assert out["access_surface"]["rbac"] == "not_implemented"


def test_enterprise_surface_elevated_plaintext(monkeypatch):
    monkeypatch.setattr(
        esp_mod,
        "get_dashboard_transport_snapshot",
        lambda: {
            "mode": "http",
            "tls_active": False,
            "insecure_http_explicit_opt_in": True,
            "show_insecure_banner": True,
        },
    )
    monkeypatch.setattr(
        esp_mod,
        "get_runtime_trust_snapshot",
        lambda _cfg: {
            "trust_state": "trusted",
            "trust_level": "expected",
            "license_state": "OPEN",
            "license_mode": "open",
        },
    )
    out = esp_mod.get_enterprise_surface_posture({"api": {"require_api_key": False}})
    assert out["severity"] == "elevated"
    assert out["reasons"] == ["plaintext_http_explicit"]


def test_enterprise_surface_elevated_on_fingerprint_mismatch(monkeypatch):
    monkeypatch.setattr(
        esp_mod,
        "get_dashboard_transport_snapshot",
        lambda: {
            "mode": "https",
            "tls_active": True,
            "insecure_http_explicit_opt_in": False,
            "show_insecure_banner": False,
            "tls_posture": {
                "checked": True,
                "ok": False,
                "trust_reasons": ["tls_cert_fingerprint_mismatch"],
            },
        },
    )
    monkeypatch.setattr(
        esp_mod,
        "get_runtime_trust_snapshot",
        lambda _cfg: {
            "trust_state": "trusted",
            "trust_level": "expected",
            "license_state": "OPEN",
            "license_mode": "open",
        },
    )
    monkeypatch.setattr(
        "core.integrity_anchor.get_integrity_snapshot",
        lambda: {"integrity_state": "ok"},
    )
    out = esp_mod.get_enterprise_surface_posture({"api": {"require_api_key": False}})
    assert out["severity"] == "elevated"
    assert "tls_cert_fingerprint_mismatch" in out["reasons"]


def test_enterprise_surface_elevated_api_key_misconfigured(monkeypatch):
    monkeypatch.setattr(
        esp_mod,
        "get_dashboard_transport_snapshot",
        lambda: {
            "mode": "https",
            "tls_active": True,
            "insecure_http_explicit_opt_in": False,
            "show_insecure_banner": False,
        },
    )
    monkeypatch.setattr(
        esp_mod,
        "get_runtime_trust_snapshot",
        lambda _cfg: {
            "trust_state": "trusted",
            "trust_level": "expected",
            "license_state": "OPEN",
            "license_mode": "open",
        },
    )
    out = esp_mod.get_enterprise_surface_posture(
        {"api": {"require_api_key": True, "api_key": ""}}
    )
    assert out["severity"] == "elevated"
    assert "api_key_required_but_unresolved" in out["reasons"]
    assert out["access_surface"]["mode"] == "api_key_misconfigured"


def test_enterprise_surface_caution_license_degraded(monkeypatch):
    monkeypatch.setattr(
        esp_mod,
        "get_dashboard_transport_snapshot",
        lambda: {
            "mode": "https",
            "tls_active": True,
            "insecure_http_explicit_opt_in": False,
            "show_insecure_banner": False,
        },
    )
    monkeypatch.setattr(
        esp_mod,
        "get_runtime_trust_snapshot",
        lambda _cfg: {
            "trust_state": "degraded",
            "trust_level": "expected",
            "license_state": "VALID",
            "license_mode": "enforced",
        },
    )
    out = esp_mod.get_enterprise_surface_posture({"api": {"require_api_key": False}})
    assert out["severity"] == "caution"
    assert "license_trust_degraded" in out["reasons"]


def test_enterprise_surface_rbac_enabled_when_config_and_tier_allow(monkeypatch):
    monkeypatch.setattr(
        esp_mod,
        "get_dashboard_transport_snapshot",
        lambda: {
            "mode": "https",
            "tls_active": True,
            "insecure_http_explicit_opt_in": False,
            "show_insecure_banner": False,
        },
    )
    monkeypatch.setattr(
        esp_mod,
        "get_runtime_trust_snapshot",
        lambda _cfg: {
            "trust_state": "trusted",
            "trust_level": "expected",
            "license_state": "OPEN",
            "license_mode": "open",
        },
    )
    cfg = {
        "api": {
            "require_api_key": False,
            "rbac": {"enabled": True},
        },
        "licensing": {"effective_tier": "pro"},
    }
    out = esp_mod.get_enterprise_surface_posture(cfg)
    assert out["access_surface"]["rbac"] == "enabled"
