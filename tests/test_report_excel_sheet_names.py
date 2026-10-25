"""Excel worksheet titles must be openpyxl-safe (#1113 demo exposed Praise sheet bug)."""

from report.generator import _SHEET_PRAISE_CONTROLS, _excel_safe_sheet_title


def test_praise_sheet_title_sanitizes_slash() -> None:
    raw = "Praise / existing controls"
    assert "/" not in _SHEET_PRAISE_CONTROLS
    assert _SHEET_PRAISE_CONTROLS == _excel_safe_sheet_title(raw)
    assert len(_SHEET_PRAISE_CONTROLS) <= 31
