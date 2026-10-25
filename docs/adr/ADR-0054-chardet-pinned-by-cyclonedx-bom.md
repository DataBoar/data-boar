# ADR 0054 — Decline `chardet` semver-major bumps while `cyclonedx-bom` pins `chardet<6.0`

- **Status:** Accepted
- **Date (UTC):** 2026-05-15
- **Authors:** Data Boar automation
- **Deciders:** Fabio Leitao

## Context

The SBOM workflow builds the production image and runs CycloneDX/Syft. The builder installs the pinned closure from `requirements.txt` via `pip`. A **`ResolutionImpossible`** at that step turns the SBOM job red.

`chardet` is **not** a runtime Data Boar dependency. It is pulled in **transitively** by **`cyclonedx-bom`** (dev/SBOM toolchain). Current `cyclonedx-bom` releases (for example 7.3.0) still declare **`chardet>=5.1,<6.0`** in `requires_dist`.

Dependabot therefore proposed semver-major `chardet` bumps (for example 5.x to 7.x) that **cannot** resolve alongside `cyclonedx-bom`, reproducing the same pip error on every cycle.

## Decision

1. **Dependabot `ignore`** — under the `uv` ecosystem block, ignore **`version-update:semver-major`** for `chardet` until `cyclonedx-bom` allows `chardet>=6`.
2. **Dev direct pin** — add `"chardet>=5.1,<6.0"` under `[dependency-groups] dev` so the resolver and Dependabot see the same cap as the SBOM closure (mirrors the `beautifulsoup4` / `ebcdic` precedent).
3. **Lock + export** — same PR updates `uv.lock` and `requirements.txt` per [ADR 0030](ADR-0030-python-dependency-update-closure-single-pass.md).
4. **Regression tests** — `tests/test_upstream_capped_dependencies.py` asserts the dev pin and the Dependabot ignore stay present.

## Consequences

- SBOM CI stops failing on deterministic impossible `chardet` major bumps.
- Runtime behavior unchanged: `chardet` remains a dev-transitive only.
- When upstream lifts `chardet<6`, remove the dev pin, the `ignore` entry, and the chardet-specific tests in one reviewed change.

## References

- [ADR 0044](ADR-0044-dependabot-uv-ecosystem-for-pyproject-lock-closure.md) — uv Dependabot ecosystem.
- [ADR 0049](ADR-0049-no-brittle-mitigations-robust-input-handling.md) — no brittle mitigations.
- CycloneDX BOM metadata: [pypi cyclonedx-bom JSON](https://pypi.org/pypi/cyclonedx-bom/json).
