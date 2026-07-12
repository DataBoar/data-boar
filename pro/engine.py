"""
Pro+ scanner wrapper with optional Rust pre-filter.

When Rust extension is unavailable, behavior falls back to Open Core pre-filter.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import Any

from core.prefilter import OpenCorePreFilter
from pro.worker_logic import basic_python_scan

try:
    from boar_fast_filter import FastFilter

    RUST_AVAILABLE = True
except Exception:
    FastFilter = None  # type: ignore[assignment]
    RUST_AVAILABLE = False

_worker_filter_instance: Any = None


class ProScanner:
    """
    Pro scanner facade that narrows candidate rows before deep scan.

    ``deep_scan_fn`` and ``legacy_scan_fn`` are injected so this wrapper remains
    framework-agnostic and testable.
    """

    def __init__(
        self,
        *,
        deep_scan_fn: Callable[[list[str]], Any] | None = None,
        legacy_scan_fn: Callable[[list[str]], Any] | None = None,
        profile_terms: Sequence[str] | None = None,
        profile_regexes: Sequence[str] | None = None,
    ) -> None:
        self._profile_signals_active = bool(profile_terms or profile_regexes)
        self._fallback = OpenCorePreFilter(
            profile_terms=profile_terms,
            profile_regexes=profile_regexes,
            recall_first_passthrough_on_profile=True,
        )
        self._deep_scan_fn = deep_scan_fn
        self._legacy_scan_fn = legacy_scan_fn
        self.fast_filter = FastFilter() if RUST_AVAILABLE and FastFilter else None

    def scan(self, data_batch: list[str]) -> Any:
        if self._profile_signals_active:
            if self._deep_scan_fn is None:
                return data_batch
            return self._deep_scan_fn(data_batch)
        if self.fast_filter is not None:
            suspect_indices = self.fast_filter.filter_batch(data_batch)
            filtered_data = [
                data_batch[i]
                for i in suspect_indices
                if isinstance(i, int) and 0 <= i < len(data_batch)
            ]
            if self._deep_scan_fn is None:
                return filtered_data
            return self._deep_scan_fn(filtered_data)

        filtered_data = self._fallback.filter_candidates(data_batch)
        if self._legacy_scan_fn is None:
            return filtered_data
        return self._legacy_scan_fn(filtered_data)


def process_chunk_worker(
    chunk: Sequence[str], profile_signals_active: bool = False
) -> list[str]:
    """
    Process worker entrypoint for ``ProcessPoolExecutor``.

    The Rust filter is lazily initialized inside each child process.

    Slice 3 — memory hygiene refactor (algorithmic efficiency only):

    The previous shape always materialized ``data_batch = [str(item) for
    item in chunk]`` even when ``chunk`` was already a ``list[str]`` (the
    common path: the orchestrator already coerces values to ``str`` in
    ``ProOrchestrator._row_to_payload``). For the recorded 200k profile
    (``tests/benchmarks/official_benchmark_200k.json``, Pro path at
    **0.574x** the OpenCore baseline) that copy was a per-chunk allocation
    we paid for nothing.

    Now we coerce only when the input is not already a ``list``-of-``str``
    — this preserves the contract for tuple / iterator / mixed-type inputs
    while skipping the redundant copy on the hot path. No precision,
    sample cap, timeout, or fallback predicate was changed.

    Doctrine: ``docs/ops/inspirations/DEFENSIVE_SCANNING_MANIFESTO.md`` §2
    (relief valves, not knobs) and ``THE_ART_OF_THE_FALLBACK.md`` §2
    (Rust path → Python fallback, no silent demotion).
    """
    global _worker_filter_instance

    # Cheap O(1) probe: when the orchestrator already produced a
    # ``list[str]`` (the documented hot path — see
    # ``ProOrchestrator._row_to_payload`` which calls ``str(value)`` per
    # column), we reuse the list directly and skip a per-chunk allocation.
    # For tuples, generators, or first-element-non-``str`` inputs we coerce
    # defensively so the downstream filter contract still holds. The probe
    # is O(1) — checking ``isinstance(chunk, list)`` and the first element
    # only — which is why this is a memory refactor and not a precision
    # change.
    if isinstance(chunk, list) and chunk and isinstance(chunk[0], str):
        data_batch: list[str] = chunk
    elif isinstance(chunk, list) and not chunk:
        data_batch = []
    else:
        data_batch = [str(item) for item in chunk]

    if _worker_filter_instance is None and RUST_AVAILABLE and FastFilter is not None:
        _worker_filter_instance = FastFilter()

    if profile_signals_active:
        return deep_ml_analysis(data_batch)

    if _worker_filter_instance is not None:
        suspect_indices = _worker_filter_instance.filter_batch(data_batch)
        suspects = [
            data_batch[i]
            for i in suspect_indices
            if isinstance(i, int) and 0 <= i < len(data_batch)
        ]
        return deep_ml_analysis(suspects)

    return deep_ml_analysis(basic_python_scan(data_batch))


def deep_ml_analysis(suspects: list[str]) -> list[str]:
    """
    Placeholder for heavier ML/DL stage in Pro+.

    Current implementation keeps candidates unchanged to preserve compatibility.
    """
    return suspects
