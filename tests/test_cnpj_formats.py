from core.scanner import DataScanner


def test_legacy_numeric_cnpj_matches_lgpd_cnpj():
    scanner = DataScanner(detection_config={"cnpj_alphanumeric": True})
    # 11.222.333/0001-81 is a valid CNPJ (passes Mod-11 checksum gate).
    content = "Empresa ABC com CNPJ 11.222.333/0001-81 em operação."
    result = scanner.scan_column("cnpj_legacy", content)
    assert result is not None
    assert "LGPD_CNPJ" in result.get("pattern_detected", "")


def test_alphanumeric_cnpj_matches_lgpd_cnpj_alnum():
    scanner = DataScanner(detection_config={"cnpj_alphanumeric": True})
    # First 12 positions alphanumeric, last two digits remain numeric check digits.
    content = "Empresa XYZ com CNPJ AB.CDE.FGH/1234-56 registrado."
    result = scanner.scan_column("cnpj_alnum", content)
    assert result is not None
    assert "LGPD_CNPJ_ALNUM" in result.get("pattern_detected", "")


def test_mixed_cnpj_formats_can_surface_both_patterns():
    scanner = DataScanner(detection_config={"cnpj_alphanumeric": True})
    legacy = "CNPJ 12.345.678/0001-90"
    alnum = "CNPJ AB.CDE.FGH/1234-56"

    res_legacy = scanner.scan_column("cnpj_mixed_legacy", legacy)
    res_alnum = scanner.scan_column("cnpj_mixed_alnum", alnum)

    patterns = {
        res_legacy.get("pattern_detected", ""),
        res_alnum.get("pattern_detected", ""),
    }
    assert any("LGPD_CNPJ" in p for p in patterns)
    assert any("LGPD_CNPJ_ALNUM" in p for p in patterns)


# ---------------------------------------------------------------------------
# Precision / anti-FP tests (lookahead guard — Phase 5.1 groundwork)
# ---------------------------------------------------------------------------


def test_pure_numeric_cnpj_does_not_double_fire_as_alnum():
    """A valid numeric CNPJ must match LGPD_CNPJ but NOT LGPD_CNPJ_ALNUM.

    Without the lookahead guard in the ALNUM pattern, numeric CNPJs would fire
    twice when cnpj_alphanumeric is enabled, generating redundant findings and
    polluting the report.
    """
    scanner = DataScanner(detection_config={"cnpj_alphanumeric": True})
    content = "CNPJ 11.222.333/0001-81"  # pure numeric
    result = scanner.scan_column("cnpj_numeric_only", content)
    detected = result.get("pattern_detected", "") if result else ""
    # LGPD_CNPJ must fire (checksum-gated).
    assert "LGPD_CNPJ" in detected
    # LGPD_CNPJ_ALNUM must NOT fire (pure numeric — the lookahead requires a letter).
    assert "LGPD_CNPJ_ALNUM" not in detected


def test_alnum_pattern_disabled_by_default():
    """LGPD_CNPJ_ALNUM must not be active unless cnpj_alphanumeric=True."""
    scanner = DataScanner()  # default config
    content = "Empresa XYZ com CNPJ AB.CDE.FGH/1234-56 registrado."
    result = scanner.scan_column("cnpj_alnum_default_off", content)
    detected = result.get("pattern_detected", "") if result else ""
    assert "LGPD_CNPJ_ALNUM" not in detected


def test_generic_alphanumeric_id_does_not_match_alnum_cnpj():
    """A serial number / product code with no letter in positions 1-12 must not fire.

    This guards against false positives from serial numbers, lot codes, etc.
    Note: if the value IS purely alphanumeric (e.g. a lot code that has letters),
    the pattern may still fire — context guard (Phase 5.2) would narrow further.
    This test covers the subset where there are no letters.
    """
    scanner = DataScanner(detection_config={"cnpj_alphanumeric": True})
    # A 14-char purely numeric ID that looks positionally like a CNPJ but is NOT one.
    content = "serial 12345678901234"  # no letters → not a new-format CNPJ
    result = scanner.scan_column("serial_number", content)
    detected = result.get("pattern_detected", "") if result else ""
    assert "LGPD_CNPJ_ALNUM" not in detected
