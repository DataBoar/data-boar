"""
Hierarchical SQL column sample limits (convention over configuration + escape hatch).

Precedence for the default per-column cap (before ``DATA_BOAR_SQL_SAMPLE_LIMIT`` and
``resolve_sql_sample_limit``):

1. Per-table override under ``sql_sampling.overrides.targets.<target_name>.tables``.
2. Per-target ``sample_limit`` under the same target block.
3. First ``fnmatch`` match in ``sql_sampling.overrides.patterns`` (glob on table name).
4. ``file_scan.sample_limit`` (passed in as ``global_limit``).

Explicit ``sample(..., limit=...)`` in connectors still wins for that call (minor full-scan path).
"""

from __future__ import annotations

import fnmatch
from dataclasses import dataclass, field
from typing import Any


def _positive_int_cap(val: Any, *, cap: int = 10_000) -> int | None:
    try:
        n = int(val)
    except (TypeError, ValueError):
        return None
    if n < 1:
        return None
    return min(n, cap)


def _table_override_limit(
    tables: dict[str, Any], schema: str, table: str
) -> int | None:
    if not tables:
        return None
    st_key = f"{schema}.{table}".strip(".") if (schema or "").strip() else table
    for key in (st_key, table):
        if key in tables:
            lim = _positive_int_cap(tables[key])
            if lim is not None:
                return lim
    return None


def _pattern_match_limit(patterns: dict[str, int], table: str) -> int | None:
    for pattern, lim in patterns.items():
        if fnmatch.fnmatch(table, pattern):
            return max(1, int(lim))
    return None


@dataclass(frozen=True)
class SamplingPolicy:
    """Resolved ``sql_sampling.overrides`` from normalized config."""

    targets: dict[str, dict[str, Any]] = field(default_factory=dict)
    patterns: dict[str, int] = field(default_factory=dict)

    @classmethod
    def from_config(cls, config: dict[str, Any]) -> SamplingPolicy:
        block = config.get("sql_sampling") or {}
        if not isinstance(block, dict):
            return cls()
        ov = block.get("overrides") or {}
        if not isinstance(ov, dict):
            return cls()
        targets = ov.get("targets") or {}
        patterns = ov.get("patterns") or {}
        if not isinstance(targets, dict):
            targets = {}
        if not isinstance(patterns, dict):
            patterns = {}
        pnorm: dict[str, int] = {}
        for k, v in patterns.items():
            lim = _positive_int_cap(v)
            if lim is not None:
                pnorm[str(k).strip()] = lim
        return cls(targets=dict(targets), patterns=pnorm)

    def get_effective_sample_limit(
        self,
        *,
        target_name: str,
        schema: str,
        table: str,
        global_limit: int,
    ) -> int:
        """Return the row cap for one table/column sample before env/global clamps."""
        gl = _positive_int_cap(global_limit) or 1
        name = (target_name or "").strip() or "database"
        tcfg = self.targets.get(name) or {}
        if not isinstance(tcfg, dict):
            return gl

        tables = tcfg.get("tables") or {}
        if isinstance(tables, dict):
            tlim = _table_override_limit(tables, schema, table)
            if tlim is not None:
                return tlim

        lim_t = _positive_int_cap(tcfg.get("sample_limit"))
        if lim_t is not None:
            return lim_t

        plim = _pattern_match_limit(self.patterns, table)
        if plim is not None:
            return plim

        return gl

    def get_effective_limit(
        self,
        target_name: str,
        table_name: str,
        *,
        schema: str = "",
        global_limit: int,
    ) -> int:
        """Alias for :meth:`get_effective_sample_limit` (target + table + global cap)."""
        return self.get_effective_sample_limit(
            target_name=target_name,
            schema=schema,
            table=table_name,
            global_limit=global_limit,
        )
