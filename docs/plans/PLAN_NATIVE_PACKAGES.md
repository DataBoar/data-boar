# Plan: Native OS packages — interpreter ownership, nfpm, Void xbps, and Release assets (#1406 / #1403 / #1437 / #1404 / #1408)

<!-- plans-hub-summary: Native/Enterprise embeds CPython (cp314t); ADR-0084 Accepted; Linux nfpm CI (#1437) + Release assets (#1408) + Void xbps overlay (#1404, Podman) + Windows MSI/winget (#1467, blocked by Windows CI #1427 / PLAN_WINDOWS_CI_ENABLEMENT) + macOS Homebrew (#1425); commercial protection = worker caps (#551), not interpreter presence. -->

**Status:** In progress
**Date:** 2026-08-12
**Authors:** Fabio Leitao (operator); Cursor executor
**Priority:** H1 (packaging / Enterprise air-gap channel)
**GitHub:** [#1406](https://github.com/DataBoar/data-boar/issues/1406) · [#1403](https://github.com/DataBoar/data-boar/issues/1403) (foundation ✅) · [#1437](https://github.com/DataBoar/data-boar/issues/1437) (CI build) · [#1408](https://github.com/DataBoar/data-boar/issues/1408) (Release assets) · [#1404](https://github.com/DataBoar/data-boar/issues/1404) (xbps / Podman Void) · **Related:** [#1182](https://github.com/DataBoar/data-boar/issues/1182) · [#1401](https://github.com/DataBoar/data-boar/issues/1401) · [#551](https://github.com/DataBoar/data-boar/issues/551) · [#1405](https://github.com/DataBoar/data-boar/issues/1405) (signed repo) · [#1467](https://github.com/DataBoar/data-boar/issues/1467) (MSI/winget) · [#1425](https://github.com/DataBoar/data-boar/issues/1425) (Homebrew) · [#1427](https://github.com/DataBoar/data-boar/issues/1427) (Windows CI blocker) · [#1478](https://github.com/DataBoar/data-boar/issues/1478) (ADR-0085 brew honesty) · [#1541](https://github.com/DataBoar/data-boar/issues/1541) (this cross-link refresh)
**Related:** [ADR-0084](../adr/ADR-0084-native-package-embedded-cpython-by-channel.md) · [ADR-0085](../adr/ADR-0085-install-priority-ladder.md) · [PLAN_WHEELHOUSE_DISTRIBUTION.md](PLAN_WHEELHOUSE_DISTRIBUTION.md) · [PLAN_PACKAGING_EXTRAS.md](PLAN_PACKAGING_EXTRAS.md) · [PLAN_WINDOWS_CI_ENABLEMENT.md](PLAN_WINDOWS_CI_ENABLEMENT.md) (#1427)

**Synced with:** [PLANS_TODO.md](PLANS_TODO.md)

---

## Problem

Before writing an nfpm (or equivalent) manifest for native packages (#1403), the project must decide **whose CPython** runs inside the package. Layer-1 wheels are minor-pinned (not abi3). Distros do not ship `python3.14t`. Depending on distro Python makes **no-GIL structurally unreachable** on the native channel — a second-class Enterprise delivery path (same class of failure as container extras gaps, different door).

---

## Decision (recorded in ADR-0084 — Accepted)

| Channel | Interpreter | no-GIL (`cp314t`) | Notes |
| ------- | ----------- | ----------------- | ----- |
| **(a) Native / Enterprise / air-gapped** | **Embed CPython** under product prefix | **Reachable** on any distro | Matrix: `(libc × arch)`; correction invariant structural. **Surfaces:** Linux nfpm (**deb/rpm** in CI; apk/pacman/xbps later) · **Windows MSI/winget** ([#1467](https://github.com/DataBoar/data-boar/issues/1467)) · **macOS Homebrew** ([#1425](https://github.com/DataBoar/data-boar/issues/1425)) — see sibling table below |
| **(b) Community / distro upstream** | Distro `python3` | **Not offered** (document per build minor) | **Deferred**; must not be marketed as (a) |
| **(c) postinst rebuild** | N/A | N/A | **Rejected** (breaks air-gap) |

### Sibling native surfaces (same channel-a policy; not Linux-nfpm-only)

| Surface | Tracker | Status (plan view) |
| ------- | ------- | ------------------ |
| **Linux nfpm** (deb/rpm first; apk/pacman later) | [#1403](https://github.com/DataBoar/data-boar/issues/1403) · [#1437](https://github.com/DataBoar/data-boar/issues/1437) · [#1408](https://github.com/DataBoar/data-boar/issues/1408) | Foundation ✅; CI build 🔄; Release attach 🔄; metal matrix deferred |
| **Void xbps** (`void-packages` overlay, runit, Podman) | [#1404](https://github.com/DataBoar/data-boar/issues/1404) | Overlay + generator 🔄; validate in Podman Void (not metal) |
| **Windows MSI + winget** (embed `cp314` / `cp314t`) | [#1467](https://github.com/DataBoar/data-boar/issues/1467) (canonical; #1471 was a dup) | **Planned** — blocked on Windows CI ([#1427](https://github.com/DataBoar/data-boar/issues/1427): no `windows-latest` job yet) |
| **macOS Homebrew** (own tap; formula/cask) | [#1425](https://github.com/DataBoar/data-boar/issues/1425) | **Planned** — cheapest missing consumer path; **no** published formula/cask yet |
| **Install ladder honesty** | [ADR-0085](../adr/ADR-0085-install-priority-ladder.md) · [#1478](https://github.com/DataBoar/data-boar/issues/1478) | Recommend only what exists **today** (`pipx`); native / `brew` are **when published** — do not treat `brew install data-boar` as live |

### Commercial protection (normative)

Embedding `cp314t` **does not** unlock Enterprise scale. Protection remains:

- Tier **worker caps** (`scan_max_workers_pro` / `scan_max_workers_enterprise`)
- **`OPEN_MODE_WORKER_CAP = 2`** (fail-closed) for Community / open mode
- **`pro_prefilter_accel`** (Pro+)

Community at 2 workers does **not** harvest free-threaded scale. See [#551](https://github.com/DataBoar/data-boar/issues/551) and ADR-0084.

### Three packaging layers (#1403)

| Layer | Content | Rule |
| ----- | ------- | ---- |
| **1** | core + detection stack + `boar_fast_filter` (cp314t native) | **vendored + pinned** (wheelhouse `#1182`) |
| **2** | libc / OpenSSL / zlib / libffi / tesseract | **`Depends:` of the distro** (nfpm overrides per packager; no `p7zip*` — `.7z` is optional `py7zr`) |
| **3** | connector extras | **subpackages** generated from `EXTRAS_MANIFEST` |

### Artifact inventory (channel a)

| Surface | Scope addition |
| ------- | -------------- |
| **EXTRAS_MANIFEST / #1401 lineage** | Embedded interpreter: version, ABI / freethreaded flag, install prefix |
| **Integrity / release manifest** | Interpreter files in baseline; package **revision** vs upstream label edge noted in #1406 (follow-up) |

---

## Execution steps

| Step | Scope | Status |
| ---- | ----- | ------ |
| **0** | ADR-0084 Proposed + this plan + PLANS_TODO + `plans_hub_sync` | ✅ (closed #1406) |
| **1** | Operator accepts ADR-0084 (Status → Accepted) | ✅ |
| **2** | nfpm foundation (#1403): generated deb/rpm/apk/pacman manifests + connector subpackages + embed metadata | ✅ (merged #1436) |
| **3** | CI package build (#1437): populate staging with real cp314t + wheelhouse; `nfpm package` deb+rpm; install-smoke; artifacts | 🔄 |
| **3b** | Publish nfpm packages as product Release assets beside SBOMs (#1408); packager names + SHA256SUMS + `native_packages[]`; hand-built PoC `.deb` never uploaded | 🔄 |
| **4** | Lab metal validation matrix (5 hosts) + apk/musl/arm64 | ⬜ deferred / separate issues |
| **4b** | Void xbps overlay (#1404): generated `void-packages` template + runit + Podman validate | 🔄 |
| **5** | Windows CI job (`windows-latest`) so MSI/winget work is testable (#1427) | 🔄 [PLAN_WINDOWS_CI_ENABLEMENT.md](PLAN_WINDOWS_CI_ENABLEMENT.md) — PR in flight; **blocks** #1467 until green on `main` |
| **6** | Windows MSI + winget embed payload (#1467) | ⬜ planned (after #1427) |
| **7** | macOS Homebrew tap (#1425) | ⬜ planned |

Cross-link hygiene for this table: [#1541](https://github.com/DataBoar/data-boar/issues/1541).

---

## CI build (#1437)

Workflow: [`.github/workflows/native-packages.yml`](../../.github/workflows/native-packages.yml)

1. `scripts/native-nfpm-populate-staging.sh` — `uv python install 3.14.6+freethreaded` → `/usr/lib/data-boar/python3.14t`; install product + `requirements.txt`; apply hosted wheelhouse tag `wheelhouse-x86-64-v1-2026-07-29` (cp314t cells); **fail-closed** if assets are not downloadable.
2. `nfpm package` for **deb** + **rpm** (core `data-boar`; x86-64 glibc).
3. Install-smoke: debian bookworm (`.deb`) + Rocky 9 (`.rpm`) run `/usr/lib/data-boar/.../python3.14t -m data_boar --version`.
4. Upload `native-packages-x86_64-glibc` artifacts.

**Out of scope for #1437:** apk/musl, arm64, pacman metal, five-host matrix, xbps, signed repo publish.

---

## Release assets (#1408)

On `release: published` / `created`, `attach-release` uploads the **same** nfpm files that CI just built (deb/rpm/apk/pacman, packager filename convention) plus `SHA256SUMS` and a `release-manifest.json` that lists `native_packages[]`. Air-gap steps: [NATIVE_PACKAGE_RELEASE.md](../ops/NATIVE_PACKAGE_RELEASE.md).

Traps from the hand-built recipe-proof PoC stay in `scripts/native-nfpm-populate-staging.sh`: `DISABLE_SQLALCHEMY_CEXT=1` (not `--no-binary` alone), restore `EXTERNALLY-MANAGED`, normalize modes. Layer 1 overlay is `apply_wheelhouse_v1.sh` (#1182). That PoC `.deb` is **not** a publish candidate.

`SHA256SUMS.asc` lands when `NATIVE_PACKAGE_GPG_PRIVATE_KEY` is set (#1405 key ceremony). Signed repo (#1405) indexes **these** files — no rebuild.

**Out of scope for #1408:** musl/arm64 metal, xbps, inventing a signature, publishing the hand-built recipe-proof `.deb`.

---

## Acceptance (#1406 decision)

- [x] Decision in **ADR** (ADR-0084)
- [x] Plan updated **before** any nfpm
- [x] EXTRAS_MANIFEST + integrity scope called out for embedded interpreter
- [x] Channel (b) deferred and documented as **no no-GIL**
- [x] Commercial clause: caps + `pro_prefilter_accel`, not interpreter presence
- [x] ADR Accepted by operator
- [x] #1403 unblocked for implementation PR

## Acceptance (foundation #1403)

- [x] nfpm manifests for **deb / rpm / apk / archlinux (pacman)** (not xbps)
- [x] Connector subpackages **generated** from `EXTRAS_MANIFEST`
- [x] Deterministic generator + test that fails on drift
- [x] Layer-2 Depends via packager overrides; no `Depends: python3`
- [x] Embedded interpreter registered in EXTRAS_MANIFEST schema
- [x] Commercial protection: presence of `cp314t` does not unlock Enterprise

## Acceptance (CI build #1437)

- [x] Workflow + populate script land in repo (fail-closed; no fake payload path)
- [x] Plan + PLANS_TODO + `plans_hub_sync` updated
- [x] `tests/test_native_nfpm_foundation.py` remains green (generator drift)
- [ ] CI run green: `.deb` + `.rpm` artifacts + install-smoke (debian / Rocky) — verify on the #1437 PR
- [ ] Full metal matrix / apk / arm64 (later slices)

## Acceptance (Release assets #1408)

- [x] Pipeline attaches packages to the product Release with packager filename conventions
- [x] `SHA256SUMS` written in CI; `.asc` only when packaging key secret exists (no fake signature)
- [x] `release-manifest.json` gains `native_packages[]` (SBOM upload must not drop it)
- [x] Layer 1 overlay from hosted wheelhouse (#1182); hand-built PoC `.deb` never uploaded
- [x] `DISABLE_SQLALCHEMY_CEXT=1` + sqlalchemy `*.so` empty + GIL off (populate + smokes)
- [x] `EXTERNALLY-MANAGED` restored in the delivered tree
- [x] Staging modes normalized (independent of umask 027)
- [x] Air-gap verify docs EN + pt-BR
- [x] #1405 consumes the same files (documented; no rebuild)

## Acceptance (Void xbps #1404)

- [x] `void-packages` template generated from `EXTRAS_MANIFEST` (same subpackage map as #1403)
- [x] Runit service `/etc/sv/data-boar/run`; product paths do not call `systemctl`
- [x] Template stays in this repo (`packaging/void/`); upstream `void-packages` merge out of scope
- [x] Podman Void validate script (`--show` glibc/musl; `--build` fail-closed without staging)
- [x] Docs EN + pt-BR (install-by-distro + ops runbook)
- [ ] `./xbps-src pkg data-boar` green in Podman Void with populated staging (operator / CI show is parse-only)
- [ ] Finding-count parity vs deb/rpm/apk on the reference corpus after install
- [ ] musl `--build` when a musl staging tree exists (do not reuse glibc bytes)
- [x] Target **1.8.x**
