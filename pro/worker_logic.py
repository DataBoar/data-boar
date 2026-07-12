"""
Process worker helpers for Pro+ discovery orchestration.

This module is intentionally top-level and stateless-friendly so functions are
picklable by ``ProcessPoolExecutor``.

Doctrine references (Slice 3 latency refactor):

- ``docs/ops/inspirations/DEFENSIVE_SCANNING_MANIFESTO.md`` §2 — sample caps,
  statement timeouts, and dialect posture are **relief valves, not knobs**. We
  do not gain throughput by relaxing precision; we gain it by removing
  algorithmic and memory waste in the composition layer.
- ``docs/ops/inspirations/THE_ART_OF_THE_FALLBACK.md`` §2 — the Python fallback
  must not silently degrade. Same regex set, same Luhn validator, same
  acceptance contract as before; this refactor is **behavior-preserving**.
- ``docs/ops/inspirations/INTERNAL_DIAGNOSTIC_AESTHETICS.md`` §3 — one concept
  per line, no invented optimization labels.
"""

from __future__ import annotations

import re
from collections.abc import Sequence
from typing import Any

# Reuse the Open Core regex constants so the Pro fallback path applies the
# **same** CPF / email definitions as the baseline (single source of truth for
# "candidate shape"). The names are module-private in ``core.prefilter`` by
# convention — we import them here on purpose so any future tightening lands
# in one place and is picked up by both paths.
from core.prefilter import (  # noqa: PLC2701 - intentional cross-module reuse
    _CPF_CANDIDATE_RX,
    _EMAIL_CANDIDATE_RX,
)

try:
    from boar_fast_filter import FastFilter

    HAS_RUST = True
except Exception:
    FastFilter = None  # type: ignore[assignment]
    HAS_RUST = False

# Card-shape candidate (Luhn check is applied after this regex matches).
# Pattern is intentionally loose: it must match any 13-19 digit run with
# optional space or hyphen separators, so the Luhn validator decides
# acceptance. Tightening this regex risks dropping valid PANs and would
# violate the precision contract documented in the doctrine manifestos.
_CARD_PATTERN = re.compile(r"\b(?:\d[ -]?){13,19}\b")

_filter_instance: Any = None


def process_chunk_pro(
    chunk: Sequence[Any], profile_signals_active: bool = False
) -> list[str]:
    """
    Process one chunk in a worker process.

    - Pro path: Rust pre-filter (CPF/email/card+Luhn).
    - Open Core path: Python fallback candidate scan.

    The string-coercion list comprehension below is **kept on purpose**: chunks
    can arrive as tuples of arbitrary types from the orchestrator, and the
    downstream filter signatures are typed as ``list[str]``. The cost of this
    coercion is one allocation per chunk; that is intentional, not stale.
    """
    global _filter_instance
    data_strings = [str(row) for row in chunk]

    if HAS_RUST and _filter_instance is None and FastFilter is not None:
        _filter_instance = FastFilter()

    if profile_signals_active:
        return data_strings

    if HAS_RUST and _filter_instance is not None:
        suspect_indices = _filter_instance.filter_batch(data_strings)
        return [
            data_strings[i]
            for i in suspect_indices
            if isinstance(i, int) and 0 <= i < len(data_strings)
        ]

    return basic_python_scan(data_strings)


def basic_python_scan(payloads: list[str]) -> list[str]:
    """
    Open Core fallback that keeps CPF / email candidates plus Luhn-valid cards.

    Slice 3 — single-pass refactor (algorithmic efficiency only):

    The previous implementation walked ``payloads`` **twice**: once via
    :class:`~core.prefilter.OpenCorePreFilter` (CPF + email), then again to
    check Luhn-valid card numbers, with a ``set`` membership probe to avoid
    duplicates. The two-pass shape was the dominant tax in the
    ``tests/benchmarks/run_official_bench.py`` 200k profile, where the Pro
    Python fallback measured **0.574x** the throughput of the OpenCore
    baseline (``tests/benchmarks/official_benchmark_200k.json``).

    The new shape is a single pass, short-circuit ``or`` over the **same
    three predicates**:

    1. CPF candidate regex.
    2. Email candidate regex.
    3. Card-shape regex with Luhn validation.

    No regex was widened or narrowed. No sample cap was changed. No timeout,
    isolation level, or precision invariant was relaxed. The acceptance set
    is **identical** for any input — see ``tests/test_boar_orchestrator.py``
    and ``tests/test_basic_python_scan_single_pass_parity.py`` for parity
    pins.

    Memory: ``out`` grows in the same direction as before (filtered
    survivors). The previous helper allocated an extra ``list(candidates)``
    plus a ``set(candidates)`` for membership probing; both are gone in the
    fused loop.
    """
    # Hoist the bound-method lookups out of the comprehension. This is a
    # CPython micro-optimization that turns an attribute lookup per row
    # into a single local variable read; combined with the list
    # comprehension form (which avoids the per-row LOAD_METHOD + CALL on
    # ``out.append``) it removes the two largest allocation taxes from the
    # previous shape. Memory profile is strictly better than the prior
    # implementation, which materialized:
    #
    #     candidates = OpenCorePreFilter().filter_candidates(payloads)  # list
    #     out = list(candidates)                                        # copy
    #     known = set(candidates)                                       # hash set
    #
    # before the second loop. None of those intermediates exist anymore.
    cpf_search = _CPF_CANDIDATE_RX.search
    email_search = _EMAIL_CANDIDATE_RX.search
    has_card = _contains_luhn_valid_card
    return [
        value
        for value in payloads
        if value and (cpf_search(value) or email_search(value) or has_card(value))
    ]


def _contains_luhn_valid_card(value: str) -> bool:
    return any(_check_luhn(m.group(0)) for m in _CARD_PATTERN.finditer(value))


def _check_luhn(card_number: str) -> bool:
    digits = [int(ch) for ch in card_number if ch.isdigit()]
    if len(digits) < 13 or len(digits) > 19:
        return False
    total = 0
    for idx, digit in enumerate(reversed(digits)):
        if idx % 2 == 1:
            doubled = digit * 2
            total += doubled - 9 if doubled > 9 else doubled
        else:
            total += digit
    return total % 10 == 0
