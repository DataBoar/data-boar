# Author / operator — personal notes (copy to `docs/private/author_info/`)

After copying to **`docs/private/author_info/README.md`**, replace placeholders. **Never commit** `docs/private/`.

Use this tree for **you-shaped** facts (not LAN topology—that stays under **`docs/private/homelab/`**).

## Career / LinkedIn / ATS / SLI (operator only — not talent-pool candidates)

On your machine, create **`docs/private/author_info/career/`** and copy the structure from your consolidated tree (or start fresh). **Canonical map:** **`docs/private/author_info/career/README.pt_BR.md`** (private only; exists after you create it — agents **`read_file`** when present).

| Topic | Private folder (operator) | Do **not** use for the operator |
| ----- | ------------------------- | -------------------------------- |
| ATS/SLI report, Calendly guide, exports | `docs/private/author_info/career/` | `docs/private/commercial/candidates/` |
| Social **post** drafts, editorial calendar | `docs/private/social_drafts/` | — |

Talent-pool ATS files stay under **`docs/private/commercial/candidates/`** (other people). Policy: **`docs/PRIVATE_OPERATOR_NOTES.md`** §2.

## Suggested files (create as needed)

- **`career/SIDE_PROJECT_DISCLOSURE_EVIDENCE_GAP.pt_BR.md`** *(optional, private only)* — index of **employer disclosure** evidence for a public side project (email thread, Git prior art, gaps such as recruiter messages). Tracked stub: **`career/SIDE_PROJECT_DISCLOSURE_EVIDENCE_GAP.example.md`**.
- **`README.md`** (this file) — short index of what lives here.
- **`career.md`** — roles, employers, dates (text only; no secrets).
- **`education.md`** — degrees, institutions, thesis titles.
- **`certifications.md`** — cert names, vendors, expiry, links to Bitwarden items for credential refs (not passwords in plain text).
- **`narrative.md`** — blog export, timeline, or bullets for future `docs/NARRATIVE_AND_ARCHITECTURE_HISTORY.md` (source material only).
- **`ACADEMIC_NETWORK_FAMILY_ETHICS.pt_BR.md`** *(optional, private only)* — estratégia **ética** para rede acadêmica / vínculos familiares próximos (CAPES, EaD, etc.); **nunca** em Git; ver modelo em `docs/private/author_info/` na sua máquina após criar.
- **`RECENT_OPERATOR_SYNC_INDEX.pt_BR.md`** *(optional, private only)* — índice **datado** de alinhamentos do chat com o assistente; política rastreada: **`docs/ops/OPERATOR_SESSION_CAPTURE_GUIDE.md`**.

## Sharing with AI sessions

Optional at **`docs/private/WHAT_TO_SHARE_WITH_AGENT.md`**: one page listing which topics the assistant may use (e.g. “homelab host roles generic names OK: X, Y”) without pasting full CV into public chat.
