# Inspirations hub (start here)

**Português (Brasil):** [INSPIRATIONS_HUB.pt_BR.md](INSPIRATIONS_HUB.pt_BR.md)

Single **navigation page** for maintainer-chosen **external inputs** that shape Data Boar roadmap, docs tone, and hardening — without becoming automatic policy.

**Folder:** [`docs/ops/inspirations/`](README.md) (this directory).

---

## Security / GRC (hardening, compliance tone, threat framing)

| Document                                                                                | What it is                                                                                                                                                                                                              |
| --------                                                                                | ----------                                                                                                                                                                                                              |
| [SECURITY_NOW.md](SECURITY_NOW.md)                                                      | Source note: **Security Now** (GRC) — long-running operational security perspective.                                                                                                                                    |
| [OWASP.md](OWASP.md)                                                                    | OWASP projects and guidance — application security patterns.                                                                                                                                                            |
| [CISA_KEV_AND_ADVISORIES.md](CISA_KEV_AND_ADVISORIES.md)                                | CISA KEV and advisories — patch/exposure prioritization inputs.                                                                                                                                                         |
| [SUPPLY_CHAIN_AND_TRUST_SIGNALS.md](SUPPLY_CHAIN_AND_TRUST_SIGNALS.md) · [pt-BR (deferred)](SUPPLY_CHAIN_AND_TRUST_SIGNALS.pt_BR.md) | Supply chain + trust framing: registry/marketplace **fail-open** class, **shadow AI** vs governance reports, **Mar 2026 Trivy** CI/advisory pattern — links to in-repo mitigations ([ADR 0005](../../adr/ADR-0005-ci-github-actions-supply-chain-pins.md), lockfile, audit, SBOM roadmap). Short **pt-BR** page mirrors **deferred** posture block only. |
| [WAZUH_NIST_CIS_LABOP_ALIGNMENT.md](WAZUH_NIST_CIS_LABOP_ALIGNMENT.md) · [pt-BR](WAZUH_NIST_CIS_LABOP_ALIGNMENT.pt_BR.md) | **Wazuh** official doc index (components, install, use cases) for **LAB-OP** learning; **NIST CSF** + **CIS Controls** mapping to honest Data Boar vs homelab **Detect/Recover** scope — not certification. |
| [LAB_OP_OBSERVABILITY_LEARNING_LINKS.md](LAB_OP_OBSERVABILITY_LEARNING_LINKS.md) · [pt-BR](LAB_OP_OBSERVABILITY_LEARNING_LINKS.pt_BR.md) | **Mental note:** official doc bookmarks for **Grafana, Prometheus, Loki, Graylog, OpenSearch, Elasticsearch, OTel, Jaeger, Tempo, SigNoz, Netdata**; **Grafana Cloud** free tier + **Dynatrace**-style SaaS caution — aligns with [PLAN_LAB_OP_OBSERVABILITY_STACK.md](../../plans/PLAN_LAB_OP_OBSERVABILITY_STACK.md). |
| [ENTERPRISE_DB_OPS_AND_GRC_EVIDENCE.md](ENTERPRISE_DB_OPS_AND_GRC_EVIDENCE.md) · [pt-BR](ENTERPRISE_DB_OPS_AND_GRC_EVIDENCE.pt_BR.md) | **Oracle-DBA-style** operational themes (backup/restore proof, patching, segregation) + generic **GRC/cyber template** grids — what Data Boar **exports** can attach to vs out-of-scope (DBA/SOC runbooks). |
| [QUALYS_THREAT_RESEARCH.md](QUALYS_THREAT_RESEARCH.md)                                  | Qualys TRU / vulnerabilities blog — long-form coordinated disclosure (e.g. AppArmor “CrackArmor”), kernel and infrastructure risk framing.                                                                              |
| [SECURITY_INSPIRATION_GRC_SECURITY_NOW.md](../SECURITY_INSPIRATION_GRC_SECURITY_NOW.md) | Operator-facing bridge: how we **consume** Security Now–style insight in-repo.                                                                                                                                          |

**People (detailed under Security/GRC):** **Steve Gibson** is the primary public voice behind **Security Now**; full treatment stays in the notes above. A **short pointer** also appears in [ENGINEERING_CRAFT_INSPIRATIONS.md](ENGINEERING_CRAFT_INSPIRATIONS.md) for *explanatory narrative* (not duplicate policy).

---

## Doctrine (normative manifestos)

Short, normative manifestos that consolidate our **engineering DNA**. Each
file states **do / don't** rules, cites mentor seeds, and points at the code
or rule that already enforces the doctrine.

| Document                                                                                | Seeds                                                          | Scope                                                                                                                                  |
| --------                                                                                | -----                                                          | -----                                                                                                                                  |
| [THE_ART_OF_THE_FALLBACK.md](THE_ART_OF_THE_FALLBACK.md)                                | Usagi Electric · The 8-Bit Guy                                 | Fallback hierarchy: Parser SQL → Regex → Raw strings; never silently fail.                                                             |
| [DEFENSIVE_SCANNING_MANIFESTO.md](DEFENSIVE_SCANNING_MANIFESTO.md)                      | NASA SEL · Cloudflare · Steve Gibson                           | Sampling caps, statement timeouts, `WITH (NOLOCK)` posture, leading SQL comments, "guest in the customer DB" rule.                     |
| [ENGINEERING_BENCH_DISCIPLINE.md](ENGINEERING_BENCH_DISCIPLINE.md)                      | Adam Savage · Julia Evans (b0rk) · Aviões e Músicas            | Bench ergonomics, checklist culture, narrated logs.                                                                                    |
| [INTERNAL_DIAGNOSTIC_AESTHETICS.md](INTERNAL_DIAGNOSTIC_AESTHETICS.md)                  | Mark Russinovich (Sysinternals)                                | What `--verbose`, `completão -Privileged`, and audit JSON should *feel* like — a low-level diagnostic class.                           |
| [ACTIONABLE_GOVERNANCE_AND_TRUST.md](ACTIONABLE_GOVERNANCE_AND_TRUST.md)                | Tailscale narrative · Charity Majors (Honeycomb) · Cloudflare  | The executive report delivers the *path to the cure* (APG); the system explains itself.                                                |

Driving plan: [PLAN_ENGINEERING_DOCTRINE_CONSOLIDATION.md](../../plans/PLAN_ENGINEERING_DOCTRINE_CONSOLIDATION.md).

---

## Engineering craft (people, products, narrative)

| Document                                                                                  | What it is                                                                                                                                                                    |
| --------                                                                                  | ----------                                                                                                                                                                    |
| [ENGINEERING_CRAFT_INSPIRATIONS.md](ENGINEERING_CRAFT_INSPIRATIONS.md)                    | Table of **developers, channels, or products** (sysinternals-style tools, YouTube educators, TiddlyWiki lineage, etc.) with **why it matters** for Data Boar.                 |
| [ENGINEERING_CRAFT_ANALYSIS.md](ENGINEERING_CRAFT_ANALYSIS.md)                            | Short **source note**: links the table to the deep analysis (same role as [SECURITY_NOW.md](SECURITY_NOW.md) for Security Now).                                               |
| [ENGINEERING_CRAFT_INSPIRATION_ANALYSIS.md](../ENGINEERING_CRAFT_INSPIRATION_ANALYSIS.md) | **Deep analysis**: thematic clusters, mimic/avoid, workflow, checklist — parallel to [SECURITY_INSPIRATION_GRC_SECURITY_NOW.md](../SECURITY_INSPIRATION_GRC_SECURITY_NOW.md). |

Use this when designing features, operator docs, or “how we explain trade-offs” — still **not** a substitute for threat modeling or tests.

---

## How to extend

1. Add a row to the relevant table file (security note vs engineering table).
1. Keep entries **short**; link out for depth (engineering craft: update [ENGINEERING_CRAFT_INSPIRATION_ANALYSIS.md](../ENGINEERING_CRAFT_INSPIRATION_ANALYSIS.md) when **cross-cutting themes** change, not for every new row).
1. If someone spans both (e.g. security + narrative), put **detail** in Security/GRC notes and a **pointer** in engineering craft if useful.

---

## Related (outside this folder)

- [Operator notification channels](../OPERATOR_NOTIFICATION_CHANNELS.md) — how CI/alerts reach humans (separate from inspiration content).
