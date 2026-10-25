"""FN reduction slice: configurable MEDIUM threshold, suggested review sheet, ID-like heuristic."""

from pathlib import Path

import pandas as pd
import pytest

from core.database import LocalDBManager
from core.scanner import DataScanner
from core.suggested_review import (
    SUGGESTED_REVIEW_NORM_TAG,
    SUGGESTED_REVIEW_PATTERN,
    column_name_suggests_identifier_review,
)
from report.generator import (
    _build_suggested_review_rows,
    _remove_suggested_review_from_main_sheets,
    generate_report,
)


@pytest.mark.parametrize(
    "name,expected",
    [
        ("customer_id", True),
        ("order_uuid", True),
        ("line_number", True),
        ("internal_num", True),
        ("id", False),
        ("ab", False),
        ("grid_layout", False),
        ("item_count", False),
    ],
)
def test_column_name_suggests_identifier_review(name: str, expected: bool) -> None:
    assert column_name_suggests_identifier_review(name) is expected


def test_medium_confidence_threshold_changes_ml_band() -> None:
    """With fixed ML proba, lowering MEDIUM threshold promotes borderline scores to MEDIUM."""
    s_hi = DataScanner(detection_config={"medium_confidence_threshold": 40})
    s_lo = DataScanner(detection_config={"medium_confidence_threshold": 35})
    for s in (s_hi, s_lo):
        assert s.detector._ml_available and s.detector._model is not None
        s.detector._model.predict_proba = lambda X: [[0.62, 0.38]]  # 38% -> int 38
    r_hi = s_hi.scan_column("neutral_col", "hello world")
    r_lo = s_lo.scan_column("neutral_col", "hello world")
    assert r_hi["sensitivity_level"] == "LOW"
    assert r_hi["ml_confidence"] == 38
    assert r_lo["sensitivity_level"] == "MEDIUM"
    assert r_lo["pattern_detected"] == "ML_POTENTIAL"


def test_medium_confidence_threshold_clamped() -> None:
    d = DataScanner(detection_config={"medium_confidence_threshold": 999}).detector
    assert d._medium_confidence_threshold == 69
    d2 = DataScanner(detection_config={"medium_confidence_threshold": -10}).detector
    assert d2._medium_confidence_threshold == 1


def test_report_suggested_review_sheet_and_not_duplicated_in_db_findings(
    tmp_path,
) -> None:
    db_path = str(tmp_path / "audit_sr.db")
    out_dir = str(tmp_path / "out_sr")
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    mgr = LocalDBManager(db_path)
    try:
        mgr.set_current_session_id("sess-sr")
        mgr.create_session_record("sess-sr")
        mgr.save_finding(
            "database",
            target_name="db1",
            server_ip="127.0.0.1",
            engine_details="postgresql",
            schema_name="public",
            table_name="t",
            column_name="legacy_uuid",
            data_type="varchar",
            sensitivity_level="LOW",
            pattern_detected=SUGGESTED_REVIEW_PATTERN,
            norm_tag=SUGGESTED_REVIEW_NORM_TAG,
            ml_confidence=12,
        )
        mgr.save_finding(
            "database",
            target_name="db1",
            column_name="cpf",
            sensitivity_level="HIGH",
            pattern_detected="LGPD_CPF",
            norm_tag="LGPD Art. 5",
            ml_confidence=99,
        )
        mgr.finish_session("sess-sr")
        path = generate_report(mgr, "sess-sr", output_dir=out_dir, config={})
        assert path is not None
        with pd.ExcelFile(path) as xl:
            assert "Suggested review (LOW)" in xl.sheet_names
            srd = pd.read_excel(xl, sheet_name="Suggested review (LOW)")
            assert len(srd) == 1
            assert srd.iloc[0]["Column"] == "legacy_uuid"
            dbdf = pd.read_excel(xl, sheet_name="Database findings")
        assert not (dbdf["pattern_detected"] == SUGGESTED_REVIEW_PATTERN).any()
    finally:
        mgr.dispose()


def test_suggested_review_rows_empty_when_sheet_disabled() -> None:
    """No Suggested review sheet data when report.include_suggested_review_sheet is false."""
    row = {
        "target_name": "t",
        "schema_name": "",
        "table_name": "",
        "column_name": "legacy_uuid",
        "data_type": "",
        "sensitivity_level": "LOW",
        "pattern_detected": SUGGESTED_REVIEW_PATTERN,
        "norm_tag": SUGGESTED_REVIEW_NORM_TAG,
        "ml_confidence": 5,
    }
    cfg_off = {"report": {"include_suggested_review_sheet": False}}
    assert _build_suggested_review_rows([row], [], cfg_off) == []


def test_remove_suggested_review_from_main_only_when_sheet_enabled() -> None:
    row = {
        "pattern_detected": SUGGESTED_REVIEW_PATTERN,
        "column_name": "x",
    }
    out_on, _, _ = _remove_suggested_review_from_main_sheets(
        [dict(row)], [], {"include_suggested_review_sheet": True}
    )
    assert out_on == []
    out_off, _, _ = _remove_suggested_review_from_main_sheets(
        [dict(row)], [], {"include_suggested_review_sheet": False}
    )
    assert len(out_off) == 1
