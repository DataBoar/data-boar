"""Smoke and edge-case tests for optional Rust bridge ``boar_fast_filter`` (#390)."""

from __future__ import annotations

import time

import pytest

from pro.prefilter import ProPreFilter


def _fast_filter():
    mod = pytest.importorskip(
        "boar_fast_filter",
        reason="Rust extension not installed. Run maturin develop first.",
    )
    fast_filter_cls = getattr(mod, "FastFilter", None)
    assert fast_filter_cls is not None
    return fast_filter_cls()


def test_rust_bridge_fast_filter_batch() -> None:
    scanner = _fast_filter()
    data = [
        "123.456.789-00",
        "texto comum",
        "contato@empresa.com",
        "cartao valido 4111 1111 1111 1111",
        "cartao invalido 4111 1111 1111 1112",
    ] * 1000

    start = time.perf_counter()
    indices = scanner.filter_batch(data)
    elapsed = time.perf_counter() - start

    assert isinstance(indices, list)
    assert len(indices) == 3000
    # Keep as smoke threshold to avoid flaky CI on slower runners.
    assert elapsed < 2.0


def test_rust_bridge_filter_batch_empty() -> None:
    scanner = _fast_filter()
    assert scanner.filter_batch([]) == []


def test_rust_bridge_filter_batch_unicode_emoji() -> None:
    scanner = _fast_filter()
    batch = [
        "texto comum 😀 日本語 café",
        "contato@empresa.com 🎉",
        "sem PII — 🧬",
    ]
    indices = scanner.filter_batch(batch)
    assert isinstance(indices, list)
    assert 1 in indices
    assert 0 not in indices
    assert 2 not in indices


def test_rust_bridge_filter_batch_long_string() -> None:
    scanner = _fast_filter()
    long_clean = "x" * 100_000
    long_hit = ("y" * 50_000) + "contato@empresa.com" + ("z" * 50_000)
    indices = scanner.filter_batch([long_clean, long_hit])
    assert isinstance(indices, list)
    assert 0 not in indices
    assert 1 in indices


def test_pro_prefilter_fallback_when_rust_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Python path must still filter when the Rust extension is absent (#390)."""
    monkeypatch.setattr(ProPreFilter, "_load_rust_impl", staticmethod(lambda: None))
    pf = ProPreFilter()
    assert pf._rust_impl is None
    rows = ["clean", "mail beta@example.test"]
    assert pf.filter_candidates(rows) == ["mail beta@example.test"]
