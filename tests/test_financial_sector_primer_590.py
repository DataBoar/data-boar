"""#590 — financial-sector primer exists with hub registration and QSA disclaimer."""

from __future__ import annotations

from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
_PRIMER = _ROOT / "docs" / "plans" / "FINANCIAL_SECTOR_COMPLIANCE_PRIMER.md"
_HUB = _ROOT / "docs" / "plans" / "PRIMERS_HUB.md"

_HEADINGS = (
    "## PCI DSS v4.0 — Payment Card Industry Data Security Standard",
    "## SOX — Sarbanes-Oxley Section 404 (ICFR)",
    "## BACEN / CMN Resolução 4.893/2021",
)


def _heading_line_index(lines: list[str], heading: str) -> int:
    for idx, raw in enumerate(lines):
        line = raw.rstrip()
        if line == heading or line.startswith(f"{heading} {{#"):
            return idx
    raise AssertionError(f"missing heading line {heading!r}")


def test_financial_sector_primer_registered_and_disclaims_qsa() -> None:
    assert _PRIMER.is_file()
    text = _PRIMER.read_text(encoding="utf-8")
    assert (
        "<!-- plans-hub-summary: Primer PCI DSS v4.0 / SOX / BACEN — alinhamento Data Boar para setor financeiro -->"
        in text
    )
    assert "complements, does not replace, a QSA assessment for PCI DSS" in text
    assert "(roadmap)" in text
    lines = text.splitlines()
    indexes = [_heading_line_index(lines, heading) for heading in _HEADINGS]
    assert indexes == sorted(indexes)


def test_primers_hub_links_financial_sector_primer() -> None:
    hub = _HUB.read_text(encoding="utf-8")
    assert (
        "[FINANCIAL_SECTOR_COMPLIANCE_PRIMER.md](FINANCIAL_SECTOR_COMPLIANCE_PRIMER.md)"
        in hub
    )
    assert "planned — #590" not in hub
