# Plan: LLM PII-leakage monitoring — generic, multi-client

**Status:** Proposed
**Date:** 2026-08-15
**Authors:** Fabio Leitao
**Priority:** TBD (operator)

**Synced with:** [PLANS_TODO.md](PLANS_TODO.md) (central to-do list)

## When implementing steps: update docs and tests; then update PLANS_TODO.md and this file.

Data Boar already scans data **at rest** (filesystem, SQL/NoSQL, SharePoint,
HubSpot, etc.). LLM assistants (Gemini, ChatGPT, Copilot, Claude, and
similar) introduce a different exposure vector: PII **in motion**, entered
into prompts and potentially surfaced in outputs, logs, or third-party
training pipelines — invisible to a data-at-rest scan.

**Origin:** raised during Client A's (port logistics operator) Google Workspace request
(#1230) — that client's specific pain is PII leakage risk via Gemini output inside their
Workspace tenant. The operator flagged that this is likely not
Gemini-specific or client-specific: other current/future clients may need
the same governance for whichever LLM their organization uses.

**Goal:** define whether/how Data Boar can extend its "data soup" governance
model to LLM usage — detecting when sensitive data is exposed via prompts,
outputs, or LLM-adjacent logs — without inventing a new detection engine
(reuse existing pattern/ML detection where the mechanism allows sampling
text).

---

## Why this, why now

- **Market:** any org using an LLM assistant (which is now most SaaS-adjacent
  companies) has the same blind spot the #1230 client case described — DPOs have no
  visibility into what PII employees paste into prompts.
- **Differentiator:** existing DLP/CASB tools focus on network egress;
  fewer focus on the specific "did this prompt/response contain PII" question
  the way Data Boar already answers it for files/DBs.
- **Risk if we don't scope it now:** solving this once, narrowly, for
  Gemini for a single client (inside #1230) risks a one-off implementation that doesn't
  generalize — same trap as building a feature for one client instead of an
  "ingredient."

---

## Open design questions (Phase 0 — before any Phase 1 decision)

1. **What exactly gets monitored?** Two very different shapes:
   - **Usage/access logs** (who used the LLM, when, from where) — read-only,
     usually available via the provider's admin/audit API (e.g. Google
     Admin SDK Reports). Cheap, but doesn't answer "was PII actually shared."
   - **Content** (the actual prompt/response text) — answers the real
     question, but availability varies wildly by provider: some expose
     conversation logs via admin API (enterprise tiers), most consumer-tier
     products don't expose content to admins at all.
   - #1230 already resolved this for the Gemini / Google Workspace client case: it's **content**,
     not just usage. Unclear if that generalizes to every provider/client, or
     if Data Boar has to degrade gracefully to usage-only where content isn't
     available.
2. **What's the technical access pattern per provider?** Likely heterogeneous:
   - Google Workspace: Admin SDK Reports (usage) vs. Vault API / Gemini
     activity export (content, if licensed) — see #1158/#1167/#1230 for the
     Google-specific design tension already in flight.
   - OpenAI/Anthropic/Microsoft Copilot enterprise tiers: each has its own
     admin/audit surface, none identical to Google's.
   - No single "LLM connector" abstraction is obvious yet — may need a
     provider-specific connector per LLM vendor, similar to how SQL dialects
     differ but share a base pattern.
3. **Is this data-at-rest-adjacent (scan exported logs) or a new category
   (live monitoring)?** Existing connectors sample data that already sits
   somewhere. LLM content, if available at all, is usually via an export/log
   API — closer to existing patterns than a live proxy/DLP approach. Worth
   confirming this framing before assuming new infrastructure is needed.

---

## Suggested next step

Phase 0 (research) before Phase 1 (decide): pick **one** provider — most
likely Google Gemini, since #1230 already has a live client need — and
answer the three questions above concretely for that one case first. Treat
this plan as the generic umbrella; let #1230's implementation be the first
data point, then generalize once the actual Gemini API surface is known
firsthand rather than assumed.

## Relation to other issues

- #1230 — the concrete, client-confirmed first case (Gemini / Google Workspace, Client A)
- #1158 / #1167 — competing technical approaches for Google Workspace
  broadly (Vault API vs. direct Drive+Reports API) — whichever wins informs
  what's realistically available for the Gemini content question too
- #1582 — tracking issue for this generalized research question

---

## Other LLM providers to consider (once Phase 0 answers exist for Gemini)

| Provider | Admin/audit surface (to verify) | Notes |
|---|---|---|
| OpenAI (ChatGPT Enterprise) | Compliance API (audit logs) | Content access unclear — verify during Phase 0 |
| Microsoft Copilot | Purview / M365 compliance center | May overlap with existing SharePoint/M365 connector work |
| Anthropic (Claude for Work) | Admin API (usage) | Content access unclear |

**Not a commitment to build any of these** — table exists so the roadmap
stays honest about what's known vs. assumed, same convention as
`PLAN_SAP_CONNECTOR.md`'s "Other data sources" table.
