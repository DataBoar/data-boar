#Requires -Version 7.6.1
<#
.NAME
 scripts/maestro/Wait-HandlerSentinel.ps1

.SYNOPSIS
 Poll SSH targets until all requested handler sentinels report success or timeout. (#831)

.DESCRIPTION
 Each smoke handler (Handle-baremetal.ps1, Handle-docker.ps1, etc.) writes a sentinel file
 at /tmp/databoar_handler/<persona>_sentinel.txt containing the bash exit code when the smoke
 script finishes. This script polls those sentinel files via SSH and exits:
   0  - all requested handlers completed with exit 0 (pass)
   1  - one or more handlers timed out or exited non-zero (fail)
   2  - invalid usage or no nodes matching the requested personas

 Usage:
   Wait-HandlerSentinel.ps1 -Personas @("baremetal","docker") [-TimeoutSec 900] [-PollSec 10]

 Missing inventory or no matching nodes: exit 0 (nothing to wait for).
#>

param(
    [Parameter(Mandatory = $true)]
    [string[]]$Personas,
    [int]$TimeoutSec = 900,
    [int]$PollSec = 10
)

Set-StrictMode -Version 2
$ErrorActionPreference = "Continue"

$inventoryPath = Join-Path $PSScriptRoot "../../docs/private/homelab/data/inventory.json"
if (-not (Test-Path -LiteralPath $inventoryPath)) {
    exit 0
}

$inventory = Get-Content -LiteralPath $inventoryPath -Raw | ConvertFrom-Json
$sentinelDir = "/tmp/databoar_handler"

# Build list of (node, persona) pairs to wait for
$targets = [System.Collections.Generic.List[PSCustomObject]]::new()
foreach ($node in $inventory.lab_members) {
    foreach ($persona in $Personas) {
        if ($node.personas -contains $persona) {
            $targets.Add([PSCustomObject]@{
                Node    = $node
                Persona = $persona
                Done    = $false
                ExitCode = -1
            })
        }
    }
}

if ($targets.Count -eq 0) {
    exit 0
}

Write-Host ("      [HandlerSentinel] Waiting for {0} persona(s) on {1} target(s)..." -f ($Personas -join ","), $targets.Count) -ForegroundColor DarkGray

$deadline = (Get-Date).AddSeconds($TimeoutSec)
$anyFailed = $false

while ((Get-Date) -lt $deadline) {
    $pending = @($targets | Where-Object { -not $_.Done })
    if ($pending.Count -eq 0) { break }

    foreach ($t in $pending) {
        $remote      = "$($t.Node.user)@$($t.Node.hostname)"
        $sentinelFile = "$sentinelDir/$($t.Persona)_sentinel.txt"
        $result = ssh -q -o BatchMode=yes -o ConnectTimeout=8 $remote "cat $sentinelFile 2>/dev/null" 2>$null
        if ($LASTEXITCODE -eq 0 -and $null -ne $result) {
            $rc = ($result | Select-Object -First 1).Trim()
            if ($rc -match '^\d+$') {
                $t.Done     = $true
                $t.ExitCode = [int]$rc
                $statusTxt  = if ($rc -eq "0") { "PASS" } else { "FAIL (exit $rc)" }
                Write-Host ("      [HandlerSentinel] {0}@{1} persona={2}: {3}" -f `
                    $t.Node.user, $t.Node.hostname, $t.Persona, $statusTxt) -ForegroundColor DarkGray
                if ($rc -ne "0") { $anyFailed = $true }
            }
        }
    }

    if (@($targets | Where-Object { -not $_.Done }).Count -eq 0) { break }
    Start-Sleep -Seconds $PollSec
}

$timedOut = @($targets | Where-Object { -not $_.Done })
if ($timedOut.Count -gt 0) {
    foreach ($t in $timedOut) {
        Write-Warning ("      [HandlerSentinel] Timeout on {0} persona={1} after {2}s" -f `
            $t.Node.hostname, $t.Persona, $TimeoutSec)
    }
    $anyFailed = $true
}

exit $(if ($anyFailed) { 1 } else { 0 })
