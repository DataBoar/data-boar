"""Tests for ``report.grc_reporter`` (GRC executive JSON consolidator)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from report.grc_reporter import (
    SCHEMA_VERSION,
    GRCReporter,
    apply_data_category_risk_weight,
    compliance_score_heuristic_v1,
    default_heatmap_axes_from_risk,
    heatmap_quadrant,
    remediation_priority_from_score,
    risk_level_from_findings,
)
from report.grc_risk_taxonomy import LgpdDensityRiskConfig


def test_compliance_score_heuristic_bounds() -> None:
    assert compliance_score_heuristic_v1([]) == pytest.approx(100.0)
    s = compliance_score_heuristic_v1([85.0, 60.0])
    assert 0.0 <= s <= 100.0


def test_remediation_and_risk_level() -> None:
    assert remediation_priority_from_score(85) == "CRITICAL"
    assert remediation_priority_from_score(50) == "MEDIUM"
    assert risk_level_from_findings([40, 50]) == "MEDIUM"
    assert risk_level_from_findings([95]) == "CRITICAL"


def test_grc_reporter_shape_matches_contract(tmp_path: Path) -> None:
    r = GRCReporter(
        "Lab synthetic DB; sample_limit=1000",
        client_display_name="Example Org",
        session_id="sess-1",
        report_id="DB-TESTFIXED01",
        scanner_version="9.9.9-test",
        total_records_scanned=1_500_000,
    )
    r.set_compliance_mapping(
        lgpd_articles_hint=["LGPD:Art.46"],
        mapping_confidence="test_hints",
    )
    r.add_finding(
        "db:lab:dbo.clients",
        [{"type": "CPF", "count": 10, "exposure": "Cleartext"}],
        85,
        asset_class="database_table",
        location_summary="dbo.clients.cpf",
        violation_desc="Technical density note (test).",
        norm_tags=["TAG_A"],
        regulatory_impact="Workshop hypothesis: cite articles with counsel (test).",
    )
    r.add_recommendation(
        "REC-001",
        "P0",
        "Encrypt or tokenise column cpf.",
        estimated_effort="Medium",
        regulatory_impact_note="Workshop hypothesis only.",
    )
    out = tmp_path / "grc.json"
    r.export_json(out)
    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["schema_version"] == SCHEMA_VERSION
    assert data["report_metadata"]["report_id"] == "DB-TESTFIXED01"
    assert data["report_metadata"]["session_id"] == "sess-1"
    assert data["report_metadata"]["client_display_name"] == "Example Org"
    assert data["executive_summary"]["total_records_scanned"] == 1_500_000
    assert data["executive_summary"]["pii_instances_found"] == 10
    assert data["executive_summary"]["critical_assets_at_risk"] == 1
    assert "compliance_score_method" in data["executive_summary"]
    assert len(data["detailed_findings"]) == 1
    row = data["detailed_findings"][0]
    assert row["asset_id"] == "db:lab:dbo.clients"
    assert row["data_category"] == "unknown"
    assert row["risk_score_input"] == pytest.approx(85.0)
    assert row["risk_score"] == pytest.approx(87.0)
    assert row["remediation_priority"] == "CRITICAL"
    assert row["pii_types"][0]["type"] == "CPF"
    assert (
        row["regulatory_impact"]
        == "Workshop hypothesis: cite articles with counsel (test)."
    )
    assert row["heatmap_quadrant"] == "impact_high_likelihood_high"
    assert row["impact_score"] == pytest.approx(87.0)
    _, expected_like = default_heatmap_axes_from_risk(87.0)
    assert row["likelihood_score"] == pytest.approx(expected_like)
    assert len(data["recommendations"]) == 1


def test_sensitive_data_category_raises_risk_score() -> None:
    assert apply_data_category_risk_weight(50.0, "personal") == pytest.approx(50.0)
    adjusted = apply_data_category_risk_weight(50.0, "sensitive")
    assert adjusted == pytest.approx(67.0)
    assert heatmap_quadrant(60.0, 40.0) == "impact_high_likelihood_low"


def test_default_heatmap_axes_from_risk() -> None:
    imp, like = default_heatmap_axes_from_risk(0.0)
    assert imp == pytest.approx(0.0)
    assert like == pytest.approx(35.0)


def test_partial_heatmap_override_uses_default_for_missing_axis() -> None:
    r = GRCReporter("scope", report_id="DB-PARTIAL01")
    r.add_finding(
        "db:x:dbo.t",
        [{"type": "EMAIL", "count": 1}],
        60.0,
        impact_score=90.0,
    )
    row = r.to_dict()["detailed_findings"][0]
    assert row["risk_score"] == pytest.approx(62.0)
    assert row["impact_score"] == pytest.approx(90.0)
    adjusted = 62.0
    _, expected_like = default_heatmap_axes_from_risk(adjusted)
    assert row["likelihood_score"] == pytest.approx(expected_like)


def test_client_name_alias() -> None:
    r = GRCReporter("scope-x", client_name="Alias Org")
    d = r.to_dict()
    assert d["report_metadata"]["client_display_name"] == "Alias Org"


def test_conflicting_client_labels() -> None:
    with pytest.raises(ValueError, match="client_display_name and client_name"):
        GRCReporter(
            "s",
            client_display_name="A",
            client_name="B",
        )


def test_grc_reporter_lgpd_density_risk_ignores_manual_score() -> None:
    r = GRCReporter("scope", report_id="DB-DENSITY01")
    r.add_finding(
        "db:lab:dbo.mixed",
        [
            {"type": "EMAIL", "count": 5},
            {"type": "CPF", "count": 2},
        ],
        99.0,
        asset_class="database_table",
        lgpd_density=LgpdDensityRiskConfig(cap_raw=2500.0),
    )
    row = r.to_dict()["detailed_findings"][0]
    assert row["risk_density_raw"] == pytest.approx(110.0)
    assert row["risk_density_scaled_cap"] == pytest.approx(2500.0)
    assert row["dominant_risk_taxonomy"] == "financeiros_gov"
    assert row["risk_score"] == pytest.approx(4.4)
    assert row["risk_score_input"] == pytest.approx(4.4)
    assert "risk_density_breakdown" in row
    assert len(row["risk_density_breakdown"]) == 2
