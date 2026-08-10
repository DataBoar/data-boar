# Compliance-related technical reference (IT, security, integration)

**Português (Brasil):** [COMPLIANCE_TECHNICAL_REFERENCE.pt_BR.md](COMPLIANCE_TECHNICAL_REFERENCE.pt_BR.md)

**Audience:** Teams **integrating or operating** Data Boar in security, infrastructure, or compliance engineering roles. For a **non-technical** summary aimed at **legal, compliance leadership, and DPOs**, see [COMPLIANCE_AND_LEGAL.md](COMPLIANCE_AND_LEGAL.md).

This document holds details that used to clutter the legal/compliance summary: validation, encodings, API limits, timeouts, and where to automate scans.

**POC vocabulary (technical / deck use):** **Data Sniffing** names the discovery and sampling pass; **Deep Boring** names the structured Excel / report depth—see [GLOSSARY.md](GLOSSARY.md#1-product-identity--data-landscape) and [COMPLIANCE_FRAMEWORKS.md](COMPLIANCE_FRAMEWORKS.md#engine-vocabulary-poc-decks-and-technical-docs). The root [README](../README.md) decision-maker section stays in plainer language and does **not** require these labels.

---

## Security controls that support compliance programs

- **Input validation** (e.g. tenant/technician fields where applicable).
- **API request body size limits** to reduce abuse risk.
- **Logging policy:** API keys, passwords, and connection strings must not appear in logs.

Authoritative policy and hardening notes: [SECURITY.md](SECURITY.md) ([pt-BR](SECURITY.pt_BR.md)).

---

## Character encodings and multilingual configs

Configuration and pattern files support **UTF-8** (recommended), **UTF-8 with BOM**, and **legacy encodings** (e.g. Windows ANSI, Latin-1); the main config file is read with **auto-detection** where applicable. Terms and report language can follow regional needs (e.g. EN+FR for Canada, PT-BR+EN for Brazil, **EN+RU for Russia 152-FZ** samples).

**Unicode in scanned data:** Findings and Excel output treat text as **Unicode**—**Latin**, **Cyrillic**, **CJK** (e.g. Japanese), **Arabic script**, and mixed corpora are in scope at the character level. **Byte-level decoding** of sources depends on connectors and file formats; **sniffing and heuristics** can be **tuned** per deployment. **Operator dashboard UI** and **full documentation** in many additional human languages are **not** all shipped yet; direction is **roadmapped** (short- to mid-term) with **en** + **pt-BR** first—see [COMPLIANCE_FRAMEWORKS.md](COMPLIANCE_FRAMEWORKS.md#multi-language-multi-encoding-and-multi-regional-operation) and the **Roadmap — internationalization and regional depth** paragraph in the repository **[README.md](../README.md)**. **Compliance YAML samples** must be **re-reviewed periodically** as regulations and wording change—see [compliance-samples/README.md](compliance-samples/README.md#sample-maintenance).

**Policy (anti-overclaim):** “Any encoding” means **operator-tunable** config and Unicode-aware detection where implemented—not a guarantee that every connector decodes every on-disk or wire representation the same way, nor that the engine performs **universal mojibake repair** or NFC/homoglyph normalisation on all paths. Treat residual decode ambiguity as a **coverage limitation** (document or surface via `scan_failures` / connector behaviour), not as “clean.”

Step-by-step: [USAGE.md — File encoding, config, and pattern files](USAGE.md#file-encoding-config-and-pattern-files) ([pt-BR](USAGE.pt_BR.md)).

---

## Performance and resilience

**Configurable timeouts** (global and per **target**) so one slow data source does not block the entire run. See [USAGE.md](USAGE.md) and [TECH_GUIDE.md](TECH_GUIDE.md) for keys and behaviour.

---

## Recurring / automated scans

**Schedulable** runs via the **internal API** support continuous or periodic compliance monitoring; **Excel reports** and **heatmaps** per session are part of the **audit trail**. API and dashboard paths: [USAGE.md](USAGE.md), [TECH_GUIDE.md](TECH_GUIDE.md).

---

## Optional notifications (webhooks)

Off-band, after a scan **completes**, the app can send a **short summary** (Slack, Teams, generic webhook / Signal bridge, or legacy Telegram fields), including **multiple operator channels** and an optional **tenant copy** when configured — **disabled by default**; treat URLs and tokens as **secrets**. Maintainer channel policy: [OPERATOR_NOTIFICATION_CHANNELS.md](ops/OPERATOR_NOTIFICATION_CHANNELS.md). This does not replace Excel reports or TLS/network policy. See [USAGE.md — Operator notifications](USAGE.md#51-operator-notifications-optional) and [SECURITY.md](SECURITY.md).

---

## Related documents

| Topic                                        | Document                                                                   |
| -----                                        | --------                                                                   |
| Legal / compliance summary (decision-makers) | [COMPLIANCE_AND_LEGAL.md](COMPLIANCE_AND_LEGAL.md)                         |
| Methodology (discovery, risk, ROPA-style)    | [COMPLIANCE_METHODOLOGY.md](COMPLIANCE_METHODOLOGY.md)                     |
| Frameworks, samples, YAML profiles           | [COMPLIANCE_FRAMEWORKS.md](COMPLIANCE_FRAMEWORKS.md)                       |
| Full config schema, credentials, CLI         | [USAGE.md](USAGE.md)                                                       |
| Connectors, architecture, deploy             | [TECH_GUIDE.md](TECH_GUIDE.md)                                             |
| Detection patterns, ML/DL                    | [SENSITIVITY_DETECTION.md](SENSITIVITY_DETECTION.md)                       |

Full index: [README.md](README.md) · [README.pt_BR.md](README.pt_BR.md).
