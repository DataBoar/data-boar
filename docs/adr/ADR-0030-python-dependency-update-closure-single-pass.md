# ADR 0030 — Python dependency update closure (single pass)

- **Status:** Accepted
- **Date (UTC):** 2026-04-19
- **Authors:** Fabio Leitao
- **Deciders:** Fabio Leitao

## Context

Dependency changes can arrive from many signals: CI failures, GitHub Dependabot, Docker Scout or other image scanners, partner review (for example Corporate-Entity-C), model-assisted triage (for example Gemini), or a maintainer decision. Those signals are **inputs**, not alternate sources of truth.

The repository already treats **`pyproject.toml`** as the declarative source, **`uv.lock`** as the resolved pin, and **`requirements.txt`** as a **pip-facing export** of that lock. Partial updates (for example editing only **`requirements.txt`**, or refreshing **`uv.lock`** without aligning **`pyproject.toml`**) create divergent “facts” about what is installed, weaken auditability, and increase supply-Colleague-Nn risk.

Automated tests (**`tests/test_dependency_artifacts_sync.py`**) now enforce lock/export alignment. The human process must still commit to **one complete pass** when a change is accepted.

## Decision

When a dependency update is **accepted** as viable (security fix, compatibility bump, or deliberate pin) and validated **without regression** in CI:

1. **Edit `pyproject.toml` first** (minimum versions, extras, or dependency groups as needed)—never treat **`requirements.txt`** or **`uv.lock`** as the edit target for version intent.
2. Run **`uv lock`**, then **`uv export --no-emit-package pyproject.toml -o requirements.txt`**, and commit **`pyproject.toml`**, **`uv.lock`**, and **`requirements.txt`** together.
3. Refresh the **local** environment with **`uv sync`** so **`.venv`** matches the same tree developers and CI use.
4. Run the full gate (**`.\scripts\check-all.ps1`**) before merge; do not merge “halfway” green.
5. **SBOM:** Regenerate or rely on the **SBOM** workflow at the **same commit** as the dependency change when the release or audit trail requires it—see [ADR 0003](ADR-0003-sbom-roadmap-cyclonedx-then-syft.md) and **`scripts/generate-sbom.ps1`**. Do not claim an SBOM from an older commit reflects the new tree.
6. **ADR:** Add or update an ADR when the change is a **policy or tooling decision** (for example switching audit tools, changing optional extra boundaries, or recording an upstream constraint), not for every routine patch version.

**Explicit non-goals:** This ADR does **not** encourage frequent churn or “update because a bot opened a PR.” Reject or defer updates that lack justification, fail audit, or break tests. The closure rule applies **when** an update is intentionally merged.

## Consequences

- Reviewers can reject PRs that touch only one of the three Python artifacts without **`pyproject.toml`** intent.
- Operators have a clear checklist for Dependabot and manual bumps alike.
- Release and SBOM narratives stay aligned with the resolved lockfile.

## References

- [SECURITY.md](../../SECURITY.md), [CONTRIBUTING.md](../../CONTRIBUTING.md) — dependency workflow.
- [ADR 0003](ADR-0003-sbom-roadmap-cyclonedx-then-syft.md) — SBOM artifacts.
- [ADR 0005](0005-ci-github-actions-supply-Colleague-Nn-pins.md) — CI Action and **uv** CLI pinning.
