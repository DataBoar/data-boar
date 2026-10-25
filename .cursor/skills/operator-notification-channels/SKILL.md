---
name: operator-notification-channels
description: >-
  When implementing CI pings, KPI exports, or operator alerts, use at least two channels
  (GitHub + Slack and/or Signal). Telegram is not used for Data Boar operator notifications in this repo; keep secrets out of git.
---

# Operator notification channels

## When to use

- Adding or editing **GitHub Actions** that should alert a human (failures, long jobs, KPI runs).
- Discussing **Slack, Signal, or GitHub mobile** for “reach the operator” (not Telegram for this maintainer policy).
- Extending **scripts/kpi-export.py** automation with notify-on-complete.

## Instructions

1. Read **[docs/ops/OPERATOR_NOTIFICATION_CHANNELS.md](../../../docs/ops/OPERATOR_NOTIFICATION_CHANNELS.md)** (EN + pt-BR sibling).
1. **Tier A:** GitHub (watch, failed workflows, Issue `@mention`).
1. **Tier B:** Slack incoming webhook—**never** commit URLs; use `${{ secrets.SLACK_WEBHOOK_URL }}`. Workflows: **`Slack operator ping (manual)`**, **`Slack CI failure notify`**. Optional **variable** **`SLACK_MENTION_USER_ID`** for mentions—see **OPERATOR_NOTIFICATION_CHANNELS.md** §4.2 D).
1. **Tier C (chat, non-Slack):** Signal only—`signal-cli` / **signald** Docker REST on LAN; secret e.g. `SIGNAL_NOTIFY_URL`. **Telegram is not** a recommended path for this repository (maintainer policy).
1. For **KPI:** optional scheduled `workflow_dispatch` + artifact or chat summary per [PLAN_READINESS_AND_OPERATIONS.md](../../../docs/plans/PLAN_READINESS_AND_OPERATIONS.md) §4.7.
1. **X editorial pace (local, gitignored hub):** [scripts/social-x-pace-remind.ps1](../../../scripts/social-x-pace-remind.ps1) + **`SLACK_WEBHOOK_URL`** in env posts to the same Slack channel as Actions; see **OPERATOR_NOTIFICATION_CHANNELS.md** §6 and session keywords **`x-pace-check`** / **`x-posted`**.

## Legacy Git + cleanup

- **Legacy remote tidy:** [docs/ops/BRANCH_AND_DOCKER_CLEANUP.md](../../../docs/ops/BRANCH_AND_DOCKER_CLEANUP.md) §7 (optional `*-legacy-and-history-only` remote, not python2).
