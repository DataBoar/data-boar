"""Unit tests for scripts/ci_pytest_skip_ceiling.py (#1638)."""

from __future__ import annotations

import py_compile
from pathlib import Path

import pytest

from scripts.ci_pytest_skip_ceiling import (
    DEFAULT_MAX_SKIPPED,
    evaluate,
    main,
    skipped_count,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "ci_pytest_skip_ceiling.py"


def test_skip_ceiling_script_compiles() -> None:
    py_compile.compile(str(SCRIPT), doraise=True)


def test_skip_ceiling_uses_defusedxml_not_stdlib_etree() -> None:
    """Bandit B314 / Semgrep use-defused-xml-parse: JUnit parse must use defusedxml."""
    text = SCRIPT.read_text(encoding="utf-8")
    assert "import defusedxml.ElementTree as ET" in text
    assert "xml.etree.ElementTree" not in text


def test_evaluate_within_and_over_ceiling() -> None:
    assert evaluate(0, 90) == 0
    assert evaluate(90, 90) == 0
    assert evaluate(91, 90) == 1


def test_skipped_count_from_testsuite_attribute(tmp_path: Path) -> None:
    report = tmp_path / "junit.xml"
    report.write_text(
        """<?xml version="1.0" encoding="utf-8"?>
<testsuite name="pytest" tests="10" skipped="4" failures="0" errors="0">
  <testcase classname="t" name="a"><skipped message="x"/></testcase>
</testsuite>
""",
        encoding="utf-8",
    )
    assert skipped_count(report) == 4


def test_skipped_count_outer_testsuites_wins(tmp_path: Path) -> None:
    report = tmp_path / "junit.xml"
    report.write_text(
        """<?xml version="1.0" encoding="utf-8"?>
<testsuites skipped="7">
  <testsuite name="pytest" tests="10" skipped="7" failures="0" errors="0"/>
</testsuites>
""",
        encoding="utf-8",
    )
    assert skipped_count(report) == 7


def test_skipped_count_fallback_counts_skipped_elements(tmp_path: Path) -> None:
    report = tmp_path / "junit.xml"
    report.write_text(
        """<?xml version="1.0" encoding="utf-8"?>
<testsuite name="pytest" tests="2">
  <testcase classname="t" name="a"><skipped message="x"/></testcase>
  <testcase classname="t" name="b"><skipped message="y"/></testcase>
</testsuite>
""",
        encoding="utf-8",
    )
    assert skipped_count(report) == 2


def test_main_passes_under_ceiling(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    report = tmp_path / "junit.xml"
    report.write_text(
        '<testsuite name="pytest" tests="3" skipped="2" failures="0" errors="0"/>',
        encoding="utf-8",
    )
    assert main([str(report), "--max-skipped", "5"]) == 0
    out = capsys.readouterr().out
    assert "skipped=2" in out


def test_main_fails_over_ceiling(tmp_path: Path) -> None:
    report = tmp_path / "junit.xml"
    report.write_text(
        '<testsuite name="pytest" tests="3" skipped="8" failures="0" errors="0"/>',
        encoding="utf-8",
    )
    assert main([str(report), "--max-skipped", "5"]) == 1


def test_main_missing_file(tmp_path: Path) -> None:
    missing = tmp_path / "nope.xml"
    assert main([str(missing)]) == 1


def test_default_ceiling_matches_ci_constant() -> None:
    """Keep DEFAULT_MAX_SKIPPED aligned with the extras job flag."""
    assert DEFAULT_MAX_SKIPPED == 90
    text = (REPO_ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    assert f"--max-skipped {DEFAULT_MAX_SKIPPED}" in text
