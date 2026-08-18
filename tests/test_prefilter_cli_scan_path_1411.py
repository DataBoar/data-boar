"""
# regression-anchor: #1411

CLI scan-path readiness: paid-tier gate, fail-soft, status JSON, scan_evidence.

Product (#1414): no skip-before-ML path. Until PLAN §0 retires the discarded
``ProScanner`` skip WIP, ``PRO_SCAN_PATH_ZERO_REGRESSION_LATCH`` stays ON so
activation never ships that design. Do not weaken this test to force skip-path
activation.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from core.detector import SensitivityDetector
from core.licensing.tier_features import FEATURE_TIER_MAP, Tier
from core.pro_scan_path import (
    PRO_SCAN_PATH_ZERO_REGRESSION_LATCH,
    resolve_pro_scan_path,
)
from core.scanner import DataScanner
from pro.engine import ProScanner
from report.scan_evidence import write_scan_evidence_artifacts

# #1411 — probes that historically diverge when ProScanner skips non-suspects.
_PARITY_PROBES: list[tuple[str, str]] = [
    ("noise", "lorem ipsum dolor sit"),
    ("dados", "dados pessoais do titular"),
    ("consent", "personal data subject consent"),
    ("empty", ""),
    ("cpf", "390.533.447-05"),
    ("email", "a@b.co"),
    ("cnpj", "12.345.678/0001-95"),
    ("rut_shape", "12.345.678-K"),
]

_ENT_CFG = {"licensing": {"mode": "open", "effective_tier": "enterprise"}}
_CHILE = (
    Path(__file__).resolve().parents[1]
    / "docs"
    / "compliance-samples"
    / "compliance-sample-chile_privacy.yaml"
)


def _finding_key(result: dict) -> tuple[str | None, str | None]:
    return result.get("sensitivity_level"), result.get("pattern_detected")


def test_feature_tier_map_registers_pro_prefilter_accel() -> None:
    assert FEATURE_TIER_MAP["pro_prefilter_accel"] == Tier.PRO_PLUS


def test_zero_regression_latch_default_on() -> None:
    """Latch must stay True until the operator accepts speed vs recall."""
    assert PRO_SCAN_PATH_ZERO_REGRESSION_LATCH is True


def test_paid_tier_reports_rust_regex_stage_status() -> None:
    scanner = DataScanner(licensing_config=_ENT_CFG)
    st = scanner.prefilter_status
    assert st["name"] == "rust_regex_stage"
    assert st["engine"] == "core"
    assert st["tier"] == "enterprise"
    if st["active"]:
        assert st["backend"] == "rust"
        assert st["reason"] is None
    else:
        assert st["backend"] == "python"
        assert st["reason"] in (
            "rust_extension_missing",
            "rust_compile_failed",
            "no_rust_eligible_patterns",
        )
    assert scanner._pro_scanner is None


def test_open_tier_inactive() -> None:
    _, st = resolve_pro_scan_path({})
    assert st["active"] is False
    assert st["reason"] == "tier_below_pro_plus"
    assert st["engine"] == "core"


def test_env_off_short_circuits(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DATA_BOAR_PREFILTER", "off")
    _, st = resolve_pro_scan_path(_ENT_CFG)
    assert st["active"] is False
    assert st["reason"] == "env_off"


def test_chile_rut_still_found_via_core_path() -> None:
    """With latch ON, compliance regex still runs on the core detector path."""
    assert _CHILE.is_file()
    scanner = DataScanner(
        licensing_config=_ENT_CFG,
        regex_overrides_path=str(_CHILE),
        ml_patterns_path=str(_CHILE),
    )
    assert "RUT_CL" in scanner.detector.patterns
    # Column name must not be the ML term "rut" — hit should be regex.
    result = scanner.scan_column("tax_id", "12.345.678-K")
    assert result["sensitivity_level"] == "HIGH"
    assert "RUT_CL" in (result["pattern_detected"] or "")


def test_ent_latched_matches_env_off_parity(monkeypatch: pytest.MonkeyPatch) -> None:
    """Default latched Ent path must match forced-off findings (zero regression)."""
    s_default = DataScanner(licensing_config=_ENT_CFG)
    monkeypatch.setenv("DATA_BOAR_PREFILTER", "off")
    s_off = DataScanner(licensing_config=_ENT_CFG)
    for col, sample in _PARITY_PROBES:
        assert _finding_key(s_default.scan_column(col, sample)) == _finding_key(
            s_off.scan_column(col, sample)
        ), f"parity break on {col!r}"


def test_proscanner_skip_diverges_from_full_detector_report_count() -> None:
    """
    Measured divergence if the latch were lifted (ProScanner skip active).

    Reports the count; fails if somehow zero (would mean latch can be lifted
    without operator review — update docs/probe, do not silence).
    """
    det = SensitivityDetector()

    def deep(batch: list[str]) -> list[dict]:
        out: list[dict] = []
        for text in batch:
            level, pattern, _norm, _conf = det.analyze("col", text)
            out.append(
                {
                    "sensitivity_level": level,
                    "pattern_detected": pattern,
                }
            )
        return out

    pro = ProScanner(deep_scan_fn=deep, legacy_scan_fn=deep)
    divergences = 0
    for _col, sample in _PARITY_PROBES:
        full = deep([sample])[0]
        filtered = pro.scan([sample])
        fr = (
            filtered[0]
            if filtered
            else {"sensitivity_level": "LOW", "pattern_detected": None}
        )
        if _finding_key(full) != _finding_key(fr):
            divergences += 1

    # Probe 2026-07-30: 6 divergences on this set. Keep latch ON while > 0.
    assert divergences >= 1, (
        "expected ProScanner skip vs full detector to diverge; "
        f"got {divergences} — re-check probe set before lifting the latch"
    )
    # Documented floor for operator reports; do not lower to make CI green.
    assert divergences >= 5, (
        f"measured divergences={divergences} (expected >=5 on #1411 probe set); "
        "update the operator report comment in core/pro_scan_path.py if the "
        "number changed for a real reason — do not weaken the latch"
    )


def test_fail_soft_returns_core_path(monkeypatch: pytest.MonkeyPatch) -> None:
    def _boom(_cfg):
        raise RuntimeError("simulated tier failure")

    monkeypatch.setattr(
        "core.licensing.runtime_feature_tier.get_runtime_tier_for_features",
        _boom,
    )
    pro, st = resolve_pro_scan_path(_ENT_CFG)
    assert pro is None
    assert st["active"] is False
    assert st["reason"] == "fail_soft"
    assert st["engine"] == "core"


def test_engine_stamps_runtime_prefilter(tmp_path: Path) -> None:
    from core.engine import AuditEngine

    cfg = {
        **_ENT_CFG,
        "targets": [],
        "report": {"output_dir": str(tmp_path / "out")},
        "sqlite_path": str(tmp_path / "audit.db"),
        "scan": {"max_workers": 1},
    }
    engine = AuditEngine(cfg, db_path=str(tmp_path / "audit.db"))
    runtime = cfg.get("_runtime") or {}
    pf = runtime.get("prefilter") or {}
    assert pf.get("name") == "rust_regex_stage"
    assert pf.get("active") is False or pf.get("active") is True
    assert getattr(engine.scanner, "prefilter_status", {}).get("name") == (
        "rust_regex_stage"
    )


def test_scan_manifest_includes_detection_prefilter(tmp_path: Path) -> None:
    man, _md = write_scan_evidence_artifacts(
        output_dir=str(tmp_path),
        session_id="prefilter1411session",
        meta={
            "started_at": "2026-07-30T10:00:00+00:00",
            "finished_at": "2026-07-30T10:01:00+00:00",
            "config_scope_hash": "deadbeef",
        },
        about={"name": "Data Boar", "version": "0.0.0-test"},
        config={
            **_ENT_CFG,
            "targets": [],
            "file_scan": {"sample_limit": 50},
            "_runtime": {
                "prefilter": {
                    "active": False,
                    "name": "ProScanner",
                    "backend": "python",
                    "tier": "enterprise",
                    "reason": "zero_regression_latch",
                    "engine": "core",
                }
            },
        },
        db_rows=[],
        fs_rows=[],
        fail_rows=[],
        report_rows_capped=False,
    )
    loaded = yaml.safe_load(Path(man).read_text(encoding="utf-8"))
    assert "detection_prefilter" in loaded
    assert loaded["detection_prefilter"]["reason"] == "zero_regression_latch"
    assert loaded["detection_prefilter"]["active"] is False
