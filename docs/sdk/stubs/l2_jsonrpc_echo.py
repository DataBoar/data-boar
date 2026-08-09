#!/usr/bin/env python3
"""Minimal L2 JSON-RPC-over-stdio echo stub (non-production).

Reads newline-delimited JSON-RPC 2.0 requests from stdin.
For method ``databoar.remediation.decide``, returns a ``safe_hold`` decision
envelope conforming to docs/sdk/PLUGIN_CONTRACT.schema.json.

Usage (manual)::

    echo '{"jsonrpc":"2.0","id":1,"method":"databoar.remediation.decide","params":{}}' \\
      | python docs/sdk/stubs/l2_jsonrpc_echo.py
"""

from __future__ import annotations

import json
import sys
from typing import Any


SDK_CONTRACT_VERSION = "1.0.0"


def _safe_hold_decision(request_id: Any, params: dict[str, Any] | None = None) -> dict[str, Any]:
    params = params if isinstance(params, dict) else {}
    session_id = str(params.get("session_id") or "sess_stub")
    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "result": {
            "sdk_contract_version": SDK_CONTRACT_VERSION,
            "schema": "databoar.plugin.decision",
            "session_id": session_id,
            "request_id": str(params.get("request_id") or request_id or "req_stub"),
            "plugin": {
                "name": "l2_jsonrpc_echo",
                "version": "0.0.1",
                "tier": "L2",
            },
            "status": "safe_hold",
            "decided_at": "1970-01-01T00:00:00Z",
            "host_trust_level_observed": params.get("trust_level") or "unknown",
            "results": [],
            "error": {
                "code": "stub_safe_hold",
                "message": "l2_jsonrpc_echo stub — no remediation applied",
            },
        },
    }


def _error(request_id: Any, code: int, message: str) -> dict[str, Any]:
    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "error": {"code": code, "message": message},
    }


def handle_line(line: str) -> dict[str, Any] | None:
    line = line.strip()
    if not line:
        return None
    try:
        msg = json.loads(line)
    except json.JSONDecodeError:
        return _error(None, -32700, "Parse error")
    if not isinstance(msg, dict):
        return _error(None, -32600, "Invalid Request")
    req_id = msg.get("id")
    method = msg.get("method")
    if method == "databoar.remediation.decide":
        params = msg.get("params") if isinstance(msg.get("params"), dict) else {}
        return _safe_hold_decision(req_id, params)
    if method in ("initialize", "shutdown", "health"):
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {"ok": True, "sdk_contract_version": SDK_CONTRACT_VERSION},
        }
    return _error(req_id, -32601, f"Method not found: {method}")


def main() -> int:
    for line in sys.stdin:
        resp = handle_line(line)
        if resp is not None:
            sys.stdout.write(json.dumps(resp, separators=(",", ":")) + "\n")
            sys.stdout.flush()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
