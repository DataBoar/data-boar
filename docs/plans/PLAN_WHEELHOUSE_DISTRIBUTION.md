# Plan: Wheelhouse distribution via GitHub Releases (musl/no-AVX seed) (#1182)

<!-- plans-hub-summary: Seed cp314 musllinux wheelhouse via DataBoar/data-boar-site GitHub Releases, publish pipx --find-links install path, and hold Troubleshooting/matrix URL updates until hosted verification is complete. -->
<!-- plans-hub-related: PLAN_PACKAGING_EXTRAS.md, PLAN_QUICKSTART.md -->

- **Status:** In progress
- **Date:** 2026-07-12
- **Authors:** Fabio Leitao (operator); Cursor executor
- **Priority:** H1 (packaging / distribution)
- **GitHub:** [#1182](https://github.com/DataBoar/data-boar/issues/1182) `[P1][packaging]`

**Synced with:** [PLANS_TODO.md](PLANS_TODO.md)

---

## Problem

PyPI coverage on musl/no-AVX remains asymmetric for `cp314`: `scikit-learn` has no upstream musllinux wheel. A wheelhouse distribution path is required so `pipx install data-boar` works in musl environments without local toolchain builds.

---

## Decision

Use a phased wheelhouse distribution model (same direction tracked in #1182 comments):

1. **GitHub Releases assets** (immediate HTTPS seed path).
2. **GitHub Pages + CDN** (`simple/` index path).
3. **R2/S3 static index** as scalable mirror.

This slice implements step 1 for **cp314-only** and captures the exact install/proof commands.

### Current seed release (implemented in this slice)

- Site repo discovered: **`DataBoar/data-boar-site`**
- Tag: **`wheelhouse-2026-07-12`**
- Release URL: <https://github.com/DataBoar/data-boar-site/releases/tag/wheelhouse-2026-07-12>
- Asset uploaded:
  - `scikit_learn-1.9.0-cp314-cp314-musllinux_1_2_x86_64.whl`

### Install command (real path for this release)

```bash
pipx install data-boar \
  --pip-args="--find-links https://github.com/DataBoar/data-boar-site/releases/download/wheelhouse-2026-07-12/scikit_learn-1.9.0-cp314-cp314-musllinux_1_2_x86_64.whl"
```

### Proof run (Alpine musl + cp314)

`podman` validation completed on `python:3.14-alpine`:

- `pipx install data-boar` succeeded with the `--find-links` wheel URL above.
- `data-boar --demo --port 18088` produced findings (log lines with `Finding:` and `Connected:` observed).

---

## Anti-link-dead gate (mandatory sequencing)

Do **not** update the following user-facing docs with hosting URL commands until release hosting is verified for the intended channel and final URL contract:

- `docs/TROUBLESHOOTING.md` (+ `.pt_BR.md`)
- `docs/ops/OS_COMPATIBILITY_TESTING_MATRIX.md`

This avoids dead links and premature command publication.

---

## Execution checklist

| Step | Scope | Status |
| ---- | ----- | ------ |
| 1 | Discover site repository with `gh repo list` and confirm owner/name | ✅ |
| 2 | Gather `cp314` musllinux wheelhouse artifacts from `~/wheelhouse-cp314/` | ✅ |
| 3 | Create `DataBoar/data-boar-site` release `wheelhouse-2026-07-12` and upload wheel assets | ✅ |
| 4 | Record real `pipx install` command with `--pip-args --find-links` | ✅ |
| 5 | Prove install + demo in Alpine musl (`podman`) | ✅ |
| 6 | Add plan + `PLANS_TODO` entry + run `plans_hub_sync.py --write` | ✅ |
| 7 | Post-hosting docs rollout in Troubleshooting/matrix with stable URL | ⬜ |
| 8 | Expand from cp314-only to cp313/cp314 matrix as artifacts become available | ⬜ |

---

## Acceptance criteria for this slice

- [x] Site release exists with tag `wheelhouse-2026-07-12`.
- [x] cp314 musllinux wheel asset published in that release.
- [x] Real install command documented in this plan.
- [x] Alpine musl proof (`pipx install` + `--demo`) captured.
- [x] `PLANS_HUB` and `PLANS_TODO` synchronized.
- [x] No premature update to Troubleshooting / OS compatibility matrix URLs.
