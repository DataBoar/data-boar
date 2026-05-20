# Privacy Policy — Data Boar

**Português (Brasil):** [PRIVACY_POLICY.pt_BR.md](PRIVACY_POLICY.pt_BR.md)

_Last updated: 2026-05-20_

## What Data Boar is

Data Boar is an open-source sensitive-data discovery and LGPD/GDPR compliance scanner.
It runs **entirely on your own infrastructure**. There is no cloud service, no phone-home,
no telemetry, and no account required to use the Community edition.

## What this Privacy Policy covers

This policy describes:

1. What information this **GitHub repository and project** collect (if any).
2. What information the **Data Boar tool itself** collects when you run it.
3. Your rights regarding any data we hold.

## 1. The GitHub repository

This repository is hosted on [GitHub](https://github.com). By visiting it, GitHub's own
privacy policy applies to your interaction with their platform (cookies, analytics, etc.).
We do not control GitHub's data collection.

When you open a GitHub Issue, submit a Pull Request, or post a comment, your GitHub username
and the content you submit become visible to project maintainers and the public as part of the
open-source collaboration record.

We do not maintain any separate user database, newsletter list, or analytics platform for
this repository.

## 2. The Data Boar tool (what runs on your machine)

Policy reviewed against the **1.7.4-rc** product line on the public repository (local scan,
optional dashboard, tier-gated connectors). If you run a different build, compare
[docs/SUBSCRIPTION_TIERS.md](docs/SUBSCRIPTION_TIERS.md) and release notes.

Data Boar scans **your** databases, filesystems, and documents for personal data.
It does **not**:

- Send scan results, file contents, or metadata to any external server
- Contact the Data Boar project maintainers during or after a scan
- Collect usage statistics or telemetry
- Require an internet connection to run (Community edition)
- Create user accounts or store credentials beyond what you explicitly configure

Scan results are written **locally** to the output path you specify.
Your data does not leave your machine unless you explicitly export or share it.

### Licensed tiers (Pro, Partner, Enterprise)

If you use a signed licence token (JWT), the token is validated **locally**
using the embedded public key. No call is made to a licence server.
The token itself contains only: tier name, expiry date, and a cryptographic signature.
It contains no personal data about you.

### Optional dashboard authentication (when you enable it)

If you deploy the web dashboard with authentication enabled, credentials and session
metadata stay on infrastructure you control. WebAuthn and RBAC are optional operator
configuration paths documented in the technical guide; they are not required for
Community Edition CLI scans.

### Maturity assessment (local questionnaire)

The maturity assessment workflow stores answers in a local SQLite database on your
machine. It does not transmit responses to Data Boar maintainers unless you export
or share them yourself.

## 3. What we do collect (minimal)

| What | Where | Why |
|---|---|---|
| GitHub Issues / PR content | GitHub (public) | Bug reports and contributions |
| Email if you contact us directly | Maintainer email only | Support, partner enquiries |

We do not sell, broker, or share this information with third parties.

## 4. Data Boar and LGPD / GDPR

Data Boar is a tool **to help you comply** with LGPD, GDPR, and similar regulations.
It does not make compliance decisions on your behalf. Scan findings are inputs
to your own assessment process; they do not constitute legal advice.

If you use Data Boar to process data on behalf of others (as a consultant or integrator),
you are the data controller/processor for that activity.
Consult your legal counsel regarding your obligations under applicable law.

## 5. Surveillance-adjacent features (Pro and Enterprise)

Some features in licensed tiers (for example browser artefacts, legacy proprietary office
formats, and other rich-media paths in [docs/SUBSCRIPTION_TIERS.md](docs/SUBSCRIPTION_TIERS.md))
can detect personal data in artefacts that may belong to individuals other than the operator.

You must have a **legal basis** under LGPD Art. 7 (or GDPR Art. 6) before scanning data
that belongs to third parties. Data Boar's licence agreement (EULA) requires you to represent
that you hold such legal basis as a condition of use.

## 6. Children's data

Data Boar is not directed at or intended for use by children under 18.
We do not knowingly collect information from children.

## 7. Changes to this policy

We may update this policy when the product changes materially (e.g. if a SaaS edition
is introduced). We will update the `Last updated` date above and note the change
in the repository changelog.

## 8. Contact

For privacy-related questions about this project:

- Open a [GitHub Issue](https://github.com/FabioLeitao/data-boar/issues) (preferred for general questions)
- For sensitive matters, contact the maintainer directly via the email on their GitHub profile

---

_Data Boar is an open-source project. This Privacy Policy is provided in good faith
as a transparency statement. It is not a legal contract._