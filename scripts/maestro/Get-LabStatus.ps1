# scripts/maestro/Get-LabStatus.ps1
# Hierarquia de Prontidão Sanitizada: ICMP -> SSH -> TMUX

param(
    [Parameter(Mandatory=$true)][string]$TargetHost,
    [Parameter(Mandatory=$true)][string]$TargetUser,
    [string]$RunMarker = ""
)

$expectedSession = "completao"
$icmp = "DOWN"
$ssh  = "DOWN"
$tmux = "N/A"
# [Alteração 1]
$lastResult = "N/A"

Write-Host "Probing $TargetHost... " -NoNewline -ForegroundColor Gray

# 1. Teste ICMP (informativo APENAS; nunca gateia o SSH -- #952).
#    Em pwsh no Linux o socket ICMP raw pode exigir privilegio -> Test-Connection
#    lanca excecao ou retorna falso-DOWN. SSH e a fonte da verdade de prontidao;
#    um no com ICMP bloqueado mas SSH up (hardening comum) NAO deve ser pulado.
try {
    if (Test-Connection -ComputerName $TargetHost -Count 1 -Quiet -ErrorAction SilentlyContinue) {
        $icmp = "UP"
    }
} catch {
    $icmp = "DOWN"
}

# 2. Teste SSH Ninja (#952): roda SEMPRE, independente do resultado do ICMP.
#    Puxa Tmux e Status na MESMA conexao SSH usando o usuario injetado pelo Maestro.
$probeCmd = "tmux ls 2>/dev/null ; echo '@@@' ; cat ~/.labop-status 2>/dev/null ; exit 0"
$rawOutput = ssh -q -o ConnectTimeout=8 -o BatchMode=yes "${TargetUser}@${TargetHost}" "$probeCmd"

if ($LASTEXITCODE -eq 0 -and $null -ne $rawOutput) {
    $ssh = "UP"

    # 2.1 Quebra a resposta da sonda nos dois pedacos
    # CORRECAO SRE: Junta o array em uma unica string ANTES de dar o split!
    $joinedOutput = $rawOutput -join "`n"
    $parts = $joinedOutput -split "@@@"

    $tmuxLs = $parts[0]
    $statusRaw = if ($parts.Count -gt 1) { $parts[1].Trim() } else { "" }

    # 3. Valida a sessao Tmux
    if ($tmuxLs -match $expectedSession) {
        $tmux = "WARM ($expectedSession)"
    } else {
        $tmux = "COLD (No Session)"
    }

    # 4. Le telemetria (#969: NOT_RUN apos reset; STALE se marker de outro turno)
    if ($statusRaw -match '^\s*NOT_RUN\b') {
        $lastResult = "NOT_RUN"
    } elseif ($RunMarker -and $statusRaw -and $statusRaw -notmatch [regex]::Escape($RunMarker)) {
        $lastResult = "STALE ($statusRaw)"
    } elseif ($statusRaw) {
        $lastResult = $statusRaw
    } else {
        $lastResult = "NOT_RUN"
    }
}

# Feedback visual (SSH = fonte da verdade de prontidao; ICMP so informativo -- #952)
if ($ssh -eq "UP" -and $tmux -match "WARM") {
    Write-Host "[READY]" -ForegroundColor Green
} elseif ($ssh -eq "UP") {
    Write-Host "[SSH UP/NO SESSION]" -ForegroundColor Yellow
} elseif ($icmp -eq "UP") {
    Write-Host "[NETWORK ONLY (ICMP up, SSH down)]" -ForegroundColor Cyan
} else {
    Write-Host "[OFFLINE]" -ForegroundColor Red
}

# Retorna o objeto para o Maestro consolidar, se necessário
# [Alteração 3] - Retorna o objeto com a nova coluna
return [PSCustomObject]@{
    Node      = $TargetHost
    ICMP      = $icmp
    SSH       = $ssh
    Tmux      = $tmux
    Status    = $lastResult  # <--- O Maestro vai usar isso
    Timestamp = (Get-Date -Format "HH:mm:ss")
}
