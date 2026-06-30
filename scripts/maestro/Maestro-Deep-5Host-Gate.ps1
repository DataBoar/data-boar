#Requires -Version 7
<#
.SYNOPSIS
  Deep gate + handlers smoke on five lab-op hosts (#1021 re-Deep harness).

.DESCRIPTION
  Sync WorkingTree, gate --apply, handlers -Deep per persona; prints summary with
  Handlers column OK | ALARM:N | FAIL:N (#1021 R9b).
  #1021 R11: -Detach runs under tmux+setsid (avoid nohup orphan); -IdempotentTwice runs two passes.
  #1021 R12: idempotency compare uses Compare-MaestroDeepGateSummaries (no Format-Table pipeline pollution).
  #1021 R12.1: Get-MaestroDeepSummaryRows flattens pass return; row-count guard must match gate host list.
#>
param(
    [switch]$Detach,
    [switch]$IdempotentTwice
)

$ErrorActionPreference = "Continue"
$repo = (Resolve-Path "$PSScriptRoot/../..").Path
$maestro = "$PSScriptRoot"
Set-Location $repo
. "$maestro/Lab-MaestroCommon.ps1"

$log = if ($env:MAESTRO_DEEP_LOG) { $env:MAESTRO_DEEP_LOG } else { "/tmp/maestro-deep-5host-gate.log" }

if ($Detach) {
    $session = "maestro-deep-gate"
    $argTail = if ($IdempotentTwice) { "-IdempotentTwice" } else { "" }
    $inner = "cd '$repo' && setsid pwsh -NoProfile -File '$PSCommandPath' $argTail 2>&1 | tee '$log'"
    tmux kill-session -t $session 2>$null
    tmux new-session -d -s $session $inner
    Write-Host "re-Deep detached: tmux attach -t $session" -ForegroundColor Green
    Write-Host "Log: $log"
    exit 0
}

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

function Get-MaestroDeepSummaryRows {
    <#
    #1021 R12.1: flatten Invoke-MaestroDeepGatePass return (never trust nested single-element arrays).
    #>
    param([object]$RawResult)
    if ($null -eq $RawResult) { return @() }
    $flat = [System.Collections.Generic.List[object]]::new()
    foreach ($item in @($RawResult)) {
        if ($null -eq $item) { continue }
        $hasHost = $item.PSObject.Properties.Match("Host").Count -gt 0
        if ($hasHost) {
            [void]$flat.Add($item)
            continue
        }
        if ($item -is [System.Collections.IEnumerable] -and $item -isnot [string]) {
            foreach ($inner in @($item)) {
                if ($null -eq $inner) { continue }
                if ($inner.PSObject.Properties.Match("Host").Count -gt 0) {
                    [void]$flat.Add($inner)
                }
            }
        }
    }
    return @($flat)
}

function Compare-MaestroDeepGateSummaries {
    <#
    #1021 R12: compare pass1 vs pass2 rows by Host key (no pipeline/Format-Table pollution).
    #1021 R12.1: inputs flattened via Get-MaestroDeepSummaryRows.
    #>
    param(
        [object[]]$Pass1,
        [object[]]$Pass2
    )
    $rows1 = Get-MaestroDeepSummaryRows -RawResult $Pass1
    $rows2 = Get-MaestroDeepSummaryRows -RawResult $Pass2
    $mismatch = [System.Collections.Generic.List[string]]::new()
    foreach ($row in $rows1) {
        $key = [string]$row.Host
        $other = @($rows2 | Where-Object { [string]$_.Host -eq $key } | Select-Object -First 1)
        if ($other.Count -eq 0) {
            $mismatch.Add("${key}: missing in pass2")
            continue
        }
        $o = $other[0]
        $line1 = "$key|$($row.Sync)|$($row.Gate)|$($row.Handlers)"
        $line2 = "$key|$($o.Sync)|$($o.Gate)|$($o.Handlers)"
        if ($line1 -ne $line2) {
            $mismatch.Add("pass1=$line1 pass2=$line2")
        }
    }
    foreach ($row in $rows2) {
        $key = [string]$row.Host
        $found = @($rows1 | Where-Object { [string]$_.Host -eq $key })
        if ($found.Count -eq 0) {
            $mismatch.Add("${key}: missing in pass1")
        }
    }
    return [pscustomobject]@{
        Ok       = ($mismatch.Count -eq 0)
        Mismatch = @($mismatch)
        Pass1Count = $rows1.Count
        Pass2Count = $rows2.Count
    }
}

function Invoke-MaestroDeepGatePass {
    param(
        [string]$PassLabel,
        [object[]]$TargetNodes,
        [switch]$SkipPreflight
    )
    $passSummary = @()
    if (-not $SkipPreflight) {
        "=== Pre-flight Build-ContainerArtefact $PassLabel $(Get-Date -Format o) ===" | Tee-Object -FilePath $log -Append
        & "$maestro/Build-ContainerArtefact.ps1" 2>&1 | Tee-Object -FilePath $log -Append
    }

    foreach ($node in $TargetNodes) {
        $name = $node.hostname
        "`n########## DEEP $PassLabel : $name $(Get-Date -Format o) ##########" | Tee-Object -FilePath $log -Append | Out-Null
        if (-not $node) { "SKIP missing node" | Add-Content $log; continue }
        if ($node.ip -match '[^0-9.]') { "SKIP bad IP" | Add-Content $log; continue }
        $octets = ($node.ip -split "\.")[0..2] -join "."
        $node | Add-Member -NotePropertyName lab_op_subnet -NotePropertyValue "$octets.0/24" -Force

        $status = & "$maestro/Get-LabStatus.ps1" -TargetHost $node.hostname -TargetUser $node.user 2>&1
        $status | Tee-Object -FilePath $log -Append
        if ($status.SSH -ne "UP") {
            $passSummary += [pscustomobject]@{ Host = $name; Sync = "-"; Gate = "SSH_DOWN"; Handlers = "-" }
            continue
        }

        Write-Host ">>> Sync $name ($PassLabel)" -ForegroundColor Cyan
        $syncOk = [bool](& "$maestro/Sync-WorkingTree.ps1" -Node $node -Ref WorkingTree)
        "Sync result: $syncOk" | Tee-Object -FilePath $log -Append
        if (-not $syncOk) {
            $passSummary += [pscustomobject]@{ Host = $name; Sync = "FAIL"; Gate = "-"; Handlers = "SKIP" }
            continue
        }

        $isContainer = ($node.personas -contains "docker") -or ($node.personas -contains "podman") -or ($node.personas -contains "dockerswarm")
        if ($isContainer) {
            & "$maestro/Sync-ContainerArtefact.ps1" -Node $node 2>&1 | Tee-Object -FilePath $log -Append
        }

        Write-Host ">>> Gate -Deep $name ($PassLabel)" -ForegroundColor Cyan
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
        $passSummary += [pscustomobject]@{
            Host     = $name
            Sync     = "OK"
            Gate     = if ($gateOk) { "OK" } else { "ALARM" }
            Handlers = $handlersLabel
        }
    }

    "`n=== SUMMARY $PassLabel $(Get-Date -Format o) ===" | Add-Content $log
    $tableOut = $passSummary | Format-Table | Out-String
    $tableOut | Tee-Object -FilePath $log -Append | Out-Null
    Write-Host $tableOut
    # Return flat PSCustomObject rows only — no comma-nested array (R12.1).
    return @($passSummary)
}

$expectedGateHosts = @($targets).Count

Remove-Item $log -ErrorAction SilentlyContinue
$summary = Get-MaestroDeepSummaryRows -RawResult (Invoke-MaestroDeepGatePass -PassLabel "pass1" -TargetNodes $targets)

if ($IdempotentTwice) {
    "`n=== IDEMPOTENCY pass2 $(Get-Date -Format o) ===" | Add-Content $log
    $summary2 = Get-MaestroDeepSummaryRows -RawResult (
        Invoke-MaestroDeepGatePass -PassLabel "pass2" -TargetNodes $targets -SkipPreflight
    )
    $idem = Compare-MaestroDeepGateSummaries -Pass1 $summary -Pass2 $summary2
    "IDEMPOTENCY compare: pass1_rows=$($idem.Pass1Count) pass2_rows=$($idem.Pass2Count) expected=$expectedGateHosts" | Tee-Object -FilePath $log -Append
    if ($idem.Pass1Count -ne $expectedGateHosts -or $idem.Pass2Count -ne $expectedGateHosts) {
        "IDEMPOTENCY: ROW_COUNT_FAIL expected=$expectedGateHosts pass1=$($idem.Pass1Count) pass2=$($idem.Pass2Count)" | Tee-Object -FilePath $log -Append
        Write-Warning "IDEMPOTENCY: row count guard failed — verifier cannot trust match"
        exit 1
    }
    if ($idem.Ok) {
        "IDEMPOTENCY: pass1 and pass2 SUMMARY match" | Tee-Object -FilePath $log -Append
        Write-Host "IDEMPOTENCY: pass1 and pass2 SUMMARY match" -ForegroundColor Green
    } else {
        "IDEMPOTENCY: MISMATCH" | Tee-Object -FilePath $log -Append
        $idem.Mismatch | Tee-Object -FilePath $log -Append
        Write-Warning "IDEMPOTENCY: pass1 vs pass2 mismatch — see log"
        exit 1
    }
}

"`n=== GR LINES ===" | Add-Content $log
Get-Content $log | Select-String -Pattern 'GR host=' | ForEach-Object { $_.Line.Trim() } | Tee-Object -FilePath $log -Append

$totalFails = @(@($summary) | Where-Object { $_.Handlers -like 'FAIL:*' }).Count
if ($IdempotentTwice) {
    $totalFails += @(@($summary2) | Where-Object { $_.Handlers -like 'FAIL:*' }).Count
}
if ($totalFails -gt 0) { exit 1 }
exit 0
