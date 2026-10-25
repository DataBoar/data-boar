# Operator today mode — 2026-05-18 (morning pickup)

**Português (Brasil):** [OPERATOR_TODAY_MODE_2026-05-18.pt_BR.md](OPERATOR_TODAY_MODE_2026-05-18.pt_BR.md)

**Note:** **`main`** at **`acfaaf49`** includes PMO hierarchy + **2026-05-19** draft checklist — pull if needed.

---

## Block 0 — Morning reality (10–15 min)

Run **`carryover-sweep`** or **`.\scripts\operator-day-ritual.ps1 -Mode Morning`**. Then:

1. **`origin/main`:** `git fetch` · `git status -sb` · `git pull origin main` when behind — confirm **`ci.yml`** green on **`main`** before deep work.
2. **Open PRs:** `gh pr list --state open` — e.g. **#348** (deps), **#365** (draft mute Slack)— merge when green per **`.\scripts\pr-merge-when-green.ps1`** where safe.
3. **Plans PMO:** **[PLANS_DOCUMENTATION_HIERARCHY.md](../PLANS_DOCUMENTATION_HIERARCHY.md)** — issue chat decides; **`docs/plans/`** persists.
4. **Tonight’s checklist:** skim **[OPERATOR_TODAY_MODE_2026-05-19.md](OPERATOR_TODAY_MODE_2026-05-19.md)** for tomorrow handoff.

**Rolling queue:** [CARRYOVER.md](CARRYOVER.md) · **Published:** [PUBLISHED_SYNC.md](PUBLISHED_SYNC.md)

### Social / editorial (private hub) — ~2 min

- [ ] Skim **`docs/private/social_drafts/editorial/SOCIAL_HUB.md`** for **2026-05-18** / **2026-05-19** — [SOCIAL_PUBLISH_AND_TODAY_MODE.md](SOCIAL_PUBLISH_AND_TODAY_MODE.md).

---

## Carryover — spine

| Track | Item | Notes |
| ----- | ---- | ----- |
| Pilot gate | **M-PILOT-READY** | **PLANS_TODO** + release **#406** / **v1.7.4** when criteria met. |
| Plans ops | **CLI / contacts plans** | [PLAN_CLI_VALIDATE_DIFF_AND_DSAR_EXPORT.md](../../plans/PLAN_CLI_VALIDATE_DIFF_AND_DSAR_EXPORT.md), [#512](https://github.com/FabioLeitao/data-boar/issues/512) triage. |
| Governance | **Dependabot** | GitHub shows low sev alert on **`main`** — triage when you open **Security**. |

---

## End of day (**2026-05-18**)

- **`eod-sync`** or **`block-close`** — [README.md](README.md).
- If **`docs/private/`** changed: **`.\scripts\private-git-sync.ps1 -Push`**.
