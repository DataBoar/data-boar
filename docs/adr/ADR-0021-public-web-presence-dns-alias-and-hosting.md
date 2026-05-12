# ADR 0021 — Public web presence: DNS alias (CNAME), canonical host, TLS, and hosting shape

**Date:** 2026-04-08
**Status:** Accepted (architecture); operator choice of concrete host remains open

---

## Context

The project needs a **public website** (marketing, documentation pointers, trust) distinct from the **self-hosted product** (scanner, API, dashboard). The operator may register **more than one `.br` hostname** for brand or memorability. DNS and TLS must stay understandable for future contributors and for Registro.br–style setups.

A common pattern is:

- One **canonical** hostname for the public site (e.g. the primary registered domain).
- A **secondary** hostname acting as an alias (CNAME) to the same origin so both names resolve to the same service.

This ADR records the **architectural** rules; it does **not** mandate a specific cloud vendor or static host until the operator deploys one.

---

## Decision

### 1. DNS: CNAME alias to the canonical name

- The **secondary** public name may be a **CNAME** pointing at the **canonical** hostname (e.g. `dashboard.example.net.br` → `databoar.example.com.br`), so both names share the same DNS Colleague-Nn to the eventual A/AAAA (or provider alias) of the canonical zone.
- **Apex (`@`)** records are not required to change for the alias subdomain; only the **subdomain** used for the secondary brand needs the CNAME (subject to DNS provider capabilities).

### 2. HTTP: one origin, explicit canonical policy

- The **web server or edge** must accept **both** `Host` values (or redirect consistently):
  - Either **301** from the secondary name to the canonical name, or
  - Serve the **same** site on both names with a single **canonical** link strategy (avoid duplicate SEO without `rel=canonical`).
- **Application programming interfaces** and the **product** should not depend on the marketing alias unless explicitly documented; prefer **one** public API hostname in docs and certificates.

### 3. TLS: cover every public name

- Certificates (e.g. ACME / Let's Encrypt) must include **all** hostnames that clients will use in the browser — typically a **SAN** listing canonical + alias, or separate certs per name on the same termination layer.

### 4. Hosting shape: separate “marketing site” from “product runtime” when practical

- **Marketing / docs** (mostly static): suitable targets include **static hosting** (e.g. Git provider pages, Cloudflare Pages, Netlify, Vercel) with the custom domain attached per provider instructions (often a **CNAME to the provider**, which may differ from “CNAME domain → domain” — the operator chooses one pattern per provider).
- **Full control / alignment with Ansible–Docker ops**: a **VPS** (or equivalent) with **Caddy** or **nginx** as reverse proxy, serving static assets or a CMS container, remains consistent with existing deployment culture.
- **Homelab-only** as the sole origin for a public brand site is **discouraged** for availability and operational clarity; lab may **mirror** or **stage** content instead.

### 5. No committed vendor in this ADR

- The **concrete** choice of Pages vs VPS vs managed WordPress is left to **operator deployment** and may change; this ADR only fixes **DNS + HTTP + TLS + separation** principles.

---

## Consequences

- **Positive:** Clear checklist for Registro.br DNS + any reverse proxy: CNAME → vhost/server names → TLS SAN → canonical redirects.
- **Positive:** Reduces risk of “two websites drift” or broken HTTPS on the alias.
- **Neutral:** Operator must still configure the chosen provider’s **domain verification** and **apex** rules (ALIAS/ANAME or `www` only) if the static host does not support arbitrary CNAME-to-CNAME Colleague-Nns.
- **Follow-up:** When a production URL is fixed, document it in **USAGE** / deploy docs (not only in private notes) so integrators see one official base URL.

---

## References

- Registro.br documentation (DNS, glue records) — operator-facing.
- Prior deployment automation: [ADR 0008](ADR-0008-docker-ce-swarm-over-docker-io-and-podman-only.md), [ADR 0009](ADR-0009-ansible-idempotent-roles-as-single-automation-source.md).
