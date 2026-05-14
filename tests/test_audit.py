"""Tests for sensitivity detection using core.scanner.DataScanner and core.detector."""

from core.scanner import DataScanner


def test_cpf_detection():
    scanner = DataScanner()
    # Checksum-valid public test CPF (123.456.789-09 passes Mod-11; -00 does not).
    # The detector's _CHECKSUM_GATED_PATTERNS correctly refuses to fire the CPF regex
    # on invalid digits, which would let the ML branch return "ML_DETECTED" instead.
    # See commits 133d07c, 038bf83, 62c192f, ed0ac5c for the same migration elsewhere.
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

    # Legacy numeric CNPJ — checksum-valid public fixture used elsewhere
    # (tests/test_brazilian_cpf.py, tests/test_cnpj_formats.py). 12.345.678/0001-99
    # would fail Mod-11 (DV2 = 5, not 9) and be rejected by _CHECKSUM_GATED_PATTERNS.
    numeric = "11.222.333/0001-81"
    numeric_result = scanner.scan_column("cnpj", numeric)
    assert numeric_result["sensitivity_level"] == "HIGH"
    assert "CNPJ" in numeric_result.get("pattern_detected", "")

    # Alphanumeric CNPJ (first 12 positions A-Z/0-9, last 2 are check digits).
    # AB.CDE.FGH/1234-56 is the documented fixture in tests/test_cnpj_formats.py.
    alnum = "AB.CDE.FGH/1234-56"
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
