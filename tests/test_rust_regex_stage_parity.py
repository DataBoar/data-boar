"""Rust regex stage parity smoke (#1414) — Python vs Rust on built-in patterns."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

import jwt
import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from core.detector import SensitivityDetector
from core.licensing.tier_features import FEATURE_TIER_MAP, Tier
from core.rust_regex_stage import RUST_REGEX_STAGE_MIN_TEXT_CHARS
from core.licensing.guard import reset_license_guard_for_tests
from tests import hybrid_license_fixture as hlf
from tests.license_verify_pin import pin_embedded_ed25519_pem

pytestmark = pytest.mark.usefixtures(
    "hermetic_license_env"
)  # #2226: no dev license leaks in

_ENT_CFG = {"licensing": {"mode": "open", "effective_tier": "enterprise"}}


def _enforced_cfg(tmp_path: Path, dbtier: str) -> dict:
    """Create licensing config with enforced mode and signed JWT for given dbtier."""
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

    token = hlf.seal_enforced_test_token(
        priv,
        jwt.encode(
            {
                "sub": "lic-rust-stage-test",
                "iat": int(now.timestamp()),
                "exp": int((now + timedelta(days=1)).timestamp()),
                "dbtier": dbtier,
            },
            priv,
            algorithm="EdDSA",
        ),
        mldsa_private=hlf.test_mldsa_private(),
        pin=True,
    )
    lic = tmp_path / "t.lic"
    lic.write_text(token, encoding="utf-8")
    # Pin embedded Ed25519 anchor for test verification
    pin_embedded_ed25519_pem(pub_pem)
    return {"licensing": {"mode": "enforced", "license_path": str(lic)}}


def test_feature_tier_map_registers_rust_regex_stage() -> None:
    assert FEATURE_TIER_MAP["rust_regex_stage"] == Tier.PRO_PLUS


def test_rust_regex_stage_status_shape() -> None:
    det = SensitivityDetector(licensing_config=_ENT_CFG)
    status = det.rust_regex_stage_status.to_prefilter_dict()
    assert status["name"] == "rust_regex_stage"
    assert "accelerated_count" in status
    assert "translated_count" in status
    assert "python_fallback_count" in status
    assert isinstance(status.get("python_fallback_reasons"), dict)


def test_rust_stage_tier_gate_blocks_open() -> None:
    """Rust regex stage is blocked for OPEN tier (dev/lab default)."""
    det = SensitivityDetector()  # default config => Tier.OPEN
    status = det.rust_regex_stage_status.to_prefilter_dict()
    assert status["active"] is False
    assert status["tier"] == "open"
    assert status["reason"] == "tier_below_pro_plus"


def test_rust_stage_tier_gate_blocks_community() -> None:
    """Rust regex stage is blocked for Community tier."""
    det = SensitivityDetector(
        licensing_config={"licensing": {"mode": "open", "effective_tier": "community"}}
    )
    status = det.rust_regex_stage_status.to_prefilter_dict()
    assert status["active"] is False
    assert status["tier"] == "community"
    assert status["reason"] == "tier_below_pro_plus"


def test_rust_stage_tier_gate_blocks_std() -> None:
    """Rust regex stage is blocked for Std tier."""
    det = SensitivityDetector(
        licensing_config={"licensing": {"mode": "open", "effective_tier": "std"}}
    )
    status = det.rust_regex_stage_status.to_prefilter_dict()
    assert status["active"] is False
    assert status["tier"] == "std"
    assert status["reason"] == "tier_below_pro_plus"


def test_rust_stage_tier_gate_blocks_pro() -> None:
    """Rust regex stage is blocked for Pro tier (requires Pro+)."""
    det = SensitivityDetector(
        licensing_config={"licensing": {"mode": "open", "effective_tier": "pro"}}
    )
    status = det.rust_regex_stage_status.to_prefilter_dict()
    assert status["active"] is False
    assert status["tier"] == "pro"
    assert status["reason"] == "tier_below_pro_plus"


def test_rust_stage_tier_gate_permits_pro_plus() -> None:
    """Rust regex stage is permitted for Pro+ tier (rust may be missing)."""
    det = SensitivityDetector(
        licensing_config={"licensing": {"mode": "open", "effective_tier": "pro_plus"}}
    )
    status = det.rust_regex_stage_status.to_prefilter_dict()
    assert status["tier"] == "pro_plus"
    # active is False only because boar_fast_filter is not installed in test env
    # but the tier gate should allow the check to proceed
    assert status["reason"] in ("rust_extension_missing", None)


def test_rust_stage_tier_gate_permits_enterprise() -> None:
    """Rust regex stage is permitted for Enterprise tier."""
    det = SensitivityDetector(licensing_config=_ENT_CFG)
    status = det.rust_regex_stage_status.to_prefilter_dict()
    assert status["tier"] == "enterprise"
    # active is False only because boar_fast_filter is not installed in test env
    # but the tier gate should allow the check to proceed
    assert status["reason"] in ("rust_extension_missing", None)


def test_rust_stage_tier_gate_permits_partner() -> None:
    """Rust regex stage is permitted for Partner tier."""
    det = SensitivityDetector(
        licensing_config={"licensing": {"mode": "open", "effective_tier": "partner"}}
    )
    status = det.rust_regex_stage_status.to_prefilter_dict()
    assert status["tier"] == "partner"
    # active is False only because boar_fast_filter is not installed in test env
    # but the tier gate should allow the check to proceed
    assert status["reason"] in ("rust_extension_missing", None)


# --- enforced mode with signed JWT (end-to-end tier gating) ---------------


def test_rust_stage_enforced_no_token_blocks(tmp_path: Path) -> None:
    """Enforced mode without license blocks Rust stage (fail-closed)."""
    reset_license_guard_for_tests()
    det = SensitivityDetector(licensing_config={"licensing": {"mode": "enforced"}})
    status = det.rust_regex_stage_status.to_prefilter_dict()
    assert status["active"] is False
    assert status["tier"] == "community"
    assert status["reason"] == "tier_below_pro_plus"


def test_rust_stage_enforced_community_blocks(tmp_path: Path) -> None:
    """Enforced mode with Community dbtier blocks Rust stage."""
    reset_license_guard_for_tests()
    cfg = _enforced_cfg(tmp_path, "community")
    det = SensitivityDetector(licensing_config=cfg)
    status = det.rust_regex_stage_status.to_prefilter_dict()
    assert status["active"] is False
    assert status["tier"] == "community"
    assert status["reason"] == "tier_below_pro_plus"


def test_rust_stage_enforced_pro_blocks(tmp_path: Path) -> None:
    """Enforced mode with Pro dbtier blocks Rust stage (requires Pro+)."""
    reset_license_guard_for_tests()
    cfg = _enforced_cfg(tmp_path, "pro")
    det = SensitivityDetector(licensing_config=cfg)
    status = det.rust_regex_stage_status.to_prefilter_dict()
    assert status["active"] is False
    assert status["tier"] == "pro"
    assert status["reason"] == "tier_below_pro_plus"


def test_rust_stage_enforced_pro_plus_allows_gate(tmp_path: Path) -> None:
    """Enforced mode with Pro+ dbtier allows Rust stage gate to pass."""
    reset_license_guard_for_tests()
    cfg = _enforced_cfg(tmp_path, "pro_plus")
    det = SensitivityDetector(licensing_config=cfg)
    status = det.rust_regex_stage_status.to_prefilter_dict()
    assert status["tier"] == "pro_plus"
    # Gate passes; active depends on rust extension
    assert status["reason"] in ("rust_extension_missing", None)


def test_rust_stage_enforced_enterprise_allows_gate(tmp_path: Path) -> None:
    """Enforced mode with Enterprise dbtier allows Rust stage gate to pass."""
    reset_license_guard_for_tests()
    cfg = _enforced_cfg(tmp_path, "enterprise")
    det = SensitivityDetector(licensing_config=cfg)
    status = det.rust_regex_stage_status.to_prefilter_dict()
    assert status["tier"] == "enterprise"
    assert status["reason"] in ("rust_extension_missing", None)


def test_rust_stage_enforced_partner_allows_gate(tmp_path: Path) -> None:
    """Enforced mode with Partner dbtier allows Rust stage gate to pass."""
    reset_license_guard_for_tests()
    cfg = _enforced_cfg(tmp_path, "partner")
    det = SensitivityDetector(licensing_config=cfg)
    status = det.rust_regex_stage_status.to_prefilter_dict()
    assert status["tier"] == "partner"
    assert status["reason"] in ("rust_extension_missing", None)


def test_rust_stage_short_text_matches_python_only_path() -> None:
    """Below the activation length, Rust is skipped and Python handles regex."""
    pytest.importorskip(
        "boar_fast_filter",
        reason="Run maturin develop for boar_fast_filter",
    )
    col = "c"
    probe = "390.533.447-05"
    pad_len = RUST_REGEX_STAGE_MIN_TEXT_CHARS - len(col) - len(probe) - 3
    assert pad_len > 0
    sample = ("x" * pad_len) + " " + probe
    combined = f"{col} {sample}"
    assert len(combined) < RUST_REGEX_STAGE_MIN_TEXT_CHARS
    det_py = SensitivityDetector(
        licensing_config={"licensing": {"effective_tier": "community"}}
    )
    det_rust = SensitivityDetector(licensing_config=_ENT_CFG)
    assert det_rust.rust_regex_stage_status.active
    assert det_py.analyze(col, sample) == det_rust.analyze(col, sample)


def test_rust_stage_superset_on_builtin_probes() -> None:
    pytest.importorskip(
        "boar_fast_filter",
        reason="Run maturin develop for boar_fast_filter",
    )
    det_py = SensitivityDetector(
        licensing_config={"licensing": {"effective_tier": "community"}}
    )
    det_rust = SensitivityDetector(licensing_config=_ENT_CFG)
    assert det_rust.rust_regex_stage_status.active

    probes = [
        ("col", "390.533.447-05"),
        ("email", "a@example.test"),
        ("noise", "lorem ipsum"),
    ]
    for col, sample in probes:
        py = det_py.analyze(col, sample)
        ru = det_rust.analyze(col, sample)
        if py[0] == "LOW":
            assert ru[0] == "LOW"
        elif py[0] in ("MEDIUM", "HIGH"):
            assert ru[0] in ("MEDIUM", "HIGH")
            if py[1]:
                for part in str(py[1]).split("+"):
                    name = part.strip().split(" ", 1)[0]
                    if name and name in det_py.patterns:
                        assert name in str(ru[1] or "")


def test_rust_match_fail_soft_retries_python_for_rust_routed_patterns(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    pytest.importorskip(
        "boar_fast_filter",
        reason="Run maturin develop for boar_fast_filter",
    )
    det_py = SensitivityDetector(
        licensing_config={"licensing": {"effective_tier": "community"}}
    )
    det_rust = SensitivityDetector(licensing_config=_ENT_CFG)
    stage = det_rust._rust_stage
    assert stage is not None
    assert stage.rust_pattern_names

    def _fail_match(_text: str) -> tuple[set[str], bool]:
        return set(), False

    monkeypatch.setattr(stage, "match_names", _fail_match)

    probes = [
        ("col", "390.533.447-05"),
        ("email", "a@example.test"),
    ]
    for col, sample in probes:
        py = det_py.analyze(col, sample)
        restored = det_rust.analyze(col, sample)
        assert py[0] == restored[0]
        if py[1]:
            for part in str(py[1]).split("+"):
                name = part.strip().split(" ", 1)[0]
                if name and name in det_py.patterns:
                    assert name in str(restored[1] or "")
