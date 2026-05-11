# Operator today mode (dated checklists)

**Português (Brasil):** [README.pt_BR.md](README.pt_BR.md)

**Purpose:** One place for **dated day plans** (`OPERATOR_TODAY_MODE_YYYY-MM-DD.md`), the **active carryover queue**, and **how to keep “published” aligned with `pyproject.toml`** so checklists do not drift.

**Session keywords:** Type **`today-mode YYYY-MM-DD`** (English-only token) in chat; see **`.cursor/rules/session-mode-keywords.mdc`**. For **end of a work block or lab exit** (VeraCrypt / carryover / optional private stack — not necessarily calendar EOD), use **`block-close`**. Morning/evening shell helper: **`scripts/operator-day-ritual.ps1`** (Tier A readiness + lists recent files — see **Morning readiness** below).

### For assistants (Cursor / agent)

**“Today”** for checklist filenames and dated work must match the **operator workstation clock**, not only static chat context.

1. In the **integrated terminal** on the dev PC: **PowerShell** `Get-Date -Format "yyyy-MM-dd"` (or `Get-Date -Format "o"` for ISO with offset); **cmd** `date /t` (and `time /t` if needed).
2. Open or create **`OPERATOR_TODAY_MODE_<that-YYYY-MM-DD>.md`** in this folder when aligning to **today-mode**.
3. If the operator **names a different date** in chat, use their date for the file anchor.

See **`AGENTS.md`** (*Workstation calendar clock*) and **`.cursor/rules/agent-session-ritual-sync-main-and-private-stack.mdc`**.

---

## Morning readiness (SRE-style ladder)

**Goal:** Start most days with **cheap, evidence-backed** sync — without pretending that every trust/prod check runs every morning. **`carryover-sweep`** in chat maps to **`.\scripts\operator-day-ritual.ps1 -Mode Morning`** (same script).

| Tier | What | When |
| ---- | ---- | ---- |
| **A — Sync & surface** | `git fetch`, `git status -sb`, open PRs, latest **`main`** **CI** (`ci.yml`), and whether **`OPERATOR_TODAY_MODE_YYYY-MM-DD.md`** exists for **today** | **Daily** (~2 min). Always safe before deep work. |
| **B — Supply Colleague-Nn (-1)** | `uvx pip-audit -r requirements.txt` (same family as CI **Dependency audit**) | **Weekly**, before a **release**, or right after **`deps`** / lockfile work — not every breakfast. |
| **C — Image (-1b)** | `docker scout quickview` (or project policy) on the **published** image after **Dockerfile** / lock / base image changes | When the **image** or **supply** story changed — not daily. |
| **D — Second environment (-1L)** | **[HOMELAB_VALIDATION.md](../HOMELAB_VALIDATION.md)**; optional **`scripts/lab-op-sync-and-collect.ps1`** when **`docs/private/homelab/lab-op-hosts.manifest.json`** exists | When proving **deploy + connector** on a **second** machine, or on a **scheduled** lab health pass — not every morning. |

**Why not run B–D every day?** They are higher-latency or environment-dependent. Running **pip-audit + Scout + SSH lab** daily would add noise without extra safety once **`main`** is green. Tier **A** catches “surprise WIP”, **stale refs**, **open PRs**, and **red CI** before you invest hours.

**Fast path:** `.\scripts\operator-day-ritual.ps1 -Mode Morning -SkipReadiness` — file list + social hints only (rare). This **skips Tier A** (git fetch, PRs, CI snapshot); it is **not** the full code/regression gate.

**Code / dependency gate:** use **`.\scripts\check-all.ps1`** before a PR or merge (optional **`-IncludeVersionSmoke`** for version vs published release coherence). CI runs the same pytest suite, including lock/export sync tests—see [SECURITY.md](../../SECURITY.md) and [ADR 0030](../../adr/0030-python-dependency-update-closure-single-pass.md).

**Chat:** optional English token **`morning-readiness`** — same intent as **`carryover-sweep`** for Tier A + doc pointer (see **`.cursor/rules/session-mode-keywords.mdc`**).

---

## Canonical companions (read often)

| Doc | Role |
| --- | ---- |
| [CARRYOVER.md](CARRYOVER.md) | **Rolling queue** — promote, defer, or close items (no silent backlog). |
| [WORKBOARD.md](WORKBOARD.md) | **Central cockpit** — one-page routing across backlog, carryover, and reminders (without duplicating source-of-truth docs). |
| [PUBLISHED_SYNC.md](PUBLISHED_SYNC.md) | **GitHub Release + Docker Hub vs repo version** — refresh after each publish. |
| [SOCIAL_PUBLISH_AND_TODAY_MODE.md](SOCIAL_PUBLISH_AND_TODAY_MODE.md) | **Private social hub + today-mode** — planned posts, deferrals, ad-hoc evidence; pairs with gitignored **`docs/private/social_drafts/`**. pt-BR: [SOCIAL_PUBLISH_AND_TODAY_MODE.pt_BR.md](SOCIAL_PUBLISH_AND_TODAY_MODE.pt_BR.md). |
| [PRIVATE_OPERATOR_NOTES.md](../../PRIVATE_OPERATOR_NOTES.md) | Private rhythm note path (`docs/private/…`) when relevant. |
| [OPERATOR_TODAY_MODE_TEMPLATE.md](OPERATOR_TODAY_MODE_TEMPLATE.md) | **Copy-me shell** for new days (Block 0 + End of day: **`block-close`** + VeraCrypt vs **`eod-sync`**). pt-BR: [OPERATOR_TODAY_MODE_TEMPLATE.pt_BR.md](OPERATOR_TODAY_MODE_TEMPLATE.pt_BR.md). |

---

## Dated checklists (newest last)

| Date | English | pt-BR |
| ---- | ------- | ----- |
| 2026-03-26 | [OPERATOR_TODAY_MODE_2026-03-26.md](OPERATOR_TODAY_MODE_2026-03-26.md) | [OPERATOR_TODAY_MODE_2026-03-26.pt_BR.md](OPERATOR_TODAY_MODE_2026-03-26.pt_BR.md) |
| 2026-03-27 | [OPERATOR_TODAY_MODE_2026-03-27.md](OPERATOR_TODAY_MODE_2026-03-27.md) | [OPERATOR_TODAY_MODE_2026-03-27.pt_BR.md](OPERATOR_TODAY_MODE_2026-03-27.pt_BR.md) |
| 2026-03-29 | [OPERATOR_TODAY_MODE_2026-03-29.md](OPERATOR_TODAY_MODE_2026-03-29.md) | [OPERATOR_TODAY_MODE_2026-03-29.pt_BR.md](OPERATOR_TODAY_MODE_2026-03-29.pt_BR.md) |
| 2026-03-30 | [OPERATOR_TODAY_MODE_2026-03-30.md](OPERATOR_TODAY_MODE_2026-03-30.md) | [OPERATOR_TODAY_MODE_2026-03-30.pt_BR.md](OPERATOR_TODAY_MODE_2026-03-30.pt_BR.md) |
| **2026-03-31** | [OPERATOR_TODAY_MODE_2026-03-31.md](OPERATOR_TODAY_MODE_2026-03-31.md) | [OPERATOR_TODAY_MODE_2026-03-31.pt_BR.md](OPERATOR_TODAY_MODE_2026-03-31.pt_BR.md) |
| **2026-04-01** | [OPERATOR_TODAY_MODE_2026-04-01.md](OPERATOR_TODAY_MODE_2026-04-01.md) | [OPERATOR_TODAY_MODE_2026-04-01.pt_BR.md](OPERATOR_TODAY_MODE_2026-04-01.pt_BR.md) |
| **2026-04-02** | [OPERATOR_TODAY_MODE_2026-04-02.md](OPERATOR_TODAY_MODE_2026-04-02.md) | [OPERATOR_TODAY_MODE_2026-04-02.pt_BR.md](OPERATOR_TODAY_MODE_2026-04-02.pt_BR.md) |
| 2026-04-06 | [OPERATOR_TODAY_MODE_2026-04-06.md](OPERATOR_TODAY_MODE_2026-04-06.md) | — *(no `.pt_BR.md` yet)* |
| 2026-04-08 | [OPERATOR_TODAY_MODE_2026-04-08.md](OPERATOR_TODAY_MODE_2026-04-08.md) | — *(no `.pt_BR.md` yet)* |
| 2026-04-09 | [OPERATOR_TODAY_MODE_2026-04-09.md](OPERATOR_TODAY_MODE_2026-04-09.md) | — *(no `.pt_BR.md` yet)* |
| **2026-04-10** | [OPERATOR_TODAY_MODE_2026-04-10.md](OPERATOR_TODAY_MODE_2026-04-10.md) | [OPERATOR_TODAY_MODE_2026-04-10.pt_BR.md](OPERATOR_TODAY_MODE_2026-04-10.pt_BR.md) |
| **2026-04-16** | [OPERATOR_TODAY_MODE_2026-04-16.md](OPERATOR_TODAY_MODE_2026-04-16.md) | [OPERATOR_TODAY_MODE_2026-04-16.pt_BR.md](OPERATOR_TODAY_MODE_2026-04-16.pt_BR.md) |
| **2026-04-22** | [OPERATOR_TODAY_MODE_2026-04-22.md](OPERATOR_TODAY_MODE_2026-04-22.md) | [OPERATOR_TODAY_MODE_2026-04-22.pt_BR.md](OPERATOR_TODAY_MODE_2026-04-22.pt_BR.md) |
| **2026-05-11** | [OPERATOR_TODAY_MODE_2026-05-11.md](OPERATOR_TODAY_MODE_2026-05-11.md) | [OPERATOR_TODAY_MODE_2026-05-11.pt_BR.md](OPERATOR_TODAY_MODE_2026-05-11.pt_BR.md) |

**WRB paste blocks** stay next to ops runbooks (e.g. **`docs/ops/WRB_DELTA_SNAPSHOT_*.md`**) — not in this folder.

---

## Adding a new day

1. Copy **[OPERATOR_TODAY_MODE_TEMPLATE.md](OPERATOR_TODAY_MODE_TEMPLATE.md)** (or the structure from the **most recent** dated `OPERATOR_TODAY_MODE_*.md`) and rename to **`OPERATOR_TODAY_MODE_YYYY-MM-DD.md`**. Keep **Block 0 item 5** and the **End of day** line that pair **`block-close`** with VeraCrypt (**private** **`docs/private/homelab/OPERATOR_VERACRYPT_SESSION_POLICY*.md`**) vs **`eod-sync`**.
1. Link **`CARRYOVER.md`** and **`PUBLISHED_SYNC.md`** from Block 0 when the day touches release or carryover.
1. After a **real publish** (tag + GitHub Release + Docker Hub), update **`PUBLISHED_SYNC.md`**, **`docs/plans/PLANS_TODO.md`** release rows if needed, and **`python scripts/plans-stats.py --write`**.

---

## Navigation

- Parent index: **[`docs/ops/README.md`](../README.md)** ([pt-BR](../README.pt_BR.md)).
