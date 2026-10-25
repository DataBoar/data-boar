# Private notes — template (tracked in Git)

**This folder is versioned** so new clones get a **layout to copy**. Your **real** notes must live under **`docs/private/`**, which is **gitignored** — copy like this:

**Example vs real tree:** Tracked stubs under **`private.example/`** use neutral folder names (**`org-notes/`**, **`economics/`**). Your live **`docs/private/`** tree may use different names (e.g. **`employers/`**, **`operator_economics/`**) — see **[PRIVATE_OPERATOR_NOTES.md](../PRIVATE_OPERATOR_NOTES.md)** for the operator layout table.

Optional **local notify** (Signal/SMS/SMTP credentials for operator digests): copy **`private.example/notify/README.md`** into **`docs/private/notify/`** and follow that template—still **gitignored** once under `docs/private/`.

**Partner / client feedback inbox (WRB-style):** read **`private.example/feedbacks-inbox/README.md`**. The real drop folder **`docs/feedbacks, reviews, comments and criticism/`** is **gitignored** at repo root (not under `docs/private/`); create it locally when you start collecting reviews.

```bash
# From repo root (Linux/macOS/Git Bash)
mkdir -p docs/private/homelab docs/private/author_info docs/private/notify docs/private/commercial docs/private/operator_economics docs/private/academic docs/private/security_audit docs/private/scripts
cp docs/private.example/homelab/README.md docs/private/homelab/
cp docs/private.example/commercial/README.md docs/private/commercial/
cp docs/private.example/economics/README.md docs/private/operator_economics/
# Optional: seed re-teach structure (EN and/or pt-BR); rename locally e.g. to a single OPERATOR_RETEACH.md
# cp docs/private.example/homelab/OPERATOR_RETEACH.md docs/private/homelab/
# cp docs/private.example/homelab/OPERATOR_RETEACH.pt_BR.md docs/private/homelab/
cp docs/private.example/author_info/README.md docs/private/author_info/
cp docs/private.example/academic/README.md docs/private/academic/
cp docs/private.example/notify/README.md docs/private/notify/
cp docs/private.example/security_audit/PII_LOCAL_SEEDS.example.txt docs/private/security_audit/PII_LOCAL_SEEDS.txt
cp docs/private.example/scripts/clean-slate.sh.example docs/private/scripts/clean-slate.sh
chmod +x docs/private/scripts/clean-slate.sh
# Add docs/private/scripts/README.pt_BR.md locally (full operator doc; not required to match example)
# Optional: cite Dockerfiles (wf_t1r, uptk) in one place for thesis/CV
# cp docs/private.example/Dockerfiles_used.md docs/private/
```

```powershell
# Windows (PowerShell, repo root)
New-Item -ItemType Directory -Force -Path docs/private/homelab, docs/private/author_info, docs/private/notify, docs/private/commercial, docs/private/operator_economics, docs/private/academic, docs/private/security_audit, docs/private/scripts | Out-Null
Copy-Item docs/private.example/homelab/README.md docs/private/homelab/
Copy-Item docs/private.example/commercial/README.md docs/private/commercial/
Copy-Item docs/private.example/economics/README.md docs/private/operator_economics/
# Optional: Copy-Item docs/private.example/homelab/OPERATOR_RETEACH*.md docs/private/homelab/
Copy-Item docs/private.example/author_info/README.md docs/private/author_info/
Copy-Item docs/private.example/academic/README.md docs/private/academic/
Copy-Item docs/private.example/notify/README.md docs/private/notify/
Copy-Item docs/private.example/security_audit/PII_LOCAL_SEEDS.example.txt docs/private/security_audit/PII_LOCAL_SEEDS.txt
Copy-Item docs/private.example/scripts/clean-slate.sh.example docs/private/scripts/clean-slate.sh
# Optional: Copy-Item docs/private.example/Dockerfiles_used.md docs/private/
```

Then edit files **only** under `docs/private/` — Git ignores that tree (`git check-ignore -v docs/private/homelab/README.md`).

**Policy:** Read **[PRIVATE_OPERATOR_NOTES.md](../PRIVATE_OPERATOR_NOTES.md)** (tracked).

**Optional local history for the whole private tree:** `git init` inside `docs/private/` gives a **second** repository whose commits **never** push with the product repo—see **[PRIVATE_LOCAL_VERSIONING.md](../ops/PRIVATE_LOCAL_VERSIONING.md)** ([pt-BR](../ops/PRIVATE_LOCAL_VERSIONING.pt_BR.md)).

**Optional operator runbook (private only, create locally):** after you have `docs/private/`, add **`OPERATOR_LAB_STUDY_AND_PRIVATE_GIT.pt_BR.md`** at the root of `docs/private/` (bootstrap text lives only on your machine; this tracked README cannot ship the file). It covers nested-git commands, LAB-OP/LAB-NODE-01 pointers, study sequence (IA ↔ cyber / CCA prep), and tech-debt links—see also **`author_info/RECENT_OPERATOR_SYNC_INDEX.pt_BR.md`**.
