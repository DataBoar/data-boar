"""
Synthetic fixture tests for #1318 (PCI-DSS + brazil_saude column patterns) and
#1327 (LGPD address geoloc, FELCA minor columns, learned-pattern anti-generic).

All column names and sample values are fictional — no real client data (#1288).
"""

from pathlib import Path

import pytest

from core.learned_patterns import collect_learned_entries

REPO_ROOT = Path(__file__).resolve().parent.parent
SAMPLES = REPO_ROOT / "docs" / "compliance-samples"

PCI_SAMPLE = SAMPLES / "compliance-sample-pci_dss.yaml"
SAUDE_SAMPLE = SAMPLES / "compliance-sample-brazil_saude.yaml"
LGPD_SAMPLE = SAMPLES / "compliance-sample-lgpd.yaml"
FELCA_SAMPLE = SAMPLES / "compliance-sample-brazil_felca.yaml"


@pytest.fixture
def pci_scanner():
    from core.scanner import DataScanner

    path = str(PCI_SAMPLE.resolve())
    return DataScanner(regex_overrides_path=path, ml_patterns_path=path)


@pytest.fixture
def saude_scanner():
    from core.scanner import DataScanner

    path = str(SAUDE_SAMPLE.resolve())
    return DataScanner(regex_overrides_path=path, ml_patterns_path=path)


@pytest.fixture
def lgpd_scanner():
    from core.scanner import DataScanner

    path = str(LGPD_SAMPLE.resolve())
    return DataScanner(regex_overrides_path=path, ml_patterns_path=path)


@pytest.fixture
def felca_scanner():
    from core.scanner import DataScanner

    path = str(FELCA_SAMPLE.resolve())
    return DataScanner(regex_overrides_path=path, ml_patterns_path=path)


def test_pci_tokenized_credit_card_table_columns_detect_scope_reduction(pci_scanner):
    """Tokenized gateway metadata — scope-reduction signal, not raw PAN."""
    for column in (
        "last_four_digits",
        "gateway_token",
        "payment_token_id",
        "card_token_ref",
    ):
        result = pci_scanner.scan_column(column, "tok_synthetic_abc123")
        assert result["sensitivity_level"] == "HIGH"
        assert "PCI_TOKENIZED_METADATA" in result["pattern_detected"]
        assert "scope reduction" in result["norm_tag"]


def test_pci_raw_pan_column_detected_high(pci_scanner):
    result = pci_scanner.scan_column("card_number", "4111-1111-1111-1111")
    assert result["sensitivity_level"] == "HIGH"
    assert "PCI_CARD_COLUMN" in result["pattern_detected"]


def test_pci_cvv_column_detected(pci_scanner):
    result = pci_scanner.scan_column("cvv_code", "")
    assert "PCI_CVV" in result["pattern_detected"]


def test_brazil_saude_cid_column_detected(saude_scanner):
    result = saude_scanner.scan_column("codigo_cid", "J06.9")
    assert result["sensitivity_level"] == "HIGH"
    assert "PHI_CID10_COL" in result["pattern_detected"]
    assert "Art. 11" in result["norm_tag"]


def test_brazil_saude_health_plan_column_detected(saude_scanner):
    result = saude_scanner.scan_column("plano_saude_id", "SYNTH-PLAN-001")
    assert result["sensitivity_level"] == "HIGH"
    assert "PHI_HEALTH_PLAN" in result["pattern_detected"]


@pytest.mark.parametrize(
    "column_name,expected_pattern",
    [
        ("user_latitude", "LGPD_GEOLOCATION"),
        ("billing_zip_code", "LGPD_ADDRESS_COMPONENT"),
        ("customer_street_number", "LGPD_ADDRESS_COMPONENT"),
        ("profile_cep", "LGPD_ADDRESS_COMPONENT"),
    ],
)
def test_lgpd_geoloc_and_address_columns_detected(
    lgpd_scanner, column_name: str, expected_pattern: str
):
    result = lgpd_scanner.scan_column(column_name, "")
    assert result["sensitivity_level"] == "HIGH"
    assert expected_pattern in result["pattern_detected"]


@pytest.mark.parametrize(
    "column_name",
    ["profile_is_minor", "user_data_nascimento", "student_matricula_escolar"],
)
def test_felca_minor_prefixed_columns_detected(felca_scanner, column_name: str):
    result = felca_scanner.scan_column(column_name, "")
    assert result["sensitivity_level"] == "HIGH"
    assert "FELCA_MINOR_COLUMN" in result["pattern_detected"]


def _high_finding(column_name: str, pattern: str = "ML_DETECTED") -> dict:
    return {
        "column_name": column_name,
        "sensitivity_level": "HIGH",
        "pattern_detected": pattern,
        "norm_tag": "LGPD Art. 5",
        "ml_confidence": 85,
    }


def test_learned_patterns_excludes_audit_migration_generic_columns():
    """#1327: audit/migration metadata must not become learned ML terms."""
    db = [
        _high_finding("created_at"),
        _high_finding("updated_by"),
        _high_finding("migration_name"),
        _high_finding("schema_migrate_log"),
        _high_finding("flyway_audit_log"),
    ]
    entries = collect_learned_entries(
        db, [], min_sensitivity="HIGH", exclude_generic=True
    )
    assert entries == []


def test_learned_patterns_still_collects_geoloc_and_minor_columns():
    """#1327: real sensitivity signals are not suppressed by anti-generic."""
    db = [
        _high_finding("customer_latitude", "LGPD_GEOLOCATION"),
        _high_finding("profile_is_minor", "FELCA_MINOR_COLUMN"),
    ]
    entries = collect_learned_entries(
        db, [], min_sensitivity="HIGH", exclude_generic=True
    )
    texts = {e["text"] for e in entries}
    assert "customer_latitude" in texts
    assert "profile_is_minor" in texts
