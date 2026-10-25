---
name: doc-hubs-plans-sync
description: Use when editing docs/plans (PLANS_TODO, PLANS_HUB, PLAN_*), docs/MAP*, docs/README hub rows, docs/adr index, or AGENTS ADR pointer—keep hubs aligned with repo truth and ADR policy.
---

# Doc hubs and plans sync (agent + maintainer ritual)

## What is already enforced (no drift “silencioso”)

| Gate | What it guards | Command |
| ---- | -------------- | ------- |
| **plans-hub** | `PLANS_HUB.md` table matches every `PLAN_*.md` (open + `completed/`) | `python scripts/plans_hub_sync.py --check` / `--write` |
| **plans-stats** | Status dashboard block in `PLANS_TODO.md` matches tables | `python scripts/plans-stats.py --check` / `--write` |
| **Pre-commit / CI** | Same hooks as `.\scripts\check-all.ps1` Lint job | `uv run pre-commit run --all-files` |
| **Tests** | `tests/test_plans_hub_sync.py`, `tests/test_plans_stats.py`, `tests/test_docs_external_no_plan_links.py`, markdown lint | Part of `check-all` |

These **do not** auto-edit **MAP.md**, **README** pitch tables, or **AGENTS.md** ADR guidance prose—that is **human/agent ritual** below. **AGENTS.md** does **not** carry a hardcoded “current last ADR” number (it goes stale); agents discover the latest file on disk or run **`.\scripts\new-adr.ps1`** (auto-numbering).

## Ritual — after a **notable** sequencing or plan-file change

1. **`PLANS_TODO.md`:** update rows / dependency narrative (English-only history per policy).
2. **`python scripts/plans-stats.py --write`** if any status table row changed.
3. **New / renamed / `git mv` archived `PLAN_*.md`:** `python scripts/plans_hub_sync.py --write`; fix broken links per **`.cursor/rules/docs-plans.mdc`**.
4. **`.\scripts\check-all.ps1`** (or at least `uv run pre-commit run --all-files`) before commit.

## Ritual — after a **new or materially changed ADR**

1. **`docs/adr/README.md`** and **`docs/adr/README.pt_BR.md`:** index row + consequences if needed.
2. Do **not** edit **AGENTS.md** just to bump a “last ADR” number—**AGENTS.md** intentionally avoids that hardcode. Use **`.\scripts\new-adr.ps1`** for the next id or list **`docs/adr/ADR-*.md`** sorted to see the latest.
3. If the ADR changes operator-facing claims: touch **MAP** / **COMPLIANCE_AND_LEGAL** / **USAGE** pointers as appropriate (same PR when possible).

## Ritual — after **MAP.md** / **docs/README** hub edits

1. **Pair languages:** edit **`MAP.pt_BR.md`** / **`docs/README.pt_BR.md`** in the same PR as EN when the change is not EN-only typo.
2. **Broken links:** every `(...)` target under `docs/` should resolve; run **`uv run pytest tests/test_markdown_lint.py`** if you touched many links.
3. **ADR 0004:** do not add new markdown links from **external-tier** product docs into `docs/plans/`; MAP already points to **docs/README** for plans entry.

## Honest limits

- **MAP** is a **concern index**, not generated from SQLite or plans—drift is prevented by **review + PR discipline**, not by a second auto-table today.
- **“Truth”** for sequencing remains **`PLANS_TODO.md`** + **`PLANS_HUB.md`** after the scripts above—not social posts or chat summaries.

## Quick copy-paste

```powershell
cd <repo-root>
python scripts/plans_hub_sync.py --write
python scripts/plans-stats.py --write
.\scripts\check-all.ps1
```

When only docs/markdown changed: **`.\scripts\lint-only.ps1`** may be enough if you did not touch Python—still run **plans** scripts if plans files changed.
