# Terms of Use & Acceptable Use Policy — Data Boar

**Português (Brasil):** [TERMS_OF_USE.pt_BR.md](TERMS_OF_USE.pt_BR.md)

_Last updated: 2026-05-20_

## 1. Open-source licence

The Data Boar source code is available under the licence stated in the `LICENSE` file
in this repository. Your rights to use, modify, and distribute the software are governed
by that licence.

This document supplements the software licence with usage guidance specific to the
nature of this tool.

## 2. What you may do (Community edition)

With the Community (open-core) edition you may:

- Run Data Boar on systems and data **that you own or are authorised to scan**
- Use scan results in compliance reports, audits, and internal assessments
- Modify and extend the source code under the terms of the project licence
- Deploy Data Boar internally at no cost, including in a commercial organisation

## 3. What you may not do (all tiers)

Regardless of your licence tier, you may **not** use Data Boar to:

- **Scan systems or data without authorisation** from the system owner or applicable data controller
- **Conduct covert employee surveillance** — scanning personal devices or personal data of employees without their knowledge and without a valid legal basis
- **Evade legal requirements** — using Data Boar to locate and destroy personal data in response to a regulatory investigation or litigation hold
- **Re-sell** the Community edition as a competing commercial product without complying with the open-source licence
- **Misrepresent findings** — presenting Data Boar scan results as a complete legal compliance certification

## 4. Commercial use and licensing tiers

Delivering Data Boar scan results to third parties as part of a paid service (consulting,
audit, MSSP) requires at minimum a **Pro licence**. See [docs/SUBSCRIPTION_TIERS.md](docs/SUBSCRIPTION_TIERS.md),
[docs/LICENSING_SPEC.md](docs/LICENSING_SPEC.md), and [docs/LICENSING_OPEN_CORE_AND_COMMERCIAL.md](docs/LICENSING_OPEN_CORE_AND_COMMERCIAL.md).

Using Data Boar across multiple client environments requires at minimum a **Partner licence**.

## 5. Surveillance-adjacent features

Features that scan browser artefacts, legacy proprietary office formats, and other
rich-media paths listed in [docs/SUBSCRIPTION_TIERS.md](docs/SUBSCRIPTION_TIERS.md)
(for example screenshot folders or audio when enabled in your build) are restricted
to licensed tiers and require explicit operator acknowledgment at runtime.

By enabling these features you represent that:

1. You have a valid legal basis (LGPD Art. 7, GDPR Art. 6, or equivalent) for the scan
2. If scanning employee data, you have complied with applicable labour law requirements regarding employee monitoring in your jurisdiction
3. You will retain scan results only as long as legally required and will secure them appropriately

## 6. No warranty; no compliance guarantee

Data Boar is provided "as is" without warranty of any kind. Scan results are probabilistic
and may contain false positives or false negatives. They do not constitute a legal finding
or a certification of compliance with LGPD, GDPR, or any other regulation.

Always engage qualified legal counsel before making compliance decisions based on scan results.

## 7. Responsible disclosure

If you discover a security vulnerability in Data Boar, please report it via the process
described in `SECURITY.md`. Do not open a public GitHub Issue for security vulnerabilities.

## 8. Changes to these terms

We may update this document when the product or licence model changes materially.
Check the `Last updated` date and the git history of this file.

## 9. Contact

Open a [GitHub Issue](https://github.com/FabioLeitao/data-boar/issues) for
general questions. For commercial licensing enquiries, contact the maintainer via GitHub.

---

_These terms are a good-faith guide to appropriate use. They do not replace the software
licence in `LICENSE` or any signed commercial agreement._