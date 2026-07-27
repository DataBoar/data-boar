# PLAN: Unified session report export CLI (#1326)

**Status:** Done
**Date:** 2026-07-27
**Authors:** Fabio Leitao
**Priority:** H1
**GitHub:** [Issue #1326](https://github.com/DataBoar/data-boar/issues/1326)

<!-- plans-hub-summary: Unified `data-boar-report --format` exports (md/docx/pdf/xlsx/heatmap/dsar/json/audit-trail/all) from SQLite without re-scan; thin per-format console scripts. -->

**Depends on:** #1325 (`--regenerate-report` / Excel+heatmap path on `main.py`)

**Relates to:** `PLAN_PDF_GRC_REPORT.md` (GRC JSON PDF — separate track), `BENCHMARK_EVOLUTION.md` (`data-boar-report` executive Markdown)

---

## Context

Operators need one CLI surface to regenerate **all** session artefacts from **SQLite only** (no live connectors, no `--web`). Block B (#1325) added `--regenerate-report` on `main.py` for Excel + heatmap + `learned_patterns`. This plan extends **`data-boar-report`** with `--format` and thin wrappers (`data-boar-xlsx`, `data-boar-pdf`, …) while keeping **`--regenerate-report`** as a stable alias on `main.py`.

**Renderers:** `python-docx` and `reportlab` only (pure Python — no WeasyPrint/pandoc/xhtml2pdf) to preserve min-spec / musl gate posture (#821).

---

## Scope

| Format | Output | Engine |
| ------ | ------ | ------ |
| `md` | Executive Markdown | `report.executive_report` (default) |
| `docx` | Executive Word | `report.executive_docx` |
| `pdf` | Executive PDF | `report.executive_pdf` |
| `xlsx` | Excel workbook | `report.generator.generate_report` |
| `heatmap` | PNG | `report.generator.generate_session_heatmap` |
| `dsar` | DSAR JSON | `core.dsar_export` |
| `json` | Scan manifest JSON | `report.scan_evidence._build_manifest` |
| `audit-trail` | Audit trail JSON | `core.audit_export` |
| `all` | Full bundle | All of the above |

---

## Implementation checklist

| # | Task | Status |
| - | ---- | ------ |
| 1 | `report/session_export.py` dispatcher + docx/pdf renderers | ✅ Done |
| 2 | `cli/reporter.py` `--format`, `--output-dir`, `--dsar-include-samples` | ✅ Done |
| 3 | `cli/format_entrypoints.py` + `[project.scripts]` wrappers | ✅ Done |
| 4 | `generate_session_heatmap()` in `report/generator.py` | ✅ Done |
| 5 | Tests per format (`tests/test_session_report_export_formats.py`) | ✅ Done |
| 6 | `docs/data_boar.1` + `data-boar-report --help` | ✅ Done |
| 7 | Keep `main.py --regenerate-report` unchanged (compat alias) | ✅ Done |

---

## Compatibility

- **`main.py --regenerate-report`:** retained; documented as the Excel+heatmap shortcut. Unified export lives on **`data-boar-report --format`**.
- **Default `data-boar-report`:** `--format md` preserves pre-#1326 behaviour.

---

## Acceptance

- `data-boar-report --format <fmt> --session-id <id> --config <cfg>` writes expected artefact(s) under `report.output_dir`.
- `check-all.sh --enforced` green; one pytest per format (+ `all` bundle test).
