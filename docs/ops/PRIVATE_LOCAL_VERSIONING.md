# Local versioning for `docs/private/` (never GitHub)

**Português (Brasil):** [PRIVATE_LOCAL_VERSIONING.pt_BR.md](PRIVATE_LOCAL_VERSIONING.pt_BR.md)

**Purpose:** Keep a **revision history** of your gitignored private tree (notes, estimates, financing drafts, “thinking journal”) **without** attaching it to the **public** Data Boar repository or GitHub.

---

## 1. Is it possible?

**Yes.** The main repo lists **`docs/private/`** in **`.gitignore`**, so:

- Nothing under that path is committed when you work in the product repo.
- A **nested** **`.git`** directory inside **`docs/private/`** is also ignored by the parent repo (same ignore rule). It becomes a **separate Git repository** whose history stays **local** (or on **your** backup remote), not on `origin` of this project.

You still get a **single workspace** in Cursor: **`data-boar/`** (clone of **FabioLeitao/data-boar**) with **`docs/private/`** inside it—only **two** Git histories if you choose to init the inner repo.

---

## 2. Recommended pattern: nested Git at `docs/private/`

From repo root (after `docs/private/` exists):

```bash
cd docs/private
git init
# Optional: main as default branch name
git branch -M main
git add .
git commit -m "chore: bootstrap private notes repo"
```

## Remotes (pick one):

| Option                  | Use when                                                                                                                  |
| ------                  | --------                                                                                                                  |
| **No remote**           | You only want history on this disk; backups are copies/USB/restic.                                                        |
| **`file://` bare repo** | Second folder on disk or NAS, e.g. `git remote add backup file:///path/to/private-notes.git` then `git push backup main`. |
| **Self-hosted SSH**     | Your own server—not GitHub—if you want off-PC history without publishing product-adjacent strategy.                       |

**Do not** add a GitHub (or public) remote for this tree unless you **explicitly** want that content online.

---

## 3. Other version-control tools (Mercurial, Bazaar)

**Possible** (e.g. `hg init` in `docs/private/`), but you add a second toolchain and mental overhead. **Git-only** is enough for most operators and matches backup tutorials. Use **Hg/Bzr** only if you already rely on them elsewhere.

---

## 4. “Separate folder that feels like the same tree”

Alternatives:

- **Sibling directory** (e.g. `~/private-data-boar-notes`) with its own Git repo, and **shortcuts** or **sync** into `docs/private/`—more moving parts.
- **Directory junction / symlink** on Windows—works for some setups; **breaks** if paths or sync tools disagree. Prefer **nested Git** under **`docs/private/`** unless you have a strong reason.

---

## 5. Backups (still local or controlled)

- **Encrypted** external drive or **restic**/similar to a bucket you control.
- **`git bundle create`** periodic snapshots if you want single-file exports.
- If you use **pCloud / `P:`**, treat it as **convenience**, not a secrets vault; encryption-at-rest policy is your decision.

---

## 6. What to store for motivation, funding, and estimates

Keep **numbers, comparisons, and narrative** that would be awkward on GitHub under **`docs/private/operator_economics/`** (and **`commercial/`** when client-facing). Suggested filenames (create locally; see **[private.example/operator_economics/README.md](../private.example/operator_economics/README.md)**):

- **Phase effort (demo / beta / production):** rough ranges, assumptions, who could help—good for **you** and for **assistant context** when you ask for planning help.
- **Financing / budget / purchase comparisons:** options, links, “why this vendor”—still **private** if it reveals runway or strategy.
- **Q&A / thinking journal:** dated entries (questions, answers, follow-ups)—like a **private blog**; link from **`author_info/RECENT_OPERATOR_SYNC_INDEX.pt_BR.md`** if useful.

**Tracked** product plans stay in **`docs/plans/`**; use private files for **sensitive** or **preliminary** numbers, then **promote** only what is safe into plans when ready.

---

## 7. Safety reminders

- **`tests/test_confidential_commercial_guard.py`** still applies: never **`git add -f docs/private/...`** into the **main** repo.
- **Assistants** may **`read_file`** private Markdown when you ask for planning help—still **no** pasting of those tables into **tracked** files or issues.

---

## 8. Related docs

- [PRIVATE_OPERATOR_NOTES.md](../PRIVATE_OPERATOR_NOTES.md) — layout of `docs/private/`.
- [PRIVATE_STACK_SYNC_RITUAL.md](PRIVATE_STACK_SYNC_RITUAL.md) — **stub** for the **`private-stack-sync`** session keyword (stacked private Git close; no secrets).
- [OPERATOR_SESSION_CAPTURE_GUIDE.md](OPERATOR_SESSION_CAPTURE_GUIDE.md) — chat → durable notes.
- [private.example/README.md](../private.example/README.md) — copy-me bootstrap.
