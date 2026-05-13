# Plan (future): public website, marketing depth, and extra doc languages

**Status:** Pending
**Date:** 2026-03-21
**Authors:** Fabio Leitao
**Priority:** H3

**Purpose:** Capture intent so we do not forget: a **stronger public surface** (site + optional extra languages) aligned with **branding** (Data Boar / dashBOARd, data soup narrative) and **trust** (releases, docs, use cases).

---

## 1. Documentation in additional human languages

- **Today:** User-facing docs are **English (canonical)** + **Brazilian Portuguese (pt-BR)** per [docs-policy](../../.cursor/rules/docs-policy.mdc).
- **Later (evaluate):** Add languages that match **markets or compliance narratives** you care about — e.g. **Spanish (es)** for LatAm, **Japanese (ja)**, **Russian (ru)**, **Arabic (ar)** when there is a **concrete channel, customer request, or partner**—not speculative “translate everything.” Each new language implies **ongoing sync** cost with EN; treat as a **deliberate** decision, not a one-off translation burst. **Compliance sample YAML** (e.g. **152-FZ** with EN+RU terms) can lead **ahead** of full doc translation where regulations require local language in **data labels and reports** first.
- **Pilot scope (optional third locale before full GTM):** If you add **one** extra language beyond the default **EN + pt-BR**, treat it as a **pilot**: **mirror EN** and **code truth**, and **limit the first wave** to **high-traffic** tracked surfaces (e.g. root **README** pitch block, **`docs/COMPLIANCE_AND_LEGAL.md`**) unless you commit to maintaining the **full** doc tree in that locale — same discipline as EN ↔ pt-BR, extended per file.
- **Mechanics (when ready):** Mirror the existing EN ↔ pt-BR pattern: language switchers, index rows in `docs/README.md`, and a rule for which files are translated (product docs yes; `docs/plans/` may stay EN-only).
- **Encoding / scripts:** Repo docs and the **dashBOARd** reuse the same **Unicode-first** assumptions as the scan pipeline (Cyrillic, CJK, Arabic script in **examples and report text** today; **full localized UI strings** follow the dashboard milestones in [PLAN_DASHBOARD_I18N.md](completed/PLAN_DASHBOARD_I18N.md)). **Public suggestions** (issues) for missing locales or charset edge cases are welcome; **consulting** can fund **priority** translation or custom compliance wording. A **public** language list (Asian, African, European regional—**Mandarin**, **Cantonese**, **Indonesian**, **Amharic**, **Catalan**, **Basque**, etc.) lives in the repository **README** roadmap paragraph so **marketing** and **buyer** surfaces do not deep-link into this plan file.

---

## 2. Full descriptive / marketing website (possibly multilingual)

**Goal:** A **dedicated site** (not only GitHub README) for **discovery**, **pitch**, and **credibility** — similar in *role* to how serious projects present themselves (e.g. **FreeBSD**, **Ubuntu**, **Snort**, **pfSense**): clear value prop, downloads/releases, docs entry points, and community or commercial CTA. **Form** (static vs CMS, exact layout) is TBD; **content pillars** should include:

| Pillar                | Notes                                                                                                                      |
| ------                | -----                                                                                                                      |
| **Pitch**             | Decision-maker narrative; optional **longer** “deep pitch” page.                                                           |
| **Use cases**         | Sectors, scan/report stories, compliance framing (without overclaiming).                                                   |
| **How-tos**           | Short guided paths that link into **canonical** `docs/` (USAGE, DEPLOY) so we do not fork truth.                           |
| **Documentation hub** | Links or embedded paths to **version-synced** docs (same major/minor as releases).                                         |
| **Releases**          | Prominent links to **GitHub Releases**, **Docker Hub** tags, and `docs/releases/`.                                         |
| **Branding**          | Mascot, dashBOARd sub-brand, visual consistency with [COPYRIGHT_AND_TRADEMARK.md](../COPYRIGHT_AND_TRADEMARK.md) guidance. |

**Hosting:** See [HOSTING_AND_WEBSITE_OPTIONS.md](../HOSTING_AND_WEBSITE_OPTIONS.md) (static site options). Keep **no secrets** on the public site.

**i18n on the site:** If the site is multilingual, define **which locales** ship first and how they stay aligned with EN source copy (same discipline as repo docs).

### 2.1 Website vs pitch deck vs GitHub docs — **depth contract** (not scheduled yet)

**We are not building the public website now** — this subsection is a **planning memory** so GTM work does not collapse everything into one surface.

| Surface                                                                                                           | Role                                                                                                | **Depth** — what belongs here                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      |
| -------                                                                                                           | ----                                                                                                | ------------------------------                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     |
| **Stakeholder pitch** (e.g. private `docs/private/pitch/`, `.pptx` pairs, short live talk)                        | Convince and qualify; **Data Boar** story, mascot / **data soup** metaphor, outcomes, trust framing | **Shallow technical:** almost no HOWTO, no config dumps, no operator runbooks. **Not** a substitute for compliance review.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         |
| **GitHub — README + “compliance & legal” tree** (`docs/COMPLIANCE_AND_LEGAL.md`, frameworks, licensing, SECURITY) | Canonical **legal/compliance narrative**, exportable PDFs mindset, open-core boundary               | **Legal and governance depth** — still **not** the full HOWTO layer; deep **usage** stays in `USAGE` / `TECH_GUIDE` etc.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           |
| **Future public website**                                                                                         | Discovery, downloads, **documentation hub**, credibility, CTA                                       | **Major difference vs pitch:** hosts (or **deep-links in a version-aware way**) the **full technical layer**: **USAGE**, **TECH_GUIDE**, **TESTING**, **DOCKER_SETUP** / deploy, **compliance-samples** walkthroughs, **scenario** pages, **release notes** (`docs/releases/`), a **richer roadmap** naming **specific active fronts** (what you are actually building — connectors, dashboard, notifications, …), prominent **Docker Hub** and **GitHub repo** links, changelog / security pointers. **Keep in sync** with the repo as capabilities evolve (CI link checks, same major/minor as tagged releases). |

**Rule of thumb:** If a buyer **needs to install, tune, or audit** behaviour, that content **lives on the future site (or linked canonical docs)** — not in the pitch deck or the compliance-legal **summary** tone of the presentation.

### 2.2 Same multilingual “tricks” as **dashBOARd**

When the site ships, **reuse the same i18n design choices** planned for the dashboard HTML surface — see [PLAN_DASHBOARD_I18N.md](completed/PLAN_DASHBOARD_I18N.md): **path-prefixed** locales (e.g. `/en/`, `/pt-br/`), **cookie → `Accept-Language` → configured fallback**, **JSON** message catalogs (or mirrored pattern for static site generators), and **CI key parity** across locale files where applicable. **D-WEB** / **M-LOCALE-V1** remain the **product** implementation; the **marketing site** should **not invent a conflicting** locale scheme.

### 2.3 Presentation refresh ↔ website readiness (cadence cue)

- As **capabilities** grow (new connectors, report types, governance features), expect to produce a **new stakeholder presentation pair** (e.g. refreshed `.pptx` or `slides.yaml` **EN + pt-BR** under `docs/private/pitch/`).
- **Heuristic:** when you **rewrite the pitch** for a new selling story, treat it as a **trigger** to **schedule** (not necessarily ship immediately) a **website content pass**: roadmap section, release links, technical hub TOC, and “what’s new” — so the **public** story does not lag the **private** deck.
- **pt-BR copy** in the deck (and later on the **public** `pt-br/` site) should follow **Brazilian** Portuguese, not European forms — same bar as **`*.pt_BR.md`** (see **`.cursor/rules/docs-pt-br-locale.mdc`**). If `slides.yaml` or flattened **`SLIDES_WEBSITE_SYNC.pt_BR.md`** ever live in **tracked** paths, extend **`tests/test_docs_pt_br_locale.py`** (`_extra_locale_scan_paths`) so CI catches regressions.
- The **website** remains the **deep** layer; the **presentation** stays **derivative and shallow-technical**, seeded from the same brand narrative.

---

## 3. Dependencies and sequencing (high level)

1. **Stable product story** — version cadence, support posture, and what we promise publicly.
1. **Legal / trademark** — counsel pass on public claims and name use where needed.
1. **Content owner** — who approves site copy and translations.
1. **Automation** — optional CI to publish from a `website/` repo or branch; link checker for docs URLs.

---

## 4. Related tracked material

- [SPRINTS_AND_MILESTONES.md](SPRINTS_AND_MILESTONES.md) — milestone **M-SITE-READY** (first public site + doc hub) and Kanban pointer.
- [HOSTING_AND_WEBSITE_OPTIONS.md](../HOSTING_AND_WEBSITE_OPTIONS.md) — hosting memo.
- [LICENSING_OPEN_CORE_AND_COMMERCIAL.md](../LICENSING_OPEN_CORE_AND_COMMERCIAL.md) — pitch and open-core boundary.
- [PLANS_TODO.md](PLANS_TODO.md) — backlog pointer to this file.
- [README.md](../../README.md) — current public entry point until a site exists.

---

## 5. When to activate

Promote this from “reminder” to a **sprint-sized** initiative when:

- Homelab / second-environment confidence is in a good state (**–1L** / **M-LAB**), and
- Priority band **A** hygiene is not blocking, and
- You have bandwidth for **ongoing** translation + site maintenance.

Until then, **no obligation** to implement; this file is the **memory hook**.
