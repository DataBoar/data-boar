# Operator today mode — 2026-04-16 (quality gates → Corporate-Entity-C-ready → 1.6.9 + features)

**Português (Brasil):** [OPERATOR_TODAY_MODE_2026-04-16.pt_BR.md](OPERATOR_TODAY_MODE_2026-04-16.pt_BR.md)

**Use this date for your timezone:** Checklist is **2026-04-16** (not 04-17). **Block A** can run **this evening** and **after sleep** on the same calendar day or the next session — same file.

**Theme:** Run **maintenance and quality gates in order** so **Dependabot**, **CodeQL**, **SonarQube** (when your instance/MCP is up), **Docker Scout**, and **CI** tell one story — then **feature work** toward **1.6.9**. When **Corporate-Entity-C** reviews, the narrative is **green CI**, **fewer alerts**, **rebased image**, and **evidence in WRB**.

**Re-verify after sleep:** **`gh pr list --state open --author "dependabot[bot]"`** and **`.\scripts\maintenance-check.ps1`**.

---

## Session QA / handoff (evening 2026-04-16 → next session)

- **`origin/main`:** Merged **#188** (`python-multipart` — Dependabot **medium** cleared). **`git pull origin main`** on this machine — **open Dependabot security alerts:** **0** after merge (confirm with **Security → Dependabot** or **`maintenance-check.ps1`**).
- **If you touch deps manually:** **`pyproject.toml`** → **`uv lock`** → **`uv export --no-emit-package pyproject.toml -o requirements.txt`** → **`.\scripts\check-all.ps1`**.
- **Umbrella snapshot (read-only):** **`.\scripts\maintenance-check.ps1`** — Dependabot PRs + alerts + Scout hint; needs **`gh auth login`** and optional Docker for **–1b**.
- **Code scanning:** **CodeQL** — triage **Error** first (regex / quality); **note** can wait. **Semgrep** / **Bandit** in **CI** — fix regressions you introduce.
- **SonarQube:** If **home lab** or **IDE/MCP** is up, skim **new** issues on `main`; **[SONARQUBE_HOME_LAB.md](../SONARQUBE_HOME_LAB.md)** · **[sonar-project.properties](../../sonar-project.properties)**. If **down**, skip — **not** a blocker.
- **Docker Desktop / Scout (–1b):** **`docker pull fabioleitao/data_boar:latest`** → **`docker scout quickview`** / **`docker scout recommendations`** → **`.\scripts\docker-scout-critical-gate.ps1`** on **`fabioleitao/data_boar:latest`** (**0 CRITICAL**). Plan **Dockerfile** base refresh (e.g. newer **`python:3.13-slim`**) for **1.6.9** image build.
- **Working tree:** Commit or revert **`docs/ops/Corporate-Entity-C_REVIEW_REQUEST_GUIDELINE.md`** and other ops WIP before feature PRs.
- **Corporate-Entity-C / WRB:** When gates are **green**, **[Corporate-Entity-C_REVIEW_REQUEST_GUIDELINE.md](../Corporate-Entity-C_REVIEW_REQUEST_GUIDELINE.md)** + **[WRB_DELTA_SNAPSHOT_2026-04-16.md](../WRB_DELTA_SNAPSHOT_2026-04-16.md)** — **appreciation-first**, **code is truth**.

**Planning (carryover):** Enterprise discovery — **three complementary tracks** — [ADR 0024](../../adr/ADR-0024-enterprise-discovery-three-complementary-tracks.md); **PLANS_TODO** / **PLANS_HUB** bullets (**not** a legal promise).

**Release compass:** Next version after **v1.6.8** → **1.6.9** — [PUBLISHED_SYNC.md](PUBLISHED_SYNC.md), **`docs/VERSIONING.md`**, [SPRINTS_AND_MILESTONES.md](../../plans/SPRINTS_AND_MILESTONES.md).

---

## Block 0 — Morning reality check (10–15 min)

1. `git fetch origin` · `git status -sb` · `gh pr list --state open`
2. **`git pull origin main`** if behind.
3. **Stacked private git:** if **`docs/private/`** has meaningful unpushed commits, **`.\scripts\private-git-sync.ps1`** when appropriate.
4. `- [ ] **Block close (lab / VC):** when pausing later, **`block-close`** + VeraCrypt policy in **private** **`docs/private/homelab/OPERATOR_VERACRYPT_SESSION_POLICY*.md`** — not a substitute for **`eod-sync`**.

**Canonical rolling queue:** [CARRYOVER.md](CARRYOVER.md) · **Published truth:** [PUBLISHED_SYNC.md](PUBLISHED_SYNC.md)

### Social / editorial (private hub) — ~2 min

- [ ] Skim **`docs/private/social_drafts/editorial/SOCIAL_HUB.md`** for today / tomorrow rows — [SOCIAL_PUBLISH_AND_TODAY_MODE.md](SOCIAL_PUBLISH_AND_TODAY_MODE.md).

---

## Block A — Quality gates (before the feature token budget)

Order is **intentional**: supply Colleague-Nn and repo scans first, **image** second, **optional Sonar** when available, then **full gate**.

### A0 — One-shot triage

- [ ] **`.\scripts\maintenance-check.ps1`**

### A1 — Dependabot / GitHub Security (order –1)

- [ ] **Security → Dependabot:** open alerts **0** (or merged with **`pyproject.toml` + `uv.lock` + `requirements.txt`** aligned) — **#188** merged **2026-04-16** session.
- [ ] **Open Dependabot PRs:** merge **security** PRs when CI green.

### A2 — CodeQL (GitHub → Code scanning)

- [ ] **Error** severity: fix or dismiss with a **short** justification.
- [ ] **Warning:** only if quick; otherwise defer.

### A3 — SonarQube (optional, home lab / MCP)

- [ ] If **reachable:** triage **new** issues on `main` after merges.
- [ ] If **unavailable:** continue — **CodeQL + CI** carry the story.

### A4 — Docker Scout (–1b)

- [ ] **`docker scout quickview fabioleitao/data_boar:latest`** (and **`recommendations`** if rebuilding).
- [ ] **`.\scripts\docker-scout-critical-gate.ps1`** — **0 CRITICAL** with fix path, or documented **not fixed upstream**.
- [ ] **Image hygiene:** [scripts/docker-prune-local.ps1](../../scripts/docker-prune-local.ps1) · [scripts/docker/README.md](../../scripts/docker/README.md).

### A5 — Repo gate before features

- [ ] **`.\scripts\check-all.ps1`** on **`main`** after merges.
- [ ] **`git push origin main`** if local commits are intentional and tests pass.

### A6 — Corporate-Entity-C narrative

- [ ] **[Corporate-Entity-C_REVIEW_REQUEST_GUIDELINE.md](../Corporate-Entity-C_REVIEW_REQUEST_GUIDELINE.md)** committed — no mystery diffs.
- [ ] **WRB / external round:** delta snapshot + hash when you **send** — guideline **§** paste order (**appreciation-first** where applicable).

---

## Block B — New features + a healthy next release

- [ ] **One primary slice** from **`docs/plans/PLANS_TODO.md`** (Kanban **Selected** / **In progress**) — **one PR theme**, tests + docs as needed.
- [ ] **Optional second slice** only if the first is merged or blocked — [TOKEN_AWARE_USAGE.md](../../plans/TOKEN_AWARE_USAGE.md).
- [ ] **Release prep:** changelog / `docs/releases/`, **`docs/VERSIONING.md`**, tag + GitHub Release + Docker push — **[PUBLISHED_SYNC.md](PUBLISHED_SYNC.md)** and **`python scripts/plans-stats.py --write`** if **`PLANS_TODO.md`** rows change.

---

## Carryover — (edit)

- [ ] Close **Block A** before declaring “feature day.”
- [ ] (add items)

---

## End of day

- **`eod-sync`** or **`.\scripts\operator-day-ritual.ps1 -Mode Eod`**
- Draft **`OPERATOR_TODAY_MODE_<next-date>.md`** only when you **close the calendar day** or need a fresh dated shell.

---

## Quick references

- **PLANS:** [PLANS_TODO.md](../../plans/PLANS_TODO.md) · [PLANS_HUB.md](../../plans/PLANS_HUB.md)
- **Security:** [SECURITY.md](../../SECURITY.md) · [COMMIT_AND_PR.md](../COMMIT_AND_PR.md)
- **SonarQube:** [SONARQUBE_HOME_LAB.md](../SONARQUBE_HOME_LAB.md)
- Session keywords: **`.cursor/rules/session-mode-keywords.mdc`**
