# Architecture Decision Records (ADR)

**English:** [README.md](README.md)

Notas curtas e duradouras que registram **por que** o projeto escolheu um caminho — não só *o que* o código faz. Complementam o **índice da documentação** ([README.pt_BR.md](../README.pt_BR.md) — *Interno e referência* aponta a árvore de planos) para contexto de backlog, e [TESTING.pt_BR.md](../TESTING.pt_BR.md) (o que a CI exige).

## Convenção

| Item          | Regra                                                                                                                                                                         |
| ------------- | ------------------------------------------------------------------------------------------------------------------------------------------                                    |
| **Local**     | Esta pasta: **`docs/adr/`**                                                                                                                                                   |
| **Nome**      | **`ADR-0000-...`** opcional (baseline / meta); **`ADR-0001-titulo-kebab-curto.md`**, **`ADR-0002-...`** para decisões substantivas — incrementar a cada ADR; título estável após o merge. |
| **Idioma**    | **Arquivos numerados (`ADR-0000-*.md`, `ADR-0001-*.md`, …) ficam só em inglês** (texto canônico, como os planos em `docs/plans/`). Este README tem pt-BR.                             |
| **Formato**   | Preferir seções: **Context**, **Decision**, **Consequences**, **References** (estilo MADR serve). Manter em uma ou duas telas.                                                |
| **Quando**    | Comportamento relevante à segurança, trade-offs de docs/ferramenta que voltam a incomodar contribuidores, ou o que não queremos “apagar” sem registro.                        |

## Índice

Os títulos na tabela abaixo ficam em **inglês** (canônicos, iguais ao [README.md](README.md)); o status usa rótulos em pt-BR (**Aceito** / **Proposto** / **Deferido** / **Reservado**). A CI exige a mesma cobertura de arquivos ADR numerados no índice EN e neste índice pt-BR.

| ADR  | Título                                                                                                                         | Status   |
| ---- | ------------------------------------------------------------------------------------------------------------------------------ | -------- |
| 0000  | [Project origin, ADR baseline, and UMADR ecosystem regency](ADR-0000-project-origin-and-adr-baseline.md) (canonical mother; #994) | Aceito |
| 0001  | [Markdown fix script, MD029, and semantic step lists](ADR-0001-markdown-fix-script-md029-and-semantic-step-lists.md) | Aceito |
| 0002  | [Operator-facing security and technical docs](ADR-0002-operator-facing-security-and-technical-docs.md) | Aceito |
| 0003  | [SBOM roadmap — CycloneDX then Syft](ADR-0003-sbom-roadmap-cyclonedx-then-syft.md) | Aceito |
| 0004  | [Information architecture — external-tier docs must not link into `plans/`](ADR-0004-external-docs-no-markdown-links-to-plans.md) | Aceito |
| 0005  | [CI and GitHub Actions supply chain — pinned SHAs and pinned uv CLI](ADR-0005-ci-github-actions-supply-chain-pins.md) | Aceito |
| 0006  | [Operator today-mode layout and published-release sync](ADR-0006-operator-today-mode-layout-and-published-sync.md) | Aceito |
| 0007  | [Synthetic data corpus as mandatory pre-requisite before real production data](ADR-0007-synthetic-data-corpus-before-real-data.md) | Aceito |
| 0008  | [Docker CE (official repo) + Compose plugin + Swarm as primary lab container runtime](ADR-0008-docker-ce-swarm-over-docker-io-and-podman-only.md) | Aceito |
| 0009  | [Ansible idempotent roles as single automation source for LAB-NODE-01 lab baseline](ADR-0009-ansible-idempotent-roles-as-single-automation-source.md) | Aceito |
| 0010  | [IP Declaration as prior-art protection for Data Boar at CLT employment](ADR-0010-ip-declaration-prior-art-protection-at-employment.md) | Aceito |
| 0011  | [Layered observability stack for lab-op (Munin + Wazuh + Prometheus + Monit + rsyslog/GELF)](ADR-0011-lab-op-observability-stack-layered.md) | Aceito |
| 0012  | [OCR and image-based sensitive data detection (Tesseract primary, EasyOCR opt-in, BLOB/base64)](ADR-0012-ocr-image-sensitive-data-detection.md) | Proposto |
| 0013  | [Browser artifact scanning — SQLite (default) + LevelDB (opt-in) strategy](ADR-0013-browser-artifact-sqlite-leveldb-scan-strategy.md) | Aceito |
| 0014  | [Rename repository and package from python3-lgpd-crawler to data-boar](ADR-0014-rename-repo-and-package-python3-lgpd-crawler-to-data-boar.md) | Aceito |
| 0015  | [PoC test infrastructure with synthetic corpus and API testing](ADR-0015-poc-test-infrastructure-synthetic-corpus-and-api-testing.md) | Aceito |
| 0016  | [OpenTofu corporate IaC path alongside existing Ansible operations](ADR-0016-opentofu-corporate-iac-path-alongside-ansible.md) | Aceito |
| 0017  | [Quasi-identification risk/confidence contract and LGPD guardrails](ADR-0017-quasi-identification-risk-confidence-contract-and-lgpd-guardrails.md) | Aceito |
| 0018  | [PII anti-recurrence guardrails for tracked files and branch history](ADR-0018-pii-anti-recurrence-guardrails-for-tracked-files-and-branch-history.md) | Aceito |
| 0019  | [PII verification cadence and manual review gate](ADR-0019-pii-verification-cadence-and-manual-review-gate.md) | Aceito |
| 0020  | [CI must scan full Git history for PII anti-recurrence patterns](ADR-0020-ci-full-git-history-pii-gate.md) | Aceito |
| 0021  | [Public web presence — DNS alias (CNAME), canonical host, TLS, hosting shape](ADR-0021-public-web-presence-dns-alias-and-hosting.md) | Aceito |
| 0022  | [Public glossary — compliance laws, roles, and platform terms](ADR-0022-public-glossary-compliance-and-platform-terms.md) | Aceito |
| 0023  | [Windows primary dev PC filename search — Everything (`es.exe`) first, capped PowerShell fallback](ADR-0023-windows-primary-dev-filename-search-everything-es-first-with-fallback.md) | Aceito |
| 0024  | [Enterprise discovery — three complementary tracks (planning posture)](ADR-0024-enterprise-discovery-three-complementary-tracks.md) | Aceito |
| 0025  | [Compliance positioning — evidence and inventory, not a legal-conclusion engine](ADR-0025-compliance-positioning-evidence-inventory-not-legal-conclusion-engine.md) | Aceito |
| 0026  | [Optional jurisdiction hints — DPO-facing, heuristic, metadata-only](ADR-0026-optional-jurisdiction-hints-dpo-facing-heuristic-metadata-only.md) | Aceito |
| 0027  | [Commercial tier boundaries — licensing docs and future JWT claims](ADR-0027-commercial-tier-boundaries-licensing-docs-and-future-jwt-claims.md) | Aceito |
| 0028  | [Lab external connectivity evaluation playbook (tracked)](ADR-0028-lab-external-connectivity-eval-playbook.md) | Aceito |
| 0029  | [Cursor Markdown preview guardrail + lab-smoke Ansible hook](ADR-0029-cursor-markdown-preview-guardrail-and-lab-smoke-ansible-hook.md) | Aceito |
| 0030  | [Python dependency update closure (single pass)](ADR-0030-python-dependency-update-closure-single-pass.md) | Aceito |
| 0031  | [PyPI packaging with Hatchling (flat layout)](ADR-0031-pypi-packaging-hatchling-flat-layout.md) | Aceito |
| 0032  | [Maturity self-assessment — per-batch history on dashboard HTML](ADR-0032-maturity-assessment-batch-history-sqlite.md) | Aceito |
| 0033  | [WebAuthn open Relying Party — JSON endpoints (Phase 1)](ADR-0033-webauthn-open-relying-party-json-endpoints.md) | Aceito |
| 0034  | [Outbound HTTP User-Agent — `DataBoar-Prospector/<version>`](ADR-0034-outbound-http-user-agent-data-boar-prospector.md) | Aceito |
| 0035  | [README stakeholder pitch vs optional deck vocabulary](ADR-0035-readme-stakeholder-pitch-vs-deck-vocabulary.md) | Aceito |
| 0036  | [Exception and log PII redaction pipeline](ADR-0036-exception-and-log-pii-redaction-pipeline.md) | Aceito |
| 0037  | [Data Boar self-audit log and governance of the auditor](ADR-0037-data-boar-self-audit-log-governance.md) | Aceito |
| 0038  | [Jurisdictional ambiguity — alert and inventory, do not decide law](ADR-0038-jurisdictional-ambiguity-alert-dont-decide.md) | Aceito |
| 0039  | [Retention and evidence posture in bonded / customs-adjacent contexts](ADR-0039-retention-evidence-posture-bonded-customs-adjacent-contexts.md) | Aceito |
| 0040  | [Assistant default: private stack evidence mirrors without rhetorical asks](ADR-0040-assistant-private-stack-evidence-mirrors-default.md) | Aceito |
| 0041  | [Lab completão optional data contract preflight before host smoke](ADR-0041-lab-completao-data-contract-preflight.md) | Aceito |
| 0042  | [Public LAB lessons archive + hub (dated snapshots)](ADR-0042-lab-lessons-learned-archive-contract.md) | Aceito |
| 0043  | [SQL column sampling — non-null filter and strategy hook](ADR-0043-sql-column-sampling-non-null-and-strategy-hook.md) | Aceito |
| 0044  | [Dependabot uv ecosystem for pyproject + lock closure](ADR-0044-dependabot-uv-ecosystem-for-pyproject-lock-closure.md) | Aceito |
| 0045  | [ADR metadata and format standardization](ADR-0045-adr-metadata-and-format-standardization.md) | Aceito |
| 0046  | [Operator intent and blameless collaboration posture](ADR-0046-operator-intent-and-blameless-collaboration.md) | Aceito |
| 0047  | [RCA-first defect investigation and fix discipline](ADR-0047-rca-first-defect-investigation-and-fix-discipline.md) | Aceito |
| 0048  | [Operator-facing taxonomy and naming contract preservation](ADR-0048-operator-facing-taxonomy-and-naming-contract-preservation.md) | Aceito |
| 0049  | [No brittle mitigations — robust input handling over symptom suppression](ADR-0049-no-brittle-mitigations-robust-input-handling.md) | Aceito |
| 0050  | [Plan document metadata standard](ADR-0050-plan-document-metadata-standard.md) | Aceito |
| 0051  | [Incremental filesystem scan: file-identity fingerprint contract](ADR-0051-incremental-filesystem-scan-file-identity-fingerprint.md) | Aceito |
| 0052  | [YAML plugin system: centralized schema and unified plugin file](ADR-0052-yaml-plugin-system-centralized-schema.md) | Aceito |
| 0053  | [`ebcdic` direct upper-bound pin and Dependabot ignore for blocked semver-major](ADR-0053-ebcdic-direct-upper-bound-and-dependabot-ignore.md) | Aceito |
| 0054  | [Decline `chardet` semver-major bumps while `cyclonedx-bom` pins `chardet<6.0`](ADR-0054-chardet-pinned-by-cyclonedx-bom.md) | Aceito |
| 0055  | [Orthogonal priority axes (H/U/A/P/G/S/M) anti-collision contract](ADR-0055-orthogonal-priority-axes-anti-collision-contract.md) | Aceito |
| 0056  | [Cryptographic ADR inventory (inv-adr.ps1 + SSH ed25519 attestation)](ADR-0056-cryptographic-adr-inventory-inv-adr-ssh-attestation.md) | Aceito |
| 0057  | [Lightweight hub index (co-located links, no file moves)](ADR-0057-lightweight-hub-index-co-located-links.md) | Aceito |
| 0058  | [Primer hub registration ritual](ADR-0058-primer-hub-registration-ritual.md) | Aceito |
| 0059  | [Arquitetura de plugin de remediação (hook mínimo do host)](ADR-0059-remediation-plugin-architecture.md) | Proposto |
| 0060 | [`db/` Ruff and Bandit exclusion — risk accepted](ADR-0060-db-lint-bandit-exclusion-risk-accepted.md) | Aceito |
| 0061 | [ADR-0061 U-axis issue sub-order and cross-milestone gate](ADR-0061-u-axis-issue-suborder-and-cross-milestone-gate.md) | Aceito |
| 0062 | [ADR-0062 Agent containment: triple-audit offband pattern](ADR-0062-agent-containment-triple-audit-offband-pingpong.md) | Aceito |
| 0063 | [ed25519 (EdDSA) for license JWT signing](ADR-0063-ed25519-license-jwt-signing.md) | Aceito |
| 0064 | [License enforcement — additive open-core + JWT](ADR-0064-license-enforcement-additive-model.md) | Proposto |
| 0065 | [NIST SP 800-228A as REST API security hardening reference](ADR-0065-nist-sp800228a-api-security-reference.md) | Deferido |
| 0066 | [TAMPERED state behavior — fail-closed in enforced mode](ADR-0066-tampered-state-behavior.md) | Aceito |
| 0067  | *Reservado* — number freed (was #769 plugin auth); see **0075** | Reservado |
| 0068 | [Primary Linux dev workstation (temporary)](ADR-0068-primary-linux-dev-workstation-temporary.md) | Aceito |
| 0069 | [Cap rpds-py below the 2026 CalVer pivot](ADR-0069-cap-rpds-py-below-the-2026-calver-pivot.md) | Aceito |
| 0070 | [Primer taxonomy and home: technical/onboarding vs deliverable](ADR-0070-primer-taxonomy-and-home.md) | Aceito |
| 0071 | [Self-protecting PII gate: word-boundary matcher, CODEOWNERS, tripwire, FP allowlist](ADR-0071-self-protecting-pii-gate.md) | Aceito |
| 0072 | [Commit Gate vs Release Gate: distinct criteria](ADR-0072-commit-gate-vs-release-gate-distinct-criteria.md) | Aceito |
| 0073 | [Version scheme: octet-maturity side-channel + release-line roadmap](ADR-0073-version-scheme-octet-maturity-and-roadmap.md) | Aceito |
| 0074 | [Supply-chain Layer 1: digest pins and Rust SCA](ADR-0074-supply-chain-layer1-digest-pins-and-rust-sca.md) | Proposto |
| 0075 | [Plugin authentication — file-based license vs Bearer](ADR-0075-plugin-auth-file-based-vs-bearer.md) | Proposto |
| 0076 | [OPA/Rego as CI tier drift linter (not runtime)](ADR-0076-opa-rego-ci-tier-drift-linter-not-runtime.md) | Proposto |
| 0077 | [Filesystem scan does not honor client `.gitignore`](ADR-0077-filesystem-scan-no-client-gitignore-by-design.md) | Aceito |
| 0078 | [Multi-pattern regex: RegexSet before Vectorscan (benchmark gate; 2026-07-31 amend — RegexSet spike failed, cached Regex loop next)](ADR-0078-multi-pattern-regex-benchmark-gate-regexset-before-vectorscan.md) | Proposto |
| 0079 | [Ecosystem engineering rigor canon (UMADR satellites)](ADR-0079-ecosystem-engineering-rigor-canon.md) | Proposto |
| 0080 | [Local validation gate is inviolable: full check-all before any push or PR](ADR-0080-local-validation-gate-inviolable.md) | Proposto |
| 0081 | [No silent ML confidence failures on single-class compliance profiles](ADR-0081-no-silent-ml-confidence-single-class-hardening.md) | Proposto |
| 0082 | [Web exposure safe-by-default boundary controls](ADR-0082-web-exposure-safe-by-default-boundary-controls.md) | Aceito |
| 0083 | [Rust regex stage: accept form B (findings superset)](ADR-0083-rust-regex-stage-superset-accept-form-b.md) | Aceito |
| 0084 | [Native package: embed CPython by channel (Enterprise vs community)](ADR-0084-native-package-embedded-cpython-by-channel.md) | Aceito |
| 0085 | [Install priority ladder (native-first when shipped; pipx today)](ADR-0085-install-priority-ladder.md) | Proposto |
| 0086 | [Contrato language-neutral do Plugin SDK (L1/L2/L3)](ADR-0086-plugin-sdk-language-neutral-contract.md) | Proposto |
| 0087 | [Malha bidirecional zero-trust do Plugin SDK](ADR-0087-plugin-sdk-bidirectional-zero-trust-mesh.md) | Proposto |

| 0088 | [Verifique o verificador: checagens de integridade/autorização não podem depender do artefato que verificam](ADR-0088-verify-the-verifier-no-self-referential-trust-chain.md) | Aceito |

## Docs relacionados

| Doc | Notas |
| ----- | ------------------------------------------------------------------------------------------------------------------------------------ |
| [CONTRIBUTING.pt_BR.md](../../CONTRIBUTING.pt_BR.md) | fluxo do contribuidor; menciona MD029 e o script de correção. |
| [SECURITY.pt_BR.md](../../SECURITY.pt_BR.md) · [docs/TECH_GUIDE.pt_BR.md](../TECH_GUIDE.pt_BR.md) | entradas para operadores ([ADR 0002](ADR-0002-operator-facing-security-and-technical-docs.md)). |
| [QUALITY_WORKFLOW_RECOMMENDATIONS.md](../QUALITY_WORKFLOW_RECOMMENDATIONS.md) | §6 (MD029), §7 (ADRs), SBOM. *(EN.)* |
| [docs/ops/WORKFLOW_DEFERRED_FOLLOWUPS.pt_BR.md](../ops/WORKFLOW_DEFERRED_FOLLOWUPS.pt_BR.md) | follow-ups de workflow/supply-chain ([ADR 0005](ADR-0005-ci-github-actions-supply-chain-pins.md) sobre pin de Actions/uv). |
| [.cursor/rules/markdown-lint.mdc](../../.cursor/rules/markdown-lint.mdc) | quando rodar `fix_markdown_sonar.py` e renumeração pós-script. |
| [.cursor/rules/audience-segmentation-docs.mdc](../../.cursor/rules/audience-segmentation-docs.mdc) | links externos vs internos; [ADR 0004](ADR-0004-external-docs-no-markdown-links-to-plans.md). |

## Índice geral da documentação

Veja [docs/README.pt_BR.md](../README.pt_BR.md) para o mapa completo.

## Ecossistema UMADR (repositórios satélite)

O **data-boar** é a regência UMADR **canônica** ([ADR 0000](ADR-0000-project-origin-and-adr-baseline.md) + [ADR 0045](ADR-0045-adr-metadata-and-format-standardization.md)). Rigor de engenharia compartilhado com satélites: [ADR 0079](ADR-0079-ecosystem-engineering-rigor-canon.md). Outros repositórios do ecossistema DEVEM:

1. Manter **ADR-0000** só como **gênese** (origem/rebrand — sem modus operandi do operador).
2. Adicionar ADR(s) **reference-stub** apontando para o ADR-0000 e o ADR-0079 públicos do data-boar (não duplicar a house rule nem o cânone de rigor).
3. Registrar **rebrands** em ADR dedicado (ver [ADR 0014](ADR-0014-rename-repo-and-package-python3-lgpd-crawler-to-data-boar.md)).
4. Usar nomes com **quatro dígitos** e corpos de ADR **somente em inglês**.

Acompanhamento: GitHub [#994](https://github.com/DataBoar/data-boar/issues/994).

