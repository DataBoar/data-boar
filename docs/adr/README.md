# Architecture Decision Records (ADR)

**Português (Brasil):** [README.pt_BR.md](README.pt_BR.md)

Short, durable notes that capture **why** the project chose an approach—not only *what* the code does. They complement the **documentation index** ([README.md](../README.md) — *Internal and reference* lists the planning tree) for backlog context, and [TESTING.md](../TESTING.md) (what CI enforces).

## Convention

| Item         | Rule                                                                                                                                                                                               |
| -----------  | ------------------------------------------------------------------------------------------------------------------------------------                                                               |
| **Location** | This folder: **`docs/adr/`**                                                                                                                                                                       |
| **Naming**   | **`0000-...`** optional **baseline / meta** (e.g. origin); **`0001-short-kebab-title.md`**, **`0002-...`** for substantive decisions — increment for each new ADR; title stays stable after merge. |
| **Language** | **Numbered ADR files (`0000-*.md`, `0001-*.md`, …) are English-only** (canonical text, like plan files under `docs/plans/`). This README has pt-BR.                                                |
| **Format**   | Prefer sections: **Context**, **Decision**, **Consequences**, **References** (MADR-style is fine). Keep to one or two screens.                                                                     |
| **When**     | Security-relevant behaviour, doc/tooling trade-offs that keep biting contributors, or anything you do not want refactored away silently.                                                           |

## Index

| ADR   | Title                                                                                                                                                  | Status   |
| ----- | ------------------------------------------------------------------------------------------------------------------------------------------------------ | -------- |
| 0000  | [Project origin and ADR baseline](0000-project-origin-and-adr-baseline.md)                                                                             | Accepted |
| 0001  | [Markdown fix script, MD029, and semantic step lists](0001-markdown-fix-script-md029-and-semantic-step-lists.md)                                       | Accepted |
| 0002  | [Operator-facing security and technical docs](0002-operator-facing-security-and-technical-docs.md)                                                      | Accepted |
| 0003  | [SBOM roadmap — CycloneDX then Syft](0003-sbom-roadmap-cyclonedx-then-syft.md)                                                                         | Accepted |
| 0004  | [Information architecture — external-tier docs must not link into `plans/`](0004-external-docs-no-markdown-links-to-plans.md)                          | Accepted |
| 0005  | [CI and GitHub Actions supply chain — pinned SHAs and pinned uv CLI](0005-ci-github-actions-supply-chain-pins.md)                                       | Accepted |
| 0006  | [Operator today-mode layout and published-release sync](0006-operator-today-mode-layout-and-published-sync.md)                                          | Accepted |
| 0007  | [Synthetic data corpus as mandatory pre-requisite before real production data](0007-synthetic-data-corpus-before-real-data.md)                          | Accepted |
| 0008  | [Docker CE (official repo) + Compose plugin + Swarm as primary lab container runtime](0008-docker-ce-swarm-over-docker-io-and-podman-only.md)           | Accepted |
| 0009  | [Ansible idempotent roles as single automation source for LAB-NODE-01 lab baseline](0009-ansible-idempotent-roles-as-single-automation-source.md)               | Accepted |
| 0010  | [IP Declaration as prior-art protection for Data Boar at CLT employment](0010-ip-declaration-prior-art-protection-at-employment.md)                     | Accepted |
| 0011  | [Layered observability stack for lab-op (Munin + Wazuh + Prometheus + Monit + rsyslog/GELF)](0011-lab-op-observability-stack-layered.md)                | Accepted |
| 0012  | [OCR and image-based sensitive data detection (Tesseract primary, EasyOCR opt-in, BLOB/base64)](0012-ocr-image-sensitive-data-detection.md)             | Proposed |
| 0013  | [Browser artifact scanning — SQLite (default) + LevelDB (opt-in) strategy](0013-browser-artifact-sqlite-leveldb-scan-strategy.md)                        | Accepted |
| 0014  | [Rename repository and package from python3-lgpd-crawler to data-boar](0014-rename-repo-and-package-python3-lgpd-crawler-to-data-boar.md)               | Accepted |
| 0015  | [PoC test infrastructure with synthetic corpus and API testing](0015-poc-test-infrastructure-synthetic-corpus-and-api-testing.md)                         | Accepted |
| 0016  | [OpenTofu corporate IaC path alongside existing Ansible operations](0016-opentofu-corporate-iac-path-alongside-ansible.md)                                | Accepted |
| 0017  | [Quasi-identification risk/confidence contract and LGPD guardrails](0017-quasi-identification-risk-confidence-contract-and-lgpd-guardrails.md)             | Accepted |
| 0018  | [PII anti-recurrence guardrails for tracked files and branch history](0018-pii-anti-recurrence-guardrails-for-tracked-files-and-branch-history.md)         | Accepted |
| 0019  | [PII verification cadence and manual review gate](0019-pii-verification-cadence-and-manual-review-gate.md)                                                   | Accepted |
| 0020  | [CI must scan full Git history for PII anti-recurrence patterns](0020-ci-full-git-history-pii-gate.md)                                                         | Accepted |
| 0021  | [Public web presence — DNS alias (CNAME), canonical host, TLS, hosting shape](0021-public-web-presence-dns-alias-and-hosting.md)                              | Accepted |
| 0022  | [Public glossary — compliance laws, roles, and platform terms](0022-public-glossary-compliance-and-platform-terms.md)                                         | Accepted |
| 0023  | [Windows primary dev PC filename search — Everything (`es.exe`) first, capped PowerShell fallback](0023-windows-primary-dev-filename-search-everything-es-first-with-fallback.md) | Accepted |
| 0024  | [Enterprise discovery — three complementary tracks (planning posture)](0024-enterprise-discovery-three-complementary-tracks.md) | Accepted |
| 0025  | [Compliance positioning — evidence and inventory, not a legal-conclusion engine](0025-compliance-positioning-evidence-inventory-not-legal-conclusion-engine.md) | Accepted |
| 0026  | [Optional jurisdiction hints — DPO-facing, heuristic, metadata-only](0026-optional-jurisdiction-hints-dpo-facing-heuristic-metadata-only.md) | Accepted |
| 0027  | [Commercial tier boundaries — licensing docs and future JWT claims](0027-commercial-tier-boundaries-licensing-docs-and-future-jwt-claims.md) | Accepted |
| 0028  | [Lab external connectivity evaluation playbook (tracked)](0028-lab-external-connectivity-eval-playbook.md) | Accepted |
| 0029  | [Cursor Markdown preview guardrail + lab-smoke Ansible hook](0029-cursor-markdown-preview-guardrail-and-lab-smoke-ansible-hook.md) | Accepted |
| 0030  | [Python dependency update closure (single pass)](0030-python-dependency-update-closure-single-pass.md) | Accepted |
| 0031  | [PyPI packaging with Hatchling (flat layout)](0031-pypi-packaging-hatchling-flat-layout.md) | Accepted |
| 0032  | [Maturity self-assessment — per-batch history on dashboard HTML](0032-maturity-assessment-batch-history-sqlite.md) | Accepted |
| 0033  | [WebAuthn open Relying Party — JSON endpoints (Phase 1)](0033-webauthn-open-relying-party-json-endpoints.md) | Accepted |
| 0034  | [Outbound HTTP User-Agent — `DataBoar-Prospector/<version>`](0034-outbound-http-user-agent-data-boar-prospector.md) | Accepted |
| 0035  | [README stakeholder pitch vs optional deck vocabulary](0035-readme-stakeholder-pitch-vs-deck-vocabulary.md) | Accepted |
| 0036  | [Exception and log PII redaction pipeline](0036-exception-and-log-pii-redaction-pipeline.md) | Accepted |
| 0037  | [Data Boar self-audit log and governance of the auditor](0037-data-boar-self-audit-log-governance.md) | Accepted |
| 0038  | [Jurisdictional ambiguity — alert and inventory, do not decide law](0038-jurisdictional-ambiguity-alert-dont-decide.md) | Accepted |
| 0039  | [Retention and evidence posture in bonded / customs-adjacent contexts](0039-retention-evidence-posture-bonded-customs-adjacent-contexts.md) | Accepted |
| 0040  | [Assistant default: private stack evidence mirrors without rhetorical asks](0040-assistant-private-stack-evidence-mirrors-default.md) | Accepted |
| 0041  | [Lab completão optional data contract preflight before host smoke](0041-lab-completao-data-contract-preflight.md) | Accepted |
| 0042  | [Public LAB lessons archive + hub (dated snapshots)](0042-lab-lessons-learned-archive-contract.md) | Accepted |
| 0043  | [SQL column sampling — non-null filter and strategy hook](0043-sql-column-sampling-non-null-and-strategy-hook.md) | Accepted |

## Related docs

- [CONTRIBUTING.md](../../CONTRIBUTING.md) — contributor workflow; links MD029 and the fix script.
- [SECURITY.md](../../SECURITY.md) · [docs/TECH_GUIDE.md](../TECH_GUIDE.md) — operator entry points ([ADR 0002](0002-operator-facing-security-and-technical-docs.md)).
- [QUALITY_WORKFLOW_RECOMMENDATIONS.md](../QUALITY_WORKFLOW_RECOMMENDATIONS.md) — §6 (MD029), §7 (ADRs), SBOM.
- [docs/ops/WORKFLOW_DEFERRED_FOLLOWUPS.md](../ops/WORKFLOW_DEFERRED_FOLLOWUPS.md) — deferred workflow/supply-chain notes ([ADR 0005](0005-ci-github-actions-supply-chain-pins.md) for Action/uv pinning).
- [.cursor/rules/markdown-lint.mdc](../../.cursor/rules/markdown-lint.mdc) — when to run `fix_markdown_sonar.py` and post-script renumbering.
- [.cursor/rules/audience-segmentation-docs.mdc](../../.cursor/rules/audience-segmentation-docs.mdc) — external vs internal doc links; [ADR 0004](0004-external-docs-no-markdown-links-to-plans.md).

## Documentation index

See [docs/README.md](../README.md) for the full documentation map.

