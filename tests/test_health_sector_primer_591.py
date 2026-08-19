"""#591 — health-sector primer exists with hub registration and BAA disclaimer."""

from __future__ import annotations

from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
_PRIMER = _ROOT / "docs" / "plans" / "HEALTH_SECTOR_COMPLIANCE_PRIMER.md"
_HUB = _ROOT / "docs" / "plans" / "PRIMERS_HUB.md"

_HEADINGS = (
    "## HIPAA — Privacy, Security, and Breach Notification (US)",
    "### Eighteen Safe Harbor identifiers (45 CFR § 164.514(b)(2))",
    "## Brazil — LGPD Art. 11 plus ANS, ANVISA, CFM",
)


def _heading_line_index(lines: list[str], heading: str) -> int:
    for idx, raw in enumerate(lines):
        line = raw.rstrip()
        if line == heading or line.startswith(f"{heading} {{#"):
            return idx
    raise AssertionError(f"missing heading line {heading!r}")


def test_health_sector_primer_registered_and_disclaims_baa() -> None:
    assert _PRIMER.is_file()
    text = _PRIMER.read_text(encoding="utf-8")
    assert (
        "<!-- plans-hub-summary: Primer HIPAA/PHI / ANS / ANVISA / CFM — alinhamento Data Boar para setor de saúde -->"
        in text
    )
    assert "does **not** replace access controls, encryption, or a **BAA**" in text
    assert "do **not** emit `HIPAA` / `HIPAA PHI`" in text
    assert "six-digit **operadora** registry" in text
    assert "compliance-sample-brazil_saude.yaml" in text
    assert "**#511**" in text
    assert "(roadmap)" in text
    for n in range(1, 19):
        assert f"| {n} |" in text
    lines = text.splitlines()
    indexes = [_heading_line_index(lines, heading) for heading in _HEADINGS]
    assert indexes == sorted(indexes)


def test_primers_hub_links_health_sector_primer() -> None:
    hub = _HUB.read_text(encoding="utf-8")
    assert (
        "[HEALTH_SECTOR_COMPLIANCE_PRIMER.md](HEALTH_SECTOR_COMPLIANCE_PRIMER.md)"
        in hub
    )
    assert "planned — #591" not in hub
