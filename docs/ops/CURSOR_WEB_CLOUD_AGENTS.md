# Cursor Web / Cloud Agents — visibility, safety, and evidence capture

**pt-BR:** [CURSOR_WEB_CLOUD_AGENTS.pt_BR.md](CURSOR_WEB_CLOUD_AGENTS.pt_BR.md)

## Goal

Use Cursor Web / Cloud Agents to **reduce toil** (reproducible sandbox runs), without:

- leaking secrets,
- confusing LAN-only behavior (LAB-OP),
- or burning tokens on heavy gates unnecessarily.

## Do Cloud Agents require commits / PRs to “see” changes?

**Visibility rule of thumb:**

- **Uncommitted local changes**: Cloud Agents will **not** see them.
- **Local commits not pushed**: Cloud Agents will **not** see them.
- **Pushed commits to a branch**: Cloud Agents **can** see them (they pull from the remote repo).
- **PRs**: not strictly required for visibility, but **recommended** for:
  - reviewable context,
  - CI evidence,
  - and a durable “paper trail” (SRE-style).

So: **push is mandatory**, PR is **optional but usually worth it**.

## Safety constraints

- **No secrets** in:
  - setup/update scripts,
  - committed files,
  - or PR descriptions.
- Cloud Agents are not a substitute for **operator LAN** access or `docs/private/` workflows.

Source of truth: `.cursor/rules/cloud-agents-token-aware-safety.mdc`.

## Token-aware gating

Default (cheap) refresh gates:

- `uv sync`
- `uv run pre-commit run --all-files`

Run heavy gates only at milestones:

- pre-PR / pre-merge
- pre-version bump / pre-release / pre-publish
- pre-WRB (when you want “all green” evidence)

## Network troubleshooting (Chat/Agent fail on LAB but pass on DMZ/hotspot)

If Cursor Network Diagnostic shows:

- **Chat** failing with “streaming responses are being buffered by a proxy…”
- **Agent** failing with “bidirectional streaming is not supported by the http2 proxy…”

and at the same time **DMZ or phone hotspot** passes, the issue is in the **LAB-ROUTER-01/SSID/VLAN network path** (not in Windows).

### Quick checklist (LAB-ROUTER-01 / UniFi Network) — most likely order

1) **Traffic Routes / policy-based routing (VPN client / special egress path)**
   - Look for rules forcing the LAB SSID/VLAN through a different route/tunnel.
   - Temporarily disable and re-run the Diagnostic.

2) **Threat Management (IDS/IPS)**
   - Test “Detect only” (or Off for 2 minutes) and re-run.
   - If it fixes it, tune the profile/signatures rather than leaving it Off.

3) **Ad Blocking / Content filtering / DNS Shield (if enabled)**
   - Temporarily disable to isolate.

4) **Smart Queues / QoS / aggressive traffic shaping (if enabled)**
   - Temporarily disable to isolate.

### SRE evidence

- Keep two screenshots: Diagnostic **failing** on LAB SSID and **passing** on DMZ/hotspot.
- Record which toggle fixed it.

## Docker MCP Toolkit (MCP_DOCKER) in Cursor (local integration)

If `Settings → Tools & MCP` shows `MCP_DOCKER` as error, the most common causes are:

- the gateway is not running, and/or
- the `cursor` client is disconnected in `docker mcp`.

### Step-by-step (Windows)

1) In one terminal, keep the gateway running:

```powershell
docker mcp gateway run
```

1) In another terminal, connect the Cursor client:

```powershell
docker mcp client connect cursor
docker mcp client ls
docker mcp tools ls
```

1) Restart Cursor if needed (the CLI will hint when required).

### Notes

- This `docker mcp gateway` version uses `run` (no `start/status`).
- If an optional server (e.g. `dockerhub`) fails due to missing token, it doesn't block basic `MCP_DOCKER` usage.

## Evidence capture (SRE habit)

Treat Cloud Agent output like CI output:

- link to the run (or keep screenshots) as **evidence**
- store sensitive logs **only** under `docs/private/`
- keep redacted summaries in tracked docs when helpful

Private template: `docs/private.example/cursor_web/README.md` (copy to `docs/private/cursor_web/`).
