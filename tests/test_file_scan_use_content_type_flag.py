from __future__ import annotations

from pathlib import Path

from connectors.filesystem_connector import FilesystemConnector


class DummyScanner:
    def scan_file_content(self, *_args, **_kwargs):
        return None


class DummyDB:
    def save_failure(self, *_args, **_kwargs):
        pass

    def save_finding(self, *_args, **_kwargs):
        pass


def test_filesystem_connector_reads_use_content_type_flag() -> None:
    target_config = {
        "name": "fs-test",
        "path": ".",
        "recursive": False,
        "file_scan": {
            "scan_compressed": False,
            "use_content_type": True,
        },
    }
    connector = FilesystemConnector(
        target_config=target_config,
        scanner=DummyScanner(),
        db_manager=DummyDB(),
        extensions=[".txt"],
        scan_sqlite_as_db=False,
        sample_limit=1,
        file_sample_max_chars=1,
    )
    assert connector.use_content_type is True


def test_use_content_type_forces_pdf_extraction_when_enabled(
    tmp_path: Path, monkeypatch
) -> None:
    # Create a fake "PDF" file with .txt extension
    fake_pdf = tmp_path / "renamed.txt"
    fake_pdf.write_bytes(b"%PDF-1.4\n%mock\n")

    # Build a target config pointing to this directory
    target_config = {
        "name": "fs-test",
        "path": str(tmp_path),
        "recursive": False,
        "file_scan": {
            "scan_compressed": False,
            "use_content_type": True,
        },
    }

    # Stub scanner and DB to keep the run light
    class StubScanner:
        def scan_file_content(self, *_args, **_kwargs):
            return None

    class StubDB:
        def save_failure(self, *_args, **_kwargs):
            pass

        def save_finding(self, *_args, **_kwargs):
            pass

    # Capture which extension _read_text_sample is called with
    called_ext: list[str] = []

    def fake_read_text_sample(path: Path, ext: str, *_args, **_kwargs) -> str:  # type: ignore[override]
        called_ext.append(ext)
        return ""

    # Force infer_content_type to say "pdf" for our file
    monkeypatch.setattr(
        "connectors.filesystem_connector._read_text_sample",
        fake_read_text_sample,
        raising=True,
    )

    connector = FilesystemConnector(
        target_config=target_config,
        scanner=StubScanner(),
        db_manager=StubDB(),
        extensions=[".txt"],
        scan_sqlite_as_db=False,
        sample_limit=1,
        file_sample_max_chars=1,
    )

    connector.run()

    # We expect exactly one call and that the effective extension was forced to .pdf
    assert called_ext == [".pdf"]


def test_use_content_type_keeps_extension_when_disabled(
    tmp_path: Path, monkeypatch
) -> None:
    fake_pdf = tmp_path / "renamed.txt"
    fake_pdf.write_bytes(b"%PDF-1.4\n%mock\n")

    target_config = {
        "name": "fs-test",
        "path": str(tmp_path),
        "recursive": False,
        "file_scan": {
            "scan_compressed": False,
            "use_content_type": False,
        },
    }

    class StubScanner:
        def scan_file_content(self, *_args, **_kwargs):
            return None

    class StubDB:
        def save_failure(self, *_args, **_kwargs):
            pass

        def save_finding(self, *_args, **_kwargs):
            pass

    called_ext: list[str] = []

    def fake_read_text_sample(path: Path, ext: str, *_args, **_kwargs) -> str:  # type: ignore[override]
        called_ext.append(ext)
        return ""

    monkeypatch.setattr(
        "connectors.filesystem_connector._read_text_sample",
        fake_read_text_sample,
        raising=True,
    )

    connector = FilesystemConnector(
        target_config=target_config,
        scanner=StubScanner(),
        db_manager=StubDB(),
        extensions=[".txt"],
        scan_sqlite_as_db=False,
        sample_limit=1,
        file_sample_max_chars=1,
    )

    connector.run()

    # With the toggle off we should keep the original extension (.txt)
    assert called_ext == [".txt"]
