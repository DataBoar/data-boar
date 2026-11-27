"""OpenCorePreFilter vs ``FastFilter.filter_batch`` index parity (#2186).

After #1984 the Rust prefilter applies bounded CPF, e-mail, and Luhn-valid card
families. The Python Open Core prefilter must keep the same rows before fallback
or benchmark parity is meaningless.
"""

from __future__ import annotations

import hashlib
import importlib.util
import os
from pathlib import Path

import pytest

from core.prefilter import OpenCorePreFilter

# Two environments (#2186): GitHub CI has no maturin build, so a missing extension
# stays a declared skip there. Local/Buildbot runs export BOAR_REQUIRE_RUST=1 via
# scripts/check-all.sh (cicatrix: the parity test used to skip silently there), so the
# same missing extension must FAIL LOUD instead of hiding the parity regression.
if importlib.util.find_spec("boar_fast_filter") is None:
    if os.environ.get("BOAR_REQUIRE_RUST") == "1":
        pytest.fail(
            "boar_fast_filter is missing with BOAR_REQUIRE_RUST=1; the #2186 "
            "parity test must not skip silently. Rebuild with: uv run maturin "
            "develop --release --manifest-path rust/boar_fast_filter/Cargo.toml",
            pytrace=False,
        )
    pytest.skip(
        "boar_fast_filter not built; parity runs in Buildbot (#2186)",
        allow_module_level=True,
    )

boar_fast_filter = importlib.import_module("boar_fast_filter")

# A present-but-STALE compiled extension must not pass silently: build.rs bakes the
# sha256 of these same files into the module at compile time. The frame (relative
# path, NUL, bytes, NUL) must match rust/boar_fast_filter/build.rs byte for byte.
_CRATE_ROOT = Path(__file__).resolve().parents[1] / "rust" / "boar_fast_filter"


def _crate_source_hash() -> str:
    src = _CRATE_ROOT / "src"
    rel_paths = [
        "Cargo.toml",
        *(p.relative_to(_CRATE_ROOT).as_posix() for p in src.rglob("*.rs")),
    ]
    digest = hashlib.sha256()
    for rel in sorted(rel_paths):
        digest.update(rel.encode("utf-8"))
        digest.update(b"\0")
        digest.update((_CRATE_ROOT / rel).read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


if os.environ.get("BOAR_REQUIRE_RUST") == "1":
    _expected = _crate_source_hash()
    _actual = getattr(boar_fast_filter, "__src_hash__", None)
    if _actual != _expected:
        pytest.fail(
            f"boar_fast_filter is STALE: compiled __src_hash__={_actual!r}, "
            f"source sha256={_expected!r}. Rebuild with: uv run maturin develop "
            "--release --manifest-path rust/boar_fast_filter/Cargo.toml",
            pytrace=False,
        )

# (line, kept_by_contract)
_PREFILTER_PARITY_LINES: list[tuple[str, bool]] = [
    ("4111 1111 1111 1111", True),
    ("4111-1111-1111-1111", True),
    ("4111111111111111", True),
    ("4532 1123 4456 7789", False),
    ("4532112344567789", False),
    ("123.456.789-00", True),
    ("12345678900", True),
    ("123 456 789 00", True),
    ("cpf:123/456/789/00", True),
    ("email@teste.com", True),
    ("maria@domínio.com.br", True),
    ("378282246310005", True),
    ("3782 822463 10005", True),
    ("30569309025904", True),
    ("3056 9309 0259 04", True),
    ("apenas texto sem sinais", False),
    ("prefix12345678901suffix", False),
]


def _python_kept_indices(batch: list[str]) -> list[int]:
    scanner = OpenCorePreFilter()
    out: list[int] = []
    for idx, line in enumerate(batch):
        if scanner.filter_candidates([line]):
            out.append(idx)
    return out


def _rust_kept_indices(batch: list[str]) -> list[int]:
    from boar_fast_filter import FastFilter

    return FastFilter().filter_batch(batch)


@pytest.mark.parametrize("line,expected_kept", _PREFILTER_PARITY_LINES)
def test_prefilter_line_contract(line: str, expected_kept: bool) -> None:
    batch = [line]
    rust_ix = _rust_kept_indices(batch)
    python_ix = _python_kept_indices(batch)
    assert (len(rust_ix) == 1) == expected_kept, (line, rust_ix)
    assert (len(python_ix) == 1) == expected_kept, (line, python_ix)
    assert rust_ix == python_ix


def test_prefilter_full_corpus_index_parity() -> None:
    batch = [line for line, _ in _PREFILTER_PARITY_LINES]
    rust_ix = _rust_kept_indices(batch)
    python_ix = _python_kept_indices(batch)
    assert rust_ix == python_ix, (rust_ix, python_ix, batch)


def test_generate_test_data_hit_parity() -> None:
    from tests.benchmarks.run_official_bench import generate_test_data

    data = generate_test_data(200_000)
    rust_ix = _rust_kept_indices(data)
    python_ix = _python_kept_indices(data)
    assert rust_ix == python_ix
