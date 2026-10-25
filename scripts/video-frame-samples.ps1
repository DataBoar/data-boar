#!/usr/bin/env pwsh
# Extract still frames from video for assistant context (ffmpeg). Token-aware: capped width, named outputs.
#
# Usage:
#   .\scripts\video-frame-samples.ps1 -MediaPath "C:\path\clip.mp4" -Timestamp 3 -Timestamp 12.5
#   .\scripts\video-frame-samples.ps1 -MediaPath ".\clip.mp4" -TimestampsCsv "0,3,10"
#
# Docs: docs/ops/VIDEO_FRAME_EXTRACT_FOR_AGENT.md

param(
    [string]$MediaPath = "",

    [double[]]$Timestamp = @(),

    [string]$TimestampsCsv = "",

    [string]$OutputDir = "",

    [ValidateRange(0, 7680)]
    [int]$MaxWidth = 0,

    [switch]$ProbeOnly,

    [switch]$Help
)

$ErrorActionPreference = "Stop"

if ($Help) {
    @"
video-frame-samples.ps1 - extract PNG frames from video (ffmpeg) for agent context

Usage:
  .\scripts\video-frame-samples.ps1 -MediaPath <file> [-Timestamp <sec> ...] [-TimestampsCsv "1,3,10"]
  [-OutputDir <dir>] [-MaxWidth <px>] [-ProbeOnly]

-TimestampsCsv   Comma-separated seconds (optional; merges with -Timestamp).
-MaxWidth        If > 0, scales frame so width <= MaxWidth (height keeps aspect).
-ProbeOnly       Print duration (ffprobe) and exit 0.

Requires: ffmpeg and ffprobe on PATH (e.g. winget install ffmpeg).

Docs: docs/ops/VIDEO_FRAME_EXTRACT_FOR_AGENT.md
"@
    exit 0
}

if ([string]::IsNullOrWhiteSpace($MediaPath)) {
    Write-Host "video-frame-samples: -MediaPath is required (unless -Help)" -ForegroundColor Red
    exit 2
}

function Resolve-FfmpegExe {
    $cmd = Get-Command "ffmpeg" -ErrorAction SilentlyContinue
    if ($cmd -and (Test-Path -LiteralPath $cmd.Source)) {
        return [string]$cmd.Source
    }
    $winget = Join-Path $env:LOCALAPPDATA "Microsoft\WinGet\Links\ffmpeg.exe"
    if (Test-Path -LiteralPath $winget) {
        return [string](Resolve-Path -LiteralPath $winget).Path
    }
    return $null
}

function Resolve-FfprobeExe {
    $cmd = Get-Command "ffprobe" -ErrorAction SilentlyContinue
    if ($cmd -and (Test-Path -LiteralPath $cmd.Source)) {
        return [string]$cmd.Source
    }
    $winget = Join-Path $env:LOCALAPPDATA "Microsoft\WinGet\Links\ffprobe.exe"
    if (Test-Path -LiteralPath $winget) {
        return [string](Resolve-Path -LiteralPath $winget).Path
    }
    return $null
}

$ffmpeg = Resolve-FfmpegExe
$ffprobe = Resolve-FfprobeExe
if (-not $ffmpeg -or -not $ffprobe) {
    Write-Host "video-frame-samples: ffmpeg/ffprobe not found. Install: winget install ffmpeg" -ForegroundColor Red
    exit 3
}

if (-not (Test-Path -LiteralPath $MediaPath)) {
    Write-Host "video-frame-samples: media not found: $MediaPath" -ForegroundColor Red
    exit 2
}

$mediaFull = [string](Resolve-Path -LiteralPath $MediaPath).Path

$durStr = & $ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 -i $mediaFull 2>&1
$durLine = ([string]$durStr).Trim() -split "`r?`n" | Where-Object { $_.Trim().Length -gt 0 } | Select-Object -First 1
$duration = 0.0
if (-not [double]::TryParse([string]$durLine, [ref]$duration)) {
    Write-Host "video-frame-samples: ffprobe could not read duration" -ForegroundColor Red
    exit 3
}

if ($ProbeOnly) {
    Write-Host "duration_sec=$duration"
    Write-Host "media=$mediaFull"
    exit 0
}

$times = New-Object System.Collections.Generic.List[double]
foreach ($t in $Timestamp) {
    $times.Add([double]$t)
}
if ($TimestampsCsv.Trim().Length -gt 0) {
    foreach ($piece in $TimestampsCsv.Split(",")) {
        $p = $piece.Trim()
        if ($p.Length -eq 0) { continue }
        $val = 0.0
        if (-not [double]::TryParse($p, [ref]$val)) {
            Write-Host "video-frame-samples: invalid timestamp in -TimestampsCsv: $p" -ForegroundColor Red
            exit 4
        }
        $times.Add($val)
    }
}

if ($times.Count -eq 0) {
    Write-Host "video-frame-samples: pass -Timestamp and/or -TimestampsCsv" -ForegroundColor Red
    exit 4
}

$uniqueSorted = $times | Sort-Object -Unique
$outParent = $OutputDir.Trim()
if ($outParent.Length -eq 0) {
    $stamp = Get-Date -Format "yyyyMMdd-HHmmss"
    $outParent = Join-Path ([System.IO.Path]::GetTempPath()) ("video-frames-" + $stamp)
}
if (-not (Test-Path -LiteralPath $outParent)) {
    New-Item -ItemType Directory -Path $outParent -Force | Out-Null
}
$outParentFull = [string](Resolve-Path -LiteralPath $outParent).Path

$i = 0
$written = New-Object System.Collections.Generic.List[string]
foreach ($t in $uniqueSorted) {
    if ($t -lt 0) {
        Write-Host "video-frame-samples: skip negative timestamp: $t" -ForegroundColor Yellow
        continue
    }
    $seek = $t
    if ($duration -gt 0 -and $t -gt $duration) {
        Write-Host "video-frame-samples: clamp $t to duration $duration" -ForegroundColor Yellow
        $seek = $duration
    }
    $i++
    $safe = ([string]$seek) -replace "\.", "_"
    $outFile = Join-Path $outParentFull ("frame-{0:d3}-{1}s.png" -f $i, $safe)

    $vfArg = $null
    if ($MaxWidth -gt 0) {
        $w = $MaxWidth
        $vfArg = "scale='min(iw,$w)':-2"
    }
    $ffmpegArgs = @("-hide_banner", "-loglevel", "error", "-y", "-ss", ([string]$seek), "-i", $mediaFull, "-vframes", "1")
    if ($vfArg) {
        $ffmpegArgs += @("-vf", $vfArg)
    }
    $ffmpegArgs += $outFile

    & $ffmpeg @ffmpegArgs
    if ($LASTEXITCODE -ne 0) {
        Write-Host "video-frame-samples: ffmpeg failed at ${seek}s exit=$LASTEXITCODE" -ForegroundColor Red
        exit 3
    }
    if (Test-Path -LiteralPath $outFile) {
        $written.Add([string](Resolve-Path -LiteralPath $outFile).Path)
    }
}

Write-Host "video-frame-samples: OK"
Write-Host "duration_sec=$duration"
Write-Host "output_dir=$outParentFull"
foreach ($w in $written) {
    Write-Host $w
}

exit 0
