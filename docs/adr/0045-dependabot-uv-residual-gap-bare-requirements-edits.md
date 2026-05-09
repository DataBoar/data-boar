# ADR 0045 — Dependabot `uv` ecosystem residual gap on bare `requirements.txt` edits

## Status

Accepted.

## Context

[ADR 0044](0044-dependabot-uv-ecosystem-for-pyproject-lock-closure.md) switched
`.github/dependabot.yml` to the `uv` ecosystem so Dependabot would advance
`pyproject.toml`, `uv.lock`, and (via `dependabot-sync.yml`) `requirements.txt`
together — closing the drift surfaced by [ADR 0030](0030-python-dependency-update-closure-single-pass.md)
and the lock-vs-export guard (`tests/test_dependency_artifacts_sync.py`).

That assumption held for the common case but missed a residual scenario observed
on PR #347 (`dependabot/uv/chardet-7.4.3`, GitHub Actions run `25607356677`):

- `chardet` is a **transitive** dependency, pulled in by `cyclonedx-bom 7.3.0`,
  whose published metadata declares `chardet (>=5.1,<6.0)`.
- Dependabot's `uv` ecosystem still treats `chardet` as a direct production
  pin **because it appears in `requirements.txt`** (the pip-facing export).
- Bumping `chardet` to `7.4.3` cannot be expressed in `uv.lock` without
  loosening the `cyclonedx-bom` cap; no `cyclonedx-bom` release > 7.3.0 is on
  PyPI yet. So Dependabot opened a PR that **edits `requirements.txt` only**,
  with 37 wheel hashes for `chardet 7.4.3`, and **leaves `uv.lock` and
  `pyproject.toml` untouched**.
- The auto-sync workflow (`.github/workflows/dependabot-sync.yml`) had a path
  filter of `[uv.lock, pyproject.toml]`, so it never fired. The lock-vs-export
  guard then failed CI deterministically across `Lint (pre-commit)`,
  `Test (Python 3.12)`, `Test (Python 3.13)`, and `SBOM`.

The guard is doing its job. The fix has to address the **silent gap** between
"Dependabot edits a single resolver-managed file" and "the lock stays the
single source of truth".

## Decision

Three small, defence-in-depth changes — none of them silence the guard:

1. **Path filter widens to include `requirements.txt`.**
   `.github/workflows/dependabot-sync.yml` now also triggers when Dependabot
   touches `requirements.txt` in isolation. Combined with the existing
   `if: github.actor == 'dependabot[bot]'`, only Dependabot-authored bare
   edits flow into the auto-sync.

2. **`uv lock` runs before `uv export`, making the lock authoritative.**
   When `pyproject.toml` and `uv.lock` already agree (the ADR 0044 happy path),
   `uv lock` is a no-op and the export step regenerates `requirements.txt`
   exactly as before. When Dependabot's bare edit produced a `requirements.txt`
   the resolver cannot satisfy, `uv lock` re-resolves and `uv export` writes
   the **resolver-truth** content back to the PR branch — so the next CI run
   passes the lock-vs-export guard. The trailing commit step now stages
   `uv.lock` plus `requirements.txt` together (no-op safe).

3. **`chardet` major bumps are ignored in `.github/dependabot.yml`.**
   While the upstream `cyclonedx-bom <6` cap on `chardet` holds, opening the
   same incompatible PR every Monday is alert-fatigue without signal. A narrow
   `ignore` rule (`update-types: ["version-update:semver-major"]`) keeps
   minor/patch bumps in scope and disappears the moment the upstream cap
   relaxes. Drop the rule when `cyclonedx-bom` publishes a release that lifts
   the constraint.

A regression assertion in `tests/test_github_workflows.py::
test_dependabot_sync_workflow_present_and_valid` pins `requirements.txt` into
the workflow path filter so a future refactor cannot reintroduce the gap
silently.

### What this is not

- **Not** a relaxation of [ADR 0030](0030-python-dependency-update-closure-single-pass.md).
  The closure rule is unchanged: the three artifacts must move together. The
  workflow now enforces it on a wider trigger surface.
- **Not** a way to bypass the lock-vs-export guard. The guard remains strict;
  the workflow simply prevents Dependabot from arriving at the guard with a
  resolver-incoherent `requirements.txt`.
- **Not** a database-touching change. Zero impact on connector code, SQLite
  benchmark fixtures, or the `WITH (NOLOCK)` posture in
  `docs/ops/inspirations/DEFENSIVE_SCANNING_MANIFESTO.md`.

## Consequences

### Positive

- Dependabot mis-bumps on transitive caps no longer red-light four parallel
  CI jobs (`Lint`, `Test 3.12`, `Test 3.13`, `SBOM`) for the same root cause.
- The lock stays the single source of truth — when Dependabot's intent is
  resolver-incompatible, the auto-sync corrects `requirements.txt` back on
  the PR branch instead of letting the guard fail and waiting for a human.
- Operator alert fatigue drops; weekly Dependabot runs no longer recreate the
  blocked `chardet` PR while the upstream cap holds.
- The hardening follows
  [`docs/ops/inspirations/THE_ART_OF_THE_FALLBACK.md`](../ops/inspirations/THE_ART_OF_THE_FALLBACK.md):
  the strongest source (the resolver) wins; degraded inputs (Dependabot's
  isolated `requirements.txt` edit) are reconciled, not silenced.

### Negative / trade-offs

- The auto-sync now amends the PR branch on **any** Dependabot-authored
  `requirements.txt` change, including the (rare) case where Dependabot's
  intent is correct but the resolver disagrees. The committed amendment makes
  the disagreement explicit in the PR diff; reviewers can decide whether the
  lock or the bump is wrong. This is preferable to silent CI red.
- The `chardet` ignore rule is targeted and time-limited; it must be revisited
  whenever `cyclonedx-bom` publishes a release. Tracked via the comment in
  `.github/dependabot.yml` itself.

### Follow-ups (none required to merge)

1. When `cyclonedx-bom` ships a release that drops the `chardet <6` cap,
   remove the `ignore` block in `.github/dependabot.yml` and run `uv lock
   --upgrade-package chardet` + `uv export` to land the bump cleanly.
2. PR #347 is structurally unmergeable while the upstream cap holds; the
   operator should close it as superseded by this ADR (Dependabot will not
   recreate it because of the new ignore rule).

## References

- [ADR 0030 — Python dependency update closure (single pass)](0030-python-dependency-update-closure-single-pass.md)
- [ADR 0044 — Dependabot uv ecosystem](0044-dependabot-uv-ecosystem-for-pyproject-lock-closure.md)
- [ADR 0005 — CI and GitHub Actions supply chain pins](0005-ci-github-actions-supply-chain-pins.md)
- [`docs/ops/inspirations/THE_ART_OF_THE_FALLBACK.md`](../ops/inspirations/THE_ART_OF_THE_FALLBACK.md)
- `tests/test_dependency_artifacts_sync.py` — lock vs export guard.
- `tests/test_github_workflows.py::test_dependabot_sync_workflow_present_and_valid`
  — path-filter regression guard.
- `.github/workflows/dependabot-sync.yml` — hardened workflow.
- `.github/dependabot.yml` — current ecosystem and ignore rules.
- Failed run that motivated this ADR: GitHub Actions `25607356677` on
  `dependabot/uv/chardet-7.4.3` (PR #347).
