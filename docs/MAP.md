# Documentation topic map (navigation by concern)

**Português (Brasil):** [MAP.pt_BR.md](MAP.pt_BR.md)

This page is a **concern-driven index**: it connects high-level questions (what a **CISO**, **DPO**, or **security architect** cares about) to the concrete guides where behaviour, config keys, and limits are defined. **Child and minor data** is listed **first** on purpose: the product treats that **linguistic category** as a dedicated lane (detector, report elevation, samples—not a generic PII footnote). Use this map when you already know the topic (e.g. minors, cross-border hints) and want the shortest path without browsing every folder. The full flat index remains **[README.md](README.md)** ([pt-BR](README.pt_BR.md)).

---

## POC documentation spine (v1.7.x)

For a **proof-of-concept** or partner dry-run, read in this order so dense docs do not hide posture-critical material:

1. **[TECH_GUIDE.md](TECH_GUIDE.md)** ([pt-BR](TECH_GUIDE.pt_BR.md)) — install, first scan, ports, connectors overview.
2. **This MAP** — scan the tables below (minors → jurisdiction → detection bridges → governance of the auditor). For **multinational tension** narrative (not legal advice), read **[JURISDICTION_COLLISION_HANDLING.md](JURISDICTION_COLLISION_HANDLING.md)** ([pt-BR](JURISDICTION_COLLISION_HANDLING.pt_BR.md)) after the jurisdiction rows.
3. **[USAGE.md](USAGE.md)** ([pt-BR](USAGE.pt_BR.md)) — `detection` keys, `report.jurisdiction_hints`, CLI/API/dashboard flags.
4. **Governance of the auditor (evidence today vs gaps):** **[ADR 0037](adr/ADR-0037-data-boar-self-audit-log-governance.md)** (English).
5. **Jurisdiction hints (not legal conclusions):** **[ADR 0026](adr/ADR-0026-optional-jurisdiction-hints-dpo-facing-heuristic-metadata-only.md)** (English) plus the jurisdiction row in the table below.

**Execution plans and PMO tables** live under plain-text path ``docs/plans/`` in your checkout; this map does **not** link there from product-tier Markdown ([ADR 0004](adr/ADR-0004-external-docs-no-markdown-links-to-plans.md)). Use **[docs/README.md](README.md)** — *Internal and reference* ([pt-BR](README.pt_BR.md)) as the deliberate entry (PLANS_TODO, PLANS_HUB, completed plans).

---

## ADR hooks (POC-relevant, English bodies)

| ADR | Why it matters in a POC |
| --- | ----------------------- |
| [0000](adr/ADR-0000-project-origin-and-adr-baseline.md) | Baseline: ADRs complement code and plans; where to look first. |
| [0004](adr/ADR-0004-external-docs-no-markdown-links-to-plans.md) | Why pitch docs link here and to **docs/README**, not straight into ``docs/plans/``. |
| [0026](adr/ADR-0026-optional-jurisdiction-hints-dpo-facing-heuristic-metadata-only.md) | Jurisdiction hints: metadata-only, DPO-facing; limits of legal claims. |
| [0035](adr/ADR-0035-readme-stakeholder-pitch-vs-deck-vocabulary.md) | README stakeholder tone vs optional deck vocabulary elsewhere. |
| [0036](adr/ADR-0036-exception-and-log-pii-redaction-pipeline.md) | Exception/log redaction; safer operator evidence in logs and DB text. |
| [0037](adr/ADR-0037-data-boar-self-audit-log-governance.md) | Self-audit: what is provable today (sessions, export trail, wipes) vs explicit gaps. |

Full index: [adr/README.md](adr/README.md) ([pt-BR](adr/README.pt_BR.md)).

---

## Minor data and child-related privacy (technical scope)

| Question | Read first | Config / behaviour | Related |
| -------- | ---------- | ------------------- | ------- |
| How does the product flag **possible minor** data (DOB, age columns), thresholds, optional full scan, and cross-reference? | **[MINOR_DETECTION.md](MINOR_DETECTION.md)** ([pt-BR](MINOR_DETECTION.pt_BR.md)) | `detection.minor_age_threshold`, `detection.minor_full_scan`, `detection.minor_cross_reference` | [SENSITIVITY_DETECTION.md](SENSITIVITY_DETECTION.md) ([pt-BR](SENSITIVITY_DETECTION.pt_BR.md)), [USAGE.md](USAGE.md) `detection` / report sections ([pt-BR](USAGE.pt_BR.md)) |
| Brazil **FELCA** (digital child/adolescent statute) and how the product positions **metadata-only** support? | **[COMPLIANCE_FRAMEWORKS.md](COMPLIANCE_FRAMEWORKS.md)** — *Auditable and management standards* ([pt-BR](COMPLIANCE_FRAMEWORKS.pt_BR.md)) | Same: minor flags are inventory-oriented, not age verification | [COMPLIANCE_AND_LEGAL.md](COMPLIANCE_AND_LEGAL.md) ([pt-BR](COMPLIANCE_AND_LEGAL.pt_BR.md)) |
| **U.S.** COPPA / CA AB 2273 / CO CPA minors — **technical** YAML samples (norm tags, not legal advice)? | **[COMPLIANCE_FRAMEWORKS.md](COMPLIANCE_FRAMEWORKS.md)** — compliance samples table and disclaimers ([pt-BR](COMPLIANCE_FRAMEWORKS.pt_BR.md)) | Files under [compliance-samples/](compliance-samples/) (e.g. `compliance-sample-us_ftc_coppa.yaml`) | [compliance-samples/README.md](compliance-samples/README.md) ([pt-BR](compliance-samples/README.pt_BR.md)) |

Design history for minor detection lives in a **completed** plan file under `docs/plans/completed/` in your checkout (`PLAN_MINOR_DATA_DETECTION`); the operator guide above is the maintained entry point (no plan link here per information-architecture rules).

---

## Jurisdiction hints (heuristic, metadata-only)

| Question | Read first | Config / behaviour | Related |
| -------- | ---------- | ------------------- | ------- |
| What are **jurisdiction hints**, who are they for, and how do I enable them (CLI, API, dashboard, YAML)? | **[USAGE.md](USAGE.md)** — search **jurisdiction_hints** / **Report info** ([pt-BR](USAGE.pt_BR.md)) | `report.jurisdiction_hints`, `--jurisdiction-hint`, `POST /scan` body | [COMPLIANCE_AND_LEGAL.md](COMPLIANCE_AND_LEGAL.md) ([pt-BR](COMPLIANCE_AND_LEGAL.pt_BR.md)) |
| Why hints are **not** legal conclusions and what ADR locked in? | **[ADR 0026](adr/ADR-0026-optional-jurisdiction-hints-dpo-facing-heuristic-metadata-only.md)** (English) | Index: [adr/README.md](adr/README.md) ([pt-BR](adr/README.pt_BR.md)) | [COMPLIANCE_TECHNICAL_REFERENCE.md](COMPLIANCE_TECHNICAL_REFERENCE.md) ([pt-BR](COMPLIANCE_TECHNICAL_REFERENCE.pt_BR.md)) |
| Multinational **“perfect storm”** — overlapping regimes, anchor vs drift, port-style storyboard? | **[JURISDICTION_COLLISION_HANDLING.md](JURISDICTION_COLLISION_HANDLING.md)** ([pt-BR](JURISDICTION_COLLISION_HANDLING.pt_BR.md)) | Same opt-in hints; **no** numeric collision score in product yet | [ADR 0038](adr/ADR-0038-jurisdictional-ambiguity-alert-dont-decide.md), [use-cases/README.md](use-cases/README.md) ([pt-BR](use-cases/README.pt_BR.md)) — incl. port logistics storyboard |

---

## Sensitive detection and compliance depth (bridge topics)

| Question | Read first | Notes |
| -------- | ---------- | ----- |
| Regex, ML/DL, overrides, connector format hints | **[SENSITIVITY_DETECTION.md](SENSITIVITY_DETECTION.md)** ([pt-BR](SENSITIVITY_DETECTION.pt_BR.md)) | Pairs with [USAGE.md](USAGE.md) report and `detection` keys ([pt-BR](USAGE.pt_BR.md)) |
| Norm tags, samples, multi-region operation | **[COMPLIANCE_FRAMEWORKS.md](COMPLIANCE_FRAMEWORKS.md)** ([pt-BR](COMPLIANCE_FRAMEWORKS.pt_BR.md)) | Includes Brazil insurance LGPD anchor subsection and sample table |
| Encodings, API limits, evidence posture (IT / DPO) | **[COMPLIANCE_TECHNICAL_REFERENCE.md](COMPLIANCE_TECHNICAL_REFERENCE.md)** ([pt-BR](COMPLIANCE_TECHNICAL_REFERENCE.pt_BR.md)) | Operational limits, not legal advice |

---

## Governance of the auditor (who watches the watcher?)

| Question | Read first | Notes |
| -------- | ---------- | ----- |
| What evidence exists **today** for scan attribution, wipes, export bundles, and log redaction? What is **not** implemented yet? | **[ADR 0037](adr/ADR-0037-data-boar-self-audit-log-governance.md)** (English) | Honest baseline for **CISO / SOC2-style** narratives; avoids over-claiming per-report or per-config immutable audit rows. |
| SRE alignment (health, logs, future metrics) | **[OBSERVABILITY_SRE.md](OBSERVABILITY_SRE.md)** ([pt-BR](OBSERVABILITY_SRE.pt_BR.md)) | Links this ADR for governance-of-the-auditor framing. |

---

## Public tree PII hygiene (operator ritual)

| Question | Read first | Notes |
| -------- | ---------- | ----- |
| On-demand pass: private seeds, **HEAD** scan order, leak prevention defaults | **[PII_REMEDIATION_RITUAL.md](ops/PII_REMEDIATION_RITUAL.md)** ([pt-BR](ops/PII_REMEDIATION_RITUAL.pt_BR.md)) | Session keyword **`pii-remediation-ritual`**; complements—not replaces—the cadence below. |
| Short / mid / long cadence, **SAFE** checklist, history rewrite cautions | **[PII_PUBLIC_TREE_OPERATOR_GUIDE.md](ops/PII_PUBLIC_TREE_OPERATOR_GUIDE.md)** ([pt-BR](ops/PII_PUBLIC_TREE_OPERATOR_GUIDE.pt_BR.md)) | Canonical runbook; **`pii-fresh-audit`** for Windows fresh-clone proof. |

---

## Reports, exports, and GRC-shaped outputs

| Question | Read first |
| -------- | ---------- |
| How do SQLite findings become **Excel**, **heatmap**, **executive Markdown** (`POC_SUMMARY_*.md`), **evidence YAML** (`scan_manifest_*.yaml`), **audit JSON**, and **maturity CSV/MD**? How do I regenerate the desk summary from SQLite (`data-boar-report`)? What is **planned** vs **shipped** for a scan-linked **PDF**? Where is the **GRC risk-matrix JSON** contract? | **[REPORTS_AND_COMPLIANCE_OUTPUTS.md](REPORTS_AND_COMPLIANCE_OUTPUTS.md)** ([pt-BR](REPORTS_AND_COMPLIANCE_OUTPUTS.pt_BR.md)) · **[USAGE.md](USAGE.md)** section 5 ([pt-BR](USAGE.pt_BR.md)) · **[GRC_EXECUTIVE_REPORT_SCHEMA.md](GRC_EXECUTIVE_REPORT_SCHEMA.md)** ([pt-BR](GRC_EXECUTIVE_REPORT_SCHEMA.pt_BR.md)) |

---

## Cursor agent cold start (token-aware)

| Question | Read first | Notes |
| -------- | ---------- | ----- |
| New chat, **low context**, or operator typed **`short`** / **`token-aware`** — where do I start without re-reading all of **`AGENTS.md`**? | **[OPERATOR_AGENT_COLD_START_LADDER.md](ops/OPERATOR_AGENT_COLD_START_LADDER.md)** ([pt-BR](ops/OPERATOR_AGENT_COLD_START_LADDER.pt_BR.md)) | One-screen **ordered ladder**, task router, seven non-negotiables (homelab **`ssh`** = §7); then **`CURSOR_AGENT_POLICY_HUB`** / **`TOKEN_AWARE_SCRIPTS_HUB`** as needed. |

---

## Where this fits

- **Technical install and run:** [TECH_GUIDE.md](TECH_GUIDE.md) ([pt-BR](TECH_GUIDE.pt_BR.md)) ends with a short **Topic map** pointer back here.
- **Product philosophy (evidence over theatre):** [philosophy/THE_WHY.md](philosophy/THE_WHY.md) ([pt-BR](philosophy/THE_WHY.pt_BR.md)); retention boundary in sensitive zones: [ADR 0039](adr/ADR-0039-retention-evidence-posture-bonded-customs-adjacent-contexts.md).
- **Glossary (terms by theme):** [GLOSSARY.md](GLOSSARY.md) ([pt-BR](GLOSSARY.pt_BR.md)).

If a topic is missing from this map, add a row in **both** `MAP.md` and `MAP.pt_BR.md` in the same PR.

## Keeping hubs aligned with repo truth

**Plans sequencing and file inventory** are enforced by **`plans_hub_sync.py`** and **`plans-stats.py`** (see **CONTRIBUTING.md** and pre-commit). **This MAP** is curated: after you add or change hub rows, run **`.\scripts\check-all.ps1`** or **`.\scripts\lint-only.ps1`** when the diff is docs-only, and follow the **doc-hubs-plans-sync** Cursor skill (`.cursor/skills/doc-hubs-plans-sync/SKILL.md`) so **ADR index**, **AGENTS** last-ADR pointer, and **paired pt-BR** stay in sync.
