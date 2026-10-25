"""Regression guards for German terms on the Benelux sample (#1275)."""

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
BENELUX_SAMPLE = (
    REPO_ROOT / "docs" / "compliance-samples" / "compliance-sample-benelux.yaml"
)

_GERMAN_TERMS = (
    "personenbezogene Daten",
    "Einwilligung",
    "betroffene Person",
    "Verantwortlicher",
    "Auftragsverarbeiter",
    "besondere Kategorien personenbezogener Daten",
    "Aufsichtsbehörde",
)


def test_benelux_includes_german_inventory_terms():
    text = BENELUX_SAMPLE.read_text(encoding="utf-8")
    for term in _GERMAN_TERMS:
        assert term in text


def test_benelux_header_mentions_german_community():
    text = BENELUX_SAMPLE.read_text(encoding="utf-8")
    assert "Ostbelgien" in text or "German-speaking" in text
