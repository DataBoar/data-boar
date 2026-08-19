# Governance Lens quickstart (Pro)

**Português (Brasil):** [GOVERNANCE_LENS_QUICKSTART.pt_BR.md](GOVERNANCE_LENS_QUICKSTART.pt_BR.md)

Short operator path: enable Governance Lens, generate a GRC-oriented Markdown report from an existing SQLite session, and export DOCX/PDF with **pandoc** (optional, not bundled).

**See also:** [USAGE.md](../USAGE.md#governance-lens-pro) · [TECH_GUIDE.md](../TECH_GUIDE.md#governance-lens-architecture) · [deploy/config.example.yaml](../../deploy/config.example.yaml)

## Prerequisites

- A completed scan session in the local SQLite DB (`sqlite_path` in config).
- **Pro** (or Enterprise) license tier with `governance_lens_pro` allowed — in lab, `licensing.mode: open` + `licensing.effective_tier: pro`.
- Curated framework map: licensees receive `governance_framework_map_pro.yaml` under commercial terms. Open Core ships **`config/governance_framework_map_pro.example.yaml`** for lab/tests (`governance.map_file`).

**Pandoc** is an **optional external** tool for DOCX/PDF export — not installed or bundled with Data Boar.

## 1. Enable in config

```yaml
licensing:
  effective_tier: pro   # lab only; production uses your license file / JWT

governance:
  enabled: true
  tier: pro
  map_file: config/governance_framework_map_pro.example.yaml   # lab; replace with licensed map in production
```

## 2. Run a scan or reuse a session

**New scan:**

```bash
python main.py --config config.yaml
```

**Existing session:** list sessions via the dashboard or SQLite; note the `session_id` UUID.

## 3. Generate the GRC Markdown report

```bash
python main.py --config config.yaml --governance-report ./relatorio_grc.md
```

Optional session pin:

```bash
python main.py --config config.yaml --session <session_id> --governance-report ./relatorio_grc.md
```

Omit the path to write under `report.output_dir` as `Governance_Lens_<prefix>.md`. The command prints the absolute path on **stdout**. Exit **1** if no session exists; exit **2** if combined with `--web`.

With `governance.enabled: true`, the Excel workbook also includes a **Governance View** sheet when reports are generated.

## 4. Export DOCX (pandoc)

From the repo root (paths relative to defaults file):

```bash
pandoc relatorio_grc.md --defaults config/pandoc_governance.yaml -o relatorio_grc.docx
```

Word styles come from `docs/templates/governance_reference.docx`.

## 5. Export PDF (pandoc + LaTeX)

```bash
pandoc relatorio_grc.md --defaults config/pandoc_governance.yaml \
  -o relatorio_grc.pdf --to=pdf -V pdf-engine=lualatex
```

Requires a working **LuaLaTeX** (or another engine you configure). PDF export is operator-side only.

## 6. Pandoc is optional

Data Boar delivers **pandoc-ready Markdown** and `config/pandoc_governance.yaml`. Install [pandoc](https://pandoc.org/) (and LaTeX for PDF) on the operator workstation or CI image when you need DOCX/PDF — the Python package does not depend on them.

## Disclaimer

Governance Lens output **assists technical inventory and GRC narrative**; it does **not** constitute a certified audit, legal opinion, or regulatory attestation. Human review by DPO, CISO, internal audit, or counsel is required before external use.
