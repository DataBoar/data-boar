# Engineering craft inspirations — how we learn, what to adopt, what to avoid

**Português (Brasil):** [ENGINEERING_CRAFT_INSPIRATION_ANALYSIS.pt_BR.md](ENGINEERING_CRAFT_INSPIRATION_ANALYSIS.pt_BR.md)

## Purpose

Explain how this project **consumes** the [engineering craft inspirations table](inspirations/ENGINEERING_CRAFT_INSPIRATIONS.md) (YouTube channels, tool authors, educators) as **craft and narrative input** — not as requirements, endorsements of every take, or substitutes for tests and threat modeling.

The table stays **short** (names, links, one-line “why here”). This document holds **cross-cutting analysis**: themes, habits worth imitating, failure modes, and a repeatable checklist.

**Short index note in-folder:** [inspirations/ENGINEERING_CRAFT_ANALYSIS.md](inspirations/ENGINEERING_CRAFT_ANALYSIS.md).

## Sources (ongoing)

- **Canonical list:** [ENGINEERING_CRAFT_INSPIRATIONS.md](inspirations/ENGINEERING_CRAFT_INSPIRATIONS.md) — add or remove rows there; update clusters below only when the *pattern* changes.
- **Security narrative overlap:** [SECURITY_INSPIRATION_GRC_SECURITY_NOW.md](SECURITY_INSPIRATION_GRC_SECURITY_NOW.md) and [inspirations/SECURITY_NOW.md](inspirations/SECURITY_NOW.md) — **Steve Gibson** / *Security Now* is detailed there; the craft table links that row **only** for explanatory style, not duplicate GRC policy.

This is a living guide. Extend it when we repeatedly extract the same lesson from different creators.

## Is this class of source good for us?

### Strengths (why yes)

- **Operator empathy:** Many entries model how real people install, break, and recover systems — parallel to CONTRIBUTING, first-run docs, and homelab validation.
- **Explain-the-stack habits:** Clear mental models, “show the failure,” and measured benchmarks help privacy/compliance storytelling stay honest.
- **Locale and audience calibration:** pt-BR rows anchor how Brazilian operators consume specs, risk, and tutorials — reduces accidental “US-default” prose in operator-facing text.
- **Long-arc product narrative:** Shipped tools and retro/debug stories reinforce documenting trade-offs and legacy constraints.

### Limits (why not blindly)

- **Entertainment and pacing:** Fast or meme-heavy formats teach **density and hooks**, not contractual behavior; they must not replace ADRs, tests, or SECURITY.md.
- **Vendor and channel incentives:** Vendor academies and single-stack educators skew toward one ecosystem; neutral product docs still need stack-agnostic framing where required.
- **Jurisdiction and domain:** Aviation, consumer repair, or retro hobbies are **analogies** for narrative discipline — not legal, safety, or infosec authority for Data Boar.
- **Parasocial risk:** “We like this creator” must not become “we must agree with their latest take.”

## Thematic clusters (use the table by theme)

Use these clusters when mining the table; creators may appear in more than one mentally, but the **table row** remains the single link target.

| Cluster                                | Intent for Data Boar                                             | Example rows (non-exhaustive)                                                |
| -------                                | --------------------                                             | -----------------------------                                                |
| **Inclusive onboarding**               | Plain language, lower intimidation for CLI and first-run paths   | Veronica Explains, Savvy Nik, Diolinux Labs, *You Suck at Programming*       |
| **Hook vs depth**                      | README blurbs and “what bucket is this?” without false precision | Fireship (pair with slower docs)                                             |
| **Homelab and infrastructure**         | Runbooks, LAN/storage reality, operator-grade failures           | Level1Techs, UniFi Academy (vendor caveat), Gary H Tech, SafeSourceTVs       |
| **Legacy and patience**                | Odd encodings, old exports, “what we tried”                      | Michael MJD, Nostalgia Nerd, The 8-Bit Guy, Cathode Ray Dude, Usagi Electric |
| **Science and math explanation**       | Counterintuitive ideas, honest uncertainty, visuals              | Veritasium, 3Blue1Brown, Steve Mould, Stand-up Maths                         |
| **Shipping and systems depth**         | Trustworthy tooling narrative, OS-scale honesty                  | Mark Russinovich, Dave Plummer, GitHub (official channel)                    |
| **Portable doc patterns**              | Small reusable doc pieces, wiki-in-a-file thinking               | TiddlyWiki lineage rows                                                      |
| **pt-BR operator reality**             | Tone, price/performance, local security literacy                 | Diolinux Labs, Clube do Hardware, Colleague-Q Colleague-Kentel, Aviões e Músicas         |
| **Low-level and security engineering** | First principles for performance and trust boundaries            | Low Level Academy / StackSmash / LowLevelTV                                  |

## What to mimic

- **Name the failure mode** before the fix (or before the “happy path” only).
- **Show your work:** what was measured, what changed, what still broke — especially in homelab and benchmark notes.
- **Separate marketing hook from contract:** short explainers point readers to enforceable behavior (code, config, tests).
- **Safety and scope disclaimers** where physical risk, high voltage, or regulated domains appear — even when the analogy is only narrative.
- **Cross-link to repo truth:** inspiration → plan, ADR, test, or operator runbook — not floating admiration.

## What to avoid

- Treating a creator’s opinion as **implicit product policy** without an artifact in-repo.
- **Vendor capture** in supposedly neutral architecture or compliance sections.
- **False precision:** comedy, memes, or confidence editing must not stand in for detection certainty or legal claims.
- **Burying the limit:** if the scanner or model is uncertain, docs should say so — regardless of how polished an external explainer looks.

## Practical workflow (token-aware)

1. **Sample by cluster** (see table above), not by binge-watching every back catalog in one pass.
1. For each candidate habit, label **Adopt now**, **Backlog with rationale**, or **Reject (not fit)**.
1. Attach the outcome to one **repo artifact** (plan, ADR, doc section, test, workflow guard).
1. If a row goes stale or off-mission, **prune the table**; trim this file’s cluster examples to match.

## Evaluation checklist (per external habit or format)

- Does it improve **operator clarity** or **contributor onboarding**, not only entertainment value?
- Can we **verify** the behavior we care about (tests, logs, reproducible steps)?
- Does it conflict with **security-by-default** or compliance posture documented elsewhere?
- Is the **maintenance cost** acceptable (ongoing doc debt, support burden)?
- If the source is **vendor-specific**, is neutral wording preserved where the product must stay stack-agnostic?

## Current decision snapshot

- **Inspiration quality:** High variance by channel; **themes** matter more than any single personality.
- **Adoption posture:** Selective; table + this analysis are **inputs**, not mandates.
- **Immediate use:** onboarding tone, honest limits in operator docs, homelab/realism notes, cluster-based mining.

## Related docs

- [ENGINEERING_CRAFT_INSPIRATIONS.md](inspirations/ENGINEERING_CRAFT_INSPIRATIONS.md)
- [inspirations/README.md](inspirations/README.md) / [inspirations/INSPIRATIONS_HUB.md](inspirations/INSPIRATIONS_HUB.md)
- [SECURITY_INSPIRATION_GRC_SECURITY_NOW.md](SECURITY_INSPIRATION_GRC_SECURITY_NOW.md) (security narrative; partial overlap)
- [CONTRIBUTING.md](../CONTRIBUTING.md)
- [AGENTS.md](../../AGENTS.md)
