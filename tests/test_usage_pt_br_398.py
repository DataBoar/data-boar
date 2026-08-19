"""#398 — USAGE.pt_BR must carry connector YAML headings plus sections 5–7."""

from __future__ import annotations

from pathlib import Path

_USAGE_PT = Path(__file__).resolve().parents[1] / "docs" / "USAGE.pt_BR.md"

_SECTION_HEADINGS = (
    "## 5. Baixando relatórios (resumo)",
    "### 5.1 Notificações ao operador (opcional)",
    "## 6. Infraestrutura como Código — OpenTofu / Terraform",
    "## 7. Referência rápida",
)

_CONNECTOR_HEADINGS = (
    "## Snowflake (optional, .[bigdata])",
    "## Basic auth",
    "## Bearer token (static or from environment)",
    "## OAuth2 client credentials (machine-to-machine)",
    "## Custom headers (e.g. API key or Negotiate)",
    "## Power BI (`type: powerbi`)",
    "## Dataverse / Power Apps (`type: dataverse` or `type: powerapps`)",
    "## SMB/CIFS",
    "## WebDAV",
    "## SharePoint",
    "## NFS (path = local mount point; mount NFS before scanning)",
)


def _heading_line_index(lines: list[str], heading: str) -> int:
    for idx, raw in enumerate(lines):
        line = raw.rstrip()
        if line == heading or line.startswith(f"{heading} {{#"):
            return idx
    raise AssertionError(f"missing heading line {heading!r}")


def test_usage_pt_br_has_sections_5_6_7_and_connector_headings() -> None:
    lines = _USAGE_PT.read_text(encoding="utf-8").splitlines()
    section_indexes = [
        _heading_line_index(lines, heading) for heading in _SECTION_HEADINGS
    ]
    assert section_indexes == sorted(section_indexes), (
        "sections 5, 5.1, 6, and 7 must appear in that order"
    )
    for heading in _CONNECTOR_HEADINGS:
        _heading_line_index(lines, heading)
