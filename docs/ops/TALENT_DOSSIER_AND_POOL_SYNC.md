# Talent dossier workflow and pool sync snapshot

**Português (Brasil):** [TALENT_DOSSIER_AND_POOL_SYNC.pt_BR.md](TALENT_DOSSIER_AND_POOL_SYNC.pt_BR.md)

**Purpose:** Describe how to turn **team PDFs** in the private tree into **bilingual candidate dossiers** and refresh the **pool sync snapshot**, without hunting through `scripts/` every session.

**Audience:** Maintainer / operator only. **Do not** commit real `docs/private/` content.

---

## Prerequisites (local machine)

1. **PDFs** live under **`docs/private/team_info/`** (one PDF per person; file name becomes the dossier slug).
2. **Output folder** exists or will be created: **`docs/private/commercial/candidates/`**.
3. **Scaffold:** **`scripts/candidate-dossier-scaffold.ps1`** (tracked in the repo).

If those paths are missing, create them on the operator machine only (see **`docs/private.example/commercial/candidates/README.md`**).

---

## Shorthand: `talent-dossier`

Dot-source the helper from PowerShell (optional; add to **`$PROFILE`** for a persistent alias):

```powershell
. "C:\path\to\data-boar\scripts\talent-dossier.ps1"
```

**Repo root resolution (in order):**

1. **`--repo-root <path>`** on the command line.
2. Environment variable **`DATA_BOAR_REPO_ROOT`** (directory of the clone).
3. Parent of the **`scripts/`** folder where **`talent-dossier.ps1`** lives (portable default).

---

## Subcommands

| Subcommand | What it does |
| ---------- | ------------- |
| **`next`** (default) | Pick the first **pending** PDF: one that does **not** yet have **both** `slug.md` and `slug.pt_BR.md` under `candidates/`. Run the scaffold. Optionally loop until no pending PDFs remain. |
| **`list`** / **`status`** | List pending PDFs and whether each is **MISSING** or **PARTIAL** (only one language file). |
| **`network`** / **`export-network`** / **`exportmesh`** | Run **`scripts/export_talent_relationship_mermaid.py`** to refresh relationship map exports. |

---

## Common flags (`next`)

| Flag | Effect |
| ---- | ------ |
| **`--advisor-remote`** | Passes **`-AdvisorRemote`** to the scaffold (remote advisor / non-customer-facing default). |
| **`--caution`** / **`--low-priority-caution`** | Passes **`-LowPriorityCaution`** (extra guardrails in the generated dossier). |
| **`--no-loop`** | Generate **one** dossier then stop (default **`next`** loops through all pending PDFs). |
| **`--dry-run`** | Print the next PDF that would be processed; do **not** write files. |
| **`--overwrite`** | Allow replacing existing `slug.md` / `slug.pt_BR.md` (use with care). |
| **`--operator-relationship <TAG>`** | Forwarded to the scaffold (manual relationship tag when file name inference is not enough). |

**Examples:**

```powershell
talent-dossier next --advisor-remote --caution
talent-dossier list
talent-dossier next --no-loop --dry-run
```

---

## Pool sync snapshot

After **`next`** completes at least one generation in a loop, the helper runs **`scripts/generate_pool_sync_snapshot.py`** so **`docs/private/commercial/POOL_SYNC_SNAPSHOT_YYYY-MM-DD.md`** reflects PDFs vs dossier files **for that day**.

You can run the generator manually:

```powershell
uv run python scripts/generate_pool_sync_snapshot.py --repo-root . --date 2026-04-02
```

---

## Related scripts and docs

| Item | Role |
| ---- | ---- |
| **`scripts/ats.ps1`** + **`scripts/ats-profile.ps1`** | Separate **ATS / pool** shortcuts (import, scan, list). Not a substitute for dossier generation; complementary. |
| **`docs/TALENT_POOL_LEARNING_PATHS.md`** | Public **role archetypes** (A–F); no personal data. |
| **`docs/ops/LINKEDIN_ATS_PLAYBOOK.md`** | Public **LinkedIn + ATS** playbook (headline, skills, cadence, SSI context). |
| **`docs/private.example/commercial/candidates/LEARNING_ROADMAP_TEMPLATE.md`** | Template for per-person **private** learning roadmaps (not committed). |

---

## Revision

| Date | Note |
| ---- | ---- |
| 2026-04-02 | Initial runbook; portable repo root for `talent-dossier.ps1`. |
