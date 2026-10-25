"""
Live scan progress lines for long-running audits (#1328).

Emits periodic ``target X/Y · table N/M · ~Z% · ETA ~W min`` to stderr when enabled.
Table totals come from connector discovery (e.g. SQLAlchemy ``discover()``) — not guessed.
"""

from __future__ import annotations

import sys
import threading
import time
from dataclasses import dataclass
from typing import Any, TextIO


@dataclass
class _TargetTableState:
    target_index: int
    target_name: str
    tables_total: int | None = None
    tables_done: int = 0
    table_started_at: float = 0.0
    first_table_at: float | None = None


@dataclass
class ScanProgressConfig:
    enabled: bool = True
    interval_seconds: float = 30.0
    interval_tables: int = 5

    @classmethod
    def from_scan_config(cls, scan_cfg: dict[str, Any] | None) -> ScanProgressConfig:
        raw = scan_cfg if isinstance(scan_cfg, dict) else {}
        enabled = raw.get("progress", True)
        if isinstance(enabled, str):
            enabled = enabled.strip().lower() not in {"0", "false", "no", "off"}
        try:
            interval_seconds = float(raw.get("progress_interval_seconds", 30.0))
        except (TypeError, ValueError):
            interval_seconds = 30.0
        try:
            interval_tables = int(raw.get("progress_interval_tables", 5))
        except (TypeError, ValueError):
            interval_tables = 5
        return cls(
            enabled=bool(enabled),
            interval_seconds=max(5.0, interval_seconds),
            interval_tables=max(1, interval_tables),
        )


class ScanProgress:
    """Thread-safe progress reporter for multi-target scans."""

    def __init__(
        self,
        config: ScanProgressConfig,
        *,
        stream: TextIO | None = None,
        monotonic: Any = time.monotonic,
    ) -> None:
        self._cfg = config
        self._stream = stream if stream is not None else sys.stderr
        self._monotonic = monotonic
        self._lock = threading.Lock()
        self._targets_total = 0
        self._targets_started = 0
        self._targets_finished = 0
        self._run_started = 0.0
        self._last_emit = 0.0
        self._by_thread: dict[int, _TargetTableState] = {}

    @property
    def enabled(self) -> bool:
        return self._cfg.enabled

    def start_run(self, targets_total: int) -> None:
        if not self.enabled:
            return
        with self._lock:
            self._targets_total = max(0, int(targets_total))
            self._targets_started = 0
            self._targets_finished = 0
            self._run_started = self._monotonic()
            self._last_emit = 0.0
            self._by_thread.clear()

    def begin_target(self, target_index: int, target_name: str) -> None:
        if not self.enabled:
            return
        tid = threading.get_ident()
        with self._lock:
            self._targets_started = max(self._targets_started, target_index)
            self._by_thread[tid] = _TargetTableState(
                target_index=target_index,
                target_name=target_name,
                table_started_at=self._monotonic(),
            )
        self._maybe_emit(force=True)

    def end_target(self, target_name: str) -> None:
        if not self.enabled:
            return
        tid = threading.get_ident()
        with self._lock:
            self._targets_finished += 1
            self._by_thread.pop(tid, None)
        self._maybe_emit(force=True)

    def set_tables_total(self, total: int, *, target_name: str | None = None) -> None:
        if not self.enabled:
            return
        tid = threading.get_ident()
        with self._lock:
            state = self._by_thread.get(tid)
            if state is None:
                return
            if target_name and state.target_name != target_name:
                return
            state.tables_total = max(0, int(total))

    def advance_table(
        self,
        table_index: int,
        *,
        table_label: str = "",
        target_name: str | None = None,
    ) -> None:
        """Call once per table (after discovery). ``table_index`` is 1-based."""
        if not self.enabled:
            return
        now = self._monotonic()
        tid = threading.get_ident()
        with self._lock:
            state = self._by_thread.get(tid)
            if state is None:
                return
            if target_name and state.target_name != target_name:
                return
            state.tables_done = max(state.tables_done, int(table_index))
            state.table_started_at = now
            if state.first_table_at is None:
                state.first_table_at = now
        force = False
        if table_index == 1:
            force = True
        elif (
            self._cfg.interval_tables > 0
            and table_index % self._cfg.interval_tables == 0
        ):
            force = True
        self._maybe_emit(force=force, table_label=table_label)

    def _maybe_emit(self, *, force: bool = False, table_label: str = "") -> None:
        if not self.enabled:
            return
        now = self._monotonic()
        with self._lock:
            if not force and (now - self._last_emit) < self._cfg.interval_seconds:
                return
            line = self._format_line(table_label=table_label, now=now)
            self._last_emit = now
        if line:
            self._stream.write(line + "\n")
            self._stream.flush()

    def _format_line(self, *, table_label: str, now: float) -> str:
        tid = threading.get_ident()
        state = self._by_thread.get(tid)
        if state is None and self._by_thread:
            state = next(iter(self._by_thread.values()))
        if state is None:
            done = self._targets_finished
            total = self._targets_total
            return f"[data-boar] scan progress · target {done}/{total}"

        t_idx = state.target_index
        t_total = self._targets_total
        name = state.target_name
        n = state.tables_done
        m = state.tables_total

        parts = [f"[data-boar] scan progress · target {t_idx}/{t_total} ({name})"]
        if m is not None and m > 0:
            pct = min(100, int(round(100.0 * n / m)))
            parts.append(f"table {n}/{m}")
            if table_label:
                parts[-1] += f" ({table_label})"
            parts.append(f"~{pct}%")
            eta = self._eta_minutes(state, now=now)
            if eta is not None:
                parts.append(f"ETA ~{eta:.0f} min")
            else:
                parts.append("ETA n/a")
        else:
            parts.append(f"table {n}")
            if table_label:
                parts.append(f"({table_label})")
            parts.append("total tables pending discovery")
        return " · ".join(parts)

    def _eta_minutes(self, state: _TargetTableState, *, now: float) -> float | None:
        if state.tables_total is None or state.tables_total <= 0:
            return None
        if state.tables_done < 2 or state.first_table_at is None:
            return None
        elapsed = now - state.first_table_at
        if elapsed <= 0:
            return None
        per_table = elapsed / max(1, state.tables_done - 1)
        remaining_tables = max(0, state.tables_total - state.tables_done)
        return (remaining_tables * per_table) / 60.0


_NOOP = ScanProgress(ScanProgressConfig(enabled=False))


def scan_progress_from_config(config: dict[str, Any]) -> ScanProgress:
    scan_cfg = config.get("scan") if isinstance(config.get("scan"), dict) else {}
    cfg = ScanProgressConfig.from_scan_config(scan_cfg)
    if not cfg.enabled:
        return _NOOP
    return ScanProgress(cfg)
