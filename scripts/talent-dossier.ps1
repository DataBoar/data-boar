# Talent dossier shorthand helper (PowerShell)
#
# Goal: make `talent-dossier next --advisor-remote --caution` (alias: `--remote`) available without
# needing to search in docs/scripts every time.
#
# Repo root: defaults to parent of this script's folder; override with
#   -Environment variable DATA_BOAR_REPO_ROOT, or
#   -Flag --repo-root <path> (must appear before subcommand is not required; parsed globally).
#
# This file is meant to be dot-sourced from your PowerShell `$PROFILE`.

function Get-SafeSlug {
    param([Parameter(Mandatory = $true)][string]$Name)
    $normalized = $Name.ToLowerInvariant()
    $normalized = $normalized -replace "[^a-z0-9]+", "-"
    $normalized = $normalized.Trim("-")
    if ([string]::IsNullOrWhiteSpace($normalized)) {
        throw "Could not generate a safe slug from candidate name."
    }
    return $normalized
}

function Get-PendingTeamPdfs {
    param(
        [Parameter(Mandatory = $true)][string]$TeamDir,
        [Parameter(Mandatory = $true)][string]$CandidatesDir
    )

    $pending = @()
    $pdfs = Get-ChildItem -Path $TeamDir -Filter "*.pdf" -File | Sort-Object Name

    foreach ($pdf in $pdfs) {
        $slug = Get-SafeSlug -Name $pdf.BaseName
        $ptPath = Join-Path $CandidatesDir "$slug.pt_BR.md"
        $enPath = Join-Path $CandidatesDir "$slug.md"

        $ptOk = Test-Path -LiteralPath $ptPath
        $enOk = Test-Path -LiteralPath $enPath

        if ($ptOk -and $enOk) {
            continue
        }

        if ($ptOk -or $enOk) {
            $status = "PARTIAL"
        } else {
            $status = "MISSING"
        }

        $pending += [pscustomobject]@{
            PdfPath = $pdf.FullName
            Slug = $slug
            PtPath = $ptPath
            EnPath = $enPath
            Status = $status
        }
    }

    return $pending
}

function Invoke-TalentDossierNext {
    param(
        [Parameter(Mandatory = $true)][string]$RepoRoot,
        [Parameter(Mandatory = $true)][bool]$AdvisorRemote,
        [Parameter(Mandatory = $true)][bool]$Caution,
        [Parameter(Mandatory = $false)][string]$OperatorRelationship = "",
        [Parameter(Mandatory = $true)][bool]$Loop,
        [Parameter(Mandatory = $true)][bool]$DryRun,
        [Parameter(Mandatory = $true)][bool]$Overwrite
    )

    $teamDir = Join-Path $RepoRoot "docs/private/team_info"
    $candDir = Join-Path $RepoRoot "docs/private/commercial/candidates"
    $scaffold = Join-Path $RepoRoot "scripts/candidate-dossier-scaffold.ps1"

    if (-not (Test-Path -LiteralPath $scaffold)) {
        throw "Scaffold script not found: $scaffold"
    }

    $maxIterations = 50
    $iterations = 0

    $generatedAny = $false
    $completed = $false
    do {
        $pending = Get-PendingTeamPdfs -TeamDir $teamDir -CandidatesDir $candDir

        if ($pending.Count -eq 0) {
            Write-Host "talent-dossier: no pending team PDFs."
            $completed = $true
            break
        }

        $next = $pending | Select-Object -First 1
        $iterations++

        Write-Host ("talent-dossier: next => {0} (Status={1})" -f $next.PdfPath, $next.Status)

        if ($DryRun) {
            Write-Host "talent-dossier: dry-run enabled; not generating dossiers."
            return
        }

        $commandArgs = @(
            "-File", $scaffold,
            "-CandidatePdfPath", $next.PdfPath,
            "-OutputDir", $candDir
        )

        if ($AdvisorRemote) {
            $commandArgs += "-AdvisorRemote"
        }
        if ($Caution) {
            $commandArgs += "-LowPriorityCaution"
        }
        if (-not [string]::IsNullOrWhiteSpace($OperatorRelationship)) {
            $commandArgs += "-OperatorRelationship", $OperatorRelationship
        }
        if ($Overwrite) {
            $commandArgs += "-Overwrite"
        }

        & powershell @commandArgs
        $generatedAny = $true

        if (-not $Loop) {
            return
        }
    } while ($iterations -lt $maxIterations)

    if ($generatedAny) {
        Update-PoolSyncSnapshotNow -RepoRoot $RepoRoot
    }

    if ($completed) {
        return
    }

    throw "talent-dossier: reached max iterations ($maxIterations). Stop to avoid runaway execution."
}

function Update-PoolSyncSnapshotNow {
    param(
        [Parameter(Mandatory = $true)]
        [string]$RepoRoot
    )

    $dateStamp = Get-Date -Format "yyyy-MM-dd"
    $outPath = Join-Path (Join-Path $RepoRoot "docs/private/commercial") ("POOL_SYNC_SNAPSHOT_$dateStamp.md")

    # Generate snapshot (and normalize known display mojibake patterns in generator).
    & uv run python "scripts/generate_pool_sync_snapshot.py" --repo-root $RepoRoot --date $dateStamp | Out-Null

    # Post-normalize just in case.
    $normScript = Join-Path $RepoRoot "scripts/normalize_pool_sync_snapshot.ps1"
    if (Test-Path -LiteralPath $normScript) {
        & powershell -NoProfile -ExecutionPolicy Bypass -File $normScript -SnapshotPath $outPath | Out-Null
    }
}

function Get-TalentDossierRepoRoot {
    param([string]$ExplicitRepoRoot)
    if (-not [string]::IsNullOrWhiteSpace($ExplicitRepoRoot)) {
        return (Resolve-Path -LiteralPath $ExplicitRepoRoot).Path
    }
    $envRoot = $env:DATA_BOAR_REPO_ROOT
    if (-not [string]::IsNullOrWhiteSpace($envRoot) -and (Test-Path -LiteralPath $envRoot)) {
        return (Resolve-Path -LiteralPath $envRoot).Path
    }
    # Same directory layout as other repo scripts: scripts/ -> repo root
    $here = $PSScriptRoot
    if ([string]::IsNullOrWhiteSpace($here)) {
        $here = Split-Path -Parent $MyInvocation.MyCommand.Path
    }
    return (Resolve-Path (Join-Path $here "..")).Path
}

function Invoke-TalentDossier {
    [CmdletBinding()]
    param(
        [Parameter(ValueFromRemainingArguments = $true)]
        [string[]]$RemainingArgs
    )

    if ($RemainingArgs.Count -eq 0) {
        $RemainingArgs = @("next")
    }

    $subcommand = $null
    $AdvisorRemote = $false
    $Caution = $false
    $Loop = $true
    $DryRun = $false
    $Overwrite = $false
    $OperatorRelationship = ""
    $ExplicitRepoRoot = ""

    for ($i = 0; $i -lt $RemainingArgs.Count; $i++) {
        $t = $RemainingArgs[$i]

        if (-not $t.StartsWith("--") -and [string]::IsNullOrWhiteSpace($subcommand)) {
            $subcommand = $t
            continue
        }

        switch ($t) {
            "--advisor-remote" { $AdvisorRemote = $true }
            "--remote" { $AdvisorRemote = $true }
            "--caution" { $Caution = $true }
            "--low-priority-caution" { $Caution = $true }
            "--no-loop" { $Loop = $false }
            "--loop" { $Loop = $true }
            "--dry-run" { $DryRun = $true }
            "--overwrite" { $Overwrite = $true }
            "--repo-root" {
                if ($i + 1 -ge $RemainingArgs.Count) {
                    throw "--repo-root expects a path (next token)."
                }
                $ExplicitRepoRoot = $RemainingArgs[$i + 1]
                $i++
            }
            "--operator-relationship" {
                if ($i + 1 -ge $RemainingArgs.Count) {
                    throw "--operator-relationship expects a value (next token)."
                }
                $OperatorRelationship = $RemainingArgs[$i + 1]
                $i++
            }
        }
    }

    $repoRoot = Get-TalentDossierRepoRoot -ExplicitRepoRoot $ExplicitRepoRoot

    if ([string]::IsNullOrWhiteSpace($subcommand)) {
        $subcommand = "next"
    }

    if ($subcommand -eq "next") {
        Invoke-TalentDossierNext -RepoRoot $repoRoot -AdvisorRemote $AdvisorRemote -Caution $Caution -OperatorRelationship $OperatorRelationship -Loop $Loop -DryRun $DryRun -Overwrite $Overwrite
        return
    }

    if ($subcommand -eq "status" -or $subcommand -eq "list") {
        $teamDir = Join-Path $repoRoot "docs/private/team_info"
        $candDir = Join-Path $repoRoot "docs/private/commercial/candidates"
        $pending = Get-PendingTeamPdfs -TeamDir $teamDir -CandidatesDir $candDir
        if ($pending.Count -eq 0) {
            Write-Host "talent-dossier: no pending team PDFs."
            return
        }
        $pending | Select-Object PdfPath, Status | Format-Table -AutoSize
        return
    }

    if ($subcommand -eq "network" -or $subcommand -eq "export-network" -or $subcommand -eq "exportmesh") {
        # Generate Mermaid export from relationship map.
        $generator = Join-Path $repoRoot "scripts\\export_talent_relationship_mermaid.py"
        if (-not (Test-Path -LiteralPath $generator)) {
            throw "Network generator not found: $generator"
        }
        & uv run python $generator
        return
    }

    throw "talent-dossier: unknown subcommand '$subcommand' (supported: next, status, list, network/export-network)."
}

# If someone executes this file directly, forward to the function.
if ($MyInvocation.InvocationName -ne ".") {
    Invoke-TalentDossier @Args
}

# Keep the original shorthand name working.
Set-Alias -Name "talent-dossier" -Value Invoke-TalentDossier -Option AllScope

