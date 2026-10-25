"""Tests for ``core.throttler.BoarThrottler`` adaptive control."""

from __future__ import annotations

from core.throttler import BoarThrottler


def test_throttler_scales_up_in_safe_zone() -> None:
    t = BoarThrottler(target_latency_ms=200, max_workers=4, window_size=4)
    assert t.current_workers == 1
    t.record_latency(0.05)
    t.record_latency(0.06)
    assert t.current_workers >= 2


def test_throttler_scales_down_on_critical_latency() -> None:
    t = BoarThrottler(target_latency_ms=100, max_workers=8, window_size=3)
    t.current_workers = 8
    t.record_latency(0.30)
    t.record_latency(0.35)
    assert t.current_workers <= 4


def test_throttler_sleep_time_positive_only_when_over_target() -> None:
    t = BoarThrottler(target_latency_ms=200, backoff_factor=1.5)
    assert t.get_sleep_time() == 0.0
    t.record_latency(0.25)
    assert t.get_sleep_time() > 0.0
