"""
Off-band and scan-completion notifications (webhooks, Slack, Teams, Telegram).

Default: disabled in config. Secrets come from env or config; never log full URLs.
See docs/USAGE.md and PLAN_NOTIFICATIONS_OFFBAND_AND_SCAN_COMPLETE.md.
"""

from __future__ import annotations

import json
import logging
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

_LOGGER = logging.getLogger("LGPDAudit")

# Phase 3 (Corporate-Entity-C / PLAN_NOTIFICATIONS): transient webhook failures (5xx, network).
_WEBHOOK_MAX_ATTEMPTS = 3

# Dedupe successful scan-complete rounds per session (process-local; avoids duplicate POSTs).
_SCAN_COMPLETE_OK_LOCK = threading.Lock()
_SCAN_COMPLETE_OK_SESSIONS: set[str] = set()
_MAX_DEDUPE_SESSIONS = 10_000


def _post_json(url: str, payload: dict[str, Any], timeout_s: float = 15.0) -> None:
    data = json.dumps(payload).encode("utf-8")
    for attempt in range(_WEBHOOK_MAX_ATTEMPTS):
        req = urllib.request.Request(
            url,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=timeout_s) as resp:  # nosec B310 — webhook; scheme is always https (caller-validated URL from config)
                resp.read()
            return
        except urllib.error.HTTPError as e:
            if e.code >= 500 and attempt < _WEBHOOK_MAX_ATTEMPTS - 1:
                time.sleep(0.5 * (2**attempt))
                continue
            raise
        except urllib.error.URLError:
            if attempt < _WEBHOOK_MAX_ATTEMPTS - 1:
                time.sleep(0.5 * (2**attempt))
                continue
            raise


def _post_form(url: str, body: dict[str, str], timeout_s: float = 15.0) -> None:
    encoded = urllib.parse.urlencode(body).encode("utf-8")
    for attempt in range(_WEBHOOK_MAX_ATTEMPTS):
        req = urllib.request.Request(
            url,
            data=encoded,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=timeout_s) as resp:  # nosec B310 — webhook; scheme is always https (caller-validated URL from config)
                resp.read()
            return
        except urllib.error.HTTPError as e:
            if e.code >= 500 and attempt < _WEBHOOK_MAX_ATTEMPTS - 1:
                time.sleep(0.5 * (2**attempt))
                continue
            raise
        except urllib.error.URLError:
            if attempt < _WEBHOOK_MAX_ATTEMPTS - 1:
                time.sleep(0.5 * (2**attempt))
                continue
            raise


def send_slack_webhook(url: str, text: str, timeout_s: float = 15.0) -> None:
    _post_json(url, {"text": text}, timeout_s=timeout_s)


def send_teams_webhook(url: str, text: str, timeout_s: float = 15.0) -> None:
    # Incoming webhook connector accepts a simple body with "text" in many tenants.
    _post_json(url, {"text": text}, timeout_s=timeout_s)


def send_generic_webhook(url: str, text: str, timeout_s: float = 15.0) -> None:
    _post_json(url, {"text": text}, timeout_s=timeout_s)


def send_telegram(
    bot_token: str, chat_id: str, text: str, timeout_s: float = 15.0
) -> None:
    api = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    _post_form(api, {"chat_id": chat_id, "text": text}, timeout_s=timeout_s)


def _str_or_empty(v: Any) -> str:
    if v is None:
        return ""
    if isinstance(v, str):
        return v.strip()
    return str(v).strip()


def send_single_operator_channel_block(
    block: dict[str, Any],
    text: str,
    *,
    timeout_s: float = 15.0,
) -> tuple[str | None, bool, str | None]:
    """
    Send ``text`` to the first configured URL in one channel block (Slack → Teams → Telegram → generic).

    ``block`` is a flat dict (e.g. one entry from ``operator.channels`` or legacy ``operator``).
    """
    slack = _str_or_empty(block.get("slack_webhook_url"))
    if slack:
        try:
            send_slack_webhook(slack, text, timeout_s=timeout_s)
            return "slack", True, None
        except (urllib.error.URLError, OSError, ValueError) as e:
            return "slack", False, str(e)

    teams = _str_or_empty(block.get("teams_webhook_url"))
    if teams:
        try:
            send_teams_webhook(teams, text, timeout_s=timeout_s)
            return "teams", True, None
        except (urllib.error.URLError, OSError, ValueError) as e:
            return "teams", False, str(e)

    token = _str_or_empty(block.get("telegram_bot_token"))
    chat = _str_or_empty(block.get("telegram_chat_id"))
    if token and chat:
        try:
            send_telegram(token, chat, text, timeout_s=timeout_s)
            return "telegram", True, None
        except (urllib.error.URLError, OSError, ValueError) as e:
            return "telegram", False, str(e)

    generic = _str_or_empty(block.get("generic_webhook_url"))
    if generic:
        try:
            send_generic_webhook(generic, text, timeout_s=timeout_s)
            return "generic", True, None
        except (urllib.error.URLError, OSError, ValueError) as e:
            return "generic", False, str(e)

    return None, False, "no operator webhook configured"


def send_to_first_configured_operator_channel(
    notifications_cfg: dict[str, Any],
    text: str,
    *,
    timeout_s: float = 15.0,
) -> tuple[str | None, bool, str | None]:
    """
    Send ``text`` using legacy flat ``operator`` keys (ignores ``operator.channels``).

    For multi-channel lists, use :func:`send_all_operator_notifications`.

    Returns (channel_or_none, success, error_message).
    """
    op = notifications_cfg.get("operator") or {}
    if not isinstance(op, dict):
        op = {}
    flat = {k: v for k, v in op.items() if k != "channels"}
    return send_single_operator_channel_block(flat, text, timeout_s=timeout_s)


def send_all_operator_notifications(
    notifications_cfg: dict[str, Any],
    text: str,
    *,
    timeout_s: float = 15.0,
) -> list[tuple[str | None, bool, str | None]]:
    """
    Send to every configured operator target.

    If ``operator.channels`` is a non-empty list, each item is one channel block. Otherwise uses
    legacy single-path priority (same as :func:`send_to_first_configured_operator_channel`).
    """
    n = notifications_cfg if isinstance(notifications_cfg, dict) else {}
    op = n.get("operator") or {}
    if not isinstance(op, dict):
        op = {}
    raw_ch = op.get("channels")
    if isinstance(raw_ch, list) and len(raw_ch) > 0:
        results: list[tuple[str | None, bool, str | None]] = []
        for item in raw_ch:
            if not isinstance(item, dict):
                continue
            results.append(
                send_single_operator_channel_block(item, text, timeout_s=timeout_s)
            )
        return results if results else [(None, False, "no operator webhook configured")]
    return [send_to_first_configured_operator_channel(n, text, timeout_s=timeout_s)]


def _channel_block_is_configured(block: dict[str, Any]) -> bool:
    return bool(
        _str_or_empty(block.get("slack_webhook_url"))
        or _str_or_empty(block.get("teams_webhook_url"))
        or (
            _str_or_empty(block.get("telegram_bot_token"))
            and _str_or_empty(block.get("telegram_chat_id"))
        )
        or _str_or_empty(block.get("generic_webhook_url"))
    )


def _resolve_tenant_channel_block(
    tenant_cfg: dict[str, Any], tenant_name: str | None
) -> dict[str, Any] | None:
    """Return one channel block for a tenant webhook, or None."""
    if not isinstance(tenant_cfg, dict):
        return None
    name = _str_or_empty(tenant_name)
    if not name:
        return None
    key = name.lower()
    by_t = tenant_cfg.get("by_tenant") or {}
    if isinstance(by_t, dict) and key in by_t:
        block = by_t[key]
        if isinstance(block, dict) and _channel_block_is_configured(block):
            return block
    if _str_or_empty(tenant_cfg.get("default_slack_webhook_url")):
        return {"slack_webhook_url": tenant_cfg.get("default_slack_webhook_url")}
    if _str_or_empty(tenant_cfg.get("default_generic_webhook_url")):
        return {
            "generic_webhook_url": tenant_cfg.get("default_generic_webhook_url"),
        }
    return None


def build_scan_complete_message(
    summary: dict[str, Any],
    *,
    public_base_url: str | None = None,
) -> str:
    """Format a short pt-BR operator brief (counts + how to fetch report)."""
    sid = summary.get("session_id") or "?"
    total = int(summary.get("total_findings") or 0)
    high = int(summary.get("high") or 0)
    medium = int(summary.get("medium") or 0)
    low = int(summary.get("low") or 0)
    dob = int(summary.get("dob_possible_minor") or 0)
    failures = int(summary.get("scan_failures") or 0)
    tenant = summary.get("tenant_name") or "—"
    tech = summary.get("technician_name") or "—"
    status = summary.get("status") or "completed"
    lines = [
        "Data Boar — scan concluído",
        f"Sessão: {sid}",
        f"Status: {status}",
        f"Achados (total): {total} — HIGH: {high}, MEDIUM: {medium}, LOW: {low}",
        f"Possível menor (DOB_POSSIBLE_MINOR): {dob}",
        f"Falhas de target: {failures}",
        f"Inquilino: {tenant} | Técnico: {tech}",
        "Relatório Excel: página Reports no dashboard ou GET /report (último) ou GET /reports/{session_id}.",
        f"Heatmap: GET /heatmap/{sid}",
    ]
    base = (public_base_url or "").strip().rstrip("/")
    if base:
        lines.append(f"Base URL (se configurada): {base}")
    return "\n".join(lines)


def should_send_scan_complete_notification(
    config: dict[str, Any],
    summary: dict[str, Any],
) -> bool:
    """Return True if notifications are enabled and filters allow sending."""
    n = config.get("notifications") or {}
    if not isinstance(n, dict):
        return False
    if not bool(n.get("enabled", False)):
        return False
    is_err = (summary.get("status") or "") == "completed_errors"
    notify_fail = bool(n.get("notify_on_failure", True))
    # Worker-level failures: only when explicitly allowed (default on).
    if is_err:
        return notify_fail

    on_complete = bool(n.get("on_scan_complete", True))
    if not on_complete:
        return False
    if bool(n.get("notify_only_if_high_or_critical", False)):
        high = int(summary.get("high") or 0)
        dob = int(summary.get("dob_possible_minor") or 0)
        if high < 1 and dob < 1:
            return False
    return True


def _dedupe_should_skip(session_id: str, n: dict[str, Any]) -> bool:
    if not bool(n.get("dedupe_scan_complete_per_session", True)):
        return False
    with _SCAN_COMPLETE_OK_LOCK:
        return session_id in _SCAN_COMPLETE_OK_SESSIONS


def _dedupe_mark_success(session_id: str) -> None:
    with _SCAN_COMPLETE_OK_LOCK:
        if len(_SCAN_COMPLETE_OK_SESSIONS) >= _MAX_DEDUPE_SESSIONS:
            _SCAN_COMPLETE_OK_SESSIONS.clear()
        _SCAN_COMPLETE_OK_SESSIONS.add(session_id)


def _maybe_record_notification_audit(
    db_manager: Any,
    config: dict[str, Any],
    *,
    session_id: str | None,
    trigger: str,
    recipient: str,
    channel: str | None,
    success: bool,
    err: str | None,
) -> None:
    """Append one row to notification_send_log when enabled (default on). Never raises."""
    n = config.get("notifications") if isinstance(config, dict) else None
    if not isinstance(n, dict) or not bool(n.get("notify_audit_log", True)):
        return
    if not hasattr(db_manager, "record_notification_send_log"):
        return
    try:
        db_manager.record_notification_send_log(
            session_id=session_id,
            trigger=trigger,
            recipient=recipient,
            channel=channel,
            success=success,
            error_message=err,
        )
    except Exception as e:
        # Audit rows are best-effort; keep notification flow non-blocking.
        _LOGGER.debug("notification audit row skipped: %s", e)


def notify_scan_complete_sync(
    config: dict[str, Any],
    db_manager: Any,
    session_id: str,
) -> None:
    """
    If configured, send operator notification(s) and optional tenant copy with session summary.

    Call after the session is finished and (for CLI) after report generation if desired.
    Does not raise on webhook errors; logs warnings.
    """
    summary = db_manager.get_session_scan_summary_for_notification(session_id)
    if not should_send_scan_complete_notification(config, summary):
        return
    n = config.get("notifications") or {}
    if not isinstance(n, dict):
        n = {}
    if _dedupe_should_skip(session_id, n):
        _LOGGER.info(
            "Notification skipped (dedupe scan-complete): session=%s",
            session_id,
        )
        return
    public_base = (n.get("public_base_url") or "").strip() or None
    text = build_scan_complete_message(summary, public_base_url=public_base)
    op_results = send_all_operator_notifications(n, text)
    any_ok = any(r[1] for r in op_results)
    for channel, ok, err in op_results:
        if ok:
            _LOGGER.info(
                "Notification sent (scan complete): session=%s channel=%s",
                session_id,
                channel,
            )
        else:
            _LOGGER.warning(
                "Notification failed (scan complete): session=%s channel=%s err=%s",
                session_id,
                channel,
                err,
            )
        _maybe_record_notification_audit(
            db_manager,
            config,
            session_id=session_id,
            trigger="scan_complete",
            recipient="operator",
            channel=channel,
            success=ok,
            err=err,
        )

    tenant_cfg = n.get("tenant") or {}
    if isinstance(tenant_cfg, dict):
        tblock = _resolve_tenant_channel_block(
            tenant_cfg,
            summary.get("tenant_name") if isinstance(summary, dict) else None,
        )
        if tblock:
            tch, tok, terr = send_single_operator_channel_block(tblock, text)
            if tok:
                any_ok = True
                _LOGGER.info(
                    "Tenant notification sent (scan complete): session=%s channel=%s",
                    session_id,
                    tch,
                )
            else:
                _LOGGER.warning(
                    "Tenant notification failed (scan complete): session=%s channel=%s err=%s",
                    session_id,
                    tch,
                    terr,
                )
            _maybe_record_notification_audit(
                db_manager,
                config,
                session_id=session_id,
                trigger="scan_complete",
                recipient="tenant",
                channel=tch,
                success=tok,
                err=terr,
            )

    if any_ok:
        _dedupe_mark_success(session_id)


def notify_scan_complete_background(
    config: dict[str, Any],
    db_manager: Any,
    session_id: str,
) -> None:
    """Fire-and-forget scan-complete notification (does not block CLI/API)."""

    def _run() -> None:
        try:
            notify_scan_complete_sync(config, db_manager, session_id)
        except Exception as e:
            _LOGGER.warning(
                "notify_scan_complete_background failed: session=%s err=%s",
                session_id,
                e,
            )

    threading.Thread(target=_run, daemon=True).start()


def send_manual_operator_message(
    config: dict[str, Any],
    text: str,
    *,
    timeout_s: float = 15.0,
    db_manager: Any | None = None,
) -> tuple[str | None, bool, str | None]:
    """
    Part A (off-band): send a free-form message if notifications.enabled is true
    and at least one operator channel is configured. Uses the same routing as scan-complete
    (all ``operator.channels`` entries, or legacy single path).

    Optional ``db_manager``: when set, append rows to ``notification_send_log`` (manual trigger).
    """
    n = config.get("notifications") or {}
    if not isinstance(n, dict) or not bool(n.get("enabled", False)):
        return None, False, "notifications.enabled is false"
    results = send_all_operator_notifications(n, text, timeout_s=timeout_s)
    if not results:
        return None, False, "no operator webhook configured"
    for channel, ok, err in results:
        if db_manager is not None:
            _maybe_record_notification_audit(
                db_manager,
                config,
                session_id=None,
                trigger="manual",
                recipient="operator",
                channel=channel,
                success=ok,
                err=err,
            )
    any_ok = any(r[1] for r in results)
    if any_ok:
        labels = "+".join(r[0] for r in results if r[1] and r[0]) or "operator"
        return labels, True, None
    first_err = next((r[2] for r in results if r[2]), "all channels failed")
    return None, False, first_err
