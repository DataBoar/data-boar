# Plan: Bandit (Python security linter)

**Status:** Completed (all implementation phases; Phase 4 habit doc in `.cursor/` remains ongoing)
**Date:** 2026-03-26
**Authors:** Fabio Leitao
**Priority:** H0
**Depends on:** ADR-0037

**Synced with:** [PLANS_TODO.md](../PLANS_TODO.md)

## Purpose

**Bandit** finds common security anti-patterns (assert in “production”, `try/except/pass`, subprocess usage, weak crypto hints, naive SQL string detection) that **unit tests may not cover**. It **complements** **CodeQL**, **Semgrep**, and **Ruff**—different engines, different rules.

**Config:** `[tool.bandit]` in **`pyproject.toml`** (`exclude_dirs`, `skips`, `level` / `confidence` **MEDIUM**, `recursive`, `aggregate`). **CI:** `.github/workflows/ci.yml` job **Bandit (strict)** runs **`uv run bandit -r . -c pyproject.toml -ll -ii`** (fails the merge on MEDIUM+ severity with MEDIUM+ confidence per the CLI; `pyproject` still supplies excludes and skips).

---

## Phases

| Phase | Content                                                                                                                                                                                                                                    | Status    |
| ----- | -------                                                                                                                                                                                                                                    | ------    |
| **1** | Add **`bandit`** to **`[dependency-groups] dev`** (`uv add --dev bandit`); document local command.                                                                                                                                         | Done    |
| **2** | Add **`[tool.bandit]`** in **`pyproject.toml`**: `exclude_dirs`, **`skips`** (empty; **B608** handled with inline **`# nosec B608`** on identifier-built SQL), `level`/`confidence` **MEDIUM**, `recursive`, `aggregate`. CI job **strict** (`-r .`, `-ll`, `-ii`). | Done    |
| **3** | Triage **low** findings (`-i` or full report): fix, **`# nosec Bxxx`** (pragma line = **test id only**—no trailing words; Bandit otherwise logs spurious “Test in comment” warnings), or extend **`skips`** after review. **Do not** raise CI to `-i` until counts collapse—noise stays acceptable vs token cost. | Done    |
| **4** | Update **`.cursor/skills/quality-sonarqube-codeql/SKILL.md`** and **`.cursor/rules/quality-sonarqube-codeql.mdc`** when running Bandit after security-sensitive edits (habit, not always full suite).                                      | Ongoing |

---

## Phase 3 — Low-severity triage (closed 2026-05-14)

**Strict gate (unchanged):** `uv run bandit -r . -c pyproject.toml -ll -ii` → **0 issues** (MEDIUM severity + MEDIUM confidence and above).

**Inclusive scan (`-i`) snapshot** on ~31k LOC (same excludes as `pyproject.toml`; **`tests/`** and **`db/`** excluded):

| Test ID | Count | Disposition |
| ------- | ----: | ------------- |
| **B110** | 42 | Mostly defensive `try`/`except`/`pass` on optional HTML or metadata paths (`api/routes.py`, report/dashboard helpers). Accepted: swallow keeps UX when enrichment fails; not security boundaries. |
| **B603** / **B404** / **B607** | 13 + 11 + 10 | **`scripts/`** and tooling: `subprocess` with **fixed argv** (`git`, `docker`, interpreters) or operator-controlled paths. Accepted for maintainer-only CLIs; review again if a script starts taking untrusted input. |
| **B608** | 13 | **Medium severity, Low confidence** only below strict gate; production SQL sampling uses connector-vetted identifiers with **`# nosec B608`** on the pragma line only (rationale in module docstring / `sql_connector`). |
| **B105** | 8 | Fixture / template strings (`wrong_pass`, OAuth URL template, HR test labels)—not production secrets. |
| **B112** | 3 | Iterator / scan loops: continue on expected parse gaps. |
| **B101** | 3 | Test-only `assert` (excluded tree still picks some paths—acceptable). |
| **B311** | 3 | Non-crypto `random` use (sampling / fuzz)—acceptable where not used for tokens. |

**Hygiene fixes shipped with this closure:** shortened **`# nosec B608`** / **`# nosec B310`** lines in **`connectors/sql_sampling.py`** and **`utils/notify.py`** so Bandit stops treating trailing comment words as bogus test IDs.

**Cadence:** Re-run **`uv run bandit -r . -c pyproject.toml -i`** after large edits to **`connectors/`**, **`api/`**, or **`scripts/`**, or quarterly; treat new **Medium+Medium** hits as CI blockers immediately.

---

## Commands

```bash
# Matches CI Bandit (strict) job
uv run bandit -r . -c pyproject.toml -ll -ii

# Full triage (includes low; exit code may be non-zero)
uv run bandit -r . -c pyproject.toml -i
```

**Scope:** Aligns with Ruff `extend-exclude` legacy dirs; **`tests/`** excluded from Bandit paths by default (add only if you want to lint test code for `assert` / mocks).

---

## Relationship to Semgrep / CodeQL

| Tool        | Role                                                                                               |
| ----        | ----                                                                                               |
| **CodeQL**  | Deep semantic queries; GitHub Security tab.                                                        |
| **Semgrep** | Registry rules + fast PR signal (`p/python`).                                                      |
| **Bandit**  | AST plugin style; good for **assert**, **subprocess**, `try/except/pass`, heuristic SQL strings. |

---

## Last updated

2026-05-14 — Phase 3 closed: low-severity inventory documented; pragma-line nosec hygiene; strict CI unchanged. Plan archived under **`docs/plans/completed/`**.
