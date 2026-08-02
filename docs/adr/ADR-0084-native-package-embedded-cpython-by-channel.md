# ADR 0084 — Native package: embed CPython by channel (Enterprise vs community)

- **Date (UTC):** 2026-08-02
- **Authors:** Fabio Leitao
- **Deciders:** Fabio Leitao

## Status

Proposed

### Status history

- 2026-08-02 — Proposed (born Proposed per ADR-0045 / Phase 1 T1; records operator decision on [#1406](https://github.com/DataBoar/data-boar/issues/1406); promotes to Accepted when operator accepts). Unblocks nfpm design [#1403](https://github.com/DataBoar/data-boar/issues/1403) only after this record is Accepted and the plan row is synced — **this ADR does not ship nfpm**.

## Context

Native OS packages (deb/rpm/apk/… — tracked under [#1403](https://github.com/DataBoar/data-boar/issues/1403)) must answer **whose Python interpreter** runs the product **before** any nfpm manifest is written. The choice changes package size, build matrix, maintenance, and — decisive for Enterprise — **whether free-threaded CPython (`cp314t` / no-GIL) is reachable on that channel**.

Layer-1 vendored wheels (numpy, pandas, scipy, scikit-learn) are **not** `abi3`; they pin to an exact CPython minor. Only `boar_fast_filter` is `cp38-abi3` across minors. A native package that vendors layer 1 is therefore locked to **one** minor at build time.

No distribution packages `python3.14t` in the field posture that motivated [#1406](https://github.com/DataBoar/data-boar/issues/1406). Depending on distro `python3` makes **`cp314t` structurally unreachable** on that channel. Measured no-GIL benefit and finding parity: [#1398](https://github.com/DataBoar/data-boar/issues/1398). Delivering a “native Enterprise” channel that cannot run no-GIL repeats the second-class delivery class documented for containers in [#1399](https://github.com/DataBoar/data-boar/issues/1399) by another door.

Options considered in #1406:

| Option | Summary |
| ------ | ------- |
| **(a) Embed CPython** | Ship interpreter under product prefix (same idea as the container image). |
| **(b) Distro `python3`** | Small package; upstream-friendly; **no no-GIL**. |
| **(c) Rebuild on postinst** | Rejected — kills air-gap. |

Container extras inventory ([#1401](https://github.com/DataBoar/data-boar/issues/1401)) and release integrity ([#856](https://github.com/DataBoar/data-boar/issues/856) / build-identity plans) already track artifact contents. An embedded interpreter is an artifact component and must enter those scopes when (a) is implemented — **not** left as tribal knowledge.

### License / commercial protection (mandatory clause)

**Embedding `cp314t` does not grant Enterprise scale by itself.** Commercial protection of the no-GIL / multi-thread scale path remains the **existing tier worker caps and accelerator gates** from the licensing matrix ([#551](https://github.com/DataBoar/data-boar/issues/551)):

- `scan_max_workers_pro` / `scan_max_workers_enterprise` (and related tier tables)
- **`OPEN_MODE_WORKER_CAP = 2`** (Community / open mode) with **fail-closed** enforcement
- **`pro_prefilter_accel`** (Pro+ / paid accelerator entitlement)

Community capped at **2 workers** does **not** harvest free-threaded scale even if the binary tree contains `cp314t`. The interpreter is a **delivery substrate**; entitlement remains **cap + feature gates**, not “presence of freethreaded CPython on disk.”

Related governance: [ADR 0027](ADR-0027-licensing-mode-default-and-fail-closed.md) (fail-closed licensing posture where applicable), [ADR 0064](ADR-0064-open-core-vs-commercial-boundary.md) (open-core vs commercial boundary), [ADR 0073](ADR-0073-version-scheme-octet-maturity-and-roadmap.md) (version / maturity lines), [ADR 0083](ADR-0083-rust-regex-stage-superset-accept-form-b.md) (paid/accelerated regex path vs Community refuse-and-warn).

## Decision

1. **Channel (a) — native / Enterprise / air-gapped:** **Embed CPython** in the native package (layout under a product-owned prefix such as `/usr/lib/data-boar/`, exact path TBD in the nfpm slice). Provide **`cp314` and `cp314t`** so no-GIL is **reachable on any target distro** in this channel. Build matrix is **`(libc × arch)`**, not “every distro minor.” Correction invariant for layer-1 wheels becomes a **structural** property of the embed (byte-identical stack per build cell), not hope that distro numpy matches.

2. **Channel (b) — community / distro-upstream:** **Deferred.** When pursued, that channel **explicitly does not offer no-GIL**; each build documents the exact CPython minor. It must not be marketed as equivalent to the Enterprise native channel.

3. **Option (c)** remains **rejected** (air-gap incompatible).

4. **Commercial protection clause (normative):** Entitlement for scale / accelerator remains **worker caps + `pro_prefilter_accel` (#551)** — **not** the mere presence of embedded `cp314t`. Shipping the interpreter **must not** leak Enterprise capacity to Community.

5. **Artifact inventory scopes (when (a) is implemented):**
   - **`EXTRAS_MANIFEST` / packaging inventory lineage from [#1401](https://github.com/DataBoar/data-boar/issues/1401):** the embedded interpreter (version, ABI tag / freethreaded flag, install prefix) is in scope alongside optional extras.
   - **Integrity / release manifest:** the embedded interpreter files participate in the integrity baseline / release manifest the same way other behaviour-critical artifact roots do (legitimate package upgrade re-baseline already exists; package **revision** vs upstream version edge remains a follow-up called out in #1406 — not reimplemented here).

6. **Ordering:** **No nfpm / #1403 implementation** until this ADR is Accepted (or the operator explicitly waives in a later record) and [PLAN_NATIVE_PACKAGES.md](../plans/PLAN_NATIVE_PACKAGES.md) carries the same decision. This PR records the decision only.

## Consequences

- Enterprise native packaging can target no-GIL without waiting for distros to ship `python3.14t`.
- Package size grows (~150–300 MB class per #1406); distro-proper upstream of the **Enterprise** embed is not a goal.
- Community/upstream path, if ever opened, stays honest about **no no-GIL**.
- #1403 may proceed to nfpm design **after** acceptance of this ADR + plan sync — still a separate implementation PR.
- Licensing tests and claims must continue to prove **caps**, not “freethreaded binary ⇒ Enterprise.”

## References

- [#1406](https://github.com/DataBoar/data-boar/issues/1406) — decision issue (this ADR)
- [#1403](https://github.com/DataBoar/data-boar/issues/1403) — native packages / nfpm (blocked until decision)
- [#1398](https://github.com/DataBoar/data-boar/issues/1398) — no-GIL measurement
- [#1401](https://github.com/DataBoar/data-boar/issues/1401) — EXTRAS_MANIFEST / check-extras
- [#1399](https://github.com/DataBoar/data-boar/issues/1399) — container delivery gap class
- [#551](https://github.com/DataBoar/data-boar/issues/551) — worker caps / tier matrix
- [PLAN_NATIVE_PACKAGES.md](../plans/PLAN_NATIVE_PACKAGES.md)
- [PLAN_PACKAGING_EXTRAS.md](../plans/PLAN_PACKAGING_EXTRAS.md)
