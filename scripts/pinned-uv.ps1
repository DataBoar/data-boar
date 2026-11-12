#!/usr/bin/env pwsh
#requires -Version 7.0
<#
.SYNOPSIS
  Print the directory of the uv pinned in .github/uv-version (#2232). PowerShell twin of
  scripts/pinned-uv.sh: keep the two in sync (docs/ops/SCRIPTS_CROSS_PLATFORM_PAIRING.md).

.DESCRIPTION
  stdout: ONE line, the directory that holds the pinned uv (prepend it to PATH).
  stderr: progress and errors. Exit 0 only when that exact uv version is available.

  Cache (outside the repo, global PATH untouched):
    $DATA_BOAR_UV_CACHE_DIR, else $XDG_CACHE_HOME/data-boar, else %LOCALAPPDATA%\data-boar
    (Windows) or ~/.cache/data-boar, then uv-<version>/uv[.exe]

  Resolution order (every step needs `uv --version` to print EXACTLY the pinned version):
    1. the cached binary;
    2. a uv already on PATH (any platform; it is linked/copied into the cache dir, not hashed);
    3. otherwise the official astral-sh/uv release asset of THIS platform is downloaded and its
       SHA256 is checked against the digest registered in tests/test_uv_version_single_source.py
       (KNOWN_ASSET_SHA256, one entry per <version>/<asset>, from the official release).
       No digest, no download.
  There is no skip and no fallback to another version: failure is a hard error. The script is
  idempotent: a second run finds the cache and downloads nothing.

  Test seams (same names as the .sh twin): PINNED_UV_BASE_URL replaces
  https://github.com/astral-sh/uv/releases/download (the digest check still applies; file:// works);
  PINNED_UV_UNAME overrides "<os>-<arch>" (e.g. Darwin-arm64, Windows-x86_64).
#>
[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Write-Err([string]$Message) { [Console]::Error.WriteLine($Message) }
function Fail([string]$Message) {
    Write-Err "pinned-uv.ps1: ERROR: $Message"
    exit 1
}

$root = (Get-Item $PSScriptRoot).Parent.FullName
$versionFile = Join-Path $root '.github/uv-version'
$guardTest = Join-Path $root 'tests/test_uv_version_single_source.py'
$baseUrl = if ($env:PINNED_UV_BASE_URL) { $env:PINNED_UV_BASE_URL } else { 'https://github.com/astral-sh/uv/releases/download' }

if (-not (Test-Path -LiteralPath $versionFile)) { Fail "$versionFile not found" }
$version = (Get-Content -LiteralPath $versionFile -Raw) -replace '\s', ''
if ($version -notmatch '^\d+\.\d+\.\d+$') {
    Fail "$versionFile must hold only a version like 0.11.2, got '$version'"
}

$homeDir = if ($env:HOME) { $env:HOME } else { $env:USERPROFILE }
if ($env:DATA_BOAR_UV_CACHE_DIR) { $cacheRoot = $env:DATA_BOAR_UV_CACHE_DIR }
elseif ($env:XDG_CACHE_HOME) { $cacheRoot = Join-Path $env:XDG_CACHE_HOME 'data-boar' }
elseif ($IsWindows -and $env:LOCALAPPDATA) { $cacheRoot = Join-Path $env:LOCALAPPDATA 'data-boar' }
else { $cacheRoot = Join-Path $homeDir '.cache' 'data-boar' }

$exeName = if ($IsWindows) { 'uv.exe' } else { 'uv' }
$destDir = Join-Path $cacheRoot "uv-$version"
$destBin = Join-Path $destDir $exeName

function Get-ReportedVersion([string]$Path) {
    try { $line = & $Path --version 2>$null | Select-Object -First 1 } catch { return $null }
    if (-not $line) { return $null }
    $parts = "$line" -split '\s+'
    if ($parts.Count -ge 2) { return $parts[1] }
    return $null
}

function Write-ResultAndExit([string]$Dir) {
    # Success pipeline (not [Console]::Out): `$d = & pinned-uv.ps1` in check-all.ps1 must capture it;
    # with -File the same line still lands on stdout.
    Write-Output $Dir
    exit 0
}

# 1. cached binary
if ((Test-Path -LiteralPath $destBin) -and ((Get-ReportedVersion $destBin) -eq $version)) {
    Write-Err "pinned-uv.ps1: using cached uv $version ($destBin)"
    Write-ResultAndExit $destDir
}

# 2. any platform: a uv of EXACTLY the pinned version already on PATH is enough. We do not hash an
#    install the developer made themselves; the digest registry only guards what we download.
$pathCmd = Get-Command uv -CommandType Application -ErrorAction SilentlyContinue | Select-Object -First 1
if ($pathCmd) {
    $pathUv = $pathCmd.Source
    if ((Get-ReportedVersion $pathUv) -eq $version) {
        New-Item -ItemType Directory -Force -Path $destDir | Out-Null
        # Concurrent runs (one check-all per worktree): build the link/copy under a name unique to
        # this process, then ONE rename over the destination (remove + create is not atomic).
        $linkTmp = Join-Path $destDir ".uv.link.$([guid]::NewGuid().ToString('N').Substring(0, 8))"
        if ($IsWindows) {
            Copy-Item -LiteralPath $pathUv -Destination $linkTmp -Force
        }
        else {
            New-Item -ItemType SymbolicLink -Path $linkTmp -Target $pathUv | Out-Null
        }
        # File.Move(.., $true) is an atomic replace (rename / MoveFileEx); Move-Item -Force removes
        # the destination first and loses the race against another process ("already exists").
        [System.IO.File]::Move($linkTmp, $destBin, $true)
        Write-Err "pinned-uv.ps1: using uv $version found on PATH ($pathUv)"
        Write-ResultAndExit $destDir
    }
}

# 3. download, verify, install
function Get-PlatformTag {
    if ($env:PINNED_UV_UNAME) { return $env:PINNED_UV_UNAME }
    $os = if ($IsWindows) { 'Windows' } elseif ($IsMacOS) { 'Darwin' } elseif ($IsLinux) { 'Linux' } else { 'Unknown' }
    $arch = switch ([System.Runtime.InteropServices.RuntimeInformation]::OSArchitecture) {
        'X64' { 'x86_64' }
        'Arm64' { 'aarch64' }
        default { "$_" }
    }
    return "$os-$arch"
}

$platform = Get-PlatformTag
$asset = switch ($platform) {
    'Linux-x86_64' { 'uv-x86_64-unknown-linux-gnu.tar.gz' }
    { $_ -in 'Linux-aarch64', 'Linux-arm64' } { 'uv-aarch64-unknown-linux-gnu.tar.gz' }
    'Darwin-x86_64' { 'uv-x86_64-apple-darwin.tar.gz' }
    { $_ -in 'Darwin-arm64', 'Darwin-aarch64' } { 'uv-aarch64-apple-darwin.tar.gz' }
    { $_ -in 'Windows-x86_64', 'Windows-amd64' } { 'uv-x86_64-pc-windows-msvc.zip' }
    { $_ -in 'Windows-aarch64', 'Windows-arm64' } { 'uv-aarch64-pc-windows-msvc.zip' }
    default { $null }
}
if (-not $asset) {
    Fail "no uv $version in the cache ($destBin) or on PATH, and this script downloads only for Linux, macOS and Windows on x86_64/aarch64 (this platform: $platform). Install uv $version so that 'uv --version' reports exactly $version and keep it on PATH (this script finds it there), or place it at $destBin"
}

if (-not (Test-Path -LiteralPath $guardTest)) { Fail "$guardTest not found (digest registry)" }
$pattern = '"' + [regex]::Escape("$version/$asset") + '":\s*"([0-9a-f]{64})"'
$match = [regex]::Match((Get-Content -LiteralPath $guardTest -Raw), $pattern)
if (-not $match.Success) {
    Fail "no official SHA256 registered for uv $version / $asset in $guardTest (KNOWN_ASSET_SHA256); refusing to download an unverified binary"
}
$expectedSha = $match.Groups[1].Value

New-Item -ItemType Directory -Force -Path $cacheRoot | Out-Null
$tmp = Join-Path $cacheRoot ".fetch-$([guid]::NewGuid().ToString('N').Substring(0, 8))"
New-Item -ItemType Directory -Force -Path $tmp | Out-Null
try {
    $archive = Join-Path $tmp $asset
    $url = "$baseUrl/$version/$asset"
    Write-Err "pinned-uv.ps1: downloading uv $version from $url"
    try {
        if ($url -like 'file://*') {
            Copy-Item -LiteralPath ([System.Uri]::new($url).LocalPath) -Destination $archive -Force
        }
        else {
            Invoke-WebRequest -Uri $url -OutFile $archive -MaximumRetryCount 3 -RetryIntervalSec 2 -TimeoutSec 300 | Out-Null
        }
    }
    catch {
        Fail "download of uv $version failed ($url): $($_.Exception.Message)"
    }

    $actualSha = (Get-FileHash -Algorithm SHA256 -LiteralPath $archive).Hash.ToLowerInvariant()
    if ($actualSha -ne $expectedSha) {
        Fail "SHA256 mismatch for uv $version ($asset): expected $expectedSha, got $actualSha"
    }

    $extract = Join-Path $tmp 'x'
    New-Item -ItemType Directory -Force -Path $extract | Out-Null
    if ($asset.EndsWith('.zip')) {
        Expand-Archive -LiteralPath $archive -DestinationPath $extract -Force
    }
    else {
        & tar -xzf $archive -C $extract
        if ($LASTEXITCODE -ne 0) { Fail 'cannot extract the uv tarball' }
    }
    $found = Get-ChildItem -LiteralPath $extract -Recurse -File | Where-Object { $_.Name -eq $exeName } | Select-Object -First 1
    if (-not $found) { Fail "archive has no $exeName" }

    New-Item -ItemType Directory -Force -Path $destDir | Out-Null
    # Prepared inside this process's private $tmp (same filesystem as the cache) and moved with ONE
    # rename: concurrent runs never share a temp file (review of #2233; twin of pinned-uv.sh).
    $newBin = Join-Path $tmp "$exeName.ready"
    Copy-Item -LiteralPath $found.FullName -Destination $newBin -Force
    if (-not $IsWindows) { & chmod 755 $newBin }
    [System.IO.File]::Move($newBin, $destBin, $true) # atomic replace, see the PATH branch above
}
finally {
    Remove-Item -LiteralPath $tmp -Recurse -Force -ErrorAction SilentlyContinue
}

$reported = Get-ReportedVersion $destBin
if ($reported -ne $version) { Fail "installed uv reports '$reported', expected $version" }
Write-Err "pinned-uv.ps1: installed uv $version in $destDir (SHA256 verified)"
Write-ResultAndExit $destDir
