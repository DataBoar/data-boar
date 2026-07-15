import zipfile
from pathlib import Path

import pytest

from connectors.filesystem_connector import FilesystemConnector
from core.scanner import DataScanner

try:
    import py7zr  # noqa: F401

    HAS_PY7ZR = True
except ImportError:
    HAS_PY7ZR = False


class _DummyDB:
    def __init__(self) -> None:
        self.failures: list[tuple[str, str, str]] = []
        self.findings: list[dict] = []

    def save_failure(self, target_name: str, reason: str, details: str) -> None:
        self.failures.append((target_name, reason, details))

    def save_finding(self, *args, **kwargs) -> None:
        self.findings.append(kwargs)


def test_scan_compressed_off_does_not_scan_inside_archives(tmp_path):
    root = tmp_path / "root"
    root.mkdir()
    zip_path = root / "data.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("inner.txt", "CPF 123.456.789-00")

    db = _DummyDB()
    scanner = DataScanner()

    target = {"name": "FS", "type": "filesystem", "path": str(root), "recursive": True}
    connector = FilesystemConnector(
        target,
        scanner,
        db,
        extensions=[".zip"],
        scan_sqlite_as_db=False,
        sample_limit=5000,
        file_passwords={},
    )
    connector.run()

    # With scan_compressed False, we do not open the zip; no inner findings.
    inner_findings = [f for f in db.findings if "|" in f.get("file_name", "")]
    assert len(inner_findings) == 0


def test_scan_compressed_on_scans_inside_zip_and_reports_findings(tmp_path):
    root = tmp_path / "root"
    root.mkdir()
    zip_path = root / "data.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("inner.txt", "Contact: CPF 123.456.789-00 and email a@b.com")

    db = _DummyDB()
    scanner = DataScanner()

    target = {
        "name": "FS",
        "type": "filesystem",
        "path": str(root),
        "recursive": True,
        "file_scan": {
            "scan_compressed": True,
            "compressed_extensions": [".zip"],
        },
    }
    connector = FilesystemConnector(
        target,
        scanner,
        db,
        extensions=[".zip", ".txt"],
        scan_sqlite_as_db=False,
        sample_limit=5000,
        file_passwords={},
    )
    connector.run()

    inner_findings = [f for f in db.findings if "|" in f.get("file_name", "")]
    assert len(inner_findings) >= 1
    assert any("data.zip|" in f.get("file_name", "") for f in inner_findings)


def test_scan_compressed_sample_zip_in_data_dir():
    """Use the real sample under tests/data/compressed to validate Phase 4."""
    sample_dir = Path(__file__).resolve().parent / "data" / "compressed"
    sample_zip = sample_dir / "sample1.zip"
    if not sample_zip.exists():
        return  # skip if samples not present

    db = _DummyDB()
    scanner = DataScanner()

    target = {
        "name": "FS",
        "type": "filesystem",
        "path": str(sample_dir),
        "recursive": False,
        "file_scan": {
            "scan_compressed": True,
            "compressed_extensions": [".zip"],
        },
    }
    connector = FilesystemConnector(
        target,
        scanner,
        db,
        extensions=[".zip", ".txt", ".yaml", ".pdf"],
        scan_sqlite_as_db=False,
        sample_limit=10000,
        file_passwords={},
    )
    connector.run()

    inner_findings = [f for f in db.findings if "|" in f.get("file_name", "")]
    assert len(inner_findings) >= 1, (
        "expected at least one finding from inside sample1.zip"
    )


def test_7z_archive_handling_with_or_without_compressed_extra():
    """With [compressed] extra (py7zr) we scan .7z; without it we record archive_unsupported."""
    sample_dir = Path(__file__).resolve().parent / "data" / "compressed"
    sample_7z = sample_dir / "sample2.7z"
    if not sample_7z.exists():
        pytest.skip("tests/data/compressed/sample2.7z not present")

    db = _DummyDB()
    scanner = DataScanner()
    target = {
        "name": "FS",
        "type": "filesystem",
        "path": str(sample_dir),
        "recursive": False,
        "file_scan": {
            "scan_compressed": True,
            "compressed_extensions": [".7z", ".zip"],
        },
    }
    connector = FilesystemConnector(
        target,
        scanner,
        db,
        extensions=[".7z", ".txt", ".yaml"],
        scan_sqlite_as_db=False,
        sample_limit=10000,
        file_passwords={},
    )
    connector.run()

    unsupported_7z = [
        d
        for _, reason, d in db.failures
        if reason == "archive_unsupported" and d and "sample2.7z" in d
    ]
    if HAS_PY7ZR:
        assert len(unsupported_7z) == 0, "with py7zr installed, .7z should be opened"
    else:
        assert len(unsupported_7z) >= 1, (
            "without py7zr, .7z should yield archive_unsupported"
        )


def test_archive_budget_config_clamped_on_connector():
    """file_scan budget keys land on FilesystemConnector after loader clamp (#1233)."""
    from config.loader import normalize_config

    out = normalize_config(
        {
            "targets": [],
            "report": {"output_dir": "."},
            "file_scan": {
                "max_members": 500_000,  # above clamp → 100_000
                "max_total_uncompressed": 500,  # below → 1_000_000
                "max_expansion_ratio": 0.1,  # below → 1.0
            },
        }
    )
    assert out["file_scan"]["max_members"] == 100_000
    assert out["file_scan"]["max_total_uncompressed"] == 1_000_000
    assert out["file_scan"]["max_expansion_ratio"] == 1.0

    db = _DummyDB()
    connector = FilesystemConnector(
        {
            "name": "FS",
            "type": "filesystem",
            "path": ".",
            "file_scan": {
                "scan_compressed": True,
                "max_members": out["file_scan"]["max_members"],
                "max_total_uncompressed": out["file_scan"]["max_total_uncompressed"],
                "max_expansion_ratio": out["file_scan"]["max_expansion_ratio"],
            },
        },
        DataScanner(),
        db,
        extensions=[".txt"],
        scan_sqlite_as_db=False,
    )
    assert connector.max_members == 100_000
    assert connector.max_total_uncompressed == 1_000_000
    assert connector.max_expansion_ratio == 1.0


def test_scan_archive_at_path_applies_default_budgets_when_omitted(tmp_path):
    """Defaults apply even when caller omits budget kwargs (share connectors)."""
    from unittest.mock import MagicMock, patch

    from connectors.filesystem_connector import (
        DEFAULT_MAX_EXPANSION_RATIO,
        DEFAULT_MAX_MEMBERS,
        DEFAULT_MAX_TOTAL_UNCOMPRESSED,
        scan_archive_at_path,
    )

    zip_path = tmp_path / "d.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_STORED) as z:
        for i in range(5):
            z.writestr(f"m{i}.txt", "x")

    seen: dict = {}

    def _capture_iter(*args, **kwargs):  # type: ignore[no-untyped-def]
        seen.clear()
        seen.update(kwargs)
        return iter(())

    with patch(
        "connectors.filesystem_connector.iter_archive_members",
        side_effect=_capture_iter,
    ):
        scan_archive_at_path(
            archive_path=zip_path,
            archive_display_name=zip_path.name,
            target_name="T",
            path_display=str(tmp_path),
            scanner=MagicMock(),
            db_manager=_DummyDB(),
            extensions={".txt"},
            max_inner_size=None,
            file_passwords={},
            file_sample_max_chars=5000,
        )

    assert seen.get("max_members") == DEFAULT_MAX_MEMBERS
    assert seen.get("max_total_uncompressed") == DEFAULT_MAX_TOTAL_UNCOMPRESSED
    assert seen.get("max_expansion_ratio") == DEFAULT_MAX_EXPANSION_RATIO
