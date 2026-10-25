# Plan: ML/DL detection of additional sensitive categories

## Goal

Configure the application (with **examples**) so that **ML and DL** can detect other important **sensitive personal data** categories, such as:

- **CID/ICD** (medical diagnosis codes, e.g. CID-10, ICD-10)
- **Gender**
- **Religion / religious affiliation**
- **Political affiliation**
- **Politically exposed person (PEP)**
- **Race / skin color / ethnic origin**
- **Workers union affiliation**
- **Genetic data**
- **Biometric data**
- **Sex life / sexual orientation**
- Related terms (e.g. health condition, disability, union membership)

These categories are often **sensitive personal data** under LGPD (Art. 5 II, 11), GDPR (Art. 4(15), 9), and similar laws, and should be surfaced for the DPO, security, and compliance teams.

## Principles (non-destructive, no regression)

- **Configuration-driven:** Use existing `ml_patterns_file` / `dl_patterns_file` and `sensitivity_detection.ml_terms` / `sensitivity_detection.dl_terms`. No change to detector logic beyond using the terms you provide.
- **Examples first:** Provide ready-to-use YAML examples (EN and PT-BR oriented) so users can copy or merge into their config.
- **Optional:** Users who do not add these terms keep current behaviour; adding terms is additive.
- **Tests:** Any new built-in or example terms should be covered by tests; existing tests must still pass.

---

## Sensitive categories and example terms

Use these as **text** in your ML/DL training terms with **label: sensitive**. You can add them to a file and set `ml_patterns_file` / `dl_patterns_file`, or put them under `sensitivity_detection.ml_terms` / `sensitivity_detection.dl_terms` in your config.

| Category                   | Example terms (EN / PT-BR)                                                                                              |
| ---                        | ---                                                                                                                     |
| **CID/ICD (diagnosis)**    | cid, icd, diagnosis code, medical code, disease classification, código de doença, CID-10, ICD-10, diagnóstico médico    |
| **Gender**                 | gender, sex, sexo, gênero, identidade de gênero, gender identity                                                        |
| **Religion**               | religion, religious affiliation, religião, filiação religiosa, creed, crença                                            |
| **Political**              | political affiliation, political opinion, filiação política, opinião política, partido, party affiliation               |
| **PEP**                    | politically exposed person, PEP, pessoa politicamente exposta, PEP list, cargo político                                 |
| **Race / skin color**      | race, ethnic origin, skin color, cor da pele, raça, origem étnica, ethnicity, etnia                                     |
| **Union**                  | union affiliation, workers union, sindicato, filiação sindical, trade union, labor union                                |
| **Genetic**                | genetic data, genetic information, dados genéticos, DNA, genetic test, teste genético                                   |
| **Biometric**              | biometric data, fingerprint, facial recognition, biometria, impressão digital, reconhecimento facial, iris, voice print |
| **Sex life / orientation** | sex life, sexual orientation, orientação sexual, vida sexual, intimate data, dados íntimos                              |
| **Health / disability**    | health condition, disability, deficiência, condição de saúde, medical condition, chronic disease, doença crônica        |

You can also add **non_sensitive** counter-examples (e.g. "department" without "political", "employee_id" without "union") to reduce false positives.

---

## Example configuration (YAML)

See **[sensitivity_terms_sensitive_categories.example.yaml](sensitivity_terms_sensitive_categories.example.yaml)** for a full list of terms you can copy into your `ml_patterns_file` / `dl_patterns_file` or into `sensitivity_detection.ml_terms` / `sensitivity_detection.dl_terms`.

## Inline in config.yaml:

```yaml
sensitivity_detection:
  ml_terms:

    - { text: "cid", label: sensitive }
    - { text: "icd", label: sensitive }
    - { text: "gender", label: sensitive }
    - { text: "religion", label: sensitive }
    - { text: "political affiliation", label: sensitive }
    - { text: "politically exposed person", label: sensitive }
    - { text: "race", label: sensitive }
    - { text: "skin color", label: sensitive }
    - { text: "union affiliation", label: sensitive }
    - { text: "genetic data", label: sensitive }
    - { text: "biometric data", label: sensitive }
    - { text: "sexual orientation", label: sensitive }

    # ... (see example file for full list)
  dl_terms:
    # Same or subset for DL (sentence embeddings work well with phrases)
    - { text: "religious affiliation", label: sensitive }
    - { text: "political opinion", label: sensitive }
    - { text: "genetic information", label: sensitive }

```

## Using a file:

```yaml
ml_patterns_file: config/sensitivity_terms_sensitive_categories.yaml
dl_patterns_file: config/sensitivity_terms_sensitive_categories.yaml
```

---

## Reporting (norm_tag and recommendation_overrides)

When the detector classifies a column as sensitive based on these terms, it will use **pattern_detected** (e.g. ML_DETECTED) and **norm_tag** (e.g. LGPD/GDPR/CCPA context). To give DPO/compliance clearer labels per category, you can:

1. **regex_overrides_file:** Add patterns for specific codes (e.g. CID-10 code format) with a **norm_tag** like "LGPD Art. 5 II – health" or "GDPR Art. 9 – health data".
1. **report.recommendation_overrides:** Add entries for norm_tag patterns so the Recommendations sheet shows the right "Base legal" and "Relevante para" for health, religion, political, etc.

## Example recommendation_overrides for these categories:

```yaml
report:
  recommendation_overrides:

    - norm_tag_pattern: "health"

      base_legal: "LGPD Art. 5 II, 11 – dado de saúde; GDPR Art. 9"
      risk: "Dados de saúde ou condição médica; tratamento especial e base legal específica."
      recommendation: "Garantir base legal e consentimento; restringir acesso; considerar anonimização."
      priority: "CRÍTICA"
      relevant_for: "DPO, Compliance, Área de Saúde"

    - norm_tag_pattern: "religious"

      base_legal: "LGPD Art. 5 II, 11 – convicção religiosa; GDPR Art. 9"
      risk: "Dado sensível; discriminação e tratamento diferenciado."
      recommendation: "Minimização; base legal e consentimento explícito; acesso restrito."
      priority: "CRÍTICA"
      relevant_for: "DPO, Compliance, RH"
```

---

## Sequential to-dos

| #   | To-do                                                                                                                                                                                                                                           | Status |
| --- | ---                                                                                                                                                                                                                                             | ---    |
| 1   | **Example file:** Create `sensitivity_terms_sensitive_categories.example.yaml` with terms for CID/ICD, gender, religion, political, PEP, race, union, genetic, biometric, sex life, health/disability (EN and PT-BR oriented).                  | ✅ Done |
| 2   | **Documentation:** In `SENSITIVITY_DETECTION.md` (EN), add a section "Sensitive categories (health, religion, political, etc.)" with link to this plan and to the example file; list categories and example terms in a table.                   | ✅ Done |
| 3   | **Documentation PT-BR:** In `SENSITIVITY_DETECTION.pt_BR.md`, add the same section in Portuguese with link to the example file and plan.                                                                                                        | ✅ Done |
| 4   | **Built-in defaults (optional):** Consider adding a subset of these terms to `DEFAULT_ML_TERMS` in `core/detector.py` so out-of-the-box detection includes e.g. religion, political, gender, biometric, genetic. Keep additive and documented.  | ✅ Done |
| 5   | **Recommendation overrides example:** Add an example in USAGE or in this plan for `recommendation_overrides` covering health, religion, political, PEP, race, union, genetic, biometric, sex life (Base legal, Risk, Recommendation, Priority). | ✅ Done |
| 6   | **Tests:** Add a test that, when ML terms include e.g. "religion" and "political affiliation", columns/samples containing those terms are classified as sensitive (HIGH or appropriate level); existing tests still pass.                       | ✅ Done |

---

## References

- LGPD Art. 5 (personal data), Art. 5 II, 11 (sensitive personal data).
- GDPR Art. 4(15), Art. 9 (special categories).
- Existing: [SENSITIVITY_DETECTION.md](SENSITIVITY_DETECTION.md), [sensitivity_terms.example.yaml](sensitivity_terms.example.yaml), `core/detector.py` (DEFAULT_ML_TERMS, ml_terms from file or config).
