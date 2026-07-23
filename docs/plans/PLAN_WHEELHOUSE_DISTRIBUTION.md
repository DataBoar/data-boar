# Plan: Wheelhouse distribution via GitHub Releases (pan-ABI matrix) (#1182)

<!-- plans-hub-summary: Pan-ABI wheelhouse matrix — cp312/cp313/cp314 × (manylinux|musllinux) × (x86_64|arm64) for non-abi3 third-party deps; ONE cp38-abi3 wheel per (libc×arch) for boar_fast_filter; seed via DataBoar/data-boar-site Releases; hold Troubleshooting/matrix URLs until hosting verified. -->
<!-- plans-hub-related: PLAN_PACKAGING_EXTRAS.md, PLAN_QUICKSTART.md -->

- **Status:** In progress
- **Date:** 2026-07-12 (scope rewrite 2026-07-22 — pan-ABI / full matrix)
- **Authors:** Fabio Leitao (operator); Cursor executor
- **Priority:** H1 (packaging / distribution)
- **GitHub:** [#1182](https://github.com/DataBoar/data-boar/issues/1182) `[P1][packaging]` · cross-ref [#782](https://github.com/DataBoar/data-boar/issues/782) (abi3 wheel matrix) · **GAP-001** (wheel-matrix / maturin)

**Synced with:** [PLANS_TODO.md](PLANS_TODO.md)

---

## Problem

PyPI coverage on **musl / no-AVX** (and other edge corners) stays asymmetric: some compiled dependencies ship incomplete platform tags (classic gap: `scikit-learn` musllinux on newer CPython tags). A **wheelhouse** fills those upstream holes so `pipx install data-boar` works without a local toolchain.

Two **orthogonal** packaging tracks must not be confused:

| Track | ABI model | What the wheelhouse / release matrix must publish |
| ----- | --------- | ------------------------------------------------- |
| **`boar_fast_filter`** (our Rust/PyO3 ext) | **abi3-py38** (`rust/boar_fast_filter/Cargo.toml`) | **ONE** `cp38-abi3` wheel per `(libc × arch)` — serves **all** CPython **3.8+**. **Do not** emit per-`cpXXX` wheels for this extension. Tracked as [#782](https://github.com/DataBoar/data-boar/issues/782) / **GAP-001**. |
| **Third-party compiled deps** (numpy, pandas, scipy, scikit-learn, pydantic-core, cryptography, pillow, …) | **Not** abi3 (stable ABI) for the scientific / ML stack we care about | **Per-`cpXXX`:** `cp312` + `cp313` + `cp314`, each × `(manylinux/glibc \| musllinux/musl)` × `(x86_64 \| arm64)`. Wheelhouse priority = **fill upstream gaps** (e.g. sklearn `cp314` musllinux). |

The first hosted seed (2026-07-12) proved the **HTTPS + `--find-links`** path for **one** gap artifact (`scikit-learn` `cp314` musllinux). That seed is **not** the end state — the plan target is the **full pan-ABI matrix** above.

**CI gating note:** `cp314` remains **signal-only** in CI gating (compat / foresight), not a hard release gate. The wheelhouse still **builds and hosts** `cp314` cells so musl/no-AVX hosts on 3.14 do not fall back to source builds.

---

## Decision

Use a phased wheelhouse distribution model (same direction tracked in #1182 comments):

1. **GitHub Releases assets** (immediate HTTPS seed path).
2. **GitHub Pages + CDN** (`simple/` index path).
3. **R2/S3 static index** as scalable mirror.

### ABI rules (non-negotiable)

1. **`boar_fast_filter` → abi3 only**
   - Source of truth: `pyo3` feature **`abi3-py38`** in `rust/boar_fast_filter/Cargo.toml`.
   - Publish **one** `cp38-abi3` wheel per `(manylinux|musllinux) × (x86_64|arm64)` (typically 3–4 wheels; see #782).
   - **Never** generate `cp312` / `cp313` / `cp314` tagged wheels for this crate — they waste CI and mislead operators about ABI collapse.
   - Cross-ref: issue **#782**, internal gap id **GAP-001** (wheel-matrix / maturin).

2. **Third-party compiled deps → per-CPython tag**
   - Matrix axes:
     - **CPython:** `cp312`, `cp313`, `cp314`
     - **libc:** `manylinux` (glibc), `musllinux` (musl)
     - **arch:** `x86_64`, `arm64` / `aarch64`
   - Prefer consuming **upstream PyPI** wheels when present; wheelhouse **only** publishes cells that upstream lacks or that need `auditwheel repair` / no-AVX rebuilds.
   - Example gap class: `scikit-learn` **cp314 musllinux** (seed already hosted).

### Target matrix (third-party deps)

```text
{cp312, cp313, cp314}
  × {manylinux (glibc), musllinux (musl)}
  × {x86_64, arm64}
```

Plus, separately (not multiplied by cpXXX):

```text
boar_fast_filter: cp38-abi3 × {manylinux, musllinux} × {x86_64, arm64}
```

### Current seed release (slice already shipped — cp314 musllinux gap)

- Site repo: **`DataBoar/data-boar-site`**
- Tag: **`wheelhouse-2026-07-12`**
- Release URL: <https://github.com/DataBoar/data-boar-site/releases/tag/wheelhouse-2026-07-12>
- Asset uploaded:
  - `scikit_learn-1.9.0-cp314-cp314-musllinux_1_2_x86_64.whl`

### Install command (real path for this seed)

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
| 8 | Expand from the cp314 musllinux seed to the **full** third-party matrix (`cp312` + `cp313` + `cp314`) × `(manylinux\|musllinux)` × `(x86_64\|arm64)`, filling upstream gaps; keep `boar_fast_filter` on **abi3-only** (#782 / GAP-001). Note: **cp314 = signal-only** in CI gating | ⬜ |

---

## Acceptance criteria for this slice

- [x] Site release exists with tag `wheelhouse-2026-07-12`.
- [x] cp314 musllinux wheel asset published in that release.
- [x] Real install command documented in this plan.
- [x] Alpine musl proof (`pipx install` + `--demo`) captured.
- [x] `PLANS_HUB` and `PLANS_TODO` synchronized.
- [x] No premature update to Troubleshooting / OS compatibility matrix URLs.
- [ ] Plan scope documents **pan-ABI** rules: abi3 for `boar_fast_filter`; per-`cp312`/`cp313`/`cp314` for third-party compiled deps.
- [ ] Full matrix artifacts + hosted index (`simple/` or equivalent) before broad doc rollout (step 7).
