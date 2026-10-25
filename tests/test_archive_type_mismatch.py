"""Archive extension vs magic mismatch must surface in scan_failures (#1354 Part A)."""

from __future__ import annotations

from pathlib import Path

import pytest

from connectors.filesystem_connector import FilesystemConnector
from core.archives import (
    SCAN_FAILURE_REASON_ARCHIVE_TYPE_MISMATCH,
    describe_archive_type_mismatch,
)
from core.scanner import DataScanner


class _DummyDB:
    def __init__(self) -> None:
        self.failures: list[tuple[str, str, str]] = []
        self.findings: list[dict] = []

    def save_failure(self, target_name: str, reason: str, details: str) -> None:
        self.failures.append((target_name, reason, details))

    def save_finding(self, *args, **kwargs) -> None:
        self.findings.append(kwargs)


def test_describe_archive_type_mismatch_tar_bz2_with_gzip_bytes():
    sample_dir = Path(__file__).resolve().parent / "data" / "compressed"
    sample3 = sample_dir / "sample3.tgz"
    sample4 = sample_dir / "sample4.tar.bz2"
    if not sample3.is_file() or not sample4.is_file():
        pytest.skip("compressed samples not present")
    assert sample3.read_bytes() == sample4.read_bytes()

    mismatch = describe_archive_type_mismatch(sample4)
    assert mismatch is not None
    assert "extension=tar.bz2" in mismatch
    assert "magic=gzip" in mismatch
    assert describe_archive_type_mismatch(sample3) is None


def test_scan_compressed_records_archive_type_mismatch_for_sample4():
    sample_dir = Path(__file__).resolve().parent / "data" / "compressed"
    sample3 = sample_dir / "sample3.tgz"
    sample4 = sample_dir / "sample4.tar.bz2"
    if not sample3.is_file() or not sample4.is_file():
        pytest.skip("compressed samples not present")

    db = _DummyDB()
    scanner = DataScanner()
    target = {
        "name": "FS",
        "type": "filesystem",
        "path": str(sample_dir),
        "recursive": False,
        "file_scan": {"scan_compressed": True},
    }
    connector = FilesystemConnector(
        target,
        scanner,
        db,
        extensions=[".tgz", ".tar.bz2", ".txt", ".yaml", ".pdf"],
        scan_sqlite_as_db=False,
        sample_limit=10000,
        file_passwords={},
    )
    connector.run()

    mismatches = [
        f for f in db.failures if f[1] == SCAN_FAILURE_REASON_ARCHIVE_TYPE_MISMATCH
    ]
    assert mismatches, "expected archive_type_mismatch for mislabeled sample4.tar.bz2"

    sample3_inner = [f for f in db.findings if "sample3.tgz|" in f.get("file_name", "")]
    assert len(sample3_inner) >= 1, "sample3.tgz should expand and yield inner findings"

    sample4_plain = [f for f in db.findings if f.get("file_name") == "sample4.tar.bz2"]
    assert not sample4_plain, (
        "mislabeled archive should not be scanned as a plain file when mismatch is recorded"
    )


def test_use_content_type_does_not_expand_mislabeled_archive():
    """#1354 option (b): use_content_type does not dispatch compressed archives."""
    sample_dir = Path(__file__).resolve().parent / "data" / "compressed"
    sample4 = sample_dir / "sample4.tar.bz2"
    if not sample4.is_file():
        pytest.skip("compressed samples not present")

    db = _DummyDB()
    scanner = DataScanner()
    target = {
        "name": "FS",
        "type": "filesystem",
        "path": str(sample_dir),
        "recursive": False,
        "file_scan": {"scan_compressed": True, "use_content_type": True},
    }
    connector = FilesystemConnector(
        target,
        scanner,
        db,
        extensions=[".tgz", ".tar.bz2", ".txt", ".yaml", ".pdf"],
        scan_sqlite_as_db=False,
        sample_limit=10000,
        file_passwords={},
    )
    connector.run()

    mismatches = [
        f for f in db.failures if f[1] == SCAN_FAILURE_REASON_ARCHIVE_TYPE_MISMATCH
    ]
    assert mismatches, (
        "use_content_type must not expand sample4; still archive_type_mismatch"
    )
    sample4_inner = [
        f for f in db.findings if "sample4.tar.bz2|" in f.get("file_name", "")
    ]
    assert not sample4_inner, "mislabeled archive must not yield inner members"
