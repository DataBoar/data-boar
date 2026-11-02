"""SSOT + FastFilter parity for CREDIT_CARD (#1984)."""

from __future__ import annotations

import re
from pathlib import Path

import pytest
import yaml

from core.detector import DEFAULT_PATTERNS
from core.scanner import DataScanner
from utils.luhn_card import CREDIT_CARD_PATTERN

_ROOT = Path(__file__).resolve().parents[1]
_RUST_LIB = _ROOT / "rust" / "boar_fast_filter" / "src" / "lib.rs"
_PCI_YAML = _ROOT / "docs" / "compliance-samples" / "compliance-sample-pci_dss.yaml"
_LGPD_YAML = _ROOT / "docs" / "compliance-samples" / "compliance-sample-lgpd.yaml"

_AMEX = "378282246310005"
_DINERS = "30569309025904"
_VISA = "4111111111111111"


def test_detector_uses_luhn_card_ssot() -> None:
    assert DEFAULT_PATTERNS["CREDIT_CARD"][0] == CREDIT_CARD_PATTERN


def test_rust_credit_card_pattern_matches_ssot() -> None:
    rust_src = _RUST_LIB.read_text(encoding="utf-8")
    # Match the Regex::new call with raw string literal, possibly split across lines.
    # The pattern may be formatted by cargo fmt as:
    #   let credit_card_pattern = Regex::new(
    #       r"....",
    #   )?;
    match = re.search(
        r"let credit_card_pattern = Regex::new\(\s*r\"([^\"]*)\"",
        rust_src,
        flags=re.DOTALL,
    )
    assert match is not None, "credit_card_pattern Regex::new missing in lib.rs"
    # The captured group may have escaped backslashes; compare after normalizing.
    rust_pattern = match.group(1)
    assert rust_pattern == CREDIT_CARD_PATTERN


def test_pci_pan_pattern_matches_ssot() -> None:
    data = yaml.safe_load(_PCI_YAML.read_text(encoding="utf-8"))
    pan = next(item for item in data["regex"] if item["name"] == "PAN")
    assert pan["pattern"] == CREDIT_CARD_PATTERN


def test_lgpd_credit_card_pattern_matches_ssot() -> None:
    data = yaml.safe_load(_LGPD_YAML.read_text(encoding="utf-8"))
    card = next(item for item in data["regex"] if item["name"] == "CREDIT_CARD")
    assert card["pattern"] == CREDIT_CARD_PATTERN


def test_fastfilter_does_not_drop_python_credit_card_hits() -> None:
    pytest.importorskip(
        "boar_fast_filter", reason="Run maturin develop for boar_fast_filter"
    )
    from boar_fast_filter import FastFilter

    samples = [
        _AMEX,
        "3782 822463 10005",
        _DINERS,
        "3056 9309 0259 04",
        _VISA,
        "4111\t1111\t1111\t1111",
        "4111\u00a01111\u00a01111\u00a01111",
    ]
    scanner = DataScanner()
    rust_filter = FastFilter()
    for sample in samples:
        result = scanner.scan_column("notes", sample)
        assert "CREDIT_CARD" in (result.get("pattern_detected") or ""), sample
        assert rust_filter.filter_batch([sample]) == [0], sample
