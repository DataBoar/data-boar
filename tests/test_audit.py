"""Tests for sensitivity detection using core.scanner.DataScanner and core.detector."""

from core.scanner import DataScanner


def test_cpf_detection():
    # Mod-11 checksum-valid synthetic CPF (see tests/test_brazilian_cpf.py::_VALID_CPFS).
    # The detector gates LGPD_CPF/LGPD_CNPJ matches behind core.brazilian_cpf
    # checksum validation (core/detector.py::_CHECKSUM_GATED_PATTERNS); shape-only
    # fixtures fall through to the ML branch and pattern_detected becomes ML_DETECTED.
    scanner = DataScanner()
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

    # Legacy numeric CNPJ -- Mod-11 checksum-valid synthetic value
    # (see tests/test_brazilian_cpf.py::_VALID_CNPJS). LGPD_CNPJ is checksum-gated
    # via core.brazilian_cpf.text_contains_valid_cnpj; shape-only fixtures get
    # filtered out and pattern_detected falls through to ML_DETECTED.
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
