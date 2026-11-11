# Plan: Governance exports — RoPA evidence, SARIF, and SIEM / webhook findings push

**Status:** Complete (archived under `docs/plans/completed/`)
**Date:** 2026-11-10
**Authors:** Fabio Leitao
**Priority:** H2 U2
**Depends on:** Notifications flow (`utils/notify.py`, `notification_send_log`); session diff (`LocalDBManager.diff_sessions`); tier map (`core/licensing/tier_features.py`)
**GitHub:** [#837](https://github.com/DataBoar/data-boar/issues/837) (RoPA / Art. 30 export) · [#838](https://github.com/DataBoar/data-boar/issues/838) (SARIF / SIEM / webhook push)

<!-- plans-hub-summary: Pro+ governance exports: a RoPA (GDPR Art. 30 / LGPD Art. 37) evidence workbook built from scan metadata with unknown fields left as "A COMPLETAR", a SARIF 2.1.0 export, and a post-scan SIEM/webhook findings push whose payload carries the new-since-last-scan delta. Evidence, not legal conclusion; metadata only. -->
<!-- plans-hub-related: PLAN_NOTIFICATIONS_OFFBAND_AND_SCAN_COMPLETE.md, completed/PLAN_CLI_VALIDATE_DIFF_AND_DSAR_EXPORT.md, PLAN_FINDINGS_CORPORATE_REPOSITORY_EXPORT.md -->

## Purpose

Two gaps shared one design:

- **RoPA (#837):** a DPO expects a Record of Processing Activities, not a list of findings. The scan can supply the technical half (which personal-data categories, where, how sensitive, under which norm tags). It cannot supply the controller/DPO, purposes, legal basis, recipients, transfers, retention or security measures (Art. 30(1)(a)–(g)).
- **Findings push (#838):** `/findings` is a pull. A security team wants the result as an event in its SIEM, and wants to know what is **new**, not the same total every week.

Language everywhere is **evidence**, never a legal conclusion, and exports are **metadata only** (no samples).

## Relationship to other plans

- **[PLAN_NOTIFICATIONS_OFFBAND_AND_SCAN_COMPLETE.md](../PLAN_NOTIFICATIONS_OFFBAND_AND_SCAN_COMPLETE.md)** — the push extends its scan-complete hook; it does not change the human brief, channels or tenant routing. The delta fields it lacked (new count, resolved count, previous session) are provided here.
- **[PLAN_CLI_VALIDATE_DIFF_AND_DSAR_EXPORT.md](PLAN_CLI_VALIDATE_DIFF_AND_DSAR_EXPORT.md)** — reuses the session-diff identity keys; `new_findings_count` / `resolved_count` always agree with `--diff`. Same export CLI pattern as `--export-dsar`.
- **[PLAN_FINDINGS_CORPORATE_REPOSITORY_EXPORT.md](../PLAN_FINDINGS_CORPORATE_REPOSITORY_EXPORT.md)** — complementary: that plan syncs rows into a customer database (`findings_sink`); this one pushes a per-scan event.
- Tier ladder: [SUBSCRIPTION_TIERS.md](../../SUBSCRIPTION_TIERS.md) lists SARIF/SIEM push and RoPA export at Pro+.

## Non-goals

- Prometheus `/metrics`, a Signal channel and syslog (RFC 5424) output — separate fronts.
- Native Sentinel / Elastic adapters (they use the generic webhook adapter).
- Automatic legal-basis or purpose inference; any claim of compliance.
- Exporting samples or content.

## Design decisions

- **One metadata view** (`core/findings_common.py`) shared by RoPA, SARIF and the push, keyed like `diff_sessions`.
- **Tier:** explicit `ropa_export` and `findings_siem_push` = Pro+ in `FEATURE_TIER_MAP` (an absent key would fall through to Community). SARIF export and the push share `findings_siem_push`.
- **Baseline:** most recent earlier session that finished (`completed` / `completed_errors`) with the same scope hash; none → `null` delta (no alert flood on the first run).
- **Push hardening:** env-var-only token, https (loopback may use http), SSRF guard + connection pinned to validated IPs, no redirects, capped response/payload, bounded retries, redacted logs.
- **Hook placement:** the push runs before, and independently of, the human-brief filters; a failure never blocks the brief or the scan. The one-shot CLI waits (bounded) for the notification thread.

## Phases

| Phase | Deliverable | Status |
| ----- | ----------- | ------ |
| A | Tier map keys + gating tests (`ropa_export`, `findings_siem_push`) | ✅ Done |
| B | Shared findings view + session delta (`core/findings_common.py`) | ✅ Done |
| C | RoPA evidence export: `--export-ropa`, `ropa:` config block + validation, XLSX + JSON, `A COMPLETAR` | ✅ Done |
| D | SARIF 2.1.0 export: `--export-sarif`, structural validation tests | ✅ Done |
| E | Findings push: config + validation, JSON/SARIF envelopes, `splunk_hec` adapter, delta, SSRF/https/redirect/size/retry, notify hook, audit rows | ✅ Done |
| F | Offline tests (loopback server, TLS fail-closed), secrets-never-logged tests | ✅ Done |
| G | Docs EN + pt-BR (USAGE, SECURITY, TECH_GUIDE), man pages, operator-help manifest, bash completion, README pitch | ✅ Done |

## Acceptance (met)

- [x] `--export-ropa` writes `.xlsx` + `.json`; without the `ropa:` block every Art. 30(1) field the scan cannot know is `A COMPLETAR`.
- [x] `--export-sarif` emits SARIF 2.1.0 (rule per detector, level from sensitivity, logical/physical locations, fingerprints, no samples).
- [x] Push payload carries `new_findings_count`, `resolved_count`, `previous_session_id`; `splunk_hec` sends `Authorization: Splunk <token>`.
- [x] Tests are network-free; tier gating blocks Community/Std/Pro and allows Pro+/Enterprise/Open.
- [x] Token and URL path/query never appear in logs, results or audit rows.

**Synced with:** [PLANS_TODO.md](../PLANS_TODO.md)
