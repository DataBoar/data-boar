"""Tests for sensitivity detection using core.scanner.DataScanner and core.detector."""

from core.scanner import DataScanner


def test_cpf_detection():
    scanner = DataScanner()
    # Synthetic checksum-valid CPF from the documented test corpus
    # (tests/test_brazilian_cpf.py::_VALID_CPFS). The legacy placeholder
    # `123.456.789-00` fails Mod-11 by design and is the canonical INVALID
    # documentation fixture, so it would be dropped by _CHECKSUM_GATED_PATTERNS.
    result = scanner.scan_column("cpf", "123.456.789-09")
    assert result["sensitivity_level"] == "HIGH"
    assert "LGPD_CPF" in result.get("pattern_detected", "") or "CPF" in result.get(
        "pattern_detected", ""
    )


def test_email_detection():
    scanner = DataScanner()
    result = scanner.scan_column("email", "user@example.com")
    assert result["sensitivity_level"] == "HIGH"
    assert "EMAIL" in result.get("pattern_detected", "")


def test_cnpj_numeric_and_alnum_detection():
    # Enable alphanumeric CNPJ so both legacy numeric and new alnum formats are detected by regex.
    scanner = DataScanner(detection_config={"cnpj_alphanumeric": True})

    # Synthetic checksum-valid CNPJ from the documented test corpus
    # (tests/test_brazilian_cpf.py::_VALID_CNPJS). The previous placeholder
    # `12.345.678/0001-99` is the canonical INVALID-DV fixture and would be
    # dropped by _CHECKSUM_GATED_PATTERNS in core/detector.py.
    numeric = "11.222.333/0001-81"
    numeric_result = scanner.scan_column("cnpj", numeric)
    assert numeric_result["sensitivity_level"] == "HIGH"
    assert "CNPJ" in numeric_result.get("pattern_detected", "")

    # New alphanumeric CNPJ format: first 12 positions A–Z/0–9, last 2 digits
    alnum = "AB.CDE.F12/GH34-56"
    alnum_result = scanner.scan_column("cnpj_alnum", alnum)
    assert alnum_result["sensitivity_level"] == "HIGH"
    assert "CNPJ" in alnum_result.get("pattern_detected", "")


def test_low_sensitivity():
    scanner = DataScanner()
    result = scanner.scan_column("item_count", "42")
    assert result["sensitivity_level"] in ("LOW", "MEDIUM", "HIGH")
    # Non-personal context often yields LOW
    assert "sensitivity_level" in result
    assert "pattern_detected" in result


def test_religion_classified_as_sensitive():
    """With default ML terms (including 'religion'), columns/samples with religion are sensitive (HIGH or MEDIUM)."""
    scanner = DataScanner()
    result = scanner.scan_column("religion", "user religion catholic")
    assert result["sensitivity_level"] in ("HIGH", "MEDIUM")
    assert "pattern_detected" in result


def test_political_affiliation_classified_as_sensitive():
    """With default ML terms (including 'political affiliation'), columns/samples with that phrase are sensitive."""
    scanner = DataScanner()
    result = scanner.scan_column(
        "political_affiliation", "political affiliation registered"
    )
    assert result["sensitivity_level"] in ("HIGH", "MEDIUM")
    assert "pattern_detected" in result
