# WRB — delta snapshot for next mail (2026-04-03)

**Português (Brasil):** [WRB_DELTA_SNAPSHOT_2026-04-03.pt_BR.md](WRB_DELTA_SNAPSHOT_2026-04-03.pt_BR.md)

Paste the **paragraph below** into your Corporate-Entity-C email **after** the master prompt in [Corporate-Entity-C_REVIEW_REQUEST_GUIDELINE.md](Corporate-Entity-C_REVIEW_REQUEST_GUIDELINE.md) (or merge into §2 in [Corporate-Entity-C_WRB_REVIEW_AND_SEND.pt_BR.md](Corporate-Entity-C_WRB_REVIEW_AND_SEND.pt_BR.md) before send). Update **commit hash** if you send after a new merge.

---

## Version truth (avoid confusion)

- **`pyproject.toml` / docs** on `main` target **1.6.8** (see `docs/releases/1.6.8.md`).
- **Latest published Git tag** at send time: confirm **`v1.6.8`** on GitHub Releases and matching Docker Hub tags (`1.6.8`, `latest`).
- Ask Corporate-Entity-C to treat **“since last market delivery”** as **since `v1.6.8` tag**, unless they confirm a newer tag on GitHub.
- If you have **uncommitted local changes** on the dev PC, call that out as **not yet on `origin/main`**—separate lens from the tagged release.

---

## English paste block (optional annex to the long request)

```text
Supplementary context (2026-04-03):

Since the prior WRB delta snapshot (2026-03-31), we advanced the working tree toward 1.6.8 alignment and tightened operator-facing flows: session keyword / LAB-OP SSH naming consistency (canonical host alias `lab-op` in examples), operator session shorthands index, token-aware docs cross-links, and Markdown table hygiene in session-mode rules. Homelab automation scripts and private-example manifests were updated to match the same SSH alias. A verified public bundle for optional external LLM triage (Gemini) is generated with `export_public_gemini_bundle.py --verify` (not a substitute for git/CI/pytest).

Please keep the three time lenses separate. For “since last tagged release”, use v1.6.8 as baseline if that remains the latest published release at send time, and separate any unshipped `main` work. (Refer to the latest `main` commit hash at send time if needed.)
```

---

## Re-send note (if a previous WRB e-mail was lost)

Paste **after** the supplementary block above (or right after *Olá, equipe Corporate-Entity-C* in the long PT prompt) so reviewers without thread memory still have a clear anchor.

```text
Short note — re-send: We are sending this WRB request again; an earlier message may not have reached you. Please treat this e-mail (and the linked in-repo briefing paths below) as the single source of truth — we do not assume you retain context from a prior thread. Our last report from you remains the 2026-03-18 delivery; tracking: docs/plans/Corporate-Entity-C_ANALISE_2026-03-18.md. At send time, please confirm the latest GitHub tag (expected v1.6.8 unless superseded) and use `main` at commit: REPLACE_WITH_SHORT_HASH (run `git rev-parse --short HEAD` before send).
```

---

## Related

- [Corporate-Entity-C_IN_REPO_BASELINE.md](Corporate-Entity-C_IN_REPO_BASELINE.md) — paths for reviewers.
- [PLANS_TODO.md](../plans/PLANS_TODO.md) — backlog state.
- [GEMINI_PUBLIC_BUNDLE_REVIEW.md](GEMINI_PUBLIC_BUNDLE_REVIEW.md) — safe bundle workflow (output under `docs/private/`).
