# ADR 0014 — Rename repository and package from `python3-lgpd-crawler` to `data-boar`

**Status:** Accepted — package and primary docs executed in-repo; PyPI publish and optional legacy-remote removal remain operator follow-ups
**Date:** 2026-04-05
**Deciders:** Fabio Tavares Leitao

---

## Context

The project was bootstrapped under the name `python3-lgpd-crawler` — a descriptive,
technical name that accurately described its first form: a Python crawler for LGPD compliance.

Since then, the product has evolved substantially:

- A mascot ("Data Boar"), branded dashboard, and full product identity were adopted
- The GitHub repository was already renamed to `data-boar` on GitHub
  (`github.com/FabioLeitao/data-boar`) — GitHub redirects the old URL
- The `origin` remote in `.git/config` already points to `data-boar.git`
- PyPI slug `data-boar` / `data_boar` is available (confirmed in PLAN_LOGO_AND_NAMING.md)
- The old name `python3-lgpd-crawler` still appears in ~50 tracked files (docs, pyproject.toml,
  CI references, ADRs) and is a branding inconsistency

The only reason the package name (`pyproject.toml [project] name`) was not changed earlier
was deferred priority. There are no downstream consumers pinning to PyPI since the package
is not yet publicly published there.

## Decision

Rename all remaining references from `python3-lgpd-crawler` to `data-boar` (or `data_boar`
for Python identifiers) as part of the next planned release:

| Asset | Old | New |
|---|---|---|
| `pyproject.toml` package name | `python3-lgpd-crawler` | `data-boar` |
| `pyproject.toml` package description | mentions lgpd-crawler | update to match brand |
| GitHub repo (already done) | `python3-lgpd-crawler` | `data-boar` ✅ |
| `origin` remote (already done) | lgpd-crawler.git | data-boar.git ✅ |
| All `*.md` docs referencing old name | ~50 files | batch replace |
| CI workflow file names (if any hardcoded) | lgpd-crawler | data-boar |
| Docker Hub image tags | `data_boar:*` already in use | confirm consistency |
| Collaborator clone remotes (collaborator) | lgpd-crawler.git | data-boar.git (one command) |

**Historical mentions** in ADRs, changelogs, and `docs/plans/completed/` describing the
original name are acceptable and should be retained for historical accuracy — they do not
need to be changed.

## Consequences

### Positive

- Branding consistency: the product is uniformly called "Data Boar" everywhere
- Cleaner first impression for new contributors and partners
- PyPI publish-ready name if/when we submit the package
- Removes the only remaining legacy artifact of the project's origin phase

### Negative / risks

- ~50 files to touch — automated batch replace needed to avoid partial replacement
- `git filter-repo` is NOT required; only a `sed`/`StrReplace` pass on HEAD files
- Collaborator clone remote needs one manual update: `git remote set-url origin git@github.com:FabioLeitao/data-boar.git`
- GitHub redirect for the old URL expires eventually (~1 year) — the sooner the better

### Not a concern

- Git history: commit messages mentioning the old name are historical record — acceptable to keep
- ADR 0000 (project origin): explicitly documents the old name for historical context — keep as-is

## Execution checklist (for the release implementing this ADR)

- [x] `pyproject.toml`: change `name = "python3-lgpd-crawler"` to `name = "data-boar"`
- [x] Batch replace `python3-lgpd-crawler` → `data-boar` in primary operator docs (README, CONTRIBUTING, GLOSSARY, USAGE, SECURITY, TECH_GUIDE, releases narrative, Sonar defaults, etc.)
- [x] CI workflows: no hardcoded old package name found
- [ ] Run `check-all` to confirm no regressions (before merge)
- [ ] `docs/ops/REMOTES_AND_ORIGIN.md`: keep operational git remote names for copy-paste; optional doc-only trim later
- [ ] Notify collaborator with: `git remote set-url origin git@github.com:FabioLeitao/data-boar.git` (if still on old URL)
- [ ] Tag the release with a changelog note when publishing **data-boar** to PyPI
- [ ] Optional: remove legacy second remote from `.git/config` after [BRANCH_AND_DOCKER_CLEANUP.md](../ops/BRANCH_AND_DOCKER_CLEANUP.md) §7

## References
- `docs/plans/completed/PLAN_LOGO_AND_NAMING.md`
- `docs/ops/REMOTES_AND_ORIGIN.md`
