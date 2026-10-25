# ATS / SLI exports layout (private tree)

**Real outputs** live under **`docs/private/`** (gitignored from `origin`). This folder documents **where generators write** so operators and assistants do not hunt by guess.

## LinkedIn Talent Playbooks v2 (MD / HTML / DOCX / PDF)

| Item | Path (under `docs/private/`) |
| ---- | ----------------------------- |
| Source Markdown (v2) | `commercial/candidates/linkedin_peer_review/individual/v2/*_PLAYBOOK_V2.pt_BR.md` |
| **Exports** (pandoc + optional wkhtmltopdf) | `commercial/ats_sli_hub/exports/v2/` |
| Subfolders | `html/`, `docx/`, `pdf/` (one file per playbook stem) |

**Generator (repo root):**

```bash
uv run python scripts/generate_talent_playbooks_v2.py
```

- **`--no-export`** — write only MD under `individual/v2/`.
- **`--export-only`** — regenerate exports from existing MD (requires **pandoc**; PDF needs **wkhtmltopdf** on PATH or default Windows install path).

**License / sensitivity:** candidate-facing copy may include **PII** — **never** commit **`docs/private/`** to the public GitHub remote.

## Maintainer ritual (full v2 regeneration)

In the **private** workspace, the operator keeps a step-by-step checklist (Portuguese) in
**`docs/private/commercial/ats_sli_hub/README_RITUAL_EXPORTS.pt_BR.md`** — run **`generate_talent_playbooks_v2.py`**, then **`ats-hub-export.ps1`** via **`pwsh`**, then optional **wkhtmltopdf** batch for hub `exports/pdf/*.html`. That file is not on GitHub `origin`.

## Finding export files quickly (Windows primary dev PC)

Prefer **`.\scripts\es-find.ps1`** ( **`es.exe`** / Everything index). Example:

```powershell
.\scripts\es-find.ps1 -Query "*PLAYBOOK_V2*" -SearchRoot "docs\private\commercial\ats_sli_hub\exports\v2" -MaxCount 40
```

If **`es.exe`** is missing: **`-FallbackPowerShell`** on the same script, or **`Glob`** inside the workspace. See **`docs/ops/EVERYTHING_ES_PRIMARY_WINDOWS_DEV_LAB.md`**.
