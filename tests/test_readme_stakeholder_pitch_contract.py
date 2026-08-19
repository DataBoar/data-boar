"""
Guardrail: root README stakeholder block stays plain-language (ADR 0035).

Deck-only labels (Data Sniffing / Deep Boring) belong in compliance/glossary
docs, not in the executive pitch section before the technical overview.
"""

from __future__ import annotations

from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[1]


def _slice_between(text: str, start_heading: str, end_heading: str) -> str:
    i0 = text.find(start_heading)
    i1 = text.find(end_heading)
    assert i0 != -1, f"missing start heading {start_heading!r}"
    assert i1 != -1, f"missing end heading {end_heading!r}"
    assert i0 < i1, "start heading must appear before end heading"
    return text[i0:i1]


@pytest.mark.parametrize(
    ("readme_name", "start", "end", "required_heading"),
    [
        (
            "README.md",
            "## For decision-makers and compliance leads",
            "## Technical overview",
            "**Sniffing with judgment:**",
        ),
        (
            "README.pt_BR.md",
            "## Para gestores e líderes de conformidade",
            "## Visão técnica",
            "**Farejando com critério:**",
        ),
    ],
)
def test_readme_stakeholder_pitch_headings_and_no_deck_jargon(
    readme_name: str,
    start: str,
    end: str,
    required_heading: str,
) -> None:
    path = _REPO_ROOT / readme_name
    text = path.read_text(encoding="utf-8")
    pitch = _slice_between(text, start, end)
    assert required_heading in pitch, (
        f"{readme_name} stakeholder block must include {required_heading!r}"
    )
    assert "Data Sniffing" not in pitch, (
        f"{readme_name}: keep deck label 'Data Sniffing' out of the stakeholder pitch "
        "(use COMPLIANCE_FRAMEWORKS / GLOSSARY; see ADR 0035)."
    )
    assert "Deep Boring" not in pitch, (
        f"{readme_name}: keep deck label 'Deep Boring' out of the stakeholder pitch "
        "(see ADR 0035)."
    )


def test_readme_release_banner_en_pt_br_pair() -> None:
    """#397 — pt-BR must mirror the EN release/changelog banner heading."""
    en = (_REPO_ROOT / "README.md").read_text(encoding="utf-8")
    pt = (_REPO_ROOT / "README.pt_BR.md").read_text(encoding="utf-8")
    assert "**Current release" in en
    assert "**Versão atual" in pt
