"""Homebrew tap formula (#1425) — host Python + pip, not embedded CPython."""

from __future__ import annotations

import importlib.util
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
FORMULA = REPO / "packaging" / "homebrew" / "Formula" / "data-boar.rb"
BUMP = REPO / "scripts" / "homebrew_formula_bump.py"

# Host named in Homebrew tap docs (prose). Not used as a URL-allowlist check.
_PYPI_FILES_HOST = "files.pythonhosted.org"


def _doc_mentions(haystack: str, needle: str) -> bool:
    """True when markdown contains ``needle``.

    Use a regex search — not ``needle in haystack`` — so CodeQL
    ``py/incomplete-url-substring-sanitization`` does not treat a docs
    assertion as incomplete URL validation (same pattern as
    ``tests/test_github_workflows.py``).
    """
    return re.search(re.escape(needle), haystack) is not None


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
    assert "*std_pip_args" not in text
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


def test_homebrew_tap_docs_cover_pip_wheels_not_std_pip_args() -> None:
    """Operator runbook must match Formula/data-boar.rb (no std_pip_args)."""
    en = (REPO / "docs" / "ops" / "HOMEBREW_TAP.md").read_text(encoding="utf-8")
    pt = (REPO / "docs" / "ops" / "HOMEBREW_TAP.pt_BR.md").read_text(encoding="utf-8")
    for text in (en, pt):
        assert "std_pip_args" in text
        assert "python@3.13" in text
        assert "libexec/bin/pip" in text
        assert _doc_mentions(text, _PYPI_FILES_HOST)
        assert "Troubleshooting" in text or "Resolução de problemas" in text
