# Social publishing, today-mode, and carryover

**Português (Brasil):** [SOCIAL_PUBLISH_AND_TODAY_MODE.pt_BR.md](SOCIAL_PUBLISH_AND_TODAY_MODE.pt_BR.md)

**Purpose:** Tie **dated** operator checklists (`OPERATOR_TODAY_MODE_*.md`), the **rolling carryover** queue, and **private** social editorial work (**`docs/private/social_drafts/`**) so planned posts are not invisible, deferrals get a date, and ad-hoc manual posts still leave a **durable trace** in the hub and optional **evidence** files.

**No automation posts for you:** this is **process + paths**. The assistant follows these rules when you use **`today-mode`**, **`carryover-sweep`**, **`eod-sync`**, or **`social-today-check`** (see **`.cursor/rules/session-mode-keywords.mdc`**).

---

## Source of truth (private tree)

| What | Where |
| --- | --- |
| Inventory (L\*/X\*/T\*/IG\*/W\*, URLs, estado) | **`docs/private/social_drafts/editorial/SOCIAL_HUB.md`** |
| Month grid (plan vs done) | **`docs/private/social_drafts/editorial/EDITORIAL_MASTER_CALENDAR_YYYY-MM.pt_BR.md`** (rename month as needed) |
| Post Markdown + filename prefix rule | **`docs/private/social_drafts/drafts/`** — see **Convenção de nomes** in the hub |

---

## Morning (`carryover-sweep` / `operator-day-ritual.ps1 -Mode Morning`)

1. Skim **SOCIAL_HUB** for rows where **Alvo editorial** is **today** or **tomorrow** and **Estado** is **`draft`**, **`scheduled`**, or **`deferred`** (with a note).
2. Skim the **month calendar** row for **today** / **tomorrow** (if the file exists for the current month).
3. If nothing is due, stop — **no spam**.

**Script hint:** the morning ritual prints paths to the hub and any **`EDITORIAL_MASTER_CALENDAR_*.pt_BR.md`** under **`editorial/`** when present.

---

## Defer / carryover

If a planned post **does not** go out:

1. **SOCIAL_HUB:** set **Estado** to **`deferred`** (or keep **`draft`**) and add **Next target date** in **URL / notas** or **Alvo editorial**.
2. **Rename** the draft file prefix to **`YYYY-MM-DD`** = the **new** planned date (see hub README).
3. **EDITORIAL_MASTER:** adjust the calendar row or add a **carryover** line for the new month if needed.
4. **Optional:** add one line to **`docs/ops/today-mode/CARRYOVER.md`** only when the deferral is a **real** cross-day commitment (not every micro-move).

---

## End of day (`eod-sync`)

Before closing: if you **published** something today, update **SOCIAL_HUB** (**Estado**, **Publicado em**, **URL**). If you only **scheduled** it, mark **`scheduled`** and note the platform time if useful.

---

## Ad-hoc manual posts (blog / Data Boar / any network)

When you publish **without** a pre-existing draft row (or the assistant learns after the fact):

1. **SOCIAL_HUB:** add or update the **inventory row** (new id **L\*/X\*/…** if needed), **`published`**, date, permalink, short note (**manual / unplanned**).
2. **Evidence (optional but recommended):** create a file under **`docs/private/social_drafts/drafts/evidence/`** (create the folder if missing). Use this filename pattern (single line, no spaces):

   `YYYY-MM-DD_evidence_<network>_<short-slug>.md`

   Content: title, **public** URL, **locale**, one paragraph of **what went live** (paste or summary), and **PII/commercial** guard — no secrets; redact if pasting from a platform.

3. **Filename prefix:** use the **actual** publication date (same rule as normal drafts).

This folder is **gitignored** from the public GitHub `origin` like the rest of **`docs/private/`**; still commit in the **stacked private** repo when you use it.

---

## Assistant behavior (Cursor)

- On **`today-mode YYYY-MM-DD`**: after opening the dated checklist, **optionally** **`read_file`** the private hub and calendar and list **due or overdue** draft lines for **that date** and **the next calendar day** (if files exist). **Do not** invent posts; **do not** paste full URLs into **tracked** GitHub issues/PRs without redaction policy.
- On **`social-today-check`**: same skim, **short pt-BR** nudge if something is due or overdue.
- If you report a **new** manual post: offer to **update the hub** + **draft an evidence file** under **`drafts/evidence/`** (operator pastes text).

---

## Related

- **`docs/ops/today-mode/README.md`** — today-mode index
- **`docs/ops/today-mode/CARRYOVER.md`** — rolling queue
- **`docs/private/social_drafts/README.md`** (private) — layout + prefix rule
- **Skill:** **`.cursor/skills/operator-social-today-alignment/SKILL.md`**
