# Plan: Microsoft 365 read-only connectors via Microsoft Graph (SharePoint Online, OneDrive, Exchange Online)

**Status:** In progress (design and Phase 0/1 delegated mode; no connector code merged yet)
**Date:** 2026-11-10 (updated 2026-11-17)
**Authors:** Fabio Leitao
**Priority:** H1
**GitHub:** [#2206](https://github.com/DataBoar/data-boar/issues/2206)
**Depends on:** [PLAN_CONNECTOR_TIER_GATING.md](PLAN_CONNECTOR_TIER_GATING.md) (fail-closed tier map, #854); token-host allowlist (#2007, done)
**Tier (default for new features):** Enterprise. New features start at Enterprise and are lowered only after validation, by operator decision. The SharePoint on-prem, PowerBI and Dataverse connectors are Pro today; this connector is not assumed to follow them.

<!-- plans-hub-summary: Read-only Microsoft 365 inventory via Microsoft Graph: SharePoint Online and OneDrive files first (delegated device-code mode proven on a personal OneDrive, then app-only for work tenants), Exchange Online mail later; least-privilege consent, Graph throttling, simulated-Graph tests; starts at Enterprise until validated. -->
<!-- plans-hub-related: PLAN_CONNECTOR_TIER_GATING.md, PLAN_PRODUCT_TIERS_AND_OPEN_CORE.md, PLAN_MULTI_INSTANCE_REPORT_HUB.md -->

## Context

Concrete enterprise demand exists for a personal-data inventory (LGPD and peers) that covers
Microsoft 365: files in SharePoint Online and OneDrive, and mail in Exchange Online. Data Boar
has no reader for these today.

## Verified state (2026-11-10, `origin/main`)

- `connectors/sharepoint_connector.py` targets **SharePoint on-prem** (REST with NTLM or basic
  auth). **Hypothesis, not validated:** it does not authenticate against SharePoint Online
  (Entra ID / OAuth). There is no lab tenant to prove it either way.
- `connectors/microsoft_identity.py` already holds the token-host allowlist
  (`login.microsoftonline.com`, #2007). The `powerbi` and `dataverse` connectors already use
  client credentials against Azure AD, so the authentication base exists.
- The only Graph issue is #2050, a **remediation writer** (P3). There is **no reader** and no
  Exchange/mail connector (#885 is research only).
- The WebDAV/rclone mount workaround is **discarded** (operator decision, 2026-11-17): the
  product needs native cloud access that a company can trust, not a third-party mount.

## Decisions (2026-11-17, operator; reversible in Phase 0)

- New connector type `sharepoint_online` in `connectors/sharepoint_online_connector.py`; one type
  for SharePoint Online and OneDrive; the on-prem `sharepoint_connector.py` does not change.
  Reason: the tier map is keyed by `type` and fail-closed (#854), the on-prem type is Pro while this one
  starts at Enterprise, and the credential-host gate (`config/loader.py`, #2086) must point at the
  Microsoft login and Graph hosts, not at `site_url`.
- Tier: Enterprise until validated. Minimal sharing: one file; no refactor of `sharepoint`,
  `webdav` or `smb` now.
- **Delegated mode first** (device code flow, public client, no secret, scopes `Files.Read` +
  `offline_access`), proven against a personal OneDrive restricted to a synthetic folder. The
  folder restriction is enforced by the connector (the scope alone reads the whole drive).
  **App-only (client credentials) for a work tenant is the next phase.**
- Tokens only in memory or in an ephemeral `0600` file outside the repository; never in the repo,
  logs, reports or findings. Documentation (en_US + pt_BR) ships in the repository.

## Phases

| Phase | Deliverable | Status |
| ----- | ----------- | ------ |
| 0 | Real proof against a personal OneDrive in delegated mode (device code, `Files.Read` + `offline_access`, synthetic folder): Graph listing, file in OneDrive, Boar report. Issue [#2260](https://github.com/DataBoar/data-boar/issues/2260). | ⬜ Pending (needs the operator's app registration) |
| 1 | `sharepoint_online` reader, delegated mode: device code flow, list/download inside the configured folder, reuse the file-connector extraction and detection, `@odata.nextLink` paging, honour `429` + `Retry-After`, simulated-Graph tests. Issue [#2261](https://github.com/DataBoar/data-boar/issues/2261). | ⬜ Pending |
| 1c | App-only (client credentials) for a work tenant, `Sites.Selected` vs `Sites.Read.All` to be confirmed. Issue [#2262](https://github.com/DataBoar/data-boar/issues/2262). | ⬜ Pending |
| 1b | Incremental scan through Graph delta queries | ⬜ Pending |
| 2 | Exchange Online mail: body and attachments, scoped by mailbox or group, application permission restricted by the tenant access policy | ⬜ Pending |
| 3 | Permission and consent guide (en_US + pt_BR) ready for the customer DPO and IT team | ⬜ Pending |

Out of scope: Teams/chat, any write path (#2048, #2050), Gmail/Workspace (#1158, #1167).

## Least privilege and security requirements

- Prefer `Sites.Selected` over `Sites.Read.All`. Whether `Sites.Selected` also covers per-user
  OneDrive sites, and which mail permission model is current (application access policy vs.
  newer Exchange scoping), **must be confirmed against Microsoft's current documentation during
  the Phase 1/2 design**, not assumed here.
- Host allowlist for `graph.microsoft.com` and for the token host, reusing
  `microsoft_identity`; SSRF guard as in the other connectors.
- Secrets only through environment variables; never in logs, reports or findings. Findings
  carry metadata only (no content exfiltration).
- Tests use a **simulated Graph** (paging, throttling, expired token, permission denied).
  Evidence from a real tenant is added only when a development tenant exists, with synthetic data.

## Tier and gating

The tier map is **fail-closed** (#854): a new connector type needs an explicit entry in the
exhaustive connector tier map before it can run outside `Tier.OPEN`. Entry: Enterprise, the
default for every new feature. Lowering it to another tier happens only after validation and is
an operator decision (record it in
[PLAN_CONNECTOR_TIER_GATING.md](PLAN_CONNECTOR_TIER_GATING.md)).

## Relationship to other plans

- [PLAN_CONNECTOR_TIER_GATING.md](PLAN_CONNECTOR_TIER_GATING.md): boundary table and fail-closed map.
- [PLAN_MULTI_INSTANCE_REPORT_HUB.md](PLAN_MULTI_INSTANCE_REPORT_HUB.md): consolidates findings when
  several instances scan different Microsoft 365 tenants or sites.
- [PLAN_PRODUCT_TIERS_AND_OPEN_CORE.md](PLAN_PRODUCT_TIERS_AND_OPEN_CORE.md): open-core posture.

Synced with [PLANS_TODO.md](PLANS_TODO.md).
