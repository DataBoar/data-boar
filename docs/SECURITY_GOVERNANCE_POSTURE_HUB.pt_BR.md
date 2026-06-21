# Postura de segurança, governança, safety, qualidade e proveniência — hub

**English:** [SECURITY_GOVERNANCE_POSTURE_HUB.md](SECURITY_GOVERNANCE_POSTURE_HUB.md)

> **Para agentes:** leia esta página quando precisar do **mapa dos mapas** de postura de segurança, gates de governança, contenção de agentes e evidência de supply chain. **Não** movemos arquivos canônicos — só links co-localizados ([ADR-0057](adr/ADR-0057-lightweight-hub-index-co-located-links.md)). O espelho vault do operador (git privado empilhado em `docs/private/`) pode ter runbooks de lab; este hub fica no **`origin`** público.

## Como usar

1. Escolha um tema abaixo (Cyber, Governança, Safety, Qualidade de código, Proveniência).
2. Siga os caminhos em backticks — não assuma arquivo movido.
3. Para cadeias de integridade/tamper/release, comece em [`docs/ops/INTEGRITY_HUB.md`](ops/INTEGRITY_HUB.md).

## Cyber

| Tema | Pontos de entrada |
| ---- | ----------------- |
| Reporte de vulnerabilidades e versões suportadas | [`SECURITY.md`](../SECURITY.md) · [`SECURITY.pt_BR.md`](../SECURITY.pt_BR.md) |
| Gates de PII (árvore rastreada + histórico) | [ADR-0018](adr/ADR-0018-pii-anti-recurrence-guardrails-for-tracked-files-and-branch-history.md) · [ADR-0019](adr/ADR-0019-pii-seed-gate-staged-files.md) · [ADR-0020](adr/ADR-0020-ci-full-git-history-pii-gate.md) · [ADR-0071](adr/ADR-0071-self-protecting-pii-gate.md) · [`docs/ops/PII_PUBLIC_TREE_OPERATOR_GUIDE.md`](ops/PII_PUBLIC_TREE_OPERATOR_GUIDE.md) |
| Tamper / confiança em runtime | [ADR-0066](adr/ADR-0066-fail-closed-runtime-trust-tamper-posture.md) · [`docs/ops/INTEGRITY_HUB.md`](ops/INTEGRITY_HUB.md) |
| Postura alinhada a NIST | [ADR-0065](adr/ADR-0065-nist-csf-aligned-security-posture-mapping.md) |
| Supply chain (deps, SBOM, pins) | [ADR-0005](adr/ADR-0005-ci-quality-gates-and-supply-chain-scanning.md) · [ADR-0003](adr/ADR-0003-sbom-roadmap-cyclonedx-then-syft.md) · [ADR-0073](adr/ADR-0073-version-scheme-octet-maturity-and-roadmap.md) (Proposed) · ADR de postura supply-chain rastreia **#987** |
| Stack de segurança no host de lab | [`docs/ops/DATA_BOAR_LAB_SECURITY_TOOLING.md`](ops/DATA_BOAR_LAB_SECURITY_TOOLING.md) |
| Host-binding / identidade HTTP de saída | [ADR-0034](adr/ADR-0034-outbound-http-user-agent-data-boar-prospector.md) · `.cursor/rules/homelab-ssh-via-terminal.mdc` (situacional) |

## Governança

| Tema | Pontos de entrada |
| ---- | ----------------- |
| Contrato do agente (não negociáveis) | [`AGENTS.md`](../AGENTS.md) |
| Metadados e formato de ADR | [ADR-0045](adr/ADR-0045-adr-metadata-and-format-standardization.md) |
| Gates de issue / release | [ADR-0061](adr/ADR-0061-u-axis-issue-suborder-and-cross-milestone-gate.md) · [ADR-0072](adr/ADR-0072-commit-gate-vs-release-gate-distinct-criteria.md) (Proposed) |
| Contenção de agentes (A.I.I.D.C.O.B.P.P.) | [ADR-0062](adr/ADR-0062-agent-containment-triple-audit-offband-pingpong.md) · [`docs/adr/ADR-0062-diagram.mermaid`](adr/ADR-0062-diagram.mermaid) · [`docs/ops/lab_lessons_learned/LAB_LESSON_AIIDCOBPP_QUAD_AUDIT.md`](ops/lab_lessons_learned/LAB_LESSON_AIIDCOBPP_QUAD_AUDIT.md) |
| Governança de log de auto-auditoria | [ADR-0037](adr/ADR-0037-data-boar-self-audit-log-governance.md) |
| Taxonomia / eixos de prioridade | [ADR-0048](adr/ADR-0048-orthogonal-priority-axes-h-u-g-p.md) · [ADR-0055](adr/ADR-0055-orthogonal-priority-axes-anti-collision-contract.md) |
| Diagramas de posicionamento em governança | [`docs/ops/governance/DATABOAR_GOVERNANCE_DIAGRAMS.md`](ops/governance/DATABOAR_GOVERNANCE_DIAGRAMS.md) |
| Mapa de políticas Cursor | [`docs/ops/CURSOR_AGENT_POLICY_HUB.md`](ops/CURSOR_AGENT_POLICY_HUB.md) |
| Guardrails de versão / release | [`docs/VERSIONING.md`](VERSIONING.md) · `.cursor/rules/release-versioning.mdc` · `security/version_policy.yaml` |

## Safety

| Tema | Pontos de entrada |
| ---- | ----------------- |
| Gates de segurança e PII (nunca enfraquecer) | `.cursor/rules/never-weaken-security-gates.mdc` · [ADR-0049](adr/ADR-0049-no-brittle-mitigations-robust-input-handling.md) |
| RCA-first / investigação | [ADR-0047](adr/ADR-0047-rca-first-operator-investigation-before-blocking.md) · `.cursor/rules/operator-investigation-before-blocking.mdc` |
| Release com gate do operador (#406) | GitHub **#406** · [ADR-0072](adr/ADR-0072-commit-gate-vs-release-gate-distinct-criteria.md) (Proposed) · reopen automático rastreia **#990** |
| Proteção da estação de dev primária | [`docs/ops/PRIMARY_LINUX_WORKSTATION_PROTECTION.md`](ops/PRIMARY_LINUX_WORKSTATION_PROTECTION.md) · [`docs/ops/PRIMARY_WINDOWS_WORKSTATION_PROTECTION.md`](ops/PRIMARY_WINDOWS_WORKSTATION_PROTECTION.md) |

## Qualidade de código

| Tema | Pontos de entrada |
| ---- | ----------------- |
| Stack de gates no CI | [ADR-0005](adr/ADR-0005-ci-quality-gates-and-supply-chain-scanning.md) · `.github/workflows/ci.yml` |
| Ritual de gate local | [`docs/TESTING.md`](TESTING.md) · `./scripts/check-all.sh` / `.\scripts\check-all.ps1` |
| Análise estática | Bandit · Semgrep · CodeQL (workflows) · Ruff/pre-commit |
| Sem mitigações frágeis | [ADR-0049](adr/ADR-0049-no-brittle-mitigations-robust-input-handling.md) |

## Proveniência

| Tema | Pontos de entrada |
| ---- | ----------------- |
| Inventário cripto de ADRs | [ADR-0056](adr/ADR-0056-adr-inventory-ed25519-attestation-workflow.md) · `scripts/inv-adr.ps1` · [`docs/adr/INVENTORY.txt`](adr/INVENTORY.txt) |
| Roadmap Sigstore / cosign | [`docs/ops/RELEASE_INTEGRITY.md`](ops/RELEASE_INTEGRITY.md) · `docs/plans/PLAN_BUILD_IDENTITY_RELEASE_INTEGRITY.md` (interno) |
| SBOM | [ADR-0003](adr/ADR-0003-sbom-roadmap-cyclonedx-then-syft.md) · [`SECURITY.md`](../SECURITY.md) § SBOM |
| Closure de dependências | [ADR-0030](adr/ADR-0030-python-dependency-update-closure-single-pass.md) · [ADR-0044](adr/ADR-0044-dependabot-uv-ecosystem-for-pyproject-lock-closure.md) |

## Vault ↔ repo

| Superfície | Papel |
| ---------- | ----- |
| **Repo público** | Política, ADRs, guards de CI, runbooks sem segredos |
| **Git privado empilhado (`docs/private/`)** | Hostnames de lab, manifests, narrativas de completão, evidência comercial/legal — nunca colar em arquivos rastreados |
| **Espelho vault do operador** | Cópia opcional no lado Claude; **este** arquivo é o índice público canônico |

## Hubs relacionados

- [`docs/hubs/INDEX.md`](hubs/INDEX.md)
- [`docs/ops/INTEGRITY_HUB.md`](ops/INTEGRITY_HUB.md)
- [`docs/ops/LAB_LESSONS_LEARNED.md`](ops/LAB_LESSONS_LEARNED.md)

## Ritual de atualização

1. Adicione linhas aqui (EN + espelho pt-BR) quando um ADR ou guard de postura entrar.
2. Registre este hub em [`docs/hubs/INDEX.md`](hubs/INDEX.md).
3. Rode `./scripts/check-hubs.sh` antes do merge.

Refs: GitHub **#992**, **#991**, **#987**, saga de versionamento pós-**#970**.
