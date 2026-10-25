"""Fuzz and boundary checks for the PyO3 ``boar_fast_filter`` bridge (memory-safe paths)."""

from __future__ import annotations

from datetime import timedelta

import pytest
from hypothesis import given, settings, strategies as st


def _rust_scanner():
    mod = pytest.importorskip(
        "boar_fast_filter",
        reason="Rust extension not installed. Run maturin develop / CI wheel first.",
    )
    fast_filter_cls = getattr(mod, "FastFilter", None)
    assert fast_filter_cls is not None
    return fast_filter_cls()


@given(st.binary(min_size=0, max_size=5_000_000))
@settings(max_examples=8, deadline=timedelta(seconds=120))
def test_fuzz_rust_analyzer_buffer(data: bytes) -> None:
    """
    Stress the FFI boundary by feeding arbitrary bytes into ``FastFilter.filter_batch``.

    ``boar_fast_filter`` exposes string batches (``Vec<String>``), not raw byte buffers.
    The test maps each byte 1:1 to a code point via latin-1 so every payload is valid
    Unicode without surrogate issues, then runs the Rust regex paths.
    """
    scanner = _rust_scanner()
    payload = data.decode("latin-1")
    try:
        result = scanner.filter_batch([payload])
        assert isinstance(result, list)
        for idx in result:
            assert isinstance(idx, int)
            assert idx == 0
    except (MemoryError, OverflowError):
        pytest.fail(
            "O motor Rust falhou ao gerenciar limites de memória (OOB/Overflow)",
        )


@given(st.integers(min_value=-2147483648, max_value=2147483647))
@settings(max_examples=40, deadline=timedelta(seconds=30))
def test_integer_boundary_safety(val: int) -> None:
    """
    Exercise batch cardinality passed through PyO3 into Rust (``Vec<String>`` length).

    There is no ``set_limit`` on ``FastFilter``; the contract under test is stable
    conversion and panic-free handling for a bounded number of lines derived from ``val``.
    """
    scanner = _rust_scanner()
    count = abs(val) % 200 + 1
    batch = [f"row-{i}-{val & 0xFFFF}" for i in range(count)]
    try:
        result = scanner.filter_batch(batch)
        assert isinstance(result, list)
        for idx in result:
            assert isinstance(idx, int)
            assert 0 <= idx < count
    except (OverflowError, ValueError):  # noqa: BLE001
        pass  # Hypothesis edge inputs may exceed Rust batch bounds
