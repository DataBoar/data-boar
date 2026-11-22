# Microsoft Graph delegated OneDrive proof — Phase 0 (#2260)

**Date:** 2026-11-18 (scan start UTC `2026-11-18T12:37:26`, America/Sao_Paulo operator context).

**Issue:** [#2260](https://github.com/DataBoar/data-boar/issues/2260) — real proof against a **personal** OneDrive through the Data Boar `sharepoint_online` reader (not a probe outside the product).

This document is **evidence of what was run**, not a legal conclusion and does not claim regulatory completeness.

## Product and environment

| Field | Value |
| ----- | ----- |
| Surface | Public **presentation** demo instance (`apresentacao.dashboard.net.br`) per [PLAN_LIVE_DEMO_SANDBOX.md](../../plans/PLAN_LIVE_DEMO_SANDBOX.md) — same build family as the curated demo, **without** the 30-minute reset |
| Reported application version (export) | `1.8.1` (demo license pack, `lab` environment on the export) |
| Session ID | `c001d83a80c8_20261118_123726` |
| Connector | `type: sharepoint_online`, `auth.mode: delegated`, `tenant: consumers`, `drive: me` |
| Microsoft Graph | Production global cloud (`https://graph.microsoft.com/v1.0`, `login.microsoftonline.com`) |
| Scopes (configured) | `Files.Read` + `offline_access` |
| Download host allowlist (configured) | `.microsoftpersonalcontent.com` |

Credentials (`auth.client_id`, `auth.token_cache_path`, passwords, Supabase keys, and every other secret) stay **outside** this repository and are **not** reproduced here. Use placeholders in tickets and samples: `<APP_CLIENT_ID>`, `<TOKEN_CACHE_PATH>`.

## Configuration shape (redacted; operator Podman host)

Two Enterprise targets on the same delegated app registration:

| Target name | `root_folder` | Role |
| ----------- | ------------- | ---- |
| `Microsoft 365 - OneDrive` | `/Documents` | Primary personal OneDrive folder walk (`max_depth: 16`) |
| `Microsoft 365 - OneDrive - Attachments` | `/Attachments` | Secondary folder (attachments-style content) |

Other targets on the same config (synthetic corpus, lab SQL/NoSQL, SMB, external Postgres pooler) are **out of scope** for #2260; they do not affect this proof.

Shared reader keys matched the documented contract in [USAGE.md](../../USAGE.md#microsoft-graph-delegated-mode-type-sharepoint_online): `graph.base_url`, `download_host_suffixes`, `page_size`, `max_pages_per_folder`, `http_timeout_seconds`, `throttle_max_wait_seconds`, `max_file_bytes`, `include_names: []`.

## Verification (no customer content in Git)

1. **Live dashboard API (read-only, public):** `GET https://apresentacao.dashboard.net.br/findings` returned HTTP 200 with `session_id` = `c001d83a80c8_20261118_123726` and filesystem rows for targets `Microsoft 365 - OneDrive` and `Microsoft 365 - OneDrive - Attachments` with display paths prefixed `onedrive:` (the format emitted by `connectors/sharepoint_online_connector.py`).
2. **Operator-held Excel export** from the same session (filename pattern `Relatorio_Auditoria_<session_id>.xlsx`, kept locally, not committed):
   - **Report info** sheet: same `Session ID`, version `1.8.1`.
   - **Filesystem findings:** **72** rows for `Microsoft 365 - OneDrive`, **1** row for `Microsoft 365 - OneDrive - Attachments` (**73** rows with an `onedrive:` path prefix). File names and cell content are **not** copied into tracked docs.

Re-check any time:

```bash
curl -sS 'https://apresentacao.dashboard.net.br/findings' | python3 -c "
import json,sys
d=json.load(sys.stdin)
print('session_id', d.get('session_id'))
fs=[f for f in d.get('findings',[]) if f.get('source_type')=='filesystem' and 'OneDrive' in (f.get('target_name') or '')]
print('onedrive_filesystem_rows', len(fs))
print('sample_path', (fs[0].get('path') if fs else None))
"
```

## Phase 0 verdict vs limits

| Claim | Verdict |
| ----- | ------- |
| Personal OneDrive (`tenant: consumers`, `drive: me`) scanned **through the Boar connector** with Graph delegated mode | **Proven** on 2026-11-18 (this session) |
| Simulated-Graph unit/acceptance tests in CI | Unchanged — still the automated gate |
| SharePoint Online **site** libraries | **Not proven** |
| Work or school Entra tenant (`tenant: <TENANT_ID>`, multitenant customer app) | **Not proven** |
| App-only / unattended / dashboard-initiated sign-in | **Not in scope** ([#2262](https://github.com/DataBoar/data-boar/issues/2262)) |
| Publisher-verified multitenant consent in customer tenants | **Not proven** |

## Cross-links

- Operator runbook: [M365_GRAPH_DELEGATED_RUNBOOK.md](../M365_GRAPH_DELEGATED_RUNBOOK.md)
- Customer pilot framing: [M365_GRAPH_CUSTOMER_PILOT.md](../M365_GRAPH_CUSTOMER_PILOT.md)
- Plan slice: [PLAN_M365_GRAPH_CONNECTORS.md](../../plans/PLAN_M365_GRAPH_CONNECTORS.md) Phase 0
- Portuguese summary: [m365_graph_onedrive_delegated_2260_2026-11-18.pt_BR.md](m365_graph_onedrive_delegated_2260_2026-11-18.pt_BR.md)