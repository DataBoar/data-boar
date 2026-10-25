# LinkedIn and ATS playbook (public-safe)

**Português (Brasil):** [LINKEDIN_ATS_PLAYBOOK.pt_BR.md](LINKEDIN_ATS_PLAYBOOK.pt_BR.md)

**Purpose:** Give talent pool members and operators a **single, concrete** reference for LinkedIn discoverability, ATS-friendly resumes, and healthy professional habits (including **SSI** context). This doc stays **generic**: no employer names, salaries, or copy-paste text tied to one person.

**Relationship to other docs:**

- Short checklist: **[`docs/TALENT_POOL_LEARNING_PATHS.md`](../TALENT_POOL_LEARNING_PATHS.md)** section 9.
- Role archetypes and optional certs: same file, sections 2–7.
- **Private** headline, About, and featured bullets for **founder or priority candidates** belong in **`docs/private/commercial/`** (for example a file such as `LINKEDIN_ATS_AND_POSITIONING_PLAYBOOK.pt_BR.md` or per-slug notes under `candidates/<slug>/`). Copy from **`docs/private.example/commercial/LINKEDIN_ATS_PRIVATE_SUPPLEMENT_TEMPLATE.pt_BR.md`** if you need a blank.

---

## 1. Goals (what “good” looks like)

1. **Clarity:** Recruiters and hiring managers understand **role, seniority, and proof** in under 30 seconds.
2. **ATS match:** Exported CV and LinkedIn share **consistent keywords** for the target track (without keyword stuffing).
3. **Trust:** Claims match **evidence** (repos, releases, docs, measurable outcomes). Avoid compliance or legal overclaim.
4. **Sustainability:** A **small weekly habit** beats a one-time rewrite.

---

## 2. Social Selling Index (SSI) on LinkedIn

LinkedIn’s **SSI** is a **dashboard metric** (not a public score on your profile). It is grouped into **four pillars** (labels may vary slightly over time):

1. Establishing a **professional brand**
2. Finding the **right people**
3. Engaging with **insights**
4. Building **relationships**

**Ethical use:** Improve **real** visibility and relationships. Do not spam connections, fake engagement, or misrepresent skills.

**Practical habits (about 30 minutes per week):**

- Update **one** section per week (headline → About → top experience → featured).
- Share **one** substantive post or comment (technical insight, release note, lesson learned) every 1–2 weeks.
- Accept that SSI is a **guide**, not a hiring guarantee.

---

## 3. ATS mechanics (resume files)

- Prefer **one column**, **standard section titles** (Experience, Education, Skills), and **simple bullets**.
- Export **PDF** from the same source of truth as LinkedIn (avoid divergent Word vs PDF).
- File name pattern: **`Role_LastName_FirstName.pdf`** or locale convention; avoid special characters.
- Mirror **5–10 core keywords** from the target job description **naturally** in experience bullets (not a giant keyword block).

---

## 4. LinkedIn section-by-section

### 4.1 Photo and banner

- Photo: professional, readable at thumbnail size.
- Banner: optional; can reinforce **domain** (privacy, security, data platform) without clutter.

### 4.2 Headline

- Formula: **`Role | Outcome | Domain`** (example shape: *Backend engineer | Data protection tooling | Python / CI*).
- Avoid empty buzzwords (“passionate”, “guru”). Prefer **verbs and domains** recruiters search for.

### 4.3 About

- First two lines: **who you are** and **what you ship**.
- Middle: **proof** (products, metrics, stack, governance awareness).
- Close: **what you want next** (role type, remote/hybrid, scope) without sounding desperate.

### 4.4 Experience

- Use **STAR-style** bullets where possible: situation, task, action, **measurable** result.
- Tie work to **security, quality, and maintainability** when true (tests, CI, reviews).

### 4.5 Skills and endorsements

- Pin **3–5** skills that match the **target role**.
- Order skills so the top matches **ATS + reality** (languages, frameworks, cloud, security).

### 4.6 Licenses and certifications

- List **verifiable** credentials; avoid expired badges unless still relevant and labeled.

### 4.7 Featured

- Link **public** artifacts: GitHub releases, talks, **docs** you authored, case studies without sensitive client data.

### 4.8 Recommendations

- **Give** thoughtful recommendations to earn reciprocity over time; **ask** peers who know your work.

---

## 5. Keyword packs by archetype (A–F)

Use as **seeds**; personalize with real stack and projects.

| Archetype | Example keyword seeds |
| --------- | --------------------- |
| **A** Backend / Python | Python, pytest, API design, connectors, performance, typing, packaging |
| **B** API / web | REST, OpenAPI, authn/z, HTTP security, frontend basics, UX for admins |
| **C** DevOps / CI | GitHub Actions, Docker, supply chain, SBOM, release engineering, SRE |
| **D** Docs / compliance narrative | Technical writing, LGPD-aware language, evidence, risk language, bilingual EN/pt-BR |
| **E** AppSec | Threat modeling, CodeQL, dependency risk, secure defaults, disclosure |
| **F** QA / test | pytest, fixtures, regression strategy, CI gates, flake reduction |

---

## 6. Cadence

| Cadence | Actions |
| ------- | ------- |
| **Weekly (~30 min)** | One profile tweak; one insight or comment; review one job description for keyword alignment. |
| **Monthly** | Re-read About and headline; refresh Featured; export fresh CV PDF. |
| **Quarterly** | Skills audit vs target role; certifications lane only if **one** lane is active (see learning paths doc). |

---

## 7. Private supplement (founder or priority candidates)

When you need **final copy** (headline variants, full About, featured list) for specific people:

1. Keep it under **`docs/private/commercial/`** (not committed).
2. Start from **`docs/private.example/commercial/LINKEDIN_ATS_PRIVATE_SUPPLEMENT_TEMPLATE.pt_BR.md`**.
3. Keep this public playbook as the **method**; private files hold **names and exact wording**.

---

## 8. Locale, jurisdiction, and certification pricing (assistants + operators)

When you produce **ATS / LinkedIn recommendations** for a candidate, **anchor the narrative to the candidate’s target market** — not a generic English or a default you are used to from another region.

### 8.1 Pick a locale and compliance frame

| Target market | Suggested LinkedIn / CV language | Primary privacy / data-protection frame for local employers |
| ------------- | -------------------------------- | ------------------------------------------------------------- |
| Canada | **en_CA** (or **fr_CA** for Quebec-facing roles) | **PIPEDA** (federal); provincial laws (e.g. **Alberta PIPA**, **BC PIPA**, **Quebec Law 25**); **Bill C-27** trajectory (CPPA / AIDA — verify current status when advising). |
| European Union / UK job posts | **en_GB** or local EU language | **UK GDPR** / **EU GDPR** as appropriate to the role. |
| Brazil | **pt-BR** | **LGPD**. |
| United States | **en_US** | Sectoral US privacy (FTC, HIPAA where relevant); **state** laws (e.g. CPRA) when the role is state-specific. |

**Do not** present **GDPR** as the default “must-have” compliance vocabulary for **Canadian-only** roles — recruiters in Canada expect **PIPEDA** / Canadian provincial context first; mention **GDPR** when the role is **multinational / EU data** or the employer asks for it.

### 8.2 Certifications: issuer location vs candidate location

- Many programs (e.g. compliance/ethics certs from **US-based** bodies) quote **USD** list prices and US exam sites. **Before** recommending a budget line, **check** the issuer’s official site for **Canada** pricing in **CAD**, **Canadian test centres**, **taxes**, and **chapter / member** discounts.
- If the candidate might sit the exam in the **US**, note **USD** as a scenario — clearly **separate** from **Canada CAD** totals.
- Apply the same discipline for other countries (local chapter, VAT/GST, exam delivery mode).

### 8.3 Assistant guardrail (one sentence)

**Match locale + jurisdiction + currency to the candidate’s target geography** in every talent-ATS export; when unsure, **say so** and point to **primary sources** (issuer pricing page, regulator text) instead of guessing.

---

## Revision

| Date | Note |
| ---- | ---- |
| 2026-04-02 | Initial full playbook; SSI context; ATS + LinkedIn sections; archetype keywords. |
| 2026-04-08 | Section 8: locale-aware compliance and certification pricing (en_CA / PIPEDA / Bill C-27; GDPR not default for Canada). |
