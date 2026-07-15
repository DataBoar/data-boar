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


def test_archive_budget_max_members_stops_and_records_failure(tmp_path):
    """Many small members: stop at max_members; fail-closed with archive_budget_exceeded (#1233)."""
    from core.archives import (
        SCAN_FAILURE_REASON_ARCHIVE_BUDGET_EXCEEDED,
        iter_archive_members,
    )

    zip_path = tmp_path / "many.zip"
    n_members = 20
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_STORED) as z:
        for i in range(n_members):
            z.writestr(f"m{i:02d}.txt", f"payload-{i}")

    failures: list[tuple[str, str, str]] = []
    materialized: list[str] = []

    def _on_fail(reason: str, member: str, details: str) -> None:
        failures.append((reason, member, details))

    for name, _data in iter_archive_members(
        zip_path,
        "zip",
        max_inner_size=1_000_000,
        allowed_extensions={".txt"},
        on_member_read_failure=_on_fail,
        max_members=5,
        max_total_uncompressed=1_000_000_000,
        max_expansion_ratio=10_000.0,
    ):
        materialized.append(name)

    assert len(materialized) == 5
    assert len(materialized) < n_members
    assert any(r == SCAN_FAILURE_REASON_ARCHIVE_BUDGET_EXCEEDED for r, _, _ in failures)

    db = _DummyDB()
    scan_archive_at_path(
        archive_path=zip_path,
        archive_display_name=zip_path.name,
        target_name="T",
        path_display=str(tmp_path),
        scanner=MagicMock(scan_file_content=MagicMock(return_value=None)),
        db_manager=db,
        extensions={".txt"},
        max_inner_size=1_000_000,
        file_passwords={},
        file_sample_max_chars=5000,
        max_members=5,
        max_total_uncompressed=1_000_000_000,
        max_expansion_ratio=10_000.0,
    )
    budget = [
        f for f in db.failures if f[1] == SCAN_FAILURE_REASON_ARCHIVE_BUDGET_EXCEEDED
    ]
    assert len(budget) >= 1


def test_archive_budget_expansion_ratio_before_materialize(tmp_path):
    """High declared/compressed ratio trips before reading remaining members (#1233)."""
    from core.archives import (
        SCAN_FAILURE_REASON_ARCHIVE_BUDGET_EXCEEDED,
        iter_archive_members,
    )

    zip_path = tmp_path / "ratio.zip"
    # Highly compressible payloads → tiny archive, large declared uncompressed total.
    payload = b"0" * 200_000
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        for i in range(8):
            z.writestr(f"big{i}.txt", payload)

    compressed = zip_path.stat().st_size
    assert compressed > 0
    assert (8 * len(payload)) / compressed > 50

    failures: list[tuple[str, str, str]] = []
    materialized: list[str] = []

    def _on_fail(reason: str, member: str, details: str) -> None:
        failures.append((reason, member, details))

    for name, _data in iter_archive_members(
        zip_path,
        "zip",
        max_inner_size=10_000_000,
        allowed_extensions={".txt"},
        on_member_read_failure=_on_fail,
        max_members=1000,
        max_total_uncompressed=1_000_000_000,
        max_expansion_ratio=20.0,
    ):
        materialized.append(name)

    assert len(materialized) < 8
    assert any(r == SCAN_FAILURE_REASON_ARCHIVE_BUDGET_EXCEEDED for r, _, _ in failures)
    assert any("max_expansion_ratio" in d for _, _, d in failures)


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


# --- #1250 / #1248: real py7zr BytesIOFactory path (not ZipFile-.read lookalike) ---


def test_7z_iter_archive_members_roundtrip_yields_pii_content(tmp_path):
    """Unencrypted .7z: inner text is materialized (was AttributeError before #1250)."""
    pytest.importorskip("py7zr")
    import py7zr

    from core.archives import iter_archive_members

    seven = tmp_path / "pii.7z"
    payload = (
        b"Contact: demo.user@example.com\n"
        b"CPF 123.456.789-00 synthetic sample for archive read proof.\n"
    )
    with py7zr.SevenZipFile(seven, "w") as z:
        z.writestr(payload, "inner/doc.txt")

    got = list(
        iter_archive_members(
            seven,
            "7z",
            max_inner_size=1_000_000,
            allowed_extensions={".txt"},
        )
    )
    assert len(got) == 1
    name, data = got[0]
    assert name == "inner/doc.txt"
    assert b"123.456.789-00" in data
    assert b"demo.user@example.com" in data


def test_7z_iter_archive_members_multi_and_filters(tmp_path):
    """Multiple allowed members are read; disallowed ext / oversized skipped."""
    pytest.importorskip("py7zr")
    import py7zr

    from core.archives import iter_archive_members

    seven = tmp_path / "multi.7z"
    with py7zr.SevenZipFile(seven, "w") as z:
        z.writestr(b"one", "a.txt")
        z.writestr(b"two", "b.txt")
        z.writestr(b"skip-bin", "c.bin")
        z.writestr(b"X" * 5000, "huge.txt")

    got = {
        name: data
        for name, data in iter_archive_members(
            seven,
            "7z",
            max_inner_size=100,
            allowed_extensions={".txt"},
        )
    }
    assert set(got) == {"a.txt", "b.txt"}
    assert got["a.txt"] == b"one"
    assert got["b.txt"] == b"two"
    assert "c.bin" not in got
    assert "huge.txt" not in got


def test_7z_encrypted_without_password_is_encrypted_no_password(tmp_path):
    """Password-protected .7z without config password → encrypted_no_password, not archive_read_error."""
    pytest.importorskip("py7zr")
    import py7zr

    from core.archives import (
        SCAN_FAILURE_REASON_ARCHIVE_READ_ERROR,
        SCAN_FAILURE_REASON_ENCRYPTED_NO_PASSWORD,
        iter_archive_members,
    )

    seven = tmp_path / "locked.7z"
    with py7zr.SevenZipFile(seven, "w", password="correct-horse") as z:
        z.writestr(b"secret payload", "vault.txt")

    failures: list[tuple[str, str, str]] = []

    def _on_fail(reason: str, member: str, details: str) -> None:
        failures.append((reason, member, details))

    got = list(
        iter_archive_members(
            seven,
            "7z",
            max_inner_size=1_000_000,
            allowed_extensions={".txt"},
            file_passwords={},
            on_member_read_failure=_on_fail,
        )
    )
    assert got == []
    assert failures
    assert all(r == SCAN_FAILURE_REASON_ENCRYPTED_NO_PASSWORD for r, _, _ in failures)
    assert all(r != SCAN_FAILURE_REASON_ARCHIVE_READ_ERROR for r, _, _ in failures)
    assert not any("AttributeError" in d for _, _, d in failures)
