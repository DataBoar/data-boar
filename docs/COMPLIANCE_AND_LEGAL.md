# Compliance and legal — summary for legal and compliance leaders

**Português (Brasil):** [COMPLIANCE_AND_LEGAL.pt_BR.md](COMPLIANCE_AND_LEGAL.pt_BR.md)

**Primary audience:** **Legal**, **compliance leadership**, and **DPOs** assessing fit, risk, and evidence—not day-to-day IT configuration. For **YAML, API limits, encodings, and timeouts**, see [COMPLIANCE_TECHNICAL_REFERENCE.md](COMPLIANCE_TECHNICAL_REFERENCE.md); for **full config and commands**, see [USAGE.md](USAGE.md). For **verification modules** and **ROPA-style automation priorities** (method bridge for coursework and audits), see [COMPLIANCE_METHODOLOGY.md](COMPLIANCE_METHODOLOGY.md).

This page states **what Data Boar reveals**, **what it does not do**, **which regulatory framings** you can align with, **what artifacts** support audits, and how **professional services** can help map your **data soup** before the product **ingests and digests** it.

---

## What we surface (and under which provisions)

- **Personal and sensitive data:** Detection of common PII (e.g. CPF, email, phone) and **special categories** in the sense of **LGPD Art. 5 II** and **GDPR Art. 9** (health, religion, political opinion, biometric, genetic, and related).
- **Quasi-identifiers and re-identification risk:** Combinations that can contribute to identifying individuals, consistent with **LGPD Art. 5** and **GDPR Recital 26**.
- **Possible minor-related data:** Indicators aligned with **LGPD Art. 14** and **GDPR Art. 8** (human review may still be required).
- **Regional and ambiguous identifiers:** Region-specific document labels and ambiguous fields flagged for **manual confirmation** where automation cannot assert certainty.
- **Multi-source visibility:** One coherent view across the **data soup** your organisation configures—databases, files, APIs, business-intelligence and collaboration systems, and other **connector** types described at a high level in [COMPLIANCE_FRAMEWORKS.md](COMPLIANCE_FRAMEWORKS.md) and [TECH_GUIDE.md](TECH_GUIDE.md)—without claiming completeness of every legacy system until targets are in scope.
- **Filesystem and rich-media triage:** The engine can **sample enough context** from text-like files to apply judgment—reducing alert fatigue where content looks like **entertainment or boilerplate** while **strong pattern matches** remain prominent for remediation. For file targets, **optional** rich-media handling includes **metadata** (e.g. EXIF, ID3, container tags), **optional OCR** on images, and **subtitle** sidecar text where configured—within sampling limits and optional dependencies (see [USAGE.md](USAGE.md) and [COMPLIANCE_TECHNICAL_REFERENCE.md](COMPLIANCE_TECHNICAL_REFERENCE.md)). **Steganography**, full-frame media analytics, **embedded tracker / web-bug** heuristics (including social/ad network patterns discussed in security education media), and systematic detection of **document-layer concealment** (e.g. microscopic or low-contrast text, hidden structure, Unicode cloaking, deeply nested embedded objects) are **not** represented as exhaustive today; they are phased as **future opt-in** capabilities—see [TECH_GUIDE.md](TECH_GUIDE.md) and [COMPLIANCE_TECHNICAL_REFERENCE.md](COMPLIANCE_TECHNICAL_REFERENCE.md) for what ships today—so reporting stays proportionate, limits sensitive-data copying, and avoids unbounded CPU/I/O.
- **Optional jurisdiction hints (DPO/counsel triage):** When enabled, the Excel **Report info** sheet can include **heuristic** notes when **finding metadata** (e.g. column/path/norm tags) suggests **possible** relevance to certain regimes (e.g. U.S. state consumer privacy framings, Japan APPI)—**not** a determination that a law applies, **not** a substitute for jurisdictional analysis, and **not** based on full cell dumps stored in SQLite. Operators opt in via config, CLI, API, or dashboard; see [USAGE.md](USAGE.md) and [ADR 0026](adr/ADR-0026-optional-jurisdiction-hints-dpo-facing-heuristic-metadata-only.md).

---

## What we do not do

- **We do not store or exfiltrate PII content** for reporting: the tool retains **metadata** (location, pattern type, sensitivity level, framework tags) so teams gain **visibility for maturity and remediation** without copying personal data into a second datastore. Excel outputs describe **findings and recommendations**, not raw personal fields.

---

## Regulatory alignment: built-in and configuration-led

- **Built into reports and detection language today:** **LGPD**, **GDPR**, **CCPA**, **HIPAA**, **GLBA** (norm references and recommendation text).
- **Additional jurisdictions and internal policies:** Many further frameworks (e.g. UK GDPR, PIPEDA, POPIA, APPI, PCI-DSS, and regional profiles) can be reflected through **configuration profiles**—adjusting pattern sets, labels, and report wording—**without forking the product**. What “small change” means in practice (files, merge steps) is documented for implementation teams in [COMPLIANCE_FRAMEWORKS.md](COMPLIANCE_FRAMEWORKS.md). **Roadmap** items continue to extend coverage over time.
- **Languages (brief):** **Data** can already carry many **scripts** in findings and reports (**Unicode**); **operator-facing** **dashboard** and **documentation** localizations beyond **English** and **Brazilian Portuguese** are **phased** on a **demand-led** cadence, together with **regional compliance samples** where needed—a **non-technical** list of **direction** (not a release promise), plus **executive-readable** roadmap framing for boards and audits, sits in the **Roadmap** paragraph of the repository [README.md](../README.md).

**U.S. — children’s and minors’ privacy (technical mapping only):** Optional YAML samples support **technical** and **operational** inventory work (e.g. DPO review, audit preparation, or scoping under counsel)—including framings sometimes associated with **federal COPPA (FTC Rule)**, **California AB 2273**, and **Colorado CPA** rules affecting consumers under 18. This is **not legal advice**, **not** age verification or parental-consent proof, and **not** a determination that any law applies. Use [COMPLIANCE_FRAMEWORKS.md](COMPLIANCE_FRAMEWORKS.md) and [compliance-samples/](compliance-samples/) for file names and merge steps.

**U.S. — HIPAA, HITECH, and protected health information (technical inventory only):** Built-in **HIPAA** norm tags and recommendation text support **discovery and mapping** of health-related and identifier patterns in configured sources—the same **metadata-only** reporting model as elsewhere. The **HITECH Act** strengthened HIPAA enforcement and breach-notification expectations; Data Boar **does not** determine whether a **breach** occurred, count individuals for notification, substitute for a **risk assessment** under the Security Rule, or draft **HHS OCR** (Office for Civil Rights) inquiry responses. It **does** help teams **locate** possible **PHI/ePHI** exposure for **prioritisation, remediation, and repeatable scan artefacts** that may support **governance and counsel-led** programmes. Align labels and wording via [COMPLIANCE_FRAMEWORKS.md](COMPLIANCE_FRAMEWORKS.md), [compliance-samples/](compliance-samples/), **regex and recommendation overrides**, and optional **professional services** above.

**H.R. 7898 (P.L. 116-321) and “safe harbor” for recognized security practices:** This U.S. statute **amended the HITECH Act** so **HHS** must **take into account** whether a **covered entity** or **business associate** has implemented **recognized security practices** (per statute: e.g. **NIST** and **Cybersecurity Act of 2015** §405(d), including **HICP**, and other federally recognized programmes) for **at least 12 months** when making certain determinations on **investigations**, **audits**, and **penalties**—often described as a **mitigating** “HIPAA safe harbor,” **not** immunity from enforcement. Data Boar **does not** assess **Security Rule** controls, certify **recognized security practices**, or establish **safe-harbor** eligibility; it **does** support **repeatable inventory evidence** (where **PHI/ePHI** may appear) that organisations may combine with **documented** security programmes under **counsel** and **security leadership**.

---

## Risk management (ISO 31000 — framing only)

**ISO 31000** concerns **organizational** risk management—not a software feature list. Data Boar **does not** perform your enterprise risk assessment or substitute for DPO or counsel. It improves **visibility** over personal and sensitive data so you can **prioritize** technical remediation and produce **evidence**; **which** risks to treat, accept, or transfer remains **your** process. We do **not** reproduce the standard on this page. For the same positioning in implementation-oriented language (including how this relates to **SBOM** as supply-chain / incident-response practice), see [ISO 31000 (framing)](COMPLIANCE_FRAMEWORKS.md#iso-31000-framing) under [COMPLIANCE_FRAMEWORKS.md](COMPLIANCE_FRAMEWORKS.md).

When your organization uses **ISO 31000** as its **risk-management framework**, **data inventory and scan reports** fit the **risk-treatment cycle**: they show **where** personal and sensitive data sit, support **prioritisation** of controls and remediation, and yield **repeatable artefacts** for monitoring and review. That is often useful for **DPOs and buyers** aligning technical visibility with **their** process—without the product setting risk appetite or approving treatment choices.

---

## ISO/IEC, ABNT NBR, and IoCs (positioning for DPOs and security leads)

**ISO/IEC management systems (and ABNT NBR in Brazil):** Organisations that pursue or maintain certifications often need **documented** visibility over **where** **personal data** and **special-category** information are processed. International standards are published as **ISO/IEC**; in **Brazil** the same technical content is adopted as **ABNT NBR ISO/IEC …** (titles and purchase paths: [GLOSSARY.md](GLOSSARY.md) § *ISO/IEC management-system standards*, table). Data Boar **does not** certify, audit, or replace an accredited assessment; it supplies **technical inventory evidence**—**metadata-only findings** and **repeatable scans**—that teams can use alongside **asset** and **processing** records.

- **ISO/IEC 27001** (**ISMS**): helps show **which** configured targets may hold information that feeds your **scope** and **risk treatment**—locations and categories, **not** a full control matrix.
- **ISO/IEC 27701** (**PIMS**): privacy extension aligned with declared regulations (e.g. **LGPD**, **GDPR**); product-facing detail in [Auditable and management standards (supporting role)](COMPLIANCE_FRAMEWORKS.md#auditable-and-management-standards-supporting-role) under [COMPLIANCE_FRAMEWORKS.md](COMPLIANCE_FRAMEWORKS.md).
- **ISO/IEC 27005** (information security **risk** guidance): discovery and mapping **inform** treatment decisions about **data at rest** in configured sources; they do **not** replace your methodology or risk register.

**Indicators of Compromise (IoCs):** In **security operations** and **incident response**, **IoCs** are observables used to detect or hunt threats—e.g. file hashes, malicious domains or IP addresses, YARA-style signatures—usually applied to **logs**, **endpoints**, and **network telemetry**. Data Boar is **not** a SIEM, EDR, or threat-intelligence platform: it does **not** ingest firewall flows or correlate **network IoCs** across the estate. It **can** complement **governance and IR readiness** by locating **stored data** where **credentials, tokens, or other security artifacts** may appear (see [Extended sensitive categories](#extended-sensitive-categories-configuration-and-services)) and by supporting **repeatable inventory** after an event—**metadata-only** for personal data, **not** malware analysis or forensic imaging. **Do not confuse** optional **embedded tracker / marketing-pixel** heuristics in exports (privacy **governance** signals) with **IoCs**—see *tracking references (embedded)* in [GLOSSARY.md](GLOSSARY.md).

---

## Evidence and outputs (for audits and governance)

**Stakeholder posture (PoC and committees):** **Executive Markdown** (`POC_SUMMARY_*.md`) and the companion **`scan_manifest_*.yaml`** are **GRC-adjacent** artefacts: they summarise **session status**, **sensitivity roll-up**, **how reads were bounded** (sampling, timeouts, dialect posture where relevant), and **remediation-oriented priorities** (including a **per-pattern action inventory**) while keeping the Markdown body **free of raw personal data**. They support **risk and compliance** conversations and **DPO/CISO** briefing packs; they are **not** a full enterprise GRC suite, a **regulatory certificate**, or a substitute for **counsel-led** attestations. Operators may regenerate the Markdown from **local SQLite only** using **`data-boar-report`** (no new live connector reads). Operational detail: [USAGE.md](USAGE.md) section 5; artefact map: [REPORTS_AND_COMPLIANCE_OUTPUTS.md](REPORTS_AND_COMPLIANCE_OUTPUTS.md).

- **Excel reports** per scan **session**: findings by source, field/path, pattern type, sensitivity, and framework-oriented recommendation text (legal basis, risk, suggested action, priority where configured).
- **Heatmaps** and **trend views** across sessions to show **evolution**, not only a point-in-time snapshot.
- **Repeatable runs** (including automation via API) so monitoring can match your **operating model**; technical detail of scheduling and limits: [COMPLIANCE_TECHNICAL_REFERENCE.md](COMPLIANCE_TECHNICAL_REFERENCE.md).
- **Optional operator signals (webhooks):** When `notifications` is enabled, the app can POST a short scan-completion summary (e.g. Slack, Teams, generic URL / Signal bridge, or legacy Telegram fields), including **multiple operator channels** or an optional **tenant copy** when configured — **default off**; this is operational convenience and **does not replace** Excel outputs or constitute legal evidence by itself. Maintainer channel policy: [OPERATOR_NOTIFICATION_CHANNELS.md](ops/OPERATOR_NOTIFICATION_CHANNELS.md). See [USAGE.md — Operator notifications](USAGE.md#51-operator-notifications-optional).
- **Build identity and runtime posture (operators):** Reports record **application version** in “Report info”; a planned enhancement will expose **release vs development** builds and optional **integrity** signals for enterprises (no change to legal scope until implemented). For **operational** deployment checks (not legal evidence by itself), the API **`GET /status`** includes a **`runtime_trust`** snapshot summarising whether the running configuration/environment matches expectations (e.g. unexpected local overrides).

---

## Professional services: mapping the data soup

Organisations rarely have a single, tidy inventory of every **ingredient** in their **data soup**—shadow copies, legacy exports, BI models, and ad hoc shares are common. **Data Boar** is built to **ingest and digest** what you point it at; **discovering and prioritising** those sources, **tuning** norm tags and recommendation language, and **bridging** legal expectations with technical scope is often a **joint** exercise.

**Contracted services** (consulting and fine-tuning) are available to help: scoping targets, aligning configuration to your **regulatory mix**, and shortening time-to-trust—without replacing your **DPO** or **counsel**. For licensing and commercial boundaries, see [LICENSING_OPEN_CORE_AND_COMMERCIAL.md](LICENSING_OPEN_CORE_AND_COMMERCIAL.md). **Get in touch** via GitHub or [contact@databoar.com.br](mailto:contact@databoar.com.br) for professional services enquiries—no obligation.

---

## Extended sensitive categories (configuration and services)

Beyond the **built-in** framings (e.g. LGPD, GDPR, HIPAA, PCI-oriented card data), organisations sometimes need **discovery and mapping** for:

- **Health and clinical-adjacent data** (longitudinal records, form types, diagnosis coding—beyond a single HIPAA label on the report);
- **Intellectual property**–related indicators (names of columns or content that suggest marks, filings, or proprietary assets—**not** a determination of legal ownership);
- **Security artifacts** in stored data (credentials, tokens, key material—**distinct from** the product’s **log redaction** helpers, which only protect operational logs);
- **Onboarding and financial-crime–adjacent data (PEP, KYC, CDD, EDD):** **Where** **customer**, **beneficial-owner**, or **case-file** **personal data** may appear across **legacy systems**, **exports**, and **collaboration** stores—including **columns or documents** that may contain **criminal-record**, **background-check**, or **good-conduct certificate** results (when they relate to an **identifiable** person: **personal data**; legal classification **GDPR** Art. **10** and **LGPD** context-specific rules **with counsel**—not the same closed list as **LGPD** Art. **5 II** for every use case)—**not** **sanctions** or **PEP list matching**, **not** **identity verification**, and **not** **AML transaction monitoring** (those remain specialist **KYC/AML** platforms).

**PEP / KYC / CDD / EDD positioning:** Live **KYC**, **CDD**, **EDD**, and **PEP** programmes typically combine **list screening**, **document checks**, and **monitoring** through **dedicated vendors**; Data Boar **does not** match individuals against **OFAC**, **UN**, **EU**, or commercial **PEP** databases or **determine** PEP status. It **can** help **find possible PII** and **over-retained onboarding artefacts** in your **data soup** so **privacy** and **operational risk** teams **prioritise remediation** and **evidence hygiene**—using **regex**, **ML/DL terms**, **recommendation overrides**, **[compliance-samples/](compliance-samples/)**, and optional **consulting** to align **policy wording** and **locale**. **No** **AML** certification; **metadata-only** findings.

**How this is delivered:** the same **engine** already supports **regex overrides**, **ML/DL training terms**, and **recommendation text** overrides (see [SENSITIVITY_DETECTION.md](SENSITIVITY_DETECTION.md) and [COMPLIANCE_FRAMEWORKS.md](COMPLIANCE_FRAMEWORKS.md)). Tuning for **noise**, **locale**, and **sector lexicon** often benefits from **consulting** so targets and pattern sets match your **data soup** and risk appetite. The product **does not** certify legal categories by acronym; it produces **metadata-only findings** for **governance and remediation**.

**Internal roadmap:** optional sample profiles and deeper positioning may be tracked in the repository’s **plans** tree (maintainers: see **docs/README** — *Internal and reference*). **Positioning decision (architecture):** [ADR 0025 — Compliance positioning: evidence and inventory, not a legal-conclusion engine](adr/ADR-0025-compliance-positioning-evidence-inventory-not-legal-conclusion-engine.md).

---

## Flexible positioning: joint delivery without claiming to eliminate legal risk

The product is **designed to adapt**: **configuration profiles**, **regex and recommendation overrides**, **[compliance-samples/](compliance-samples/)**, and **professional services** can tune discovery and report wording to your **regulatory mix** and **data soup**—without forking the core engine.

**Support role (how we help):** Data Boar **surfaces technical indicators** (pattern hits, sensitivity, framework-oriented tags, locations) so **legal**, **DPO**, **compliance analysts**, and **consulting** can **prioritise review**. It does **not** substitute for **legal conclusions** such as “this is a violation” or “notification is required”; those depend on **human judgment** about **facts**, **purpose**, **legal basis**, and **organisational process**. In documentation and commercial conversations, prefer **possible exposure**, **indicators for specialist review**, and **evidence for governance**—not **determinations** of **unlawfulness**.

**Value together:** Organisations gain **repeatable inventory artefacts**, **metadata-only** reporting, and **remediation-oriented** recommendations; **counsel** and **specialists** apply **law** and **policy**; **consulting** bridges **scope** and **configuration**. That **joint** delivery model is intentional—see [ADR 0025](adr/ADR-0025-compliance-positioning-evidence-inventory-not-legal-conclusion-engine.md).

**Where this is recorded:** This page, [COMPLIANCE_FRAMEWORKS.md](COMPLIANCE_FRAMEWORKS.md), and **ADR 0025**. Maintainer orientation and sector backlog: internal plan **`PLAN_COMPLIANCE_EVIDENCE_MAPPING.md`** (see [docs/README.md](README.md) — *Internal and reference* — for navigation; no buyer-facing deep link into `docs/plans/` per [ADR 0004](adr/ADR-0004-external-docs-no-markdown-links-to-plans.md)). There is **no** separate **QA journal** document for compliance positioning in this repository; optional **operator-only** nuance may still live under **gitignored** `docs/private/` per [PRIVATE_OPERATOR_NOTES.md](PRIVATE_OPERATOR_NOTES.md).

---

## Where to go next

| Need                                                | Document                                                                                                                  |
| ----                                                | --------                                                                                                                  |
| **Legal / compliance summary (this page)**          | You are here                                                                                                              |
| **IT: encodings, API limits, timeouts, automation** | [COMPLIANCE_TECHNICAL_REFERENCE.md](COMPLIANCE_TECHNICAL_REFERENCE.md) ([pt-BR](COMPLIANCE_TECHNICAL_REFERENCE.pt_BR.md)) |
| **Framework list and sample profiles**              | [COMPLIANCE_FRAMEWORKS.md](COMPLIANCE_FRAMEWORKS.md) · [COMPLIANCE_FRAMEWORKS.pt_BR.md](COMPLIANCE_FRAMEWORKS.pt_BR.md)   |
| **Config schema, credentials, CLI/API**             | [USAGE.md](USAGE.md) · [USAGE.pt_BR.md](USAGE.pt_BR.md)                                                                   |
| **Security policy**                                 | [SECURITY.md](SECURITY.md) · [SECURITY.pt_BR.md](SECURITY.pt_BR.md)                                                       |
| **Install, connectors, deploy**                     | [TECH_GUIDE.md](TECH_GUIDE.md) · [TECH_GUIDE.pt_BR.md](TECH_GUIDE.pt_BR.md)                                               |
| **Glossary**                                        | [GLOSSARY.md](GLOSSARY.md) · [GLOSSARY.pt_BR.md](GLOSSARY.pt_BR.md)                                                       |
| **Full documentation index**                        | [README.md](README.md) · [README.pt_BR.md](README.pt_BR.md)                                                               |
