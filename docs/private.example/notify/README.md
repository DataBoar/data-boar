# Operator notify — local secrets layout (template)

**Copy this tree into gitignored `docs/private/notify/`** on each machine. This folder under **`private.example/`** is **tracked** only as a **blueprint**; **real** credentials, Signal session data, and phone numbers must **never** be committed.

## Why

- Run **Signal** (`signal-cli` / **signald**) or **SMS** (e.g. Twilio) **locally** or on your **homelab** host.
- **Bind-mount** a directory under **`docs/private/notify/`** into the container so session state and `.env` stay **outside Git**.
- **Trigger** sends with a **script you run** (PowerShell, bash) or a scheduled task—**not** from the public repo with embedded secrets.

## Suggested layout (create under `docs/private/notify/`)

| Path (local only)        | Use                                                                                                                   |
| ------------------------ | ---                                                                                                                   |
| `.env`                   | API keys, SMTP, Twilio SID/token, **never** commit. Add `.env` to `.gitignore` if you ever move this tree by mistake. |
| `signald/` or `signal/`  | **signald** / **signal-cli** data directory as required by the image you choose (follow that image’s docs).           |
| `logs/` (optional)       | Local debug logs; gitignored with parent `docs/private/`.                                                             |

**Collaborators:** Replicate the **same layout** under **their own** `docs/private/notify/` with **their** numbers, sessions, and keys. Nothing in this template grants access to anyone else’s setup.

## Docker (illustrative only)

Adjust image names and flags to match the image you audit and trust:

```bash
# Example shape: mount local state + env (paths are on the HOST)
docker run --rm \
  -v "$(pwd)/docs/private/notify/signald:/signald" \
  --env-file docs/private/notify/.env \
  … your-signald-image …
```

Do **not** paste real host paths, tokens, or phone numbers into **tracked** Markdown.

## Signal on a **different** machine (LAB‑OP — spare lab host)

To **keep CPU/RAM off the dev workstation**, run **signald** / **signal-cli REST** in Docker on **another host** on your LAN (same idea as parking **Uptime Colleague-Ma** integrations on a server). Then **trigger** from anywhere that can reach it:

- Put the **base URL** (and optional API token) in **`docs/private/notify/.env`** on the machine that *sends* the request — e.g. `SIGNAL_REST_URL=http://<lab-host>:<port>` — **never** commit.
- **Call** the API with **`curl`** (headers + JSON body) exactly like you would from Uptime Colleague-Ma: same pattern, different endpoint and payload per your image’s docs.
- **Network:** restrict who can hit that port (**firewall** / Docker publish only on **RFC1918**, or **Tailscale**); do not expose the Signal bridge to the public internet without hardening.
- **Cursor / agent:** does **not** call your lab by itself; **you** run `curl` from the dev PC terminal, or a **local script**, or the lab host runs **cron** — the agent only helps **draft** the command if you paste a redacted example.

## Trigger script (your repo or local)

Keep **`scripts/`** versions **generic**: read paths from env vars or default to `docs/private/notify/.env`. Optional `scripts/notify-operator-local.example.ps1` may be added later as a **stub** (no secrets, no real endpoints).

## See also

- **[OPERATOR_NOTIFICATION_CHANNELS.md](../../ops/OPERATOR_NOTIFICATION_CHANNELS.md)** ([pt-BR](../../ops/OPERATOR_NOTIFICATION_CHANNELS.pt_BR.md)) — tiers A–D, Signal §3, EOD digest §7.
- **[PRIVATE_OPERATOR_NOTES.md](../../PRIVATE_OPERATOR_NOTES.md)** — `docs/private/` policy.
