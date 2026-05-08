# ADR 0002: Operator-facing security and technical documentation

**Status:** Accepted
**Date:** 2026-03-25
**Authors:** Fabio Leitao

---

## Context

Contributors and **operators** (people who deploy, harden, and run Data Boar) need a small set of **canonical** documents. Scattering “why we did X” only in issues or chat causes repeated questions and risky refactors (e.g. weakening TLS, widening bind addresses, or skipping dependency audit).

## Decision

1. Treat **[SECURITY.md](../../SECURITY.md)** (root) and **[docs/SECURITY.md](../SECURITY.md)** as the **security** entry points: supported Python versions, reporting vulnerabilities, dependency hygiene, and technician-oriented hardening pointers.
1. Treat **[docs/TECH_GUIDE.md](../TECH_GUIDE.md)** as the **technical** entry point: install, run modes (CLI/API/web), connectors, config, and operational flags (including TLS and bind behaviour).
1. When a change affects **how the product is run or secured**, update **SECURITY** and/or **TECH_GUIDE** (and **pt-BR** pairs) in the same PR whenever the behaviour is user-visible; link from release notes when the change is significant.
1. **ADRs** under **`docs/adr/`** record **why** for durable decisions that are easy to misread from code alone; link **SECURITY** / **TECH_GUIDE** from an ADR when the decision directly affects operators (see also [ADR 0001](0001-markdown-fix-script-md029-and-semantic-step-lists.md) for doc tooling).

## Consequences

- **Positive:** One place to send auditors, homelab operators, and enterprise IT; less duplicate explanation in random Markdown.
- **Negative:** Slightly more discipline per PR when behaviour changes; pt-BR must stay in sync per [docs/README.md](../README.md) policy.

## References

- [SECURITY.md](../../SECURITY.md) · [docs/SECURITY.md](../SECURITY.md)
- [docs/TECH_GUIDE.md](../TECH_GUIDE.md) · [docs/TECH_GUIDE.pt_BR.md](../TECH_GUIDE.pt_BR.md)
- [CONTRIBUTING.md](../../CONTRIBUTING.md) — docs and secrets hygiene
