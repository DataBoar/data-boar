param(
    [string]$EnvFile = "docs/private/homelab/.env.ssh.LAB-ROUTER-01-se-cursor.local",
    [string]$OutputPath
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Parse-EnvFile {
    param([Parameter(Mandatory = $true)][string]$Path)

    if (-not (Test-Path -LiteralPath $Path)) {
        throw "Env file not found: $Path"
    }

    $map = @{}
    foreach ($line in Get-Content -LiteralPath $Path) {
        if ($line -match "^\s*$") { continue }
        if ($line -match "^\s*#") { continue }
        if ($line -match "^\s*([A-Za-z_][A-Za-z0-9_]*)=(.*)$") {
            $key = $matches[1]
            $val = $matches[2]
            $map[$key] = $val
        }
    }

    return $map
}

function Require-Tool {
    param([Parameter(Mandatory = $true)][string]$Name)
    if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
        throw "Required tool not found in PATH: $Name"
    }
}

Require-Tool -Name "plink"

$cfg = Parse-EnvFile -Path $EnvFile

$sshAlias = $cfg["SSH_ALIAS"]
$sshHost = $cfg["SSH_HOST"]
$sshPort = if ($cfg["SSH_PORT"]) { $cfg["SSH_PORT"] } else { "22" }
$sshUser = if ($cfg["SSH_USER"]) { $cfg["SSH_USER"] } else { "root" }
$authMode = if ($cfg["SSH_AUTH_MODE"]) { $cfg["SSH_AUTH_MODE"].ToLowerInvariant() } else { "password" }
$sshPassword = $cfg["SSH_PASSWORD"]
$keyPath = $cfg["SSH_KEY_PATH"]
$hostKeyFingerprint = $cfg["SSH_EXPECTED_HOSTKEY_FINGERPRINT"]

if (-not $sshHost) {
    throw "Missing SSH_HOST in env file."
}

if ($authMode -notin @("password", "key")) {
    throw "Invalid SSH_AUTH_MODE '$authMode'. Use: password | key"
}

if (-not $OutputPath) {
    $ts = Get-Date -Format "yyyyMMdd_HHmmss"
    $OutputPath = "docs/private/homelab/reports/unifi_ssh_deep_audit_$ts.log"
}

$parent = Split-Path -Parent $OutputPath
if ($parent -and -not (Test-Path -LiteralPath $parent)) {
    New-Item -ItemType Directory -Path $parent -Force | Out-Null
}

$remoteCmd = @(
    "echo '=== audit_scope ==='",
    "echo 'read_only'",
    "echo '=== whoami ==='",
    "whoami",
    "echo '=== hostname ==='",
    "hostname",
    "echo '=== date ==='",
    "date",
    "echo '=== uname -a ==='",
    "uname -a",
    "echo '=== os-release ==='",
    "cat /etc/os-release",
    "echo '=== listening admin ports (top) ==='",
    "ss -lntup | sed -n '1,120p'",
    "echo '=== sshd -T subset ==='",
    "sshd -T 2>/dev/null | egrep '^(port|listenaddress|permitrootlogin|passwordauthentication|pubkeyauthentication|kbdinteractiveauthentication|allowusers|maxauthtries|maxsessions|clientaliveinterval|clientalivecountmax)' || true",
    "echo '=== sshd_config active lines ==='",
    "grep -v '^#' /etc/ssh/sshd_config 2>/dev/null | sed '/^$/d' || true",
    "echo '=== firewall chains (top) ==='",
    "(command -v iptables && iptables -S | sed -n '1,160p') 2>/dev/null || true",
    "(command -v nft && nft list ruleset | sed -n '1,160p') 2>/dev/null || true"
) -join "; "


if (-not $hostKeyFingerprint) {
    Write-Output "No SSH_EXPECTED_HOSTKEY_FINGERPRINT set; probing ed25519 host key fingerprint..."
    Require-Tool -Name "ssh-keyscan"
    Require-Tool -Name "ssh-keygen"

    $scan = & ssh-keyscan -T 8 -p $sshPort -t ed25519 $sshHost 2>$null
    if (-not $scan) {
        throw ("Unable to fetch host key fingerprint with ssh-keyscan for {0}:{1}" -f $sshHost, $sshPort)
    }

    $fpLine = $scan | ssh-keygen -lf - -E sha256
    if ($fpLine -notmatch "^(\d+)\s+(SHA256:[^\s]+)") {
        throw "Could not parse host key fingerprint from ssh-keygen output: $fpLine"
    }

    $bits = $matches[1]
    $fp = $matches[2]
    $hostKeyFingerprint = "ssh-ed25519 $bits $fp"
    Write-Output "Pinned host key fingerprint: $hostKeyFingerprint"
}

$plinkArgs = @("-batch", "-ssh", "-P", $sshPort, "-l", $sshUser)

if ($hostKeyFingerprint) {
    $plinkArgs += @("-hostkey", $hostKeyFingerprint)
}

if ($authMode -eq "password") {
    if (-not $sshPassword) {
        throw "SSH_AUTH_MODE=password but SSH_PASSWORD is empty."
    }
    $plinkArgs += @("-pw", $sshPassword)
}
else {
    if (-not $keyPath) {
        throw "SSH_AUTH_MODE=key but SSH_KEY_PATH is empty."
    }
    $plinkArgs += @("-i", $keyPath)
}

$plinkArgs += @($sshHost, $remoteCmd)

Write-Output "Running deep audit via SSH..."
Write-Output ("Target: {0}@{1}:{2}" -f $sshUser, $sshHost, $sshPort)
if ($sshAlias) {
    Write-Output "Alias: $sshAlias"
}
Write-Output "Auth mode: $authMode"

$raw = & plink @plinkArgs 2>&1
$exitCode = $LASTEXITCODE

$header = @(
    "=== local_runner ===",
    "timestamp=$(Get-Date -Format o)",
    "env_file=$EnvFile",
    ("target={0}@{1}:{2}" -f $sshUser, $sshHost, $sshPort),
    "auth_mode=$authMode",
    "exit_code=$exitCode",
    ""
)

$header + $raw | Set-Content -LiteralPath $OutputPath -Encoding UTF8

if ($exitCode -ne 0) {
    Write-Error "Deep audit failed (exit=$exitCode). See: $OutputPath"
}

Write-Output "Report written: $OutputPath"
