"""CLI: enforced licensing block must exit cleanly, never with a traceback (#2188)."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

from core.engine import AuditEngine
from core.licensing.errors import LicenseBlockedError

_WHAT_TO_DO = (
    "What to do: Provide a valid license file and verify key "
    "(see docs/LICENSING_SPEC.md)."
)


def _run_main(monkeypatch: pytest.MonkeyPatch, argv: list[str]) -> None:
    import main as main_module

    monkeypatch.setattr(sys, "argv", ["main.py", *argv])
    main_module.main()


def _block_scan(monkeypatch: pytest.MonkeyPatch, state: str, message: str) -> None:
    def _raise(self, *args, **kwargs):
        raise LicenseBlockedError(state, message)

    monkeypatch.setattr(AuditEngine, "start_audit", _raise)


def _config(tmp_path: Path) -> Path:
    src = tmp_path / "data"
    src.mkdir()
    cfg = tmp_path / "c.yaml"
    cfg.write_text(
        f"""targets:
  - name: files-share
    type: filesystem
    path: {src.as_posix()}
report:
  output_dir: {tmp_path.as_posix()}
sqlite_path: {(tmp_path / "a.db").as_posix()}
api:
  port: 8765
scan:
  max_workers: 1
""",
        encoding="utf-8",
    )
    return cfg


def _assert_clean_block(capsys, state: str, message: str) -> None:
    err = capsys.readouterr().err
    assert f"Licensing: scan blocked ({state})." in err
    assert message in err
    assert _WHAT_TO_DO in err
    assert "Traceback" not in err


def test_demo_blocked_unlicensed_exits_2_without_traceback(monkeypatch, capsys):
    msg = "license blocked: missing_license_file"
    _block_scan(monkeypatch, "UNLICENSED", msg)
    with pytest.raises(SystemExit) as ei:
        _run_main(monkeypatch, ["--demo"])
    assert ei.value.code == 2
    _assert_clean_block(capsys, "UNLICENSED", msg)


def test_demo_blocked_expired_outside_grace_exits_2_without_traceback(
    monkeypatch, capsys
):
    msg = "license blocked: expired_outside_grace"
    _block_scan(monkeypatch, "EXPIRED_OUTSIDE_GRACE", msg)
    with pytest.raises(SystemExit) as ei:
        _run_main(monkeypatch, ["--demo"])
    assert ei.value.code == 2
    _assert_clean_block(capsys, "EXPIRED_OUTSIDE_GRACE", msg)


def test_oneshot_blocked_still_exits_2_with_same_text(monkeypatch, tmp_path, capsys):
    msg = "license blocked: missing_license_file"
    _block_scan(monkeypatch, "UNLICENSED", msg)
    with pytest.raises(SystemExit) as ei:
        _run_main(monkeypatch, ["--config", str(_config(tmp_path))])
    assert ei.value.code == 2
    _assert_clean_block(capsys, "UNLICENSED", msg)


def test_resume_blocked_still_exits_2_without_traceback(monkeypatch, tmp_path, capsys):
    """--resume must also exit cleanly when license blocks the scan (#2188)."""
    msg = "license blocked: license_blocked_state"
    _block_scan(monkeypatch, "UNLICENSED", msg)
    with pytest.raises(SystemExit) as ei:
        _run_main(
            monkeypatch,
            ["--config", str(_config(tmp_path)), "--resume", "some-session-id"],
        )
    assert ei.value.code == 2
    _assert_clean_block(capsys, "UNLICENSED", msg)
