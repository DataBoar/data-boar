# Plan: Plugin SDK guide (Enterprise remediation — L1)

<!-- plans-hub-summary: Guia de desenvolvimento de plugins Enterprise — Protocol, interface, exemplos, segurança -->
<!-- plans-hub-related: PLAN_REMEDIATION_INTERFACE.md, PLAN_YAML_PLUGIN_SYSTEM.md -->

**Status:** Active
**Date:** 2026-08-03
**Authors:** Fabio Leitao
**Priority:** H1

**GitHub:** [#611](https://github.com/DataBoar/data-boar/issues/611) · depends on [#606](https://github.com/DataBoar/data-boar/issues/606) · epic [#865](https://github.com/DataBoar/data-boar/issues/865) (L2/L3) · follow-up [#1443](https://github.com/DataBoar/data-boar/issues/1443)

**Synced with:** [PLANS_TODO.md](PLANS_TODO.md)

**Related:** [PLAN_REMEDIATION_INTERFACE.md](PLAN_REMEDIATION_INTERFACE.md) (host hook + manifest), [PLAN_YAML_PLUGIN_SYSTEM.md](PLAN_YAML_PLUGIN_SYSTEM.md) (YAML **pattern** plugins — different surface), [ADR-0059](../adr/ADR-0059-remediation-plugin-architecture.md)

---

## Problem

[#606](https://github.com/DataBoar/data-boar/issues/606) shipped `core/plugins/` (`RemediationPlugin`, loader, fail-graceful hook, Enterprise gate). Without a partner-facing SDK guide, third parties cannot build against the real contract — the hook exists but the ecosystem cannot grow.

---

## Goal

Ship bilingual operator/partner docs that describe **only** the real L1 API:

- Protocol members and `PluginError`
- `module.path:ClassName` loading + YAML `remediation:` block
- Tier gate + fail-graceful Safe-Hold
- Minimal Python example + local test via **direct** `remediate()`
- Honest note that automatic findings JSONL wiring is follow-up **#1443**
- Security: same-process trust; L2/L3 → epic **#865**

Public paths: `docs/PLUGIN_SDK.md` + `docs/PLUGIN_SDK.pt_BR.md` (no pricing / commercial numbers).

---

## Phases

| Phase | Deliverable | Status |
| ----- | ----------- | ------ |
| **1 – L1 SDK guide** | EN + pt-BR PLUGIN_SDK, hub/README/USAGE/TECH_GUIDE cross-refs, this plan | 🔄 **#611** (this PR) |
| **2 – Findings path honesty** | After **#1443**, refresh “test locally / automatic wiring” sections | ⬜ |
| **3 – L2/L3 SDK chapters** | Document sandbox / sidecar when epic **#865** lands APIs | ⬜ |

---

## Non-goals

- Implementing a sample remediator product in core.
- Changing the Protocol signature (that is **#1443** / remediation plan phases).
- Duplicating YAML pattern-plugin authoring (see `PLAN_YAML_PLUGIN_SYSTEM` / ADR-0052).

---

## Acceptance (plan)

- [x] `docs/PLUGIN_SDK.md` + `.pt_BR.md` cover Protocol, I/O contract, example, register, test, security, use-case examples
- [x] Cross-refs to USAGE + TECH_GUIDE (+ docs README row)
- [x] This plan + `plans_hub_sync.py --write` + `PLANS_TODO.md` entry
- [ ] Refresh after **#1443** (automatic findings path)
