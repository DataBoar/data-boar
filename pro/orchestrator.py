# Copyright (c) 2025-2026, FabioLeitao. All rights reserved.
# This file is part of the Pro tier and is proprietary — NOT covered by
# the repository's root BSD-3-Clause LICENSE. See pro/LICENSE.
"""
Pro+ discovery orchestrator with multiprocessing and adaptive throttling.
"""

from __future__ import annotations

import concurrent.futures
import time
from collections.abc import Mapping, Sequence
from typing import Any

from core.database_manager import DataDiscoveryEngine
from core.throttler import BoarThrottler
from pro.engine import process_chunk_worker
from pro.state_tracker import BoarStateTracker


class ProOrchestrator:
    """
    SRE-friendly orchestrator that dispatches chunks to process workers.
    """

    def __init__(
        self,
        db_engine: DataDiscoveryEngine | str,
        *,
        max_workers: int | None = None,
        target_latency_ms: float = 250.0,
        batch_limit: int = 1000,
        checkpoint_file: str = ".data_boar_state.json",
        id_column: str = "id",
        sleep_fn: Any = time.sleep,
    ) -> None:
        self.db = (
            db_engine
            if isinstance(db_engine, DataDiscoveryEngine)
            else DataDiscoveryEngine(str(db_engine))
        )
        resolved_workers = max(1, int(max_workers or 1))
        self.throttler = BoarThrottler(
            target_latency_ms=target_latency_ms,
            max_workers=resolved_workers,
        )
        self.batch_limit = max(1, int(batch_limit))
        self.id_column = id_column
        self.is_running = True
        self._sleep_fn = sleep_fn
        self.findings: list[str] = []
        self.tracker = BoarStateTracker(checkpoint_file=checkpoint_file)
        self._risk_score_accumulated = 0

    def run_discovery(self, table_name: str) -> list[str]:
        """
        Run one discovery pass over ``table_name`` and return accumulated findings.
        """
        with concurrent.futures.ProcessPoolExecutor(
            max_workers=self.throttler.max_workers
        ) as executor:
            checkpoint = self.tracker.table_checkpoint(table_name)
            last_id = int(checkpoint.get("last_processed_id", 0))
            while self.is_running:
                current_concurrency = max(1, int(self.throttler.current_workers))
                start_fetch = time.perf_counter()
                chunks, max_id = self._get_next_chunks(
                    table_name, count=current_concurrency, last_id=last_id
                )
                fetch_latency = time.perf_counter() - start_fetch

                if not chunks:
                    self.tracker.mark_completed(
                        table_name,
                        last_id=last_id,
                        risk_score_accumulated=self._risk_score_accumulated,
                    )
                    break

                self.throttler.record_latency(fetch_latency)
                futures = [
                    executor.submit(process_chunk_worker, chunk)
                    for chunk in chunks
                    if chunk
                ]

                for future in concurrent.futures.as_completed(futures):
                    result = future.result()
                    if result:
                        self._report_findings(result)

                if max_id is not None:
                    last_id = max_id
                    self.tracker.save_checkpoint(
                        table_name,
                        last_id=last_id,
                        risk_score_accumulated=self._risk_score_accumulated,
                    )

                cooldown = self.throttler.get_sleep_time()
                if cooldown > 0:
                    self._sleep_fn(cooldown)
        return self.findings

    def _get_next_chunks(
        self, table: str, count: int, *, last_id: int
    ) -> tuple[list[list[str]], int | None]:
        rows, _columns = self.db.fetch_after_id(
            table,
            last_id=last_id,
            id_column=self.id_column,
            limit=self.batch_limit,
        )
        if not rows:
            return [], None
        payloads = [self._row_to_payload(row) for row in rows]
        ids = [int(row[self.id_column]) for row in rows if self.id_column in row]
        max_seen_id = max(ids) if ids else last_id
        return _split_evenly(payloads, max(1, count)), max_seen_id

    def _report_findings(self, findings: Sequence[str]) -> None:
        self.findings.extend(str(item) for item in findings)
        self._risk_score_accumulated += len(findings)

    @staticmethod
    def _row_to_payload(row: Mapping[str, Any]) -> str:
        return " ".join(str(value) for value in row.values() if value is not None)


def _split_evenly(values: list[str], parts: int) -> list[list[str]]:
    if not values:
        return []
    chunk_size = max(1, len(values) // parts)
    chunks = [
        values[idx : idx + chunk_size] for idx in range(0, len(values), chunk_size)
    ]
    return [chunk for chunk in chunks if chunk]
