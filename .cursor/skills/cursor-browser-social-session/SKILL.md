# Skill: browser automation policy (public template)

## When to use

Third-party web UIs in the **Cursor embedded browser** (MCP `cursor-ide-browser`) when the task needs **UI + session**, not a public JSON API.

## Policy (generic)

1. **Try first:** `browser_tabs` → `browser_navigate` → `browser_snapshot` (and clicks) **before** claiming no access.
2. **Cold session + SSO:** if the site offers **Continue with Google** / equivalent SSO and that identity is in scope, **attempt the click** before escalating to the operator.
3. **Escalate once** after a real blocker (captcha, hard MFA, broken a11y tree, timeout) — do not ask for passwords in chat.
4. **Cleanup:** unlock if locked; close tabs opened only for this task to free RAM. Closing a tab is **not** logout — do not clear cookies unless asked.
5. **Secrets / PII:** never paste credentials, full mail bodies, or private attachment text into **tracked** files; prefer gitignored private notes when persistence is needed.

## Operator-specific runbook

Account lists, vendor names tied to personal infra, and warm-session playbooks for this workstation live under **gitignored** **`.cursor/private/skills/cursor-browser-social-session/`** (issue #1191). Rules that remain public: **`.cursor/rules/cursor-browser-social-sso-hygiene.mdc`**, **`.cursor/rules/operator-browser-warm-session.mdc`**.
