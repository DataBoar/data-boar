# ADR 0090 — Open-core / plugin boundary: Pro auditability, reference sample, reverse leakage guard

- **Date (UTC):** 2026-08-18
- **Authors:** Fabio Leitao
- **Deciders:** Fabio Leitao

## Status

Accepted

### Status history

- 2026-08-18 — Proposed (GitHub [#811](https://github.com/DataBoar/data-boar/issues/811)). Number **0090** chosen so it does not collide with [ADR-0089](ADR-0089-native-package-signed-repository-hosting-keys-and-community-boundary.md) ([#1405](https://github.com/DataBoar/data-boar/issues/1405), signed native package repos; now **Accepted** on `main`).
- 2026-08-28 — Accepted (operator ratification: G1 `PLAN_PRO_PLUGIN_AUDITABILITY.md`;
  G3 child [#1624](https://github.com/DataBoar/data-boar/issues/1624) OPEN as designed;
  G2 in declared scope — this ADR remains design, code is follow-up). Genesis Date
  (UTC) unchanged.

## Context

Data Boar’s commercial shape is already partially decided:

| Existing ADR / plan | Covers | Does **not** cover |
| ------------------- | ------ | ------------------ |
| [ADR 0027](ADR-0027-commercial-tier-boundaries-licensing-docs-and-future-jwt-claims.md) | Open-core vs Pro/Partner/Enterprise narrative; JWT claim docs; named buyers only in `docs/private/` | How a regulated customer **audits the Pro/plugin binary** without receiving full OSS |
| [ADR 0052](ADR-0052-yaml-plugin-system-centralized-schema.md) | Central YAML **pattern** plugin schema + validator | Executable SDK **sample** plugin / CI conformance of L1–L3 contracts |
| [ADR 0086](ADR-0086-plugin-sdk-language-neutral-contract.md) (Proposed) | Language-neutral L1/L2/L3 envelope | Public reference plugin; Pro IP leakage guard; sample-vs-crown-jewel curation |
| [PLAN_PRODUCT_TIERS_AND_OPEN_CORE.md](../plans/PLAN_PRODUCT_TIERS_AND_OPEN_CORE.md) | Tier feature matrix | Artifact auditability model for Pro |
| [PLAN_YAML_PLUGIN_SYSTEM.md](../plans/PLAN_YAML_PLUGIN_SYSTEM.md) | Pattern-plugin rollout | Partner sidecar training sample |

Related in-flight plugin work: [#769](https://github.com/DataBoar/data-boar/issues/769) (auth), [#784](https://github.com/DataBoar/data-boar/issues/784) (Rust SDK panic-safety/FFI), [#785](https://github.com/DataBoar/data-boar/issues/785) (rate-limit surface), epic [#865](https://github.com/DataBoar/data-boar/issues/865).

**Vocabulary (do not collapse):**

1. **Scan Audit Trail** — evidence of *what the engine did* on a customer dataset (findings, manifests, `--export-audit-trail`).
2. **Artifact auditability** — evidence of *where the Pro/plugin engine came from* (build inputs, SBOM, signed provenance) so a regulated buyer can trust the scanner without the Pro tree being public BSD-3.

This ADR decides four gaps (**G1–G4**) from [#811](https://github.com/DataBoar/data-boar/issues/811). Named partner examples (tokenization, proprietary heuristics, author-side capabilities) stay under **gitignored** `docs/private/` per ADR-0027 item 3.

## Decision

### G1 — Pro auditability under least privilege (“narrow sudoer”)

Deliver **layered** artifact auditability; do **not** publish Pro/plugin crown-jewel source on the public BSD-3 tree.

| Layer | Mechanism | Default? |
| ----- | --------- | -------- |
| **A — Standard commercial** | Reproducible (or rebuildable) Pro/plugin artifacts + **SBOM** ([ADR 0003](ADR-0003-sbom-roadmap-cyclonedx-then-syft.md)) + **signed provenance / attestation** bound to the artifact digest | **Yes** — default offer for Enterprise/Pro procurement |
| **B — Deep contractual** | Source-available under **NDA** and/or time-boxed, read-only, **logged** review (clean-room / escrow-style) | When contract or regulator requires deeper inspection |
| **C — Optional** | Independent third-party attestation | When the buyer’s compliance program requires it |

**Non-goals for G1:** turning Pro into Community OSS; replacing scan Audit Trail with SBOM; implementing NDA tooling in this ADR’s documentation slice.

Operational backlog for layers A–C lives in [PLAN_PRO_PLUGIN_AUDITABILITY.md](../plans/PLAN_PRO_PLUGIN_AUDITABILITY.md).

### G2 — Public reference / sample plugin = executable spec + CI conformance

1. Maintain **one deliberately public** reference plugin that is commercially “cold” but pedagogically complete: exercises auth, lifecycle, and panic-safety/FFI (or the current SDK surface) end-to-end.
2. License: **BSD-3** (or equivalent “fork as starting point”) — explicit derivation welcome for third-party sidecars.
3. **CI conformance:** the sample must run in CI as a **contract canary** against the Plugin SDK envelope ([ADR 0086](ADR-0086-plugin-sdk-language-neutral-contract.md) / `docs/sdk/PLUGIN_CONTRACT.schema.json`). Failure means the contract drifted — treat as a breaking signal, not a flaky test.
4. **Not** the same artifact as ADR-0052’s YAML pattern plugins (`plugin_schema.yaml` / `patterns_plugin_file`).

**Implementation of the sample plugin is out of scope for the #811 documentation PR** — track as a follow-up issue once this ADR is Accepted (or explicitly greenlit while Proposed).

### G3 — Reverse leakage guard (Pro → public)

1. The public tree **must** gain a pre-commit/CI gate that **blocks restricted/Pro content** from landing on `origin` (inverse of the PII history / seed gate family; same fail-loud spirit as [ADR 0071](ADR-0071-self-protecting-pii-gate.md)).
2. Shape (design only in this ADR): path denylist and/or content markers + CODEOWNERS / tripwire for gate files; never weaken the gate to pass CI (see always-on never-weaken-security-gates doctrine).
3. **Code for the gate is not part of the #811 docs PR** — child issue for implementation: [#1624](https://github.com/DataBoar/data-boar/issues/1624).

### G4 — Curation: sample vs crown-jewel

| Eligible for **public sample** | Treat as **crown-jewel / Pro** (private repo, NDA, or gated artifact) |
| ------------------------------ | -------------------------------------------------------------------- |
| Exercises the **full public contract** without partner IP | Contains partner IP, paid differentiators, or author-side exclusive capability |
| Safe to publish under BSD-3; leakage does not burn margin | Leakage burns margin, partner trust, or regulated customer confidence |
| Pedagogically complete for third-party sidecar authors | “Hot” connectors / tokenization / proprietary heuristics |

Curators apply this table; they do **not** invent one-off exceptions without updating this ADR or the thin auditability plan.

## Alternatives considered

| Alternative | Why rejected |
| ----------- | ------------ |
| Publish Pro source as BSD-3 | Burns commercial margin and partner IP; contradicts open-core model |
| NDA-only auditability (no SBOM/provenance) | Fails modern regulated procurement that expects machine-verifiable supply chain |
| Sample as documentation only (no CI) | Contract drifts silently; partners cannot trust the SDK story |
| Reverse guard = CODEOWNERS alone | Easy to bypass; no CI tripwire |
| Collapse sample into ADR-0052 YAML plugins | Wrong abstraction layer (patterns ≠ SDK sidecar lifecycle) |

## Consequences

### Positive

- Partner onboarding and Enterprise procurement share one **artifact auditability** story distinct from scan Audit Trail.
- Third-party sidecar authors get a **public, CI-backed** starting point without receiving crown jewels.
- Public tree gains an explicit **anti-leak** obligation before Pro content can ship.

### Negative / trade-offs

- Follow-up work: sample plugin, reverse-guard implementation, NDA/clean-room playbooks (private ops).
- Must keep ADR-0086 schema, sample CI, and this ADR aligned when the contract moves.

### Watch

- When [ADR 0064](ADR-0064-license-enforcement-additive-model.md) is **Accepted** and runtime gating ships, re-read G1 language so “Pro artifact” matches enforced tiers.
- Child issues: G2 sample implementation; G3 reverse-guard code ([#1624](https://github.com/DataBoar/data-boar/issues/1624)); optional G1 layer-C vendor process (private).
- Adjacent supply chain: [#1405](https://github.com/DataBoar/data-boar/issues/1405) / [ADR-0089](ADR-0089-native-package-signed-repository-hosting-keys-and-community-boundary.md) (signed native package repos, Accepted) — numbering collision avoided by using **0090**.

## Related Decisions

- Amends (append-only Status history + Related): [ADR 0027](ADR-0027-commercial-tier-boundaries-licensing-docs-and-future-jwt-claims.md), [ADR 0052](ADR-0052-yaml-plugin-system-centralized-schema.md)
- [ADR 0003](ADR-0003-sbom-roadmap-cyclonedx-then-syft.md) — SBOM roadmap (G1 layer A)
- [ADR 0071](ADR-0071-self-protecting-pii-gate.md) — fail-loud gate doctrine (G3 spirit)
- [ADR 0086](ADR-0086-plugin-sdk-language-neutral-contract.md) — SDK contract (G2 CI target)
- [ADR 0088](ADR-0088-verify-the-verifier-no-self-referential-trust-chain.md) — verification order when attesting artifacts
- [ADR 0084](ADR-0084-native-package-embedded-cpython-by-channel.md) — native packaging channel (adjacent to #1405)

## References

- Issue [#811](https://github.com/DataBoar/data-boar/issues/811)
- [PLAN_PRODUCT_TIERS_AND_OPEN_CORE.md](../plans/PLAN_PRODUCT_TIERS_AND_OPEN_CORE.md)
- [PLAN_YAML_PLUGIN_SYSTEM.md](../plans/PLAN_YAML_PLUGIN_SYSTEM.md)
- [PLAN_PRO_PLUGIN_AUDITABILITY.md](../plans/PLAN_PRO_PLUGIN_AUDITABILITY.md)
- [PLAN_PLUGIN_SDK.md](../plans/PLAN_PLUGIN_SDK.md) · [PLAN_PLUGIN_PARTNER_INTERFACE.md](../plans/PLAN_PLUGIN_PARTNER_INTERFACE.md)
- Plugin auth / FFI / rate-limit: [#769](https://github.com/DataBoar/data-boar/issues/769), [#784](https://github.com/DataBoar/data-boar/issues/784), [#785](https://github.com/DataBoar/data-boar/issues/785)
- ENT subscription capability roadmap (separate track): [#643](https://github.com/DataBoar/data-boar/issues/643) / `docs/plans/ENT_CAPABILITY_ROADMAP.md` when merged
- G3 implementation child: [#1624](https://github.com/DataBoar/data-boar/issues/1624)
