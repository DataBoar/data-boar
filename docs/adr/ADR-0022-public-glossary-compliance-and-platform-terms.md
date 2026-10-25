# ADR 0022 — Public glossary — compliance laws, roles, and platform terms

- **Status:** Accepted
- **Date (UTC):** 2026-04-08
- **Authors:** Fabio Leitao
- **Deciders:** Fabio Leitao

## Context

[GLOSSARY.md](../GLOSSARY.md) originally emphasised **product** vocabulary: **finding**, **session**, **target**, **connector**, **heatmap**, **ADR**, etc. External readers also hit **acronyms and laws** scattered across [USAGE.md](../USAGE.md), [COMPLIANCE_FRAMEWORKS.md](../COMPLIANCE_FRAMEWORKS.md), [OBSERVABILITY_SRE.md](../OBSERVABILITY_SRE.md), and [SECURITY.md](../SECURITY.md) — **LGPD**, **GDPR**, **DPO**, **SRE**, **OAuth2**, **TLS**, **SBOM**, **SLI/SLO/SLA**, **ML/DL**, and others — without a single short definition page.

| Option | Pros | Cons |
|---|---|---|
| **Expand GLOSSARY.md** with one-line definitions and links to long-form docs | Discoverable from [docs/README.md](../README.md); keeps EN + pt-BR pairs ([GLOSSARY.pt_BR.md](../GLOSSARY.pt_BR.md)); avoids duplicating full legal text | Must stay short; risk of drift vs COMPLIANCE_FRAMEWORKS if not updated together |
| Rely only on inline explanation in each doc | No new file rows | Readers repeat context; translators work harder |
| New separate “compliance terms” doc | Could go deeper | Splits glossary; more links to maintain |

## Decision

1. **Treat [GLOSSARY.md](../GLOSSARY.md) as the umbrella index** for both product terms and **cross-cutting platform / compliance / transport** terms that appear in operator and integrator docs.
2. **Keep definitions to one table row** (short); point to **canonical detail** in COMPLIANCE_FRAMEWORKS, USAGE, SENSITIVITY_DETECTION, OBSERVABILITY_SRE, SECURITY, or ADRs (e.g. SBOM → [ADR 0003](ADR-0003-sbom-roadmap-cyclonedx-then-syft.md)).
3. **Maintain English + pt-BR** glossary files in lockstep when adding or changing entries (same skill as other user-facing docs).
4. **Include culture-of-delivery terms** (e.g. **Agile Manifesto**) only as minimal gloss + pointer that they are not product features — avoids bloating the table while helping readers who see maintainer-facing references.
5. **Organise the glossary by theme**, not as a single alphabetical table: sections such as product identity, session/targets, findings/overrides, laws/roles, APIs/transport, ML, etc. Within each section, sort rows **alphabetically** by the first column. Add a short **taxonomy** overview (table mapping theme → scope) at the top of [GLOSSARY.md](../GLOSSARY.md) so readers know how to browse.

## Consequences

- **Positive:** Lower barrier for DPOs, SREs, and integrators; single jump-off point linked from [docs/README.md](../README.md).
- **Negative:** More rows to review when compliance or observability docs change meaningfully.
- **Watch:** Do not paste long statutory text into the glossary; legal nuance stays in COMPLIANCE_FRAMEWORKS and sample YAML.

## References

- [GLOSSARY.md](../GLOSSARY.md) · [GLOSSARY.pt_BR.md](../GLOSSARY.pt_BR.md) — **§5** adds **ANPD**, **controller/processor**, **processor (operador)**, **legal basis**, **controls (report recommendations)**, **data subject**, tightened **DPO**/**LGPD**/**GDPR** links, plus **data-category** rows (**PII**, **sensitive personal data / special category data**, **PHI**, **cardholder data**); **§6** adds **Zero Trust**, **least privilege**, **secure by design**, **privacy by design**, **defense in depth**, **shift-left security** (posture alignment, pointers to SECURITY/NIST); **§7** adds **DoS/DDoS**, **connect/read timeouts**, **`rate_limit`**, **HTTP 413 body limit**, **`scan.max_workers`** (customer load controls; pointers to USAGE/SECURITY/DEPLOY); **§8** **LLM** (dictionary entry) plus **ML/DL**, **TF-IDF**, and **Random Forest** with cross-references; **§2** **sampling**; **§3** **regex** (vs **regex override**) and **false negative/positive**; **§9** adds **anonymization/pseudonymization**, **data minimization**, **subprocessor**, plus public links (Planalto, gdpr-info.eu, HHS HIPAA, SEC SOX, EDPB, ANPD); **§10** **ISO/IEC 27001/27005/27701**; positioning: [ADR 0025](ADR-0025-compliance-positioning-evidence-inventory-not-legal-conclusion-engine.md).
- **Later glossary rows (deploy + formats + licensing drafts):** **§6** **container** (Docker/OCI image), **CVE**, **SAST**; **§7** **JSON**, **YAML**, **CSP**, **HSTS**, **OpenAPI**, **CDN**, **WAF**, **reverse proxy** (edge vs in-app mitigations); **§11** **JWT**, **open core**, **OSS**, **subscription level** — pointers to [LICENSING_OPEN_CORE_AND_COMMERCIAL.md](../LICENSING_OPEN_CORE_AND_COMMERCIAL.md) / [LICENSING_SPEC.md](../LICENSING_SPEC.md). Taxonomy row “Security operations & assurance” was folded into **§6**/**§7** to avoid an empty section.
- [ADR 0002](ADR-0002-operator-facing-security-and-technical-docs.md) (operator-facing docs)
- [ADR 0004](ADR-0004-external-docs-no-markdown-links-to-plans.md) (external-tier IA)
- [.cursor/skills/documentation-en-pt-br/SKILL.md](../../.cursor/skills/documentation-en-pt-br/SKILL.md)
