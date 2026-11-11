"""Synthetic fixtures shared by the RoPA / SARIF / findings-push tests (#837, #838).

Not a test module. All data is synthetic (``example.test`` style).
"""

from __future__ import annotations

import json
import threading
from collections.abc import Callable
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

from core.database import LocalDBManager

SESSION_OLD = "govsess-old-0001"
SESSION_NEW = "govsess-new-0002"


def seed_two_sessions(db_path: str) -> tuple[str, str]:
    """Create an OLD and a NEW session.

    Delta OLD -> NEW: one finding is new (``users.cpf``), one is resolved
    (``old_export.csv``), two are unchanged.
    """
    mgr = LocalDBManager(db_path)
    try:
        mgr.create_session_record(SESSION_OLD)
        mgr.set_current_session_id(SESSION_OLD)
        mgr.save_finding(
            "database",
            target_name="crm-db",
            schema_name="public",
            table_name="users",
            column_name="email",
            sensitivity_level="HIGH",
            pattern_detected="EMAIL",
            norm_tag="GDPR Art. 4(1)",
        )
        mgr.save_finding(
            "filesystem",
            target_name="file-share",
            path="/srv/exports",
            file_name="report_may.csv",
            sensitivity_level="MEDIUM",
            pattern_detected="LGPD_CPF, EMAIL",
            norm_tag="LGPD Art. 5(II)",
        )
        mgr.save_finding(
            "filesystem",
            target_name="file-share",
            path="/srv/exports",
            file_name="old_export.csv",
            sensitivity_level="LOW",
            pattern_detected="PHONE_BR",
            norm_tag="LGPD Art. 5(I)",
        )
        mgr.finish_session(SESSION_OLD)

        mgr.create_session_record(SESSION_NEW)
        mgr.set_current_session_id(SESSION_NEW)
        mgr.save_finding(
            "database",
            target_name="crm-db",
            schema_name="public",
            table_name="users",
            column_name="email",
            sensitivity_level="HIGH",
            pattern_detected="EMAIL",
            norm_tag="GDPR Art. 4(1)",
        )
        mgr.save_finding(
            "database",
            target_name="crm-db",
            schema_name="public",
            table_name="users",
            column_name="cpf",
            sensitivity_level="HIGH",
            pattern_detected="LGPD_CPF",
            norm_tag="LGPD Art. 5(II)",
        )
        mgr.save_finding(
            "filesystem",
            target_name="file-share",
            path="/srv/exports",
            file_name="report_may.csv",
            sensitivity_level="MEDIUM",
            pattern_detected="LGPD_CPF, EMAIL",
            norm_tag="LGPD Art. 5(II)",
        )
        mgr.finish_session(SESSION_NEW)
    finally:
        mgr.dispose()
    return SESSION_OLD, SESSION_NEW


class RecordingServer:
    """Loopback HTTP server that records requests and replays canned statuses."""

    def __init__(
        self,
        statuses: list[int] | None = None,
        *,
        response_body: bytes = b"{}",
        extra_headers: dict[str, str] | None = None,
        delay: float = 0.0,
    ) -> None:
        self.requests: list[dict[str, Any]] = []
        self.statuses = list(statuses or [200])
        owner = self

        class Handler(BaseHTTPRequestHandler):
            def do_POST(self) -> None:  # noqa: N802 - stdlib hook name
                length = int(self.headers.get("Content-Length") or 0)
                body = self.rfile.read(length) if length else b""
                owner.requests.append(
                    {
                        "path": self.path,
                        "headers": {k.lower(): v for k, v in self.headers.items()},
                        "body": body,
                    }
                )
                idx = min(len(owner.requests) - 1, len(owner.statuses) - 1)
                if delay:
                    import time

                    time.sleep(delay)
                try:
                    self.send_response(owner.statuses[idx])
                    for k, v in (extra_headers or {}).items():
                        self.send_header(k, v)
                    self.send_header("Content-Length", str(len(response_body)))
                    self.end_headers()
                    self.wfile.write(response_body)
                except (BrokenPipeError, ConnectionResetError):
                    pass

            def log_message(self, *_a: Any) -> None:  # silence test output
                return

        self.httpd = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.port = self.httpd.server_address[1]
        self._thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)

    def __enter__(self) -> RecordingServer:
        self._thread.start()
        return self

    def __exit__(self, *_exc: Any) -> None:
        self.httpd.shutdown()
        self.httpd.server_close()
        self._thread.join(timeout=5)

    @property
    def url(self) -> str:
        return f"http://127.0.0.1:{self.port}/services/collector/event"

    def json_bodies(self) -> list[dict[str, Any]]:
        return [json.loads(r["body"]) for r in self.requests]


def push_config(
    url: str,
    *,
    tier: str | None = "pro_plus",
    **push: Any,
) -> dict[str, Any]:
    """Normalized config (as ``load_config`` returns it) with the push enabled."""
    from config.loader import normalize_config

    licensing: dict[str, Any] = {"mode": "open"}
    if tier:
        licensing["effective_tier"] = tier
    findings_push = {
        "enabled": True,
        "url": url,
        "allow_private_networks": True,
        "auth_env": "API_TEST_SIEM_TOKEN",
        **push,
    }
    return normalize_config(
        {
            "targets": [],
            "licensing": licensing,
            "notifications": {"enabled": True, "findings_push": findings_push},
        }
    )


def no_sleep() -> Callable[[float], None]:
    calls: list[float] = []

    def _sleep(seconds: float) -> None:
        calls.append(seconds)

    _sleep.calls = calls  # type: ignore[attr-defined]
    return _sleep


# Structural subset of the SARIF 2.1.0 schema: the REQUIRED members and enums that
# a consumer relies on (full schema is not vendored; no network in tests).
SARIF_SUBSET_SCHEMA: dict[str, Any] = {
    "type": "object",
    "required": ["version", "runs"],
    "properties": {
        "version": {"const": "2.1.0"},
        "$schema": {"type": "string"},
        "runs": {
            "type": "array",
            "minItems": 1,
            "items": {
                "type": "object",
                "required": ["tool"],
                "properties": {
                    "tool": {
                        "type": "object",
                        "required": ["driver"],
                        "properties": {
                            "driver": {
                                "type": "object",
                                "required": ["name"],
                                "properties": {
                                    "name": {"type": "string", "minLength": 1},
                                    "version": {"type": "string"},
                                    "rules": {
                                        "type": "array",
                                        "items": {
                                            "type": "object",
                                            "required": ["id"],
                                            "properties": {
                                                "id": {"type": "string"},
                                                "defaultConfiguration": {
                                                    "type": "object",
                                                    "properties": {
                                                        "level": {
                                                            "enum": [
                                                                "none",
                                                                "note",
                                                                "warning",
                                                                "error",
                                                            ]
                                                        }
                                                    },
                                                },
                                            },
                                        },
                                    },
                                },
                            }
                        },
                    },
                    "invocations": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "required": ["executionSuccessful"],
                            "properties": {"executionSuccessful": {"type": "boolean"}},
                        },
                    },
                    "results": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "required": ["message"],
                            "properties": {
                                "ruleId": {"type": "string"},
                                "ruleIndex": {"type": "integer", "minimum": 0},
                                "level": {"enum": ["none", "note", "warning", "error"]},
                                "baselineState": {
                                    "enum": ["new", "unchanged", "updated", "absent"]
                                },
                                "message": {
                                    "type": "object",
                                    "required": ["text"],
                                    "properties": {"text": {"type": "string"}},
                                },
                                "locations": {
                                    "type": "array",
                                    "items": {"type": "object", "minProperties": 1},
                                },
                                "partialFingerprints": {
                                    "type": "object",
                                    "additionalProperties": {"type": "string"},
                                },
                            },
                        },
                    },
                },
            },
        },
    },
}


def assert_valid_sarif(doc: dict[str, Any]) -> None:
    """Validate against the subset schema + cross-references (ruleId/ruleIndex)."""
    import jsonschema

    jsonschema.validate(doc, SARIF_SUBSET_SCHEMA)
    for run in doc["runs"]:
        rules = run["tool"]["driver"].get("rules", [])
        ids = [r["id"] for r in rules]
        assert len(ids) == len(set(ids)), "duplicate rule ids"
        for res in run.get("results", []):
            if "ruleIndex" in res:
                assert rules[res["ruleIndex"]]["id"] == res["ruleId"]
            elif "ruleId" in res:
                assert res["ruleId"] in ids
