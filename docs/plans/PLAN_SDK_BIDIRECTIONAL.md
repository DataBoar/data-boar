# PLAN — Plugin SDK bidirectional zero-trust mesh (#1116)

**Status:** 🟡 In progress (Fatia C wiring landed; scan opt-in follow-up)
**Issue:** [#1116](https://github.com/DataBoar/data-boar/issues/1116)
**ADR:** [ADR-0087](../adr/ADR-0087-plugin-sdk-bidirectional-zero-trust-mesh.md)
**Depends on:** Fatia B contract ([PLAN_PLUGIN_SDK_CONTRACT.md](PLAN_PLUGIN_SDK_CONTRACT.md) / [#865](https://github.com/DataBoar/data-boar/issues/865))
**Design source:** vault GAP-010 (aggregation — not invention)

## Motivation

Host-only SDK leaves Boar unable to act as a **guest-plugin** (augmented capacity) and leaves trust one-sided. Mesh doctrine: *host contains bad plugin ↔ plugin refuses tinted host*.

## Phases

| # | Item | Status |
| - | ---- | ------ |
| 1 | Schema: attestation challenge/response + `mesh_role`; `trust_level` both sides | ✅ |
| 2 | `core/sdk/mutual_attestation.py` Ed25519 handshake (fail-closed) | ✅ |
| 3 | Conformance: host-tinted → guest refuses; guest-violates → host contains | ✅ |
| 4 | Dogfood: `boar_fast_filter` party + Rust `guest_accepts_host_trust` | ✅ |
| 5 | ADR-0087 + inventory + genesis fixture | ✅ |
| 6 | Hub / PLANS_TODO order row | ✅ |
| 7 | Document Futurex 4-timestamp chain as canonical partner case (no driver) | ✅ |
| 8 | Opt-in scan-path wiring (Enterprise) | ⬜ follow-up |

## Acceptance (#1116)

- [x] Contract guest-side + host-side surfaces; `trust_level` on both
- [x] Conformance tests for both roles
- [x] `boar_fast_filter` mutual attestation dogfood with core
- [x] This plan + `plans_hub_sync.py --write` + PLANS_TODO
- [x] ADR symmetric contract (0087)
- [x] Anti-overclaim: C2PA-**inspired**, never “certified” without CAI

## Out of scope (this slice)

- Futurex / Wabix production drivers
- Claiming C2PA / CAI certification
- Mandatory enablement on every scan (opt-in remains follow-up)

## Futurex canonical note

Boar↔Futurex bidirectional value (eyes↔hands) uses a **four-timestamp signed** handoff (vault FUTUREX-C2PA-FPE-ARCHITECTURE). That pattern maps onto attestation challenge/response + decision/receipt envelopes; drivers stay demand-pulled.
