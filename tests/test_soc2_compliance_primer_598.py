"""#598 — SOC 2 primer exists with hub registration and CPA disclaimer."""

from __future__ import annotations

from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
_PRIMER = _ROOT / "docs" / "plans" / "SOC2_COMPLIANCE_PRIMER.md"
_HUB = _ROOT / "docs" / "plans" / "PRIMERS_HUB.md"

_HEADINGS = (
    "## Privacy TSC (P1–P8)",
    "## Security TSC — CC6 (not Confidentiality)",
)


def _heading_line_index(lines: list[str], heading: str) -> int:
    for idx, raw in enumerate(lines):
        line = raw.rstrip()
        if line == heading or line.startswith(f"{heading} {{#"):
            return idx
    raise AssertionError(f"missing heading line {heading!r}")


def test_soc2_primer_registered_and_disclaims_cpa() -> None:
    assert _PRIMER.is_file()
    text = _PRIMER.read_text(encoding="utf-8")
    assert (
        "<!-- plans-hub-summary: Primer SOC 2 Privacy TSC — Data Boar como gerador de evidência para auditoria SOC 2 -->"
        in text
    )
    assert "does **not** perform a SOC 2 examination" in text
    assert "licensed **CPA**" in text
    assert "There is **no** `compliance-sample-*.yaml` for SOC 2" in text
    assert "**P2**" in text
    assert "**P8**" in text
    assert "not a consent log" in text
    assert "#549](https://github.com/DataBoar/data-boar/issues/549) is closed" in text
    assert "Default is off" in text
    assert "no** built-in scheduler" in text
    assert "not** record third-party disclosures" in text
    assert "(roadmap)" in text
    for n in range(1, 9):
        assert f"**P{n}**" in text
    lines = text.splitlines()
    indexes = [_heading_line_index(lines, heading) for heading in _HEADINGS]
    assert indexes == sorted(indexes)


def test_primers_hub_links_soc2_primer() -> None:
    hub = _HUB.read_text(encoding="utf-8")
    assert "[SOC2_COMPLIANCE_PRIMER.md](SOC2_COMPLIANCE_PRIMER.md)" in hub
    assert "planned — #598" not in hub
