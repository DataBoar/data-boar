# ADR 0005 — CI and GitHub Actions supply chain — pinned SHAs and pinned uv CLI

- **Status:** Accepted
- **Date (UTC):** 2026-03-27
- **Authors:** Fabio Leitao
- **Deciders:** Fabio Leitao

## Context

CI pipelines that pull **third-party GitHub Actions** by **moving tags** (for example `uses: actions/checkout@v4` resolving to whatever commit the tag currently points to) are exposed to **supply-chain** classes of risk: a compromised or malicious update to the action repository can change behaviour **without** a deliberate edit in this repo. The same class of concern applies to **floating tool installers** (for example instructing a setup action to install the **latest** CLI every run), which makes builds **non-reproducible** and widens the window for unexpected upstream change.

This project already treats **Python** dependencies with a **committed lockfile** (`uv.lock`), **pip-audit** in CI, and **Dependabot** for pip and Actions. That stack addresses **known vulnerable packages** and **notification** of Action updates; it does **not** by itself fix tag-moving or silent installer drift.

**Incident example (March 2026):** The **Trivy** ecosystem published a supply-chain advisory where **malicious actors** altered **official distribution channels** — including **force-pushed or recreated tags** on **`trivy-action`** and **`setup-trivy`** GitHub Actions and compromised **binaries/images** — with impact on CI runners that executed those steps (credential theft while scans still *appeared* normal). See [GitHub Advisory GHSA-69fq-xp46-6x23](https://github.com/advisories/GHSA-69fq-xp46-6x23) and [Microsoft’s defender guidance](https://www.microsoft.com/en-us/security/blog/2026/03/24/detecting-investigating-defending-against-the-trivy-supply-chain-compromise/). **This repository does not use Trivy in `.github/workflows/`**, so that specific vector was **not** exercised here; the case still illustrates why **immutable SHA pins** and **explicit tool versions** matter for **any** third-party Action or installer added later.

## Decision

1. In **`.github/workflows/`** workflows that use third-party Actions (including **CI**, **CodeQL**, **Semgrep**, **slack-ops-digest**, and related jobs), reference each third-party action with a **`uses:`** line that pins the **full 40-character commit SHA** of the action repository. Keep a **human-readable version** in a trailing YAML **comment** on the same line (for example `# v6`) for maintainers.
1. For **`astral-sh/setup-uv`**, set an explicit **`version:`** for the **uv** CLI **semver** in **`ci.yml`** (and the same wherever that step is used). **Do not** use **`version: "latest"`** for uv in CI: bumps become **explicit PRs** after local/CI verification.
1. **Dependabot** (`github-actions` ecosystem) remains the primary **mechanism to propose** SHA bumps; reviewers read upstream release notes before merge.
1. **Enforcement:** **`tests/test_github_workflows.py`** asserts that **`ci.yml`** contains **`astral-sh/setup-uv@`** with a pinned SHA and **does not** contain **`version: "latest"`** for that action, and that **`uses:`** lines that pin third-party actions include a **40-character** hex SHA. Extend the test when new workflows add pinned third-party actions if regression risk warrants it.

## Consequences

- **Positive:** Reduces **tag-moving** and **silent installer drift** risk; improves **reproducibility** of CI installs; documents intent for contributors and security reviewers.
- **Negative:** **More churn** from Dependabot PRs and manual comment updates; reviewers must verify SHA + release notes.
- **Explicit non-guarantees:** Pinning **does not** eliminate **zero-day** compromise of a **already-pinned** commit, **social engineering** or **bypass** of review, **malicious code** that passes as a legitimate upstream release, **typosquat** or **non-CVE** malware in PyPI (see **pip-audit** scope), or risks on **maintainer laptops** (extensions, MCP, local tooling) **outside** these workflows. Honest scope for buyers and operators stays in **[SECURITY.md](../../SECURITY.md)**, **[COMPLIANCE_AND_LEGAL.md](../COMPLIANCE_AND_LEGAL.md)** (risk treatment framing), and narrative notes such as **[docs/ops/inspirations/SUPPLY_CHAIN_AND_TRUST_SIGNALS.md](../ops/inspirations/SUPPLY_CHAIN_AND_TRUST_SIGNALS.md)**.

## References

- [WORKFLOW_DEFERRED_FOLLOWUPS.md](../ops/WORKFLOW_DEFERRED_FOLLOWUPS.md) — backlog; **PyPI + Actions** row points here for the authoritative decision.
- [SUPPLY_CHAIN_AND_TRUST_SIGNALS.md](../ops/inspirations/SUPPLY_CHAIN_AND_TRUST_SIGNALS.md) — how the repo **consumes** supply-chain lessons; scope limits.
- [ADR 0003](ADR-0003-sbom-roadmap-cyclonedx-then-syft.md) — SBOM for **inventory / IR**, complementary to CI pinning.
- [QUALITY_WORKFLOW_RECOMMENDATIONS.md](../QUALITY_WORKFLOW_RECOMMENDATIONS.md) — quality layers and branch protection.
- [`tests/test_github_workflows.py`](../../tests/test_github_workflows.py) — `test_ci_yml_pins_actions_and_uv_cli`.
- [GitHub: Security hardening for GitHub Actions](https://docs.github.com/en/actions/security-guides/security-hardening-for-github-actions) — general upstream guidance.
- [GHSA-69fq-xp46-6x23](https://github.com/advisories/GHSA-69fq-xp46-6x23) (Trivy ecosystem compromise, March 2026) — example of **tag** and **binary** supply-chain risk in CI-adjacent tooling.
