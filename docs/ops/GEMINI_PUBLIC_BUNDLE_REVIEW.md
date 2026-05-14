# External LLM review bundle (Gemini) — safe workflow

**Portuguese (pt-BR):** [GEMINI_PUBLIC_BUNDLE_REVIEW.pt_BR.md](GEMINI_PUBLIC_BUNDLE_REVIEW.pt_BR.md)

**After a `cat` incident:** step-by-step recovery and the Windows meta script `**scripts/recovery-doc-bundle-sanity.ps1`** — **[DOC_BUNDLE_RECOVERY_PLAYBOOK.md](DOC_BUNDLE_RECOVERY_PLAYBOOK.md)** ([pt-BR](DOC_BUNDLE_RECOVERY_PLAYBOOK.pt_BR.md)).

## Authority (Gemini vs Git + tests)

External LLM review (e.g. Gemini on `**export_public_gemini_bundle.py`** output) is **optional batch triage**—not a stand-alone audit report and **not** a substitute for `**git` history**, **CI**, or **pytest**. Use it like other **external digests** (e.g. Corporate-Entity-C / WRB-style inputs): good for **prioritization**, still subordinate to reproducible checks. In-repo guardrails include `**--verify`** on bundle export, `**audit_concat_*`** helpers where you use them, `**recovery-doc-bundle-sanity.ps1`**, and the **recovery playbook** when a bundle goes wrong.

**After each run:** capture suggestions in **[plans/PLAN_GEMINI_FEEDBACK_TRIAGE.md](../plans/PLAN_GEMINI_FEEDBACK_TRIAGE.md)** (optional to-dos, non-authoritative) before promoting anything into **[PLANS_TODO.md](../plans/PLANS_TODO.md)** or an issue.

This runbook avoids **manual `cat *.md`** mistakes: the bundle is built from `**git ls-files` only**, excludes `**docs/private/`**, and wraps every file as:

```text

--- FILE: path/relative/to/repo ---
<exact file contents>

```

## Build (recommended)

From the repo root:

```bash

uv run python scripts/export_public_gemini_bundle.py \
  --output docs/private/gemini_bundles/public_bundle_$(date -I).txt \
  --compliance-yaml \
  --verify

```

**Windows (PowerShell):** do **not** paste the line above — `$(date -I)` is **bash**; PowerShell mis-parses it and you get a broken path like `**public_bundle_.txt`**. Use a dated path explicitly:

```powershell

uv run python scripts/export_public_gemini_bundle.py `
  --output "docs/private/gemini_bundles/public_bundle_$(Get-Date -Format 'yyyy-MM-dd').txt" `
  --compliance-yaml `
  --verify

```

(On PowerShell, `$(Get-Date -Format 'yyyy-MM-dd')` inside **double-quoted** strings expands to the ISO date.)

On Linux/macOS you can use:

```bash

./scripts/export_public_gemini_bundle.sh -o /tmp/public_bundle.txt --compliance-yaml --verify

```

Flags:

| Flag                | Meaning                                                   |
| ------------------- | --------------------------------------------------------- |
| `--compliance-yaml` | Also include `docs/compliance-samples/*.yaml`             |
| `--cursor`          | Include `.cursor/**/*.md` (large; usually off)            |
| `--plans`           | Include `docs/plans/**/*.md` (large; usually off)         |
| `--no-workflows`    | Skip `.github/workflows/*` and `dependabot.yml`           |
| `--verify`          | After writing, re-read each section and diff against disk |
| `--dry-run`         | Show how many paths would be included                     |

**Output path:** keep bundles under `**docs/private/...`** (gitignored) so nothing accidental lands in Git.

## Suggested Gemini prompt (copy/paste)

**Consolidates four review angles** we used in separate runs before (EN + infra, pt-BR locale, compliance YAML samples, deep synthesis)—see **[PLAN_GEMINI_FEEDBACK_TRIAGE.md](../plans/PLAN_GEMINI_FEEDBACK_TRIAGE.md)** §6. One attachment, one reply.

Use the bundle as **the only** large attachment; do **not** add private notes. Keep the **text below short** so the model budget goes to the file—not to repeating instructions.

### If you see error **13**, `RESOURCE_EXHAUSTED`, or timeouts (mobile / busy API)

- **Shorten the prompt:** use the **compact** variant in the second block below.
- **Slim the bundle:** `uv run python scripts/export_public_gemini_bundle.py --dry-run` (path count), then try `**--no-workflows`** and/or drop optional flags; see [Flags](#build-recommended).
- **Cap output:** ask for **at most N bullets per section** (compact block).
- Retry **off-peak**; very large attachments + long answers hit quota and context limits.

### Full prompt (default)

**Role line:** we use a **single sentence** of role + domain (below) instead of a long “you are…” paragraph. That usually matches or beats fluffy persona text: what drives quality here is **scope, output shape, and FILE: citations**—not a job title. If you prefer zero role wording, delete the first sentence and keep “You review…”.

```text

You are a technical documentation reviewer for an open-source, security-adjacent product (Data Boar — LGPD-style sensitivity / compliance scanning). Review the attached bundle only; sections look like:
--- FILE: <path> ---
<body>

Treat the attachment as the only evidence base. Do not assume other files exist. Do not invent behaviour—if unsure, write “confirm in code/tests”. Implemented code and tests outrank docs when they disagree. Code IS the "source of true" for what ever is docummented or created in this attached bundle.

Cover these four tracks in one answer (same priority order):
(A) EN + workflows + onboarding: contradictions, security posture, CI/Docker/pipeline footguns, broken promises vs a typical deploy path.
(B) pt-BR pairs (*.pt_BR.md): accidental pt-PT-flavoured or unnatural wording; unnatural translations; EN↔pt mismatches in technical meaning (not literary translation), flag drifs.
(C) docs/compliance-samples/*.yaml: pattern/override footguns, false-positive risk, false-negative risk, maintainability—not legal advice or opinios.
(D) Cross-cutting: “deep” risks (operator confusion, override gaps, numeric false-positive flood) and open questions.

Severity: tag each finding P0 (ship blocker / misleading security), P1 (should fix soon), or P2 (nice-to-have). Optional urgency: Hot / Warm / Cold (Hot = verify within days if true).

Output (use exactly these headings; keep each bullet one line + FILE:path when possible):
## Executive summary (max 7 bullets)
## (A) EN + infra + CI
## (B) pt-BR locale
## (C) Compliance YAML samples
## (D) Cross-cutting / open questions
## P0
## P1
## P2

```

### Compact prompt (when the API is overwhelmed or the bundle is huge)

```text

Same attachment format (--- FILE: ---). Data Boar = LGPD-style scanner; triage only.

In **one** reply, max **8** findings total across all sections, each: `- [P0|P1|P2] FILE:path — one sentence`.

Sections (very short):
## Summary (3 bullets)
## Findings (max 8, with FILE:)
## Open questions (max 3)

Skip prose. No duplication of file contents.

```

Tighten or shorten the prompt when the bundle is near the model’s context limit (`--dry-run` helps gauge size).

## Related automation

- **Headerless legacy bundles:** `scripts/audit_concatenated_markdown.py` (H1 heuristic or `--cat-order` byte split).
- **Sliding-window “puzzle piece” heuristic:** `scripts/audit_concat_sliding_window.py` builds an index of every *N*-line window over tracked `*.md` / `*.yaml` / `*.yml`, then marks which lines in your concatenated blob are covered by at least one matching window. **Uncovered** runs may be glue between files, manual edits, or text that no longer exists on disk — **not proof** of loss (generic lines and boundary effects happen). Example:

  ```bash

  uv run python scripts/audit_concat_sliding_window.py \
    -i docs/private/mess_concatenated_gemini_sanity_check/sobre-data-boar.md \
    --window 25 --strip-bundle-markers --show-sample-matches 15

  ```

  Optional: `--rstrip-lines` if editors varied trailing spaces; `--include-private-corpus` only if you intentionally want `docs/private/**` in the corpus. `--fail-if-uncovered-pct-above 0` exits non-zero when any line stays uncovered (strict CI-style gate; often too noisy for real blobs).
  **Multi-pass:** `--sweep-windows 12,15,18,22,25,30` prints one comparison table (run again with `--rstrip-lines` to compare whitespace barriers). See **[DOC_BUNDLE_RECOVERY_PLAYBOOK.md](DOC_BUNDLE_RECOVERY_PLAYBOOK.md)** § Multi-pass.
- **Operator notification policy:** [OPERATOR_NOTIFICATION_CHANNELS.md](OPERATOR_NOTIFICATION_CHANNELS.md).

