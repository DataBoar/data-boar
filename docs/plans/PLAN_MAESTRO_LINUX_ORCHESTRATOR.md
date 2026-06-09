# Plan: Maestro Linux orchestrator portability

**Status:** Active
**Date:** 2026-06-03
**Authors:** Fabio Leitao
**Priority:** H1
**GitHub:** [#786](https://github.com/FabioLeitao/data-boar/issues/786)

<!-- plans-hub-summary: portabilização do Maestro para orquestrador Linux (wsl.exe→bash nativo, podman fallback, git_origin no inventory) -->
<!-- plans-hub-related: PLAN_MAESTRO_BENCHMARK_METRICS_AND_FIX.md, docs/ops/LAB_COMPLETAO_RUNBOOK.md -->

## Context

The Maestro pre-flight orchestrator ran on **L14** (Windows 11 + WSL2). The canonical dev/orchestrator host is now **T14** (LMDE 7, native Linux). Three pre-flight bugs block completão runs without Windows-specific assumptions.

## Scope

| # | Bug | File | Fix |
| - | --- | ---- | --- |
| 1 | `wsl.exe` required for WorkingTree rsync | `Sync-WorkingTree.ps1` | `$IsWindows` → WSL; else native `bash -c` |
| 2 | Ref-fetch hardcodes `git@github.com:…` | `Sync-WorkingTree.ps1` | Optional `git_origin` on inventory node |
| 3 | Build artefact assumes Docker only | `Build-ContainerArtefact.ps1` | `Test-ContainerEngineReady` → docker then podman |

**Out of scope (this plan):** handler logic, inventory schema beyond optional `git_origin`, `docs/private/` inventory content.

## Inventory: optional `git_origin`

Nodes that cannot reach GitHub directly (e.g. air-gapped lab, LAN-only fetch) may set:

```json
{
  "hostname": "alpine-emachines",
  "git_origin": "ssh://leitao@t14-leitao/home/leitao/Projects/dev/data-boar",
  "path": "~/Projects/dev/data-boar",
  "user": "leitao"
}
```

When absent, Ref-fetch keeps the canonical default: `git@github.com:FabioLeitao/data-boar.git`.

## Implementation checklist

| Phase | Task | Status |
| ----- | ---- | ------ |
| 1 | Bug 1 — `$IsWindows` rsync guard | ✅ |
| 2 | Bug 2 — `$Node.git_origin` override | ✅ |
| 3 | Bug 3 — podman fallback in `Build-ContainerArtefact.ps1` | ✅ |
| 4 | `tests/test_maestro_scripts.py` guards | ✅ |
| 5 | Pre-flight on T14 against real inventory | ⬜ Operator |

## Verification

```powershell
# From repo root on T14 (pwsh 7.6+)
pwsh -NoProfile -File scripts/maestro/Maestro.ps1 -WhatIf   # if supported
uv run pytest tests/test_maestro_scripts.py -q
```

Operator: one WorkingTree sync + one Ref-fetch node with custom `git_origin` + build with podman-only engine.

## References

- [LAB_COMPLETAO_RUNBOOK.md](../ops/LAB_COMPLETAO_RUNBOOK.md)
- [PLAN_MAESTRO_BENCHMARK_METRICS_AND_FIX.md](PLAN_MAESTRO_BENCHMARK_METRICS_AND_FIX.md)
