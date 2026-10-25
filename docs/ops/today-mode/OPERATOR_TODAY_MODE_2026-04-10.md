# Operator today mode — 2026-04-10 (carryover + effective focus)

**Português (Brasil):** [OPERATOR_TODAY_MODE_2026-04-10.pt_BR.md](OPERATOR_TODAY_MODE_2026-04-10.pt_BR.md)

> Prepared while closing **2026-04-09** so **2026-04-10** opens with explicit carryover — not a blank page. If the calendar already shows **2026-04-11**, treat this file as the **2026-04-10** archive and open **`OPERATOR_TODAY_MODE_2026-04-11.md`** when it exists.

---

## Block 0 — Morning reality check (10–15 min)

Run **`carryover-sweep`** or **`.\scripts\operator-day-ritual.ps1 -Mode Morning`**, then:

1. `git fetch origin` · `git status -sb` · `gh pr list --state open`
2. **`origin/main`:** after **2026-04-09** eod-sync, **PR #177** (Dependabot `cryptography`) was **merged** and **`main` pulled** (fast-forward `requirements.txt` / `uv.lock`). Re-pull if another machine merged overnight.
3. **Working tree (public repo):** still likely **large local diff** (many modified + untracked files) — **decide today:** themed commits, branch, stash, or continue — do **not** assume a clean `main` without looking.
4. **Stacked private git (`docs/private/`):** if still pending, schedule **`.\scripts\private-git-sync.ps1`** (and **`-Push`** if policy says so).
5. `- [ ] **Block close (lab / VC):** when pausing or leaving lab later, type **`block-close`** in chat and follow VeraCrypt session policy in **private** **`docs/private/homelab/OPERATOR_VERACRYPT_SESSION_POLICY*.md`** — optional **boundary** checklist, **not** the full **`eod-sync`** git/gh ritual.

**Canonical rolling queue:** [CARRYOVER.md](CARRYOVER.md) · **Published truth:** [PUBLISHED_SYNC.md](PUBLISHED_SYNC.md)

---

## Carryover — from `OPERATOR_TODAY_MODE_2026-04-09.md` (still open)

- [ ] **Private repo:** `private-git-sync` until the pending queue feels honest (ritual still flagged volume).
- [ ] **Public working tree:** close or split into PRs/commits (high volume).
- [x] **PR #177** Dependabot `cryptography` — **merged** post-2026-04-09 eod-sync; keep watching new Dependabot rows per **`SECURITY.md`**.
- [x] **Ansible / USAGE (docs + `main`):** done **2026-04-09** (`USAGE.pt_BR.md` Ansible section, pushed to `main`).
- [ ] **LAB-NODE-01 / `uv` / ansible `--check`:** still open — see **`OPERATOR_TODAY_MODE_2026-04-06.md`**.
- [ ] **Homelab / hardware** (NVMe, VeraCrypt): private notes only — not duplicated here.

---

## Carryover — from [CARRYOVER.md](CARRYOVER.md) (rolling queue highlights)

Pick **one or two** rows for deep work; defer the rest with a date or PLANS row:

- [ ] Release gate **1.6.8** (notes + tests + publish/defer) — see **`OPERATOR_TODAY_MODE_2026-04-02.md`** Block C if still the anchor.
- [ ] External round **WRB + Gemini** (“code is truth”) — **`PLAN_GEMINI_FEEDBACK_TRIAGE.md`**
- [ ] Quantified snapshot (`progress-snapshot.ps1`) if still unrun
- [ ] Founder LinkedIn/ATS full refresh (private playbook)
- [ ] Time Machine USB recovery path (**`TIME_MACHINE_USB_RECOVERY_AND_REPURPOSE.md`**)
- [ ] **Corporate-Entity-C WRB** e-mail — paste block: latest **`WRB_DELTA_SNAPSHOT_*.md`**
- [ ] Optional: **Gemini Cold doc slice** · **`/help` parity** when CLI flags next change

---

## Social + editorial (private hub)

- **Inventory:** `docs/private/social_drafts/editorial/SOCIAL_HUB.md` (shortcut: `docs/private/social_drafts/SOCIAL_HUB.md`)
- **Queues:** `EDITORIAL_INSTAGRAM_THREADS_2026-04.md` · `EDITORIAL_X_ROTACAO_2026-04.md` · LinkedIn series file if present
- **Goal for today:** open **SOCIAL_HUB** — pick **one** publish or **one** draft advance (X / WordPress / LinkedIn line **L2** if calendar fits)

---

## Suggested priorities — **2026-04-10**

1. **Stabilise git story:** `git status` → smallest honest commit or intentional branch (public); touch **private-git-sync** if stack is noisy.
2. **One carryover win:** e.g. private sync **or** one themed docs/workflow commit **or** one social draft shipped.
3. **`gh pr list`** — expect **zero** open if nothing new overnight; merge greens per **`pr-merge-when-green.ps1`** when safe.
4. **Cursor / agent policy:** if still mid-consolidation (`CURSOR_AGENT_POLICY_HUB`, `AGENTS` index), continue in **small** PRs — avoid mixing with unrelated product code.

### Doc slice (glossary — **Stark Law**)

- [x] **`docs/GLOSSARY.md` / `GLOSSARY.pt_BR.md`:** entrada **Stark Law** (EUA — autoencaminhamento *Medicare*, distinto de HIPAA/PHI); ligação CMS; remissões **PHI** / **HCP**. *Commit local até `git push`.*

### Doc slice (glossary — **CPML** + **PJ vs dado pessoal**)

- [x] **CPML** revisto: contexto **Stark** / **FDA** / compliance comercial (**CGMP**, **CPGM**) vs sigla de engenharia; **não** confundir com **CGMP** sem fonte.
- [x] Nova entrada **legal entity and personal data (scanning)** — CNPJ/LTDA/S.A. **não** desligam LGPD para e-mail/telefone/nome de colaborador na amostra; comportamento do motor descrito (regex/ML, sem “só PJ = ignorar”).

---

## End of day

- **`block-close`** + VeraCrypt (private homelab policy above) when ending a **work block** or leaving lab; **`eod-sync`** for **`operator-day-ritual -Mode Eod`** + git/gh/PR + tomorrow’s today-mode pointer.
- **`eod-sync`** in chat **or** **`.\scripts\operator-day-ritual.ps1 -Mode Eod`**
- Prepare or skim **`OPERATOR_TODAY_MODE_2026-04-11.md`** next

---

## Quick references

- Yesterday: [OPERATOR_TODAY_MODE_2026-04-09.md](OPERATOR_TODAY_MODE_2026-04-09.md)
- Token-aware hub (if in tree): `docs/ops/TOKEN_AWARE_SCRIPTS_HUB.md`
- Study cadence: `docs/plans/PORTFOLIO_AND_EVIDENCE_SOURCES.md` (operator calendar)
- Private rhythm: `docs/private/TODAY_MODE_CARRYOVER_AND_FOUNDER_RHYTHM.md`
