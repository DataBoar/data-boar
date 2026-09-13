# Primer: Global privacy regulations (PIPEDA, POPIA, APPI, Vietnam PDPD, FELCA)

<!-- plans-hub-summary: Primer regulações globais de privacidade — PIPEDA / POPIA / APPI / Vietnam PDPD / FELCA -->

<!-- plans-hub-related: PRIVACY_MANAGEMENT_STANDARDS_PRIMER.md, completed/PLAN_ADDITIONAL_COMPLIANCE_SAMPLES.md, completed/PLAN_COMPLIANCE_STANDARDS_ALIGNMENT.md -->

**Audience:** Compliance teams in multinationals; DPOs at exporters; partners who need **inventory language** across Canada, South Africa, Japan, Vietnam, and Brazil (minors / digital platforms).

**Product stance:** Data Boar is a **technical evidence and inventory** layer ([ADR-0025](../adr/ADR-0025-compliance-positioning-evidence-inventory-not-legal-conclusion-engine.md)). This primer does **not** certify PIPEDA, POPIA, APPI, PDPD, or FELCA. It does **not** decide notification, retention calendars, or whether a cross-border transfer is lawful.

**Related:** [COMPLIANCE_FRAMEWORKS.md](../COMPLIANCE_FRAMEWORKS.md) (how to attach samples) · [compliance-samples/README.md](../compliance-samples/README.md) · [PRIVACY_MANAGEMENT_STANDARDS_PRIMER.md](PRIVACY_MANAGEMENT_STANDARDS_PRIMER.md) (ISO 27701 / NIST PF) · [PITCH_DPO.md](../pitch/PITCH_DPO.md)

**Issue context:** GitHub **[#600](https://github.com/DataBoar/data-boar/issues/600)** asked for this narrative because Tier-2 jurisdictions had **samples without a primer**. The issue table that said PIPEDA / POPIA / APPI had “no sample yet” is **stale relative to `main`**. Coverage below is **what is on disk now**, not that 2026-05 issue snapshot.

Vietnam **PDPD** YAML (and Brazil **FELCA** YAML) from **[#477](https://github.com/DataBoar/data-boar/issues/477)** remain the **shape baseline**: header disclaimers, `norm_tag`, regex + ML terms, `recommendation_overrides`, pair-with notes. This primer does **not** recreate those files.

---

## Honest coverage status (tree, not aspiration)

| Regulation | Jurisdiction | `compliance-sample-*.yaml` | Built-in `DEFAULT_PATTERNS` | This primer | Typical gap |
| ---------- | ------------ | --------------------------- | ---------------------------- | ----------- | ----------- |
| **PIPEDA** | Canada (federal private sector) | **Yes** — [compliance-sample-pipeda.yaml](../compliance-samples/compliance-sample-pipeda.yaml) | **No** (profile / overrides) | This file | Does not evaluate consent, OPC findings, or provincial overlay by itself |
| **Quebec Law 25** (related, not in #600 list) | Quebec private sector | **Yes** — [compliance-sample-canada_qc_law25.yaml](../compliance-samples/compliance-sample-canada_qc_law25.yaml) | **No** | Pointer only | Complements PIPEDA for QC; still inventory, not CAI determination |
| **POPIA** | South Africa | **Yes** — [compliance-sample-popia.yaml](../compliance-samples/compliance-sample-popia.yaml) | **No** | This file | Does not apply s.72 transfer tests or Information Regulator exemptions |
| **APPI** (2022 revision) | Japan | **Yes** — [compliance-sample-appi.yaml](../compliance-samples/compliance-sample-appi.yaml) | **No** | This file | Does not classify purpose of use or 2022 cross-border conditions |
| **Vietnam PDPD** (Decree 13/2023) | Vietnam | **Yes** — [compliance-sample-vietnam_pdpd.yaml](../compliance-samples/compliance-sample-vietnam_pdpd.yaml) (**#477**) | **No** | This file | Does not file with Bộ Công an / MPS |
| **FELCA** (Lei 15.211/2025) | **Brazil** (not Vietnam) | **Yes** — [compliance-sample-brazil_felca.yaml](../compliance-samples/compliance-sample-brazil_felca.yaml) (**#477**) | **No** | This file | **Not** age verification; pair with [LGPD sample](../compliance-samples/compliance-sample-lgpd.yaml) |

Issue #600 listed FELCA under Vietnam. On disk, FELCA is the **Brazilian** digital statute for children and adolescents; Vietnam coverage is **PDPD** only.

---

## PIPEDA (Canada)

**Jurisdiction / in force:** Federal **Personal Information Protection and Electronic Documents Act** for most private-sector organisations in Canada (in force in stages from **2001**). Oversight: [Office of the Privacy Commissioner of Canada (OPC)](https://www.priv.gc.ca/). Provincial private-sector laws (e.g. Quebec **Law 25**) can apply **instead of or in addition to** PIPEDA depending on the organisation — **counsel decides**. Do **not** treat cancelled federal reform bills as in force.

**Protected categories (map to detection):** PIPEDA s. 2 “personal information” is broad. The sample tags **SIN** shapes, **precise geolocation** (same four-decimal geometry as EU GDPR / VCDPA samples), and **EN+FR** ML terms (`personal information` / `renseignements personnels`, consent vocabulary). Built-in email/phone/name detectors still apply when the engine’s core patterns run; the sample adds **Canadian identifiers and bilingual labels**.

**Main duties (organisational — not product features):** accountability, identifying purposes, consent, limiting collection/use/retention/disclosure, accuracy, safeguards, openness, individual access, challenging compliance. **Breach reporting** to OPC / individuals is an organisational workflow. Data Boar can **locate copies** and support a **`--diff`** after cleanup; it does **not** start the 72-hour-style clock or draft the notice.

**Coverage:** Sample **exists**. Optional [jurisdiction hints](../USAGE.md) may mention Canadian-framed tags when metadata matches — **heuristic**, not OPC advice ([ADR 0026](../adr/ADR-0026-optional-jurisdiction-hints-dpo-facing-heuristic-metadata-only.md)).

**Commercial relevance:** Default profile for **Canada-facing** private-sector inventory (EN+FR reports). Pair Law 25 when the buyer is Quebec-private-sector heavy.

---

## POPIA (South Africa)

**Jurisdiction / in force:** **Protection of Personal Information Act 4 of 2013**. Information Regulator: commencement of core conditions **1 July 2020**; remaining provisions **1 July 2021** (sample header). Authority: [Information Regulator (South Africa)](https://inforegulator.org.za/).

**Protected categories:** “Personal information” (s.1), including location data that identifies a person; **special personal information** (s.26); **children’s** information (s.34). Sample: **SA ID** (13-digit / spaced), geolocation geometry, EN terms, `norm_tag` **POPIA**.

**Main duties:** eight conditions for lawful processing; operator vs responsible party; **security compromises** notification; **s.72** cross-border restrictions. The scanner **does not** decide adequacy, Binding Corporate Rules, or consent to transfer.

**Coverage:** Sample **exists**. No POPIA-specific connector. Same inventory motor as LGPD/GDPR profiles.

**Commercial relevance:** English-language African private-sector and pan-African programmes that already speak GDPR-like vocabulary (“responsible party” ≈ controller).

---

## APPI (Japan — 2022 revision)

**Jurisdiction / in force:** **Act on the Protection of Personal Information** (個人情報の保護に関する法律). Last major revision **effective April 2022**. Authority: [Personal Information Protection Commission (PPC)](https://www.ppc.go.jp/en/).

**Protected categories:** personal information (個人情報), sensitive personal information requiring care (要配慮個人情報), retained personal data (保有個人データ). Sample: **My Number** (12-digit), Japanese **postal** shapes, geolocation (位置情報), **EN + Japanese** terms.

**Main duties:** specify purpose of use; consent for sensitive categories; individual rights on retained personal data; **2022** extra rules on **cross-border** provision (Art. 24 in sample notes). Data Boar **does not** classify purpose or apply transfer conditions.

**Coverage:** Sample **exists**. APPI may appear in optional jurisdiction-hint copy when tags match.

**Commercial relevance:** APAC handlers and exporters storing Japanese identifiers (My Number, kana/kanji column names).

---

## Vietnam PDPD (Decree 13/2023) — baseline sample (#477)

**Jurisdiction / in force:** **Nghị định 13/2023/NĐ-CP**; sample header: **1 July 2024** (transitional period ended). Authority framing: Ministry of Public Security / cybersecurity department (see YAML header — not reproduced here as legal text).

**Protected categories:** personal data and **sensitive** classes in the decree (IDs, social insurance, precise location, etc.). Sample: **CCCD** (12-digit), legacy **CMND** (9-digit), passport/phone/tax/BHXH shapes, geolocation, **EN + Vietnamese** terms. **High collision risk** on short numeric IDs — treat as **inventory signals**, same as other national-ID samples.

**Main duties:** extra-territorial collection of data of individuals in Vietnam (sample note); localisation / transfer / impact assessment are **organisational**. Product: discovery + `norm_tag` **Vietnam PDPD Art. …** labels for report text.

**Coverage:** Sample **exists** (**#477**). **Use this file as the template** when adding another jurisdiction YAML (header + pair-with + `recommendation_overrides`).

**Commercial relevance:** Vietnam operations and APAC shared-services centres; pair with Singapore PDPA or EU GDPR samples for multi-hub estates ([compliance-samples README](../compliance-samples/README.md)).

---

## FELCA (Brazil — Lei 15.211/2025) — same #477 drop as PDPD

**Jurisdiction / in force:** **Estatuto Digital da Criança e do Adolescente**; sample header: **17 March 2026**. Authority: **ANPD**. Official text: seek **Planalto** / official gazette — do not copy articles here.

**Protected categories:** fields that **may** relate to minors and guardians (DOB/age labels, parental consent columns, school enrollment, child profiles). Pair with **LGPD** for general Brazilian PII.

**Main duties:** platform obligations toward children/adolescents (consent of responsible person, etc.) are **not** implemented as product workflows. [MINOR_DETECTION.md](../MINOR_DETECTION.md) is the engine lane; FELCA YAML is **lexicon + tags**.

**Coverage:** Sample **exists** (**#477**). Gap: **no** age-gating, parental OTP, or “this account is a child” classifier beyond heuristics.

**Commercial relevance:** Brazilian EdTech / social / games with under-18 users; always **LGPD + FELCA**, not FELCA alone.

---

## What Data Boar never maps from this primer

| Obligation | Product |
| ---------- | ------- |
| Breach / security-compromise **notification** | Locate stores; **you** notify |
| **Retention** schedules | `--diff` after deletion; no calendar engine |
| **International transfer** legal test | Inventory of copies that *might* be in-scope; no adequacy engine |
| **Consent** capture | Not a consent log (`--export-audit-trail` is scan/session evidence) |

---

## Anti-overclaim checklist

1. Cite the **YAML path** actually merged into the customer config.
2. State that **DEFAULT_PATTERNS** still centre on LGPD / GDPR / CCPA / HIPAA / GLBA unless overrides are loaded.
3. Do not claim a **sample that is not in** `docs/compliance-samples/` (this file’s table is the check).
4. Do not call FELCA a Vietnam law.
5. Run **`--validate-config`** before production scans ([USAGE.md](../USAGE.md)).

---

## Maintainer

When a new jurisdiction YAML ships, add a **status-table row** here and a line in [COMPLIANCE_FRAMEWORKS.md](../COMPLIANCE_FRAMEWORKS.md) (product index — **do not** link that page back into `docs/plans/`). After editing the hub summary, run `python scripts/plans_hub_sync.py --write` (indexes `PLAN_*.md` only; this primer is listed in [PRIMERS_HUB.md](PRIMERS_HUB.md)).
