# Plan: Windows CI enablement (`windows-latest`) — #1427

<!-- plans-hub-summary: Add GitHub Actions windows-latest job (pytest + native pip/pipx + --demo smokes); unblocks MSI/winget #1467; documents tested vs declared Windows; lists .ps1 not exercisable in CI. -->
<!-- plans-hub-related: PLAN_NATIVE_PACKAGES.md, PLAN_QUICKSTART.md -->

**Status:** Pending (plan scaffold — implementation not started)
**Date:** 2026-08-17
**Authors:** Fabio Leitao (operator); Cursor executor
**Priority:** **`[H1][U1]`** [P1] milestone **v1.8.0** / **1.8.x** packaging spine
**GitHub:** [#1427](https://github.com/DataBoar/data-boar/issues/1427) (canonical)
**Unblocks:** [#1467](https://github.com/DataBoar/data-boar/issues/1467) (Windows MSI + winget) · narrative hardening in [PLAN_NATIVE_PACKAGES.md](PLAN_NATIVE_PACKAGES.md) step **5**
**Sibling (same class, separate issue — do not mix):** [#1425](https://github.com/DataBoar/data-boar/issues/1425) (macOS / Homebrew CI–install path)
**Related docs / ADR:** [ADR-0023](../adr/ADR-0023-primary-windows-dev-workstation.md) (if present; else primary-Windows workstation ops) · [OS_COMPATIBILITY_TESTING_MATRIX.md](../ops/OS_COMPATIBILITY_TESTING_MATRIX.md) · [#1112](https://github.com/DataBoar/data-boar/issues/1112) (Windows native quickstart) · [#1406](https://github.com/DataBoar/data-boar/issues/1406) ✅ (interpreter ownership — **not** a blocker for this CI slice)

**Synced with:** [PLANS_TODO.md](PLANS_TODO.md)

---

## Problem

The product **declares** OS-independent / Windows support and ships a large PowerShell surface, but **GitHub Actions never runs on Windows** (`windows-latest` / `windows-2022` count = **0** in `.github/workflows/`). Linux-only CI cannot prove the native install path that ICP / packaging stories assume.

Without a green Windows job:

- MSI / winget ([#1467](https://github.com/DataBoar/data-boar/issues/1467)) cannot honestly claim a tested runtime path.
- Operators rely on manual guides instead of automated regression.
- Failures on Windows stay **unknown until a human hits them**.

---

## Goal (MVP — not the full matrix)

Add **minimum viable** Windows validation on every PR / `main` push that matters for packaging confidence:

1. Job on **`windows-latest`** with **at least one** supported Python version.
2. **Native install smoke** (`pip` / `pipx` — no Docker) aligned with what [#1112](https://github.com/DataBoar/data-boar/issues/1112) documents (or will document).
3. **`--demo` smoke:** start → produce findings → exit cleanly.
4. Document that Windows is **tested**, not only **declared**.
5. Explicit inventory of **critical `.ps1` scripts that CI will not run** (no silent “we test PowerShell” claim).

### Out of scope (this plan)

| Item | Tracker / note |
| ---- | -------------- |
| macOS CI / Homebrew | [#1425](https://github.com/DataBoar/data-boar/issues/1425) — separate issue |
| MSI / winget / MSIX build | [#1467](https://github.com/DataBoar/data-boar/issues/1467) — **after** this plan’s AC are green |
| Full Python matrix on Windows (3.12+3.13+3.14) | Optional follow-up; MVP = **one** version |
| Running all ~138 `.ps1` in CI | Impossible / low ROI; inventory + selective later |
| Self-hosted Windows runner | Not required for MVP |

---

## Acceptance criteria (from #1427)

- [ ] Workflow job Windows **green on `main`**
- [ ] Native install smoke (`pip` / `pipx`) **passing**
- [ ] `--demo` smoke **passing** on Windows
- [ ] Compatibility / ops docs updated: Windows **tested** (not only declared)
- [ ] Critical `.ps1` **not** exercisable in CI listed **explicitly** in this plan or linked ops doc
- [ ] This plan linked from [PLANS_TODO.md](PLANS_TODO.md) + [PLANS_HUB.md](PLANS_HUB.md) (`plans_hub_sync.py --write`)

---

## Relationship to other plans

| Plan / issue | Relationship |
| ------------ | ------------ |
| [PLAN_NATIVE_PACKAGES.md](PLAN_NATIVE_PACKAGES.md) | Step **5** = this work; step **6** (#1467) blocked until green |
| [#1467](https://github.com/DataBoar/data-boar/issues/1467) | **Downstream** consumer — MSI/winget must not ship before Windows CI exists |
| [#1425](https://github.com/DataBoar/data-boar/issues/1425) | **Sibling** platform gap (macOS); do not combine workflows in one PR unless operator asks |
| [#1112](https://github.com/DataBoar/data-boar/issues/1112) | Quickstart Windows nativo — smoke steps should match documented install; CI may **drive** doc truth if #1112 lags |
| [#1406](https://github.com/DataBoar/data-boar/issues/1406) | Interpreter ownership **decided** (ADR-0084); CI Windows validates **dev/pip path**, not embedded MSI payload yet |

---

## Proposed design

### Workflow shape (preferred)

| Option | Pros | Cons |
| ------ | ---- | ---- |
| **A. New job in `ci.yml`** (`needs` / parallel with Linux test) | One PR surface; gatekeeper sees Windows | Lengthens `ci.yml`; Windows minutes bill |
| **B. Dedicated `windows-ci.yml`** | Isolates flaky Windows; easier `paths` filters later | Extra workflow; must still be required check |

**Default for implementation:** **A** for MVP (single required check name), unless `ci.yml` size or timeout forces **B**.

### Job outline (MVP)

```text
runs-on: windows-latest
steps:
  - checkout
  - setup-python (one of 3.12 / 3.13 — pick what Linux already trusts most)
  - install uv (or pip) per repo convention
  - uv sync / pip install -e ".[dev]" (or documented equivalent)
  - pytest: start with a **known-green subset** if full suite OOMs/times out; expand once green
  - install-smoke: pipx or pip install from the checkout wheel / editable
  - demo-smoke: python -m … --demo (exact flag from USAGE / main.py — pin in plan when implementing)
```

**Cost control:** Prefer **one** Python; `fail-fast: false` only if matrix expands later. Cache `uv` / pip on Windows when stable.

### PowerShell honesty

Maintain a short table (fill during implementation):

| Script / class | In CI Windows? | Reason |
| -------------- | -------------- | ------ |
| `check-all.ps1` | ⬜ TBD | May call Linux-only tools / Pester / long gate |
| `lab-completao-*.ps1` | ❌ | Needs lab SSH / private manifest |
| `private-git-sync.ps1` | ❌ | Private remotes / VeraCrypt |
| Core product CLI (`main.py` / entrypoints) | ✅ | Primary MVP |

Update this table in the **same PR** that adds the job so docs cannot claim silent PS coverage.

### Docs touchpoints

| Doc | Change |
| --- | ------ |
| [OS_COMPATIBILITY_TESTING_MATRIX.md](../ops/OS_COMPATIBILITY_TESTING_MATRIX.md) (and/or sibling Windows note) | State that **GHA `windows-latest`** exercises install + demo (+ pytest subset) |
| QUICKSTART / #1112 surfaces | Align install smoke with documented commands |
| This plan AC checkboxes | Flip to ✅ when merged |

Do **not** add markdown links from **external-tier** product docs into `docs/plans/` (audience rule).

---

## Execution steps

| Step | Scope | Status |
| ---- | ----- | ------ |
| **0** | This plan + `PLANS_TODO` row + `plans_hub_sync` + cross-link from `PLAN_NATIVE_PACKAGES` | ⬜ (this PR / docs slice) |
| **1** | Spike: run full or subset pytest on a Windows GHA branch; record failures / timeouts | ⬜ |
| **2** | Land `windows-latest` job (install deps + pytest MVP) green on PR | ⬜ |
| **3** | Native `pip`/`pipx` install smoke | ⬜ |
| **4** | `--demo` smoke | ⬜ |
| **5** | Docs: tested vs declared + `.ps1` exclusion table | ⬜ |
| **6** | Merge to `main`; confirm required check green; close #1427 | ⬜ |
| **7** | Hand off to [#1467](https://github.com/DataBoar/data-boar/issues/1467) / `PLAN_NATIVE_PACKAGES` step 6 | ⬜ after AC |

---

## Risks and mitigations

| Risk | Mitigation |
| ---- | ---------- |
| Full pytest too slow / flaky on Windows | Subset first; promote to fuller suite later |
| Path / line-ending / encoding bugs | Treat as **product bugs** to fix, not “skip Windows” |
| Minute cost | Single Python; optional `paths:` later; do not add macOS in same job |
| Overclaim on PowerShell | Explicit exclusion table in plan / ops |

---

## Done when

#1427 AC boxes are checked, this plan’s steps **0–6** are ✅, `PLAN_NATIVE_PACKAGES` step **5** is ✅, and #1467 is unblocked for **implementation planning** (not auto-started).
