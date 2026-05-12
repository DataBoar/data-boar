# Compliance frameworks and extensibility

The application helps DPO, security, and compliance teams discover and map personal or sensitive data with configurable regulation-oriented labels and recommendation text. This document describes which frameworks are explicitly referenced today, where to find sample configuration, and how to extend support to others (e.g. UK GDPR, PIPEDA, APPI, POPIA) without code changes.

**Decision-makers (legal / compliance leadership):** start with the non-technical summary [COMPLIANCE_AND_LEGAL.md](COMPLIANCE_AND_LEGAL.md) ([pt-BR](COMPLIANCE_AND_LEGAL.pt_BR.md)); return here for **files, samples, and merge steps**.

**Português (Brasil):** [COMPLIANCE_FRAMEWORKS.pt_BR.md](COMPLIANCE_FRAMEWORKS.pt_BR.md)

### Governance-ready exports (briefings vs configuration depth)

**`norm_tag`**, **recommendation overrides**, and the Excel workbook remain the **primary** way to align **detection and report wording** with each **framework profile** you merge from [compliance-samples/](compliance-samples/). For **CISO/DPO read-outs** of a **completed** scan, the product may also emit **executive Markdown** and a **`scan_manifest_*.yaml`** alongside the XLSX: they summarise **execution posture** (sampling, timeouts, dialect notes where applicable) and **prioritised remediation** without pasting sensitive literals—useful when **counsel** asks both *what* was labelled and *how* reads were bounded. They are **governance-adjacent** artefacts, **not** a substitute for programme-level GRC tooling or legal sign-off—see **Evidence and outputs** in [COMPLIANCE_AND_LEGAL.md](COMPLIANCE_AND_LEGAL.md) and [REPORTS_AND_COMPLIANCE_OUTPUTS.md](REPORTS_AND_COMPLIANCE_OUTPUTS.md).

### Engine vocabulary (POC decks and technical docs)

The root [README](../README.md) **“For decision-makers”** section stays in **plain stakeholder language** (for example **sniffing with judgment** on the **data soup** metaphor). It does **not** require the internal deck labels below.

For **slide banks, workshop handouts, and structured compliance technical docs** (this page, [COMPLIANCE_TECHNICAL_REFERENCE.md](COMPLIANCE_TECHNICAL_REFERENCE.md), [GLOSSARY.md](GLOSSARY.md)), optional paired labels **Data Sniffing** (the **discovery and sampling pass**: connectors, bounded reads, sensitivity detection) and **Deep Boring** (the **structured compliance-report depth**: Excel workbooks, **norm_tag** alignment, **recommendation overrides**, heatmaps) keep vocabulary stable. They are **two halves of one session**, not competing features. Internal plans may still say *“deep sniffing”* or *“sniffing harder”*; when you promote copy to **decks** or **technical** prose for procurement/DPO workshops, you may standardise on **Data Sniffing** / **Deep Boring** as defined in [GLOSSARY.md](GLOSSARY.md#1-product-identity--data-landscape)—without treating the README executive blurb as the place to introduce those names.

<a id="deterministic-detection-vs-generative-llm-hype"></a>

### Deterministic detection vs generative LLM hype (product posture)

**Discovered evidence vs narrated “AI”.** The engine produces **repeatable** **findings** from **regex**, **named patterns**, and **supervised** **ML/DL** on **your** training terms—plus structured signals such as **quasi-identifier** aggregation, **minor**-related columns, and **jurisdiction hints / tension** (always **heuristic**, never “applicable law” in software). That is a different contract from **generative LLMs**, which optimise for fluent text and may vary run-to-run. For architecture and audit expectations, see [TECH_GUIDE.md](TECH_GUIDE.md#detection-stack-vs-generative-llms); for terminology (**LLM**, **deterministic detection stack**, **Google Gemini** maintainer tooling), see [GLOSSARY.md](GLOSSARY.md) §8–9 and [docs/ops/LLM_AGENT_EDITING_CAUTION.md](ops/LLM_AGENT_EDITING_CAUTION.md). For a **vendor-neutral** timeline from **1950s** symbolic work through **AI winters**, **expert systems**, statistical ML, **deep learning**, and today’s **LLMs**—and where each family fits—see [AI_EVOLUTION_PRIMER.md](AI_EVOLUTION_PRIMER.md) ([pt-BR](AI_EVOLUTION_PRIMER.pt_BR.md)).

---

## Regulations we support today (built-in and config examples)

**Built-in (out of the box):** The detector and reports explicitly reference **LGPD** (Brazil), **GDPR** (EU), **CCPA** (California), **HIPAA** (US health), and **GLBA** (US financial). Findings use these norm tags and recommendation text by default.

**Sample configuration and examples:** We provide config-file examples so you can align with more regulations without changing code (including **per-region YAML profiles** under **`compliance-samples/`**, e.g. **Russia 152-FZ** — see [List of samples and links](#list-of-samples-and-links)):

- **[regex_overrides.example.yaml](regex_overrides.example.yaml)** – custom regex patterns with `norm_tag` (e.g. LGPD Art. 5, CCPA). Copy and extend for other identifiers (e.g. UK NIN, Canadian SIN) and set `norm_tag` to your framework.
- **Recommendation overrides** – in [USAGE.md](USAGE.md) (report section) you will find `report.recommendation_overrides`: list of `norm_tag_pattern`, `base_legal`, `risk`, `recommendation`, `priority`, `relevant_for`. Use this to tailor report text for any regulation (UK GDPR, PIPEDA, POPIA, APPI, PCI-DSS, or internal norms).
- **ML/DL terms** – [SENSITIVITY_DETECTION.md](SENSITIVITY_DETECTION.md) and the main config support `ml_patterns_file`, `dl_patterns_file`, or inline `sensitivity_detection.ml_terms` / `dl_terms` so you can add framework-specific terms (e.g. “personal information”, “data subject”, “responsible party”) for better detection and labelling.

**Compliance samples (one profile per regulation):** Sample configs for **UK GDPR**, **EU GDPR**, **Benelux**, **PIPEDA**, **POPIA**, **APPI**, **PCI-DSS**, **Russia (Federal Law 152-FZ)**, and other regions are in [compliance-samples/](compliance-samples/). Each sample is a single YAML file with regex patterns, ML terms, and recommendation overrides for that framework. See the [Compliance samples](#compliance-samples) section below for the full list, what goes in which file, and how to use them. For **language and target audience** (e.g. PIPEDA → EN + FR for Canada; **152-FZ** → EN + RU terms in the Russian sample), see the [compliance-samples README](compliance-samples/README.md).

---

## Brazil insurance sector (LGPD anchoring + prudential references) {#brazil-insurance-sector-lgpd-anchoring-prudential-references}

**Not legal advice.** This subsection orients technical and compliance readers who operate in **Brazilian private insurance** (SUSEP-supervised undertakings, brokers, and service providers). It is **not** a substitute for counsel, ANPD guidance, or prudential supervision practice.

**What the product does here:** Data Boar supports **discovery, sampling, and metadata-oriented reporting** (including configurable **`norm_tag`** text). It does **not** certify **LGPD** compliance, **SUSEP/CNSP** compliance, solvency reporting, licensing, or any supervisory outcome.

**LGPD as the primary data-protection anchor:** Personal and sensitive data processed in insurance workflows remain subject to the **Lei Geral de Proteção de Dados** (LGPD). Official text: [Planalto — Lei nº 13.709/2018](https://www.planalto.gov.br/ccivil_03/leis/2018/l13709.htm). The **ANPD** publishes guidance applicable across sectors: [gov.br — ANPD](https://www.gov.br/anpd/pt-br).

**Prudential and market-conduct layer (sector, not a substitute for LGPD):** **SUSEP** supervises private insurance in Brazil; **CNSP** (within that policy ecosystem) issues resolutions that firms must operationalise alongside LGPD where personal data is involved. Official entry point for instruments and communications: [gov.br — SUSEP](https://www.gov.br/susep/pt-br). **Circular letters** and **CNSP** norms appear in SUSEP’s official **legislation / normative** channels on the same portal; always use the **current consolidated** text on **gov.br** before relying on any deep link.

**Optional YAML skeleton:** For **generic** insurance-sector column names and document vocabulary with **LGPD-inventory-oriented** `norm_tag` strings (still **not** a regulatory certification), see [compliance-sample-br_insurance_lgpd_anchor.yaml](compliance-samples/compliance-sample-br_insurance_lgpd_anchor.yaml) in the table below. Pair it with the full **[compliance-sample-lgpd.yaml](compliance-samples/compliance-sample-lgpd.yaml)** profile when you need Brazilian identifier coverage (CPF, CNPJ, etc.).

---

## Compliance samples

Sample configuration files for **UK GDPR**, **EU GDPR**, **Benelux**, **PIPEDA**, **POPIA**, **APPI**, **PCI-DSS**, **Russia (152-FZ)**, and optional regional frameworks are in [compliance-samples/](compliance-samples/). Each file is self-contained (regex overrides, ML terms, recommendation overrides) so you can enable one framework by pointing your config at that file and merging its overrides.

Laws, guidance, and real-world identifier usage evolve in many sampled jurisdictions—not only those with the fastest statutory churn. **Statutes and official texts are also reworded or replaced over time**, so YAML that “matched last year” may need updates even when politics are stable. Plan to **refresh samples you rely on** (regex, terms, overrides) on a cadence that fits your risk—**quarterly or before a minor release** is a reasonable default for high-stakes profiles; see [Sample maintenance](compliance-samples/README.md#sample-maintenance) in the compliance-samples README. The **152-FZ** sample header calls out especially frequent legal churn; treat it as a template for documenting review risk in other jurisdictions.

### List of samples and links

| Regulation / region           | Sample file                                                                                                 | Purpose                                                                                             |
| -------------------           | -----------                                                                                                 | -------                                                                                             |
| **LGPD (Brazil)**             | [compliance-sample-lgpd.yaml](compliance-samples/compliance-sample-lgpd.yaml)                               | Bilingual PT-BR + EN terms; RG/CEP regex; Brazilian deployments.                                    |
| **Brazil (insurance sector — LGPD inventory skeleton)** | [compliance-sample-br_insurance_lgpd_anchor.yaml](compliance-samples/compliance-sample-br_insurance_lgpd_anchor.yaml) | Generic insurance lexicon + LGPD-anchored **`norm_tag`** for inventory; **not** SUSEP/CNSP certification (see [insurance subsection](#brazil-insurance-sector-lgpd-anchoring-prudential-references)). |
| **UK GDPR**                   | [compliance-sample-uk_gdpr.yaml](compliance-samples/compliance-sample-uk_gdpr.yaml)                         | UK post-Brexit, ICO-aligned; norm_tag and recommendation overrides.                                 |
| **EU GDPR (EEA)**             | [compliance-sample-eu_gdpr.yaml](compliance-samples/compliance-sample-eu_gdpr.yaml)                         | EU 2016/679 Art. 4(1), EDPB, member-state DPAs; optional EN + DE/FR terms.                          |
| **Benelux (BE, NL, LU)**      | [compliance-sample-benelux.yaml](compliance-samples/compliance-sample-benelux.yaml)                         | EU GDPR base + national IDs (BSN, NISS, LU); national DPA overrides; EN + NL/FR.                    |
| **PIPEDA (Canada)**           | [compliance-sample-pipeda.yaml](compliance-samples/compliance-sample-pipeda.yaml)                           | Personal information, consent; Canadian identifiers (e.g. SIN); EN + FR.                            |
| **POPIA (South Africa)**      | [compliance-sample-popia.yaml](compliance-samples/compliance-sample-popia.yaml)                             | Responsible party, personal information; SA identifiers.                                            |
| **APPI (Japan)**              | [compliance-sample-appi.yaml](compliance-samples/compliance-sample-appi.yaml)                               | Personal information, retained personal data; PPC alignment.                                        |
| **PCI-DSS**                   | [compliance-sample-pci_dss.yaml](compliance-samples/compliance-sample-pci_dss.yaml)                         | Payment card patterns and recommendation overrides for merchants/assessors.                         |
| **Philippines (DPA)**         | [compliance-sample-philippines_dpa.yaml](compliance-samples/compliance-sample-philippines_dpa.yaml)         | RA 10173, NPC; personal/sensitive personal information.                                             |
| **Australia (Privacy Act)**   | [compliance-sample-australia_privacy.yaml](compliance-samples/compliance-sample-australia_privacy.yaml)     | Privacy Act 1988, OAIC, APPs; optional TFN regex.                                                   |
| **Singapore (PDPA)**          | [compliance-sample-singapore_pdpa.yaml](compliance-samples/compliance-sample-singapore_pdpa.yaml)           | PDPA 2012, PDPC; personal data, DNC; NRIC regex.                                                    |
| **UAE (PDPL)**                | [compliance-sample-uae_pdpl.yaml](compliance-samples/compliance-sample-uae_pdpl.yaml)                       | Decree-Law 45/2021; personal/sensitive data; EN + optional AR.                                      |
| **Argentina (PDPA)**          | [compliance-sample-argentina_pdpa.yaml](compliance-samples/compliance-sample-argentina_pdpa.yaml)           | Ley 25.326, DNPDP; datos personales; ES + EN; CUIT/CUIL/DNI regex.                                  |
| **Kenya (DPA)**               | [compliance-sample-kenya_dpa.yaml](compliance-samples/compliance-sample-kenya_dpa.yaml)                     | Data Protection Act 2019, ODPC; personal data, data controller.                                     |
| **India (DPDP)**              | [compliance-sample-india_dpdp.yaml](compliance-samples/compliance-sample-india_dpdp.yaml)                   | DPDP Act 2023, DPBI; Aadhaar/PAN regex; EN.                                                         |
| **Turkey (KVKK)**             | [compliance-sample-turkey_kvkk.yaml](compliance-samples/compliance-sample-turkey_kvkk.yaml)                 | Law 6698, KVKK Board; kişisel veri; EN + TR; TC Kimlik regex.                                       |
| **New Zealand (Privacy Act)** | [compliance-sample-new_zealand_privacy.yaml](compliance-samples/compliance-sample-new_zealand_privacy.yaml) | Privacy Act 2020, OPC; personal information, IPPs.                                                  |
| **Russia (152-FZ)**           | [compliance-sample-russia_152_fz.yaml](compliance-samples/compliance-sample-russia_152_fz.yaml)             | Federal Law 152-FZ, Roskomnadzor; EN + RU terms; SNILS + heuristic INN regex; **revalidate often**. |
| **Saudi (PDPL)**              | [compliance-sample-saudi_pdpl.yaml](compliance-samples/compliance-sample-saudi_pdpl.yaml)                   | Royal Decree M/19, SDAIA; personal/sensitive data.                                                  |
| **Israel (PPL)**              | [compliance-sample-israel_ppl.yaml](compliance-samples/compliance-sample-israel_ppl.yaml)                   | Privacy Protection Law, PPA; personal information, database registrar.                              |
| **Colombia (Law 1581)**       | [compliance-sample-colombia_1581.yaml](compliance-samples/compliance-sample-colombia_1581.yaml)             | Ley 1581/2012, SIC; datos personales; ES + EN; CC/NIT regex.                                        |
| **Chile (Privacy)**           | [compliance-sample-chile_privacy.yaml](compliance-samples/compliance-sample-chile_privacy.yaml)             | Law 19.628; datos personales; ES + EN; RUT regex.                                                   |
| **Nigeria (NDPR)**            | [compliance-sample-nigeria_ndpr.yaml](compliance-samples/compliance-sample-nigeria_ndpr.yaml)               | NDPR 2019, NITDA; personal data, data controller.                                                   |
| **Morocco (Law 09-08)**       | [compliance-sample-morocco_09_08.yaml](compliance-samples/compliance-sample-morocco_09_08.yaml)             | Law 09-08, CNDP; données à caractère personnel; FR + EN; CIN regex.                                 |
| **Switzerland (FADP)**        | [compliance-sample-switzerland_fadp.yaml](compliance-samples/compliance-sample-switzerland_fadp.yaml)       | Revised FADP, FDPIC; personal data; EN + optional DE/FR/IT; AHV/UID regex.                          |
| **U.S. (FTC COPPA)**          | [compliance-sample-us_ftc_coppa.yaml](compliance-samples/compliance-sample-us_ftc_coppa.yaml)               | Federal children's online privacy **technical mapping**; not age verification or legal advice.      |
| **U.S. (CA AB 2273)**         | [compliance-sample-us_ca_ab2273_caadca.yaml](compliance-samples/compliance-sample-us_ca_ab2273_caadca.yaml) | California Age-Appropriate Design Code **labelling**; applicability varies—counsel required.        |
| **U.S. (CO CPA — minors)**    | [compliance-sample-us_co_cpa_minors.yaml](compliance-samples/compliance-sample-us_co_cpa_minors.yaml)       | Colorado Privacy Act / under-18 contexts **technical mapping**; not “known minor” detection.        |
| **U.S. (FCPA / internal policy pack)** | [compliance-sample-us_fcpa_internal_policy_pack.yaml](compliance-samples/compliance-sample-us_fcpa_internal_policy_pack.yaml) | **FCPA**-adjacent and employer **anti-corruption policy** lexicon (**inventory**); not bribery detection or legal conclusion. |

### What goes in which file

Each sample can provide up to three kinds of content. Your **main config** references or merges them as follows:

| Config key / file                                             | Purpose                                                                                         | What the sample provides                                                                                                                                                 |
| -----------------                                             | -------                                                                                         | -------------------------                                                                                                                                                |
| **`regex_overrides_file`**                                    | Custom regex patterns; match → finding with HIGH and given `norm_tag`.                          | A list of `{ name, pattern, norm_tag }` (e.g. UK NIN, Canadian SIN, SA ID). Samples may use key `regex` or `patterns`.                                                   |
| **`ml_patterns_file`** / **`sensitivity_detection.ml_terms`** | ML (and DL) training terms; column names and sample text classified as sensitive/non_sensitive. | A list of `{ text, label }` with framework-specific terms (e.g. “data subject”, “personal information”, “responsible party”). Samples may use key `terms` or `ml_terms`. |
| **`report.recommendation_overrides`**                         | Override “Base legal”, “Risco”, “Recomendação”, “Prioridade”, “Relevante para” per `norm_tag`.  | A list of `{ norm_tag_pattern, base_legal, risk, recommendation, priority, relevant_for }` to merge into your config.                                                    |

The same YAML file can contain **regex**, **terms**, and **recommendation_overrides**; you set `regex_overrides_file` and `ml_patterns_file` to that file path, and copy the `recommendation_overrides` block into your main config under `report.recommendation_overrides`.

### How to use a sample

1. **Choose the sample** for your regulation from the table above (or from [compliance-samples/README.md](compliance-samples/README.md)).
1. **Set paths in your main config** (e.g. `config.yaml`):

   ```yaml
   regex_overrides_file: docs/compliance-samples/compliance-sample-pipeda.yaml
   ml_patterns_file: docs/compliance-samples/compliance-sample-pipeda.yaml
   ```

   Use the same file for both if the sample contains both `regex` and `terms`.

1. **Merge recommendation overrides:** Copy the `recommendation_overrides` list from the sample file into your config under `report.recommendation_overrides` (merge with any overrides you already have). See [USAGE.md](USAGE.md) (report section) for the structure.
1. **Run the scan** (CLI or API). Findings will use the norm tags and recommendation text from the sample; the Excel report will show the framework-specific Base legal, Risco, Recomendação, and Prioridade.

---

## Multi-language, multi-encoding, and multi-regional operation {#multi-language-multi-encoding-and-multi-regional-operation}

Whatever the **language**, **encoding**, or **region** of your data soup, the application is built to handle it: you can run compliance scans and reports in the language and encoding of your region without breaking in production.

### What is supported

- **Multiple languages in terms and reports:** Compliance samples can include terms in the language(s) of the target region (e.g. EN+FR for PIPEDA/Canada, PT-BR+EN for LGPD/Brazil, Japanese or Arabic for APAC/MENA, **EN+RU for Russia 152-FZ**). The Excel report and recommendation text support **Unicode** (e.g. base_legal and recommendation in Japanese, Arabic, Cyrillic, or accented characters).
- **Scripts and charset behaviour in data:** The scan and report pipeline is **Unicode-first**. Real-world content often mixes **Latin**, **Cyrillic** (e.g. Russian), **CJK** (e.g. Japanese kanji/kana), and **Arabic script** (including RTL presentation where the viewer supports it). Unusual or legacy **byte encodings** for configs and pattern files are handled via **auto-detection** (main config) and **`pattern_files_encoding`** (pattern files); **encoding sniffing and heuristics** for specific corpora can be **tuned further** (config, patterns, connectors) when a deployment needs stricter behaviour—contact us for **consulting** if your IT, security, compliance, or DPO teams require a **custom language/encoding profile**.
- **Multiple encodings for config and pattern files:** The **main config file** is read with **auto-detection** (UTF-8, UTF-8 with BOM, Windows ANSI/cp1252, Latin-1), so it loads even when saved in a legacy encoding. **Pattern files** (regex overrides, ML/DL terms) use the encoding set by **`pattern_files_encoding`** in your config (default **`utf-8`**). Set it to `cp1252` or `latin_1` only when your pattern or sample files are saved in that encoding.
- **Multiple regions:** Use the compliance sample that matches your region or regulation (LGPD, UK GDPR, EU GDPR, Benelux, PIPEDA, POPIA, APPI, PCI-DSS, **152-FZ**, or optional regional samples). Each sample is a single YAML file; you point your config at it and merge its recommendation overrides.

### Operator UI, docs, and extra locales (short- to mid-term roadmap)

Today, **tracked** product documentation is **English + pt-BR**; the **dashBOARd** web UI is largely **English** in templates. **Many** locales people ask for are **not** shipped yet—**full** dashboard and documentation surfaces in additional human languages and scripts (e.g. **es**, **fr**, **ja**, **ru**, **ar**, plus **Mandarin / Cantonese**, **Indonesian**, **Korean**, **Thai**, **Vietnamese**, **Hindi** and other **Indic** scripts, **Ethiopian / Amharic**, **broader African** contexts, **Catalan**, **Basque**, **Galician**, and more) sit on a **short- to mid-range**, **demand-driven** roadmap **together with** matching **compliance-sample** profiles where regulations warrant them. We welcome **public suggestions** (issues or discussions) on **locale or encoding gaps**; **commercial consulting** can accelerate **tailored** wording, samples, or integration hooks where the open defaults are not enough. A **public** summary of this direction (without internal planning filenames) is in the **Roadmap — internationalization and regional depth** paragraph in the repository **[README.md](../README.md)** ([pt-BR](../README.pt_BR.md)).

### How to enable and operate

1. **Choose the right sample for your region**

   See the [compliance-samples README](compliance-samples/README.md) table and the “Language and target audience” section. For example: Brazil → LGPD (PT-BR+EN); Canada → PIPEDA (EN+FR); UK → UK GDPR; EEA → EU GDPR; Benelux → Benelux sample; Japan → APPI; South Africa → POPIA; **Russia → 152-FZ** (EN+RU terms; **revalidate often**).

1. **Save config and sample files in UTF-8 (recommended)**

   Saving everything in **UTF-8** avoids encoding issues with multilingual terms. The main config file will still load if it is in another encoding (auto-detection).

1. **Set paths and encoding in your config**

   In your main `config.yaml` (or `config.json`):

   ```yaml
   # Optional: only if your pattern/sample files are NOT in UTF-8 (e.g. legacy cp1252)
   pattern_files_encoding: utf-8

   regex_overrides_file: docs/compliance-samples/compliance-sample-pipeda.yaml
   ml_patterns_file: docs/compliance-samples/compliance-sample-pipeda.yaml
   ```

   Then merge the sample’s **`recommendation_overrides`** into your config under `report.recommendation_overrides` (see [USAGE](USAGE.md) report section).

1. **Run the scan**

   Use the CLI or API as usual. Findings will use the norm tags and recommendation text from the sample; the Excel report will show Unicode correctly.

For full encoding options and examples, see [USAGE – File encoding](USAGE.md#file-encoding-config-and-pattern-files) (EN) and [USAGE.pt_BR – Encoding de arquivos](USAGE.pt_BR.md#file-encoding-config-and-pattern-files) (pt-BR).

---

**Assistance with tuning:** If your organization needs **further or better compatibility** with a specific regulation or compliance scope (e.g. VCDPA, CPA, sector-specific rules), we can assist—by **creating tailored configuration files** or making **slight code-side adjustments**—when you reach out. This helps potential customers adopt the tool for their jurisdiction or auditor expectations without starting from scratch.

---

## Auditable and management standards (supporting role)

The application does **not** certify organisations. It provides **discovery and mapping** of personal and sensitive data and **metadata-only** reporting, which supports evidence-based accountability and audit preparation.

### ISO 31000 (framing)

**ISO 31000** is a **guideline for organizational risk management** (context, assessment, treatment, monitoring)—not a product control catalogue, and **not** summarized here. **Positioning:** your organization’s **risk management process** should **guide prioritization** of which systems to scan, which remediations to pursue first, and which regulatory profiles to enable. Data Boar **supports evidence** (discovery, mapping, metadata-only reports) and **does not replace** your risk analysis, risk acceptance, or governance decisions. **Software supply Colleague-Nn** and **incident-response** inventory (SBOM for dependencies and images) are documented separately as **security / release** practice—see [SECURITY.md](../SECURITY.md), [RELEASE_INTEGRITY.md](RELEASE_INTEGRITY.md), and [ADR 0003](adr/ADR-0003-sbom-roadmap-cyclonedx-then-syft.md)—and are **not** a stand-in for ISO 31000.

- **ISO/IEC 27701 (Colleague-KS):** ISO/IEC 27701 requires PII controllers and processors to know where PII is and to document the scope of processing. Our scans and reports (findings, norm tags, Excel output) help you produce that evidence and align with the regulations you declare under ISO/IEC 27701 (e.g. LGPD, GDPR, CCPA). **Technical scope:** [COMPLIANCE_TECHNICAL_REFERENCE.md](COMPLIANCE_TECHNICAL_REFERENCE.md).
- **SOC 2:** A common pressure point for corporates; SOC 2 (Type I/II) expects documented controls over the security, availability, and confidentiality of systems that process sensitive data. We do not perform SOC 2 audits. Our **discovery and mapping** of where personal or sensitive data resides, plus metadata-only reporting, supports control design and audit preparation (e.g. evidence of data inventory and scope). Norm tags and recommendation overrides can be aligned to the trust principles and criteria you use.
- **FELCA (Lei 15.211/2025 – Estatuto Digital da Criança e do Adolescente):** In force from 17 March 2026, FELCA applies to digital platforms directed at or accessible by minors in Brazil. We do not implement age verification or platform controls. Our **minor data detection** (e.g. date-of-birth and age-related columns, “possible minor” flags) and reports help you map where data relating to minors is processed and support transparency and accountability (e.g. toward ANPD). **Technical notes:** [MINOR_DETECTION.md](MINOR_DETECTION.md).

**Other compliance to watch:** Regional child-protection or platform laws (beyond FELCA), sector-specific rules (e.g. health, finance), and new data-localisation or cross-border requirements may affect your scope. We extend support via config and [compliance-samples](compliance-samples/) as norms become relevant; no code change is required to add new norm tags or recommendation text.

**Extended sensitive categories (clinical adjacency, IP indicators, security artifacts in stored data):** The same engine can be tuned for additional lexicons and regex shapes—often with **consulting** to scope targets and reduce false positives. Positioning for buyers and DPOs (without linking to internal PMO detail): [COMPLIANCE_AND_LEGAL.md](COMPLIANCE_AND_LEGAL.md#extended-sensitive-categories-configuration-and-services).

**U.S. child and minor privacy (technical only):** Optional samples ([FTC COPPA framing](compliance-samples/compliance-sample-us_ftc_coppa.yaml), [California AB 2273](compliance-samples/compliance-sample-us_ca_ab2273_caadca.yaml), [Colorado CPA minors context](compliance-samples/compliance-sample-us_co_cpa_minors.yaml)) add **norm tags and report wording** for audit prep, DPO review, and operational scoping. They do **not** provide legal advice, verify parental consent, or prove compliance. **Disclaimers and sample intent:** [COMPLIANCE_TECHNICAL_REFERENCE.md](COMPLIANCE_TECHNICAL_REFERENCE.md) and each YAML file’s header comments under [compliance-samples/](compliance-samples/).

Other auditable or regional norms can be addressed via our config-driven norm tags and [compliance-samples](compliance-samples/); we continue to extend documentation and samples as new standards become relevant.

---

## Explicitly referenced today (built-in labels)

The built-in regex patterns and report labels refer to these frameworks (with example `norm_tag` values):

| Framework | Scope                                   | Example norm_tag (in reports) |
| ---       | ---                                     | ---                           |
| **LGPD**  | Brazil – Lei Geral de Proteção de Dados | `LGPD Art. 5`                 |
| **GDPR**  | EU – General Data Protection Regulation | `GDPR Art. 4(1)`              |
| **CCPA**  | California – Consumer Privacy Act       | `CCPA`                        |
| **HIPAA** | US – Health data                        | Health/insurance context      |
| **GLBA**  | US – Financial services                 | `PCI/GLBA` (e.g. credit card) |

Findings are stored with a free-form **`norm_tag`** and **`pattern_detected`**; the Excel report uses them in the **Recommendations** sheet (Base legal, Risco, Recomendação, Prioridade, Relevante para).

---

## Extensibility

- **`norm_tag`** and **`pattern_detected`** are open: you can set them to any framework or internal label.
- **Regex overrides:** Use [regex_overrides_file](SENSITIVITY_DETECTION.md#custom-regex-patterns-detecting-new-personalsensitive-values) to add patterns and set `norm_tag` to e.g. `"UK GDPR"`, `"PIPEDA s. 2"`, `"APPI"`, `"POPIA"` so they appear in reports and recommendations.
- **Recommendation overrides (config):** Use `report.recommendation_overrides` in config to tailor "Base legal", "Relevante para", and other recommendation text per `norm_tag` pattern—so UK GDPR, PIPEDA, APPI, POPIA, or custom norms get the right labels and text without changing code. See [USAGE.md](USAGE.md) (report section) for an example.
- **Custom connectors:** New data sources can emit findings with any `norm_tag`; reporting and recommendations will use config overrides when provided, otherwise the built-in fallbacks.

No change to detector logic or thresholds is required; extensibility is via config and optional override files.

**Documentation index** (all topics, both languages): [README.md](README.md) · [README.pt_BR.md](README.pt_BR.md). For configuration schema and report options, see [USAGE.md](USAGE.md) ([pt-BR](USAGE.pt_BR.md)) and [TECH_GUIDE.md](TECH_GUIDE.md) ([pt-BR](TECH_GUIDE.pt_BR.md)).
