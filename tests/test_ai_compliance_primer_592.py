"""#592 — AI compliance primer exists with hub registration and data-layer disclaimer."""

from __future__ import annotations

from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
_PRIMER = _ROOT / "docs" / "plans" / "AI_COMPLIANCE_PRIMER.md"
_HUB = _ROOT / "docs" / "plans" / "PRIMERS_HUB.md"

_HEADINGS = (
    "## Framework × obligation × Data Boar (status)",
    "## EU AI Act — Regulation (EU) 2024/1689",
    "## ISO/IEC 42001:2023 — AI Management Systems",
    "## NIST AI RMF 1.0 — GOVERN, MAP, MEASURE, MANAGE",
)


def _heading_line_index(lines: list[str], heading: str) -> int:
    for idx, raw in enumerate(lines):
        line = raw.rstrip()
        if line == heading or line.startswith(f"{heading} {{#"):
            return idx
    raise AssertionError(f"missing heading line {heading!r}")


def test_ai_compliance_primer_registered_and_disclaims_model_eval() -> None:
    assert _PRIMER.is_file()
    text = _PRIMER.read_text(encoding="utf-8")
    assert (
        "<!-- plans-hub-summary: Primer EU AI Act / ISO 42001 / NIST AI RMF — Data Boar como compliance layer para AI pipelines -->"
        in text
    )
    assert (
        "covers the **data layer** — it does **not** evaluate the model itself" in text
    )
    assert "There is **no** `compliance-sample-*.yaml` for the EU AI Act" in text
    assert "category mismatch" in text
    assert "2 August 2026" in text
    assert "2 December 2027" in text
    assert "2026/1744" in text
    assert "**6.1.2**" in text
    assert "not** a shipped detector field on scan findings" in text
    assert "(roadmap)" in text
    assert "Art. 12 model-operation logs" in text
    assert "not** per-session operator/target lists" in text
    assert "scan_sessions_summary" in text
    lines = text.splitlines()
    indexes = [_heading_line_index(lines, heading) for heading in _HEADINGS]
    assert indexes == sorted(indexes)


def test_primers_hub_links_ai_compliance_primer() -> None:
    hub = _HUB.read_text(encoding="utf-8")
    assert "[AI_COMPLIANCE_PRIMER.md](AI_COMPLIANCE_PRIMER.md)" in hub
    assert "planned — #592" not in hub
