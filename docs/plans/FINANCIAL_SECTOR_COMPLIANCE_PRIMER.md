# Primer: Financial sector compliance (PCI DSS v4.0, SOX, BACEN CMN 4.893/2021)

<!-- plans-hub-summary: Primer PCI DSS v4.0 / SOX / BACEN — alinhamento Data Boar para setor financeiro -->

**Audience:** Compliance teams at banks, fintechs, acquirers, and processors; PCI **QSA** / internal assessors; GRC and internal audit on listed or IF-regulated entities.

**Product stance:** Data Boar **discovers where** payment, customer, and financially relevant fields sit in configured targets. It **complements, does not replace, a QSA assessment for PCI DSS**. It is **not** a SOX auditor, **not** a BACEN inspection pack, and **not** a card-data vault, tokenisation, or encryption product.

**Related:** [COMPLIANCE_FRAMEWORKS.md](../COMPLIANCE_FRAMEWORKS.md) · [USAGE.md — Governance Lens (Enterprise)](../USAGE.md#governance-lens-enterprise) · [compliance-sample-pci_dss.yaml](../compliance-samples/compliance-sample-pci_dss.yaml) · [compliance-sample-brazil_bacen4893.yaml](../compliance-samples/compliance-sample-brazil_bacen4893.yaml) · [GLOSSARY.md](../GLOSSARY.md) (CHD, SOX)

---

## PCI DSS v4.0 — Payment Card Industry Data Security Standard

Scope here is **stored account data** and **incident response evidence**, not the full 12-requirement standard. Data Boar does **not** implement network segmentation, key management, or payment-page controls.

### Requirement 3 — Protect stored account data

Requirement 3 asks entities to **limit SAD/CHD storage**, **render PAN unreadable** where storage is allowed, and **never store** authentication data after authorisation (CVV, full track, PIN). Data Boar **finds** those shapes; it does **not** tokenise, encrypt, or delete them.

| Reference | Intent | Data Boar capability (shipped) | Notes |
| --------- | ------ | ------------------------------ | ----- |
| Req. 3 (inventory) | Know where PAN / CHD live | Built-in **`CREDIT_CARD`** (Luhn / Mod 10) on filesystem and connector targets; PCI sample **`PAN`**, column-name gates (`PCI_CARD_COLUMN`, `PCI_CVV`, `PCI_CARD_EXPIRY`, `PCI_TRACK2`) | Pair [compliance-sample-pci_dss.yaml](../compliance-samples/compliance-sample-pci_dss.yaml) via `regex_overrides_file` + `report.recommendation_overrides` |
| Req. 3.2 / 3.3 (SAD) | Do not retain CVV / track | Sample patterns flag **column names** and track-like strings with `norm_tag` PCI-DSS | Heuristic — confirm with QSA sampling |
| Req. 3.4 (render PAN unreadable) | Tokenise / encrypt / truncate | Findings + assessor-oriented **recommendation text** (e.g. tokenise PAN) | The engine **does not** apply tokenisation |
| Req. 3 (scope reduction) | Distinguish tokens vs live PAN | Sample `PCI_TOKENIZED_METADATA` (last-four / gateway token columns) | Still in-scope for QSA judgment |

**(roadmap)** Tighter PAN context gates (proximity / plugin Phase 1b) so sample `PAN` and built-in `CREDIT_CARD` do not double-fire — `PLANS_TODO.md` row **S4b**.

### Requirement 12.10 — Incident response plan

PCI asks for a **tested IR plan**, including how you **locate and contain** cardholder data after a suspected breach.

| Reference | Intent | Data Boar capability (shipped) | Notes |
| --------- | ------ | ------------------------------ | ----- |
| 12.10 (locate CHD) | Find copies during IR | Same discovery path as Req. 3; dashBOARd + Excel / heatmap | Run against **configured** targets only |
| 12.10 (evidence of what changed) | Session comparison | **`--diff SESSION_A SESSION_B`** | Not a SIEM |
| 12.10 (who scanned what) | Operator accountability | Session SQLite + **`--export-audit-trail`** JSON (`data_wipe_log`, session summary, `trust_state`) | **Not** a WORM / legally immutable log |
| 12.10 (notify operators) | Short post-scan brief | Optional Slack / Teams / webhook notifications | Off by default — [USAGE.md](../USAGE.md#51-operator-notifications-optional) |

**Data Boar complements, does not replace, a QSA assessment for PCI DSS.** Pentest scoping (Req. 11.3) and ASV scans stay with the assessor programme — see issue **#1271** for a structured 11.3 note if you need that chapter later.

### Enterprise GRC narrative (optional)

With **Enterprise** Governance Lens (`governance.tier: enterprise`), `--governance-report` can add **PCI-DSS v4.0** control-gap **storytelling** (lab example map in-repo; licensed production map is **not** in public Git). Heuristic example in [USAGE.md](../USAGE.md#governance-lens-enterprise): `CREDIT_CARD` / `PCI_CARD` → Req. 3.4 language. **Not** a ROC or AOC.

---

## SOX — Sarbanes-Oxley Section 404 (ICFR)

Section 404 is about **internal control over financial reporting** (ICFR) and the IT general controls (ITGC) that support it. Data Boar is **not** a financial-statement auditor and **does not** certify ICFR.

| Theme | Typical 404 / ITGC ask | Data Boar capability (shipped) | Gap / roadmap |
| ----- | ---------------------- | ------------------------------ | ------------- |
| Sensitive-field inventory | Know which systems hold data that could affect reporting integrity | Configured **targets** + findings (including financial identifiers when you enable samples) | You still own the **in-scope application list** |
| Repeatable evidence | Show the same check ran again | Scheduled / API scans, Excel + heatmap, **`--diff`** | Not a GRC platform of record |
| Accountability trail | Who ran which scan | Session metadata, **`--export-audit-trail`**, optional notification send log | SQLite can be copied or wiped — **not** an immutable SOX archive |
| Access / SoD | Who can see findings | Optional dashboard **API key**, **WebAuthn**, **RBAC** (Pro+) | **(roadmap)** SSO/OIDC — [PLAN_DASHBOARD_REPORTS_ACCESS_CONTROL.md](PLAN_DASHBOARD_REPORTS_ACCESS_CONTROL.md) |

**Relevance:** US **issuers** and many **subsidiaries** reuse the same evidence pack. Pair this primer with counsel: SOX language in reports is **governance evidence**, not an audit opinion — [GLOSSARY.md](../GLOSSARY.md) **SOX**.

**(roadmap)** Access/metadata findings for ITGC narratives — [PLAN_ENTERPRISE_HR_SST_ERP_CONNECTORS.md](PLAN_ENTERPRISE_HR_SST_ERP_CONNECTORS.md) (SOC software ≠ SOX).

---

## BACEN / CMN Resolução 4.893/2021

Cybersecurity policy for Brazilian **instituições financeiras** and payment institutions (consolidates / updates the former **4.658/2018** line). In force from **February 2022**. Complements **LGPD** — IFs typically need **both**. Pair [compliance-sample-brazil_bacen4893.yaml](../compliance-samples/compliance-sample-brazil_bacen4893.yaml) with the LGPD sample.

Article numbers below follow **this repo’s** shipped maps ([USAGE.md — Governance Lens (Enterprise)](../USAGE.md#governance-lens-enterprise), [COMPLIANCE_FRAMEWORKS.md](../COMPLIANCE_FRAMEWORKS.md), BACEN sample `norm_tag` / `base_legal`). They are **heuristic labels for reports**, not a substitute for reading the Resolução.

This primer does **not** cover Basel III (capital / liquidity). That frame is adjacent but **out of scope** for this file.

### Inventory inputs (customer data and critical systems)

Mapping where customer and payment fields live is an IF programme input. This repo does **not** pin that inventory duty to Art. 6º (USAGE maps Art. 6º to the **incident action plan**; the sample uses Art. 6 for **cryptographic** policy language and Arts. 6–8 for IR activation).

| Intent | Data Boar capability (shipped) | Notes |
| ------ | ------------------------------ | ----- |
| Bootstrap systems in scope | **Scope import** (CSV → YAML `targets` fragment) + discovery on those targets | [SCOPE_IMPORT_QUICKSTART.md](../ops/SCOPE_IMPORT_QUICKSTART.md) |
| Field types (Pix, accounts, card tokens, NSU-class) | BACEN sample regex / ML terms (`BACEN_CHAVE_PIX`, conta/agência, card-field names) | Heuristic; confirm with the IF data dictionary |

### Article map used in product docs and samples

| Reference (repo map) | Intent in shipped docs | Data Boar capability (shipped) | Notes |
| -------------------- | ---------------------- | ------------------------------ | ----- |
| Art. 4º | Cybersecurity policy (USAGE Enterprise example) | Findings on customer/payment fields; `LGPD_CPF` / `CREDIT_CARD` heuristics → policy narrative | [USAGE.md](../USAGE.md#governance-lens-enterprise) |
| Art. 6º / Arts. 6–8 | Incident **action / response** plan (USAGE); sample also cites Art. 6 for **crypto** controls | Same discovery path during IR; Enterprise Lens example: PII on an API target → Art. 6º incident-plan language | Not a SOC ticketing system |
| Art. 11 | **Relevant-incident notification** to BACEN within **4 business days** | Sample `norm_tag` `BACEN 4893 Art. 11 (notificação incidente)` + recommendation text; locate copies via scan + **`--diff`** | Data Boar **does not send** the BACEN notice |
| Art. 16 | IT outsourcing / third-party cybersecurity clauses | Sample `BACEN 4893 Art. 16 (terceirização)` on vendor-related fields | Contract review stays with jurídico / CISO |

The BACEN sample header also mentions an **annual security-policy review** as programme cadence. That is **not** Art. 11 in this repo (Art. 11 is notification-only). Data Boar can feed **repeatable scan evidence** into the IF’s own review; it **does not** generate an official BACEN annual filing.

**Disclaimer:** Output is a **technical starting point**. It does **not** certify BACEN, LGPD, or FEBRABAN compliance.

---

## Anti-overclaim checklist

Before citing this primer in RFPs or audit packs:

1. Name **which connectors and samples** were in scope (PCI sample, BACEN sample, both).
2. Mark **(roadmap)** rows as planned, not delivered.
3. Keep the **QSA / SOX / BACEN** disclaimers in customer-facing text.
4. Do **not** call `--export-audit-trail` an immutable or legally binding archive.
5. Run **`--validate-config`** before production scans ([USAGE.md](../USAGE.md)).

---

## Maintainer

When features ship, update the tables above and [PRIMERS_HUB.md](PRIMERS_HUB.md). Run `python scripts/plans_hub_sync.py --write` after hub-summary edits (hub table lists `PLAN_*.md` only; this primer is indexed in **PRIMERS_HUB**).
