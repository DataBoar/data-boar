"""
Resolve effective product tier for feature gating (YAML ``licensing.effective_tier``, JWT ``dbtier``).

Shared by API routes, RBAC, and maturity POC so tier logic stays in one place.
"""

from __future__ import annotations

import os
from typing import Any

from core.licensing.tier_features import Tier


def is_dev_tier_override_env() -> bool:
    """True when CI/dev may honor DATA_BOAR_TIER_OVERRIDE (never production builds)."""
    env = os.environ.get("DATA_BOAR_ENV", "").strip().lower()
    if env in ("development", "dev", "ci"):
        return True
    debug = os.environ.get("DEBUG", "").strip().lower()
    return debug in ("1", "true", "yes")


def tier_override_from_env() -> Tier | None:
    """Optional lab/CI tier simulation via DATA_BOAR_TIER_OVERRIDE."""
    raw = os.environ.get("DATA_BOAR_TIER_OVERRIDE", "").strip().lower()
    if not raw or not is_dev_tier_override_env():
        return None
    return map_dbtier_string_to_tier(raw)


def map_dbtier_string_to_tier(raw: str) -> Tier:
    """Map JWT ``dbtier`` / lab ``effective_tier`` strings to :class:`Tier`."""
    r = raw.strip().lower()
    if not r:
        return Tier.OPEN
    if r in ("enterprise", "ent"):
        return Tier.ENTERPRISE
    if r in ("pro", "professional", "consultant", "partner", "trial"):
        return Tier.PRO
    if r in ("community", "standard", "oss", "open_core"):
        return Tier.COMMUNITY
    return Tier.COMMUNITY


def get_runtime_tier_for_features(cfg: dict[str, Any]) -> Tier:
    """
    Resolve tier for ``is_feature_available``: JWT ``dbtier`` when enforced and VALID/GRACE wins over
    ``licensing.effective_tier``; otherwise lab YAML; default OPEN (all features on).
    """
    env_override = tier_override_from_env()
    if env_override is not None:
        return env_override

    dbtier_claim = ""
    try:
        from core.licensing.guard import get_license_guard

        g = get_license_guard(cfg)
        c = g.context
        if c.state in ("VALID", "GRACE"):
            dbtier_claim = str(getattr(c, "dbtier", "") or "").strip().lower()
    except Exception:
        pass
    lc = cfg.get("licensing") if isinstance(cfg.get("licensing"), dict) else {}
    yaml_tier = str(lc.get("effective_tier") or "").strip().lower()
    if dbtier_claim:
        return map_dbtier_string_to_tier(dbtier_claim)
    if yaml_tier:
        return map_dbtier_string_to_tier(yaml_tier)
    return Tier.OPEN
