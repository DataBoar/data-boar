# Plan: Gemini feedback triage (non-authoritative)

**Status:** Pending
**Date:** 2026-03-29
**Authors:** Fabio Leitao
**Priority:** H3

<!-- plans-hub-summary: Gemini triage from 2026-03-26 local bundle (WRB folder): P0/P1/P2 rows with IDs—non-authoritative until verified and promoted. -->
<!-- plans-hub-related: TOKEN_AWARE_USAGE.md, PLANS_TODO.md, PORTFOLIO_AND_EVIDENCE_SOURCES.md, PYTHON_UPGRADE_PLAYBOOK.md -->

**Synced with:** [PLANS_TODO.md](PLANS_TODO.md) (pointer only). **Workflow bundle:** [GEMINI_PUBLIC_BUNDLE_REVIEW.md](../ops/GEMINI_PUBLIC_BUNDLE_REVIEW.md) ([pt-BR](../ops/GEMINI_PUBLIC_BUNDLE_REVIEW.pt_BR.md)).

**Promoted operator hygiene (post-triage, not “Gemini as authority”):** dated checklists consolidated under **`docs/ops/today-mode/`** with **`PUBLISHED_SYNC.md`** and **`CARRYOVER.md`** — see [ADR 0006](../adr/ADR-0006-operator-today-mode-layout-and-published-sync.md).

**Source texts (maintainer machine, gitignored):** `docs/feedbacks, reviews, comments and criticism/` — same drop zone as **Corporate-Entity-C / WRB**-style reviews (rule **`.cursor/rules/operator-feedback-inbox.mdc`**, token **`feedback-inbox`**). Gemini exports used for §6: `Gemini - revisao e recomendações … EN …`, `… pt_BR …`, `… compliance config samples yaml …`, `Gemini - raciocinio profundo …` (filenames show `2006_03_26` typo; treat as **2026-03-26**). **Do not** commit that folder; this plan holds the **distilled triage** only.

---

## 1. Purpose

Use feedback from **Gemini** (or similar) runs on the **public documentation bundle** in a way that is:

- **Safe:** no secret or private data in tracked files; raw long outputs stay under **`docs/private/`** (gitignored).
- **Honest:** LLM output is **triage**, not **authority** — same class as digests (e.g. WRB-style inputs), **below** **`git`**, **CI**, and **pytest**.
- **Actionable together:** we can decide **if**, **when**, and **with what urgency** an item enters real sequencing.

This plan **does not** replace security review, legal review, or the commercial roadmap in **[PORTFOLIO_AND_EVIDENCE_SOURCES.md](PORTFOLIO_AND_EVIDENCE_SOURCES.md)**.

---

## 2. Authority and safety rules

| Rule | Detail |
| ---- | ------ |
| **Non-authoritative** | Nothing in Gemini’s list is “must ship” until a maintainer verifies it against **code** and **tests** (or explicitly documents an exception). |
| **Bundle discipline** | Generate bundles only via **`export_public_gemini_bundle.py`** (with **`--verify`**), per the ops runbook — avoid manual `cat` concatenation. |
| **Storage** | Prefer the agreed folder **`docs/feedbacks, reviews, comments and criticism/`** (gitignored) for full Gemini / Corporate-Entity-C text; alternatively **`docs/private/gemini_bundles/`** or journals — **never** paste webhooks, credentials, or client-specific data into **tracked** Markdown. |
| **Promotion** | To enter **[PLANS_TODO.md](PLANS_TODO.md)** order table or a feature slice: add an explicit row/issue and treat Gemini as **source: external triage** (optional label in GitHub). |

---

## 3. Decision gates (before sequencing)

Answer **all** that apply for each candidate item:

1. **Verifiable:** Can we confirm or falsify with `pytest`, `grep`, or a documented manual step?
2. **Risk:** Does it touch **security**, **misleading deploy**, or **compliance wording**? If yes, higher priority **after** quick verification — not “later never,” but not automatic merge.
3. **Cost:** Rough **agent/operator token** and **calendar** cost — prefer alignment with **[TOKEN_AWARE_USAGE.md](TOKEN_AWARE_USAGE.md)** and **[SPRINTS_AND_MILESTONES.md](SPRINTS_AND_MILESTONES.md)** themes (e.g. **S0** trust burst vs **S5** housekeeping).
4. **Alignment:** Does it help **Data Boar** goals: **trustworthy scans**, **clear operator path**, **LGPD/compliance narrative**, **shipping without regressions**? If it is only **cosmetic prose**, default to **low pressure** and batch with **`docs`** / **houseclean** sessions.

---

## 4. Urgency (“pressa”) — suggested labels

| Label | Meaning | Typical slot |
| ----- | ------- | ------------ |
| **Hot** | Possible **safety**, **wrong security advice in docs**, or **broken first-run** — verify within **days** if confirmed. | Same week as discovery; may jump ahead of a small feature slice. |
| **Warm** | **Clarity**, **cross-links**, **onboarding friction** — batch in a **docs** pass or **S5** buffer sprint. | Within **1–3 weeks** if capacity exists. |
| **Cold** | Style, optional rewording, “nice to have” structure — **no** dedicated sprint until idle. | Backlog; revisit in quarterly doc review. |

**Priority band A** (Dependabot, Scout, Hub tags) still **wins** when trust/supply-Colleague-Nn is red — Gemini items do **not** override **[CODE_PROTECTION_OPERATOR_PLAYBOOK.md](../CODE_PROTECTION_OPERATOR_PLAYBOOK.md)** or **–1 / –1b** in `PLANS_TODO`.

---

## 5. Alignment with Data Boar and “future you”

| Goal area | Gemini feedback is **strongly aligned** when… | **Weak or neutral** when… |
| --------- | --------------------------------------------- | --------------------------- |
| **Trust & evidence** | It flags **contradictions** between USAGE, SECURITY, and runtime (e.g. bind defaults, API keys). | It suggests **marketing** copy only. |
| **Operator success** | It surfaces **footguns** (CI, Docker, first scan). | It asks for **features** not in repo (hallucination — verify). |
| **Compliance narrative** | It spots **unclear** DPO/legal boundaries (we still run **human** review). | It reads like **legal advice** — do not treat as counsel. |
| **Portfolio / study** | N/A — keep personal cadence in **[PORTFOLIO_AND_EVIDENCE_SOURCES.md](PORTFOLIO_AND_EVIDENCE_SOURCES.md)**; Gemini doc review is **product/docs**, not **CWL/CCA** scheduling. | |

---

## 6. Triage rows — Gemini bundle **2026-03-26** (from local WRB folder)

**Instructions:** These rows **summarize** the four Gemini text files in `docs/feedbacks, reviews, comments and criticism/` (historical split: EN+infra, pt-BR, YAML samples, deep pass). New runs can use **one** consolidated prompt — see **[GEMINI_PUBLIC_BUNDLE_REVIEW.md](../ops/GEMINI_PUBLIC_BUNDLE_REVIEW.md)** § *Suggested Gemini prompt* ([pt-BR](../ops/GEMINI_PUBLIC_BUNDLE_REVIEW.pt_BR.md)). Rows are **not** approved work — decide per §3 before any PR. Update the **Status** column as you dismiss, verify, or promote.

### 6.1 Document + infra bundle (EN + configs)

| ID | Item (Gemini wording compressed) | Verify how | Urgency (§4) | Aligns §5? | Status |
| -- | -------------------------------- | ---------- | ------------ | ----------- | ------ |
| **G-26-01** | **Log path leakage:** absolute host paths (`C:\Users\…`) in sample/production logs → risk of information disclosure. | Audit logging/redaction in `core/` / config; grep for path emission in audit logs. | Hot if confirmed in product logs | Trust | **Mitigado (2026-03):** `utils/audit_log_display.py` + `audit_log_name` em `normalize_config`; logs de filesystem usam raiz `pasta?hex` e caminhos relativos ou `target?hash` fora da raiz; ver **docs/SECURITY.md** e **docs/USAGE.md**. |
| **G-26-02** | **Python version drift:** `Dockerfile` uses **3.13-slim**; `pyproject.toml` / Sonar still anchor **3.12** in places → confusion for local vs Docker. | Compare `Dockerfile`, `pyproject.toml` `[tool.mypy]` / CI matrix, `sonar-project.properties`; see [PYTHON_UPGRADE_PLAYBOOK.md](PYTHON_UPGRADE_PLAYBOOK.md). | Warm | Operator success | **Mitigado (2026-03):** **TECH_GUIDE** (EN/pt-BR) — subseção *Python minor versions*; comentário em **`sonar-project.properties`**; matriz CI já em **PYTHON_UPGRADE_PLAYBOOK**. |
| **G-26-03** | **CEP_BR regex** (`\b\d{5}-?\d{3}\b`) too generic → false positives (SKU, IDs). | Review `varios-settings` / compliance samples + scanner behaviour; decide doc-only warning vs context heuristic. | Warm | Trustworthy scans | **Mitigado (2026-03):** documentação em **SENSITIVITY_DETECTION** (EN/pt-BR) + comentários em **compliance-sample-lgpd.yaml** / **regex_overrides.example.yaml**; `CEP_BR` incluído em **`WEAK_PATTERNS_IN_ENTERTAINMENT`** (`core/detector.py`) para não subir a HIGH só por formato em letras/cifras; catálogo/SKU fora desse contexto segue HIGH — operador deve validar. Testes: **`tests/test_logic.py`** (`test_cep_br_*`). |
| **G-26-04** | **Package name vs brand:** alinhar PyPI/docs a **Data Boar** / `data-boar`. | Feito: `pyproject` + docs; publicação PyPI quando houver release. | Cold | Operator success | ✅ |
| **G-26-05** | **System libs** (`libpq-dev`, `unixodbc-dev`, …) not listed for **non-Docker** install. | Add “Prerequisites” to README/TECH_GUIDE if gaps remain; test on clean Debian/Ubuntu. | Warm | Operator success | **Mitigado (2026-03):** **TECH_GUIDE** (EN/pt-BR) já tinha bloco `apt`; alinhado ao **Dockerfile** com **`default-libmysqlclient-dev`**; **README** / **README.pt_BR** — *Quick start* aponta para **Requirements / Requisitos** antes de `uv sync`. |
| **G-26-06** | **Docker persistence:** `CONFIG_PATH=/data` but unclear **volume** for SQLite/report state. | [DOCKER_SETUP.md](../DOCKER_SETUP.md) ([pt-BR](../DOCKER_SETUP.pt_BR.md)) / DEPLOY — ensure `docker run -v` is explicit. | Warm | Operator success | **Mitigado (2026-03):** **DOCKER_SETUP** (EN/pt-BR) — seção *Data persistence / Persistência de dados* (`/data`, bind mount, perda sem volume). |
| **G-26-07** | **COMPLIANCE_TAGS.md** — glossary of `norm_tag` / sensitivity labels. | New doc slice; link from COMPLIANCE_FRAMEWORKS or GLOSSARY. | Cold | Compliance narrative | ⬜ |
| **G-26-08** | **README:** sample report table + quality **badges** (Sonar/Ruff). | Docs + CI badge URLs; avoid noisy shields. | Cold | Trust / adoption | ⬜ |
| **G-26-09** | **Man page duplication** (why two man pages) redundant in install flow. | Editorial pass on `docs/data_boar.1` / install docs. | Cold | Docs hygiene | ⬜ |
| **G-26-10** | **Open questions** (passworded ZIP/PDF, OCR, ML perf on 100GB+, read-only guarantee, Slack per-tenant, NoSQL, log rotation, learned patterns + Docker rebuild, encoding, cron): track as **FAQ** or **limitations** — not automatic scope. | Check USAGE/TECH_GUIDE for existing answers; add FAQ row only where still blank. | Cold | Mixed | ⬜ |

### 6.2 pt-BR linguistic review (`… pt_BR …` file)

| ID | Item | Verify how | Urgency | Aligns §5? | Status |
| -- | ---- | ---------- | ------- | ----------- | ------ |
| **G-26-11** | **pt-PT drift** (“teu”, “vê”, “enviares”, “académico”, “ping” for Slack) undermines LGPD-facing tone. | `uv run pytest tests/test_docs_pt_br_locale.py`; manual pass on cited files (e.g. ACADEMIC_USE_AND_THESIS.pt_BR). | Warm | Compliance narrative | **Mitigado (2026-03):** revisão manual em **ACADEMIC_USE_AND_THESIS.pt_BR**, **GEMINI_PUBLIC_BUNDLE_REVIEW.pt_BR**, **WRB_DELTA_…**, **OPERATOR_LAB_DOCUMENT_MAP.pt_BR**; guard **`test_docs_pt_br_locale.py`** verde. |
| **G-26-12** | **Legal disclaimer phrasing** — “parecer para o teu estudo” → **seu estudo**; imperatives **consulte/veja** not informal **vê**. | Same + legal-comfort review (human). | Warm | Compliance narrative | **Mitigado (2026-03):** mesmo pacote que **G-26-11** (tom formal / pt-BR em **ACADEMIC_USE_AND_THESIS.pt_BR**). |
| **G-26-13** | **Corporate-Entity-C** referred to ambiguously (entity gender / what it is) — align EN↔pt-BR. | Glossary or one-line definition in docs; match EN. | Cold | Clarity | **Mitigado (2026-04):** entrada **Corporate-Entity-C / WRB** em **GLOSSARY.md** e **GLOSSARY.pt_BR.md** (seção 9), com link a **Corporate-Entity-C_IN_REPO_BASELINE** e guideline — vocabulário de processo, não módulo do produto. |

### 6.3 Compliance YAML samples (`… compliance config samples …` file)

| ID | Item | Verify how | Urgency | Aligns §5? | Status |
| -- | ---- | ---------- | ------- | ----------- | ------ |
| **G-26-14** | **`include_profiles` / auto-merge** of samples — avoid manual merge errors for `recommendation_overrides`. | Product decision: new config feature vs better docs; check if YAML `!include` or similar exists. | Cold (feature) | Operator success | ⬜ |
| **G-26-15** | **DNI_AR** `\b\d{7,8}\b` too broad → mass false positives. | Sample YAML comments + doc warning; optional stricter sample. | Warm | Trustworthy scans | **Mitigado (2026-03):** comentários em **compliance-sample-argentina_pdpa.yaml**; tabela e texto em **SENSITIVITY_DETECTION** (EN/pt-BR) (*Generic digit patterns*). |
| **G-26-16** | **Duplicated English terms** across country samples → redundant work if many profiles loaded. | Doc: explain composition pattern; long-term `base-global.yaml` idea. | Cold | DX | ⬜ |
| **G-26-17** | **`norm_tag_pattern` substring collisions** — ordering/anchoring in matcher. | Code review of override matching; add test if gap. | Warm | Trustworthy scans | **Mitigado (2026-03):** docstring **`_find_override_row`** (`report/generator.py`); teste **`test_recommendation_overrides_first_match_wins_put_specific_before_generic`**; checklist em **USAGE** (ordem específica antes de genérica). |
| **G-26-18** | **Parser behaviour:** unknown keys / multi `norm_tag` / ML + encoding questions — answer with code truth or doc. | Read notifier + scanner tests; document limits. | Cold | Operator success | ⬜ |

### 6.4 Deep reasoning (`… raciocinio profundo …` file)

| ID | Item | Verify how | Urgency | Aligns §5? | Status |
| -- | ---- | ---------- | ------- | ----------- | ------ |
| **G-26-19** | **“Black hole” of overrides:** operator uses sample LGPD but forgets manual merge of **recommendation_overrides** → report looks like “dumb grep”. | USAGE/TECH_GUIDE **bold** checklist; optional validation warning if overrides empty when samples expect them. | Warm | Compliance narrative | **Mitigado (2026-03):** checklist numerada em **USAGE** / **USAGE.pt_BR** (mesclar overrides, revisar regex, ordem de padrões) — sem warning em runtime neste passo. |
| **G-26-20** | **Numeric FP flood** — doc table “precision / scope limits” for generic digit patterns. | Short table in SENSITIVITY or compliance doc. | Warm | Trust | **Mitigado (2026-03):** tabela + parágrafo em **SENSITIVITY_DETECTION** (EN/pt-BR). |
| **G-26-21** | Same as **G-26-02** + **G-26-05** (env sync + prerequisites) — **I3** intersection. | Single implementation pass if promoted. | Warm | Operator success | **Mitigado (2026-03):** interseção coberta pelas linhas **G-26-02** e **G-26-05** (mesma sessão de docs). |
| **G-26-22** | **Legal tone + pt-BR** — formal register for disclaimers; YAML labels as “base legal sugerida” style (optional copy tweak). | Human + locale tests. | Warm | Compliance narrative | **Mitigado (2026-03):** alinhado ao pacote **G-26-11** / **G-26-12** (teses e disclaimers em **ACADEMIC_USE_AND_THESIS.pt_BR**). |

**Dismissal:** If an item is **wrong** after verification, mark **Dismissed** in chat or a short note under the row (stops re-churn).

**Promotion:** When you agree to implement, open a **PR** or add a **PLANS_TODO** row — link **`G-26-…`** in the PR description.

---

## 7. Relationship to sequencing

- **Default:** Items stay in **§6** until promoted.
- **Do not** bulk-copy Gemini bullets into **[PLANS_TODO.md](PLANS_TODO.md)** without gate **§3**.
- **Sprint fit:** Prefer **S5** (maintenance) for doc-only; **S0** only if a Gemini flag implies **trust/supply-Colleague-Nn** doc mismatch worth fixing before the next release.

---

## 8. Changelog

| Date | Note |
| ---- | ---- |
| 2026-03-29 | Initial plan — optional triage, non-authoritative; hub + `PLANS_TODO` pointer. |
| 2026-03-31 | Populated §6 with **concrete IDs G-26-01…22** from Gemini texts in gitignored `docs/feedbacks, reviews, comments and criticism/` (bundle dated **2026-03-26** in content; filenames typo `2006`). |
| 2026-03-27 | Warm-batch verification: **G-26-02**, **G-26-06**, **G-26-11…12**, **G-26-15**, **G-26-17**, **G-26-19…22** marked **Mitigado** — docs, `sonar-project.properties` comment, `compliance-sample-argentina_pdpa.yaml`, `report/generator.py` docstring, **`tests/test_report_recommendations.py`** ordering test. |
