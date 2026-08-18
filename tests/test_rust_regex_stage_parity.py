"""Rust regex stage parity smoke (#1414) — Python vs Rust on built-in patterns."""

from __future__ import annotations

import pytest

from core.detector import SensitivityDetector
from core.licensing.tier_features import FEATURE_TIER_MAP, Tier

_ENT_CFG = {"licensing": {"mode": "open", "effective_tier": "enterprise"}}


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
