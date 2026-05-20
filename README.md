# Data Boar

**Data Boar** — enterprise data discovery and risk governance: compliance-aware mapping of personal and sensitive data across your data soup (intelligence engine, not a single-jurisdiction “audit app”).

![Data Boar mascot](api/static/mascot/data_boar_mascote_color.svg)

**LGPD — real-world witness report (ISP field visit, Brazil):** [English](docs/LGPD_WITNESS_REPORT_NIO_FIELD_VISIT_2026.md) · [Português (Brasil)](docs/LGPD_WITNESS_REPORT_NIO_FIELD_VISIT_2026.pt_BR.md)

**Português (Brasil):** [README.pt_BR.md](README.pt_BR.md) · [docs/USAGE.pt_BR.md](docs/USAGE.pt_BR.md) · → [Audience guide](docs/AUDIENCE_GUIDE.md) — who should read which docs · **5 min (pt-BR):** [QUICKSTART.md](QUICKSTART.md)

---

## For decision-makers and compliance leads

Your organization needs to know **where** personal and sensitive data lives—to comply with **LGPD**, **GDPR**, **CCPA**, **GLBA**, and other major frameworks, and to avoid costly surprises. **Data Boar** is a **multi-dialect**, **SRE-friendly** engine for **data discovery** and **actionable compliance** (risk assessment and governance-oriented outputs — Excel, heatmaps, executive Markdown, evidence manifests). It helps you build **compliance awareness** and surface **possible violations** without out-of-control cost: one configurable engine that scans your data and reports what it finds, so IT, cybersecurity, compliance, and DPOs can take informed action.

**What we surface:** Beyond obvious PII (CPF, CNPJ – including the new alphanumeric format, email, phone), we use **AI** (ML and optional DL) to detect **sensitive categories** (health, religion, political opinion, biometric, genetic—LGPD Art. 5 II, GDPR Art. 9), **field combinations that can re-identify individuals in context** (LGPD Art. 5, GDPR Recital 26), and **possible minor data** (LGPD Art. 14, GDPR Art. 8). We recognise regional document names and flag ambiguous identifiers for manual confirmation, and reveal exposure across **legacy columns**, **exports**, **dashboards**, and **multiple sources** in one view—so you see gaps that manual checks or rule-only tools often miss. Findings carry **norm_tag** and the same risk vocabulary as the Excel output; when jargon piles up (**quasi-identifier**, categories, cross-border nuance), the [Glossary](docs/GLOSSARY.md#glossary-stakeholder-jargon) aligns engineering, compliance, and procurement on one lexicon.

**Children's and minors' data — first-class, not a footnote:** Possible minor columns and values get **dedicated detector logic**, elevated report treatment (including optional deeper DB resampling and **cross-reference** with identifiers or health-like fields in the same table or path), and **compliance-sample YAML** vocabulary for US child-privacy contexts—always as **inventory and triage signals**, never as legal age verification. That is a deliberate **linguistic category** in the product: the same “boar” that digs through messy enterprise data is wired to **surface child-related exposure early** for DPO and security review. Technical limits and config keys: [MINOR_DETECTION.md](docs/MINOR_DETECTION.md) ([pt-BR](docs/MINOR_DETECTION.pt_BR.md)); concern-first map: [MAP.md](docs/MAP.md) ([pt-BR](docs/MAP.pt_BR.md)).

The real risk—**shadow IT** and beyond—often hides in parallel spreadsheets, forgotten folders, legacy databases, lack of standardization, tangled flows, poorly documented applications, exceptions, and excessive data collection. Data Boar keeps sniffing through your data soup to uncover those hidden ingredients—including renamed or cloaked files and weaker transport or storage—so compliance and legal teams see what’s really there, not just how it’s presented. **Rich media today:** optional **metadata** scans, **image OCR**, and **subtitle** sidecars help surface ingredients that plain full-text search often misses. **On the horizon (phased, often opt-in):** stronger signals for **embedded trackers**, **steganography**, and **document-layer tricks** (microtext, Unicode cloaking, nested embedded objects)—without promising exhaustive detection until each slice ships.

**Hungry for your data soup:** Like a **boar**, we dig into many sources and don't stop at the surface. Whatever the ingredients—**files**, **SQL**, **NoSQL**, **APIs**, **Power BI**, **Dataverse**, **SharePoint**, **SMB/NFS**, and more—we're built to ingest and digest it. We **do not store or exfiltrate** PII, only **metadata** (where found, pattern type, sensitivity), so you get visibility for remediation without moving data.

**Why it holds up:** One engine, **config-driven** (regex, ML/DL terms, norm tags, recommendation overrides)—no code changes to align with different frameworks. **Excel reports**, **heatmaps**, and **trends** across sessions; **schedulable** scans via API. Baseline patterns cover **LGPD**, **GDPR**, **CCPA**, **GLBA**, and **sample configs** extend to **UK GDPR**, **EU GDPR**, **Benelux**, **PIPEDA**, **POPIA**, **APPI**, **PCI-DSS**, US healthcare vocabulary, and more—each with **framework guidance** under **compliance-samples** (navigate from the table below). **Regulatory positioning**, sector-specific inventory limits (including US health), and optional **professional services** are summarised in [Compliance and legal](docs/COMPLIANCE_AND_LEGAL.md).

Multilingual and legacy encodings are supported; **configurable timeouts** and **security hardening** (validation, headers, audit) are in place. **Compressed files:** scan inside archives (zip, tar, gz, 7z with optional extra) via **config**, **CLI**, or the **dashboard**—full flags and I/O notes are in **USAGE** (table below). Optional **content-type** detection helps find renamed or cloaked files (e.g. a PDF saved with a **misleading non-text extension** such as `.mp3`—magic bytes still reveal the real format); early **crypto/transport** visibility (e.g. TLS vs plaintext) is collected for database and API targets.

**Sniffing with judgment:** Plain-text reads use a **configurable character budget** so the engine sees real structure—not a useless nib—before it decides; **entertainment-shaped** content routes **noisy ML hints** into a **review band** instead of crowding the report with spurious “certain” alerts, while **hard pattern hits** (IDs, payment data, strong PII) stay decisive for triage.

**Roadmap:** We continue to broaden **discovery** (richer files and media, **cloud** and **enterprise** connectors), improve **alerts** when scans finish, and keep **security and dependency** practices strong. **Operator CLI (in progress):** **config validation** before scans, **session diff** for regression evidence, and **DSAR-oriented export** helpers that default to **metadata-first** outputs—maintainers track slices in the repository’s planning tree (see **docs/README.md** *Internal and reference*). **Language** coverage in the UI and docs, and **regional** compliance samples, grow **incrementally** with demand—not every market at once. **Already shipped (opt-in):** **jurisdiction hints**—DPO-oriented notes on the Excel **Report info** sheet from **metadata-only** signals (**not** legal conclusions), so multinational teams can **prioritise counsel review**. Turn them on in config, CLI, dashboard, or API; details: [USAGE](docs/USAGE.md). **For boards and audits:** outputs stay **briefing-ready**—leadership gets **clear priorities and concrete evidence** on data visibility and compliance posture **without** treating an engineering roadmap as the main slide deck. **Framework lists**, **audit-oriented norms** (e.g. ISO 27701, SOC 2), minors’ privacy **sample profiles**, and SBOM/API positioning: [COMPLIANCE_FRAMEWORKS.md](docs/COMPLIANCE_FRAMEWORKS.md). **Shipped vs phased:** [docs/releases/](docs/releases/).

**We invite you to get in touch** to see how Data Boar can support your compliance journey.

**Typical scenarios:** Preparing for an audit or regulator request; mapping data before a migration or DLP rollout; raising compliance awareness without a full war room; supporting data privacy consultants as the technical evidence layer in LGPD adequacy engagements.

> **Current release:** **1.7.3**. **Docker Hub:** **`fabioleitao/data_boar:1.7.3`** or **`latest`**. Summary: [CHANGELOG.md](CHANGELOG.md). Full notes: [docs/releases/1.7.3.md](docs/releases/1.7.3.md) and the [GitHub Releases page](https://github.com/FabioLeitao/data-boar/releases). Prior golden: **`v1.7.2-safe`** / **`1.7.2+safe`** — [docs/releases/1.7.2-safe.md](docs/releases/1.7.2-safe.md).
> **Working pre-release on `main`:** **`1.7.4-rc`** — draft GitHub **pre-release** notes: [docs/releases/1.7.4-rc.md](docs/releases/1.7.4-rc.md) (does **not** move Docker **`latest`**; stable remains **1.7.3** until **1.7.4** final).
> **Documentation note:** This README and `docs/USAGE.md` are the canonical English references. When features or options change, update **both** languages to keep them in sync.

**Product blog (narrative updates, shorter posts):** [databoar.wordpress.com](https://databoar.wordpress.com) — canonical technical documentation remains in this repository (`docs/`).

---

## The Architect's Vault

Investors, integration partners, and senior technical reviewers often skim the README and then ask: **where is the decision trail?** This section is the deliberate **front door** to narrative, positioning, and architecture records that sit beside the code—so the repository reads as a **governed product**, not “just another script.” Execution backlogs and PMO tables stay one hop away via [docs/README.md](docs/README.md) (*Internal and reference*); per [ADR 0004](docs/adr/ADR-0004-external-docs-no-markdown-links-to-plans.md), this README avoids one-click Markdown links into the **plans** subtree under **docs** from this pitch surface.

| If you need… | Start here |
| ------------- | ---------- |
| **Value proposition** (boards, legal, compliance, procurement — concise brief) | [DECISION_MAKER_VALUE_BRIEF.md](docs/DECISION_MAKER_VALUE_BRIEF.md) · [pt-BR](docs/DECISION_MAKER_VALUE_BRIEF.pt_BR.md) |
| **Architecture Decision Records** (context, decision, consequences — numbered series) | [docs/adr/README.md](docs/adr/README.md) · [pt-BR index](docs/adr/README.pt_BR.md) |
| **Narrative and architecture history** (curated product story and stack evolution — placeholder until expanded) | [NARRATIVE_AND_ARCHITECTURE_HISTORY.md](docs/NARRATIVE_AND_ARCHITECTURE_HISTORY.md) · [pt-BR](docs/NARRATIVE_AND_ARCHITECTURE_HISTORY.pt_BR.md) |
| **Governance of the auditor** (what the app can prove today about scans, exports, and operator evidence) | [ADR 0037](docs/adr/ADR-0037-data-boar-self-audit-log-governance.md) · [SRE framing](docs/OBSERVABILITY_SRE.md) ([pt-BR](docs/OBSERVABILITY_SRE.pt_BR.md)) |
| **Concern-first navigation** (minors, jurisdiction hints, CISO-style paths) | [MAP.md](docs/MAP.md) · [pt-BR](docs/MAP.pt_BR.md) |
| **Child / minor data** (thresholds, cross-reference, samples — dedicated operator guide) | [MINOR_DETECTION.md](docs/MINOR_DETECTION.md) · [pt-BR](docs/MINOR_DETECTION.pt_BR.md) |
| **Full documentation index** (all topics; entry to internal reference in one place) | [docs/README.md](docs/README.md) · [pt-BR](docs/README.pt_BR.md) |
| **Why evidence-first** (public philosophy — no personal history) | [THE_WHY.md](docs/philosophy/THE_WHY.md) · [pt-BR](docs/philosophy/THE_WHY.pt_BR.md) |

---

## Compliance methodology

Data Boar is positioned as **technical inventory and triage**: it finds **where** categories of personal and sensitive data may live, assigns **technical** severity and norm-oriented hints, and leaves **lawful basis, purpose, and retention** choices with **DPO / counsel**. For **coursework (e.g. LGPD adequacy indices)**, we publish a concise **verification-module map** and a **ROPA-style column prioritisation** (what to automate first vs human-owned)—so the README is not only a feature list but a **bridge to compliance method**. Full detail: [COMPLIANCE_METHODOLOGY.md](docs/COMPLIANCE_METHODOLOGY.md) · [pt-BR](docs/COMPLIANCE_METHODOLOGY.pt_BR.md).

---

## Technical overview

Data Boar runs as a **one-shot CLI** audit or as a **REST API** (default port 8088) with a web dashboard. You configure **targets** (databases, filesystems, APIs, shares, Power BI, Dataverse) and **sensitivity detection** (regex + ML, optional DL) in a single **YAML or JSON** config file. It writes findings and session metadata to a local **SQLite** database and produces **Excel reports** and a **heatmap PNG** per session.

| If you need…                                                      | See                                                                                                                                                                                                                                          |
| ----------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Open core vs **Pro / Enterprise** subscription scope (draft; pricing TBD) | [LICENSING_OPEN_CORE_AND_COMMERCIAL.md](docs/LICENSING_OPEN_CORE_AND_COMMERCIAL.md) · [pt-BR](docs/LICENSING_OPEN_CORE_AND_COMMERCIAL.pt_BR.md) · [LICENSING_SPEC.md](docs/LICENSING_SPEC.md) (token technicalities, EN) |
| Compliance frameworks, samples, legal summary (DPOs, procurement) | [COMPLIANCE_FRAMEWORKS.md](docs/COMPLIANCE_FRAMEWORKS.md) · [COMPLIANCE_AND_LEGAL.md](docs/COMPLIANCE_AND_LEGAL.md) · [compliance-samples/](docs/compliance-samples/) ([frameworks index](docs/COMPLIANCE_FRAMEWORKS.md#compliance-samples)) |
| Compliance methodology (verification modules, ROPA-style automation priorities) | [COMPLIANCE_METHODOLOGY.md](docs/COMPLIANCE_METHODOLOGY.md) · [pt-BR](docs/COMPLIANCE_METHODOLOGY.pt_BR.md) |
| Reports and compliance outputs (XLSX, heatmap, audit JSON, maturity export; PDF roadmap) | [REPORTS_AND_COMPLIANCE_OUTPUTS.md](docs/REPORTS_AND_COMPLIANCE_OUTPUTS.md) · [pt-BR](docs/REPORTS_AND_COMPLIANCE_OUTPUTS.pt_BR.md) |
| Product direction and release cadence                             | [docs/releases/](docs/releases/) · [GitHub Releases](https://github.com/FabioLeitao/data-boar/releases)                                                                                                                                      |
| Install, run, CLI/API reference, connectors, deploy               | [Technical guide (EN)](docs/TECH_GUIDE.md) · [Guia técnico (pt-BR)](docs/TECH_GUIDE.pt_BR.md)                                                                                                                                                |
| Configuration schema, credentials, examples                       | [USAGE.md](docs/USAGE.md) · [USAGE.pt_BR.md](docs/USAGE.pt_BR.md)                                                                                                                                                                            |
| Deploy (Docker, Compose, Kubernetes)                              | [deploy/DEPLOY.md](docs/deploy/DEPLOY.md) · [deploy/DEPLOY.pt_BR.md](docs/deploy/DEPLOY.pt_BR.md)                                                                                                                                            |
| Sensitivity detection (ML/DL terms)                               | [SENSITIVITY_DETECTION.md](docs/SENSITIVITY_DETECTION.md) · [SENSITIVITY_DETECTION.pt_BR.md](docs/SENSITIVITY_DETECTION.pt_BR.md)                                                                                                            |
| Minor / child-related data (thresholds, optional full scan, cross-ref, samples) | [MINOR_DETECTION.md](docs/MINOR_DETECTION.md) · [MINOR_DETECTION.pt_BR.md](docs/MINOR_DETECTION.pt_BR.md)                                                                                                                                   |
| Testing, security, contributing                                   | [docs/TESTING.md](docs/TESTING.md) · [SECURITY.md](SECURITY.md) · [CONTRIBUTING.md](CONTRIBUTING.md)                                                                                                                                         |
| **`pip` from PyPI                                                 | **`pip install data-boar`** when published; until then **git clone** + **`uv sync`** — see [CONTRIBUTING.md — Repository and install identity](CONTRIBUTING.md#repository-and-install-identity-data-boar).                                     |

**Quick start (from repo root):** On **Linux (native, not Docker)**, install system libraries **before** `uv sync`—see [Technical guide — Requirements and environment preparation](docs/TECH_GUIDE.md#requirements-and-environment-preparation) (example `apt` line includes `libpq-dev`, `unixodbc-dev`, and related headers; add `default-libmysqlclient-dev` if building **mysqlclient**). Then `uv sync` → prepare `config.yaml` (see `deploy/config.example.yaml` and [USAGE](docs/USAGE.md)) → `uv run python main.py --config config.yaml --validate-config` to pre-flight targets (no scan) → `uv run python main.py --config config.yaml` for one-shot, or `uv run python main.py --config config.yaml --web --allow-insecure-http` for plaintext API/dashboard (default bind `127.0.0.1`, e.g. [http://127.0.0.1:8088/](http://127.0.0.1:8088/); for TLS use `--https-cert-file` / `--https-key-file`; use `--host 0.0.0.0` only with network controls). Full flags: `uv run python main.py --help`. **Do not commit** root `config.yaml` (`.gitignore`); it may contain LAN paths and secrets—see [CONTRIBUTING.md](CONTRIBUTING.md#public-repo-hygiene-lan-credentials).

**Full documentation index** (browse all topics and languages): [docs/README.md](docs/README.md) · [docs/README.pt_BR.md](docs/README.pt_BR.md).

**Glossary** (terms and domain language): [docs/GLOSSARY.md](docs/GLOSSARY.md) · [docs/GLOSSARY.pt_BR.md](docs/GLOSSARY.pt_BR.md).

**Legal:** [TERMS_OF_USE.md](TERMS_OF_USE.md) ([pt-BR](TERMS_OF_USE.pt_BR.md)) · [PRIVACY_POLICY.md](PRIVACY_POLICY.md) ([pt-BR](PRIVACY_POLICY.pt_BR.md)).

**License and copyright:** [LICENSE](LICENSE) ([pt-BR](LICENSE.pt_BR.md)) · [NOTICE](NOTICE) ([pt-BR](NOTICE.pt_BR.md)) · [docs/COPYRIGHT_AND_TRADEMARK.md](docs/COPYRIGHT_AND_TRADEMARK.md) ([pt-BR](docs/COPYRIGHT_AND_TRADEMARK.pt_BR.md)).

**Maintainer:** [Fabio Leitao on GitHub](https://github.com/FabioLeitao) — Docker Hub namespace `fabioleitao`. The **product blog** link is above; other personal professional social links are not embedded in this README — see the GitHub profile (policy: `**tests/test_pii_guard.py`**, `**docs/ops/COMMIT_AND_PR.md**`). Set the GitHub profile **Website** field to `https://databoar.wordpress.com` if you want a one-click entry point to the blog.