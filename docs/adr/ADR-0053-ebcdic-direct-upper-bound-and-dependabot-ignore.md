# ADR 0053 — `ebcdic` direct upper-bound pin and Dependabot ignore for blocked semver-major

- **Status:** Accepted
- **Date (UTC):** 2026-05-15
- **Authors:** Fabio Leitao (operator), Data Boar automation
- **Deciders:** Fabio Leitao

## Context

`extract-msg 0.55.x`, declared in `pyproject.toml` for Outlook `.msg` scanning, publishes `requires_dist` that caps **`ebcdic>=1.1.1,<2`**. No resolver can satisfy **`ebcdic>=2`** while that series is in use.

Without an explicit `ebcdic` line in our `pyproject.toml`, Dependabot (uv ecosystem) still proposed **`ebcdic` 2.x** bumps that fail at Docker/SBOM `pip install` time with `ResolutionImpossible`, blocking CI (tests, pre-commit, SBOM).

This mirrors the existing pattern for `beautifulsoup4<4.14` (same `extract-msg` release line): declare the upstream cap **directly** so resolution fails early, not only inside the image build.

## Decision

1. **Direct pin in `pyproject.toml`** — add `"ebcdic>=1.1.1,<2"` next to other direct dependencies. Resolved version stays the same; Dependabot sees the cap during its own resolution.
2. **Dependabot `ignore`** — under the `uv` ecosystem block, ignore **`version-update:semver-major`** for `ebcdic` (defense in depth). This does **not** suppress security advisories.
3. **Lock + export in one PR** — `uv lock` and `uv export --no-emit-package pyproject.toml -o requirements.txt` in the same change set; `tests/test_dependency_artifacts_sync.py` keeps the three artifacts aligned ([ADR 0030](ADR-0030-python-dependency-update-closure-single-pass.md), [ADR 0044](ADR-0044-dependabot-uv-ecosystem-for-pyproject-lock-closure.md)).
4. **Regression tests** — `tests/test_upstream_capped_dependencies.py` pattern-matches `pyproject.toml` and `.github/dependabot.yml` (no network, no resolver).

## Consequences

- Dependabot stops reopening impossible `ebcdic` major bumps; CI noise drops.
- When `extract-msg` relaxes its `ebcdic<2` cap, remove the pin, the `ignore` entry, and the ebcdic-specific tests **in the same PR**.

## References

- Upstream cap: [extract-msg 0.55.0 on PyPI](https://pypi.org/project/extract-msg/0.55.0/) (`requires_dist`).
- Related: [ADR 0049](ADR-0049-no-brittle-mitigations-robust-input-handling.md) (declarative bounds over brittle workarounds).
