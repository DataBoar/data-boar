"""
Structured feature-tier checks (graceful deny paths for Pro/Enterprise gates).

Use :func:`check_feature` before activating tier-gated product behaviour.
"""

from __future__ import annotations

from dataclasses import dataclass

from core.licensing.tier_features import (
    Tier,
    get_required_tier,
    is_feature_available,
)

_TIER_LABEL = {
    Tier.COMMUNITY: "Community",
    Tier.PRO: "Pro",
    Tier.ENTERPRISE: "Enterprise",
    Tier.OPEN: "Open",
}


@dataclass(frozen=True)
class FeatureCheckResult:
    """Outcome of a tier gate check — never raises for tier denial."""

    allowed: bool
    reason: str
    feature: str
    required_tier: str
    current_tier: str


def _tier_label(tier: Tier) -> str:
    return _TIER_LABEL.get(tier, tier.value)


def check_feature(feature: str, current_tier: Tier) -> FeatureCheckResult:
    """
    Return whether *feature* is allowed for *current_tier* with a human-readable reason.

    OPEN tier bypasses restrictions (lab / enforcement off). Denials do not raise.
    """
    name = (feature or "").strip()
    required = get_required_tier(name)
    allowed = is_feature_available(name, current_tier)
    if allowed:
        reason = ""
    elif current_tier == Tier.OPEN:
        reason = ""
    else:
        reason = (
            f"Feature '{name}' requires {_tier_label(required)} tier or higher; "
            f"current tier is {_tier_label(current_tier)}. "
            "Upgrade your subscription or set licensing.effective_tier in lab config."
        )
    return FeatureCheckResult(
        allowed=allowed,
        reason=reason,
        feature=name,
        required_tier=required.value,
        current_tier=current_tier.value,
    )
