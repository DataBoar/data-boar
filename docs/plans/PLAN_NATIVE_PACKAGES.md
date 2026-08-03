# Plan: Native OS packages — interpreter ownership and nfpm (#1406 / #1403)

<!-- plans-hub-summary: Native/Enterprise embeds CPython (cp314t); ADR-0084 Accepted; nfpm foundation (#1403) generates deb/rpm/apk/pacman + connector subpackages from EXTRAS_MANIFEST; commercial protection = worker caps (#551), not interpreter presence. -->

**Status:** In progress
**Date:** 2026-08-02
**Authors:** Fabio Leitao (operator); Cursor executor
**Priority:** H1 (packaging / Enterprise air-gap channel)
**GitHub:** [#1406](https://github.com/DataBoar/data-boar/issues/1406) `[P1][1.8.x][packaging][decision]` · [#1403](https://github.com/DataBoar/data-boar/issues/1403) (nfpm foundation) · **Related:** [#1398](https://github.com/DataBoar/data-boar/issues/1398) · [#1401](https://github.com/DataBoar/data-boar/issues/1401) · [#551](https://github.com/DataBoar/data-boar/issues/551) · [#1404](https://github.com/DataBoar/data-boar/issues/1404) (xbps)
**Related:** [ADR-0084](../adr/ADR-0084-native-package-embedded-cpython-by-channel.md) · [ADR-0027](../adr/ADR-0027-commercial-tier-boundaries-licensing-docs-and-future-jwt-claims.md) · [ADR-0064](../adr/ADR-0064-license-enforcement-additive-model.md) · [ADR-0073](../adr/ADR-0073-version-scheme-octet-maturity-and-roadmap.md) · [ADR-0083](../adr/ADR-0083-rust-regex-stage-superset-accept-form-b.md) · [PLAN_PACKAGING_EXTRAS.md](PLAN_PACKAGING_EXTRAS.md)

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
| **1** | core + detection stack + `boar_fast_filter` (abi3) | **vendored + pinned** (wheelhouse) |
| **2** | libc / OpenSSL / zlib / libffi / tesseract / p7zip | **`Depends:` of the distro** (nfpm overrides per packager) |
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
| **2** | nfpm foundation (#1403): generated deb/rpm/apk/pacman manifests + connector subpackages + embed metadata | 🔄 in progress |
| **3** | Wire embedded interpreter into runtime integrity / CI package build | ⬜ follow-up (not this foundation slice) |
| **4** | Lab metal validation matrix (5 hosts) + xbps (#1404) | ⬜ deferred / separate issues |

---

## Out of scope (foundation #1403 PR)

- Real package build in CI and lab metal install matrix.
- **xbps** / Void (`#1404`).
- Debian proper / Alpine aports / AUR official sponsorship.
- Changing runtime worker-cap enforcement (already owned by #551 lineage).

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
- [x] Connector subpackages **generated** from `EXTRAS_MANIFEST` (mssql / nosql / shares / compressed / dataformats / richmedia)
- [x] Deterministic generator + test that fails on drift
- [x] Layer-2 Depends via packager overrides; no `Depends: python3` (embed prefix)
- [x] Embedded interpreter registered in EXTRAS_MANIFEST schema
- [x] Commercial protection: presence of `cp314t` does not unlock Enterprise
- [ ] CI build + metal validation (next slices)
