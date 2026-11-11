"""Post-scan findings push to a SIEM / webhook (#838).

After a scan finishes, POST one structured event to an operator-configured
endpoint (``notifications.findings_push``). The event is a delta-first
envelope: ``new_findings_count`` / ``resolved_count`` / ``previous_session_id``
turn "47 findings again" into "3 new since the last scan".

Envelopes: ``json`` (Data Boar's own) or ``sarif`` (SARIF 2.1.0). Adapters:
``webhook`` (generic; Sentinel / Elastic / anything that takes an authenticated
HTTPS POST) and ``splunk_hec`` (``Authorization: Splunk <token>``).

Security posture (findings carry paths and host names, so the push is hardened):

* Auth token comes ONLY from a process environment variable named in the
  config (``auth_env``). A literal token in config is refused at load.
* ``https`` required; plain ``http`` only for a loopback host.
* Destination is checked by the shared SSRF guard (``connectors.url_guard``)
  and the TCP connection goes to the guard-validated IPs (no second DNS
  lookup, TLS still verifies the configured host name).
* Redirects are never followed; response bodies are read with a hard cap.
* Payload size is capped; findings are trimmed (most sensitive kept) and the
  envelope says ``findings_truncated: true``.
* Retries (bounded backoff) on 5xx / 408 / 429 / timeouts / connection errors.
* Metadata only (no samples). Logs and ``notification_send_log`` carry a
  redacted ``scheme://host:port`` label and fixed error classes — never the
  URL path or query, never the token, never raw exception text.
"""

from __future__ import annotations

import http.client
import json
import logging
import os
import re
import socket
import ssl
import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlparse

from config.loader import normalize_findings_push, validate_findings_push_url
from connectors.url_guard import (
    resolve_and_validate_outbound_url,
    target_allows_private,
)
from core.about import get_about_info
from core.findings_common import (
    FindingRecord,
    SessionDelta,
    collect_session_findings,
    compute_session_delta,
    session_meta,
)
from core.licensing.errors import FeatureTierBlockedError
from core.licensing.feature_gate import require_feature
from core.sarif_export import build_sarif_document

FINDINGS_PUSH_FEATURE = "findings_siem_push"
ENVELOPE_SCHEMA = "data-boar.findings-push"
ENVELOPE_SCHEMA_VERSION = 1
RESPONSE_READ_LIMIT = 64 * 1024
_RETRY_STATUSES = frozenset({408, 425, 429})
_TOKEN_RE = re.compile(r"^[\x21-\x7e]{1,4096}$")

_LOGGER = logging.getLogger("LGPDAudit")


@dataclass(frozen=True)
class PushResult:
    """Outcome of one push. ``detail`` is always safe to log and persist."""

    status: str  # sent | skipped | failed
    channel: str  # webhook | splunk_hec | ""
    detail: str
    attempts: int = 0
    findings_included: int = 0
    findings_truncated: bool = False

    @property
    def ok(self) -> bool:
        return self.status == "sent"


class FindingsPushError(RuntimeError):
    """Push failed. The message is a fixed, redaction-safe description."""


def redacted_destination(url: str) -> str:
    """``scheme://host[:port]`` only — no userinfo, path, query or fragment."""
    p = urlparse(url or "")
    host = p.hostname or "?"
    if ":" in host:
        host = f"[{host}]"
    port = f":{p.port}" if p.port else ""
    return f"{(p.scheme or '?').lower()}://{host}{port}"


def push_settings(config: dict[str, Any] | None) -> dict[str, Any] | None:
    """Normalized ``findings_push`` settings, or ``None`` when the push is off."""
    n = (config or {}).get("notifications")
    if not isinstance(n, dict) or not bool(n.get("enabled", False)):
        return None
    settings = normalize_findings_push(n.get("findings_push"))
    if not settings["enabled"] or not settings["url"]:
        return None
    return settings


# --- payload ----------------------------------------------------------------


def _json_finding(rec: FindingRecord, delta: SessionDelta) -> dict[str, Any]:
    return {
        "fingerprint": rec.fingerprint(),
        "source_type": rec.kind,
        "target": rec.target,
        "location": rec.location,
        "patterns": rec.patterns,
        "sensitivity": rec.sensitivity or "UNSPECIFIED",
        "norm_tag": rec.norm_tag,
        "is_new": delta.is_new(rec) if delta.available else None,
    }


def _envelope(
    *,
    session_id: str,
    meta: dict[str, Any],
    summary: dict[str, Any],
    delta: SessionDelta,
    scope: str,
    selected: list[FindingRecord],
    included: int,
    total_in_scope: int,
) -> dict[str, Any]:
    about = get_about_info()
    return {
        "schema": ENVELOPE_SCHEMA,
        "schema_version": ENVELOPE_SCHEMA_VERSION,
        "event": "scan_complete",
        "application": {"name": about["name"], "version": about["version"]},
        "session_id": session_id,
        "session": {
            "status": meta.get("status"),
            "started_at": meta.get("started_at"),
            "finished_at": meta.get("finished_at"),
            "tenant_name": meta.get("tenant_name"),
        },
        "previous_session_id": delta.previous_session_id,
        "new_findings_count": delta.new_findings_count,
        "resolved_count": delta.resolved_count,
        "delta_available": delta.available,
        "summary": {
            "total_findings": int(summary.get("total_findings") or 0),
            "high": int(summary.get("high") or 0),
            "medium": int(summary.get("medium") or 0),
            "low": int(summary.get("low") or 0),
            "scan_failures": int(summary.get("scan_failures") or 0),
        },
        "findings_scope": scope,
        "findings_total_in_scope": total_in_scope,
        "findings_included": included,
        "findings_truncated": included < total_in_scope,
        "findings": [_json_finding(r, delta) for r in selected[:included]],
        "metadata_only": True,
    }


def _wrap_hec(settings: dict[str, Any], body: dict[str, Any], now: float) -> dict:
    default_type = (
        "data_boar:sarif" if settings["format"] == "sarif" else "data_boar:findings"
    )
    hec: dict[str, Any] = {
        "time": round(now, 3),
        "source": settings.get("hec_source") or "data-boar",
        "sourcetype": settings.get("hec_sourcetype") or default_type,
        "event": body,
    }
    if settings.get("hec_index"):
        hec["index"] = settings["hec_index"]
    return hec


def build_push_body(
    settings: dict[str, Any],
    db_manager: Any,
    session_id: str,
    *,
    now: float | None = None,
) -> tuple[bytes, int, bool]:
    """Serialize the event. Returns ``(body, findings_included, truncated)``.

    Findings are ordered most-sensitive-first, capped by ``max_findings`` and
    then halved until the serialized body fits ``max_payload_bytes``.
    """
    sid = (session_id or "").strip()
    meta = session_meta(db_manager, sid)
    records, failures = collect_session_findings(db_manager, sid)
    delta = compute_session_delta(db_manager, sid)
    summary = dict(db_manager.get_session_scan_summary_for_notification(sid) or {})
    summary["scan_failures"] = failures

    scope = settings["findings_scope"]
    if scope == "new" and delta.available:
        selected = [r for r in records if delta.is_new(r)]
    else:
        scope = "all"  # first scan (no baseline): everything is the baseline
        selected = records
    total = len(selected)
    included = min(total, int(settings["max_findings"]))
    stamp = time.time() if now is None else now
    limit = int(settings["max_payload_bytes"])

    while True:
        if settings["format"] == "sarif":
            doc: dict[str, Any] = build_sarif_document(
                selected[:included],
                session_id=sid,
                meta=meta,
                delta=delta,
                scan_failures=failures,
                extra_run_properties={
                    "event": "scan_complete",
                    "findings_scope": scope,
                    "findings_total_in_scope": total,
                    "findings_included": included,
                    "findings_truncated": included < total,
                    "summary": {
                        k: summary.get(k)
                        for k in ("total_findings", "high", "medium", "low")
                    },
                },
            )
        else:
            doc = _envelope(
                session_id=sid,
                meta=meta,
                summary=summary,
                delta=delta,
                scope=scope,
                selected=selected,
                included=included,
                total_in_scope=total,
            )
        payload = (
            _wrap_hec(settings, doc, stamp)
            if settings["adapter"] == "splunk_hec"
            else doc
        )
        body = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode(
            "utf-8"
        )
        if len(body) <= limit:
            return body, included, included < total
        if included == 0:
            raise FindingsPushError(
                "payload exceeds max_payload_bytes even without findings"
            )
        included //= 2


# --- transport --------------------------------------------------------------


def _connect_pinned(ips: list[str], port: int, timeout: float) -> socket.socket:
    last: OSError | None = None
    for ip in ips:
        try:
            return socket.create_connection((ip, port), timeout)
        except OSError as exc:
            last = exc
    raise last if last else OSError("no validated address to connect to")


class _PinnedHTTPConnection(http.client.HTTPConnection):
    """Plain HTTP (loopback only) that dials a guard-validated IP."""

    def __init__(self, host: str, port: int, ips: list[str], timeout: float) -> None:
        super().__init__(host, port, timeout=timeout)
        self._pin_ips = ips

    def connect(self) -> None:
        self.sock = _connect_pinned(self._pin_ips, self.port, self.timeout)


class _PinnedHTTPSConnection(http.client.HTTPSConnection):
    """HTTPS that dials a guard-validated IP but verifies the configured host."""

    def __init__(
        self,
        host: str,
        port: int,
        ips: list[str],
        timeout: float,
        context: ssl.SSLContext,
    ) -> None:
        super().__init__(host, port, timeout=timeout, context=context)
        self._pin_ips = ips
        self._tls_context = context

    def connect(self) -> None:
        raw = _connect_pinned(self._pin_ips, self.port, self.timeout)
        try:
            self.sock = self._tls_context.wrap_socket(raw, server_hostname=self.host)
        except Exception:
            raw.close()
            raise


def _tls_context() -> ssl.SSLContext:
    ctx = ssl.create_default_context()
    ctx.minimum_version = ssl.TLSVersion.TLSv1_2
    return ctx


def _auth_headers(settings: dict[str, Any]) -> dict[str, str]:
    env_name = settings.get("auth_env") or ""
    if not env_name:
        return {}
    token = (os.environ.get(env_name) or "").strip()
    if not token:
        raise FindingsPushError("auth token environment variable is not set or empty")
    if not _TOKEN_RE.fullmatch(token):
        raise FindingsPushError("auth token contains illegal characters")
    if settings["adapter"] == "splunk_hec":
        return {"Authorization": f"Splunk {token}"}
    scheme = settings.get("auth_scheme") or ""
    value = f"{scheme} {token}" if scheme else token
    return {settings.get("auth_header") or "Authorization": value}


def _request_target(parsed: Any) -> str:
    path = parsed.path or "/"
    return f"{path}?{parsed.query}" if parsed.query else path


def _attempt(
    settings: dict[str, Any],
    parsed: Any,
    ips: list[str],
    body: bytes,
    headers: dict[str, str],
) -> int:
    """One POST. Returns the HTTP status; raises only OSError-family errors."""
    scheme = parsed.scheme.lower()
    port = parsed.port or (443 if scheme == "https" else 80)
    timeout = float(settings["timeout_seconds"])
    host = parsed.hostname or ""
    conn: http.client.HTTPConnection
    if scheme == "https":
        conn = _PinnedHTTPSConnection(host, port, ips, timeout, _tls_context())
    else:
        conn = _PinnedHTTPConnection(host, port, ips, timeout)
    try:
        conn.request("POST", _request_target(parsed), body=body, headers=headers)
        resp = conn.getresponse()
        resp.read(RESPONSE_READ_LIMIT)  # bounded; the body is never logged
        return int(resp.status)
    finally:
        conn.close()


def _post_with_retry(
    settings: dict[str, Any],
    parsed: Any,
    ips: list[str],
    body: bytes,
    headers: dict[str, str],
    sleep: Callable[[float], None],
) -> tuple[int, str | None]:
    """Returns ``(attempts, error_class_or_None)``; the class is a fixed string."""
    max_attempts = int(settings["max_attempts"])
    error = "unknown error"
    for attempt in range(max_attempts):
        retryable = True
        try:
            status = _attempt(settings, parsed, ips, body, headers)
        except TimeoutError:
            error = "timeout"
        except ssl.SSLError:
            error, retryable = "TLS error", False
        except (OSError, http.client.HTTPException):
            error = "connection error"
        else:
            if 200 <= status < 300:
                return attempt + 1, None
            if 300 <= status < 400:
                return attempt + 1, f"HTTP {status} (redirect not followed)"
            error = f"HTTP {status}"
            retryable = status >= 500 or status in _RETRY_STATUSES
        if not retryable or attempt == max_attempts - 1:
            return attempt + 1, error
        sleep(0.5 * (2**attempt))
    return max_attempts, error


def push_findings_for_session(
    config: dict[str, Any],
    db_manager: Any,
    session_id: str,
    *,
    sleep: Callable[[float], None] = time.sleep,
    now: float | None = None,
) -> PushResult:
    """Push one session's findings event. Never raises; never logs secrets."""
    settings = push_settings(config)
    if settings is None:
        return PushResult("skipped", "", "findings_push disabled")
    channel = settings["adapter"]
    dest = redacted_destination(settings["url"])

    try:
        require_feature(config, FINDINGS_PUSH_FEATURE)
    except FeatureTierBlockedError:
        _LOGGER.warning(
            "Findings push skipped: feature requires Pro+ (session=%s)", session_id
        )
        return PushResult("skipped", channel, "feature tier blocked")

    try:
        validate_findings_push_url(settings["url"])
        err, pinned = resolve_and_validate_outbound_url(
            settings["url"],
            allow_private=target_allows_private(settings),
            label="notifications.findings_push.url",
        )
        if err:
            # The guard message embeds the URL; keep only the fixed class.
            raise FindingsPushError(
                "destination rejected by SSRF guard "
                "(set allow_private_networks to opt in to a private host)"
            )
        if urlparse(settings["url"]).scheme.lower() == "http" and not all(
            ip.is_loopback for ip in pinned
        ):
            # Config-time check is on the literal host; re-check what it resolved to.
            raise FindingsPushError("plain http is allowed only to a loopback address")
        headers = {
            "Content-Type": "application/json",
            "Accept": "*/*",
            "Connection": "close",
            "User-Agent": f"data-boar/{get_about_info()['version']}",
            **_auth_headers(settings),
        }
        body, included, truncated = build_push_body(
            settings, db_manager, session_id, now=now
        )
        attempts, failure = _post_with_retry(
            settings,
            urlparse(settings["url"]),
            [str(ip) for ip in pinned],
            body,
            headers,
            sleep,
        )
    except FindingsPushError as exc:
        detail = exc.args[0] if exc.args else "push failed"
        _LOGGER.warning(
            "Findings push failed: session=%s dest=%s reason=%s",
            session_id,
            dest,
            detail,
        )
        return PushResult("failed", channel, str(detail))
    except Exception as exc:  # noqa: BLE001 - fail-soft; log only the class
        cls = type(exc).__name__
        _LOGGER.warning(
            "Findings push failed: session=%s dest=%s reason=%s", session_id, dest, cls
        )
        return PushResult("failed", channel, f"unexpected error ({cls})")

    if failure:
        _LOGGER.warning(
            "Findings push failed: session=%s dest=%s reason=%s attempts=%d",
            session_id,
            dest,
            failure,
            attempts,
        )
        return PushResult(
            "failed",
            channel,
            failure,
            attempts=attempts,
            findings_included=included,
            findings_truncated=truncated,
        )
    _LOGGER.info(
        "Findings push sent: session=%s dest=%s format=%s findings=%d truncated=%s",
        session_id,
        dest,
        settings["format"],
        included,
        truncated,
    )
    return PushResult(
        "sent",
        channel,
        "ok",
        attempts=attempts,
        findings_included=included,
        findings_truncated=truncated,
    )


__all__ = [
    "FINDINGS_PUSH_FEATURE",
    "FindingsPushError",
    "PushResult",
    "build_push_body",
    "push_findings_for_session",
    "push_settings",
    "redacted_destination",
]
