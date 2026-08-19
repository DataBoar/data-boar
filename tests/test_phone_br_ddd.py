"""PHONE_BR requires a Brazilian DDD/area code (#393)."""

from __future__ import annotations

import re
from pathlib import Path

from core.detector import DEFAULT_PATTERNS
from core.scanner import DataScanner

REPO_ROOT = Path(__file__).resolve().parents[1]
PHONE_BR_RE = re.compile(DEFAULT_PATTERNS["PHONE_BR"][0])


def test_phone_br_regex_requires_ddd_in_default_patterns() -> None:
    """Optional DDD group must not remain in the built-in pattern."""
    pat = DEFAULT_PATTERNS["PHONE_BR"][0]
    assert r"(?:\(?\d{2}\)?\s?)?" not in pat
    assert r"\(?\d{2}\)?" in pat


def test_phone_br_rejects_eight_and_nine_digit_ids() -> None:
    for sample in ("1234-5678", "98765-4321", "12345678"):
        assert PHONE_BR_RE.search(sample) is None, sample


def test_phone_br_matches_numbers_with_ddd() -> None:
    samples = (
        "(21) 99999-0000",
        "21 99999-0000",
        "(11)98765-4321",
        "+55 11 98765-4321",
        "11987654321",
    )
    for sample in samples:
        assert PHONE_BR_RE.search(sample), sample


def test_scanner_does_not_tag_order_id_as_phone_br() -> None:
    result = DataScanner().scan_column("order_ref", "1234-5678")
    pattern = result.get("pattern_detected") or ""
    assert "PHONE_BR" not in pattern


def test_scanner_still_tags_lab_smoke_phone_with_ddd() -> None:
    result = DataScanner().scan_column(
        "comment_text",
        "Sem national_id; apenas texto operacional SKU-99999-X e telefone falso (21) 99999-0000.",
    )
    pattern = result.get("pattern_detected") or ""
    assert "PHONE_BR" in pattern


def test_log_redaction_and_lgpd_sample_keep_phone_br_in_sync() -> None:
    pat = DEFAULT_PATTERNS["PHONE_BR"][0]
    validation = (REPO_ROOT / "core" / "validation.py").read_text(encoding="utf-8")
    sample = (
        REPO_ROOT / "docs" / "compliance-samples" / "compliance-sample-lgpd.yaml"
    ).read_text(encoding="utf-8")
    assert pat in validation
    yaml_pat = pat.replace("\\", "\\\\")
    assert yaml_pat in sample
