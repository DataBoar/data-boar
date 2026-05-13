# Plan: GRC-inspired trust accelerators for enterprise recognition

**Status:** Active
**Date:** 2026-03-25
**Authors:** Fabio Leitao
**Priority:** H0

**Audience:** Internal product planning (operator + maintainers)

## Purpose

Translate practical security inspiration (Security Now / GRC style) into concrete Data Boar slices that improve enterprise trust, auditability, and commercial readiness without derailing token-aware delivery.

## Current baseline (already good)

- Secure-by-default direction is documented (HTTPS-first and explicit risk mode planning).
- Release and process discipline improved (tests, checks, runbooks, release notes).
- Trust and hardening narrative exists in plans/docs, with clear migration awareness.

## Gap to "THE SOLUTION" brand target

We still need a stronger "trust evidence loop" in runtime behavior:

1. **Detect** suspicious trust state quickly.
1. **Communicate** degraded confidence clearly to operators/stakeholders.
1. **Constrain output** when trust state is degraded.
1. **Prove traceability** in a way enterprise reviewers can audit.

## Proposed accelerators (new slices)

### A1 — Trust-state contract (small, high leverage)

- Define one canonical runtime contract:
- `trusted`, `degraded`, `untrusted` (or equivalent naming).
- Wire contract to:
- logs/stdout/stderr,
- API status payload,
- report metadata,
- DB/audit row.

**Why now:** creates single-source-of-truth semantics for all later security work.

### A2 — Output confidence policy

- Add deterministic policy for degraded trust:
- normal output in `trusted`,
- reduced output and warning header in `degraded`,
- strict minimal output in `untrusted`.

**Why now:** aligns with enterprise expectation that risky states do not emit normal-looking evidence.

### A3 — Crypto/runtime baseline self-check

- Add startup/runtime checks for minimum TLS/crypto posture (no weak/EOL protocols/ciphers).
- Persist self-check results in status/audit surfaces.

**Why now:** operationalizes existing "non-negotiable crypto baseline" intent.

### A4 — Evidence packet for review cycles

- Create one compact "review packet" template per milestone:
- what changed,
- why risk is reduced,
- test proof,
- known limits and next step.

**Why now:** improves external review quality (Corporate-Entity-C or enterprise stakeholders) and sales confidence.

## Suggested milestone mapping

- **M-TRUST-01:** A1 contract + tests + docs.
- **M-TRUST-02:** A2 output confidence gates + report/API markers.
- **M-TRUST-03:** A3 crypto self-check + observability links.
- **M-TRUST-04:** A4 review packet process adopted in one cycle.

## Corporate-Entity-C review integration suggestion

Ask next Corporate-Entity-C cycle after **M-TRUST-01** (minimum) lands, preferably with part of **M-TRUST-02**.
This gives reviewers concrete runtime deltas, not only roadmap prose.

## Optional backlog cross-link (privacy / rich media)

- **Tier 3b embedded tracker heuristics** (opt-in; Meta/TikTok-style references in rich media): [PLAN_ADDITIONAL_DATA_SOUP_FORMATS.md](PLAN_ADDITIONAL_DATA_SOUP_FORMATS.md) § Tier 3b. Fits enterprise narrative (governance + optional advanced mode) without blocking core trust work.

## Token-aware execution notes

- Keep each accelerator as one narrow PR slice (contract, policy, self-check, packet).
- Do not bundle all security tracks together in one large change.
- Update operator-facing docs only for behavior already shipped.

## Candidate to-do entries for `PLANS_TODO.md` (future sync)

1. Add row: "Trust-state contract and propagation (A1)".
1. Add row: "Confidence-gated output policy (A2)".
1. Add row: "Crypto baseline self-check surfacing (A3)".
1. Add row: "Enterprise review evidence packet template (A4)".

---

This plan is an accelerator overlay; it complements existing HTTPS/default-hardening plans rather than replacing them.
