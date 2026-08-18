"""Governance Lens — Pro-tier GRC gap generator and Excel integration."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from core.database import LocalDBManager
from report.generator import generate_report
from report.governance_lens import GovernanceLensGenerator

_FIXTURE_MAP = "tests/fixtures/governance_framework_map_test.yaml"
_REPO_ROOT = Path(__file__).resolve().parents[1]


def _pro_gov_config(*, enabled: bool = True) -> dict:
    return {
        "licensing": {"mode": "open", "effective_tier": "pro"},
        "governance": {
            "enabled": enabled,
            "tier": "pro",
            "map_file": _FIXTURE_MAP,
        },
    }


def _generator() -> GovernanceLensGenerator:
    return GovernanceLensGenerator(
        _pro_gov_config(),
        config_path=_REPO_ROOT / "deploy" / "config.example.yaml",
    )


def test_maps_lgpd_cpf_in_nonprod_to_cobit_dss05():
    gen = _generator()
    rows = [
        {
            "target_name": "postgres-homolog-dev",
            "pattern_detected": "LGPD_CPF",
            "sensitivity_level": "HIGH",
        }
    ]
    result = gen.generate_from_rows(rows, [], [])
    assert any(g.framework_id == "COBIT-DSS05.04" for g in result.control_gaps)
    cobit = next(g for g in result.control_gaps if g.framework_id == "COBIT-DSS05.04")
    assert cobit.finding_count == 1
    assert (
        "CPF" in cobit.control_gap_title or "não produtiva" in cobit.control_gap_title
    )


def test_aggregates_duplicate_controls():
    gen = _generator()
    rows = [
        {
            "target_name": "lab-db-test",
            "pattern_detected": "LGPD_CPF",
            "sensitivity_level": "MEDIUM",
        },
        {
            "target_name": "staging-db",
            "pattern_detected": "LGPD_CPF",
            "sensitivity_level": "HIGH",
        },
    ]
    result = gen.generate_from_rows(rows, [], [])
    cobit_gaps = [g for g in result.control_gaps if g.framework_id == "COBIT-DSS05.04"]
    assert len(cobit_gaps) == 1
    assert cobit_gaps[0].finding_count == 2
    assert cobit_gaps[0].max_sensitivity == "HIGH"


def test_risk_level_alto_when_nonprod_findings():
    gen = _generator()
    rows = [
        {
            "target_name": f"homolog-db-{i}",
            "pattern_detected": "EMAIL",
            "sensitivity_level": "LOW",
        }
        for i in range(3)
    ]
    result = gen.generate_from_rows(rows, [], [])
    assert result.risk_level == "alto"


def test_empty_findings_returns_empty_gaps():
    gen = _generator()
    result = gen.generate_from_rows([], [], [])
    assert result.control_gaps == []
    assert result.framework_summary == {}
    assert result.risk_level == "baixo"


def test_excel_tab_governance_view_present(tmp_path):
    db_path = str(tmp_path / "gov_lens.db")
    out_dir = str(tmp_path / "out")
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    mgr = LocalDBManager(db_path)
    try:
        mgr.set_current_session_id("gov-s1")
        mgr.create_session_record("gov-s1")
        mgr.save_finding(
            "database",
            target_name="homolog-postgres",
            column_name="cpf",
            sensitivity_level="HIGH",
            pattern_detected="LGPD_CPF",
            norm_tag="LGPD",
            ml_confidence=90,
        )
        mgr.finish_session("gov-s1")
        path = generate_report(
            mgr,
            "gov-s1",
            output_dir=out_dir,
            config=_pro_gov_config(),
        )
        assert path is not None
        with pd.ExcelFile(path) as xl:
            assert "Governance View" in xl.sheet_names
            df = pd.read_excel(xl, sheet_name="Governance View")
        assert "COBIT-DSS05.04" in df.to_string()
        risk_rows = df[df["Seção"] == "Nível de risco"]
        assert not risk_rows.empty
    finally:
        mgr.dispose()


def test_governance_disabled_skips_excel_tab(tmp_path):
    db_path = str(tmp_path / "gov_off.db")
    out_dir = str(tmp_path / "out_off")
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    mgr = LocalDBManager(db_path)
    try:
        mgr.set_current_session_id("gov-off")
        mgr.create_session_record("gov-off")
        mgr.save_finding(
            "database",
            target_name="T1",
            column_name="cpf",
            sensitivity_level="HIGH",
            pattern_detected="LGPD_CPF",
            norm_tag="LGPD",
            ml_confidence=90,
        )
        mgr.finish_session("gov-off")
        path = generate_report(
            mgr,
            "gov-off",
            output_dir=out_dir,
            config=_pro_gov_config(enabled=False),
        )
        assert path is not None
        with pd.ExcelFile(path) as xl:
            assert "Governance View" not in xl.sheet_names
    finally:
        mgr.dispose()
