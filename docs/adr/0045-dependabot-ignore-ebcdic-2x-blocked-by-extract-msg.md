# ADR 0045 — Dependabot ignores `ebcdic` 2.x while `extract-msg` pins `ebcdic<2`

## Status

Accepted.

## Context

The repository pins Python dependencies with `uv` per [ADR 0044](0044-dependabot-uv-ecosystem-for-pyproject-lock-closure.md): Dependabot uses `package-ecosystem: "uv"` so PRs move `pyproject.toml` and `uv.lock` together, and `.github/workflows/dependabot-sync.yml` regenerates `requirements.txt` automatically. The drift guard `tests/test_dependency_artifacts_sync.py::test_requirements_txt_matches_uv_export` enforces the single-source-of-truth contract from [ADR 0030](0030-python-dependency-update-closure-single-pass.md).

On 2026-05-09 Dependabot opened **PR #346** (`deps(uv): bump ebcdic from 1.1.1 to 2.0.1`) that **only modified `requirements.txt`** — it left `pyproject.toml` and `uv.lock` untouched. CI run [`25607342909`](https://github.com/FabioLeitao/data-boar/actions/runs/25607342909) failed on:

- `Test (Python 3.12) / Run tests`
- `Test (Python 3.13) / Run tests`
- `Lint (pre-commit) / Pre-commit (all files)`

with the same single assertion:

```text
AssertionError: requirements.txt does not match `uv export` from the lockfile.
Regenerate: uv export --no-emit-package pyproject.toml -o requirements.txt
```

`Bandit (strict)` and `Dependency audit` stayed green; the failure is a dependency-metadata drift, not a runtime regression.

### Why the resolver refuses

`ebcdic` is not declared in `pyproject.toml`. It enters the tree transitively via `extract-msg`. The latest published `extract-msg` (`0.55.0`, our current pin via `extract-msg>=0.55.0`) declares in its `requires_dist`:

```text
ebcdic<2,>=1.1.1
```

Verified with PyPI metadata. Therefore the upper bound on `ebcdic` is **owned by upstream**, not by Data Boar. `uv lock --upgrade-package ebcdic` is a no-op — `uv` correctly refuses to advance past `1.1.1` because doing so would violate `extract-msg`'s constraint. The auto-sync workflow in `dependabot-sync.yml` could not heal PR #346 either: its `paths:` filter triggers on `uv.lock` / `pyproject.toml` changes, and Dependabot wrote neither of those.

### Why this is not a security issue

- `Dependency audit` job stayed green — no advisory pulls `ebcdic` into a vulnerable version on this branch.
- The `ebcdic 2.0.x` series upstream changelog ([roskakori/CodecMapper CHANGES](https://github.com/roskakori/CodecMapper/blob/master/CHANGES.md)) describes 2.0.0 as a "*pure technical release that does not change the functionality*" (build/CI modernisation, drops Python 2 / 3.8) and 2.0.1 as a "*pure documentation update*". The version bump carries no functional or security delta the project is missing.
- `Bandit (strict)` reports zero issues on the working tree.

## Decision

1. Add an **ignore** entry in `.github/dependabot.yml` under the `uv` ecosystem block:

   ```yaml
   ignore:
     - dependency-name: "ebcdic"
       versions: [">=2.0.0"]
   ```

   This stops Dependabot from re-opening invalid bumps for `ebcdic 2.x`.

2. **Close PR #346** as superseded by this ADR and its implementation. The PR cannot land — the resolver legitimately refuses it, and the drift guard correctly rejects the partial edit. Closing it complies with the *Unique and Clean PR protocol* (no dangling unmergeable branches).

3. **Do not silence or weaken the drift guard.** `test_requirements_txt_matches_uv_export` is doing its job; the fix lives at the source (Dependabot config), not at the test.

4. **Revisit when upstream relaxes.** When `extract-msg` ships a release that allows `ebcdic>=2`, remove the `ignore` entry and let the normal `uv` ecosystem flow apply the bump together with the `extract-msg` upgrade.

## Consequences

### Positive

- CI stops being interrupted by an unmergeable Dependabot PR every weekly schedule.
- The drift guard remains strict; the lock file stays the single source of truth.
- The decision is auditable: the ignore rule names the package, the upstream constraint is documented here, and the closing condition (upstream relaxes) is explicit.
- No application code, no SQL connector path, and no DB transaction is touched. The defensive scanning posture (`docs/ops/inspirations/DEFENSIVE_SCANNING_MANIFESTO.md`) and fallback contract (`docs/ops/inspirations/THE_ART_OF_THE_FALLBACK.md`) are unaffected.

### Negative / trade-offs

- We hold `ebcdic` at `1.1.1` until `extract-msg` upstream changes its bound. Acceptable: upstream describes 2.0.x as a non-functional release.
- A future maintainer might be tempted to remove the `ignore` rule without checking `extract-msg`'s `requires_dist`. The inline comment in `dependabot.yml` and this ADR mitigate that risk.

### Follow-ups (none required to merge)

1. Periodically (e.g. every two months, or whenever `extract-msg` ships a new release) re-check whether the `ebcdic<2` cap has been lifted; remove the ignore entry when it has.
2. If `extract-msg` becomes unmaintained or blocks other necessary upgrades, escalate via a separate ADR proposing to replace it with another `.msg` parser.

## References

- [ADR 0030 — Python dependency update closure (single pass)](0030-python-dependency-update-closure-single-pass.md)
- [ADR 0044 — Dependabot uv ecosystem](0044-dependabot-uv-ecosystem-for-pyproject-lock-closure.md)
- `tests/test_dependency_artifacts_sync.py` — lock vs export guard.
- `.github/dependabot.yml` — current configuration with the new `ignore` entry.
- `.github/workflows/dependabot-sync.yml` — auto-regeneration of `requirements.txt` (path-filtered on `uv.lock` / `pyproject.toml`).
- Failed run: GitHub Actions [`25607342909`](https://github.com/FabioLeitao/data-boar/actions/runs/25607342909) on `dependabot/uv/ebcdic-2.0.1` (PR #346).
- Upstream constraint source: `extract-msg` `0.55.0` `requires_dist` on PyPI declares `ebcdic<2,>=1.1.1`.
- `docs/ops/inspirations/DEFENSIVE_SCANNING_MANIFESTO.md` — defensive posture preserved.
- `docs/ops/inspirations/THE_ART_OF_THE_FALLBACK.md` — connector fallback contract unchanged.
