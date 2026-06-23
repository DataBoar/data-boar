# ADR 0068 — Primary Linux dev workstation (temporary)

- **Status:** Proposed
- **Date (UTC):** 2026-06-09
- **Authors:** Fabio Leitao
- **Deciders:** Fabio Leitao

### Status history

- 2026-06-09 — Proposed
- 2026-06-23 — Amended: Maestro canonical guard (#948) — orchestrator never align/overwrite target

## Context

The operator’s **Windows primary dev workstation** (ThinkPad **L-series**, Windows 11 + WSL2) failed on **2026-06-07** (**GSOD** / **CLOCK_WATCHDOG_TIMEOUT**, suspected **VRM**). It is under **Lenovo warranty repair** (case **E0482B2DMD**). Day-to-day **`data-boar`** development moved to **primary Linux dev workstation** (LMDE 7), which now holds the **canonical** Git clone (`~/Projects/dev/data-boar`).

Tracked policy still described a **Windows-only** “primary dev PC” (**`PRIMARY_WINDOWS_WORKSTATION_PROTECTION.md`**, **`.cursor/rules/primary-windows-workstation-protected-no-destructive-repo-ops.mdc`**, **ADR 0023** for **`es.exe`**). Assistants and operators on the Linux primary dev workstation had **no** Linux-equivalent blast-radius guard, and the Linux primary clone ran **`git commit`** without **`pre-commit install`**, bypassing PII and lint hooks.

| Surface | Before | Gap |
| --- | --- | --- |
| Canonical clone protection | Windows L-series role | Linux primary unprotected in docs/rules |
| Filename search | **`es-find.ps1`** / **`es.exe`** ([ADR 0023](ADR-0023-windows-primary-dev-filename-search-everything-es-first-with-fallback.md)) | Linux primary had no documented **`find`/`fd`/`plocate`** contract |
| Full PR gate | **`check-all.ps1`** on Windows | **`check-all.sh`** mandatory on the Linux primary dev workstation but not ritualized |
| Pre-commit on commit | Expected on primary clone | Linux primary clone never ran **`uv run pre-commit install`** |

## Decision

1. **Declare primary Linux dev workstation (LMDE 7) the temporary primary dev workstation** until the Windows laptop returns from Lenovo repair. Canonical clone path: **`~/Projects/dev/data-boar`** (**`DATA_BOAR_ROOT`** — placeholders in public docs).
2. **Add Linux protection docs and an always-on Cursor rule:** **`docs/ops/PRIMARY_LINUX_WORKSTATION_PROTECTION.md`** (+ **`.pt_BR.md`**) and **`.cursor/rules/primary-linux-workstation-protected-no-destructive-repo-ops.mdc`** — same destructive prohibitions as the Windows doc, adapted for Linux paths and **`/tmp/`** fresh-clone audits.
3. **Map operator tooling (Linux primary and lab-op SSH):**

   | Windows (primary when restored) | Linux primary / Linux |
   | --- | --- |
   | **`scripts/es-find.ps1`** / **`es.exe`** | **`find`**, **`fd`**, **`locate`/`plocate`** (**plocate 1.1.23** on primary Linux dev workstation) |
   | Content search (repo scripts) | **`git grep`**, **`grep -r`** |
   | **`check-all.ps1`** | **`./scripts/check-all.sh`** |
   | **`%TEMP%`** fresh-clone audits | **`/tmp/`** (or dedicated temp dir) |
   | Session keyword **`es-find`** | **Windows-only** — unchanged |

4. **[ADR 0023](ADR-0023-windows-primary-dev-filename-search-everything-es-first-with-fallback.md) remains `Accepted` and unchanged** — Windows **`es.exe`** / **`es-find`** protection applies again when the L-series primary returns from RMA. This ADR **does not** Supersede, Deprecate, or replace ADR 0023. On Linux primary, use Linux tools below instead of **`es-find`**. Lab-op SSH: **`find`**, **`fd`**, **`locate`/`plocate`**, **`git grep`**, **`grep -r`**.
5. **Mandatory quality ritual on the Linux primary dev workstation:** **`uv run pre-commit install`** once per clone; **`./scripts/check-all.sh`** green **before** every PR. Tracked in **`docs/plans/PLAN_PRIMARY_LINUX_WORKSTATION_PROTECTION.md`** ([#801](https://github.com/FabioLeitao/data-boar/issues/801)).
6. **Maestro canonical guard (GitHub #948):** the orchestrator / **`protect_canonical`** inventory node is **never** a WorkingTree rsync overwrite or **`lab-op-git-ensure-ref -Mode Reset`** target; ephemeral refs use **`/tmp/databoar_bench/<ref>`**. Implemented in **`scripts/maestro/Maestro-CanonicalGuard.ps1`** — fail-closed when flags are ambiguous.

## Reversion when Windows primary returns

When Lenovo repair completes and the operator confirms the Windows laptop is again the **canonical** dev workstation:

1. **Reprioritize protection docs:** resume **`PRIMARY_WINDOWS_WORKSTATION_PROTECTION.md`** + **`primary-windows-workstation-protected-no-destructive-repo-ops.mdc`** on that machine; run **`uv run pre-commit install`** on the Windows canonical clone if hooks are missing.
2. **Update this ADR or add a short amendment row** in **`docs/plans/PLAN_PRIMARY_LINUX_WORKSTATION_PROTECTION.md`**: record **end date** of Linux-primary period and whether **`DATA_BOAR_ROOT`** moved back to Windows or stays split (operator choice — document in **`docs/private/`**, not public paths).
3. **Linux primary role after reversion:** default = **lab-op / secondary** (Maestro, completão, SSH inventory) — **not** sole canonical clone unless the operator explicitly keeps development canonical on the Linux primary dev workstation and demotes Windows to secondary (requires a **new ADR** or amendment here).
4. **Do not delete** Linux protection docs — they remain valid for any future Linux-primary period and for **lab-op** filename search semantics.

## Consequences

- **Positive:** Linux primary canonical clone gets the same **destructive-op** and **PII hook** expectations as the former Windows primary; assistants stop assuming **`es-find`** on Linux.
- **Positive:** Clear **reversion checklist** when case **E0482B2DMD** closes.
- **Neutral:** Windows protection artifacts stay in-tree for repair completion — no mass rename of historical ADR/commits.
- **Risk:** Two “primary” narratives if reversion is not recorded — mitigate with plan checklist + private operator note on switch-over date.
- **Follow-up:** Close [#801](https://github.com/FabioLeitao/data-boar/issues/801); refresh **`AGENTS.md`**, **`docs/adr/README.md`**, **`docs/plans/PLANS_HUB.md`**, and **`docs/adr/INVENTORY.txt`** in the same PR.

## References

- **`docs/ops/PRIMARY_LINUX_WORKSTATION_PROTECTION.md`**
- **`docs/ops/PRIMARY_WINDOWS_WORKSTATION_PROTECTION.md`**
- **`docs/plans/PLAN_PRIMARY_LINUX_WORKSTATION_PROTECTION.md`**
- [ADR 0023](ADR-0023-windows-primary-dev-filename-search-everything-es-first-with-fallback.md)
- **`docs/ops/COMMIT_AND_PR.md`** · **`docs/ops/PII_PUBLIC_TREE_OPERATOR_GUIDE.md`** H.9–H.10
