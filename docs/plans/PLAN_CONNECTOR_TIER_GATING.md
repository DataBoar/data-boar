# PLAN: Connector tier gating (registry enforcement)

**Status:** In progress
**Date:** 2026-06-11
**Authors:** Fabio Leitao
**Priority:** H0
**Depends on:** #719 (env bypass removed), #704 (licensing matrix green)

**Owner:** Fabio Leitao
**Relates to:** `PLAN_PRODUCT_TIERS_AND_OPEN_CORE.md`, `LICENSING_SPEC.md`, issues #843, #705, #610 (pricing docs)
**Tier:** boundary definition — Community vs Pro connectors

---

## Context

The `FEATURE_TIER_MAP` (`core/licensing/tier_features.py`) tiered some cloud
connectors (Snowflake/SAP/S3/Azure/GCS = Pro), but the implemented corporate
connectors stayed OUT of the map — de facto free in open-core: PowerBI,
SharePoint, Dataverse, WebDAV, SMB/CIFS, NFS, MSSQL, Oracle. Worse, the
connector registry did not call `require_feature` at instantiation, so there
was no per-connector shielding (the licensing matrix #704 enforces at the API
route level only).

## Boundary (operator decision, ratified 2026-06-11)

| Tier | Connectors |
| ---- | ---------- |
| **Open-core** | filesystem · self-hosted SQL/NoSQL (sqlite/pg/mysql/mongo/redis) · compressed · generic REST |
| **Pro** | PowerBI, SharePoint, Dataverse, WebDAV, SMB/CIFS, NFS, MSSQL, Oracle + Snowflake/SAP/S3/Azure/GCS |
| **Enterprise** | plugin/partner remediation · CMDB connectors · findings-sink to corp DB · scheduled-scan UI |

Principles (non-negotiable): open-core stays useful (never gate "scan your
own data soup"); fail-loud actionable errors + `scan_failures` row (never a
silent skip); gate bites only in `licensing.mode: enforced` — `Tier.OPEN`
stays free for dev and lab.

## Phases

| Phase | Deliverable | Status |
| ----- | ----------- | ------ |
| A | `FEATURE_TIER_MAP` completed: `connector_rest` (Community) + 9 corporate connectors (Pro) + 4 features from #705 | ✅ Done |
| B | Registry gate: `require_connector_allowed()` in `core/connector_registry.py`; engine `_run_target` uses it (actionable error + `tier_blocked` scan_failure) | ✅ Done |
| C | Per-connector gating tests (`tests/test_connector_tier_gating.py`): map entries, target resolution, community/pro/OPEN behaviour, enforced JWT end-to-end, engine failure row | ✅ Done |
| D | Pricing/tier docs refresh (#610 `PRICING.md` does not exist yet — boundary documented in `tier_features.py` docstring and this plan until #610 lands) | ⬜ Pending |
| E | Enterprise connector families (CMDB, findings-sink) gated when implemented | ⬜ Pending |

## Notes

- `powerapps` targets map to `connector_dataverse` (same connector family).
- MSSQL/Oracle gate via `type: database` + `driver` prefix; postgres, mysql,
  sqlite drivers are intentionally unmapped (open-core).
