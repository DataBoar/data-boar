# Suggested full-day plan — lab-op + product (reusable checklist)

**Português (Brasil):** [OPERATOR_NEXT_DAY_CHECKLIST.pt_BR.md](OPERATOR_NEXT_DAY_CHECKLIST.pt_BR.md)

**Purpose:** A **single-day** operator order of work: light **security** maintenance, **homelab** unblocks, optional **–1L** validation, optional **Corporate-Entity-C** email, and **one** light product slice if energy remains. The agent cannot SSH, use your GitHub session, or touch your hardware.

**Broader context:** [OPERATOR_MANUAL_ACTIONS.md](OPERATOR_MANUAL_ACTIONS.md) · [PLANS_TODO.md](../plans/PLANS_TODO.md) “Resume next session”.

**Dated one-day focus:** see **[today-mode/README.md](today-mode/README.md)** (indexed checklists). Current example: [OPERATOR_TODAY_MODE_2026-04-02.md](today-mode/OPERATOR_TODAY_MODE_2026-04-02.md) ([pt-BR](today-mode/OPERATOR_TODAY_MODE_2026-04-02.pt_BR.md)). **WRB delta (example):** [WRB_DELTA_SNAPSHOT_2026-04-16.md](WRB_DELTA_SNAPSHOT_2026-04-16.md). **Published** stable line is **`v1.7.3`** / **`1.7.3`** on GitHub + Hub; **`main`** may already show a **pre-release** working line (for example **`1.7.4-rc`**) before the next stable publish ([VERSIONING.md](../VERSIONING.md)). Prior golden **`v1.7.2-safe`** / **`1.7.2+safe`**: [docs/releases/1.7.2-safe.md](../releases/1.7.2-safe.md). Keep reconcile rows in [today-mode/PUBLISHED_SYNC.md](today-mode/PUBLISHED_SYNC.md).

---

## Morning (~2–3h) — security + unblocks

| #  | Activity                                                                                                                                                          | “Done” criterion                                                        |
| -  | --------                                                                                                                                                          | ----------------                                                        |
| M1 | **Band A (–1):** GitHub → **Security → Dependabot** — triage or close **one** item (PR / `pyproject` + `uv lock` + `requirements.txt` + `check-all`)              | One alert handled **or** note “nothing critical today” in private notes |
| M2 | **Band A (–1b):** if you pushed an image recently — `docker scout quickview` on your tag                                                                          | Screenshot or private note if follow-up needed                          |
| M3 | **LAB-OP — `<lab-host-2>` / secondary SBC:** fix `git status` on `homelab-host-report.sh` **or** run `lab-op-sync-and-collect.ps1 -SkipGitPull`                         | New report under `docs/private/homelab/reports/` **or** clean pull      |
| M4 | **ThinkPad LAB-NODE-01 + LMDE 7:** continue [LMDE7_LAB-NODE-01_DEVELOPER_SETUP.pt_BR.md](LMDE7_LAB-NODE-01_DEVELOPER_SETUP.pt_BR.md) through §8 checklist **or** record where you stopped | One line in private notes                                               |

---

## Afternoon (~3–4h) — validation or external comms

| #  | Activity                                                                                                                                                     | “Done” criterion                                                                     |
| -  | --------                                                                                                                                                     | ----------------                                                                     |
| T1 | **Order –1L:** on **one** lab host, [HOMELAB_VALIDATION.md](HOMELAB_VALIDATION.md) §1.1–1.2 + §2 synthetic **or** §1.3–1.5 Docker if containers already work | Dated note with pass/fail; paste outputs to `docs/private/` if you want agent review |
| T2 | **Corporate-Entity-C (optional):** send baseline email using [Corporate-Entity-C_IN_REPO_BASELINE.md](Corporate-Entity-C_IN_REPO_BASELINE.md) + cite `Corporate-Entity-C_ANALISE_2026-03-18.md`              | Sent **or** draft saved with send date                                               |
| T3 | **Read-only:** skim [PLAN_LAB_OP_OBSERVABILITY_STACK.md](../plans/PLAN_LAB_OP_OBSERVABILITY_STACK.md) §1 — pick **A or B** + **C or D** later                | One sentence in private runbook                                                      |

---

## Late afternoon / light evening (≤1h)

| #  | Activity                                                                                                       | “Done” criterion                    |
| -  | --------                                                                                                       | ----------------                    |
| N1 | Refresh **`docs/private/WHAT_TO_SHARE_WITH_AGENT.md`**                                                         | File saved                          |
| N2 | If **SNMP Task Scheduler** runs — tail latest `snmp_LAB-ROUTER-01_probe_*.log`                                           | Glance OK/errors                    |
| N3 | **One** product slice only if energy left: see “What to start next” in [PLANS_TODO.md](../plans/PLANS_TODO.md) | Named issue/branch for next morning |

---

## Opening/closing mini-ritual (anti-chaos)

- **Open (5 min):** run `carryover-sweep` (or `.\scripts\operator-day-ritual.ps1 -Mode Morning`) and lock exactly one primary front for the day.
- **Close (5-10 min):** run `eod-sync` (or `.\scripts\operator-day-ritual.ps1 -Mode Eod`) and write deferred items with a date in `CARRYOVER`.
- **Simple rule:** if it is not in today-mode or carryover, it does not exist tomorrow.

---

## What the agent **cannot** do for you

- SSH to hosts, `sudo` on your LAB-NODE-01, log into GitHub as you.
- Send Corporate-Entity-C email — can only draft text.
- Decide laptop RAM for Grafana/Graylog — you measure and document.

---

**Tip:** Next chat: *“Follow OPERATOR_NEXT_DAY_CHECKLIST; done M1–M3; blocked on M4 because …”*.
