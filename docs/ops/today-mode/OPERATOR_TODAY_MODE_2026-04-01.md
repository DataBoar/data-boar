# Operator today mode — 2026-04-01 (release-ready slice, token-aware)

**Português (Brasil):** [OPERATOR_TODAY_MODE_2026-04-01.pt_BR.md](OPERATOR_TODAY_MODE_2026-04-01.pt_BR.md)

**Purpose:** Ship one **coherent, reviewable slice** toward production readiness, without carrying silent backlog. Boundaries: **`carryover-sweep`** · **`eod-sync`** · **`scripts/operator-day-ritual.ps1`**.

---

## Block 0 — Truth + carryover (≈ 15–25 min)

1) Walk **[CARRYOVER.md](CARRYOVER.md)** — close, defer with date, or promote to PLANS/issue for each ⬜.
1) Confirm version truth (see **[PUBLISHED_SYNC.md](PUBLISHED_SYNC.md)**):
   - **Published**: **`v1.6.8`** on GitHub + Docker Hub when the release pipeline is complete; if Hub lags, track it there — do not tell customers a version they cannot pull yet.
   - **Working**: `main` should match **`pyproject.toml`**; pre-release suffixes (`-beta`/`-rc`) are working only.

---

## Block A — Ship the Cursor/MCP + version tracking slice (≈ 30–60 min)

- If anything still separates **working** from **published** (e.g. open PR for **1.6.8** docs slice), close it; otherwise skip.
- Keep it **workflow/docs focused**; no feature work mixed in this PR.

**Token-aware gate:** `.\scripts\lint-only.ps1` is enough for this slice (already green locally).

---

## Block B — WRB (Corporate-Entity-C) and minimal evidence (≈ 20–40 min)

- Use the paste block: **`docs/ops/WRB_DELTA_SNAPSHOT_2026-03-31.md`**
- Update its “Version truth” bullets if the baseline moved (published **`v1.6.8`** per **PUBLISHED_SYNC**).
- Send the email (or explicitly defer with a date in **CARRYOVER**).

---

## Block C — Slack ping proof-of-life (≈ 10–15 min)

- Follow **`docs/ops/OPERATOR_NOTIFICATION_CHANNELS.md`** and record a **CHAN-OK** note once phone + desktop alert is confirmed.

---

## Stop condition

Day slice is **done** when:

- **CARRYOVER** updated (no silent pending).
- Any **version/docs** PR needed for **1.6.8** publish truth is **closed** or **N/A** (see **PUBLISHED_SYNC**).
- WRB is **sent** (or deferred with a date).
- Slack ping is **confirmed** (or deferred with a date).
