# ADR 0076 — OPA/Rego as CI drift linter for commercial tier enforcement (not runtime)

- **Date (UTC):** 2026-06-30
- **Authors:** Fabio Leitao
- **Deciders:** Fabio Leitao

## Status

Proposed

### Status history

- 2026-06-30 — Proposed (research closure GitHub #1079)

## Context

Tier boundaries are documented in [ADR 0027](ADR-0027-commercial-tier-boundaries-licensing-docs-and-future-jwt-claims.md) and implemented across **`core/licensing/tier_features.py`** (`FEATURE_TIER_MAP`), **`runtime_feature_tier.py`**, **`connector_registry.py`**, **`sampling_policy.py`**, and **`enterprise_surface_posture.py`**. Symptoms of **drift** between the documented ladder and code are tracked as **#854**, **#887**, and **#845**.

External research (off-band, RO-verified #1079) evaluated **Open Policy Agent (OPA)** / **Rego** as a way to express the tier régua in one place.

| Option | Pros | Cons |
| --- | --- | --- |
| **OPA daemon + Go binding at runtime** | Single policy engine in production | Breaks lightweight `pip install` open-core; new runtime dep; overlaps JWT/`LicenseGuard` |
| **Rego as CI/lint only (chosen direction)** | Catches drift before merge; no customer runtime cost | Requires exporting a machine-readable snapshot from Python for diff |
| **Status quo (dispersed `if tier`)** | No new tooling | Drift recurs (#854-class) |

## Decision

1. **Do not** add OPA or `ethyca-fides` as a **runtime** dependency or replace **`core/licensing/`** JWT/Ed25519 enforcement.
2. **Adopt as target architecture (when scheduled):** a **CI lint step** that:
   - loads a **canonical Rego policy** mirroring [ADR 0027](ADR-0027-commercial-tier-boundaries-licensing-docs-and-future-jwt-claims.md) / `#853` ladder;
   - compares against a **generated manifest** from `FEATURE_TIER_MAP` + connector registry metadata;
   - **fails the build** on mismatch (missing connector row, tier downgrade, orphan feature).
3. **Prototype (isolated, not wired to CI yet):** `research/licensing/opa_tier_drift_prototype/` — sample Rego + README; proves expressiveness for connector tier cases (#854) without touching production gates.
4. **Implementation** of the CI job is **out of scope** for #1079; track via follow-up issue after operator prioritizes #854/#887/#845 cluster.

## Consequences

- **Positive:** Clear north star for tier drift prevention without bloating the runtime image.
- **Negative:** Two sources of truth until the exporter + lint land; Rego must be maintained when tiers change.
- **Watch:** When CI lint ships, extend `tests/test_claims_consistency.py` or add a dedicated gate — do not weaken existing connector fail-closed registry (#854).

## References

- GitHub **#1079** (evaluation), **#854**, **#887**, **#845**
- `research/licensing/opa_tier_drift_prototype/README.md`
- [ADR 0064](ADR-0064-license-enforcement-additive-model.md) — runtime enforcement stays additive
