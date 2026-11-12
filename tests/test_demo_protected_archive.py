"""Demo scenario: password-protected 7z (#1447 demo v0, archive states from #828).

Without the password the archive is flagged in ``scan_failures``
(``encrypted_no_password``) and never reported as clean; with the demo password
in ``file_passwords`` the inner content is read and produces findings.

The py7zr-backed tests are *defined* only when the optional ``compressed`` extra
is installed, so they never count as skips (extras job skip ceiling, see #2233).
"""

from __future__ import annotations

import builtins
import contextlib
import importlib.util
import io
from pathlib import Path

from connectors.filesystem_connector import FilesystemConnector
from core.archives import SCAN_FAILURE_REASON_ENCRYPTED_NO_PASSWORD
from core.demo import synthetic_corpus as sc
from core.scanner import DataScanner

_SUBDIR = "9_protected_archive"


class _CaptureDB:
    def __init__(self) -> None:
        self.findings: list[dict] = []
        self.failures: list[tuple[str, str, str]] = []

    def save_failure(self, target_name: str, reason: str, details: str) -> None:
        self.failures.append((target_name, reason, details))

    def save_finding(self, *args, **kwargs) -> None:
        self.findings.append(kwargs)


def _generate(base: Path) -> Path:
    with contextlib.redirect_stdout(io.StringIO()):
        sc.generate_corpus(base, ["protected_archive"])
    return base / _SUBDIR


def _scan(root: Path, file_passwords: dict[str, str]) -> _CaptureDB:
    db = _CaptureDB()
    FilesystemConnector(
        {
            "name": "demo",
            "type": "filesystem",
            "path": str(root),
            "recursive": True,
            "file_scan": {"scan_compressed": True, "compressed_extensions": [".7z"]},
        },
        DataScanner(),
        db,
        extensions=[".7z", ".txt"],
        scan_sqlite_as_db=False,
        sample_limit=5000,
        file_passwords=file_passwords,
    ).run()
    return db


def test_protected_archive_scenario_is_registered_and_documented():
    """Scenario is selectable and its EXPECTED text documents the demo password."""
    assert "protected_archive" in sc.ALL_SCENARIOS
    assert sc.DEMO_ARCHIVE_PASSWORD in sc.EXPECTED[_SUBDIR]


def test_protected_archive_without_py7zr_skips_archive_but_keeps_note(
    tmp_path, monkeypatch
):
    """Without the optional extra the generator still succeeds (no .7z written)
    and leaves EXPECTED.txt explaining how to enable the scenario."""
    real_import = builtins.__import__

    def _no_py7zr(name, *args, **kwargs):  # type: ignore[no-untyped-def]
        if name == "py7zr":
            raise ImportError("py7zr not installed")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", _no_py7zr)
    out = _generate(tmp_path)
    assert not (out / sc.PROTECTED_ARCHIVE_NAME).exists()
    assert "compressed" in (out / "EXPECTED.txt").read_text(encoding="utf-8")


if importlib.util.find_spec("py7zr") is not None:

    def test_protected_archive_is_really_encrypted(tmp_path):
        import py7zr

        archive = _generate(tmp_path) / sc.PROTECTED_ARCHIVE_NAME
        assert archive.is_file()
        with py7zr.SevenZipFile(archive, "r") as z:
            assert z.needs_password()

    def test_protected_archive_without_password_is_flagged_not_clean(tmp_path):
        out = _generate(tmp_path)
        db = _scan(out, file_passwords={})
        flagged = [
            f
            for f in db.failures
            if f[1] == SCAN_FAILURE_REASON_ENCRYPTED_NO_PASSWORD
            and sc.PROTECTED_ARCHIVE_NAME in f[2]
        ]
        assert flagged, db.failures
        assert not [f for f in db.findings if "|" in str(f.get("file_name", ""))]

    def test_protected_archive_with_demo_password_yields_findings(tmp_path):
        out = _generate(tmp_path)
        db = _scan(out, file_passwords={".7z": sc.DEMO_ARCHIVE_PASSWORD})
        assert not [
            f for f in db.failures if f[1] == SCAN_FAILURE_REASON_ENCRYPTED_NO_PASSWORD
        ]
        inner = [
            f
            for f in db.findings
            if sc.PROTECTED_ARCHIVE_NAME in str(f.get("file_name", ""))
            and "|" in str(f.get("file_name", ""))
        ]
        assert inner, db.findings
        assert any("LGPD_CPF" in str(f.get("pattern_detected")) for f in inner)
