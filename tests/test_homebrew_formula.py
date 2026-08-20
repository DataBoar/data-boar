"""Homebrew tap formula (#1425) — host Python + pip, not embedded CPython."""

from __future__ import annotations

import importlib.util
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
FORMULA = REPO / "packaging" / "homebrew" / "Formula" / "data-boar.rb"
BUMP = REPO / "scripts" / "homebrew_formula_bump.py"


def _bump_mod():
    spec = importlib.util.spec_from_file_location("homebrew_formula_bump", BUMP)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_formula_is_host_python_pip_not_embed() -> None:
    text = FORMULA.read_text(encoding="utf-8")
    assert "class DataBoar < Formula" in text
    assert 'license "BSD-3-Clause"' in text
    assert 'depends_on "python@3.13"' in text
    assert "virtualenv_create" in text
    assert "pip" in text
    assert "data-boar --version" in text
    assert "--demo" in text
    assert "assert_path_exists" in text
    assert "assert File.exist?" not in text
    assert "/usr/lib/data-boar" not in text
    assert "python3.14t" not in text


def test_formula_url_sha256_parse_roundtrip() -> None:
    mod = _bump_mod()
    text = FORMULA.read_text(encoding="utf-8")
    ver, url, sha = mod.parse_formula(text)
    assert ver
    assert url.startswith("https://files.pythonhosted.org/")
    assert url.endswith(".tar.gz")
    assert len(sha) == 64
    rewritten = mod.render_formula(text, url, sha)
    assert rewritten == text
    other = mod.render_formula(
        text,
        "https://files.pythonhosted.org/packages/aa/bb/data_boar-9.9.9.tar.gz",
        "a" * 64,
    )
    assert (
        'url "https://files.pythonhosted.org/packages/aa/bb/data_boar-9.9.9.tar.gz"'
        in other
    )
    assert f'sha256 "{"a" * 64}"' in other


def test_bump_script_help() -> None:
    import subprocess
    import sys

    proc = subprocess.run(
        [sys.executable, str(BUMP), "--help"],
        check=True,
        capture_output=True,
        text=True,
    )
    assert "--write" in proc.stdout
    assert "--check" in proc.stdout
