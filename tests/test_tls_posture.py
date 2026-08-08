"""S2a wave-2a: dashboard TLS cipher/protocol posture probe (no network bind)."""

from __future__ import annotations

import ssl
from unittest.mock import MagicMock

import core.tls_posture as tp


def test_find_weak_cipher_names_flags_denylist():
    names = [
        "TLS_AES_256_GCM_SHA384",
        "ECDHE-RSA-AES128-GCM-SHA256",
        "RC4-SHA",
        "DES-CBC3-SHA",
    ]
    weak = tp.find_weak_cipher_names(names)
    assert weak == ["RC4-SHA", "DES-CBC3-SHA"]


def test_find_weak_cipher_names_empty_when_modern_only():
    names = ["TLS_AES_128_GCM_SHA256", "ECDHE-ECDSA-CHACHA20-POLY1305"]
    assert tp.find_weak_cipher_names(names) == []


def test_probe_ssl_context_ok_for_default_tls12_server_context():
    tp.clear_tls_posture_snapshot()
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ctx.minimum_version = ssl.TLSVersion.TLSv1_2
    snap = tp.probe_ssl_context(ctx)
    assert snap["checked"] is True
    assert snap["ok"] is True
    assert snap["trust_reasons"] == []
    assert snap["minimum_tls_version"] == "TLSv1_2"
    assert snap["cipher_count"] >= 0


def test_probe_ssl_context_flags_protocol_below_baseline():
    ctx = MagicMock(spec=ssl.SSLContext)
    ctx.minimum_version = ssl.TLSVersion.TLSv1
    ctx.get_ciphers.return_value = [
        {"name": "ECDHE-RSA-AES128-GCM-SHA256"},
    ]
    snap = tp.probe_ssl_context(ctx)
    assert snap["ok"] is False
    assert tp.REASON_PROTOCOL in snap["trust_reasons"]
    assert "minimum_tls_version" in snap["issues"][0]


def test_probe_ssl_context_flags_weak_ciphers():
    ctx = MagicMock(spec=ssl.SSLContext)
    ctx.minimum_version = ssl.TLSVersion.TLSv1_2
    ctx.get_ciphers.return_value = [
        {"name": "ECDHE-RSA-AES128-GCM-SHA256"},
        {"name": "RC4-MD5"},
    ]
    snap = tp.probe_ssl_context(ctx)
    assert snap["ok"] is False
    assert tp.REASON_CIPHER in snap["trust_reasons"]
    assert "RC4-MD5" in snap["weak_ciphers"]


def test_set_get_clear_tls_posture_snapshot():
    tp.clear_tls_posture_snapshot()
    assert tp.get_tls_posture_snapshot() is None
    tp.set_tls_posture_snapshot({"checked": True, "ok": True, "trust_reasons": []})
    got = tp.get_tls_posture_snapshot()
    assert got is not None
    assert got["ok"] is True
    # Mutating returned copy must not alter store
    got["ok"] = False
    assert tp.get_tls_posture_snapshot()["ok"] is True
    tp.clear_tls_posture_snapshot()
    assert tp.get_tls_posture_snapshot() is None
