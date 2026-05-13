# Dashboard mobile responsive layout

**Status:** Deferred
**Date:** 2026-04-12
**Authors:** Fabio Leitao
**Priority:** H2

**Synced with:** [PLANS_TODO.md](PLANS_TODO.md) (Tier 4 / `[H3][U2]`), [SPRINTS_AND_MILESTONES.md](SPRINTS_AND_MILESTONES.md) (dashboard web surface). **Independent** of dashboard i18n (**D-WEB** / **M-LOCALE-V1** in [PLAN_DASHBOARD_I18N.md](completed/PLAN_DASHBOARD_I18N.md)) — ship responsive CSS first where possible. **Retest** after locale-prefixed routes or **#86** RBAC changes ([PLAN_DASHBOARD_REPORTS_ACCESS_CONTROL.md](PLAN_DASHBOARD_REPORTS_ACCESS_CONTROL.md)).

## When implementing: update USAGE/TECH_GUIDE touch if operator-visible; update PLANS_TODO.md / sprints / this file; run `plans-stats` + `plans_hub_sync` if tables change.

## Purpose

Make the **operator dashboard** (Jinja + shared CSS) **usable on narrow viewports** (phone and small tablet browsers): no horizontal clipping of critical actions, readable tables, touch-friendly controls, and a navigation pattern that works without a desktop-wide horizontal nav bar.

## Why it matters

- Operators legitimately **open the dashboard from a phone** on VPN or on-call (status, start scan, grab a report link).
- Current layout is **desktop-first** (`api/static/style.css`, flex nav, wide tables).
- **CSS-first** keeps scope bounded (no SPA, no new JS framework) — aligned with [completed NEXT_STEPS](completed/NEXT_STEPS.md) “no WebSocket/streaming UI” posture.

## Scope and boundaries

| In scope | Out of scope |
| -------- | ------------ |
| **CSS** media queries and layout tweaks in `api/static/style.css` (and minimal template class hooks if needed) | Replacing server-rendered UI with a SPA or mobile app |
| **Templates** under `api/templates/` — nav wrapping, table wrappers, optional scroll regions | Push notifications or PWA install prompts |
| **Touch-friendly** targets (buttons, links) where they are too tight on 320–390px width | Full redesign system (**D-WEB**) — coordinate, but do not block a minimal responsive pass |
| **Chart** area (`dashboard.html` / JS) — scales or scrolls without breaking the page | New charting library |
| **Manual QA** matrix: iPhone Safari + Chrome Android (or DevTools device emulation as minimum before merge) | Automated visual regression suite (optional follow-up) |

## Baseline (current implementation)

- **Viewport:** `base.html` already includes `<meta name="viewport" content="width=device-width, initial-scale=1.0">`.
- **Nav:** `.nav` is a single horizontal `flex` row with five links — **likely to overflow** on narrow screens.
- **Tables:** `.table` is full-width without horizontal scroll wrapper on small screens — **sessions / reports** tables may require **overflow-x: auto** on a parent.
- **Main:** `.main { max-width: 960px; }` — acceptable; focus on nav + tables + cards.

## Target UX (acceptance)

1. **320px width:** All primary nav destinations remain reachable (wrapped, hamburger, or stacked — **decision in M-MOBILE-AUDIT**).
1. **No critical** button or “Start scan” flow requires horizontal page scroll at common phone widths.
1. **Tables:** Session and report lists are **readable** (min font size, row height) and **scroll horizontally inside a container** where needed rather than breaking the whole page layout.
1. **Chart:** Visible without overlapping other cards; does not force infinite page width.
1. **Config / Help / About:** Long prose and monospace config editor remain usable (minimum: no worse than today; ideally padded scroll areas).

## Milestones

| ID | Name | Type | Done when |
| -- | ---- | ---- | --------- |
| **M-MOBILE-AUDIT** | **Mobile layout audit** | Doc / checklist | Written inventory of each route (`/`, `/reports`, `/config`, `/help`, `/about`): screenshot or notes for 375px and 768px; list of concrete CSS/HTML changes; nav pattern chosen (documented in this file). |
| **M-MOBILE-V1** | **Responsive v1 on `main`** | Code | Media queries + template tweaks merged; manual QA matrix passed; USAGE or TECH_GUIDE short note (“dashboard works on mobile browsers” or limitations); no regressions in existing desktop tests. |

## Implementation checklist (execute when scheduled)

1. **M-MOBILE-AUDIT:** Complete the audit table; paste or link evidence under `docs/` only if operator-approved (otherwise keep evidence local).
1. **Nav:** Implement chosen pattern — e.g. flex-wrap + shorter labels, stacked nav under `max-width`, or minimal “menu” toggle **without** heavy JS dependencies (prefer CSS + small markup change).
1. **Tables:** Wrap `.table` blocks in a scroll container class; consider `font-size` / padding on small screens.
1. **Buttons:** Ensure `.btn` / primary actions meet approximate **44px** touch target where feasible (padding, not necessarily larger text).
1. **Charts:** Confirm canvas/SVG container in `dashboard.html` + `dashboard.js` respects `max-width: 100%` and parent flex/grid.
1. **Tests:** Add or extend a **lightweight** test if feasible (e.g. template render smoke); otherwise document **manual QA** steps for CI-skipped paths.
1. **Docs:** One paragraph in USAGE (and pt-BR mirror) under web dashboard section — mobile expectations and known limitations.
1. **Follow-up:** After **M-LOCALE-V1** or **#86**, re-run manual audit on prefixed paths if HTML structure changes.

## Coordination with other plans

| Plan | Relationship |
| ---- | ------------- |
| [PLAN_DASHBOARD_I18N.md](completed/PLAN_DASHBOARD_I18N.md) | Responsive layout can ship **before** locale prefixes; **re-verify** after path prefixes (nav links, switcher). |
| [PLAN_DASHBOARD_REPORTS_ACCESS_CONTROL.md](PLAN_DASHBOARD_REPORTS_ACCESS_CONTROL.md) | RBAC may change who sees `/reports`; **retest** responsive tables after #86 phases. |
| [PLAN_WEBSITE_AND_DOCS_I18N_FUTURE.md](PLAN_WEBSITE_AND_DOCS_I18N_FUTURE.md) | **Out of scope** — public marketing site is separate. |

## See also

- `api/templates/base.html`, `api/templates/dashboard.html`, `api/templates/reports.html`, `api/static/style.css`, `api/static/app.js`, `api/static/dashboard.js`
- [TECH_GUIDE.md](../TECH_GUIDE.md) — dashboard architecture overview
- [PLANS_TODO.md](PLANS_TODO.md) — row “Dashboard mobile responsive” and Tier 4 sequencing
