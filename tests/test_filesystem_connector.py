"""Filesystem connector sampling (optional deps, legacy office paths)."""

from __future__ import annotations

import builtins
import sys
import types
from pathlib import Path

import pytest


@pytest.fixture(autouse=True)
def _clear_mammoth_module() -> object:
    sys.modules.pop("mammoth", None)
    yield
    sys.modules.pop("mammoth", None)


def test_doc_file_extracts_text_with_mammoth(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fake = types.ModuleType("mammoth")

    def _extract_raw_text(_fh: object) -> types.SimpleNamespace:
        return types.SimpleNamespace(value="CPF 123.456.789-09 dados cliente")

    fake.extract_raw_text = _extract_raw_text
    monkeypatch.setitem(sys.modules, "mammoth", fake)

    doc = tmp_path / "contrato.doc"
    doc.write_bytes(b"fake binary")

    from connectors.filesystem_connector import _read_text_sample

    text = _read_text_sample(doc, ".doc", 500, {})
    assert "CPF" in text
    assert "dados" in text


def test_doc_file_falls_back_when_mammoth_import_fails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    real_import = builtins.__import__

    def fake_import(
        name: str,
        globals_arg: dict[str, object] | None = None,
        locals_arg: dict[str, object] | None = None,
        fromlist: tuple[str, ...] = (),
        level: int = 0,
    ) -> object:
        if name == "mammoth":
            raise ImportError("no mammoth")
        return real_import(name, globals_arg, locals_arg, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", fake_import)

    doc = tmp_path / "contrato.doc"
    doc.write_bytes(b"fake binary")

    from connectors.filesystem_connector import _read_text_sample

    assert _read_text_sample(doc, ".doc", 500, {}) == ""


def test_doc_file_falls_back_on_mammoth_extract_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fake = types.ModuleType("mammoth")

    def _extract_raw_text(_fh: object) -> None:
        raise ValueError("bad doc")

    fake.extract_raw_text = _extract_raw_text
    monkeypatch.setitem(sys.modules, "mammoth", fake)

    doc = tmp_path / "broken.doc"
    doc.write_bytes(b"not-a-real-docx")

    from connectors.filesystem_connector import _read_text_sample

    assert _read_text_sample(doc, ".doc", 500, {}) == ""
