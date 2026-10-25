# BUS — gitleaks binary org-wide sweep

**Tracks:** DataBoar/maestro#10, DataBoar/maestro#69 (org-wide), perf reference **maestro PR #11**.

## Problem

After repos moved from a personal account to the **DataBoar** org, `gitleaks/gitleaks-action@v2`
requires a **paid org license**. The upstream **gitleaks CLI** remains open-source and free.

## Decision

Replace every `gitleaks/gitleaks-action@…` step with a **pinned binary** install:

1. Download official release tarball (`VER` + `linux_x64`).
2. Verify `sha256sum` against `gitleaks_${VER}_checksums.txt`.
3. Run `./gitleaks git . --no-banner --redact --exit-code 1` with `fetch-depth: 0`.

**Never** use `latest` without checksum. **Never** commit API keys or license files for the Action.

## Canonical workflow (lite — docs / scaffold / souls)

Copy to `.github/workflows/gitleaks.yml`. Pin `actions/checkout` to full SHA (ADR 0005 habit).

```yaml
name: Gitleaks

permissions:
  contents: read

on:
  push:
    branches: [main, master]
  pull_request:
    branches: [main, master]
  workflow_dispatch:

jobs:
  scan:
    name: Secret scan (Gitleaks)
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@df4cb1c069e1874edd31b4311f1884172cec0e10 # v6.0.3
        with:
          fetch-depth: 0
          persist-credentials: false

      - name: gitleaks (binary, no org-license)
        run: |
          VER="8.30.1"
          BASE="https://github.com/gitleaks/gitleaks/releases/download/v${VER}"
          TARBALL="gitleaks_${VER}_linux_x64.tar.gz"
          curl -sSfL "${BASE}/${TARBALL}" -o "${TARBALL}"
          curl -sSfL "${BASE}/gitleaks_${VER}_checksums.txt" -o gl.sums
          grep " ${TARBALL}$" gl.sums | sha256sum -c -
          tar -xzf "${TARBALL}" gitleaks
          ./gitleaks git . --no-banner --redact --exit-code 1
```

**Full** variant (product repos): add weekly `schedule`, `.gitleaks.toml` allowlists, Slack
failure notify — see `data-boar/.github/workflows/gitleaks.yml`.

## Per-repo ritual (grep → swap → PR → green)

| Step | Action |
| ---- | ------ |
| 1 | `rg 'gitleaks-action' .github/workflows` — if hit, swap step for binary block above |
| 2 | If no `gitleaks.yml`, **add** lite workflow (keep existing `paranoid-governance` inline grep) |
| 3 | Branch `ci/gitleaks-binary-org-sweep`, one PR per repo, title `ci(gitleaks): binary pin (org-wide #10)` |
| 4 | `gh pr checks` green → merge (operator/Cursor) |
| 5 | Tick row in inventory below |

## Inventory (2026-07-02 audit)

| Repo | gitleaks.yml | Notes |
| ---- | ------------ | ----- |
| data-boar | BINARY | full + slack optional |
| maestro | BINARY | ref PR #11 |
| carrion-crow | BINARY | `.gitleaksignore` for fixtures (#7) |
| quirky-quati | ADD | has ci/codeql |
| license-studio | ADD | go.yml only |
| souls (paranoid-governance) | ADD | 9 repos — keep governance workflow |
| data-boar-shared | ADD | docs |
| data-boar-site | ADD | static site |
| faithful-ferret, sage-remora, resolute-rikki, polyglot-pangolin | ADD | no workflows yet |
| homing-robin, platypus, stealthy-stoat | ADD when content exists | |
| data-boar-sdk, data-boar-sidecars | SKIP | empty placeholders |

## Out of scope (this BUS)

- UMADR normalization (#994) — next sweep
- semgrep mutable-action-tag pins (maestro#12) — after gitleaks green
- DNS / domain / HubSpot secrets — operator only

## References

- [gitleaks releases](https://github.com/gitleaks/gitleaks/releases)
- data-boar ADR 0005 (Action SHA pins)
