"""Lab-smoke #1332 false-positive fixture (#1371).

Reproduces CREDIT_CARD hits from space-joined INTEGER column samples (no real card
numbers). Primary acceptance uses ``xfail(strict=True)`` until #1332 lands: CI stays
green while the bug exists; XPASS(strict) forces marker removal when the fix ships.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from connectors.sample_value_dedup import join_distinct_sample
from core.scanner import DataScanner

_LAB_SMOKE_INIT = (
    Path(__file__).resolve().parents[1] / "deploy" / "lab-smoke-stack" / "init"
)
_ENGINES = ("postgres", "mariadb", "mssql", "oracle")
_FP_TABLE = "03_lab_fp_numeric_ids.sql"
_SAMPLE_LIMIT = 5

# Mirrors init/*/03_lab_fp_numeric_ids.sql row semantics (synthetic only).
_FP_COLUMN_VALUES: dict[str, list[int]] = {
    "id": [1001, 1002, 1003, 1004, 1005],
    "ref_a": [2001, 2002, 2003, 2004, 2005],
    "ref_b": [3001, 3002, 3003, 3004, 3005],
    "ref_c": [4001, 4002, 4003, 4004, 4005],
    "ctrl_3digit": [101, 102, 103, 104, 105],
    "ctrl_5digit": [10001, 10002, 10003, 10004, 10005],
}
_FP_TRIGGER_COLUMNS = ("id", "ref_a", "ref_b", "ref_c")
_FP_NEGATIVE_COLUMNS = ("ctrl_3digit", "ctrl_5digit")


def _pattern_has_credit_card(pattern_detected: str | None) -> bool:
    return "CREDIT_CARD" in (pattern_detected or "")


def _joined_sample(column: str, *, distinct_cap: int) -> str:
    return join_distinct_sample(_FP_COLUMN_VALUES[column], distinct_cap=distinct_cap)


def _scan_credit_card_hits(scanner: DataScanner, columns: tuple[str, ...]) -> int:
    hits = 0
    for column in columns:
        sample = _joined_sample(column, distinct_cap=_SAMPLE_LIMIT)
        result = scanner.scan_column(column, sample)
        if _pattern_has_credit_card(result.get("pattern_detected")):
            hits += 1
    return hits


def test_lab_fp_numeric_ids_sql_parity_across_engines() -> None:
    for engine in _ENGINES:
        path = _LAB_SMOKE_INIT / engine / _FP_TABLE
        assert path.is_file(), f"missing {path}"


# strict=True (unlike ad-hoc xfail elsewhere): XPASS must fail CI so the marker is removed with #1332.
@pytest.mark.xfail(
    strict=True,
    reason="falso-positivo por concatenacao de amostra — #1332",
)
def test_lab_fp_numeric_ids_credit_card_must_be_zero_after_1332_fix() -> None:
    """Target state for #1332 — xfail until join/sampling no longer crosses value boundaries."""
    scanner = DataScanner()
    hits = _scan_credit_card_hits(scanner, _FP_TRIGGER_COLUMNS)
    assert hits == 0, (
        f"lab_fp_numeric_ids must not report CREDIT_CARD on INTEGER columns "
        f"(expected 0, got {hits} on {_FP_TRIGGER_COLUMNS}); see #1332"
    )


def test_lab_fp_numeric_ids_negative_controls_never_credit_card() -> None:
    scanner = DataScanner()
    hits = _scan_credit_card_hits(scanner, _FP_NEGATIVE_COLUMNS)
    assert hits == 0


def test_lab_fp_numeric_ids_sample_limit_one_suppresses_credit_card_fp() -> None:
    scanner = DataScanner()
    sample = _joined_sample("id", distinct_cap=1)
    result = scanner.scan_column("id", sample)
    assert not _pattern_has_credit_card(result.get("pattern_detected"))


@pytest.mark.parametrize(
    ("column", "sample", "expected_pattern"),
    [
        ("national_id", "123.456.789-09", "LGPD_CPF"),
        ("contact_email", "audit.synthetic@example.invalid", "EMAIL"),
        (
            "comment_text",
            "Sem national_id; apenas texto operacional SKU-99999-X e telefone falso (21) 99999-0000.",
            "PHONE_BR",
        ),
        ("data_nascimento", "15/06/2015", "DOB_POSSIBLE_MINOR"),
    ],
)
def test_lab_smoke_corpus_core_patterns_remain_detected(
    column: str, sample: str, expected_pattern: str
) -> None:
    """Regression guard: #1332 fix must not blind the rest of the lab SQL corpus."""
    scanner = DataScanner()
    result = scanner.scan_column(column, sample)
    pattern = result.get("pattern_detected") or ""
    assert expected_pattern in pattern, (
        f"expected {expected_pattern} in pattern_detected, got {pattern!r}"
    )
