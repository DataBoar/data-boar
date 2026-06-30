"""Courtesy upgrade wait gating (ADR-DRAFT-0076)."""

from __future__ import annotations

from core.licensing.courtesy_nudge import (
    DEFAULT_COURTESY_WAIT_SECONDS,
    courtesy_nudge_wait_seconds,
)
from core.licensing.tier_features import Tier


def test_community_has_courtesy_wait() -> None:
    assert courtesy_nudge_wait_seconds(Tier.COMMUNITY) == DEFAULT_COURTESY_WAIT_SECONDS


def test_std_and_above_skip_courtesy_wait() -> None:
    for tier in (
        Tier.STD,
        Tier.PRO,
        Tier.PRO_PLUS,
        Tier.ENTERPRISE,
        Tier.PARTNER,
        Tier.OPEN,
    ):
        assert courtesy_nudge_wait_seconds(tier) == 0
