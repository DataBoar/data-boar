# ADR 0045 — `chardet` major bumps blocked by `cyclonedx-bom` (Dependabot ignore + stop condition)

## Status

Accepted.

## Context

`chardet` is **not** a direct dependency of Data Boar. It is pulled in **only** by
`cyclonedx-bom`, which the project lists in `[dependency-groups].dev` so the
**SBOM** workflow (`.github/workflows/sbom.yml`, see [ADR 0003](0003-sbom-roadmap-cyclonedx-then-syft.md))
can generate a CycloneDX bill of materials from the resolved tree. The transitive
trail is preserved in the lock — see `requirements.txt` near the `chardet==…`
block:

```text
chardet==5.2.0 \
    --hash=sha256:...
    # via cyclonedx-bom
```

Dependabot opened PR #347 (`dependabot/uv/chardet-7.4.3`) to bump
`chardet 5.2.0 → 7.4.3` in `uv.lock`. The Docker SBOM build (run `25607356665`)
crashed in the builder stage with:

```text
ERROR: Cannot install -r /app/requirements.docker.txt (line 430) and chardet==7.4.3
The conflict is caused by:
    The user requested chardet==7.4.3
    cyclonedx-bom 7.3.0 depends on chardet<6.0 and >=5.1
ERROR: ResolutionImpossible
```

`cyclonedx-bom 7.3.0` is the **latest** release on PyPI at the time of this ADR
and still pins `chardet>=5.1,<6.0`. There is no upstream relax we can pick up by
bumping `cyclonedx-bom` itself; the cap is **physics**, not policy.

The SBOM workflow guard caught the conflict. Suppressing the guard, faking a
green CI, or shipping a fork/patch of either package would violate the
`AGENTS.md` *Risk posture* rule and the
[Defensive scanning manifesto](../ops/inspirations/DEFENSIVE_SCANNING_MANIFESTO.md)
*no surprise side effects* clause. The honest path is to **decline the bump**
with documented evidence and let Dependabot revisit it when the upstream cap
moves.

## Decision

Add a **scoped Dependabot ignore** for `chardet` major-version bumps in
`.github/dependabot.yml`, under the `package-ecosystem: "uv"` block:

```yaml
ignore:
  - dependency-name: "chardet"
    update-types: ["version-update:semver-major"]
```

Rationale:

- **`semver-major`** only — Dependabot can still propose security-relevant patch
  or minor bumps inside the `5.x` line if upstream releases them, so the
  transitive supply chain stays observable.
- **Single dependency, named** — the ignore does not blanket the lock; every
  other package keeps the existing weekly cadence.
- **Comment carries the stop condition** in `dependabot.yml` itself, mirrored
  in this ADR: when `cyclonedx-bom` ships a release that allows `chardet>=6`,
  drop the ignore and let Dependabot bump `chardet` again.

PR #347 is closed as **superseded — blocked upstream by `cyclonedx-bom<6.0`**.

## Consequences

### Positive

- `SBOM`, `Test (3.12/3.13)`, and `Lint (pre-commit)` jobs stop failing on a
  bump that cannot resolve. Alert fatigue drops on subsequent Dependabot runs.
- Supply-chain narrative stays honest: the constraint is recorded in
  `dependabot.yml`, in this ADR, and in the closed PR — three independent
  paper trails for a future operator or auditor.
- No runtime change. No SQL behaviour change. No DB lock posture change. The
  Docker image continues to build with `chardet==5.2.0` exactly as it did
  before PR #347.

### Negative / trade-offs

- Until `cyclonedx-bom` relaxes the cap, Dependabot will not propose `chardet`
  major upgrades automatically. If a `chardet 6+` security advisory lands, the
  operator must triage it manually (the `5.x` line still receives Dependabot
  patch/minor PRs because only `semver-major` is ignored).
- The repository now carries one named upstream-block entry. New entries
  belong in this ADR pattern (cite upstream, name the stop condition) — not as
  unscoped ignores.

### Follow-ups (none required to merge)

1. Watch [`cyclonedx-bom` PyPI](https://pypi.org/project/cyclonedx-bom/) and
   [its repository](https://github.com/CycloneDX/cyclonedx-python). When a
   release lands that allows `chardet>=6`, remove the ignore block, run
   `uv lock --upgrade-package chardet`, regenerate `requirements.txt`, and
   close this ADR loop with a follow-up note (or supersede it).
2. Optional later: trim `cyclonedx-bom` out of the **production** Docker image.
   Today the Dockerfile installs the full lock (including dev deps) into the
   builder. Pruning dev deps from the runtime layer would eliminate this class
   of upstream conflict at the **image** level. Tracked separately — not in
   scope for the SBOM red-CI fix.

## References

- [ADR 0003 — SBOM roadmap (CycloneDX then Syft)](0003-sbom-roadmap-cyclonedx-then-syft.md)
- [ADR 0030 — Python dependency update closure (single pass)](0030-python-dependency-update-closure-single-pass.md)
- [ADR 0044 — Dependabot uses the `uv` ecosystem](0044-dependabot-uv-ecosystem-for-pyproject-lock-closure.md)
- [Defensive scanning manifesto](../ops/inspirations/DEFENSIVE_SCANNING_MANIFESTO.md)
- [The art of the fallback](../ops/inspirations/THE_ART_OF_THE_FALLBACK.md)
- Failed SBOM run: GitHub Actions `25607356665` on
  `dependabot/uv/chardet-7.4.3` (PR #347).
- Upstream pin: `cyclonedx-bom 7.3.0` `requires_dist` →
  `chardet>=5.1,<6.0`.
