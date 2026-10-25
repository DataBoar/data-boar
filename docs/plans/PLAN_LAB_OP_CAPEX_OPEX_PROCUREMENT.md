# LAB-OP — CAPEX / OPEX & Procurement (tracked plan)

**Status:** Active
**Date:** 2026-04-02
**Authors:** Fabio Leitao
**Priority:** H2

**pt-BR:** [PLAN_LAB_OP_CAPEX_OPEX_PROCUREMENT.pt_BR.md](PLAN_LAB_OP_CAPEX_OPEX_PROCUREMENT.pt_BR.md)

**Scope:** Operator infrastructure (LAB-OP): hardware, networking, power/HVAC, physical security, software, subscriptions, AI tokens, training. No prices, store links, or real identifiers here — real details in the gitignored private file.

**Private file (details & prices):** `docs/private/homelab/LAB_OP_SHOPPING_LIST_AND_POWER.pt_BR.md`

**Related plans:**

| Topic | Plan / Doc |
| ----- | ---------- |
| Observability (metrics/logs/SIEM) | [PLAN_LAB_OP_OBSERVABILITY_STACK.md](PLAN_LAB_OP_OBSERVABILITY_STACK.md) |
| Firewall/L3/access/sequence | [PLAN_LAB_FIREWALL_ACCESS_AND_OBSERVABILITY.md](PLAN_LAB_FIREWALL_ACCESS_AND_OBSERVABILITY.md) |
| Production-readiness (homelab) | `docs/ops/HOMELAB_VALIDATION.md` |

---

## Procurement principle

> **Evidence before expense.** Every item must have a traceable justification (host report, real incident, Lynis warning, temperature, power outage, measured bottleneck). Promote items P2→P1→P0 only when evidence or imminent risk justifies it.

**Priority layers:**
- **P0 (priority now):** eliminates real downtime, security, or delivery risk today.
- **P1 (needed soon):** improves robustness, repeatability, operational quality.
- **P2 (dreams / future horizon):** significant upgrades when budget and evidence align.

---

## 1. Computers and hosts (LAB-OP)

### Key gaps

- **LAB-NODE-01**: 16 GiB DDR5 (1 free SODIMM slot) — P0 upgrade to 32 GiB.
- **LAB-NODE-02 E6430**: aging CPU (2012), no VT-d, candidate for retirement.
- **All hosts**: confirm lshw / dmidecode before buying RAM.

### Existing assets that should influence buying decisions

- **Do not buy around wishful assumptions.** Confirm what is already in service, what is already stored, and what is only “known to exist but not yet repaired”.
- **Storage already owned** (including items waiting for repair) should be logged in the private master list before buying new disks/NAS gear.
- **WSL2 on the primary Windows dev PC** is a valid interim “cheap capacity” option for extra Docker / pytest / smoke work if the machine is already available and Windows must stay on it.

---

## 2. Networking (LAN, Wi-Fi, firewall, redundancy)

- **P0**: automated LAB-ROUTER-01/switch/AP config backups; UPS for network equipment.
- **P1**: 2nd ISP link (failover), LAB-ROUTER-01 cold spare, VLAN isolation validation.
- **P2**: 2.5G/10G inter-host links.

### Redundancy questions to answer explicitly

- Is the current **LAB-ROUTER-01** the only firewall/router path?
- Is there a realistic **cold spare** path (same model, borrowable unit, or “buy later”)?
- Does the lab need **dual-WAN failover** now, or only after customer-facing uptime depends on it?

---

## 3. Power (Enel, solar, UPS)

- **P0**: UPS for network gear.
- **P1**: real consumption measurement, UPS for critical hosts, solar expansion review.
- **P2**: battery storage, critical load automation.

### Decision rule

- **Measure first** when possible: meter, clamp, smart plug, UPS telemetry, or solar inverter data.
- **Ask Enel for a load increase only after evidence** shows the current service is near the limit or blocks HVAC / UPS / server growth.

---

## 4. HVAC — cooling and environment

Photos (operator): LG Dual Inverter and Elgin 12000 BTU R32 Inverter. See pt-BR version for full analysis.

- **P0**: preventive maintenance on current HVAC.
- **P1**: new inverter HVAC if peak temperature threatens hardware.
- **P1**: temperature/humidity sensor with logging.
- **P2**: HVAC redundancy.

### Facility-first rule

- Before replacing the current HVAC, verify:
  - peak room temperature,
  - whether the reserve unit can be repaired cheaply,
  - whether electrical service / outlet / breaker support the chosen inverter model.

---

## 5. Software, subscriptions, tokens, training

- **P0**: GitHub, Cursor, domain(s).
- **P1**: AI tokens (Anthropic/Gemini), observability, Docker Hub plan.
- **P1 training**: CWL cyber, AI academy.
- **P2**: Cloud/DevOps/SRE training.

### OPEX categories to track privately

- **Core operator productivity**: GitHub, Cursor, domains, password manager.
- **AI / review capacity**: Anthropic, Gemini, OpenAI, token bursts, WRB.
- **Observability / distribution**: Grafana Cloud, Docker Hub, optional SaaS.
- **Training**: cyber, AI, infra/SRE, compliance/governance.

---

## 6. Investment sequence (summary)

```
Phase 1 (now, low cost):
  LAB-NODE-01 RAM → network UPS → LAB-ROUTER-01 config backup → external SSD → maintenance kit

Phase 2 (when budget allows):
  Temperature sensor → HVAC (if needed) → 2nd ISP → host UPS → Proxmox server

Phase 3 (growth):
  Solar expansion → Pi 4/5 → 2.5G switch → LAB-ROUTER-01 spare
  → heavy observability (Wazuh/Graylog)
```

### What this plan should change in other plans

- **Observability plans** should treat budget and RAM as explicit constraints, not afterthoughts.
- **Firewall / access plans** should call out where spend is required (UPS, ISP redundancy, cold spare).
- **Private economics notes** keep the real prices and vendor links; this tracked plan keeps the prioritization logic.

---

## 7. Tracking

- **Private list (real prices):** `docs/private/homelab/LAB_OP_SHOPPING_LIST_AND_POWER.pt_BR.md`
- **Public example (no prices):** `docs/ops/LAB_OP_SHOPPING_LIST_EXAMPLE.md`
- **PLANS_TODO.md:** LAB-OP CAPEX/OPEX & Procurement line.
- **Operator doc map:** `docs/ops/OPERATOR_LAB_DOCUMENT_MAP.md`

**State:** 🔄 Active — promote items P2→P1→P0 as evidence from host reports and real incidents accumulates.
