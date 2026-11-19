# Public demo deployment (`dashboard.net.br`, #1447)

Versioned Quadlet units that reproduce the public demo on a single host with
rootless Podman. Host-specific values (hostname, addresses, passwords, edge
configuration) are **not** in this repository; they live on the host and in the
private runbook.

| File | Purpose |
| ---- | ------- |
| `quadlet/dashboard.container` | Main instance (port 8088). Restores `~/demo/data` from `~/demo/baseline` on every start. |
| `quadlet/apresentacao.container` | Presentation instance (port 8089). Never reset. |
| `quadlet/demo-reset.timer` + `.service` | Every 30 minutes: `systemctl --user restart dashboard.service`. Runs no container itself. |
| `quadlet/samba.container` | Read-only SMB share of `~/demo/corpus` on `127.0.0.1:4450`, 96 MiB limit. |
| `samba/container.json` | sambacc share and globals (read-only share `corpus`, SMB3). |
| `samba/users.example.json` | Template for `~/demo/samba/users.json` (host only, never committed). |
| `bin/demo-restore-baseline.sh` | Baseline restore, run as the dashboard's `ExecStartPre` (Linux host only). |

Why the reset changed: the previous oneshot unit ran `podman start` itself, so
the container's `conmon` stayed in the oneshot's cgroup and systemd killed it
at the stop timeout, leaving the container without a monitor. Restarting the
Quadlet service keeps `conmon` in `dashboard.service`.

## Apply on the demo host (operator action)

Run as the demo user, after taking the backup in step 1.

1. Back up: `cp -a ~/demo ~/demo.bak-$(date +%Y%m%d-%H%M)` and save the
   current `podman run` commands and `~/.config/systemd/user/demo-reset.*`.
2. Create the baseline from the clean data directory (right after a reset):
   `podman unshare cp -a ~/demo/data/. ~/demo/baseline/` (must contain
   `config.yaml`).
3. Copy files: `bin/demo-restore-baseline.sh` to `~/demo/bin/` (executable),
   `samba/container.json` to `~/demo/samba/`, and create
   `~/demo/samba/users.json` from the example with a real password (mode 600).
   The corpus must be world-readable (`chmod -R o+rX ~/demo/corpus`).
4. Stop the old units and containers:
   `systemctl --user disable --now demo-reset.timer demo-reset.service`,
   then `podman stop -t 20 dashboard apresentacao && podman rm dashboard apresentacao`.
5. Install: copy `quadlet/*` to `~/.config/containers/systemd/`, except the
   prospect pod files (`demo-prospect*` and `demo-slot-restore.service`, see the
   next section), then `systemctl --user daemon-reload`.
6. Start: `systemctl --user start dashboard apresentacao samba demo-reset.timer`.
7. Check: `systemctl --user list-timers demo-reset.timer`;
   `systemctl --user start demo-reset.service` must end with `Result=success`;
   `podman exec dashboard true` must work afterwards.
8. To scan SMB from the dashboard, add a target to the baseline `config.yaml`
   (`type: smb`, `host: 127.0.0.1`, `port: 4450`, `share: corpus`,
   `allow_private_networks: true`, `pass_from_env` pointing at a variable in
   `~/demo/env`). The SMB connector is a Pro-tier connector.

## Rollback (operator action)

1. `systemctl --user disable --now demo-reset.timer` and
   `systemctl --user stop dashboard apresentacao samba`.
2. Remove the copied files from `~/.config/containers/systemd/`, then
   `systemctl --user daemon-reload`.
3. Restore `~/demo` from the backup of step 1 and re-run the saved `podman run`
   commands and the previous reset units.

## Prospect pods (`prospect-up` / `prospect-down`, #2280)

During a presentation, one ephemeral Data Boar instance only for one prospect,
at `https://<slug>.dashboard.net.br/`. The host runs at most two Data Boar
instances, so the pod **takes the dashboard slot**: `prospect-up` stops the
public `dashboard` (never removes it), and `prospect-down` or the TTL reaper
brings it back and checks its `/status`. One prospect at a time; the
`apresentacao` is never touched. Design: `docs/desenho/2280.1.md`.

| File | Purpose |
| ---- | ------- |
| `prospect/prospect.py` | CLI (Python 3.11+, standard library only): `up`, `down`, `list`, `reap`, `restore-slot`, `teardown`. Reads the private inventory `~/demo/prospect/inventory.json` (mode 600) or `$PROSPECT_INVENTORY`. |
| `prospect/config.prospect.yaml` | Pod config: synthetic corpus only, no network target, API key from the pod env, profile and recommendations copied from host files. |
| `prospect/site.caddy.tmpl` | Per-host proxy route: `basic_auth` with an operator-supplied password (hashed by the CLI), the pod API key injected, the pod certificate pinned, no `log`. |
| `quadlet/demo-prospect@.container` | Pod template: internal network per slug, port only on `127.0.0.1`, 700 MiB without swap, read-only root, tmpfs data, no capabilities, `LogDriver=none`, no `[Install]`. The signed image and the license hostname come from the host drop-in `demo-prospect@.container.d/10-host.conf` (never in the repo). |
| `quadlet/demo-prospect.slice` | `MemoryMax=720M` for the pod. |
| `quadlet/demo-slot-restore.service` | Oneshot that runs `prospect.py restore-slot`; the pod's `ExecStopPost` starts it with `--no-block`. |
| `quadlet/demo-prospect-reap.timer` + `.service` | Every 2 minutes: `prospect.py reap` (expired or dead pods, labelled orphans, the dashboard slot). |

How the slot is handled:

- `up` writes `slot.json` before stopping anything, stops `demo-reset.timer` if
  active, then `podman stop -t 20 dashboard` (mode `podman`) or
  `systemctl --user stop dashboard.service` (mode `systemd`).
- The dashboard comes back only through
  `systemd-run --user --scope --collect podman start dashboard`, so its `conmon`
  lives in its own scope and is not killed with a oneshot (the scar described
  above).
- If the dashboard does not come back healthy (`trust_state` `trusted` and
  `integrity.integrity_state` `validated`), the command exits 8 and alerts once
  per incident: a journal line (`journalctl --user -t databoar-prospect -p err`),
  the `ALERT` file and the optional `prospect_alert_cmd`. The reaper retries every
  cycle without repeating the alert.

Exit codes: 0 success (also idempotent), 2 invalid usage or missing
`--stop-dashboard`, 3 leftovers, 4 another prospect active or instance count or
port or memory out of the model, 5 host prerequisite or inventory, 6 proxy
refused the route, 7 pod not healthy or license not valid, 8 dashboard did not
come back.

### Apply prospect pods (operator action, after the proxy changes of task 2280.5)

1. The `demo_prospect` Ansible role (task 2280.3) installs the CLI and the two
   templates in `~/demo/prospect/bin/`, the inventory, the `prospect-up`,
   `prospect-down` and `prospect-list` shortcuts in `~/.local/bin`, the pod
   template and its `10-host.conf` in `~/.config/containers/systemd/`, and the
   slice, `demo-slot-restore.service` and the reaper in
   `~/.config/systemd/user/`, with the reaper timer enabled.
2. Check: `prospect-list` shows `dashboard: no ar`;
   `systemctl --user list-timers demo-prospect-reap.timer` shows the timer.
3. Session: generate a password (at least 20 characters), then
   `printf '%s\n' '<password>' | prospect-up <slug> --stop-dashboard --password-stdin [--ttl 30m]`
   prints the URL, the user `prospect`, `expires_at` and the warning that the
   public dashboard is down (the password is not echoed). `prospect-down <slug>` ends it.
4. Maintenance: with the reaper timer enabled, a `dashboard` stopped outside a
   prospect session is started again within 2 minutes, a planned maintenance
   included. Run `systemctl --user stop demo-prospect-reap.timer` before stopping
   the `dashboard`, and `systemctl --user start demo-prospect-reap.timer` after.
   While a prospect pod is alive, `prospect-down` of another slug,
   `prospect.py restore-slot` and the reaper leave the `dashboard` stopped and
   print `dashboard não religada: slot ocupado por <slug>`.

### Rollback of prospect pods (operator action)

1. `prospect-down <slug>` for any active session, then
   `systemctl --user disable --now demo-prospect-reap.timer`.
2. Remove the files of step 1 of "Apply prospect pods" and run
   `systemctl --user daemon-reload`.
3. Check that `dashboard` is `running` (`podman ps`) and that no
   `databoar.prospect` container or network is left
   (`podman ps -a --filter label=databoar.prospect`,
   `podman network ls --filter label=databoar.prospect`).
