# Plan: Plugin partner interface (L1 / L2 / L3)

<!-- plans-hub-summary: Plugin partner interface L1/L2/L3 — in-process Rust/Python, Clojure sidecar, external API (technology partner, DLP, custom webhook); Enterprise tier; dep: JWT + silo segregation post-1.7.4. -->
<!-- plans-hub-related: PLAN_PLUGIN_SDK.md, PLAN_REMEDIATION_INTERFACE.md, PLAN_YAML_PLUGIN_SYSTEM.md -->

**Status:** Active (doc slice — #695)
**Date:** 2026-08-09
**Authors:** Fabio Leitao
**Priority:** H4 / P2
**GitHub:** [#695](https://github.com/DataBoar/data-boar/issues/695) · hook [#606](https://github.com/DataBoar/data-boar/issues/606) · manifest [#649](https://github.com/DataBoar/data-boar/issues/649) · L1 guide [#611](https://github.com/DataBoar/data-boar/issues/611) · epic [#865](https://github.com/DataBoar/data-boar/issues/865) · bidirectional follow-up [#1116](https://github.com/DataBoar/data-boar/issues/1116)

**Synced with:** [PLANS_TODO.md](PLANS_TODO.md)

**Tier:** **Enterprise only** — not available in open-core Community builds. L1 hook exists today behind `remediation_plugin`; L2/L3 runtimes are **planned**, not shipped.

**Related:** [PLAN_PLUGIN_SDK.md](PLAN_PLUGIN_SDK.md) (L1 author guide), [PLAN_REMEDIATION_INTERFACE.md](PLAN_REMEDIATION_INTERFACE.md) (host phases), [PLUGIN_SDK.md](../PLUGIN_SDK.md), [ADR-0059](../adr/ADR-0059-remediation-plugin-architecture.md) (L1), [PLAN_YAML_PLUGIN_SYSTEM.md](PLAN_YAML_PLUGIN_SYSTEM.md) (**different** surface — detector pattern plugins, not remediation partners).

---

## Problem

Data Boar owns **discovery + evidence**. Remediation (tokenize, mask, label, revoke) is partner-specific. Without a published **coupling hierarchy** and a **stable L3 payload/receipt shape**, every partner forks ad-hoc HTTP or in-process hacks. The first demand-pulled L3 consumer is a **technology partner** (tokenization / FPE class); the wiring must stay generic for DLP SaaS, custom webhooks, and future vendors.

---

## Goal (this plan — Fatia A / #695)

**Documentation only** in this slice:

1. Record the **L1 / L2 / L3** hierarchy with YAML examples.
2. Specify the **L3 request payload** and **async receipt** schemas (fields, types, required/optional).
3. Skeleton **how to add a new driver**.
4. State **Enterprise** and security deps explicitly.
5. List the **ADR prerequisite** before any L2/L3 runtime code.

Runtime implementation of L2/L3 drivers belongs to epic **#865** (and later demand-pulled partner PRs). Bidirectional / zero-trust guest-side is **#1116** — out of scope here.

---

## Coupling hierarchy

```
L1 — In-process (maximum performance; same OS process)
  · Rust accelerator (e.g. boar_fast_filter via PyO3) for scan path
  · Python RemediationPlugin hooks (#606 / ADR-0059) for post-scan remediation
  · Documented for partners today: docs/PLUGIN_SDK.md (#611)

L2 — Sidecar process (other runtime, host-orchestrated)
  · Example target: policy / re-id / rule-DSL sidecar (e.g. JVM or other)
  · Transport: findings JSON via stdin, named pipe, or local IPC
  · Isolation: hard timeout, CPU/mem cap, kill → Safe-Hold (#865)
  · Not shipped as a public API yet

L3 — External API (decoupled output feed)
  · Host POSTs a structured manifest/payload; partner processes asynchronously
  · Optional async receipt written back into the remediation audit trail
  · Examples: technology-partner tokenize API, DLP cloud, custom_webhook
  · Not shipped as a built-in driver yet
```

**Design principle:** the partner receives a **structured payload** and has **no visibility into core internals**. Zero coupling beyond the published contract. Credentials never live in YAML — only `env_var` names.

---

## What exists today vs planned

| Layer | Status on `main` | Operator surface |
| ----- | ---------------- | ---------------- |
| L1 remediation hook | ✅ #606 + #1443 | `remediation.enabled` + `plugin: "module:Class"` |
| L1 partner guide | ✅ #611 | `docs/PLUGIN_SDK.md` |
| Remediation manifest export | ✅ #649 | `--export-remediation-manifest` |
| L2 sidecar contract | ⬜ #865 | Planned — schema + sandbox |
| L3 HTTP drivers | ⬜ #865 + this plan’s schema | Planned — `driver:` block below |
| Bidirectional / guest Boar | ⬜ #1116 | After host contract stable |

---

## Config shape (target — L3; not wired yet)

Illustrative `config.yaml` for a future L3 driver. **Do not** treat this as live API until #865 ships the loader.

```yaml
# Enterprise tier — L3 partner driver (PLANNED; not loaded by core today)
remediation:
  enabled: true
  # L1 today uses `plugin: "module.path:ClassName"` (see PLUGIN_SDK.md).
  # Future L3 uses `driver:` instead of (or in addition to) in-process plugin.
  driver: partner_provider          # or: dlp_api | custom_webhook | null
  endpoint: https://partner.example.com/api/v1/remediate
  auth:
    type: api_key
    env_var: PARTNER_API_KEY        # never hardcode secrets
  on_finding:
    min_severity: high
    pii_types: [credit_card, cpf, pan]
  output:
    receipt_field: partner_remediation_receipt
    append_to_manifest: true
```

**L1 today** (shipped — for comparison):

```yaml
remediation:
  enabled: false
  plugin: null           # e.g. "myorg.stealthizer:StealthizerPlugin"
  verify_after: true
  config: {}
```

---

## Planned drivers (catalogue — not commitments)

| Driver | Use case | Tier | Status |
| ------ | -------- | ---- | ------ |
| `partner_provider` | Sensitive-data remediation / tokenize (technology partner) | Enterprise | Priority when demand-pulled |
| `dlp_api` | Cloud DLP findings feed | Enterprise | Potential partner |
| `custom_webhook` | Any proprietary HTTPS endpoint | Enterprise | Generic built-in (planned) |
| `varonis_remediation` | Access revocation via Varonis-class API | Enterprise | Future |
| `purview_label` | Sensitivity label on Microsoft stack | Enterprise | Future |

Names are **catalogue labels**. Shipping a driver requires a dedicated PR, Enterprise gate, and the ADR below.

---

## L3 request payload (host → partner)

Metadata-oriented by default (aligns with #649 remediation taxonomy). **No raw PII samples** in the default profile. Opt-in “real data” payloads (if ever) are **Enterprise + explicit customer authorization** and are **out of scope** for the default contract (see epic #865 / vault GAP-010).

### Envelope

| Field | Type | Required | Notes |
| ----- | ---- | -------- | ----- |
| `sdk_contract_version` | string (semver) | yes | Contract pin, e.g. `"1.0.0"` when #865 freezes schema |
| `schema` | string | yes | Constant `"databoar.remediation.l3.request"` |
| `session_id` | string | yes | Host scan / session id |
| `issued_at` | string (ISO-8601 UTC) | yes | Host clock |
| `trust_level` | string | yes | Host integrity/trust signal (e.g. from runtime trust / integrity anchor). Partner **SHOULD** Safe-Hold if tinted/adulterated (#865 comment). |
| `integrity_state` | string | optional | Finer integrity enum when available |
| `source` | object | yes | `{ "product": "data-boar", "version": "<semver>" }` |
| `filter` | object | optional | Echo of `on_finding` (min_severity, pii_types) |
| `targets` | array of Target | yes | One entry per remediation target (may be empty) |
| `callback` | object | optional | How to return a receipt (see below) |

### Target object

| Field | Type | Required | Notes |
| ----- | ---- | -------- | ----- |
| `finding_id` | string | yes | Stable id from host taxonomy |
| `source_type` | string | yes | e.g. `sql`, `filesystem`, … |
| `connection_ref` | string | optional | Opaque connection label (not a secret) |
| `schema` | string | optional | DB schema / namespace |
| `table` | string | optional | |
| `column` | string | optional | |
| `path` | string | optional | Filesystem path when applicable |
| `pii_type` | string | yes | Normalized type token |
| `severity` | string | optional | Host severity if present |
| `suggested_profile` | string | optional | Remediation hint (mask / tokenize / …) |
| `norm_tag` | string | optional | Compliance tag when present |

### Callback object (optional)

| Field | Type | Required | Notes |
| ----- | ---- | -------- | ----- |
| `mode` | string | yes | `none` \| `webhook` \| `poll_url` |
| `webhook_url` | string | if mode=webhook | Partner POSTs receipt here (customer-controlled) |
| `correlation_id` | string | yes | Echoed on receipt |

### Example (abbreviated)

```json
{
  "sdk_contract_version": "1.0.0",
  "schema": "databoar.remediation.l3.request",
  "session_id": "sess_example",
  "issued_at": "2026-08-09T12:00:00Z",
  "trust_level": "trusted",
  "source": { "product": "data-boar", "version": "1.7.4" },
  "filter": { "min_severity": "high", "pii_types": ["cpf", "pan"] },
  "targets": [
    {
      "finding_id": "f-001",
      "source_type": "sql",
      "schema": "hr",
      "table": "employees",
      "column": "tax_id",
      "pii_type": "cpf",
      "suggested_profile": "tokenize"
    }
  ],
  "callback": {
    "mode": "webhook",
    "webhook_url": "https://customer.example.com/hooks/databoar-receipt",
    "correlation_id": "corr-001"
  }
}
```

Formal JSON Schema file lives under `docs/sdk/` when **#865** Fatia B lands (`PLUGIN_CONTRACT.schema.json`). This plan is the **normative field list** until that file exists.

---

## L3 async receipt (partner → host)

| Field | Type | Required | Notes |
| ----- | ---- | -------- | ----- |
| `sdk_contract_version` | string | yes | Must match or be compatible with request |
| `schema` | string | yes | `"databoar.remediation.l3.receipt"` |
| `correlation_id` | string | yes | From request callback |
| `session_id` | string | yes | Echo |
| `partner` | object | yes | `{ "driver": "partner_provider", "name": "...", "version": "..." }` |
| `status` | string | yes | `accepted` \| `completed` \| `partial` \| `failed` \| `safe_hold` |
| `completed_at` | string (ISO-8601 UTC) | yes | |
| `results` | array of Result | optional | Per-finding outcomes |
| `error` | object | optional | `{ "code": "...", "message": "..." }` — no secrets |

### Result object

| Field | Type | Required | Notes |
| ----- | ---- | -------- | ----- |
| `finding_id` | string | yes | |
| `action` | string | yes | e.g. `tokenized`, `masked`, `skipped`, `failed` |
| `partner_ref` | string | optional | Partner-side ticket / token id (**not** the cleartext value) |

When `output.append_to_manifest: true`, the host stores the receipt under `output.receipt_field` on the session audit / remediation report (exact persistence path = #865 implementation).

---

## Integration guide (skeleton — new driver)

1. **Pick a tier:** L1 (Python Protocol today) vs L2 (sidecar) vs L3 (HTTPS). Prefer L3 when the partner already has an API; L1 when latency and same-host trust are acceptable.
2. **Read** [PLUGIN_SDK.md](../PLUGIN_SDK.md) for L1; this plan for L2/L3 shapes; wait for `docs/sdk/PLUGIN_CONTRACT.schema.json` (#865) before freezing production clients.
3. **Never** send secrets in config — only `auth.env_var` names. Rotate via the customer secret store.
4. **Implement** against the payload/receipt tables above. Validate `trust_level` before acting; on tinted host → `status: safe_hold`.
5. **Register** the driver name in the catalogue table via a Data Boar PR (Enterprise feature gate + tests). Do not patch `core/` with partner business logic.
6. **Prove** with synthetic findings only in CI; customer data stays in the customer environment.
7. **Document** overclaim boundaries: Data Boar does not claim partner certifications (e.g. C2PA “certified”) unless an external CA attests them.

---

## Security and dependencies

| Topic | Rule |
| ----- | ---- |
| Tier | Enterprise feature gate (`remediation_plugin` / future L2–L3 gates). |
| Open-core | No L2/L3 partner drivers in Community. |
| Secrets | Env vars / vault only; never commit partner URLs with embedded credentials. |
| Default payload | Metadata / locations only — no raw PII samples. |
| Fail-graceful | Partner failure → Safe-Hold of remediation target; **never** abort the scan worker (#606 doctrine, #865 generalization). |
| Dep before L2/L3 runtime | JWT + feature-silo segregation (post-1.7.4 product posture); stable #606 / #649. |

### ADR prerequisite (before L2/L3 implementation)

**Do not implement L2/L3 loaders or HTTP drivers until a new ADR is Accepted** covering at least:

1. **Public contract stability** — versioning of `sdk_contract_version`, what may change without a major bump.
2. **Data handling** — what L3 receives, what the host retains, what is discarded; default metadata-only.
3. **Auth & credential isolation** — sidecar/API auth; no secret material in process logs.
4. **Relationship to** [ADR-0059](../adr/ADR-0059-remediation-plugin-architecture.md) (L1 remains; this ADR extends the boundary for L2/L3).

Tracking: create via `scripts/new-adr.ps1` when Fatia B/#865 starts code; link the ADR number here and in #695 / #865.

---

## Phases

| Phase | Deliverable | Status |
| ----- | ----------- | ------ |
| **A – This plan (#695)** | Hierarchy, L3 schemas, driver skeleton, PLANS hub/TODO | 🔄 This PR |
| **B – Contract files (#865)** | `docs/sdk/*.schema.json`, `docs/SDK.md`, conformance tests | ⬜ |
| **C – First L3 driver** | Demand-pulled `custom_webhook` or `partner_provider` | ⬜ |
| **D – Bidirectional (#1116)** | Guest-side + dogfood attestation | ⬜ |

---

## Acceptance (#695)

- [x] This file with `<!-- plans-hub-summary: ... -->`
- [x] L1/L2/L3 hierarchy + YAML examples
- [x] L3 request + receipt field tables
- [x] New-driver integration skeleton
- [x] Enterprise tier explicit
- [x] ADR listed as prerequisite before implementation
- [x] References to #606 and #649
- [x] `PLANS_TODO.md` entry
- [x] `python scripts/plans_hub_sync.py --write` (this PR)

---

## Non-goals

- Implementing HTTP clients, sidecars, or Futurex/Nightfall/Varonis SDKs in this PR.
- Changing `RemediationPlugin` Protocol signatures.
- Claiming partner product certifications.
- Bidirectional guest-Boar mesh (#1116 / GAP-010) — document only as later phase.
