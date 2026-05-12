# Reports and compliance-oriented outputs

**Português (Brasil):** [REPORTS_AND_COMPLIANCE_OUTPUTS.pt_BR.md](REPORTS_AND_COMPLIANCE_OUTPUTS.pt_BR.md)

**Audience:** CISOs, DPOs, integrators, and **students** who need one place to see how **technical scan artefacts** (SQLite, row metadata) become **human-facing** deliverables—without treating the product as a full enterprise GRC suite.

**See also:** [COMPLIANCE_METHODOLOGY.md](COMPLIANCE_METHODOLOGY.md) (verification modules and ROPA-style automation boundaries), [COMPLIANCE_AND_LEGAL.md](COMPLIANCE_AND_LEGAL.md) (legal posture), [MAP.md](MAP.md) (concern-first navigation).

---

## What ships today vs what is planned

| Output | Status | Notes |
| ------ | ------ | ----- |
| **Excel (XLSX)** per scan session | **Shipped** | Primary tabular artefact: findings, report info, trends when history exists, optional cross-ref and suggested-review sheets—see below. |
| **Executive Markdown (`POC_SUMMARY_*.md`) + evidence YAML (`scan_manifest_*.yaml`)** | **Shipped** | Written alongside the XLSX when `generate_report` runs. Markdown is stakeholder-safe: aggregated patterns/counts, **methodology / security** narrative, **Top 3** APG priorities, and a **full per-pattern remediation inventory**; no column/table/path/cell samples. YAML captures sampling/timeouts and DBA/SRE audit bullets. Regenerate Markdown from SQLite only: **`data-boar-report`** — [USAGE.md](USAGE.md) (section 5) ([pt-BR](USAGE.pt_BR.md)). |
| **Heatmap PNG** | **Shipped** | Visual density companion to the session report. |
| **HTML** reports / dashboard views | **Shipped** | Operator-facing; tier and config may apply. |
| **Audit trail JSON** (`--export-audit-trail`) | **Shipped** | Machine-readable governance snapshot (sessions summary, wipe log, runtime trust, dashboard transport, **maturity integrity counts**). Schema version field: see `core/audit_export.py` and [ADR 0037](adr/ADR-0037-data-boar-self-audit-log-governance.md). |
| **Maturity self-assessment POC** (dashboard questionnaire) | **Shipped (gated)** | When `api.maturity_self_assessment_poc_enabled` and tier allow it: answers stored in SQLite with optional row HMAC; **CSV and Markdown download** via `GET /{locale}/assessment/export?format=csv|md`—not a combined scan PDF. |
| **Executive PDF (“GRC-like” from scan findings)** | **Planned** | Registered as a **Pro-tier** feature name in `core/licensing/tier_features.py` (`report_pdf`); generator module is **not** present under `report/` yet. Maintainers trace scope via the internal plans tree (plain-text path `docs/plans/`, entry filename **`PLAN_PDF_GRC_REPORT.md`**) from **docs/README** — *Internal and reference*; this doc does **not** link there per [ADR 0004](adr/ADR-0004-external-docs-no-markdown-links-to-plans.md). |
| **GRC executive JSON (risk matrix contract)** | **Partial (Python)** | Spec + example: [GRC_EXECUTIVE_REPORT_SCHEMA.md](GRC_EXECUTIVE_REPORT_SCHEMA.md) ([pt-BR](GRC_EXECUTIVE_REPORT_SCHEMA.pt_BR.md)), [../schemas/grc_executive_report.v1.example.json](../schemas/grc_executive_report.v1.example.json). Consolidator class **`report.grc_reporter.GRCReporter`** builds the payload from caller-supplied rows; optional LGPD-aligned **density** uses **`core.intelligence`** (`calculate_risk`, `PII_MAPPING`) plus **`report.grc_risk_taxonomy`** (`LgpdDensityRiskConfig`, full SQLite ingest still roadmap). Optional **Streamlit** executive viewer: install with ``uv sync --extra grc-dashboard``, then ``streamlit run app/dashboard.py`` (path override: env ``DATA_BOAR_GRC_JSON``). **XLSX + PDF export** from the same JSON: ``uv run python scripts/export_reports.py --input <path-to-v1.json>`` (writes ``*_remediation.xlsx`` and ``*_executive.pdf`` beside the input unless ``--xlsx`` / ``--pdf`` are set); implementation **`report.grc_export_multiformat`**. |

---

## Pipeline: from findings to “CISO language”

1. **Scan** writes **metadata-only** rows into SQLite (`database_findings`, `filesystem_findings`, `scan_failures`, session tables, optional aggregated cross-ref, optional data-source inventory—when implemented for the session).
2. **`generate_report`** (`report/generator.py`) reads those rows and builds:
   - **Executive summary** sheet (aggregated view).
   - **Database findings** / **Filesystem findings** sheets (columnar detail: target, location, pattern, sensitivity, `norm_tag`, recommendation text where configured).
   - **Report info** (session, version, optional jurisdiction-hint notes when enabled—heuristic, not legal conclusion).
   - Optional sheets: **Trends**, **Cross-ref data – ident. risk**, **Suggested review (LOW)**, **Data source inventory**, **Scan failures**.
3. **Heatmap** image is written alongside the workbook.
4. **Executive Markdown + manifest** (`POC_SUMMARY_*.md`, `scan_manifest_*.yaml`) are best-effort: failure does not block the XLSX (see [USAGE.md](USAGE.md) section 5, [pt-BR](USAGE.pt_BR.md)).
5. **Operators** combine Excel + heatmap + optional **audit trail JSON** and optional **desk-summary Markdown** for governance and audit **preparation**—still not a substitute for counsel or enterprise GRC workflow.

---

## Maturity assessment exports (separate from scan XLSX)

The **organisational maturity** POC is a **parallel** track: answers and rubric scoring are rendered to **CSV** or **Markdown** for download. They are **self-reported signals** (disclaimer in export), not a product determination of legal adequacy.

Integrity summaries for those answers can also appear inside **`--export-audit-trail`** JSON (`maturity_assessment_integrity`) for alignment with dashboard/`GET /status`—see ADR 0037.

---

## Future “single PDF” and JSON feeding it (design direction)

**GRC JSON contract (CISO/DPO matrix):** before or alongside PDF, use the **risk-matrix** payload described in [GRC_EXECUTIVE_REPORT_SCHEMA.md](GRC_EXECUTIVE_REPORT_SCHEMA.md) so React/Streamlit/report engines share one **audit-ready** shape (`report_metadata`, `executive_summary`, `compliance_mapping` hints, `detailed_findings`, `recommendations`).

When a **scan-linked PDF** ships, a sensible **data contract** is likely to merge:

- **Findings slice:** aggregated counts, top severities, jurisdiction-tension flags (metadata-only), heatmap image reference or embedded PNG.
- **Governance slice:** subset of `build_audit_trail_payload` (schema version, app version, session list, integrity fields).
- **Maturity slice (optional):** one chosen batch’s rubric summary + disclaimer—not auto-merged legal basis from connector names.

**Coordination with external LLM tooling (e.g. Gemini):** use the **stable JSON** from `--export-audit-trail` and **exported CSV/MD** as inputs to **draft** narrative sections; keep **canonical** scoring and tables in-repo. Do not paste secrets or raw PII into prompts.

---

## Product guardrails (inventory auto-fill)

**Titular inference** (e.g. “tripulante vs motorista” from column or system context) and **automatic “base legal”** strings tied to a product name (e.g. customs systems) are **high false-positive** and **high misrepresentation** risks. Public methodology is to surface **categories, locations, tension, and triage priority** and leave **lawful basis and data-subject role** to **DPO / counsel**—see [COMPLIANCE_METHODOLOGY.md](COMPLIANCE_METHODOLOGY.md) and [ADR 0038](adr/ADR-0038-jurisdictional-ambiguity-alert-dont-decide.md). If a future feature adds **suggested** legal-language templates, they must remain **explicitly non-authoritative** and opt-in.

---

## Where to configure and test

- **Report output directory and behaviour:** [USAGE.md](USAGE.md) — `report` keys ([pt-BR](USAGE.pt_BR.md)).
- **Executive Markdown from SQLite:** [USAGE.md](USAGE.md) (section 5) — `data-boar-report` ([pt-BR](USAGE.pt_BR.md)).
- **POC maturity pack path and gate:** [USAGE.md](USAGE.md) — `api.maturity_self_assessment_poc_enabled`, `api.maturity_assessment_pack_path` ([pt-BR](USAGE.pt_BR.md)).
- **Synthetic / lab validation:** [TESTING_POC_GUIDE.md](TESTING_POC_GUIDE.md) ([pt-BR](TESTING_POC_GUIDE.pt_BR.md)) for corpus and SBOM-style reviewer notes—not a substitute for this output map.
