# PLAN: Product Tiers and Open-Core Boundary Definition

**Status:** Pending
**Date:** 2026-04-04
**Authors:** Fabio Leitao
**Priority:** H1
**Depends on:** ADR-0025

**Priority:** [H2][U1] — near-term before partner onboarding
**Related:** `docs/LICENSING_OPEN_CORE_AND_COMMERCIAL.md`, `docs/LICENSING_SPEC.md`, `docs/plans/PLANS_TODO.md`

> This plan defines **which capabilities belong to each tier** of the Data Boar product.
> Final pricing, contract terms, and JWT claim enforcement require legal review first.
> The feature matrix here drives product decisions and must be kept in sync with
> `LICENSING_OPEN_CORE_AND_COMMERCIAL.md` and `LICENSING_SPEC.md` (dbtier claim).

---

## Tier Model (4+1 levels)

| Tier | Token claim | Target audience | Enforcement |
|---|---|---|---|
| **Community / Open Core** | `dbtier: community` (or absent) | Researchers, DPOs, IT teams, students, freelancers | Mode `open` — no JWT required |
| **Trial / POC** | `dbtier: trial` | Pre-sales evaluators, POC engagements | Mode `enforced`; row-capped + watermarked |
| **Pro / Consultant** | `dbtier: pro` | Independent consultants, MSSP, small integrators | Mode `enforced`; full features for single-client engagements |
| **Partner** | `dbtier: partner` | Resellers, system integrators, multi-client MSP | Mode `enforced`; multi-client use permitted; co-brand rules apply |
| **Enterprise** | `dbtier: enterprise` | Large orgs, regulated industries, white-label | Mode `enforced`; all features + SLA + custom support |

> The `dbtier` claim is already planned in `LICENSING_SPEC.md` §Future extensions.
> Enforcement of feature gates per tier is NOT yet implemented — this plan drives that work.

**Related product tracks (keep separate):** [PLAN_MATURITY_SELF_ASSESSMENT_GRC_QUESTIONNAIRE.md](PLAN_MATURITY_SELF_ASSESSMENT_GRC_QUESTIONNAIRE.md) (org/process questionnaire — commercial POC) and [PLAN_PDF_GRC_REPORT.md](PLAN_PDF_GRC_REPORT.md) (technical findings PDF “em prosa” — Pro tier). Both depend on **tier semantics** from this plan once **Phases 1–2** ship.

---

## Feature Matrix

Legend: ✅ Included | 🔶 Limited | ❌ Not included | 🔜 Planned for this tier

### Core Detection Engine

| Capability | Community | Trial | Pro | Partner | Enterprise |
|---|---|---|---|---|---|
| LGPD regex patterns (CPF, RG, email, phone, address) | ✅ | ✅ | ✅ | ✅ | ✅ |
| GDPR patterns (EU formats) | ✅ | ✅ | ✅ | ✅ | ✅ |
| CCPA / US patterns | ✅ | ✅ | ✅ | ✅ | ✅ |
| COPPA / child data patterns | ✅ | ✅ | ✅ | ✅ | ✅ |
| CNPJ (including alphanumeric format) | ✅ | ✅ | ✅ | ✅ | ✅ |
| Quasi-identifier aggregation | ✅ | ✅ | ✅ | ✅ | ✅ |
| Minor data detection | ✅ | ✅ | ✅ | ✅ | ✅ |
| Fuzzy column name matching | ✅ | ✅ | ✅ | ✅ | ✅ |
| Content-type cloaking detection | 🔶 basic | 🔶 | ✅ | ✅ | ✅ |
| ML/DL-assisted sensitivity heuristics | ❌ | 🔶 limited | ✅ | ✅ | ✅ |
| Confidence scoring + FN reduction techniques | ❌ | 🔶 | ✅ | ✅ | ✅ |
| Synthetic data validation | ❌ | ❌ | 🔜 | ✅ | ✅ |

### Data Sources / Connectors

| Capability | Community | Trial | Pro | Partner | Enterprise |
|---|---|---|---|---|---|
| Filesystem (local directories) | ✅ | ✅ | ✅ | ✅ | ✅ |
| SQLite, CSV, JSON, JSONL | ✅ | ✅ | ✅ | ✅ | ✅ |
| PostgreSQL, MySQL, MariaDB | ✅ | ✅ | ✅ | ✅ | ✅ |
| Microsoft SQL Server | ✅ | ✅ | ✅ | ✅ | ✅ |
| MongoDB, Redis | ✅ | ✅ | ✅ | ✅ | ✅ |
| Oracle DB | 🔶 config only | ✅ | ✅ | ✅ | ✅ |
| SAP connector | ❌ | ❌ | 🔜 | ✅ | ✅ |
| Enterprise HR / ERP connectors (RM, TOTVS, SAP HR) | ❌ | ❌ | ❌ | 🔜 | ✅ |
| Object storage (S3, Azure Blob, GCS) | ❌ | ❌ | 🔜 | ✅ | ✅ |
| Office 365 / SharePoint / OneDrive (Graph API) | ❌ | ❌ | 🔜 | ✅ | ✅ |
| Google Drive / Workspace | ❌ | ❌ | 🔜 | ✅ | ✅ |
| Confluence / Jira (Atlassian) | ❌ | ❌ | ❌ | 🔜 | ✅ |
| Opt-in network port/service scanning | ❌ | ❌ | ❌ | 🔜 | ✅ |

### File Format Ingestion (Data Soup)

| Capability | Community | Trial | Pro | Partner | Enterprise |
|---|---|---|---|---|---|
| Plain text, Markdown, HTML | ✅ | ✅ | ✅ | ✅ | ✅ |
| PDF (pdfminer baseline) | ✅ | ✅ | ✅ | ✅ | ✅ |
| Office (DOCX, XLSX, PPTX) | ✅ | ✅ | ✅ | ✅ | ✅ |
| Email (EML, MSG) | ✅ | ✅ | ✅ | ✅ | ✅ |
| Archives (ZIP, TAR, GZIP) | ✅ | ✅ | ✅ | ✅ | ✅ |
| EPUB, Parquet, ORC | ✅ | ✅ | ✅ | ✅ | ✅ |
| Images with EXIF / HEIC (Apple) | ✅ | ✅ | ✅ | ✅ | ✅ |
| Rich media (video/audio metadata, subtitles) | ✅ | ✅ | ✅ | ✅ | ✅ |
| SQLite (browser history, app caches) | ✅ | ✅ | ✅ | ✅ | ✅ |
| Legacy office (WPD, Lotus 1-2-3, ODF, RTF) | ❌ | 🔶 | ✅ | ✅ | ✅ |
| OpenDocument (LibreOffice full suite) | ❌ | 🔶 | ✅ | ✅ | ✅ |
| MS Access (.mdb/.accdb) | ❌ | ❌ | ✅ | ✅ | ✅ |
| MS OneNote, MS Project, MS Visio | ❌ | ❌ | ✅ | ✅ | ✅ |
| PostScript, LaTeX, DVI | ❌ | ❌ | 🔜 | ✅ | ✅ |
| MHTML/MHT (browser saves) | ❌ | ❌ | ✅ | ✅ | ✅ |
| Binary strings extraction (ELF, MZ, DLL, EXE) | ❌ | ❌ | 🔜 | ✅ | ✅ |
| Browser artifact ingestion (Chrome/Firefox history, cache) | ❌ | ❌ | 🔜 | 🔜 | ✅ |

### Report and Dashboard

| Capability | Community | Trial | Pro | Partner | Enterprise |
|---|---|---|---|---|---|
| Excel report (risk heatmap + findings) | ✅ | 🔶 capped | ✅ | ✅ | ✅ |
| Dashboard (dashBOARd) web UI | ✅ | ✅ | ✅ | ✅ | ✅ |
| Report RBAC / access control | ❌ | ❌ | ❌ | 🔜 | ✅ |
| Multi-session report history | ✅ | 🔶 | ✅ | ✅ | ✅ |
| Compliance evidence mapping output | 🔶 | 🔶 | ✅ | ✅ | ✅ |
| GRC-ready output (ISO 27701, FELCA) | ❌ | ❌ | 🔜 | ✅ | ✅ |
| White-label / custom logo in report | ❌ | ❌ | ❌ | 🔜 | ✅ |
| Dashboard i18n (multi-language) | ❌ | ❌ | 🔜 | ✅ | ✅ |
| Dashboard HTTPS by default | ✅ | ✅ | ✅ | ✅ | ✅ |
| Audit trail / immutable scan log | ❌ | ❌ | 🔶 | ✅ | ✅ |

### Security and Compliance Hardening

| Capability | Community | Trial | Pro | Partner | Enterprise |
|---|---|---|---|---|---|
| Strong crypto validation (AES-256, TLS 1.2+) | ✅ | ✅ | ✅ | ✅ | ✅ |
| Machine-bound license (dbmfp) | ❌ | ❌ | ✅ | ✅ | ✅ |
| Secrets vault integration (Bitwarden CLI, env) | ✅ | ✅ | ✅ | ✅ | ✅ |
| Release integrity / tamper detection | ✅ | ✅ | ✅ | ✅ | ✅ |
| SBOM generation | ✅ | ✅ | ✅ | ✅ | ✅ |
| SSO / LDAP / SAML integration | ❌ | ❌ | ❌ | 🔜 | ✅ |
| Custom revocation lists | ❌ | ❌ | ✅ | ✅ | ✅ |

### Deployment and Operations

| Capability | Community | Trial | Pro | Partner | Enterprise |
|---|---|---|---|---|---|
| CLI (main.py) + API (FastAPI) | ✅ | ✅ | ✅ | ✅ | ✅ |
| Docker Hub image | ✅ | ✅ | ✅ | ✅ | ✅ |
| Self-hosted (bare metal / VM) | ✅ | ✅ | ✅ | ✅ | ✅ |
| Self-upgrade / version check | ❌ | ❌ | 🔜 | ✅ | ✅ |
| Notifications (Slack, GitHub, webhook) | ✅ | ✅ | ✅ | ✅ | ✅ |
| API key auth (enforced) | 🔶 optional | ✅ | ✅ | ✅ | ✅ |
| Multi-tenant deployment (data isolation) | ❌ | ❌ | ❌ | 🔜 | ✅ |
| SLA / priority support | ❌ | ❌ | ❌ | 🔶 | ✅ |
| Kubernetes / orchestration guides | ❌ | ❌ | 🔜 | ✅ | ✅ |
| Custom installation and config | ❌ | ❌ | 🔶 | ✅ | ✅ |

### Commercial / Partner Rights

| Capability | Community | Trial | Pro | Partner | Enterprise |
|---|---|---|---|---|---|
| Use for internal DPO audit | ✅ | ✅ | ✅ | ✅ | ✅ |
| Deliver audit as service to 1 client | ❌ | ❌ | ✅ | ✅ | ✅ |
| Deliver audit to multiple clients (MSP/MSSP) | ❌ | ❌ | ❌ | ✅ | ✅ |
| Co-brand in report cover | ❌ | ❌ | 🔶 | ✅ | ✅ |
| White-label (remove Data Boar attribution) | ❌ | ❌ | ❌ | ❌ | ✅ (add-on) |
| Redistribute to end-customers | ❌ | ❌ | ❌ | ✅ (with contract) | ✅ |
| OEM / embed in own product | ❌ | ❌ | ❌ | ❌ | ✅ (add-on) |

---

## Tier Value Narrative (for sales / partner conversations)

### Community
The full audit capability for a single organization's internal DPO, IT team, or researcher.
Not for consulting delivery to third-party clients. Builds trust, ecosystem, and inbound leads.
**Constraint:** Must not be used to deliver paid services to third-party clients.

### Trial / POC
Time-limited (e.g. 30-90 days), row-capped (15 findings visible), watermarked.
Ideal for enterprise pre-sales and formal POC engagements. JWT required.
**Revenue model:** Convert to Pro/Partner/Enterprise after trial.

### Pro / Consultant
For the independent consultant, solo MSSP operator, or small integrator who delivers to
**one client engagement at a time**. Full detection capabilities, legacy format ingestion,
cloud connectors (planned), compliance output.
**Revenue model:** Annual license per consultant seat. Possible per-engagement add-ons.
**Key differentiator from Community:** Can deliver the tool output as a professional service.

### Partner
For system integrators, MSSPs, and resellers managing **multiple client engagements concurrently**.
Multi-client use is explicitly licensed. Co-branding in reports is permitted.
Access to SSO (planned), advanced connectors, and the partner portal (future).
**Revenue model:** Annual subscription per partner org + per-seat or per-customer usage tier.
**Key differentiator from Pro:** Multi-client use rights; partner brand in deliverables.

### Enterprise
For large organizations deploying internally at scale, regulated industries (banking, health, port
terminals), and OEM partners embedding Data Boar in their own product suite.
All features, SLA, dedicated support, white-label rights as an add-on.
**Revenue model:** Annual enterprise agreement; custom pricing based on scope, users, connectors.

---

## Technical Enforcement Roadmap (JWT claims → runtime gates)

| Phase | What to implement | Status |
|---|---|---|
| 0 (done) | `dbtier` planned in LICENSING_SPEC.md; JWT infra exists | ✅ Done |
| 1 | Add `dbtier` and `dbfeatures` claims to issued tokens | Not started |
| 2 | `LicenseGuard.check_feature(feature_name)` helper | Not started |
| 3 | Gate Pro features behind `check_feature()` in connectors/reports | Not started |
| 4 | Gate Partner rights (multi-client, co-brand) via `dbtier` check | Not started |
| 5 | Gate Enterprise features (white-label, SSO, RBAC) | Not started |
| 6 | `dbextras_profile` drives `uv` install profiles for heavy deps | Not started |

> Priority: implement Phase 1-2 before first paid engagements.
> Phase 6 last — requires uv extras redesign.

---

## What to Protect as IP (Monetizable Moats)

Listed in priority order from a "partner trying to steal value" perspective:

1. **Advanced connector logic** (SAP, Enterprise HR/ERP, cloud APIs) — high implementation cost
2. **ML/DL heuristics** (the trained models, prompt engineering, confidence calibration) — not open-sourceable
3. **Compliance evidence mapping** (the legal mapping from findings to LGPD/GDPR articles) — expert knowledge
4. **Multi-tenant isolation architecture** (when implemented) — enterprise trust requirement
5. **Report/dashboard trade dress** — mascot, Excel layout, heatmap visual — brand value
6. **Legacy/exotic format ingestion** — niche, high-effort, differentiator from basic grep tools
7. **Partner multi-client licensing model** — the right to serve third parties is the Pro→Partner upsell

---

## Open Questions (to resolve with legal + product)

- [ ] Final tier names: Community / Pro / Partner / Enterprise — or different marketing names?
- [ ] Can a Community license user self-host and charge for it indirectly? (CLT → license clear?)
- [ ] Should Oracle connector be Community or gated? (it's complex to configure)
- [ ] Trial tier: time-limited only, or feature-limited only, or both?
- [ ] Partner tier: per-org pricing, per-seat, or per-audit-engagement?
- [ ] White-label: separate add-on SKU or only Enterprise-included?
- [ ] Academic/thesis exception: grant letter or special license type?

---

## Pending Tasks

| # | Task | Priority |
|---|---|---|
| 1 | Legal review of tier definitions and partner rights language | [H2] before first paid deal |
| 2 | Implement Phase 1-2 JWT enforcement (dbtier + check_feature) | [H2][U1] |
| 3 | Update LICENSING_OPEN_CORE_AND_COMMERCIAL.md with link to this plan | [H1] |
| 4 | Draft Pro/Partner one-pager for partner conversations | [H2] |
| 5 | Create `tools/license-studio` private repo for issuer tooling | [H2] |
| 6 | Define academic/thesis exception policy | [H3] |
| 7 | Add `dbfeatures` to LICENSING_SPEC.md claims table | [H2] |