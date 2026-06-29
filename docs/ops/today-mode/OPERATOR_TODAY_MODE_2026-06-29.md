# Operator today-mode — 2026-06-29 (housekeeping wave 2 · TestPyPI · pause audits)

**pt-BR:** [OPERATOR_TODAY_MODE_2026-06-29.pt_BR.md](OPERATOR_TODAY_MODE_2026-06-29.pt_BR.md)

**Headline:** **Rest + token refill day** — finish **plans/housekeeping** before new **feature** slices. **TestPyPI** has **`1.7.4`** + **`1.7.4.post1`** (2026-06-27); local **`pyproject.toml`** = **`1.7.4.post1`**. **Claude Code** legacy-hardware / **pipx** / Alpine **musl** investigation (no-AVX Celeron ~2009, ML stack without DL) **not yet in public repo** — capture when allowance refills (~**17:00** operator-local).

**`main` anchor:** `07b5dc50` — **#1052** PyPI OIDC merge; **`ci.yml` green** (last run **2026-06-27**). **Published stable:** [PUBLISHED_SYNC.md](PUBLISHED_SYNC.md) (**v1.7.4** GitHub + Hub); TestPyPI is **separate** — [test.pypi.org/project/data-boar](https://test.pypi.org/project/data-boar/).

**In-flight (public git, not on `main`):** branch **`houseclean/plans-drift-archive-91`** — commit **`61df9df0`** (archive 5 completed plans + detection/secrets status); **4 link fixes unstaged** (PII gate on stage). **PR [#1062](https://github.com/FabioLeitao/data-boar/pull/1062)** — **#1056** docs survey (**merge after** or **rebase with** plans-drift).

---

## Block 0 — Morning reality (10–15 min)

Run **`carryover-sweep`** / **`morning-readiness`**. Then:

1. **`origin/main`:** `git fetch` · `git status -sb` · `gh run list --workflow ci.yml --branch main --limit 1`.
2. **Open PRs:** `gh pr list --state open` — **product:** **#1062** · **houseclean:** push/open PR for **`houseclean/plans-drift-archive-91`** · **Dependabot:** hold unless **`deps`** session (**#974** `py7zr` still a sane first pick).
3. **Stacked private git:** EOD **2026-06-29** ran **`./scripts/private-git-sync.sh --push`** — private **`1fddf98`**; bare **origin** + configured **lab-*** mirrors OK — re-run **`private-stack-sync`** if any mirror push did not finish.
4. **Token budget:** Composer-first until premium refill (~**17:00**); **no** heavy audit/investigation marathons before refill unless you explicitly promote one row.

**Rolling queue:** [CARRYOVER.md](CARRYOVER.md) · **Published truth:** [PUBLISHED_SYNC.md](PUBLISHED_SYNC.md)

### Social / editorial (~2 min)

- [ ] Skim **`docs/private/social_drafts/editorial/SOCIAL_HUB.md`** — [SOCIAL_PUBLISH_AND_TODAY_MODE.md](SOCIAL_PUBLISH_AND_TODAY_MODE.md).

---

## Priority — housekeeping before features

**Rule:** No new **feature** epic until **housekeeping wave 2** lands on `main` (or explicit operator override).

| Order | Track | Intent | Notes |
| ----- | ----- | ------ | ----- |
| **1** | **Plans drift #91** | Merge **`houseclean/plans-drift-archive-91`** | 5 plans → `completed/`; **detection** stays **Active** (#1056); **secrets** Phase A only; fix **4 links** via allowlist or generic hostnames — separate micro-PR if needed |
| **2** | **Plans drift wave 2** | Archive easy wins + `PLANS_TODO` honesty | **`PLAN_OPERATING_DOMAIN_*`** (all ✅, #483 closed) · **`PLAN_SCOPE_IMPORT_*`** (phases A–E on `main`, reconcile C/E text) · **`PLAN_CLI_VALIDATE_*`** if **#520–#522** closed · **HTTPS** phase table in `PLANS_TODO` still ⬜ while plan is **completed/** |
| **3** | **#1056 / #1062** | Merge docs survey after rebase on `main` | Then **#1057→#1058→#1059→#1061→#1060** (docs-first order agreed) |
| **4** | **Legacy pipx / Alpine** | Promote Claude investigation → tracked plan or ADR | Hardware: single-core Celeron ~2009, **no AVX**, Alpine **musl**, numpy/scipy/pandas/sklearn **ML (not DL)** — evidence in **`docs/private/`**; **do not** paste LAN/PII in public PR |
| **5** | **Defer** | **A.I.I.D.C.O.B.P.P. v2**, Maestro e2e, **deps** bulk (**#1025**) | After housekeeping green |

**Yesterday / session (do not lose):** TestPyPI **`1.7.4.post1`** published **2026-06-27**; audits paused — **merited rest**.

---

## Carryover — secondary

- [ ] Confirm **TestPyPI** vs **`pyproject.toml`** / **`PUBLISHED_SYNC`** narrative (Test ≠ production PyPI).
- [ ] **`gh pr checks`** on **#1062** before merge.
- [ ] Refresh stale **CARRYOVER** row **“v1.7.4-rc on main”** → shipped.
- [ ] **Premium roster (2026-07-09):** planning only.

---

## End of day (2026-06-29)

- **`eod-sync`** + **`private-stack-sync`** if private or homelab evidence changed.
- Next checklist: **`OPERATOR_TODAY_MODE_2026-06-30.md`** at next **`eod-sync`**.

---

## Quick references

- Session keywords: `today-mode`, `carryover-sweep`, `eod-sync`, `houseclean`, `private-stack-sync`, `block-close`
- Plans PMO: `docs/plans/PLANS_TODO.md`, `PLAN_TAXONOMY_AXES.md`, internal housekeeping **#91** (Claude Code — not a GitHub issue)
- Token-aware: `docs/plans/TOKEN_AWARE_USAGE.md`
