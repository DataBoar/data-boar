# Plan: Windows CI enablement (`windows-latest`) — #1427

<!-- plans-hub-summary: Add GitHub Actions windows-latest job (pytest + native pip/pipx + --demo smokes); unblocks MSI/winget #1467; documents tested vs declared Windows; lists .ps1 not exercisable in CI. -->
<!-- plans-hub-related: PLAN_NATIVE_PACKAGES.md, PLAN_QUICKSTART.md -->

**Status:** In progress (implementation on branch — merge closes #1427)
**Date:** 2026-08-17
**Authors:** Fabio Leitao (operator); Cursor executor
**Priority:** **`[H1][U1]`** [P1] milestone **v1.8.0** / **1.8.x** packaging spine
**GitHub:** [#1427](https://github.com/DataBoar/data-boar/issues/1427) (canonical)
**Unblocks:** [#1467](https://github.com/DataBoar/data-boar/issues/1467) (Windows MSI + winget) · narrative hardening in [PLAN_NATIVE_PACKAGES.md](PLAN_NATIVE_PACKAGES.md) step **5**
**Sibling (same class, separate issue — do not mix):** [#1425](https://github.com/DataBoar/data-boar/issues/1425) (macOS / Homebrew CI–install path)
**Related docs / ADR:** [OS_COMPATIBILITY_TESTING_MATRIX.md](../ops/OS_COMPATIBILITY_TESTING_MATRIX.md) · [#1112](https://github.com/DataBoar/data-boar/issues/1112) (Windows native quickstart) · [#1406](https://github.com/DataBoar/data-boar/issues/1406) ✅ (interpreter ownership — **not** a blocker for this CI slice)

**Synced with:** [PLANS_TODO.md](PLANS_TODO.md)

---

## Problem

The product **declares** OS-independent / Windows support and ships a large PowerShell surface, but **GitHub Actions never ran on Windows**. Linux-only CI cannot prove the native install path that ICP / packaging stories assume.

---

## Goal (MVP — shipped in this PR)

1. Job **`test-windows`** on **`windows-latest`** (Python **3.12**).
2. **Native install smoke:** `pip install .` + `data-boar --version` (pipx not required for MVP; `pip` is the native path exercised).
3. **Headless demo smoke:** `scripts/demo_headless.py` (cross-platform equivalent of `scripts/demo.sh --headless` — scan + report, no uvicorn hang).
4. Docs: Windows **tested** in [OS_COMPATIBILITY_TESTING_MATRIX.md](../ops/OS_COMPATIBILITY_TESTING_MATRIX.md).
5. Explicit **`.ps1` not in CI** table below.

### Out of scope (unchanged)

macOS CI (#1425), MSI/winget (#1467), full Python matrix on Windows, running all `scripts/*.ps1` in CI.

---

## Acceptance criteria

- [x] Workflow job Windows on `windows-latest` (merge proves green on `main`)
- [x] Native install smoke (`pip install .`)
- [x] Headless demo smoke (`scripts/demo_headless.py`)
- [x] Compatibility matrix documents Windows as **CI-tested**
- [x] Critical `.ps1` **not** exercisable in CI listed below
- [x] Plan + hub / `PLANS_TODO` wired

---

## PowerShell honesty (CI does **not** run these)

| Script / class | In CI Windows? | Reason |
| -------------- | -------------- | ------ |
| `check-all.ps1` / `check-all.sh` | ❌ | Full local gate; Linux job covers pytest/pre-commit separately |
| `lab-completao-*.ps1` / Maestro wrappers | ❌ | Lab SSH / private manifest / operator LAN |
| `private-git-sync.ps1` | ❌ | Private remotes / VeraCrypt / pCloud |
| `es-find.ps1` / Everything wrappers | ❌ | Windows-dev-PC only; not GHA |
| Homelab / Bitwarden / social collect scripts | ❌ | Secrets + interactive sessions |
| Product CLI (`main.py` / `data-boar`) | ✅ | pytest + pip smoke + `demo_headless.py` |

---

## Execution steps

| Step | Scope | Status |
| ---- | ----- | ------ |
| **0** | Plan + `PLANS_TODO` + hub + cross-link | ✅ |
| **1** | Spike / land job | ✅ (this PR) |
| **2** | `windows-latest` + pytest | ✅ |
| **3** | Native `pip` install smoke | ✅ |
| **4** | Headless demo smoke | ✅ |
| **5** | Docs + `.ps1` table | ✅ |
| **6** | Merge + close #1427 | ⬜ |
| **7** | Hand off #1467 | ⬜ after merge |

---

## Implementation notes

- Workflow: `.github/workflows/ci.yml` job **`test-windows`**; Slack failure notify **`needs`** includes it.
- Guards: `tests/test_github_workflows.py` (`test_ci_yml_has_windows_test_job`); `tests/test_cli_demo.py` (`test_demo_headless_script_completes`).
- Full `--demo` (dashboard) is **not** used in CI (would hang on uvicorn); headless scan is the AC-equivalent smoke.
