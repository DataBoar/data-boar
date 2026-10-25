"""Tests for scripts/social_x_thread_lengths.py (markdown thread block validation)."""

from __future__ import annotations

import subprocess
import sys
import textwrap
from pathlib import Path


def _run_script(drafts_dir: Path) -> int:
    repo = Path(__file__).resolve().parent.parent
    script = repo / "scripts" / "social_x_thread_lengths.py"
    return subprocess.run(
        [sys.executable, str(script), "--drafts-dir", str(drafts_dir)],
        cwd=repo,
        check=False,
    ).returncode


def test_social_x_thread_lengths_ok(tmp_path: Path) -> None:
    good = tmp_path / "2026-01-01_x_test_ok.md"
    good.write_text(
        textwrap.dedent(
            """
            ## Thread pronta

            ```
            short
            ```
            """
        ).strip(),
        encoding="utf-8",
    )
    assert _run_script(tmp_path) == 0


def test_social_x_thread_lengths_too_long(tmp_path: Path) -> None:
    long_body = "x" * 300
    bad = tmp_path / "2026-01-01_x_test_bad.md"
    bad.write_text(
        textwrap.dedent(
            f"""
            ## Thread pronta

            ```
            {long_body}
            ```
            """
        ).strip(),
        encoding="utf-8",
    )
    assert _run_script(tmp_path) == 1
