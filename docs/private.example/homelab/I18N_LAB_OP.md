# LAB-OP private docs — English + Brazilian Portuguese pairs

**Português (Brasil):** [I18N_LAB_OP.pt_BR.md](I18N_LAB_OP.pt_BR.md)

When you maintain **`docs/private/homelab/`** (gitignored), prefer **two files per topic** where prose matters:

| Pattern             | Role                                                                                                       |
| -------             | ----                                                                                                       |
| **`Name.md`**       | **English** — good for international collaborators, Mermaid-heavy pages, or **summary** maps.              |
| **`Name.pt_BR.md`** | **Brazilian Portuguese (pt-BR)** — not European Portuguese; see **`.cursor/rules/docs-pt-br-locale.mdc`**. |

## Exceptions / pragmatism

- **`LAB_SECURITY_POSTURE`:** **`LAB_SECURITY_POSTURE.pt_BR.md`** holds **full evidence** (long). **`LAB_SECURITY_POSTURE.md`** is a **short EN index** pointing to the pt-BR file — avoids duplicating 900+ lines until a full EN translation is needed.
- **`iso-inventory`:** **`iso-inventory.md`** keeps the **`find`** path list; **`iso-inventory.pt_BR.md`** mirrors layout + policy in pt-BR and tells you to **sync** the file list with EN.
- **Large matrices:** **`LAB_SOFTWARE_INVENTORY.pt_BR.md`** may stay a **structured summary** with the **full table** in EN — reduce drift.

**Automation:** **`tests/test_docs_pt_br_locale.py`** scans **every** **`*.pt_BR.md`** under the repo (excluding **`.venv`** / **`node_modules`** only), **including** **`docs/private/**`** when that tree exists locally — same bar as markdown lint for operator notes. Still avoid pasting raw **pt-PT** into prose; use **`.cursor/rules/docs-pt-br-locale.mdc`** as the style guide.

## Templates

**`OPERATOR_RETEACH.md`** + **`OPERATOR_RETEACH.pt_BR.md`** in **`private.example/homelab/`** (placeholders only).
