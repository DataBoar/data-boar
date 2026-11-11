# Plan: dashBOARd mascot presence per screen and refreshed favicon (branding)

**Status:** In progress (favicon, About page and README banner done; two illustrations blocked on assets)
**Date:** 2026-11-11
**Authors:** Fabio Leitao
**Priority:** H2
**GitHub:** [#1450](https://github.com/DataBoar/data-boar/issues/1450)
**Depends on:** canonical mascot art from the public site repository (`images/`)

<!-- plans-hub-summary: Refresh the dashBOARd branding: new favicon set, the pot mascot on the About page and as the README banner, and (blocked on art) contextual illustrations for the reports empty state and the idle dashboard; working screens keep only the small mark. -->
<!-- plans-hub-related: PLAN_WEB_GUI_DESIGN_SYSTEM_EVOLUTION.md, PLAN_DASHBOARD_MOBILE_RESPONSIVE.md -->

## Context

The brand was recreated (the boar mascot and the DataBoar wordmark). The dashBOARd should reflect it
without turning a forensic-style tool into a mascot parade. Rule: **constant anchor** (small mark or
favicon on every screen) plus a **large illustration only on threshold or empty screens**; working
screens stay clean. Layered brand doctrine: detailed 3D mascot art is rare (favicon, hero), flat marks
may repeat sparingly.

## Source of the assets

The public site repository (`images/`) is the canonical source. On 2026-11-11 it holds the favicon set
(`favicon.ico` at the root, `favicon-32.png`, `icon-192.png`, `apple-touch-icon.png`) and
`mascot-pot.png`. It does **not** hold `mascot-hero` nor `data-soup-pot`.

Repository convention: only `api/static/mascot/*.png` is un-ignored for PNGs, so the new PNGs live
there. The previous art (`api/static/mascot/` originals and `api/static/logo-candidates/`) is preserved
for lineage.

## Phases

| Phase | Deliverable | Status |
| ----- | ----------- | ------ |
| A | New `api/static/favicon.ico`; `favicon-32`, `icon-192`, `apple-touch-icon` under `api/static/mascot/`; links in `base.html` | ✅ Done |
| B | About page uses `mascot-pot` (generous, not giant) | ✅ Done |
| C | README banner (EN + pt-BR) centered; it keeps the site-hosted `mascot-pot` URL that `tests/test_docs_markdown.py` pins (and that PyPI can render) | ✅ Done |
| D | Reports page empty state uses `data-soup-pot` | ⬜ Blocked: asset not yet in the canonical source |
| E | Idle/ready dashboard uses `mascot-hero` (never as splash or nag) | ⬜ Blocked: asset not yet in the canonical source |
| F | Dark theme: dark wordmark variant (cream "Data", gold "Boar") if a dark theme ships | ⬜ Pending |
| G | Tests guarding asset presence, sizes and README banner (`tests/test_dashboard_branding_assets.py`) | ✅ Done |

Working screens (running scan, tables, config) keep only the small mark; no large illustration there.

## Relationship to other plans

- [PLAN_WEB_GUI_DESIGN_SYSTEM_EVOLUTION.md](PLAN_WEB_GUI_DESIGN_SYSTEM_EVOLUTION.md) (#1004) records the visual
  direction; this plan delivers the assets and their placement. Complementary, not duplicated.
- [PLAN_DASHBOARD_MOBILE_RESPONSIVE.md](PLAN_DASHBOARD_MOBILE_RESPONSIVE.md): illustrations must stay within the
  responsive layout (`max-width: 100%`).

Synced with [PLANS_TODO.md](PLANS_TODO.md).
