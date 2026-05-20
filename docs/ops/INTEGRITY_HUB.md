<!-- plans-hub-summary: Hub de navegação para todas as camadas de tamper detection e integridade do produto -->

# Integrity and tamper detection — navigation hub

**Português (Brasil):** [INTEGRITY_HUB.pt_BR.md](INTEGRITY_HUB.pt_BR.md)

> **For agents (Claude / Cursor):**
>
> - Before implementing any integrity logic: check whether it already exists in this hub.
> - Before creating a new integrity ADR: read [ADR-0037](../adr/ADR-0037-data-boar-self-audit-log-governance.md), [ADR-0039](../adr/ADR-0039-retention-evidence-posture-bonded-customs-adjacent-contexts.md), and [ADR-0051](../adr/ADR-0051-incremental-filesystem-scan-file-identity-fingerprint.md).
> - On runtime hash verification failure: follow [INTEGRITY_CHECK_ALPHA_LOGIC.md](INTEGRITY_CHECK_ALPHA_LOGIC.md) and `core/runtime_trust.py` — prefer **Safe-Hold** / degraded mode; do not silently patch around failed checks.
> - `scripts/inv-adr.ps1` covers **`docs/adr/`** only; `scripts/evidence-hash-manifest.ps1` covers **gitignored** legal evidence under `docs/private/`.

> **Agent/Cursor:** read this page first. It maps **where** each piece lives. Do not rewrite integrity logic without checking what already exists here.

## Chain of trust

Source → Build → Deploy → Runtime → Docs/ADR

| Stage | Entry points |
| ----- | -------------- |
| Source | Git tags, signed commits (operator policy) |
| Build | [PLAN_BUILD_IDENTITY_RELEASE_INTEGRITY.md](../plans/PLAN_BUILD_IDENTITY_RELEASE_INTEGRITY.md), deterministic Rust evidence in [RELEASE_INTEGRITY.md](RELEASE_INTEGRITY.md) |
| Deploy | [docs/RELEASE_INTEGRITY.md](../RELEASE_INTEGRITY.md) (licensing digest + optional manifest), [release-integrity-check.ps1](../../scripts/release-integrity-check.ps1) |
| Runtime | `core/runtime_trust.py`, [INTEGRITY_CHECK_ALPHA_LOGIC.md](INTEGRITY_CHECK_ALPHA_LOGIC.md) |
| Docs/ADR | `scripts/inv-adr.ps1`, [docs/adr/INVENTORY.txt](../adr/INVENTORY.txt) |

## Quick index by layer

### 1. Product runtime (Python)

| Module / doc | Role |
| ------------ | ---- |
| [`core/runtime_trust.py`](../../core/runtime_trust.py) | Tinted state, degraded mode when trust checks fail |
| [`core/licensing/integrity.py`](../../core/licensing/integrity.py) | License tier / manifest verification |
| [`core/maturity_assessment/integrity.py`](../../core/maturity_assessment/integrity.py) | Maturity assessment seal (`DATA_BOAR_MATURITY_INTEGRITY_SECRET`) |
| [INTEGRITY_CHECK_ALPHA_LOGIC.md](INTEGRITY_CHECK_ALPHA_LOGIC.md) | Design spec for optional startup hash checks (alpha) |

### 2. Release artifacts

| Doc / script | Role |
| ------------ | ---- |
| [docs/RELEASE_INTEGRITY.md](../RELEASE_INTEGRITY.md) | **Public product doc** — optional tamper-evidence for **licensing** (build digest, signed file manifest, SBOM pointers) |
| [RELEASE_INTEGRITY.md](RELEASE_INTEGRITY.md) | **Ops release specification** — Rust build evidence, SRE throttling, GRC taxonomy, release checklist |
| [PLAN_BUILD_IDENTITY_RELEASE_INTEGRITY.md](../plans/PLAN_BUILD_IDENTITY_RELEASE_INTEGRITY.md) | Roadmap for build identity and stronger release integrity |
| [release-integrity-check.ps1](../../scripts/release-integrity-check.ps1) | Post-release verification script |
| [example-release-manifest.json](../../scripts/example-release-manifest.json) | Example signed-manifest schema |

### 3. Evidence (private tree — legal / operator hashes)

| Script | Role |
| ------ | ---- |
| [evidence-hash-manifest.ps1](../../scripts/evidence-hash-manifest.ps1) | SHA-256 / SHA-512 manifest for files under `docs/private/` (GPG detached sign is operator-side) |

### 4. Docs and ADR integrity

| Artifact | Role |
| -------- | ---- |
| [inv-adr.ps1](../../scripts/inv-adr.ps1) | ADR inventory with per-file SHA-256 and attested `InventoryHash` |
| [docs/adr/INVENTORY.txt](../adr/INVENTORY.txt) | Generated manifest — verify offline after `inv-adr.ps1` |
| `docs/adr/INVENTORY.txt.sig` | Detached SSH ed25519 signature (operator workflow; optional until signed) |

### 5. Related ADRs

| ADR | Scope |
| --- | ----- |
| [ADR-0037](../adr/ADR-0037-data-boar-self-audit-log-governance.md) | Self-audit log governance (what the auditor logs today vs gaps) |
| [ADR-0039](../adr/ADR-0039-retention-evidence-posture-bonded-customs-adjacent-contexts.md) | Retention and evidence posture in complex regulated contexts |
| [ADR-0051](../adr/ADR-0051-incremental-filesystem-scan-file-identity-fingerprint.md) | File identity fingerprint for incremental scans (not cryptographic tamper-evidence) |

## When to trigger Safe-Hold

- **Runtime:** If configured integrity checks fail at startup or during guarded paths, `core/runtime_trust.py` may enter a **tinted** / degraded state — treat output as **not** full-trust compliance evidence until the operator restores known-good bits or disables the check deliberately per runbook.
- **ADR inventory:** If `INVENTORY.txt` does not match a verified signature or regenerated hash from `inv-adr.ps1`, **do not commit** ADR changes without re-running the inventory script and reconciling with the maintainer.

## `docs/RELEASE_INTEGRITY.md` vs `docs/ops/RELEASE_INTEGRITY.md` (resolved)

These files share a basename but are **intentionally different** — not a stale duplicate.

| File | Audience | Content |
| ---- | -------- | ------- |
| [docs/RELEASE_INTEGRITY.md](../RELEASE_INTEGRITY.md) | Product / integrators | **Licensing** tamper-evidence: `_build_digest.txt`, `DATA_BOAR_EXPECTED_BUILD_DIGEST`, optional signed manifest JSON, SBOM workflow links |
| [docs/ops/RELEASE_INTEGRITY.md](RELEASE_INTEGRITY.md) | Operators / SRE | **Release engineering** spec: deterministic Rust builds, hash discipline, throttling/resume, GRC weights, release checklist |

Cross-links exist in both documents and in [INTEGRITY_CHECK_ALPHA_LOGIC.md](INTEGRITY_CHECK_ALPHA_LOGIC.md). Start here when unsure which file applies.

## Related navigation

- [hubs/INDEX.md](../hubs/INDEX.md) — map of all hubs
- [SECURITY.md](../../SECURITY.md) — vulnerability reporting and supply-chain artifacts
- [CODE_PROTECTION_OPERATOR_PLAYBOOK.md](../CODE_PROTECTION_OPERATOR_PLAYBOOK.md) — operator hardening (Priority band A)
