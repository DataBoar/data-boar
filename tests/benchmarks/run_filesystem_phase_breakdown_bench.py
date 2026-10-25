#!/usr/bin/env python3
"""
Filesystem scan phase breakdown (research benchmark for #1078 / #1080).

Measures wall time for: directory enumeration (walk/glob) vs file read+extract sample
vs detector scan_file_content on a synthetic corpus of plain .txt files.

Does NOT claim SMB/NFS latency — local ext4/tmpfs only. Use to gate parallel-walk
and vectorscan work: if read+detect dominate, regex SIMD is not the first lever.
"""

from __future__ import annotations

import argparse
import json
import platform
import statistics
import subprocess
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

BENCHMARK_ID = "filesystem_phase_breakdown_v1"


def _git_sha_short() -> str | None:
    try:
        out = subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            stderr=subprocess.DEVNULL,
            text=True,
        )
        return out.strip() or None
    except (OSError, subprocess.CalledProcessError):
        return None


def _seed_corpus(root: Path, *, file_count: int) -> None:
    root.mkdir(parents=True, exist_ok=True)
    payload = (
        "Holder: sample_holder_a\nID: 123.456.789-00\nEmail: sample@example.com\n"
        "Phone: (11) 90000-0000\n"
    )
    for i in range(file_count):
        (root / f"doc_{i:05d}.txt").write_text(payload, encoding="utf-8")


def _time_glob_walk(root: Path, iterations: int) -> float:
    timings: list[float] = []
    for _ in range(iterations):
        start = time.perf_counter()
        count = 0
        for p in root.glob("**/*"):
            if p.is_file():
                count += 1
        timings.append(time.perf_counter() - start)
        assert count > 0
    return statistics.mean(timings)


def _time_read_samples(root: Path, iterations: int, max_chars: int) -> float:
    from connectors.filesystem_connector import _read_text_sample

    files = [p for p in root.glob("**/*") if p.is_file()]
    timings: list[float] = []
    for _ in range(iterations):
        start = time.perf_counter()
        for fp in files:
            _read_text_sample(fp, ".txt", max_chars, {})
        timings.append(time.perf_counter() - start)
    return statistics.mean(timings)


def _time_detect(root: Path, iterations: int, max_chars: int) -> float:
    from connectors.filesystem_connector import _read_text_sample
    from core.scanner import DataScanner

    scanner = DataScanner()
    files = [p for p in root.glob("**/*") if p.is_file()]
    timings: list[float] = []
    for _ in range(iterations):
        start = time.perf_counter()
        for fp in files:
            content = _read_text_sample(fp, ".txt", max_chars, {})
            scanner.scan_file_content(content, fp)
        timings.append(time.perf_counter() - start)
    return statistics.mean(timings)


def run_benchmark(
    *,
    file_count: int,
    warmup: int,
    iterations: int,
    max_chars: int,
) -> dict[str, Any]:
    import tempfile

    with tempfile.TemporaryDirectory(prefix="db_fs_bench_") as tmp:
        root = Path(tmp)
        _seed_corpus(root, file_count=file_count)
        print(f"[*] Filesystem phase breakdown: {file_count:,} txt files under {root}")

        for _ in range(warmup):
            _time_glob_walk(root, 1)
            _time_read_samples(root, 1, max_chars)
            _time_detect(root, 1, max_chars)

        walk_s = _time_glob_walk(root, iterations)
        read_s = _time_read_samples(root, iterations, max_chars)
        detect_s = _time_detect(root, iterations, max_chars)

        # read pass includes read; detect pass includes read+detect
        read_only_s = max(read_s, 0.0)
        detect_only_s = max(detect_s - read_s, 0.0)
        total_s = walk_s + detect_s
        walk_pct = 100.0 * walk_s / total_s if total_s else 0.0
        read_pct = 100.0 * read_only_s / total_s if total_s else 0.0
        detect_pct = 100.0 * detect_only_s / total_s if total_s else 0.0
        matching_pct = detect_pct  # scan_file_content ~= matching+ML for txt

        print(f"    walk/glob mean: {walk_s:.4f}s ({walk_pct:.1f}%)")
        print(f"    read sample mean: {read_only_s:.4f}s ({read_pct:.1f}%)")
        print(f"    detect delta mean: {detect_only_s:.4f}s ({detect_pct:.1f}%)")

        return {
            "benchmark_id": BENCHMARK_ID,
            "generated_at_utc": datetime.now(UTC).isoformat(),
            "git_sha": _git_sha_short(),
            "host": platform.platform(),
            "file_count": file_count,
            "iterations": iterations,
            "max_chars": max_chars,
            "seconds": {
                "walk_glob": walk_s,
                "read_sample": read_only_s,
                "detect_delta": detect_only_s,
                "total_estimated": total_s,
            },
            "percent_of_total": {
                "walk_glob": round(walk_pct, 2),
                "read_sample": round(read_pct, 2),
                "detect_matching": round(matching_pct, 2),
            },
            "gate_notes": {
                "vectorscan_threshold_pct": 15,
                "parallel_walk_threshold_pct": 15,
                "matching_below_vectorscan_gate": matching_pct < 15,
                "walk_below_parallel_gate": walk_pct < 15,
            },
        }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--files", type=int, default=2000)
    parser.add_argument("--warmup", type=int, default=1)
    parser.add_argument("--iterations", type=int, default=3)
    parser.add_argument("--max-chars", type=int, default=12_000)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("tests/benchmarks/filesystem_phase_breakdown.json"),
    )
    args = parser.parse_args()
    payload = run_benchmark(
        file_count=args.files,
        warmup=args.warmup,
        iterations=args.iterations,
        max_chars=args.max_chars,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"[+] Wrote {args.output}")


if __name__ == "__main__":
    main()
