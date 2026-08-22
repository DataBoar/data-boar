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

### Closure after Dependabot PRs (#1419, 2026-08-21)

The auto-sync workflow **no longer unsigned-pushes** to Dependabot branches under `required_signatures`. It posts a handoff comment (+ artifact) or opens a **signed child PR** when `DEPENDABOT_SYNC_SSH_SIGNING_KEY` is configured. See [docs/ops/DEPENDABOT_REQUIREMENTS_SYNC.md](../ops/DEPENDABOT_REQUIREMENTS_SYNC.md). Operator-signed closure (ADR 0030) remains the default path.

### Closure is automated by an existing workflow

The repository already ships **`.github/workflows/dependabot-sync.yml`**, which:

- Triggers on `pull_request` touching `uv.lock` or `pyproject.toml`.
- Runs only for `github.event.pull_request.user.login == 'dependabot[bot]'`.
- Re-runs `uv export --no-emit-package pyproject.toml -o requirements.txt` and either hands off to the operator (comment + artifact) or opens a signed child PR when signing secrets exist.

That workflow **never fired** on PR #324 because the `pip` ecosystem only edits `requirements.txt` — neither `uv.lock` nor `pyproject.toml` changed, so the path filter did not match. Switching to the `uv` ecosystem makes Dependabot edit `uv.lock` (and `pyproject.toml` minimums when applicable), which **does** match the path filter and lets `dependabot-sync.yml` run the export closure step. **Signed** completion still requires operator action or configured SSH signing secrets ([#1419](https://github.com/DataBoar/data-boar/issues/1419)).

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
- The auto-sync workflow needs `permissions: contents: write` and `pull-requests: write`, and runs only for Dependabot PRs. Any future audit of the actor guard must check `dependabot-sync.yml` together with this ADR and [DEPENDABOT_REQUIREMENTS_SYNC.md](../ops/DEPENDABOT_REQUIREMENTS_SYNC.md) (#1419).

### Follow-ups (none required to merge)

1. Optional: rename the auto-sync workflow file/ID to make the link to the `uv` ecosystem explicit (cosmetic; not required for correctness).
2. ADR 0030 remains the canonical closure description — leave its operator checklist intact for manual / non-Dependabot updates.

## References

- [ADR 0030 — Python dependency update closure (single pass)](ADR-0030-python-dependency-update-closure-single-pass.md)
- [ADR 0005 — CI and GitHub Actions supply chain pins](ADR-0005-ci-github-actions-supply-chain-pins.md)
- `tests/test_dependency_artifacts_sync.py` — lock vs export guard.
- `.github/dependabot.yml` — current configuration.
- Failed run that motivated this ADR: GitHub Actions `25606471817` on `dependabot/pip/pip-minor-patch-8a525e5820`.
