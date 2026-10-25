# Operator guide: What to ask IT for (minimal permissions)

**Português (Brasil):** [OPERATOR_IT_REQUIREMENTS.pt_BR.md](OPERATOR_IT_REQUIREMENTS.pt_BR.md)

**See also:** [USAGE.md](../USAGE.md) (configuration), [TROUBLESHOOTING_CREDENTIALS_AND_AUTH.md](../TROUBLESHOOTING_CREDENTIALS_AND_AUTH.md) (auth issues).

This document helps **service providers and operators** who deploy or run Data Boar and need to **request access from the IT team**. It states the **minimum permissions** required for each type of source (databases, file shares, APIs, etc.), **what we do not need**, and a **brief justification** so you can confidently request least-privilege access and align with zero-trust or strict policies.

---

## Why minimal permissions matter

- **Zero-trust and policy:** Many organizations enforce zero-trust or strict IAM. Asking for broad rights (e.g. admin, full database access, or write on shares) can lead to rejection or make the tool **incompatible** with those policies.
- **Trust and audit:** IT and security are more likely to approve a **read-only, scoped** request. Over-asking can undermine trust and trigger heavier review.
- **Defense for minimal access:** Data Boar only **discovers structure** (schemas, tables, columns, file names) and **reads a small sample** of content to run sensitivity detection. It **does not write, delete, or modify** any data or metadata. It does not need DBA rights, share ownership, or admin roles—only enough to **list** and **read** within the agreed scope.

Use the sections below as a **checklist** when preparing your request to IT. Where your organisation uses different names (e.g. “Reader” vs “Read-only role”), map our needs to the closest role and mention that **no write or admin** is required.

---

## Summary table: minimal access by source type

| Source type        | What to ask IT for (minimal)                                                                    | What we do **not** need                          |
| ------------------ | ---------------------------------------------------------------------------------------------   | ------------------------------------------------ |
| **Filesystem**     | Read + list on the path(s) we scan (e.g. service account with read-only to `/data/audit`)       | Write, delete, execute, admin                    |
| **SQL databases**  | Read-only role: SELECT on target tables; metadata (list schemas/tables/columns)                 | INSERT/UPDATE/DELETE, DDL, backup, admin         |
| **MongoDB**        | Read on database: list collections, find (read documents)                                       | Write, drop, admin                               |
| **Redis**          | Commands: SCAN (and connection). No write commands                                              | SET, DEL, FLUSH, CONFIG, admin                   |
| **SMB / CIFS**     | Read + list on share/path (e.g. Read share permission, list folder contents, read files)        | Write, delete, change permissions                |
| **WebDAV**         | Read + list (PROPFIND, GET) on the base path                                                    | PUT, DELETE, PROPPATCH, write                    |
| **SharePoint**     | Read folder and files (e.g. “View” or “Read” on the site/folder); download file content         | Edit, delete, manage site                        |
| **NFS**            | Read + list on the mounted path (same as filesystem; mount is usually done by IT)               | Write, delete, root squash bypass                |
| **REST / API**     | GET access to the endpoints we scan; token with read-only or minimal scope                      | POST/PUT/DELETE, admin scope                     |
| **Power BI**       | Power BI API read (e.g. “Read all datasets” or workspace read); OAuth scope as in our connector | Publish, edit reports, admin                     |
| **Dataverse**      | Read tables/entities (e.g. environment read or table read); OAuth scope for Dataverse API       | Create/update/delete, admin                      |

---

## 1. Filesystem

- **Ask for:** Read and list on the **exact path(s)** configured in the filesystem target (e.g. `/data/audit`, `D:\Compliance\Scan`). The account that runs the scanner (or the service account you configure) must have **read** and **list directory** on that path and, if recursive scan is enabled, on subdirectories.
- **We do not need:** Write, delete, execute, or ownership. We do not need access to the rest of the machine beyond the configured path.
- **Why this is enough:** We only open files for **read**, read a **sample** of the content (see `file_scan.sample_limit`), and run sensitivity detection. No file is modified or deleted. Limiting the path in config keeps scope minimal; you can ask IT to restrict the account to that path only.

---

## 2. SQL databases (PostgreSQL, MySQL, MariaDB, SQL Server, Oracle, SQLite)

- **Ask for:** A **read-only** user/role that can:
- **List** schemas (where applicable), tables, and columns (metadata/catalog access).
- **SELECT** on the tables (or schemas) you intend to scan.
- No INSERT, UPDATE, DELETE, or DDL (CREATE/ALTER/DROP). No backup/restore, no admin.
- **Concrete examples:**
- **PostgreSQL:** Role with `CONNECT` on the database and `SELECT` on the tables (or schema) to scan; or `pg_read_all_data` if you must (still read-only). Avoid `pg_read_all_settings` and superuser.
- **MySQL / MariaDB:** User with `SELECT` and metadata (e.g. `SHOW` or access to `information_schema` for the databases we scan). No `INSERT`, `UPDATE`, `DELETE`, `CREATE`, `DROP`.
- **SQL Server:** User with `db_datareader` (or `SELECT` on specific tables) and permission to read metadata (e.g. `sys.tables`, `sys.columns`). No `db_datawriter`, no `db_owner`.
- **Oracle:** User with `SELECT` on the target tables/schemas and `SELECT_CATALOG_ROLE` (or equivalent) only if needed for listing objects. No DBA, no write.
- **We do not need:** Any write privilege, DDL, backup, replication, or server admin.
- **Why this is enough:** We use the engine’s metadata APIs to discover schemas/tables/columns, then run **SELECT** with a small **LIMIT** per column to sample values. Findings are metadata (table/column, pattern type); we do not store full row content. Read-only is sufficient and aligns with zero-trust.

---

## 3. MongoDB

- **Ask for:** A user with **read** on the database(s) we scan: `listCollections`, `find` (we use a small limit per collection). No `insert`, `update`, `delete`, `drop`, or `createCollection`.
- **We do not need:** Write, drop, or admin roles (e.g. `root`, `dbAdmin`).
- **Why this is enough:** We list collections, then run `find().limit(n)` to sample documents. We only read field names and sample values for sensitivity detection; we do not persist full documents.

---

## 4. Redis

- **Ask for:** Connection and **read-only** usage. We use **SCAN** to iterate key names and run detection on key names (and optionally key types). If Redis ACLs are used, a role that allows **SCAN** and optionally **TYPE**; **no** SET, DEL, FLUSH, CONFIG, or other write/admin commands.
- **We do not need:** Any write or administrative command.
- **Why this is enough:** We only need to read key names (and optionally types) to detect sensitive patterns; we do not need to read or store key values for the detection logic we ship. Read-only keeps impact minimal.

---

## 5. SMB / CIFS shares

- **Ask for:** **Read** and **list** on the share (or the specific path under the share) we scan. Typically: “Read” share permission and “List folder contents” + “Read” on the folder(s). The account (e.g. domain user or service account) must be able to open files for read and list directory contents.
- **We do not need:** Write, delete, change permissions, or “Full control.”
- **Why this is enough:** We list files under the path, open each file for **read**, extract a text sample (same as filesystem), and run detection. No file is written or deleted. Request only the share/path you need so IT can scope the permission.

---

## 6. WebDAV

- **Ask for:** **Read** and **list** on the base path: PROPFIND (list) and GET (read file content). No PUT, DELETE, PROPPATCH, or other write methods.
- **We do not need:** Write, delete, or lock.
- **Why this is enough:** We list resources, download file content with GET, then run the same file-scan logic as filesystem. Read-only is sufficient.

---

## 7. SharePoint

- **Ask for:** **View** or **Read** on the site or folder we scan: list files in the folder and download file content (e.g. via “Get file content” / `$value`). Often “Site Visitors” or “Read” is enough for the target library/folder.
- **We do not need:** Edit, delete, manage site, or full control.
- **Why this is enough:** We use the REST API to list files and GET file content, then run sensitivity detection. No upload or modification.

---

## 8. NFS

- **Ask for:** The path we scan is typically a **local mount** that IT (or the host) has already mounted. The account running the scanner needs **read** and **list** on that mount (same as filesystem). If IT controls NFS exports, request read-only export for the audit host if possible.
- **We do not need:** Write, delete, or root/sudo to bypass squash.
- **Why this is enough:** We use the same logic as the filesystem connector on the mounted path; read and list are sufficient.

---

## 9. REST / API targets

- **Ask for:** **GET** access to the URL(s) we scan (base_url + paths or discover_url). If the API uses tokens, request a token with **read-only** or the **minimum scope** that allows GET on those endpoints. No POST/PUT/DELETE unless the API is used only for discovery and we do not send body data.
- **We do not need:** Write scope, admin scope, or scope beyond the endpoints we call.
- **Why this is enough:** We only perform GET requests, parse response (e.g. JSON), and run detection on keys and sample values. No data is sent to the API except what is required for auth (e.g. OAuth token request).

---

## 10. Power BI

- **Ask for:** Power BI API **read** access: e.g. “Read all datasets” or read access to the workspaces/datasets we scan. Our connector uses the scope `<https://analysis.windows.net/powerbi/api/.defaul>t` (Azure AD). IT should grant the app registration the minimal Power BI permission that allows listing workspaces/datasets and executing read-only queries (e.g. Execute Queries for sampling).
- **We do not need:** Publish, edit reports/datasets, or admin.
- **Why this is enough:** We list datasets and tables, run small DAX queries to sample data, and run sensitivity detection. Read-only API access is sufficient.

---

## 11. Dataverse / Power Apps

- **Ask for:** **Read** access to the environment and tables (entities) we scan: e.g. environment read or “Read” on the target tables. OAuth scope is typically the Dataverse resource (e.g. `https://<org>.crm.dynamics.com/.default` or similar). The app registration should have the minimum role that allows reading table metadata and rows.
- **We do not need:** Create, update, delete, or system admin.
- **Why this is enough:** We list tables and sample rows via the Web API for sensitivity detection. No writes.

---

## Checklist for your request to IT

When you send your request, you can include:

1. **Scope:** Exact path(s), database(s), share(s), or API base URL(s) we will access.
1. **Identity:** The account or app (e.g. service account, Azure AD app) that will be used.
1. **Required access:** “Read and list only” (or the row from the summary table above for that source).
1. **What we do not need:** “No write, delete, or admin.”
1. **Justification:** “Compliance / data-discovery scan: discover and sample content for sensitivity detection; no data modification or export of full content; findings are metadata only (location and pattern type).”

If IT asks for a written justification, you can point them to this document and to the fact that the application is designed to operate with **least privilege** so it remains compatible with zero-trust and strict IAM policies.

---

## Last updated

Document created. Update when new connectors or permission requirements are added.
