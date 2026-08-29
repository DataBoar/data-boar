# Plan (future): dashBOARd design-system evolution

**Status:** Pending
**Date:** 2026-08-29
**Authors:** Fabio Leitao
**Priority:** H3

<!-- plans-hub-summary: Intent-only: adopt tokens/components/templates from the private data-boar-design-system sibling into dashBOARd after functional GUI tracks. No private assets copied here. Milestone v1.8.0. -->

**Purpose:** Capture **intent and direction** so visual evolution of the operator HTML dashboard (**dashBOARd**) is not forgotten. This is **not** an implementation slice now.

**GitHub:** [#1004](https://github.com/DataBoar/data-boar/issues/1004)

---

## Private sibling — name and purpose only

The organisation keeps a **private** repository named **`data-boar-design-system`**. Public onboarding already lists it as the design-language home for several TUIs in the bestiary (see [CURSOR_ECOSYSTEM_ONBOARDING.md](../ops/CURSOR_ECOSYSTEM_ONBOARDING.md)).

**In this public tree we record only:**

- The **repo name**.
- The **purpose**: shared **tokens**, **components**, and **templates** that should eventually inform dashBOARd (and related operator surfaces) so the GUI does not invent a conflicting visual language.

**Hard rule:** do **not** paste, copy, or vendor **assets**, **rendered decks**, **CSS dumps**, or **component source** from that private repo into `data-boar`. Direction lives here; artefacts stay in the private clone.

---

## Why a separate plan

Existing dashboard plans cover **functional** tracks — HTTPS, mobile layout, RBAC/session, i18n. They do **not** own visual-system adoption. Mixing token/component work into those PRs would sprawl scope and risk leaking private design files.

**Depends on (sequencing, not a code import):**

- [PLAN_DASHBOARD_MOBILE_RESPONSIVE.md](PLAN_DASHBOARD_MOBILE_RESPONSIVE.md) — usable layout first.
- [PLAN_DASHBOARD_REPORTS_ACCESS_CONTROL.md](PLAN_DASHBOARD_REPORTS_ACCESS_CONTROL.md) — identity/RBAC before a visual restyle of gated routes.
- Parallel, not blocking: [PLAN_WEBSITE_AND_DOCS_I18N_FUTURE.md](PLAN_WEBSITE_AND_DOCS_I18N_FUTURE.md) (public site branding vs in-app GUI).

**Milestone:** **v1.8.0** (intent captured; implementation when the operator promotes this row).

---

## Intended phases (when promoted)

1. **Inventory (public tree only):** list current dashBOARd CSS/templates (`api/static/`, `api/templates/`) vs the **intended** token/component roles (colour, type, spacing, form, table, status) — **roles**, not copied values from the private repo.
2. **Map surfaces:** login/status, scan, reports, help/about — which should consume tokens first.
3. **Adopt incrementally:** thin PRs that change public CSS/templates **written in this repo**, informed by operator review of the private DS — still **no** binary or deck paste.
4. **Visual QA:** desktop + mobile after functional tracks; no new JS framework implied.

---

## Out of scope

- Rewriting dashBOARd as a SPA or importing a third-party component kit as a substitute for the private DS.
- Publishing private DS marketing decks on GitHub.
- Claiming dashBOARd already implements that design system.

---

## Related

- [PLANS_TODO.md](PLANS_TODO.md) — backlog pointer (order **4ds**).
- [SPRINTS_AND_MILESTONES.md](SPRINTS_AND_MILESTONES.md) — dashboard cluster / Backlog.
