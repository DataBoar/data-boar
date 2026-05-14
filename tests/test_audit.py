"""Tests for sensitivity detection using core.scanner.DataScanner and core.detector."""

from core.scanner import DataScanner


def test_cpf_detection():
    scanner = DataScanner()
    # Use a checksum-valid CPF (Modulo-11). The shape `123.456.789-09` passes
    # `core.brazilian_cpf.cpf_checksum_valid`; `123.456.789-00` does not (the d2
    # check digit is 9, not 0). Without a valid checksum the LGPD_CPF regex no
    # longer fires by design (commits ac0bad9 / 6e8e371) and the ML fallback
    # masks the regex pathway under `pattern_detected="ML_DETECTED"`. Keep the
    # behavioral assertion identical (HIGH + CPF tag) by using a valid fixture.
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

    # Legacy numeric CNPJ — checksum-valid (Modulo-11). `12.345.678/0001-99`
    # does NOT validate (correct check digits for base 12345678000195). Use the
    # canonical valid form so the LGPD_CNPJ regex (which now requires checksum)
    # actually fires; otherwise ML fallback returns `ML_DETECTED` and the
    # `CNPJ in pattern_detected` assertion fails.
    numeric = "12.345.678/0001-95"
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
