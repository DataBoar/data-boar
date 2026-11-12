"""SMB connector keeps the compound archive suffix (#1447 demo).

Measured on the demo share: ``cadastro.tar.bz2`` was spooled to a temp file named
``*.bz2`` because only ``Path(filename).suffix`` was used, so the archive reader
saw a single bz2 stream instead of a tar archive and the PII inside was silently
missed (no finding, no failure).
"""

from __future__ import annotations

import bz2
import gzip
import io
import tarfile
from unittest.mock import MagicMock, patch

import pytest

from connectors.smb_connector import SMBConnector


class _DB:
    def __init__(self) -> None:
        self.failures: list[tuple[str, str, str]] = []

    def save_failure(self, target_name: str, reason: str, details: str) -> None:
        self.failures.append((target_name, reason, details))

    def save_finding(self, *args, **kwargs) -> None:
        pass


def _tar_bytes() -> bytes:
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w") as tf:
        data = b"cpf 123.456.789-09"
        info = tarfile.TarInfo("inner.txt")
        info.size = len(data)
        tf.addfile(info, io.BytesIO(data))
    return buf.getvalue()


def _scan_names(filename: str, content: bytes) -> list[str]:
    seen: list[str] = []

    def _capture(**kwargs):
        seen.append(kwargs["archive_path"].name)

    mock_smb = MagicMock()
    mock_smb.walk.return_value = [("\\\\127.0.0.1\\corpus", [], [filename])]
    mock_smb.open_file.return_value.__enter__.return_value.read.return_value = content
    target = {
        "name": "smb-demo",
        "host": "127.0.0.1",
        "port": 4450,
        "share": "corpus",
        "user": "u",
        "pass": "unit-test-only",
        "allow_private_networks": True,
        "file_scan": {"scan_compressed": True},
    }
    with (
        patch("connectors.smb_connector._SMB_AVAILABLE", True),
        patch("connectors.smb_connector.smbclient", mock_smb),
        patch("connectors.smb_connector.scan_archive_at_path", side_effect=_capture),
    ):
        SMBConnector(
            target, scanner=MagicMock(), db_manager=_DB(), extensions=[".txt"]
        ).run()
    return seen


@pytest.mark.parametrize(
    ("filename", "content", "suffix"),
    [
        ("cadastro.tar.bz2", bz2.compress(_tar_bytes()), ".tar.bz2"),
        ("cadastro.tar.gz", gzip.compress(_tar_bytes()), ".tar.gz"),
        ("CADASTRO.TAR.GZ", gzip.compress(_tar_bytes()), ".tar.gz"),
        ("cadastro.tgz", gzip.compress(_tar_bytes()), ".tgz"),
        ("cadastro.zip", b"PK\x05\x06" + b"\0" * 18, ".zip"),
        ("notas.gz", gzip.compress(b"x"), ".gz"),
    ],
)
def test_temp_archive_keeps_compound_suffix(filename, content, suffix):
    names = _scan_names(filename, content)
    assert len(names) == 1, names
    assert names[0].endswith(suffix), names
