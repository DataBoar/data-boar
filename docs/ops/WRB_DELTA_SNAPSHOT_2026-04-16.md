# WRB — delta snapshot for next mail (2026-04-16)

**Português (Brasil):** [WRB_DELTA_SNAPSHOT_2026-04-16.pt_BR.md](WRB_DELTA_SNAPSHOT_2026-04-16.pt_BR.md)

Paste into your Corporate-Entity-C email **after** the master prompt in [Corporate-Entity-C_REVIEW_REQUEST_GUIDELINE.md](Corporate-Entity-C_REVIEW_REQUEST_GUIDELINE.md) (sections *Report format requested…*, *Reusable request message*, and especially **Prompt mestre completo (PT-BR)** — that is the long briefing: executive + technical + DevSecOps, linguistic category model, drift checks, three time lenses, prior-recommendation verification). You can also merge into §2 in [Corporate-Entity-C_WRB_REVIEW_AND_SEND.pt_BR.md](Corporate-Entity-C_WRB_REVIEW_AND_SEND.pt_BR.md) before send.

**Suggested paste order:** (1) optional **Appreciation lead-in** (warm opening) → (2) **English paste block** (scope + hash) → (3) **Re-send note** only if a previous mail was lost.

**Before sending:** run `git rev-parse --short HEAD` and replace every **`REPLACE_WITH_SHORT_HASH`** in the paste blocks below.

---

## Version truth (avoid confusion)

- **`pyproject.toml` / docs** on `main` target **1.6.8** working toward **1.6.9** when the next bundle ships — see [PUBLISHED_SYNC.md](today-mode/PUBLISHED_SYNC.md) and [docs/VERSIONING.md](../VERSIONING.md).
- **Latest published Git tag** (market / Docker / testers baseline at last verification): **`v1.6.8`** — see [PUBLISHED_SYNC.md](today-mode/PUBLISHED_SYNC.md) (re-confirm on GitHub Releases + Docker Hub at send time).
- **`main` ahead of `v1.6.8`:** about **211** commits when this snapshot was drafted (re-run `git rev-list --count v1.6.8..HEAD` at send time). **Tip of `main`:** substitute **`REPLACE_WITH_SHORT_HASH`** in the paste blocks below with `git rev-parse --short HEAD` immediately before send (full three lenses in the guideline: cumulative history → since last Corporate-Entity-C report → since last **tagged** release to **current branch tip**).
- Ask Corporate-Entity-C to treat **“since last market delivery”** as **since `v1.6.8`**, unless they confirm a newer tag on GitHub.
- If you have **uncommitted local changes** on the dev PC, call that out as **not yet on `origin/main`** — separate lens from the tagged release.

---

## Appreciation lead-in (optional — paste before the supplementary block)

Use when you want a short, forward-looking thank-you **without** sounding like a complaint about lost context. Omit entirely if the thread is already warm.

```text
We remain very grateful for your **2026-03-18** evolution review and the **2026-03-23** premium follow-up. Both gave us a clear, actionable picture of Data Boar (maturity, documentation, security/hardening themes) and have directly shaped how we prioritize work in the repository. If e-mail context on your side has moved on, that is entirely fine: **`docs/ops/Corporate-Entity-C_IN_REPO_BASELINE.md`**, **`docs/plans/Corporate-Entity-C_ANALISE_2026-03-18.md`**, and (where helpful) **`docs/plans/Corporate-Entity-C_ANALISE_2026-03-23_EVOLUTIVA.md`** are our canonical record of what we took from your analyses. We are asking for a **forward-looking** review against **today’s** `main` (commit hash below), not a replay of old threads — and we would be glad to keep building on the partnership you have already invested in this product.
```

---

## English paste block (optional annex to the long request)

```text
Supplementary context (2026-04-16):

Since the prior WRB delta snapshot (2026-04-03), work on `main` continued toward the next release line (docs/cursor/ops alignment, ADR 0024 enterprise-discovery posture, private.example social_drafts mirrors, operator session/browser warm-session policy, scripts including ATS helper and lab-op rituals, dependency hygiene). For scope, compare **last Corporate-Entity-C delivery** (2026-03-18; tracking `docs/plans/Corporate-Entity-C_ANALISE_2026-03-18.md`) vs **current tree**, and separately **`v1.6.8` tag → `main`** (~211 commits at snapshot; not yet a new numbered release unless you have cut one since).

Please keep the **three time lenses** separate. For “since last tagged release”, use **`v1.6.8`** as baseline if that remains the latest published release at send time, and isolate **unshipped `main`** work. Use `main` at commit **REPLACE_WITH_SHORT_HASH** (run `git rev-parse --short HEAD` before send).
```

---

## Re-send note (if a previous WRB e-mail was lost)

Paste **after** the appreciation block (if used) and the supplementary block — or right after *Olá, equipe Corporate-Entity-C* in the long PT prompt — so reviewers without thread memory still have a clear anchor.

```text
Short note — re-send: We are sending this WRB request again; an earlier message may not have reached you. Please treat this e-mail (and the linked in-repo briefing paths below) as the single source of truth — we do not assume you retain context from a prior thread. Our last report from you remains the 2026-03-18 delivery; tracking: docs/plans/Corporate-Entity-C_ANALISE_2026-03-18.md. At send time, please confirm the latest GitHub tag (expected v1.6.8 unless superseded) and use `main` at commit: REPLACE_WITH_SHORT_HASH (run `git rev-parse --short HEAD` before send).
```

---

## Related

- [Corporate-Entity-C_IN_REPO_BASELINE.md](Corporate-Entity-C_IN_REPO_BASELINE.md) — paths for reviewers.
- [Corporate-Entity-C_REVIEW_REQUEST_GUIDELINE.md](Corporate-Entity-C_REVIEW_REQUEST_GUIDELINE.md) — **full WRB prompt** (EN block + PT-BR “Prompt mestre completo”).
- [PLANS_TODO.md](../plans/PLANS_TODO.md) — backlog state.
- [GEMINI_PUBLIC_BUNDLE_REVIEW.md](GEMINI_PUBLIC_BUNDLE_REVIEW.md) — safe bundle workflow (output under `docs/private/`).
