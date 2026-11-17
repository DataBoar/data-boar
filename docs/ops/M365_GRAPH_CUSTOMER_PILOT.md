# Microsoft Graph reader: pilot script for the customer's administrator (English)

**Português (Brasil):** [M365_GRAPH_CUSTOMER_PILOT.pt_BR.md](M365_GRAPH_CUSTOMER_PILOT.pt_BR.md)

**Status:** the `sharepoint_online` reader (delegated mode) is tested **only against a simulated Microsoft Graph**. Its real-account proof covers a **personal OneDrive** ([#2260](https://github.com/DataBoar/data-boar/issues/2260)) and **has not run yet**. It has **not** been validated in a work or school tenant or against SharePoint Online. A customer pilot is therefore an **evaluation**: record what happens, and claim nothing beyond it. Background and Microsoft references: [TECH_GUIDE.md, "Microsoft 365 via Graph"](../TECH_GUIDE.md#microsoft-365-via-graph).

Use placeholders in tickets and notes: `<APP_CLIENT_ID>`, `<TENANT_ID>`, `user@example.com`. Never paste real identifiers, tokens or codes into a Data Boar issue.

## 1. Minimum permissions

| What | Value |
| --- | --- |
| Permission type | **Delegated** only (a person signs in). No application permission. |
| Microsoft Graph permissions | `Files.Read` and `offline_access` (refresh token). Nothing else; remove `User.Read` if the portal adds it. |
| Credentials on the app | **None**: no client secret, no certificate. "Allow public client flows" = Yes. |
| Who signs in | A pilot user whose OneDrive holds a test folder with synthetic files. |
| Where the scan runs | A one-shot CLI scan from a terminal (`python main.py --config ...` or `docker run -it`). The web dashboard, the API and schedulers cannot sign in. |

Before the pilot, check two tenant settings (both are the administrator's decision, not Data Boar's):

1. **User consent:** whether users may consent to apps, and to which publishers ([configure user consent](https://learn.microsoft.com/en-us/entra/identity/enterprise-apps/configure-user-consent)). Data Boar has **no verified publisher**; if the app is multitenant and registered outside your tenant, users will likely be unable to consent and you grant admin consent instead ([publisher verification](https://learn.microsoft.com/en-us/entra/identity-platform/publisher-verification-overview), [grant admin consent](https://learn.microsoft.com/en-us/entra/identity/enterprise-apps/grant-admin-consent)). Registering the app in your own tenant avoids cross-tenant consent.
2. **Device code flow:** Conditional Access may block it ([block authentication flows](https://learn.microsoft.com/en-us/entra/identity/conditional-access/policy-block-authentication-flows)). If it is blocked, the delegated reader cannot run; an exception scoped to the pilot user is your decision. The unattended app-only mode ([#2262](https://github.com/DataBoar/data-boar/issues/2262)) is planned, not delivered.

## 2. What the reader reads, and what it does not

**Reads:**

- Only the folder set in `root_folder` (or `root_folder_id`) in the **signed-in user's** OneDrive (`drive: me`), and its subfolders, walked by item id.
- Only files whose extension is in the configured scan list, up to `max_file_bytes` each. Content is downloaded to a private temporary directory, scanned and deleted.

**Does not read:**

- Anything outside that folder. Note that **the permission alone would allow more**: `Files.Read` lets the token read the user's whole drive and files shared with the user ([permissions reference](https://learn.microsoft.com/en-us/graph/permissions-reference)). The restriction to the folder is enforced **by the reader**, not by Microsoft.
- Shortcuts to other drives, packages (such as OneNote notebooks), items flagged as malware, deleted items and items from another drive. They are skipped and reported as counts, without names.
- Other users' drives, SharePoint sites, Teams, mail or calendars. It writes nothing.

**What it keeps:** findings with a display path such as `onedrive:/<folder>/<file>`, file name, pattern and sensitivity. No item ids, account names, e-mail addresses or download URLs. Tokens stay in memory during the scan and are never written to disk, logs or reports.

## 3. Pilot steps

1. Register the app (or use the vendor's app) with the settings in section 1.
2. Create a test folder in the pilot user's OneDrive and put only synthetic files in it.
3. On the scanning host, write a configuration **outside any repository**. Every key is required (no default; a missing key fails with `config_error` citing it; reference: [USAGE.md](../USAGE.md)). The values below are for the Microsoft global cloud; a sovereign cloud uses its own hosts ([TECH_GUIDE.md](../TECH_GUIDE.md#microsoft-365-via-graph)). The download host suffix of a work tenant is an unconfirmed hypothesis: if the reader refuses a download with `scope_violation`, record only the suffix it reports.

   ```yaml
   targets:
     - name: pilot-onedrive
       type: sharepoint_online
       auth:
         mode: delegated
         tenant: <TENANT_ID>
         client_id: <APP_CLIENT_ID>
         login_host: login.microsoftonline.com
         allowed_login_hosts: [login.microsoftonline.com]
         scopes: "https://graph.microsoft.com/Files.Read offline_access"
       graph:
         base_url: https://graph.microsoft.com/v1.0
         allowed_hosts: [graph.microsoft.com]
       download_host_suffixes: [.sharepoint.com]
       drive: me
       root_folder: /DataBoar-Pilot
       max_depth: 32
       max_file_bytes: 104857600
       page_size: 200
       max_pages_per_folder: 10000
       http_timeout_seconds: 30
       throttle_max_wait_seconds: 120
   ```

4. Run `python main.py --config <file>` from a terminal; the pilot user follows the printed instructions (address and code) in a browser.
5. Compare the report with the synthetic files you placed. Record the outcome as it happened (ran, failed or blocked, and why).

## 4. Revoke access after the pilot

- **Administrator:** in Enterprise applications, review and revoke the permissions granted to the app, for the organization or for the pilot user ([review permissions granted to enterprise applications](https://learn.microsoft.com/en-us/entra/identity/enterprise-apps/manage-application-permissions)), then delete the enterprise application if it is no longer needed ([delete an enterprise application](https://learn.microsoft.com/en-us/entra/identity/enterprise-apps/delete-application-portal)). If you registered the app yourself, delete the app registration.
- **User with a personal Microsoft account:** remove the app at [account.live.com/consent/Manage](https://account.live.com/consent/Manage).
- Delete the test folder, the configuration file and the local report if they are no longer needed.
