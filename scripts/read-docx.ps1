#Requires -Version 7.0
<#
.NAME
 scripts/read-docx.ps1

.SYNOPSIS
 Extract plain text from .docx files without Word or pandoc.

.DESCRIPTION
 Unzips word/document.xml, word/footnotes.xml, and word/endnotes.xml from
 each .docx, strips XML tags, and emits a deterministic plain-text dump.
 Helper for ingesting evidence docs, ATS/candidate exports, or engagement
 documents into agent context without requiring Office or pandoc.
 Mirrors scripts/read-eml.ps1 in shape and intent.

.PARAMETER Folder
 Folder to scan for .docx files. Defaults to 'docs/private'.

.PARAMETER Path
 Optional explicit list of .docx files (overrides Folder).

.PARAMETER Exclude
 Filenames to skip.

.EXAMPLE
 .\scripts\read-docx.ps1 -Folder docs/private/commercial/candidates
 .\scripts\read-docx.ps1 -Path docs/private/author_info/profile.docx
#>
[CmdletBinding()]
param(
    [string]$Folder = 'docs\private',
    [string[]]$Path,
    [string[]]$Exclude = @()
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

Add-Type -AssemblyName System.IO.Compression.FileSystem

function Convert-DocxToText {
    [CmdletBinding()]
    param([Parameter(Mandatory)][string]$LiteralPath)

    $zip = [System.IO.Compression.ZipFile]::OpenRead($LiteralPath)
    try {
        $sb = [System.Text.StringBuilder]::new()
        foreach ($entryName in @('word/document.xml', 'word/footnotes.xml', 'word/endnotes.xml')) {
            $entry = $zip.Entries | Where-Object { $_.FullName -eq $entryName } | Select-Object -First 1
            if (-not $entry) { continue }
            $reader = [System.IO.StreamReader]::new($entry.Open())
            try { $xml = $reader.ReadToEnd() } finally { $reader.Dispose() }

            # Paragraph + line breaks -> newlines, tabs -> tab, strip remaining tags.
            $xml = $xml -replace '<w:p[ >][^<]*?(?=<)', "`n"
            $xml = $xml -replace '</w:p>', "`n"
            $xml = $xml -replace '<w:br[^>]*/>', "`n"
            $xml = $xml -replace '<w:tab[^>]*/>', "`t"
            $text = [System.Text.RegularExpressions.Regex]::Replace($xml, '<[^>]+>', '')
            $text = [System.Net.WebUtility]::HtmlDecode($text)
            [void]$sb.AppendLine($text)
        }
        return $sb.ToString()
    } finally {
        $zip.Dispose()
    }
}

if ($Path) {
    $files = $Path | ForEach-Object { Get-Item -LiteralPath $_ }
} else {
    if (-not (Test-Path -LiteralPath $Folder)) {
        Write-Error "Folder not found: $Folder"
        return
    }
    $files = Get-ChildItem -LiteralPath $Folder -Filter *.docx -File -Recurse | Sort-Object Name
}

foreach ($f in $files) {
    if ($Exclude -contains $f.Name) { continue }
    Write-Output ''
    Write-Output ('=' * 64)
    Write-Output ("FILE: " + $f.Name)
    Write-Output ('=' * 64)
    try {
        $text = Convert-DocxToText -LiteralPath $f.FullName
        # Collapse 3+ blank lines to 2 for readability.
        $text = [System.Text.RegularExpressions.Regex]::Replace($text, "(\r?\n){3,}", "`n`n")
        Write-Output $text.TrimEnd()
    } catch {
        Write-Warning ("Failed to read {0}: {1}" -f $f.Name, $_.Exception.Message)
    }
}
