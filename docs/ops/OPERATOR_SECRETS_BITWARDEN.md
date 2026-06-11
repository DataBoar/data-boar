# Operator secrets: Bitwarden (password manager as your vault)

**Purpose:** Explain how **Bitwarden** fits next to Data Boar’s **`pass_from_env` / `*_from_env`**, gitignored **`config.yaml`**, and the future **in-app vault** ([PLAN_SECRETS_VAULT.md](../plans/PLAN_SECRETS_VAULT.md)).

---

## Can Bitwarden be your “secrets repository”?

**Yes — as the system where *you* store and retrieve secrets.** It is **not** (today) wired into the app as automatic runtime injection.

| Layer                              | Role                                                                                                                                                                                                                             |
| -----                              | ----                                                                                                                                                                                                                             |
| **Bitwarden vault**                | **Human source of truth:** DB passwords, API keys, SNMP/auth material, vendor cloud keys, TLS passphrases, “where is my homelab VLAN doc” pointers.                                                                              |
| **Environment variables**          | **Runtime for Data Boar:** `pass_from_env`, `api_key_from_env`, etc. You **copy** from Bitwarden when starting the process, or use a **small launcher script** / container orchestrator that injects env from your secret store. |
| **Gitignored `config.yaml`**       | May still hold secrets locally; prefer **env** for anything you might accidentally paste; **never** commit.                                                                                                                      |
| **Phase B in-app vault** (planned) | **Application-embedded** encrypted store and `@vault:` references — a **different** mechanism from Bitwarden; both can coexist (Bitwarden = operator backup; in-app = server-local).                                             |

---

## Free tier vs paid (verify current plans on [bitwarden.com](https://bitwarden.com/pricing/))

**Free (personal)** is usually **enough** for a **solo** developer/operator to hold **all** project and homelab secrets: **unlimited passwords**, **sync**, **generator**, and **2FA on your Bitwarden account** (enable it).

**Paid tiers** often add value when:

- You want **TOTP codes inside the vault** next to each login (Premium-style feature — free users often use a **separate** authenticator app).
- **Bitwarden Authenticator** (e.g. **iPhone**): scans **QR** codes for **OTP/TOTP** and can **sync** with your Bitwarden account alongside passwords—one ecosystem across **browser extension**, **desktop**, and **mobile**. Exact capabilities (sync, item linking) depend on **current** Bitwarden product docs and **your** plan; verify on [bitwarden.com](https://bitwarden.com/pricing/) and the Authenticator help pages.
- You need **encrypted file attachments** (license blobs, small key backups) beyond what notes allow.
- You want **Families** / **Teams** / **Organizations** for **shared collections** (future collaborators or household).
- You want **emergency access**, **advanced 2FA**, or **directory integration** at org scale.

**When paid “makes sense for later development”:** If you add **teammates**, **shared lab** credentials, or you want **one** place for **TOTP + secrets** with audit-friendly sharing — not because Data Boar **requires** Bitwarden Premium to run.

---

## Sharing secrets (partner, lab-op, small team)

**Bitwarden sharing is not “add a friend to my personal vault.”** You use an **Organization** (paid tier: **Teams**, **Enterprise**, or **Families** for household-style sharing). Everyone keeps their **own** Bitwarden login; the org owns **shared collections**.

## Typical setup:

1. **Decide the billing owner** (one account creates or upgrades the org on [bitwarden.com](https://bitwarden.com/pricing/) — verify current plan names and limits).
1. **Create the organization** in the web vault (**Admin console**): name it e.g. `Homelab` or `Lab-op`.
1. **Invite members** by email → they **accept** and join with their existing Bitwarden account (or create one).
1. **Create collections** (logical folders the org shares), e.g. `UniFi`, `SNMP`, `GitHub`, `Solar API`, `SSH jump`, `LAB-OP — hardware receipts` — **no secrets in the collection name** if it’s sensitive.
1. **Move or duplicate items** into those collections and set **member access** (read-only vs can edit) per collection.
1. **2FA:** Require **2FA on the Bitwarden account** for anyone who can read production creds; store **recovery codes** safely (offline or per Bitwarden’s emergency guidance).

**Families vs Teams:** **Families** is often enough for **two adults + shared household** secrets; **Teams** fits **named collaborators** and more **admin/audit** style features — compare pricing and features on Bitwarden’s site before you commit.

**CLI (`bw`) with org items:** After `bw login` / `bw unlock`, org vault items are available to the CLI the same as personal items, subject to your **permissions** on each collection. Prefer **`BW_SESSION`** with short TTL for scripts; never commit session tokens.

**If you only need occasional handoff:** A **single** operator can still use **export** (encrypted) or **emergency access** — not a substitute for ongoing shared ops; use an **org** when two people must **routinely** use the same rotating secrets.

---

## Practices that work well with this repo

1. **One item per logical secret** (e.g. “Lab Postgres read-only”) with **custom fields** for host, user, DB name, password.
1. **Secure Note** for long tokens or PEM blocks — paste into **local** env or file only; never into tracked Markdown.
1. **Bitwarden CLI (`bw`)** — after `bw unlock`, use **`BW_SESSION`** with short lifetime to script `bw get password …` into env for local runs. **Do not** commit session strings or master password.
1. **Master password** and **2FA recovery codes** — store recovery codes **offline** or in Bitwarden **printout flow** per Bitwarden guidance; not in **`docs/private/`** in plaintext next to the repo if the disk is shared (that whole tree is gitignored but still **local disk**).
1. **Authenticator + vault** — If you use **Bitwarden Authenticator** on **iOS/Android**, keep **screen lock** and **vault timeout** tight; OTPs are as sensitive as passwords for sites that rely on TOTP alone.

---

## Repository contract — `bw` CLI, CI, docs, and tests

**Agreed policy** (operator + assistants + contributors): treat this as **non-negotiable** alongside [SECURITY.md](../../SECURITY.md).

| Rule | Detail |
| ---- | ------ |
| **Never commit** | Secrets, **`BW_SESSION`** (or any vault session token), or **`.env`** files containing **live** credentials. |
| **Local use only** | **`bw unlock`** / **`bw get`** in **local** scripts or in **documentation** only as **example commands** (placeholders, no real values). Use **`BW_SESSION`** with **short TTL**; the **operator** unlocks on **their own** machine. |
| **CI (GitHub Actions)** | **Do not** connect Bitwarden to **public** GitHub-hosted runners **without an explicit, reviewed design**. Prefer **[GitHub Actions secrets](https://docs.github.com/en/actions/security-guides/using-secrets-in-github-actions)** for what the pipeline needs. **`bw`** stays for **local dev** and **homelab** workflows. |
| **Skills / `.cursor/rules`** | May describe the **flow** (e.g. “after `bw unlock`, export env vars…”) **without** real passwords, tokens, or session strings. |
| **Tests** | **Mock** environment variables; **pytest** in **CI** must **not** depend on a **real** Bitwarden vault or live **`bw`** session. |

---

## Verify `bw` on each machine (no remote check from the repo)

**This repository and Cursor cannot SSH into your LAN** or read `/usr/local/bin` on **your** workstations. Only **you** can confirm install paths.

**On each Linux host** (SSH or local terminal), run:

```bash
command -v bw && bw --version
```

- **If you see a path + version:** CLI is on **`PATH`** for that shell user.
- **If empty / “not found”:** not installed for that user, or installed outside **`PATH`** (e.g. `~/bin`, `~/.npm-global/bin`).

**Optional** (shows lock state; may echo **account email** — **redact** if you paste output):

```bash
bw status
```

**Debian/Ubuntu** (only if installed via `apt` / `.deb`):

```bash
dpkg-query -W -f='${Status}\t${Package}\t${Version}\n' bitwarden-cli 2>/dev/null || true
```

**Automated bundle:** [HOMELAB_HOST_PACKAGE_INVENTORY.md](HOMELAB_HOST_PACKAGE_INVENTORY.md) — run `scripts/homelab-host-report.sh` on **each** host; it prints a **`bw`** block when present.

**Windows (e.g. dev laptop):** The **desktop** Bitwarden app does **not** install **`bw`**. Install **Bitwarden CLI** separately (for example **`winget install Bitwarden.CLI`** — confirm the current package ID with **`winget search`**). After install, reopen the terminal and check `where bw` in **cmd** or `Get-Command bw` in **PowerShell**. Full workstation notes (Topgrade, WSL, one-package-manager-per-tool): [OPERATOR_PACKAGE_MAINTENANCE_AND_BW_CLI.md](OPERATOR_PACKAGE_MAINTENANCE_AND_BW_CLI.md).

---

## Homelab alignment

- **Internal** topology (VLANs, IPs): Bitwarden Secure Note **or** **`docs/private/homelab/`** — pick one system of record ([PRIVATE_OPERATOR_NOTES.md](../PRIVATE_OPERATOR_NOTES.md)).
- **Solar / inverter API keys:** Bitwarden + public docs only describe **where** to put keys, not the values ([HOMELAB_SOLAR_MONITORING_INTEGRATION.md](HOMELAB_SOLAR_MONITORING_INTEGRATION.md)).

---

## Plan decision notes (maintainer-only path)

**Families / Premium / Teams** trade-offs and “no AI seat” — optional private notes: **`docs/private/operator_economics/BITWARDEN_SUBSCRIPTION_DECISION_NOTES.md`** (local workspace only; layout pointer: **`docs/private.example/economics/README.md`**).

## See also

- [OPERATOR_PACKAGE_MAINTENANCE_AND_BW_CLI.md](OPERATOR_PACKAGE_MAINTENANCE_AND_BW_CLI.md) — Windows / WSL / Linux package hygiene, `bw` install, Topgrade and `gta`.
- [SECURITY.md](../../SECURITY.md) — redaction, env-based secrets, `config.yaml` hygiene.
- [PLAN_SECRETS_VAULT.md](../plans/PLAN_SECRETS_VAULT.md) — Phase B in-app vault (separate track).
- [CONTRIBUTING.md](../../CONTRIBUTING.md) — do not commit credentials.

**Português (Brasil):** [OPERATOR_SECRETS_BITWARDEN.pt_BR.md](OPERATOR_SECRETS_BITWARDEN.pt_BR.md)
