# Operator session capture — turning chat into durable notes

**Português (Brasil):** [OPERATOR_SESSION_CAPTURE_GUIDE.pt_BR.md](OPERATOR_SESSION_CAPTURE_GUIDE.pt_BR.md)

**Purpose:** When you and the assistant align on **strategy**, **policy**, **tooling**, or **next steps** in chat, **high-value** threads deserve a **small durable artifact** so you can **reopen**, **teach future-you**, or **spawn plans**—without flooding tracked docs or leaking sensitive facts.

**Not a substitute for:** [PLANS_TODO.md](../plans/PLANS_TODO.md), release notes, or ADRs. This is **operator memory hygiene**.

---

## 1. What to capture

| Worth capturing                                                           | Usually skip                                                  |
| ---------------                                                           | ------------                                                  |
| Decisions (“Slack before Signal, then both”)                              | Full chat transcripts                                         |
| New **policy** (where CLI dumps live, commercial vs operator economics)   | Passwords, tokens, raw `last`/`w` output in **tracked** files |
| Pointers (“GitHub Mobile = channel A; Cursor mobile = companion caveats”) | One-off typos, duplicate of existing plan rows                |
| Ethical / career framing you may reread                                   | Anything that belongs **only** in counsel or HR               |
| “We agreed folder X for Y”                                                | Long prose that duplicates `AGENTS.md`                        |

---

## 2. Where to put it (sensitivity)

| Sensitivity                                   | Location                                          | Examples                                                                                 |
| -----------                                   | --------                                          | --------                                                                                 |
| **Public / team**                             | Tracked `docs/` (EN + pt-BR when operator-facing) | This guide, `OPERATOR_NOTIFICATION_CHANNELS`, `PRIVATE_OPERATOR_NOTES` policy rows       |
| **Product + roadmap**                         | `docs/plans/`, `PLANS_TODO`                       | New `PLAN_*.md` when the idea becomes a **scoped** deliverable                           |
| **Personal, strategic, family, OPEX numbers** | **`docs/private/`** only                          | Academic ethics note, electricity tables, client-specific proposal drafts                |
| **LAN, habits, IPs, session dumps**           | **`docs/private/homelab/`** (e.g. `reports/`)     | `uptime`, `last`, `lastlog` — see [PRIVATE_OPERATOR_NOTES.md](PRIVATE_OPERATOR_NOTES.md) |

**Rule of thumb:** If losing the note would **hurt your career or compliance** but must **not** appear on GitHub → **`docs/private/`** with a **dated** filename or section.

---

## 3. Suggested private layout (optional index)

Maintain a **light index** so future search is fast:

- **`docs/private/author_info/RECENT_OPERATOR_SYNC_INDEX.pt_BR.md`** (or similar)—**bullet index** with dates and **links to other private files** (relative paths only).
- One **topic = a few bullets**, not a novel.

Copy-me pointer (tracked): **`docs/private.example/author_info/README.md`**.

---

## 4. Agent / assistant behaviour

When the operator asks to **“save this for later”**, **“document what we agreed”**, or **“capture the session”**:

1. **Classify** each item: tracked policy vs plan vs **private** only.
1. **Update** the smallest set of files (prefer **one** new private note + **optional** one tracked cross-link).
1. **Never** commit LAN IPs, hostnames, family names tied to institutions, or commercial numbers—**private** or redacted.
1. If the idea is a **feature slice**, suggest a **`PLANS_TODO`** row or plan file update **separately** (do not merge unrelated topics into one giant private dump).

Cursor: **`.cursor/rules/operator-session-capture.mdc`** and **`.cursor/skills/operator-session-capture/SKILL.md`**.

---

## 5. Related docs

- [PRIVATE_LOCAL_VERSIONING.md](PRIVATE_LOCAL_VERSIONING.md) — optional **nested Git** for `docs/private/` (local history, no GitHub).
- [PRIVATE_OPERATOR_NOTES.md](PRIVATE_OPERATOR_NOTES.md) — private tree table, CLI habit artifacts.
- [OPERATOR_NOTIFICATION_CHANNELS.md](OPERATOR_NOTIFICATION_CHANNELS.md) — Slack + Signal phased pattern.
- [TOKEN_AWARE_USAGE.md](../plans/TOKEN_AWARE_USAGE.md) — session scope vs plan work.
- [AGENTS.md](../../AGENTS.md) — confidentiality and automation scripts.
