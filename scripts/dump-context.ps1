#!/usr/bin/env pwsh
<#
.SYNOPSIS
  Dumps governance/agent context into one TXT file for external audits.

.DESCRIPTION
  Captures high-signal repository governance surfaces (rules, skills, CI/editor
  config, operational inspirations, wrapper/gate scripts) into a single text
  bundle with deterministic file boundaries and metadata.

  Privacy guardrails:
  - Excludes any path containing a directory segment named "private".
  - Excludes any file whose basename starts with ".env".
#>

param(
    [string]$OutputFile = "data-boar-blackbox-audit.txt"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location $repoRoot

$targetDirs = @(
    ".cursor",
    ".vscode",
    ".github",
    "docs/ops/inspirations",
    "scripts"
)

$targetFiles = @(
    "AGENTS.md",
    ".gitignore",
    "pyproject.toml",
    "uv.lock",
    ".pre-commit-config.yaml",
    "docs/plans/PLANS_TODO.md",
    ".cursor/rules/session-mode-keywords.mdc",
    ".cursor/rules/check-all-gate.mdc",
    "scripts/check-all.ps1",
    "scripts/check-all.sh",
    "scripts/pre-commit-and-tests.ps1",
    "scripts/pre-commit-and-tests.sh"
)

function Test-ExcludedPath {
    param(
        [Parameter(Mandatory = $true)]
        [string]$PathValue
    )

    $normalized = $PathValue -replace "\\", "/"
    $segments = $normalized.Split("/")
    if ($segments -contains "private") {
        return $true
    }

    $baseName = [System.IO.Path]::GetFileName($normalized)
    if ($baseName -like ".env*") {
        return $true
    }

    return $false
}

function New-OrderedFileList {
    $files = [System.Collections.Generic.HashSet[string]]::new(
        [System.StringComparer]::OrdinalIgnoreCase
    )

    foreach ($f in $targetFiles) {
        if ((Test-Path -LiteralPath $f) -and -not (Test-ExcludedPath -PathValue $f)) {
            [void]$files.Add(($f -replace "\\", "/"))
        }
    }

    foreach ($dir in $targetDirs) {
        if (-not (Test-Path -LiteralPath $dir)) {
            continue
        }

        $tracked = & git ls-files -- $dir 2>$null
        foreach ($path in $tracked) {
            if ([string]::IsNullOrWhiteSpace($path)) {
                continue
            }
            $normalized = $path -replace "\\", "/"
            if (Test-ExcludedPath -PathValue $normalized) {
                continue
            }
            if (Test-Path -LiteralPath $normalized) {
                [void]$files.Add($normalized)
            }
        }
    }

    return @($files | Sort-Object)
}

function Write-FileBlock {
    param(
        [Parameter(Mandatory = $true)]
        [System.IO.StreamWriter]$Writer,
        [Parameter(Mandatory = $true)]
        [string]$RelativePath
    )

    if (Test-ExcludedPath -PathValue $RelativePath) {
        return
    }

    if (-not (Test-Path -LiteralPath $RelativePath)) {
        return
    }

    $item = Get-Item -LiteralPath $RelativePath -ErrorAction Stop
    if ($item.PSIsContainer) {
        return
    }

    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $mode = $item.Mode
    $size = $item.Length

    $Writer.WriteLine("")
    $Writer.WriteLine("#### START_FILE: $RelativePath ####")
    $Writer.WriteLine("TIMESTAMP: $timestamp")
    $Writer.WriteLine("PERMISSIONS: $mode")
    $Writer.WriteLine("SIZE_BYTES: $size")
    $Writer.WriteLine("-----------------------------------------------------------")
    try {
        $content = Get-Content -LiteralPath $RelativePath -Raw -ErrorAction Stop
        if ($null -ne $content) {
            $Writer.WriteLine($content)
        }
    } catch {
        $Writer.WriteLine("[UNREADABLE_OR_BINARY] $($_.Exception.Message)")
    }
    $Writer.WriteLine("#### END_FILE: $RelativePath ####")
}

$outputPath = Join-Path $repoRoot $OutputFile
$encoding = [System.Text.UTF8Encoding]::new($false)
$writer = [System.IO.StreamWriter]::new($outputPath, $false, $encoding)

try {
    $now = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $branch = (& git rev-parse --abbrev-ref HEAD 2>$null)
    $headSha = (& git rev-parse HEAD 2>$null)

    $writer.WriteLine("===========================================================")
    $writer.WriteLine("DATA BOAR - AGENT AUDIT DUMP - $now")
    $writer.WriteLine("Scope: Rules, Skills, Rituals, Taxonomy and Gates")
    $writer.WriteLine("BRANCH: $branch")
    $writer.WriteLine("HEAD: $headSha")
    $writer.WriteLine("PRIVACY_GUARD: skip */private/* and .env*")
    $writer.WriteLine("===========================================================")

    $allFiles = New-OrderedFileList
    foreach ($relativePath in $allFiles) {
        Write-FileBlock -Writer $writer -RelativePath $relativePath
    }
} finally {
    $writer.Dispose()
}

if (Test-Path -LiteralPath "check-all.log") {
    Add-Content -LiteralPath $outputPath -Value ""
    Add-Content -LiteralPath $outputPath -Value "#### TELEMETRY: check-all.log (Tail 100) ####"
    Get-Content -LiteralPath "check-all.log" -Tail 100 | Add-Content -LiteralPath $outputPath
}

Write-Host "Dump concluido: $outputPath" -ForegroundColor Green
