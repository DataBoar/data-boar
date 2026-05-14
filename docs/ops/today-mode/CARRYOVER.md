# Today-mode carryover queue (rolling)

**Português (Brasil):** [CARRYOVER.pt_BR.md](CARRYOVER.pt_BR.md)

**Purpose:** Single **rolling list** of operator items that survive across dated `OPERATOR_TODAY_MODE_*` files. **Close, defer with date, or move to `PLANS_TODO` / an issue** — nothing immortal without an owner.

**Related:** **`carryover-sweep`** (morning), **`eod-sync`** (evening), **`docs/private/TODAY_MODE_CARRYOVER_AND_FOUNDER_RHYTHM.md`** (private).

---

## Queue (update in place)

| Item | Source | Status | Next step / defer |
| ---- | ------ | ------ | ----- |
| **`v1.7.4-rc` on `main` + GitHub pre-release; Hub stable still `1.7.3`** | [OPERATOR_TODAY_MODE_2026-05-11.md](OPERATOR_TODAY_MODE_2026-05-11.md) · [PUBLISHED_SYNC.md](PUBLISHED_SYNC.md) | ✅ Shipped (RC) | Controlled lab timing **1.7.3 vs 1.7.4-rc** before promoting **S1–S3** product slices; no Hub **`latest`** move unless stable **1.7.4** publish. |
| **`zizmor` workflow (warn-first)** — `.github/workflows/zizmor.yml` + local **`scripts/workflow-security-lint.ps1`** / **`.sh`** (manual pre-commit hook) | PR **#354** merged **2026-05-11** | ✅ Done | Local advisory default; enforce via **`-Enforce`**, **`DATA_BOAR_ENFORCE_ZIZMOR=true`**, or GitHub **`ZIZMOR_ENFORCE`** when baseline is clean. |
| **Maestro DB matrix evidence (all-to-all)** | [LAB_LESSONS_LEARNED_2026_05_10.md](../lab_lessons_learned/LAB_LESSONS_LEARNED_2026_05_10.md) | ⬜ Pending | One consolidated round + per-host configs in **`docs/private/homelab/reports/`**. |
| **Post-`1.7.4` short-sprint closure (pick one)** — **S3 CNPJ Phase 5**, **S1 Bandit Phase 3**, **S2 Scope import Phase E** | `PLANS_TODO.md` H1/U1 | ⬜ Pending | After lab metrics or same day if no LAB slot — **`feature`** + **`check-all`**. |
| **`benchmark-ab` harness on `main` (PR #229)** — `scripts/benchmark-ab.ps1`, `benchmark_runs/` gitignore, runbook/hub, `docs/plans/BENCHMARK_EVOLUTION.md` | EOD **2026-04-27** (carryover from completão / benchmark ritual) | ✅ Merged (CI green) | When LAB slot exists, run `.\scripts\benchmark-ab.ps1` and replace **TBD** rows in `BENCHMARK_EVOLUTION.md` with real `benchmark_runs/times.txt` + manifest deltas. |
| **1.7.0 shipped; CI `ci.yml` Sonar `if` fix; beta testers (IDENTIDADE_COLABORADOR_A / IDENTIDADE_COLABORADOR_B) synthetic tests; lab-op smoke** | [OPERATOR_TODAY_MODE_2026-04-17.md](OPERATOR_TODAY_MODE_2026-04-17.md) | ⬜ Pending | **`gh run list --workflow ci.yml`** green on `main`; **`git pull`**; short tester brief; optional **`lab-op-sync-and-collect.ps1`** / **`docker pull`** `1.7.0` — [PUBLISHED_SYNC.md](PUBLISHED_SYNC.md) |
| **1.6.9 prep + Corporate-Entity-C-ready gates (Dependabot → CodeQL → Sonar? → Scout → check-all)** | [OPERATOR_TODAY_MODE_2026-04-16.md](OPERATOR_TODAY_MODE_2026-04-16.md) | ⬜ Superseded by 1.7.0 lane | Older checklist row — close or archive when **2026-04-17** items are done; **Corporate-Entity-C** still follows [Corporate-Entity-C_REVIEW_REQUEST_GUIDELINE.md](../Corporate-Entity-C_REVIEW_REQUEST_GUIDELINE.md) |
| Close **1.6.8 release gate** (notes + tests + publish/defer decision) | 2026-04-02 | ⬜ Pending | Follow `OPERATOR_TODAY_MODE_2026-04-02.md` Block C; if deferred, write explicit target date |
| New external round **WRB + Gemini** with "code is truth" framing | 2026-04-02 | ⬜ Pending | Send WRB with 3 time lenses and build Gemini bundle with `--verify`; triage in `PLAN_GEMINI_FEEDBACK_TRIAGE.md` |
| Quantified snapshot (today / 3 days / 7 days) with front split | 2026-04-02 | ⬜ Pending | Run `.\scripts\progress-snapshot.ps1 -OutputMarkdown docs/private/progress/progress_snapshot_2026-04-02.md` |
| Founder LinkedIn/ATS profile full refresh | 2026-04-02 | ⬜ Pending | Apply private playbook section in `LINKEDIN_ATS_AND_POSITIONING_PLAYBOOK.pt_BR.md` |
| Time Machine USB recovery before repurposing as P0 external backup | 2026-04-02 | ⬜ Pending | Follow `docs/ops/TIME_MACHINE_USB_RECOVERY_AND_REPURPOSE.md` (read-only triage -> copy -> wipe -> new backup policy) |
| **Corporate-Entity-C WRB** e-mail | 2026-03-26 / 03-29 / 03-31 | ⬜ Pending | Paste block: **`docs/ops/WRB_DELTA_SNAPSHOT_2026-03-31.md`** — send today or defer with a date in PLANS/private |
| **Slack** proof-of-ping (desktop + phone) | 2026-03-27 | ✅ Done | Founder-only channel confirmed; ping received on desktop + phone (**CHAN-OK**) |
| **Dependabot** PRs (#134 pypdf, #144 starlette, #147 pip group) | 2026-03-29 / 30 / 03-31 | ✅ Done | Merged (green + mergeable). Keep watching new PRs per **`SECURITY.md`** |
| **Branch protection** (required checks) | 2026-03-26 optional | ⬜ Optional | Enable when you want CI/Semgrep enforced on `main` |
| **Gemini Cold doc slice** (e.g. G-26-04 + G-26-13) | `PLANS_TODO.md` | ⬜ Optional | One **`docs`** PR; safest items first |
| **`/help` vs `main.py`** parity skim | 2026-03-29 | ⬜ When flags change | After next CLI/dashboard flag — **`tests/test_operator_help_sync.py`** |

**Done / archived (do not resurrect without new work):**

- **Tag `v1.6.7` + GitHub Release + Docker Hub** — shipped **2026-03-26** — see [PUBLISHED_SYNC.md](PUBLISHED_SYNC.md).
- **Help-sync / OpenAPI / README `--host`** for the 2026-03-27 pass — see completion logs in [OPERATOR_TODAY_MODE_2026-03-27.md](OPERATOR_TODAY_MODE_2026-03-27.md).

---

## Housekeeping PR (this folder move)

If you have **local commits** that created **`docs/ops/today-mode/`**, finish themed commits (docs/workflow), run **`.\scripts\lint-only.ps1`** or **`check-all`**, then merge to `main`.

---

## LAB-NODE-01 + LMDE (parallel)

Hardware install is **out of Git** — use **[`docs/ops/LMDE7_LAB-NODE-01_DEVELOPER_SETUP.md`](../LMDE7_LAB-NODE-01_DEVELOPER_SETUP.md)** ([pt-BR](../LMDE7_LAB-NODE-01_DEVELOPER_SETUP.pt_BR.md)) when the laptop is ready for **uv**, **git**, **SSH** keys, and repo clone.
