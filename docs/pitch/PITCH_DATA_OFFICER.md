# Data Officer pitch — CDO, stewards, and senior data engineers

**Português (Brasil):** [PITCH_DATA_OFFICER.pt_BR.md](PITCH_DATA_OFFICER.pt_BR.md) · **Index:** [INDEX.md](INDEX.md)

**Audience:** Chief Data Officers (CDO), Data Stewards, and senior data engineers who work in DAMA-DMBOK language (lifecycle, quality, stewardship)—not primarily legal counsel or board procurement.

---

## The problem this audience already has

You cannot govern data you have not inventoried. A data-governance programme (GGD / DAMA-DMBOK) that starts from policies and models **without** a current map of **where personal and sensitive data actually live** produces plans that auditors and engineers cannot execute.

The question is not “do we have a policy?” It is “where is the sensitive data, and can we show an auditor what we found?”

Vocabulary: [GLOSSARY.md](../GLOSSARY.md) §12 (DMBOK, Data Steward, data quality).

## What Data Boar is in that programme

A **maturity-assessment instrument for sensitive data already in the estate**—step 0 before a grounded GGD plan. It locates and classifies **possible** personal and sensitive exposure (files, databases, shares, application exports) and emits **session-bound evidence** (findings, heatmap, Audit Trail).

- **It is:** technical discovery, inventory support, repeatable evidence for stewards and engineers.
- **It is not:** a data-catalog replacement, a quality-firehose, legal advice, or a substitute for Data Owner decisions.

Full leadership brief (if you need the board slide): [DECISION_MAKER_VALUE_BRIEF.md](../DECISION_MAKER_VALUE_BRIEF.md).

```mermaid
flowchart LR
    D["Demand: implement GGD"]
    D --> B["Diagnose first"]
    B --> DB["Data Boar: inventory, maturity, existing PII surface"]
    DB --> P["Plan aligned to what is actually there"]
```

## Lifecycle where discovery is critical

DAMA-DMBOK organises many functions. Two stages are where **unknown sensitive data** most often breaks a programme:

| Stage | Why discovery matters |
| ----- | --------------------- |
| **Store** | Data sits in files, RDBMS, NoSQL, object stores, and backups—often outside the catalog the steward maintains. |
| **Use** | Exports, reports, notebooks, and SaaS dumps move copies into places policy never named. |

Data Boar samples **configured** targets and reports **locations and pattern classes**. It does not rewrite lineage graphs or certify ISO/IEC 25012 scores.

## Shared responsibility (one slide)

| Party | Owns |
| ----- | ---- |
| **Your organization** | Lawful scope, Data Owner / Steward RACI, credentials, retention, what to remediate |
| **Data Boar** | Configured scans, technical findings, repeatable session artifacts |

## Outcomes you can expect in 30 / 60 / 90 days

> **Deploy in hours. First scan in days.** Horizons below are operational maturity, not activation time.

| Horizon | Realistic milestone |
| ------- | ------------------- |
| **30 days** | Scoped scan on agreed stores/exports; heatmap of high-risk pattern classes; steward vs engineer owners named |
| **60 days** | Repeatable cadence; session-to-session trend; glossary aligned with DPO/security (same words, not two inventories) |
| **90 days** | Evidence pack that can **inform** a GGD roadmap and audit **preparation**—not proof that governance is complete |

## Next step

- **Security / GRC depth:** [PITCH_CISO.md](PITCH_CISO.md)
- **Privacy / lawful-basis depth:** [PITCH_DPO.md](PITCH_DPO.md)
- **IT Evaluate–Direct–Monitor cycle:** [PITCH_IT_GOVERNANCE.md](PITCH_IT_GOVERNANCE.md)
- **Detection vs generative hype:** [COMPLIANCE_FRAMEWORKS.md](../COMPLIANCE_FRAMEWORKS.md#deterministic-detection-vs-generative-llm-hype)
