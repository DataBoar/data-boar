"""Type stub for the optional compiled extension ``boar_fast_filter`` (#2186).

Pyright cannot see the PyO3 module built at runtime. This stub gives it the real
public surface (FastFilter, RegexStageEngine, __src_hash__) without disabling
reportMissingImports. Keep it in sync with rust/boar_fast_filter/src/lib.rs.
"""

from collections.abc import Sequence

__src_hash__: str

class FastFilter:
    def __init__(self) -> None: ...
    def filter_batch(self, batch: Sequence[str]) -> list[int]: ...

class RegexStageEngine:
    @staticmethod
    def compile_patterns(
        names: Sequence[str],
        patterns: Sequence[str],
        size_limit: int | None = None,
    ) -> "RegexStageEngine": ...
    def match_names(self, text: str) -> list[str]: ...

def guest_accepts_host_trust(trust_level: str) -> bool: ...
