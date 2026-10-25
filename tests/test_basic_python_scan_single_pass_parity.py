"""
Parity guard for the Slice 3 single-pass refactor of ``basic_python_scan``.

Why this lives in the test suite (Julia Evans-style note):

- Slice 3 fused two passes (OpenCore prefilter + Luhn loop) into a single
  pass over ``payloads`` for algorithmic efficiency. The dominant cost in the
  recorded ``tests/benchmarks/official_benchmark_200k.json`` profile (Pro at
  **0.574x** the OpenCore baseline) was redundant iteration plus the
  ``set`` membership probe used to deduplicate hits.
- Because the refactor is intentionally **behavior-preserving**, this test
  pins the **acceptance set** of the new shape against:

  1. The Open Core ``OpenCorePreFilter`` baseline (CPF + email rows must be
     a strict subset of the new output, regardless of insertion order).
  2. A Luhn-validated card row that the OpenCore filter alone never accepted.
  3. An empty / whitespace row, which must never appear in the survivors.

- If a future PR widens, narrows, or reorders the predicates in
  ``basic_python_scan``, one of these assertions will surface the change so
  the operator and reviewers see it explicitly. Doctrine: ``THE_ART_OF_THE_FALLBACK``
  forbids silent demotions; this is its machine-readable echo.

Defensive posture (DEFENSIVE_SCANNING_MANIFESTO spirit):

- Pure-Python, in-process, no DB connection, no ``sqlite3`` writes, no file
  locks. Safe to run alongside any other test or even a live scan.
"""

from __future__ import annotations

from core.prefilter import OpenCorePreFilter
from pro.worker_logic import basic_python_scan

# Card numbers chosen for deterministic Luhn behaviour:
# ``4111 1111 1111 1111`` is the canonical Luhn-valid PAN used in payment
# fixtures across the industry; the trailing-digit variant (``...1112``) is
# Luhn-invalid by exactly one digit, so it must never enter the output.
_LUHN_VALID_CARD = "4111 1111 1111 1111"
_LUHN_INVALID_CARD = "4111 1111 1111 1112"


def test_single_pass_keeps_opencore_subset() -> None:
    """OpenCore-accepted CPF/email rows survive the fused predicate."""
    payloads = [
        "safe text",
        "cpf 390.533.447-05",
        "email ops@example.test",
        "  ",
        "",
        "another clean cell",
        f"card {_LUHN_VALID_CARD}",
        f"invalid {_LUHN_INVALID_CARD}",
    ]
    new_out = basic_python_scan(payloads)
    open_core_out = OpenCorePreFilter().filter_candidates(payloads)

    # All OpenCore survivors must remain in the new output. We compare as
    # sets to keep this assertion order-agnostic; the previous two-pass
    # implementation appended Luhn cards after the prefilter pass, so the
    # tail order changed deliberately.
    assert set(open_core_out).issubset(set(new_out))
    assert "safe text" not in new_out
    assert "another clean cell" not in new_out
    assert "" not in new_out
    assert "  " not in new_out


def test_single_pass_admits_luhn_card_only_when_valid() -> None:
    """The Luhn predicate behaves as the third member of the fused ``or`` chain."""
    valid_row = f"transaction card={_LUHN_VALID_CARD}"
    invalid_row = f"declined card={_LUHN_INVALID_CARD}"
    out = basic_python_scan([valid_row, invalid_row])
    assert valid_row in out
    assert invalid_row not in out


def test_single_pass_does_not_duplicate_rows_with_multiple_signals() -> None:
    """A row that hits two predicates must appear at most once.

    The previous two-pass shape used ``set(candidates)`` for membership
    probing; the fused loop uses short-circuit ``or`` so a single row can
    only be appended once even when both CPF and Luhn signals match.
    """
    row = f"cpf 390.533.447-05 with PAN {_LUHN_VALID_CARD}"
    out = basic_python_scan([row, row])
    # Both copies are independent inputs, but each must appear *exactly*
    # once per input (no de-duplication, no tripling).
    assert out.count(row) == 2


def test_single_pass_short_circuits_on_empty_input() -> None:
    """An empty list returns an empty list — no exceptions, no allocations leak."""
    assert basic_python_scan([]) == []


def test_single_pass_handles_long_clean_corpus_without_growth() -> None:
    """A 5_000-row clean corpus must yield zero survivors.

    This pins that the early-exit ``if not value: continue`` plus the
    short-circuit predicate chain do not accidentally append anything for
    rows that match none of the three signals.
    """
    payloads = ["clean payload " + str(i) for i in range(5_000)]
    out = basic_python_scan(payloads)
    assert out == []
