# ADR 0048 — Operator-facing taxonomy and naming contract preservation

- **Status:** Accepted
- **Date (UTC):** 2026-05-12
- **Authors:** Fabio Leitao
- **Deciders:** Fabio Leitao

## Context

Data Boar exposes several layers of taxonomy that function as operator-facing contracts:
config YAML keys (appear in every customer deployment file), `norm_tag` values (appear
verbatim in customer Excel compliance reports and may feed downstream parsers), report
sheet and column names (Excel output structure customers may depend on), CLI flag names
(appear in customer runbooks and CI scripts), domain vocabulary (Data Sniffing, Deep
Boring, Safe-Hold, Audit Trail — see `persona-rigor.mdc`), and internal code artifact
taxonomy (Python module docstrings, function names, PowerShell CBH headers:
`.NAME`, `.SYNOPSIS`, `.DESCRIPTION`).

Drift between any of these layers and actual behavior reduces operator trust, silently
breaks downstream automation, and increases the cost of onboarding, support, and audit.
Renaming a config key or a `norm_tag` string mid-deployment is a **breaking change** —
even when the behavior is identical — because customers' deployment files, Excel macros,
or compliance dashboards hold the old value.

## Decision

1. **Config YAML keys are breaking-change surface.** Renaming or removing a key requires
   a migration note in `CHANGELOG.md`, a deprecation cycle or explicit version bump, and
   a search for references in operator docs (`USAGE.md`, `DEPLOY.md`, sample YAMLs).
2. **`norm_tag` strings are customer-report contracts.** Any change to a `norm_tag` value
   must be treated as a breaking change: update `CHANGELOG.md`, search all fixtures and
   tests, and note impact on existing customer reports.
3. **Report sheet and column names follow the same rule.** Names that appear in Excel
   output or API response fields are operator-facing contracts; changing them is a breaking
   change regardless of internal refactor intent.
4. **CLI flag names are operator-facing contracts.** Renaming or removing a flag requires a
   deprecation note and update to `USAGE.md` and `docs/OPERATOR_HELP_AUDIT.md`. The
   `operator-help-sync` skill and rule govern the sync procedure.
5. **Domain vocabulary is frozen at the canonical four.** Data Sniffing, Deep Boring,
   Safe-Hold, and Audit Trail must not be renamed, aliased, or replaced by
   vendor-neutral synonyms in any operator- or customer-facing surface — including
   marketing copy, compliance docs, and report output. New product terms follow the same
   naming-by-decision protocol: add to `GLOSSARY.md` and `GLOSSARY.pt_BR.md` before use.
6. **Code artifact taxonomy must reflect behavior.** Python module docstrings, function
   names, and PowerShell CBH headers (`.NAME`, `.SYNOPSIS`, `.DESCRIPTION`) must describe
   current behavior. Refactors that change behavior update all affected taxonomy elements
   in the same commit. Reviewers (human or agent) verify taxonomy consistency as part of
   PR review. Suggest adding missing CBH or docstrings when touching a script that lacks
   them.

## Rationale

The product runs against production customer databases and produces compliance evidence.
A silent rename of a `norm_tag` value or a config key can reach a DPO dashboard before
anyone notices — at which point the customer's evidence trail is corrupted and re-scanning
may be required. Treating operator-facing identifiers as contracts (not implementation
details) prevents this class of failure at the source.

The frozen domain vocabulary (`persona-rigor.mdc`) exists for the same reason:
"Deep Boring" in a customer report cross-referenced against an external summary loses
meaning if the internal label silently changed to "Deep Scan" in a refactor.

## Consequences

- **Positive:** Customer deployments and Excel reports survive minor version upgrades
  without manual intervention.
- **Positive:** Onboarding contributors and AI agents have a clear list of what "breaking
  change" means in this repo beyond code behavior.
- **Negative:** Refactors carry a mandatory taxonomy-update obligation, which slightly
  increases PR scope.
- **Ongoing:** `CHANGELOG.md` entries for any rename of config keys, `norm_tag` values,
  report fields, or CLI flags — even when behavior is unchanged.
- **Ongoing:** Code reviewers (human or agent) check: does the PR rename any item on the
  operator-facing taxonomy surface? If yes, is there a `CHANGELOG.md` entry?

## Alternatives Considered

1. **Free-form naming with "best effort" docs update** (rejected): creates invisible
   breaking changes; discovered by customers in production.
2. **Auto-generated taxonomy from code** (rejected): hides intent behind generated text;
   does not scale to multifunction modules and does not cover `norm_tag` or config key
   contracts.
3. **Rely on existing `persona-rigor.mdc` rule alone** (rejected): the rule protects domain
   vocabulary but does not create a durable record covering config keys, `norm_tag`,
   report fields, and CLI flags — all of which are breaking-change surface.

## Related Decisions

- [ADR 0022 — Public glossary — compliance laws, roles, and platform terms](ADR-0022-public-glossary-compliance-and-platform-terms.md)
- [ADR 0034 — Outbound HTTP User-Agent](ADR-0034-outbound-http-user-agent-data-boar-prospector.md)
- [ADR 0046 — Operator intent and blameless collaboration posture](ADR-0046-operator-intent-and-blameless-collaboration.md)
- [ADR 0047 — RCA-first defect investigation and fix discipline](ADR-0047-rca-first-defect-investigation-and-fix-discipline.md)

## References

- [`persona-rigor.mdc`](../../.cursor/rules/persona-rigor.mdc) — frozen domain vocabulary contract
- [`operator-help-sync.mdc`](../../.cursor/rules/operator-help-sync.mdc) — CLI flag and help-text sync procedure
- [`docs/GLOSSARY.md`](../GLOSSARY.md) — canonical product terminology
- [`docs/OPERATOR_HELP_AUDIT.md`](../OPERATOR_HELP_AUDIT.md) — drift guard for CLI surface
