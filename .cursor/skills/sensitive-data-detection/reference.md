# Reference: Regulatory Norms and Pattern–Norm Mapping

Use this when you need exact legal definitions or to map detection patterns to articles of law.

---

## LGPD (Lei Geral de Proteção de Dados – Brazil)

## Law 13.709/2018

### Personal data (Art. 5, I)

> Dado pessoal: informação relacionada a uma pessoa natural identificada ou identificável.

Examples: name, CPF, RG, email, phone, address, IP, cookie identifiers, etc.
**Patterns**: CPF, CNPJ (when linked to natural person), email, phone, full name, birth date, identifiers in logs.

### Sensitive personal data (Art. 5, II)

> Dado pessoal sensível: dado pessoal sobre origem racial ou étnica, convicção religiosa, opinião política, filiação a sindicato ou a organização de caráter religioso, filosófico ou político, dado referente à saúde ou à vida sexual, dado genético ou biométrico, quando vinculado a uma pessoa natural.

Examples: health records, biometrics, religion, political opinion, union membership, sexual orientation, genetic data.
**Patterns**: No single regex; use ML on column names/labels (e.g. “saúde”, “biometria”, “religião”, “CRM”, “prontuário”) and content policies.

### Anonymized data (Art. 5, III)

> Dado anonimizado: dado relativo a titular que não possa ser identificado, considerando a utilização de meios técnicos razoáveis e disponíveis na ocasião de seu tratamento.

Aggregates, statistics, or irreversibly anonymized data are not “personal data” under LGPD. Tag as “anonymous/aggregate” when appropriate.

---

## GDPR (General Data Protection Regulation – EU)

## Regulation (EU) 2016/679

### Personal data (Art. 4(1))

> Any information relating to an identified or identifiable natural person (‘data subject’).

Same conceptual scope as LGPD: identifiers, location, online identifier, factors specific to physical, physiological, genetic, mental, economic, cultural or social identity.
**Patterns**: Email, phone (E.164 or national), name, DOB, national ID, IP, device ID, etc.

### Special categories (Art. 9) – sensitive

> Racial or ethnic origin, political opinions, religious or philosophical beliefs, trade union membership, genetic data, biometric data, health, sex life or sexual orientation.

Map to “sensitive” category; same ML/context approach as LGPD sensitive data.

---

## CCPA/CPRA (California)

## California Consumer Privacy Act (as amended by CPRA)

“Personal information” is broadly defined (identifiers, commercial information, biometric, geolocation, etc.).
**Patterns**: Same as above; include “consumer”, “household”, “device” identifiers where relevant.

---

## Pattern–Norm Quick Map

| Pattern / context        | LGPD             | GDPR         | Typical category     |
| ------------------------ | ---------------- | ------------ | -------------------- |
| CPF, RG                  | Art. 5 I         | Art. 4(1)    | Personal             |
| Email, phone, name       | Art. 5 I         | Art. 4(1)    | Personal             |
| Birth date, address      | Art. 5 I         | Art. 4(1)    | Personal             |
| Health, biometrics       | Art. 5 II        | Art. 9       | Sensitive            |
| Religion, political      | Art. 5 II        | Art. 9       | Sensitive            |
| Genetic, sexual          | Art. 5 II        | Art. 9       | Sensitive            |
| Anonymous/aggregate      | Art. 5 III       | Rec. 26      | Non-personal         |

---

## Implementation Notes

- **Laws change.** Treat article numbers and definitions as reference; for production compliance, confirm against current official text.
- **Context matters.** A CNPJ can be “personal” (sole proprietor) or “non-personal” (company only); tag with category and let policy rules decide.
- **Minimize false positives.** Prefer high-precision regex (with validation where applicable) and thresholded ML scores; document confidence in reports.
