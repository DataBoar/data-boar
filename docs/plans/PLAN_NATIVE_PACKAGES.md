# Plan: Native OS packages — interpreter ownership and nfpm (#1406 / #1403 / #1437)

<!-- plans-hub-summary: Native/Enterprise embeds CPython (cp314t); ADR-0084 Accepted; nfpm foundation + CI build (#1437) for deb/rpm x86-64 glibc from wheelhouse; commercial protection = worker caps (#551), not interpreter presence. -->

**Status:** In progress
**Date:** 2026-08-02
**Authors:** Fabio Leitao (operator); Cursor executor
**Priority:** H1 (packaging / Enterprise air-gap channel)
**GitHub:** [#1406](https://github.com/DataBoar/data-boar/issues/1406) · [#1403](https://github.com/DataBoar/data-boar/issues/1403) (foundation ✅) · [#1437](https://github.com/DataBoar/data-boar/issues/1437) (CI build) · **Related:** [#1182](https://github.com/DataBoar/data-boar/issues/1182) · [#1401](https://github.com/DataBoar/data-boar/issues/1401) · [#551](https://github.com/DataBoar/data-boar/issues/551) · [#1404](https://github.com/DataBoar/data-boar/issues/1404) (xbps)
**Related:** [ADR-0084](../adr/ADR-0084-native-package-embedded-cpython-by-channel.md) · [PLAN_WHEELHOUSE_DISTRIBUTION.md](PLAN_WHEELHOUSE_DISTRIBUTION.md) · [PLAN_PACKAGING_EXTRAS.md](PLAN_PACKAGING_EXTRAS.md)

**Synced with:** [PLANS_TODO.md](PLANS_TODO.md)

---

## Problem

Before writing an nfpm (or equivalent) manifest for native packages (#1403), the project must decide **whose CPython** runs inside the package. Layer-1 wheels are minor-pinned (not abi3). Distros do not ship `python3.14t`. Depending on distro Python makes **no-GIL structurally unreachable** on the native channel — a second-class Enterprise delivery path (same class of failure as container extras gaps, different door).

---

## Decision (recorded in ADR-0084 — Accepted)

| Channel | Interpreter | no-GIL (`cp314t`) | Notes |
| ------- | ----------- | ----------------- | ----- |
| **(a) Native / Enterprise / air-gapped** | **Embed CPython** under product prefix | **Reachable** on any distro | Matrix: `(libc × arch)`; correction invariant structural |
| **(b) Community / distro upstream** | Distro `python3` | **Not offered** (document per build minor) | **Deferred**; must not be marketed as (a) |
| **(c) postinst rebuild** | N/A | N/A | **Rejected** (breaks air-gap) |

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
| **4** | Lab metal validation matrix (5 hosts) + apk/musl/arm64 + xbps (#1404) | ⬜ deferred / separate issues |

---

## CI build (#1437)

Workflow: [`.github/workflows/native-packages.yml`](../../.github/workflows/native-packages.yml)

1. `scripts/native-nfpm-populate-staging.sh` — `uv python install 3.14.6+freethreaded` → `/usr/lib/data-boar/python3.14t`; install product + `requirements.txt`; apply hosted wheelhouse tag `wheelhouse-x86-64-v1-2026-07-29` (cp314t cells); **fail-closed** if assets are not downloadable.
2. `nfpm package` for **deb** + **rpm** (core `data-boar`; x86-64 glibc).
3. Install-smoke: debian bookworm (`.deb`) + Rocky 9 (`.rpm`) run `/usr/lib/data-boar/.../python3.14t -m data_boar --version`.
4. Upload `native-packages-x86_64-glibc` artifacts.

**Out of scope for #1437:** apk/musl, arm64, pacman metal, five-host matrix, xbps, signed repo publish.

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
- [ ] Full metal matrix / apk / arm64 / xbps (later slices)
