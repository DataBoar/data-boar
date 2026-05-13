# Plan: Operator API key–first auth UX (reduce JWT / manual Bearer toil)

**Status:** Pending
**Date:** 2026-03-29
**Authors:** Fabio Leitao
**Priority:** H2

**Horizon / urgency:** `[H3]` / `[U2]` — **sidequest · exploratory**; run in a **buffer** sprint or after a coherent main slice when operator ergonomics matter more than feature depth.

**Session cue (English token):** treat as **`sidequest`** with subtype **`exploratory`** — stop when spike outcome is recorded; resume primary track per [PLANS_TODO.md](PLANS_TODO.md).

**Synced with:** [PLANS_TODO.md](PLANS_TODO.md) · [TOKEN_AWARE_USAGE.md](TOKEN_AWARE_USAGE.md) · [SPRINTS_AND_MILESTONES.md](SPRINTS_AND_MILESTONES.md) (buffer / sidequests).

---

## Problem statement

Operators and automation often face **short-lived JWTs** or long paste strings for **Bearer** auth: **human error** (wrong header, truncated token, clock skew), **shell history** leakage, and **toil** on every refresh. **Secure-by-design** here means **prefer standard machine-to-machine patterns** (long-lived **API key** or **OAuth2 client credentials**) over hand-pasted session JWTs for routine API/dashboard client use — **not** inventing a custom token protocol.

---

## What already exists in product (no new crypto)

- **Data Boar’s own API:** When `api.require_api_key: true`, clients send **`X-API-Key`** or **`Authorization: Bearer <key>`** with a key resolved from config / `api_key_from_env` — see [optional_api_key_middleware](../api/routes.py) narrative and [SECURITY.md](../SECURITY.md).
- **REST/API scan targets:** **`token_from_env`**, **`oauth2_client`** with secrets via env — see [TECH_GUIDE.md](../TECH_GUIDE.md) / [TECH_GUIDE.pt_BR.md](../TECH_GUIDE.pt_BR.md) auth table and [TROUBLESHOOTING_CREDENTIALS_AND_AUTH.md](../TROUBLESHOOTING_CREDENTIALS_AND_AUTH.md).

This plan is about **closing the gap between capability and operator habit**: docs, examples, and optional small UX so people **default** to API key + env (or vault inject) instead of JWT copy-paste.

---

## Design direction: rotation, least privilege, off-band handoff, one-shot CLI

**Zero trust + least privilege:** Treat separately (a) **enterprise-negotiated** Bearer / IdP-issued tokens, (b) **Data Boar’s** runtime API key (`api.require_api_key`), and (c) **per-target** scan credentials. Do **not** reuse one class where another belongs. Each should have its own **lifetime**, **rotation policy**, and **blast radius**.

**Validity, expiry, rotate:** Assume **re-validation** is normal operations — who may **issue**, who may **consume**, max TTL, audit expectation, and how technicians **request rotation** without pasting long-lived secrets into Slack/email.

**Off-band focal point:** Material that grants access should flow **out-of-band** from a **focal** role (security owner, IdP admin, break-glass approver) to the **technician running Data Boar** — a **different channel** than the API/dashboard TLS path (e.g. voice callback, cleared ticket attachment, time-boxed vault grant). Same-band “here is the Bearer” in chat duplicates risk.

**One-shot CLI (OTP-*like* ergonomics, standard crypto only):** Product direction worth evaluating: technician runs a **single-use or short-TTL enrollment** via CLI — **paste once**, `stdin`, or **scan a QR** that encodes a **standard** one-time or short-lived string (transport only; e.g. URL or opaque ticket id minted server-side). After success, the **durable** secret lands in **operator-controlled** storage (env, sealed secret, vault path); the **one-shot** value is **consumed** and **invalid**. Mental model: same as **typing an OTP** or **scanning an `otpauth://` setup QR once** — **not** a custom TOTP algorithm.

**If implementing later:** Prefer existing primitives (opaque server-minted tokens, short JWT with explicit `jti` + replay suppression, or well-audited patterns) — design review before code.

---

## Spike scope (maximum one or two sessions)

| Step   | Action                                                                                                                                                                                                                                        | Done when                                                                               |
| ----   | ------                                                                                                                                                                                                                                        | ---------                                                                               |
| **S1** | **Inventory:** List every place docs or scripts imply “paste JWT” or manual Bearer for **Data Boar** or **example targets**.                                                                                                                  | Short bullet list in this file or PLANS_TODO row notes.                                 |
| **S2** | **Conventions:** Propose one operator pattern — e.g. `DATA_BOAR_API_KEY` in env, curl snippet, Compose/K8s secretRef; link [OPERATOR_SECRETS_BITWARDEN.md](../ops/OPERATOR_SECRETS_BITWARDEN.md) where relevant.                              | EN + pt-BR touch in USAGE/SECURITY **only if** gaps are real (token-aware).             |
| **S3** | **Product split (optional):** If HTML/dashboard is the pain point, cross-link **Phase 0–1** of [PLAN_DASHBOARD_REPORTS_ACCESS_CONTROL.md](PLAN_DASHBOARD_REPORTS_ACCESS_CONTROL.md) (cookie / route-class) — **no** commitment in this spike. | Explicit “out of scope” or “handoff to #86” note.                                       |
| **S4** | **Exit:** Choose **A** doc-only alignment, **B** small CLI/dashboard affordance (e.g. copy-safe setup hint), or **C** defer — update [PLANS_TODO.md](PLANS_TODO.md).                                                                          | Status row + dashboard refresh.                                                         |
| **S5** | **Policy sketch:** Capture least-privilege split + **off-band** focal → technician flow + **one-shot CLI / QR transport** idea (this section); note whether exit **B** should include enrollment UX or stay docs-only.                        | Bullet appendix in this file or PR description; no obligation to ship product in spike. |

---

## Out of scope (for this exploratory plan)

- Replacing **commercial licensing JWT** ([LICENSING_SPEC.md](../LICENSING_SPEC.md)) — different concern (entitlement vs session).
- Full **Secrets Phase B** vault ([PLAN_SECRETS_VAULT.md](PLAN_SECRETS_VAULT.md)) — Phase A env patterns suffice for spike.
- **SSO / OIDC** as first-class in-app IdP — documented elsewhere (e.g. reverse-proxy pattern in sprints doc).

---

## Dependencies & relationships

| Plan / doc                                                                            | Relationship                                                                                                                     |
| ----------                                                                            | ------------                                                                                                                     |
| [PLAN_DASHBOARD_REPORTS_ACCESS_CONTROL.md](PLAN_DASHBOARD_REPORTS_ACCESS_CONTROL.md)  | Global API key today is “clunky for pure HTML”; RBAC phases may add cookie or multi-key — **coordinate** D-WEB middleware story. |
| [PLAN_SECRETS_VAULT.md](PLAN_SECRETS_VAULT.md)                                        | Env-based keys align with Phase A; vault references future `@vault:` / Phase B.                                                  |
| [TROUBLESHOOTING_CREDENTIALS_AND_AUTH.md](../TROUBLESHOOTING_CREDENTIALS_AND_AUTH.md) | Single credential per target; Data Boar key header rules.                                                                        |

---

## Completion (when promoted from exploratory)

- [ ] S1–S5 completed (S5 is policy/note-taking); outcome **A/B/C** recorded in PLANS_TODO.
- [ ] If docs change: EN + pt-BR pairs per docs policy.
- [ ] `python scripts/plans-stats.py --write` after PLANS_TODO edits.
