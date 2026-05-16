# Partner / client feedback inbox — blueprint (tracked)

**Português (Brasil):** [README.pt_BR.md](README.pt_BR.md)

**This folder is versioned** as a **policy stub only**. **Do not** put raw Corporate-Entity-C PDFs, Gemini dumps, or other full review payloads in Git.

## Where drops live (operator machine)

Create **`docs/feedbacks, reviews, comments and criticism/`** at the **repo root** (same level as **`docs/`**). That path is **gitignored** — it is **not** under **`docs/private/`**.

- **Habit:** paste incoming partner or client feedback there (WRB-style drops, Corporate-Entity-C analyses, **Gemini** exports, **Claude (e.g. Sonnet) multi-persona / external review** text — anything you do not want on `origin`).
- **Distilled** conclusions and IDs belong in **tracked** plans or ops notes after you redact — never paste full confidential tables into GitHub **issues**, **PR bodies**, or public Markdown.

### GitHub issues (optional tracker)

You may **open issues** from a review batch so work is visible on **`origin`**. Keep issue bodies **short** (title + one-line pointer + optional checklist). **Posture:** those reviews are **recommendations**, **not** authoritative — same as **Gemini** rounds: triage each item as **done**, **deferred** (with a plan link or date), **won’t do** (brief reason), or **already satisfied**, then close or comment. The **agent + maintainer** decide; do not treat vendor LLM output as a merge gate by default.

## Optional mirror (stacked private Git)

If you use a **nested** repository under **`docs/private/`**, you may also keep receipts under **`docs/private/feedbacks_and_reviews/`** and commit there per **`docs/ops/PRIVATE_LOCAL_VERSIONING.md`** — still **never** push those files to the **product** GitHub remote.

## Agents (Cursor)

When the operator uses the **`feedback-inbox`** session keyword, assistants **`read_file`** / list the gitignored drop folder first. If it is **empty**, say so. If **origin** (Corporate-Entity-C vs Gemini vs **Claude external** vs other) is unclear, **ask** before attributing rows in **`docs/plans/`** or **`PLANS_TODO.md`**. If the operator **named the source** in chat, use that label.

## See also

- **[PRIVATE_OPERATOR_NOTES.md](../../PRIVATE_OPERATOR_NOTES.md)** — feedback path vs `docs/private/`.
- **`.cursor/rules/session-mode-keywords.mdc`** — **`feedback-inbox`** row.
