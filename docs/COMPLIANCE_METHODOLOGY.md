# Compliance methodology — discovery, technical risk, and ROPA-style fields

**Português (Brasil):** [COMPLIANCE_METHODOLOGY.pt_BR.md](COMPLIANCE_METHODOLOGY.pt_BR.md)

**Audience:** DPOs, security leads, integrators, and **students** aligning academic LGPD adequacy work with a **technical inventory** product. This page is **methodology and prioritisation**—not legal advice. For legal boundaries and outputs, see [COMPLIANCE_AND_LEGAL.md](COMPLIANCE_AND_LEGAL.md); for frameworks and samples, [COMPLIANCE_FRAMEWORKS.md](COMPLIANCE_FRAMEWORKS.md). For **Excel, heatmap, audit JSON, maturity export, and PDF roadmap**, see [REPORTS_AND_COMPLIANCE_OUTPUTS.md](REPORTS_AND_COMPLIANCE_OUTPUTS.md).

---

## What “methodology” means for Data Boar

Data Boar is built to answer **technical** questions with **repeatable evidence**:

1. **Where** might personal or sensitive-category data appear in configured sources?
2. **How strong** is the signal (pattern, ML/DL hint, cross-table context)?
3. **Which norm-oriented tags** (`norm_tag`, recommendation text) help humans align findings with **their** regulatory mix?

That is **not** the same as declaring **legal adequacy** (e.g. that a given processing is lawful) or filling every column of a **Record of processing activities** (ROPA / **RIPD**-style inventory under LGPD) without human ownership. The methodology below keeps that boundary explicit while giving you **verification modules** you can map to coursework, audits, or internal checklists—including checklists you maintain outside this repo.

---

## Aligning your own adequacy index (e.g. a diagnostic Word template)

Many organisations and courses use a **structured adequacy or gap-analysis index** (sections, weights, evidence columns). If you have a private template (for example a `diagnostico_indice_adequacao_lgpd_*.docx`), treat it as the **source of section headings and weights**; map each section to one or more **modules** in the table below. The public repository does **not** embed proprietary syllabi or unpublished coursework verbatim—keep full text under **`docs/private/`** if you need a line-by-line trace, and contribute back only **generic** headings or priorities suitable for all operators.

---

## Verification modules (product-shaped)

These modules describe **what the software can verify or signal today** (or in clearly documented phased work), not what counsel “signs off.”

| Module | Verification intent | Primary product pointers |
| ------ | ------------------- | ------------------------- |
| **M1 — Presence and category** | Is there evidence of personal or special-category data in scope, and **which category** (pattern / norm tag)? | Findings sheets, `norm_tag`, [SENSITIVITY_DETECTION.md](SENSITIVITY_DETECTION.md), [GLOSSARY.md](GLOSSARY.md) |
| **M2 — Technical severity** | How urgent is **technical** triage (sensitivity band, priority text, quasi-identifier / cross-ref risk)? | Excel columns, “Cross-ref data – ident. risk” where populated, [MAP.md](MAP.md) |
| **M3 — Data-source posture** | What **systems** held the data (product, protocol, transport hints) without copying cell contents? | “Data source inventory” sheet when enabled, [TECH_GUIDE.md](TECH_GUIDE.md) |
| **M4 — Minors and vulnerable contexts** | Are there **signals** consistent with possible minor-related fields or combinations needing policy review? | [MINOR_DETECTION.md](MINOR_DETECTION.md) |
| **M5 — Jurisdictional tension** | Do metadata hints suggest **more than one** plausible regime so counsel can prioritise? | [JURISDICTION_COLLISION_HANDLING.md](JURISDICTION_COLLISION_HANDLING.md), [ADR 0038](adr/ADR-0038-jurisdictional-ambiguity-alert-dont-decide.md) |
| **M6 — Governance of the auditor** | Can the organisation show **who ran** scans and what artefacts exist for export? | [ADR 0037](adr/ADR-0037-data-boar-self-audit-log-governance.md) |
| **M7 — Retention in sealed / customs-adjacent contexts** | Is **retention** of artefacts understood as **operator-owned**, without automated “legal basis” tags? | [ADR 0039](adr/ADR-0039-retention-evidence-posture-bonded-customs-adjacent-contexts.md) |

**Risk level in this methodology** means **technical and triage risk** (exposure, category strength, combination risk)—**not** a substitute for your enterprise risk register or legal conclusion.

---

## ROPA-style columns: what to automate first

Typical processing-register columns (names vary by template): **Titular**, **Finalidade**, **Base legal**, **Categoria**, **Prazo de retenção**, **Compartilhamento**, **Medidas de segurança**, **Operador**, **Transferências internacionais**, etc.

Suggested **automation priority** for Data Boar (and similar inventory engines):

| Column / theme | Automate first? | Rationale |
| -------------- | --------------- | --------- |
| **Categoria dos dados / tipo de dado** | **Yes — already core** | Strong fit: patterns, ML/DL hints, `norm_tag`, sensitivity. |
| **Local / sistema / ativo de tratamento** | **Yes — high value** | Target, schema, table, path, connector type; “Data source inventory” extends this. |
| **Grau de risco técnico / prioridade de triagem** | **Yes — already core** | Recommendation sheets (“Base legal”, “Risco”, “Prioridade” columns are **guidance text**, not asserted legal basis—see below). |
| **Titular** (identidade do titular) | **Later / mostly human** | Inferring *who* is the data subject from column names alone is unreliable; use **category** and **location** first, then DPO fills titular from process knowledge. |
| **Finalidade** | **Human-led** | Purpose comes from **business process** and records of processing; optional future: **metadata hints** (column names, app names) as *suggestions only*. |
| **Base legal** | **Never auto-assert** | The engine may surface **recommendation language** aligned to norms; **choosing** lawful basis remains **counsel / DPO**. See [ADR 0038](adr/ADR-0038-jurisdictional-ambiguity-alert-dont-decide.md) posture. |
| **Prazo de retenção** | **Human-led** | Not derivable from content samples without policy and legal context. |
| **Compartilhamento / terceiros** | **Partial** | “Where else does this attribute appear?” (multi-target scans) supports **inventory**; contracts and legal relationships stay outside the tool. |
| **Medidas de segurança** | **Partial** | Technical signals (e.g. TLS vs plaintext, version inventory, hardening recommendations where shipped) inform **security** workstreams—not a full ISO 27001 control attestation. |
| **Transferência internacional** | **Hints only** | Optional jurisdiction hints flag **tension** for review, not a transfer mechanism decision. |

If you want the next **product** slice, the highest leverage is usually: **(1)** richer **category + location** exports, **(2)** optional **purpose hints** from metadata (always labelled as non-authoritative), **(3)** tighter **cross-system** linkage for “same logical attribute in two places”—still without auto-filling **base legal** or **titular**.

---

## Related reading

- [COMPLIANCE_AND_LEGAL.md](COMPLIANCE_AND_LEGAL.md) — what the product does and does not claim.
- [philosophy/THE_WHY.md](philosophy/THE_WHY.md) — evidence-first posture.
- [COMPLIANCE_TECHNICAL_REFERENCE.md](COMPLIANCE_TECHNICAL_REFERENCE.md) — limits, sampling, timeouts.
