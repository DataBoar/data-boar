"""Compare ``uv export`` requirements text across uv versions (#2228).

Skeleton: implemented in the next commit.
"""

from __future__ import annotations


def normalize_uv_export_text(text: str) -> str:
    raise NotImplementedError


def markers_equivalent(a: str, b: str) -> bool:
    raise NotImplementedError


def diff_requirements(committed: str, fresh: str) -> list[str]:
    raise NotImplementedError
