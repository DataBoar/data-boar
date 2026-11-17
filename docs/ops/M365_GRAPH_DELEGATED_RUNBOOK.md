# Microsoft Graph reader, delegated mode: Phase 0 runbook (English)

**Português (Brasil):** [M365_GRAPH_DELEGATED_RUNBOOK.pt_BR.md](M365_GRAPH_DELEGATED_RUNBOOK.pt_BR.md)

**Issues:** [#2260](https://github.com/DataBoar/data-boar/issues/2260) (Phase 0, real proof) and [#2261](https://github.com/DataBoar/data-boar/issues/2261) (the `sharepoint_online` reader). Epic [#2206](https://github.com/DataBoar/data-boar/issues/2206).

**Status:** Phase 0 is **pending**. The reader is implemented and tested **only against a simulated Microsoft Graph**. Nothing in this repository proves yet that it reads a real OneDrive.

**What Phase 0 can prove, and what it cannot.** Phase 0 runs the reader against the **operator's personal OneDrive**, in one synthetic folder, with a human signing in by device code. It proves a **personal OneDrive only**. It does **not** prove SharePoint Online, a work or school tenant, conditional access policies of a tenant, app-only (unattended) access or real throttling. None of those may be claimed from Phase 0.

---

## 1. What the reader does

- Type `sharepoint_online`, read-only, **Enterprise** tier.
- A human signs in with the OAuth **device code** flow: public client, **no client secret**, scopes `Files.Read` and `offline_access`.
- Sign-in is allowed only in a **one-shot CLI scan run from a terminal**. The web dashboard, the API and any scheduler never sign in; a target started from them fails with `auth_required`.
- `Files.Read` lets the token read the **whole drive**. The reader, not the token, restricts the scan to `root_folder`: it resolves the folder once and only walks item ids below it. Shortcuts to other drives (`remoteItem`), packages, items flagged as malware or deleted, and items from another drive are skipped and counted.
- Tokens live **in memory only**, for the duration of the scan. Nothing is written to disk. The refresh token is valid for about 90 days and is not bound to the folder, which is why it is never stored.

## 2. Register the application (operator)

Do this in the Microsoft Entra admin center (App registrations). Never copy any identifier from this step into the repository, an issue or the evidence file.

1. **Where:** if your personal Microsoft account cannot register an app without an Entra tenant (not confirmed), create a free tenant only to host the registration. The account that signs in during the scan is still your personal account.
2. **Supported account types:** "Personal Microsoft accounts only".
3. **Redirect URI:** none. The device code flow does not use one (Phase 0 confirms this; if sign-in fails asking for one, record the error code and report it).
4. **Authentication:** "Allow public client flows" = **Yes** ("Enable the following mobile and desktop flows"). With **No**, the token endpoint fails with `invalid_client` (AADSTS7000218).
5. **API permissions:** Microsoft Graph, **delegated**, `Files.Read`. If the portal added `User.Read`, remove it. `offline_access` is requested at sign-in.
6. **Certificates & secrets:** create **nothing**. No client secret, no certificate.
7. Note the **Application (client) ID** somewhere private. You will pass it through an environment variable.

## 3. Prepare the synthetic folder (operator)

1. Generate synthetic files **outside the repository**:

   ```bash
   uv run python scripts/generate_synthetic_poc_corpus.py --output /tmp/m365-phase0-corpus --scenario happy
   ```

2. In your OneDrive, create a folder such as `/DataBoar-Sintetico` and upload a few of the generated text files (for example `.txt` and `.csv`). Use only synthetic content.
3. Keep the local copies: the evidence compares names, sizes and SHA-256 of the local files with what the reader lists.

## 4. Ephemeral configuration (outside the repository)

Create a config file **outside the repository** (for example `/tmp/m365-phase0.yaml`). The client ID comes from an environment variable; the YAML holds only the variable **name**:

```yaml
targets:
  - name: onedrive-sintetico
    type: sharepoint_online
    auth:
      mode: delegated                     # the only mode available now
      tenant: consumers                   # personal accounts
      client_id_from_env: M365_CLIENT_ID  # variable name, not the value
    drive: me                             # the only drive available now
    root_folder: /DataBoar-Sintetico      # required; never the drive root
    # max_depth: 32                       # optional, 1..256
    # max_file_bytes: 104857600           # optional, default 100 MiB
    # throttle_max_wait_seconds: 120      # optional, 1..600
report:
  output_dir: /tmp/m365-phase0-report
sqlite_path: /tmp/m365-phase0-report/audit.db
```

```bash
export M365_CLIENT_ID='<application (client) ID>'   # never commit it
```

With `DATA_BOAR_CREDENTIAL_STRICT=1`, also allow both destinations: `DATA_BOAR_CREDENTIAL_ALLOWED_HOSTS=login.microsoftonline.com,graph.microsoft.com`.

## 5. Run the scan from a terminal

```bash
uv run python main.py --config /tmp/m365-phase0.yaml
```

In Docker, the container needs a terminal (`-it`), the variable and the config:

```bash
docker run -it --rm -e M365_CLIENT_ID \
  -v /tmp/m365-phase0.yaml:/data/m365-phase0.yaml:ro \
  -v /tmp/m365-phase0-report:/tmp/m365-phase0-report \
  <data-boar image> main.py --config /data/m365-phase0.yaml
```

The reader prints one line on standard error:

```text
To sign in to Microsoft for target 'onedrive-sintetico', open https://microsoft.com/devicelogin and enter the code <CODE>. The code expires in 15 minutes.
```

Open the address in a browser, type the code, sign in with your personal account and accept the consent. The consent screen should ask only to read your files and to keep access (record what it shows, without identifiers). The scan then continues on its own.

## 6. Evidence

Write the result in `docs/ops/evidence/M365_PHASE0_<date>.md` **as it happened**: ran, failed or blocked, and why. If the app registration was not available, the result is "blocked: no app registration".

1. **Listing by the reader** (costs one more device code, because it is another process):

   ```bash
   uv run python - <<'PY'
   from config.loader import load_config
   from connectors.sharepoint_online_connector import SharePointOnlineConnector, enable_interactive_sign_in
   target = load_config("/tmp/m365-phase0.yaml")["targets"][0]
   enable_interactive_sign_in()
   for e in SharePointOnlineConnector(target, None, None).list_scope():
       print(e.display_path, e.size, e.skipped_reason or "")
   PY
   ```

2. **The same files locally:** name, size and SHA-256 (`sha256sum /tmp/m365-phase0-corpus/<files>`).
3. **Report summary:** number of findings per file and pattern.

Checklist for Phase 0:

| Id | What the real account proves | If it fails |
| --- | --- | --- |
| P0-1 | Personal-account registration with public client flows = Yes accepts device code with `tenant: consumers` | record the AADSTS code; review section 2 |
| P0-2 | The consent screen asks only to read files and keep access | review scopes and this runbook |
| P0-3 | The token endpoint returns a refresh token; note the observed `expires_in` (never the token) | review refresh handling |
| P0-4 | Device code works without a redirect URI | add the redirect URI to section 2 |
| P0-5 | The real download host ends in an allowlisted suffix (`.files.1drv.com` or `.microsoftpersonalcontent.com`); note the suffix only | the reader refuses the download (`scope_violation`); the allowlist needs a design revision before merge |
| P0-6 | `list_scope()` lists only the synthetic folder, with the same names and sizes as the local files | blocks the merge |
| P0-7 | (optional) a shortcut to another folder shows up as skipped | review the shortcut rule |
| P0-8 | The report has the findings expected from the synthetic content | blocks the merge |
| P0-9 | No `skipped` failure with `other_drive` for a plain synthetic folder | the drive id rule needs a design revision before merge |

**Never** write in the evidence file, an issue or a commit: tenant id, client ID, drive or item ids, e-mail, account name, download URL, token, the user code, or a screenshot showing any of them.

## 7. Revoke access afterwards

1. Remove the app from your personal Microsoft account at [account.live.com/consent/Manage](https://account.live.com/consent/Manage). Work or school tenants: see [TECH_GUIDE.md, "Microsoft 365 via Graph"](../TECH_GUIDE.md#microsoft-365-via-graph).
2. Delete the app registration (and the temporary tenant, if you created one only for this).
3. Delete the synthetic folder and the local temporary files and report.

## 8. Common errors

| Failure (`reason`) | Likely cause |
| --- | --- |
| `auth_required` | The scan did not run from a terminal, or ran from the web dashboard, the API or a scheduler. Delegated sign-in needs a human; unattended scans need app-only mode ([#2262](https://github.com/DataBoar/data-boar/issues/2262), not available yet). |
| `auth_failed` "token endpoint error invalid_client (AADSTS7000218)" | "Allow public client flows" is No. |
| `auth_failed` "Microsoft sign-in was declined" or "code expired" | The consent was refused, or the code was not entered in time. Run again. |
| `auth_failed` in a work or school tenant | The tenant may block device code flow through conditional access (Microsoft-managed policy). This runbook covers personal accounts only. |
| `config_error` citing `#2262` | `auth.mode: app_only` or `drive` other than `me`: not available yet. |
| `scope_violation` "download host not allowlisted" | The real download host is not in the allowlist. Record the suffix only and report it (P0-5). |
| `skipped` "N items skipped: ..." | Items outside the rules (shortcuts, packages, other drive). Counts only, no names. |
