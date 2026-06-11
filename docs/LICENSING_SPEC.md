# Licensing specification (runtime)

Technical specification for **optional** commercial enforcement. Default is **open** mode (no token required).

## Modes

| Mode       | Config / env                                                    | Behaviour                                                                                          |
| ----       | ------------                                                    | ----------                                                                                         |
| `open`     | `licensing.mode: open` or unset; `DATA_BOAR_LICENSE_MODE=enforced` can escalate | Full functionality; license token optional; status shows **OPEN**                                  |
| `enforced` | `licensing.mode: enforced`                                      | Valid signed token required for ingest/digest; invalid/expired/revoked/tampered states block scans |

### No environment bypass (#719)

Enforcement state is determined **only** by `licensing.mode: enforced` plus a
valid signed license. Environment variables can never disable it:

- `DATA_BOAR_LICENSE_MODE=open` is **ignored** when YAML sets `mode: enforced`
  (the attempt is recorded as a CRITICAL audit event). The env var can only
  **escalate** `open` → `enforced`.
- `DATA_BOAR_ENV=development`, `DEBUG=1`, and the former
  `DATA_BOAR_TIER_OVERRIDE` have **zero** licensing effect. The dev/CI tier
  override was removed — use a locally issued signed QA license instead
  (`scripts/issue_dev_license_jwt.py`).
- Without a valid license in enforced mode the runtime **fails closed**:
  scans are denied (Safe-Hold / HTTP 403) and the feature tier is capped to
  Community — never "open".

Every enforcement decision (allow / deny / clamp / expire) is recorded on the
`data_boar.licensing.audit` logger with the `LICENSE_AUDIT` prefix.

Environment variables override YAML when set:

- `DATA_BOAR_LICENSE_MODE` — `enforced` (escalation only; `open` cannot downgrade YAML `enforced`)
- `DATA_BOAR_LICENSE_PATH` — path to JWT file (`.lic`)
- `DATA_BOAR_LICENSE_PUBLIC_KEY_PATH` — PEM file with **Ed25519 public** key (verify only)
- `DATA_BOAR_LICENSE_PUBLIC_KEY_PEM` — inline PEM (alternative to path; dev/CI only)
- `DATA_BOAR_LICENSE_REVOCATION_PATH` — JSON file listing revoked license IDs
- `DATA_BOAR_RELEASE_MANIFEST_PATH` — optional JSON manifest for integrity (see [RELEASE_INTEGRITY.md](RELEASE_INTEGRITY.md))
- `DATA_BOAR_EXPECTED_BUILD_DIGEST` — optional hex SHA-256; if set, compared to embedded build digest

## YAML (`config.yaml`)

```yaml
licensing:
  mode: open                    # open | enforced
  public_key_path: ""           # Ed25519 public PEM
  license_path: ""              # signed JWT file
  revocation_list_path: ""      # optional JSON revoke list
  manifest_path: ""             # optional release manifest
  machine_bind_strict: false    # if true, token mfp must match host fingerprint
```

## License JWT payload (claims)

Signed with **Ed25519** (JWS `EdDSA`). Standard claims:

| Claim | Meaning             |
| ----- | -------             |
| `sub` | License ID (unique) |
| `iat` | Issued-at (unix)    |
| `exp` | Expiration (unix)   |

Custom claims (namespaced to avoid collisions):

| Claim       | Type   | Meaning                                                                         |
| -----       | ----   | -------                                                                         |
| `dbcid`     | string | Customer ID                                                                     |
| `dbcname`   | string | Customer display name                                                           |
| `dbenv`     | string | Target environment: `production`, `qa`, `uat`, `homologation`, `debug`, `trial` |
| `dbmfp`     | string \| array | Expected machine fingerprint(s). Single hex string = one host; **array of hex strings = deployment pack** (#718 + #846): runtime accepts when its own fingerprint ∈ pack. Empty/absent = any host. **Malformed claim (wrong type) fails closed** (`INVALID`) — never degrades to "unbound". |
| `dbtrial`   | bool   | Trial / POC: cap report rows and watermark                                      |
| `dbmaxrows` | int    | Max data rows in report when trial (e.g. 15)                                    |
| `dbissuer`  | string | Issuer operator id (e.g. SSH key fingerprint or email)                          |
| `dbkid`     | string | Signing key id for rotation                                                     |
| `dbgrace`   | int    | Grace period end (unix); after `exp`, still **GRACE** until this time           |
| `dbmax_workers` | int | Max parallel scan workers (#551). **Enforced mode only:** the engine clamps `scan.max_workers` to `min(scan.max_workers, dbmax_workers)`. Absent/zero on a usable license → tier defaults apply (Community **2** / Pro **5** / Enterprise **unlimited**). Open mode never caps. Clamp is fail-soft and audited (`workers_clamped`, WARNING). |
| `dbmax_deployments` | int | Max distinct **licensed production sites** (fingerprints) for this token (#846). **Issuance-enforced:** the issuer emits the `dbmfp` pack with at most this many entries; runtime reads the claim into `LicenseContext.max_deployments` (audit/report surface) and validates only its **own** fingerprint ∈ pack. **0** may mean **unlimited** when contract allows (Enterprise). Pro default pending operator ratification — see `DEFAULT_PRO_DEPLOYMENTS` in `core/licensing/guard.py`. |
| `dbdeployment_pack_id` | string | Id of a **commercial add-on** (e.g. “+5 sites”) for audit/refill trail (#846); surfaced in `LicenseContext.deployment_pack_id`. Issuer: `scripts/issue_dev_license_jwt.py --dbmfp-pack <hex,hex,...> [--pack-id ...]`. |

**Multi-site verification (honest boundary, #718 + #846):** Implemented via option (1) — **array** of allowed fingerprints in the `dbmfp` claim (deployment pack). Runtime validates only that **its own** `compute_machine_fingerprint()` (hostname + optional `DATA_BOAR_MACHINE_SEED`) is in the pack — the **global** deploy count is enforced at **issuance** (the issuer signs a pack of at most `dbmax_deployments` fingerprints); the runtime cannot count other sites. Alternatives kept for reference: (2) **online** registration (privacy + ops cost); (3) **multiple JWTs** same `dbcid`, one fingerprint each. See [LICENSING_OPEN_CORE_AND_COMMERCIAL.md](LICENSING_OPEN_CORE_AND_COMMERCIAL.md) §Deployments, copies, and sites.

## Lifecycle states

| State              | Meaning                                                                |
| -----              | -------                                                                |
| `OPEN`             | Enforcement off; community / dev build                                 |
| `VALID`            | Token signature OK, not expired (or in grace), not revoked, machine OK |
| `GRACE`            | Past `exp` but before `dbgrace`                                        |
| `EXPIRED`          | Past grace                                                             |
| `REVOKED`          | License ID on revocation list                                          |
| `UNLICENSED`       | Enforced but no token or unreadable token                              |
| `INVALID`          | Bad signature or malformed JWT                                         |
| `MACHINE_MISMATCH` | `dbmfp` set and does not match host                                    |
| `TAMPERED`         | Release integrity / manifest check failed                              |
| `CRACKED`          | Reserved for future anti-tamper signals (e.g. bytecode check failures) |

## Machine fingerprint

Computed as **SHA-256** hex over a stable string built from:

- Hostname (short)
- Optional: `DATA_BOAR_MACHINE_SEED` (set in deployment for Docker/VM stability)

Docker: set `DATA_BOAR_MACHINE_SEED` to a deployment-specific secret so containers on the same image share one licensed fingerprint.

## Revocation file format

JSON:

```json
{
  "revoked_license_ids": ["license-uuid-1", "license-uuid-2"]
}
```

## Trial / POC behaviour

When `dbtrial` is true:

- Scan may run (if otherwise valid) but **report generation** caps findings to `dbmaxrows` and appends synthetic “teaser” rows (watermarked).
- Logs and Report info sheet state **TRIAL**.

## Blocking rule

When mode is **enforced** and state is not `VALID` or `GRACE` (and not `OPEN`):

- **CLI**: `start_audit` raises `LicenseBlockedError`; message printed to stderr.
- **API**: `POST /scan`, `POST /start`, `POST /scan_database` return **403** with `detail.license_state`.

Health and About still respond so operators can see **why** the system is restricted.

## Future extensions (planning reminder — partner tiers / consulting SKUs)

When you **change or harden licensing** for IP and profitability, you may introduce **separate commercial programs** (e.g. **direct end-customer** vs **partner / pro / enterprise**—exact names and contracts TBD with counsel). One goal: allow **partners** to use a **partner-level** entitlement to serve **their customers’** engagements without collapsing into the same SKU as a single-tenant end user.

**Not implemented today.** Possible directions (to be validated legally and product-wise):

| Idea                  | Notes                                                                                                                              |             |                                                                                                   |
| ----                  | -----                                                                                                                              |             |                                                                                                   |
| **Custom JWT claims** | e.g. `dbprogram` or `dbtier` (`direct` \                                                                                           | `partner` \ | `enterprise`, …) and optional `dbmax_customers` / `dbconsulting_allowed`—names illustrative only. |
| **Enforcement**       | `LicenseGuard` and report metadata would read claims and block or watermark **unauthorised** consulting or multi-customer use.     |             |                                                                                                   |
| **Issuance**          | Private issuer (`tools/license-studio` or successor) issues different token **templates** per SKU; audit log records program/tier. |             |                                                                                                   |

Keep this section in sync with [LICENSING_OPEN_CORE_AND_COMMERCIAL.md](LICENSING_OPEN_CORE_AND_COMMERCIAL.md) (“Future product tiers” and **Brand, narrative, and experience IP** — mascot, data soup, dashBOARd, report/UI presentation, companion resources). **Do not add claims to production tokens until contracts and pricing are defined.**

### Future extension: entitlement-driven feature packs and kill switch

Not implemented yet. Planning target: when tier contracts are frozen, license claims can drive
which optional capabilities are available at runtime and which installer extras are permitted.

| Claim / control idea                                  | Purpose                                                                                                                               |
| ---                                                   | ---                                                                                                                                   |
| `dbtier` (`standard`, `pro`, `partner`, `enterprise`) | Single source of truth for entitlement tier in runtime, report info, and audit trail. **Implementation (2026-04):** when `licensing.mode` is **enforced** and the token is **VALID** or **GRACE**, the verify path copies this claim into `LicenseContext.dbtier` and `GET /health` → `license.dbtier`; dashboard code maps it to internal tier for **optional** feature gates (e.g. maturity POC) alongside lab-only `licensing.effective_tier` in YAML. **Maturity POC gate:** `docs/plans/PLAN_MATURITY_SELF_ASSESSMENT_GRC_QUESTIONNAIRE.md` § *Next slice*; regression: `tests/test_api_assessment_poc.py` (`test_assessment_enforced_jwt_dbtier_*`). |
| `dbmax_workers` (int)                                 | Optional cap on **parallel scan workers** (open core policy target: **1** default, **2** max — see [LICENSING_OPEN_CORE_AND_COMMERCIAL.md](LICENSING_OPEN_CORE_AND_COMMERCIAL.md)). Pro/Enterprise: higher or **unbounded** in token (`0` = unlimited — product decision). |
| `dbmax_targets` (int)                                 | Optional cap on **configured targets** per session or deployment envelope; **0** may mean unlimited when contract allows.              |
| `dbfeatures` (string list)                            | Explicit feature flags independent from tier defaults (e.g. `compressed_scan`, `content_type_cloaking`, future `ai_heuristics_plus`). |
| `dbkill` / revocation overlays                        | Emergency disable for vulnerable/abused capabilities without shipping a full app update.                                              |
| `dbextras_profile` (`core`, `plus`, `full`)           | Maps entitlement to allowed dependency packs (`.[nosql]`, `.[datalake]`, etc.) in controlled environments.                            |

## Operational policy sketch (to refine in plan + legal):

1. **Enterprise**: allow all vetted extras profiles (`full`) and all optional runtime controls; **workers/targets**: **unlimited** in entitlement (subject to host), unless contract narrows.
1. **Pro / Partner**: allow a curated subset (for example cloaking/content-type checks and selected premium heuristics), deny high-cost packs by default; **workers/targets**: **above open-core caps**, not necessarily unlimited; some **premium ingredients** may be **Enterprise-only**.
1. **Open core / community** (no paid token): when enforcement is active for a **build** that embeds tier defaults, align with **1–2 workers** and **capped targets** policy — see [LICENSING_OPEN_CORE_AND_COMMERCIAL.md](LICENSING_OPEN_CORE_AND_COMMERCIAL.md) §Scale and concurrency.
1. **Standard** (if used as a label): core runtime only, with a short allowlist of low-risk options (example: compressed archive scan).
1. **Enforcement posture**: fail closed for disallowed premium options in `enforced` mode, but keep explicit operator guidance in logs/docs.

**`uv`/extras note:** automatic dependency installation must be **opt-in** and auditable (prefer explicit operator command or installer profile), never silent package mutation during scan runtime. Record entitlement decisions in audit surfaces once implemented.
