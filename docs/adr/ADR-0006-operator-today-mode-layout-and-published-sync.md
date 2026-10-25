# ADR 0006 — Operator today-mode layout and published-release sync

- **Status:** Accepted
- **Date (UTC):** 2026-03-30
- **Authors:** Fabio Leitao
- **Deciders:** Fabio Leitao

## Context

Dated operator checklists (`OPERATOR_TODAY_MODE_*.md`) lived next to dozens of other runbooks under `docs/ops/`, which made them easy to miss and let **carryover** items (e.g. “tag pending”) drift after GitHub Releases and Docker Hub already matched `pyproject.toml`. LLM-assisted triage (e.g. **Gemini** feedback plans) also produced actionable doc rows that needed a **durable home** without mixing them into product code.

## Decision

1. **Folder:** Keep all dated today-mode files under **`docs/ops/today-mode/`** with an index **`README.md`**, a rolling **`CARRYOVER.md`**, and **`PUBLISHED_SYNC.md`** that records **last verified** GitHub Release + Docker Hub vs **`pyproject.toml`** (refreshed after each publish).
2. **Automation boundary:** Version alignment remain guarded by tests (e.g. `pyproject.toml` ↔ runtime/man pages); **remote** publish state stays a **documented operator/agent check** listed in `PUBLISHED_SYNC.md`, not a CI network call to GitHub/Docker by default.
3. **Gemini / LLM triage** stays **non-authoritative** per existing plan policy; this ADR only records **where** promoted hygiene work lives so it is not reverted silently.

## Consequences

- Session keywords (**`today-mode`**, **`carryover-sweep`**, **`eod-sync`**) and **`scripts/operator-day-ritual.ps1`** point at **`docs/ops/today-mode/`** paths.
- Contributors open **`docs/ops/today-mode/README.md`** instead of searching flat `docs/ops/` for dates.
- After each release, update **`PUBLISHED_SYNC.md`** and matching **`docs/plans/PLANS_TODO.md`** rows to avoid “immortal pending” release tasks.

## References

- `docs/ops/today-mode/README.md` — index and conventions.
- `docs/plans/PLAN_GEMINI_FEEDBACK_TRIAGE.md` — LLM triage promotion rules (non-canonical until merged into plans/issues).
- `.cursor/rules/session-mode-keywords.mdc` — operator tokens.
