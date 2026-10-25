# Source note — CISA KEV and advisories

Primary links:

- [CISA Known Exploited Vulnerabilities Catalog](https://www.cisa.gov/known-exploited-vulnerabilities-catalog)
- [CISA Cybersecurity Advisories](https://www.cisa.gov/news-events/cybersecurity-advisories)

Why this source is useful:

- Prioritized view of vulnerabilities with active exploitation evidence.
- Helps separate "nice to patch" from "urgent to patch".

How we consume it:

- Use for priority decisions in dependency and runtime hardening work.
- Cross-check against Dependabot/pip-audit and release gates.

Watch-outs:

- KEV relevance depends on stack/deployment exposure.
- Avoid panic updates; keep reproducibility and regression safety.
