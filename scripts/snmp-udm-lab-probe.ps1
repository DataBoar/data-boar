#Requires -Version 5.1
<#
.SYNOPSIS
  Optional SNMPv3 walk to LAB-ROUTER-01-SE (interfaces table) using secrets from environment variables only.

.DESCRIPTION
  Do NOT pass passwords on the command line in chat. Set variables in the same PowerShell session:

    $env:LAB_LAB-ROUTER-01_SNMP_HOST = "<gateway IP>"
    $env:LAB_LAB-ROUTER-01_SNMP_V3_USER = "..."
    $env:LAB_LAB-ROUTER-01_SNMP_AUTH_PASS = "..."
    $env:LAB_LAB-ROUTER-01_SNMP_PRIV_PASS = "..."

  **Windows:** Native `snmpwalk.exe` is uncommon. This script:
  1) Uses `snmpwalk` if it is on PATH (rare on Windows), else
  2) Uses **WSL** (`wsl.exe`) if installed and `snmpwalk` exists inside the default distro.

  Install Net-SNMP **inside WSL** (not on Windows): open your Linux distro, then:
    sudo apt update && sudo apt install -y snmp
  (Optional MIB names: `snmp-mibs-downloader` on some releases needs **non-free**; not required for this script  - numeric OIDs work without it.)

  Optional: -WslDistro "Ubuntu-22.04" if your default distro is wrong (see: wsl -l -v).

  **Multiple devices:** same four variable names in different gitignored files (e.g. `.env.snmp.gateway.local`,
  `.env.snmp.switch.local`). Use **-EnvFile** so you do not overwrite credentials between runs:
    .\scripts\snmp-LAB-ROUTER-01-lab-probe.ps1 -EnvFile docs\private\homelab\.env.snmp.switch.local -WslDistro Debian

.EXAMPLE
  .\scripts\snmp-LAB-ROUTER-01-lab-probe.ps1

.EXAMPLE
  .\scripts\snmp-LAB-ROUTER-01-lab-probe.ps1 -WslDistro "Debian"

.EXAMPLE
  .\scripts\snmp-LAB-ROUTER-01-lab-probe.ps1 -EnvFile docs\private\homelab\.env.snmp.switch.local -WslDistro Debian
#>
param(
    [string] $WslDistro = "",
    [string] $EnvFile = ""
)

$ErrorActionPreference = "Stop"

if ($EnvFile) {
    if (-not (Test-Path -LiteralPath $EnvFile)) {
        Write-Error "EnvFile not found: $EnvFile"
        exit 1
    }
    Get-Content -LiteralPath $EnvFile | Where-Object { $_ -and $_ -notmatch '^\s*#' } | ForEach-Object {
        $pair = $_ -split '=', 2
        if ($pair.Count -eq 2) {
            Set-Item -Path "Env:$($pair[0].Trim())" -Value $pair[1].Trim().Trim('"')
        }
    }
}

$hostIp = $env:LAB_LAB-ROUTER-01_SNMP_HOST
$user = $env:LAB_LAB-ROUTER-01_SNMP_V3_USER
$auth = $env:LAB_LAB-ROUTER-01_SNMP_AUTH_PASS
$priv = $env:LAB_LAB-ROUTER-01_SNMP_PRIV_PASS

if (-not $hostIp -or -not $user -or -not $auth -or -not $priv) {
    Write-Host @"
Missing env vars. Set in this session (do not paste secrets into chat):
  `$env:LAB_LAB-ROUTER-01_SNMP_HOST
  `$env:LAB_LAB-ROUTER-01_SNMP_V3_USER
  `$env:LAB_LAB-ROUTER-01_SNMP_AUTH_PASS
  `$env:LAB_LAB-ROUTER-01_SNMP_PRIV_PASS

Windows: install snmp tools inside WSL, then re-run this script from PowerShell.
See docs/private.example/homelab/CREDENTIALS_AND_LAB_SECRETS.md section ""SNMP on Windows (PowerShell + WSL)"".
"@
    exit 2
}

# Interfaces table OID (standard IF-MIB)
$oid = "1.3.6.1.2.1.2.2"
$snmpArgs = @(
    "-v3", "-l", "authPriv",
    "-u", $user,
    "-a", "SHA", "-A", $auth,
    "-x", "AES", "-X", $priv,
    $hostIp,
    $oid
)

$native = Get-Command snmpwalk -ErrorAction SilentlyContinue
if ($native) {
    & snmpwalk @snmpArgs
    exit $LASTEXITCODE
}

$wsl = Get-Command wsl.exe -ErrorAction SilentlyContinue
if (-not $wsl) {
    Write-Host @"
snmpwalk was not found on PATH, and wsl.exe was not found.

On Windows, use one of these:

  **A) WSL (recommended)**  - Install:  wsl --install   (then rColleague-Sot if prompted).
  In your Linux distro terminal:
    sudo apt update && sudo apt install -y snmp
  Back in PowerShell (same session where you set LAB_LAB-ROUTER-01_SNMP_*), run this script again.

  **B) Linux laptop/VM on the LAN**  - Run snmpwalk there (see HOMELAB_UNIFI_LAB-ROUTER-01_LAB_NETWORK.md).

  **C) Rare:** Add a Net-SNMP Windows build to PATH (project does not ship binaries).
"@
    exit 1
}

# Probe: same shell as snmpwalk run (bash -lc). Unique marker avoids false positives
# when WSL prints MOTD/banner text containing the letters "OK".
$probeScript = 'command -v snmpwalk >/dev/null 2>&1 && echo __SNMPWALK_PROBE_OK__'
$probe = ""
try {
    $probeArgs = @("-e", "bash", "-lc", $probeScript)
    if ($WslDistro) {
        $probe = & wsl.exe -d $WslDistro @probeArgs 2>$null
    } else {
        $probe = & wsl.exe @probeArgs 2>$null
    }
} catch {
    $probe = ""
}

$probeTrim = if ($probe) { $probe.Trim() } else { "" }
if ($probeTrim -ne "__SNMPWALK_PROBE_OK__") {
    Write-Host @"
snmpwalk is not installed inside WSL yet.

Open a **Linux** shell (Start menu -> your distro, or:  wsl $(if ($WslDistro) { "-d $WslDistro " }))

Then run **once** (Debian/Ubuntu inside WSL):
  sudo apt update
  sudo apt install -y snmp
  command -v snmpwalk
  # Expect: /usr/bin/snmpwalk  - if empty, snmp did not install.
  # Do NOT require snmp-mibs-downloader  - on Debian 13 (trixie) it may be in non-free or absent; this probe uses numeric OIDs only.

Return to **PowerShell**, keep your `$env:LAB_LAB-ROUTER-01_SNMP_*` variables, and run:
  .\scripts\snmp-LAB-ROUTER-01-lab-probe.ps1$(if ($WslDistro) { " -WslDistro `"$WslDistro`"" })

List distros:  wsl -l -v
If the default distro has no snmpwalk, pass -WslDistro `"NameFromList`".
"@
    exit 1
}

# Pass Windows env vars into WSL for snmpwalk only (Microsoft: WSLENV)
$prevWslEnv = $env:WSLENV
$forward = @(
    "LAB_LAB-ROUTER-01_SNMP_HOST",
    "LAB_LAB-ROUTER-01_SNMP_V3_USER",
    "LAB_LAB-ROUTER-01_SNMP_AUTH_PASS",
    "LAB_LAB-ROUTER-01_SNMP_PRIV_PASS"
) -join ":"
if ($prevWslEnv) {
    $env:WSLENV = "$forward`:$prevWslEnv"
} else {
    $env:WSLENV = $forward
}

# snmpwalk reads credentials from env inside WSL (forwarded via WSLENV); avoids echoing secrets in process argv
$remoteBash = @'
snmpwalk -v3 -l authPriv -u "$LAB_LAB-ROUTER-01_SNMP_V3_USER" -a SHA -A "$LAB_LAB-ROUTER-01_SNMP_AUTH_PASS" -x AES -X "$LAB_LAB-ROUTER-01_SNMP_PRIV_PASS" "$LAB_LAB-ROUTER-01_SNMP_HOST" OID_PLACEHOLDER
'@ -replace "OID_PLACEHOLDER", $oid

try {
    # Single argument to bash -lc (entire snmpwalk line)
    $bashInvoke = @("-e", "bash", "-lc", $remoteBash)
    if ($WslDistro) {
        & wsl.exe -d $WslDistro @bashInvoke
    } else {
        & wsl.exe @bashInvoke
    }
    $exitCode = $LASTEXITCODE
} finally {
    $env:WSLENV = $prevWslEnv
}

if ($null -eq $exitCode) { $exitCode = 0 }
exit $exitCode
