# ADR 0075 — Plugin authentication — file-based license vs Bearer per-request

- **Date (UTC):** 2026-06-21
- **Authors:** Fabio Leitao
- **Deciders:** Fabio Leitao

## Status

Proposed

### Status history

- 2026-06-21 — Proposed (renumbered from GitHub #769; **0067** collides with ADR-0068)

## Context

External plugins (L3) and in-process extensions (L2) need a clear **auth boundary** with
the core before implementation ([ADR 0052](ADR-0052-yaml-plugin-system-centralized-schema.md),
GitHub #695). FastAPI RBAC patterns (`require_permission`, #86, #414) are the idiomatic
scope gate for HTTP surfaces.

License enforcement is [ADR 0064](ADR-0064-license-enforcement-additive-model.md) —
**tier** (what product edition) must stay orthogonal to **scope** (what action on what resource).

**Numbering note:** Issue #769 originally targeted ADR-0067; **0067** was consumed by the
primary Linux workstation ADR (now **0068**). This record uses the next free slot **0075**
(**0074** reserved for supply-chain ADR, GitHub #987).

## Decision

**Adopt option C (hybrid) as the default architecture (Proposed):**

| Layer | Mechanism | Controls |
| --- | --- | --- |
| **Host / core process** | File-based JWT license ([ADR 0063](ADR-0063-ed25519-license-jwt-signing.md), [ADR 0064](ADR-0064-license-enforcement-additive-model.md)) | **Tier** — Community / Pro / Enterprise |
| **Plugin runtime** | Internal RBAC — `require_permission` factories, plugin manifest permissions | **Scope** — which APIs and data domains |

Plugins **inherit the host tier** (option A property) but gain **distinct scope** via RBAC
(option B property) **without** issuing a second per-request Bearer JWT to external plugins
by default.

### Options retained for Enterprise extensions

| Option | When to use |
| --- | --- |
| **A — File-based only** | Single-tenant deployments; plugin tier = host tier; simplest path. |
| **B — Bearer per-request** | Future Enterprise multi-tenant broker when plugins need **identity separate from host tier** — requires token issuance endpoint; **not** v1.8 default. |
| **C — Hybrid (chosen default)** | L2/L3 partner interface (#695): Ed25519 file license + internal permission checks. |

**Explicit non-choice:** HS256 symmetric “course JWT” patterns are **inferior** to the
existing Ed25519 file-based model and must not replace [ADR 0063](ADR-0063-ed25519-license-jwt-signing.md).

## Rationale

1. **Orthogonal axes:** Licensing and RBAC stay separable — easier to test and audit.
2. **Backward compatibility:** Matches current `LicenseGuard` + dashboard permission model.
3. **Enterprise readiness:** Option B remains available without forcing token infrastructure
   on every L3 integrator on day one.

## Consequences

- **Positive:** Clear build order — enforce tier ([ADR 0064](ADR-0064-license-enforcement-additive-model.md)),
  then plugin permission schema ([ADR 0052](ADR-0052-yaml-plugin-system-centralized-schema.md)).
- **Negative:** Hybrid model needs documented permission matrix for partners.
- **Watch:** Revisit Bearer per-request when #695 L3 external auth requirements solidify.

## Alternatives Considered

Full analysis of options A/B/C — see Decision table; A alone insufficient for per-plugin
scope; B alone adds operational burden before L3 demand is proven.

## Related Decisions

- [ADR 0052 — YAML plugin system](ADR-0052-yaml-plugin-system-centralized-schema.md)
- [ADR 0064 — License enforcement](ADR-0064-license-enforcement-additive-model.md)
- GitHub #769 (renumbered here), #695, #86, #414

## References

- [Documenting Architecture Decisions (Michael Nygard)](https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions)
- Operator study notes (private vault) — FastAPI securing/deploying/scaling mapping
