#Requires -Version 5.1
<#
.SYNOPSIS
    Orquestrador de coleta periodica via session cookies (Growatt, Enel, LinkedIn, redes sociais).

.DESCRIPTION
    Gerencia o ciclo de coleta para todos os servicos que requerem sessao autenticada.
    Frequencias sugeridas:
    - Growatt  : semanal (toda segunda-feira)
    - Enel     : mensal (primeiro dia do mes)
    - LinkedIn : por demanda (verificar candidatos apos envio de dicas ATS)
    - Outras redes: por demanda

    Verifica automaticamente quais sessoes estao validas antes de coletar.

.PARAMETER Service
    all (default) | growatt | enel | linkedin | social | status

.PARAMETER Force
    Ignora verificacao de frequencia e coleta mesmo que ja coletou recentemente.

.EXAMPLE
    .\scripts\session-collect.ps1                   # coleta tudo que esta na janela
    .\scripts\session-collect.ps1 -Service growatt  # apenas Growatt
    .\scripts\session-collect.ps1 -Service status   # mostra status de todas as sessoes
    .\scripts\session-collect.ps1 -Service linkedin # verifica colaboradores no LinkedIn

.NOTES
    Shorthand no chat: session-collect growatt | session-collect enel | session-collect status
    Skill: .cursor/skills/session-aware-collect/SKILL.md
    Sessoes: docs/private/homelab/.env.*.session (gitignored)
#>
param(
    [ValidateSet("all","growatt","enel","aguas","claro","leste","finance","linkedin","social","status")]
    [string]$Service = "all",
    [switch]$Force
)

$ErrorActionPreference = "Continue"
$repoRoot   = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$privateDir = Join-Path $repoRoot "docs\private\homelab"
$stateFile  = Join-Path $privateDir "session-collect-state.json"

function Write-Header($msg) { Write-Host "`n=== $msg ===" -ForegroundColor Cyan }
function Write-Ok($msg)     { Write-Host "  OK  $msg" -ForegroundColor Green }
function Write-Warn($msg)   { Write-Host " WARN $msg" -ForegroundColor Yellow }
function Write-Info($msg)   { Write-Host "  ... $msg" -ForegroundColor Gray }
function Write-Skip($msg)   { Write-Host " SKIP $msg" -ForegroundColor DarkGray }

function Get-State {
    if (Test-Path $stateFile) {
        return Get-Content $stateFile | ConvertFrom-Json
    }
    return @{ growatt = $null; enel = $null; linkedin = $null; social = $null }
}

function Save-State($state) {
    $state | ConvertTo-Json | Set-Content $stateFile -Encoding UTF8
}

function Should-Collect($service, $state, $daysInterval) {
    if ($Force) { return $true }
    $last = $state.$service
    if (-not $last) { return $true }
    $elapsed = (Get-Date) - [DateTime]$last
    return $elapsed.TotalDays -ge $daysInterval
}

$state = Get-State

Write-Header "Session Collect -- Orquestrador ($(Get-Date -Format 'yyyy-MM-dd HH:mm'))"

# --- STATUS ---
if ($Service -eq "status") {
    Write-Header "Status das Sessoes e Ultima Coleta"
    $services = @{
        "growatt"  = @{ Interval = 7;  EnvFile = ".env.growatt.session";  Label = "Growatt (semanal)" }
        "enel"     = @{ Interval = 30; EnvFile = ".env.enel.session";     Label = "Enel (mensal)" }
        "linkedin" = @{ Interval = 14; EnvFile = "";                      Label = "LinkedIn (quinzenal, browser warm)" }
        "social"   = @{ Interval = 30; EnvFile = "";                      Label = "Redes sociais (mensal, browser warm)" }
    }
    foreach ($svc in $services.GetEnumerator()) {
        $last     = $state.($svc.Key)
        $daysAgo  = if ($last) { [math]::Round(((Get-Date) - [DateTime]$last).TotalDays, 0) } else { "nunca" }
        $envPath  = if ($svc.Value.EnvFile) { Join-Path $privateDir $svc.Value.EnvFile } else { "" }
        $hasCred  = if ($envPath -and (Test-Path $envPath)) { "cookie OK" } else { "sem cookie" }
        $status   = if ($last) { "ultima: $daysAgo dias atras" } else { "NUNCA COLETADO" }
        $next     = if ($last) {
            $nextDate = ([DateTime]$last).AddDays($svc.Value.Interval)
            if ($nextDate -lt (Get-Date)) { "JA VENCEU" } else { $nextDate.ToString("yyyy-MM-dd") }
        } else { "IMEDIATO" }
        Write-Host "  $($svc.Value.Label)" -ForegroundColor Cyan
        Write-Host "    Status: $status | Proximo: $next | Credencial: $hasCred"
    }
    exit 0
}

# --- GROWATT ---
if ($Service -in @("all","growatt")) {
    $interval = 7  # dias
    if (Should-Collect "growatt" $state $interval) {
        Write-Header "Growatt -- Verificando sessao"
        $envFile = Join-Path $privateDir ".env.growatt.session"
        if (Test-Path $envFile) {
            Write-Info "Rodando: .\scripts\growatt-session-collect.ps1 -Mode save"
            & (Join-Path $repoRoot "scripts\growatt-session-collect.ps1") -Mode save
            $state.growatt = (Get-Date -Format "o")
            Save-State $state
            Write-Ok "Growatt: coleta concluida"
        } else {
            Write-Warn "Growatt: cookie nao configurado"
            Write-Info "  Arquivo: $envFile"
            Write-Info "  Guia: .\scripts\growatt-session-collect.ps1 -Mode check"
        }
    } else {
        $last = $state.growatt
        Write-Skip "Growatt: coletado ha menos de $interval dias ($last) -- use -Force para forcar"
    }
}

# --- ENEL ---
if ($Service -in @("all","enel")) {
    $interval = 30  # dias
    if (Should-Collect "enel" $state $interval) {
        Write-Header "Enel -- Verificando dados"
        Write-Info "Enel requer verificacao manual mensal no browser (guardrail: sem formularios)"
        Write-Info "  1. Abrir: https://www.enel.com.br/pt/private-area.html"
        Write-Info "  2. Anotar consumo e status em: docs/private/homelab/ENEL_ACCOUNT_NOTES.md"
        Write-Info "  3. Para ler dados existentes: .\scripts\enel.ps1"
        $state.enel = (Get-Date -Format "o")
        Save-State $state
        Write-Ok "Enel: lembrete registrado -- verificar manualmente no browser"
    } else {
        $last = $state.enel
        Write-Skip "Enel: verificado ha menos de $interval dias ($last) -- use -Force para forcar"
    }
}


# --- AGUAS DE NITEROI ---
if ($Service -in @("all","aguas","finance")) {
    $interval = 30
    if (Should-Collect "aguas" $state $interval -or $Force) {
        Write-Header "Aguas de Niteroi -- Instrucoes de Coleta"
        & (Join-Path $repoRoot "scripts\aguas.ps1") -Mode browser
        $state.aguas = (Get-Date -Format "o")
        Save-State $state
        Write-Ok "Aguas: instrucoes exibidas -- verificar e registrar com aguas.ps1 -Mode save"
    } else { Write-Skip "Aguas: verificado recentemente ($($state.aguas))" }
}

# --- CLARO CELULAR ---
if ($Service -in @("all","claro","finance")) {
    $interval = 30
    if (Should-Collect "claro" $state $interval -or $Force) {
        Write-Header "Claro Celular -- Instrucoes de Coleta"
        & (Join-Path $repoRoot "scripts\claro.ps1") -Mode browser
        $state.claro = (Get-Date -Format "o")
        Save-State $state
        Write-Ok "Claro: instrucoes exibidas"
    } else { Write-Skip "Claro: verificado recentemente ($($state.claro))" }
}

# --- LESTE TELECOM ---
if ($Service -in @("all","leste","finance")) {
    $interval = 30
    if (Should-Collect "leste" $state $interval -or $Force) {
        Write-Header "Leste Telecom -- Instrucoes de Coleta"
        & (Join-Path $repoRoot "scripts\leste.ps1") -Mode browser
        $state.leste = (Get-Date -Format "o")
        Save-State $state
        Write-Ok "Leste: instrucoes exibidas"
    } else { Write-Skip "Leste: verificado recentemente ($($state.leste))" }
}

# --- DASHBOARD FINANCEIRO ---
if ($Service -eq "finance") {
    Write-Header "Dashboard Financeiro Completo"
    & (Join-Path $repoRoot "scripts\household-finance.ps1") -Mode status
}
# --- LINKEDIN (candidatos) ---
if ($Service -in @("all","linkedin")) {
    $interval = 14  # dias
    if (Should-Collect "linkedin" $state $interval) {
        Write-Header "LinkedIn -- Verificar colaboradores"
        Write-Info "Uso do browser warm para verificar progresso ATS dos colaboradores:"
        Write-Info "  talent.ps1 linkedin candidate_a"
        Write-Info "  talent.ps1 linkedin candidate_b"
        Write-Info "  talent.ps1 linkedin candidate_c"
        Write-Info "  talent.ps1 linkedin candidate_d"
        Write-Info ""
        Write-Info "Checklist ATS: ver headlines, Open to Work, certificacoes novas"
        Write-Info "Skill: .cursor/private/skills/candidate-ats-evaluation/SKILL.md (Passo 4)"

        $state.linkedin = (Get-Date -Format "o")
        Save-State $state
        Write-Ok "LinkedIn: checklist exibido -- executar manualmente com browser warm"
    } else {
        $last = $state.linkedin
        Write-Skip "LinkedIn: verificado ha menos de $interval dias ($last)"
    }
}

# --- REDES SOCIAIS (X, Instagram, Threads, FacColleague-Sok) ---
if ($Service -in @("all","social")) {
    $interval = 30  # dias
    if (Should-Collect "social" $state $interval) {
        Write-Header "Redes Sociais -- Checklist de atualizacoes"
        Write-Info "Com browser warm, verificar:"
        Write-Info "  X (@presuntorj)        : https://x.com/presuntorj"
        Write-Info "  Instagram (@presuntorj) : https://www.instagram.com/presuntorj/"
        Write-Info "  Threads (@presuntorj)   : https://www.threads.com/@presuntorj"
        Write-Info "  Gravatar                : https://gravatar.com/fabioleitao"
        Write-Info ""
        Write-Info "Para colaboradores -- verificar atividade recente:"
        foreach ($candidato in @("candidate_a","candidate_b","candidate_c","candidate_d")) {
            Write-Info "  talent.ps1 linkedin $candidato"
        }
        $state.social = (Get-Date -Format "o")
        Save-State $state
        Write-Ok "Social: checklist exibido -- executar manualmente com browser warm"
    } else {
        $last = $state.social
        Write-Skip "Social: verificado ha menos de $interval dias ($last)"
    }
}

Write-Header "Concluido"
Write-Info "Para ver status: .\scripts\session-collect.ps1 -Service status"

