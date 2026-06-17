# ADR 0069 — Cap `rpds-py` below the 2026 CalVer pivot

- **Date (UTC):** 2026-06-17
- **Authors:** Fabio Leitao (operator), Data Boar automation
- **Deciders:** Fabio Leitao
- **Consulted:** Claude Code (read-only auditor)

## Status

Accepted

### Status history

- 2026-06-17 — Accepted

## Context

`rpds-py` is a **transitive** dependency only (`referencing` → `jsonschema`); nothing in
`pyproject.toml` declares it directly. Upstream pivoted from `0.x` SemVer to **CalVer** at
**`2026.5.1`**. PyPI confirms `2026.5.1` is a **legitimate** release (a real CalVer pivot,
not a typosquat) — but it is **breaking for this suite**: Dependabot **#871** proposed the
`2026.5.1` bump and CI went red on **Lint + Test 3.12 / 3.13 / 3.14** (4 reds).

During the Lote B Python dependency drain, `uv lock --upgrade` would pull `rpds-py 2026.5.1`
and turn `check-all` red, burning a validation cycle for a transitive package no direct
dependency actually needs at the CalVer epoch.

This is the same shape already governed for other upstream-capped transitives where a newer
version is legitimate yet unusable in our resolution or runtime:
[ADR 0053](ADR-0053-ebcdic-direct-upper-bound-and-dependabot-ignore.md) (`ebcdic<2`) and
[ADR 0054](ADR-0054-chardet-pinned-by-cyclonedx-bom.md) (`chardet<6`).

## Decision

1. **Resolver cap via `[tool.uv]`** — declare
   `constraint-dependencies = ["rpds-py<2026"]` in `pyproject.toml`. Because `rpds-py` is
   transitive, a direct `[project]` dependency line would misrepresent the graph; uv's
   `constraint-dependencies` bounds the resolved version **without** declaring a first-class
   dependency. The resolved version stays on the working pre-CalVer `0.x` line
   (`0.30.0` at time of writing).
2. **Lock + export in one PR** — `uv lock` keeps `rpds-py` on `0.x`; `requirements.txt` is
   regenerated via `uv export`; the three artifacts stay aligned
   ([ADR 0030](ADR-0030-python-dependency-update-closure-single-pass.md),
   [ADR 0044](ADR-0044-dependabot-uv-ecosystem-for-pyproject-lock-closure.md)).
3. **Dependabot `ignore`** — under the `uv` ecosystem block, ignore
   **`version-update:semver-major`** for `rpds-py` (defense in depth). This does **not**
   suppress security advisories.
4. **Regression guards** — `tests/test_upstream_capped_dependencies.py` asserts, with no
   network and no resolver: (a) the `[tool.uv]` `rpds-py<2026` constraint string in
   `pyproject.toml`, (b) the locked `rpds-py` major `< 2026` in `uv.lock`, and (c) the
   `rpds-py` `version-update:semver-major` ignore entry in `.github/dependabot.yml`.

## Rationale

1. **`constraint-dependencies` vs direct pin:** `ebcdic` / `chardet` are pinned directly
   because they surface as resolver-visible caps; `rpds-py` is purely transitive via
   `jsonschema`'s `referencing`, so `[tool.uv] constraint-dependencies` is the correct uv
   lever — it bounds resolution without falsely declaring a direct dependency (keeps the SBOM
   and dependency graph honest).
2. **`<2026`, not an exact `0.x` ceiling:** the breaking change is the **CalVer epoch itself**;
   any `2026.x` is the new incompatible series. The year boundary is the minimal,
   intention-revealing bound and still lets compatible `0.x` patches flow.
3. **Three layered guards:** the pyproject guard catches removal of the constraint; the lock
   guard catches resolver drift into CalVer; the dependabot guard catches removal of the
   ignore that would let the breaking major PR reopen. Together they make the cap
   regression-proof without running a live resolver in CI.

## Consequences

- **Positive:** `check-all` / CI stay green; Dependabot stops reopening the breaking
  `rpds-py 2026.x` major; the cap is machine-enforced, not tribal knowledge.
- **Negative:** the project stays on the `0.x` line and forgoes any genuine improvements in
  the CalVer series until it is explicitly validated.
- **Watch / removal:** when the suite is validated against the CalVer series (full matrix
  3.12 / 3.13 / 3.14 green), remove the `[tool.uv]` constraint, the Dependabot ignore, and
  the three `rpds-py` guards **in the same PR**, and record adoption (amend this ADR's Status
  history or supersede it).

## Alternatives Considered

1. **Accept `rpds-py 2026.5.1` now** (rejected): turns `check-all` / CI red across the
   matrix; would burn a validation cycle mid-drain for a transitive package.
2. **Direct pin in `[project]` dependencies** (rejected): `rpds-py` is not a direct
   dependency; declaring it as one misrepresents the dependency graph and the SBOM.
3. **Pin to an exact `0.x` version** (rejected): brittle; blocks compatible `0.x` patches.
   `<2026` bounds exactly the breaking epoch.
4. **Dependabot `ignore` only, no resolver constraint** (rejected): would not stop
   `uv lock --upgrade` from pulling the CalVer build; the resolver cap is the load-bearing
   control, the ignore is defense in depth.

## Related Decisions

- [ADR 0053 — `ebcdic` direct upper-bound and Dependabot ignore](ADR-0053-ebcdic-direct-upper-bound-and-dependabot-ignore.md)
- [ADR 0054 — `chardet` pinned by cyclonedx-bom](ADR-0054-chardet-pinned-by-cyclonedx-bom.md)
- [ADR 0030 — Python dependency update closure (single pass)](ADR-0030-python-dependency-update-closure-single-pass.md)
- [ADR 0044 — Dependabot uv ecosystem for pyproject/lock closure](ADR-0044-dependabot-uv-ecosystem-for-pyproject-lock-closure.md)
- [ADR 0045 — ADR metadata and format standardization](ADR-0045-adr-metadata-and-format-standardization.md)

## References

- Upstream: `rpds-py 2026.5.1` on PyPI (CalVer pivot); transitive via `referencing` → `jsonschema`.
- Dependabot PR **#871** — `rpds-py 2026.5.1` bump (CI red on 3.12 / 3.13 / 3.14).
- `pyproject.toml` `[tool.uv]` `constraint-dependencies`; `.github/dependabot.yml` `uv` `ignore`.
- `tests/test_upstream_capped_dependencies.py` — `pyproject.toml`, `uv.lock`, and `dependabot.yml` guards.
