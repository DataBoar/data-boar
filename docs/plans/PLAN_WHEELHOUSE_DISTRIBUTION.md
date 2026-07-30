# Plan: Wheelhouse distribution via GitHub Releases (pan-ABI matrix) (#1182)

<!-- plans-hub-summary: Pan-ABI wheelhouse matrix — cp312/cp313/cp314 + cp314t (no-GIL) × (manylinux|musllinux) × (x86_64|arm64) × CPU baseline (x86-64-v1 for GIL cells); hosted wheelhouse-x86-64-v1-2026-07-29 = 56 assets (10× cp314t); mariadb glibc recipe + CI recipe gates (#1367/#1379); aarch64 mariadb still #1366. -->
<!-- plans-hub-related: PLAN_PACKAGING_EXTRAS.md, PLAN_QUICKSTART.md -->

- **Status:** In progress (x86-64-v1 slice shipped; recipe CI gates live; arm64 + PEP 503 index pending)
- **Date:** 2026-07-12 (scope rewrite 2026-07-22; v1 release + doc rollout 2026-07-29 — [#1365](https://github.com/DataBoar/data-boar/issues/1365); mariadb glibc recipe 2026-07-29 — [#1367](https://github.com/DataBoar/data-boar/issues/1367); recipe CI 2026-07-29 — [#1379](https://github.com/DataBoar/data-boar/issues/1379); **cp314t / no-GIL cells 2026-07-30**)
- **Authors:** Fabio Leitao (operator); Cursor executor
- **Priority:** H1 (packaging / distribution)
- **GitHub:** [#1182](https://github.com/DataBoar/data-boar/issues/1182) `[P1][packaging]` · cross-ref [#782](https://github.com/DataBoar/data-boar/issues/782) (abi3 wheel matrix) · **GAP-001** (wheel-matrix / maturin) · doc slice [#1365](https://github.com/DataBoar/data-boar/issues/1365) · mariadb glibc recipe [#1367](https://github.com/DataBoar/data-boar/issues/1367) · recipe CI [#1379](https://github.com/DataBoar/data-boar/issues/1379) · aarch64 axis [#1366](https://github.com/DataBoar/data-boar/issues/1366)

**Synced with:** [PLANS_TODO.md](PLANS_TODO.md)

---

## Problem

PyPI coverage on **musl / no-AVX / x86-64-v1** (and other edge corners) stays asymmetric: some compiled dependencies ship incomplete platform tags or ISA baselines too high for pre-2011 CPUs. A **wheelhouse** fills those upstream holes so `pipx install data-boar` works without a local toolchain — **and** is today the **only** channel for the `boar_fast_filter` Rust accelerator (PyPI `data-boar` wheel is `py3-none-any` with zero compiled extensions).

Two **orthogonal** packaging tracks must not be confused:

| Track | ABI model | What the wheelhouse / release matrix must publish |
| ----- | --------- | ------------------------------------------------- |
| **`boar_fast_filter`** (our Rust/PyO3 ext) | **abi3-py38** (`rust/boar_fast_filter/Cargo.toml`) | **ONE** `cp38-abi3` wheel per `(libc × arch)` — serves **all** CPython **3.8+**. **Do not** emit per-`cpXXX` wheels for this extension. **Not distributed on PyPI today.** Tracked as [#782](https://github.com/DataBoar/data-boar/issues/782) / **GAP-001**. |
| **Third-party compiled deps** (numpy, pandas, scipy, scikit-learn, pydantic-core, cryptography, pillow, …) | **Not** abi3 (stable ABI) for the scientific / ML stack we care about | **Per-`cpXXX`:** `cp312` + `cp313` + `cp314` (+ **`cp314t`** free-threaded / no-GIL where hosted), each × `(manylinux/glibc \| musllinux/musl)` × `(x86_64 \| arm64)`. Wheelhouse priority = **fill upstream gaps** and **x86-64-v1** rebuilds where PyPI baseline is too high. |

The first hosted seed (2026-07-12) proved **HTTPS + `--find-links`** for **one** gap artifact (`scikit-learn` `cp314` musllinux). The **x86-64-v1** release (2026-07-29) is the first **full dependency-closed** slice for x86_64. On **2026-07-30** the same tag gained **10× `cp314t`** free-threaded cells (see below) — **56** assets total.

**CI gating note:** `cp314` remains **signal-only** in CI gating (compat / foresight), not a hard release gate. The wheelhouse still **builds and hosts** `cp314` (+ `cp314t`) cells so musl/no-AVX hosts on 3.14 (GIL) and free-threaded foresight hosts do not fall back to source builds.

---

## Decision

Use a phased wheelhouse distribution model (same direction tracked in #1182 comments):

1. **GitHub Releases assets** (immediate HTTPS seed path) — **live for x86-64-v1**.
2. **GitHub Pages + CDN** (`simple/` index path).
3. **R2/S3 static index** as scalable mirror.

### Matrix axes (four dimensions)

```text
{cp312, cp313, cp314, cp314t}
  × {manylinux (glibc), musllinux (musl)}
  × {x86_64, arm64}
  × {CPU baseline: x86-64-v1 for GIL cells where needed; cp314t = upstream/default ISA (not v1)}
```

Plus, separately:

```text
boar_fast_filter:
  · cp38-abi3 × {manylinux, musllinux} × {x86_64, arm64}   # GIL 3.8+ — does NOT load on free-threaded
  · cp314-cp314t × {manylinux, musllinux} × x86_64         # dedicated free-threaded build (maturin --interpreter python3.14t)
```

**libc vs CPU baseline are orthogonal.** Container musl on an AVX laptop proves musl, not v1. Metal **alpine-emachines** (Celeron 900) proves both. **`cp314` and `cp314t` are not interchangeable** (`SOABI=cpython-314-…` vs `cpython-314t-…`).

### ABI rules (non-negotiable)

1. **`boar_fast_filter` → abi3 only** — one wheel per `(manylinux|musllinux) × (x86_64|arm64)`; never per-`cpXXX` ([#782](https://github.com/DataBoar/data-boar/issues/782) / **GAP-001**).
2. **Third-party compiled deps → per-CPython tag** — fill upstream gaps; v1 rebuilds use gated builds (`popcnt=0` on numpy baseline).
3. **`--find-links` adds an index; it does not prefer.** Identical filenames to PyPI mean step 1 alone can still install upstream AVX wheels. **Required user contract:** offline `--force-reinstall` for numpy/scipy/scikit-learn/pandas, then `pipx inject` for `boar_fast_filter` — documented in [TROUBLESHOOTING.md](../TROUBLESHOOTING.md) and release `README.md`.

### Hosted release — x86-64-v1 (verified 2026-07-29)

| Field | Value |
| ----- | ----- |
| Site repo | **`DataBoar/data-boar-site`** |
| Tag | **`wheelhouse-x86-64-v1-2026-07-29`** |
| Release URL | <https://github.com/DataBoar/data-boar-site/releases/tag/wheelhouse-x86-64-v1-2026-07-29> |
| Assets | **56** wheels + `SHA256SUMS` + `README.md` (install + verification en_US / pt_BR) — original **46** GIL/v1 cells + **10× `cp314t`** (2026-07-30); includes `mariadb` on both libcs × cp312/313/314 |
| Offline proof | Operator re-downloaded; checksums matched (incl. 3 new glibc `mariadb` wheels); clean-container offline install |

### Free-threaded / no-GIL — `cp314t` cells (added 2026-07-30)

Ten wheels on the same release tag for CPython **3.14 free-threaded** (`python3.14t`, PEP 703). Operator already refreshed the **site-repo release description**; this plan records the measured matrix and CPU-contract decision.

| Package | manylinux | musllinux | Upstream / build note |
| ------- | --------- | --------- | --------------------- |
| **numpy** 2.5.1 | ✅ | ✅ | Upstream publishes cp314t (15/15 variants measured upstream) |
| **scipy** 1.18.0 | ✅ | ✅ | Upstream publishes cp314t (10/10) |
| **pandas** 3.0.5 | ✅ | ✅ | Upstream publishes cp314t (10/10) |
| **scikit-learn** 1.9.0 | ✅ | ✅ | Upstream: manylinux **4** variants; **musllinux = 0 for every variant** — musl cell **built here from source** (`SK_OK`, **10 325 434** bytes) |
| **boar_fast_filter** 0.1.0 | ✅ `cp314-cp314t` | ✅ `cp314-cp314t` | Built with **maturin `--interpreter python3.14t`**, one wheel per libc. The release **`cp38-abi3` does not load** on free-threaded. |

**`popcnt` measured (2026-07-30):**

| Wheel | popcnt | CPU contract |
| ----- | ------ | ------------ |
| numpy **cp314t** | **1477** | Requires **x86-64-v2+** (not a v1 baseline rebuild) |
| scipy / pandas / sklearn **cp314t** | **0** | No popcnt in those trees (measured) |

**Operator decision (recorded):** free-threaded cells **do not** need an x86-64-v1 baseline rebuild. The min-spec host (Celeron 900, 2 cores, 2009) gains nothing from real parallelism and is not a container free-threaded target. The two sets coexist with **declared CPU contracts**: GIL **`cp312`/`cp313`/`cp314`** = v1 / `popcnt=0` (Celeron-safe); **`cp314t`** = parallelism on v2+ hardware.

**ABI:** `cp314` `SOABI=cpython-314-…` vs `cp314t` `SOABI=cpython-314t-…` — **not interchangeable**.

### Install command (verified on metal — musl example)

`--find-links` accepts a **local folder**, a **direct `.whl` URL**, or an **HTML links page** — **not** a GitHub release page. Download wheels first:

```bash
TAG=wheelhouse-x86-64-v1-2026-07-29
mkdir -p ~/wheelhouse-v1
gh release download "$TAG" --repo DataBoar/data-boar-site \
  --pattern '*musllinux*' --pattern '*-none-any.whl' --dir ~/wheelhouse-v1

export TMPDIR="${TMPDIR:-/var/tmp/data-boar-build}"
mkdir -p "$TMPDIR"

pipx install data-boar --pip-args="--find-links $HOME/wheelhouse-v1"
pipx runpip data-boar install --no-index --find-links $HOME/wheelhouse-v1 \
  --force-reinstall numpy scipy scikit-learn pandas
pipx inject data-boar boar_fast_filter --pip-args="--no-index --find-links $HOME/wheelhouse-v1"
```

Full verification steps (`.so` size, `objdump popcnt`, `_ML_AVAILABLE`, `--demo` traps): release `README.md` and [TROUBLESHOOTING.md](../TROUBLESHOOTING.md) §x86-64-v1.

### Proof runs

| Run | musl | x86-64-v1 (no AVX) | Notes |
| --- | ---- | ------------------ | ----- |
| Seed `wheelhouse-2026-07-12` (Alpine container on AVX host) | ✅ | ❌ not exercised | Proved single-wheel `--find-links` for sklearn gap only |
| **`wheelhouse-x86-64-v1-2026-07-29`** (metal Celeron 900, Alpine) | ✅ | ✅ | **26** `--demo` findings, `_ML_AVAILABLE=True`; 13 ML-path findings |
| **`--demo` matrix 1.7.4.post10** (10 cells) | ✅ void-musl + Alpine cp312/313/314 | ✅ alpine-emachines metal | See [OS_COMPATIBILITY_TESTING_MATRIX.md](../ops/OS_COMPATIBILITY_TESTING_MATRIX.md) §Tier 3.6 |

### PEP 503 index trap (record before building `simple/`)

Hosting a **`simple/`** index **alone** does **not** remove the two-step install while PyPI remains reachable with **same version + same platform tag**:

- Our numpy and PyPI numpy are both **`2.5.1`** with the same manylinux/musllinux tag → **version tie**.
- **Tie-breaker:** PEP 440 **local version** segment — e.g. **`2.5.1+x86v1`** sorts above public **`2.5.1`** and still satisfies `numpy==2.5.1` (`==` ignores local segment).
- **`--extra-index-url` without local versions** merges candidate lists; it does **not** guarantee the wheelhouse wheel wins.

**Operator decision:** ship **`+x86v1`** (or equivalent) **together with** the index — not index-first expecting a one-liner.

### Build decisions (versioned here — full runbook may stay in operator vault)

**Machine-readable source of truth:** [`scripts/wheelhouse/recipe-manifest.yaml`](../../scripts/wheelhouse/recipe-manifest.yaml). CI loads pins from that file only ([#1379](https://github.com/DataBoar/data-boar/issues/1379)). Tables below are human mirrors — if prose and manifest disagree, **fix the manifest and update prose**.

Three decisions that make v1 builds work (from release `README.md`):

1. **`-Dcpu-baseline=none -Dcpu-dispatch=none`** on the numpy meson build.
2. **`--no-build-isolation`** on `pip wheel` — without it, `-C setup-args` never reach meson and the wheel matches PyPI byte-for-byte.
3. **System OpenBLAS** (`apk add openblas-dev` / `dnf install openblas-devel`), never PyPI `scipy-openblas` — distro builds use `DYNAMIC_ARCH`.

**Container base:** `manylinux_2_28` for glibc (numpy 2.5 requires gcc ≥ 10.3; `manylinux2014` toolchain is too old). Aligns with RHEL 7 / CentOS 7 Docker-only stance in Troubleshooting.

Publication gate: build **aborts** if numpy baseline contains any `popcnt` instruction.

### CI — recipe guaranteed, not only documented (#1379)

Documented ≠ guaranteed. Without CI, a silent recipe regression ships a wheel that **installs** and then `Illegal instruction`s on the client. Poisoned signature (measured twice): `_multiarray_umath.so` ≈ **10.7 MB / popcnt=1453** vs correct ≈ **5.1 MB / popcnt=0**.

| Trigger | What runs | Why |
| ------- | --------- | --- |
| **PR / push** touching `scripts/wheelhouse/**`, this PLAN, or the workflow | Connector/C checksum + **canary** `musl` × `cp312` (~10–25 min) | Full matrix ≈ **1 h** (scipy ≈ 70%) — not every PR |
| **Weekly cron** + `workflow_dispatch` `scope=full` | All `musl\|glibc` × `cp312/313/314` cells in parallel | Catches cross-cell drift without blocking day-to-day PRs |

Workflow: [`.github/workflows/wheelhouse-recipe.yml`](../../.github/workflows/wheelhouse-recipe.yml). Scripts: [`scripts/wheelhouse/`](../../scripts/wheelhouse/). Hard-fail gates (ported from vault `build-v1-*.sh`): `popcnt == 0`, umath `.so` size `< 8_000_000`, scipy has no `libscipy_openblas`, Connector/C sha256 matches the manifest.

### `mariadb` (extra `sql-community`) — reproducible glibc recipe (#1367)

PyPI publishes **no** `mariadb` wheels on any platform — sdist only. Every `.[sql-community]` install compiles from source and needs MariaDB Connector/C headers on the host. This is **universal** (not musl-specific, not min-spec) and hits the **open-core / free** tier.

**musl x86_64** was already buildable (Alpine ships a compatible `mariadb-connector-c-dev`) and published. **glibc** blocked on `manylinux_2_28` because the image ships Connector/C **3.1.11** while the Python driver requires **≥ 3.3.1**.

#### Path chosen by measured elimination (2026-07-29)

| Option | Verdict | Why |
| ------ | ------- | --- |
| Base `manylinux_2_34` / AlmaLinux 9 | **Dead** | Ships `mariadb-connector-c-devel` **3.2.6**; driver still needs **≥ 3.3.1**. Raising the glibc floor would cost reach and would **not** fix the version gap. |
| Official MariaDB repo via `curl \| bash` | **Rejected** | Unverified remote script inside the chain that produces a distributable artifact. |
| **Build Connector/C from source** (pinned tarball + checksum) | **Chosen** | Auditable inputs; no third-party package repo in the build chain. |

#### Pinned inputs (exact — do not “upgrade casually”)

Canonical file: [`scripts/wheelhouse/recipe-manifest.yaml`](../../scripts/wheelhouse/recipe-manifest.yaml) key `mariadb_connector_c` (CI checksum job reads that file, not this table).

| Field | Value |
| ----- | ----- |
| Source tarball | <https://github.com/mariadb-corporation/mariadb-connector-c/archive/refs/tags/v3.4.6.tar.gz> |
| **sha256** | `27b57790896b7464e1b87fb29bad49e31ee36fdb6942e5c86284c6af9630be0e` |
| Container base | `quay.io/pypa/manylinux_2_28_x86_64` |
| cmake flags | `-DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX=/usr/local -DWITH_SSL=OPENSSL -DWITH_UNIT_TESTS=OFF -DWITH_EXTERNAL_ZLIB=ON -DCMAKE_POLICY_VERSION_MINIMUM=3.5` |

Then: `pip wheel --no-deps --no-binary mariadb mariadb` per `cp312` / `cp313` / `cp314`, `auditwheel repair --plat manylinux_2_28_x86_64`, publication gate `objdump` (no forbidden ISA).

#### Trap — embedded zlib vs modern CMake

The **bundled** zlib inside Connector/C declares `cmake_minimum_required` older than 3.5. Modern CMake rejects that with: `Compatibility with CMake < 3.5 has been removed`.

- **`-DWITH_EXTERNAL_ZLIB=ON`** uses system zlib and avoids the failure — and reduces what gets embedded in the wheel.
- **`-DCMAKE_POLICY_VERSION_MINIMUM=3.5`** remains a safety net for any leftover ancient submodules.

#### Tag gain — wheel reaches below the build base

`auditwheel` reported the repaired wheel needs only **glibc 2.17**, not 2.28. Final platform tag:

```text
manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64
```

So the wheel reaches **farther** than the build image — including RHEL 7–class glibc floors that [TROUBLESHOOTING.md](../TROUBLESHOOTING.md) marks as unsupported for **native product install**. That is a packaging reach win for this cell, not a change to the product’s supported-install story.

#### Verification (real DB, not compile-only)

Clean-container offline install + connect to **lab-mariadb** from `deploy/lab-smoke-stack`:

```text
MARIADB OK | driver 1.1.14 | lab_customers = 5
```

`objdump` gate executed — no forbidden instructions. The three glibc wheels are on **`wheelhouse-x86-64-v1-2026-07-29`**; `SHA256SUMS` updated; operator re-download matched all three checksums. Release now **46 assets / ~470 MB** with `mariadb` complete on both libcs × cp312/313/314.

Operator build script (vault reference, not required in-repo): `no-avx-toolkit/scripts/build-v1-mariadb-glibc.sh`.

### Coverage matrix — `mariadb` 1.1.14 (wheelhouse vs PyPI gap)

PyPI: **no wheels anywhere**. Wheelhouse fills cells below.

| | musllinux | manylinux (glibc) |
| --- | :---: | :---: |
| **x86_64** cp312/313/314 | ✅ published | ✅ published (#1367 recipe) |
| **aarch64** cp312/313/314 | ❌ gap | ❌ gap — same fix path under [#1366](https://github.com/DataBoar/data-boar/issues/1366) |

#1367 records the **glibc x86_64 recipe**; it does **not** close until aarch64 is decided (tracked on #1366).

---

## Anti-link-dead gate

**Satisfied for x86-64-v1 (2026-07-29):** release verified, checksums re-checked, offline install proven. User-facing URLs updated in:

- `docs/TROUBLESHOOTING.md` (+ `.pt_BR.md`)
- `docs/ops/OS_COMPATIBILITY_TESTING_MATRIX.md` (+ `.pt_BR.md`)

Future releases must repeat verify-before-link for new tags.

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
| 7 | Post-hosting docs rollout in Troubleshooting/matrix with stable URL (**x86-64-v1**) | ✅ ([#1365](https://github.com/DataBoar/data-boar/issues/1365)) |
| 7b | Pin reproducible `mariadb` glibc build (Connector/C from source) + publish cp312/313/314 | ✅ ([#1367](https://github.com/DataBoar/data-boar/issues/1367) — recipe; aarch64 → [#1366](https://github.com/DataBoar/data-boar/issues/1366)) |
| 7c | CI rebuilds recipe from manifest; hard-fail objdump / size / openblas / Connector/C checksum | ✅ ([#1379](https://github.com/DataBoar/data-boar/issues/1379)) |
| 8 | Expand arm64 slice + hosted PEP 503 `simple/` index with **`+x86v1`** local versions | ⬜ |
| 9 | Optional: copy full build runbook from vault into `docs/ops/` | ⬜ |

---

## Acceptance criteria

- [x] Site release exists with tag `wheelhouse-2026-07-12` (seed).
- [x] Site release exists with tag **`wheelhouse-x86-64-v1-2026-07-29`** (full x86_64 v1 slice).
- [x] Real two-step install + `boar_fast_filter` inject documented with verified URL.
- [x] Alpine musl + **metal v1** proof (`pipx` + `--demo` ≥ 20 findings, `_ML_AVAILABLE=True`).
- [x] `PLANS_HUB` and `PLANS_TODO` synchronized.
- [x] Troubleshooting / OS compatibility matrix URLs live (anti-link-dead satisfied).
- [x] Plan documents pan-ABI rules + **fourth CPU baseline axis** + PEP 503 local-version trap.
- [x] `boar_fast_filter` non-distribution on PyPI recorded.
- [x] `mariadb` glibc x86_64 recipe pinned (tarball URL + sha256 + cmake flags) and wheels published (#1367).
- [x] CI executes recipe from `recipe-manifest.yaml` with hard-fail gates (#1379).
- [ ] `mariadb` aarch64 both libcs (#1366).
- [ ] arm64 wheelhouse + `simple/` index (#1182 remainder).

---

## Historical seed reference (`wheelhouse-2026-07-12`)

Single-wheel URL (sklearn cp314 musllinux gap only — **does not** fix v1 numpy):

```bash
pipx install data-boar \
  --pip-args="--find-links https://github.com/DataBoar/data-boar-site/releases/download/wheelhouse-2026-07-12/scikit_learn-1.9.0-cp314-cp314-musllinux_1_2_x86_64.whl"
```

Superseded for production musl/v1 paths by **`wheelhouse-x86-64-v1-2026-07-29`**.
