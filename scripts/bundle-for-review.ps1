<#
.NAME
  bundle-for-review.ps1

.SYNOPSIS
  Bundles files from any project or folder into a single Markdown file for agent/reviewer ingest.

.DESCRIPTION
  Creates a single Markdown bundle file intended for upload/ingest when ZIP
  uploads are blocked by the chat or Copilot UI.

  The bundle includes:
    - Inline content for text/code files:
      .ps1, .psm1, .psd1, .md, .txt, .json, .yml, .yaml, .xml, .csv

    - Extracted plain text from .docx files:
      Word documents are OpenXML ZIP packages. This script extracts
      word/document.xml and converts it to readable plain text.

    - Stub entries for unsupported binary files:
      .pdf, .pptx, .png, .jpg, .jpeg, .zip

  The output is deterministic:
    - Files are processed in sorted path order.
    - Each file is clearly delimited with a FILE header.
    - Text/code content is placed inside fenced Markdown code blocks.

  This script does not mutate source files.

.PARAMETER Root
  Root folder containing breadcrumb files.

.PARAMETER OutFile
  Output Markdown bundle path.

.EXAMPLE
  pwsh -ExecutionPolicy Bypass -File .\bundle.ps1

.EXAMPLE
  pwsh -ExecutionPolicy Bypass -File .\bundle.ps1 -Root ".\SteadySentinelBreadCrumbs" -OutFile ".\SteadySentinelBreadCrumbs_BUNDLE.md"

.NOTES
  Authoring context:
    Steady Sentinel recovery / repo reconstruction.

  Important:
    In PowerShell scripts, the param() block must appear before executable
    statements such as Set-StrictMode or variable assignments.
#>

param(
  [string]$Root = ".\BreadCrumbs",
  [string]$OutFile = ".\BreadCrumbs_BUNDLE.md"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Get-MarkdownFenceLanguage {
  param(
    [string]$Extension
  )

  switch ($Extension.ToLowerInvariant()) {
    ".ps1"  { return "powershell" }
    ".psm1" { return "powershell" }
    ".psd1" { return "powershell" }
    ".json" { return "json" }
    ".yml"  { return "yaml" }
    ".yaml" { return "yaml" }
    ".md"   { return "markdown" }
    ".txt"  { return "text" }
    ".xml"  { return "xml" }
    ".csv"  { return "csv" }
    default { return "text" }
  }
}

function Test-TextFile {
  param(
    [string]$Extension
  )

  return $Extension.ToLowerInvariant() -in @(
    ".ps1",
    ".psm1",
    ".psd1",
    ".json",
    ".yml",
    ".yaml",
    ".md",
    ".txt",
    ".xml",
    ".csv"
  )
}

function Test-DocxFile {
  param(
    [string]$Extension
  )

  return $Extension.ToLowerInvariant() -eq ".docx"
}

function Test-UnsupportedBinaryFile {
  param(
    [string]$Extension
  )

  return $Extension.ToLowerInvariant() -in @(
    ".pdf",
    ".pptx",
    ".png",
    ".jpg",
    ".jpeg",
    ".zip"
  )
}

function Convert-DocxToPlainText {
  param(
    [Parameter(Mandatory)]
    [string]$Path
  )

  Add-Type -AssemblyName System.IO.Compression -ErrorAction SilentlyContinue
  Add-Type -AssemblyName System.IO.Compression.FileSystem -ErrorAction SilentlyContinue

  $archive = [System.IO.Compression.ZipFile]::OpenRead($Path)

  try {
    $entry = $archive.Entries |
      Where-Object { $_.FullName -eq "word/document.xml" } |
      Select-Object -First 1

    if ($null -eq $entry) {
      return "[DOCX TEXT EXTRACTION FAILED: word/document.xml not found]"
    }

    $stream = $entry.Open()
    $reader = New-Object System.IO.StreamReader($stream)

    try {
      $xml = $reader.ReadToEnd()
    }
    finally {
      $reader.Close()
      $stream.Close()
    }

    # Preserve paragraph boundaries before stripping tags.
    $xml = $xml -replace "</w:p>", "`n"
    $xml = $xml -replace "</w:tab>", "`t"

    # Strip remaining XML tags.
    $text = $xml -replace "<[^>]+>", ""

    # Decode XML/HTML entities.
    $text = [System.Net.WebUtility]::HtmlDecode($text)

    # Normalize excessive blank lines.
    $text = $text -replace "(`r?`n){3,}", "`n`n"

    return $text.Trim()
  }
  catch {
    return "[DOCX TEXT EXTRACTION FAILED: $($_.Exception.Message)]"
  }
  finally {
    $archive.Dispose()
  }
}

function Write-BundleLine {
  param(
    [Parameter(Mandatory)]
    [System.IO.StreamWriter]$Writer,

    [AllowEmptyString()]
    [string]$Text = ""
  )

  $Writer.WriteLine($Text)
}

# Validate input folder.
if (-not (Test-Path $Root)) {
  throw "Root folder not found: $Root"
}

$rootPath = (Resolve-Path -Path $Root).Path

# Reset output file.
if (Test-Path $OutFile) {
  Remove-Item $OutFile -Force
}

$utf8NoBom = New-Object System.Text.UTF8Encoding($false)
$writer = New-Object System.IO.StreamWriter($OutFile, $false, $utf8NoBom)

try {
  Write-BundleLine -Writer $writer -Text "# Steady Sentinel Breadcrumbs Bundle"
  Write-BundleLine -Writer $writer -Text ""
  Write-BundleLine -Writer $writer -Text ("Generated: " + (Get-Date).ToString("s"))
  Write-BundleLine -Writer $writer -Text ("Source root: " + $rootPath)
  Write-BundleLine -Writer $writer -Text ""
  Write-BundleLine -Writer $writer -Text "> This bundle was generated for Steady Sentinel context reconstruction."
  Write-BundleLine -Writer $writer -Text "> Text/code files are inlined. DOCX files are converted to plain text. Unsupported binaries are listed."
  Write-BundleLine -Writer $writer -Text ""

  $files = Get-ChildItem -Path $rootPath -Recurse -File | Sort-Object FullName

  foreach ($file in $files) {
    $relativePath = $file.FullName.Substring($rootPath.Length).TrimStart("\")
    $extension = $file.Extension

    Write-BundleLine -Writer $writer -Text ""
    Write-BundleLine -Writer $writer -Text "---"
    Write-BundleLine -Writer $writer -Text ("## FILE: " + $relativePath)
    Write-BundleLine -Writer $writer -Text ("- Size: " + $file.Length + " bytes")
    Write-BundleLine -Writer $writer -Text ("- LastWriteTime: " + $file.LastWriteTime.ToString("s"))
    Write-BundleLine -Writer $writer -Text ""

    if (Test-TextFile -Extension $extension) {
      $language = Get-MarkdownFenceLanguage -Extension $extension

      Write-BundleLine -Writer $writer -Text ('```' + $language)

      $content = Get-Content -Path $file.FullName -Raw -ErrorAction Stop
      $writer.WriteLine($content)

      Write-BundleLine -Writer $writer -Text '```'
      continue
    }

    if (Test-DocxFile -Extension $extension) {
      Write-BundleLine -Writer $writer -Text '```text'

      $docxText = Convert-DocxToPlainText -Path $file.FullName
      $writer.WriteLine($docxText)

      Write-BundleLine -Writer $writer -Text '```'
      continue
    }

    if (Test-UnsupportedBinaryFile -Extension $extension) {
      Write-BundleLine -Writer $writer -Text "(BINARY FILE — listed but not inlined)"
      continue
    }

    Write-BundleLine -Writer $writer -Text "(UNRECOGNIZED FILE TYPE — listed but not inlined)"
  }
}
finally {
  $writer.Close()
}

Write-Host ("Created: " + (Resolve-Path $OutFile).Path)