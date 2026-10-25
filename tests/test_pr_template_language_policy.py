"""Guard: PR template bilingual mix is documented (#400)."""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
PR_TEMPLATE = REPO_ROOT / ".github" / "PULL_REQUEST_TEMPLATE.md"


def test_pr_template_documents_intentional_en_pt_br_mix() -> None:
    text = PR_TEMPLATE.read_text(encoding="utf-8")
    assert "Language policy:" in text
    assert "structural headers in EN" in text
    assert "checklist in pt-BR" in text
    assert "## Description" in text
    assert "## 🧱 Checklist de Integridade" in text
