"""S2a wave-1: canonical trust_state (license + integrity + transport)."""

from __future__ import annotations

import core.canonical_trust as ct


def test_canonical_trusted_https_open_license(monkeypatch):
    monkeypatch.setattr(
        ct,
        "get_dashboard_transport_snapshot",
        lambda: {
            "mode": "https",
            "tls_active": True,
            "insecure_http_explicit_opt_in": False,
        },
    )
    monkeypatch.setattr(
        ct,
        "get_runtime_trust_snapshot",
        lambda _cfg: {"trust_state": "trusted", "license_state": "OPEN"},
    )
    monkeypatch.setattr(
        "core.integrity_anchor.get_integrity_snapshot",
        lambda: {"integrity_state": "ok"},
    )
    snap = ct.get_canonical_trust_snapshot({})
    assert snap["trust_state"] == "trusted"
    assert snap["trust_reasons"] == []
    assert snap["output_confidence"] == "full"


def test_canonical_degraded_on_plaintext_http(monkeypatch):
    monkeypatch.setattr(
        ct,
        "get_dashboard_transport_snapshot",
        lambda: {
            "mode": "http",
            "tls_active": False,
            "insecure_http_explicit_opt_in": True,
        },
    )
    monkeypatch.setattr(
        ct,
        "get_runtime_trust_snapshot",
        lambda _cfg: {"trust_state": "trusted", "license_state": "OPEN"},
    )
    monkeypatch.setattr(
        "core.integrity_anchor.get_integrity_snapshot",
        lambda: {"integrity_state": "ok"},
    )
    snap = ct.get_canonical_trust_snapshot({})
    assert snap["trust_state"] == "degraded"
    assert snap["trust_reasons"] == ["plaintext_http_explicit"]
    assert snap["output_confidence"] == "reduced"
    assert snap["license_trust_state"] == "trusted"


def test_canonical_untrusted_on_integrity_tamper(monkeypatch):
    monkeypatch.setattr(
        ct,
        "get_dashboard_transport_snapshot",
        lambda: {
            "mode": "https",
            "tls_active": True,
            "insecure_http_explicit_opt_in": False,
        },
    )
    monkeypatch.setattr(
        ct,
        "get_runtime_trust_snapshot",
        lambda _cfg: {"trust_state": "trusted", "license_state": "OPEN"},
    )
    monkeypatch.setattr(
        "core.integrity_anchor.get_integrity_snapshot",
        lambda: {"integrity_state": "tampered"},
    )
    snap = ct.get_canonical_trust_snapshot({})
    assert snap["trust_state"] == "untrusted"
    assert "integrity_tampered" in snap["trust_reasons"]
    assert snap["output_confidence"] == "minimal"


def test_canonical_untrusted_wins_over_plaintext(monkeypatch):
    monkeypatch.setattr(
        ct,
        "get_dashboard_transport_snapshot",
        lambda: {
            "mode": "http",
            "tls_active": False,
            "insecure_http_explicit_opt_in": True,
        },
    )
    monkeypatch.setattr(
        ct,
        "get_runtime_trust_snapshot",
        lambda _cfg: {"trust_state": "untrusted", "license_state": "REVOKED"},
    )
    monkeypatch.setattr(
        "core.integrity_anchor.get_integrity_snapshot",
        lambda: {"integrity_state": "ok"},
    )
    snap = ct.get_canonical_trust_snapshot({})
    assert snap["trust_state"] == "untrusted"
    assert snap["trust_reasons"] == [
        "license_trust_untrusted",
        "plaintext_http_explicit",
    ]


def test_not_configured_transport_does_not_degrade(monkeypatch):
    monkeypatch.setattr(
        ct,
        "get_dashboard_transport_snapshot",
        lambda: {
            "mode": "not_configured",
            "tls_active": False,
            "insecure_http_explicit_opt_in": False,
        },
    )
    monkeypatch.setattr(
        ct,
        "get_runtime_trust_snapshot",
        lambda _cfg: {"trust_state": "trusted", "license_state": "OPEN"},
    )
    monkeypatch.setattr(
        "core.integrity_anchor.get_integrity_snapshot",
        lambda: {"integrity_state": "unknown"},
    )
    snap = ct.get_canonical_trust_snapshot({})
    assert snap["trust_state"] == "trusted"
    assert "plaintext_http_explicit" not in snap["trust_reasons"]
