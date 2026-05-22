# Dependabot: Pygments CVE-2026-4539 (upstream patch pending)

**Last triage:** **2026-05-22** (wave **#656** / issue **#427**).

**Status (2026-05-22):** **Resolved on `main`.** **`pygments` 2.20.0** is on PyPI and pinned in **`pyproject.toml`** (`>=2.20.0`) and **`uv.lock`**. **`pip-audit`** / Dependabot should no longer flag **CVE-2026-4539** at this floor. Re-check after each **pygments** release if new advisories appear.

---

## Historical context (pre-2.20.0)

**`pip-audit`** and GitHub **Dependabot** flagged **pygments** at **2.19.2** with **CVE-2026-4539** (inefficient regex in **`AdlLexer`**, local-access / ReDoS class issue).

**Why we could not bump earlier:** PyPI’s latest release was **2.19.2** — no newer version resolved the advisory until **2.20.0** (2026-03-29).

**Residual risk (operator judgment):** Data Boar uses **Pygments** for **syntax highlighting** in CLI/UX paths, not for untrusted remote lexer selection in typical deployments.

## If a new Pygments advisory appears

1. Raise **`pygments`** floor in **`pyproject.toml`** to the patched release.
1. Run **`uv lock`**, **`uv export --no-emit-package pyproject.toml -o requirements.txt`**, **`.\scripts\check-all.ps1`**.
1. Merge; re-run **`pip-audit`** (CI **Audit** job) or **`uv run pip-audit`** locally.

**Optional GitHub UI:** Maintainers may **dismiss** stale alerts with **`patch_unavailable`** and a comment linking this doc — **recheck** after each **pygments** release on PyPI.

**Related:** [SECURITY.md](../SECURITY.md), [DEPENDABOT_PYOPENSSL_SNOWFLAKE.md](DEPENDABOT_PYOPENSSL_SNOWFLAKE.md).

**Cadence:** On each **Band A order –1** pass and at least **quarterly** — see **PLANS_TODO.md** *Every order –1 pass* and *Quarterly blocked-dependency checkpoint*.
