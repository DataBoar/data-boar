# WRB — delta snapshot for next mail (2026-03-26)

**Português (Brasil):** [WRB_DELTA_SNAPSHOT_2026-03-26.pt_BR.md](WRB_DELTA_SNAPSHOT_2026-03-26.pt_BR.md)

Paste the **paragraph below** into your Corporate-Entity-C email **after** the master prompt in [Corporate-Entity-C_REVIEW_REQUEST_GUIDELINE.md](Corporate-Entity-C_REVIEW_REQUEST_GUIDELINE.md) (or merge into §2 in [Corporate-Entity-C_WRB_REVIEW_AND_SEND.pt_BR.md](Corporate-Entity-C_WRB_REVIEW_AND_SEND.pt_BR.md) before send). Update **commit hash** if you send after a new merge.

---

## Version truth (avoid confusion)

- **`pyproject.toml` / docs** on `main` target **1.6.7** (see `docs/releases/1.6.7.md`).
- **Latest published Git tag** is **`v1.6.7`** with matching GitHub Release and Docker Hub tags (`1.6.7` and `latest`).
- Ask Corporate-Entity-C to treat **“since last market delivery”** as **since `v1.6.7` tag**, unless they confirm a newer tag on GitHub.

---

## English paste block (optional annex to the long request)

```text
Supplementary context (2026-03-26):

Since our last WRB cycle and since tag v1.6.6, main has accumulated (or will ship in the next merge) work including: CI lint job aligned with `pre-commit run --all-files` (Ruff, plans-stats --check, markdown, pt-BR locale, commercial guard); new local hook `plans-stats-check`; Semgrep workflow for Python SAST; ADR series 0000–0003 (origin baseline, MD029, operator docs, SBOM roadmap); docs/ops/WORKFLOW_DEFERRED_FOLLOWUPS; academic thesis guidance (ACADEMIC_USE_AND_THESIS + pt-BR); quality rule/skill updates; Slack operator ping verified.

Please keep the three time lenses separate. For “since last tagged release”, use v1.6.7 as baseline (latest published release), and separate unshipped `main` work if any.
```

---

## Related

- [Corporate-Entity-C_IN_REPO_BASELINE.md](Corporate-Entity-C_IN_REPO_BASELINE.md) — paths for reviewers.
- [PLANS_TODO.md](../plans/PLANS_TODO.md) — backlog state.
