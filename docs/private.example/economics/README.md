# Operator economics — template (tracked in Git)

**This folder is versioned** as a **layout reminder only**. **Do not** put real amounts, account numbers, or utility identifiers in Git.

## Purpose (local only)

Create **`docs/private/operator_economics/`** on your machine for **operator-side** money and cost planning:

- **Home / lab OPEX:** electricity baselines, bandwidth, subscriptions (e.g. editor, APIs) — *your* household/lab, not a client’s bill.
- **Investment / shopping lists:** hardware wishlists, CapEx notes, phased spend — still **confidential**, still **gitignored**.

## How it relates to `commercial/`

| Tree                                   | Use                                                                                                                                        |
| ----                                   | ---                                                                                                                                        |
| **`docs/private/commercial/`**         | **Client-facing** economics: consulting pricing studies, proposals with numbers, partner margins, engagement-specific facts.               |
| **`docs/private/operator_economics/`** | **Your** runway and cost base: personal/lab operating costs, tools, upgrades — informs *your* pricing floor indirectly, not customer SOWs. |

If a file mixes both (e.g. one workbook), pick **one primary home** or split into two linked files; avoid duplicating sensitive numbers.

## Suggested local-only filenames (you create; never commit)

Use plain Markdown under **`docs/private/operator_economics/`** (or split by language). These names are **examples**—adjust to taste:

| File (example)                                | Content                                                                                                                                                                                                                                                                      |
| --------------                                | -------                                                                                                                                                                                                                                                                      |
| **`EFFORT_PHASES_DEMO_BETA_PRODUCTION.md`**   | Rough **effort ranges** and assumptions per release stage; what would unlock **help** or funding; links to **`docs/plans/`** when a slice graduates to tracked work.                                                                                                         |
| **`FINANCING_AND_BUDGET_OPTIONS.md`**         | Runway, grants, pricing comparisons, **purchase** options—still **private** if it reveals strategy.                                                                                                                                                                          |
| **`OPERATOR_QA_JOURNAL.pt_BR.md`** (or `.md`) | Dated **questions / answers / follow-ups** from you + assistant—private “thinking log”; optional **meme / metaphor interpretations** you asked the assistant to preserve for re-study; index rows can point here from **`author_info/RECENT_OPERATOR_SYNC_INDEX.pt_BR.md`**. |
| **`BITWARDEN_SUBSCRIPTION_DECISION_NOTES*.md`** | Optional **maintainer copy**: decision matrix (**Free / Premium / Families / Teams**), “no AI seat,” FX notes — **not** current prices (link **bitwarden.com/pricing**). Tracked operator surface: **`docs/ops/OPERATOR_SECRETS_BITWARDEN*.md`**. |

**Version history:** Optional **nested Git** (or backups) for the whole **`docs/private/`** tree—see tracked **[PRIVATE_LOCAL_VERSIONING.md](../../ops/PRIVATE_LOCAL_VERSIONING.md)** ([pt-BR](../../ops/PRIVATE_LOCAL_VERSIONING.pt_BR.md)).

## Bootstrap (PowerShell, repo root)

```powershell
New-Item -ItemType Directory -Force -Path docs/private/operator_economics | Out-Null
Copy-Item docs/private.example/economics/README.md docs/private/operator_economics/
# Edit locally; never commit docs/private/
```

## Policy

- **`docs/PRIVATE_OPERATOR_NOTES.md`** — full private layout table.
- **Agents:** may **`read_file`** here when you ask for cost/runway help; **never** paste full tables into **tracked** files or public issues.
