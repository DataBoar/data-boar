#!/usr/bin/env python3
"""
Slack telemetry helper for Data Boar operator workflows.

Primary webhook env var:
  - SLACK_WEBHOOK_DATA_BOAR_OPS

Compatibility fallback:
  - SLACK_WEBHOOK_URL
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request


def _resolve_webhook_url() -> str:
    primary = (os.getenv("SLACK_WEBHOOK_DATA_BOAR_OPS") or "").strip()
    if primary:
        return primary
    return (os.getenv("SLACK_WEBHOOK_URL") or "").strip()


def _is_valid_slack_webhook(url: str) -> bool:
    if not url:
        return False
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme != "https":
        return False
    if parsed.netloc not in {"hooks.slack.com", "hooks.slack-gov.com"}:
        return False
    if not parsed.path.startswith("/services/"):
        return False
    return True


def send_telemetry(message: str) -> int:
    webhook_url = _resolve_webhook_url()
    if not webhook_url:
        print("MISSING_WEBHOOK: Telemetry offline.")
        return 0

    if not _is_valid_slack_webhook(webhook_url):
        print("INVALID_WEBHOOK: Expected Slack incoming webhook URL.", file=sys.stderr)
        return 2

    payload = {"text": f"🚀 *DATA BOAR TELEMETRY* 🚀\n{message}"}
    body = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        webhook_url,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(  # nosec B310
            request, timeout=15.0
        ) as response:
            response.read()
        print("TELEMETRY_SENT")
        return 0
    except urllib.error.URLError as exc:
        print(f"TELEMETRY_FAILED: {exc}", file=sys.stderr)
        return 1


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Send Data Boar telemetry to Slack via webhook env vars."
    )
    parser.add_argument(
        "message",
        nargs="?",
        default="Heartbeat: Agente Operacional.",
        help="Telemetry message body.",
    )
    args = parser.parse_args()
    return send_telemetry(args.message.strip())


if __name__ == "__main__":
    raise SystemExit(main())
