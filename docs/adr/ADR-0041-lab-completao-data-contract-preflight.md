# ADR 0041 — Lab completão data contract preflight (optional)

## Context

Lab completão orchestration historically validated **reachability** (SSH, `uv`, Docker/Podman) and could start **scans** against databases whose **schemas drifted** (renamed columns, dropped tables). That wastes time and blurs “product defect” vs “test fixture mismatch”.

## Decision

Add an **optional** preflight step, wired into **`scripts/lab-completao-orchestrate.ps1`**, that runs **`scripts/lab_completao_data_contract_check.py`** when the private manifest sets **`completaoDataContractsPath`** to a YAML file.

- The YAML lists **required column names** per **schema + table**, using **SQLAlchemy URLs from environment variables** (`connection.url_from_env`) — **no secrets in YAML**.
- The checker runs **after** **`lab-op-git-ensure-ref`** and **before** per-host SSH smoke so failures fail **fast** and deterministically.
- Operators can bypass with **`-SkipDataContractPreflight`** when intentionally skipping contracts.

Tracked documentation: **`docs/ops/LAB_COMPLETAO_RUNBOOK.md`**; example contracts: **`docs/private.example/homelab/completao_data_contracts.example.yaml`**.

## Consequences

- **Exit semantics:** **`lab_completao_data_contract_check.py`** follows **`DATA_BOAR_COMPLETAO_EXIT_v1`** (documented in **`docs/ops/LAB_COMPLETAO_RUNBOOK.md`**): **0** ok, **1** connectivity/credentials, **2** schema/contract shape, **3** reserved for future compliance hooks.
- **Positive:** clearer separation between **fixture/schema regressions** and **scanner regressions**; reproducible completão when lab DB shape is part of the contract.
- **Negative:** operators must maintain the YAML + session env vars; mis-set manifest path is a **hard error** (intentional: silent skip would hide misconfiguration).
- **Scope:** v1 validates **column presence** only (not types, constraints, or row counts). Extend later if needed.

## References

- `scripts/lab_completao_data_contract_check.py`
- `scripts/lab-completao-orchestrate.ps1`
- `docs/private.example/homelab/completao_data_contracts.example.yaml`
