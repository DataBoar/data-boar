# Doc bundle recovery playbook (after a manual `cat` / copy mess)

**Portuguese (Brazil):** [DOC_BUNDLE_RECOVERY_PLAYBOOK.pt_BR.md](DOC_BUNDLE_RECOVERY_PLAYBOOK.pt_BR.md)

**Scope:** You accidentally concatenated, moved, or duplicated Markdown/YAML (e.g. Explorer + `cat`), and you want to **confirm nothing tracked was lost** and to **regain a safe workflow**. This is **operator / maintainer** procedural text — not product user documentation.

**Does not replace:** normal delivery gates (**`.\scripts\check-all.ps1`**, pre-commit, full pytest). Use this playbook **after** incidents involving **local trees** or **ad-hoc bundles**, not for routine PR quality.

---

## Blameless baseline

1. **Git remains the source of truth** for anything **tracked**. `origin/main` (or your release tag) is the comparison anchor.
1. **Heuristics** (H1 split, sliding windows, prefix hints) reduce anxiety and surface suspects; they **do not prove** data loss or integrity.
1. **Prevention:** generate LLM bundles only via **`scripts/export_public_gemini_bundle.py`** (with **`--verify`**), not raw shell globs — see **[GEMINI_PUBLIC_BUNDLE_REVIEW.md](GEMINI_PUBLIC_BUNDLE_REVIEW.md)**.

---

## Recovery order (do roughly this sequence)

| Step | Goal                                                               | Command / action                                                                                                                                                                                                                                             |
| ---- | ----                                                               | ------------------                                                                                                                                                                                                                                           |
| 1    | Stop the bleeding                                                  | Do not mass-save over tracked files. Copy suspicious blobs under **`docs/private/...`** only (gitignored).                                                                                                                                                   |
| 2    | Sync refs                                                          | `git fetch origin` and compare: `git status -sb`, `git diff --name-only origin/main`.                                                                                                                                                                        |
| 3    | Restore tracked paths from Git                                     | Per path: `git restore path` or `git restore --source=origin/main -- path`. Entire tree example: `git restore --source=origin/main -- docs/` (careful: discards **local** changes under that path).                                                          |
| 4    | Rebuild a **known-good** bundle (optional)                         | `uv run python scripts/export_public_gemini_bundle.py --output docs/private/gemini_bundles/recovery_$(date -I).txt --compliance-yaml --verify`                                                                                                               |
| 5    | Forensics on **your** messy blob                                   | If you kept a concatenated file, run the **meta script** below or the individual Python tools (steps 6–7).                                                                                                                                                   |
| 6    | Byte-faithful split (best if you still have **exact `cat` order**) | `uv run python scripts/audit_concatenated_markdown.py -i blob.md --cat-order order.txt` — generate **`order.txt`** with `--emit-order-glob` (see script `--help` and GEMINI doc).                                                                            |
| 7    | Headerless / unknown order                                         | **Sliding window:** `uv run python scripts/audit_concat_sliding_window.py -i blob.md --window 25` and add **`--strip-bundle-markers`** if the blob used `--- FILE: ... ---`. **H1 split:** `uv run python scripts/audit_concatenated_markdown.py -i blob.md` |

**PowerShell (step 4):** the `$(date -I)` snippet is for **bash** only. On Windows use `--output "docs/private/gemini_bundles/recovery_$(Get-Date -Format 'yyyy-MM-dd').txt"` (see **[GEMINI_PUBLIC_BUNDLE_REVIEW.md](GEMINI_PUBLIC_BUNDLE_REVIEW.md)**).

---

## One-shot meta script (Windows)

From repo root:

```powershell
# Tooling sanity only (pytest compile checks for the three Python helpers)
.\scripts\recovery-doc-bundle-sanity.ps1

# Full local forensic pass on a saved blob (adjust path)
.\scripts\recovery-doc-bundle-sanity.ps1 -BundlePath "docs\private\mess_concatenated_gemini_sanity_check\sobre-data-boar.md" -Headerless -SlidingWindow 25

# Include verbose H1 chunk audit (long console output)
.\scripts\recovery-doc-bundle-sanity.ps1 -BundlePath "docs\private\...\blob.md" -IncludeH1Audit
```

**Parameters (summary):** see **`Get-Help .\scripts\recovery-doc-bundle-sanity.ps1`**. Typical flags: **`-BundlePath`**, **`-Headerless`** (passes **`--strip-bundle-markers`** to the sliding-window step), **`-SlidingWindow`**, **`-SkipPytest`**, **`-IncludeH1Audit`**, **`-DryRun`**.

---

## Multi-pass window sweep (noise vs signal)

**Smaller** `--window` values match more easily (often **higher % covered**, fewer gap blocks). **Larger** windows are stricter and can “break” coverage at file edges. Run **two** sweeps when unsure: without and with **`--rstrip-lines`**. If both tables are **identical**, trailing spaces were not the barrier; if `rstrip` shrinks gaps, you had whitespace drift only.

```bash
uv run python scripts/audit_concat_sliding_window.py -i docs/private/.../blob.md \
  --strip-bundle-markers --sweep-windows 12,15,18,22,25,30
uv run python scripts/audit_concat_sliding_window.py -i docs/private/.../blob.md \
  --strip-bundle-markers --rstrip-lines --sweep-windows 12,15,18,22,25,30
```

**Heuristic:** gap ranges that **persist** across several window sizes (e.g. the same line band at 18 and 25) are better hand-triage targets than ranges that only appear at a single huge window (often boundary noise). About **five** sizes in the 12–30 band is usually enough before diminishing returns.

---

## Final round bucket (“boss level”) — extra restored traces

When you discover **more** recovered copies later (“undelete” / Explorer / backup), **do not** scatter them randomly: put them under **`docs/private/mess_concatenated_gemini_sanity_check/final_round_bucket/`** (same private tree as the first sanity pass — gitignored). A local **`README.md`** there explains the same commands.

**Workflow:** copy blob(s) in → run **`--sweep-windows`** (and optional **`recovery-doc-bundle-sanity.ps1`**) on **each** new file → compare gap tables to your first-pass blob if helpful. **Git + `main`** remain the authority; this folder is **only** for confidence / archaeology.

**Perfectionism stop rule:** if `git status` is clean against `origin/main`, first-pass heuristics already showed **~99%+** coverage, and the new blob does not claim to replace tracked content, **declare victory** and move on.

### One-shot concat + name map (many loose files)

When the bucket is a pile of **separate** `.md` / `.yaml` / `.htm` / `.html` saves (browser export, undelete), use **`scripts/build_final_round_bucket_concat.py`** to build a single blob with `--- FILE: … ---` markers, optionally print **basename alignment** against the tracked tree (excluding `docs/private/`), and optionally run the **multi-pass sliding-window** sweep in one go.

```bash
# Basename clues: exact name, stem-normalized (e.g. "File (1).htm"), or no tracked peer
uv run python scripts/build_final_round_bucket_concat.py --map-names

# Write default concat (under the bucket): .../final_round_bucket/_concat_for_sliding_window.md
uv run python scripts/build_final_round_bucket_concat.py

# Build + compact sweep table (same defaults as manual --sweep-windows 12,15,18,22,25,30)
uv run python scripts/build_final_round_bucket_concat.py --sweep --quiet-gaps

# Also try trailing-whitespace normalization on corpus + input
uv run python scripts/build_final_round_bucket_concat.py --sweep --quiet-gaps --rstrip-lines
```

Flags: **`--bucket`**, **`--output`**, **`--repo-root`**, **`--sweep-windows`**, **`--dry-run`**. HTML inputs are tag-stripped to approximate text lines for the matcher (not byte-faithful to Markdown sources).

---

## How to interpret results

- **Sliding-window “% covered”** near **100%** on a blob that should mirror **current `main`**: strong signal your tree is aligned; small gaps are often **boundary lines**, **text drift** since the snapshot, or **glue** between files — triage the printed gap previews, not the percentage alone.
- **`audit_concatenated_markdown.py` (H1)** “no exact match”: may still be recoverable via Git or a **prefix hint**; chunks can be **old edits** or **non-doc** snippets.
- **`export_public_gemini_bundle.py --verify` failing**: your working tree **differs** from what was written into the bundle — regenerate or fix files before trusting the export.

---

## Lessons learned (short)

- Prefer **`git ls-files`**-driven exports and **`--verify`**, not **`cat *.md`**, for LLM attachments.
- Keep **one** private “sanity” copy of blobs under **`docs/private/`**; avoid pasting LAN paths or secrets into **tracked** docs.
- Run **`recovery-doc-bundle-sanity.ps1`** or the individual scripts after an incident to **document confidence** (SRE-style) without pretending heuristics are cryptographic proof.

---

## Related links

- **[GEMINI_PUBLIC_BUNDLE_REVIEW.md](GEMINI_PUBLIC_BUNDLE_REVIEW.md)** — safe bundle build, prompts, tool list.
- **`scripts/audit_concatenated_markdown.py`**, **`scripts/audit_concat_sliding_window.py`**, **`scripts/export_public_gemini_bundle.py`**, **`scripts/build_final_round_bucket_concat.py`** — source of truth for flags and behaviour.
- **[COMMIT_AND_PR.md](COMMIT_AND_PR.md)** — normal hygiene after the tree is clean.
