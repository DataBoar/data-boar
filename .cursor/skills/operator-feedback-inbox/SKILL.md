# Operator feedback inbox (WRB-style drops)

## When to use

The operator types **`feedback-inbox`** or asks to find or interpret **partner / collaborator / client** feedback that lands outside normal **`docs/private/`** commits.

## Steps

1. Read **`docs/private.example/feedbacks-inbox/README.md`** (and **`.pt_BR.md`** if they use pt-BR) for the **drop path** contract.
1. List or **`read_file`** under **`docs/feedbacks, reviews, comments and criticism/`** (repo root, gitignored). If the folder is **empty or absent**, report that.
1. If **origin** of a file is ambiguous, **ask** before mapping content to **`docs/plans/`**, **`PLANS_TODO.md`**, or **GitHub issue/PR bodies**. Known labels include **Corporate-Entity-C**, **Gemini**, **Claude (external export / multi-persona audit)** — when the operator states the source, **use it** without rhetorical re-probing.
1. **GitHub issues** opened from a review are **optional trackers**. Keep them **short**; link back to inbox filename **in chat or private notes**, not full pastes. **Triage:** each item is **advisory** — record **done / deferred / won’t do / already covered** as the maintainer decides (same non-authoritative posture as **Gemini**).
1. Prefer **short distilled bullets** in the right tier (**tracked** plan vs **`docs/private/`** evidence) — never paste full confidential tables into public Markdown or PR bodies.

## Never

- Commit raw drops from the gitignored inbox to **`origin`**.
- Guess which review round a file belongs to when attribution affects tracked planning.

## Related

- **`.cursor/rules/operator-feedback-inbox.mdc`**
- **`docs/PRIVATE_OPERATOR_NOTES.md`**
- **`.cursor/rules/session-mode-keywords.mdc`** (`feedback-inbox` row)
