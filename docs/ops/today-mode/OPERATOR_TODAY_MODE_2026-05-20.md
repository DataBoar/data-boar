# Operator today mode — 2026-05-20 (early morning)

**Português (Brasil):** [OPERATOR_TODAY_MODE_2026-05-20.pt_BR.md](OPERATOR_TODAY_MODE_2026-05-20.pt_BR.md)

**Note:** Drafted at **eod-sync** after **2026-05-19** — social + private W7 land first; product slices after **B1**.

**`main` anchor:** `05e4a4af` — **#615** INTEGRITY_HUB merged; docs batch **#608–#614** on **`main`**. **#559** tier gates merged (**#567**). Open PRs: **#365** (draft), **#348** (Dependabot).

---

## Block 0 — Morning reality (10–15 min)

Run **`carryover-sweep`** or **`.\scripts\operator-day-ritual.ps1 -Mode Morning`**. Then:

1. **`origin/main`:** `git fetch` · `git status -sb` · `git pull origin main` when behind — confirm **`ci.yml`** green on **`main`** before deep work.
2. **Open PRs:** `gh pr list --state open` — merge when green per **`.\scripts\pr-merge-when-green.ps1`** where safe (skip **#365** while **DRAFT** unless you intend to ship).
3. **Private stack:** if **`docs/private/`** changed overnight: **`.\scripts\private-git-sync.ps1 -Push`** (W7 draft **1d59afaa** already pushed to **lab-*** mirrors).
4. **Plans PMO:** Skim **`docs/plans/PLANS_TODO.md`** — **M-PILOT-READY** still open; **#606** (P0 plugin hook) blocks Enterprise tokenizer narrative.

**Rolling queue:** [CARRYOVER.md](CARRYOVER.md) · **Published:** [PUBLISHED_SYNC.md](PUBLISHED_SYNC.md)

### Social / editorial (private hub) — priority today

| Alvo | Row | Action |
| ---- | --- | ------ |
| **2026-05-20** | **B1** Bluesky | Publish `@presuntorj.bsky.social` — draft `2026-05-09_bsky_databoar_llm_incident_echo.md`; update **SOCIAL_HUB** → `published` + URL |
| **2026-05-21** | **X5** | Prep/validate thread: `uv run python scripts/social_x_thread_lengths.py` |
| **2026-05-22** | **W5 / L6 / W6** | Block editorial (LLM kit relaunch + fabioleitao gerúndio) — warm session Meta + WP |
| **2026-05-29** | **W7** | Draft ready in private — `2026-05-29_wordpress_databoar_1201_testes_pre_commit.md` (audit **1.201** passes, **259.95s**) |

See [SOCIAL_PUBLISH_AND_TODAY_MODE.md](SOCIAL_PUBLISH_AND_TODAY_MODE.md) · **`docs/private/social_drafts/editorial/SOCIAL_HUB.md`**.

---

## Suggested focus (after social)

| Priority | Item | Notes |
| -------- | ---- | ----- |
| **Social** | **B1** today | Timing before Rafael/weAi demo scheduling — public proof of engineering posture |
| **P1** | [#582](https://github.com/FabioLeitao/data-boar/issues/582) / [#583](https://github.com/FabioLeitao/data-boar/issues/583) | ADR-0056/0057 for **inv-adr** + hub pattern (pairs with **INTEGRITY_HUB**) |
| **P1** | [#578](https://github.com/FabioLeitao/data-boar/issues/578) | RULES_AND_SKILLS_HUB navigation |
| **P0** | [#606](https://github.com/FabioLeitao/data-boar/issues/606) | Minimal Enterprise plugin hook — tokenizer partnership depends on this |
| **H1** | **M-PILOT-READY** | **#406** stable **v1.7.4** + completão clean on four hosts |

---

## Carryover — spine

| Track | Item | Notes |
| ----- | ---- | ----- |
| Commercial | Rafael / weAi | POC demo OK on **1.7.3** / **1.7.4-rc**; stable **1.7.4** + MOU before tokenization pitch |
| Editorial | W7 private draft | **SOCIAL_HUB** row W7 — publish **2026-05-29** on databoar.wordpress.com |
| Pilot gate | **M-PILOT-READY** | See **PLANS_TODO** checklist — not empty queue |

---

## End of day (**2026-05-20**)

- **`eod-sync`** + **`private-stack-sync`** if private or social hub changed.
- Tomorrow checklist path: **`OPERATOR_TODAY_MODE_2026-05-21.md`** (create at next **eod-sync** if missing).
