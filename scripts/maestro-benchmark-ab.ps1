#Requires -Version 7.6.1
<#
.NAME
 scripts/maestro-benchmark-ab.ps1

.SYNOPSIS
 Wrapper Maestro A/B para benchmark opt-in (stable vs candidate) com notas privadas reproduziveis.

.DESCRIPTION
 Executa duas rodadas Maestro -Deep com trilhas separadas (stable/beta), refs distintas e portas web
 distintas para evitar colisao. Opcionalmente roda Maestro -Collect apos cada rodada.
 Gera nota privada em docs/private/homelab/reports com os parametros usados no experimento.
#>

param(
    [string]$LegacyRef = "v1.7.3",
    [string]$CandidateRef = "v1.7.4-rc",
    [ValidateSet("stable", "beta")]
    [string]$LegacyTrack = "stable",
    [ValidateSet("stable", "beta")]
    [string]$CandidateTrack = "beta",
    [int]$LegacyWebPort = 18088,
    [int]$CandidateWebPort = 28088,
    [string]$RunId = "",
    [switch]$BenchCompare,
    [switch]$SkipCollect,
    [string]$ProjectRoot = "",
    [string]$NotesPath = "",
    [int]$SleepBeforeCollect = 120
)

Set-StrictMode -Version 2
$ErrorActionPreference = "Continue"

if ([string]::IsNullOrWhiteSpace($RunId)) {
    $RunId = Get-Date -Format "yyyyMMdd_HHmmss"
}

$repoRoot = if ($ProjectRoot) {
    (Resolve-Path -LiteralPath $ProjectRoot).Path
} else {
    (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..")).Path
}

$maestroPath = Join-Path $repoRoot "scripts\maestro\Maestro.ps1"
if (-not (Test-Path -LiteralPath $maestroPath)) {
    Write-Error "Maestro.ps1 not found: $maestroPath"
    exit 2
}

$privateReportsDir = Join-Path $repoRoot "docs\private\homelab\reports"
if (-not (Test-Path -LiteralPath $privateReportsDir)) {
    New-Item -ItemType Directory -Force -Path $privateReportsDir | Out-Null
}

if ([string]::IsNullOrWhiteSpace($NotesPath)) {
    $NotesPath = Join-Path $privateReportsDir "MAESTRO_BENCHMARK_AB_${RunId}.md"
}

function Invoke-BenchmarkRound {
    param(
        [Parameter(Mandatory = $true)]
        [string]$RoundLabel,
        [Parameter(Mandatory = $true)]
        [string]$Ref,
        [Parameter(Mandatory = $true)]
        [string]$Track,
        [Parameter(Mandatory = $true)]
        [int]$WebPort,
        [Parameter(Mandatory = $true)]
        [string]$RunMarker,
        [Parameter(Mandatory = $true)]
        [bool]$CompareEnabled,
        [Parameter(Mandatory = $true)]
        [bool]$CollectEnabled,
        [Parameter(Mandatory = $true)]
        [string]$MaestroScript,
        [int]$SleepBeforeCollect = 120
    )

    Write-Host ""
    Write-Host ("--- [Maestro Benchmark] Rodada {0}: ref={1} track={2} web_port={3} ---" -f $RoundLabel, $Ref, $Track, $WebPort) -ForegroundColor Cyan
    $start = Get-Date

    $deepArgs = @{
        Ref = $Ref
        Deep = $true
        BenchTrack = $Track
        BenchRunId = $RunMarker
        BenchWebPort = $WebPort
        BenchCompare = $CompareEnabled
    }
    & $MaestroScript @deepArgs | Out-Null
    $deepExit = $LASTEXITCODE
    $endDeep = Get-Date

    $collectExit = $null
    if ($CollectEnabled) {
        if ($SleepBeforeCollect -gt 0) {
            Write-Host ("      [Benchmark] Waiting {0}s for async smoke to finish before Collect..." -f $SleepBeforeCollect) -ForegroundColor DarkGray
            Start-Sleep -Seconds $SleepBeforeCollect
        }
        $collectArgs = @{
            Ref = $Ref
            Collect = $true
            BenchTrack = $Track
            BenchRunId = $RunMarker
            BenchWebPort = $WebPort
            BenchCompare = $CompareEnabled
        }
        & $MaestroScript @collectArgs | Out-Null
        $collectExit = $LASTEXITCODE
    }

    return ,([PSCustomObject]@{
        label = $RoundLabel
        ref = $Ref
        track = $Track
        webPort = $WebPort
        runId = $RunMarker
        startedAt = $start
        endedAt = $endDeep
        deepExit = $deepExit
        collectExit = $collectExit
        elapsedSeconds = [math]::Round((New-TimeSpan -Start $start -End $endDeep).TotalSeconds, 2)
    })
}

$rounds = @(
    @{ Label = "A"; Ref = $LegacyRef; Track = $LegacyTrack; WebPort = $LegacyWebPort },
    @{ Label = "B"; Ref = $CandidateRef; Track = $CandidateTrack; WebPort = $CandidateWebPort }
)

$results = @()
$worstExit = 0

Push-Location -LiteralPath $repoRoot
try {
    foreach ($r in $rounds) {
        $res = Invoke-BenchmarkRound `
            -RoundLabel $r.Label `
            -Ref $r.Ref `
            -Track $r.Track `
            -WebPort $r.WebPort `
            -RunMarker $RunId `
            -CompareEnabled $BenchCompare `
            -CollectEnabled (-not $SkipCollect) `
            -MaestroScript $maestroPath `
            -SleepBeforeCollect $SleepBeforeCollect
        $results += $res

        if ($res.deepExit -gt $worstExit) { $worstExit = $res.deepExit }
        if ($null -ne $res.collectExit -and $res.collectExit -gt $worstExit) { $worstExit = $res.collectExit }
    }
}
finally {
    Pop-Location
}

$nowUtc = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
$noteLines = @(
    "# Maestro Benchmark A/B - $RunId",
    "",
    "- Generated UTC: $nowUtc",
    "- Repo root: $repoRoot",
    "- Inventory source: docs/private/homelab/data/inventory.json",
    "- Same target surfaces: filesystem/network shares/DB personas from inventory + handlers",
    "- Deep mode: enabled in both rounds",
    "- Collect mode after each round: $((-not $SkipCollect).ToString().ToLowerInvariant())",
    "- Bench compare flag: $($BenchCompare.ToString().ToLowerInvariant())",
    "",
    "## Reproducible configs",
    "",
    "| Round | Ref | Track | Web port | Bench run id | Deep exit | Collect exit | Deep elapsed (s) |",
    "| --- | --- | --- | --- | --- | --- | --- | --- |"
)

foreach ($res in $results) {
    $collectTxt = if ($null -eq $res.collectExit) { "n/a" } else { [string]$res.collectExit }
    $noteLines += ("| {0} | {1} | {2} | {3} | {4} | {5} | {6} | {7} |" -f $res.label, $res.ref, $res.track, $res.webPort, $res.runId, $res.deepExit, $collectTxt, $res.elapsedSeconds)
}

$benchCompareFlag = if ($BenchCompare) { "-BenchCompare" } else { "" }
$skipCollectFlag = if ($SkipCollect) { "-SkipCollect" } else { "" }
$cmdLine = ".\scripts\maestro-benchmark-ab.ps1 -LegacyRef `"$LegacyRef`" -CandidateRef `"$CandidateRef`" -LegacyTrack `"$LegacyTrack`" -CandidateTrack `"$CandidateTrack`" -LegacyWebPort $LegacyWebPort -CandidateWebPort $CandidateWebPort -RunId `"$RunId`" $benchCompareFlag $skipCollectFlag"
$cmdLine = ($cmdLine -replace "\s+", " ").Trim()

$noteLines += @(
    "",
    "## Commands",
    "",
    "```powershell",
    $cmdLine,
    "```",
    "",
    "## Notes",
    "",
    "- Handlers received benchmark context via Maestro opt-in parameters (track/run_id/web_port).",
    "- Host smoke emitted isolated artifacts under /tmp/databoar_bench/<track>/metrics when bench-track is set.",
    "- Keep this file private (docs/private)."
)

Set-Content -LiteralPath $NotesPath -Value ($noteLines -join "`r`n") -Encoding utf8
Write-Host ("[Maestro Benchmark] Nota privada salva em: {0}" -f $NotesPath) -ForegroundColor Green

exit $worstExit
