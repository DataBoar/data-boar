# scripts/maestro/Get-LabStatus.ps1
# Hierarquia de Prontidão Sanitizada: ICMP -> SSH -> TMUX

param(
    [Parameter(Mandatory=$true)][string]$TargetHost,
    [Parameter(Mandatory=$true)][string]$TargetUser
)

$expectedSession = "completao"
$icmp = "DOWN"
$ssh  = "DOWN"
$tmux = "N/A"
# [Alteração 1]
$lastResult = "N/A"

Write-Host "Probing $TargetHost... " -NoNewline -ForegroundColor Gray

# 1. Teste ICMP (Ping silencioso)
if (Test-Connection -ComputerName $TargetHost -Count 1 -Quiet) {
    $icmp = "UP"

# 2. Teste SSH Ninja: Puxa Tmux e Status na MESMA conexão SSH usando usuario injetado pelo Maestro
    $probeCmd = "tmux ls 2>/dev/null ; echo '@@@' ; cat ~/.labop-status 2>/dev/null ; exit 0"
    $rawOutput = ssh -q -o ConnectTimeout=8 -o BatchMode=yes "${TargetUser}@${TargetHost}" "$probeCmd"

    if ($LASTEXITCODE -eq 0 -and $null -ne $rawOutput) {
        $ssh = "UP"

        # 2.1 Quebra a resposta da sonda nos dois pedaços
        # CORREÇÃO SRE: Junta o array em uma única string ANTES de dar o split!
        $joinedOutput = $rawOutput -join "`n"
        $parts = $joinedOutput -split "@@@"

        $tmuxLs = $parts[0]
        $statusRaw = if ($parts.Count -gt 1) { $parts[1].Trim() } else { "" }

        # 3. Valida a sessão Tmux
        if ($tmuxLs -match $expectedSession) {
            $tmux = "WARM ($expectedSession)"
        } else {
            $tmux = "COLD (No Session)"
        }

	# 4. Lê telemetria (sem criar novas variáveis desnecessárias ou abrir novas sessoes ssh)
        if ($statusRaw) {
            $lastResult = $statusRaw
        } else {
            $lastResult = "PENDING"
        }
    }
}

# Feedback visual mantido original (Essencial para o SRE)
if ($icmp -eq "UP" -and $ssh -eq "UP" -and $tmux -match "WARM") {
    Write-Host "[READY]" -ForegroundColor Green
} elseif ($icmp -eq "UP" -and $ssh -eq "UP") {
    Write-Host "[SSH UP/NO SESSION]" -ForegroundColor Yellow
} elseif ($icmp -eq "UP") {
    Write-Host "[NETWORK ONLY]" -ForegroundColor Cyan
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
