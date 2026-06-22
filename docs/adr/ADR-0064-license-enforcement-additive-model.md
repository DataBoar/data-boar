# ADR 0064 — License enforcement — additive open-core + JWT Pro/Enterprise

- **Date (UTC):** 2026-06-21
- **Authors:** Fabio Leitao
- **Deciders:** Fabio Leitao

## Status

Proposed

### Status history

- 2026-06-21 — Proposed (materializes GitHub #709; fulfills ADR-0027 Watch per #993)

## Context

[ADR 0027](ADR-0027-commercial-tier-boundaries-licensing-docs-and-future-jwt-claims.md)
(2026-04-17) documented tier boundaries and **deferred runtime enforcement** to product
and counsel. The Watch condition (“when JWT claims go live, revalidate docs”) is now
actionable for the **1.8.0-beta** enforcement line (renumbered from an earlier phantom
beta roadmap per issue #772; see [ADR 0073](ADR-0073-version-scheme-octet-maturity-and-roadmap.md)).

Signing algorithm is [ADR 0063](ADR-0063-ed25519-license-jwt-signing.md). Plugin auth
boundaries for L2/L3 are [ADR 0075](ADR-0075-plugin-auth-file-based-vs-bearer.md).

### Enrichment: revocation, telemetry, and tier ladder

| Topic | Decision direction (Proposed) |
| --- | --- |
| **Tier ladder** | Community (no JWT / invalid JWT) → Pro → Enterprise per `dbtier` claim and [ADR 0027](ADR-0027-commercial-tier-boundaries-licensing-docs-and-future-jwt-claims.md) public docs; numeric caps (`dbmax_workers`, …) remain a **later** enforcement phase. |
| **Revocation (GitHub #717)** | Online revocation list or signed short-lived tokens are **out of v1 enforcement MVP**; key rotation + expiry handle most cases until #717 ships. |
| **Beacon / heartbeat / kill-switch** | Operator private design note (*self-upgrade beacon heartbeat*, 2026-06-15) describes **optional** enterprise telemetry and remote policy hooks — **not** required for Community tier; must not brick open-core when absent. Details stay in `docs/private/` until product+counsel approve public spec. |

## Decision

### Two operating modes

1. **`mode: open`** (dev / unlicensed default) — `Tier.OPEN` bypasses enforcement;
   open-core **never requires** a license file.
2. **`mode: enforced`** (production) — `LicenseGuard` verifies ed25519 JWT ([ADR 0063](ADR-0063-ed25519-license-jwt-signing.md)),
   maps `dbtier` to `Tier`, and `is_feature_available(feature, tier)` gates Pro/Enterprise
   entry points.

### Invariant

**Missing JWT never blocks Community features.** Invalid or expired JWT in enforced mode
degrades to **Community** with warnings (configurable grace), not hard crash — aligned with
[ADR 0066](ADR-0066-tampered-state-behavior.md) for tamper paths.

### Runtime tier resolution (`runtime_feature_tier.py` priority)

1. `DATA_BOAR_TIER_OVERRIDE` (only when `DATA_BOAR_ENV=development`)
2. JWT `dbtier` when `LicenseGuard` state is VALID or GRACE
3. `licensing.effective_tier` in YAML (lab/manual)
4. `Tier.OPEN` fallback

### v1.8.0-beta call-site scope (minimum)

Enforced gating at Pro/Enterprise entry points including: PDF report, scheduled scans,
enterprise connectors (Snowflake, SAP, S3, Azure Blob, GCS), and `ocr_images` (Pro tier).

Unit tests continue using `effective_tier: enterprise` in YAML — **no JWT required in pytest**.

## Rationale

| Alternative | Why rejected |
| --- | --- |
| Hard block without license | Destroys open-core adoption |
| YAML-only tier without JWT | No cryptographic proof — editable by anyone |
| Hardware-bound license only | Poor fit for containers/cloud |
| SaaS-only online callback | Fails air-gapped deployments |

## Consequences

- **Positive:** Commercial protection with documented additive model; ADR-0027 Watch closed.
- **Negative:** Call-site coverage must stay in sync with `LICENSING_SPEC.md`; beacon/kill-switch
  remains private until explicitly published.
- **Watch:** Numeric claim enforcement; sidecar L2/L3 scope restriction (#695, #699); PQC
  migration per ADR-0063.

## Alternatives Considered

See rationale table.

## Related Decisions

- [ADR 0027 — Commercial tier boundaries](ADR-0027-commercial-tier-boundaries-licensing-docs-and-future-jwt-claims.md) — Watch fulfilled by this ADR
- [ADR 0063 — ed25519 JWT signing](ADR-0063-ed25519-license-jwt-signing.md)
- [ADR 0066 — TAMPERED fail-closed](ADR-0066-tampered-state-behavior.md)
- [ADR 0075 — Plugin auth model](ADR-0075-plugin-auth-file-based-vs-bearer.md)
- GitHub #709, #717, #993

## References

- [`docs/LICENSING_OPEN_CORE_AND_COMMERCIAL.md`](../LICENSING_OPEN_CORE_AND_COMMERCIAL.md)
- [`docs/LICENSING_SPEC.md`](../LICENSING_SPEC.md)
- [Documenting Architecture Decisions (Michael Nygard)](https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions)
