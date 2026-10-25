# Commercial notes — template (tracked in Git)

**This folder is versioned** as a **layout reminder only**. **Do not** put real pricing, rate cards, or client-specific commercial terms in Git.

## Where the real files live

Create **`docs/private/commercial/`** locally (same **`docs/private/`** tree as **`homelab/`** — **gitignored**). **Operator OPEX / lista de compras / luz** fit better in sibling **`docs/private/operator_economics/`** (see **`../operator_economics/README.md`**). Place **client-facing** sensitive documents here, for example:

- Maturity / readiness **consulting pricing** study (EN + pt-BR pair).
- Partner margin notes, proposal templates with **numbers** (redact before any copy to tracked files).
- **Talent candidates** (dossiers, per-person learning roadmaps): see **`candidates/README.md`** in this folder for layout; public **archetype** guide: **`docs/TALENT_POOL_LEARNING_PATHS.md`**. **LinkedIn / ATS private supplement** (headline, About, featured — copy to `docs/private/commercial/`): **`LINKEDIN_ATS_PRIVATE_SUPPLEMENT_TEMPLATE.pt_BR.md`**. Operator runbooks: **`docs/ops/TALENT_DOSSIER_AND_POOL_SYNC.md`**, **`docs/ops/LINKEDIN_ATS_PLAYBOOK.md`**.
- **ATS / SLI export bundles (v2 playbooks — MD/HTML/DOCX/PDF):** layout and generator pointer — **`ats_sli_hub/exports/README.md`** (real outputs only under **`docs/private/.../ats_sli_hub/exports/v2/`**).

## Bootstrap (PowerShell, repo root)

```powershell
New-Item -ItemType Directory -Force -Path docs/private/commercial | Out-Null
# Copy from your backup or recreate; never commit contents of docs/private/
```

## Policy

- **`docs/PRIVATE_OPERATOR_NOTES.md`** — private tree rules.
- **Agents:** may **`read_file`** under **`docs/private/`** on the operator workstation; **never** paste full rate tables into **tracked** Markdown or **public** issues.
- **Automation:** **`tests/test_confidential_commercial_guard.py`** (CI + pre-commit) fails if **`docs/private/`** or stray **`docs/.../commercial/`** paths appear in the Git index, or if forbidden **pricing-study** filenames sit under tracked **`docs/`**. Cursor rule: **`.cursor/rules/confidential-commercial-never-tracked.mdc`**. Skill: **`.cursor/skills/confidential-commercial-layout/SKILL.md`**.

## Naming (suggestion)

- `MATURITY_CONSULTING_PRICING_STUDY.md` + `MATURITY_CONSULTING_PRICING_STUDY.pt_BR.md` — internal working conclusions, scenarios, what-if, Data Boar licensing **interaction** (all **confidential**).
