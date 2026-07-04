# ADR 0074 — Supply-chain Layer 1: digest pins and Rust SCA

- **Date (UTC):** 2026-06-23
- **Authors:** Fabio Leitao
- **Deciders:** Fabio Leitao

## Status

Proposed

### Status history

- 2026-06-23 — Proposed (materialized to close dangling reference: supply-chain posture #987 cited across CI, Dockerfile, dependabot, grype, and deny.toml since PR #998; ADR file missing — PR #997 touched only INVENTORY.txt).

## Context

The build and release pipeline pulls third-party GitHub Actions, base container images, and Rust crates — each a supply-chain entry point. Without pinning and scanning, a compromised upstream tag or a vulnerable transitive crate can enter a release silently.

[ADR 0005](ADR-0005-ci-github-actions-supply-chain-pins.md) established Action SHA pinning and a pinned **uv** CLI in CI; this ADR records **Layer 1** of the broader supply-chain posture (GitHub #987) and ties together digest-pinned images, Rust SCA, and distroless image scanning already enforced in workflows and tests.

## Decision

Layer 1 of the supply-chain posture is mandatory and mechanical:

1. **Actions pinned to full commit SHAs** — no floating tags in `.github/workflows/*`.
2. **Base image digest pins** — `Dockerfile` `FROM` lines pinned by digest; the Dependabot docker ecosystem proposes digest bumps.
3. **Rust SCA before merge** — `cargo-deny` (`rust/boar_fast_filter/deny.toml`) gates advisories and license drift.
4. **Distroless + Grype gate** — the assembled image is scanned; findings block release.

## Rationale

1. Pinning removes the moving-tag attack surface: a rebuilt CI run resolves the exact bytes reviewed.
2. Rust SCA catches vulnerable transitive crates before they reach a build, not after.

Each layer is additive and does not replace the previous one; Layer 1 is the mechanical floor on which detection layers (L3/L4) rest.

## Consequences

- **Positive:** Reproducible, reviewable supply-chain; no floating upstream.
- **Negative:** Digest/SHA bumps require Dependabot churn and a review cadence.

## Related Decisions

- [ADR 0005 — CI and GitHub Actions supply chain pins](ADR-0005-ci-github-actions-supply-chain-pins.md)
- [ADR 0063 — Ed25519 license JWT signing](ADR-0063-ed25519-license-jwt-signing.md)
- [ADR 0075 — Plugin authentication: file-based vs Bearer](ADR-0075-plugin-auth-file-based-vs-bearer.md)
- GitHub #987 (decision) · #988 (Layer 1 implementation) · #997 (inventory-only merge — the gap)
- [PLAN_IMAGE_HARDENING](../plans/completed/PLAN_IMAGE_HARDENING.md) (completed)

## References

- `tests/test_github_workflows.py` — Layer 1 workflow and Dockerfile guards
- `tests/test_docker_image_hardening.py` — digest-pinned `FROM` stages
- `.github/dependabot.yml` — docker ecosystem digest bumps
- `.grype.yaml` — distroless scan policy
- `rust/boar_fast_filter/deny.toml` — `cargo-deny` policy
