# Plan: Readiness and operations (meta / “see the forest”)

**Status:** Pending
**Date:** 2026-03-15
**Authors:** Fabio Leitao
**Priority:** H0

**Purpose:** Capture aspects that are easy to miss when focused on feature plans—so you can decide what to formalise, automate, or document next. No obligation to implement everything; use as a prioritised checklist.

---

## 1. Do you need a custom MCP?

## Recommendation: No, unless you have a specific gap.

- **What you have:** Cursor + Git + CI (tests, Ruff, pip-audit, Sonar when configured) + existing MCPs (e.g. browser, GitKraken) + good docs and plans. That already covers most development and review workflows.
- **When a custom MCP might be worth it:** You need to automate something Cursor and existing tools don’t cover—e.g. calling an internal API, driving a proprietary system, or generating project-specific reports from your repo. Building and maintaining an MCP has a cost; only add one if the benefit is clear (e.g. “we run this check every release and it saves us X hours”).
- **Conclusion:** You’re fine without a custom MCP for current goals. Revisit if a concrete automation need appears.

---

## 2. Workflow and automation (quick wins)

| Item                                    | To-do / status                                                                                                                                                                                                                         |
| ------                                  | ----------------                                                                                                                                                                                                                       |
| **Ruff in CI**                          | Done (lint job in `ci.yml`).                                                                                                                                                                                                           |
| **Pre-commit**                          | Done: Ruff check (--fix) and Ruff format (--check) run on commit. See `.pre-commit-config.yaml` and rule `pre-commit-ruff`. Optional: add markdown lint to pre-commit if desired.                                                      |
| **Check-all script**                    | Done: `scripts/check-all.ps1` wraps `scripts/pre-commit-and-tests.ps1` so `.\scripts\check-all.ps1` runs lint/format (pre-commit) + full pytest in one command. Use as a local gate before Commit/PR when Agent Review is misbehaving. |
| **Release checklist**                   | Done: In CONTRIBUTING (audit, docs, secrets, lockfile). Release history = git + `docs/releases/`; no separate CHANGELOG required.                                                                                                      |
| **QUALITY_WORKFLOW_RECOMMENDATIONS.md** | Done: Lists Bandit, Semgrep, mypy, SBOM. Adopt incrementally when you want an extra safety layer; not required for “being set.”                                                                                                        |

---

## 3. Cursor automation (rules and skills – reminders)

- **Rules:** Later, add Cursor RULEs encoding production hardening defaults (loopback host for non-container runs; production profile requires API key; no new `try/except/pass` without logging; no plaintext passwords in tracked configs).
- **Skills:** Later, add a “Security hardening checklist” skill that walks WABIX findings (host/auth/secrets/Excel formula escaping/parse gates) before marking a change as prod-ready.

## 4. Prioritised checklist (release, security, runbooks, compliance, onboarding, dependency policy)

Each item is a small doc update or script. Status: **Done** | **Not started** | **Optional**. When you implement one, do the change, update EN + pt-BR if docs, then set Status to Done in this file.

### 4.1 Release and versioning

| To-do                                                                                                                                                                                      | Status      |
| -------                                                                                                                                                                                    | --------    |
| Changelog discipline: release history = git + `docs/releases/`; every tagged release has an entry in `docs/releases/`. See CONTRIBUTING.                                                   | Done        |
| Optional: add short “Compatibility and deprecation” sentence in CONTRIBUTING or USAGE (e.g. we avoid breaking config keys; when we deprecate, we document for at least one minor version). | Not started |

### 4.2 Security response

| To-do                                                                                                                                                                                         | Status   |
| -------                                                                                                                                                                                       | -------- |
| Vulnerability reporting: do not open public issue with exploit; maintainer response. Optional SLAs in SECURITY.md (acknowledge 5 working days; high/critical fix or document within 30 days). | Done     |
| Dependabot security PRs: optional SLA in SECURITY.md (P0; merge or respond within 5 working days). CONTRIBUTING points to SECURITY.                                                           | Done     |
| Optional: “Review SLAs annually” or leave as-is.                                                                                                                                              | Optional |

### 4.3 Operations and runbooks

| To-do                                                                                                                                                                                             | Status      |
| -------                                                                                                                                                                                           | --------    |
| Operator runbook one-pager: if app is down → check /health and logs, config and CONFIG_PATH, disk and SQLite path, restart or scale; if scan hangs → … Place in docs or extend OBSERVABILITY_SRE. | Not started |
| Backup and restore: minimal “what to backup” (config, SQLite, report dir) and “how to restore” in USAGE or deploy docs.                                                                           | Not started |

### 4.4 Compliance and evidence (you are an audit/compliance tool)

| To-do                                                                                                                                                                                  | Status      |
| -------                                                                                                                                                                                | --------    |
| “Compliance and evidence” subsection in SECURITY or dedicated doc: how we prove our own compliance (access control to config/repo, audit trail, no secrets in logs, dependency audit). | Not started |
| Data retention: mention in USAGE or deploy docs “consider retention policy for report.output_dir and sqlite_path” and who can delete.                                                  | Not started |

### 4.5 Onboarding

| To-do                                                                                                                                                    | Status      |
| -------                                                                                                                                                  | --------    |
| Short “Onboarding” checklist in CONTRIBUTING (e.g. 1. Clone, 2. uv sync, 3. Copy config example, 4. uv run pytest, 5. Read PLANS_TODO for current work). | Not started |
| Optional: handover or “key decisions” doc (why we chose X, where the traps are) for bus factor.                                                          | Optional    |

### 4.6 Dependencies and upgrades

| To-do                                                                                                                                                                                                                         | Status                   |
| -------                                                                                                                                                                                                                       | --------                 |
| Python/platform support sentence in README or CONTRIBUTING: we support Python 3.12 and 3.13 on Linux, macOS, Windows; we will announce deprecation of a version at least one minor release ahead.                             | Not started              |
| Optional: written “upgrade policy” (e.g. we refresh lockfile at least every N months or when a critical CVE appears).                                                                                                         | Optional                 |
| Docker/Dependabot vulnerability triage: for each release cycle, review GitHub Dependabot alerts and Docker Scout quickview for the base image; classify P0/P1 vulns and decide which to patch in-code vs via base-image bump. | Tracked (partially done) |
| Future Cursor rule/skill: add a security rule/skill that reminds the agent to check Dependabot and Docker Scout summaries before declaring a release “prod-ready”, within token constraints.                                  | Optional                 |

### 4.7 W-KPI baseline (release / CI / security ops)

Token-aware baseline with 2 manual KPIs (no new tooling required):

| KPI                          | How to measure                                                                           | Cadence | Initial target                       |
| ---                          | ---                                                                                      | ---     | ---                                  |
| CI pass rate                 | Last 10 PRs to `main`: count green CI checks before merge (`successful PRs / total PRs`) | Weekly  | >= 90%                               |
| Security maintenance latency | Business days between opening and merge/mitigation of high/critical Dependabot alert/PR  | Weekly  | <= 5 business days for high/critical |

Notes:

- Data sources: GitHub PR list/checks + Dependabot alerts/PR timestamps.
- Keep a small markdown note per release cycle in `docs/releases/X.Y.Z.md` with the latest KPI snapshot.
- Lightweight export script available: `python scripts/kpi-export.py --limit-prs 10` (stdout) or `--out docs/releases/kpi_snapshot.md`.
- **Optional automation (backlog, non-blocking):** scheduled or `workflow_dispatch` GitHub Action runs `kpi-export.py`, uploads **artifact** (short retention) or posts a summary to Slack/Telegram via secrets—**never** commit tokens. Combine with [OPERATOR_NOTIFICATION_CHANNELS.md](../ops/OPERATOR_NOTIFICATION_CHANNELS.md) for “ping me when the snapshot runs or fails.”

---

## 5. How to use this plan

- **Token-aware:** Each checklist item can be done in one short session; open only this file plus the doc or script you edit. See [TOKEN_AWARE_USAGE.md](TOKEN_AWARE_USAGE.md) for short vs long-term and one-session workflow.
- **This file is the readiness checklist.** Items are small (doc update or script). No obligation to implement every to-do; “Optional” and “When needed” are valid.
- **When you implement an item:** Do the change (doc or script). If it’s docs, update EN + pt-BR per the documentation policy. Then set the item’s Status to **Done** in §2 or §3 of this file.
- **Revisit when:** You do a release, onboard someone new, or get an audit request. Use the checklist to decide what to formalise next.
- **PLANS_TODO** lists the same goal categories (Release, Security response, Runbooks, Compliance evidence, Onboarding, Dependency policy, Check-all script) and links here so the team doesn’t forget. Status is updated only in this file to avoid duplication.

---

*Last updated: restructured §4 as prioritised checklist with explicit to-dos and Status; added check-all script to §2; added §3 reminder for future Cursor rules/skills; added Docker/Dependabot vulnerability triage items; updated §5 workflow.*
