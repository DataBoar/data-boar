# Plan: Bandit (Python security linter)

**Status:** Completed
**Date:** 2026-03-26
**Authors:** Fabio Leitao
**Priority:** H0
**Depends on:** ADR-0037

**Synced with:** [PLANS_TODO.md](PLANS_TODO.md)

## Purpose

**Bandit** finds common security anti-patterns (assert in “production”, `try/except/pass`, subprocess usage, weak crypto hints, naive SQL string detection) that **unit tests may not cover**. It **complements** **CodeQL**, **Semgrep**, and **Ruff**—different engines, different rules.

**Config:** `[tool.bandit]` in **`pyproject.toml`** (`exclude_dirs`, `skips`, `level` / `confidence` **MEDIUM**, `recursive`, `aggregate`). **CI:** `.github/workflows/ci.yml` job **Bandit (strict)** runs **`uv run bandit -r . -c pyproject.toml -ll -ii`** (fails the merge on MEDIUM+ severity with MEDIUM+ confidence per the CLI; `pyproject` still supplies excludes and skips).

---

## Phases

| Phase | Content                                                                                                                                                                                                                                    | Status    |
| ----- | -------                                                                                                                                                                                                                                    | ------    |
| **1** | Add **`bandit`** to **`[dependency-groups] dev`** (`uv add --dev bandit`); document local command.                                                                                                                                         | ✅ Done    |
| **2** | Add **`[tool.bandit]`** in **`pyproject.toml`**: `exclude_dirs`, **`skips`** (**B608** vetted identifier-built SQL), `level`/`confidence` **MEDIUM**, `recursive`, `aggregate`. CI job **strict** (`-r .`, `-ll`, `-ii`). | ✅ Done    |
| **3** | Triage **low** findings (`-i` or full report): fix, **`# nosec Bxxx`** with one-line justification, or extend **`skips`** / per-file config after review. Optionally raise CI to **low** once clean.                                       | ⬜ Pending |
| **4** | Update **`.cursor/skills/quality-sonarqube-codeql/SKILL.md`** and **`.cursor/rules/quality-sonarqube-codeql.mdc`** when running Bandit after security-sensitive edits (habit, not always full suite).                                      | 🔄 Ongoing |

---

## Commands

```bash
# Matches CI Bandit (strict) job
uv run bandit -r . -c pyproject.toml -ll -ii

# Full triage (includes low; noisier)
uv run bandit -r . -c pyproject.toml -i
```

**Scope:** Aligns with Ruff `extend-exclude` legacy dirs; **`tests/`** excluded from Bandit paths by default (add only if you want to lint test code for `assert` / mocks).

---

## Relationship to Semgrep / CodeQL

| Tool        | Role                                                                                               |
| ----        | ----                                                                                               |
| **CodeQL**  | Deep semantic queries; GitHub Security tab.                                                        |
| **Semgrep** | Registry rules + fast PR signal (`p/python`).                                                      |
| **Bandit**  | AST plugin style; good for **assert**, **subprocess**, **try/except/pass**, heuristic SQL strings. |

---

## Last updated

2026-04-28 — CI strict (`-r .`, `-ll`, `-ii`); `pyproject` baseline MEDIUM + recursive; plan alinhado.
