# WRB — delta snapshot for next mail (2026-03-31)

**Português (Brasil):** [WRB_DELTA_SNAPSHOT_2026-03-31.pt_BR.md](WRB_DELTA_SNAPSHOT_2026-03-31.pt_BR.md)

Paste the **paragraph below** into your Corporate-Entity-C email **after** the master prompt in [Corporate-Entity-C_REVIEW_REQUEST_GUIDELINE.md](Corporate-Entity-C_REVIEW_REQUEST_GUIDELINE.md) (or merge into §2 in [Corporate-Entity-C_WRB_REVIEW_AND_SEND.pt_BR.md](Corporate-Entity-C_WRB_REVIEW_AND_SEND.pt_BR.md) before send). Update **commit hash** if you send after a new merge.

---

## Version truth (avoid confusion)

- **`pyproject.toml` / docs** on `main` target **1.6.7** (see `docs/releases/1.6.7.md`).
- **Latest published Git tag** is **`v1.6.7`** with matching GitHub Release and Docker Hub tags (`1.6.7` and `latest`).
- Ask Corporate-Entity-C to treat **“since last market delivery”** as **since `v1.6.7` tag**, unless they confirm a newer tag on GitHub.

---

## English paste block (optional annex to the long request)

```text
Supplementary context (2026-03-31):

Since tag v1.6.7, we have been tightening operator workflows and Docker hygiene without changing the product’s core scanning behavior. Notable deltas include: Docker Desktop + Docker Hub MCP integration notes (token-aware, secrets never committed, PAT least-privilege guidance); a Docker Hub MCP troubleshooting note for token format expectations; a new operator runbook and Cursor guardrail for using Docker’s “Gordon” assistant safely (inputs-only, no secrets, convert advice into tests/docs/scripts, then run repo gates); and ongoing “engineering craft inspirations” catalog updates that shape documentation tone (not policy).

Please keep the three time lenses separate. For “since last tagged release”, use v1.6.7 as baseline (latest published release), and separate unshipped `main` work if any. (If needed, refer to the latest main commit hash at send time.)
```

---

## Related

- [Corporate-Entity-C_IN_REPO_BASELINE.md](Corporate-Entity-C_IN_REPO_BASELINE.md) — paths for reviewers.
- [PLANS_TODO.md](../plans/PLANS_TODO.md) — backlog state.
