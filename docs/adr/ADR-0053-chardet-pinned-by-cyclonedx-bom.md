# ADR 0053 — Decline `chardet` semver-major bumps while `cyclonedx-bom` pins `chardet<6.0`

- **Status:** Accepted
- **Date (UTC):** 2026-05-14
- **Authors:** Data Boar SRE Automation Agent
- **Deciders:** Fabio Leitao

## Context

The SBOM workflow (`.github/workflows/sbom.yml`) builds the production image with
the same `Dockerfile` used by the publish path, then runs Syft against the
resulting image. The builder stage installs the pinned closure from
`requirements.txt` via `pip install -r /app/requirements.docker.txt`. Any
`ResolutionImpossible` from `pip` at that step makes the SBOM job red and blocks
the corresponding PR check.

Dependabot ([PR #347](https://github.com/FabioLeitao/data-boar/pull/347),
`deps(uv): Bump chardet from 5.2.0 to 7.4.3`) proposed a semver-major bump of
`chardet`. The bump fails the SBOM build because:

- `chardet` is **not** a direct Data Boar dependency. It does not appear in
  `[project.dependencies]` of `pyproject.toml`, and no Data Boar runtime module
  imports it.
- `chardet` is pulled in **transitively** by `cyclonedx-bom` (the SBOM
  generator). The annotation in `requirements.txt` reads `# via cyclonedx-bom`.
- `pyproject.toml` declares `cyclonedx-bom>=7.0.0`. The latest release on PyPI
  at the time of this ADR is `cyclonedx-bom 7.3.0` (2026-03-30), which still
  pins `chardet>=5.1,<6.0` in `requires_dist`
  (verified via `https://pypi.org/pypi/cyclonedx-bom/json`).

Because no `cyclonedx-bom` release currently allows `chardet>=6`, every weekly
Dependabot iteration that attempts to bump `chardet` into the 6.x or 7.x line
will reproduce the same `pip` error in the SBOM build:

```text
ERROR: Cannot install -r /app/requirements.docker.txt (line 430) and chardet==7.4.3
because these package versions have conflicting dependencies.
  The user requested chardet==7.4.3
  cyclonedx-bom 7.3.0 depends on chardet<6.0 and >=5.1
ERROR: ResolutionImpossible
```

Failing run for the audit trail: GitHub Actions
[run 25879920050](https://github.com/FabioLeitao/data-boar/actions/runs/25879920050).

## Decision

Add a scoped `ignore` rule under the `package-ecosystem: "uv"` block in
`.github/dependabot.yml` that declines `chardet` semver-major bumps until the
upstream cap moves:

```yaml
ignore:
  - dependency-name: "chardet"
    update-types: ["version-update:semver-major"]
```

Patch and minor bumps within the `chardet 5.x` line continue to flow, so
security advisories against `chardet 5.x` remain observable through Dependabot.

This ADR is the explicit paper trail for that ignore rule, with a documented
**stop condition**: when `cyclonedx-bom` publishes a release that allows
`chardet>=6`, remove the ignore entry and let Dependabot bump `chardet` again.

This is consistent with [ADR 0049](ADR-0049-no-brittle-mitigations-robust-input-handling.md)
(no brittle mitigations): the SBOM build keeps its strong resolver guard and
keeps surfacing real conflicts. We are not silencing the diagnostic — we are
declining an upstream-impossible bump and recording why.

## Consequences

### Positive

- SBOM workflow stops reporting a deterministic red on every weekly Dependabot
  iteration for a bump it cannot accept.
- Zero behavioral change for runtime code: `chardet` stays at the same
  transitive version that `cyclonedx-bom` already constrains.
- No impact on Data Boar's DB connectors, scanners, or report writers. No
  `time.sleep`, no broad `except`, no schema mutation, no skipped tests.
- The stop condition is explicit: when the upstream cap moves, the ignore
  entry is removed in a single, reviewable commit.

### Negative / accepted trade-offs

- Dependabot will not propose `chardet 6.x`/`7.x` until the ignore entry is
  removed. Watch `cyclonedx-bom` releases (and its `requires_dist`) at a
  reasonable cadence; manual rollback of this ADR is part of the routine when
  the cap lifts.
- The ignore is intentionally **scoped to `chardet` only**; it does not weaken
  Dependabot coverage for any other package.

## Verification

- `.github/dependabot.yml` parses (existing `tests/test_github_workflows.py`
  YAML parse guard).
- The Docker SBOM build, exercised by `.github/workflows/sbom.yml` on every PR
  that mutates the lockfile, continues to be the canonical regression gate. If
  some future change accidentally drags `chardet>=6` into the lock outside of
  Dependabot, the SBOM workflow surfaces the same `ResolutionImpossible`.

## References

- Failing run: <https://github.com/FabioLeitao/data-boar/actions/runs/25879920050>
- Dependabot PR (declined): <https://github.com/FabioLeitao/data-boar/pull/347>
- `cyclonedx-bom` 7.3.0 release metadata: <https://pypi.org/pypi/cyclonedx-bom/json>
- ADR 0044 — Dependabot uv ecosystem for pyproject/lock closure.
- ADR 0049 — No brittle mitigations — robust input handling over symptom
  suppression.
