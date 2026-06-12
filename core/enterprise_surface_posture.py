"""
Enterprise-facing snapshot: transport + license trust + global API-key surface.

When ``api.rbac.enabled`` is active and tier allows it, ``access_surface.rbac`` reflects enforcement;
otherwise it stays ``not_implemented``. It pairs transport and access posture
for `/status`, `/health`, and dashboard banners so demos can show a single JSON
bundle aligned with PLAN_DASHBOARD_REPORTS_ACCESS_CONTROL Phase 0 narrative.
"""

from __future__ import annotations

from typing import Any

from core.dashboard_transport import get_dashboard_transport_snapshot
from core.host_resolution import effective_api_key_configured
from core.rbac_settings import rbac_enforcement_active
from core.runtime_trust import get_runtime_trust_snapshot


def _severity_from_reasons(reasons: list[str]) -> str:
    if (
        "plaintext_http_explicit" in reasons
        or "license_trust_untrusted" in reasons
        or "api_key_required_but_unresolved" in reasons
        or "integrity_tampered" in reasons
    ):
        return "elevated"
    if "license_trust_degraded" in reasons:
        return "caution"
    return "nominal"


def get_enterprise_surface_posture(config: dict[str, Any]) -> dict[str, Any]:
    """
    Return a stable dict for API consumers and templates.

    ``severity`` drives tinted UI: ``nominal`` | ``caution`` | ``elevated``.
    """
    dt = get_dashboard_transport_snapshot()
    rt = get_runtime_trust_snapshot(config)
    api_cfg = config.get("api") if isinstance(config.get("api"), dict) else {}
    require_key = bool(api_cfg.get("require_api_key"))
    key_ok = effective_api_key_configured(api_cfg)

    if require_key and key_ok:
        access_mode = "api_key_global"
    elif require_key and not key_ok:
        access_mode = "api_key_misconfigured"
    else:
        access_mode = "open_html"

    trust_state = str(rt.get("trust_state") or "unknown")

    reasons: list[str] = []
    mode = str(dt.get("mode") or "")
    insecure = bool(dt.get("insecure_http_explicit_opt_in"))
    if mode == "http" and insecure:
        reasons.append("plaintext_http_explicit")
    if trust_state == "untrusted":
        reasons.append("license_trust_untrusted")
    if trust_state == "degraded":
        reasons.append("license_trust_degraded")
    if access_mode == "api_key_misconfigured":
        reasons.append("api_key_required_but_unresolved")

    # #856: tampered integrity anchor tints the whole posture (ADR-0066).
    from core.integrity_anchor import get_integrity_snapshot

    integrity_state = str(get_integrity_snapshot().get("integrity_state", "unknown"))
    if integrity_state == "tampered":
        reasons.append("integrity_tampered")

    severity = _severity_from_reasons(reasons)

    rbac_on = rbac_enforcement_active(config)
    rbac_val = "enabled" if rbac_on else "not_implemented"
    rbac_note = (
        "Per-route roles enforced when api.rbac.enabled and tier allows dashboard_rbac; "
        "see USAGE / TECH_GUIDE."
    )
    if not rbac_on:
        rbac_note = (
            "Per-route RBAC is optional (api.rbac); when off, only the global API key gate applies "
            "if api.require_api_key is true."
        )

    summary_parts = [
        f"transport={mode}",
        f"trust_state={trust_state}",
        f"access={access_mode}",
    ]
    return {
        "severity": severity,
        "reasons": reasons,
        "summary": "; ".join(summary_parts),
        "dashboard_transport": dt,
        "runtime_trust": {
            "trust_state": trust_state,
            "trust_level": rt.get("trust_level"),
            "license_state": rt.get("license_state"),
            "license_mode": rt.get("license_mode"),
        },
        "access_surface": {
            "mode": access_mode,
            "require_api_key": require_key,
            "effective_api_key_configured": key_ok,
            "rbac": rbac_val,
            "note": rbac_note,
        },
    }
