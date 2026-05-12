# ADR 0044 — Dependabot uses the `uv` ecosystem for Python deps (pyproject + lock closure)

- **Status:** Accepted
- **Date (UTC):** 2026-05-09
- **Authors:** Fabio Leitao
- **Deciders:** Fabio Leitao

## Context

The repository pins Python dependencies with **`uv`**:

- **`pyproject.toml`** (PEP 621) is the **declarative** source of intent (minimum versions / extras).
- **`uv.lock`** is the **resolved** pin.
- **`requirements.txt`** is a **pip-facing export** of `uv.lock` produced by `uv export --no-emit-package pyproject.toml -o requirements.txt`.

[ADR 0030](ADR-0030-python-dependency-update-closure-single-pass.md) requires those three artifacts to move **together** in a single pass when an update is accepted. The guard `tests/test_dependency_artifacts_sync.py::test_requirements_txt_matches_uv_export` runs `uv export --frozen` and compares against the committed `requirements.txt`; any drift fails CI.

Until now, **`.github/dependabot.yml`** declared the Python ecosystem as `pip`. The Dependabot `pip` ecosystem inspects requirement files (e.g. `requirements.txt`) and **edits them in isolation** — it does **not** know about `uv.lock` and does **not** rewrite `pyproject.toml` minimums. Result: every grouped Dependabot PR landed an updated `requirements.txt` while `uv.lock` and `pyproject.toml` stayed at the previous resolution. The lock-vs-export guard then failed CI deterministically.

Concrete failure that motivated this ADR:

- PR #324 (`dependabot/pip/pip-minor-patch-8a525e5820`) bumped 9 packages **only** in `requirements.txt`. CI run `25606471817` failed `test_requirements_txt_matches_uv_export` on Python 3.12 and 3.13 because `uv export --frozen` (using the unmodified `uv.lock`) did not match the committed file.

The CI guard is doing its job — it prevents supply-chain drift. The fix must address the **source of the divergence**, not silence the guard.

## Decision

Switch `.github/dependabot.yml` to the **`uv`** ecosystem for Python dependencies:

```yaml
- package-ecosystem: "uv"
  directory: "/"
  ...
  groups:
    uv-minor-patch:
      patterns: ["*"]
      update-types: ["minor", "patch"]
```

The Dependabot `uv` ecosystem natively understands `pyproject.toml` (PEP 621) plus `uv.lock`, so PRs ship those two artifacts together. Commit-message prefix changes from `deps(pip)` to `deps(uv)` to mirror the ecosystem and stay obvious in `git log`.

### Closure is automated by an existing workflow

The repository already ships **`.github/workflows/dependabot-sync.yml`**, which:

- Triggers on `pull_request` touching `uv.lock` or `pyproject.toml`.
- Runs only for `github.actor == 'dependabot[bot]'`.
- Re-runs `uv export --no-emit-package pyproject.toml -o requirements.txt` and commits the regenerated `requirements.txt` back to the PR branch.

That workflow **never fired** on PR #324 because the `pip` ecosystem only edits `requirements.txt` — neither `uv.lock` nor `pyproject.toml` changed, so the path filter did not match. Switching to the `uv` ecosystem makes Dependabot edit `uv.lock` (and `pyproject.toml` minimums when applicable), which **does** match the path filter and lets `dependabot-sync.yml` complete the closure automatically. Operator action is therefore **not required** for routine bumps; manual closure (per ADR 0030) is reserved for changes the operator pulls locally or for cases where the auto-sync workflow is intentionally skipped.

### Migration of the in-flight pip-ecosystem PR

PR #324 was opened under the old `pip` ecosystem and cannot be auto-converted. Recommended close-out:

- Close PR #324 with a note pointing at this ADR.
- Dependabot will recreate the equivalent group on the next weekly schedule under the `uv` ecosystem (or the maintainer can comment `@dependabot recreate` on a fresh PR if needed).

## Consequences

### Positive

- Dependabot PRs now respect the closure rule of ADR 0030 by default — `pyproject.toml` and `uv.lock` advance together.
- The lock-vs-export guard (`test_requirements_txt_matches_uv_export`) stays strict; we no longer fight it on routine bumps.
- Commit prefix `deps(uv)` documents the resolver in history and SBOM narratives.
- Fewer red Dependabot PRs reduces alert fatigue and keeps the operator focused on real signals.

### Negative / trade-offs

- One-time churn: the in-flight `dependabot/pip/*` branch and `deps(pip)` commit prefix retire. Existing PRs under the old prefix must be closed (or rebased) before Dependabot reissues them under `uv`.
- The auto-sync workflow needs `permissions: contents: write` and runs only for `dependabot[bot]`. Any future audit of the actor guard must check `dependabot-sync.yml` together with this ADR.

### Follow-ups (none required to merge)

1. Optional: rename the auto-sync workflow file/ID to make the link to the `uv` ecosystem explicit (cosmetic; not required for correctness).
2. ADR 0030 remains the canonical closure description — leave its operator checklist intact for manual / non-Dependabot updates.

## References

- [ADR 0030 — Python dependency update closure (single pass)](ADR-0030-python-dependency-update-closure-single-pass.md)
- [ADR 0005 — CI and GitHub Actions supply chain pins](ADR-0005-ci-github-actions-supply-chain-pins.md)
- `tests/test_dependency_artifacts_sync.py` — lock vs export guard.
- `.github/dependabot.yml` — current configuration.
- Failed run that motivated this ADR: GitHub Actions `25606471817` on `dependabot/pip/pip-minor-patch-8a525e5820`.
