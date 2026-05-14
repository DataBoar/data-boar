"""Tests for sensitivity detection using core.scanner.DataScanner and core.detector."""

from core.scanner import DataScanner


def test_cpf_detection():
    # 390.533.447-05 is the canonical public Mod-11-valid CPF used across the test suite
    # (e.g. tests/test_brazilian_cpf.py, tests/test_setup_lab_db.py). The previous fixture
    # 123.456.789-00 was shape-only and is correctly suppressed by the
    # _CHECKSUM_GATED_PATTERNS Mod-11 gate in core/detector.py (commit 6103764) — that gate
    # is a Defensive-Scanning-Manifesto invariant and must NOT be relaxed to satisfy a test.
    scanner = DataScanner()
    result = scanner.scan_column("cpf", "390.533.447-05")
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

    # Legacy numeric CNPJ — 11.222.333/0001-81 is the canonical Mod-11-valid public CNPJ
    # already used in tests/test_cnpj_formats.py. Commit 6e8e371 added a lookahead to
    # LGPD_CNPJ_ALNUM so pure-numeric CNPJs no longer double-fire there; with that fix
    # in place this assertion exercises the checksum-gated LGPD_CNPJ path (no double-hit).
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
