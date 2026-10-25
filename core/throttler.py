"""
Adaptive Rate Limiting (ARL) controller for discovery/scanner loops.

This is a lightweight feedback controller: it tracks moving average latency and
adjusts worker concurrency and optional cool-off sleep without hard-failing scans.
"""

from __future__ import annotations

import collections
import logging


class BoarThrottler:
    """Adaptive worker controller based on database/query latency."""

    def __init__(
        self,
        *,
        target_latency_ms: float = 200.0,
        max_workers: int = 10,
        window_size: int = 10,
        backoff_factor: float = 1.5,
    ) -> None:
        self.target_latency = max(1.0, float(target_latency_ms)) / 1000.0
        self.max_workers = max(1, int(max_workers))
        self.current_workers = 1
        self.latency_history: collections.deque[float] = collections.deque(
            maxlen=max(1, int(window_size))
        )
        self.backoff_factor = max(0.0, float(backoff_factor))

    def record_latency(self, latency_seconds: float) -> None:
        """Store the latest latency and adjust workers from moving average."""
        if latency_seconds < 0:
            return
        self.latency_history.append(float(latency_seconds))
        avg_latency = sum(self.latency_history) / len(self.latency_history)
        self._adjust_throttle(avg_latency)

    def _adjust_throttle(self, avg_latency: float) -> None:
        if avg_latency > self.target_latency * 2:
            self.current_workers = max(1, int(self.current_workers / 2))
            logging.warning(
                "BoarThrottler: high latency %.3fs, reducing to %s workers",
                avg_latency,
                self.current_workers,
            )
            return

        if avg_latency > self.target_latency:
            self.current_workers = max(1, self.current_workers - 1)
            return

        if avg_latency < self.target_latency * 0.8:
            if self.current_workers < self.max_workers:
                self.current_workers += 1
                logging.info(
                    "BoarThrottler: stable latency %.3fs, increasing to %s workers",
                    avg_latency,
                    self.current_workers,
                )

    def get_sleep_time(self) -> float:
        """Return adaptive cool-off seconds (0 when stable)."""
        if not self.latency_history:
            return 0.0
        avg = sum(self.latency_history) / len(self.latency_history)
        return max(0.0, avg - self.target_latency) * self.backoff_factor
