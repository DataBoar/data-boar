"""
Dashboard TLS posture self-check (S2a wave-2a / GRC A3 thin).

Probes the HTTPS ``SSLContext`` for minimum protocol and weak cipher names.
Results feed ``dashboard_transport.tls_posture`` and canonical ``trust_reasons``.
No network bind — inspects the context OpenSSL will use for the listener.
"""

from __future__ import annotations

import ssl
from typing import Any

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

_last_snapshot: dict[str, Any] | None = None


def clear_tls_posture_snapshot() -> None:
    """Drop process-local posture (HTTP mode or tests)."""
    global _last_snapshot
    _last_snapshot = None


def set_tls_posture_snapshot(snapshot: dict[str, Any]) -> None:
    """Publish posture for status/health/audit within this process."""
    global _last_snapshot
    _last_snapshot = dict(snapshot)


def get_tls_posture_snapshot() -> dict[str, Any] | None:
    """Return last probe result, or None if HTTPS was not configured this run."""
    return None if _last_snapshot is None else dict(_last_snapshot)


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


def _tls_version_label(version: ssl.TLSVersion | int | None) -> str:
    if version is None:
        return "unknown"
    try:
        return ssl.TLSVersion(version).name
    except (ValueError, TypeError):
        return str(version)


def probe_ssl_context(ctx: ssl.SSLContext) -> dict[str, Any]:
    """
    Inspect ``ctx`` for TLS >= 1.2 and absence of weak cipher names.

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

    ok = not trust_reasons
    if ok:
        summary = (
            f"TLS posture OK (minimum={min_label}, "
            f"ciphers_checked={len(cipher_names)}, weak=0)."
        )
    else:
        summary = "TLS posture below baseline: " + "; ".join(issues)

    # Stable reason order
    ordered = [r for r in (REASON_PROTOCOL, REASON_CIPHER) if r in trust_reasons]

    return {
        "checked": True,
        "ok": ok,
        "minimum_tls_version": min_label,
        "cipher_count": len(cipher_names),
        "weak_ciphers": weak,
        "issues": issues,
        "trust_reasons": ordered,
        "summary": summary,
    }
