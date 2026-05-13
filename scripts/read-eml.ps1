#Requires -Version 7.0
<#
.NAME
 scripts/read-eml.ps1

.SYNOPSIS
 Extract plain text from .eml files (RFC 2822 email exports).

.DESCRIPTION
 Parses base64 and quoted-printable text/plain parts from .eml files.
 Helper for reading email evidence exports (e.g. corporate email PDFs,
 feedback threads, legal correspondence) without a mail client.
 Mirrors scripts/read-docx.ps1 in shape and intent.

.PARAMETER Folder
 Folder to scan for .eml files. Defaults to 'docs\private'.

.PARAMETER Exclude
 Filenames to skip.

.EXAMPLE
 .\scripts\read-eml.ps1 -Folder docs\private\legal_dossier
 .\scripts\read-eml.ps1 -Folder "docs\feedbacks, reviews, comments and criticism"
#>
[CmdletBinding()]
param(
    [string]$Folder = 'docs\private',
    [string[]]$Exclude = @()
)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Get-EmlPlainText {
    param([string]$Path)
    $raw = Get-Content -LiteralPath $Path -Raw
    $out = New-Object System.Collections.Generic.List[string]

    # base64-encoded text/plain parts
    $pat1 = '(?s)Content-Type:\s*text/plain[^\r\n]*\r?\nContent-Transfer-Encoding:\s*base64\r?\n\r?\n(.*?)\r?\n--'
    foreach ($m in [regex]::Matches($raw, $pat1)) {
        $b64 = ($m.Groups[1].Value -replace '\s', '')
        try {
            $bytes = [Convert]::FromBase64String($b64)
            [void]$out.Add([System.Text.Encoding]::UTF8.GetString($bytes))
        } catch {}
    }

    # quoted-printable text/plain parts
    $pat2 = '(?s)Content-Type:\s*text/plain[^\r\n]*\r?\nContent-Transfer-Encoding:\s*quoted-printable\r?\n\r?\n(.*?)\r?\n--'
    foreach ($m in [regex]::Matches($raw, $pat2)) {
        $qp = $m.Groups[1].Value -replace '=\r?\n', ''
        $qp = [regex]::Replace($qp, '=([0-9A-Fa-f]{2})', { param($x) [char][Convert]::ToInt32($x.Groups[1].Value, 16) })
        [void]$out.Add($qp)
    }

    if ($out.Count -eq 0) { return "<no plaintext part found>" }
    return ($out -join "`n----- next part -----`n")
}

if (-not (Test-Path -LiteralPath $Folder)) {
    Write-Error "Folder not found: $Folder"
    return
}

$files = Get-ChildItem -LiteralPath $Folder -Filter *.eml -File -Recurse | Sort-Object Name
foreach ($f in $files) {
    if ($Exclude -contains $f.Name) { continue }
    Write-Host ""
    Write-Host ("=" * 64)
    Write-Host ("FILE: " + $f.Name)
    Write-Host ("=" * 64)
    $text = Get-EmlPlainText -Path $f.FullName
    # Strip common confidentiality boilerplate
    $text = $text -replace '(?s)THE INFORMATION CONTAINED IN THIS MESSAGE.*', ''
    $text = $text -replace '(?s)CONFIDENTIALITY NOTICE:.*', ''
    Write-Host $text
}
