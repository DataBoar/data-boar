# Source note — OWASP projects/guidance

**Português (Brasil):** [OWASP.pt_BR.md](OWASP.pt_BR.md)

Primary links:

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [OWASP ASVS](https://owasp.org/www-project-application-security-verification-standard/)
- [OWASP Cheat Sheet Series](https://cheatsheetseries.owasp.org/)

Why this source is useful:

- Widely adopted application security baseline.
- Actionable checklists for auth, session, transport, validation, logging.

How we consume it:

- Use as a structured checklist for review and backlog triage.
- Prefer narrow, testable slices (example: one check mapped to one test or workflow).

Watch-outs:

- Do not overfit generic web guidance to non-web modules.
- Keep scope proportional to current roadmap stage.

## OWASP AI Security & Privacy Guide — OWASP AI Exchange

- Primary: [OWASP AI security overview](https://owaspai.org/docs/ai_security_overview/)
- Relevance: the Exchange **documents** privacy-related AI attacks (membership inference, model inversion, training-data leakage) and discusses mitigations such as data minimization and obfuscating training data. Data Boar can support a **preventive inventory** of PII in candidate training stores and related systems. It is **not** a membership-inference or model-inversion detector, and it is **not** “the” control for that attack class.
- How we consume it: use as a **positioning** reference when scanning training datasets or data lakes that may feed models. It does **not** replace a product threat model, an AI-system assessment, or accredited privacy engineering.
- Watch-outs: **inspiration / alignment only** — not OWASP certification, not EU AI Act conformity, not a substitute for [ADR-0025](../../adr/ADR-0025-compliance-positioning-evidence-inventory-not-legal-conclusion-engine.md) (inventory vs legal conclusion).
