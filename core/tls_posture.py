"""
Dashboard TLS posture self-check (S2a wave-2a/2b / GRC A3 thin).

Probes the HTTPS ``SSLContext`` for minimum protocol and weak cipher names,
and optionally the leaf cert SHA-256 fingerprint against a configured allow-list
(rotation-safe: any listed digest matches).

Results feed ``dashboard_transport.tls_posture`` and canonical ``trust_reasons``.
No network bind — inspects the context / PEM OpenSSL will use for the listener.

Publish via ``os.environ`` (same pattern as ``configure_dashboard_transport``)
so uvicorn worker processes that fork after startup still see the probe result.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import ssl
from pathlib import Path
from typing import Any

from cryptography import x509
from cryptography.hazmat.primitives import serialization

# Substrings matched against OpenSSL cipher *names* (case-insensitive).
# Keep conservative: only clearly weak / export / NULL suites.
_WEAK_CIPHER_TOKENS = (
    "RC4",
    "DES-CBC",
    "DES-CBC3",
    "3DES",
    "MD5",
    "NULL",
    "EXP",
    "EXPORT",
    "aNULL",
    "eNULL",
    "ADH",
    "AECDH",
    "IDEA",
    "SEED",
)

REASON_PROTOCOL = "tls_protocol_below_baseline"
REASON_CIPHER = "tls_cipher_baseline_weak"
REASON_FINGERPRINT = "tls_cert_fingerprint_mismatch"

_TLS_TRUST_REASONS = (REASON_PROTOCOL, REASON_CIPHER, REASON_FINGERPRINT)

# Survives uvicorn worker fork (unlike a module-global only).
ENV_TLS_POSTURE = "DATA_BOAR_TLS_POSTURE"

_HEX64 = re.compile(r"^[0-9a-f]{64}$")


def clear_tls_posture_snapshot() -> None:
    """Drop published posture (HTTP mode or tests)."""
    os.environ.pop(ENV_TLS_POSTURE, None)


def set_tls_posture_snapshot(snapshot: dict[str, Any]) -> None:
    """Publish posture to the environment (read by API workers and status)."""
    os.environ[ENV_TLS_POSTURE] = json.dumps(
        snapshot, separators=(",", ":"), sort_keys=True
    )


def get_tls_posture_snapshot() -> dict[str, Any] | None:
    """
    Return last probe result from the environment, or None if unset / invalid.

    Workers must not rely on supervisor-only memory — always read ``ENV_TLS_POSTURE``.
    """
    raw = os.environ.get(ENV_TLS_POSTURE)
    if not raw:
        return None
    try:
        data = json.loads(raw)
    except (TypeError, ValueError, json.JSONDecodeError):
        return None
    if not isinstance(data, dict):
        return None
    return dict(data)


def find_weak_cipher_names(cipher_names: list[str]) -> list[str]:
    """Return cipher names that match the weak-token denylist (stable order)."""
    weak: list[str] = []
    seen: set[str] = set()
    for name in cipher_names:
        upper = name.upper()
        if any(tok in upper for tok in _WEAK_CIPHER_TOKENS):
            if name not in seen:
                seen.add(name)
                weak.append(name)
    return weak


def normalize_cert_fingerprints(raw: Any) -> list[str]:
    """
    Normalize ``api.https_cert_fingerprint_sha256`` to unique lowercase hex digests.

    Accepts a single string or a list of strings. Colons/spaces/hyphens are stripped.
    Invalid entries (not 64 hex chars after normalize) are dropped.
    """
    if raw is None:
        return []
    items: list[Any]
    if isinstance(raw, str):
        items = [raw]
    elif isinstance(raw, (list, tuple)):
        items = list(raw)
    else:
        return []
    out: list[str] = []
    seen: set[str] = set()
    for item in items:
        if not isinstance(item, str):
            continue
        cleaned = re.sub(r"[\s:\-]", "", item.strip()).lower()
        if not _HEX64.match(cleaned):
            continue
        if cleaned not in seen:
            seen.add(cleaned)
            out.append(cleaned)
    return out


def expected_fingerprints_from_api_cfg(api_cfg: dict[str, Any] | None) -> list[str]:
    """Read and normalize ``api.https_cert_fingerprint_sha256`` (list or scalar)."""
    if not api_cfg:
        return []
    return normalize_cert_fingerprints(api_cfg.get("https_cert_fingerprint_sha256"))


def sha256_fingerprint_pem_file(path: str | Path) -> str:
    """
    Return lowercase hex SHA-256 of the leaf certificate DER from a PEM file.

    Uses the first certificate in the file (leaf / end-entity).
    """
    data = Path(path).read_bytes()
    cert = x509.load_pem_x509_certificate(data)
    der = cert.public_bytes(serialization.Encoding.DER)
    return hashlib.sha256(der).hexdigest()


def _tls_version_label(version: ssl.TLSVersion | int | None) -> str:
    if version is None:
        return "unknown"
    try:
        return ssl.TLSVersion(version).name
    except (ValueError, TypeError):
        return str(version)


def probe_ssl_context(
    ctx: ssl.SSLContext,
    *,
    cert_path: str | Path | None = None,
    expected_fingerprints: Any = None,
) -> dict[str, Any]:
    """
    Inspect ``ctx`` for TLS >= 1.2, weak cipher names, and optional cert fingerprint.

    Fingerprint baseline (wave-2b):
    - No configured baseline → observe/display current fingerprint only (no trust downgrade).
    - Baseline list present → match **any** digest (rotation window); else
      ``tls_cert_fingerprint_mismatch``.

    Returns a JSON-serializable snapshot with ``ok``, ``issues``, and
    ``trust_reasons`` suitable for canonical trust folding.
    """
    issues: list[str] = []
    trust_reasons: list[str] = []

    min_ver = getattr(ctx, "minimum_version", None)
    min_label = _tls_version_label(min_ver)
    if min_ver is None or (
        isinstance(min_ver, ssl.TLSVersion) and min_ver < ssl.TLSVersion.TLSv1_2
    ):
        issues.append(f"minimum_tls_version={min_label} (require TLSv1_2+)")
        trust_reasons.append(REASON_PROTOCOL)

    cipher_names: list[str] = []
    try:
        for item in ctx.get_ciphers() or []:
            name = item.get("name") if isinstance(item, dict) else None
            if name:
                cipher_names.append(str(name))
    except (AttributeError, NotImplementedError, ValueError):
        cipher_names = []

    weak = find_weak_cipher_names(cipher_names)
    if weak:
        issues.append("weak_ciphers=" + ",".join(weak[:12]))
        trust_reasons.append(REASON_CIPHER)

    baseline = normalize_cert_fingerprints(expected_fingerprints)
    current_fp: str | None = None
    fp_match: bool | None = None
    if cert_path is not None:
        try:
            current_fp = sha256_fingerprint_pem_file(cert_path)
        except (OSError, ValueError, TypeError) as exc:
            issues.append(f"cert_fingerprint_unreadable={exc.__class__.__name__}")
            if baseline:
                trust_reasons.append(REASON_FINGERPRINT)
                fp_match = False
        else:
            if baseline:
                fp_match = current_fp in baseline
                if not fp_match:
                    issues.append(
                        "cert_fingerprint_mismatch="
                        f"current={current_fp[:16]}… "
                        f"baseline_count={len(baseline)}"
                    )
                    trust_reasons.append(REASON_FINGERPRINT)
            # else: observe-only — fp_match stays None

    ok = not trust_reasons
    if ok:
        fp_note = (
            f", fingerprint={current_fp[:16]}… (observe)"
            if current_fp and fp_match is None
            else (
                f", fingerprint_match=true (baseline={len(baseline)})"
                if current_fp and fp_match is True
                else ""
            )
        )
        summary = (
            f"TLS posture OK (minimum={min_label}, "
            f"ciphers_checked={len(cipher_names)}, weak=0{fp_note})."
        )
    else:
        summary = "TLS posture below baseline: " + "; ".join(issues)

    ordered = [r for r in _TLS_TRUST_REASONS if r in trust_reasons]

    return {
        "checked": True,
        "ok": ok,
        "minimum_tls_version": min_label,
        "cipher_count": len(cipher_names),
        "weak_ciphers": weak,
        "cert_fingerprint_sha256": current_fp,
        "cert_fingerprint_baseline": baseline,
        "cert_fingerprint_match": fp_match,
        "issues": issues,
        "trust_reasons": ordered,
        "summary": summary,
    }
