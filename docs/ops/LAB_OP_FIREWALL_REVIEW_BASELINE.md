# LAB-OP firewall review baseline (public-safe)

**pt-BR:** [LAB_OP_FIREWALL_REVIEW_BASELINE.pt_BR.md](LAB_OP_FIREWALL_REVIEW_BASELINE.pt_BR.md)

## Purpose

Record a reviewable and study-friendly baseline of firewall posture without exposing private inventory details (hostnames, LAN topology, management endpoints, or secrets).

## Scope

- Read-only review of firewall and console settings.
- No destructive action (`apply`, `reset`, `root`) during the review.
- Findings are mapped to prioritized remediation phases.

## Public-safe findings snapshot

### Current strengths

- WAN boundary follows default-deny behavior.
- Internal segmentation model is active (isolate + explicit allow exceptions).
- Security add-ons/content filtering are enabled in baseline form.

### Priority risks (generic)

- **P1:** drop-rule observability can be improved (logging and auditability).
- **P1:** potential stale/orphan rule entries need ownership validation.
- **P1:** admin-access hardening baseline needs explicit periodic verification.
- **P2:** outbound controls from less-trusted segments can be tightened.
- **P2:** alias/group naming and ownership metadata can be clearer.

## Score model

- **Current score:** **74/100**
- **Projected score after remediation:** **82-88/100**

Scoring rationale emphasizes: perimeter deny posture, segmentation quality, admin-plane hardening, rule hygiene, and operational observability.

## Recommended rollout (safe order)

### Phase A - no downtime

1. Enable and validate drop-rule logging.
2. Audit suspicious/stale rules and disable before removal.
3. Register ownership and purpose for allow exceptions.

### Phase B - admin-plane hardening

1. Verify management access baseline (method, origin restriction, minimum exposure).
2. Keep unnecessary remote-management paths disabled by default.

### Phase C - controlled egress hardening

1. Move lower-trust segments toward explicit egress allow-lists.
2. Keep rollback steps pre-defined per rule batch.

## SSH-assisted deep audit access (public-safe)

Use this when GUI does not expose full admin-plane details (for example SSH daemon status/port/origin restrictions).

1. Configure an SSH host alias on the operator workstation (`~/.ssh/config`).
2. Confirm key-based auth works (`ssh <alias> 'whoami'`).
3. Keep least privilege by default:
   - use read-only commands first;
   - prefer targeted `sudo -n` checks over broad root shells.
4. Store host-specific values and exact commands only in `docs/private/homelab/` (gitignored).
5. Ask the assistant to run the deep audit from the integrated terminal using that alias.

Public docs should keep only the workflow. Never publish hostnames, LAN IPs, management URLs, keys, or tokens.

### Reusable automation

- Script: `scripts/unifi-ssh-deep-audit.ps1`
- Input: private `.env` (for example: `docs/private/homelab/.env.ssh.LAB-ROUTER-01-se-cursor.local`)
- Output: log file under `docs/private/homelab/reports/`

Example:

```powershell
.\scripts\unifi-ssh-deep-audit.ps1 -EnvFile "docs/private/homelab/.env.ssh.LAB-ROUTER-01-se-cursor.local"
```

## Private/public split policy

- **Private truth:** `docs/private/homelab/LAB_OP_FIREWALL_REVIEW_2026-04-05.pt_BR.md`
- **Public abstraction:** this runbook (generic, no sensitive topology).

Use the private document for operations and incident handling, and this public one for process review, onboarding, and study references.

## Concrete step-by-step (enable + validate SSH)

> Session-validated state: `unifi.local` resolves and port 22 is reachable, but authentication fails with `Permission denied (publickey,keyboard-interactive)`.

1. Open UniFi with an admin account at the exact path: `System > Control Panel > Console > SSH`.
2. Enable `SSH`.
3. Run `Change Password` (or register a public key in the equivalent option).
4. Apply and wait for provisioning.
5. Validate from the operator terminal:
   - `ssh -o BatchMode=yes -o ConnectTimeout=8 LAB-ROUTER-01-se-cursor "echo SSH_OK && whoami"`
6. If authentication fails, check effective user and auth method:
   - `ssh -G LAB-ROUTER-01-se-cursor | findstr /R "^user "`
   - confirm correct `User` in the alias block in `~/.ssh/config`;
   - confirm whether password or key mode is expected.
7. If connectivity fails (timeout/refused), review:
   - SSH enabled on the correct target;
   - configured port (22 or custom);
   - ACL/firewall path between workstation and gateway.

Only after step 5 succeeds should deep hardening audit commands be executed.
