# Primer: Supply chain security signals in this repository

**Português (Brasil):** [SUPPLY_CHAIN_SECURITY_PRIMER.pt_BR.md](SUPPLY_CHAIN_SECURITY_PRIMER.pt_BR.md)

Maps common **supply-chain** practices to files and workflows you can verify in `data-boar`. Not a substitute for your organisation’s SSDF program.

---

## 1. Practice → evidence

| Practice | Where to look |
| -------- | ------------- |
| **SBOM generation** | `.github/workflows/sbom.yml`; `scripts/generate-sbom.sh` (see [ADR-0003](../adr/ADR-0003-sbom-roadmap-cyclonedx-then-syft.md)) |
| **Dependency updates** | `.github/dependabot.yml`; `uv.lock` / `requirements.txt` / `pylock.toml`; [DEPENDABOT_REQUIREMENTS_SYNC.md](../ops/DEPENDABOT_REQUIREMENTS_SYNC.md) |
| **Vulnerability scan (OSV)** | `scripts/run-osv-scanner.sh`; enforced tier in `scripts/check-all-security-scans.sh` |
| **Secret scanning** | `security/gitleaks.toml`; `.github/workflows/gitleaks.yml`; `scripts/run-gitleaks-strict.sh` |
| **Workflow pinning** | Action SHAs in `.github/workflows/` (see [ADR-0005](../adr/ADR-0005-ci-github-actions-supply-chain-pins.md); `tests/test_github_workflows.py`) |
| **Signed commits** | `CONTRIBUTING.md`; ruleset `required_signatures`; Dependabot sync uses allowed signers in `scripts/ci_dependabot_requirements_sync.sh` |
| **Gate file tripwire** | `scripts/gate_change_tripwire.py` at start of `check-all.sh`; `.github/CODEOWNERS` |
| **OpenSSF Scorecard** | `.github/workflows/scorecard.yml`; posture in [BUILD_PROVENANCE_POSTURE.md](../ops/BUILD_PROVENANCE_POSTURE.md) / [ADR-0092](../adr/ADR-0092-build-provenance-scorecard-and-github-release-attestations.md) |
| **Release attestations** | `sbom.yml` build provenance on version tags (same ADR) |

---

## 2. What is not claimed

- No guarantee every dependency is free of CVEs — scanners reduce risk; operators still triage alerts.
- No container image signing doc duplicated here — follow [DOCKER_IMAGE_RELEASE_ORDER.md](../ops/DOCKER_IMAGE_RELEASE_ORDER.md) for release order.
- Private lab mirrors and offline artifact vaults are **out of scope** for this public primer.

---

## 3. Where to go next

| Need | Doc |
| ---- | --- |
| Local full gate | `./scripts/check-all.sh` ([ADR-0080](../adr/ADR-0080-local-validation-gate-inviolable.md)) |
| Branch / merge rules | [BRANCH_PROTECTION.md](../ops/BRANCH_PROTECTION.md) |
| DevSecOps deploy angle | [IAC_AND_DEVSECOPS_PRIMER.md](IAC_AND_DEVSECOPS_PRIMER.md) |
