# Operator today mode — 2026-04-20 (sync `main`, optional PyPI publish, lab cadence)

**Português (Brasil):** [OPERATOR_TODAY_MODE_2026-04-20.pt_BR.md](OPERATOR_TODAY_MODE_2026-04-20.pt_BR.md)

**Theme:** **`main`** local has **two commits not yet on `origin`** (workstation-clock today-mode docs + PyPI **Hatchling** packaging / `pypi-publish.ps1` / ADR 0031). **First:** `git push origin main` when ready (or open PR if you batch differently). **Optional:** first **PyPI** upload under **`data-boar`** with **`UV_PUBLISH_TOKEN`** — see **`CONTRIBUTING.md`** (*Publishing to PyPI*). **Cadence:** **–1L** / **`HOMELAB_VALIDATION.md`** when hardware time allows — not blocking the push.

---

## Block 0 — Morning reality check (10–15 min)

Run **`carryover-sweep`** or **`.\scripts\operator-day-ritual.ps1 -Mode Morning`**. Then:

1. **`git fetch origin`** · **`git status -sb`** — confirm whether **`origin/main`** absorbed yesterday’s local commits after push.
2. **Stacked private:** if **`docs/private/`** changed overnight, **`.\scripts\private-git-sync.ps1`** (and **`-Push`** per habit).

**Rolling queue:** [CARRYOVER.md](CARRYOVER.md) · **Published truth:** [PUBLISHED_SYNC.md](PUBLISHED_SYNC.md)

### Social / editorial (private hub) — ~2 min

- [ ] Skim **`docs/private/social_drafts/editorial/SOCIAL_HUB.md`** for **Alvo** matching **2026-04-20** — [SOCIAL_PUBLISH_AND_TODAY_MODE.md](SOCIAL_PUBLISH_AND_TODAY_MODE.md).

---

## Carryover — from 2026-04-19 EOD

- [ ] **`git push origin main`** — publishes docs + build packaging commits (verify **`check-all`** green locally if you did not run before commit).
- [ ] **PyPI (optional, superseded):** current flow = OIDC dispatch (`pypi-publish.ps1 -Target testpypi|pypi`) — see **`CONTRIBUTING.md`**; historical checklist below used API token.
- [ ] **`.vscode/`** — untracked at EOD; ignore, gitignore, or commit settings **only** if intentional.

---

## End of day

- **`eod-sync`** or **`.\scripts\operator-day-ritual.ps1 -Mode Eod`**
- Skim **`OPERATOR_TODAY_MODE_2026-04-21.md`** next (create from template if needed)

---

## Quick references

- **`docs/ops/CURSOR_AGENT_POLICY_HUB.md`** — situational “today” + workstation clock
- **`scripts/pypi-publish.ps1`** · **`CONTRIBUTING.md`** (PyPI)
- Session keywords: **`private-stack-sync`**, **`eod-sync`**
