# Open core and commercial licensing (draft policy)

**Português (Brasil):** [LICENSING_OPEN_CORE_AND_COMMERCIAL.pt_BR.md](LICENSING_OPEN_CORE_AND_COMMERCIAL.pt_BR.md)

This document describes the **intended** product boundary for Data Boar: an **open-core** distribution (community trust, auditability) plus **commercial** capabilities enforced by cryptographic licensing. It is a **draft** for operators and contributors; **final license terms require legal review** before you change the root `LICENSE` or ship paid builds.

## Model (Bitwarden-style hybrid)

| Layer                                     | Intent                                                                                                        | Typical license posture                                                                                                                                                                                          |
| -----                                     | ------                                                                                                        | ------------------------                                                                                                                                                                                         |
| **Open core**                             | Essential scan, reporting, dashboard, connectors baseline; buildable from public sources without a paid token | Remains under a permissive or strong-copyleft OSI-approved license (today: **BSD 3-Clause** in `LICENSE`; future option: **AGPL-3.0** for server-side if you want stronger “self-host must share changes” terms) |
| **Commercial / source-available modules** | Enterprise features, advanced policies, premium connectors, or controlled trial/POC behaviour                 | **Source-available** terms: code may be visible for audit, but **production use requires a valid subscription** and a **signed license token** (see [LICENSING_SPEC.md](LICENSING_SPEC.md))                      |

This mirrors the industry pattern used by projects such as **Bitwarden**: core under GPL/AGPL-style terms, with separate directories or packages under a **commercial / source-available** license for paid features. See Bitwarden’s server `LICENSE_FAQ.md` and `bitwarden_license/` layout for the idea (do not copy their license text without counsel).

## What stays in the public repository

- Scanner engine, connectors (baseline), report generation, API/dashboard (dashBOARd), tests, docs for **operators** (USAGE, SECURITY, deployment guides).
- **Runtime verification only**: public **Ed25519 verify key** (not the signing key), revocation list format, and the behaviour of `core/licensing/` when `licensing.enforcement` is enabled.

**Note:** Open-source licensing of **code** under BSD (or future AGPL) does **not** waive **trademark**, **trade-dress**, or **commercial goodwill** in the **name, mascot, narrative, and product experience** below. Forks may redistribute code under license terms but must not imply endorsement or confuse origin unless permitted. Counsel should align `LICENSE`, `NOTICE`, trademark policy, and any **partner / white-label** SKUs (see [Future product tiers](#future-product-tiers-partners-vs-end-customers-planning-reminder)) with this inventory.

## Brand, narrative, and experience IP (inventory for counsel and commercial policy)

When you harden **IP protection**, **commercial** offers, or **partner** programs, treat the following as an explicit **checklist** alongside patents/trade secrets (if any) and cryptographic licensing. This is **not legal advice**; use it to brief counsel and to scope what contracts and enforcement should cover.

| Layer                                         | What to protect (examples)                                                                                                                                                                                                                                                                | Where documented / embodied                                                                                                                                                                                      |
| -----                                         | --------------------------                                                                                                                                                                                                                                                                | ---------------------------                                                                                                                                                                                      |
| **Name and sub-brands**                       | **Data Boar** as product name; **dashBOARd** as the web dashboard sub-brand; consistent spelling and capitalization in UI, README, Docker metadata                                                                                                                                        | Root README, `core/about.py`, API/templates, [MASCOT.md](MASCOT.md)                                                                                                                                              |
| **Mascot and visual identity**                | Boar character artwork (SVG/PNG), favicon, placement in dashboard/About/help, **Excel report** (Report info sheet), **heatmap** watermark; colour vs B&W variants                                                                                                                         | [MASCOT.md](MASCOT.md), `api/static/mascot/`, `NOTICE`, `report/generator.py`                                                                                                                                    |
| **“Data soup” and scope metaphor**            | The **heterogeneous audit scope** (databases, filesystems, APIs, shares, archives, future formats) described as a unified **data soup** or equivalent narrative; connector **taxonomy** and “one audit across many sources” positioning                                                   | [USAGE.md](USAGE.md), [TECH_GUIDE.md](TECH_GUIDE.md), [TOPOLOGY.md](TOPOLOGY.md), deploy docs, [COMPLIANCE_TECHNICAL_REFERENCE.md](COMPLIANCE_TECHNICAL_REFERENCE.md)                                            |
| **Mythology, tone, and metaphors**            | **Boar / trail / audit** language; compliance framing (LGPD/GDPR/CCPA and samples); **risk heatmap** as visual metaphor; “sensitivity”, “findings”, “quasi-identifiers” as part of product voice                                                                                          | README, COMPLIANCE docs, report wording, dashboard copy                                                                                                                                                          |
| **Overall appearance (trade dress–adjacent)** | Dashboard **layout** (cards, status, chart), nav labels, dark/light styling patterns; **Excel** sheet structure, column conventions, attribution blocks; API **OpenAPI** titles where branded                                                                                             | `api/templates/`, static CSS, report layout code                                                                                                                                                                 |
| **Operation and “how it works”**              | **CLI one-shot** vs **API + dashboard** vs **Docker** default command; session/report lifecycle; licensing states in About/health — the **documented operator story** is **copyrightable expression**; **secret** know-how that is **not** published may be a separate trade-secret topic | [USAGE.md](USAGE.md), [TECH_GUIDE.md](TECH_GUIDE.md), [deploy/DEPLOY.md](deploy/DEPLOY.md), [LICENSING_SPEC.md](LICENSING_SPEC.md)                                                                               |
| **Companion resources and adjacent apps**     | **Docker Hub** image naming (`fabioleitao/data_boar`, tags); future **public website** copy; **private** issuer tooling (`tools/license-studio` — separate repo); other repos you cite in portfolio (e.g. infra demos) — clarify which are **product family** vs **personal**             | [DOCKER_SETUP.md](DOCKER_SETUP.md), [HOSTING_AND_WEBSITE_OPTIONS.md](HOSTING_AND_WEBSITE_OPTIONS.md); maintainer portfolio pointers under **Internal and reference** in [README.md](README.md); private runbooks |

**Partner / enterprise angle:** If partners deliver audits to **their** customers, contracts should state whether they may **co-brand**, must **retain** Data Boar attribution, or **white-label** (and under which SKUs). That interacts with trademark and the **mascot** in reports exports.

**Practical steps (with counsel):** (1) Trademark search/register **word mark** and optionally **logo/mascot** in key jurisdictions and classes (e.g. software, SaaS). (2) Add or tighten **trademark usage** paragraph in `NOTICE` or a `TRADEMARK.md` if needed. (3) Ensure **commercial / source-available** license text reserves **brand** clauses (no suggestion of affiliation). (4) Align **release integrity** and **license JWT** claims if you ever encode **tier** or **program** (see [LICENSING_SPEC.md](LICENSING_SPEC.md) future extensions).

For copyright vs trademark basics and registration pointers, see [COPYRIGHT_AND_TRADEMARK.md](COPYRIGHT_AND_TRADEMARK.md).

## What must never be in the public repository

- **Private signing keys**, operator “blob” secrets, or any material that allows forging valid license JWTs.
- The **license issuance** tool source or binaries intended only for your team (maintain in a **separate private repository**; see `tools/license-studio/README.md`).

## Default behaviour (development and CI)

With **no enforcement** (default), the application runs in **open** mode: no license file is required, and all features behave as today. This preserves forks, tests, and academic use until you explicitly enable enforcement in config or environment (see [LICENSING_SPEC.md](LICENSING_SPEC.md)).

## Next steps (legal)

1. Choose **BSD 3-Clause vs AGPL-3.0** for the open core (AGPL increases copyleft on network use; BSD maximizes adoption—trade-off with counsel).
1. Draft a **commercial / source-available** license for paid modules (or adapt a vetted template).
1. Add **NOTICE** / **THIRD_PARTY** files if you redistribute cryptography or other stacks under varied licenses.

## Commercial subscription tiers: Pro vs Enterprise (working model)

**Status:** Working model for **product and sales conversations** — **not** final contract language. **Pricing is undecided.** Tier names (`Pro`, `Enterprise`, `Partner`) may shift; **JWT claims and runtime gates** in [LICENSING_SPEC.md](LICENSING_SPEC.md) are not fully implemented yet. The **feature-by-feature matrix** lives in the maintainer plan `docs/plans/PLAN_PRODUCT_TIERS_AND_OPEN_CORE.md` (plain-text path — internal planning, not a buyer-facing link target).

**Why paid tiers at all:** The **open core** is already capable (scan engine, dashboard, baseline connectors, compliance samples, optional jurisdiction hints, and more). **Subscription** is for **corporate-grade packaging**: entitlement clarity, support and liability boundaries, premium connector and detection packs as they ship, and governance features large buyers expect. The split below is **what to reserve for paid SKUs** vs what remains **community trust and adoption** in the public tree.

### Open core (no subscription required)

- **Intent:** Full-featured **self-host** for transparency, research, and adoption; same codebase contributors and CI exercise.
- **Boundary:** Stays aligned with **public** `LICENSE` (today BSD 3-Clause). Commercial enforcement **off** (`licensing.mode: open`) unless the operator opts in.

### Scale and concurrency (working model — workers, targets, premium ingredients)

**Status:** Worker caps are **ratified (2026-06-11, #853) and implemented in `enforced` mode** (#551 — `dbmax_workers` claim + tier defaults in `core/licensing/guard.py`). **Workers ≈ concurrent TARGETS** scanned in parallel — that is the buyer-facing framing. Target-count ceilings (`dbmax_targets`) remain a **policy target**; finalize with product + counsel.

| Tier | Workers (≈ concurrent targets scanned) | Targets (configured targets per session or deployment envelope) | Premium “data soup” ingredients |
| ---- | ----------------------------------------------- | ---------------------------------------------------------------- | -------------------------------- |
| **Open core / Community** | **2** (ratified) | **Capped but generous** (exact ceiling TBD — e.g. large enough for real pilots, not unlimited fleet-wide inventory) | Full **public** feature set today; when gated features appear, open core stays on the **baseline** pack unless you explicitly widen for community experiments. |
| **Pro** | **4** (ratified) | **Higher cap** than open | **Curated** premium connectors/heuristics — **not** every high-cost ingredient (see Enterprise). |
| **Pro+** | **8** (ratified — claim-driven: issued tokens carry `dbmax_workers: 8`) | **Higher cap** than Pro | Pro **plus** custom RBAC roles, push SARIF/SIEM, RoPA export, deployment pack — see [SUBSCRIPTION_TIERS.md](SUBSCRIPTION_TIERS.md). |
| **Enterprise** | **Unlimited** in entitlement (actual throughput = **host CPU/RAM/IO** and operator tuning) | **Unlimited** in entitlement (same practical limits) | **Widest** entitlement: ingredients that are **expensive, risky, or niche** may be **Enterprise-only** (e.g. certain network-adjacent probes, full enterprise connector tier, white-label report paths) — **exact list TBD**; align with `docs/plans/PLAN_PRODUCT_TIERS_AND_OPEN_CORE.md`. |
| **Partner** | Typically **Pro- or Enterprise-like** envelope per contract | **Multi-customer** metering may use **separate** caps — not the same SKU problem as single-tenant open core | Co-brand / programme rules in contract, not only worker counts. |

**Why cap open core at all:** Keeps the **free** tier honest (not a stealth unlimited batch product), reduces **abuse** as a costless parallel loader, and preserves a **clear upsell** for organisations that need fleet-scale scans. Forks under the license may still run uncapped until they adopt **your** builds with enforcement — position with counsel if you tighten **AGPL** or **trademark** posture later.

**Implementation pointer:** `dbmax_workers` is **implemented** (#551 — enforced-mode clamp, fail-soft, audited); `dbmax_targets` remains a future signed claim — see [LICENSING_SPEC.md](LICENSING_SPEC.md); `LicenseGuard` + config resolution when `licensing.mode: enforced`.

### Deployments, copies, and sites (Pro vs Enterprise)

**Status:** Working **commercial + technical** model — **not** enforced in code today. Align contracts with what you can **verify** (machine binding, optional allowlists — see [LICENSING_SPEC.md](LICENSING_SPEC.md)).

| Tier | Licensed **copies** / **sites** (production use) | Typical picture |
| ---- | ----------------------------------------------- | --------------- |
| **Pro** | **Two** deployments per license (operator-ratified 2026-06-11 — `DEFAULT_PRO_DEPLOYMENTS = 2`): the typical picture is **one on-prem footprint + one cloud/branch** for the **same organisation context**, **or** a **consultant’s laptop + one engagement server**. Not a fleet-wide entitlement. Same SKU story: **one organisation context** or **one consultant**; **Pro+** packs extend to **5** (admin convenience, ~linear pricing). |
| **Enterprise** | **More than one** authorized deployment per license (and a **higher** price). Packaging examples (mix and match in contracts): **bundles of five** sites (branches, data centres, or **named** cloud tenants), **partial** coverage (some branches or some tenants — not the whole estate), or **unlimited** deployments for global accounts (still subject to **support** and **abuse** guardrails in the contract). Realistic driver: organisations with **many** sites and **multiple** cloud directories/tenants need **flexible** counts without buying a full seat per VM. |

**Federated groups (branch silos, shared CISO, local P&L):** In **distributed** operators (e.g. **ports, terminals, logistics, or multi-country industrials**), each **site** is often its own **knowledge, data, and systems silo**: local compliance and regulation, **local** budget and capex/opex, local management priorities—while **group** leadership sets **common** security tooling, standards, and strategic vendor **volume** deals (EDR, vuln platforms, productivity suites, firewall baselines, hardware norms). That pattern **does not** map to **one** Pro license for the **whole** group: **enterprise-wide** coverage, governance, and deployment counts are **Enterprise** SKUs. It **does** map to **one or more Pro entitlements per site** when a **single location** buys **separate** production footprints—e.g. **one Pro** for a **cloud** tenant and **another Pro** for **on-premises** at **that** site—without requiring HQ mandate or peer branches to mirror the purchase. **Yes, that is coherent** with Pro = **per-deployment** entitlement; **group-wide** roll-out and pricing belong in **Enterprise** contracts.

**Control via JWT (and friends):** A single **`dbmfp`** already pins **one** host fingerprint. For **Pro**, that maps naturally to **one** slot. For **Enterprise**, you need a **policy + data structure** that scales:

- **Claims:** `dbmax_deployments` (integer — **2** for Pro, ratified; **5** for Pro+ pack; **5, 10, 25**, or **0** = unlimited for Enterprise, product decision); optional **`dbmfp_allowlist`** or a **companion signed file** (list of allowed machine seeds / deployment IDs) if the JWT would get too large — issue **refreshed tokens** or **add-on packs** when the customer buys **+5 sites** or adds tenants.
- **Operational reality:** Issuance/refill (renewal, **pack** purchases) should live in **private issuer** tooling with an **audit log** (`dbcid`, who signed, slot count) — heavier deals may need **human** review; automation can assist drafting, but **counsel + product** own the template.

**Partner / consultant:** Pro-like **one** laptop may still be the norm; **Partner Enterprise** deals might use **deployment packs** tied to **programme** claims (`dbprogram`) — see future extensions in [LICENSING_SPEC.md](LICENSING_SPEC.md).

### Pro subscription (single organisation or consultant-led engagement)

**Typical buyer:** One company **or** an independent consultant / small integrator serving **one client context** per entitlement (exact metering TBD with counsel).

**Reserve for Pro-class SKUs (illustrative — product may ship pieces earlier in open core):**

- **Commercial entitlement** and **standard support** channel (SLA lighter than Enterprise).
- **Single licensed production deployment** per license (see [Deployments, copies, and sites](#deployments-copies-and-sites-pro-vs-enterprise)) — not multi-site fleet rights. The **same** legal entity may hold **multiple Pro SKUs** for **different** footprints (e.g. **cloud vs on-prem** at **one** site); that is still **not** a substitute for **group-wide** Enterprise where the **whole** organisation needs coverage.
- **Higher worker and target ceilings** than open core — but **not** necessarily “everything”: some **premium ingredients** may be **Enterprise-only** if cost-to-serve or risk is too high for Pro (see table above).
- **Premium detection and format coverage** where cost-to-serve is high: e.g. full ML/DL-assisted stacks where gated, stronger content-type / “cloaking” surfaces, legacy or niche formats — aligned with the internal feature matrix.
- **Machine-bound license** and **named deployment** limits as in [LICENSING_SPEC.md](LICENSING_SPEC.md) (`dbmfp`, trial caps).
- **Priority** triage of issues — not the same as 24/7 or named CSM (those lean Enterprise).

**Not the main Enterprise differentiator:** Org-wide SSO, white-label reports, full cloud/HR connector packs, or multi-tenant MSP programmes — those map closer to **Partner** or **Enterprise** (see plan).

### Enterprise subscription (regulated, global, or strategic accounts)

**Typical buyer:** Large org, regulated industry, or buyer needing **vendor-grade** governance and roadmaps.

**Reserve for Enterprise-class SKUs (illustrative):**

- **Unlimited workers and targets** in **entitlement** (subject to hardware — see [Scale and concurrency](#scale-and-concurrency-working-model--workers-targets-premium-ingredients)); optional **Enterprise-only** premium ingredients not offered on Pro.
- **Multiple authorized deployments per license** (sites / tenants / branches) — **packs**, **partial** estate coverage, or **unlimited** — priced accordingly; see [Deployments, copies, and sites](#deployments-copies-and-sites-pro-vs-enterprise).
- **Everything in Pro** that your contract defines, plus **stronger commercial terms**: SLA, **dedicated** or named support where offered, indemnities and liability caps per counsel.
- **Governance and identity:** e.g. SSO/SAML, report **RBAC**, immutable audit trails, evidence exports aimed at **GRC / audit** workflows — as the product matures.
- **Broadest connector and format entitlement:** enterprise SaaS (e.g. object storage, M365/Graph at scale, HR/ERP paths), optional **network-oriented** capabilities, **white-label** or strict **co-brand** rules — per [Brand, narrative, and experience IP](#brand-narrative-and-experience-ip-inventory-for-counsel-and-commercial-policy).
- **Custom integration** or **professional services** may be **attached** to Enterprise (or sold separately); see maintainer commercial workflow, not this doc.

### Partner (often a separate SKU)

**Consulting / MSP / reseller** programmes — **multi-customer** use, co-brand vs white-label, and **different cost-to-serve** — are **not** the same problem as single-tenant Pro or global Enterprise. Treat **Partner** as its own entitlement family in contracts; technically it may map to claims such as `dbtier: partner` (see [LICENSING_SPEC.md](LICENSING_SPEC.md) future extensions). **Do not** collapse Partner into “just Pro with more seats” without pricing and legal review.

### Pricing and enforcement

- **Pricing:** Not fixed in this repository; when you publish SKUs, do it in **commercial** materials after counsel review.
- **Enforcement:** When implemented, **signed JWT** claims (e.g. `dbtier`, optional `dbmax_workers`, `dbmax_targets`, `dbmax_deployments`, `dbfeatures`) should match what was sold — see [LICENSING_SPEC.md](LICENSING_SPEC.md) §Future extensions and operational policy sketch.

## Future product tiers: partners vs end customers (planning reminder)

**Reminder for a later licensing pass** (IP protection, commerciality, profitability): consider **multiple commercial SKUs** with different **objectives, entitlements, and price points**—not unlike how database vendors segment **Express**, **Standard**, **Enterprise**, **Enterprise + options**, **RAC / add-ons**, etc. **Pro vs Enterprise boundaries** for positioning are spelled out in [Commercial subscription tiers: Pro vs Enterprise (working model)](#commercial-subscription-tiers-pro-vs-enterprise-working-model) above.

**Use case to preserve explicitly:** **Consulting / integration partners** who hold a **partner-grade** (or **pro** / **enterprise**—names TBD) subscription and use Data Boar to deliver audits or implementations for **their customers** (third-party end clients), under **their** contract and entitlement, as distinct from:

- A **regular commercial** SKU aimed at **organisations that consume the product directly** (internal DPO / IT), and
- Optional **trial / POC** or **academic** postures you already separate in policy.

**Why it matters:** Partner-led delivery changes **risk, support, liability, metering, and brand** expectations. Pricing should reflect **different cost-to-serve** (e.g. multi-customer use, higher support load, possible white-label or co-brand rules). **Final tier names, contract text, and technical enforcement** require **legal + product** decisions before implementation.

**Technical direction (later):** encode tier/program in signed tokens (see [LICENSING_SPEC.md](LICENSING_SPEC.md) “Future extensions”) and enforce in `LicenseGuard` / reporting only after claims and contracts are fixed.

## Related documents

- [LICENSING_SPEC.md](LICENSING_SPEC.md) — token format, states, machine binding, revocation.
- docs/plans/PLAN_PRODUCT_TIERS_AND_OPEN_CORE.md — **feature matrix per tier** (Community / Pro / Partner / Enterprise); enforcement roadmap; what to protect as IP. (internal maintainer file — see docs/README.md Internal section)
- [RELEASE_INTEGRITY.md](RELEASE_INTEGRITY.md) — optional signed release manifest.
- [HOSTING_AND_WEBSITE_OPTIONS.md](HOSTING_AND_WEBSITE_OPTIONS.md) — private repos and public site options.
- [ACADEMIC_USE_AND_THESIS.md](ACADEMIC_USE_AND_THESIS.md) ([pt-BR](ACADEMIC_USE_AND_THESIS.pt_BR.md)) — thesis / dissertation use of public docs and code (not legal advice).
