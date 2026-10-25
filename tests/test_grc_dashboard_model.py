"""Tests for ``app.grc_dashboard_model`` (no Streamlit dependency)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.grc_dashboard_model import (
    compliance_mapping_hints,
    findings_chart_rows,
    load_grc_json,
    peak_asset_risk_score,
    validate_grc_v1,
)

_REPO = Path(__file__).resolve().parents[1]
_EXAMPLE = _REPO / "schemas" / "grc_executive_report.v1.example.json"


def test_load_example_v1() -> None:
    data = load_grc_json(_EXAMPLE)
    assert data["schema_version"] == "data_boar_grc_executive_report_v1"
    assert peak_asset_risk_score(data) == pytest.approx(100.0)
    rows = findings_chart_rows(data)
    assert len(rows) == 2
    assert rows[0]["remediation_priority"] == "CRITICAL"


def test_validate_rejects_wrong_schema() -> None:
    bad = json.loads(_EXAMPLE.read_text(encoding="utf-8"))
    bad["schema_version"] = "wrong"
    with pytest.raises(ValueError, match="Unsupported schema_version"):
        validate_grc_v1(bad)


def test_compliance_mapping_hints_nonempty() -> None:
    data = load_grc_json(_EXAMPLE)
    h = compliance_mapping_hints(data)
    assert "LGPD" in h
