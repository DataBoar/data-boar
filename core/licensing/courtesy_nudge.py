"""Courtesy wait before tier-gated UX (ADR-DRAFT-0076).

Community (and enforcement-off lab without a paid tier) may show a short courtesy
delay before upgrade prompts. Std and above skip the wait.
"""

from __future__ import annotations

from core.licensing.tier_features import Tier

DEFAULT_COURTESY_WAIT_SECONDS = 5

_NO_WAIT_TIERS = frozenset(
    {
        Tier.STD,
        Tier.PRO,
        Tier.PRO_PLUS,
        Tier.ENTERPRISE,
        Tier.PARTNER,
        Tier.OPEN,
    }
)


def courtesy_nudge_wait_seconds(tier: Tier) -> int:
    """Return seconds to wait before showing a courtesy upgrade nudge (0 = skip)."""
    if tier in _NO_WAIT_TIERS:
        return 0
    return DEFAULT_COURTESY_WAIT_SECONDS
