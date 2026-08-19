"""#651 — README front door to Enterprise remediation use-cases (coming, not shipped)."""

from __future__ import annotations

from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
_EN = _ROOT / "README.md"
_PT = _ROOT / "README.pt_BR.md"
_FORBIDDEN = (
    "docs/plans/",
    "Protegrity",
    "Privacera",
    "Informatica",
    "TokenEx",
    "Voltage",
    "format-preserving",
    "FPE",
    "immutable",
)


def test_readme_enterprise_remediation_hooks_are_coming() -> None:
    en = _EN.read_text(encoding="utf-8")
    pt = _PT.read_text(encoding="utf-8")
    assert "Enterprise remediation hooks" in en
    assert "(coming:" in en
    assert "Hooks de remediação Enterprise" in pt
    assert "em breve" in pt
    for text in (en, pt):
        assert "USE_CASE_SCAN_AND_REMEDIATE.md" in text
        assert "USE_CASE_TOKENIZED_FINDINGS.md" in text
        for banned in _FORBIDDEN:
            assert banned not in text, f"README must not contain {banned!r}"
