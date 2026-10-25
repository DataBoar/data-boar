#!/usr/bin/env python3
"""
POST ``/scan`` on a Data Boar web dashboard, then poll ``/status`` until idle.

Operator / homelab helper — not used by CI. For a scan on another host, set the
base URL via environment **``DATA_BOAR_BASE``** or **``--base``** (e.g.
``http://127.0.0.1:8088``). If **``api.require_api_key``** is enabled, pass
**``DATA_BOAR_API_KEY``** or **``--api-key``** (never commit keys). Do **not**
commit real lab hostnames or LAN URLs in this repo; see root **``AGENTS.md``**
and **``docs/PRIVATE_OPERATOR_NOTES.md``**.

**Token-aware reuse:** one documented entry point — ``uv run python scripts/poll_dashboard_scan.py --help`` — no per-host script names in the repo (do **not** add one-off ``.cursor/*.py`` files with hardcoded lab hostnames).
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request

from connectors.url_guard import validate_outbound_url

DEFAULT_BASE = "http://127.0.0.1:8088"
DEFAULT_POLL_INTERVAL = 10
DEFAULT_MAX_POLLS = 120


def _assert_dashboard_url(url: str) -> None:
    """Reject non-http(s) and unparseable URLs before urlopen (#529).

    Loopback / RFC1918 are **allowed**: this helper polls a local dashBOARd
    (default ``http://127.0.0.1:8088``). ``allow_private=True`` is required
    so :func:`validate_outbound_url` does not treat localhost as SSRF.
    """
    err = validate_outbound_url(url, allow_private=True, label="dashboard URL")
    if err:
        raise ValueError(err)


def _extra_headers(api_key: str | None) -> dict[str, str]:
    h: dict[str, str] = {}
    if api_key:
        h["X-API-Key"] = api_key
    return h


def get_json(
    base: str,
    path: str,
    *,
    extra_headers: dict[str, str] | None = None,
) -> dict:
    headers = dict(extra_headers or {})
    url = f"{base.rstrip('/')}{path}"
    _assert_dashboard_url(url)
    req = urllib.request.Request(url, method="GET", headers=headers)
    with urllib.request.urlopen(req, timeout=60) as r:  # nosec B310 — url_guard
        return json.loads(r.read().decode())


def post_json(
    base: str,
    path: str,
    body: dict,
    *,
    extra_headers: dict[str, str] | None = None,
) -> dict:
    headers = {"Content-Type": "application/json"}
    headers.update(extra_headers or {})
    data = json.dumps(body).encode()
    url = f"{base.rstrip('/')}{path}"
    _assert_dashboard_url(url)
    req = urllib.request.Request(
        url,
        data=data,
        method="POST",
        headers=headers,
    )
    with urllib.request.urlopen(req, timeout=60) as r:  # nosec B310 — url_guard
        return json.loads(r.read().decode())


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument(
        "--base",
        default=os.environ.get("DATA_BOAR_BASE", DEFAULT_BASE).rstrip("/"),
        help=f"Dashboard root URL (default: env DATA_BOAR_BASE or {DEFAULT_BASE})",
    )
    p.add_argument(
        "--api-key",
        default=(os.environ.get("DATA_BOAR_API_KEY") or "").strip() or None,
        help="X-API-Key when require_api_key is true (default: env DATA_BOAR_API_KEY)",
    )
    p.add_argument(
        "--interval",
        type=int,
        default=DEFAULT_POLL_INTERVAL,
        metavar="SEC",
        help=f"Seconds between /status polls (default: {DEFAULT_POLL_INTERVAL})",
    )
    p.add_argument(
        "--max-polls",
        type=int,
        default=DEFAULT_MAX_POLLS,
        metavar="N",
        help=f"Max poll iterations before timeout (default: {DEFAULT_MAX_POLLS})",
    )
    args = p.parse_args(argv)
    base = args.base.rstrip("/")
    if args.interval < 1:
        p.error("--interval must be >= 1")
    if args.max_polls < 1:
        p.error("--max-polls must be >= 1")
    xh = _extra_headers(args.api_key)

    print("POST /scan ...")
    start = post_json(base, "/scan", {}, extra_headers=xh)
    print(json.dumps(start, indent=2))
    sid = start.get("session_id", "")
    for i in range(args.max_polls):
        time.sleep(args.interval)
        st = get_json(base, "/status", extra_headers=xh)
        print(
            f"[{i}] running={st.get('running')} findings={st.get('findings_count')} "
            f"session={st.get('current_session_id')!r}"
        )
        if not st.get("running"):
            print("idle")
            print(json.dumps(get_json(base, "/status", extra_headers=xh), indent=2))
            if sid:
                print(f"\nDownload report: curl -sOJ {base}/reports/{sid}")
            return 0
    total_s = args.max_polls * args.interval
    print(
        f"timeout after {args.max_polls} polls × {args.interval}s ≈ {total_s}s, still running"
    )
    return 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except urllib.error.URLError as e:
        print("URLError:", e, file=sys.stderr)
        raise SystemExit(2) from e
