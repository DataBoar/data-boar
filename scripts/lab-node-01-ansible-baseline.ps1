param(
  [Parameter(Mandatory = $false)]
  [string]$SshHost = "lab-node-01",

  [Parameter(Mandatory = $false)]
  [string]$RepoPath = "~/Projects/dev/data-boar",

  [Parameter(Mandatory = $false)]
  [switch]$Apply,

  [Parameter(Mandatory = $false)]
  [switch]$SkipCheck,

  # Omit when sudo is NOPASSWD for this user (no BECOME password prompt).
  [Parameter(Mandatory = $false)]
  [switch]$NoAskBecomePass,

  # Run only playbooks/lab-node-01-podman.yml (Podman + rootless deps) instead of the full baseline.
  [Parameter(Mandatory = $false)]
  [switch]$PodmanOnly
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function ConvertTo-UnixLf {
  param([string]$Text)
  if ([string]::IsNullOrEmpty($Text)) { return $Text }
  return ($Text -replace "`r`n", "`n" -replace "`r", "`n").TrimEnd()
}

# Bash does not expand ~ inside double quotes. Remote `cd "~/foo"` fails; use $HOME instead.
function Get-BashCdPath {
  param([string]$RepoOrPath)
  if ($RepoOrPath -match '^\~/(.*)$') {
    return "`$HOME/$($Matches[1])"
  }
  return $RepoOrPath
}

function Invoke-LAB-NODE-01Ssh {
  param(
    [string]$Cmd,
    # Remote sudo/become often needs a TTY (e.g. Defaults requiretty). Plain ssh has none.
    [switch]$AllocateTTY
  )
  $Cmd = ConvertTo-UnixLf $Cmd
  if ($AllocateTTY) {
    ssh -tt $SshHost $Cmd
  } else {
    ssh $SshHost $Cmd
  }
  if ($LASTEXITCODE -ne 0) {
    throw "SSH command failed with exit code $LASTEXITCODE"
  }
}

Write-Host "== LAB-NODE-01 Ansible $(if ($PodmanOnly) { 'Podman-only' } else { 'baseline' }) ==" -ForegroundColor Cyan
Write-Host "Host: $SshHost"
Write-Host "Repo: $RepoPath"
Write-Host "Mode: $(if ($Apply) { 'APPLY' } else { 'CHECK' })"
$playbookRel = if ($PodmanOnly) { "playbooks/lab-node-01-podman.yml" } else { "playbooks/lab-node-01-baseline.yml" }
Write-Host "Playbook: $playbookRel"

$bashRepoRoot = Get-BashCdPath $RepoPath
$bashAnsibleDir = Get-BashCdPath "$RepoPath/ops/automation/ansible"

# Remote scripts must use LF only: PowerShell here-strings are CRLF on Windows and break bash (cd $'path\r', set, perl, ansible).
$preflightLines = @(
  'set -eu',
  "cd `"$bashRepoRoot`"",
  'command -v git >/dev/null',
  'command -v ansible-playbook >/dev/null'
)
Invoke-LAB-NODE-01Ssh ($preflightLines -join "`n")

# Passwordless path: narrow sudoers allows sudo -n /bin/bash .../lab-node-01-ansible-labop-podman-apply.sh {--apply|--check}
# (see ops/automation/ansible/roles/lab_node_01_labop_sudoers and docs/ops/LAB_OP_PRIVILEGED_COLLECTION.md).
if ($PodmanOnly -and $NoAskBecomePass) {
  Write-Host "Using LAB-OP sudoers wrapper (sudo -n ... lab-node-01-ansible-labop-podman-apply.sh); no BECOME password prompt." -ForegroundColor Cyan
  $wrapperLines = @('set -eu', "cd `"$bashRepoRoot`"")
  if ($Apply -and -not $SkipCheck) {
    $wrapperLines += 'sudo -n /bin/bash scripts/lab-node-01-ansible-labop-podman-apply.sh --check'
    $wrapperLines += 'sudo -n /bin/bash scripts/lab-node-01-ansible-labop-podman-apply.sh --apply'
  } elseif ($Apply) {
    $wrapperLines += 'sudo -n /bin/bash scripts/lab-node-01-ansible-labop-podman-apply.sh --apply'
  } else {
    $wrapperLines += 'sudo -n /bin/bash scripts/lab-node-01-ansible-labop-podman-apply.sh --check'
  }
  Invoke-LAB-NODE-01Ssh ($wrapperLines -join "`n")
  Write-Host "Done." -ForegroundColor Green
  return
}

# Ansible calls sudo non-interactively unless you pass --ask-become-pass (-K). A prior `sudo -v` does not satisfy that.
$becomePart = if ($NoAskBecomePass) { "" } else { "--ask-become-pass" }
if (-not $NoAskBecomePass) {
  Write-Host "Ansible will prompt once per playbook run for BECOME (sudo) password on $SshHost (use -NoAskBecomePass if NOPASSWD)." -ForegroundColor Yellow
}

# Generate a local inventory pinned to localhost/local connection, then run check/apply.
$runModeArgs = if ($Apply) { "--diff" } else { "--check --diff" }

$runLines = @(
  'set -eu',
  "cd `"$bashAnsibleDir`"",
  'cp -f inventory.example.ini inventory.local.ini',
  "perl -0777 -pe 's/^\[lab-node-01\]\n.*?\n\n/[lab-node-01]\nlocalhost ansible_connection=local\n\n/ms' -i inventory.local.ini"
)
if ($Apply -and -not $SkipCheck) {
  $runLines += "ANSIBLE_ROLES_PATH=./roles ansible-playbook -i inventory.local.ini $becomePart $playbookRel --check --diff"
  $runLines += "ANSIBLE_ROLES_PATH=./roles ansible-playbook -i inventory.local.ini $becomePart $playbookRel --diff"
} else {
  $runLines += "ANSIBLE_ROLES_PATH=./roles ansible-playbook -i inventory.local.ini $becomePart $playbookRel $runModeArgs"
}
Invoke-LAB-NODE-01Ssh ($runLines -join "`n") -AllocateTTY

Write-Host "Done." -ForegroundColor Green
