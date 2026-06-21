# ADR 0073 — Version scheme: octet-maturity build numbers + release-line roadmap

- **Date (UTC):** 2026-06-21
- **Authors:** Fabio Leitao
- **Deciders:** Fabio Leitao
- **Consulted:** Claude (RO auditor); Steve Gibson / GRC (Engineering Craft Inspiration)

## Status

Proposed

### Status history

- 2026-06-21 — Proposed

## Context

Versioning today is governed only by `docs/VERSIONING.md` (major.minor.build + `-beta`/`-rc`). Two LLM naive-default slips:

1. Premature promotion `1.7.4-rc → 1.7.4` (#970) — a build with no maturity semantics let "bump to stable" happen without structural meaning.
2. Phantom roadmap `1.7.5-beta` (#772) — agents inferred "next = 1.7.5" by naive increment, against the real roadmap (1.8.x).

A richer scheme (vault `self-upgrade-beacon-heartbeat-design-2026-06-15`, Gibson-style) was intended to stay internal; the failures justify exposing it in the public number.

## Decision

1. **Octet-maturity in the build (Gibson DNS-beacon style):** **0–127 beta · 128–199 rc · 200–255 release** (`.200` = GA; `.201` = fix-1; …). The beacon A-record carries this (lightweight trigger); the public number now exposes it too.
2. **Burned GA:** `1.7.4` (≡ build `.200`) = VOID (#970); the real release starts at `1.7.4.201` (fix-1 post-GA).
3. **Release-line roadmap (semver intent):** `1.7.4.x` = open-core maturity + commercial JWT protection (fix line); `1.8.x` = augmented corporate capacities (re-ID, sidecars, plugins/Clojure — new function, does **not** fit a 1.7 minor). **`1.7.5` does not exist.** Specific = `1.8.0-beta`, generic = `1.8.x`, horizon = `1.9.x`.
4. `docs/VERSIONING.md` documents (1) + (3); full DNS-beacon/heartbeat/kill-switch lifecycle = 1.8.x roadmap (PLAN_SELF_UPGRADE), out of scope here.

## Rationale

- Octet-maturity makes "is this a release?" a property of the **number**, not inference → kills the #970 class.
- Explicit roadmap (no 1.7.5) → kills the #772 class.
- Gibson lineage: proven scheme (SpinRite/DNSBench build numbers), Engineering Craft Inspiration the repo already tracks.

## Consequences

- **Positive:** the number self-documents maturity; agents cannot invent 1.7.5 or naively bump stable.
- **Cost:** VERSIONING.md update + exposure (ex-internal) + CI guard (denylist strings + stable-com-gate-aberto).
- **Pairs with ADR-0072 (gate)** — together they surround the whole release surface.

## Alternatives Considered

1. **Pure semver suffix-only (current):** rejected — produced #970 + #772.
2. **Keep octet internal-only:** rejected — the failures prove the public number needs the discipline.

## Related Decisions

- [ADR 0072 — Commit Gate vs Release Gate](ADR-0072-commit-gate-vs-release-gate-distinct-criteria.md)
- [ADR 0045 — ADR metadata and format standardization (UMADR)](ADR-0045-adr-metadata-and-format-standardization.md)
- [ADR 0048 — operator-facing taxonomy and naming contract](ADR-0048-operator-facing-taxonomy-and-naming-contract-preservation.md)
- GitHub #970 (`1.7.4` VOID), #971 (VERSIONING octet), #772 (`1.7.5` → `1.8`), #717 (kill-switch), PLAN_SELF_UPGRADE

## References

- Steve Gibson / GRC versioning (DNSBench `1.3.6668.0`-style) — Engineering Craft Inspiration (vault `_inspirations/SECURITY_INSPIRATION_GRC_SECURITY_NOW.md`)
