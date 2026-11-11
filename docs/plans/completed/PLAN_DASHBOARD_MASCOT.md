# Plan: dashBOARd mascot presence per screen and refreshed favicon (branding)

**Status:** Complete (archived in `docs/plans/completed/`)
**Date:** 2026-11-11
**Authors:** Fabio Leitao
**Priority:** H2
**GitHub:** [#1450](https://github.com/DataBoar/data-boar/issues/1450)
**Depends on:** canonical mascot art from the public site repository (`images/`)

<!-- plans-hub-summary: dashBOARd branding refresh, complete: new favicon set, the final mascot set replacing the legacy art in every template, large illustration only on About, the empty Reports state and the idle dashboard, and the small face mark on every screen. -->
<!-- plans-hub-related: PLAN_WEB_GUI_DESIGN_SYSTEM_EVOLUTION.md, PLAN_DASHBOARD_MOBILE_RESPONSIVE.md -->

## Context

The brand was recreated (the boar mascot and the DataBoar wordmark). The dashBOARd should reflect it
without turning a forensic-style tool into a mascot parade. Rule: **constant anchor** (small face mark
or favicon on every screen) plus a **large illustration only on threshold or empty screens**; working
screens stay clean. Layered brand doctrine: detailed 3D mascot art is rare (favicon, hero), flat marks
may repeat sparingly.

## Source of the assets

The public site repository (`images/`) is the canonical source; the product keeps **byte-identical
copies** in `api/static/mascot/` (the only folder where PNGs are un-ignored). The final set:

| File | What it is | Used in |
| ---- | ---------- | ------- |
| `mascot-pot.png` | boar with the soup pot, tusk fixed | About page |
| `mascot-hero.png` | the boar alone (pot area transparent) | idle dashboard, hidden while a scan runs |
| `data-soup-pot.png` | the pot and steam alone (boar transparent) | Reports page, empty state |
| `mascot-mark-face.png` | the face (mark) | small anchor in every page heading and in the dashboard footer |
| `favicon.ico`, `favicon-32.png`, `icon-192.png`, `apple-touch-icon.png` | favicon set | `base.html` |

The previous art (the original SVG and its derivatives under `api/static/mascot/`, and
`api/static/logo-candidates/`) is **preserved for lineage** and is no longer used by any dashboard
template.

## Phases

| Phase | Deliverable | Status |
| ----- | ----------- | ------ |
| A | New `api/static/favicon.ico`; `favicon-32`, `icon-192`, `apple-touch-icon` under `api/static/mascot/`; links in `base.html` | ✅ Done |
| B | About page uses `mascot-pot` (generous, not giant) | ✅ Done |
| C | README banner (EN + pt-BR) centered; it keeps the site-hosted `mascot-pot` URL that `tests/test_docs_markdown.py` pins (and that PyPI can render) | ✅ Done |
| D | Reports page empty state uses `data-soup-pot` | ✅ Done |
| E | Idle dashboard uses `mascot-hero` (inline, never a splash or nag; hidden while a scan runs) | ✅ Done |
| F | Dark theme: dark wordmark variant | ✅ Not applicable: the dashboard has no dark theme |
| G | Tests guarding asset presence, sizes, alpha cutouts, placement rule and the banner (`tests/test_dashboard_branding_assets.py`) | ✅ Done |
| H | Replace every legacy-art usage in templates with the new set (full grep, none left); small face mark on every screen | ✅ Done |

Working screens (running scan, tables, config) keep only the small mark; no large illustration there.

## Known leftovers (outside this issue)

The Excel report (`report/generator.py`) still embeds the legacy `data_boar_mascote_color_full.png`, and
`scripts/build_favicon.py` still builds a favicon from the legacy art. Both are documented as legacy in
`docs/MASCOT.md`; changing the report artwork is a separate decision.

## Relationship to other plans

- [PLAN_WEB_GUI_DESIGN_SYSTEM_EVOLUTION.md](../PLAN_WEB_GUI_DESIGN_SYSTEM_EVOLUTION.md) (#1004) records the visual
  direction; this plan delivered the assets and their placement. Complementary, not duplicated.
- [PLAN_DASHBOARD_MOBILE_RESPONSIVE.md](../PLAN_DASHBOARD_MOBILE_RESPONSIVE.md): illustrations stay within the
  responsive layout (`max-width: 100%`).

Synced with [PLANS_TODO.md](../PLANS_TODO.md).
