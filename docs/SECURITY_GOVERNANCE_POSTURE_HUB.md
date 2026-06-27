# Security, governance, safety, quality & provenance — posture hub

**Português (Brasil):** [SECURITY_GOVERNANCE_POSTURE_HUB.pt_BR.md](SECURITY_GOVERNANCE_POSTURE_HUB.pt_BR.md)

> **For agents (Cursor / Claude):** read this page when you need the **map of maps** for security posture, governance gates, agent containment, and supply-chain evidence. We **do not** move canonical files — co-located links only ([ADR-0057](adr/ADR-0057-lightweight-hub-index-co-located-links.md)). Operator vault mirror (stacked private git under `docs/private/`) may hold lab-specific security runbooks; this hub stays on **public** `origin`.

## How to use

1. Pick a theme row below (Cyber, Governance, Safety, Code quality, Provenance).
2. Follow backtick paths to the real file — never assume a moved path.
3. For integrity/tamper/release evidence chains, start at [`docs/ops/INTEGRITY_HUB.md`](ops/INTEGRITY_HUB.md).

## Cyber

| Topic | Entry points |
| ----- | ------------ |
| Vulnerability reporting & supported versions | [`SECURITY.md`](../SECURITY.md) · [`SECURITY.pt_BR.md`](../SECURITY.pt_BR.md) |
| PII gates (tracked tree + history) | [ADR-0018](adr/ADR-0018-pii-anti-recurrence-guardrails-for-tracked-files-and-branch-history.md) · [ADR-0019](adr/ADR-0019-pii-seed-gate-staged-files.md) · [ADR-0020](adr/ADR-0020-ci-full-git-history-pii-gate.md) · [ADR-0071](adr/ADR-0071-self-protecting-pii-gate.md) · [`docs/ops/PII_PUBLIC_TREE_OPERATOR_GUIDE.md`](ops/PII_PUBLIC_TREE_OPERATOR_GUIDE.md) |
| Tamper / runtime trust | [ADR-0066](adr/ADR-0066-fail-closed-runtime-trust-tamper-posture.md) · [`docs/ops/INTEGRITY_HUB.md`](ops/INTEGRITY_HUB.md) |
| NIST-aligned posture | [ADR-0065](adr/ADR-0065-nist-csf-aligned-security-posture-mapping.md) |
| Supply chain (deps, SBOM, pins) | [ADR-0005](adr/ADR-0005-ci-quality-gates-and-supply-chain-scanning.md) · [ADR-0003](adr/ADR-0003-sbom-roadmap-cyclonedx-then-syft.md) · [ADR-0073](adr/ADR-0073-version-scheme-octet-maturity-and-roadmap.md) (Proposed) · supply-chain posture ADR tracks GitHub **#987** |
| Lab host security stack | [`docs/ops/DATA_BOAR_LAB_SECURITY_TOOLING.md`](ops/DATA_BOAR_LAB_SECURITY_TOOLING.md) |
| Host-binding / outbound identity | [ADR-0034](adr/ADR-0034-outbound-http-user-agent-data-boar-prospector.md) · `.cursor/rules/homelab-ssh-via-terminal.mdc` (situational) |

## Governance

| Topic | Entry points |
| ----- | ------------ |
| Agent contract (non-negotiables) | [`AGENTS.md`](../AGENTS.md) |
| ADR metadata & format | [ADR-0045](adr/ADR-0045-adr-metadata-and-format-standardization.md) |
| Issue / release gates | [ADR-0061](adr/ADR-0061-u-axis-issue-suborder-and-cross-milestone-gate.md) · [ADR-0072](adr/ADR-0072-commit-gate-vs-release-gate-distinct-criteria.md) (Proposed) |
| Agent containment (A.I.I.D.C.O.B.P.P.) | [ADR-0062](adr/ADR-0062-agent-containment-triple-audit-offband-pingpong.md) · [`docs/adr/ADR-0062-diagram.mermaid`](adr/ADR-0062-diagram.mermaid) · [`docs/ops/lab_lessons_learned/LAB_LESSON_AIIDCOBPP_QUAD_AUDIT.md`](ops/lab_lessons_learned/LAB_LESSON_AIIDCOBPP_QUAD_AUDIT.md) |
| Self-audit log governance | [ADR-0037](adr/ADR-0037-data-boar-self-audit-log-governance.md) |
| Taxonomy / priority axes | [ADR-0048](adr/ADR-0048-orthogonal-priority-axes-h-u-g-p.md) · [ADR-0055](adr/ADR-0055-orthogonal-priority-axes-anti-collision-contract.md) |
| Governance positioning diagrams | [`docs/ops/governance/DATABOAR_GOVERNANCE_DIAGRAMS.md`](ops/governance/DATABOAR_GOVERNANCE_DIAGRAMS.md) |
| Cursor policy map | [`docs/ops/CURSOR_AGENT_POLICY_HUB.md`](ops/CURSOR_AGENT_POLICY_HUB.md) |
| Version / release guardrails | [`docs/VERSIONING.md`](VERSIONING.md) · `.cursor/rules/release-versioning.mdc` · `security/version_policy.yaml` |

## Safety

| Topic | Entry points |
| ----- | ------------ |
| Security & PII gates (never weaken) | `.cursor/rules/never-weaken-security-gates.mdc` · [ADR-0049](adr/ADR-0049-no-brittle-mitigations-robust-input-handling.md) |
| RCA-first / investigation | [ADR-0047](adr/ADR-0047-rca-first-operator-investigation-before-blocking.md) · `.cursor/rules/operator-investigation-before-blocking.mdc` |
| Operator-gated release (#406) | GitHub **#406** · [ADR-0072](adr/ADR-0072-commit-gate-vs-release-gate-distinct-criteria.md) (Proposed) · operator-gated reopen tracks **#990** |
| Primary workstation protection | [`docs/ops/PRIMARY_LINUX_WORKSTATION_PROTECTION.md`](ops/PRIMARY_LINUX_WORKSTATION_PROTECTION.md) · [`docs/ops/PRIMARY_WINDOWS_WORKSTATION_PROTECTION.md`](ops/PRIMARY_WINDOWS_WORKSTATION_PROTECTION.md) |

## Code quality

| Topic | Entry points |
| ----- | ------------ |
| CI gate stack | [ADR-0005](adr/ADR-0005-ci-quality-gates-and-supply-chain-scanning.md) · `.github/workflows/ci.yml` |
| Local gate ritual | [`docs/TESTING.md`](TESTING.md) · [`docs/QUALITY_WORKFLOW_RECOMMENDATIONS.md`](QUALITY_WORKFLOW_RECOMMENDATIONS.md) · `./scripts/check-all.sh` / `.\scripts\check-all.ps1` |
| Static analysis | Bandit · Semgrep · Zizmor · CodeQL (workflows) · Ruff/pre-commit |
| No brittle mitigations | [ADR-0049](adr/ADR-0049-no-brittle-mitigations-robust-input-handling.md) |

## Provenance

| Topic | Entry points |
| ----- | ------------ |
| ADR crypto inventory | [ADR-0056](adr/ADR-0056-adr-inventory-ed25519-attestation-workflow.md) · `scripts/inv-adr.ps1` · [`docs/adr/INVENTORY.txt`](adr/INVENTORY.txt) |
| Sigstore / cosign roadmap | [`docs/ops/RELEASE_INTEGRITY.md`](ops/RELEASE_INTEGRITY.md) · `docs/plans/PLAN_BUILD_IDENTITY_RELEASE_INTEGRITY.md` (internal) |
| SBOM | [ADR-0003](adr/ADR-0003-sbom-roadmap-cyclonedx-then-syft.md) · [`SECURITY.md`](../SECURITY.md) § SBOM |
| Dependency closure | [ADR-0030](adr/ADR-0030-python-dependency-update-closure-single-pass.md) · [ADR-0044](adr/ADR-0044-dependabot-uv-ecosystem-for-pyproject-lock-closure.md) |

## Vault ↔ repo cross-link

| Surface | Role |
| ------- | ---- |
| **Public repo (this tree)** | Policy, ADRs, CI guards, operator runbooks without secrets |
| **Stacked private git (`docs/private/`)** | Lab hostnames, manifests, completão narratives, commercial/legal evidence — never paste into tracked files |
| **Operator vault mirror** | Optional Claude-side hub copy; **this** file is the canonical public index |

## Related hubs

- [`docs/hubs/INDEX.md`](hubs/INDEX.md) — map of all hubs
- [`docs/ops/INTEGRITY_HUB.md`](ops/INTEGRITY_HUB.md) — tamper detection & release evidence
- [`docs/ops/LAB_LESSONS_LEARNED.md`](ops/LAB_LESSONS_LEARNED.md) — rolling lab lessons + archive index

## Update ritual

1. Add rows here (EN + pt-BR mirror) when a new posture ADR or guard lands.
2. Register this hub in [`docs/hubs/INDEX.md`](hubs/INDEX.md).
3. Run `./scripts/check-hubs.sh` before merge.

Refs: GitHub **#992**, **#991**, **#987**, post-**#970** versioning saga.
