#!/usr/bin/env python3
"""Schedule-friendly Cloudflare GraphQL Analytics → OTLP metrics exporter (#1599).

Examples (no secrets in argv):

  # Dry-run from fixture (CI / local without Cloudflare token):
  uv run python scripts/cloudflare_graphql_otel_export.py --fixture tests/fixtures/cloudflare/http_requests_adaptive_groups.json --dry-run

  # Live (token + zone from env only):
  export CLOUDFLARE_API_TOKEN=...   # zone-scoped Analytics Read
  export CLOUDFLARE_ZONE_ID=...
  uv run python scripts/cloudflare_graphql_otel_export.py --dry-run
  uv sync --extra otel && uv run python scripts/cloudflare_graphql_otel_export.py

Never prints tokens. Orthogonal to Faro / DataBoar Site browser RUM.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from datetime import timedelta
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from core.cloudflare_edge_metrics import (  # noqa: E402
    QUERY_HTTP_REQUESTS_ADAPTIVE_V1,
    build_variables,
    compute_window,
    emit_otlp_metrics,
    extract_series,
    graphql_url_from_env,
    load_fixture,
    normalize_series,
    parse_hostname_allowlist,
    points_as_jsonable,
    post_graphql,
    read_watermark,
    resolve_credentials_from_env,
    write_watermark,
)

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger("cloudflare_graphql_otel_export")


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Export Cloudflare httpRequestsAdaptiveGroups aggregates to OTLP (service.name=cloudflare-edge)."
    )
    p.add_argument(
        "--fixture",
        type=Path,
        help="Path to GraphQL JSON fixture (skips live API; no token required).",
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="Print normalized metric points as JSON; do not call OTLP.",
    )
    p.add_argument(
        "--lookback-minutes",
        type=int,
        default=int(os.environ.get("CLOUDFLARE_EXPORT_LOOKBACK_MINUTES") or "60"),
    )
    p.add_argument(
        "--overlap-minutes",
        type=int,
        default=int(os.environ.get("CLOUDFLARE_EXPORT_OVERLAP_MINUTES") or "5"),
    )
    p.add_argument(
        "--lag-minutes",
        type=int,
        default=int(os.environ.get("CLOUDFLARE_EXPORT_LAG_MINUTES") or "5"),
        help="End clock lag for Cloudflare Analytics freshness.",
    )
    p.add_argument(
        "--limit",
        type=int,
        default=int(os.environ.get("CLOUDFLARE_EXPORT_LIMIT") or "1000"),
        help="GraphQL series limit (cardinality bound).",
    )
    p.add_argument(
        "--watermark",
        type=Path,
        default=Path(
            os.environ.get("CLOUDFLARE_EXPORT_WATERMARK_PATH")
            or str(
                Path.home() / ".cache" / "data-boar" / "cloudflare_edge_watermark.txt"
            )
        ),
    )
    p.add_argument(
        "--no-watermark",
        action="store_true",
        help="Ignore and do not update watermark file.",
    )
    p.add_argument(
        "--hostname-allowlist",
        default=os.environ.get("CLOUDFLARE_HOSTNAME_ALLOWLIST") or "",
        help="Comma-separated hostnames (e.g. databoar.com.br). Empty = no allowlist filter.",
    )
    p.add_argument(
        "--include-non-eyeball",
        action="store_true",
        help="Rejected in v1 (eyeball is required in the versioned query).",
    )
    p.add_argument(
        "--otlp-endpoint",
        default="",
        help="Override OTEL_EXPORTER_OTLP_METRICS_ENDPOINT / OTEL_EXPORTER_OTLP_ENDPOINT.",
    )
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    allowlist = parse_hostname_allowlist(args.hostname_allowlist or None)
    watermark = None if args.no_watermark else read_watermark(args.watermark)
    window = compute_window(
        lookback=timedelta(minutes=max(1, args.lookback_minutes)),
        overlap=timedelta(minutes=max(0, args.overlap_minutes)),
        lag=timedelta(minutes=max(0, args.lag_minutes)),
        watermark=watermark,
    )

    if args.fixture:
        payload = load_fixture(args.fixture)
        logger.info("Loaded fixture %s (live Cloudflare API skipped)", args.fixture)
    else:
        token, zone_id = resolve_credentials_from_env()
        variables = build_variables(
            zone_id=zone_id,
            window=window,
            limit=max(1, min(args.limit, 5000)),
            eyeball_only=not args.include_non_eyeball,
        )
        payload = post_graphql(
            query=QUERY_HTTP_REQUESTS_ADAPTIVE_V1,
            variables=variables,
            token=token,
            url=graphql_url_from_env(),
        )

    series = extract_series(payload)
    batch = normalize_series(
        series,
        window=window,
        hostname_allowlist=allowlist,
        max_hostnames=32,
    )
    logger.info(
        "Normalized %s points from %s groups (dropped_host=%s) window=[%s,%s)",
        len(batch.points),
        batch.raw_group_count,
        batch.dropped_hostname_count,
        window.start.isoformat(),
        window.end.isoformat(),
    )

    if args.dry_run:
        print(json.dumps(points_as_jsonable(batch), indent=2, sort_keys=True))
        return 0

    ok = emit_otlp_metrics(batch, endpoint=args.otlp_endpoint or None)
    if not ok:
        return 2

    if not args.no_watermark and not args.fixture:
        write_watermark(args.watermark, window.end)
        logger.info("Watermark updated %s", args.watermark)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
