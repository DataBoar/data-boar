#!/usr/bin/env python3
from __future__ import annotations

import argparse
import time

from pro.orchestrator import ProOrchestrator


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db-url", required=True)
    parser.add_argument("--table", default="users")
    parser.add_argument("--checkpoint", default="data/qa_completao_state.json")
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--batch-limit", type=int, default=2000)
    parser.add_argument("--target-latency-ms", type=float, default=2500.0)
    parser.add_argument("--sleep-per-loop", type=float, default=0.02)
    args = parser.parse_args()

    orchestrator = ProOrchestrator(
        args.db_url,
        max_workers=args.workers,
        batch_limit=args.batch_limit,
        checkpoint_file=args.checkpoint,
        target_latency_ms=args.target_latency_ms,
        sleep_fn=lambda seconds: time.sleep(max(seconds, args.sleep_per_loop)),
    )
    findings = orchestrator.run_discovery(args.table)
    print(
        "SCAN_DONE",
        f"findings={len(findings)}",
        f"final_workers={orchestrator.throttler.current_workers}",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
