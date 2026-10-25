# Talent pool — optional learning mini-roadmaps (by role archetype)

**Português (Brasil):** [TALENT_POOL_LEARNING_PATHS.pt_BR.md](TALENT_POOL_LEARNING_PATHS.pt_BR.md)

**Audience:** Maintainer and trusted collaborators planning **how to help people grow** while they contribute to Data Boar. This file uses **role archetypes only** — no candidate names, scores, or LinkedIn URLs (those stay under **`docs/private/`**).

**See also:** [COLLABORATION_TEAM.md](COLLABORATION_TEAM.md), [CONTRIBUTING.md](../CONTRIBUTING.md); planning entry points (no direct links from this tier per ADR 0004): `docs/plans/PORTFOLIO_AND_EVIDENCE_SOURCES.md` (study cadence, CWL sequence, PUCRS supplements), `docs/plans/PLANS_HUB.md`.

---

## 1. How to use this with a real person

1. **Match** the person to the closest archetype below (they may span two; pick a primary).
2. **Onboard** them on the **Data Boar** column first — small PRs beat long courses.
3. **Optional learning:** pick **one** external lane at a time (certificate or extension course) so progress stays visible on GitHub and on their CV.
4. **Private record:** copy **`docs/private.example/commercial/candidates/LEARNING_ROADMAP_TEMPLATE.md`** to **`docs/private/commercial/candidates/<slug>/LEARNING_ROADMAP.md`** and fill in goals, dates, and notes from your LinkedIn / interview dossier — **never commit** that tree.

---

## 2. Archetype A — Python backend (scanner, connectors, reports)

**Fits:** Engineers who ship Python features, tests, and refactors.

| Horizon                                           | Data Boar (repo)                                                                                                                                                                                                        | Career / optional certs                                                                                                                                                                                                                                 |
| -------                                           | ----------------                                                                                                                                                                                                        | ------------------------                                                                                                                                                                                                                                |
| **First 2–4 weeks**                               | [CONTRIBUTING.md](../CONTRIBUTING.md), [TESTING.md](TESTING.md), `uv sync`, `scripts/check-all.ps1` or `pytest`; read [TECH_GUIDE.md](TECH_GUIDE.md) areas matching their first issue (e.g. core pipeline, connectors). | —                                                                                                                                                                                                                                                       |
| **Next 1–2 quarters**                             | Own a **thin vertical slice** (issue → PR → docs/tests).                                                                                                                                                                | If they want **defensive cyber** credibility aligned with the product: follow **CWL** sequence in `docs/plans/PORTFOLIO_AND_EVIDENCE_SOURCES.md` section 3.2 (**BTF → C3SA**, then onward) — **one paid lane at a time**. |
| **Thesis / compliance narrative (if applicable)** | Point them at [ACADEMIC_USE_AND_THESIS.md](ACADEMIC_USE_AND_THESIS.md) and `docs/plans/PLAN_LATO_SENSU_THESIS.md` — artifact is the codebase.                                               | PUCRS **Gestão do Conhecimento e Transformação Digital** can strengthen **governance / KM** story; confirm offering on the official PUCRS catalog (see PORTFOLIO section 3.3).                                                                          |

---

## 3. Archetype B — API, dashboard, or full-stack web

**Fits:** Contributors touching `api/`, static dashboard, OpenAPI, or HTTP/auth flows.

| Horizon               | Data Boar (repo)                                                                                                                          | Career / optional certs                                                                                                                                                                     |
| -------               | ----------------                                                                                                                          | ------------------------                                                                                                                                                                    |
| **First 2–4 weeks**   | Same hygiene as A; add API smoke paths from TESTING; respect **security** notes in [SECURITY.md](../SECURITY.md) (no secrets in UI/docs). | —                                                                                                                                                                                           |
| **Next 1–2 quarters** | Issues labeled around dashboard/API; keep changes **reviewable** (small PRs).                                                             | General **web/API security** awareness pairs well with CWL basics; optional **AZ-900**-style cloud literacy if their CV is light on cloud (see PORTFOLIO certifications table for pattern). |

---

## 4. Archetype C — DevOps, CI, Docker, release tooling

**Fits:** People who prefer workflows, images, scripts, and CI gates.

| Horizon               | Data Boar (repo)                                                                                                                                                                                   | Career / optional certs                                                                                                                                                       |
| -------               | ----------------                                                                                                                                                                                   | ------------------------                                                                                                                                                      |
| **First 2–4 weeks**   | [.github/workflows/](../.github/workflows/), [docs/ops/DOCKER_IMAGE_RELEASE_ORDER.md](ops/DOCKER_IMAGE_RELEASE_ORDER.md) if touching images; run **`check-all`** before suggesting workflow edits. | —                                                                                                                                                                             |
| **Next 1–2 quarters** | Scoped PRs: pin actions, Scout follow-ups, or doc runbooks — match `docs/plans/PLANS_TODO.md` maintenance rows when possible.                                                            | **SRE** or **platform** certs (see PORTFOLIO CV-derived list) align with this path; keep **supply-chain** mindset (pinned actions, provenance) as a concrete portfolio story. |

---

## 5. Archetype D — Technical writing, compliance narrative, or LGPD-facing docs

**Fits:** Strong writers who clarify **USAGE**, **COMPLIANCE_***, **GLOSSARY**, or operator runbooks — usually **documentation** commits, not core detector code.

| Horizon               | Data Boar (repo)                                                                                                                                                                                                                                          | Career / optional certs                                                                                                                                                                                  |
| -------               | ----------------                                                                                                                                                                                                                                          | ------------------------                                                                                                                                                                                 |
| **First 2–4 weeks**   | [docs/README.md](README.md), [.cursor/rules/docs-policy.mdc](../.cursor/rules/docs-policy.mdc), [.cursor/rules/audience-segmentation-docs.mdc](../.cursor/rules/audience-segmentation-docs.mdc) — **no** new `docs/plans/` links from buyer-facing tiers. | —                                                                                                                                                                                                        |
| **Next 1–2 quarters** | Bilingual EN + pt-BR pairs where required; run **`pytest tests/test_docs_pt_br_locale.py`** on touched `*.pt_BR.md`.                                                                                                                                      | PUCRS **Gestão do Conhecimento e Transformação Digital**, **Compliance Criminal**, or **A Escuta dos Excessos** map well to **DPO/legal/compliance** dialogue — see PORTFOLIO section 3.3 for fit notes. |

---

## 6. Archetype E — Security review, AppSec-shaped contributors

**Fits:** People who triage **CodeQL**, dependency risk, or **SECURITY.md** reports.

| Horizon               | Data Boar (repo)                                                                     | Career / optional certs                                                                                                                                         |
| -------               | ----------------                                                                     | ------------------------                                                                                                                                        |
| **First 2–4 weeks**   | [SECURITY.md](../SECURITY.md), reproduce findings locally, minimal fixes with tests. | —                                                                                                                                                               |
| **Next 1–2 quarters** | Align with maintainer on **severity** and disclosure; avoid drive-by refactors.      | **CWL** track (section 3.2) is the strongest match; optional **IBM / Certiprof**-style foundations already listed in PORTFOLIO if they need entry-level badges. |

---

## 7. Archetype F — QA / test harness expansion

**Fits:** Contributors who add **pytest** coverage, fixtures, or regression guards.

| Horizon               | Data Boar (repo)                                                                         | Career / optional certs                                                                                                       |
| -------               | ----------------                                                                         | ------------------------                                                                                                      |
| **First 2–4 weeks**   | [TESTING.md](TESTING.md), `scripts/quick-test.ps1`, one module at a time.                | —                                                                                                                             |
| **Next 1–2 quarters** | Prefer **fast, deterministic** tests; document any new gates in TESTING or ops runbooks. | **ISTQB**-style material is optional and generic; product-specific value is **pytest + CI** evidence on their GitHub profile. |

---

## 8. Maintainer checklist (short)

- [ ] Archetype chosen; **first issue** is small and merged quickly.
- [ ] **Private** roadmap file created from the template (if you track per-person plans).
- [ ] At most **one** heavy external course/cert **in flight** per person unless they explicitly own only study hours.
- [ ] Link **Data Boar work** (PRs) in their private roadmap so career narrative and product help stay tied.

---

## 9. LinkedIn and ATS narrative checklist (public-safe)

Use this checklist to improve discoverability without leaking private customer data:

- Keep headline outcome-oriented (privacy engineering, compliance enablement, secure-by-design).
- In About/Summary, separate **what was built** from **what is roadmap**.
- Mention measurable engineering evidence (tests, CI gates, releases, docs ownership).
- Use role-appropriate keywords (AppSec, Data Privacy, DPO support, API security, SRE, governance).
- Avoid overclaims (no "certifies compliance" language; use "supports evidence and remediation").
- Link only public artifacts (docs, release notes, PRs, talks) and keep customer identifiers private.

**Full playbook** (sections, ATS export, SSI context, archetype keyword seeds): **[`docs/ops/LINKEDIN_ATS_PLAYBOOK.md`](ops/LINKEDIN_ATS_PLAYBOOK.md)** ([pt-BR](ops/LINKEDIN_ATS_PLAYBOOK.pt_BR.md)).

---

## Revision

| Date       | Note                                                   |
| ---------- | ----                                                   |
| 2026-03-27 | Initial archetype roadmaps + private template pointer. |
| 2026-04-01 | Added LinkedIn/ATS narrative checklist for public profiles. |
| 2026-04-02 | Linked to full **`LINKEDIN_ATS_PLAYBOOK`** in `docs/ops/`. |
