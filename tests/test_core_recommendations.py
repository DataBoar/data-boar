"""``core.recommendations`` — dicionário APG Fase A."""

from core.recommendations import apg_lookup


def test_apg_lookup_unknown_falls_back_to_generic() -> None:
    row = apg_lookup("UNKNOWN_PATTERN_XYZ")
    assert row["risk"] == "Low"
    assert "retenção" in row["action"].lower()
