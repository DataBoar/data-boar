# Smoke: maturity self-assessment POC (operator runbook)

**Portuguese (Brazil):** [SMOKE_MATURITY_ASSESSMENT_POC.pt_BR.md](SMOKE_MATURITY_ASSESSMENT_POC.pt_BR.md)

**Plan:** [PLAN_MATURITY_SELF_ASSESSMENT_GRC_QUESTIONNAIRE.md](../plans/completed/PLAN_MATURITY_SELF_ASSESSMENT_GRC_QUESTIONNAIRE.md) (POC ready checklist).

This runbook closes **manual** checklist items **3** (happy path) and **4** (optional integrity). **Automated** gate **1** is covered by CI and by `scripts/smoke-maturity-assessment-poc.ps1` (subset of pytest).

**Evidence levels (A/B/C):** [PLAN_MATURITY_SELF_ASSESSMENT_GRC_QUESTIONNAIRE.md](../plans/completed/PLAN_MATURITY_SELF_ASSESSMENT_GRC_QUESTIONNAIRE.md) § *POC ready — evidence levels* — **A** = this script + CI; **B** = USAGE + ADR; **C** = §D below.

---

## A. Autonomous smoke (any machine with the repo)

From the repo root (Windows):

```powershell
.\scripts\smoke-maturity-assessment-poc.ps1
```

Full gate before merge remains **`.\scripts\check-all.ps1`** (not replaced by this script).

### Pytest coverage vs browser checklist (§D)

Automated tests exercise the **same routes and persistence** as §D without a browser. Use this table to see what is already proven in CI; **§D** remains the **human UX** check (layout, redirects, file download in a real browser).

| Runbook §D | Covered in tests (representative) |
| --- | --- |
| D1 — page loads, questions from pack | `test_assessment_renders_yaml_pack_when_configured`, tier/flag tests in `tests/test_api_assessment_poc.py` |
| D2 — submit → redirect / saved batch | `test_assessment_post_persists_answers`, `test_assessment_post_persists_answers_with_integrity_secret` |
| D3 — summary + recent submissions | History/batch behaviour in `tests/test_api_assessment_poc.py`, `tests/test_database.py::test_maturity_assessment_batch_summaries_newest_first` |
| D4 — batch in URL / summary link | Same module (GET with `saved` / `batch` query patterns) |
| D5 — CSV / Markdown export | CSV and Markdown export assertions inside `test_assessment_post_persists_answers` |
| D6 — `pt-br` locale | `test_assessment_placeholder_200_when_flag_on_open_tier` (GET `/pt-br/assessment`) |

**Why §D is still required for “full POC ready”:** Styling, accessibility, and real download behaviour are not a substitute for one **operator pass** through the runbook — see [PLAN_MATURITY_SELF_ASSESSMENT_GRC_QUESTIONNAIRE.md](../plans/completed/PLAN_MATURITY_SELF_ASSESSMENT_GRC_QUESTIONNAIRE.md) § *Autonomous vs operator*.

---

## B. Manual smoke -- prerequisites

1. **`uv sync`** (or your usual env) so `main.py` runs.
2. A **writable** `config.yaml` (or `CONFIG_PATH`) -- **do not** commit real paths or secrets; use a **copy** of [deploy/config.example.yaml](../../deploy/config.example.yaml) or a lab-only file under `docs/private/` patterns per [PRIVATE_OPERATOR_NOTES.md](../PRIVATE_OPERATOR_NOTES.md).
3. Copy the **sample pack** to a path you can reference in YAML (or point at the repo fixture):

   - `tests/fixtures/maturity_assessment/sample_pack.yaml`

---

## C. Minimal `config.yaml` snippets (lab)

Under **top-level `api:`** (merge with your existing file; do not duplicate `api:` keys):

```yaml
api:
  maturity_self_assessment_poc_enabled: true
  maturity_assessment_pack_path: /absolute/or/repo-relative/path/to/sample_pack.yaml
```

Under **top-level `licensing:`** (for **tier** Pro+ in open mode):

```yaml
licensing:
  effective_tier: pro
```

If you use **`licensing.mode: enforced`**, you must satisfy [LICENSING_SPEC.md](../LICENSING_SPEC.md) (JWT + public key). See [USAGE.md](../USAGE.md) -- JWT `dbtier` overrides YAML `effective_tier` when the token is valid.

Start the web UI (TLS or explicit HTTP per [USAGE.md](../USAGE.md)):

```powershell
uv run python main.py --web --allow-insecure-http --host 127.0.0.1 --port 8088
```

Set `CONFIG_PATH` if your YAML is not `./config.yaml`.

---

## D. Browser checklist (happy path)

| Step | Action | Pass |
| --- | --- | --- |
| D1 | Open `http://127.0.0.1:8088/en/assessment` (or your bind/port) | Page loads (not **404**); questions from the YAML pack appear. |
| D2 | Answer at least one question, submit the form | **303** redirect to `.../assessment?saved=1&batch=...` |
| D3 | On the summary page | Row count and rubric % (if `scores` exist in pack); **Recent submissions** table lists the batch. |
| D4 | Click **Summary** / history link for the batch | Same batch loads in the URL. |
| D5 | **Download CSV** (and optionally Markdown) | File downloads; CSV contains question ids / answers. |
| D6 | `http://127.0.0.1:8088/pt-br/assessment` | Same flow works in pt-BR locale (strings from `api/locales/pt-BR.json`). |

---

## E. Optional integrity demo (checklist item 4)

1. Stop the process. Set **`DATA_BOAR_MATURITY_INTEGRITY_SECRET`** to a non-empty test value (session env or shell) **before** starting `main.py` again.
2. Submit a **new** assessment (new batch id).
3. **`GET http://127.0.0.1:8088/status`** (with API key if `require_api_key` is on) -- JSON should include **`maturity_assessment_integrity`** with non-zero verified counts when rows are sealed.
4. **`python main.py --export-audit-trail -`** (or a temp file path) -- same integrity object should appear in the audit trail payload.

Unset the secret when you are done if this was only a lab test.

---

## F. After this checkpoint

- **#86** (dashboard session / passwordless, then RBAC): follow [PLAN_DASHBOARD_REPORTS_ACCESS_CONTROL.md](../plans/PLAN_DASHBOARD_REPORTS_ACCESS_CONTROL.md) on a **dedicated branch** -- do not mix with ad-hoc maturity edits unless the plan says so.
- **DOCX to YAML** (private questionnaire content): keep curation under **`docs/private/`** and shape per `core/maturity_assessment/pack.py` -- see PLAN_MATURITY **DOCX workflow** and **tenant** packaging when a real customer pack is in scope.
