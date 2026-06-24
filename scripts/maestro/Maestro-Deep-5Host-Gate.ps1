#Requires -Version 7
<#
.SYNOPSIS
  Deep gate + handlers smoke on five lab-op hosts (#1021 re-Deep harness).

.DESCRIPTION
  Sync WorkingTree, gate --apply, handlers -Deep per persona; prints summary with
  Handlers column OK | ALARM:N | FAIL:N (#1021 R9b).
#>
$ErrorActionPreference = "Continue"
$repo = (Resolve-Path "$PSScriptRoot/../..").Path
$maestro = "$PSScriptRoot"
Set-Location $repo
. "$maestro/Lab-MaestroCommon.ps1"

$invPath = "$repo/docs/private/homelab/data/inventory.json"
if (-not (Test-Path -LiteralPath $invPath)) {
    Write-Error "Missing inventory: $invPath"
    exit 2
}
$inv = Get-Content $invPath -Raw | ConvertFrom-Json
# Host list from private inventory only (no hardcoded hostnames in tracked tree — PII gate).
$targets = @($inv.lab_members | Where-Object {
        $_.hostname -and ($_.ip -match '^\d+\.\d+\.\d+\.\d+$')
    })
$log = if ($env:MAESTRO_DEEP_LOG) { $env:MAESTRO_DEEP_LOG } else { "/tmp/maestro-deep-5host-gate.log" }
Remove-Item $log -ErrorAction SilentlyContinue
$summary = @()

"=== Pre-flight Build-ContainerArtefact $(Get-Date -Format o) ===" | Tee-Object -FilePath $log -Append
& "$maestro/Build-ContainerArtefact.ps1" 2>&1 | Tee-Object -FilePath $log -Append

foreach ($node in $targets) {
    $name = $node.hostname
    "`n########## DEEP: $name $(Get-Date -Format o) ##########" | Tee-Object -FilePath $log -Append | Out-Null
    if (-not $node) { "SKIP missing node" | Add-Content $log; continue }
    if ($node.ip -match '[^0-9.]') { "SKIP bad IP" | Add-Content $log; continue }
    $octets = ($node.ip -split "\.")[0..2] -join "."
    $node | Add-Member -NotePropertyName lab_op_subnet -NotePropertyValue "$octets.0/24" -Force

    $status = & "$maestro/Get-LabStatus.ps1" -TargetHost $node.hostname -TargetUser $node.user 2>&1
    $status | Tee-Object -FilePath $log -Append
    if ($status.SSH -ne "UP") {
        $summary += [pscustomobject]@{ Host = $name; Sync = "-"; Gate = "SSH_DOWN"; Handlers = "-" }
        continue
    }

    Write-Host ">>> Sync $name" -ForegroundColor Cyan
    $syncOk = [bool](& "$maestro/Sync-WorkingTree.ps1" -Node $node -Ref WorkingTree)
    "Sync result: $syncOk" | Tee-Object -FilePath $log -Append
    if (-not $syncOk) {
        $summary += [pscustomobject]@{ Host = $name; Sync = "FAIL"; Gate = "-"; Handlers = "SKIP" }
        continue
    }

    $isContainer = ($node.personas -contains "docker") -or ($node.personas -contains "podman") -or ($node.personas -contains "dockerswarm")
    if ($isContainer) {
        & "$maestro/Sync-ContainerArtefact.ps1" -Node $node 2>&1 | Tee-Object -FilePath $log -Append
    }

    Write-Host ">>> Gate -Deep $name" -ForegroundColor Cyan
    $gateOk = Invoke-LabopGateReadiness -Node $node -Deep
    "Gate result: $gateOk" | Tee-Object -FilePath $log -Append

    $handlerFails = 0
    $handlerAlarms = 0
    $handlerRan = 0
    if ($gateOk) {
        $ordered = $node.personas | Sort-Object {
            switch ($_) {
                "docker" { 0; break }
                "podman" { 0; break }
                "dockerswarm" { 0; break }
                "web" { 2; break }
                default { 1; break }
            }
        }
        foreach ($persona in $ordered) {
            $handler = "$maestro/handlers/Handle-$persona.ps1"
            if (-not (Test-Path -LiteralPath $handler)) {
                "HANDLER_MISSING: $persona" | Add-Content $log
                continue
            }
            Write-Host "   Handler $persona on $name" -ForegroundColor DarkCyan
            & $handler -Node $node -Ref WorkingTree -Deep 2>&1 | Tee-Object -FilePath $log -Append
            $handlerRan++
            Add-MaestroHandlerExitTally -ExitCode $LASTEXITCODE -FailCount ([ref]$handlerFails) -AlarmCount ([ref]$handlerAlarms)
        }
    } else {
        "HANDLERS_SKIPPED gate failed (Maestro contract)" | Add-Content $log
    }

    $handlersLabel = Format-MaestroHandlersSummary -GateOk $gateOk -HandlerRan $handlerRan `
        -HandlerFails $handlerFails -HandlerAlarms $handlerAlarms
    $summary += [pscustomobject]@{
        Host     = $name
        Sync     = "OK"
        Gate     = if ($gateOk) { "OK" } else { "ALARM" }
        Handlers = $handlersLabel
    }
}

"`n=== SUMMARY $(Get-Date -Format o) ===" | Add-Content $log
$summary | Format-Table | Out-String | Tee-Object -FilePath $log -Append
$summary | Format-Table

"`n=== GR LINES ===" | Add-Content $log
Get-Content $log | Select-String -Pattern 'GR host=' | ForEach-Object { $_.Line.Trim() } | Tee-Object -FilePath $log -Append

$totalFails = ($summary | Where-Object { $_.Handlers -like 'FAIL:*' }).Count
if ($totalFails -gt 0) { exit 1 }
exit 0
