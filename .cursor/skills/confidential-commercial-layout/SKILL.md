# Confidential commercial and client-specific documents

## When to use

Operator or agent is writing or moving **pricing**, **proposal numbers**, **client-specific** engagement notes, **strategic** drafts, or any material that could **harm competitive position** or **expose client facts** if published.

## Rules

1. **Location:** **`docs/private/`** only (entire tree is **gitignored**). Use **`docs/private/commercial/`** for **client-facing** pricing and proposals; use **`docs/private/operator_economics/`** for **your** OPEX (utilities, tools), shopping lists, and runway (see **`docs/private.example/economics/README.md`**).
1. **Never commit** those files. Do not `git add -f` under **`docs/private/`** or **`.cursor/private/`**.
1. **Tracked repo** may hold **templates** in **`docs/private.example/commercial/README.md`** — no real numbers, no client names.
1. **Public docs** may describe **product** licensing and compliance **without** bespoke rates or identifiable client stories.
1. **Refinement:** When the operator brings **updated project facts** for a client, realign **`docs/private/commercial/MATURITY_CONSULTING_PRICING_STUDY*.md`** (or successor files) in **private** only — see **`docs/PRIVATE_OPERATOR_NOTES.md`**.

## Verification

- `git check-ignore -v docs/private/commercial/<file>`
- `uv run pytest tests/test_confidential_commercial_guard.py -q`

## Related

- **`.cursor/rules/confidential-commercial-never-tracked.mdc`**
- **`tests/test_confidential_commercial_guard.py`**
