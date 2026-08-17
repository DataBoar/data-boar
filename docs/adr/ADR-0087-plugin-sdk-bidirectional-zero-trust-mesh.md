# ADR 0087 — Plugin SDK bidirectional zero-trust mesh (#1116)

- **Date (UTC):** 2026-08-09
- **Authors:** Fabio Leitao
- **Deciders:** Fabio Leitao

## Status

Proposed

### Status history

- 2026-08-09 — Proposed ([#1116](https://github.com/DataBoar/data-boar/issues/1116); Fatia C; vault GAP-010 aggregation)

## Context

[ADR-0086](ADR-0086-plugin-sdk-language-neutral-contract.md) fixed the language-neutral **host→plugin** envelope. Epic design (vault **GAP-010**) requires a **mesh**, not a one-way chain: Boar must also act as a **guest-plugin** (augmented capacity inside another host), with `trust_level` on **both** roles and mutual attestation before data exchange.

Related: [#865](https://github.com/DataBoar/data-boar/issues/865) · [#695](https://github.com/DataBoar/data-boar/issues/695) · [#917](https://github.com/DataBoar/data-boar/issues/917) (SSHSIG) · [ADR-0059](ADR-0059-remediation-plugin-architecture.md) · [ADR-0075](ADR-0075-plugin-auth-file-based-vs-bearer.md) · Ed25519 license spine.

First in-house conformant guest: **`rust/boar_fast_filter`** (dogfood) — distrust even “home” components.

## Decision

1. **Symmetric roles** — Contract messages carry `role: host|guest`. The same `trust_level` enum applies to both parties ([`PLUGIN_CONTRACT.schema.json`](../sdk/PLUGIN_CONTRACT.schema.json) attestation challenge/response).

2. **Mutual attestation before data** — Challenge/response with Ed25519, pinned peer pubkeys, nonce echo (anti-replay), freshness window, integrity anchor. Implemented in `core/sdk/mutual_attestation.py`. Channel opens only when both legs verify.

3. **Bidirectional Safe-Hold** — Guest refuses tinted/adulterated host (`rejected_host_trust` / `HOST_TRUST_REJECTED`) and does not process. Host contains guest violations (bad signature, crash) without aborting the scan worker.

4. **Dogfood path** — `core/sdk/boar_fast_filter_dogfood.py` + Rust `guest_accepts_host_trust` prove the mesh with a component we control. Production scan wiring may opt into this gate later; conformance tests lock the contract now.

5. **Anti-overclaim** — Attestation envelopes are **C2PA-inspired** Content Credential shapes. Do **not** claim CAI / C2PA **certification** without a real CAI path.

6. **Futurex canonical case (document)** — The four-timestamp signed Boar↔Futurex handoff remains the partner bidirectional pattern; not implemented as a driver in this ADR.

7. **IP / ownership** — When Boar runs as guest inside another platform, plugin/connector ownership MUST be defined in the engagement paper **before** production packaging (GAP-010 caveat).

## Consequences

### Positive

- Zero-trust doctrine is testable without waiting for external partners.
- ADR-0086 host envelope stays valid; attestation messages are additive.

### Negative / trade-offs

- Key pinning and release-anchor distribution are operational debt (lab keys ≠ customer HSM).
- Full scan-path opt-in for dogfood attestation is a follow-up (Enterprise / 1.8.x).

## References

- [PLAN_SDK_BIDIRECTIONAL.md](../plans/PLAN_SDK_BIDIRECTIONAL.md)
- [docs/SDK.md](../SDK.md) (bidirectional section)
- Vault GAP-010 (operator-private design source; aggregation, not invention)
