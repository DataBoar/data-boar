"""S2a wave-2a/2b: dashboard TLS posture probe (no network bind)."""

from __future__ import annotations

import datetime
import os
import ssl
import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID

import core.tls_posture as tp

REPO_ROOT = Path(__file__).resolve().parents[1]


def _write_self_signed_pem(cert_path: Path, key_path: Path) -> None:
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    subject = issuer = x509.Name(
        [x509.NameAttribute(NameOID.COMMON_NAME, "data-boar-tls-posture-test")]
    )
    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(
            datetime.datetime.now(datetime.UTC) - datetime.timedelta(days=1)
        )
        .not_valid_after(
            datetime.datetime.now(datetime.UTC) + datetime.timedelta(days=30)
        )
        .sign(key, hashes.SHA256())
    )
    cert_path.write_bytes(cert.public_bytes(serialization.Encoding.PEM))
    key_path.write_bytes(
        key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption(),
        )
    )


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
    assert tp.ENV_TLS_POSTURE not in os.environ
    tp.set_tls_posture_snapshot({"checked": True, "ok": True, "trust_reasons": []})
    assert tp.ENV_TLS_POSTURE in os.environ
    got = tp.get_tls_posture_snapshot()
    assert got is not None
    assert got["ok"] is True
    # Mutating returned copy must not alter store
    got["ok"] = False
    assert tp.get_tls_posture_snapshot()["ok"] is True
    tp.clear_tls_posture_snapshot()
    assert tp.get_tls_posture_snapshot() is None
    assert tp.ENV_TLS_POSTURE not in os.environ


def test_tls_posture_readable_in_child_process_like_uvicorn_worker():
    """
    api.workers>1: workers fork after supervisor set_tls_posture_snapshot.
    Child must see reasons via env (not supervisor-only module memory).
    """
    tp.clear_tls_posture_snapshot()
    tp.set_tls_posture_snapshot(
        {
            "checked": True,
            "ok": False,
            "trust_reasons": [tp.REASON_CIPHER],
            "weak_ciphers": ["RC4-MD5"],
            "summary": "TLS posture below baseline: weak_ciphers=RC4-MD5",
        }
    )
    try:
        child = r"""
import os, sys
sys.path.insert(0, os.environ["DATA_BOAR_REPO_ROOT"])
from core.tls_posture import ENV_TLS_POSTURE, REASON_CIPHER, get_tls_posture_snapshot
assert ENV_TLS_POSTURE in os.environ, "env missing in child"
snap = get_tls_posture_snapshot()
assert snap is not None
assert snap["ok"] is False
assert REASON_CIPHER in snap["trust_reasons"]
print("worker_ok")
"""
        env = os.environ.copy()
        env["DATA_BOAR_REPO_ROOT"] = str(REPO_ROOT)
        proc = subprocess.run(
            [sys.executable, "-c", child],
            env=env,
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
            check=False,
        )
        assert proc.returncode == 0, proc.stderr
        assert "worker_ok" in proc.stdout
    finally:
        tp.clear_tls_posture_snapshot()


def test_normalize_cert_fingerprints_accepts_list_and_scalar():
    a = "A" * 64
    b = "b" * 64
    colon = ":".join(a[i : i + 2] for i in range(0, 64, 2))
    assert tp.normalize_cert_fingerprints(a) == [a.lower()]
    assert tp.normalize_cert_fingerprints([colon, b, "not-a-fingerprint", a]) == [
        a.lower(),
        b.lower(),
    ]
    assert tp.normalize_cert_fingerprints(None) == []
    assert tp.expected_fingerprints_from_api_cfg(
        {"https_cert_fingerprint_sha256": [a, b]}
    ) == [a.lower(), b.lower()]


def test_probe_observe_fingerprint_without_baseline(tmp_path: Path):
    cert = tmp_path / "cert.pem"
    key = tmp_path / "key.pem"
    _write_self_signed_pem(cert, key)
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ctx.minimum_version = ssl.TLSVersion.TLSv1_2
    snap = tp.probe_ssl_context(ctx, cert_path=cert, expected_fingerprints=None)
    assert snap["ok"] is True
    assert snap["cert_fingerprint_sha256"]
    assert len(snap["cert_fingerprint_sha256"]) == 64
    assert snap["cert_fingerprint_baseline"] == []
    assert snap["cert_fingerprint_match"] is None
    assert tp.REASON_FINGERPRINT not in snap["trust_reasons"]


def test_probe_fingerprint_match_any_in_rotation_list(tmp_path: Path):
    cert = tmp_path / "cert.pem"
    key = tmp_path / "key.pem"
    _write_self_signed_pem(cert, key)
    current = tp.sha256_fingerprint_pem_file(cert)
    old = "0" * 64
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ctx.minimum_version = ssl.TLSVersion.TLSv1_2
    snap = tp.probe_ssl_context(
        ctx,
        cert_path=cert,
        expected_fingerprints=[old, current.upper()],
    )
    assert snap["ok"] is True
    assert snap["cert_fingerprint_match"] is True
    assert snap["cert_fingerprint_baseline"] == [old, current]
    assert tp.REASON_FINGERPRINT not in snap["trust_reasons"]


def test_probe_fingerprint_mismatch_degrades(tmp_path: Path):
    cert = tmp_path / "cert.pem"
    key = tmp_path / "key.pem"
    _write_self_signed_pem(cert, key)
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ctx.minimum_version = ssl.TLSVersion.TLSv1_2
    snap = tp.probe_ssl_context(
        ctx,
        cert_path=cert,
        expected_fingerprints=["f" * 64],
    )
    assert snap["ok"] is False
    assert snap["cert_fingerprint_match"] is False
    assert tp.REASON_FINGERPRINT in snap["trust_reasons"]
