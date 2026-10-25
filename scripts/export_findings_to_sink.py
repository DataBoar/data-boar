#!/usr/bin/env python3
"""Echo one scan session from local SQLite to the configured findings_sink (#552).

Prefer the main CLI:

  uv run python main.py --config config.yaml --export-findings-sink SESSION_ID

This script is the same push with optional --allow-sample-export.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from config.loader import load_config  # noqa: E402
from core.engine import AuditEngine  # noqa: E402
from core.findings_sink import (  # noqa: E402
    FindingsSinkError,
    SampleExportNotAcknowledged,
    push_session_to_sink,
)
from core.licensing.errors import FeatureTierBlockedError  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="config.yaml")
    parser.add_argument("session_id")
    parser.add_argument(
        "--allow-sample-export",
        action="store_true",
        help="Required when findings_sink.include_sample_content is true (LGPD Art. 46).",
    )
    args = parser.parse_args()
    config = load_config(args.config)
    engine = AuditEngine(config, config_path=args.config)
    try:
        label = push_session_to_sink(
            config,
            engine.db_manager,
            args.session_id,
            allow_sample_export=bool(args.allow_sample_export),
            require_explicit_sample_ack=True,
        )
    except SampleExportNotAcknowledged as exc:
        print(str(exc), file=sys.stderr)
        return 1
    except FeatureTierBlockedError as exc:
        print(f"Licensing: {exc}", file=sys.stderr)
        return 2
    except FindingsSinkError as exc:
        print(f"Findings sink error: {exc}", file=sys.stderr)
        return 1
    finally:
        engine.db_manager.dispose()
    print(f"Findings exported to {label}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
