# Cross-platform script pairing (Windows `.ps1` ↔ Linux/macOS `.sh`)

**Português (Brasil):** [SCRIPTS_CROSS_PLATFORM_PAIRING.pt_BR.md](SCRIPTS_CROSS_PLATFORM_PAIRING.pt_BR.md)

## Purpose

Some **developer gates** and **thin wrappers** exist in **two forms**: **PowerShell** (historical primary workstation: Windows 11) and **bash** (Linux / macOS, CI-like shells, collaborators). This document is the **contract** to keep them **behaviourally aligned** when either side changes — similar in spirit to **code → English docs → pt-BR docs**, but for **automation entry points**.

**Related:** **`.cursor/rules/repo-scripts-wrapper-ritual.mdc`** (always skim the hub before reinventing shell), **`docs/ops/TOKEN_AWARE_SCRIPTS_HUB.md`**, **`.cursor/skills/token-aware-automation/SKILL.md`**.

## Rules (maintainers + assistants)

1. **Paired scripts:** When you **add** or **change behaviour** (flags, order of steps, exit codes, retry logic) in one member of a pair, update the **sibling** in the **same PR** when practical; if not, add a **tracked TODO** (e.g. `PLANS_TODO.md` row) and link both filenames so the gap is visible.
2. **New gate wrapper:** If you introduce a **new** Windows-first **`scripts/*.ps1`** that operators are expected to run routinely from the repo root, consider whether a **`scripts/*.sh`** twin is warranted for Linux — and vice versa if you add a **Linux-first** **`*.sh`** that Windows contributors would miss.
3. **Not everything is paired:** Lab-only **`*.sh`** (SSH targets), Windows-only **`es-find.ps1`**, and large orchestrators may stay **single-platform**; document that in the hub row or script header instead of inventing a hollow twin.
4. **Canonical behaviour:** The **`.ps1`** remains the **reference** for Windows-first docs strings today; **`.sh`** mirrors **intent** (`uv`, `pre-commit`, `pytest` flags). If behaviour diverges, fix the drift — do not “paper over” with docs-only claims.

## Current paired gates (dev PC)

| Intent | Windows | Linux / macOS |
| ------ | ------- | ------------- |
| Full gate (gatekeeper + plans + pre-commit + pytest) | `scripts/check-all.ps1` | `scripts/check-all.sh` |
| Lint / hooks only | `scripts/lint-only.ps1` | `scripts/lint-only.sh` |
| Pytest subset (`-Path` / `-Keyword`) | `scripts/quick-test.ps1` | `scripts/quick-test.sh` |
| Pre-commit + full pytest (no gatekeeper / no plans-stats) | `scripts/pre-commit-and-tests.ps1` | `scripts/pre-commit-and-tests.sh` |

**Note:** `check-all.ps1` calls **`gatekeeper-audit.ps1`**, the **Rust guard** (`cargo fmt` / `check` / `test` under `rust/boar_fast_filter/`), then **`plans-stats.py --write`**, then delegates to **`pre-commit-and-tests.ps1`**. **`check-all.sh`** mirrors that order: PII seeds through **`uv run python scripts/gatekeeper_audit.py`** (no **`pwsh`** dependency — issue **`#560`**), same Rust guard with **`PYO3_USE_ABI3_FORWARD_COMPATIBILITY`**, **`plans-stats.py`**, then **`pre-commit-and-tests.sh`**. The **`pre-commit`** bundle also invokes **`gatekeeper_audit.py`** on each commit alongside the other guards. **`pre-commit-and-tests.*`** skips gatekeeper, Rust, and plans-stats by design; it runs **`tests/security/test_mem_integrity.py`** first (Hypothesis + PyO3), then the full pytest suite with **`--deselect`** on that file so the gate stays explicit without duplicating Hypothesis examples.

## Verification

- **Linux / CI:** `bash -n scripts/<name>.sh` (see **`tests/test_scripts.py`**).
- **Windows:** PowerShell parse checks for **`*.ps1`** in the same test module.
