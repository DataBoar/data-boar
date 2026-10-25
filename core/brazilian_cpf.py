"""
Brazilian CPF and CNPJ checksum validation and optional text scan for
context-aware PII hints.

``core.detector`` matches CPF/CNPJ *shape* with the built-in regex patterns.
This module adds **Modulo-11** check-digit validation so 11/14-digit-like
tokens that are **not** valid numbers can be filtered in the detection loop,
reducing false positives on sequential IDs, counters, or test data.

**CPF fiscal region (9th digit):**
The 9th digit (index 8 in the 11-digit string) encodes the fiscal region
where the CPF was originally issued.  Since **Provimento CNJ nº 63/2017**
(reinforced by Lei nº 14.534/2023), CPFs issued at birth registration must
reflect the state where the birth was registered.  For older CPFs (issued
before 2017-2018, when the person was already an adult), the region digit
may *not* match the declared birth state because the CPF was obtained from a
different state.  Use `cpf_fiscal_region()` only as a **forensic hint**; do
not reject a CPF solely because region and birth state diverge.

**Sync:** keep ``CPF_SHAPE_PATTERN`` and ``CNPJ_SHAPE_PATTERN`` identical to
the corresponding pattern strings in ``core.detector.DEFAULT_PATTERNS``.
"""

from __future__ import annotations

import re
from typing import Any

CPF_SHAPE_PATTERN = r"\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b"
CNPJ_SHAPE_PATTERN = r"\b\d{2}\.?\d{3}\.?\d{3}/?\d{4}-?\d{2}\b"
_CPF_RX = re.compile(CPF_SHAPE_PATTERN)
_CNPJ_RX = re.compile(CNPJ_SHAPE_PATTERN)

# ---------------------------------------------------------------------------
# CPF fiscal-region map (9th digit → issuing region / states)
# Source: Receita Federal do Brasil digit encoding (unchanged since 1972).
# Post-2017 (Provimento CNJ 63/2017): CPF must be assigned at birth
# registration, so the 9th digit should match the birth state for newborns.
# For CPFs issued to adults, the digit reflects where the CPF was *obtained*.
# ---------------------------------------------------------------------------
CPF_FISCAL_REGION_MAP: dict[str, dict] = {
    "0": {
        "states": ["RS"],
        "region": "Região 0",
        "description": "Rio Grande do Sul",
    },
    "1": {
        "states": ["DF", "GO", "MS", "MT", "TO"],
        "region": "Região 1",
        "description": "Distrito Federal e Centro-Oeste",
    },
    "2": {
        "states": ["AC", "AM", "AP", "PA", "RO", "RR"],
        "region": "Região 2",
        "description": "Norte (Amazônia Legal)",
    },
    "3": {
        "states": ["CE", "MA", "PI"],
        "region": "Região 3",
        "description": "Nordeste Norte",
    },
    "4": {
        "states": ["AL", "PB", "PE", "RN"],
        "region": "Região 4",
        "description": "Nordeste Leste",
    },
    "5": {
        "states": ["BA", "SE"],
        "region": "Região 5",
        "description": "Nordeste Sul",
    },
    "6": {
        "states": ["MG"],
        "region": "Região 6",
        "description": "Minas Gerais",
    },
    "7": {
        "states": ["ES", "RJ"],
        "region": "Região 7",
        "description": "Espírito Santo e Rio de Janeiro",
    },
    "8": {
        "states": ["SP"],
        "region": "Região 8",
        "description": "São Paulo",
    },
    "9": {
        "states": ["PR", "SC"],
        "region": "Região 9",
        "description": "Paraná e Santa Catarina",
    },
}


def cpf_fiscal_region(digits: str) -> dict | None:
    """
    Return the fiscal-region entry for a normalised 11-digit CPF string.

    The 9th digit (``digits[8]``) encodes the Receita Federal issuing region.
    Returns ``None`` if *digits* is not an 11-digit string.

    Example::

        >>> cpf_fiscal_region("22171061634")
        {'states': ['MG'], 'region': 'Região 6', 'description': 'Minas Gerais'}
    """
    if not digits or len(digits) != 11 or not digits.isdigit():
        return None
    return CPF_FISCAL_REGION_MAP.get(digits[8])


def cpf_birth_state_consistent(digits: str, declared_state: str) -> bool | None:
    """
    Return True when *declared_state* is listed in the CPF's fiscal region.

    Returns ``None`` when the region cannot be determined (invalid digits) or
    when *declared_state* is empty.  Always treat the result as a **hint**:
    a mismatch does not prove fraud because CPFs issued before 2017 reflect
    where the person *enrolled*, not where they were born.
    """
    if not declared_state:
        return None
    region = cpf_fiscal_region(digits)
    if region is None:
        return None
    return declared_state.upper().strip() in region["states"]


def normalize_cpf_digits(value: str) -> str | None:
    """Return 11 digits only, or None if the string cannot be a CPF payload."""
    if not value:
        return None
    digits = re.sub(r"\D", "", value)
    if len(digits) != 11 or not digits.isdigit():
        return None
    return digits


def normalize_cnpj_digits(value: str) -> str | None:
    """Return 14 digits only, or None if the string cannot be a CNPJ payload."""
    if not value:
        return None
    digits = re.sub(r"\D", "", value)
    if len(digits) != 14 or not digits.isdigit():
        return None
    return digits


def cpf_checksum_valid(digits: str) -> bool:
    """
    True if ``digits`` (exactly 11 decimal digits) passes both CPF check digits.

    Rejects known-invalid sequences (all same digit). Does not prove the
    number is *issued* or belongs to a person—only that it satisfies the public
    checksum algorithm used by Receita Federal.
    """
    if len(digits) != 11 or not digits.isdigit():
        return False
    if digits == digits[0] * 11:
        return False

    def _digit(base: str, count: int) -> int:
        total = sum(int(base[i]) * (count + 1 - i) for i in range(count))
        remainder = total % 11
        return 0 if remainder < 2 else 11 - remainder

    if _digit(digits, 9) != int(digits[9]):
        return False
    if _digit(digits, 10) != int(digits[10]):
        return False
    return True


def cnpj_checksum_valid(digits: str) -> bool:
    """
    True if ``digits`` (exactly 14 decimal digits) passes both CNPJ check digits.

    Covers the legacy all-numeric format (RFB since 1963). The newer
    alphanumeric format (RFB Instrução Normativa 2.229/2024, effective 2026)
    uses the same algorithm but with digits extracted differently — that format
    is matched by ``LGPD_CNPJ_ALNUM`` and is *not* validated here.

    Rejects known-invalid sequences (all same digit). Does not prove the CNPJ
    is active or registered — only that it satisfies the public check algorithm.
    """
    if len(digits) != 14 or not digits.isdigit():
        return False
    if digits == digits[0] * 14:
        return False

    _W1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    _W2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]

    def _digit(base: str, weights: list[int]) -> int:
        total = sum(int(base[i]) * weights[i] for i in range(len(weights)))
        remainder = total % 11
        return 0 if remainder < 2 else 11 - remainder

    if _digit(digits, _W1) != int(digits[12]):
        return False
    if _digit(digits, _W2) != int(digits[13]):
        return False
    return True


def text_contains_valid_cpf(text: str) -> bool:
    """Return True if *any* CPF-shaped token in ``text`` passes checksum."""
    for m in _CPF_RX.finditer(text):
        d = normalize_cpf_digits(m.group())
        if d and cpf_checksum_valid(d):
            return True
    return False


def text_contains_valid_cnpj(text: str) -> bool:
    """Return True if *any* CNPJ-shaped token in ``text`` passes checksum."""
    for m in _CNPJ_RX.finditer(text):
        d = normalize_cnpj_digits(m.group())
        if d and cnpj_checksum_valid(d):
            return True
    return False


class PIIValidator:
    """Optional validator for CPF shape + checksum over free text or column samples."""

    @staticmethod
    def validate_cpf(cpf: str) -> bool:
        """Return True only when the value is 11 digits and passes both verifiers."""
        normalized = normalize_cpf_digits(cpf)
        if normalized is None:
            return False
        return cpf_checksum_valid(normalized)

    @staticmethod
    def validate_cnpj(cnpj: str) -> bool:
        """Return True only when the value is 14 digits and passes both verifiers."""
        normalized = normalize_cnpj_digits(cnpj)
        if normalized is None:
            return False
        return cnpj_checksum_valid(normalized)

    def scan_content(self, text: str) -> dict[str, Any]:
        """
        Find CPF-shaped substrings and keep those that pass ``validate_cpf``.

        Returns structured hits with a coarse ``risk_score`` for reporting demos.
        **Do not** persist raw matched values to public logs—``masked_tail`` exposes
        only the last two digits of the normalized form.
        """
        found: list[dict[str, Any]] = []
        risk_score = 0
        if not text:
            return {"found": found, "risk_score": risk_score}

        for match in _CPF_RX.finditer(text):
            raw = match.group()
            if not self.validate_cpf(raw):
                continue
            digits = normalize_cpf_digits(raw)
            if digits is None:
                continue
            masked_tail = digits[-2:]
            found.append(
                {
                    "type": "BRAZIL_CPF",
                    "masked_tail": masked_tail,
                    "confidence": "HIGH",
                }
            )
            risk_score += 10
        return {"found": found, "risk_score": risk_score}
