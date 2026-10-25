"""
Tests for ``report.nist_csf_hints`` and the optional ``nist_csf_function_hint`` field
emitted by ``report.grc_reporter.GRCReporter`` (issue #760).

Scope: NIST CSF 2.0 **only**, heuristic hints (ADR-0025) derived from a versioned,
shipped mapping table (``report/nist_csf_mapping.yaml``). The field is non-breaking and
omitted when no norm_tag maps.
"""

from __future__ import annotations

import pytest
import yaml

from report import nist_csf_hints
from report.grc_reporter import NIST_CSF_HINT_METHOD, GRCReporter


def test_mapping_version_and_disclaimer() -> None:
    assert nist_csf_hints.mapping_version() == "nist_csf_2_0_hint_v1"
    disc = nist_csf_hints.disclaimer()
    assert disc
    assert "ADR-0025" in disc


def test_shipped_mapping_yaml_is_well_formed() -> None:
    raw = nist_csf_hints._MAPPING_PATH.read_text(encoding="utf-8")
    data = yaml.safe_load(raw)
    assert isinstance(data, dict)
    assert data["mapping_version"] == "nist_csf_2_0_hint_v1"
    assert isinstance(data["rules"], list) and data["rules"]
    for rule in data["rules"]:
        assert "match" in rule and str(rule["match"]).strip()
        assert isinstance(rule["csf"], list) and rule["csf"]


@pytest.mark.parametrize(
    "norm_tags, expected",
    [
        (["LGPD Art. 5"], ["ID.AM", "PR.DS"]),
        (["GDPR Art. 4(1)"], ["ID.AM", "PR.DS"]),
        (["Personal data context"], ["ID.AM", "PR.DS"]),
        (["Health/insurance context"], ["GV", "ID.AM", "PR.DS"]),
        (["PII_AMBIGUOUS"], ["ID.AM"]),
        (["TAG_A"], []),
        ([], []),
        (None, []),
    ],
)
def test_csf_functions_for_norm_tags(
    norm_tags: list[str] | None, expected: list[str]
) -> None:
    assert nist_csf_hints.csf_functions_for_norm_tags(norm_tags) == expected


def test_csf_codes_dedup_and_canonical_order() -> None:
    # Union of personal (ID.AM, PR.DS) + sensitive (GV, ID.AM, PR.DS), sorted GV<ID<PR.
    result = nist_csf_hints.csf_functions_for_norm_tags(
        ["LGPD Art. 5", "Health/insurance context"]
    )
    assert result == ["GV", "ID.AM", "PR.DS"]


def test_reporter_emits_csf_hint_when_mapped() -> None:
    r = GRCReporter("scope", report_id="DB-CSF01")
    r.add_finding(
        "db:lab:dbo.clients",
        [{"type": "CPF", "count": 3}],
        80.0,
        norm_tags=["LGPD Art. 5"],
    )
    data = r.to_dict()
    row = data["detailed_findings"][0]
    assert row["nist_csf_function_hint"] == ["ID.AM", "PR.DS"]
    cm = data["compliance_mapping"]
    assert cm["nist_csf_mapping_version"] == "nist_csf_2_0_hint_v1"
    assert cm["nist_csf_function_hint_method"] == NIST_CSF_HINT_METHOD
    assert "ADR-0025" in cm["nist_csf_function_hint_disclaimer"]


def test_reporter_omits_csf_hint_when_unmapped() -> None:
    r = GRCReporter("scope", report_id="DB-CSF02")
    r.add_finding(
        "db:lab:dbo.misc",
        [{"type": "EMAIL", "count": 1}],
        40.0,
        norm_tags=["TAG_A"],
    )
    data = r.to_dict()
    row = data["detailed_findings"][0]
    assert "nist_csf_function_hint" not in row
    cm = data["compliance_mapping"]
    assert "nist_csf_mapping_version" not in cm
    assert "nist_csf_function_hint_disclaimer" not in cm
