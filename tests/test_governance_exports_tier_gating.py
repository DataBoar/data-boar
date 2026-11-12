"""Tier gating for the governance exports (#837 RoPA, #838 SARIF / SIEM push).

Both are Pro+ per docs/SUBSCRIPTION_TIERS.md. They need EXPLICIT map entries:
an absent key would fall through to Community in ``is_feature_available``.
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone

import jwt
import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from core.licensing.errors import FeatureTierBlockedError
from core.licensing.feature_gate import check_feature, require_feature
from core.licensing.guard import reset_license_guard_for_tests
from core.licensing.tier_features import (
    FEATURE_TIER_MAP,
    Tier,
    features_for_tier,
    is_feature_available,
)
from tests.license_verify_pin import pin_embedded_ed25519_pem

pytestmark = pytest.mark.usefixtures(
    "hermetic_license_env"
)  # #2226: no dev license leaks in

FEATURES = ("ropa_export", "findings_siem_push")


@pytest.fixture(autouse=True)
def _clean_guard():
    reset_license_guard_for_tests()
    yield
    reset_license_guard_for_tests()
    os.environ.pop("DATA_BOAR_LICENSE_PUBLIC_KEY_PEM", None)


def _cfg(tier: str | None) -> dict:
    lc: dict = {"mode": "open"}
    if tier:
        lc["effective_tier"] = tier
    return {"licensing": lc}


@pytest.mark.parametrize("feature", FEATURES)
def test_map_entry_is_explicit_pro_plus(feature):
    assert FEATURE_TIER_MAP[feature] == Tier.PRO_PLUS


@pytest.mark.parametrize("feature", FEATURES)
@pytest.mark.parametrize("tier", [Tier.COMMUNITY, Tier.STD, Tier.PRO])
def test_blocked_below_pro_plus(feature, tier):
    assert is_feature_available(feature, tier) is False
    assert feature not in features_for_tier(tier)
    assert check_feature(feature, tier).allowed is False


@pytest.mark.parametrize("feature", FEATURES)
@pytest.mark.parametrize(
    "tier", [Tier.PRO_PLUS, Tier.ENTERPRISE, Tier.PARTNER, Tier.OPEN]
)
def test_allowed_at_pro_plus_and_above(feature, tier):
    assert is_feature_available(feature, tier) is True
    assert check_feature(feature, tier).allowed is True


@pytest.mark.parametrize("feature", FEATURES)
@pytest.mark.parametrize("tier", ["community", "std", "pro"])
def test_require_feature_raises_below_pro_plus(feature, tier):
    reset_license_guard_for_tests()
    with pytest.raises(FeatureTierBlockedError) as exc_info:
        require_feature(_cfg(tier), feature)
    msg = str(exc_info.value)
    assert feature in msg and "Pro+" in msg


@pytest.mark.parametrize("feature", FEATURES)
@pytest.mark.parametrize("tier", ["pro_plus", "enterprise", None])
def test_require_feature_passes_at_pro_plus_enterprise_and_open(feature, tier):
    reset_license_guard_for_tests()
    require_feature(_cfg(tier), feature)  # Tier.OPEN (no simulation) bypasses


def _signed_license(tmp_path, dbtier: str) -> dict:
    priv = Ed25519PrivateKey.generate()
    pub_pem = (
        priv.public_key()
        .public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        .decode("ascii")
    )
    now = datetime.now(timezone.utc)
    from tests.hybrid_license_fixture import seal_enforced_test_token

    token = seal_enforced_test_token(
        priv,
        jwt.encode(
            {
                "sub": "lic-gov-exports",
                "iat": int(now.timestamp()),
                "exp": int((now + timedelta(days=1)).timestamp()),
                "dbtier": dbtier,
            },
            priv,
            algorithm="EdDSA",
        ),
    )
    lic = tmp_path / "t.lic"
    lic.write_text(token, encoding="utf-8")
    pin_embedded_ed25519_pem(pub_pem)
    return {"licensing": {"mode": "enforced", "license_path": str(lic)}}


@pytest.mark.parametrize("feature", FEATURES)
@pytest.mark.parametrize("tier", ["community", "pro"])
def test_enforced_license_below_pro_plus_blocks(tmp_path, feature, tier):
    cfg = _signed_license(tmp_path, tier)
    with pytest.raises(FeatureTierBlockedError):
        require_feature(cfg, feature)


@pytest.mark.parametrize("feature", FEATURES)
@pytest.mark.parametrize("tier", ["pro_plus", "enterprise"])
def test_enforced_license_pro_plus_or_enterprise_allows(tmp_path, feature, tier):
    cfg = _signed_license(tmp_path, tier)
    require_feature(cfg, feature)


@pytest.mark.parametrize("feature", FEATURES)
def test_enforced_without_license_fails_closed(feature):
    with pytest.raises(FeatureTierBlockedError):
        require_feature({"licensing": {"mode": "enforced"}}, feature)
