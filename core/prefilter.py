"""
Pre-filter contract and Open Core implementation.

Goal: reduce candidate payloads before expensive validation/ML without changing
the downstream raw findings contract.
"""

from __future__ import annotations

import re
from collections.abc import Sequence
from typing import Protocol, runtime_checkable

_CPF_CANDIDATE_RX = re.compile(r"\d{3}\D?\d{3}\D?\d{3}\D?\d{2}")
_EMAIL_CANDIDATE_RX = re.compile(r"[^\s@]+@[^\s@]+\.[^\s@]+")


@runtime_checkable
class PreFilter(Protocol):
    """Contract used by discovery/scanner layers (Open Core and Pro+)."""

    name: str

    def filter_candidates(self, payloads: list[str]) -> list[str]:
        """Return only strings likely to contain sensitive candidates."""


class OpenCorePreFilter:
    """
    Basic regex-based candidate filter (Open Core baseline).

    Keeps rows that look like CPF-shape or e-mail; all others are dropped before
    deeper validation.
    """

    name = "open_core_regex_prefilter_v1"

    def __init__(
        self,
        *,
        profile_terms: Sequence[str] | None = None,
        profile_regexes: Sequence[str] | None = None,
        recall_first_passthrough_on_profile: bool = False,
    ) -> None:
        self._profile_terms = tuple(
            t.strip().lower()
            for t in (profile_terms or [])
            if isinstance(t, str) and t.strip()
        )
        self._profile_regexes = tuple(self._compile_profile_regexes(profile_regexes))
        self._profile_signals_active = bool(
            self._profile_terms or self._profile_regexes
        )
        self._recall_first_passthrough_on_profile = bool(
            recall_first_passthrough_on_profile
        )

    def filter_candidates(self, payloads: list[str]) -> list[str]:
        if self._profile_signals_active and self._recall_first_passthrough_on_profile:
            # Recall-first contract: when profile signals are active and this prefilter
            # is used as an eliminating gate, pass all rows downstream.
            return list(payloads)
        out: list[str] = []
        for item in payloads:
            if self._looks_sensitive(item):
                out.append(item)
        return out

    @staticmethod
    def _compile_profile_regexes(
        profile_regexes: Sequence[str] | None,
    ) -> list[re.Pattern[str]]:
        out: list[re.Pattern[str]] = []
        for raw in profile_regexes or ():
            if not isinstance(raw, str):
                continue
            pattern = raw.strip()
            if not pattern:
                continue
            try:
                out.append(re.compile(pattern, re.IGNORECASE))
            except re.error:
                # Invalid profile regex should not break scanning.
                continue
        return out

    def _looks_sensitive(self, value: str) -> bool:
        if not value:
            return False
        if _CPF_CANDIDATE_RX.search(value) or _EMAIL_CANDIDATE_RX.search(value):
            return True
        lowered = value.lower()
        if any(term in lowered for term in self._profile_terms):
            return True
        return any(rx.search(value) for rx in self._profile_regexes)
