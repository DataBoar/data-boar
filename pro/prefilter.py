"""
Pro+ pre-filter loader with graceful fallback.

Rust module is optional for now; when unavailable, we transparently reuse
Open Core filter so the pipeline stays functional.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from core.prefilter import OpenCorePreFilter, PreFilter


class ProPreFilter:
    """
    Pro+ candidate pre-filter facade.

    If a Rust extension is available, use it. Otherwise keep safe fallback to Open Core.
    """

    name = "pro_prefilter_auto_v1"

    def __init__(
        self,
        *,
        profile_terms: Sequence[str] | None = None,
        profile_regexes: Sequence[str] | None = None,
    ) -> None:
        self._profile_signals_active = bool(profile_terms or profile_regexes)
        self._fallback = OpenCorePreFilter(
            profile_terms=profile_terms,
            profile_regexes=profile_regexes,
            recall_first_passthrough_on_profile=True,
        )
        self._rust_impl = self._load_rust_impl()

    @staticmethod
    def _load_rust_impl() -> Any | None:
        """
        Lazy import of Rust extension function (future PyO3 module).

        Expected signature:
            fast_scan_buffer(payloads: list[str]) -> list[str]
        """
        try:
            from boar_fast_filter import FastFilter  # type: ignore

            return FastFilter()
        except Exception:
            return None

    def filter_candidates(self, payloads: list[str]) -> list[str]:
        if self._profile_signals_active:
            # Recall-first parity: custom profile signals loaded => do not eliminate rows.
            return list(payloads)
        if self._rust_impl is None:
            return self._fallback.filter_candidates(payloads)
        try:
            indexes = self._rust_impl.filter_batch(payloads)
            if isinstance(indexes, list):
                return [
                    payloads[i]
                    for i in indexes
                    if isinstance(i, int) and 0 <= i < len(payloads)
                ]
        except Exception:
            pass
        return self._fallback.filter_candidates(payloads)


def get_prefilter(
    *,
    enable_pro: bool = False,
    profile_terms: Sequence[str] | None = None,
    profile_regexes: Sequence[str] | None = None,
) -> PreFilter:
    """
    Return active pre-filter implementation.

    ``enable_pro=False`` keeps Open Core behavior; ``True`` tries Pro+ then fallback.
    """
    if enable_pro:
        return ProPreFilter(
            profile_terms=profile_terms,
            profile_regexes=profile_regexes,
        )
    return OpenCorePreFilter(
        profile_terms=profile_terms,
        profile_regexes=profile_regexes,
    )
