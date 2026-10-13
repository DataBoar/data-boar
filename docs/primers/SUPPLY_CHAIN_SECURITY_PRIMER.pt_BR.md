# Primer: Sinais de segurança de supply chain neste repositório

**English:** [SUPPLY_CHAIN_SECURITY_PRIMER.md](SUPPLY_CHAIN_SECURITY_PRIMER.md)

Mapeia práticas comuns de **supply chain** para arquivos e workflows verificáveis no `data-boar`. Não substitui o programa SSDF da sua organização.

---

## 1. Prática → evidência

| Prática | Onde olhar |
| ------- | ---------- |
| **Geração de SBOM** | `.github/workflows/sbom.yml`; `scripts/generate-sbom.sh` ([ADR-0003](../adr/ADR-0003-sbom-roadmap-cyclonedx-then-syft.md)) |
| **Atualização de dependências** | `.github/dependabot.yml`; `uv.lock` / `requirements.txt` / `pylock.toml`; [DEPENDABOT_REQUIREMENTS_SYNC.pt_BR.md](../ops/DEPENDABOT_REQUIREMENTS_SYNC.pt_BR.md) |
| **Scan de vulnerabilidade (OSV)** | `scripts/run-osv-scanner.sh`; tier enforced em `scripts/check-all-security-scans.sh` |
| **Varredura de segredos** | `security/gitleaks.toml`; `.github/workflows/gitleaks.yml`; `scripts/run-gitleaks-strict.sh` |
| **Pin de workflows** | SHAs em `.github/workflows/` ([ADR-0005](../adr/ADR-0005-ci-github-actions-supply-chain-pins.md); `tests/test_github_workflows.py`) |
| **Commits assinados** | `CONTRIBUTING.md`; ruleset `required_signatures`; sync Dependabot em `scripts/ci_dependabot_requirements_sync.sh` |
| **Tripwire de gates** | `scripts/gate_change_tripwire.py` no início de `check-all.sh`; `.github/CODEOWNERS` |
| **OpenSSF Scorecard** | `.github/workflows/scorecard.yml`; [BUILD_PROVENANCE_POSTURE.pt_BR.md](../ops/BUILD_PROVENANCE_POSTURE.pt_BR.md) / [ADR-0092](../adr/ADR-0092-build-provenance-scorecard-and-github-release-attestations.md) |
| **Atestações de release** | provenance de build em tags no `sbom.yml` (mesmo ADR) |

---

## 2. O que não afirmamos

- Não há garantia de zero CVE — scanners reduzem risco; o operador ainda faz triagem.
- Assinatura de imagem container segue [DOCKER_IMAGE_RELEASE_ORDER.pt_BR.md](../ops/DOCKER_IMAGE_RELEASE_ORDER.pt_BR.md).
- Espelhos de lab privados ficam **fora** deste primer público.

---

## 3. Onde ir depois

| Necessidade | Doc |
| ----------- | --- |
| Gate local completo | `./scripts/check-all.sh` ([ADR-0080](../adr/ADR-0080-local-validation-gate-inviolable.md)) |
| Regras de branch/merge | [BRANCH_PROTECTION.pt_BR.md](../ops/BRANCH_PROTECTION.pt_BR.md) |
| Ângulo DevSecOps de deploy | [IAC_AND_DEVSECOPS_PRIMER.pt_BR.md](IAC_AND_DEVSECOPS_PRIMER.pt_BR.md) |
