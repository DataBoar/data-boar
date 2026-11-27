"""OpenCorePreFilter vs ``FastFilter.filter_batch`` index parity (#2186).

After #1984 the Rust prefilter applies bounded CPF, e-mail, and Luhn-valid card
families. The Python Open Core prefilter must keep the same rows before fallback
or benchmark parity is meaningless.
"""

from __future__ import annotations

import importlib.util
import os

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
