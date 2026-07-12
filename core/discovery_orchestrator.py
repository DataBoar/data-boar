"""
Discovery orchestrator: active table sampling -> PII validation -> raw assets payload.

This module bridges SQLAlchemy discovery with ``PIIValidator`` so the next step can
feed ``scripts/generate_grc_report.py`` directly (assets/id/findings shape).
"""

from __future__ import annotations

from concurrent.futures import ProcessPoolExecutor
from collections import Counter
from collections.abc import Mapping, Sequence
import time
from typing import Any

from core.brazilian_cpf import PIIValidator
from core.database_manager import DataDiscoveryEngine
from core.prefilter import PreFilter
from core.throttler import BoarThrottler
from pro.prefilter import get_prefilter
from pro.worker_logic import process_chunk_pro


class BoarDiscovery:
    """
    Run a full active discovery pass over database tables.

    Current validator focuses on CPF checksum-backed hits. The orchestrator is generic
    so future validators can add more PII types without changing the output contract.
    """

    def __init__(
        self,
        db_url: str,
        *,
        sample_limit: int = 100,
        worker_processes: int = 1,
        adaptive_rate_limit: bool = False,
        target_latency_ms: float = 200.0,
        sleep_fn: Any = time.sleep,
        enable_pro_prefilter: bool = False,
        profile_terms: Sequence[str] | None = None,
        profile_regexes: Sequence[str] | None = None,
    ) -> None:
        self.db = DataDiscoveryEngine(db_url)
        self.validator = PIIValidator()
        self.sample_limit = max(1, int(sample_limit))
        self.worker_processes = max(1, int(worker_processes))
        self.adaptive_rate_limit = bool(adaptive_rate_limit)
        self.sleep_fn = sleep_fn
        self.throttler = BoarThrottler(
            target_latency_ms=target_latency_ms,
            max_workers=self.worker_processes,
        )
        self.prefilter: PreFilter = get_prefilter(
            enable_pro=enable_pro_prefilter,
            profile_terms=profile_terms,
            profile_regexes=profile_regexes,
        )

    def run_full_scan(self) -> dict[str, Any]:
        """
        Discover tables, sample rows, validate content, return ``raw_scan_results`` shape.
        """
        raw_results: dict[str, Any] = {"assets": []}
        schema_map = self.db.get_all_tables()

        for table_name in schema_map:
            fetch_started = time.perf_counter()
            rows, _keys = self.db.fetch_sample_data(table_name, limit=self.sample_limit)
            fetch_elapsed = time.perf_counter() - fetch_started
            self._after_fetch_latency(fetch_elapsed)
            findings = self._scan_table_rows(rows)
            if findings:
                raw_results["assets"].append(
                    {"id": table_name, "findings": self._counter_to_findings(findings)}
                )

        return raw_results

    def _scan_table_rows(self, rows: Sequence[Mapping[str, Any]]) -> Counter[str]:
        active_workers = self._active_workers()
        if active_workers > 1 and len(rows) > 1:
            return self._scan_table_rows_parallel(rows, active_workers)
        return self._scan_table_rows_sequential(rows)

    def _active_workers(self) -> int:
        if self.adaptive_rate_limit:
            return max(1, int(self.throttler.current_workers))
        return max(1, int(self.worker_processes))

    def _after_fetch_latency(self, fetch_elapsed_seconds: float) -> None:
        if not self.adaptive_rate_limit:
            return
        self.throttler.record_latency(fetch_elapsed_seconds)
        wait = self.throttler.get_sleep_time()
        if wait > 0:
            self.sleep_fn(wait)

    def _scan_table_rows_sequential(
        self, rows: Sequence[Mapping[str, Any]]
    ) -> Counter[str]:
        contents = [self._row_to_content(row) for row in rows]
        contents = self.prefilter.filter_candidates(contents)
        counts: Counter[str] = Counter()
        for content in contents:
            out = self.validator.scan_content(content)
            found = out.get("found") if isinstance(out, Mapping) else None
            if not isinstance(found, list):
                continue
            for hit in found:
                if isinstance(hit, Mapping):
                    t = str(hit.get("type", "")).strip()
                    if t:
                        counts[t] += 1
        return counts

    def _scan_table_rows_parallel(
        self, rows: Sequence[Mapping[str, Any]], active_workers: int
    ) -> Counter[str]:
        contents = [self._row_to_content(row) for row in rows]
        contents = self.prefilter.filter_candidates(contents)
        counts: Counter[str] = Counter()
        with ProcessPoolExecutor(max_workers=active_workers) as pool:
            for type_list in pool.map(_scan_content_types, contents):
                counts.update(type_list)
        return counts

    @staticmethod
    def _counter_to_findings(counter: Counter[str]) -> list[dict[str, Any]]:
        return [
            {"type": pii_type, "count": count} for pii_type, count in counter.items()
        ]

    @staticmethod
    def _row_to_content(row: Mapping[str, Any]) -> str:
        # Only values are scanned; keys/column names stay metadata.
        return " ".join(str(v) for v in row.values() if v is not None)


def _scan_content_types(content: str) -> list[str]:
    """Worker-safe helper: scan one text row and return found type labels."""
    out = PIIValidator().scan_content(content)
    found = out.get("found") if isinstance(out, Mapping) else None
    if not isinstance(found, list):
        return []
    types: list[str] = []
    for hit in found:
        if isinstance(hit, Mapping):
            t = str(hit.get("type", "")).strip()
            if t:
                types.append(t)
    return types


class BoarOrchestrator:
    """
    Pro-oriented orchestrator that combines multiprocessing and adaptive throttling.

    It dispatches full row chunks to process workers, where Rust/OpenCore pre-filter
    logic runs in isolated processes.
    """

    def __init__(
        self,
        db_url: str,
        *,
        max_workers: int | None = None,
        target_latency_ms: float = 250.0,
        batch_limit: int = 1000,
        sleep_fn: Any = time.sleep,
        profile_signals_active: bool = False,
    ) -> None:
        resolved_workers = max(1, int(max_workers or 1))
        self.db = DataDiscoveryEngine(db_url)
        self.batch_limit = max(1, int(batch_limit))
        self.throttler = BoarThrottler(
            target_latency_ms=target_latency_ms,
            max_workers=resolved_workers,
        )
        self.results: list[str] = []
        self.sleep_fn = sleep_fn
        self.profile_signals_active = bool(profile_signals_active)

    def run_discovery(self, table_name: str) -> list[str]:
        """
        Run discovery for one table and return collected suspect payloads.
        """
        futures: dict[Any, None] = {}
        with ProcessPoolExecutor(max_workers=self.throttler.max_workers) as executor:
            start_time = time.perf_counter()
            batch, _keys = self.db.fetch_sample_data(table_name, limit=self.batch_limit)
            latency = time.perf_counter() - start_time
            self.throttler.record_latency(latency)
            if not batch:
                return []

            allowed = max(1, int(self.throttler.current_workers))
            while len(futures) >= allowed:
                self._collect_completed(futures)

            future = executor.submit(
                process_chunk_pro, batch, self.profile_signals_active
            )
            futures[future] = None
            self._collect_completed(futures)

            sleep_seconds = self.throttler.get_sleep_time()
            if sleep_seconds > 0:
                self.sleep_fn(sleep_seconds)

            while futures:
                self._collect_completed(futures)
        return self.results

    def _collect_completed(self, futures: dict[Any, None]) -> None:
        done = [future for future in futures if future.done()]
        for future in done:
            try:
                result = future.result()
            except Exception:
                del futures[future]
                continue
            if result:
                self.results.extend(str(item) for item in result)
            del futures[future]
