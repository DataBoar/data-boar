"""
Distinct-value sampling — deduplicate before applying the per-column cap (#1337).

Strategy **(b)**: fetch up to ``distinct_cap * multiplier`` rows with the existing
LIMIT/TOP/ROWNUM/SAMPLE SQL shape, then dedupe client-side and cap at ``distinct_cap``.
Query plans stay unchanged (no ``SELECT DISTINCT`` sort hazard on large heaps).

Strategy **(c)**: when ``estimated_row_count`` is known and does not exceed the fetch
budget, fetch only that many rows (no over-read on tiny tables).
"""

from __future__ import annotations

import os
from collections.abc import Iterable
from typing import Any

from connectors.sql_sampling import _HARD_MAX_SAMPLE, resolve_sql_sample_limit

_ENV_FETCH_MULTIPLIER = "DATA_BOAR_SAMPLE_FETCH_MULTIPLIER"
_DEFAULT_FETCH_MULTIPLIER = 10


def resolve_fetch_multiplier() -> int:
    """Multiplier for row fetch budget before client-side distinct cap."""
    raw = os.environ.get(_ENV_FETCH_MULTIPLIER, "").strip()
    if not raw:
        return _DEFAULT_FETCH_MULTIPLIER
    try:
        v = int(raw)
    except ValueError:
        return _DEFAULT_FETCH_MULTIPLIER
    return max(1, min(v, 100))


def resolve_fetch_row_budget(
    distinct_cap: int,
    *,
    estimated_row_count: int | None = None,
) -> int:
    """
    Rows to read from the source before distinct-value deduplication.

    - ``distinct_cap`` is clamped via :func:`resolve_sql_sample_limit`.
    - When ``estimated_row_count`` is set and ``<= distinct_cap * multiplier``, use
      the estimate (tiny tables — strategy **c**).
    - Otherwise ``min(distinct_cap * multiplier, _HARD_MAX_SAMPLE)``.
    """
    cap = resolve_sql_sample_limit(distinct_cap)
    mult = resolve_fetch_multiplier()
    budget = min(cap * mult, _HARD_MAX_SAMPLE)
    if (
        estimated_row_count is not None
        and estimated_row_count > 0
        and estimated_row_count < budget
    ):
        return max(1, estimated_row_count)
    return max(cap, budget)


def distinct_values_capped(
    raw_values: Iterable[Any],
    *,
    distinct_cap: int,
    max_value_len: int = 200,
) -> list[str]:
    """
    Preserve first-seen order; skip nulls; cap at ``distinct_cap`` unique strings.
    """
    lim = resolve_sql_sample_limit(distinct_cap)
    seen: set[str] = set()
    out: list[str] = []
    for raw in raw_values:
        if raw is None:
            continue
        s = str(raw)[:max_value_len]
        if s in seen:
            continue
        seen.add(s)
        out.append(s)
        if len(out) >= lim:
            break
    return out


def join_distinct_sample(
    raw_values: Iterable[Any],
    *,
    distinct_cap: int,
    max_value_len: int = 200,
) -> str:
    """Space-joined distinct sample string for detector input (not persisted)."""
    return " ".join(
        distinct_values_capped(
            raw_values, distinct_cap=distinct_cap, max_value_len=max_value_len
        )
    )
