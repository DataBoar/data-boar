"""#652 — biometric use-case ties non-resettable data to vaultless tokenization."""

from __future__ import annotations

from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
_EN = _ROOT / "docs" / "use-cases" / "USE_CASE_BIOMETRIC_DATA_PROTECTION.md"
_PT = _ROOT / "docs" / "use-cases" / "USE_CASE_BIOMETRIC_DATA_PROTECTION.pt_BR.md"
_FORBIDDEN = (
    "Protegrity",
    "Privacera",
    "Informatica",
    "TokenEx",
    "Voltage",
    "format-preserving",
    "FPE",
    "AES",
    "HSM",
    "immutable",
    "docs/plans/",
)


def test_biometric_use_case_vaultless_non_resettable() -> None:
    en = _EN.read_text(encoding="utf-8")
    pt = _PT.read_text(encoding="utf-8")
    assert "## Why vaultless tokenization matters for non-resettable data" in en
    assert "## Por que tokenização vaultless importa para dados não resetáveis" in pt
    assert "LGPD Art. 11" in en
    assert "GDPR Art. 9" in en
    assert "LGPD art. 11" in pt
    assert "GDPR art. 9" in pt
    assert "LGPD Art. 46" in en
    assert "LGPD art. 46" in pt
    assert "Enterprise plugin (**coming**)" in en
    assert "plugin Enterprise (**em breve**)" in pt
    assert "Remediation via plugin coming" in en
    assert "Before/after audit trail coming" in en
    assert "Remediação via plugin em breve" in pt
    assert "Trilha antes/depois em breve" in pt
    assert "not** a live biometric" in en
    assert "não** é biometria ao vivo" in pt
    assert "ships today" in en
    assert "entrega hoje" in pt
    assert "Why vaultless tokenization matters for non-resettable data** above" in en
    assert (
        "Por que tokenização vaultless importa para dados não resetáveis** acima" in pt
    )
    for text in (en, pt):
        for banned in _FORBIDDEN:
            assert banned not in text, f"biometric use-case must not contain {banned!r}"
