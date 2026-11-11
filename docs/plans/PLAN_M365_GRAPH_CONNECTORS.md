# Plan: Microsoft 365 read-only connectors via Microsoft Graph (SharePoint Online, OneDrive, Exchange Online)

**Status:** Pending (design only; no connector code yet)
**Date:** 2026-11-10
**Authors:** Fabio Leitao
**Priority:** H1
**GitHub:** [#2206](https://github.com/DataBoar/data-boar/issues/2206)
**Depends on:** [PLAN_CONNECTOR_TIER_GATING.md](PLAN_CONNECTOR_TIER_GATING.md) (fail-closed tier map, #854); token-host allowlist (#2007, done)
**Tier (proposed, pending operator ratification):** Pro, same family as the SharePoint on-prem, PowerBI and Dataverse connectors already ratified as Pro

<!-- plans-hub-summary: Read-only Microsoft 365 inventory via Microsoft Graph (app-only): SharePoint Online and OneDrive files first, Exchange Online mail second; least-privilege consent, Graph throttling, simulated-Graph tests; proposed Pro tier. -->
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
- Workaround candidate: mount OneDrive/SharePoint through WebDAV or rclone and use
  `connectors/webdav_connector.py`. **There is no recorded proof that this works.**

## Phases

| Phase | Deliverable | Status |
| ----- | ----------- | ------ |
| 0 | Validate or discard the WebDAV/rclone workaround against a development tenant; record the result either way. **Blocked: no tenant available.** Until then the workaround is documented as *unvalidated*. | ⬜ Pending (blocked on tenant) |
| 1 | SharePoint Online + OneDrive files: app-only (client credentials) auth, list sites/drives, download to temp, reuse the file-connector extraction and detection, `@odata.nextLink` paging, honour `429` + `Retry-After` | ⬜ Pending |
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
exhaustive connector tier map before it can run outside `Tier.OPEN`. Proposed entry: Pro. The
operator ratifies or changes it (record the decision in
[PLAN_CONNECTOR_TIER_GATING.md](PLAN_CONNECTOR_TIER_GATING.md)); until then this plan does not
claim a tier.

## Relationship to other plans

- [PLAN_CONNECTOR_TIER_GATING.md](PLAN_CONNECTOR_TIER_GATING.md): boundary table and fail-closed map.
- [PLAN_MULTI_INSTANCE_REPORT_HUB.md](PLAN_MULTI_INSTANCE_REPORT_HUB.md): consolidates findings when
  several instances scan different Microsoft 365 tenants or sites.
- [PLAN_PRODUCT_TIERS_AND_OPEN_CORE.md](PLAN_PRODUCT_TIERS_AND_OPEN_CORE.md): open-core posture.

Synced with [PLANS_TODO.md](PLANS_TODO.md).
