# Plan: Off-band notifications and scan-completion notifications

**Status:** Pending
**Date:** 2026-03-15
**Authors:** Fabio Leitao
**Priority:** H2

**Synced with:** [PLANS_TODO.md](PLANS_TODO.md) (central to-do list)

## When implementing steps: update docs and tests; then update PLANS_TODO.md and this file.

This plan covers (1) **off-band notifications to you** (the operator/developer) about progress or completion of important work (e.g. major steps, large commits, crucial releases, or completion of tasks you request in this environment), and (2) **in-app notifications** so that when a **scan completes** (one-shot CLI, scheduled, or web-started), the **operator and/or tenant** receive a short brief (total findings, by severity, DOB possible minor) and a reminder of how to download the report. Channels considered: **Signal, WhatsApp, Telegram, Slack, Microsoft Teams, SMS**. The plan also recommends **improvements and extensions** of these capabilities.

---

## Part A: Off-band notifications to you (task / milestone completion)

### Goal (off-band to you)

Receive a notification **outside the IDE** when:

- A requested task or instruction in this coding session is **complete** (or at major sub-steps).
- **Major project events** occur: large commits, crucial releases, or other milestones you care about.

### Constraint

The **Cursor/IDE environment** does not natively send messages to Signal, WhatsApp, Telegram, Slack, Teams, or SMS. Notifications must be triggered by something that **can** call an API or webhook: a **script you run**, a **CI job** (e.g. GitHub Actions), or a **small helper** in the project that posts to a configurable webhook.

### Recommended approach

1. **Generic webhook notifier in the project**
   - Add a small module or script (e.g. `utils/notify.py` or `scripts/notify_webhook.py`) that:
     - Accepts a **message** and an optional **channel** or **webhook URL** (from config or env).
     - Supports one or more **back ends**: Slack incoming webhook, Teams incoming webhook, Telegram Bot API, generic HTTP POST (so you can use IFTTT/Zapier for WhatsApp/Signal/SMS).
   - **No secrets in repo:** Webhook URLs and API keys come from **config** (e.g. `notifications.slack_webhook_url`) or **environment variables** (e.g. `NOTIFY_SLACK_WEBHOOK`), with config taking precedence; secrets never committed.
   - You (or a Cursor rule / script) can **call** this notifier at the end of a session or after a major step, e.g. `python scripts/notify_webhook.py "Scan-complete plan done"` or from CI on release tag.

1. **Use existing integrations**
   - **Slack:** Incoming webhook (POST JSON to URL). Easiest.
   - **Teams:** Incoming webhook (Connector). Similar.
   - **Telegram:** Bot API `sendMessage` (need bot token and chat id).
   - **WhatsApp / Signal / SMS:** Often via third-party (Twilio, Vonage, or IFTTT/Zapier that subscribe to a webhook or email). The project can expose a **generic HTTP webhook**; you configure IFTTT/Zapier to forward to WhatsApp/Signal/SMS.

1. **When to trigger “task complete”**
   - **Manual:** Run the notifier script after you finish a conversation or a big change.
   - **CI:** In GitHub Actions (or similar), on events such as “push to main”, “release published”, “tag created”, call the same webhook or script with a short message (e.g. “Release v1.6.0 cut”) so you get notified off-band.
   - **Cursor/agent:** No direct “when this chat task is done, call webhook” in Cursor today; a **Cursor rule** could remind you to run the notifier at the end of important tasks, or we document “after major plan/feature, run: …”.

### Deliverables (Part A)

- Optional **notifier module/script** with:
- Generic webhook POST (JSON body with `text` or `message`).
- Optional adapters for Slack, Teams, Telegram (so one config can choose channel).
- **Config** (optional): e.g. `notifications.notify_on_scans`, `notifications.webhook_url` or `notifications.slack_webhook_url`, etc., read from config or env.
- **Docs:** How to set up Slack/Teams/Telegram/webhook, and how to trigger from CI or manually for “task/milestone complete”.

---

## Part B: In-app notifications when a scan completes

### Goal (scan-complete to operator/tenant)

When a **scan completes** (whether triggered by **one-shot CLI**, **scheduled job**, or **web** POST /scan or /start), optionally notify the **operator** and/or **tenant** with:

- A **short brief:** total findings, and counts by severity (e.g. critical if we add it, high, medium, low/minor) and **DOB possible minor** (special attention).
- A **reminder** of how to **download the report** (e.g. “Download report: open Reports page or GET /report; for this session: GET /reports/{session_id}”).

### Triggers

- **CLI one-shot:** After `start_audit()` and `generate_final_reports()` in main.py, if notifications are enabled, call notifier with session_id and summary.
- **Web-started scan:** After the background scan finishes and report is generated (e.g. in the same flow that today updates status), if enabled, send notification.
- **Scheduled scan:** When the scheduler runs the audit and report generation, after success (and optionally on failure), send notification.

### Message content (scan-complete brief)

- **Total findings** (database + filesystem).
- **By severity:** HIGH, MEDIUM, LOW (and optional “critical” if we introduce that level).
- **DOB possible minor:** Count of findings that indicate possible minor data (special attention); see report recommendations.
- **Scan failures:** Number of targets that failed (unreachable, auth, timeout).
- **Tenant / technician** (if set) for context.
- **How to download:** “Download the Excel report from the Reports page (Dashboard) or via GET /report (latest) or GET /reports/{session_id}. Heatmap: GET /heatmap or GET /heatmap/{session_id}.”
- **Optional:** Base URL of the app (e.g. from config or request) so the message can include a direct link to the reports list.

### Recipients

- **Operator:** Configurable (e.g. one Slack channel, one Telegram chat, or a list of webhooks). Stored in config or env (e.g. `notifications.operator_webhook` or `NOTIFY_OPERATOR_SLACK`).
- **Tenant:** Optional. If tenant_name is set for the scan, config could map tenant to a webhook or channel (e.g. `notifications.tenant_webhooks.acme_corp: url`); otherwise no tenant notification or use a default channel.

### Channels (implementation priority)

| Channel             | Typical method                                              | Priority                       |
| ------------        | ---------------------------                                 | --------                       |
| **Slack**           | Incoming webhook                                            | High                           |
| **Teams**           | Incoming webhook (Connector)                                | High                           |
| **Telegram**        | Bot API sendMessage                                         | High                           |
| **Generic webhook** | HTTP POST (for IFTTT/Zapier → WhatsApp, Signal, email, SMS) | High                           |
| **WhatsApp**        | Often via Twilio/API or IFTTT                               | Medium (after generic webhook) |
| **Signal**          | Often via third-party or bot                                | Medium                         |
| **SMS**             | Twilio / Vonage / IFTTT                                     | Medium                         |

Implementing **generic webhook + Slack + Teams + Telegram** covers most cases; WhatsApp/Signal/SMS can be reached via a generic webhook plus external tool.

### Config schema (example)

```yaml
notifications:
  enabled: false   # default off; opt-in
  on_scan_complete: true
  # Operator: single channel or list
  operator:
    slack_webhook_url: ${NOTIFY_SLACK_WEBHOOK}   # or inline (not recommended in repo)
    # OR teams_webhook_url, telegram_bot_token + chat_id, or generic webhook_url
  tenant:
    # Optional: map tenant_name to webhook or channel
    default_webhook_url: ${NOTIFY_TENANT_WEBHOOK}
  message_template: null   # optional override; else use built-in brief
```

Secrets: prefer env vars (e.g. `NOTIFY_SLACK_WEBHOOK`) or a secrets vault (see Secrets plan); config can reference `${VAR}` for expansion.

---

## Part C: Recommendations and improvements

1. **Only notify when enabled:** Default `notifications.enabled: false`; no traffic or secrets until the operator configures it.
1. **Optional “only if important”:** Config flag e.g. `notify_only_if_high_or_critical: true` so you only get a message when there is at least one HIGH (or critical) or DOB possible minor finding; reduces noise.
1. **Digest vs immediate:** For scheduled scans, consider a **daily digest** (one message per day with all completed scans and totals) vs **immediate** per scan; configurable.
1. **Retry and rate limiting:** If the webhook POST fails (5xx, timeout), retry with backoff (e.g. 1–3 times). Rate limit outbound notifications (e.g. max one per session per channel) to avoid spam.
1. **Audit log:** Log that a notification was sent (session_id, channel, timestamp) in a small table or append-only log; do not log the message body if it contains counts that might be sensitive in some policies.
1. **i18n:** Message template or body could be localised (e.g. pt_BR) from config or locale setting.
1. **Link to report:** When the app has a known base URL (e.g. from config or request), include in the message a direct link to the reports list or to GET /reports/{session_id} so the operator can open it in one click.
1. **Failure notifications:** Optionally notify when a scan **fails** (e.g. all targets failed or engine error) so the operator can react; separate config flag.
1. **Off-band “task done” (Part A):** In CI, trigger the same notifier on release tag or on main build success so you get “Release vX.Y.Z published” or “Build green” on Slack/Telegram without opening the repo.

---

## Implementation phases (to-dos)

### Phase 1: Notifier module and config

| #   | To-do                                                                                                                                                                        | Status                                                  |
| --- | ---------------------------------------------------------------------                                                                                                        | ------                                                  |
| 1.1 | Add optional config section `notifications` (enabled, on_scan_complete, operator webhook/channel, tenant optional). Secrets from env or config; document no secrets in repo. | ✅ Done (`config/loader.py`)                             |
| 1.2 | Implement small notifier (e.g. utils/notify.py or scripts/notify_webhook.py): generic HTTP POST, optional Slack/Teams/Telegram adapters; message body as JSON or form.       | ✅ Done (`utils/notify.py`, `scripts/notify_webhook.py`) |
| 1.3 | Document how to get Slack/Teams/Telegram webhooks and how to trigger “task/milestone” notification from CI or manually (Part A).                                             | ✅ Done (`docs/USAGE.md` §5.1, `USAGE.pt_BR.md`)         |

### Phase 2: Scan-complete summary and trigger

| #   | To-do                                                                                                                                                                                                         | Status                                                                                                                                  |
| --- | ---------------------------------------------------------------------                                                                                                                                         | ------                                                                                                                                  |
| 2.1 | Add helper to build **scan-complete summary** from session: total findings, by sensitivity_level (HIGH, MEDIUM, LOW), DOB possible minor count, scan failures count, tenant/technician.                       | ✅ Done (`LocalDBManager.get_session_scan_summary_for_notification`)                                                                     |
| 2.2 | After report generation (CLI one-shot in main.py, and web background scan completion in api/routes.py), if notifications.enabled and on_scan_complete, call notifier with summary and “how to download” text. | ✅ Done (background thread; CLI after report; API after `run_targets` / `scan_database`)                                                 |
| 2.3 | Include in message: session_id, brief counts, link or instructions for report download (Reports page, GET /report, GET /reports/{session_id}).                                                                | ✅ Done (`build_scan_complete_message`)                                                                                                  |
| 2.4 | Optional: notify_only_if_high_or_critical and failure notification (notify on scan failure).                                                                                                                  | ✅ Partial (`notify_only_if_high_or_critical`, `notify_on_failure` for `completed_errors`; worker failure semantics in `core/engine.py`) |

### Phase 3: Tenant and multi-channel

| #   | To-do                                                                                                                     | Status                                                                                                                                                                     |
| --- | ---------------------------------------------------------------------                                                     | ------                                                                                                                                                                     |
| 3.1 | If tenant_name is set and notifications.tenant is configured, send a copy to tenant channel/webhook (or default_webhook). | ✅ Done (`tenant.by_tenant`, `default_*` in `config/loader.py`; `notify_scan_complete_sync` in `utils/notify.py`)                                                           |
| 3.2 | Support multiple operator channels (e.g. Slack + Telegram) from config list.                                              | ✅ Done (`operator.channels` list)                                                                                                                                          |
| 3.3 | Retry on 5xx/timeout; rate limit per session per channel.                                                                 | 🔄 Partial (retries in `utils/notify.py`; **dedupe** per `session_id` after successful send via `dedupe_scan_complete_per_session`; fine-grained per-channel cap → backlog) |

### Phase 4: Docs, audit, and improvements

| #   | To-do                                                                                                                    | Status                                                                                                              |
| --- | ---------------------------------------------------------------------                                                    | ------                                                                                                              |
| 4.1 | USAGE and SECURITY: document notifications config, secrets handling, and “how to download report” text used in messages. | ✅ Done (USAGE §5.1; root **SECURITY.md** + **docs/SECURITY.md** / **.pt_BR.md** technician notes)                   |
| 4.2 | Optional: audit log of notifications sent (session_id, channel, timestamp).                                              | ✅ Done (`notification_send_log` table + `record_notification_send_log`; `notify_audit_log` config; no message body) |
| 4.3 | Recommendations (digest, i18n, link to report, failure notify) as config options or future work in plan.                 | ⬜ (``public_base_url`` / report hints already in scan-complete message; digest/i18n → backlog)                      |
| 4.4 | Tests: unit test for summary builder; optional integration test with mock webhook.                                       | ✅ Partial (summary + webhook mocks in ``tests/test_notify.py``; manual script audit covered)                        |

---

## Dependencies and constraints

- **Secrets:** Webhook URLs and API keys must not be committed; use env or vault (see Secrets plan). Config can reference `${VAR}`.
- **Backward compatible:** Notifications disabled by default; no behaviour change when not configured.
- **No blocking:** Sending a notification must not block report generation or the scan flow; fire-and-forget or background task, with retry.

---

## Conflict and placement in roadmap

- **No conflicts.** Additive (config, notifier module, hook after report generation). Can follow Secrets vault Phase A so that webhook URLs can optionally be stored in env or vault.
- **Placement:** See [PLANS_TODO.md](PLANS_TODO.md). Can be implemented after Configurable timeouts or in parallel with other plans.

---

## Last updated with plan file. Update PLANS_TODO.md when completing or adding to-dos.
