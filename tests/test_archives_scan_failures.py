"""#828 — archive member read failures must surface in scan_failures, not silent skip."""

import zipfile
from unittest.mock import MagicMock

import pytest

from connectors.filesystem_connector import FilesystemConnector, scan_archive_at_path
from core.archives import (
    SCAN_FAILURE_REASON_ENCRYPTED_NO_PASSWORD,
    SCAN_FAILURE_REASON_WRONG_PASSWORD,
    classify_7z_member_read_failure,
    classify_zip_member_read_failure,
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


def test_classify_zip_member_read_failure_encrypted_no_password():
    err = RuntimeError("File inner.txt is encrypted, password required for extraction")
    assert (
        classify_zip_member_read_failure(err, encrypted=True, password_provided=False)
        == SCAN_FAILURE_REASON_ENCRYPTED_NO_PASSWORD
    )


def test_classify_zip_member_read_failure_wrong_password():
    err = RuntimeError("Bad password for file 'inner.txt'")
    assert (
        classify_zip_member_read_failure(err, encrypted=True, password_provided=True)
        == SCAN_FAILURE_REASON_WRONG_PASSWORD
    )


def test_classify_zip_member_read_failure_bad_crc32_wrong_password():
    err = zipfile.BadZipFile("Bad CRC-32 for file 'inner.txt'")
    assert (
        classify_zip_member_read_failure(err, encrypted=True, password_provided=True)
        == SCAN_FAILURE_REASON_WRONG_PASSWORD
    )


def test_classify_7z_member_read_failure_password_required():
    pytest.importorskip("py7zr")
    from py7zr.exceptions import PasswordRequired

    assert (
        classify_7z_member_read_failure(PasswordRequired(), password_provided=False)
        == SCAN_FAILURE_REASON_ENCRYPTED_NO_PASSWORD
    )


def test_classify_7z_member_read_failure_crc_wrong_password():
    pytest.importorskip("py7zr")
    from py7zr.exceptions import CrcError

    assert (
        classify_7z_member_read_failure(
            CrcError(0, 1, "member.txt"), password_provided=True
        )
        == SCAN_FAILURE_REASON_WRONG_PASSWORD
    )
    assert (
        classify_7z_member_read_failure(
            OSError("crc check failed"), password_provided=True
        )
        == SCAN_FAILURE_REASON_WRONG_PASSWORD
    )


def test_scan_archive_at_path_inner_sample_uses_on_read_barrier(
    tmp_path, monkeypatch: pytest.MonkeyPatch
):
    """Encrypted PDF inside a zip must record scan_failures via on_read_barrier (#828)."""
    import connectors.filesystem_connector as fs_mod

    zip_path = tmp_path / "bundle.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("inner.pdf", b"%PDF-1.4")

    db = _DummyDB()
    scanner = MagicMock()
    scanner.scan_file_content.return_value = None

    def _capture_barrier_read(*_args, **kwargs):  # type: ignore[no-untyped-def]
        barrier = kwargs.get("on_read_barrier")
        if barrier is not None:
            barrier("encrypted_no_password", "encrypted inner pdf")
        return ""

    monkeypatch.setattr(fs_mod, "_read_text_sample", _capture_barrier_read)

    scan_archive_at_path(
        archive_path=zip_path,
        archive_display_name=zip_path.name,
        target_name="T",
        path_display=str(tmp_path),
        scanner=scanner,
        db_manager=db,
        extensions={".pdf"},
        max_inner_size=1_000_000,
        file_passwords={},
        file_sample_max_chars=5000,
    )

    encrypted = [
        f for f in db.failures if f[1] == SCAN_FAILURE_REASON_ENCRYPTED_NO_PASSWORD
    ]
    assert len(encrypted) == 1
    assert "bundle.zip|inner.pdf" in encrypted[0][2]


def test_scan_compressed_encrypted_zip_member_records_failure(
    tmp_path, monkeypatch: pytest.MonkeyPatch
):
    """Encrypted inner member without password must not masquerade as a clean archive scan."""
    root = tmp_path / "root"
    root.mkdir()
    zip_path = root / "locked.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("inner.txt", "CPF 123.456.789-00")

    original_getinfo = zipfile.ZipFile.getinfo

    def _encrypted_getinfo(self, name):  # type: ignore[no-untyped-def]
        info = original_getinfo(self, name)
        info.flag_bits = info.flag_bits | 0x1
        return info

    def _encrypted_read(self, name, pwd=None):  # type: ignore[no-untyped-def]
        raise RuntimeError(
            f"File {name!r} is encrypted, password required for extraction"
        )

    monkeypatch.setattr(zipfile.ZipFile, "getinfo", _encrypted_getinfo)
    monkeypatch.setattr(zipfile.ZipFile, "read", _encrypted_read)

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

    encrypted_failures = [
        f for f in db.failures if f[1] == SCAN_FAILURE_REASON_ENCRYPTED_NO_PASSWORD
    ]
    assert len(encrypted_failures) >= 1
    assert any("locked.zip" in f[2] for f in encrypted_failures)
    inner_findings = [f for f in db.findings if "|" in f.get("file_name", "")]
    assert len(inner_findings) == 0


def test_scan_archive_at_path_wrong_password_records_failure(
    tmp_path, monkeypatch: pytest.MonkeyPatch
):
    zip_path = tmp_path / "bad_pwd.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("inner.txt", "hello")

    db = _DummyDB()
    scanner = MagicMock()
    scanner.scan_file_content.return_value = None
    original_getinfo = zipfile.ZipFile.getinfo

    def _encrypted_getinfo(self, name):  # type: ignore[no-untyped-def]
        info = original_getinfo(self, name)
        info.flag_bits = info.flag_bits | 0x1
        return info

    def _bad_password_read(self, name, pwd=None):  # type: ignore[no-untyped-def]
        if getattr(self, "pwd", None):
            raise RuntimeError("Bad password for file 'inner.txt'")
        raise RuntimeError("File 'inner.txt' is encrypted, password required")

    monkeypatch.setattr(zipfile.ZipFile, "getinfo", _encrypted_getinfo)
    monkeypatch.setattr(zipfile.ZipFile, "read", _bad_password_read)

    scan_archive_at_path(
        archive_path=zip_path,
        archive_display_name=zip_path.name,
        target_name="T",
        path_display=str(tmp_path),
        scanner=scanner,
        db_manager=db,
        extensions={".txt"},
        max_inner_size=1_000_000,
        file_passwords={".zip": "wrong-secret"},
        file_sample_max_chars=5000,
    )

    wrong = [f for f in db.failures if f[1] == SCAN_FAILURE_REASON_WRONG_PASSWORD]
    assert len(wrong) >= 1
