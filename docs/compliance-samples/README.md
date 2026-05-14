# Compliance samples

**Português (Brasil):** [README.pt_BR.md](README.pt_BR.md)

Sample configuration files to enable **additional compliance frameworks** with the same scan-and-report flow. Copy the relevant blocks into your main config, or set `regex_overrides_file` / `ml_patterns_file` and merge the sample’s `report.recommendation_overrides`. The set includes **Russia (Federal Law 152-FZ)** alongside LGPD, GDPR family, PIPEDA, APPI, and others—see the table below and [COMPLIANCE_FRAMEWORKS.md](../COMPLIANCE_FRAMEWORKS.md#list-of-samples-and-links) ([pt-BR](../COMPLIANCE_FRAMEWORKS.pt_BR.md#lista-de-amostras-e-links)). For how to use and how each framework maps to config, see [COMPLIANCE_FRAMEWORKS.md](../COMPLIANCE_FRAMEWORKS.md) ([pt-BR](../COMPLIANCE_FRAMEWORKS.pt_BR.md)).

For operational governance (scope, minimization, retention, traceability), use [OPERATOR_GOVERNANCE_CHECKLIST.md](OPERATOR_GOVERNANCE_CHECKLIST.md) ([pt-BR](OPERATOR_GOVERNANCE_CHECKLIST.pt_BR.md)).

## Sample files (one per regulation)

| File                                           | Purpose                                                                                                                                                             |
| ------                                         | ---------                                                                                                                                                           |
| **compliance-sample-lgpd.yaml**                | LGPD (Brazil): bilingual PT-BR + EN terms (e.g. documento oficial / official document, RG, CNH / Driver License); RG/CEP regex; **precise geolocation** regex (same geometry as VCDPA / EU GDPR sample); for Brazilian deployments.          |
| **compliance-sample-br_insurance_lgpd_anchor.yaml** | Brazil insurance sector: **skeleton** EN-header sample with generic insurance terms and LGPD-inventory **`norm_tag`** strings; **not** SUSEP/CNSP certification — see [COMPLIANCE_FRAMEWORKS.md](../COMPLIANCE_FRAMEWORKS.md#brazil-insurance-sector-lgpd-anchoring-prudential-references). |
| **compliance-sample-uk_gdpr.yaml**             | UK GDPR (UK post-Brexit + EU-like): norm_tag and recommendation overrides aligned with ICO and UK provisions.                                                       |
| **compliance-sample-eu_gdpr.yaml**             | EU GDPR (EEA): EU 2016/679 Art. 4(1), EDPB, member-state DPAs; optional EN + DE/FR terms.                                                                           |
| **compliance-sample-benelux.yaml**             | Benelux (BE, NL, LU): EU GDPR base + national IDs (BSN, NISS, Luxembourg ID) and national DPA overrides; EN + NL/FR terms.                                          |
| **compliance-sample-pipeda.yaml**              | PIPEDA (Canada, federal private sector): personal information, consent, and Canadian identifiers (e.g. SIN).                                                        |
| **compliance-sample-popia.yaml**               | POPIA (South Africa): responsible party, personal information, and SA identifiers.                                                                                  |
| **compliance-sample-appi.yaml**                | APPI (Japan): personal information and retained personal data; terms and overrides for PPC alignment.                                                               |
| **compliance-sample-pci_dss.yaml**             | PCI-DSS (payment card data): card/financial patterns and recommendation overrides for merchants and assessors.                                                      |
| **compliance-sample-philippines_dpa.yaml**     | Philippines DPA (RA 10173): NPC; personal information, sensitive personal information; EN.                                                                          |
| **compliance-sample-australia_privacy.yaml**   | Australia Privacy Act 1988: OAIC, APPs; personal information; TFN/Medicare regex; EN.                                                                               |
| **compliance-sample-singapore_pdpa.yaml**      | Singapore PDPA 2012: PDPC; personal data, DNC; NRIC regex; EN.                                                                                                      |
| **compliance-sample-uae_pdpl.yaml**            | UAE PDPL (Decree-Law 45/2021): UAE Data Office; personal/sensitive data; EN + optional AR terms.                                                                    |
| **compliance-sample-argentina_pdpa.yaml**      | Argentina Ley 25.326: DNPDP; datos personales; ES + EN terms; CUIT/CUIL/DNI regex.                                                                                  |
| **compliance-sample-kenya_dpa.yaml**           | Kenya Data Protection Act 2019: ODPC; personal data, data controller; EN.                                                                                           |
| **compliance-sample-india_dpdp.yaml**          | India DPDP Act 2023: DPBI; personal data, data fiduciary; Aadhaar/PAN regex; EN.                                                                                    |
| **compliance-sample-turkey_kvkk.yaml**         | Turkey KVKK (Law 6698): KVKK Board; kişisel veri; EN + TR terms; TC Kimlik regex.                                                                                   |
| **compliance-sample-new_zealand_privacy.yaml** | New Zealand Privacy Act 2020: OPC; personal information, IPPs; EN.                                                                                                  |
| **compliance-sample-russia_152_fz.yaml**       | Russia Federal Law 152-FZ: Roskomnadzor; personal data operator; EN + RU terms; SNILS regex and heuristic INN (high FP risk—see file header); **revalidate often**. |
| **compliance-sample-saudi_pdpl.yaml**          | Saudi PDPL (Royal Decree M/19): SDAIA; personal/sensitive data; EN.                                                                                                 |
| **compliance-sample-israel_ppl.yaml**          | Israel Privacy Protection Law: PPA; personal information, database registrar; EN.                                                                                   |
| **compliance-sample-colombia_1581.yaml**       | Colombia Ley 1581/2012: SIC; datos personales; ES + EN terms; CC/NIT regex.                                                                                         |
| **compliance-sample-chile_privacy.yaml**       | Chile Law 19.628: datos personales; ES + EN terms; RUT regex.                                                                                                       |
| **compliance-sample-nigeria_ndpr.yaml**        | Nigeria NDPR 2019: NITDA; personal data, data controller; EN.                                                                                                       |
| **compliance-sample-morocco_09_08.yaml**       | Morocco Law 09-08: CNDP; données à caractère personnel; FR + EN terms; CIN regex.                                                                                   |
| **compliance-sample-switzerland_fadp.yaml**    | Switzerland revised FADP: FDPIC; personal data; EN + optional DE/FR/IT terms; AHV/UID regex.                                                                        |
| **compliance-sample-us_ftc_coppa.yaml**        | U.S. FTC COPPA (children's online privacy): **technical mapping** terms and overrides; not age verification or legal advice.                                        |
| **compliance-sample-us_ca_ab2273_caadca.yaml** | California AB 2273 (Age-Appropriate Design Code): **labelling** for voluntary scoping; applicability requires counsel.                                              |
| **compliance-sample-us_co_cpa_minors.yaml**    | Colorado Privacy Act — minors / under-18 contexts: **technical** norm tags; does not establish “known minor” legally.                                               |
| **compliance-sample-us_va_vcdpa.yaml**         | Virginia VCDPA: sensitive-category terms; **precision geolocation** regexes (4+ decimals + keyword/JSON shape); B2B/employment scope **not** auto-classified — see file header. |
| **compliance-sample-us_fcpa_internal_policy_pack.yaml** | U.S. **FCPA** + employer **anti-corruption policy** lexicon (**inventory**); not bribery detection or legal advice.                                               |

All samples in the tables above are available. Each sample is self-contained (regex overrides, ML terms, recommendation overrides) so you can enable one framework by including that file's blocks in your config. For the **full regional table**, filenames, and how to merge samples into `config.yaml`, see [COMPLIANCE_FRAMEWORKS.md](../COMPLIANCE_FRAMEWORKS.md#compliance-samples) ([pt-BR](../COMPLIANCE_FRAMEWORKS.pt_BR.md#amostras-de-conformidade)).

### Sample maintenance

**All** compliance samples are **technical starting points**, not a substitute for legal review. Even when a statute is stable, **regulator guidance**, **court and DPA interpretations**, **sector rules** (e.g. PCI-DSS revisions), **identifier formats** in real data, and **rewording or consolidation of official legal text** drift—so regexes, ML terms, and `recommendation_overrides` deserve **periodic review** for any framework you rely on (e.g. **before a minor release** or on a **quarterly** cadence for high-risk profiles).

**Especially fast-moving** among the regulations we already sample: **U.S. state** privacy laws and minors-related bills (e.g. California, Colorado); **EU / UK** (ongoing legislative and guidance churn, including EDPB and ICO materials); **India DPDP** (new Act, rules and authority practice still settling); **Middle East PDPLs** (UAE, Saudi); and **Russia 152-FZ** (frequent statutory and secondary changes—see the header comment in `compliance-sample-russia_152_fz.yaml` as an example of documenting that risk in-file). **Revalidate with counsel** when your facts or the legal baseline change.

### Language and target audience

When choosing or authoring a sample, consider the **language(s)** of the target region so column names and labels in data are detected:

| Regulation / region               | Recommended language(s) for terms and labels                                                                   |
| -------------------               | ---------------------------------------------                                                                  |
| **LGPD (Brazil)**                 | Portuguese (BR) and English (e.g. "documento oficial" and "official document", "CNH" and "Driver License").    |
| **Brazil (insurance — LGPD skeleton)** | Portuguese (BR) and English for policy/claims/brokerage column names; merge with full LGPD sample for national IDs. |
| **PIPEDA (Canada)**               | English and French (e.g. "personal information" and "renseignements personnels") where scanning Canadian data. |
| **UK GDPR**                       | English.                                                                                                       |
| **EU GDPR (EEA)**                 | English; optional German/French for multilingual EU data.                                                      |
| **Benelux (BE, NL, LU)**          | English plus Dutch and/or French (e.g. BSN, NISS, national ID column names).                                   |
| **POPIA (South Africa)**          | English; add local languages in terms if your data uses them.                                                  |
| **APPI (Japan)**                  | Japanese and/or English as needed for column names.                                                            |
| **PCI-DSS**                       | English.                                                                                                       |
| **Philippines (DPA)**             | English.                                                                                                       |
| **Australia / NZ**                | English.                                                                                                       |
| **Singapore (PDPA)**              | English.                                                                                                       |
| **UAE / Saudi (PDPL)**            | English; optional Arabic for column names.                                                                     |
| **Argentina / Colombia / Chile**  | Spanish and English (e.g. datos personales / personal data).                                                   |
| **Kenya / Nigeria**               | English.                                                                                                       |
| **Morocco**                       | French and/or Arabic as relevant.                                                                              |
| **India (DPDP)**                  | English.                                                                                                       |
| **Turkey (KVKK)**                 | Turkish and English (e.g. kişisel veri / personal data).                                                       |
| **Russia (152-FZ)**               | Russian and English (e.g. персональные данные / personal data); revalidate terms when regulations are amended. |
| **Switzerland (FADP)**            | English; optional DE/FR/IT.                                                                                    |
| **U.S. (COPPA, AB 2273, CO CPA, VCDPA)** | English (column names and privacy programs in U.S. deployments).                                               |

Document in the sample header or in [COMPLIANCE_FRAMEWORKS](../COMPLIANCE_FRAMEWORKS.md) when a sample includes multi-language terms. See also the rule **.cursor/rules/compliance-samples-language.mdc**.

**For authors:** Use **double-quoted** YAML for regex `pattern` values with **escaped backslashes** (e.g. `pattern: "\\b[A-Z]{2}\\s?\\d{6}\\s?[A-D]\\b"`). This avoids "Invalid escape sequence" linter errors and loads correctly; the value passed to the regex engine is `\b`, `\s`, `\d` as intended. Do not use single-quoted or unescaped `\d`/`\s` in double quotes. Tests in `tests/test_compliance_samples.py` validate structure and that the detector loads each sample.

**Encoding:** Save sample files in **UTF-8** so multilingual terms (e.g. Japanese, Arabic, French, **Russian Cyrillic**) are handled correctly. The main config file is read with auto-detection (UTF-8, UTF-8-sig, cp1252, latin_1). Pattern files use the config key **`pattern_files_encoding`** (default `utf-8`); set it to `cp1252` or `latin_1` only if your environment uses legacy encodings. Scanned **data** is handled as **Unicode** in the pipeline (Latin, Cyrillic, CJK, Arabic script, etc.); **sniffing and heuristics** can be tuned per deployment—see [COMPLIANCE_FRAMEWORKS.md](../COMPLIANCE_FRAMEWORKS.md#multi-language-multi-encoding-and-multi-regional-operation) (EN) / [pt-BR](../COMPLIANCE_FRAMEWORKS.pt_BR.md#operação-multilíngue-multi-encoding-e-multirregional). **Dashboard UI and full doc translations** in many locales are **roadmapped**, not all shipped yet—high-level direction is in the **Roadmap — internationalization** paragraph in the repository **[README.md](../../README.md)**. Step-by-step encoding keys: [USAGE.md](../USAGE.md#file-encoding-config-and-pattern-files) (EN) / [USAGE.pt_BR.md](../USAGE.pt_BR.md#file-encoding-config-and-pattern-files) (pt-BR).
