# Primer: SaaS, AIaaS, and Data Boar’s delivery model

**Português (Brasil):** [AAS_MODELS_PRIMER.pt_BR.md](AAS_MODELS_PRIMER.pt_BR.md)

**Audience:** integrators, security reviewers, and buyers comparing “as a service” labels with what actually runs in their environment.

---

## 1. Vocabulary

| Term | Usual meaning | Data Boar in *this* public repo |
| ---- | ------------- | -------------------------------- |
| **SaaS** | Vendor hosts the app; tenants share an operated service | **Not** the core product model today — you deploy the scanner where your data lives |
| **AIaaS** | Model/inference API billed per token or call | **Not** the core — discovery is **deterministic** pattern/detector logic, not a hosted LLM that reads your corpus |
| **On-prem / customer VPC** | You run containers or VMs; data stays in your boundary | **Yes** — default story in [LICENSING_OPEN_CORE_AND_COMMERCIAL.md](../LICENSING_OPEN_CORE_AND_COMMERCIAL.md) and [DEPLOY.md](../deploy/DEPLOY.md) |
| **Managed future** | Possible later offering | **Thesis only** — do not claim a public multi-tenant SaaS from this tree |

---

## 2. Evidence in tracked docs

- **Deployment:** Ansible + Docker/OpenTofu under `deploy/` ([IAC_AND_DEVSECOPS_PRIMER.md](IAC_AND_DEVSECOPS_PRIMER.md)); Pro licenses describe **limited production footprints** (`dbmax_deployments` in [LICENSING_SPEC.md](../LICENSING_SPEC.md)), not unlimited SaaS seats.
- **AI posture:** [AI_COMPLIANCE_PRIMER.md](AI_COMPLIANCE_PRIMER.md) states the product covers the **data layer** — it does **not** evaluate models. [GLOSSARY.md](../GLOSSARY.md) separates marketing “AI” vocabulary from shipped detector behaviour.
- **Optional OTel:** Metrics/traces are **opt-in** via `DATA_BOAR_OTEL_ENABLED` (`core/otel_setup.py`) — telemetry export, not AIaaS.

---

## 3. What we do not claim

- No hosted “upload your data to databoar.com for scanning” flow in versioned product docs.
- No per-token inference pricing or model card in this repository.
- Connector targets may include **SaaS exports** (files/APIs you configure) — that is **inventory of third-party systems**, not Data Boar becoming those vendors’ SaaS.

---

## 4. Where to go next

| Need | Doc |
| ---- | --- |
| Install paths | [DEPLOY.md](../deploy/DEPLOY.md) |
| License tiers / deployments | [LICENSING_OPEN_CORE_AND_COMMERCIAL.md](../LICENSING_OPEN_CORE_AND_COMMERCIAL.md) |
| AI regulation primer (data layer only) | [AI_COMPLIANCE_PRIMER.md](AI_COMPLIANCE_PRIMER.md) |
