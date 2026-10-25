# Operator today mode — 2026-04-22 (post PR #213: README pitch, plans hub, compliance mirrors)

**Português (Brasil):** [OPERATOR_TODAY_MODE_2026-04-22.pt_BR.md](OPERATOR_TODAY_MODE_2026-04-22.pt_BR.md)

**Theme:** **`main`** should include **PR #213** (README stakeholder pitch + deck vocabulary, **ADR 0035**, plans hub/todo wording, **COMPLIANCE** / **GLOSSARY** / **TECH_GUIDE** / **TESTING** touch-ups, **`test_readme_stakeholder_pitch_contract`**). **First:** **`git fetch origin`** · **`git checkout main`** · **`git pull origin main`** — confirm tip of **`origin/main`** and clean **`git status`**. **Then:** pick the next **`PLANS_TODO.md`** row or a small **`feature`** slice; run **`.\scripts\check-all.ps1`** before any new PR. **Stacked private:** sync if **`docs/private/`** changed — **`.\scripts\private-git-sync.ps1`**.

---

## Block 0 — Morning reality check (10–15 min)

Run **`carryover-sweep`** or **`.\scripts\operator-day-ritual.ps1 -Mode Morning`**. Then:

1. Confirm **no open PR** supersedes doc README pitch work ( **`gh pr list --state open`** ).
2. Optional quick doc guard: **`uv run pytest tests/test_readme_stakeholder_pitch_contract.py tests/test_docs_pt_br_locale.py -q`**

**Rolling queue:** [CARRYOVER.md](CARRYOVER.md) · **Published truth:** [PUBLISHED_SYNC.md](PUBLISHED_SYNC.md)

### Social / editorial (private hub) — ~2 min

- [ ] Skim **`docs/private/social_drafts/editorial/SOCIAL_HUB.md`** for **Alvo** matching **2026-04-22** — [SOCIAL_PUBLISH_AND_TODAY_MODE.md](SOCIAL_PUBLISH_AND_TODAY_MODE.md).

---

## Carryover — from prior EOD

- [ ] **`main`** fast-forwarded after **#213** merge — no stray **`docs/readme-stakeholder-pitch-restore`** work left unpulled unless you open a follow-up branch.
- [ ] **Private git:** ritual may have flagged pending lines — commit/push private repo when appropriate (no secrets in public PRs).

---

## End of day

- **`eod-sync`** or **`.\scripts\operator-day-ritual.ps1 -Mode Eod`**
- Skim **`OPERATOR_TODAY_MODE_2026-04-23.md`** next (create from this file if needed)

---

## Quick references

- **`docs/adr/ADR-0035-readme-stakeholder-pitch-vs-deck-vocabulary.md`** — pitch vs deck wording
- **`docs/plans/PLANS_TODO.md`** · **`docs/plans/PLANS_HUB.md`**
- Session keywords: **`eod-sync`**, **`carryover-sweep`**, **`pmo-view`**
