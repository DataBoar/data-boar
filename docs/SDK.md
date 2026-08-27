# Boar Plugin SDK — language-neutral contract

**Português (Brasil):** companion narrative stays in [PLUGIN_SDK.pt_BR.md](PLUGIN_SDK.pt_BR.md) for the **L1 Python** how-to; this file is the **contract hub** (epic [#865](https://github.com/DataBoar/data-boar/issues/865)).

## What “SDK” means here

| Term | Meaning |
| ---- | ------- |
| **Contract** | Versioned JSON envelope (`sdk_contract_version`) — the fixed point |
| **Plugin** | Binding surface where a sidecar/runtime touches Data Boar |
| **Sidecar** | Runtime that executes (in-process, OS process, or remote API) |
| **Transport** | Adapter carrying the same envelope (stdio / gRPC / HTTP) — not a parallel protocol |

Machine schema (plugin envelope): [`sdk/PLUGIN_CONTRACT.schema.json`](sdk/PLUGIN_CONTRACT.schema.json)

L1 **metadata_manifest** (sidecar input, `--export-l1`): pin of DataBoar/data-boar-sdk `schema/metadata_manifest.schema.json` at [`sdk/metadata_manifest.schema.json`](sdk/metadata_manifest.schema.json) + [`sdk/metadata_manifest.pin.json`](sdk/metadata_manifest.pin.json) (not a second contract).

L3 **transformed_rows** (real-data plane, `--export-l3`): pin of `schema/transformed_rows.schema.json` at [`sdk/transformed_rows.schema.json`](sdk/transformed_rows.schema.json) + [`sdk/transformed_rows.pin.json`](sdk/transformed_rows.pin.json) (not a second contract). Grant-scoped; stdout unless `--l3-persist`. Network drift canary: `DATA_BOAR_SDK_SCHEMA_CHECK=1` / workflow `sdk-schema-pin-canary.yml`. Refresh pins: `scripts/sync_sdk_schema_pin.py`. `co_columns` waits on [data-boar-sdk#41](https://github.com/DataBoar/data-boar-sdk/issues/41).

Examples: [`sdk/example-request.json`](sdk/example-request.json), [`sdk/example-decision.json`](sdk/example-decision.json)

## Tiers (L1 / L2 / L3)

| Tier | Coupling | Status | Partner entry |
| ---- | -------- | ------ | ------------- |
| **L1** | In-process Python `RemediationPlugin` | **Shipped** (#606 / #611 / #1443) | [PLUGIN_SDK.md](PLUGIN_SDK.md) |
| **L2** | Sidecar process (stdin/stdout JSON-RPC-shaped, or local gRPC) | **Contract defined**; reference stdio stub under `docs/sdk/stubs/` | This doc + [#695](https://github.com/DataBoar/data-boar/issues/695) |
| **L3** | External HTTPS API | **Schema defined**; drivers demand-pulled | [#695](https://github.com/DataBoar/data-boar/issues/695) · [ADR-0086](adr/ADR-0086-plugin-sdk-language-neutral-contract.md) |

YAML **detection** plugins ([ADR-0052](adr/ADR-0052-yaml-plugin-system-centralized-schema.md)) are a **different** surface — they teach the detector patterns; they are not remediation partners.

## Envelope fields (normative)

All messages carry:

- `sdk_contract_version` — semver pin (start: `1.0.0`)
- `schema` — message type constant (`databoar.remediation.l3.request` \| `databoar.plugin.decision` \| `databoar.remediation.l3.receipt`)

**Host → plugin request** also carries:

- `trust_level` / optional `integrity_state` — host trust signals
- `targets[]` — metadata-only remediation targets (no raw PII samples by default)
- optional `capabilities[]` — go-plugin-shaped negotiation tokens

**Plugin → host decision** carries per-finding `action` + `reason`. Status `rejected_host_trust` / `safe_hold` means the plugin refused to act.

## Bidirectional mesh (#1116)

Topology is a **mesh**, not a one-way host chain: Boar may be **host** or **guest-plugin**. Same `trust_level` enum on both roles.

| Message | Schema const | Role |
| ------- | ------------ | ---- |
| Challenge | `databoar.attestation.challenge` | host or guest |
| Response | `databoar.attestation.response` | host or guest (Ed25519 `signature_b64`) |

Examples: [`sdk/example-attestation-challenge.json`](sdk/example-attestation-challenge.json), [`sdk/example-attestation-response.json`](sdk/example-attestation-response.json).

**Dogfood:** `boar_fast_filter` is the first in-house guest (`core/sdk/boar_fast_filter_dogfood.py` + Rust `guest_accepts_host_trust`). Mutual attestation must succeed before filter batches cross the boundary.

**Anti-overclaim:** envelopes are **C2PA-inspired** — not CAI / C2PA certified.

Implementation: [ADR-0087](adr/ADR-0087-plugin-sdk-bidirectional-zero-trust-mesh.md) · issue [#1116](https://github.com/DataBoar/data-boar/issues/1116).

## Fail-graceful (Safe-Hold)

Invariant: a plugin that crashes, hangs, returns invalid output, or rejects trust **must not** abort the Data Boar scan worker.

- **L1 today:** `maybe_run_remediation_hook` catches `PluginError` and other exceptions → stderr + skip ([ADR-0059](adr/ADR-0059-remediation-plugin-architecture.md)).
- **L2/L3 (planned):** hard timeout, kill → Safe-Hold, schema validation of decision/receipt before applying side effects ([ADR-0086](adr/ADR-0086-plugin-sdk-language-neutral-contract.md)).
- **Bidirectional:** guest refuses tinted host; host contains guest crypto/runtime violations ([ADR-0087](adr/ADR-0087-plugin-sdk-bidirectional-zero-trust-mesh.md)).

## Transport prior art (do not reinvent)

Tier is chosen **by environment policy** up front (air-gap vs local sidecar vs remote). See [data-boar-sdk#6](https://github.com/DataBoar/data-boar-sdk/issues/6) and ladder [#1199](https://github.com/DataBoar/data-boar/issues/1199):

| Prior art | Role |
| --------- | ---- |
| HashiCorp **go-plugin** | Versioned handshake, health, gRPC host↔plugin, deadlines |
| **Connect-RPC** | One `.proto` → gRPC + HTTP/JSON |
| **JSON-RPC / stdio** (LSP, **MCP**) | F2 air-gap first-class |

Protobuf (when used) is a **projection** of this JSON Schema envelope — not a second semantic contract.

## How to conform (any language)

1. Emit/consume messages that validate against `PLUGIN_CONTRACT.schema.json`.
2. Honor `sdk_contract_version` negotiation (reject unknown major; Safe-Hold).
3. On tinted/adulterated `trust_level`, return `status: rejected_host_trust` or `safe_hold` — do not remediate.
4. Never require network for the F2/stdio path.
5. For L1 Python only, also implement `RemediationPlugin` per [PLUGIN_SDK.md](PLUGIN_SDK.md).

## Reference stub (L2 stdio)

`docs/sdk/stubs/l2_jsonrpc_echo.py` — minimal JSON-RPC-over-stdio echo that returns a `safe_hold` decision for any request. Used in conformance tests; not a production remediator.

## Related ADRs / issues

- [ADR-0059](adr/ADR-0059-remediation-plugin-architecture.md) — L1 in-process hook
- [ADR-0086](adr/ADR-0086-plugin-sdk-language-neutral-contract.md) — language-neutral host contract
- [ADR-0087](adr/ADR-0087-plugin-sdk-bidirectional-zero-trust-mesh.md) — bidirectional / guest-side mesh
- Epic [#865](https://github.com/DataBoar/data-boar/issues/865) · partner [#695](https://github.com/DataBoar/data-boar/issues/695) · L1 guide [#611](https://github.com/DataBoar/data-boar/issues/611) · bidirectional [#1116](https://github.com/DataBoar/data-boar/issues/1116)
- Maintainer plan index: [docs/README.md](README.md) (*Internal and reference*)
