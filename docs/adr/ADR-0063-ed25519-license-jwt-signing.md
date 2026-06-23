# ADR 0063 — ed25519 (EdDSA) for license JWT signing

- **Date (UTC):** 2026-06-21
- **Authors:** Fabio Leitao
- **Deciders:** Fabio Leitao

## Status

Proposed

### Status history

- 2026-06-21 — Proposed (materializes GitHub #708; enriched per #993)

## Context

Commercial tiers ([ADR 0027](ADR-0027-commercial-tier-boundaries-licensing-docs-and-future-jwt-claims.md))
document illustrative JWT claims; runtime signing needs a **single, reviewable** algorithm
choice before further keys are generated or rotated.

The operator selected **ed25519 (EdDSA)** in session 2026-05-24 with a v1 key pair
distributed to **operator-controlled** backup destinations (never committed to `origin`).
Enforcement architecture is [ADR 0064](ADR-0064-license-enforcement-additive-model.md).

### Lab and key-hygiene findings (2026-06, genericized)

Homelab inventory and completão evidence surfaced **related but distinct** risks:

| Finding class | Implication for this ADR |
| --- | --- |
| **License signing material on shared lab nodes** | PKCS#8 / PEM paths under operator home directories must stay **out of repo** and off shared lab images; rotation and backup policy live in operator vault + [ADR 0056](ADR-0056-cryptographic-adr-inventory-inv-adr-ssh-attestation.md) inventory discipline. |
| **Universal ed25519 SSH host/user keys without passphrase** | Same **algorithm family** as license signing but **different purpose** — SSH lateral movement risk is operational hygiene, not a reason to change JWT algorithm; passphrase policy and per-host keys are tracked in operator private runbooks. |
| **Provenance / supply-chain posture** | Holistic signing-key lifecycle (generation, backup count, rotation triggers) will be extended in **ADR-0074** (Proposed, GitHub #987) — this ADR owns **algorithm + JWT role** only. |

**Public tree rule:** No private key paths, fingerprints, or host-specific key filenames in
tracked ADRs — placeholders only.

## Decision

1. **Algorithm:** **ed25519 (EdDSA)** per FIPS 186-5 (2023) and RFC 8032 for license JWT
   signatures; JWK representation per RFC 8037 when needed.
2. **Asymmetric model:** **Private key** — operator-only storage; **public key** — sole
   verification artifact eligible for the public repo (`core/licensing/license-pub-vN.pem`).
3. **Distribution format:** PKCS#8 PEM for Go/Python interoperability; OpenSSH format
   acceptable for operator backups only.
4. **Rotation:** New key version → new public file (`license-pub-v2.pem`, …); legacy JWTs
   remain valid until natural expiry unless revocation ships ([ADR 0064](ADR-0064-license-enforcement-additive-model.md) / GitHub #717).
5. **Post-quantum watch:** When organizational policy mandates PQC (FIPS 204/205), plan a
   **new ADR** for algorithm migration — ed25519 is acceptable for v1.x–v2.x horizon.

## Rationale

| Criterion | ed25519 | RS256 | ES256 (P-256) | HS256 |
| --- | --- | --- | --- | --- |
| Key size / ops | 32-byte keys; deterministic signatures | Large RSA keys; slower verify | NIST curve; PRNG sensitivity in signing | Symmetric — secret on verifier |
| Open-core fit | Public verify, private issue | OK | OK | **Unacceptable** — verifier is public |
| Go / Python | `crypto/ed25519`, `cryptography` + PyJWT EdDSA | Mature | More edge cases | Simple but wrong trust model |

## Consequences

- **Positive:** One clear algorithm for `LicenseGuard` and issuer tooling; aligns with
  [ADR 0056](ADR-0056-cryptographic-adr-inventory-inv-adr-ssh-attestation.md) ed25519 inventory attestation.
- **Negative:** Rotation and backup discipline are operator-critical; lab exposure class
  must be remediated in private ops, not by weakening signing choice.
- **Watch:** ADR-0074 supply-chain ADR may add mandatory rotation cadence and backup
  verification steps.

## Alternatives Considered

See rationale table — RS256, ES256, and HS256 rejected for the reasons above.

## Related Decisions

- [ADR 0027 — Commercial tier boundaries and JWT claims](ADR-0027-commercial-tier-boundaries-licensing-docs-and-future-jwt-claims.md)
- [ADR 0056 — Cryptographic ADR inventory](ADR-0056-cryptographic-adr-inventory-inv-adr-ssh-attestation.md)
- [ADR 0064 — License enforcement additive model](ADR-0064-license-enforcement-additive-model.md)
- ADR-0074 (Proposed, #987) — supply-chain and signing-key provenance (not yet materialized)

## References

- FIPS 186-5 (2023) — EdDSA
- [RFC 8032 — Edwards-Curve Digital Signature Algorithm (EdDSA)](https://www.rfc-editor.org/rfc/rfc8032)
- [RFC 8037 — CFRG Elliptic Curve ECDH and EdDSA Algorithms for JOSE](https://www.rfc-editor.org/rfc/rfc8037)
- GitHub #708 — source issue
