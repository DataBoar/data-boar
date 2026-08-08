"""
Canonical runtime trust_state (S2a / GRC A1–A2 marker).

Combines license trust, integrity tamper, and dashboard transport insecurity into
one operator-facing ``trusted`` | ``degraded`` | ``untrusted`` contract for
``GET /status``, ``GET /health``, and ``--export-audit-trail``.

Does not replace ``runtime_trust`` (license-focused) or ``enterprise_surface``
(severity bundle); those remain for existing consumers.
"""

from __future__ import annotations

from typing import Any

from core.dashboard_transport import get_dashboard_transport_snapshot
from core.runtime_trust import get_runtime_trust_snapshot

_STATE_RANK = {"trusted": 0, "degraded": 1, "untrusted": 2}
_CONFIDENCE = {
    "trusted": "full",
    "degraded": "reduced",
    "untrusted": "minimal",
}


def _worse(a: str, b: str) -> str:
    return a if _STATE_RANK.get(a, 0) >= _STATE_RANK.get(b, 0) else b


def get_canonical_trust_snapshot(config: dict[str, Any]) -> dict[str, Any]:
    """
    Return canonical trust fields for status/health/audit surfaces.

    Keys: ``trust_state``, ``trust_reasons``, ``output_confidence``,
    plus compact ``license_trust_state`` / ``integrity_state`` / ``transport_mode``
    for demos without digging into nested objects.
    """
    rt = get_runtime_trust_snapshot(config)
    dt = get_dashboard_transport_snapshot()

    from core.integrity_anchor import get_integrity_snapshot

    integrity_state = str(get_integrity_snapshot().get("integrity_state") or "unknown")

    license_state = str(rt.get("trust_state") or "degraded")
    if license_state not in _STATE_RANK:
        license_state = "degraded"

    state = license_state
    reasons: list[str] = []

    if license_state == "untrusted":
        reasons.append("license_trust_untrusted")
    elif license_state == "degraded":
        reasons.append("license_trust_degraded")

    if integrity_state == "tampered":
        state = _worse(state, "untrusted")
        reasons.append("integrity_tampered")

    mode = str(dt.get("mode") or "")
    insecure = bool(dt.get("insecure_http_explicit_opt_in"))
    if mode == "http" and insecure:
        state = _worse(state, "degraded")
        reasons.append("plaintext_http_explicit")

    # Stable order for tests / demos
    reason_order = (
        "integrity_tampered",
        "license_trust_untrusted",
        "license_trust_degraded",
        "plaintext_http_explicit",
    )
    ordered = [r for r in reason_order if r in reasons]
    for r in reasons:
        if r not in ordered:
            ordered.append(r)

    return {
        "trust_state": state,
        "trust_reasons": ordered,
        "output_confidence": _CONFIDENCE.get(state, "reduced"),
        "license_trust_state": str(rt.get("trust_state") or "unknown"),
        "integrity_state": integrity_state,
        "transport_mode": mode or "unknown",
    }
