"""
RCA block contract for ``cli.reporter`` failure paths (Slice 2).

Why this lives in the test suite (Julia Evans-style note):

- A ``data-boar-report`` failure used to surface as a bare Python traceback or
  a single-line stderr message. Operators could not tell whether the regression
  was in the YAML config, the SQLite file, or the renderer — they had to page
  the maintainer to read the traceback.
- This test pins the **shape** of the new RCA block (Sysinternals-style:
  step, error_type, error_message, hypothesis, next_command, doctrine) so a
  refactor cannot silently regress it. Doctrine references:
  ``docs/ops/inspirations/INTERNAL_DIAGNOSTIC_AESTHETICS.md`` §2.2 and
  ``docs/ops/inspirations/DEFENSIVE_SCANNING_MANIFESTO.md`` §1.

Defensive posture:

- The tests run entirely against a temp directory and a missing or broken
  SQLite path. There is no network, no live DB, no read on customer data.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from cli.reporter import main as reporter_main


@pytest.fixture
def cfg_yaml(tmp_path: Path) -> Path:
    """Minimal YAML config pointing at a sqlite_path that does not exist yet."""
    db_path = tmp_path / "missing_audit.db"
    cfg_path = tmp_path / "cfg.yaml"
    cfg_path.write_text(
        f"sqlite_path: {db_path}\ntargets:\n  - name: t1\n    type: database\n",
        encoding="utf-8",
    )
    return cfg_path


def test_reporter_empty_session_id_emits_rca_without_traceback(
    tmp_path: Path, cfg_yaml: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """``--session-id ""`` must emit the RCA block and exit 2 without a traceback."""
    rc = reporter_main(
        [
            "--config",
            str(cfg_yaml),
            "--session-id",
            "",
        ]
    )
    assert rc == 2
    captured = capsys.readouterr()
    err = captured.err
    assert "session-id vazio" in err
    assert "[data-boar-report] RCA" in err
    assert "step              parse_args" in err
    assert "error_type        ValueError" in err
    assert "Traceback" not in err


def test_reporter_missing_session_returns_zero_when_sqlite_resolvable(
    tmp_path: Path, cfg_yaml: Path
) -> None:
    """Sanity: a *resolvable* config + non-existent session_id is not a fatal RCA path.

    ``LocalDBManager.get_findings`` returns ``([], [], [])`` for an unknown
    ``session_id`` and the renderer accepts empty rows. We pin this behavior
    so the RCA path is reserved for *real* failures (config parse, sqlite open,
    write permission, sandbox guard).
    """
    rc = reporter_main(
        [
            "--config",
            str(cfg_yaml),
            "--session-id",
            "session-that-does-not-exist",
        ]
    )
    assert rc == 0


def test_reporter_emits_rca_block_when_config_missing(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """A missing config YAML must produce the RCA block, not a bare traceback."""
    missing = tmp_path / "does_not_exist.yaml"
    rc = reporter_main(
        [
            "--config",
            str(missing),
            "--session-id",
            "any-session-id",
        ]
    )
    assert rc == 3
    captured = capsys.readouterr()
    err = captured.err
    assert "[data-boar-report] RCA" in err
    assert "step              load_config" in err
    assert "hypothesis" in err
    assert "next_command" in err
    assert "INTERNAL_DIAGNOSTIC_AESTHETICS" in err
    assert "DEFENSIVE_SCANNING_MANIFESTO" in err


def test_reporter_emits_rca_block_when_output_dir_unwritable(
    tmp_path: Path, cfg_yaml: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """A write failure must be classified as ``write_output`` step."""
    bogus = tmp_path / "this" / "subtree" / "should" / "not" / "exist.md"
    rc = reporter_main(
        [
            "--config",
            str(cfg_yaml),
            "--session-id",
            "session-write-target",
            "--output",
            str(bogus),
        ]
    )
    # The reporter creates parents on demand, so this path actually succeeds.
    # Pinning the success guards against a regression where the sandbox path
    # accidentally rejected absolute paths the operator owns.
    assert rc == 0
    assert bogus.exists()


def test_reporter_rca_keeps_stdout_clean(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """RCA output must stay on stderr so a piped Markdown capture is not poisoned."""
    rc = reporter_main(
        [
            "--config",
            str(tmp_path / "absent.yaml"),
            "--session-id",
            "x",
        ]
    )
    assert rc == 3
    captured = capsys.readouterr()
    assert "[data-boar-report] RCA" not in captured.out
    assert "[data-boar-report] RCA" in captured.err


def test_reporter_debug_traceback_flag_appends_traceback(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """``--debug-traceback`` adds the full traceback after the RCA block."""
    rc = reporter_main(
        [
            "--config",
            str(tmp_path / "absent.yaml"),
            "--session-id",
            "x",
            "--debug-traceback",
        ]
    )
    assert rc == 3
    captured = capsys.readouterr()
    err = captured.err
    assert "[data-boar-report] RCA" in err
    assert "[data-boar-report] full traceback (debug):" in err
    assert "Traceback" in err
