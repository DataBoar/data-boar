# ADR 0053 — `ebcdic` direct upper-bound pin and Dependabot ignore for blocked semver-major

- **Status:** Accepted
- **Date (UTC):** 2026-05-14
- **Authors:** Fabio Leitao (operator), Data Boar SRE Automation Agent
- **Deciders:** Fabio Leitao

## Context

`extract-msg 0.55.0` — a direct dependency declared in `pyproject.toml` for `.msg` (Outlook) file scanning — declares a hard transitive cap `ebcdic>=1.1.1,<2` in its `requires_dist`. As long as the project depends on the `extract-msg 0.55.x` series, **no resolver can satisfy `ebcdic>=2`**.

Without an explicit upper-bound on `ebcdic` in our own `pyproject.toml`, Dependabot's `uv` ecosystem proposed `ebcdic 1.1.1 → 2.0.1` (PR #346, `dependabot/uv/ebcdic-2.0.1`). The PR's pre-merge checks reproduced the unresolvable conflict at image build time:

```
ERROR: Cannot install -r /app/requirements.docker.txt (line 428) and ebcdic==2.0.1
because these package versions have conflicting dependencies.
The conflict is caused by:
    The user requested ebcdic==2.0.1
    extract-msg 0.55.0 depends on ebcdic<2 and >=1.1.1
ERROR: ResolutionImpossible
```

Failure surfaced as red `Test (Python 3.12)`, `Test (Python 3.13)`, `Lint (pre-commit)`, and `Generate SBOMs (CycloneDX + Syft)` — see GitHub Actions run `25879925361`. Three follow-up PRs (#349 pin, #351 dependabot ignore, #352 closure gap) attempted to fix this but each tried to claim ADR slot `0045`, which was already taken on `main` by `ADR-0045-adr-metadata-and-format-standardization.md`; all three drifted into `mergeStateStatus: DIRTY / CONFLICTING` and never landed.

This is the same upstream-cap drag pattern already documented for `beautifulsoup4<4.14` (lines 13–17 of `pyproject.toml`, also forced by `extract-msg 0.55.0`) and for `chardet<6` (forced by `cyclonedx-bom`). The recurrence makes it clear that the durable cure is an explicit declarative cap in our `pyproject.toml` so the resolver fails fast in Dependabot's own pre-resolution, not after image build inside CI.

## Decision

1. **Direct pin in `pyproject.toml`** — declare `ebcdic>=1.1.1,<2` as an explicit Data Boar dependency. The constraint is identical to the transitive contract `extract-msg 0.55.0` already imposes, so the resolved version (`1.1.1`) does not change; the difference is that Dependabot now sees the cap during its own resolution and skips proposing `2.x`.

2. **Dependabot ignore rule** — add `ignore: [{ dependency-name: "ebcdic", update-types: ["version-update:semver-major"] }]` to `.github/dependabot.yml` (defence in depth: even if a future cosmetic loosening of the `pyproject.toml` cap slips through, the major-bump PR will not be re-opened weekly). `ignore` only blocks Dependabot's *version-update* PRs; **security advisories** for `ebcdic` still surface through `dependabot/security-advisories`, so this does not silence CVE alerts.

3. **Lock and export move together** — `uv lock` and `uv export --no-emit-package pyproject.toml -o requirements.txt` are committed in the same PR; the existing closure guard (`tests/test_dependency_artifacts_sync.py`) keeps the three artefacts in lock-step (ADR 0030 + ADR 0044).

4. **Regression guard** — `tests/test_upstream_capped_dependencies.py` asserts that (a) `pyproject.toml` keeps `ebcdic<2` while `extract-msg` is pinned at `<0.56`-equivalent (`>=0.55.0` with no overriding upper bump in this file), and (b) `.github/dependabot.yml` keeps the ignore entry. The test reads both files as text and pattern-matches the contract — no I/O, no network, no resolver run, so it stays fast.

5. **Supersede the three dangling PRs** — #349, #351, #352 are functionally redundant once this PR lands; the operator is invited to close them as superseded. The dependabot PR #346 itself is the actual broken artifact — once the ignore rule lands on `main`, Dependabot will not re-file it.

### What this ADR is **not** about

- It does **not** suppress `extract-msg`. Outlook `.msg` parsing remains in scope; we depend on extract-msg upstream relaxing its `ebcdic` cap.
- It does **not** add a `time.sleep`, retry loop, or any "defensive scanning manifesto"-style fallback. The failure is supply-chain hygiene, not a runtime resilience question.
- It does **not** weaken any guard. `pii_history_guard.py`, `test_pii_guard.py`, `test_confidential_commercial_guard.py`, the lock-export guard, and the markdown PR/lint pipeline are unchanged.

## Consequences

### Positive

- Dependabot stops the weekly merry-go-round on `ebcdic 2.x`; CI noise drops; operator alert fatigue drops.
- The contract becomes visible in `pyproject.toml` next to the existing `beautifulsoup4<4.14` precedent — future readers see the upstream cap pattern in one place.
- A small, fast pytest gate prevents the cap from being silently removed by a future copy-paste edit.

### Negative / trade-offs

- One extra entry to maintain. When `extract-msg` upstream relaxes its `ebcdic<2` constraint, **both** the `pyproject.toml` upper-bound and the `dependabot.yml` ignore rule must be removed together, otherwise the resolver will still pin `1.1.1` and the cleanup will be invisible. The regression test points at this ADR so anyone editing the cap is funnelled here.
- The `ignore` directive cannot distinguish "blocked by upstream" from "we hate this package"; reviewers must read the comment above the directive (and this ADR) to know why it is there.

### Follow-ups (not required to merge)

1. When `extract-msg` ships a release that relaxes `ebcdic<2`, remove the cap from `pyproject.toml`, drop the `ignore` entry, and delete `tests/test_upstream_capped_dependencies.py::test_ebcdic_upper_bound_present` (the others remain useful as a *pattern* — keep them parameterised against the live `pyproject.toml`).
2. Audit other upstream-capped transitives the same way (`chardet<6` via `cyclonedx-bom`, `beautifulsoup4<4.14` via `extract-msg`) and consider folding them into the same regression guard so the pattern is uniform.

## References

- Failed CI run: <https://github.com/FabioLeitao/data-boar/actions/runs/25879925361> (SBOM workflow on PR #346).
- Dependabot PR #346 — `deps(uv): Bump ebcdic from 1.1.1 to 2.0.1` (to be closed by operator as superseded once this lands on `main`).
- Sibling PRs that tried the same fix but collided on ADR-0045 numbering and went DIRTY: #349, #351, #352 (to be closed as superseded).
- [ADR 0030](ADR-0030-python-dependency-update-closure-single-pass.md) — Python dependency update closure (single pass).
- [ADR 0044](ADR-0044-dependabot-uv-ecosystem-for-pyproject-lock-closure.md) — Dependabot uses the `uv` ecosystem.
- [ADR 0049](ADR-0049-no-brittle-mitigations-robust-input-handling.md) — No brittle mitigations; pinning the cap declaratively is the robust handling here.
- `pyproject.toml` (`beautifulsoup4<4.14` comment, lines 13–17) — same upstream-cap precedent.
- Upstream constraint source of truth: <https://pypi.org/project/extract-msg/0.55.0/> → `requires_dist` → `ebcdic<2 and >=1.1.1`.
