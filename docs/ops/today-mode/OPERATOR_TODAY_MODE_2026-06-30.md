# Operator today-mode — 2026-06-30 (Dependabot land · housekeeping close · roadmap)

**pt-BR:** [OPERATOR_TODAY_MODE_2026-06-30.pt_BR.md](OPERATOR_TODAY_MODE_2026-06-30.pt_BR.md)

**Headline:** Land stalled **Dependabot** PRs (validate locally — **no blind merge**; **`rpds-py` cap** per ADR-0069) → close in-flight **housekeeping** ([#91](https://github.com/FabioLeitao/data-boar/issues/91) / [#1062](https://github.com/FabioLeitao/data-boar/pull/1062) already on `main`) → **licensing ladder** follow-up ([#887](https://github.com/FabioLeitao/data-boar/issues/887) — **#1097** shipped Std/Pro+/Partner) → **quick-wins** ([#1089](https://github.com/FabioLeitao/data-boar/issues/1089)–[#1096](https://github.com/FabioLeitao/data-boar/issues/1096)).

**`main` anchor:** post-**#1097** merge (tier + security slice); **`pyproject.toml`** = **`1.7.4.post1`**. **Published stable:** [PUBLISHED_SYNC.md](PUBLISHED_SYNC.md) (**v1.7.4** GitHub + Hub **`latest`**).

---

## Block 0 — Morning reality (10–15 min)

Run **`carryover-sweep`** / **`morning-readiness`**. Then:

1. **`origin/main`:** `git fetch` · `git status -sb` · `gh run list --workflow ci.yml --branch main --limit 1`.
2. **Dependabot:** `gh pr list --author "app/dependabot" --state open` — **RED** triage **#1029** · **#1025** · **#1011** · **#975** · stale **#974**; **VERDE** **#1010** ✅ merged · **#915** hatchling (apply local) · **#912** Sonar (`workflow` scope or web merge).
3. **Stacked private git:** **`private-stack-sync`** if `docs/private/` changed since last push.

**Rolling queue:** [CARRYOVER.md](CARRYOVER.md) · **Published truth:** [PUBLISHED_SYNC.md](PUBLISHED_SYNC.md)

### Social / editorial (~2 min)

- [ ] Skim **`docs/private/social_drafts/editorial/SOCIAL_HUB.md`** — [SOCIAL_PUBLISH_AND_TODAY_MODE.md](SOCIAL_PUBLISH_AND_TODAY_MODE.md).

---

## Priority table

| Order | Track | Intent | Notes |
| ----- | ----- | ------ | ----- |
| **1** | **Dependabot land** | Close or supersede open PRs with local bumps + green CI | Skill: `.cursor/skills/dependabot-recommendations/SKILL.md`; **never** merge **`rpds-py` 2026.x** (ADR-0069) |
| **2** | **Housekeeping** | **#1062** ✅ · **#91** ✅; push **`houseclean/plans-drift-archive-91`** / **`plans-wave-2`** if still off `main` | No new **feature** epic until wave 2 lands unless operator overrides |
| **3** | **Licensing roadmap** | **#887** — enum enforced in **#1097**; close issue + any doc delta in **#853** ladder | Courtesy nudge gated Std+ (ADR-DRAFT-0076) |
| **4** | **Quick-wins** | **#1089–#1092** closed via **#1097**; **#1096** triage remainder; **#1093–#1095** governance slice | **#1080** already closed (**#1087**) |
| **5** | **Defer** | SDK **#865** · research **#1081–#1085** · 1.8 enrich **#1057–#1061** | Token-budget tail |

---

## Carryover — today

- [ ] Re-run **`gh pr checks`** on any Dependabot branch before merge (stale checks block branch protection).
- [ ] **`#912`:** `gh auth refresh -s workflow` or merge via GitHub UI.
- [ ] Confirm **`houseclean/*`** branches: open PR or delete if superseded.

---

## End of day

- **`eod-sync`** + **`private-stack-sync`** if needed.
- Next: **`OPERATOR_TODAY_MODE_2026-07-01.md`** at next session boundary.

---

## Quick references

- Dependabot / deps: **`SECURITY.md`** · ADR-0069 (`rpds-py`)
- Session keywords: **`.cursor/rules/session-mode-keywords.mdc`**
