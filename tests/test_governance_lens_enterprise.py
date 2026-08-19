"""Governance Lens Phase E — Enterprise BACEN / FEBRABAN / PCI-DSS modules."""

from __future__ import annotations

import logging
from pathlib import Path

import yaml

from report.governance_lens import (
    ENTERPRISE_TIER_WARNING,
    GovernanceLensGenerator,
)

_PRO_MAP = "tests/fixtures/governance_framework_map_test.yaml"
_ENT_MAP = "tests/fixtures/governance_framework_map_enterprise_test.yaml"
_REPO_ROOT = Path(__file__).resolve().parents[1]


def _gov_config(*, tier: str, enterprise_map: str | None = _ENT_MAP) -> dict:
    gov: dict = {
        "enabled": True,
        "tier": tier,
        "map_file": _PRO_MAP,
    }
    if enterprise_map is not None:
        gov["enterprise_map_file"] = enterprise_map
    return {
        "licensing": {"mode": "open", "effective_tier": tier},
        "governance": gov,
    }


def _generator(cfg: dict) -> GovernanceLensGenerator:
    return GovernanceLensGenerator(
        cfg,
        config_path=_REPO_ROOT / "deploy" / "config.example.yaml",
    )


def test_bacen_4893_maps_pii_in_nonprod():
    gen = _generator(_gov_config(tier="enterprise"))
    rows = [
        {
            "target_name": "postgres-homolog-dev",
            "pattern_detected": "LGPD_CPF",
            "sensitivity_level": "HIGH",
        }
    ]
    result = gen.generate_from_rows(rows, [], [])
    assert any(g.framework_id == "BACEN-4893-ART4" for g in result.control_gaps)
    bacen = next(g for g in result.control_gaps if g.framework_id == "BACEN-4893-ART4")
    assert bacen.finding_count == 1
    assert "CPF" in bacen.control_gap_title


def test_pcidss_maps_luhn_valid_card():
    gen = _generator(_gov_config(tier="enterprise"))
    rows = [
        {
            "target_name": "prod-payments",
            "pattern_detected": "PCI_CARD",
            "sensitivity_level": "HIGH",
        }
    ]
    result = gen.generate_from_rows(rows, [], [])
    assert any(g.framework_id == "PCI-DSS-4.0-REQ3.4" for g in result.control_gaps)
    pci = next(g for g in result.control_gaps if g.framework_id == "PCI-DSS-4.0-REQ3.4")
    assert pci.finding_count == 1
    assert "PAN" in pci.control_gap_title or "3.4" in pci.framework_name


def test_pro_tier_does_not_load_enterprise_map():
    gen = _generator(_gov_config(tier="pro"))
    rows = [
        {
            "target_name": "postgres-homolog-dev",
            "pattern_detected": "LGPD_CPF",
            "sensitivity_level": "HIGH",
        }
    ]
    result = gen.generate_from_rows(rows, [], [])
    assert not any(g.framework_id.startswith("BACEN-") for g in result.control_gaps)
    assert not any(g.framework_id.startswith("PCI-DSS-") for g in result.control_gaps)
    assert not any(g.framework_id.startswith("FEBRABAN-") for g in result.control_gaps)
    assert any(g.framework_id == "COBIT-DSS05.04" for g in result.control_gaps)


def test_enterprise_warning_when_wrong_tier(caplog):
    cfg = _gov_config(tier="pro")
    with caplog.at_level(logging.WARNING, logger="report.governance_lens"):
        gen = _generator(cfg)
        gen.generate_from_rows(
            [
                {
                    "target_name": "postgres-homolog-dev",
                    "pattern_detected": "LGPD_CPF",
                    "sensitivity_level": "HIGH",
                }
            ],
            [],
            [],
        )
    assert ENTERPRISE_TIER_WARNING in caplog.text


def test_enterprise_example_map_has_at_least_15_entries():
    path = _REPO_ROOT / "config" / "governance_framework_map_enterprise.example.yaml"
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert len(raw["entries"]) >= 15
    ids = {fw["id"] for entry in raw["entries"] for fw in entry["frameworks"]}
    assert any(i.startswith("BACEN-4893-") for i in ids)
    assert any(i.startswith("PCI-DSS-4.0-") for i in ids)
    assert any(i.startswith("FEBRABAN-") for i in ids)
