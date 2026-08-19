"""#650 — Enterprise remediation tease in the decision-maker value brief."""

from __future__ import annotations

from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
_EN = _ROOT / "docs" / "DECISION_MAKER_VALUE_BRIEF.md"
_PT = _ROOT / "docs" / "DECISION_MAKER_VALUE_BRIEF.pt_BR.md"
_TAGLINE = "scan once, remediate precisely, prove it"
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


def test_value_brief_enterprise_remediation_hook() -> None:
    en = _EN.read_text(encoding="utf-8")
    pt = _PT.read_text(encoding="utf-8")
    assert _TAGLINE in en
    assert f'"{_TAGLINE}"' in pt
    assert "Enterprise, coming" in en
    assert "Enterprise, em breve" in pt
    assert "tokenization, masking, or field encryption" in en
    assert "tokenização, mascaramento ou criptografia de campo" in pt
    for text in (en, pt):
        assert "USE_CASE_SCAN_AND_REMEDIATE.md" in text
        assert "USE_CASE_TOKENIZED_FINDINGS.md" in text
        for banned in _FORBIDDEN:
            assert banned not in text, f"value brief must not contain {banned!r}"
