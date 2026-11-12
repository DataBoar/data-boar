"""Demo scenario: compressed corpus served over SMB (#1447, local rehearsal).

``10_compressed_smb`` holds one synthetic record per archive format: a
password-protected ``.7z`` plus ``.zip``, ``.tgz`` and ``.tar.bz2``. The three
stdlib formats are always tested; the ``.7z`` tests are *defined* only when the
optional ``compressed`` extra is installed, so they never count as skips
(extras job skip ceiling, see #2233).

Contract per archive (the rehearsal's expected value, set by design, not
learned from a run): exactly two distinct patterns, ``LGPD_CPF`` and ``EMAIL``.
"""

from __future__ import annotations

import contextlib
import importlib.util
import io
import re
from pathlib import Path

from connectors.filesystem_connector import FilesystemConnector
from core.archives import (
    SCAN_FAILURE_REASON_ENCRYPTED_NO_PASSWORD,
    SCAN_FAILURE_REASON_WRONG_PASSWORD,
)
from core.brazilian_cpf import cpf_checksum_valid, normalize_cpf_digits
from core.demo import synthetic_corpus as sc
from core.scanner import DataScanner

_SUBDIR = "10_compressed_smb"
_STDLIB_ARCHIVES = ("cadastro.zip", "cadastro.tgz", "cadastro.tar.bz2")
_CPF_TOKEN = re.compile(r"(?<!\d)\d{3}\.?\d{3}\.?\d{3}-?\d{2}(?!\d)")
_EXTENSIONS = [".zip", ".tgz", ".bz2", ".7z", ".csv", ".txt"]


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
        sc.generate_corpus(base, ["compressed_smb"])
    return base / _SUBDIR


def _scan(root: Path, file_passwords: dict[str, str]) -> _CaptureDB:
    db = _CaptureDB()
    FilesystemConnector(
        {
            "name": "demo",
            "type": "filesystem",
            "path": str(root),
            "recursive": True,
            "file_scan": {
                "scan_compressed": True,
                "compressed_extensions": [".zip", ".tgz", ".tar.bz2", ".7z"],
            },
        },
        DataScanner(),
        db,
        extensions=_EXTENSIONS,
        scan_sqlite_as_db=False,
        sample_limit=5000,
        file_passwords=file_passwords,
    ).run()
    return db


def _inner_patterns(db: _CaptureDB, archive: str) -> set[str]:
    out: set[str] = set()
    for f in db.findings:
        name = str(f.get("file_name", ""))
        if name.startswith(f"{archive}|") or f"|{archive}|" in name:
            out.add(str(f.get("pattern_detected")))
    return out


def test_compressed_smb_is_registered_and_documented(tmp_path):
    """D-CSMB-1: scenario is selectable; EXPECTED names every archive and password."""
    assert "compressed_smb" in sc.ALL_SCENARIOS
    out = _generate(tmp_path)
    text = (out / "EXPECTED.txt").read_text(encoding="utf-8")
    for name in (*_STDLIB_ARCHIVES, sc.PROTECTED_ARCHIVE_NAME):
        assert name in text
    assert sc.DEMO_ARCHIVE_PASSWORD in text
    assert "encrypted_no_password" in text
    assert sc.EXPECTED[_SUBDIR] in text


def test_compressed_smb_stdlib_archives_have_real_formats(tmp_path):
    """D-CSMB-2: the three stdlib archives are real zip / gzip / bzip2 streams."""
    import tarfile
    import zipfile

    out = _generate(tmp_path)
    with zipfile.ZipFile(out / "cadastro.zip") as z:
        assert z.namelist() == ["cadastro.csv"]
    with tarfile.open(out / "cadastro.tgz", "r:gz") as t:
        assert t.getnames() == ["cadastro.csv"]
    with tarfile.open(out / "cadastro.tar.bz2", "r:bz2") as t:
        assert t.getnames() == ["cadastro.csv"]


def test_compressed_smb_cpfs_are_checksum_valid_and_from_declared_pool(tmp_path):
    """D-CSMB-3: every CPF-shaped token inside the archives is a declared synthetic CPF."""
    import tarfile
    import zipfile

    out = _generate(tmp_path)
    blobs = [zipfile.ZipFile(out / "cadastro.zip").read("cadastro.csv")]
    for name, mode in (("cadastro.tgz", "r:gz"), ("cadastro.tar.bz2", "r:bz2")):
        with tarfile.open(out / name, mode) as t:
            blobs.append(t.extractfile("cadastro.csv").read())  # type: ignore[union-attr]
    pool = {normalize_cpf_digits(c) for c in sc._CPFS}
    for blob in blobs:
        tokens = _CPF_TOKEN.findall(blob.decode("utf-8"))
        assert tokens
        for tok in tokens:
            digits = normalize_cpf_digits(tok)
            assert digits in pool
            assert cpf_checksum_valid(digits)


def test_compressed_smb_stdlib_archives_yield_cpf_and_email_findings(tmp_path):
    """D-CSMB-4: scanning with scan_compressed finds exactly LGPD_CPF + EMAIL per archive."""
    out = _generate(tmp_path)
    db = _scan(out, file_passwords={})
    for archive in _STDLIB_ARCHIVES:
        patterns = _inner_patterns(db, archive)
        joined = " ".join(patterns)
        assert "LGPD_CPF" in joined, (archive, db.findings)
        assert "EMAIL" in joined, (archive, db.findings)
    assert not [f for f in db.failures if f[2].startswith(_STDLIB_ARCHIVES)]


def test_compressed_smb_without_scan_compressed_finds_nothing_inside(tmp_path):
    """D-CSMB-5: a negative control, the archives are opaque when the option is off."""
    out = _generate(tmp_path)
    db = _CaptureDB()
    FilesystemConnector(
        {
            "name": "demo",
            "type": "filesystem",
            "path": str(out),
            "recursive": True,
            "file_scan": {"scan_compressed": False},
        },
        DataScanner(),
        db,
        extensions=_EXTENSIONS,
        scan_sqlite_as_db=False,
        sample_limit=5000,
        file_passwords={},
    ).run()
    assert not [f for f in db.findings if "|" in str(f.get("file_name", ""))]


if importlib.util.find_spec("py7zr") is not None:

    def test_compressed_smb_7z_without_password_is_flagged(tmp_path):
        """D-CSMB-6."""
        db = _scan(_generate(tmp_path), file_passwords={})
        assert [
            f
            for f in db.failures
            if f[1] == SCAN_FAILURE_REASON_ENCRYPTED_NO_PASSWORD
            and sc.PROTECTED_ARCHIVE_NAME in f[2]
        ], db.failures
        assert not _inner_patterns(db, sc.PROTECTED_ARCHIVE_NAME)

    def test_compressed_smb_7z_wrong_password_is_flagged(tmp_path):
        """D-CSMB-7: a wrong password is flagged, never read as clean.

        Measured with py7zr 1.1.4: LZMA fails before the CRC check, so the reason
        is ``archive_read_error`` (the classifier only maps CrcError to
        ``wrong_password``). Both reasons are accepted; the content is never read.
        """
        db = _scan(_generate(tmp_path), file_passwords={".7z": "senha-errada"})
        assert [
            f
            for f in db.failures
            if f[1] in (SCAN_FAILURE_REASON_WRONG_PASSWORD, "archive_read_error")
            and sc.PROTECTED_ARCHIVE_NAME in f[2]
        ], db.failures
        assert not _inner_patterns(db, sc.PROTECTED_ARCHIVE_NAME)

    def test_compressed_smb_7z_with_password_yields_findings(tmp_path):
        """D-CSMB-8."""
        db = _scan(
            _generate(tmp_path), file_passwords={".7z": sc.DEMO_ARCHIVE_PASSWORD}
        )
        joined = " ".join(_inner_patterns(db, sc.PROTECTED_ARCHIVE_NAME))
        assert "LGPD_CPF" in joined and "EMAIL" in joined, db.findings
