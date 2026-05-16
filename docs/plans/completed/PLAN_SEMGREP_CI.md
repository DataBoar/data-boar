# Plan: Semgrep in CI (OSS ruleset)

**Status:** ✅ **Complete** (archived under `docs/plans/completed/`). Workflow on `main`, tests, docs, Corporate-Entity-C baseline. **Slack:** **`Slack CI failure notify`** watches **`Semgrep`** (and other listed workflows) on upstream **`failure`** when **`SLACK_WEBHOOK_URL`** is set — optional operator smoke: see § below. **Synced with:** [PLANS_TODO.md](../PLANS_TODO.md).

## Purpose

Add **Semgrep** as a **complementary** static scan in GitHub Actions alongside **CodeQL** and optional **SonarQube**. Semgrep is **pattern-based**, good for **custom rules** later and quick feedback on Python anti-patterns. It does **not** replace CodeQL; it adds another lens with different rule authors and heuristics.

**Workflow file:** `.github/workflows/semgrep.yml`. **Reference:** [docs/QUALITY_WORKFLOW_RECOMMENDATIONS.md](../../QUALITY_WORKFLOW_RECOMMENDATIONS.md) §4.

**See also:** [PLAN_BANDIT_SECURITY_LINTER.md](PLAN_BANDIT_SECURITY_LINTER.md) (Bandit in **CI** / `pyproject` — overlapping SQL-string heuristics; we skip **B608** where identifiers are vetted, analogous to the Semgrep exclude above).

---

## Configuration choices

| Choice                                                                                            | Rationale                                                                                                                                                                                                                                                |
| ------                                                                                            | ---------                                                                                                                                                                                                                                                |
| **Ruleset `p/python`**                                                                            | Focused on Python; avoids pulling unrelated language packs.                                                                                                                                                                                              |
| **`--metrics=off`**                                                                               | Disables Semgrep metrics upload (privacy / simplicity for OSS CI).                                                                                                                                                                                       |
| **`--error`**                                                                                     | Fails the job on **blocking** findings so the check is meaningful.                                                                                                                                                                                       |
| **Excluded rule:** `python.sqlalchemy.security.audit.avoid-sqlalchemy-text.avoid-sqlalchemy-text` | **False positives** on our vetted `sqlalchemy.text()` usage where **identifiers** are validated/quoted and **limits** are bound; **CodeQL** and project tests already cover SQL injection surfaces. Revisit if we refactor to Core/ORM expressions only. |

---

## To-dos

| # | To-do                                                                                                                                                                             | Status         |
| - | -----                                                                                                                                                                             | ------         |
| 1 | Add `.github/workflows/semgrep.yml` (container `semgrep/semgrep`, checkout, `semgrep scan` as above).                                                                             | ✅ Done         |
| 2 | Extend `tests/test_github_workflows.py` so the workflow YAML parses and has expected `on` / job shape.                                                                            | ✅ Done         |
| 3 | Update [QUALITY_WORKFLOW_RECOMMENDATIONS.md](../../QUALITY_WORKFLOW_RECOMMENDATIONS.md) §4 to point at the workflow.                                                                 | ✅ Done         |
| 4 | Document in [PLANS_TODO.md](../PLANS_TODO.md) and ops baseline for Corporate-Entity-C.                                                                                                           | ✅ Done         |
| 5 | **Slack on Semgrep failure:** **`Slack CI failure notify`** lists **`Semgrep`** in `workflow_run.workflows` (with **`CI`**, **`Gitleaks`**, **`SBOM`**, **`Dependabot requirements.txt sync`**); live YAML **`.github/workflows/slack-ci-failure-notify.yml`** on **`origin`**, with **private snapshot** **`docs/private/raw_pastes/cursor-incident/slack-ci-failure-notify.yml.old`** for pause drills ([OPERATOR_NOTIFICATION_CHANNELS.md](../../ops/OPERATOR_NOTIFICATION_CHANNELS.md) §4.1.1). | ✅ Done |

---

## Optional operator smoke (Slack path)

To **prove** Slack fires on **Semgrep** (not only on **CI**), use a **throwaway branch** (never merge): e.g. temporarily remove `--exclude-rule …` or add a trivial Semgrep violation, push, open PR, wait for **Semgrep** workflow → **failure**, then confirm **Slack CI failure notify** ran (requires **`.github/workflows/slack-ci-failure-notify.yml`** on the default branch per [OPERATOR_NOTIFICATION_CHANNELS.md](../../ops/OPERATOR_NOTIFICATION_CHANNELS.md) §4.1.1) and the message shows **Semgrep (OSS, Python)** (or the current job `name`) in the first line. Revert the branch. Requires **`SLACK_WEBHOOK_URL`** on the repo.

---

## Optional follow-ups (non-blocking)

- **Custom rules** under `.semgrep/` for Data Boar–specific invariants (e.g. config load must use `safe_load`).
- **Stricter rules:** Add another pack (e.g. supply-chain) in a **separate** job or after triage to avoid blocking `main` unexpectedly.

---

## Last updated

2026-03-26 — Marked **Complete**; Slack `workflow_run` for **Semgrep** documented; optional smoke-test steps.
