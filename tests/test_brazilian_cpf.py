"""Tests for CPF and CNPJ checksum validation (algorithmic false-positive reduction)."""

from __future__ import annotations

import unittest

from core.brazilian_cpf import (
    CPF_FISCAL_REGION_MAP,
    PIIValidator,
    cnpj_checksum_valid,
    cpf_birth_state_consistent,
    cpf_checksum_valid,
    cpf_fiscal_region,
    normalize_cnpj_digits,
    normalize_cpf_digits,
    text_contains_valid_cnpj,
    text_contains_valid_cpf,
)


class TestNormalizeCpfDigits(unittest.TestCase):
    def test_strips_punctuation(self) -> None:
        self.assertEqual(normalize_cpf_digits("390.533.447-05"), "39053344705")

    def test_rejects_wrong_length(self) -> None:
        self.assertIsNone(normalize_cpf_digits("3905334470"))
        self.assertIsNone(normalize_cpf_digits(""))


class TestCpfChecksumValid(unittest.TestCase):
    def test_public_fixture_passes(self) -> None:
        # Widely used documentation-style number (passes DV only; not a real identity claim).
        self.assertTrue(cpf_checksum_valid("39053344705"))

    def test_rejects_all_same_digit(self) -> None:
        self.assertFalse(cpf_checksum_valid("11111111111"))

    def test_rejects_wrong_check_digit(self) -> None:
        self.assertFalse(cpf_checksum_valid("39053344704"))


class TestPIIValidator(unittest.TestCase):
    def test_validate_cpf_accepts_formatted(self) -> None:
        self.assertTrue(PIIValidator.validate_cpf("390.533.447-05"))

    def test_scan_content_skips_shape_without_valid_checksum(self) -> None:
        v = PIIValidator()
        # CPF-shaped 11 digits with invalid check digits (not a valid CPF).
        text = "id=12345678901 end"
        out = v.scan_content(text)
        self.assertEqual(out["risk_score"], 0)
        self.assertEqual(len(out["found"]), 0)

    def test_scan_content_keeps_valid_hits_masked(self) -> None:
        v = PIIValidator()
        text = "cpf 390.533.447-05 ok"
        out = v.scan_content(text)
        self.assertEqual(out["risk_score"], 10)
        self.assertEqual(len(out["found"]), 1)
        self.assertEqual(out["found"][0]["type"], "BRAZIL_CPF")
        self.assertEqual(out["found"][0]["masked_tail"], "05")
        self.assertEqual(out["found"][0]["confidence"], "HIGH")


# ---------------------------------------------------------------------------
# CNPJ tests (new in this session)
# ---------------------------------------------------------------------------


class TestNormalizeCnpjDigits(unittest.TestCase):
    def test_strips_punctuation(self) -> None:
        self.assertEqual(normalize_cnpj_digits("11.222.333/0001-81"), "11222333000181")

    def test_rejects_wrong_length(self) -> None:
        self.assertIsNone(normalize_cnpj_digits("1122233300018"))  # 13 digits
        self.assertIsNone(normalize_cnpj_digits(""))


class TestCnpjChecksumValid(unittest.TestCase):
    def test_public_fixture_passes(self) -> None:
        # Receita Federal sample number widely used in documentation.
        self.assertTrue(cnpj_checksum_valid("11222333000181"))

    def test_rejects_all_same_digit(self) -> None:
        self.assertFalse(cnpj_checksum_valid("11111111111111"))

    def test_rejects_wrong_first_check_digit(self) -> None:
        # Flip d13 from 8 to 9 → first DV fails.
        self.assertFalse(cnpj_checksum_valid("11222333000191"))

    def test_rejects_wrong_second_check_digit(self) -> None:
        # Flip d14 from 1 to 2 → second DV fails.
        self.assertFalse(cnpj_checksum_valid("11222333000182"))

    def test_rejects_sequential_id_shaped_cnpj(self) -> None:
        # 14-digit sequential counter that matches the shape but fails Mod-11.
        self.assertFalse(cnpj_checksum_valid("12345678901234"))


class TestPIIValidatorCnpj(unittest.TestCase):
    def test_validate_cnpj_accepts_formatted(self) -> None:
        self.assertTrue(PIIValidator.validate_cnpj("11.222.333/0001-81"))

    def test_validate_cnpj_rejects_invalid(self) -> None:
        self.assertFalse(PIIValidator.validate_cnpj("11.222.333/0001-99"))


class TestTextContainsValidCpf(unittest.TestCase):
    def test_finds_valid_cpf_in_text(self) -> None:
        self.assertTrue(text_contains_valid_cpf("cpf: 390.533.447-05 other"))

    def test_returns_false_for_invalid_shapes_only(self) -> None:
        # Shape matches but no valid checksum
        self.assertFalse(text_contains_valid_cpf("123.456.789-00"))

    def test_returns_true_if_any_valid_among_mixed(self) -> None:
        text = "bad=12345678901 good=390.533.447-05"
        self.assertTrue(text_contains_valid_cpf(text))


class TestTextContainsValidCnpj(unittest.TestCase):
    def test_finds_valid_cnpj_in_text(self) -> None:
        self.assertTrue(text_contains_valid_cnpj("cnpj: 11.222.333/0001-81 ok"))

    def test_returns_false_for_invalid_shapes_only(self) -> None:
        self.assertFalse(text_contains_valid_cnpj("12.345.678/9012-34"))

    def test_returns_true_if_any_valid_among_mixed(self) -> None:
        text = "bad=12345678901234 good=11.222.333/0001-81"
        self.assertTrue(text_contains_valid_cnpj(text))


# ---------------------------------------------------------------------------
# Expanded CPF corpus — generated with deterministic seed, validated offline
# ---------------------------------------------------------------------------

# Valid CPFs produced by a seeded generator and cross-checked against
# cpf_checksum_valid().  None of these belong to real individuals.
_VALID_CPFS = [
    "123.456.789-09",  # classic documentation fixture
    "390.533.447-05",  # original unit-test fixture
    "104.332.181-00",
    "317.024.090-07",
    "57634063460",  # no-punctuation variant
    "795.115.226-98",
    "693.674.818-02",
    "099.910.043-27",
    "707.126.167-99",
    "838.239.707-71",
    "187.357.421-51",
    "960.336.149-68",
]

# CPF-shaped strings with wrong check digits — must all be rejected.
_INVALID_CPF_SHAPES = [
    "123.456.789-00",  # wrong 2nd DV
    "123.456.789-10",
    "12345678901",  # plausible counter value
    "000.000.000-00",  # all zeros
    "111.111.111-11",  # all ones
    "999.999.999-99",  # all nines
]

# Valid CNPJs for test corpus (same generation approach).
_VALID_CNPJS = [
    "11.222.333/0001-81",  # original unit-test fixture
    "27.726.568/0001-40",
    "55.816.406/0001-39",
    "03.836.794/0001-16",
]


class TestCpfCorpus(unittest.TestCase):
    """Table-driven tests over the expanded CPF fixture corpus."""

    def test_all_valid_cpfs_accepted(self) -> None:
        for cpf in _VALID_CPFS:
            with self.subTest(cpf=cpf):
                self.assertTrue(
                    PIIValidator.validate_cpf(cpf),
                    f"Expected valid CPF to be accepted: {cpf}",
                )

    def test_all_valid_cpfs_found_in_text(self) -> None:
        for cpf in _VALID_CPFS:
            with self.subTest(cpf=cpf):
                self.assertTrue(
                    text_contains_valid_cpf(f"campo={cpf} fim"),
                    f"Expected text_contains_valid_cpf to find: {cpf}",
                )

    def test_false_positive_rate_zero_on_invalid_shapes(self) -> None:
        """All CPF-shaped strings with wrong check digits must be rejected.

        This is the core false-positive-reduction gate: if a document has
        CPF-looking numbers (phone refs, sequential IDs, etc.) but they fail
        Mod-11, the detector must return no findings.
        """
        # Build a document containing only invalid-shape CPFs
        doc = " ".join(_INVALID_CPF_SHAPES)
        hits = text_contains_valid_cpf(doc)
        self.assertFalse(
            hits, f"False positive(s) from invalid shapes: {_INVALID_CPF_SHAPES}"
        )

    def test_only_valid_found_in_mixed_document(self) -> None:
        """In a document mixing valid and invalid shapes, only valid ones trigger."""
        doc = " ".join(_INVALID_CPF_SHAPES + _VALID_CPFS)
        self.assertTrue(text_contains_valid_cpf(doc))
        # Confirm that removing all valid ones leaves zero hits
        doc_no_valid = " ".join(_INVALID_CPF_SHAPES)
        self.assertFalse(text_contains_valid_cpf(doc_no_valid))


class TestCnpjCorpus(unittest.TestCase):
    """Table-driven tests over the expanded CNPJ fixture corpus."""

    def test_all_valid_cnpjs_accepted(self) -> None:
        for cnpj in _VALID_CNPJS:
            with self.subTest(cnpj=cnpj):
                self.assertTrue(
                    PIIValidator.validate_cnpj(cnpj),
                    f"Expected valid CNPJ to be accepted: {cnpj}",
                )

    def test_all_valid_cnpjs_found_in_text(self) -> None:
        for cnpj in _VALID_CNPJS:
            with self.subTest(cnpj=cnpj):
                self.assertTrue(
                    text_contains_valid_cnpj(f"empresa cnpj={cnpj} ok"),
                    f"Expected text_contains_valid_cnpj to find: {cnpj}",
                )


# ---------------------------------------------------------------------------
# CPF fiscal-region / state-origin tests
#
# Legislation note:
#   - Provimento CNJ nº 63/2017: CPF mandatory in birth registrations.
#   - Lei nº 14.534/2023: CPF as universal identifier in all public documents.
#   - Before 2017: CPF could be obtained in any state; 9th digit may not
#     match birth state for persons registered before the reform.
# ---------------------------------------------------------------------------

# (cpf_digits, expected_region_digit, expected_states_include)
_FISCAL_REGION_FIXTURES: list[tuple[str, str, list[str]]] = [
    ("22171061634", "6", ["MG"]),  # 221.710.616-34 — MG
    ("33838477804", "8", ["SP"]),  # 338.384.778-04 — SP
    ("31955141924", "9", ["PR", "SC"]),  # 319.551.419-24 — PR/SC
    ("78544330380", "3", ["CE", "MA", "PI"]),  # 785.443.303-80 — Nordeste Norte
    ("01846610800", "8", ["SP"]),  # 018.466.108-00 — SP (digito 8)
    ("61826555773", "7", ["ES", "RJ"]),  # 618.265.557-73 — ES/RJ
    ("33838477804", "8", ["SP"]),  # digit 8 → SP
    ("97439529189", "1", ["DF", "GO", "MS", "MT", "TO"]),  # digit 1 → Centro-Oeste
    ("24537184442", "4", ["AL", "PB", "PE", "RN"]),  # digit 4 → Nordeste Leste
    ("85228083502", "5", ["BA", "SE"]),  # digit 5 → Nordeste Sul
    ("23071517297", "2", ["AC", "AM", "AP", "PA", "RO", "RR"]),  # digit 2 → Norte
]


class TestCpfFiscalRegion(unittest.TestCase):
    """Unit tests for cpf_fiscal_region() and cpf_birth_state_consistent()."""

    def test_map_has_all_10_regions(self) -> None:
        self.assertEqual(set(CPF_FISCAL_REGION_MAP.keys()), set("0123456789"))

    def test_every_region_has_states_and_description(self) -> None:
        for digit, info in CPF_FISCAL_REGION_MAP.items():
            with self.subTest(digit=digit):
                self.assertIn("states", info)
                self.assertIn("description", info)
                self.assertGreaterEqual(len(info["states"]), 1)

    def test_fixture_region_digit_matches(self) -> None:
        for digits, expected_digit, expected_states in _FISCAL_REGION_FIXTURES:
            with self.subTest(cpf=digits):
                region = cpf_fiscal_region(digits)
                self.assertIsNotNone(region, f"Region should not be None for {digits}")
                self.assertEqual(
                    digits[8],
                    expected_digit,
                    f"9th digit mismatch for {digits}",
                )
                for state in expected_states:
                    self.assertIn(state, region["states"])  # type: ignore[index]

    def test_invalid_digits_returns_none(self) -> None:
        self.assertIsNone(cpf_fiscal_region(""))
        self.assertIsNone(cpf_fiscal_region("1234567890"))  # 10 digits
        self.assertIsNone(cpf_fiscal_region("123456789012"))  # 12 digits

    def test_birth_state_consistent_match(self) -> None:
        # 221.710.616-34 → region 6 → MG
        self.assertTrue(cpf_birth_state_consistent("22171061634", "MG"))

    def test_birth_state_consistent_mismatch(self) -> None:
        # 221.710.616-34 → region 6 → MG; SP is NOT in region 6
        # Result is False but this is a *hint* only — pre-2017 CPFs may mismatch
        self.assertFalse(cpf_birth_state_consistent("22171061634", "SP"))

    def test_birth_state_consistent_empty_state_returns_none(self) -> None:
        self.assertIsNone(cpf_birth_state_consistent("22171061634", ""))

    def test_birth_state_consistent_case_insensitive(self) -> None:
        self.assertTrue(cpf_birth_state_consistent("22171061634", "mg"))
        self.assertTrue(cpf_birth_state_consistent("22171061634", "Mg"))

    def test_all_10_region_digits_map_to_known_states(self) -> None:
        """Regression: every digit 0-9 maps to at least one recognisable UF."""
        known_ufs = {
            "AC",
            "AL",
            "AM",
            "AP",
            "BA",
            "CE",
            "DF",
            "ES",
            "GO",
            "MA",
            "MG",
            "MS",
            "MT",
            "PA",
            "PB",
            "PE",
            "PI",
            "PR",
            "RJ",
            "RN",
            "RO",
            "RR",
            "RS",
            "SC",
            "SE",
            "SP",
            "TO",
        }
        for digit, info in CPF_FISCAL_REGION_MAP.items():
            for uf in info["states"]:
                with self.subTest(digit=digit, uf=uf):
                    self.assertIn(uf, known_ufs, f"Unknown UF '{uf}' in region {digit}")


# ---------------------------------------------------------------------------
# Large corpus regression: 30 CPFs sampled from the 266 verified externally
# ---------------------------------------------------------------------------

_LARGE_CORPUS_SAMPLE = [
    # formatted — all verified valid
    "221.710.616-34",
    "245.371.844-42",
    "338.384.778-04",
    "974.395.291-89",
    "319.551.419-24",
    "785.443.303-80",
    "554.743.563-58",
    "978.644.503-18",
    "018.466.108-00",
    "932.929.183-08",
    "061.230.758-10",
    "221.302.650-57",
    "852.280.835-02",
    "618.265.557-73",
    "168.664.796-49",
    "338.539.991-23",
    "857.632.419-91",
    "258.154.394-95",
    "394.236.838-27",
    "624.355.686-73",
    # unformatted (no punctuation)
    "47634470686",
    "65718594244",
    "85646432359",
    "63738186590",
    "60208674632",
    "61780005377",
    "97981036534",
    "05314960150",
    "25370041407",
    "08868379520",
]


class TestLargeCorpusRegression(unittest.TestCase):
    """Regression gate: 30 CPFs sampled from the 266 user-provided corpus."""

    def test_all_large_corpus_cpfs_valid(self) -> None:
        for cpf in _LARGE_CORPUS_SAMPLE:
            with self.subTest(cpf=cpf):
                self.assertTrue(
                    PIIValidator.validate_cpf(cpf),
                    f"Large-corpus CPF failed validation: {cpf}",
                )

    def test_all_large_corpus_cpfs_found_in_text(self) -> None:
        for cpf in _LARGE_CORPUS_SAMPLE:
            with self.subTest(cpf=cpf):
                self.assertTrue(
                    text_contains_valid_cpf(f"dados cpf={cpf} fim"),
                    f"text_contains_valid_cpf missed: {cpf}",
                )
