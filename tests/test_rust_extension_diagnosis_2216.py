"""#2216: when the Rust regex stage cannot load, the log and the diagnosis name the ABI and the cause."""

from __future__ import annotations

import logging
import sys
import tomllib
import types
from pathlib import Path

import pytest

import core.rust_regex_stage as rrs


def test_missing_module_is_reported_with_the_interpreter_tag(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setitem(sys.modules, "boar_fast_filter", None)  # import -> ImportError
    diag = rrs.rust_extension_diagnosis()
    assert diag["module_present"] is False
    assert diag["detail"] == "boar_fast_filter is not installed"
    assert diag["python_tag"].startswith(f"cp{sys.version_info.major}")


def test_module_without_regex_stage_engine_points_at_the_abi(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setitem(
        sys.modules, "boar_fast_filter", types.ModuleType("boar_fast_filter")
    )
    diag = rrs.rust_extension_diagnosis()
    assert diag["module_present"] is True
    assert "does not expose RegexStageEngine" in diag["detail"]


def test_free_threaded_interpreter_gets_the_cp314t_hint(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setitem(
        sys.modules, "boar_fast_filter", types.ModuleType("boar_fast_filter")
    )
    import sysconfig

    monkeypatch.setattr(
        sysconfig,
        "get_config_var",
        lambda name: 1 if name == "Py_GIL_DISABLED" else None,
    )
    diag = rrs.rust_extension_diagnosis()
    assert diag["free_threaded"] is True
    assert diag["python_tag"].endswith("t")
    assert "cp314t wheel" in diag["detail"]


def test_missing_extension_warns_once_with_reason_and_abi(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    monkeypatch.setitem(sys.modules, "boar_fast_filter", None)
    monkeypatch.setattr(rrs, "_missing_logged", False)
    with caplog.at_level(logging.WARNING, logger=rrs.logger.name):
        rrs._log_extension_missing_once()
        rrs._log_extension_missing_once()
    records = [r for r in caplog.records if "rust_extension_missing" in r.getMessage()]
    assert len(records) == 1  # once per process, not once per detector
    assert "python=cp" in records[0].getMessage()
    assert "not installed" in records[0].getMessage()


def test_cargo_manifest_keeps_abi3_as_default_and_allows_a_cp314t_build() -> None:
    """Default build stays one cp38-abi3 wheel; --no-default-features yields a per-interpreter wheel."""
    manifest = (
        Path(__file__).resolve().parents[1] / "rust" / "boar_fast_filter" / "Cargo.toml"
    )
    data = tomllib.loads(manifest.read_text(encoding="utf-8"))
    assert data["features"]["default"] == ["abi3"]
    assert data["features"]["abi3"] == ["pyo3/abi3-py38"]
    assert "abi3-py38" not in data["dependencies"]["pyo3"]["features"]
