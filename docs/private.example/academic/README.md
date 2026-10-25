# Academic contracts and enrollment notes (private only)

**This folder is a template.** Real files (signed **PUC-Rio** contracts, enrollment PDFs, benefit terms, receipts) belong under **`docs/private/academic/`** on your machine — **gitignored**, never pushed to GitHub.

## Bootstrap

```powershell
# Windows (PowerShell, repo root)
New-Item -ItemType Directory -Force -Path docs/private/academic | Out-Null
```

```bash
mkdir -p docs/private/academic
```

## Suggested local filenames (examples)

- `PUC-Rio-especializacao-contrato.pdf` — signed contract or annex describing **extension-course benefits** (two courses, value caps, deadlines). **Do not** commit.
- `Learning_and_certs.md` — if you keep a single learning ledger, it may instead live at **`docs/private/Learning_and_certs.md`** (repo convention elsewhere in plans).

## Tracked planning (public repo)

- **PUC-Rio Digital extension recommendations** (course titles, bundles): **`docs/plans/PORTFOLIO_AND_EVIDENCE_SOURCES.md`** — subsection **PUC-Rio Digital extension courses** under section 3 (after the PUCRS table). Align choices with **secretaria** confirmation against your **private** contract.
- **PUCRS** (Porto Alegre) supplements: same file, **PUCRS extension supplements** table.

## Policy

- **`docs/PRIVATE_OPERATOR_NOTES.md`** — private tree rules; no personal identifiers in **tracked** Markdown.
