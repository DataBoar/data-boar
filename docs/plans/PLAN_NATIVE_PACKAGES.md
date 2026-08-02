# Plan: Native OS packages — interpreter ownership and nfpm gate (#1406 / #1403)

<!-- plans-hub-summary: Native/Enterprise embeds CPython (cp314t reachable; libc×arch); community/upstream deferred without no-GIL; commercial protection = worker caps (#551) not interpreter presence; blocks nfpm #1403 until ADR-0084 Accepted. -->

**Status:** In progress
**Date:** 2026-08-02
**Authors:** Fabio Leitao (operator); Cursor executor
**Priority:** H1 (packaging / Enterprise air-gap channel)
**GitHub:** [#1406](https://github.com/DataBoar/data-boar/issues/1406) `[P1][1.8.x][packaging][decision]` · **Blocked until decision:** [#1403](https://github.com/DataBoar/data-boar/issues/1403) (nfpm) · **Related:** [#1398](https://github.com/DataBoar/data-boar/issues/1398) · [#1401](https://github.com/DataBoar/data-boar/issues/1401) · [#551](https://github.com/DataBoar/data-boar/issues/551)
**Related:** [ADR-0084](../adr/ADR-0084-native-package-embedded-cpython-by-channel.md) · [ADR-0027](../adr/ADR-0027-licensing-mode-default-and-fail-closed.md) · [ADR-0064](../adr/ADR-0064-open-core-vs-commercial-boundary.md) · [ADR-0073](../adr/ADR-0073-version-scheme-octet-maturity-and-roadmap.md) · [ADR-0083](../adr/ADR-0083-rust-regex-stage-superset-accept-form-b.md) · [PLAN_PACKAGING_EXTRAS.md](PLAN_PACKAGING_EXTRAS.md)

**Synced with:** [PLANS_TODO.md](PLANS_TODO.md)

---

## Problem

Before writing an nfpm (or equivalent) manifest for native packages (#1403), the project must decide **whose CPython** runs inside the package. Layer-1 wheels are minor-pinned (not abi3). Distros do not ship `python3.14t`. Depending on distro Python makes **no-GIL structurally unreachable** on the native channel — a second-class Enterprise delivery path (same class of failure as container extras gaps, different door).

---

## Decision (recorded in ADR-0084)

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

### Artifact inventory (when (a) is implemented)

| Surface | Scope addition |
| ------- | -------------- |
| **EXTRAS_MANIFEST / #1401 lineage** | Embedded interpreter: version, ABI / freethreaded flag, install prefix |
| **Integrity / release manifest** | Interpreter files in baseline; package **revision** vs upstream label edge noted in #1406 (follow-up — do not reimplement upgrade re-baseline) |

Cross-link: container extras remain mount-based ([PLAN_PACKAGING_EXTRAS.md](PLAN_PACKAGING_EXTRAS.md)); native embed is a **separate** delivery channel with the same honesty about inventory.

---

## Execution steps

| Step | Scope | Status |
| ---- | ----- | ------ |
| **0** | ADR-0084 Proposed + this plan + PLANS_TODO + `plans_hub_sync` | ✅ (docs-only; closes #1406 when merged) |
| **1** | Operator accepts ADR-0084 (Status → Accepted) | ⬜ |
| **2** | nfpm / #1403 design + manifest (embeds CPython for channel a) | ⬜ **blocked** until step 1 |
| **3** | Wire embedded interpreter into EXTRAS_MANIFEST + integrity surfaces | ⬜ with #1403 implementation |
| **4** | Optional channel (b) docs if/when community upstream is pursued | ⬜ deferred |

---

## Out of scope (this docs slice)

- **No nfpm**, no packaging scripts, no binary embed in this PR.
- No change to runtime worker-cap enforcement code (already owned by #551 lineage).

---

## Acceptance (#1406)

- [x] Decision in **ADR** (ADR-0084 Proposed; Accepted = operator promote)
- [x] Plan updated **before** any nfpm
- [x] EXTRAS_MANIFEST + integrity scope called out for embedded interpreter
- [x] Channel (b) deferred and documented as **no no-GIL**
- [x] Commercial clause: caps + `pro_prefilter_accel`, not interpreter presence
- [ ] ADR Accepted by operator
- [ ] #1403 unblocked for implementation PR
