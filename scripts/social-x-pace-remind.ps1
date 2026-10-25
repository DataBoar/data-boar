<#
.SYNOPSIS
  Lists X (Twitter) rows from SOCIAL_HUB.md that are still draft and on or past the editorial date.
  Optionally posts a short reminder to Slack (same incoming webhook pattern as GitHub Actions).

.DESCRIPTION
  Reads docs/private/social_drafts/editorial/SOCIAL_HUB.md (not on public GitHub). For inventory lines where
  the # column matches X1, X2, ... and Rede is X and Estado is draft, compares "Alvo editorial"
  (first YYYY-MM-DD in the cell) to today's date. If due, prints a line and may notify Slack.

  Slack: set SLACK_WEBHOOK_URL in the environment to the same hooks.slack.com URL as GitHub Actions.
  Optional SLACK_MENTION_USER_ID (U...) for a leading mention.

.PARAMETER SocialHubPath
  Override path to SOCIAL_HUB.md (default: repo docs/private/social_drafts/editorial/SOCIAL_HUB.md).

.PARAMETER Slack
  POST a single combined message when at least one row is due and SLACK_WEBHOOK_URL is set.

.PARAMETER WhatIf
  Show what would be sent to Slack without POSTing.

.EXAMPLE
  .\scripts\social-x-pace-remind.ps1
.EXAMPLE
  $env:SLACK_WEBHOOK_URL = 'https://hooks.slack.com/services/...'
  .\scripts\social-x-pace-remind.ps1 -Slack
#>
[CmdletBinding()]
param(
    [string] $SocialHubPath = "",
    [switch] $Slack,
    [switch] $WhatIf
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
if (-not $SocialHubPath) {
    $SocialHubPath = Join-Path $repoRoot "docs\private\social_drafts\editorial\SOCIAL_HUB.md"
}
$hubFile = [System.IO.Path]::GetFullPath($SocialHubPath)

if (-not (Test-Path -LiteralPath $hubFile)) {
    Write-Host "SOCIAL_HUB not found: $hubFile (skip)."
    exit 0
}

$today = [DateTime]::Today
$dueRows = New-Object System.Collections.Generic.List[hashtable]
$lines = Get-Content -LiteralPath $hubFile -Encoding UTF8

foreach ($line in $lines) {
    if ($line -notmatch '^\|') { continue }
    $parts = $line.Trim() -split '\|' | ForEach-Object { $_.Trim() }
    if ($parts.Count -lt 7) { continue }
    $id = $parts[1]
    if ($id -notmatch '^X\d+$') { continue }
    $rede = $parts[2]
    if ($rede -ne "X") { continue }
    $tema = $parts[4]
    $alvoRaw = $parts[5]
    $estado = $parts[6].ToLowerInvariant()
    if ($estado -ne "draft") { continue }

    $m = [regex]::Match($alvoRaw, '(\d{4}-\d{2}-\d{2})')
    if (-not $m.Success) { continue }
    $dueDate = [DateTime]::ParseExact($m.Groups[1].Value, "yyyy-MM-dd", $null)
    if ($dueDate.Date -le $today) {
        $dueRows.Add(@{
            Id         = $id
            Tema       = $tema
            Alvo       = $m.Groups[1].Value
            DraftFile  = $parts[3]
        })
    }
}

if ($dueRows.Count -eq 0) {
    Write-Host "X pace: no draft rows on or past editorial date (OK)."
    exit 0
}

Write-Host "X pace -- due or overdue (draft, alvo <= $($today.ToString('yyyy-MM-dd'))):"
foreach ($r in $dueRows) {
    Write-Host ("  {0}  alvo {1}  {2}  file {3}" -f $r.Id, $r.Alvo, $r.Tema, $r.DraftFile)
}

if (-not $Slack) {
    exit 0
}

$hook = $env:SLACK_WEBHOOK_URL
if (-not $hook -or $hook.Trim().Length -eq 0) {
    Write-Host "Slack: SLACK_WEBHOOK_URL unset; printed lines only."
    exit 0
}

$mention = ""
$mid = $env:SLACK_MENTION_USER_ID
if ($mid -and $mid.Trim() -match '^U[A-Z0-9]+$') {
    $mention = "<@$($mid.Trim())> "
}

$bodyLines = New-Object System.Collections.Generic.List[string]
$bodyLines.Add("${mention}Data Boar -- X social pace: draft row(s) on or past editorial date.")
foreach ($r in $dueRows) {
    $bodyLines.Add("$($r.Id): alvo $($r.Alvo) -- $($r.Tema) (see $($r.DraftFile))")
}
$bodyLines.Add("Hub: docs/private/social_drafts/editorial/SOCIAL_HUB.md")
$text = $bodyLines -join "`n"

$payloadObj = @{ text = $text }
$json = $payloadObj | ConvertTo-Json -Compress

if ($WhatIf) {
    Write-Host "WhatIf: would POST to Slack (${json.Length} chars JSON)."
    exit 0
}

try {
    Invoke-RestMethod -Uri $hook -Method Post -Body $json -ContentType "application/json; charset=utf-8" -TimeoutSec 30 | Out-Null
    Write-Host "Slack: posted."
} catch {
    Write-Error "Slack POST failed: $_"
    exit 1
}
