# Plan: Compliance evidence mapping – regulations to app features and reports

**Status:** Deferred
**Date:** 2026-03-18
**Authors:** Fabio Leitao
**Priority:** H0
**Depends on:** ADR-0025, ADR-0037

**Synced with:** `long-term-product-and-academic-roadmap`, [COMPLIANCE_FRAMEWORKS.md](../COMPLIANCE_FRAMEWORKS.md), [PLAN_LATO_SENSU_THESIS.md](PLAN_LATO_SENSU_THESIS.md)

This plan keeps a **structured mapping** between regulations/standards (LGPD, GDPR, FELCA, ISO/IEC 27701/27001/27002/27005, SOC 2, etc.) and **concrete app features and reports**. It is for internal and academic use—**not** for the public README roadmap.

---

## 1. Scope and structure

**Goal:** Decide which norms to include and how to represent the mapping.

### To-dos (Scope and structure)

| #   | To-do                                                                                                                                                          | Status    |
| -   | -----                                                                                                                                                          | ------    |
| 1.1 | List the primary norms to track in this mapping (LGPD, GDPR, FELCA, ISO/IEC 27701, ISO/IEC 27001/27002/27005, SOC 2; sector norms like HIPAA/GLBA; **backlog** of BR sector regulators and programme types in section 8). | ⬜ Pending |
| 1.2 | Choose a simple representation: e.g. one table per norm (control/requirement → app feature/report/plan), plus short explanatory notes.                         | ⬜ Pending |

---

## 2. LGPD and GDPR mapping

**Goal:** Link LGPD/GDPR obligations to features/reports in a way you can reuse in product docs and academic work.

### 2.1 LGPD – example slice

| LGPD reference / tema                      | App feature / report                                                                   | Notes                                                                     |
| ----------------------------------------   | --------------------------------------------------------------                         | -----                                                                     |
| Art. 5, I (dados pessoais)                 | Core detector (regex + ML/DL), norm tags `LGPD Art. 5`                                 | Detection and labelling of personal/sensitive data in “data soup”.        |
| Art. 37 (registro das operações)           | Session reports (Excel), findings tables, run history                                  | Each scan acts as evidence of where data was found and under which norms. |
| Art. 14 (dados de crianças e adolescentes) | Minor data detection (DOB/age inference, minors flags) and corresponding report fields | Helps map processing of minors’ data for FELCA/LGPD obligations.          |

### 2.2 GDPR – example slice

| GDPR reference / theme                   | App feature / report                                           | Notes                                                                    |
| ---------------------------------------  | -------------------------------------------------------------- | -----                                                                    |
| Art. 4(1) (personal data)                | Core detector (regex + ML/DL), norm tags `GDPR Art. 4(1)`      | Same detection engine; different norm tags and recommendation overrides. |
| Records of processing (Art. 30, Rec. 82) | Session inventory across connectors + Excel reports            | Inputs for RoPA and data-mapping exercises, not a full RoPA tool.        |

### To-dos (LGPD and GDPR mapping)

| #   | To-do                                                                                                                                                            | Status    |
| -   | -----                                                                                                                                                            | ------    |
| 2.1 | Derive a concise LGPD → feature/report table from `COMPLIANCE_FRAMEWORKS*` and existing plans (e.g. minors’ data, cross-ref risk, inventory, crypto & controls). | ⬜ Pending |
| 2.2 | Do the same for GDPR (focus on data subject rights, records of processing, security of processing, and accountability).                                          | ⬜ Pending |

---

## 3. ISO/IEC 27xxx and SOC 2 mapping

**Goal:** Clarify how the app **supports** (but does not replace) ISMS and trust-services controls.

### To-dos (ISO/IEC 27xxx and SOC 2)

| #   | To-do                                                                                                                                                                                                 | Status    |
| -   | -----                                                                                                                                                                                                 | ------    |
| 3.1 | For ISO/IEC 27701, identify which controls are primarily supported (e.g. records of processing, data mapping, evidence for DPIAs and cross-border flows) and link them to reports and configurations. | ⬜ Pending |
| 3.2 | For ISO/IEC 27001/27002/27005, map relevant control families (asset management, cryptography, logging/monitoring, communications security, risk treatment) to app outputs.                            | ⬜ Pending |
| 3.3 | For SOC 2 (Security/Availability/Confidentiality), note how discovery, inventory, and crypto/controls sheets act as evidence inputs for specific trust criteria.                                      | ⬜ Pending |

---

## 4. FELCA and child-protection/platform norms

**Goal:** Capture how minors’ data detection and related features support FELCA and similar laws.

### To-dos (FELCA and child-protection)

| #   | To-do                                                                                                                                        | Status    |
| -   | -----                                                                                                                                        | ------    |
| 4.1 | Map FELCA obligations (age-related, parental controls, privacy-by-default, transparency) to minors’ data detection and reporting in the app. | ⬜ Pending |
| 4.2 | Add a brief note on how the same capabilities could support other regional child-protection/platform norms (without over-claiming).          | ⬜ Pending |

---

## 5. Integration with docs and academic work

**Goal:** Reuse this mapping in product docs and thesis material without duplication.

### To-dos (Integration with docs and academic work)

| #   | To-do                                                                                                                                                                 | Status    |
| -   | -----                                                                                                                                                                 | ------    |
| 5.1 | Decide where to surface high-level summaries (e.g. small excerpts in `COMPLIANCE_FRAMEWORKS*`, more detailed tables only in this plan or thesis notes).               | ⬜ Pending |
| 5.2 | When a major feature/report is added (e.g. crypto & controls sheet, data-source inventory), update this mapping and note which norms/control families it strengthens. | ⬜ Pending |

---

## 6. Artifacts and evidence sources

When extending the mapping or writing evidence-focused docs:

- **App and Docker:** This repo and image `fabioleitao/data_boar`; supporting artifacts in `docs/private/From Docker hub list of repositories.md` (wildfly_t1r, uptk for infra/observability narrative).
- **Private docs:** CV, TCC, LinkedIn in `docs/private/` (git-ignored). See [TOKEN_AWARE_USAGE.md](TOKEN_AWARE_USAGE.md) §3.

---

## 7. Sync notes

- Use this plan as your **single source of truth** for detailed mappings; product docs should only expose what is needed for operators and decision-makers.
- Keep the tone careful: always “supports” or “provides evidence for”, never “fully complies” or “certifies”.

---

## 8. Candidate sectors, regulators, and programme types (backlog — not product promises)

**Purpose:** Remember **where** the product can **honestly** help (inventory, metadata-only findings, config-led labels) versus **what** requires **specialist tools**, **certified cryptography**, or **legal/sector counsel**. This section is **internal** scoping for future doc rows, optional `compliance-samples` YAML, and **consulting** scoping—not a public compliance claim.

**Maintainer / operator intent (internal memory — not an exhaustive development promise):** This backlog exists for **long-term orientation**, **control**, and **remembering eventual client-specific scoping** when a real engagement appears—for example a **Brazilian health-plan broker** needing **LGPD** plus **ANS**-adjacent **lexicon** and **recommendation** text (partial alignment, not a substitute for ANS regulatory filings). Listing terms or regulators **here** is **not** a commitment to build every corresponding feature; the typical response remains **configuration**, **optional samples**, **recommendation overrides**, and **professional services**, **prioritized when** a named client need shows up.

**Brazil — health data and HIPAA analogy:** There is **no** statute that copies **HIPAA/HITECH/ePHI** as a single package. **LGPD** (e.g. sensitive personal data including **health**, **Art. 11**) applies broadly; **sector** layers include **ANS** (health plans), **CFM** (medical practice / records norms), **ANVISA** (products and regulated activities), and other **RDCs** and norms. **Alignment for clients:** same engine as elsewhere—**discovery and mapping** of health-related and identifier patterns with **LGPD** (and **HIPAA** where data crosses US contexts); **not** a substitute for **clinical system** validation or **ANS/CFM**-specific controls. **Samples today:** **`compliance-sample-lgpd.yaml`**; built-in **HIPAA** tags in the app for US-facing wording; **no** separate “BR HIPAA” YAML unless we later add an optional **health-sector lexicon** sample (doc-only / low-code).

**United States — healthcare fraud & abuse (AKS, Stark, False Claims Act) — horizon:** Corporate **life sciences**, **providers**, and **payers** with **US** federal healthcare exposure often run programmes against **AKS** (**Anti-Kickback Statute**), **Stark** (**Physician Self-Referral Law**), and the **FCA** (**False Claims Act**). These are **legal** and **enforcement** regimes (**OIG**, **DOJ**, **CMS** oversight)—**not** pattern libraries the product can “implement”. Honest adjacency: **technical inventory** and **metadata-only** visibility into **where** **compensation**, **referral**, **physician**, **payer**, or **government-billing** structured data may sit (**contracts**, **rebate** tables, **CRM** exports, **email** archives, **shared drives**) so **compliance** and **counsel** can prioritise **human** review and **specialist** workflows; we **do not** score **arrangements** for **safe harbour**, **exception**, or **FCA** liability, and we **do not** replace **compliance-monitoring** tooling or **legal** opinions. Optional **`recommendation_overrides`** may name these statutes **only** under **counsel**-approved wording for a **named** engagement—never a default **public** claim of **AKS/Stark/FCA** “compliance”.

**United States — FCPA and internal anti-corruption policy packs (horizon):** The **FCPA** (**Foreign Corrupt Practices Act**) combines **anti-bribery** prohibitions with **books-and-records** and **internal accounting controls** expectations for **issuers** and certain other persons—**DOJ** and **SEC** enforcement. Employers may maintain **internal** norms (sometimes abbreviated **FPCA** or similar) to **operationalise** **FCPA**-aligned **controls** alongside **privacy** and **records** governance. Honest adjacency: **inventory** and **metadata-only** findings for **where** **policy** language, **approval** trails, **third-party** / **intermediary** due-diligence **artefacts**, **training** **records**, or **contract** clauses appear in the **data soup**—**supporting** **DPO**, **legal**, and **compliance** in **control** testing and **signals of possible non-conformity** for **human** prioritisation; we **do not** **detect** **bribes**, **conclude** **FCPA** **violations**, or replace **specialist** **anti-corruption** **monitoring** or **legal** analysis. Optional **`compliance-samples`** lexicon and **`recommendation_overrides`** only with **counsel**-approved wording for **named** engagements—same **ceiling** as [ADR 0025](../adr/ADR-0025-compliance-positioning-evidence-inventory-not-legal-conclusion-engine.md).

**United States — False Claims Act (adjacent); FDA; United Kingdom FCA; insurance markets — horizon:** **(1) FCA (US) adjacent:** Clients may also cite **state** **False Claims Acts**, **Civil Monetary Penalties Law** (**CMPL**), **Program Fraud Civil Remedies Act** (**PFCRA**), and **OIG**/**DOJ**/**CMS** **enforcement** programmes—the same **honest adjacency** as the **FCA** paragraph above (**inventory** of relevant **records**, **not** **liability** scoring). **(2) FDA** (**Food and Drug Administration**): **FD&C Act** and **21 CFR** (e.g. **GxP**-shaped **recordkeeping** expectations); we support **discovery** of **clinical**, **pharmacovigilance**, and **regulatory** content in **files** and **repositories**—**not** **21 CFR Part 11** **system validation**, **not** **FDA** **product** **clearance** evidence. **(3) FCA (UK) — disambiguation:** **Financial Conduct Authority** is **not** the **US False Claims Act**; **UK** **financial services** **conduct** rules (**SMCR**, **Consumer Duty**, **PRA**/**FCA** **handbooks** where applicable) imply **governance** and **data** **inventory** for **UK**-shaped **operations**—same **technical** **evidence** story, **no** **FCA** **authorisation** or **conduct** **certification**. **(4) Insurance markets:** **US** — **state** **insurance** regulators and **NAIC** **model** laws (**privacy**/cyber **bulletins**, **financial** **examination** data requests); **EU** — **Solvency II**, **IDD** (**Insurance Distribution Directive**); **Brazil** — **SUSEP**/**CNSP** (already under **Brazil — financial** above). Stance: **PII**/**sensitive** **inventory** and **policy-tagged** findings for **governance**; we **do not** produce **prudential** **returns**, **actuarial** **controls**, or **market** **conduct** **automation**.

**Brazil — financial / capital markets / public sector (examples, not exhaustive):** **BACEN** (including resolutions on cybersecurity and data), **CVM**, **SUSEP**, **B3** rules, **RFB** (tax/secrecy and ancillary obligations), **Dataprev**-related and other **public-sector** processing—all sit **on top of LGPD** and sector law. The product **does not** implement **PLD/Fiscal** transaction monitoring or **regulatory reporting**; it **can** support **data inventory** and **PII/sensitive-data visibility** for **governance** and **risk** programmes. **Samples today:** **`compliance-sample-pci_dss.yaml`** (card data patterns); **no** dedicated BACEN/SUSEP YAML yet—feasible later as **`recommendation_overrides`** + terms (with **counsel** review).

**Brazil — payments, exchanges, guarantee funds, consumer credit (horizon; acronyms clients may mention):** **Interbank / payment arrangements** (including **Pix**, **STR**, institutional flows) are **BACEN**-regulated; **LGPD** still applies to **account-holder** and **operation** data in **databases**, **logs**, and **exports**—our usual **inventory** and **metadata-only** reports apply; we **do not** validate **SPI**/**Pix** message formats or **settlement** rules. **Bolsa de valores / B3** and **CVM**-supervised actors are already covered under **capital markets** above (investor and market data in the **data soup**). **Three distinct client mentions (keep separate):** **(1) FGC (Brazil)** — **Fundo Garantidor de Créditos** (deposit insurance); **prudential**/**institutional** framing, **not** a file-level “FGC compliance” detector—use in **governance** narrative only where **counsel** ties **retention** or **reporting** to evidence needs. **(2) IMF** — **International Monetary Fund**; **macro**, **IFI**, and cross-border **reporting** contexts—**peripheral** to typical corporate **data soup** unless the engagement explicitly requires that lens. **(3) U.S. FCC** — **Federal Communications Commission** (telecommunications); relevant when **vendor**, **subsidiary**, or **data-flow** language is **U.S.**-shaped (e.g. carrier, CPE, **CPNI**-adjacent discussions)—**not** Brazilian law; **do not** conflate with **FGC**. **CDC** (**Código de Defesa do Consumidor**) interacts with **LGPD** in **B2C** financial and service relationships; **recommendation** text may reference **consumer** fairness under **counsel**, not automated **CDC** compliance. **No** exhaustive tracking of every **Circular** or **Normativa** in product code—**consulting** + **overrides** when a **named** **financial** or **payments** client appears.

**Mercosur (regional horizon — not a unified data-protection statute):** The bloc **does not** supersede **national** privacy and sector laws (**LGPD** in Brazil; **Argentina** Law 25.326; **Uruguay** Law 18.331; **Paraguay** developments; etc.). **Named bloc milestones** clients may mention: **GMC Resolution 37/19** (July 2019) on **consumer protection in e-commerce**—in Brazil, **internalized** via **Federal Decree 10.271/2020** (operator-facing **CDC**/e-commerce context, not a detector template); **Additional Protocol on Electronic Commerce** / **Mercosur electronic commerce agreement** (concluded **2021**) addressing **digital trade**, **authentication**, and **online** consumer themes—**without** creating a single Mercosur-wide **personal-data** code; **mutual recognition of digital-signature certificates** (e.g. **Argentina–Uruguay**, in force **2021**). **EU–Mercosur** association/trade negotiations add **cross-border** **services/digital** expectations when/if agreements enter into force—**external** to “pure” Mercosur primary law. Stance: same **inventory** and **governance** evidence story; **no** “Mercosur compliance mode” or exhaustive **GMC** tracking in product code.

**Multi-jurisdiction privacy and sector anchors — horizon (non-exhaustive; same inventory story as LGPD/GDPR clients):** **Canada:** **PIPEDA** (federal) plus **provincial** laws (**Alberta**/**BC** **PIPA**; **Québec** **Law 25**). **EU:** **GDPR**, **ePrivacy** (instrument evolving), sector layers such as **NIS2** and **DORA** where cited by the client; **Benelux** is **not** a separate privacy statute—**Belgium** (**GBA**), **Netherlands** (**AP**), **Luxembourg** (**CNPD**) apply **GDPR** plus **national** practice. **UK:** **UK GDPR** + **Data Protection Act 2018** + **ICO** (see also **UK FCA** row above for **financial** conduct). **Switzerland:** **FADP** (revised). **Oceania / Australia & New Zealand:** **Australia** **Privacy Act** (reform trajectory); **New Zealand** **Privacy Act 2020**. **Singapore:** **PDPA**. **Hong Kong:** **PDPO**. **Taiwan:** **Personal Data Protection Act**. **Japan:** **APPI**. **South Korea:** **PIPA**. **China:** **PIPL** and **cybersecurity**/**data** **security** laws—**high** **counsel** sensitivity and **localization** themes. **India:** **DPDPA**. **ASEAN:** **Model Framework** (soft); **national** laws vary. **Middle East (examples):** **UAE** and **Saudi Arabia** **PDPL**-style laws; **Israel** **Privacy Protection Law** (and **regulator** practice)—verify **current** text with **counsel**. **Africa (examples):** **South Africa** **POPIA**; **Kenya** **DPA**; **Nigeria** **NDPR**—**fragmented**; **national** engagement scoping. **Russia:** **152-FZ** (personal data)—**localization**/**registration** themes; **sanctions** and **operations** are **outside** product scope. **Ukraine:** **Law on Personal Data Protection** (verify **current** title and **amendments** with **counsel**); **wartime** **context** for **cross-border** and **continuity**—**counsel**-led only. **Commonwealth:** **not** a single legal regime—some members mirror **UK**/**EU**-style **DPAs** (**Australia**, **NZ**, **Canada**, **India**, **Caribbean**/**Pacific** **variations**). Stance: **technical** **inventory** and **policy-tagged** findings for **named** **jurisdictions**; **no** promise of an exhaustive **per-country** **norm** **library** in **core** **code**—**optional** **`recommendation_overrides`** and **consulting** when a **real** **multi-country** **client** appears.

**Brazil — ANPD and other national agencies (non-exhaustive, horizon only):** **ANPD** (Autoridade Nacional de Proteção de Dados) issues **guidelines**, **oversight**, and **interpretation** of **LGPD**—not a separate “data type” layer for the detector, but **central** for how clients structure **privacy programmes** and **documentation**. Our role stays **technical inventory** and **evidence** for **DPO/legal** to map to ANPD expectations; **not** filing with ANPD or **representing** the client before the authority. **ANATEL** (telecommunications) and **ANAC** (civil aviation) add **sector** obligations (e.g. customer data, traffic or metadata in telecom; passenger and operational data in aviation) **on top of LGPD**—same **discovery** story with **sector-specific** **lexicon** in **overrides** when an engagement requires it. Other **agências reguladoras** (e.g. **ANEEL**, **ANP**, **ANA**, **ANS**, **ANVISA**—already noted above) follow the same pattern: **LGPD** + **sector rule** + **internal policy**; we **do not** automate **regulatory returns** or **licence** conditions. **No** promise to track every future **recommendation** or **resolution** from each agency in product code—**consulting** and **periodic review** of **norm tags** when a **named sector** client appears.

**PEP / KYC / CDD / EDD / AML adjacency:** Already positioned in [COMPLIANCE_AND_LEGAL.md](../COMPLIANCE_AND_LEGAL.md) (inventory vs list screening). Future work here is **lexicon** and **samples**, not **screening engines**.

**PCI DSS 4.x:** Existing sample targets **cardholder data** patterns; **version** evolution (3.x → 4.x) is a **periodic review** item for the sample file header and overrides—see [compliance-samples/README.md](../compliance-samples/README.md) *Sample maintenance*.

**FIPS 140-2 / 140-3:** Relevant to **deployment** (OS, OpenSSL, HSM, Python crypto stacks)—**not** something the scanner “certifies”. Mapping, if any, belongs under **operator deployment** and **environment** evidence, not detector features.

**NIST (US publications — adjacent evidence, not NIST certification):** Procurement and risk teams often use the **NIST Cybersecurity Framework (CSF) 2.0** (e.g. **Govern**, **Identify**) and the **NIST Privacy Framework** (e.g. **Identify**, **Govern**, and parts of **Control**) as **vocabulary** for data and security programmes. **NIST SP 800-122** (protecting confidentiality of PII) and **SP 800-66** (HIPAA security implementation guidance) sit close to our **inventory** and **remediation-evidence** story; they do **not** turn the product into a **NIST** assessment tool. The product **does not** walk **SP 800-53** control-by-control or produce **NIST** attestations. **NIST AI Risk Management Framework (AI RMF)** is only **adjacent** if a client needs to **map** or **inventory** data that feeds AI systems. Optional **`recommendation_overrides`** or **consulting** may reference these publications **for a named engagement**—never a default **public** promise of “implements NIST”.

**Large enterprises and mixed programmes (e.g. energy, critical infrastructure):** Organisations often publish **internal** baselines (sometimes aligned to **NIST CSF**, **ISO 27001**, **CIS**). The product supports **technical inventory** and **policy-tagged** findings; it **does not** replace **vendor-specific** or **sector-specific** compliance programmes.

**Named companies (e.g. state-owned enterprises):** **Petrobras** and similar are **not** regulators; alignment is via **their** policies and **LGPD** plus sector safety/environment rules where applicable—same **inventory** story, **no** endorsement.

**Positioning ceiling — not “the solution” for legal violation risk:** The product is a strong **technical** layer for **Identify**-style outcomes: **where** **personal** and **sensitive** data (including **health** and **financial** **identifiers** in **files**) **actually** **lives**, **duplicates**, and **leaks** across the **data soup**. It **reduces** **“we did not know it was there”** and **shadow** **copy** risk and **feeds** **DPIA**, **RoPA**, **incident** **scoping**, and **counsel** **review** with **evidence**. It **does not** **guarantee** **compliance**, **eliminate** **fines**, or **replace** **organisational** **controls**, **DPO**/**legal** **judgment**, **contracts**, **TIAs**, **purpose** **limitation**, or **sector** **reporting**. **Public** and **pitch** language must stay aligned with [COMPLIANCE_AND_LEGAL.md](../COMPLIANCE_AND_LEGAL.md): **supports** / **evidence for**, never **certifies** / **fully complies**. Durable decision record: [ADR 0025](../adr/ADR-0025-compliance-positioning-evidence-inventory-not-legal-conclusion-engine.md).

**Long-term adjacent risk domains (map / prioritise / recommend — horizon; deepen when a client names the need):** **Biometrics** and **genetic** data (plus **US** **BIPA**-style **angles** where relevant); **children**/**minors** (**COPPA**, **LGPD** **guardian** contexts). **Trade secrets** and **confidential** **business** information — **location** **discovery** only, **not** **legal** **trade-secret** **analysis**. **Legal** **privilege** — **extreme** **care** (**high** **false** **positives**); **counsel**-approved **wording** only if ever surfaced. **Cross-border** flows — **inventory** of **what** **categories** sit **where** to **inform** **TIA**/**SCC** **work**, **not** **adequacy** **decisions**. **Incident** **response** — **enumerate** **affected** **data** **classes** for **notification** **scoping** **support**, **not** **legal** **threshold** **calls**. **AI**/**ML** **training**, **fine-tuning**, and **RAG** **corpora** — **lineage**-style **inventory** (see **NIST** **AI** **RMF** row). **Vendor** **due** **diligence** **questionnaires** — **export** **evidence** from **scans**, **not** **auto-fill** **compliance**. **Whistleblower**/**ethics**/**HR** **sensitive** **queues** — same **discovery** **story** with **strict** **access** **and** **counsel** **gates**. **Sanctions**/**export** **control** — **not** **list** **screening**; at most **locating** **structured** **counterparty** **stores** **with** **boundary** **clear** vs **dedicated** **sanctions-screening** **systems**. **Recognition rule:** if the **client** **asks** for **legal** **conclusions**, **transaction** **monitoring**, or **regulatory** **returns**, that is a **gap** **misfit** — **redirect** to **counsel**/**specialist** **tools** and **document** **SOW**/**override** **scope** accordingly.

### To-dos (Sector and programme backlog)

| #   | To-do                                                                                                                                                       | Status    |
| --- | -----                                                                                                                                                       | --------- |
| 8.1 | Prioritise **one** BR-sector slice for a future optional sample or doc table (e.g. financial lexicon vs health lexicon)—token-aware; no scope creep.        | ⬜ Pending |
| 8.2 | Keep [COMPLIANCE_AND_LEGAL.md](../COMPLIANCE_AND_LEGAL.md) and [COMPLIANCE_FRAMEWORKS.md](../COMPLIANCE_FRAMEWORKS.md) as the **public** ceiling; deep regulator tables stay **here** or in **consulting** artefacts. | ⬜ Pending |
| 8.3 | When **positioning** **evolves**, re-check **COMPLIANCE_AND_LEGAL** / pitch for **alignment** with the **Positioning ceiling** paragraph above. | ⬜ Pending |
| 8.4 | On **named** **client** **request**, **triage** **Long-term** **adjacent** **risk** **domains** into **optional** **samples** or **`recommendation_overrides`** (token-aware; **counsel** for **privilege**/ **cross-border** **claims**). | ⬜ Pending |
