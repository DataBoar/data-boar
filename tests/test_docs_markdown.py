"""
Tests for Markdown documentation: structure, presence of key docs, and internal links.

Encodes good-doc practice so regressions are caught (e.g. broken links, missing README).
This project has no TypeScript/TSX files; quality coverage is Python + Markdown only.
"""

import re
from pathlib import Path


def _project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _read_md(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


# --- Key documentation files exist ---


def test_readme_exists():
    """README.md must exist at project root."""
    assert (_project_root() / "README.md").is_file()


def test_usage_doc_exists():
    """docs/USAGE.md must exist (canonical usage)."""
    assert (_project_root() / "docs" / "USAGE.md").is_file()


def test_security_doc_exists():
    """SECURITY.md must exist (security and API key)."""
    assert (_project_root() / "SECURITY.md").is_file()


def test_contributing_exists():
    """CONTRIBUTING.md must exist."""
    assert (_project_root() / "CONTRIBUTING.md").is_file()


def test_compliance_frameworks_doc_exists():
    """docs/COMPLIANCE_FRAMEWORKS.md must exist (compliance samples and frameworks)."""
    assert (_project_root() / "docs" / "COMPLIANCE_FRAMEWORKS.md").is_file()


def test_compliance_samples_folder_exists():
    """docs/compliance-samples/ must exist and contain README (compliance sample configs)."""
    root = _project_root()
    folder = root / "docs" / "compliance-samples"
    assert folder.is_dir(), "docs/compliance-samples/ should exist"
    assert (folder / "README.md").is_file(), (
        "docs/compliance-samples/README.md should exist"
    )


def test_compliance_and_legal_doc_exists():
    """docs/COMPLIANCE_AND_LEGAL.md must exist (summary for legal and compliance teams)."""
    assert (_project_root() / "docs" / "COMPLIANCE_AND_LEGAL.md").is_file()


# --- README structure (SonarQube-style doc quality) ---


def test_readme_has_title_heading():
    """README must start with a level-1 heading."""
    path = _project_root() / "README.md"
    text = _read_md(path)
    first_line = text.lstrip().split("\n")[0] if text.strip() else ""
    assert first_line.startswith("# "), "README.md should start with # Title"


def test_readme_mentions_config_and_lgpd():
    """README should mention configuration and LGPD/compliance (key product description)."""
    text = _read_md(_project_root() / "README.md")
    assert "config" in text.lower()
    assert "lgpd" in text.lower() or "compliance" in text.lower()


def test_readme_en_and_ptbr_keep_mascot_image_reference():
    """Main README files keep the mascot image link for branding consistency."""
    root = _project_root()
    mascot_url = "https://databoar.com.br/images/mascot-pot.png"
    en = _read_md(root / "README.md")
    pt = _read_md(root / "README.pt_BR.md")
    expected = f"![Data Boar mascot]({mascot_url})"
    assert expected in en, "README.md should include mascot image markdown"
    assert expected in pt, "README.pt_BR.md should include mascot image markdown"


def _readme_pitch_block(text: str, start_heading: str, next_heading: str) -> str:
    start = text.find(start_heading)
    if start == -1:
        return ""
    end = text.find(next_heading, start)
    if end == -1:
        end = len(text)
    return text[start:end]


def test_readme_pitch_avoids_direct_plans_links():
    """Landing-page pitch blocks should not deep-link docs/plans files."""
    root = _project_root()
    en = _read_md(root / "README.md")
    pt = _read_md(root / "README.pt_BR.md")
    en_pitch = _readme_pitch_block(
        en, "## For decision-makers and compliance leads", "## Technical overview"
    )
    pt_pitch = _readme_pitch_block(
        pt, "## Para gestores e líderes de conformidade", "## Visão técnica"
    )
    assert "docs/plans/" not in en_pitch, (
        "README.md pitch should avoid direct docs/plans links"
    )
    assert "docs/plans/" not in pt_pitch, (
        "README.pt_BR.md pitch should avoid direct docs/plans links"
    )


# --- docs/USAGE.md structure ---


def test_usage_has_heading_structure():
    """docs/USAGE.md should have at least one top-level heading."""
    text = _read_md(_project_root() / "docs" / "USAGE.md")
    assert "# " in text


def test_usage_mentions_cli_and_api():
    """docs/USAGE should mention CLI and API (main ways to use the app)."""
    text = _read_md(_project_root() / "docs" / "USAGE.md")
    assert "cli" in text.lower() or "command" in text.lower()
    assert "api" in text.lower() or "endpoint" in text.lower()


# --- Internal relative links: same-repo links should resolve ---


def _collect_relative_links_from_md(text: str) -> list[str]:
    """Extract relative links [text](path) where path does not start with http or #."""
    pattern = re.compile(r"\[([^\]]*)\]\(([^)#]+)\)")
    links = []
    for _label, path in pattern.findall(text):
        path = path.strip()
        if (
            path.startswith("http")
            or path.startswith("mailto:")
            or path.startswith("#")
        ):
            continue
        if "://" in path:
            continue
        links.append(path)
    return links


def test_readme_internal_links_resolve():
    """Relative links in README.md should point to existing files (no broken links)."""
    root = _project_root()
    path = root / "README.md"
    text = _read_md(path)
    links = _collect_relative_links_from_md(text)
    broken = []
    for link in links:
        # Normalize: remove anchor
        file_part = link.split("#")[0].strip()
        if not file_part:
            continue
        target = (root / file_part).resolve()
        try:
            if not target.is_file() and not target.is_dir():
                broken.append(link)
        except OSError:
            broken.append(link)
    assert not broken, f"README.md broken relative link(s): {broken}"


def test_usage_internal_links_resolve():
    """Relative links in docs/USAGE.md should point to existing files (base dir is docs/ or repo root)."""
    root = _project_root()
    path = root / "docs" / "USAGE.md"
    text = _read_md(path)
    links = _collect_relative_links_from_md(text)
    broken = []
    for link in links:
        file_part = link.split("#")[0].strip()
        if not file_part:
            continue
        # Resolve from docs/ (e.g. SENSITIVITY_DETECTION.md) or from repo root (e.g. ../SECURITY.md)
        found = False
        for base in (root / "docs", root):
            target = (base / file_part).resolve()
            try:
                if target.is_file() or target.is_dir():
                    found = True
                    break
            except OSError:
                continue
        if not found:
            broken.append(link)
    assert not broken, f"docs/USAGE.md broken relative link(s): {broken}"


def test_lab_completao_runbook_docs_exist():
    """LAB_COMPLETAO_RUNBOOK EN/pt-BR pair exists (completão vs pytest)."""
    root = _project_root()
    assert (root / "docs" / "ops" / "LAB_COMPLETAO_RUNBOOK.md").is_file()
    assert (root / "docs" / "ops" / "LAB_COMPLETAO_RUNBOOK.pt_BR.md").is_file()


def test_lab_smoke_multi_host_pt_br_no_operator_scratch_arrows():
    """LAB_SMOKE pt-BR checklist must not ship informal notes after '<-' (tracked hygiene)."""
    path = _project_root() / "docs" / "ops" / "LAB_SMOKE_MULTI_HOST.pt_BR.md"
    text = _read_md(path)
    assert " <-" not in text, (
        "Remove inline operator scratch notes (pattern ' <-' ) from "
        "docs/ops/LAB_SMOKE_MULTI_HOST.pt_BR.md; keep criteria in the table clean."
    )


# --- Optional: key doc files are non-empty and have minimal structure ---


def test_security_has_content():
    """SECURITY.md should not be empty and mention security."""
    text = _read_md(_project_root() / "SECURITY.md")
    assert len(text.strip()) > 100
    assert (
        "security" in text.lower() or "http" in text.lower() or "header" in text.lower()
    )
