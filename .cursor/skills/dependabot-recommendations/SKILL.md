---
name: dependabot-recommendations
description: Check Dependabot dependency and action recommendations, verify they are viable and safe, apply locally with full test validation, and optionally add regression tests. Use when updating dependencies, checking for stale Dependabot PRs, or preparing dependency-update PRs.
---

# Dependabot recommendations: validate and apply safely

Use this skill when updating dependencies, reviewing Dependabot PRs, or preparing the project for a dependency-update PR. Goal: apply only safe updates, keep tests green, and avoid regressions.

## When to apply

- User asks to check or apply Dependabot recommendations.
- Working on pyproject.toml, uv.lock, or requirements.txt with version bumps.
- Preparing a PR that includes dependency or GitHub Action updates.
- Opportunistic dependency hygiene (e.g. after a release or when touching lockfile).

## Workflow

### 1. Discover recommendations

- **PRs:** `gh pr list --state all` (or GitHub UI) to see open/closed Dependabot PRs (pip, uv, github_actions). On Windows, **`.\scripts\maintenance-check.ps1`** (repo root) lists open PRs from `dependabot[bot]` and can run **Docker Scout** on the published image; see **SECURITY.md**.
- **Local vs Dependabot:** Prefer applying the same version change locally rather than merging the Dependabot branch; that way you run the same validation and avoid surprises.

### 2. Verify viability

- **Direct deps:** In pyproject.toml, bump only to versions that are compatible (e.g. patch/minor within same major; check release notes for breaking changes if unsure).
- **Transitive deps:** Use `uv lock --upgrade-package <name>` to pull newer versions allowed by direct dependency constraints; do not add direct pins for transitives unless necessary for security.
- **Actions:** For `.github/workflows/*.yml`, only bump action versions that are documented as backward-compatible (e.g. actions/checkout, SonarQube scan).

### 3. Apply changes

- **pyproject.toml:** Update the relevant `>=X.Y.Z` (or `==` only where reproducibility is required).
- **Lockfile:** Run `uv lock`. For specific transitive upgrades: `uv lock --upgrade-package <name>`.
- **requirements.txt:** If the project exports it, run `uv export --no-emit-package pyproject.toml -o requirements.txt` (or the project’s documented command).
- **Actions:** Edit workflow YAML to use the new action version/tag.

### 4. Validate (mandatory)

- Run the **full test suite** so everything stays green with no errors or warnings:

  ```bash
  uv run pytest -v -W error --tb=short
  ```

- Fix any failing or warning-emitting tests; do not commit with a red or noisy suite.
- If the project uses pre-commit / Ruff: run `uv run pre-commit run --all-files` (or equivalent) so the change is PR-ready.

### 5. Regression guard (when it makes sense)

- **Security or correctness:** If the update fixes a vulnerability or a bug, add or extend a test that would fail if the fix were reverted (e.g. test that a vulnerable pattern is rejected, or that the new API contract is respected).
- **Version contract:** If the app relies on a minimum version behavior, add a test (or assertion) that documents and enforces that (so future downgrades or mistakes are caught).
- Do not add tests for every trivial patch bump; focus on behavior that must not regress.

### 6. PR readiness

- Ensure: tests green, no new linter/format issues, and (if applicable) compliance-sample or other project-specific checks still pass.
- After this, the Dependabot PR for the same update can be closed as “applied locally” if desired; the branch can be deleted once main has the change.

## Checklist (copy and track)

```

- [ ] Dependabot PRs / recommendations identified
- [ ] Version bumps verified as viable and compatible
- [ ] pyproject.toml (and/or workflows) updated; uv lock run; requirements.txt refreshed if used
- [ ] uv run pytest -v -W error — all passed, no warnings
- [ ] Pre-commit / Ruff (or project equivalent) — clean
- [ ] Regression test added if update fixes a bug or enforces a contract
- [ ] Ready for PR; Dependabot PR can be closed if same change applied locally

```

## Notes

- **Upstream-blocked alerts:** If **`uv lock`** fails after adding a security floor (e.g. **`pyopenssl>=26`**) because an optional/direct dep caps the package (e.g. **Snowflake connector** and **`bigdata`** extra), do not merge a broken lockfile. Document in **`docs/ops/`** (see **`DEPENDABOT_PYOPENSSL_SNOWFLAKE.md`**), link from **SECURITY.md**, and optionally dismiss the GitHub alert with **`patch_unavailable`** plus a comment. Revisit when upstream relaxes constraints on PyPI.
- **ebcdic / transitives:** If a Dependabot PR suggests bumping a package that appears only in the lockfile (transitive), try `uv lock --upgrade-package <name>`. If the resolver keeps the old version, a direct dependency is constraining it; document that and leave the Dependabot PR closed unless you add a direct dep.
- **uv tool version:** Dependabot PRs that only bump the `uv` version in a dependency group (e.g. for CI) are independent of app runtime; apply only if the project intends to use that uv version in CI.
