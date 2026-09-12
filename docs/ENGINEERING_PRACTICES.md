# Engineering practices

**Português (Brasil):** [ENGINEERING_PRACTICES.pt_BR.md](ENGINEERING_PRACTICES.pt_BR.md)

This page states **engineering doctrine** for the Data Boar repository: the default behaviours we enforce in code, CI, and operator workflow. It is **not** marketing copy and **not** a substitute for the linked artefacts below — each principle points to the file or config that implements it.

These four principles also appear on the public site page [Engineering Practices](https://databoar.com.br/praticas-de-engenharia.html) (DataBoar/data-boar-site#89). **This file is the canonical in-repo source**; the site summarises the same links for visitors.

---

## 1. Fail-closed by default

When a **security or hygiene condition cannot be verified**, the operation **denies** rather than proceeding with partial or assumed trust.

### Repository discipline

- **Staged and tracked-tree gates** block commits that match private operator seeds or forbidden PII patterns before they reach shared history — see the guardrail stack documented in [SECURITY.md](SECURITY.md) (Incident Response Philosophy): `scripts/gatekeeper_audit.py`, `tests/test_pii_guard.py`, `.pre-commit-config.yaml`, and `scripts/pii_history_guard.py`.
- **Local gate before push:** contributors run `./scripts/check-all.sh` / `.\scripts\check-all.ps1` (tiered mirror of CI quality and security scans) so unverifiable or failing checks stop the change **locally** instead of after a remote CI round-trip — ritual detail in [QUALITY_WORKFLOW_RECOMMENDATIONS.md](QUALITY_WORKFLOW_RECOMMENDATIONS.md) and merge policy in root [SECURITY.md](../SECURITY.md) (dependency closure: full gate before merge).
- **Runtime posture (product):** optional API key when `api.require_api_key` is enabled; strict `session_id` validation; log export blocked when a PII self-scan fails (HTTP 422) — same [SECURITY.md](SECURITY.md) tables. Enforced licensing marks modified installs **TAMPERED** when digest or manifest checks fail ([RELEASE_INTEGRITY.md](RELEASE_INTEGRITY.md), [ADR-0066](adr/ADR-0066-fail-closed-runtime-trust-tamper-posture.md)).

**Posture map:** [SECURITY_GOVERNANCE_POSTURE_HUB.md](SECURITY_GOVERNANCE_POSTURE_HUB.md) ([pt-BR](SECURITY_GOVERNANCE_POSTURE_HUB.pt_BR.md)).

---

## 2. Pin + cooldown

**Supply-chain inputs are pinned to exact versions or digests**, and **new upstream releases wait in quarantine** before Dependabot opens an update PR.

### Where it lives

- **Python:** `uv.lock` is the canonical pin (resolved from `pyproject.toml`); Dependabot `package-ecosystem: uv` keeps lock and manifest aligned — see header comments in [`.github/dependabot.yml`](../.github/dependabot.yml) and [ADR-0044](adr/ADR-0044-dependabot-uv-ecosystem-for-pyproject-lock-closure.md).
- **GitHub Actions:** workflow steps reference **commit SHAs**; Dependabot `github-actions` ecosystem refreshes those pins on a schedule.
- **Container base:** Dockerfile image digests are maintained via Dependabot `docker` ecosystem ([ADR-0074](adr/ADR-0074-supply-chain-layer1-digest-pins-and-rust-sca.md)).
- **Cooldown:** all three ecosystems above set **`cooldown: default-days: 7`** in [`.github/dependabot.yml`](../.github/dependabot.yml) — a seven-day quarantine window before a newly published version is proposed.

**Broader supply-chain evidence:** SBOM generation and CI gate stack — [ADR-0005](adr/ADR-0005-ci-quality-gates-and-supply-chain-scanning.md), [RELEASE_INTEGRITY.md](RELEASE_INTEGRITY.md) (SBOM section).

---

## 3. Integrity verified, not assumed

**Artefacts are hash- or manifest-checked before trust** — in deployment (runtime licensing guard) and in release engineering (build reproducibility).

### Mechanisms

- **Embedded build digest:** deterministic SHA-256 over sorted critical source files; mismatch under `licensing.mode: enforced` → **TAMPERED**. Generator: [`scripts/generate_build_digest.py`](../scripts/generate_build_digest.py). Operator env: `DATA_BOAR_EXPECTED_BUILD_DIGEST`.
- **Signed file manifest (optional):** per-path SHA-256 JSON from [`scripts/generate_release_manifest.py`](../scripts/generate_release_manifest.py); verified at startup when configured (`DATA_BOAR_RELEASE_MANIFEST_PATH` / `licensing.manifest_path`).
- **Release attachments:** `build-digest.txt` and `release-manifest.json` on GitHub Releases; SBOM CycloneDX artefacts from the SBOM workflow.

Full specification: **[RELEASE_INTEGRITY.md](RELEASE_INTEGRITY.md)** ([pt-BR](RELEASE_INTEGRITY.pt_BR.md)). Navigation hub: [ops/INTEGRITY_HUB.md](ops/INTEGRITY_HUB.md) ([pt-BR](ops/INTEGRITY_HUB.pt_BR.md)).

---

## 4. Metadata first

**Discovery reports what, where, and shape — not bulk exfiltration of raw content** — unless an operator explicitly configures bounded sampling for detection.

### Definition

The glossary term **Data Sniffing** names the engine’s discovery and sampling pass: connectors discover structure, read **bounded** excerpts, and run sensitivity detection — **metadata-only findings, no exfiltration** ([GLOSSARY.md](GLOSSARY.md), table row *Data Sniffing*).

### Product alignment

- Findings and reports are **inventory-oriented** evidence for CISO/DPO workflows — not legal conclusions ([COMPLIANCE_FRAMEWORKS.md](COMPLIANCE_FRAMEWORKS.md), [ADR-0025](adr/ADR-0025-compliance-positioning-evidence-inventory-not-legal-conclusion-engine.md)).
- Jurisdiction hints and compliance samples follow the same **metadata-only, heuristic** boundary ([ADR-0026](adr/ADR-0026-optional-jurisdiction-hints-dpo-facing-heuristic-metadata-only.md)).
- Philosophy summary: [philosophy/THE_WHY.md](philosophy/THE_WHY.md) ([pt-BR](philosophy/THE_WHY.pt_BR.md)).

---

## Related documentation

- [README.md](README.md) ([pt-BR](README.pt_BR.md)) — documentation index.
- [MAP.md](MAP.md) ([pt-BR](MAP.pt_BR.md)) — concern-first navigation.
- [SECURITY.md](SECURITY.md) ([pt-BR](SECURITY.pt_BR.md)) — application security fixes, tests, and technician guidance.
- [SECURITY_GOVERNANCE_POSTURE_HUB.md](SECURITY_GOVERNANCE_POSTURE_HUB.md) ([pt-BR](SECURITY_GOVERNANCE_POSTURE_HUB.pt_BR.md)) — map of security, governance, and provenance entry points.
