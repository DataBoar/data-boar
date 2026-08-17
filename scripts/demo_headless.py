#!/usr/bin/env python3
"""Cross-platform headless demo smoke (scan + report, no dashboard).

Mirrors ``scripts/demo.sh --headless`` without bash — used by Windows CI (#1427)
and local operators who prefer ``python scripts/demo_headless.py``.
"""

from __future__ import annotations

import argparse
import shutil
import sys
import tempfile
from pathlib import Path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run Data Boar demo scan headlessly (no uvicorn)."
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8088,
        help="Port written into demo.config.yaml (dashboard not started).",
    )
    parser.add_argument(
        "--keep",
        action="store_true",
        help="Do not delete the demo workspace on exit (debug).",
    )
    args = parser.parse_args(argv)

    repo_root = Path(__file__).resolve().parents[1]
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))

    from config.loader import load_config
    from core.demo.runtime import prepare_demo_workspace
    from core.engine import AuditEngine

    demo_root = Path(tempfile.gettempdir()) / "data_boar_demo"
    if demo_root.exists():
        shutil.rmtree(demo_root, ignore_errors=True)

    demo_dir, config_path, _ = prepare_demo_workspace(
        port=args.port,
        register_cleanup=False,
        demo_root=demo_root,
    )
    config = load_config(str(config_path))
    engine = AuditEngine(config)
    try:
        sid = engine.start_audit()
        report = engine.generate_final_reports(sid)
        print(f"[demo] Scan session: {sid}")
        if report:
            print(f"[demo] Report written: {report}")
        else:
            print("[demo] No findings to report.", file=sys.stderr)
            return 1
    finally:
        engine.db_manager.dispose()
        if not args.keep:
            shutil.rmtree(demo_dir, ignore_errors=True)
            print(f"[demo] Cleaned {demo_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
