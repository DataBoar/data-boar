#Requires -Version 5.1
<#
.SYNOPSIS
    Token-aware rich-media inspect: EXIF / tags + optional OCR (same stack as Data Boar file_scan).

.DESCRIPTION
    Wraps: uv run python scripts/image_inspect.py
    HEIC (iPhone): install richmedia extra (pillow-heif). OCR: pytesseract + system tesseract.
    Video tags: ffprobe on PATH. Audio tags: mutagen when installed.

.PARAMETER Path
    Media file (image, audio, video).

.PARAMETER Ocr
    Run Tesseract on images.

.PARAMETER NoMetadata
    Skip metadata (use with -Ocr for OCR-only on images).

.PARAMETER MaxChars
    Output cap (default 16000).

.PARAMETER OcrLang
    Tesseract language (default eng).

.PARAMETER OcrMaxDimension
    Max dimension for OCR downscale (default 2000).

.EXAMPLE
    .\scripts\image-inspect.ps1 -Path "docs\private\icloud_temp\IMG_1234.HEIC"
    .\scripts\image-inspect.ps1 -Path ".\photo.jpg" -Ocr -OcrLang "por"
    .\scripts\image-inspect.ps1 -Path ".\clip.mov"

.NOTES
    Docs: docs/ops/IMAGE_EXIF_OCR_FOR_AGENT.md
    iCloud fetch: scripts/icloud-photos-fetch-range.ps1
#>
param(
    [string]$Path = "",

    [switch]$Ocr,

    [switch]$NoMetadata,

    [ValidateRange(256, 500000)]
    [int]$MaxChars = 16000,

    [string]$OcrLang = "eng",

    [ValidateRange(256, 8000)]
    [int]$OcrMaxDimension = 2000,

    [switch]$Help
)

$ErrorActionPreference = "Stop"
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location $repoRoot

if ($Help) {
    @"
image-inspect.ps1 - EXIF / media tags + optional OCR (Data Boar rich_media stack)

Usage:
  .\scripts\image-inspect.ps1 -Path <file> [-Ocr] [-NoMetadata] [-MaxChars N] [-OcrLang eng|por] [-OcrMaxDimension PX]

Requires: uv; optional deps per docs/ops/IMAGE_EXIF_OCR_FOR_AGENT.md
"@
    exit 0
}

if ([string]::IsNullOrWhiteSpace($Path)) {
    Write-Host "image-inspect: -Path is required (unless -Help)" -ForegroundColor Red
    exit 2
}

if (-not (Test-Path -LiteralPath $Path)) {
    Write-Host "image-inspect: file not found: $Path" -ForegroundColor Red
    exit 2
}

$full = [string](Resolve-Path -LiteralPath $Path).Path
$uvArgs = @("run", "python", "scripts/image_inspect.py", $full, "--max-chars", "$MaxChars", "--ocr-max-dimension", "$OcrMaxDimension", "--ocr-lang", $OcrLang)
if ($NoMetadata) { $uvArgs += "--no-metadata" }
if ($Ocr) { $uvArgs += "--ocr" }

& uv @uvArgs
exit $LASTEXITCODE
