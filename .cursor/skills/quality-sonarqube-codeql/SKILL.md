---
name: quality-sonarqube-codeql
description: Apply when implementing or reviewing Python/markdown for quality and security. Ensures SonarQube-style rules (S3981, S3776, S4423, S5706, S1192) and CodeQL-relevant patterns are followed, and that the project quality tests are run and pass.
---

# Quality: SonarQube and CodeQL (enforcement and tests)

Use this skill when implementing or reviewing **Python** or **markdown** changes that can affect static analysis (SonarQube) or code scanning (CodeQL). The project encodes quality rules in **tests**; this skill ensures we follow them and run the right tests after edits.

## When to apply

- Implementing or refactoring Python (api, core, config, connectors, report, tests).
- Adding or changing markdown (README, docs, SECURITY, CONTRIBUTING).
- Code review or PR preparation for quality/security.
- After any change that might introduce S3981, S3776, bare except, weak TLS, or CodeQL findings.

## What to do

### 1. Avoid SonarQube violations (tests enforce these)

| Rule      | Avoid                                                       | Use instead                                                                             |
| --------  | --------                                                    | -------------                                                                           |
| **S3981** | `len(...) >= 0`                                             | `len(...) == 0` or `len(...) > 0` (or drop redundant check)                             |
| **S3776** | High cognitive complexity in a single function              | Extract helpers; keep functions in `tests/test_sonarqube_python.py` under complexity 15 |
| **S4423** | `ssl.create_default_context()` without minimum TLS          | Set `ctx.minimum_version = ssl.TLSVersion.TLSv1_2` (or stronger)                        |
| **S5706** | Bare `except:`                                              | `except Exception:` or specific exception types                                         |
| **S1192** | Repeated string literals for routes/response/template names | Named constants (see api/routes, report code)                                           |
| **S5856** | Session_id regex without `re.ASCII`                         | Use `re.ASCII` (or equivalent) when using `\w`                                          |

### 2. Avoid CodeQL-relevant patterns

- **Secrets:** Do not log API keys, passwords, or connection strings (see SECURITY.md, docs/SECURITY.md).
- **Injection:** Use parameterized queries and safe APIs; never concatenate user input into SQL or shell commands.
- **Crypto:** Prefer TLS 1.2+ and standard libraries; avoid weak or deprecated algorithms.
- **Path (py/path-injection):** Reuse **`api.routes._real_file_under_out_dir_str`** / **`_report_output_dir_resolved`**: `normpath(join(base_path, filename))`, then `fullpath.startswith(base_path)`, then `isfile` (CodeQL’s documented barrier). Heatmaps: **`_heatmap_png_response`** (bytes) instead of `FileResponse(path=...)`. Allowlist basenames (`_REPORT_FILENAME_PATTERN`, `_HEATMAP_FILENAME_PATTERN`). After path changes in `api/routes.py`, run **`uv run pytest tests/test_report_path_safety.py -v -W error`**.

### 3. Markdown: points of attention

When adding or editing markdown, avoid common lint issues that the test or SonarQube report:

- **MD022:** Blank line before and after each heading.
- **MD026:** No trailing punctuation (`.` `:` `;` `!` `?`) in `#` headings.
- **MD032:** Blank lines around lists (fix script applies this).
- **MD041:** File must start with a top-level heading (`# Title`), not a blank line or front matter only.
- **MD024:** No duplicate heading text in the same file; use unique text per section (e.g. "What to do (Ruff):" not repeated "What to do:").
- **MD060:** Tables aligned (run fix script); use consistent fenced code markers (all ``` or all ~~~).

After `fix_markdown_sonar.py`, restore **semantic numbering** (1. 2. 3.) in step lists by hand when the list is a real sequence.

### 4. Run Ruff and quality tests after edits

After changing Python or markdown:

**Windows:** Prefer **`.\scripts\check-all.ps1`** (full gate) or **`.\scripts\lint-only.ps1`** (runs **`pre-commit run --all-files`**) per **check-all-gate** — matches the **CI lint** job.

**Once per clone:** **`uv run pre-commit install`** so **`git commit`** runs the same hooks locally.

```bash
# Same bundle as CI lint job (.pre-commit-config.yaml): Ruff, plans-stats --check, markdown, pt-BR, commercial guard
uv run pre-commit run --all-files

# SonarQube-style + security (Python)
uv run pytest tests/test_sonarqube_python.py tests/test_security.py -v -W error

# Report/heatmap path containment (CodeQL py/path-injection; after api/routes path edits)
uv run pytest tests/test_report_path_safety.py -v -W error

# Markdown (if .md changed)
uv run python scripts/fix_markdown_sonar.py
uv run pytest tests/test_markdown_lint.py -v -W error

# Bandit (CI strict `-ll -ii`; optional but recommended after security-sensitive Python edits — same gate as CI). Low triage: `docs/plans/completed/PLAN_BANDIT_SECURITY_LINTER.md`.
uv run bandit -c pyproject.toml -r api core config connectors database file_scan report main.py -ll -q

# Mypy (dev-only, soft defaults in pyproject.toml; optional signal after large refactors — not a CI gate yet)
uv run mypy api core
```

Before opening a PR, run the full suite:

```bash
uv run pytest -v -W error
```

Fix any failure; do not commit with failing quality tests. **CI** (`.github/workflows/ci.yml`): **`lint`** = **`pre-commit run --all-files`**; **`test`** = full pytest; **Bandit** + **pip-audit** = separate jobs. **CodeQL**: `.github/workflows/codeql.yml`. **Semgrep**: `.github/workflows/semgrep.yml`. Address CodeQL findings in the Security tab.

### 5. When adding new SonarQube or CodeQL rules

Keep adding tests so we avoid regressions without breaking the app:

1. **Add a test** that enforces the new rule (in the appropriate test module).
1. **Update the rule** (`.cursor/rules/quality-sonarqube-codeql.mdc`) and this skill with the rule id and guidance.
1. **Update docs/TESTING.md** so the new rule is listed in the quality section.
1. If **`ci.yml`** **lint** job or **`.pre-commit-config.yaml`** changes materially, update **`tests/test_github_workflows.py`** (`test_ci_lint_job_runs_pre_commit_all_files`) so workflow guards stay accurate.

The full suite runs with `-W error` (pyproject.toml addopts and CI); all tests must stay green and warning-free during development so behaviour stays correct.

## Alignment with project

- **Rule:** `.cursor/rules/quality-sonarqube-codeql.mdc` – same scope (Python + markdown); apply that rule when editing those files.
- **Tests:** `tests/test_sonarqube_python.py`, `tests/test_security.py`, `tests/test_report_path_safety.py` (after `api/routes` path changes), `tests/test_markdown_lint.py`; see **docs/TESTING.md** for the full list.
- **CI:** **`ci.yml`** runs **pre-commit** (lint job), **pytest** (test job), **Bandit**, **pip-audit**; **Semgrep** and **CodeQL** are separate workflows. Keeping required checks green and fixing scanner findings is required for merge.
