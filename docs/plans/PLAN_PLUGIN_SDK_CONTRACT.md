# PLAN — Plugin SDK language-neutral contract (#865)

**Status:** 🟡 In progress
**Issue:** [#865](https://github.com/DataBoar/data-boar/issues/865)
**ADR:** [ADR-0086](../adr/ADR-0086-plugin-sdk-language-neutral-contract.md)
**Hub doc:** [docs/SDK.md](../SDK.md)

## Motivation

L1 Python remediation is shipped. Epic #865 needs a **versioned, language-neutral contract** (schema + docs + fail-graceful conformance) before L2/L3 drivers and bidirectional work (#1116).

## Sequencing (approved Fatias)

| Fatia | Issue | Deliverable |
| ----- | ----- | ----------- |
| A | #695 | Partner interface plan (transport prior art latch) |
| **B (this)** | **#865** | Schema + SDK.md + ADR-0086 + Safe-Hold conformance + thin L2 stub |
| C | #1116 | Bidirectional / guest-side (later) |

## Phases

| # | Item | Status |
| - | ---- | ------ |
| 1 | `docs/sdk/PLUGIN_CONTRACT.schema.json` + examples | ✅ |
| 2 | `docs/SDK.md` (tiers, fail-graceful, prior art, how to conform) | ✅ |
| 3 | ADR-0086 + inventory | ✅ |
| 4 | Conformance tests (invalid decision / crashing L1 → Safe-Hold; schema validates examples) | ✅ |
| 5 | Thin L2 stdio stub (`docs/sdk/stubs/l2_jsonrpc_echo.py`) | ✅ |
| 6 | Hub / PLANS_TODO order row (7e) | ✅ |

## Out of scope (this plan)

- #1116 bidirectional attestation / Futurex drivers
- Production L2/L3 remediator implementations
- Reinventing go-plugin handshake semantics

## Acceptance (epic #865 — Fatia B slice)

- [x] Machine-readable contract schema under `docs/sdk/`
- [x] Operator-facing `docs/SDK.md`
- [x] ADR proposed + G0-S inventory
- [x] Tests prove Safe-Hold on bad/crashing plugin path
- [x] Reference L2 stub present (non-production)

Full epic close may wait for remaining stub/driver polish; Fatia B lands the **contract fixed point**.
