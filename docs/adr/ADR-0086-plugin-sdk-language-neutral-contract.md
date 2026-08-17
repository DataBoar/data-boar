# ADR 0086 — Plugin SDK language-neutral contract (L1/L2/L3)

- **Date (UTC):** 2026-08-09
- **Authors:** Fabio Leitao
- **Deciders:** Fabio Leitao

## Status

Proposed

### Status history

- 2026-08-09 — Proposed (epic [#865](https://github.com/DataBoar/data-boar/issues/865); Fatia B contract files)

## Context

L1 remediation hooks ship today ([ADR-0059](ADR-0059-remediation-plugin-architecture.md)): in-process Python `RemediationPlugin`, fail-graceful Safe-Hold, Enterprise gate. Partners and sidecars need a **language-neutral, versioned envelope** for L2 (process) and L3 (HTTP) without forking core semantics per transport.

Related:

- [#695](https://github.com/DataBoar/data-boar/issues/695) / [PLAN_PLUGIN_PARTNER_INTERFACE.md](../plans/PLAN_PLUGIN_PARTNER_INTERFACE.md) — partner hierarchy + L3 field catalogue
- [#1199](https://github.com/DataBoar/data-boar/issues/1199) — envelope ladder F0→F5
- [data-boar-sdk#6](https://github.com/DataBoar/data-boar-sdk/issues/6) — gRPC adapter + prior art (go-plugin, Connect-RPC, JSON-RPC/stdio≈MCP)
- [#1116](https://github.com/DataBoar/data-boar/issues/1116) — bidirectional / guest-side (deferred; not this ADR’s implementation scope)

## Decision

1. **Contract is the fixed point** — JSON Schema at `docs/sdk/PLUGIN_CONTRACT.schema.json` defines request / decision / receipt envelopes with `sdk_contract_version`. Runtimes and languages are adapters behind that schema.

2. **Trust travels in the envelope** — Host→plugin messages include `trust_level` (and optional `integrity_state`). Conformant plugins **SHOULD** refuse remediation when the host is tinted/adulterated (`rejected_host_trust` / `safe_hold`). Full bilateral guest-side attestation remains [#1116](https://github.com/DataBoar/data-boar/issues/1116).

3. **Tier boundary** — L1 stays Protocol + `importlib` (ADR-0059). L2 = sidecar (stdio JSON-RPC-shaped and/or local gRPC). L3 = external HTTPS drivers. Open-core does not ship L2/L3 partner drivers.

4. **Fail-graceful generalized** — Invalid contract output, crash, timeout, or trust rejection → Safe-Hold of the remediation target; **never** abort the scan worker (same invariant as ADR-0059).

5. **Transport prior art, not greenfield negotiation** — Capability/version handshake and health follow **HashiCorp go-plugin**-shaped patterns; F2 air-gap uses **JSON-RPC/stdio (MCP/LSP)**; F4 dual gRPC+HTTP/JSON prefers **Connect-RPC**-shaped single service definition. Protobuf is a projection of the Schema envelope (or HITL proto-first with Schema export — tracked in sdk#6 / #1199). Tier selection is **environment policy**, not reactive fallback-on-error.

6. **Default payload is metadata-only** — No raw PII samples in the default contract profile (aligns with #649 taxonomy).

## Consequences

### Positive

- Partners can implement in any language against one schema.
- L1 docs remain valid; L2/L3 gain a stable target without rewriting ADR-0059.
- Avoids reinventing handshake already solved by mature OSS.

### Negative / trade-offs

- Schema and protobuf must stay in sync when F3.gRPC lands (process debt).
- Bidirectional zero-trust (#1116) needs a later ADR amend or sibling ADR.

### Neutral

- Reference `docs/sdk/stubs/l2_jsonrpc_echo.py` is illustrative only — not a production remediator.

## References

- [docs/SDK.md](../SDK.md)
- [PLAN_PLUGIN_SDK_CONTRACT.md](../plans/PLAN_PLUGIN_SDK_CONTRACT.md)
- Epic #865 · #695 · #1199 · data-boar-sdk#6 · #1116
