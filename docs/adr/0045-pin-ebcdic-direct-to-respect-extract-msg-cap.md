# ADR 0045 — Pin `ebcdic` directly to respect `extract-msg`'s upper bound

## Status

Accepted.

## Context

Data Boar declares `extract-msg>=0.55.0` as a direct dependency in `pyproject.toml` to parse Outlook `.msg` files in the filesystem connector. `extract-msg 0.55.0` declares the following upper-bounded transitive constraints:

- `Requires-Dist: beautifulsoup4 (<4.14,>=4.13)`
- `Requires-Dist: ebcdic (<2,>=1.1.1)`

The repo already pins `beautifulsoup4>=4.13.5,<4.14` directly in `pyproject.toml` exactly to absorb that transitive cap and stop Dependabot from churning unmergeable PRs (same comment block in `pyproject.toml`).

When Dependabot opened **PR #346** to bump `ebcdic 1.1.1 → 2.0.1`, the SBOM workflow build (run [`25607342912`](https://github.com/FabioLeitao/data-boar/actions/runs/25607342912)) failed at the `[builder 6/6]` Docker layer with:

```
ERROR: Cannot install -r /app/requirements.docker.txt (line 428) and ebcdic==2.0.1
because these package versions have conflicting dependencies.

The conflict is caused by:
    The user requested ebcdic==2.0.1
    extract-msg 0.55.0 depends on ebcdic<2 and >=1.1.1
ERROR: ResolutionImpossible
```

`ebcdic` is **not** imported by Data Boar code (`rg 'import ebcdic' = 0 matches`); it is a pure transitive dep used by `extract-msg` to decode legacy IBM EBCDIC code pages embedded in Outlook `.msg` payloads. Forcing `ebcdic 2.x` would break `extract-msg` at runtime for customers that ship `.msg` artifacts from mainframe-adjacent environments (banking, customs, port logistics) — exactly the audience our [`THE_ART_OF_THE_FALLBACK`](../ops/inspirations/THE_ART_OF_THE_FALLBACK.md) doctrine tells us to keep parsing for.

This is the same shape of problem that motivated the existing `beautifulsoup4` pin. We codify it once and stop re-litigating per Dependabot run.

## Decision

1. Add `"ebcdic>=1.1.1,<2"` as a **direct** dependency in `pyproject.toml`, with an inline comment that points at `extract-msg 0.55.0`'s `requires_dist` and at this ADR. The pin mirrors the `beautifulsoup4>=4.13.5,<4.14` pattern already in place.
2. Add an `ignore` entry in `.github/dependabot.yml` for `ebcdic` `version-update:semver-major` (and the matching `beautifulsoup4` major, retroactively) so Dependabot stops opening unmergeable major PRs while the upstream cap is in effect.
3. Regenerate `uv.lock` and `requirements.txt` in the same pass per [ADR 0030](0030-python-dependency-update-closure-single-pass.md). `ebcdic` resolves back to `1.1.1`, the only version published before the `2.x` line, so there is no functional change.
4. Close Dependabot PR #346 as **superseded** by this fix; reference this ADR in the close-out note. Future `ebcdic` security bumps within `1.x` (if any) still flow through Dependabot's `uv-minor-patch` group.

We deliberately do **not** silence the `pip` resolver, the SBOM workflow, or the lock-vs-export guard. The CI signal was correct: it caught a real upstream constraint that the operator must honor until `extract-msg` lifts it.

## Consequences

### Positive

- The SBOM, publish, and CI builds stop failing on the predictable `extract-msg ↔ ebcdic` dependency conflict.
- Operator (and future contributors) see the cap encoded in `pyproject.toml`, not buried in a Dependabot PR conversation.
- The `beautifulsoup4` and `ebcdic` ignore rules document the relationship symmetrically — re-enabling the major bump is a one-line edit when `extract-msg` releases a version with the cap lifted.
- Zero impact on database write paths, SQLite locks, or any runtime code path. The change is metadata-only.

### Negative / trade-offs

- We now own a manual checkpoint: when `extract-msg` ships a release that allows `ebcdic>=2`, we must drop the `<2` upper bound and remove the Dependabot ignore. Tracked in the ignore-rule comment for both pinned packages.
- A direct pin of a transitive package can mask future legitimate `ebcdic 2.x` security advisories that do not affect `extract-msg`. Mitigation: Dependabot **security** updates are not silenced by `version-update:semver-major` ignore rules; CVEs still surface as separate PRs.

### Follow-ups (none required to merge)

1. When `extract-msg` releases a version with `ebcdic<3` (or removes the cap entirely), update `pyproject.toml` and `dependabot.yml` together and document in a follow-up ADR or short note appended here.
2. Consider extracting the "transitive cap pinned directly" pattern into a short note in `docs/ops/` if a third package needs the same treatment.

## References

- [ADR 0030 — Python dependency update closure (single pass)](0030-python-dependency-update-closure-single-pass.md)
- [ADR 0044 — Dependabot uv ecosystem for pyproject + lock closure](0044-dependabot-uv-ecosystem-for-pyproject-lock-closure.md)
- [`docs/ops/inspirations/THE_ART_OF_THE_FALLBACK.md`](../ops/inspirations/THE_ART_OF_THE_FALLBACK.md) — keep parsing legacy payloads, do not break customer paths.
- [`docs/ops/inspirations/DEFENSIVE_SCANNING_MANIFESTO.md`](../ops/inspirations/DEFENSIVE_SCANNING_MANIFESTO.md) — respect the customer environment.
- `pyproject.toml` — direct pins for `beautifulsoup4` and (now) `ebcdic`.
- `.github/dependabot.yml` — `ignore` rules for the pinned transitive caps.
- `extract-msg 0.55.0` requires_dist: <https://pypi.org/project/extract-msg/0.55.0/>.
- Failed CI run: <https://github.com/FabioLeitao/data-boar/actions/runs/25607342912>.
- Dependabot PR (superseded): <https://github.com/FabioLeitao/data-boar/pull/346>.
