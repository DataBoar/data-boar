#Requires -Version 5.1
<#
.SYNOPSIS
  Restores the gitignored inbox docs/feedbacks, reviews, comments and criticism/ from docs/private mirrors.
.DESCRIPTION
  Additive-only: copies bundles, sobre-data-boar*.md, and (optionally) full mess_concat tree.
  Never removes existing inbox content; previous full-tree copy is renamed with __preserved_<timestamp> before refresh.
  Resolve repo root by walking up to .git (works from docs/private or docs/private.example/feedbacks-inbox).
#>
$ErrorActionPreference = "Stop"

function Get-ProductRepoRootFromScript {
  param([string]$StartDir)
  $d = $StartDir
  while ($d) {
    $gitDir = Join-Path $d ".git"
    if (Test-Path -LiteralPath $gitDir) {
      $norm = $d -replace "\\", "/"
      if ($norm -notmatch "/docs/private$") {
        return $d
      }
    }
    $parent = Split-Path $d -Parent
    if ($parent -eq $d) { break }
    $d = $parent
  }
  throw "Could not find product repository root (.git) walking up from $StartDir (skip nested docs/private/.git)"
}

$root = Get-ProductRepoRootFromScript -StartDir $PSScriptRoot
$inbox = Join-Path $root "docs\feedbacks, reviews, comments and criticism"
$gb = Join-Path $root "docs\private\gemini_bundles"
$archRoot = Join-Path $root "docs\private\feedback_inbox_archive"
$archGb = Join-Path $archRoot "gemini_bundles"
$archMess = Join-Path $archRoot "mess_concatenated_gemini_sanity_check"
$messRoot = Join-Path $root "docs\private\mess_concatenated_gemini_sanity_check"

New-Item -ItemType Directory -Force -Path $inbox | Out-Null
$log = Join-Path $inbox "RESTORE_LOG.txt"
$stamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
Add-Content -Path $log -Value "=== FEEDBACK_INBOX_RESTORE $stamp ==="
Add-Content -Path $log -Value "root=$root"

function Copy-TxtToInbox {
  param([string]$SourceDir, [string]$Label)
  if (-not (Test-Path -LiteralPath $SourceDir)) {
    Add-Content -Path $log -Value "SKIP: $Label not found at $SourceDir"
    return
  }
  Get-ChildItem -LiteralPath $SourceDir -Filter "*.txt" -File -ErrorAction SilentlyContinue | ForEach-Object {
    $dest = Join-Path $inbox ("ARCHIVE_{0}__{1}" -f $Label, $_.Name)
    Copy-Item -LiteralPath $_.FullName -Destination $dest -Force
    Add-Content -Path $log -Value ("OK copy: " + $Label + "/" + $_.Name + " -> " + (Split-Path $dest -Leaf))
  }
}

function Copy-MdToInbox {
  param([string]$SourceDir, [string]$Label)
  if (-not (Test-Path -LiteralPath $SourceDir)) {
    Add-Content -Path $log -Value "SKIP: $Label not found at $SourceDir"
    return
  }
  Get-ChildItem -LiteralPath $SourceDir -Filter "sobre-data-boar*.md" -File -ErrorAction SilentlyContinue | ForEach-Object {
    $dest = Join-Path $inbox ("ARCHIVE_{0}__{1}" -f $Label, $_.Name)
    Copy-Item -LiteralPath $_.FullName -Destination $dest -Force
    Add-Content -Path $log -Value ("OK copy: " + $Label + "/" + $_.Name + " -> " + (Split-Path $dest -Leaf))
  }
}

Copy-TxtToInbox -SourceDir $gb -Label "gemini_bundles"
if (-not (Test-Path -LiteralPath $gb) -or ((Get-ChildItem -LiteralPath $gb -Filter "*.txt" -File -ErrorAction SilentlyContinue | Measure-Object).Count -eq 0)) {
  Copy-TxtToInbox -SourceDir $archGb -Label "feedback_inbox_archive_gemini_bundles"
}
Copy-MdToInbox -SourceDir $messRoot -Label "mess_concat_root"
Copy-MdToInbox -SourceDir $archMess -Label "archive_mess_concat"

# Full tree: preserve any existing copy (no Remove-Item on operator data)
$destFull = Join-Path $inbox "ARCHIVE_full_mess_concatenated_gemini_sanity_check"
if (Test-Path -LiteralPath $messRoot) {
  if (Test-Path -LiteralPath $destFull) {
    $suffix = Get-Date -Format "yyyyMMdd_HHmmss"
    $preservedName = "ARCHIVE_full_mess_concatenated_gemini_sanity_check__preserved_$suffix"
    Rename-Item -LiteralPath $destFull -NewName $preservedName -ErrorAction Stop
    Add-Content -Path $log -Value "OK preserve prior copy: -> $preservedName"
  }
  New-Item -ItemType Directory -Force -Path $destFull | Out-Null
  robocopy $messRoot $destFull /E /NFL /NDL /NJH /NJS /nc /ns /np | Out-Null
  $rc = $LASTEXITCODE
  if ($rc -ge 8) {
    Add-Content -Path $log -Value "WARN robocopy exit $rc for full mess_concat"
  }
  else {
    Add-Content -Path $log -Value "OK full tree: mess_concatenated_gemini_sanity_check -> ARCHIVE_full_mess_concatenated_gemini_sanity_check"
  }
}
else {
  Add-Content -Path $log -Value "SKIP: full mess_concat not at $messRoot"
}

if (Test-Path -LiteralPath (Join-Path $archRoot "README.md")) {
  Copy-Item -LiteralPath (Join-Path $archRoot "README.md") -Destination (Join-Path $inbox "ARCHIVE_README_feedback_inbox_archive.md") -Force
  Add-Content -Path $log -Value "OK copy: feedback_inbox_archive/README.md -> ARCHIVE_README_feedback_inbox_archive.md"
}

Add-Content -Path $log -Value "Done."
Write-Host "Inbox: $inbox"
Write-Host "Log: $log"
