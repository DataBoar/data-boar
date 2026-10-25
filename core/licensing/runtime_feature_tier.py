"""
Resolve effective product tier for feature gating (YAML ``licensing.effective_tier``, JWT ``dbtier``).

Shared by API routes, RBAC, and maturity POC so tier logic stays in one place.

Enforcement contract (#719 — no env bypass):

- Environment variables (``DATA_BOAR_ENV``, ``DEBUG``, ``DATA_BOAR_TIER_OVERRIDE``)
  can **never** alter the effective tier or disable enforcement. The former
  dev/CI override path was removed — it let a misconfigured production
  container (``DEBUG=1``) grant Enterprise without a JWT and without audit.
- In ``mode: enforced`` the tier comes **only** from a validated signed
  license (``dbtier`` claim, state VALID/GRACE). Any other state fails
  **closed** to Community, with a CRITICAL audit record. ``licensing.
  effective_tier`` from YAML is ignored in enforced mode.
- In ``mode: open`` (default) lab simulation via ``licensing.effective_tier``
  stays available; default is OPEN (all features on).
"""

from __future__ import annotations

import logging
from typing import Any

from core.licensing.audit import audit_enforcement_event
from core.licensing.tier_features import Tier

logger = logging.getLogger("data_boar.licensing")


def map_dbtier_string_to_tier(raw: str) -> Tier:
    """Map JWT ``dbtier`` / lab ``effective_tier`` strings to :class:`Tier`."""
    r = raw.strip().lower()
    if not r:
        return Tier.OPEN
    if r in ("enterprise", "ent"):
        return Tier.ENTERPRISE
    if r in ("partner", "partner_custom", "whitelabel", "white_label"):
        return Tier.PARTNER
    if r in ("pro_plus", "pro+", "proplus"):
        return Tier.PRO_PLUS
    if r in ("pro", "professional", "consultant", "trial"):
        return Tier.PRO
    if r in ("std", "standard", "boar_std", "boar-std"):
        return Tier.STD
    if r in ("community", "oss", "open_core"):
        return Tier.COMMUNITY
    return Tier.COMMUNITY


def get_runtime_tier_for_features(cfg: dict[str, Any]) -> Tier:
    """
    Resolve tier for ``is_feature_available``.

    - **enforced:** JWT ``dbtier`` (state VALID/GRACE) is the only source;
      everything else fails closed to Community with a CRITICAL audit record.
    - **open:** lab YAML ``licensing.effective_tier``; default OPEN.
    """
    lc = cfg.get("licensing") if isinstance(cfg.get("licensing"), dict) else {}
    yaml_tier = str(lc.get("effective_tier") or "").strip().lower()

    guard = None
    try:
        from core.licensing.guard import get_license_guard

        guard = get_license_guard(cfg)
    except Exception:  # noqa: BLE001
        # License guard may be unavailable during early bootstrap. If the
        # YAML asks for enforcement, fail closed rather than open (#719).
        yaml_mode = str(lc.get("mode") or "open").strip().lower()
        if yaml_mode == "enforced":
            audit_enforcement_event(
                "tier_fail_closed",
                mode="enforced",
                state="GUARD_UNAVAILABLE",
                allowed=False,
                tier=Tier.COMMUNITY.value,
                detail="license_guard_unavailable_during_bootstrap",
            )
            return Tier.COMMUNITY
        return map_dbtier_string_to_tier(yaml_tier) if yaml_tier else Tier.OPEN

    if guard.mode == "enforced":
        c = guard.context
        if c.state in ("VALID", "GRACE"):
            dbtier_claim = str(getattr(c, "dbtier", "") or "").strip().lower()
            if dbtier_claim:
                return map_dbtier_string_to_tier(dbtier_claim)
            # Valid license without a dbtier claim: fail closed to the base
            # sellable tier — never OPEN in enforced mode (#719).
            audit_enforcement_event(
                "tier_fail_closed",
                mode="enforced",
                state=c.state,
                allowed=False,
                tier=Tier.COMMUNITY.value,
                detail="valid_license_missing_dbtier_claim",
                level=logging.WARNING,
            )
            return Tier.COMMUNITY
        if c.state == "TAMPERED":
            logger.critical(
                "LicenseGuard state=TAMPERED in enforced mode — capping effective tier to Community"
            )
        audit_enforcement_event(
            "tier_fail_closed",
            mode="enforced",
            state=c.state,
            allowed=False,
            tier=Tier.COMMUNITY.value,
            detail=c.detail or c.state.lower(),
        )
        if yaml_tier:
            audit_enforcement_event(
                "yaml_tier_ignored_enforced",
                mode="enforced",
                state=c.state,
                allowed=False,
                tier=yaml_tier,
                detail="licensing.effective_tier has no effect in enforced mode",
                level=logging.WARNING,
            )
        return Tier.COMMUNITY

    # open mode (lab / default): YAML simulation allowed; flag tampering.
    if guard.context.state == "TAMPERED":
        logger.critical(
            "LicenseGuard state=TAMPERED in open mode — unauthorized build detected"
        )
    if yaml_tier:
        return map_dbtier_string_to_tier(yaml_tier)
    return Tier.OPEN
