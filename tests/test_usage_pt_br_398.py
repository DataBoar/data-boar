"""#398 — USAGE.pt_BR must carry connector YAML headings plus sections 5–7."""

from __future__ import annotations

from pathlib import Path

_USAGE_PT = Path(__file__).resolve().parents[1] / "docs" / "USAGE.pt_BR.md"

_SECTION_HEADINGS = (
    "## 5. Baixando relatórios (resumo)",
    "## 6. Infraestrutura como Código — OpenTofu / Terraform",
    "## 7. Referência rápida",
)

_CONNECTOR_MARKERS = (
    "Snowflake",
    "Basic auth",
    "Bearer token",
    "OAuth2",
    "Custom headers",
    "Power BI",
    "Dataverse",
    "SMB/CIFS",
    "WebDAV",
    "SharePoint",
    "NFS",
)


def test_usage_pt_br_has_sections_5_6_7_and_connector_headings() -> None:
    text = _USAGE_PT.read_text(encoding="utf-8")
    for heading in _SECTION_HEADINGS:
        assert heading in text, f"missing {heading!r}"
    for marker in _CONNECTOR_MARKERS:
        assert marker in text, f"missing connector marker {marker!r}"
