# Operator social editorial + today-mode alignment

## When to use

- **`today-mode YYYY-MM-DD`**, **`carryover-sweep`**, **`eod-sync`**, or **`social-today-check`** in chat.
- The operator asks to **defer** a social post, **carry over** to another date, or record an **ad-hoc manual** post (blog, Data Boar, any network).

## Steps

1. Read **`docs/ops/today-mode/SOCIAL_PUBLISH_AND_TODAY_MODE.md`** (workflow EN; **`.pt_BR.md`** for pt-BR).
1. **`read_file`** when present: **`docs/private/social_drafts/editorial/SOCIAL_HUB.md`**, and any **`EDITORIAL_MASTER_CALENDAR_*.pt_BR.md`** in the same folder.
1. **Planned posts:** list inventory rows where **Alvo editorial** matches **today** or **tomorrow** (or the asked date) and **Estado** is not terminal — **short** bullet list, pt-BR if the operator writes in pt-BR.
1. **Defer:** guide **SOCIAL_HUB** update + **rename** draft prefix + calendar note; optional **CARRYOVER.md** only for meaningful cross-day promises.
1. **Ad-hoc publish:** offer **new/updated hub row** + optional **`docs/private/social_drafts/drafts/evidence/YYYY-MM-DD_evidence_<network>_<slug>.md`** (operator pastes body); **never** put secrets or client pricing in tracked files.

## Never

- Claim **full automation** — reminders are **manual ritual + assistant nudge**.
- Paste **unredacted** personal URLs into **public** issues/PRs if policy says otherwise.

## Related

- **`.cursor/rules/operator-social-today-mode.mdc`**
- **`docs/private/social_drafts/README.md`** (private) — filename prefix rules
- **`scripts/operator-day-ritual.ps1`** — Morning prints hub/calendar paths
