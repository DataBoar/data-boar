# Windows desktop scan over SMB: recipe and measurement template (Phase 0)

**Português (Brasil):** [WINDOWS_DESKTOP_SMB_SCAN_RECIPE.pt_BR.md](WINDOWS_DESKTOP_SMB_SCAN_RECIPE.pt_BR.md)

> **Status: DRAFT WITHOUT MEASUREMENTS.** No pilot has been run. Every statement about how this
> behaves at scale is a **hypothesis to confirm or refute**. Do not quote capacity, duration or
> "supports N machines" from this page. Plan: `docs/plans/PLAN_ENDPOINT_AGENT.md` (issue #2207).

## Goal

Reach Windows desktops that expose a share, using the existing SMB connector, **one Data Boar
instance per VLAN**, and learn what that costs before anyone designs an endpoint agent.

## Topology

```text
VLAN 10 desktops  <--SMB-->  Data Boar instance 10  --\
VLAN 20 desktops  <--SMB-->  Data Boar instance 20  ---+--> review per instance
VLAN 30 desktops  <--SMB-->  Data Boar instance 30  --/    (see MULTI_INSTANCE_FINDINGS_CSV_POC.md)
```

## Target configuration (one entry per machine or share)

Keys come from the SMB connector and `docs/USAGE.md`:

```yaml
- name: "desktop-pilot-001"
  type: smb
  host: "pc-001.corp.example"
  share: "C$"               # or a dedicated share; see the access hypothesis below
  path: "Users"
  user: "<service account>"
  pass: "<set through the project's secret handling, never a literal in a tracked file>"
  domain: "CORP"
  port: 445
  recursive: true
  allow_private_networks: true   # RFC1918 hosts need this opt-in (#1715); SMB refuses them otherwise
```

## Hypotheses to test (NOT facts)

| # | Hypothesis | How to test | Result |
| - | ---------- | ----------- | ------ |
| H1 | Needs an account with administrative access on every machine (or a dedicated share per machine) | Try a read-only service account against an admin share and against a dedicated share | not measured |
| H2 | Machines that are powered off or off the network are not reached | Count unreachable hosts per run | not measured |
| H3 | Bulk reads can trigger endpoint-protection alerts | Coordinate with the security team before the run; record alerts | not measured |
| H4 | Scale and wall-clock time are unknown | Record the metrics below | not measured |

## Pilot protocol (20 to 50 machines)

1. Get written approval from the desktop and security owners; pick a window outside business hours.
2. Choose 20 to 50 representative machines (mix of hardware age and user profile); no production
   data leaves the premises, and findings stay metadata-only.
3. Run one instance for the pilot VLAN; record the start and end of each target.
4. Fill the table below **from the run output**, not from memory. Leave a cell as "n/a" if it
   was not captured.
5. Stop immediately on any user-visible impact or on a security-team request.

## Measurement template (fill after the pilot)

| Metric | Value | How captured |
| ------ | ----- | ------------ |
| Machines targeted | | |
| Machines reached | | |
| Unreachable machines, by cause (off, firewall, credentials, other) | | |
| Wall-clock per machine (median, worst) | | |
| Total wall-clock for the VLAN | | |
| Data read per machine (median, worst) | | |
| Network load during the run (peak) | | |
| Findings per machine (metadata-only) | | |
| Failures, by cause | | |
| Endpoint-protection alerts raised | | |
| User-visible impact reported | | |

## Decision this recipe feeds

If the pilot shows the SMB path is acceptable for a class of estates, document the supported
shape here with the measured numbers. If it is not, that is the evidence for Phase 1 (endpoint
agent) in the plan. Either outcome is a valid result; an unmeasured claim is not.
