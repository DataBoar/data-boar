"""Guard: LINKEDIN_ATS_PLAYBOOK keeps locale-aware ATS section (Canada / PIPEDA)."""

from pathlib import Path


def _root() -> Path:
    return Path(__file__).resolve().parent.parent


def test_playbook_en_lists_locale_section_and_canada_frames():
    text = (_root() / "docs" / "ops" / "LINKEDIN_ATS_PLAYBOOK.md").read_text(
        encoding="utf-8"
    )
    assert "## 8. Locale, jurisdiction, and certification pricing" in text
    assert "en_CA" in text
    assert "PIPEDA" in text
    assert "Bill C-27" in text


def test_playbook_pt_br_lists_locale_section():
    text = (_root() / "docs" / "ops" / "LINKEDIN_ATS_PLAYBOOK.pt_BR.md").read_text(
        encoding="utf-8"
    )
    assert "## 8. Localidade, jurisdição e preço de certificação" in text
    assert "en_CA" in text
    assert "PIPEDA" in text


def test_ats_locale_rule_file_exists():
    p = _root() / ".cursor" / "rules" / "ats-locale-aware-recommendations.mdc"
    assert p.is_file()
    body = p.read_text(encoding="utf-8")
    assert "ats-locale-aware-recommendations" in body or "PIPEDA" in body
