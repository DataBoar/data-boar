# Corporate-Entity-C reviews — in-repo baseline paths (for reviewers)

**Purpose:** Give Corporate-Entity-C (and future reviewers) **stable paths** inside this repository for evolution tracking and WRB baselines, so reports do not say “file not found” when the operator keeps tracking under `docs/plans/`.

**Language:** This ops note is **English** (canonical for cross-audience); pt-BR dialogue in email may still reference these paths as written.

---

## Evolution review tracking (PDFs + Markdown)

| Artifact                                              | Path                                                    |
| --------                                              | ----                                                    |
| First evolution review (2026-03-18) — in-repo notes   | `docs/plans/Corporate-Entity-C_ANALISE_2026-03-18.md`               |
| Premium evolution review (2026-03-23) — in-repo notes | `docs/plans/Corporate-Entity-C_ANALISE_2026-03-23_EVOLUTIVA.md`     |
| PDFs (local / operator workspace)                     | `docs/feedbacks, reviews, comments and criticism/*.pdf` |

If a review snapshot was taken from a **different clone or branch**, ask the operator for **commit SHA** and **branch**; the files above are the **canonical** tracking locations on `main` when present.

---

## WRB (review request) guidelines

- Full request template and “Prompt mestre”: **`docs/ops/Corporate-Entity-C_REVIEW_REQUEST_GUIDELINE.md`**
- Package for send / WhatsApp short form: **`docs/ops/Corporate-Entity-C_WRB_REVIEW_AND_SEND.pt_BR.md`**

---

## Plans — cloud storage and CI (reviewer expectations)

| Topic                                                                                   | Path                                                                              |
| -----                                                                                   | ----                                                                              |
| **Object storage connectors (S3-class, Azure Blob, GCS)** — plan only until implemented | `docs/plans/PLAN_OBJECT_STORAGE_CLOUD_CONNECTORS.md`                              |
| **Semgrep in GitHub Actions** (complements CodeQL)                                      | `docs/plans/completed/PLAN_SEMGREP_CI.md` · `.github/workflows/semgrep.yml`                 |
| **Bandit** (Python linter; `ci.yml` job **strict** `-ll -ii`)                                    | `docs/plans/completed/PLAN_BANDIT_SECURITY_LINTER.md` · `[tool.bandit]` in `pyproject.toml` |

---

## Sync

Central execution order: **`docs/plans/PLANS_TODO.md`** (Corporate-Entity-C subsection).

**Optional API key via environment:** Step-by-step English runbook (variable **name** in YAML vs **secret** in env, precedence, `curl` checks, synthetic example): **[API_KEY_FROM_ENV_OPERATOR_STEPS.md](API_KEY_FROM_ENV_OPERATOR_STEPS.md)**. Cited from root **`SECURITY.md`** § Optional API key.

## Docker Scout evidence bundle (for review cycles)

When a release includes container publish/hardening updates, include these paths/output references in the Corporate-Entity-C request so findings are reproducible:

- Gate script: `scripts/docker-scout-critical-gate.ps1`
- Release order runbook: `docs/ops/DOCKER_IMAGE_RELEASE_ORDER.md`
- Docker scripts index: `scripts/docker/README.md`
- Command examples:
- `docker scout cves fabioleitao/data_boar:<tag> --only-severity critical`
- `.\scripts\docker-scout-critical-gate.ps1 -Image fabioleitao/data_boar:<tag>`

**Interpretation rule:** if Scout reports CRITICAL CVEs with **`Fixed version: not fixed`**, track as **upstream-risk monitored** (documented exception + rebuild cadence), not as an immediate app regression. If a fixed version exists, treat as actionable and prioritize remediation.

---

## Email to Corporate-Entity-C (operator copy-paste)

Use after a release or when sharing **evidence of alignment** (version strings, baseline paths). Adjust the greeting and add your name.

**Subject:** Data Boar — in-repo baseline paths & release alignment

## Body (EN):

> Hello,
>
> For our next exchange, please use these **canonical paths** in this repository (branch `main` unless we agree otherwise):
>
> - Evolution notes: `docs/plans/Corporate-Entity-C_ANALISE_2026-03-18.md` and `docs/plans/Corporate-Entity-C_ANALISE_2026-03-23_EVOLUTIVA.md`
> - Consolidated plans: `docs/plans/PLANS_TODO.md`
> - This baseline list: `docs/ops/Corporate-Entity-C_IN_REPO_BASELINE.md`
>
> **Current shipped version** is stated in the root `README.md` / `README.pt_BR.md` (“Current release”) and matches `pyproject.toml` and `docs/releases/<version>.md` for that tag.
>
> Best regards,

---

## Email status

| Item                 | Status                                     |
| ----                 | ------                                     |
| Paths list in repo   | ✅ `Corporate-Entity-C_IN_REPO_BASELINE.md` (this file) |
| Operator sends email | 🔄 Manual (paste from § above when ready)   |
