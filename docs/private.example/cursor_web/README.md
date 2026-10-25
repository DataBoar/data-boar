# Cursor Web / Cloud Agents — private evidence folder (template)

Copy this folder to `docs/private/cursor_web/` (gitignored) on the operator machine.

## What to store here

- Cloud Agent “environment setup” screenshots (snapshot + update script)
- Links to Cloud Agent runs (or exported run logs) that include sensitive details
- Any secret-bearing troubleshooting notes (never commit)

## Recommended naming

- `YYYY-MM-DD_cloud-agent_setup_<topic>.png`
- `YYYY-MM-DD_cloud-agent_run_<branch>_<topic>.txt`
- `YYYY-MM-DD_cloud-agent_notes.md`

## Redaction policy

If you need to share something publicly (issue/PR):

- remove hostnames, internal URLs, tokens, and anything operator-identifying
- prefer a short summary + “how to reproduce”

