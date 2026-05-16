# Inspiration baselines (operator-maintained)

**Português (Brasil):** [README.pt_BR.md](README.pt_BR.md)

**Start here (navigation hub):** [INSPIRATIONS_HUB.md](INSPIRATIONS_HUB.md) — brief descriptions + links to every detailed inspiration note in this folder and related ops bridges.

This folder holds **two** tracks. Both use the same idea: external material is **input**, not automatic policy; product decisions still go through our context, tests, and rollout safety.

## Security / GRC

Purpose: a small, high-signal list of sources that inform **hardening and compliance-oriented** roadmap choices.

- [Security Now / GRC](SECURITY_NOW.md)
- [OWASP projects and guidance](OWASP.md)
- [CISA KEV + advisories](CISA_KEV_AND_ADVISORIES.md)
- [Supply chain and trust signals](SUPPLY_CHAIN_AND_TRUST_SIGNALS.md) ([pt-BR — follow-ups adiados](SUPPLY_CHAIN_AND_TRUST_SIGNALS.pt_BR.md))
- [Wazuh docs + NIST CSF / CIS — lab-op alignment](WAZUH_NIST_CIS_LABOP_ALIGNMENT.md) ([pt-BR](WAZUH_NIST_CIS_LABOP_ALIGNMENT.pt_BR.md))
- [Lab-op observability — official doc bookmarks](LAB_OP_OBSERVABILITY_LEARNING_LINKS.md) ([pt-BR](LAB_OP_OBSERVABILITY_LEARNING_LINKS.pt_BR.md))
- [Enterprise DB ops + GRC evidence slots](ENTERPRISE_DB_OPS_AND_GRC_EVIDENCE.md) ([pt-BR](ENTERPRISE_DB_OPS_AND_GRC_EVIDENCE.pt_BR.md))
- [Qualys Threat Research (blog / TRU)](QUALYS_THREAT_RESEARCH.md)

## Doctrine (normative manifestos)

Short, normative manifestos consolidating the **Data Boar engineering DNA**.
Each file states do / don't rules and points at the code or rule that
already enforces it.

- [The art of the fallback](THE_ART_OF_THE_FALLBACK.md) — Parser SQL → Regex → Raw strings; never silently fail.
- [Defensive scanning manifesto](DEFENSIVE_SCANNING_MANIFESTO.md) — sampling caps, timeouts, `WITH (NOLOCK)`, leading SQL comments.
- [Engineering bench discipline](ENGINEERING_BENCH_DISCIPLINE.md) — bench ergonomics, checklist culture, narrated logs.
- [Internal diagnostic aesthetics](INTERNAL_DIAGNOSTIC_AESTHETICS.md) — Sysinternals-grade `--verbose` and audit JSON.
- [Actionable governance and trust](ACTIONABLE_GOVERNANCE_AND_TRUST.md) — APG (path to the cure), self-explaining deliverable.

Driving plan: [PLAN_ENGINEERING_DOCTRINE_CONSOLIDATION.md](../../plans/PLAN_ENGINEERING_DOCTRINE_CONSOLIDATION.md).

## Engineering craft (people, products, narrative)

Purpose: named **developers, teams, or channels** whose craftsmanship, security awareness, shipped products, documentation, or public “how we thought about the problem” narrative informs **how we build and explain** Data Boar.

- [Engineering craft inspirations](ENGINEERING_CRAFT_INSPIRATIONS.md) — table of links + short notes; fill as the maintainer adds references.
- [Engineering craft — source note](ENGINEERING_CRAFT_ANALYSIS.md) — index to the table + pointer to the deep analysis.
- [Engineering craft — deep analysis](../ENGINEERING_CRAFT_INSPIRATION_ANALYSIS.md) — themes, what to mimic/avoid, checklist (parallel to [SECURITY_INSPIRATION_GRC_SECURITY_NOW.md](../SECURITY_INSPIRATION_GRC_SECURITY_NOW.md)).

How to use this folder:

1. Read the relevant note (security line or craft line).
1. Extract one candidate action or habit.
1. Decide: adopt now, backlog, or reject.
1. Link the decision to a repo artifact (plan, ADR, doc, test, workflow).

Keep each baseline intentionally short. Add rows only when a source is **repeatedly** useful.
