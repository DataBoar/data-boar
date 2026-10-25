# Plan: Distribution format matrix (Nuitka binary / compiled module / `.pyc`) vs compat corners (#1922)

<!-- plans-hub-summary: Evaluation axis ③: wheel/sdist vs Nuitka onefile/standalone/module vs .pyc across glibc/musl/Win/macOS/FreeBSD/illumos; licensing compile is the gain; D1–D5 not implemented. -->
<!-- plans-hub-related: PLAN_WHEELHOUSE_DISTRIBUTION.md, PLAN_NATIVE_PACKAGES.md, PLAN_SELF_UPGRADE_AND_VERSION_CHECK.md, PLAN_BUILD_IDENTITY_RELEASE_INTEGRITY.md, PLAN_INTEGRITY_HARDENING.md, PLAN_PLUGIN_SDK.md, PLAN_PACKAGING_EXTRAS.md -->

**Status:** Not started (evaluation recorded; **no** Nuitka/product-code spikes)
**Date:** 2026-09-13
**Authors:** Fabio Leitao (operator); Cursor executor (plan capture from GitHub **#1922**)
**Priority:** H1 (packaging / licensing hardening evaluation) · **U2** · GitHub **[P2]**
**GitHub:** [#1922](https://github.com/DataBoar/data-boar/issues/1922) · milestone **v1.8.0**
**Related:** [OS_COMPATIBILITY_TESTING_MATRIX.md](../ops/OS_COMPATIBILITY_TESTING_MATRIX.md) · [PLAN_WHEELHOUSE_DISTRIBUTION.md](PLAN_WHEELHOUSE_DISTRIBUTION.md) · [PLAN_NATIVE_PACKAGES.md](PLAN_NATIVE_PACKAGES.md) · [ADR-0084](../adr/ADR-0084-native-package-embedded-cpython-by-channel.md) · [PLAN_SELF_UPGRADE_AND_VERSION_CHECK.md](PLAN_SELF_UPGRADE_AND_VERSION_CHECK.md) · [PLAN_BUILD_IDENTITY_RELEASE_INTEGRITY.md](PLAN_BUILD_IDENTITY_RELEASE_INTEGRITY.md) · [PLAN_INTEGRITY_HARDENING.md](PLAN_INTEGRITY_HARDENING.md)

**Synced with:** [PLANS_TODO.md](PLANS_TODO.md)

**Independence:** This front is **independent of [#676](https://github.com/DataBoar/data-boar/issues/676)** (private stealth remotes / chmod). Do not mix branches or PRs.

---

## Problem

Existing packaging work already has **two orthogonal axes**:

| Axis | What it answers | Where it lives today |
| ---- | --------------- | -------------------- |
| **① Packaging / ABI** | `libc × packager × arch × Python` (wheels, nfpm, wheelhouse, extras) | [PLAN_WHEELHOUSE_DISTRIBUTION.md](PLAN_WHEELHOUSE_DISTRIBUTION.md), [PLAN_NATIVE_PACKAGES.md](PLAN_NATIVE_PACKAGES.md), [PLAN_PACKAGING_EXTRAS.md](PLAN_PACKAGING_EXTRAS.md) |
| **② Capability / min-spec** | ISA baseline (`x86-64-v1`…`v4`, no-AVX, accel) | Wheelhouse CPU contract + [OS_COMPATIBILITY_TESTING_MATRIX.md](../ops/OS_COMPATIBILITY_TESTING_MATRIX.md) |

Issue **#1922** used the working title `PLAN_COMPAT_MATRIX_MINSPEC.md` for those two axes. **That filename is not in this tree.** Treat **①** + **②** as the existing compat story above; this plan adds **③** only.

**③ Artifact format** — *in what form* the code arrives at the customer. Today the public channel is **always** wheel / sdist via pip / pipx / uv. Candidates under evaluation: Nuitka **`--onefile` / `--standalone`**, Nuitka **`--module`**, and bytecode **`.pyc`**.

This plan **does not** decide to adopt Nuitka. It records research already in **#1922**, the format × corner matrix, and **spikes D1–D5 as next steps only**.

---

## Where the real gain is (and is not)

Raising casual reverse-engineering cost on a **distributed binary** is the point. The public GitHub tree stays **BSD-3-Clause**; compiling does **not** hide source from anyone who clones the repo.

The most concrete product target is **`core/licensing/guard.py`** / **`tier_features.py`**: with Python source on disk, a casual tier bypass is cheap. Compiling **those** modules with Nuitka **`--module`** would raise the bar. A native binary is still **reversible** — more expensive, not immune. Do not claim obfuscation or DRM.

---

## Research already recorded (issue #1922)

Legend for later tables: **E** = evidence in this issue (or dated lab comment on it); **A** = assumption still to test (D1–D5).

| Question | Answer | Class |
| -------- | ------ | ----- |
| Nuitka Win / macOS / Linux | Official support (Nuitka project docs) | **E** |
| Nuitka FreeBSD | Plausible; no formal support list | **A** → **D5** |
| Nuitka Solaris / illumos / OmniOS | No support evidence; conflicts with the already-planned illumos/OmniOS corner | **E** (absence) |
| CPython **cp3.14t** (free-threaded / no-GIL) + Nuitka | Experimental, not ready | **E** — upstream `Nuitka/Nuitka#3062` open since Aug 2024, still open as of May 2026 |
| Call `boar_fast_filter` (Rust / PyO3) | Compatible; standard C-API extension | **E** (architecture; no Data Boar Nuitka build yet) |
| Plugin loader `core/plugins/loader.py` | Compatible, **not** automatic | **E** / **A** — uses `importlib.import_module`; dynamic third-party import inside a standalone binary is a known Nuitka edge → **D2** |
| `core/integrity_anchor.py` hash detection | **Breaks as-is** | **E** — `compute_module_hashes()` hashes individual `.py` via SQLite manifest; compiled artifacts need a redesign → **D3** (design only) |
| License JWT (`core/licensing/verify.py` / `guard.py`) | Compatible (crypto verify, not import-shape) | **E** (architecture) |
| Self-upgrade | N/A until implemented | **E** — [PLAN_SELF_UPGRADE_AND_VERSION_CHECK.md](PLAN_SELF_UPGRADE_AND_VERSION_CHECK.md) **Deferred** since 2026-03-15 |
| In-repo “Robin” specialist | Not vendored (by design) | **E** — specialists are SDK sidecars, not in this tree |
| Version-check / DNSSEC TXT beacon (“Robin Light”) | Trivially compatible | **E** — DNS resolve + string compare |

**Do not** contribute no-GIL work upstream to Nuitka as part of this plan (explicitly out of scope in **#1922**).

---

## Empirical Nuitka measurement (2026-09-13)

A lab host ran an empirical **Python + Nuitka** compile among twelve language/bundler candidates (external experiment comment dated **2026-09-13**, tracked on **#1922**). **Measured** score **3/5** (not a theoretical claim):

| Criterion | Result |
| --------- | ------ |
| Round-trip | Pass |
| Embedded build metadata | Dirty formatting |
| Reproducible build (same source → same hash) | Fail |
| Truly static binary | Fail (still dynamically linked, at least `libc`) |

Languages that compile natively (e.g. FPC / Go in that same experiment) scored **5/5** without special flags.

**Source leak via `strings`:** that finding applied to **Lua** and **TypeScript** bundlers in that experiment, **not** to Python + Nuitka. “No leftover readable Python bytecode” remains consistent with the #1922 write-up. The real Nuitka gaps from that run are **reproducibility** and **fully static linking**, not wholesale source-in-the-binary.

**Impact on D3:** non-reproducibility does **not** kill a **CI-published canonical hash** of the compiled artifact (build once, publish that hash). It **does** weaken independent third-party rebuild verification. Record as a **known limitation**, not a blocker.

---

## Format × corner matrix

**Today’s product path:** wheel / sdist. Other columns are **evaluation**, not shipping channels.

| Format ↓ \ corner → | Linux glibc | Linux musl (Alpine / Void) | Windows | macOS | FreeBSD | illumos / OmniOS |
| ------------------- | ----------- | -------------------------- | ------- | ----- | ------- | ---------------- |
| **Wheel / sdist** (pip / pipx / uv) | **E** — primary documented + CI Linux | **E** / **A** — musllinux wheelhouse cells exist; metal Alpine/Void still ops matrix | **E** — `windows-latest` pytest / pip smoke (#1427 track) | **E** — Homebrew tap host Python (#1425) | **A** — epic **#1171** / ops matrix, not a Nuitka question | **A** — planned platform corner; **not** a Nuitka path (see row below) |
| **Nuitka `--onefile` / `--standalone`** | **E** official Nuitka Linux; **A** product smoke | **A** → **D4** | **E** official Nuitka Windows; **A** product smoke | **E** official Nuitka macOS; **A** product smoke | **A** → **D5** | **E** no Nuitka support evidence — **do not** plan this format for this corner |
| **Nuitka `--module`** (e.g. licensing package) | **A** → **D1** (`pip install` of compiled module) | **A** → **D4** after D1 | **A** → **D1** on Windows when D1 runs | **A** → **D1** on macOS when D1 runs | **A** → **D5** | **E** unsupported (same as standalone) |
| **`.pyc` only** | **A** — cheap bytecode; not a substitute for Nuitka; Phase 9 of self-upgrade still deferred | **A** | **A** | **A** | **A** | **A** — possible if CPython runs; unrelated to Nuitka gap |

**cp314t × Nuitka:** treat **all** Nuitka cells as **not ready** on free-threaded CPython until upstream **#3062** lands. Native-package **channel (a)** still embeds `cp314t` per ADR-0084 **without** requiring Nuitka.

**`boar_fast_filter`:** expected **OK** inside a Nuitka binary that still loads a C-API extension (**E** architecture; **A** until a real build).

---

## Relationship to other plans

| Plan | Boundary |
| ---- | -------- |
| [PLAN_WHEELHOUSE_DISTRIBUTION.md](PLAN_WHEELHOUSE_DISTRIBUTION.md) | Axis **①** wheels; remains the public Python install path unless a later ADR chooses another format |
| [PLAN_NATIVE_PACKAGES.md](PLAN_NATIVE_PACKAGES.md) | Embedded CPython + nfpm / MSI / brew; **not** Nuitka. Commercial scale stays worker caps (#551), not compiler choice |
| [PLAN_SELF_UPGRADE_AND_VERSION_CHECK.md](PLAN_SELF_UPGRADE_AND_VERSION_CHECK.md) | Deferred; in-place upgrade of a Nuitka onefile is a **future** design if self-upgrade ever ships |
| [PLAN_BUILD_IDENTITY_RELEASE_INTEGRITY.md](PLAN_BUILD_IDENTITY_RELEASE_INTEGRITY.md) / [PLAN_INTEGRITY_HARDENING.md](PLAN_INTEGRITY_HARDENING.md) | Integrity today hashes **`.py`**. D3 is a **proposal only** for compiled-artifact hashes |
| [PLAN_PLUGIN_SDK.md](PLAN_PLUGIN_SDK.md) | Dynamic `import_module` → D2 |

---

## Next steps — spikes D1–D5 (**do not implement in this issue**)

All rows stay **⬜ Pending**. No product code, no CI Nuitka job, no upstream Nuitka patches.

| ID | Spike | Status |
| -- | ----- | ------ |
| **D1** | Compile `core/licensing/*` with Nuitka **`--module`**; test **`pip install`** of the result on a supported CPython (GIL). | ⬜ Pending |
| **D2** | Exercise the plugin loader **inside** a Nuitka **`--standalone`** build (third-party / dynamic import edge). | ⬜ Pending |
| **D3** | **Propose** (docs/ADR draft only) a redesign of `integrity_anchor.py` to hash **compiled artifacts**; **do not implement**. Record CI-canonical-hash vs third-party rebuild limitation from the 2026-09-13 measurement. | ⬜ Pending |
| **D4** | Nuitka build on **musl** (Alpine and/or Void). | ⬜ Pending |
| **D5** | Confirm **real** FreeBSD Nuitka support (or document unsupported). | ⬜ Pending |

**Out of scope here:** deciding to ship Nuitka; Nuitka no-GIL upstream; mixing with **#676**.

---

## When implementing later

If a spike lands in a **future** issue: update this file’s tables (**E** vs **A**), this D1–D5 table, [PLANS_TODO.md](PLANS_TODO.md), then `python scripts/plans_hub_sync.py --write` and `python scripts/plans-stats.py --write` when dashboard rows change. Adoption of Nuitka as a **product channel** needs an **ADR** (not this evaluation plan).
