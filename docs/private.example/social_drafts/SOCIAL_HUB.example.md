# Social publish hub — example layout (tracked)

**Copy to:** a path under your **gitignored** `docs/private/` tree (e.g. next to your local drafts hub) and fill the table. **Do not** put real URLs or metrics in **tracked** files if they belong in operator-only context.

## Status legend

| Estado      | Meaning        |
| ----------- | -------------- |
| `draft`     | Not published  |
| `scheduled` | Queued in platform |
| `published` | Live           |
| `skipped`   | Will not use   |
| `deferred`  | Postponed      |

## Inventory table (template)

| # | Rede | Rascunho | Tema | Alvo | Estado | Publicado em | URL / notas |
| - | ---- | -------- | ---- | ---- | ------ | ------------ | ----------- |
| 1 | LinkedIn | `YYYY-MM-DD_linkedin_topic.md` | short | YYYY-MM-DD | draft | | |

## Related

- Editorial cadence files (optional, same private folder): `EDITORIAL_*.md`
- Draft Markdown (operator tree): `docs/private/social_drafts/drafts/` — pattern `YYYY-MM-DD_<network>_<topic>.md` (ISO date prefix with hyphens).
- **Filename prefix rule (mirror of private hub):** use **publication date** after the post is live, or **next planned publish date** while still draft/scheduled/deferred. Rename files when the date changes; keep the **Rascunho** column in `editorial/SOCIAL_HUB.md` in sync. Pairs (Threads + Instagram, etc.) may use **different** date prefixes if posts went out on different days.

## Draft naming (summary)

| Prefix meaning | Inventory `Estado` |
| --- | --- |
| Date the post **went live** on that network | `published` |
| **Next planned** publish date | `draft`, `scheduled`, `deferred` |

Concrete examples stay **only** under gitignored `docs/private/` — not in this tracked stub.
