# Corporate-Entity-C evolution review — 2026-03-23 (premium WABIX)

**Source (local / operator):** PDF `docs/feedbacks, reviews, comments and criticism/analise_evolucao_data_boar_2026-03-23_premium_wabix.pdf`.

**Source (shared URL in email):** [Google Drive PDF](https://drive.google.com/file/d/1mPCindOl8td02qNzR4vb64i4eAx6G7TC/view?usp=drivesdk) — at review time, this URL resolves to the same file name and appears to be the same report material.

**Scope announced by Corporate-Entity-C:** executive view, detailed technical analysis, DevSecOps/hardening, comparison with previous baseline, prioritized recommendations.

---

## Executive reading (quick anchor)

- The report reinforces a strong direction in docs/compliance narrative, but says core runtime/security defaults still need hardening.
- Highest recurring themes: version coherence, naming/package coherence, secure defaults, failure semantics in parallel execution, and observability/notifications.
- The report states one baseline-tracking file was "not found"; this needs an explicit clarification back to Corporate-Entity-C because `docs/plans/Corporate-Entity-C_ANALISE_2026-03-18.md` exists in-repo.

---

## Findings mapped to repo reality

| Corporate-Entity-C theme                                                         | Current repo status (2026-03-23 check)                                                                                                                                                                                                                                 | Action status                                         |
| ---                                                                  | ---                                                                                                                                                                                                                                                                    | ---                                                   |
| Version drift (`v1.6.x` vs metadata/README `1.5.4`)                  | Addressed in release flow (**1.6.4+**); keep README/releases aligned per `VERSIONING.md`.                                                                                                                                                                              | ✅ Closed in repo; communicate evidence back to Corporate-Entity-C |
| Product/package naming drift (`Data Boar` vs PyPI id) | Pacote renomeado para **`data-boar`** no repositório; publicação PyPI quando agendada.                                                                                                                                                                                                                     | ✅ Endereçado no código/docs (2026)                                     |
| API auth as optional default                                         | Startup **warning** when bind is non-loopback and API key not effectively required (`main.py` + `core/host_resolution.py`); full secure-by-default remains a product decision.                                                                                         | 🔄 Improved; continue toward stricter defaults         |
| Parallel failure semantics (`except Exception: pass`)                | Worker failures logged + `save_failure` + session `completed_errors` where applicable.                                                                                                                                                                                 | ✅ Baseline done                                       |
| Off-band notifications / observability                               | **Phase 1–4.2:** `notifications` config, `utils/notify.py`, scan-complete brief, **`operator.channels`**, **`tenant.by_tenant`**, **dedupe**, **`notification_send_log`** (sem corpo); `notify_webhook.py` grava auditoria manual via `sqlite_path`; retries 5xx/rede. | 🔄 Phase 4.3+ backlog (digest, i18n fino)              |

---

## Prioritized actions (practical sequence)

1. **Close the baseline alignment loop with Corporate-Entity-C**
   - **In-repo pointer for reviewers:** [Corporate-Entity-C_IN_REPO_BASELINE.md](../ops/Corporate-Entity-C_IN_REPO_BASELINE.md) lists canonical paths (`Corporate-Entity-C_ANALISE_2026-03-18.md`, `Corporate-Entity-C_ANALISE_2026-03-23_EVOLUTIVA.md`, feedback PDFs folder).
   - In the next email, mention `docs/plans/Corporate-Entity-C_ANALISE_2026-03-18.md` explicitly and link or cite the baseline doc above if useful.

1. **Notifications (off-band + scan-complete) — baseline + audit**
   - Implemented: `notifications` config (`config/loader.py`), `utils/notify.py`, `scripts/notify_webhook.py` (com auditoria opcional em SQLite; `--no-audit` em CI sem DB), scan-complete brief after CLI/API scans, `docs/USAGE.md` / `USAGE.pt_BR.md`.
   - **Next optional:** Phase 4.3+ em `PLAN_NOTIFICATIONS_OFFBAND_AND_SCAN_COMPLETE.md` (digest, i18n; caps finos por canal → backlog).

1. **Keep hardening debt visible in one place**
   - Continue tracking "secure-by-default auth" and "honest failure semantics" as explicit follow-ups in `PLANS_TODO.md`.
   - Avoid broad refactors; do small, auditable slices with tests/docs.

---

## Notes for next Corporate-Entity-C interaction

- If requested, ask for the shorter executive version as a companion artifact (not replacement), useful for stakeholder sync and prioritization checkpoints.
- Keep requests anchored in the established WRB structure: three temporal layers, explicit baseline markers (date + PR/commit), and chaptered PDF output.

## Maturity trail — what “done” looks like (no complaints, evidence-ready)

| Theme                                                                         | Status                                                                                                                 | Owner |
| -----                                                                         | ------                                                                                                                 | ----- |
| Version coherence (`VERSIONING.md`, README, releases)                         | ✅ In-repo; **publish** GitHub tag + Hub = operator                                                                     | O     |
| KPI + contract tests (baseline)                                               | ✅ `PLAN_READINESS_AND_OPERATIONS` §4.7 + pytest contract                                                               | —     |
| Observability / notifications (Phases 1–4.2)                                  | ✅ Config + audit + webhooks + docs                                                                                     | —     |
| API bind loopback default + docs + tests                                      | ✅ PLANS_TODO “Secure default host binding”                                                                             | —     |
| Parallel failure semantics                                                    | ✅ Engine + session `completed_errors`                                                                                  | —     |
| **Deploy examples** (K8s/Compose call out `api.require_api_key` when exposed) | ✅ `deploy/kubernetes/README.md` § Security + `configmap.yaml` comments; Compose/DEPLOY already documented              | —     |
| **Product/package naming** (`Data Boar` vs PyPI name)                         | 🔄 Backlog / counsel + packaging decision                                                                               | O     |
| **API key via env (`api_key_from_env`)** — operator clarity                   | ✅ Runbook **[API_KEY_FROM_ENV_OPERATOR_STEPS.md](../ops/API_KEY_FROM_ENV_OPERATOR_STEPS.md)** + **`SECURITY.md`** link | A     |
| **API key “secure by default”** beyond warnings                               | 🔄 Product decision (breaking change if forced on)                                                                      | O     |
| **Corporate-Entity-C email** (baseline paths + `Corporate-Entity-C_ANALISE_2026-03-18.md`)            | 🔄 Send when ready                                                                                                      | O     |
| **Priority band A** (Dependabot, Scout, Hub tags)                             | 🔄 Ongoing                                                                                                              | O+A   |
| Notifications Phase 4.3 (digest, i18n)                                        | ⬜ Backlog                                                                                                              | A     |
| **W-DECOUPLE** (detector/report)                                              | 🔄 Incremental                                                                                                          | A     |

**Agent (A):** small doc/code slices, tests, manifests comments, `scripts/` automation. **Operator (O):** GitHub release, Docker Hub, email to Corporate-Entity-C, merge when branch protection requires human, product/legal calls.

**Synced with:** `docs/plans/PLANS_TODO.md` (Corporate-Entity-C section).
