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
5. Install: copy `quadlet/*` to `~/.config/containers/systemd/`, then
   `systemctl --user daemon-reload`.
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
